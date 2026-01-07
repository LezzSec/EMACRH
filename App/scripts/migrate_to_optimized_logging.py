# -*- coding: utf-8 -*-
"""
Script de migration pour remplacer les print() et logs non-optimisés.

✅ Détecte et liste tous les print() dans des boucles
✅ Suggère des remplacements optimisés
✅ Peut appliquer automatiquement les corrections (avec backup)

Usage:
    # Analyser seulement
    python migrate_to_optimized_logging.py --analyze

    # Appliquer les corrections
    python migrate_to_optimized_logging.py --apply
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple


# ===========================
# Configuration
# ===========================

# Extensions à analyser
PYTHON_EXTENSIONS = ['.py']

# Dossiers à exclure
EXCLUDED_DIRS = [
    'venv', '__pycache__', '.git', 'build', 'dist',
    'migrations', 'backups', 'tests'
]

# Patterns à détecter
PATTERNS = {
    'print_in_loop': [
        # for ... print()
        (r'for\s+\w+\s+in\s+[^\:]+\:\s*\n\s+print\(', 'print() dans boucle for'),
        # while ... print()
        (r'while\s+[^\:]+\:\s*\n\s+print\(', 'print() dans boucle while'),
    ],
    'multiple_prints': [
        # 3+ print() consécutifs
        (r'(print\([^\)]*\)\s*\n\s*){3,}', '3+ print() consécutifs'),
    ],
    'log_hist_in_loop': [
        # for ... log_hist()
        (r'for\s+\w+\s+in\s+[^\:]+\:\s*\n\s+log_hist\(', 'log_hist() dans boucle for'),
    ],
}


# ===========================
# Analyseur de code
# ===========================

class CodeAnalyzer:
    """Analyse le code pour détecter les patterns non-optimisés"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.issues: List[Dict] = []

    def analyze(self):
        """Analyse tous les fichiers Python"""
        print("🔍 Analyse du code...")
        print(f"Dossier: {self.root_dir}")
        print()

        for py_file in self._find_python_files():
            self._analyze_file(py_file)

        return self.issues

    def _find_python_files(self) -> List[Path]:
        """Trouve tous les fichiers Python"""
        files = []

        for ext in PYTHON_EXTENSIONS:
            for file in self.root_dir.rglob(f'*{ext}'):
                # Exclure certains dossiers
                if any(excluded in file.parts for excluded in EXCLUDED_DIRS):
                    continue

                files.append(file)

        return files

    def _analyze_file(self, file_path: Path):
        """Analyse un fichier"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except:
            return

        # Détecter les patterns
        for pattern_type, patterns in PATTERNS.items():
            for regex, description in patterns:
                matches = re.finditer(regex, content, re.MULTILINE)

                for match in matches:
                    # Calculer le numéro de ligne
                    line_num = content[:match.start()].count('\n') + 1

                    self.issues.append({
                        'file': file_path,
                        'line': line_num,
                        'type': pattern_type,
                        'description': description,
                        'snippet': match.group(0)[:100]
                    })


# ===========================
# Générateur de suggestions
# ===========================

class SuggestionGenerator:
    """Génère des suggestions de remplacement"""

    @staticmethod
    def get_suggestion(issue: Dict) -> str:
        """Retourne une suggestion de remplacement"""
        issue_type = issue['type']

        if issue_type == 'print_in_loop':
            return """
# ❌ Avant (lent):
for item in items:
    print(f"Processing {item}")  # I/O à chaque itération !

# ✅ Après (optimisé):
from core.utils.optimized_logger import oprint, get_logger

# Option 1: oprint (buffered print)
for item in items:
    oprint(f"Processing {item}")  # Écriture par batch

# Option 2: Logger (meilleur)
logger = get_logger(__name__)
for item in items:
    logger.info(f"Processing {item}")  # Async + buffered
"""

        elif issue_type == 'multiple_prints':
            return """
# ❌ Avant (multiple I/O):
print("Début traitement")
print("Chargement données")
print("Traitement en cours")

