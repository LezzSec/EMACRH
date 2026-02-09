# -*- coding: utf-8 -*-
"""Script pour appliquer les vues manquantes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.configbd import get_connection

def main():
    migration_file = Path(__file__).parent.parent / 'database' / 'migrations' / 'create_missing_views.sql'

    print(f"Lecture du fichier de migration: {migration_file}")
    sql_content = migration_file.read_text(encoding='utf-8')

    # Séparer les commandes SQL
    statements = []
    current_statement = []

    for line in sql_content.split('\n'):
        # Ignorer les commentaires et lignes vides
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue

        current_statement.append(line)

        # Si la ligne se termine par ;, c'est la fin de la commande
        if stripped.endswith(';'):
            statements.append('\n'.join(current_statement))
            current_statement = []

    print(f"\nTrouve {len(statements)} commandes SQL a executer\n")

    conn = get_connection()
    cur = conn.cursor()

    try:
        for i, statement in enumerate(statements, 1):
            # Afficher un aperçu de la commande
            preview = statement.strip()[:100].replace('\n', ' ')
            print(f"[{i}/{len(statements)}] Execution: {preview}...")

            cur.execute(statement)
            print(f"  -> OK")

        conn.commit()
        print("\n=== SUCCES ===")
        print("Les vues ont ete creees avec succes!")

        # Vérifier que les vues existent
        print("\n=== VERIFICATION ===")
        cur.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
        views = [t[0] for t in cur.fetchall()]

        required_views = ['v_alertes_medicales', 'v_alertes_entretiens']
        for view_name in required_views:
            if view_name in views:
                print(f"  OK {view_name} existe")
            else:
                print(f"  ERREUR {view_name} MANQUANTE")

    except Exception as e:
        conn.rollback()
        print(f"\n=== ERREUR ===")
        print(f"Erreur lors de l'execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
