#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnostic complet des doublons dans toute la base de données
========================================================================

Analyse toutes les tables critiques pour identifier les doublons potentiels

Usage:
    python App/scripts/diagnostic_doublons_complet.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db.configbd import DatabaseConnection


class DiagnosticDoublonsComplet:
    """Diagnostique les doublons dans toutes les tables critiques"""

    def __init__(self):
        self.problemes = []

    def run_diagnostic(self):
        """Exécute le diagnostic complet"""
        print("=" * 80)
        print("DIAGNOSTIC COMPLET DES DOUBLONS")
        print("=" * 80)
        print()

        with DatabaseConnection() as conn:
            # 1. Polyvalence (déjà corrigé mais vérification)
            self._check_polyvalence_doublons(conn)

            # 2. Personnel (doublons de matricules ou noms)
            self._check_personnel_doublons(conn)

            # 3. Postes (doublons de codes)
            self._check_postes_doublons(conn)

            # 4. Contrats (plusieurs contrats actifs pour une personne)
            self._check_contrats_doublons(conn)

            # 5. Absences (chevauchements de dates)
            self._check_absences_chevauchements(conn)

            # 6. Historique (redondances massives)
            self._check_historique_redondances(conn)

        # Résumé
        self._print_summary()

    def _check_polyvalence_doublons(self, conn):
        """Vérifie les doublons dans polyvalence"""
        print("[1/6] POLYVALENCE - Doublons (operateur_id, poste_id)")
        print("-" * 80)

        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    operateur_id,
                    poste_id,
                    COUNT(*) as nb_doublons,
                    GROUP_CONCAT(id ORDER BY id) as ids
                FROM polyvalence
                GROUP BY operateur_id, poste_id
                HAVING nb_doublons > 1
                ORDER BY nb_doublons DESC
            """)
            results = cur.fetchall()

        if results:
            print(f"   [WARN] {len(results)} doublon(s) trouvé(s):")
            for r in results[:10]:
                print(f"      • Opérateur {r['operateur_id']} / Poste {r['poste_id']}")
                print(f"        → {r['nb_doublons']} entrées (IDs: {r['ids']})")
            if len(results) > 10:
                print(f"      ... et {len(results) - 10} autre(s)")
            self.problemes.append(('polyvalence', len(results)))
        else:
            print("   [OK] Aucun doublon")
        print()

    def _check_personnel_doublons(self, conn):
        """Vérifie les doublons dans personnel"""
        print("[2/6] PERSONNEL - Doublons de matricules et noms")
        print("-" * 80)

        # Doublons de matricules
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    matricule,
                    COUNT(*) as nb_doublons,
                    GROUP_CONCAT(CONCAT(nom, ' ', prenom) SEPARATOR ', ') as personnes
                FROM personnel
                WHERE matricule IS NOT NULL AND matricule != ''
                GROUP BY matricule
                HAVING nb_doublons > 1
                ORDER BY nb_doublons DESC
            """)
            matricule_doublons = cur.fetchall()

        if matricule_doublons:
            print(f"   [WARN] {len(matricule_doublons)} matricule(s) en double:")
            for r in matricule_doublons:
                print(f"      • Matricule '{r['matricule']}': {r['nb_doublons']} personnes")
                print(f"        → {r['personnes']}")
            self.problemes.append(('personnel_matricules', len(matricule_doublons)))
        else:
            print("   [OK] Aucun doublon de matricule")

        print()

        # Doublons de noms complets (même nom + prénom)
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    nom,
                    prenom,
                    COUNT(*) as nb_doublons,
                    GROUP_CONCAT(id ORDER BY id) as ids,
                    GROUP_CONCAT(matricule ORDER BY id) as matricules
                FROM personnel
                GROUP BY nom, prenom
                HAVING nb_doublons > 1
                ORDER BY nb_doublons DESC
            """)
            nom_doublons = cur.fetchall()

        if nom_doublons:
            print(f"   [WARN] {len(nom_doublons)} nom(s) complet(s) en double:")
            for r in nom_doublons[:10]:
                print(f"      • {r['nom']} {r['prenom']}: {r['nb_doublons']} entrées")
                print(f"        → IDs: {r['ids']}")
                print(f"        → Matricules: {r['matricules'] or 'Aucun'}")
            if len(nom_doublons) > 10:
                print(f"      ... et {len(nom_doublons) - 10} autre(s)")
            self.problemes.append(('personnel_noms', len(nom_doublons)))
        else:
            print("   [OK] Aucun doublon de nom complet")

        print()

    def _check_postes_doublons(self, conn):
        """Vérifie les doublons dans postes"""
        print("[3/6] POSTES - Doublons de codes poste")
        print("-" * 80)

        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    poste_code,
                    COUNT(*) as nb_doublons,
                    GROUP_CONCAT(id ORDER BY id) as ids,
                    GROUP_CONCAT(visible ORDER BY id) as visibles
                FROM postes
                GROUP BY poste_code
                HAVING nb_doublons > 1
                ORDER BY nb_doublons DESC
            """)
            results = cur.fetchall()

        if results:
            print(f"   [WARN] {len(results)} code(s) poste en double:")
            for r in results:
                print(f"      • Poste '{r['poste_code']}': {r['nb_doublons']} entrées")
                print(f"        → IDs: {r['ids']}")
                print(f"        → Visibles: {r['visibles']}")
            self.problemes.append(('postes', len(results)))
        else:
            print("   [OK] Aucun doublon de code poste")
        print()

    def _check_contrats_doublons(self, conn):
        """Vérifie les contrats multiples actifs pour une même personne"""
        print("[4/6] CONTRATS - Contrats actifs multiples par personne")
        print("-" * 80)

        with conn.cursor(dictionary=True) as cur:
            # Vérifier si la table contrats existe
            cur.execute("""
                SELECT COUNT(*) as existe
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = 'contrats'
            """)
            table_existe = cur.fetchone()['existe']

            if not table_existe:
                print("   [INFO] Table 'contrats' n'existe pas encore")
                print()
                return

            cur.execute("""
                SELECT
                    c.operateur_id,
                    p.nom,
                    p.prenom,
                    p.matricule,
                    COUNT(*) as nb_contrats_actifs,
                    GROUP_CONCAT(CONCAT(c.type_contrat, ' (',
                        DATE_FORMAT(c.date_debut, '%d/%m/%Y'), ' - ',
                        COALESCE(DATE_FORMAT(c.date_fin, '%d/%m/%Y'), 'Indéterminé'), ')')
                        ORDER BY c.date_debut SEPARATOR ' | ') as contrats
                FROM contrats c
                INNER JOIN personnel p ON p.id = c.operateur_id
                WHERE c.date_fin IS NULL OR c.date_fin >= CURDATE()
                GROUP BY c.operateur_id, p.nom, p.prenom, p.matricule
                HAVING nb_contrats_actifs > 1
                ORDER BY nb_contrats_actifs DESC
            """)
            results = cur.fetchall()

        if results:
            print(f"   [WARN] {len(results)} personne(s) avec plusieurs contrats actifs:")
            for r in results:
                print(f"      • {r['nom']} {r['prenom']} ({r['matricule'] or 'sans matricule'})")
                print(f"        → {r['nb_contrats_actifs']} contrats actifs:")
                print(f"        → {r['contrats']}")
            self.problemes.append(('contrats', len(results)))
        else:
            print("   [OK] Aucun doublon de contrat actif")
        print()

    def _check_absences_chevauchements(self, conn):
        """Vérifie les chevauchements de périodes d'absence"""
        print("[5/6] ABSENCES - Chevauchements de dates")
        print("-" * 80)

        with conn.cursor(dictionary=True) as cur:
            # Vérifier si la table absences existe
            cur.execute("""
                SELECT COUNT(*) as existe
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = 'absences'
            """)
            table_existe = cur.fetchone()['existe']

            if not table_existe:
                print("   [INFO] Table 'absences' n'existe pas encore")
                print()
                return

            cur.execute("""
                SELECT
                    a1.operateur_id,
                    p.nom,
                    p.prenom,
                    COUNT(*) as nb_chevauchements,
                    GROUP_CONCAT(DISTINCT CONCAT(
                        DATE_FORMAT(a1.date_debut, '%d/%m/%Y'), ' - ',
                        DATE_FORMAT(a1.date_fin, '%d/%m/%Y')
                    ) SEPARATOR ' | ') as periodes
                FROM absences a1
                INNER JOIN absences a2 ON a1.operateur_id = a2.operateur_id
                                       AND a1.id < a2.id
                INNER JOIN personnel p ON p.id = a1.operateur_id
                WHERE (a1.date_debut BETWEEN a2.date_debut AND a2.date_fin)
                   OR (a1.date_fin BETWEEN a2.date_debut AND a2.date_fin)
                   OR (a2.date_debut BETWEEN a1.date_debut AND a1.date_fin)
                GROUP BY a1.operateur_id, p.nom, p.prenom
                ORDER BY nb_chevauchements DESC
            """)
            results = cur.fetchall()

        if results:
            print(f"   [WARN] {len(results)} personne(s) avec des périodes qui se chevauchent:")
            for r in results[:10]:
                print(f"      • {r['nom']} {r['prenom']}")
                print(f"        → {r['nb_chevauchements']} chevauchement(s)")
                print(f"        → Périodes: {r['periodes']}")
            if len(results) > 10:
                print(f"      ... et {len(results) - 10} autre(s)")
            self.problemes.append(('absences', len(results)))
        else:
            print("   [OK] Aucun chevauchement d'absences")
        print()

    def _check_historique_redondances(self, conn):
        """Vérifie les entrées identiques dans l'historique"""
        print("[6/6] HISTORIQUE - Entrées redondantes")
        print("-" * 80)

        with conn.cursor(dictionary=True) as cur:
            # Compter les lignes identiques (même action, description, operateur, poste dans un court laps de temps)
            cur.execute("""
                SELECT
                    action,
                    description,
                    COUNT(*) as nb_occurrences
                FROM historique
                WHERE date_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY action, description
                HAVING nb_occurrences > 50
                ORDER BY nb_occurrences DESC
                LIMIT 10
            """)
            results = cur.fetchall()

        if results:
            print(f"   [INFO] Actions répétées fréquemment (7 derniers jours):")
            for r in results:
                print(f"      • '{r['action']}': {r['nb_occurrences']} fois")
                desc = r['description'][:80] + '...' if len(r['description']) > 80 else r['description']
                print(f"        → {desc}")
            print()
            print("   [NOTE] Ceci est normal si ce sont des actions légitimes")
            print("          mais peut indiquer un problème si trop répétitif")
        else:
            print("   [OK] Pas de répétitions suspectes")
        print()

    def _print_summary(self):
        """Affiche le résumé"""
        print("=" * 80)
        print("[RESUME] RÉSUMÉ DU DIAGNOSTIC")
        print("=" * 80)
        print()

        if not self.problemes:
            print("[OK] Aucun doublon détecté dans la base de données")
            print()
            return

        print(f"[WARN] {len(self.problemes)} type(s) de problème(s) détecté(s):")
        print()

        for table, count in self.problemes:
            print(f"   • {table}: {count} problème(s)")

        print()
        print("[INFO] RECOMMANDATIONS:")
        print()

        for table, count in self.problemes:
            if table == 'polyvalence':
                print("   - Polyvalence: Exécuter les requêtes de nettoyage fournies précédemment")
            elif table == 'personnel_matricules':
                print("   - Personnel (matricules): Corriger les matricules en double ou supprimer les doublons")
            elif table == 'personnel_noms':
                print("   - Personnel (noms): Vérifier s'il s'agit de vraies personnes différentes ou de doublons")
            elif table == 'postes':
                print("   - Postes: Fusionner ou renommer les postes en double")
            elif table == 'contrats':
                print("   - Contrats: Vérifier les contrats multiples actifs (peut être légitime)")
            elif table == 'absences':
                print("   - Absences: Corriger les chevauchements de dates")

        print()


def main():
    """Point d'entrée du script"""
    diagnostic = DiagnosticDoublonsComplet()
    diagnostic.run_diagnostic()

    print("=" * 80)
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARN] Interruption utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERREUR] ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
