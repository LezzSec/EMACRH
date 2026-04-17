-- =======================================================================
-- Migration : Système de Gestion Documentaire RH
-- Version : 1.0
-- Date : 2025-12-05
-- Mis à jour : 2026-04-16 — utilise personnel/personnel_id (table operateurs renommée)
-- Description : Tables pour gérer les documents RH associés aux employés
-- =======================================================================

USE emac_db;

-- Table principale des documents
CREATE TABLE IF NOT EXISTS `documents_rh` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `personnel_id` INT NOT NULL,
  `nom_fichier` VARCHAR(255) NOT NULL COMMENT 'Nom du fichier original',
  `nom_stockage` VARCHAR(255) NOT NULL COMMENT 'Nom unique du fichier sur le disque',
  `categorie` ENUM(
    'Contrat',
    'Avenant',
    'Formation',
    'Medical',
    'Administratif',
    'Attestation',
    'Autre'
  ) NOT NULL DEFAULT 'Autre',
  `type_mime` VARCHAR(100) DEFAULT NULL COMMENT 'Type MIME du fichier (application/pdf, image/png, etc.)',
  `taille_octets` BIGINT DEFAULT NULL COMMENT 'Taille du fichier en octets',
  `extension` VARCHAR(10) DEFAULT NULL COMMENT 'Extension du fichier (.pdf, .docx, etc.)',
  `chemin_relatif` VARCHAR(500) NOT NULL COMMENT 'Chemin relatif depuis le dossier uploads/',
  `date_ajout` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ajoute_par` VARCHAR(100) DEFAULT NULL COMMENT 'Utilisateur ayant ajouté le document',
  `description` TEXT DEFAULT NULL COMMENT 'Description optionnelle du document',
  `date_document` DATE DEFAULT NULL COMMENT 'Date du document (ex: date du contrat)',
  `date_expiration` DATE DEFAULT NULL COMMENT 'Date d''expiration si applicable',
  `version` INT DEFAULT 1 COMMENT 'Numéro de version du document',
  `archive` TINYINT(1) DEFAULT 0 COMMENT '1 si le document est archivé',
  `date_archivage` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_personnel` (`personnel_id`),
  KEY `idx_categorie` (`categorie`),
  KEY `idx_date_ajout` (`date_ajout`),
  KEY `idx_archive` (`archive`),
  KEY `idx_date_expiration` (`date_expiration`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Gestion des documents RH associés aux employés';

-- Ajouter la FK séparément pour gérer le cas où la table existait déjà sans FK
SET @fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = DATABASE()
      AND CONSTRAINT_NAME   = 'fk_documents_rh_personnel'
      AND CONSTRAINT_TYPE   = 'FOREIGN KEY'
);
SET @sql = IF(
    @fk_exists = 0,
    'ALTER TABLE documents_rh ADD CONSTRAINT fk_documents_rh_personnel FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE ON UPDATE CASCADE',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Table pour les métadonnées supplémentaires
CREATE TABLE IF NOT EXISTS `documents_metadata` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `document_id` INT NOT NULL,
  `cle` VARCHAR(100) NOT NULL COMMENT 'Clé de la métadonnée',
  `valeur` TEXT COMMENT 'Valeur de la métadonnée',
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  KEY `idx_cle` (`cle`),
  CONSTRAINT `fk_metadata_document`
    FOREIGN KEY (`document_id`)
    REFERENCES `documents_rh` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Métadonnées extensibles pour les documents';

-- Table d'historique des accès aux documents (audit trail)
CREATE TABLE IF NOT EXISTS `documents_acces_log` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `document_id` INT NOT NULL,
  `date_acces` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `utilisateur` VARCHAR(100) DEFAULT NULL,
  `action` ENUM('consultation', 'telechargement', 'modification', 'suppression') NOT NULL,
  `adresse_ip` VARCHAR(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  KEY `idx_date_acces` (`date_acces`),
  CONSTRAINT `fk_log_document`
    FOREIGN KEY (`document_id`)
    REFERENCES `documents_rh` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Journal des accès aux documents (audit)';

-- Vue pour les statistiques par catégorie
CREATE OR REPLACE VIEW `v_documents_stats` AS
SELECT
    d.categorie,
    COUNT(*) AS nombre_documents,
    SUM(d.taille_octets) AS taille_totale_octets,
    ROUND(SUM(d.taille_octets) / 1024 / 1024, 2) AS taille_totale_mb,
    COUNT(DISTINCT d.personnel_id) AS nombre_employes
FROM documents_rh d
WHERE d.archive = 0
GROUP BY d.categorie;

-- Vue pour les documents par employé avec infos complètes
CREATE OR REPLACE VIEW `v_documents_employes` AS
SELECT
    d.id,
    d.personnel_id,
    CONCAT(p.prenom, ' ', p.nom) AS nom_complet,
    p.statut AS statut_employe,
    d.nom_fichier,
    d.categorie,
    d.extension,
    d.taille_octets,
    ROUND(d.taille_octets / 1024, 2) AS taille_kb,
    d.date_ajout,
    d.date_document,
    d.date_expiration,
    CASE
        WHEN d.date_expiration IS NOT NULL AND d.date_expiration < CURDATE()
        THEN 'EXPIRE'
        WHEN d.date_expiration IS NOT NULL AND d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        THEN 'EXPIRE_BIENTOT'
        ELSE 'VALIDE'
    END AS statut_expiration,
    d.description,
    d.version,
    d.archive
FROM documents_rh d
INNER JOIN personnel p ON d.personnel_id = p.id;

-- Vue pour les documents expirant bientôt (alertes)
CREATE OR REPLACE VIEW `v_documents_expiration_alerte` AS
SELECT
    d.id,
    d.personnel_id,
    CONCAT(p.prenom, ' ', p.nom) AS nom_complet,
    d.nom_fichier,
    d.categorie,
    d.date_expiration,
    DATEDIFF(d.date_expiration, CURDATE()) AS jours_restants
FROM documents_rh d
INNER JOIN personnel p ON d.personnel_id = p.id
WHERE
    d.archive = 0
    AND d.date_expiration IS NOT NULL
    AND d.date_expiration > CURDATE()
    AND d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 60 DAY)
ORDER BY d.date_expiration ASC;

-- =======================================================================
-- FIN DE LA MIGRATION
-- =======================================================================
