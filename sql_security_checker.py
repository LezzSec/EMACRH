#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outil de vérification automatique de sécurité SQL pour le projet EMAC"""

import sys
import os

# Forcer l'encodage UTF-8 sur Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

"""

Scan les fichiers Python pour détecter:
- F-strings utilisées pour construire des requêtes SQL
- Concaténation de strings pour SQL
- Constructions dynamiques dangereuses
- Patterns de sécurité SQL

Usage:
    python sql_security_checker.py [--path /chemin/vers/App/core] [--fix-suggestions]
"""

import re
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Niveaux de risque de sécurité"""
    CRITICAL = "CRITIQUE"
    MEDIUM = "MOYEN"
    LOW = "FAIBLE"
    INFO = "INFO"


@dataclass
class Finding:
    """Représente une vulnérabilité trouvée"""
    file_path: str
    line_number: int
    risk_level: RiskLevel
    pattern: str
    code_snippet: str
    message: str
    suggestion: str = ""


class SQLSecurityChecker:
    """Vérificateur de sécurité SQL"""

    def __init__(self, root_path: str = None):
        self.root_path = Path(root_path or "App/core")
        self.findings: List[Finding] = []

        # Patterns dangereux à détecter
        self.dangerous_patterns = {
            # F-strings dans execute()
            r'execute\s*\(\s*f["\']': {
                'name': 'F-string in execute()',
                'risk': RiskLevel.CRITICAL,
                'message': 'F-string utilisée directement dans execute()'
            },
            # execute() avec variable simple
            r'execute\s*\(\s*\w+\s*[,)]': {
                'name': 'Variable in execute without params',
                'risk': RiskLevel.CRITICAL,
                'message': 'Variable passée directement sans paramètres'
            },
            # String format() avec SQL
            r'execute\s*\(.*\.format\s*\(': {
                'name': 'Format string in SQL',
                'risk': RiskLevel.CRITICAL,
                'message': 'Utilisation de .format() pour construire SQL'
            },
            # Concaténation visuelle
            r'query\s*\+=\s*["\'].*%|query\s*\+=\s*f["\']': {
                'name': 'Dynamic query concatenation',
                'risk': RiskLevel.MEDIUM,
                'message': 'Construction dynamique de requête avec +='
            },
        }

    def scan_file(self, file_path: Path) -> List[Finding]:
        """Scan un fichier pour les vulnérabilités SQL"""
        findings = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"⚠️ Impossible de lire {file_path}: {e}")
            return findings

        for line_num, line in enumerate(lines, 1):
            # Vérifier les patterns dangereux
            findings.extend(self._check_line(file_path, line_num, line))

        return findings

    def _check_line(self, file_path: Path, line_num: int, line: str) -> List[Finding]:
        """Vérifier une ligne pour les patterns dangereux"""
        findings = []

        # Pattern 1: F-string directement dans execute()
        if re.search(r'execute\s*\(\s*f["\']', line):
            # Vérifier si c'est vraiment SQL (pas d'erreur message)
            if 'SELECT' in line or 'INSERT' in line or 'UPDATE' in line or 'DELETE' in line or 'FROM' in line:
                findings.append(Finding(
                    file_path=str(file_path),
                    line_number=line_num,
                    risk_level=RiskLevel.CRITICAL,
                    pattern='execute(f"...")',
                    code_snippet=line.strip(),
                    message='F-string utilisée dans execute() - RISQUE INJECTION SQL',
                    suggestion='Utiliser des paramètres %s avec tuple: execute(query, params)'
                ))

        # Pattern 2: query += avec f-string
        if re.search(r'query\s*\+=\s*f["\']', line):
            findings.append(Finding(
                file_path=str(file_path),
                line_number=line_num,
                risk_level=RiskLevel.MEDIUM,
                pattern='query += f"..."',
                code_snippet=line.strip(),
                message='Construction dynamique de requête avec f-string',
                suggestion='Valider les valeurs dynamiques ou utiliser liste blanche'
            ))

        # Pattern 3: LIMIT avec interpolation
        if 'LIMIT' in line and re.search(r'\${|f["\'].*LIMIT|LIMIT.*{', line):
            findings.append(Finding(
                file_path=str(file_path),
                line_number=line_num,
                risk_level=RiskLevel.CRITICAL,
                pattern='LIMIT with interpolation',
                code_snippet=line.strip(),
                message='Clause LIMIT construite avec interpolation - RISQUE LIMIT INJECTION',
                suggestion='Utiliser int(limit) avec validation: 0 < limit <= MAX'
            ))

        # Pattern 4: WHERE avec join() et f-string
        if 'WHERE' in line and re.search(r"WHERE.*\{.*join|f['\"].*WHERE.*join", line):
            findings.append(Finding(
                file_path=str(file_path),
                line_number=line_num,
                risk_level=RiskLevel.MEDIUM,
                pattern='WHERE with dynamic join',
                code_snippet=line.strip(),
                message='Clause WHERE construite dynamiquement',
                suggestion='Valider les fragments WHERE avant de les joindre'
            ))

        # Pattern 5: Concaténation de string pour SQL
        if re.search(r'(query|sql)\s*\+=\s*["\'].*(?:SELECT|INSERT|UPDATE|DELETE|AND|OR|WHERE|LIMIT)', line):
            findings.append(Finding(
                file_path=str(file_path),
                line_number=line_num,
                risk_level=RiskLevel.MEDIUM,
                pattern='String concatenation for SQL',
                code_snippet=line.strip(),
                message='Concaténation de string pour SQL',
                suggestion='Construire les requêtes avec des variables et des paramètres séparés'
            ))

        return findings

    def scan_directory(self, root_path: Path = None) -> List[Finding]:
        """Scan récursivement le répertoire pour les vulnérabilités"""
        if root_path is None:
            root_path = self.root_path

        if not root_path.exists():
            print(f"[ERREUR] Chemin introuvable: {root_path}")
            return []

        print(f"[SCAN] Scan en cours de {root_path}...")

        all_findings = []
        python_files = list(root_path.rglob("*.py"))

        for py_file in python_files:
            # Ignorer les tests et les scripts
            if 'test' in py_file.name or 'test' in str(py_file).lower():
                continue
            if py_file.parent.name == 'scripts':
                continue

            findings = self.scan_file(py_file)
            all_findings.extend(findings)

        return all_findings

    def print_report(self, findings: List[Finding], verbose: bool = False):
        """Affiche un rapport des vulnérabilités trouvées"""
        if not findings:
            print("[OK] Aucune vulnérabilité trouvée!")
            return

        # Grouper par niveau de risque
        by_risk = {}
        for finding in findings:
            risk = finding.risk_level
            if risk not in by_risk:
                by_risk[risk] = []
            by_risk[risk].append(finding)

        # Afficher les résultats
        print("\n" + "="*80)
        print(f"[RAPPORT SQL] {len(findings)} vulnérabilité(s) trouvée(s)")
        print("="*80)

        # Résumé par niveau
        print("\n[RESUME]")
        for risk in [RiskLevel.CRITICAL, RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.INFO]:
            count = len(by_risk.get(risk, []))
            print(f"  [{risk.value}]: {count}")

        # Détails par niveau
        for risk in [RiskLevel.CRITICAL, RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.INFO]:
            findings_for_risk = by_risk.get(risk, [])
            if not findings_for_risk:
                continue

            print(f"\n{'='*80}")
            print(f"[{risk.value}]")
            print(f"{'='*80}")

            for finding in findings_for_risk:
                print(f"\n[FICHIER] {finding.file_path}:{finding.line_number}")
                print(f"  [MESSAGE] {finding.message}")
                print(f"  [PATTERN] {finding.pattern}")
                if verbose:
                    print(f"  [CODE] {finding.code_snippet}")
                    if finding.suggestion:
                        print(f"  [SUGGESTION] {finding.suggestion}")

    def export_json(self, findings: List[Finding], output_file: str):
        """Exporte les résultats en JSON"""
        import json

        data = {
            'total': len(findings),
            'critical': len([f for f in findings if f.risk_level == RiskLevel.CRITICAL]),
            'medium': len([f for f in findings if f.risk_level == RiskLevel.MEDIUM]),
            'findings': [
                {
                    'file': f.file_path,
                    'line': f.line_number,
                    'risk': f.risk_level.value,
                    'pattern': f.pattern,
                    'message': f.message,
                    'suggestion': f.suggestion,
                    'code': f.code_snippet
                }
                for f in findings
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Resultats exportes vers {output_file}")

    def generate_fix_script(self, findings: List[Finding], output_file: str):
        """Génère un script avec les suggestions de correction"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("# -*- coding: utf-8 -*-\n")
            f.write("# Script d'aide aux corrections de sécurité SQL\n")
            f.write("# GÉNÉRÉ AUTOMATIQUEMENT - À ADAPTER MANUELLEMENT\n\n")

            # Grouper par fichier
            by_file = {}
            for finding in findings:
                if finding.file_path not in by_file:
                    by_file[finding.file_path] = []
                by_file[finding.file_path].append(finding)

            for file_path, file_findings in sorted(by_file.items()):
                f.write(f"\n# {file_path}\n")
                f.write(f"# {len(file_findings)} vulnérabilité(s)\n")
                f.write("#" + "-"*78 + "\n")

                for finding in file_findings:
                    f.write(f"\n# Ligne {finding.line_number}: {finding.message}\n")
                    f.write(f"# Risque: {finding.risk_level.value}\n")
                    f.write(f"# Code: {finding.code_snippet}\n")
                    if finding.suggestion:
                        f.write(f"# Suggestion: {finding.suggestion}\n")
                    f.write("#\n")

        print(f"\n[OK] Suggestions de correction ecrites vers {output_file}")


