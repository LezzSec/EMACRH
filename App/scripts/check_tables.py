# -*- coding: utf-8 -*-
"""Script pour vérifier les tables/vues existantes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.configbd import get_connection

def main():
    conn = get_connection()
    cur = conn.cursor()

    print("=== TABLES ===")
    cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
    tables = [t[0] for t in cur.fetchall()]
    for table in sorted(tables):
        print(f"  {table}")

    print("\n=== VUES ===")
    cur.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
    views = [t[0] for t in cur.fetchall()]
    for view in sorted(views):
        print(f"  {view}")

    print("\n=== VÉRIFICATION DES VUES MANQUANTES ===")
    required_views = ['v_alertes_medicales', 'v_alertes_entretiens']
    for view_name in required_views:
        if view_name in views:
            print(f"  ✓ {view_name} existe")
        else:
            print(f"  ✗ {view_name} MANQUANTE")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
