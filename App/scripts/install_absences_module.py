# -*- coding: utf-8 -*-
"""
Script d'installation du module Absences et Congés
"""

from core.db.configbd import get_connection

def install_absences_module():
    """Installe les tables et données pour le module absences"""

    conn = get_connection()
    cur = conn.cursor()

    try:
        print("=" * 70)
        print("INSTALLATION MODULE ABSENCES ET CONGÉS")
        print("=" * 70)

        # Lire le fichier SQL
        with open('Version BDD/schema_absences_conges.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Séparer les commandes SQL
        commands = []
        current_command = []

        for line in sql_content.split('\n'):
            line = line.strip()

            # Ignorer les commentaires et lignes vides
            if not line or line.startswith('--'):
                continue

            current_command.append(line)

            # Si la ligne se termine par ;, c'est la fin d'une commande
            if line.endswith(';'):
                commands.append(' '.join(current_command))
                current_command = []

        # Exécuter chaque commande
        success_count = 0
        error_count = 0

        for i, command in enumerate(commands, 1):
            if not command.strip():
                continue

            try:
                # Ignorer les commandes CREATE OR REPLACE VIEW (syntaxe spéciale)
                if 'CREATE OR REPLACE VIEW' in command:
                    # Remplacer par DROP + CREATE
                    view_name = command.split('VIEW')[1].split('AS')[0].strip()
                    try:
                        cur.execute(f"DROP VIEW IF EXISTS {view_name}")
                    except:
                        pass
                    # Remplacer CREATE OR REPLACE par CREATE
                    command = command.replace('CREATE OR REPLACE VIEW', 'CREATE VIEW')

                cur.execute(command)
                success_count += 1

                # Afficher un message pour les tables créées
                if 'CREATE TABLE' in command:
                    table_name = command.split('TABLE')[1].split('(')[0].strip().split()[0]
                    if 'IF NOT EXISTS' in command:
                        table_name = table_name.replace('IF', '').replace('NOT', '').replace('EXISTS', '').strip()
                    print(f"[OK] Table créée: {table_name}")
                elif 'INSERT INTO' in command:
                    table_name = command.split('INSERT INTO')[1].split('(')[0].strip()
                    print(f"[OK] Données insérées dans: {table_name}")
                elif 'CREATE VIEW' in command:
                    view_name = command.split('VIEW')[1].split('AS')[0].strip()
                    print(f"[OK] Vue créée: {view_name}")

            except Exception as e:
                error_count += 1
                print(f"[ERREUR] Commande {i}: {str(e)[:100]}")

        conn.commit()

        print("\n" + "=" * 70)
        print(f"RÉSULTAT: {success_count} commandes réussies, {error_count} erreurs")
        print("=" * 70)

        # Vérifier les tables créées
        print("\nVérification des tables créées:")
        cur.execute("SHOW TABLES LIKE '%absence%' OR LIKE '%conge%' OR LIKE '%ferie%'")
        tables = cur.fetchall()

        if tables:
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cur.fetchone()[0]
                print(f"  - {table[0]}: {count} enregistrement(s)")

        print("\n[OK] Installation terminée!")
        return True

    except Exception as e:
        print(f"\n[ERREUR] Installation échouée: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    install_absences_module()
