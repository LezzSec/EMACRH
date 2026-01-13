#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vérifie la différence de comptage entre le dashboard et la gestion des évaluations
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db.configbd import DatabaseConnection

def main():
    print("=" * 70)
    print("VERIFICATION DU COMPTAGE DES RETARDS")
    print("=" * 70)
    print()

    with DatabaseConnection() as conn:
        cur = conn.cursor(dictionary=True)

        # 1. Comptage utilisé par le DASHBOARD (total des évaluations)
        print("1. DASHBOARD (main_qt.py)")
        print("   Compte: Le NOMBRE TOTAL d'évaluations en retard")
        print()
        cur.execute("""
            SELECT COUNT(*) as total
            FROM polyvalence poly
            INNER JOIN personnel p ON p.id = poly.operateur_id
            WHERE poly.prochaine_evaluation < CURDATE()
              AND p.statut = 'ACTIF'
        """)
        result = cur.fetchone()
        total_evaluations = result['total']
        print(f"   Résultat: {total_evaluations} évaluation(s) en retard")
        print()

        # 2. Comptage utilisé par GESTION DES EVALUATIONS (opérateurs groupés)
        print("2. GESTION DES EVALUATIONS (gestion_evaluation.py)")
        print("   Compte: Le NOMBRE D'OPERATEURS ayant au moins 1 retard")
        print()
        cur.execute("""
            SELECT
                p.id,
                p.nom,
                p.prenom,
                SUM(CASE WHEN poly.prochaine_evaluation < CURDATE() THEN 1 ELSE 0 END) as retard
            FROM personnel p
            INNER JOIN polyvalence poly ON poly.operateur_id = p.id
            WHERE p.statut = 'ACTIF'
            GROUP BY p.id, p.nom, p.prenom
            HAVING retard > 0
            ORDER BY retard DESC
        """)
        results = cur.fetchall()
        nb_operateurs = len(results)

        print(f"   Résultat: {nb_operateurs} opérateur(s) avec retard(s)")
        print()
        print("   Détail par opérateur:")
        for r in results:
            print(f"      • {r['nom']} {r['prenom']}: {r['retard']} évaluation(s) en retard")
        print()

        # 3. Synthèse
        print("=" * 70)
        print("SYNTHESE")
        print("=" * 70)
        print()
        print(f"Dashboard affiche:            {total_evaluations} (si compte par EVALUATIONS)")
        print(f"                          OU  {nb_operateurs} (si compte par OPERATEURS)")
        print()
        print(f"Gestion Évaluations affiche:  {nb_operateurs} ligne(s)")
        print(f"  avec détail individuel de chaque opérateur")
        print()

        if total_evaluations != nb_operateurs:
            print("[EXPLICATION]")
            print("  Le dashboard compte probablement par OPÉRATEUR (pas par évaluation)")
            print(f"  -> '{nb_operateurs} En retard' signifie '{nb_operateurs} OPERATEURS avec au moins 1 retard'")
            print()
            print("  Dans la liste, chaque ligne montre 1 opérateur avec son nombre de retards:")
            for r in results[:5]:
                print(f"    - {r['nom']}: {r['retard']} évaluation(s) en retard")
            if len(results) > 5:
                print(f"    ... et {len(results) - 5} autre(s)")

        cur.close()

    print()
    print("=" * 70)


if __name__ == '__main__':
    main()
