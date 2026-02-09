# -*- coding: utf-8 -*-
"""
Script pour vérifier et appliquer la migration des liens documents-entités
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.configbd import get_connection

def check_columns_exist():
    """Vérifie si les colonnes formation_id, contrat_id, declaration_id existent."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME IN ('formation_id', 'contrat_id', 'declaration_id')
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        return existing_columns
    finally:
        cur.close()
        conn.close()

def apply_migration():
    """Applique la migration pour ajouter les colonnes manquantes."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        print("Application de la migration...")

        # Vérifier et ajouter formation_id
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME = 'formation_id'
        """)
        if cur.fetchone()[0] == 0:
            print("  - Ajout de la colonne formation_id...")
            cur.execute("""
                ALTER TABLE `documents`
                ADD COLUMN `formation_id` INT NULL AFTER `categorie_id`
            """)
            cur.execute("""
                ALTER TABLE `documents`
                ADD CONSTRAINT `fk_documents_formation`
                    FOREIGN KEY (`formation_id`) REFERENCES `formation`(`id`)
                    ON DELETE SET NULL
            """)
            print("    ✓ formation_id ajoutée")
        else:
            print("  - formation_id existe déjà")

        # Vérifier et ajouter contrat_id
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME = 'contrat_id'
        """)
        if cur.fetchone()[0] == 0:
            print("  - Ajout de la colonne contrat_id...")
            cur.execute("""
                ALTER TABLE `documents`
                ADD COLUMN `contrat_id` INT NULL AFTER `formation_id`
            """)
            cur.execute("""
                ALTER TABLE `documents`
                ADD CONSTRAINT `fk_documents_contrat`
                    FOREIGN KEY (`contrat_id`) REFERENCES `contrat`(`id`)
                    ON DELETE SET NULL
            """)
            print("    ✓ contrat_id ajoutée")
        else:
            print("  - contrat_id existe déjà")

        # Vérifier et ajouter declaration_id
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME = 'declaration_id'
        """)
        if cur.fetchone()[0] == 0:
            print("  - Ajout de la colonne declaration_id...")
            cur.execute("""
                ALTER TABLE `documents`
                ADD COLUMN `declaration_id` INT NULL AFTER `contrat_id`
            """)
            cur.execute("""
                ALTER TABLE `documents`
                ADD CONSTRAINT `fk_documents_declaration`
                    FOREIGN KEY (`declaration_id`) REFERENCES `declaration`(`id`)
                    ON DELETE SET NULL
            """)
            print("    ✓ declaration_id ajoutée")
        else:
            print("  - declaration_id existe déjà")

        # Ajouter les index si nécessaire
        print("  - Ajout des index...")
        try:
            cur.execute("CREATE INDEX `idx_documents_formation` ON `documents`(`formation_id`)")
            print("    ✓ Index formation_id créé")
        except Exception:
            print("    - Index formation_id existe déjà")

        try:
            cur.execute("CREATE INDEX `idx_documents_contrat` ON `documents`(`contrat_id`)")
            print("    ✓ Index contrat_id créé")
        except Exception:
            print("    - Index contrat_id existe déjà")

        try:
            cur.execute("CREATE INDEX `idx_documents_declaration` ON `documents`(`declaration_id`)")
            print("    ✓ Index declaration_id créé")
        except Exception:
            print("    - Index declaration_id existe déjà")

        conn.commit()
        print("\n✅ Migration appliquée avec succès!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erreur lors de la migration: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def check_column_name():
    """Vérifie si la colonne s'appelle operateur_id ou personnel_id."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME IN ('operateur_id', 'personnel_id')
        """)
        result = cur.fetchone()
        return result[0] if result else None
    finally:
        cur.close()
        conn.close()

