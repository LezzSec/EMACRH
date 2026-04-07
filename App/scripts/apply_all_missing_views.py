# -*- coding: utf-8 -*-
"""Script pour appliquer toutes les vues manquantes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.db.configbd import get_connection

def main():
    migration_file = Path(__file__).parent.parent / 'database' / 'migrations' / 'create_all_missing_views.sql'

    print(f"Lecture du fichier de migration: {migration_file}")
    sql_content = migration_file.read_text(encoding='utf-8')

    # Séparer les commandes SQL (en ignorant ORDER BY qui n'a pas de ;)
    statements = []
    current_statement = []
    in_create_view = False

    for line in sql_content.split('\n'):
        stripped = line.strip()

        # Ignorer les commentaires vides et lignes vides
        if not stripped or stripped.startswith('--'):
            continue

        # Détecter le début d'un CREATE VIEW
        if 'CREATE VIEW' in stripped or 'DROP VIEW' in stripped:
            in_create_view = True

        current_statement.append(line)

        # Si la ligne se termine par ; c'est la fin de la commande
        if stripped.endswith(';'):
            statements.append('\n'.join(current_statement))
            current_statement = []
            in_create_view = False

    print(f"\nTrouve {len(statements)} commandes SQL a executer\n")

    conn = get_connection()
    cur = conn.cursor()

    try:
        for i, statement in enumerate(statements, 1):
            # Afficher un aperçu de la commande
            preview = statement.strip()[:80].replace('\n', ' ')
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

        required_views = [
            'v_contrat_anciennete',
            'v_contrats_fin_proche',
            'v_suivi_medical',
            'v_vie_salarie_recap'
        ]

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
