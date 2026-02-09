# -*- coding: utf-8 -*-
"""
Script complet pour configurer la table documents et la vue v_documents_complet.
Crée/met à jour tout ce qui est nécessaire pour le système documentaire.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.configbd import get_connection

def check_view_exists(view_name: str) -> bool:
    """Vérifie si une vue existe."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SHOW FULL TABLES WHERE Table_type = 'VIEW' AND Tables_in_emac_db = '{view_name}'")
        return cur.fetchone() is not None
    finally:
        cur.close()
        conn.close()

def create_view_documents_complet():
    """Crée ou recrée la vue v_documents_complet."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        print("  - Suppression de l'ancienne vue si elle existe...")
        cur.execute("DROP VIEW IF EXISTS `v_documents_complet`")

        print("  - Création de la vue v_documents_complet...")
        cur.execute("""
            CREATE VIEW `v_documents_complet` AS
            SELECT
                d.id,
                d.personnel_id,
                d.categorie_id,
                d.formation_id,
                d.contrat_id,
                d.declaration_id,
                d.nom_fichier,
                d.nom_affichage,
                d.chemin_fichier,
                d.type_mime,
                d.taille_octets,
                d.date_expiration,
                d.notes,
                d.uploaded_by,
                d.statut,
                d.date_upload,
                d.date_modification,

                -- Informations personnel
                p.nom AS personnel_nom,
                p.prenom AS personnel_prenom,
                p.matricule AS personnel_matricule,

                -- Informations catégorie
                c.nom AS categorie_nom,
                c.description AS categorie_description,
                c.couleur AS categorie_couleur,

                -- Informations formation (si lié)
                f.intitule AS formation_intitule,
                f.date_debut AS formation_date_debut,

                -- Informations contrat (si lié)
                ct.type_contrat AS contrat_type,
                ct.date_debut AS contrat_date_debut,
                ct.date_fin AS contrat_date_fin,

                -- Calcul de l'état d'expiration
                CASE
                    WHEN d.date_expiration IS NULL THEN 'non_applicable'
                    WHEN d.date_expiration < CURDATE() THEN 'expire'
                    WHEN d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 'expire_bientot'
                    ELSE 'valide'
                END AS etat_expiration,

                -- Jours avant expiration (négatif si expiré)
                CASE
                    WHEN d.date_expiration IS NOT NULL
                    THEN DATEDIFF(d.date_expiration, CURDATE())
                    ELSE NULL
                END AS jours_avant_expiration

            FROM documents d
            INNER JOIN personnel p ON d.personnel_id = p.id
            INNER JOIN categories_documents c ON d.categorie_id = c.id
            LEFT JOIN formation f ON d.formation_id = f.id
            LEFT JOIN contrat ct ON d.contrat_id = ct.id
        """)

        conn.commit()
        print("    ✓ Vue v_documents_complet créée avec succès")
        return True

    except Exception as e:
        conn.rollback()
        print(f"    ⚠️  Erreur: {e}")
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

def rename_operateur_to_personnel():
    """Renomme operateur_id en personnel_id."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        print("  - Renommage de operateur_id en personnel_id...")

        # Supprimer la contrainte FK existante
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

        conn.commit()
        print("    ✓ Colonne renommée avec succès")
        return True

    except Exception as e:
        conn.rollback()
        print(f"    ⚠️  Erreur: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def check_entity_columns():
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
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

def add_entity_columns():
    """Ajoute les colonnes de liaison vers entités (formation, contrat, declaration)."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        print("  - Ajout des colonnes de liaison...")

        # Vérifier et ajouter formation_id
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME = 'formation_id'
        """)
        if cur.fetchone()[0] == 0:
            print("    - Ajout de formation_id...")
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
            print("      ✓ formation_id ajoutée")
        else:
            print("    - formation_id existe déjà")

        # Vérifier et ajouter contrat_id
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME = 'contrat_id'
        """)
        if cur.fetchone()[0] == 0:
            print("    - Ajout de contrat_id...")
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
            print("      ✓ contrat_id ajoutée")
        else:
            print("    - contrat_id existe déjà")

        # Vérifier et ajouter declaration_id
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND COLUMN_NAME = 'declaration_id'
        """)
        if cur.fetchone()[0] == 0:
            print("    - Ajout de declaration_id...")
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
            print("      ✓ declaration_id ajoutée")
        else:
            print("    - declaration_id existe déjà")

        # Ajouter les index
        print("    - Création des index...")
        try:
            cur.execute("CREATE INDEX `idx_documents_formation` ON `documents`(`formation_id`)")
            print("      ✓ Index formation_id créé")
        except Exception:
            print("      - Index formation_id existe déjà")

        try:
            cur.execute("CREATE INDEX `idx_documents_contrat` ON `documents`(`contrat_id`)")
            print("      ✓ Index contrat_id créé")
        except Exception:
            print("      - Index contrat_id existe déjà")

        try:
            cur.execute("CREATE INDEX `idx_documents_declaration` ON `documents`(`declaration_id`)")
            print("      ✓ Index declaration_id créé")
        except Exception:
            print("      - Index declaration_id existe déjà")

        conn.commit()
        print("    ✓ Colonnes de liaison configurées")
        return True

    except Exception as e:
        conn.rollback()
        print(f"    ⚠️  Erreur: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def main():
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  CONFIGURATION COMPLETE DU SYSTÈME DOCUMENTAIRE           ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")

    success_count = 0
    total_steps = 0

    # Étape 1: Vérifier/renommer operateur_id
    print("1️⃣  Vérification de la colonne personnel_id...")
    column_name = check_column_name()

    if column_name == 'operateur_id':
        print("   ⚠️  La colonne s'appelle 'operateur_id' (devrait être 'personnel_id')")
        total_steps += 1
        if rename_operateur_to_personnel():
            success_count += 1
            column_name = 'personnel_id'
    elif column_name == 'personnel_id':
        print("   ✅ La colonne s'appelle déjà 'personnel_id'\n")
    else:
        print("   ❌ Colonne introuvable! Vérifiez que la table documents existe.")
        return

    # Étape 2: Ajouter les colonnes de liaison
    print("\n2️⃣  Vérification des colonnes de liaison...")
    existing = check_entity_columns()
    missing = set(['formation_id', 'contrat_id', 'declaration_id']) - set(existing)

    if missing:
        print(f"   ⚠️  Colonnes manquantes: {', '.join(missing)}")
        total_steps += 1
        if add_entity_columns():
            success_count += 1
    else:
        print("   ✅ Toutes les colonnes de liaison existent\n")

    # Étape 3: Créer la vue v_documents_complet
    print("\n3️⃣  Configuration de la vue v_documents_complet...")
    view_exists = check_view_exists('v_documents_complet')

    if view_exists:
        print("   ℹ️  La vue existe, elle sera recréée avec la nouvelle structure...")
    else:
        print("   ⚠️  La vue n'existe pas encore")

    total_steps += 1
    if create_view_documents_complet():
        success_count += 1

    # Résumé final
    print("\n" + "="*60)
    print("                      RÉSUMÉ")
    print("="*60)

    if total_steps == 0:
        print("✅ Configuration déjà complète, aucune action nécessaire!")
    elif success_count == total_steps:
        print(f"✅ Configuration réussie! ({success_count}/{total_steps} étapes)")
        print("\n📋 Prochaines étapes:")
        print("   1. Testez l'assignation en masse avec un document")
        print("   2. Vérifiez que le document apparaît dans l'interface")
        print("   3. Vérifiez la liaison avec la formation/absence/etc.")
    else:
        print(f"⚠️  Configuration partielle ({success_count}/{total_steps} étapes réussies)")
        print("\n⚠️  Vérifiez les erreurs ci-dessus et réessayez.")

    print("="*60)

if __name__ == "__main__":
    main()
