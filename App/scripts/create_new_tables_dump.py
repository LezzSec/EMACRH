# -*- coding: utf-8 -*-
"""
Script pour créer un dump uniquement des nouvelles tables
qui n'existent pas encore sur le serveur
"""
import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.configbd import get_connection

# Tables qui existent sur le serveur (depuis la capture d'écran)
SERVEUR_TABLES = {
    'atelier',
    'categories_documents',
    'classeur1',
    'contrat',
    'declaration',
    'demande_absence',
    'documents',
    'formation',
    'historique',
    'import_personnel',
    'jours_feries',
    'personnel',
    'personnel_backup_20251124_141820',
    'personnel_infos',
    'polyvalence',
    'postes',
    'services',
    'solde_conges',
    'tranche_age',
    'type_absence',
    'v_absences_details',
    'v_documents_complet',
    'v_documents_expiration_proche',
    'v_documents_stats_operateur',
    'v_soldes_disponibles',
    'v_stats_absences',
    'validite'
}

def get_create_table_statement(cursor, table_name):
    """Récupère le statement CREATE TABLE pour une table ou vue"""
    cursor.execute(f"SHOW CREATE TABLE {table_name}")
    result = cursor.fetchone()
    if result:
        create_stmt = result[1]

        # Si c'est une vue, nettoyer et utiliser CREATE OR REPLACE
        if 'VIEW' in create_stmt.upper():
            # Supprimer DEFINER et ALGORITHM pour éviter les problèmes de privilèges
            import re
            create_stmt = re.sub(r'CREATE.*?VIEW', 'CREATE OR REPLACE VIEW', create_stmt, flags=re.IGNORECASE)
            # Supprimer SQL SECURITY DEFINER
            create_stmt = re.sub(r'SQL SECURITY \w+', '', create_stmt, flags=re.IGNORECASE)
        else:
            # Pour les tables, ajouter IF NOT EXISTS
            create_stmt = create_stmt.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS', 1)

        return create_stmt
    return None

def get_table_data(cursor, table_name):
    """Récupère toutes les données d'une table"""
    cursor.execute(f"SELECT * FROM {table_name}")
    return cursor.fetchall()

def get_column_names(cursor, table_name):
    """Récupère les noms de colonnes d'une table"""
    cursor.execute(f"DESCRIBE {table_name}")
    return [row[0] for row in cursor.fetchall()]

def escape_value(value):
    """Échappe les valeurs pour SQL"""
    if value is None:
        return 'NULL'
    elif isinstance(value, str):
        # Échapper les apostrophes et backslashes
        escaped = value.replace('\\', '\\\\').replace("'", "\\'")
        return f"'{escaped}'"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, datetime):
        return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
    else:
        return f"'{str(value)}'"

def create_new_tables_dump():
    """Crée un dump uniquement des nouvelles tables"""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dump_file = os.path.join(
        os.path.dirname(__file__),
        '..', '..',
        'Fichiers inutilisés',
        f'nouvelles_tables_{timestamp}.sql'
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Récupérer toutes les tables locales
        cursor.execute("SHOW TABLES")
        local_tables = [row[0] for row in cursor.fetchall()]

        # Identifier les nouvelles tables
        new_tables = [t for t in local_tables if t not in SERVEUR_TABLES]

        if not new_tables:
            print("Aucune nouvelle table trouvee!")
            print("Toutes les tables locales existent deja sur le serveur.")
            return

        print(f"Nouvelles tables trouvees: {len(new_tables)}")
        for table in new_tables:
            print(f"  - {table}")

        with open(dump_file, 'w', encoding='utf-8') as f:
            # En-tête du dump
            f.write("-- =============================================\n")
            f.write("-- EMAC - Dump des nouvelles tables uniquement\n")
            f.write(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Nombre de tables: {len(new_tables)}\n")
            f.write("-- =============================================\n")
            f.write("-- ATTENTION: Ce dump contient uniquement les nouvelles tables\n")
            f.write("-- qui n'existent pas sur le serveur.\n")
            f.write("-- Il peut etre execute en toute securite sans risque\n")
            f.write("-- d'ecraser les donnees existantes.\n")
            f.write("-- =============================================\n\n")

            f.write("SET NAMES utf8mb4;\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

            # Pour chaque nouvelle table
            for table in new_tables:
                print(f"  Exportation: {table}...")

                f.write(f"-- =============================================\n")
                f.write(f"-- Nouvelle table: {table}\n")
                f.write(f"-- =============================================\n\n")

                # CREATE TABLE IF NOT EXISTS
                create_stmt = get_create_table_statement(cursor, table)
                if create_stmt:
                    f.write(f"{create_stmt};\n\n")

                # INSERT DATA
                columns = get_column_names(cursor, table)
                data = get_table_data(cursor, table)

                if data:
                    f.write(f"-- Donnees pour la table `{table}` ({len(data)} lignes)\n")

                    # Insérer par lots de 100 lignes
                    batch_size = 100
                    for i in range(0, len(data), batch_size):
                        batch = data[i:i+batch_size]

                        f.write(f"INSERT INTO `{table}` (")
                        f.write(", ".join([f"`{col}`" for col in columns]))
                        f.write(") VALUES\n")

                        for idx, row in enumerate(batch):
                            values = [escape_value(val) for val in row]
                            f.write(f"  ({', '.join(values)})")

                            if idx < len(batch) - 1:
                                f.write(",\n")
                            else:
                                f.write(";\n")

                        f.write("\n")
                else:
                    f.write(f"-- Aucune donnee dans la table `{table}`\n\n")

                f.write("\n")

            # Pied de page
            f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
            f.write("\n-- Dump des nouvelles tables termine\n")

        file_size = os.path.getsize(dump_file) / 1024
        print(f"\nDump cree avec succes: {dump_file}")
        print(f"Taille: {file_size:.2f} KB")
        print(f"\nCe fichier peut etre execute sur le serveur sans risque:")
        print(f"  mysql -u root -p emac_db < nouvelles_tables_{timestamp}.sql")

    except Exception as e:
        print(f"Erreur lors de la creation du dump: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_new_tables_dump()
