# -*- coding: utf-8 -*-
"""
Script pour mettre à jour les permissions du rôle gestion_rh
- Activer l'écriture sur 'personnel' (pour ajouter du personnel)
- Désactiver l'accès à 'grilles' (lecture/écriture/suppression)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.configbd import get_connection


def update_permissions():
    """Met à jour les permissions pour le rôle gestion_rh"""
    print(">> Mise à jour des permissions pour le rôle gestion_rh...")

    conn = get_connection()
    if not conn:
        print("[ERREUR] Impossible de se connecter à la base de données")
        return False

    cursor = conn.cursor()

    try:
        # 1. Retirer l'accès aux grilles
        print("\n[INFO] Retrait de l'accès au module 'grilles'...")
        cursor.execute("""
            UPDATE permissions
            SET lecture=0, ecriture=0, suppression=0
            WHERE role_id=3 AND module='grilles'
        """)

        # 2. Activer l'écriture sur personnel
        print("[INFO] Activation de l'écriture sur le module 'personnel'...")
        cursor.execute("""
            UPDATE permissions
            SET ecriture=1, suppression=1
            WHERE role_id=3 AND module='personnel'
        """)

        conn.commit()

        # Afficher les permissions mises à jour
        print("\n[SUCCES] Permissions mises à jour pour gestion_rh:")
        print("-" * 70)
        cursor.execute("""
            SELECT module, lecture, ecriture, suppression
            FROM permissions
            WHERE role_id=3
            ORDER BY module
        """)

        for row in cursor.fetchall():
            module = row[0]
            lecture = "OUI" if row[1] else "NON"
            ecriture = "OUI" if row[2] else "NON"
            suppression = "OUI" if row[3] else "NON"
            print(f"  {module:20s} | Lecture: {lecture:3s} | Ecriture: {ecriture:3s} | Suppression: {suppression:3s}")

        print("-" * 70)
        print("\n[INFO] Résumé des changements:")
        print("  - Les utilisateurs gestion_rh PEUVENT maintenant ajouter du personnel")
        print("  - Les utilisateurs gestion_rh NE VOIENT PLUS 'Liste et Grilles' dans le menu")

        return True

    except Exception as e:
        print(f"\n[ERREUR] Erreur lors de la mise à jour: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("MISE A JOUR DES PERMISSIONS - Gestion RH")
    print("=" * 70)
    print()

    success = update_permissions()

    print()
    print("=" * 70)

    if success:
        print("[SUCCES] Permissions mises à jour avec succès!")
        sys.exit(0)
    else:
        print("[ERREUR] La mise à jour a échoué")
        sys.exit(1)
