# -*- coding: utf-8 -*-
"""
Script d'installation du module de Gestion Documentaire RH
Crée les tables nécessaires et initialise les données de base
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier parent au PATH pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.configbd import get_connection


def install_gestion_documentaire():
    """
    Installe le module de gestion documentaire RH
    - Crée les tables nécessaires
    - Initialise les catégories par défaut
    - Crée les vues SQL
    """

    print("="*70)
    print("  Installation du Module de Gestion Documentaire RH")
    print("="*70)
    print()

    conn = None
    cur = None

    try:
        # Connexion à la base de données
        print("📦 Connexion à la base de données...")
        conn = get_connection()
        cur = conn.cursor()
        print("✓ Connexion réussie\n")

        # 1. Créer la table categories_documents
        print("📋 Création de la table 'categories_documents'...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories_documents (
                id INT NOT NULL AUTO_INCREMENT,
                nom VARCHAR(100) NOT NULL,
                description TEXT,
                couleur VARCHAR(7) DEFAULT '#3b82f6',
                exige_date_expiration BOOLEAN DEFAULT FALSE,
                ordre_affichage INT DEFAULT 0,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE KEY uk_categorie_nom (nom)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("✓ Table 'categories_documents' créée\n")

        # 2. Créer la table documents
        print("📋 Création de la table 'documents'...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INT NOT NULL AUTO_INCREMENT,
                operateur_id INT NOT NULL,
                categorie_id INT NOT NULL,
                nom_fichier VARCHAR(255) NOT NULL,
                nom_affichage VARCHAR(255) NOT NULL,
                chemin_fichier VARCHAR(500) NOT NULL,
                type_mime VARCHAR(100),
                taille_octets BIGINT DEFAULT 0,
                date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_expiration DATE NULL,
                statut ENUM('actif', 'expire', 'archive') DEFAULT 'actif',
                notes TEXT,
                uploaded_by VARCHAR(100),
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                KEY idx_operateur (operateur_id),
                KEY idx_categorie (categorie_id),
                KEY idx_statut (statut),
                KEY idx_expiration (date_expiration),
                CONSTRAINT fk_documents_personnel
                    FOREIGN KEY (operateur_id)
                    REFERENCES personnel(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_documents_categorie
                    FOREIGN KEY (categorie_id)
                    REFERENCES categories_documents(id)
                    ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        print("✓ Table 'documents' créée\n")

        # 3. Créer les triggers pour la gestion automatique du statut
        print("⚙️  Création des triggers de gestion du statut...")

        # Supprimer les triggers s'ils existent déjà
        cur.execute("DROP TRIGGER IF EXISTS tg_documents_check_expiration_bi")
        cur.execute("DROP TRIGGER IF EXISTS tg_documents_check_expiration_bu")

        # Trigger BEFORE INSERT
        cur.execute("""
            CREATE TRIGGER tg_documents_check_expiration_bi
            BEFORE INSERT ON documents
            FOR EACH ROW
            BEGIN
                IF NEW.date_expiration IS NOT NULL AND NEW.date_expiration < CURDATE() THEN
                    SET NEW.statut = 'expire';
                END IF;
            END
        """)

        # Trigger BEFORE UPDATE
        cur.execute("""
            CREATE TRIGGER tg_documents_check_expiration_bu
            BEFORE UPDATE ON documents
            FOR EACH ROW
            BEGIN
                IF NEW.date_expiration IS NOT NULL AND NEW.date_expiration < CURDATE() THEN
                    SET NEW.statut = 'expire';
                ELSEIF NEW.date_expiration IS NULL OR NEW.date_expiration >= CURDATE() THEN
                    IF OLD.statut = 'expire' THEN
                        SET NEW.statut = 'actif';
                    END IF;
                END IF;
            END
        """)
        print("✓ Triggers créés\n")

        # 4. Insérer les catégories par défaut
        print("📂 Insertion des catégories par défaut...")
        categories = [
            ('Contrats de travail', 'Contrats CDI, CDD, avenants', '#10b981', True, 1),
            ('Certificats médicaux', 'Visites médicales, aptitudes, RQTH', '#ef4444', True, 2),
            ('Diplômes et formations', 'Diplômes, certificats de formation, habilitations', '#8b5cf6', False, 3),
            ('Autorisations de travail', 'Titres de séjour, autorisations de travail pour étrangers', '#f59e0b', True, 4),
            ('Pièces d\'identité', 'CNI, passeport, permis de conduire', '#06b6d4', True, 5),
            ('Attestations diverses', 'Attestations employeur, certificats de travail', '#6366f1', False, 6),
            ('Documents administratifs', 'Fiches de paie, relevés, justificatifs', '#64748b', False, 7),
            ('Autres', 'Documents non classés', '#9ca3af', False, 99)
        ]

        cur.executemany("""
            INSERT INTO categories_documents
            (nom, description, couleur, exige_date_expiration, ordre_affichage)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                description = VALUES(description),
                couleur = VALUES(couleur),
                exige_date_expiration = VALUES(exige_date_expiration),
                ordre_affichage = VALUES(ordre_affichage)
        """, categories)
        print(f"✓ {len(categories)} catégories insérées/mises à jour\n")

        # 5. Créer les vues
        print("👁️  Création des vues SQL...")

        # Vue: Documents avec informations enrichies
        cur.execute("DROP VIEW IF EXISTS v_documents_complet")
        cur.execute("""
            CREATE VIEW v_documents_complet AS
            SELECT
                d.id,
                d.operateur_id,
                CONCAT(o.nom, ' ', o.prenom) AS operateur_nom,
                d.categorie_id,
                c.nom AS categorie_nom,
                c.couleur AS categorie_couleur,
                c.exige_date_expiration,
                d.nom_fichier,
                d.nom_affichage,
                d.chemin_fichier,
                d.type_mime,
                d.taille_octets,
                ROUND(d.taille_octets / 1024, 2) AS taille_ko,
                ROUND(d.taille_octets / 1048576, 2) AS taille_mo,
                d.date_upload,
                d.date_expiration,
                CASE
                    WHEN d.date_expiration IS NULL THEN NULL
                    WHEN d.date_expiration < CURDATE() THEN 'Expiré'
                    WHEN d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 'Expire bientôt'
                    ELSE 'Valide'
                END AS alerte_expiration,
                DATEDIFF(d.date_expiration, CURDATE()) AS jours_avant_expiration,
                d.statut,
                d.notes,
                d.uploaded_by,
                d.date_creation,
                d.date_modification
            FROM documents d
            INNER JOIN personnel o ON d.operateur_id = o.id
            INNER JOIN categories_documents c ON d.categorie_id = c.id
        """)
        print("✓ Vue 'v_documents_complet' créée")

        # Vue: Statistiques par opérateur
        cur.execute("DROP VIEW IF EXISTS v_documents_stats_operateur")
        cur.execute("""
            CREATE VIEW v_documents_stats_operateur AS
            SELECT
                o.id AS operateur_id,
                CONCAT(o.nom, ' ', o.prenom) AS operateur_nom,
                COUNT(d.id) AS total_documents,
                SUM(CASE WHEN d.statut = 'actif' THEN 1 ELSE 0 END) AS documents_actifs,
                SUM(CASE WHEN d.statut = 'expire' THEN 1 ELSE 0 END) AS documents_expires,
                SUM(CASE WHEN d.date_expiration IS NOT NULL
                         AND d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                         AND d.date_expiration >= CURDATE() THEN 1 ELSE 0 END) AS documents_expire_bientot,
                SUM(d.taille_octets) AS taille_totale_octets,
                ROUND(SUM(d.taille_octets) / 1048576, 2) AS taille_totale_mo,
                MAX(d.date_upload) AS derniere_mise_a_jour
            FROM personnel o
            LEFT JOIN documents d ON o.id = d.operateur_id
            GROUP BY o.id, o.nom, o.prenom
        """)
        print("✓ Vue 'v_documents_stats_operateur' créée")

        # Vue: Documents expirant bientôt
        cur.execute("DROP VIEW IF EXISTS v_documents_expiration_proche")
        cur.execute("""
            CREATE VIEW v_documents_expiration_proche AS
            SELECT
                d.id,
                d.operateur_id,
                CONCAT(o.nom, ' ', o.prenom) AS operateur_nom,
                d.categorie_id,
                c.nom AS categorie_nom,
                d.nom_affichage,
                d.date_expiration,
                DATEDIFF(d.date_expiration, CURDATE()) AS jours_restants,
                d.statut
            FROM documents d
            INNER JOIN personnel o ON d.operateur_id = o.id
            INNER JOIN categories_documents c ON d.categorie_id = c.id
            WHERE
                d.date_expiration IS NOT NULL
                AND d.date_expiration >= CURDATE()
                AND d.statut != 'archive'
            ORDER BY d.date_expiration ASC
        """)
        print("✓ Vue 'v_documents_expiration_proche' créée\n")

        # 6. Créer le dossier de stockage
        print("📁 Création du dossier de stockage des documents...")
        upload_dir = Path("documents")
        upload_dir.mkdir(exist_ok=True)
        print(f"✓ Dossier créé: {upload_dir.absolute()}\n")

        # Commit des changements
        conn.commit()

        print("="*70)
        print("✅ Installation terminée avec succès!")
        print("="*70)
        print()
        print("📚 Résumé de l'installation:")
        print("  • Tables créées: categories_documents, documents")
        print("  • Triggers créés: tg_documents_check_expiration_bi, tg_documents_check_expiration_bu")
        print("  • Vues créées: v_documents_complet, v_documents_stats_operateur, v_documents_expiration_proche")
        print("  • Catégories: 8 catégories par défaut")
        print(f"  • Dossier de stockage: {upload_dir.absolute()}")
        print()
        print("🎉 Le module de Gestion Documentaire RH est prêt à l'emploi!")
        print()
        print("💡 Pour accéder au module:")
        print("   Menu > Gestion Documentaire RH")
        print()

    except Exception as e:
        print(f"\n❌ ERREUR lors de l'installation: {e}")
        if conn:
            conn.rollback()
        raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    try:
        install_gestion_documentaire()
        print("Appuyez sur Entrée pour quitter...")
        input()
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation annulée par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        print("\nAppuyez sur Entrée pour quitter...")
        input()
