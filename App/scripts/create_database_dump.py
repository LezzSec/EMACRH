# -*- coding: utf-8 -*-
"""
Script pour créer un dump complet de la base de données emac_db
"""
import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.configbd import get_connection

def get_create_table_statement(cursor, table_name):
    """Récupère le statement CREATE TABLE pour une table"""
    cursor.execute(f"SHOW CREATE TABLE {table_name}")
    result = cursor.fetchone()
    return result[1] if result else None

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

def create_database_dump():
    """Crée un dump complet de la base de données"""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dump_file = os.path.join(
        os.path.dirname(__file__),
        '..', '..',
        'Fichiers inutilisés',
        f'emac_db_dump_{timestamp}.sql'
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Récupérer toutes les tables
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"Création du dump de {len(tables)} tables...")

        with open(dump_file, 'w', encoding='utf-8') as f:
            # En-tête du dump
            f.write("-- =============================================\n")
            f.write("-- EMAC Database Dump\n")
            f.write(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- Database: emac_db\n")
            f.write("-- =============================================\n\n")

            f.write("SET NAMES utf8mb4;\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

            # Pour chaque table
            for table in tables:
                print(f"  - Dumping table: {table}")

                # DROP TABLE
                f.write(f"-- =============================================\n")
                f.write(f"-- Table: {table}\n")
                f.write(f"-- =============================================\n")
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n\n")

                # CREATE TABLE
                create_stmt = get_create_table_statement(cursor, table)
                if create_stmt:
                    f.write(f"{create_stmt};\n\n")

                # INSERT DATA
                columns = get_column_names(cursor, table)
                data = get_table_data(cursor, table)

                if data:
                    f.write(f"-- Données pour la table `{table}` ({len(data)} lignes)\n")

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
                    f.write(f"-- Aucune donnée dans la table `{table}`\n\n")

                f.write("\n")

            # Pied de page
            f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
            f.write("\n-- Dump terminé\n")

        print(f"\n✓ Dump créé avec succès: {dump_file}")
        print(f"  Taille: {os.path.getsize(dump_file) / 1024:.2f} KB")

    except Exception as e:
        print(f"✗ Erreur lors de la création du dump: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_database_dump()
