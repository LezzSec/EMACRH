#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnostic et nettoyage des "retards fantômes"
=========================================================

Identifie les évaluations comptées comme "en retard" mais invisibles
dans l'interface (postes invisibles, opérateurs sans matricule, etc.)

Usage:
    python App/scripts/diagnostic_retards_fantomes.py [--fix]

Options:
    --fix    Corrige automatiquement les problèmes détectés
"""

import sys
import os
from datetime import date

# Ajouter le répertoire App au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db.configbd import DatabaseConnection, DatabaseCursor


class RetardFantomeDiagnostic:
    """Diagnostique et corrige les retards fantômes"""

    def __init__(self):
        self.problemes = []
        self.stats = {
            'total_retards': 0,
            'postes_invisibles': 0,
            'operateurs_sans_matricule': 0,
            'postes_null': 0,
            'dates_invalides': 0
        }

    def run_diagnostic(self):
        """Exécute le diagnostic complet"""
        print("=" * 70)
        print("DIAGNOSTIC DES RETARDS FANTOMES")
        print("=" * 70)
        print()

        with DatabaseConnection() as conn:
            # 1. Compter tous les retards
            self._count_all_retards(conn)

            # 2. Identifier les retards avec postes invisibles
            self._check_postes_invisibles(conn)

            # 3. Identifier les retards d'opérateurs sans matricule
            self._check_operateurs_sans_matricule(conn)

            # 4. Identifier les retards avec postes NULL
            self._check_postes_null(conn)

            # 5. Identifier les dates invalides
            self._check_dates_invalides(conn)

        # Afficher le résumé
        self._print_summary()

    def _count_all_retards(self, conn):
        """Compte tous les retards dans la base"""
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT COUNT(*) as total
                FROM polyvalence poly
                INNER JOIN personnel p ON p.id = poly.operateur_id
                WHERE poly.prochaine_evaluation < CURDATE()
                  AND p.statut = 'ACTIF'
            """)
            result = cur.fetchone()
            self.stats['total_retards'] = result['total']

        print(f"[STATS] Total des évaluations en retard: {self.stats['total_retards']}")
        print()

    def _check_postes_invisibles(self, conn):
        """Identifie les retards sur des postes invisibles"""
        print("1.  Vérification des postes invisibles...")

        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    p.nom,
                    p.prenom,
                    p.matricule,
                    pos.poste_code,
                    pos.visible,
                    poly.prochaine_evaluation,
                    poly.niveau,
                    DATEDIFF(CURDATE(), poly.prochaine_evaluation) as jours_retard
                FROM polyvalence poly
                INNER JOIN personnel p ON p.id = poly.operateur_id
                INNER JOIN postes pos ON pos.id = poly.poste_id
                WHERE poly.prochaine_evaluation < CURDATE()
                  AND p.statut = 'ACTIF'
                  AND pos.visible = 0
                ORDER BY poly.prochaine_evaluation ASC
            """)
            results = cur.fetchall()

        self.stats['postes_invisibles'] = len(results)

        if results:
            print(f"   [WARN]  {len(results)} retard(s) sur des postes invisibles:")
            for r in results[:10]:  # Limiter à 10 pour l'affichage
                print(f"      • {r['nom']} {r['prenom']} ({r['matricule'] or 'sans matricule'})")
                print(f"        → Poste: {r['poste_code']} (invisible)")
                print(f"        → Retard: {r['jours_retard']} jour(s) - Niveau: {r['niveau']}")
            if len(results) > 10:
                print(f"      ... et {len(results) - 10} autre(s)")

            self.problemes.extend([{
                'type': 'poste_invisible',
                'data': r
            } for r in results])
        else:
            print("   [OK] Aucun retard sur poste invisible")

        print()

    def _check_operateurs_sans_matricule(self, conn):
        """Identifie les retards d'opérateurs sans matricule"""
        print("2.  Vérification des opérateurs sans matricule...")

        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    p.nom,
                    p.prenom,
                    p.matricule,
                    pos.poste_code,
                    poly.prochaine_evaluation,
                    poly.niveau,
                    DATEDIFF(CURDATE(), poly.prochaine_evaluation) as jours_retard
                FROM polyvalence poly
                INNER JOIN personnel p ON p.id = poly.operateur_id
                LEFT JOIN postes pos ON pos.id = poly.poste_id
                WHERE poly.prochaine_evaluation < CURDATE()
                  AND p.statut = 'ACTIF'
                  AND (p.matricule IS NULL OR p.matricule = '')
                ORDER BY poly.prochaine_evaluation ASC
            """)
            results = cur.fetchall()

        self.stats['operateurs_sans_matricule'] = len(results)

        if results:
            print(f"   [WARN]  {len(results)} retard(s) d'opérateurs sans matricule:")
            for r in results[:10]:
                print(f"      • {r['nom']} {r['prenom']} (SANS MATRICULE)")
                print(f"        → Poste: {r['poste_code'] or 'N/A'}")
                print(f"        → Retard: {r['jours_retard']} jour(s) - Niveau: {r['niveau']}")
            if len(results) > 10:
                print(f"      ... et {len(results) - 10} autre(s)")

            self.problemes.extend([{
                'type': 'sans_matricule',
                'data': r
            } for r in results])
        else:
            print("   [OK] Aucun retard d'opérateur sans matricule")

        print()

    def _check_postes_null(self, conn):
        """Identifie les retards avec poste_id NULL"""
        print("3.  Vérification des postes NULL...")

        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    p.nom,
                    p.prenom,
                    p.matricule,
                    poly.poste_id,
                    poly.prochaine_evaluation,
                    poly.niveau,
                    DATEDIFF(CURDATE(), poly.prochaine_evaluation) as jours_retard
                FROM polyvalence poly
                INNER JOIN personnel p ON p.id = poly.operateur_id
                WHERE poly.prochaine_evaluation < CURDATE()
                  AND p.statut = 'ACTIF'
                  AND poly.poste_id IS NULL
                ORDER BY poly.prochaine_evaluation ASC
            """)
            results = cur.fetchall()

        self.stats['postes_null'] = len(results)

        if results:
            print(f"   [WARN]  {len(results)} retard(s) avec poste_id NULL:")
            for r in results[:10]:
                print(f"      • {r['nom']} {r['prenom']} ({r['matricule'] or 'sans matricule'})")
                print(f"        → Poste: NULL (données corrompues)")
                print(f"        → Retard: {r['jours_retard']} jour(s) - Niveau: {r['niveau']}")
            if len(results) > 10:
                print(f"      ... et {len(results) - 10} autre(s)")

            self.problemes.extend([{
                'type': 'poste_null',
                'data': r
            } for r in results])
        else:
            print("   [OK] Aucun retard avec poste NULL")

        print()

    def _check_dates_invalides(self, conn):
        """Identifie les dates invalides ou aberrantes"""
        print("4.  Vérification des dates invalides...")

        with conn.cursor(dictionary=True) as cur:
            # Dates trop anciennes (> 5 ans de retard = suspect)
            cur.execute("""
                SELECT
                    p.nom,
                    p.prenom,
                    p.matricule,
                    pos.poste_code,
                    poly.prochaine_evaluation,
                    poly.niveau,
                    DATEDIFF(CURDATE(), poly.prochaine_evaluation) as jours_retard
                FROM polyvalence poly
                INNER JOIN personnel p ON p.id = poly.operateur_id
                LEFT JOIN postes pos ON pos.id = poly.poste_id
                WHERE poly.prochaine_evaluation < CURDATE()
                  AND p.statut = 'ACTIF'
                  AND DATEDIFF(CURDATE(), poly.prochaine_evaluation) > 1825
                ORDER BY poly.prochaine_evaluation ASC
            """)
            results = cur.fetchall()

        self.stats['dates_invalides'] = len(results)

        if results:
            print(f"   [WARN]  {len(results)} retard(s) avec dates suspectes (> 5 ans):")
            for r in results[:10]:
                print(f"      • {r['nom']} {r['prenom']} ({r['matricule'] or 'sans matricule'})")
                print(f"        → Poste: {r['poste_code'] or 'N/A'}")
                print(f"        → Retard: {r['jours_retard']} jour(s) ({r['jours_retard'] // 365} ans !)")
                print(f"        → Date: {r['prochaine_evaluation']}")
            if len(results) > 10:
                print(f"      ... et {len(results) - 10} autre(s)")

            self.problemes.extend([{
                'type': 'date_invalide',
                'data': r
            } for r in results])
        else:
            print("   [OK] Aucune date suspecte")

        print()

    def _print_summary(self):
        """Affiche le résumé du diagnostic"""
        print("=" * 70)
        print("[RESUME] RÉSUMÉ DU DIAGNOSTIC")
        print("=" * 70)
        print()
        print(f"Total des retards dans la base:           {self.stats['total_retards']}")
        print(f"  • Postes invisibles:                    {self.stats['postes_invisibles']}")
        print(f"  • Opérateurs sans matricule:            {self.stats['operateurs_sans_matricule']}")
        print(f"  • Postes NULL (corrompus):              {self.stats['postes_null']}")
        print(f"  • Dates invalides (> 5 ans retard):     {self.stats['dates_invalides']}")
        print()

        total_problemes = sum([
            self.stats['postes_invisibles'],
            self.stats['operateurs_sans_matricule'],
            self.stats['postes_null'],
            self.stats['dates_invalides']
        ])

        retards_visibles = self.stats['total_retards'] - total_problemes

        print(f"[CIBLE] Retards réellement visibles:           {retards_visibles}")
        print(f"[FANTOME] Retards fantômes (invisibles):         {total_problemes}")
        print()

        if total_problemes > 0:
            print("[INFO] RECOMMANDATIONS:")
            print()
            if self.stats['postes_invisibles'] > 0:
                print("   1. Postes invisibles:")
                print("      → Rendre les postes visibles OU supprimer les polyvalences")
            if self.stats['operateurs_sans_matricule'] > 0:
                print("   2. Opérateurs sans matricule:")
                print("      → Ajouter un matricule OU marquer comme INACTIF")
            if self.stats['postes_null'] > 0:
                print("   3. Postes NULL:")
                print("      → Supprimer ces polyvalences (données corrompues)")
            if self.stats['dates_invalides'] > 0:
                print("   4. Dates invalides:")
                print("      → Mettre à jour avec de nouvelles dates")
            print()
            print(f"   Exécutez avec --fix pour corriger automatiquement")

    def fix_problems(self):
        """Corrige automatiquement les problèmes détectés"""
        print()
        print("=" * 70)
        print("[FIX] CORRECTION AUTOMATIQUE")
        print("=" * 70)
        print()

        if not self.problemes:
            print("[OK] Aucun problème à corriger")
            return

        print(f"[WARN]  {len(self.problemes)} problème(s) détecté(s)")
        print()

        reponse = input("Voulez-vous vraiment corriger ces problèmes ? (oui/non): ").strip().lower()
        if reponse not in ['oui', 'o', 'yes', 'y']:
            print("[ERREUR] Correction annulée")
            return

        with DatabaseConnection() as conn:
            cur = conn.cursor()
            corrections = 0

            for probleme in self.problemes:
                type_pb = probleme['type']
                data = probleme['data']

                try:
                    if type_pb == 'poste_null':
                        # Supprimer les polyvalences avec poste NULL
                        cur.execute("""
                            DELETE FROM polyvalence
                            WHERE poste_id IS NULL
                              AND prochaine_evaluation < CURDATE()
                        """)
                        corrections += cur.rowcount

                    elif type_pb == 'date_invalide':
                        # Mettre à jour les dates aberrantes vers +10 ans
                        from datetime import timedelta
                        nouvelle_date = date.today() + timedelta(days=3650)
                        cur.execute("""
                            UPDATE polyvalence
                            SET prochaine_evaluation = %s
                            WHERE prochaine_evaluation < CURDATE()
                              AND DATEDIFF(CURDATE(), prochaine_evaluation) > 1825
                        """, (nouvelle_date,))
                        corrections += cur.rowcount

                except Exception as e:
                    print(f"   [ERREUR] Erreur lors de la correction: {e}")

            conn.commit()
            cur.close()

            print()
            print(f"[OK] {corrections} correction(s) appliquée(s)")
            print()
            print("[WARN]  NOTE:")
            print("   • Les postes invisibles et opérateurs sans matricule")
            print("     nécessitent une intervention manuelle")
            print("   • Relancez le diagnostic pour vérifier")


def main():
    """Point d'entrée du script"""
    fix_mode = '--fix' in sys.argv

    diagnostic = RetardFantomeDiagnostic()
    diagnostic.run_diagnostic()

    if fix_mode:
        diagnostic.fix_problems()
    elif diagnostic.problemes:
        print()
        print("[INFO] Pour corriger automatiquement, relancez avec: python diagnostic_retards_fantomes.py --fix")

    print()
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARN]  Interruption utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERREUR] ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
