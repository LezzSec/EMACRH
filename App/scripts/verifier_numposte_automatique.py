#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vérifie que le champ numposte est correctement affecté à 'Production'
pour les opérateurs avec matricule
======================================================================

Usage:
    python App/scripts/verifier_numposte_automatique.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db.configbd import DatabaseConnection


def main():
    print("=" * 80)
    print("VÉRIFICATION DU CHAMP NUMPOSTE AUTOMATIQUE")
    print("=" * 80)
    print()

    with DatabaseConnection() as conn:
        cur = conn.cursor(dictionary=True)

        # 1. Opérateurs avec matricule MAIS sans numposte
        print("[1/3] Opérateurs avec matricule mais sans numposte...")
        print("-" * 80)

        cur.execute("""
            SELECT id, nom, prenom, matricule, numposte
            FROM personnel
            WHERE matricule IS NOT NULL
              AND matricule != ''
              AND (numposte IS NULL OR numposte = '')
            ORDER BY id DESC
            LIMIT 20
        """)
        sans_numposte = cur.fetchall()

        if sans_numposte:
            print(f"   [WARN] {len(sans_numposte)} operateur(s) avec matricule mais sans numposte:")
            for r in sans_numposte:
                print(f"      - {r['nom']} {r['prenom']} (matricule: {r['matricule']})")
                print(f"        > ID: {r['id']}, numposte: '{r['numposte'] or 'VIDE'}'")
        else:
            print("   [OK] Tous les opérateurs avec matricule ont un numposte")
        print()

        # 2. Opérateurs récents avec numposte = 'Production'
        print("[2/3] Opérateurs récents avec numposte = 'Production'...")
        print("-" * 80)

        cur.execute("""
            SELECT id, nom, prenom, matricule, numposte
            FROM personnel
            WHERE matricule IS NOT NULL
              AND matricule != ''
              AND numposte = 'Production'
            ORDER BY id DESC
            LIMIT 10
        """)
        avec_production = cur.fetchall()

        if avec_production:
            print(f"   [OK] {len(avec_production)} operateur(s) recent(s) avec numposte = 'Production':")
            for r in avec_production:
                print(f"      - {r['nom']} {r['prenom']} (matricule: {r['matricule']})")
        else:
            print("   [INFO] Aucun opérateur avec numposte = 'Production' trouvé")
        print()

        # 3. Statistiques globales
        print("[3/3] Statistiques globales...")
        print("-" * 80)

        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN matricule IS NOT NULL AND matricule != '' THEN 1 ELSE 0 END) as avec_matricule,
                SUM(CASE WHEN numposte IS NOT NULL AND numposte != '' THEN 1 ELSE 0 END) as avec_numposte,
                SUM(CASE WHEN numposte = 'Production' THEN 1 ELSE 0 END) as production
            FROM personnel
        """)
        stats = cur.fetchone()

        print(f"   Total des opérateurs:                 {stats['total']}")
        print(f"   Avec matricule:                       {stats['avec_matricule']}")
        print(f"   Avec numposte défini:                 {stats['avec_numposte']}")
        print(f"   Avec numposte = 'Production':         {stats['production']}")
        print()

        # 4. Recommandations
        if sans_numposte:
            print("=" * 80)
            print("[INFO] RECOMMANDATION")
            print("=" * 80)
            print()
            print(f"   {len(sans_numposte)} opérateur(s) avec matricule n'ont pas de numposte défini.")
            print()
            print("   Pour corriger automatiquement, exécutez:")
            print("   UPDATE personnel")
            print("   SET numposte = 'Production'")
            print("   WHERE matricule IS NOT NULL")
            print("     AND matricule != ''")
            print("     AND (numposte IS NULL OR numposte = '');")
            print()

        cur.close()

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