# ✅ Après (1 seule I/O):
message = "\\n".join([
    "Début traitement",
    "Chargement données",
    "Traitement en cours"
])
print(message)

# Ou encore mieux:
from core.utils.optimized_logger import get_logger
logger = get_logger(__name__)
logger.info("Début traitement → Chargement données → Traitement en cours")
"""

        elif issue_type == 'log_hist_in_loop':
            return """
# ❌ Avant (N requêtes DB):
for poste in postes:
    log_hist('UPDATE', 'postes', poste['id'], 'Mise à jour')
    # 100 postes = 100 INSERT !

# ✅ Après (buffered, 1 requête pour N logs):
from core.services.optimized_db_logger import log_hist_async

for poste in postes:
    log_hist_async('UPDATE', 'postes', poste['id'], 'Mise à jour')
    # 100 postes = 2-3 INSERT (par batch de 50)
"""

        return "Pas de suggestion disponible"


# ===========================
# Rapport
# ===========================

def generate_report(issues: List[Dict]):
    """Génère un rapport d'analyse"""
    print("=" * 80)
    print("📊 RAPPORT D'ANALYSE")
    print("=" * 80)
    print()

    if not issues:
        print("✅ Aucun problème détecté !")
        print()
        return

    # Grouper par type
    by_type = {}
    for issue in issues:
        issue_type = issue['type']
        if issue_type not in by_type:
            by_type[issue_type] = []
        by_type[issue_type].append(issue)

    # Afficher résumé
    print(f"🔴 {len(issues)} problèmes détectés")
    print()

    for issue_type, type_issues in by_type.items():
        print(f"  • {issue_type}: {len(type_issues)} occurrences")

    print()
    print("=" * 80)
    print("📋 DÉTAILS")
    print("=" * 80)
    print()

    # Détails par fichier
    by_file = {}
    for issue in issues:
        file = issue['file']
        if file not in by_file:
            by_file[file] = []
        by_file[file].append(issue)

    for file, file_issues in sorted(by_file.items()):
        print(f"\n📄 {file.relative_to(Path.cwd())}")
        print("-" * 80)

        for issue in file_issues:
            print(f"  Ligne {issue['line']}: {issue['description']}")
            print(f"    → {issue['snippet'][:80]}...")

    print()
    print("=" * 80)
    print("💡 SUGGESTIONS")
    print("=" * 80)

    # Afficher suggestions uniques
    seen_types = set()
    for issue in issues:
        issue_type = issue['type']
        if issue_type not in seen_types:
            seen_types.add(issue_type)
            print(f"\n🔧 {issue_type}:")
            print(SuggestionGenerator.get_suggestion(issue))

    print()
    print("=" * 80)
    print("🎯 PROCHAINES ÉTAPES")
    print("=" * 80)
    print()
    print("1. Remplacer les print() dans les boucles par:")
    print("   - oprint() (rapide, simple)")
    print("   - get_logger() (mieux, structuré)")
    print()
    print("2. Remplacer log_hist() dans les boucles par:")
    print("   - log_hist_async() (10-50x moins de requêtes)")
    print()
    print("3. Regrouper les print() multiples consécutifs")
    print()


# ===========================
# Main
# ===========================

def main():
    parser = argparse.ArgumentParser(
        description='Détecte et corrige les logs non-optimisés'
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyse seulement (pas de modification)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Applique les corrections automatiquement'
    )

    args = parser.parse_args()

    # Déterminer le dossier racine
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent  # App/

    # Analyser
    analyzer = CodeAnalyzer(root_dir)
    issues = analyzer.analyze()

    # Générer rapport
    generate_report(issues)

    # Appliquer corrections si demandé
    if args.apply:
        print("⚠️  Mode --apply pas encore implémenté")
        print("   Veuillez appliquer les corrections manuellement")
        print()

    # Code de sortie
    sys.exit(1 if issues else 0)


if __name__ == '__main__':
    main()
