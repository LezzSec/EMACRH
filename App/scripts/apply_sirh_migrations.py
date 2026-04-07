# -*- coding: utf-8 -*-
"""
Script pour appliquer les migrations SIRH (006, 007, 008)
Ajoute les tables et colonnes manquantes selon le fichier Tableau SIRH.xlsx

Usage:
    python App/scripts/apply_sirh_migrations.py
"""

import sys
import os
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.configbd import get_connection


def check_column_exists(cursor, table, column):
    """Vérifie si une colonne existe dans une table."""
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        AND COLUMN_NAME = %s
    """, (table, column))
    return cursor.fetchone()[0] > 0


def check_table_exists(cursor, table):
    """Vérifie si une table existe."""
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
    """, (table,))
    return cursor.fetchone()[0] > 0


def apply_migration_006(cursor):
    """Migration 006: Compléter la table contrat."""
    print("\n📋 Migration 006: Table contrat...")

    columns_to_add = [
        ("motif", "TEXT DEFAULT NULL COMMENT 'Motif du contrat ou du CDD'", "type_cdd"),
        ("date_sortie", "DATE DEFAULT NULL COMMENT 'Date de sortie effective'", "date_fin"),
        ("date_embauche_cdi", "DATE DEFAULT NULL COMMENT 'Date embauche CDI (passage CDD -> CDI)'", "date_sortie"),
        ("motif_sortie", "VARCHAR(100) DEFAULT NULL COMMENT 'Motif de sortie'", "date_embauche_cdi"),
        ("typologie_statut_horaire", "ENUM('Cadre forfait jour','Cadre décompte horaire','Non-cadre','Temps partiel') DEFAULT NULL", "categorie"),
        ("niveau", "VARCHAR(20) DEFAULT NULL COMMENT 'Niveau dans la grille'", "echelon"),
        ("coefficient", "INT DEFAULT NULL COMMENT 'Coefficient salarial'", "niveau"),
        ("salaire_annuel", "DECIMAL(12,2) DEFAULT NULL COMMENT 'Salaire brut annuel'", "salaire"),
        ("type_prime", "VARCHAR(100) DEFAULT NULL COMMENT 'Type de prime'", "salaire_annuel"),
        ("prime_mensuelle", "DECIMAL(10,2) DEFAULT NULL COMMENT 'Montant prime mensuel brut'", "type_prime"),
        ("prime_annuelle", "DECIMAL(12,2) DEFAULT NULL COMMENT 'Total prime annuel brut'", "prime_mensuelle"),
    ]

    added = 0
    for col_name, col_def, after_col in columns_to_add:
        if not check_column_exists(cursor, 'contrat', col_name):
            try:
                sql = f"ALTER TABLE `contrat` ADD COLUMN `{col_name}` {col_def}"
                if after_col and check_column_exists(cursor, 'contrat', after_col):
                    sql += f" AFTER `{after_col}`"
                cursor.execute(sql)
                print(f"   ✅ Colonne '{col_name}' ajoutée")
                added += 1
            except Exception as e:
                print(f"   ⚠️ Erreur pour '{col_name}': {e}")
        else:
            print(f"   ⏭️ Colonne '{col_name}' existe déjà")

    # Table de référence motifs de sortie
    if not check_table_exists(cursor, 'ref_motif_sortie'):
        cursor.execute("""
            CREATE TABLE `ref_motif_sortie` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `libelle` VARCHAR(100) NOT NULL,
                `actif` TINYINT(1) DEFAULT 1,
                PRIMARY KEY (`id`),
                UNIQUE KEY `uk_libelle` (`libelle`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        cursor.execute("""
            INSERT IGNORE INTO `ref_motif_sortie` (`libelle`) VALUES
            ('Démission'), ('Licenciement économique'), ('Licenciement pour faute'),
            ('Licenciement pour inaptitude'), ('Fin de CDD'), ('Fin de période d''essai'),
            ('Rupture conventionnelle'), ('Retraite'), ('Décès'), ('Mutation'),
            ('Fin de mission intérim'), ('Fin de stage'), ('Fin d''apprentissage')
        """)
        print("   ✅ Table 'ref_motif_sortie' créée")

    print(f"   📊 {added} colonnes ajoutées à 'contrat'")
    return added


def apply_migration_007(cursor):
    """Migration 007: Tables médicales."""
    print("\n🏥 Migration 007: Tables médicales...")

    tables_created = 0

    # Table medical
    if not check_table_exists(cursor, 'medical'):
        cursor.execute("""
            CREATE TABLE `medical` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `operateur_id` INT NOT NULL,
                `type_suivi_vip` ENUM('SIA', 'SIR', 'SI') DEFAULT NULL,
                `periodicite_vip_mois` INT DEFAULT 24,
                `date_electrocardiogramme` DATE DEFAULT NULL,
                `maladie_pro` TINYINT(1) DEFAULT 0,
                `taux_professionnel` DECIMAL(5,2) DEFAULT NULL,
                `besoins_adaptation` TEXT DEFAULT NULL,
                `demande_reconnaissance_atmp_en_cours` TINYINT(1) DEFAULT 0,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                UNIQUE KEY `uk_medical_operateur` (`operateur_id`),
                CONSTRAINT `fk_medical_operateur` FOREIGN KEY (`operateur_id`)
                    REFERENCES `personnel` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("   ✅ Table 'medical' créée")
        tables_created += 1
    else:
        print("   ⏭️ Table 'medical' existe déjà")

    # Table medical_visite
    if not check_table_exists(cursor, 'medical_visite'):
        cursor.execute("""
            CREATE TABLE `medical_visite` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `operateur_id` INT NOT NULL,
                `date_visite` DATE NOT NULL,
                `type_visite` ENUM('Embauche', 'Périodique', 'Reprise', 'À la demande', 'Pré-reprise') DEFAULT 'Périodique',
                `resultat` ENUM('Apte', 'Apte avec restrictions', 'Inapte temporaire', 'Inapte définitif') DEFAULT NULL,
                `restrictions` TEXT DEFAULT NULL,
                `medecin` VARCHAR(255) DEFAULT NULL,
                `commentaire` TEXT DEFAULT NULL,
                `prochaine_visite` DATE DEFAULT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                KEY `idx_visite_operateur` (`operateur_id`),
                KEY `idx_visite_date` (`date_visite`),
                KEY `idx_visite_prochaine` (`prochaine_visite`),
                CONSTRAINT `fk_visite_operateur` FOREIGN KEY (`operateur_id`)
                    REFERENCES `personnel` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("   ✅ Table 'medical_visite' créée")
        tables_created += 1
    else:
        print("   ⏭️ Table 'medical_visite' existe déjà")

    # Table medical_maladie_pro
    if not check_table_exists(cursor, 'medical_maladie_pro'):
        cursor.execute("""
            CREATE TABLE `medical_maladie_pro` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `operateur_id` INT NOT NULL,
                `date_reconnaissance` DATE NOT NULL,
                `numero_tableau` VARCHAR(20) DEFAULT NULL,
                `designation` VARCHAR(255) DEFAULT NULL,
                `taux_ipp` DECIMAL(5,2) DEFAULT NULL,
                `commentaire` TEXT DEFAULT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                KEY `idx_mp_operateur` (`operateur_id`),
                KEY `idx_mp_date` (`date_reconnaissance`),
                CONSTRAINT `fk_mp_operateur` FOREIGN KEY (`operateur_id`)
                    REFERENCES `personnel` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("   ✅ Table 'medical_maladie_pro' créée")
        tables_created += 1
    else:
        print("   ⏭️ Table 'medical_maladie_pro' existe déjà")

    # Table medical_accident_travail
    if not check_table_exists(cursor, 'medical_accident_travail'):
        cursor.execute("""
            CREATE TABLE `medical_accident_travail` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `operateur_id` INT NOT NULL,
                `date_accident` DATE NOT NULL,
                `heure_accident` TIME DEFAULT NULL,
                `jour_semaine` ENUM('Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche') DEFAULT NULL,
                `horaires` VARCHAR(50) DEFAULT NULL,
                `circonstances` TEXT DEFAULT NULL,
                `siege_lesions` VARCHAR(255) DEFAULT NULL,
                `nature_lesions` VARCHAR(255) DEFAULT NULL,
                `avec_arret` TINYINT(1) DEFAULT 0,
                `date_reconnaissance_at` DATE DEFAULT NULL,
                `date_debut_arret` DATE DEFAULT NULL,
                `date_fin_arret_initial` DATE DEFAULT NULL,
                `date_fin_prolongation` DATE DEFAULT NULL,
                `nb_jours_absence` INT DEFAULT NULL,
                `commentaire` TEXT DEFAULT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                KEY `idx_at_operateur` (`operateur_id`),
                KEY `idx_at_date` (`date_accident`),
                KEY `idx_at_avec_arret` (`avec_arret`),
                CONSTRAINT `fk_at_operateur` FOREIGN KEY (`operateur_id`)
                    REFERENCES `personnel` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("   ✅ Table 'medical_accident_travail' créée")
        tables_created += 1
    else:
        print("   ⏭️ Table 'medical_accident_travail' existe déjà")

    # Table medical_prolongation_arret
    if not check_table_exists(cursor, 'medical_prolongation_arret'):
        cursor.execute("""
            CREATE TABLE `medical_prolongation_arret` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `accident_id` INT NOT NULL,
                `date_debut` DATE NOT NULL,
                `date_fin` DATE NOT NULL,
                `numero_prolongation` INT DEFAULT 1,
                `commentaire` TEXT DEFAULT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                KEY `idx_prolongation_accident` (`accident_id`),
                CONSTRAINT `fk_prolongation_accident` FOREIGN KEY (`accident_id`)
                    REFERENCES `medical_accident_travail` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("   ✅ Table 'medical_prolongation_arret' créée")
        tables_created += 1
    else:
        print("   ⏭️ Table 'medical_prolongation_arret' existe déjà")

    print(f"   📊 {tables_created} tables médicales créées")
    return tables_created


def apply_migration_008(cursor):
    """Migration 008: Tables Vie du salarié."""
    print("\n👤 Migration 008: Tables Vie du salarié...")

    tables_created = 0

    # Table vie_salarie_sanction
    if not check_table_exists(cursor, 'vie_salarie_sanction'):
        cursor.execute("""
            CREATE TABLE `vie_salarie_sanction` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `operateur_id` INT NOT NULL,
                `type_sanction` ENUM(
                    'Observation verbale',
                    'Observation écrite',
                    'Avertissement',
                    'Mise à pied disciplinaire',
                    'Mise à pied conservatoire'
                ) NOT NULL,
                `date_sanction` DATE NOT NULL,
                `duree_jours` INT DEFAULT NULL,
                `motif` TEXT DEFAULT NULL,
                `document_reference` VARCHAR(255) DEFAULT NULL,
                `commentaire` TEXT DEFAULT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                KEY `idx_sanction_operateur` (`operateur_id`),
                KEY `idx_sanction_date` (`date_sanction`),
                KEY `idx_sanction_type` (`type_sanction`),
                CONSTRAINT `fk_sanction_operateur` FOREIGN KEY (`operateur_id`)
                    REFERENCES `personnel` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("   ✅ Table 'vie_salarie_sanction' créée")
        tables_created += 1
    else:
        print("   ⏭️ Table 'vie_salarie_sanction' existe déjà")

    # Table vie_salarie_alcoolemie
    if not check_table_exists(cursor, 'vie_salarie_alcoolemie'):
        cursor.execute("""
            CREATE TABLE `vie_salarie_alcoolemie` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `operateur_id` INT NOT NULL,
                `date_controle` DATETIME NOT NULL,
                `resultat` ENUM('Négatif', 'Positif') NOT NULL,
                `taux` DECIMAL(4,2) DEFAULT NULL,
                `type_controle` ENUM('Aléatoire', 'Ciblé', 'Accident') DEFAULT 'Aléatoire',
                `commentaire` TEXT DEFAULT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                KEY `idx_alcool_operateur` (`operateur_id`),
                KEY `idx_alcool_date` (`date_controle`),
                KEY `idx_alcool_resultat` (`resultat`),
                CONSTRAINT `fk_alcool_operateur` FOREIGN KEY (`operateur_id`)
                    REFERENCES `personnel` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("   ✅ Table 'vie_salarie_alcoolemie' créée")
        tables_created += 1
    else:
        print("   ⏭️ Table 'vie_salarie_alcoolemie' existe déjà")

    # Table vie_salarie_test_salivaire
    if not check_table_exists(cursor, 'vie_salarie_test_salivaire'):
        cursor.execute("""
            CREATE TABLE `vie_salarie_test_salivaire` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `operateur_id` INT NOT NULL,
                `date_test` DATETIME NOT NULL,
                `resultat` ENUM('Négatif', 'Positif', 'Non concluant') NOT NULL,
                `type_controle` ENUM('Aléatoire', 'Ciblé', 'Accident') DEFAULT 'Aléatoire',
                `commentaire` TEXT DEFAULT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                KEY `idx_salivaire_operateur` (`operateur_id`),
                KEY `idx_salivaire_date` (`date_test`),
                KEY `idx_salivaire_resultat` (`resultat`),
                CONSTRAINT `fk_salivaire_operateur` FOREIGN KEY (`operateur_id`)
                    REFERENCES `personnel` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("   ✅ Table 'vie_salarie_test_salivaire' créée")
        tables_created += 1
    else:
        print("   ⏭️ Table 'vie_salarie_test_salivaire' existe déjà")

    # Table vie_salarie_entretien
    if not check_table_exists(cursor, 'vie_salarie_entretien'):
        cursor.execute("""
            CREATE TABLE `vie_salarie_entretien` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `operateur_id` INT NOT NULL,
                `type_entretien` ENUM('EPP', 'EAP', 'Bilan 6 ans', 'Entretien annuel', 'Autre') NOT NULL,
                `date_entretien` DATE NOT NULL,
                `manager_id` INT DEFAULT NULL,
                `objectifs_atteints` TEXT DEFAULT NULL,
                `objectifs_fixes` TEXT DEFAULT NULL,
                `besoins_formation` TEXT DEFAULT NULL,
                `souhaits_evolution` TEXT DEFAULT NULL,
                `commentaire_salarie` TEXT DEFAULT NULL,
                `commentaire_manager` TEXT DEFAULT NULL,
                `document_reference` VARCHAR(255) DEFAULT NULL,
                `prochaine_date` DATE DEFAULT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                KEY `idx_entretien_operateur` (`operateur_id`),
                KEY `idx_entretien_date` (`date_entretien`),
                KEY `idx_entretien_type` (`type_entretien`),
                KEY `idx_entretien_manager` (`manager_id`),
                CONSTRAINT `fk_entretien_operateur` FOREIGN KEY (`operateur_id`)
                    REFERENCES `personnel` (`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_entretien_manager` FOREIGN KEY (`manager_id`)
                    REFERENCES `personnel` (`id`) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("   ✅ Table 'vie_salarie_entretien' créée")
        tables_created += 1
    else:
        print("   ⏭️ Table 'vie_salarie_entretien' existe déjà")

    print(f"   📊 {tables_created} tables vie_salarie créées")
    return tables_created


def main():
    print("=" * 60)
    print("🚀 Application des migrations SIRH (006, 007, 008)")
    print("=" * 60)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Appliquer les migrations
        cols_006 = apply_migration_006(cursor)
        tables_007 = apply_migration_007(cursor)
        tables_008 = apply_migration_008(cursor)

        # Commit des changements
        conn.commit()

        print("\n" + "=" * 60)
        print("✅ MIGRATIONS APPLIQUÉES AVEC SUCCÈS")
        print("=" * 60)
        print(f"   - Colonnes ajoutées (contrat): {cols_006}")
        print(f"   - Tables médicales créées: {tables_007}")
        print(f"   - Tables vie_salarie créées: {tables_008}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
