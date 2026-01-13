#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Crée le poste "PRODUCTION" par défaut dans la base de données
==============================================================

Ce poste sera automatiquement affecté aux nouveaux opérateurs avec matricule

Usage:
    python App/scripts/creer_poste_production_defaut.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db.configbd import DatabaseConnection


def main():
    print("=" * 70)
    print("CRÉATION DU POSTE 'PRODUCTION' PAR DÉFAUT")
    print("=" * 70)
    print()

    with DatabaseConnection() as conn:
        cur = conn.cursor(dictionary=True)

        # Vérifier si le poste PRODUCTION existe déjà
        cur.execute("""
            SELECT id, poste_code, visible
            FROM postes
            WHERE poste_code = 'PRODUCTION'
        """)
        existing = cur.fetchone()

        if existing:
            print(f"[INFO] Le poste 'PRODUCTION' existe déjà (ID: {existing['id']})")
            print(f"       Visible: {existing['visible']}")
            print()

            if existing['visible'] == 0:
                print("[WARN] Le poste 'PRODUCTION' est invisible.")
                reponse = input("Voulez-vous le rendre visible ? (oui/non): ").strip().lower()
                if reponse in ['oui', 'o', 'yes', 'y']:
                    cur.execute("UPDATE postes SET visible = 1 WHERE id = %s", (existing['id'],))
                    conn.commit()
                    print("[OK] Poste 'PRODUCTION' rendu visible")
            else:
                print("[OK] Le poste 'PRODUCTION' est déjà configuré correctement")
        else:
            # Créer le poste PRODUCTION
            print("[INFO] Création du poste 'PRODUCTION'...")

            # Récupérer l'ID du premier atelier disponible
            cur.execute("SELECT id, nom FROM atelier ORDER BY id LIMIT 1")
            atelier = cur.fetchone()

            if not atelier:
                print("[ERREUR] Aucun atelier trouvé dans la base de données.")
                print("         Veuillez d'abord créer un atelier.")
                return

            atelier_id = atelier['id']
            atelier_nom = atelier['nom']

            print(f"         Atelier associé: {atelier_nom} (ID: {atelier_id})")

            # Insérer le poste
            cur.execute("""
                INSERT INTO postes (poste_code, atelier_id, visible)
                VALUES ('PRODUCTION', %s, 1)
            """, (atelier_id,))

            poste_id = cur.lastrowid
            conn.commit()

            print()
            print("[OK] Poste 'PRODUCTION' créé avec succès !")
            print(f"     ID: {poste_id}")
            print(f"     Code: PRODUCTION")
            print(f"     Atelier: {atelier_nom}")
            print(f"     Visible: Oui")

        cur.close()

    print()
    print("=" * 70)
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
