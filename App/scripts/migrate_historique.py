# -*- coding: utf-8 -*-
"""
Script de migration pour ajouter les colonnes manquantes à la table historique
"""

from core.db.configbd import get_connection

def migrate_historique():
    """Ajoute les colonnes manquantes à la table historique."""
    conn = get_connection()
    cur = conn.cursor()

    migrations = [
        # table_name
        """
        ALTER TABLE historique
        ADD COLUMN table_name VARCHAR(100) DEFAULT NULL AFTER action
        """,

        # record_id
        """
        ALTER TABLE historique
        ADD COLUMN record_id VARCHAR(50) DEFAULT NULL AFTER table_name
        """,

        # utilisateur
        """
        ALTER TABLE historique
        ADD COLUMN utilisateur VARCHAR(100) DEFAULT NULL AFTER record_id
        """,

        # details
        """
        ALTER TABLE historique
        ADD COLUMN details TEXT DEFAULT NULL AFTER description
        """,

        # source
        """
        ALTER TABLE historique
        ADD COLUMN source VARCHAR(255) DEFAULT NULL AFTER details
        """,

        # Index
        """
        CREATE INDEX idx_table_name ON historique(table_name)
        """,

        """
        CREATE INDEX idx_source ON historique(source)
        """
    ]

    for i, sql in enumerate(migrations, 1):
        try:
            print(f"Exécution migration {i}/{len(migrations)}...")
            cur.execute(sql)
            conn.commit()
            print(f"[OK] Migration {i} reussie")
        except Exception as e:
            if "Duplicate column name" in str(e) or "Duplicate key name" in str(e):
                print(f"[SKIP] Migration {i} deja appliquee")
            else:
                print(f"[ERR] Erreur migration {i}: {e}")
                conn.rollback()

    # Afficher la structure finale
    print("\n" + "="*60)
    print("Structure finale de la table historique:")
    print("="*60)
    cur.execute("DESCRIBE historique")
    for row in cur.fetchall():
        print(f"  {row[0]:20s} {row[1]:20s} {row[2]}")

    cur.close()
    conn.close()
    print("\n[OK] Migration terminee avec succes !")

if __name__ == "__main__":
    migrate_historique()