def check_foreign_keys(column_name='operateur_id'):
    """Vérifie les contraintes de clés étrangères sur la colonne."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT
                CONSTRAINT_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME = %s
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (column_name,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def rename_operateur_to_personnel():
    """Renomme la colonne operateur_id en personnel_id."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        print("  - Renommage de operateur_id en personnel_id...")

        # Récupérer et supprimer la contrainte FK existante
        cur.execute("""
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME = 'operateur_id'
            AND REFERENCED_TABLE_NAME IS NOT NULL
            LIMIT 1
        """)
        result = cur.fetchone()

        if result:
            constraint_name = result[0]
            print(f"    - Suppression de la contrainte '{constraint_name}'...")
            cur.execute(f"ALTER TABLE `documents` DROP FOREIGN KEY `{constraint_name}`")

        # Renommer la colonne
        print("    - Renommage de la colonne...")
        cur.execute("""
            ALTER TABLE `documents`
            CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL
        """)

        # Recréer la contrainte FK
        print("    - Recréation de la contrainte FK vers 'personnel'...")
        cur.execute("""
            ALTER TABLE `documents`
            ADD CONSTRAINT `fk_documents_personnel`
                FOREIGN KEY (`personnel_id`) REFERENCES `personnel`(`id`)
                ON DELETE CASCADE
        """)

        # Renommer l'index si nécessaire
        try:
            cur.execute("ALTER TABLE `documents` DROP INDEX `idx_operateur`")
            cur.execute("CREATE INDEX `idx_personnel` ON `documents`(`personnel_id`)")
            print("    - Index renommé")
        except Exception:
            pass  # Index peut ne pas exister

        conn.commit()
        print("    ✓ Colonne renommée avec succès")
        print("\n    ⚠️  IMPORTANT: Vous devez aussi mettre à jour le code:")
        print("       - document_service.py : Remplacer 'operateur_id' par 'personnel_id'")
        print("       - bulk_service.py : Remplacer 'operateur_id=' par 'personnel_id='")
        return True

    except Exception as e:
        conn.rollback()
        print(f"    ⚠️  Erreur: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def fix_personnel_id_fk():
    """Corrige la contrainte de clé étrangère sur personnel_id pour pointer vers personnel."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        print("  - Correction de la clé étrangère personnel_id...")

        # Récupérer le nom de la contrainte existante
        cur.execute("""
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME = 'personnel_id'
            AND REFERENCED_TABLE_NAME IS NOT NULL
            LIMIT 1
        """)
        result = cur.fetchone()

        if result:
            constraint_name = result[0]
            print(f"    - Suppression de l'ancienne contrainte '{constraint_name}'...")
            cur.execute(f"ALTER TABLE `documents` DROP FOREIGN KEY `{constraint_name}`")

        # Créer la nouvelle contrainte pointant vers personnel
        print("    - Création de la nouvelle contrainte vers 'personnel'...")
        cur.execute("""
            ALTER TABLE `documents`
            ADD CONSTRAINT `fk_documents_personnel`
                FOREIGN KEY (`personnel_id`) REFERENCES `personnel`(`id`)
                ON DELETE CASCADE
        """)

        conn.commit()
        print("    ✓ Clé étrangère personnel_id corrigée")
        return True

    except Exception as e:
        conn.rollback()
        print(f"    ⚠️  Erreur: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def main():
    print("=== Vérification de la table documents ===\n")

    # Vérifier le nom de la colonne (operateur_id ou personnel_id)
    print("1️⃣  Vérification du nom de la colonne...")
    column_name = check_column_name()

    if column_name == 'operateur_id':
        print(f"   ⚠️  La colonne s'appelle encore 'operateur_id' (devrait être 'personnel_id')")
        response = input("   Renommer en 'personnel_id' pour plus de cohérence? (o/n): ")
        if response.lower() in ['o', 'oui', 'y', 'yes']:
            if rename_operateur_to_personnel():
                column_name = 'personnel_id'
                print()
            else:
                print("   ❌ Échec du renommage, abandon.\n")
                return
        else:
            print("   ℹ️  Conserve 'operateur_id'\n")
    elif column_name == 'personnel_id':
        print(f"   ✅ La colonne s'appelle déjà 'personnel_id'\n")

        # Vérifier la clé étrangère
        fks = check_foreign_keys('personnel_id')
        if fks:
            fk = fks[0]
            if fk['REFERENCED_TABLE_NAME'] == 'personnel':
                print(f"   ✅ personnel_id pointe correctement vers 'personnel'\n")
            else:
                print(f"   ⚠️  personnel_id pointe vers '{fk['REFERENCED_TABLE_NAME']}' (devrait être 'personnel')")
                response = input("   Corriger maintenant? (o/n): ")
                if response.lower() in ['o', 'oui', 'y', 'yes']:
                    fix_personnel_id_fk()
                print()
        else:
            print("   ⚠️  Aucune contrainte de clé étrangère trouvée sur personnel_id")
            response = input("   Créer la contrainte vers 'personnel'? (o/n): ")
            if response.lower() in ['o', 'oui', 'y', 'yes']:
                fix_personnel_id_fk()
            print()
    else:
        print("   ❌ Aucune colonne operateur_id ou personnel_id trouvée!")
        return

    # Vérifier les colonnes de liens
    print("2️⃣  Vérification des colonnes de liens (formation_id, contrat_id, etc.)...")
    existing = check_columns_exist()

    if len(existing) == 3:
        print("   ✅ Toutes les colonnes existent déjà:")
        for col in existing:
            print(f"      - {col}")
        print("\n✅ Aucune action nécessaire.")
        return

    print("   ⚠️  Colonnes manquantes:")
    missing = set(['formation_id', 'contrat_id', 'declaration_id']) - set(existing)
    for col in missing:
        print(f"      - {col}")

    if existing:
        print("\n   Colonnes existantes:")
        for col in existing:
            print(f"      - {col}")

    print("\n" + "="*60)
    response = input("\nAppliquer la migration des colonnes manquantes? (o/n): ")

    if response.lower() in ['o', 'oui', 'y', 'yes']:
        if apply_migration():
            print("\n✅ Migration terminée avec succès!")
            print("\nVous pouvez maintenant ré-essayer d'assigner une formation avec document.")
        else:
            print("\n❌ La migration a échoué. Vérifiez les erreurs ci-dessus.")
    else:
        print("\nMigration annulée.")

if __name__ == "__main__":
    main()
