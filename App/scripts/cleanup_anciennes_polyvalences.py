# -*- coding: utf-8 -*-
"""
Script pour supprimer les anciennes polyvalences de test (IMPORT_MANUEL)
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.configbd import get_connection

def cleanup_anciennes_polyvalences():
    """Supprime toutes les entrées IMPORT_MANUEL de historique_polyvalence."""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Supprimer toutes les entrées IMPORT_MANUEL
        cur.execute("DELETE FROM historique_polyvalence WHERE action_type = 'IMPORT_MANUEL'")
        deleted = cur.rowcount

        conn.commit()
        cur.close()
        conn.close()

        print(f"OK : {deleted} ancienne(s) polyvalence(s) de test supprimee(s)")
        return deleted

    except Exception as e:
        print(f"Erreur : {e}")
        return 0

if __name__ == "__main__":
    cleanup_anciennes_polyvalences()
