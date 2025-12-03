# -*- coding: utf-8 -*-
"""
Script pour supprimer des opérateurs
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db.configbd import get_connection

def delete_operators(operator_ids):
    """
    Supprime les opérateurs et leurs données associées

    Args:
        operator_ids (list): Liste des IDs à supprimer
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        for op_id in operator_ids:
            # Vérifier l'opérateur
            cur.execute("SELECT id, nom, prenom, matricule FROM personnel WHERE id = %s", (op_id,))
            operator = cur.fetchone()

            if not operator:
                print(f"Operateur {op_id} non trouve")
                continue

            print(f"Suppression de: ID={operator[0]}, {operator[2]} {operator[1]}, Matricule={operator[3]}")

            # Supprimer les polyvalences associées
            cur.execute("DELETE FROM polyvalence WHERE operateur_id = %s", (op_id,))
            deleted_poly = cur.rowcount
            print(f"  - {deleted_poly} polyvalence(s) supprimee(s)")

            # Supprimer l'historique associé
            cur.execute("DELETE FROM historique WHERE operateur_id = %s", (op_id,))
            deleted_hist = cur.rowcount
            print(f"  - {deleted_hist} entree(s) d'historique supprimee(s)")

            # Supprimer l'opérateur
            cur.execute("DELETE FROM personnel WHERE id = %s", (op_id,))
            print(f"  - Operateur supprime")

        conn.commit()
        print(f"\nSuppression terminee avec succes!")

    except Exception as e:
        print(f"Erreur: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # IDs à supprimer
    ids_to_delete = [372, 373]
    delete_operators(ids_to_delete)