def main():
    """Fonction principale"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Vérificateur de sécurité SQL pour EMAC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python sql_security_checker.py
  python sql_security_checker.py --path ./App/core --verbose
  python sql_security_checker.py --export findings.json
  python sql_security_checker.py --fix-script fixes.py
        """
    )

    parser.add_argument(
        '--path',
        default='App/core',
        help='Chemin vers le répertoire à scanner (défaut: App/core)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Affichage verbeux avec snippets de code'
    )
    parser.add_argument(
        '--export',
        help='Exporter les résultats en JSON'
    )
    parser.add_argument(
        '--fix-script',
        help='Générer un script avec les suggestions'
    )

    args = parser.parse_args()

    # Créer le vérificateur
    checker = SQLSecurityChecker(args.path)

    # Scanner
    findings = checker.scan_directory()

    # Afficher le rapport
    checker.print_report(findings, verbose=args.verbose)

    # Exporter si demandé
    if args.export:
        checker.export_json(findings, args.export)

    if args.fix_script:
        checker.generate_fix_script(findings, args.fix_script)

    # Retour avec code d'erreur approprié
    critical_count = len([f for f in findings if f.risk_level == RiskLevel.CRITICAL])
    if critical_count > 0:
        print(f"\n[ERREUR] {critical_count} vulnerabilite(s) CRITIQUE(s) trouvee(s)")
        return 1
    else:
        print(f"\n[OK] Scan complete")
        return 0


if __name__ == '__main__':
    sys.exit(main())
