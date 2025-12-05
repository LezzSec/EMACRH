-- =======================================================================
-- Migration : Système de Gestion Documentaire RH
-- Version : 1.0
-- Date : 2025-12-05
-- Description : Tables pour gérer les documents RH associés aux employés
-- =======================================================================

USE emac_db;

-- Table principale des documents
DROP TABLE IF EXISTS `documents_rh`;
CREATE TABLE `documents_rh` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `operateur_id` INT NOT NULL,
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
  `date_expiration` DATE DEFAULT NULL COMMENT 'Date d\'expiration si applicable',
  `version` INT DEFAULT 1 COMMENT 'Numéro de version du document',
  `archive` TINYINT(1) DEFAULT 0 COMMENT '1 si le document est archivé',
  `date_archivage` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_categorie` (`categorie`),
  KEY `idx_date_ajout` (`date_ajout`),
  KEY `idx_archive` (`archive`),
  KEY `idx_date_expiration` (`date_expiration`),
  CONSTRAINT `fk_documents_operateur`
    FOREIGN KEY (`operateur_id`)
    REFERENCES `operateurs` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
COMMENT='Gestion des documents RH associés aux employés';

-- Table pour les métadonnées supplémentaires (optionnel, pour extension future)
DROP TABLE IF EXISTS `documents_metadata`;
CREATE TABLE `documents_metadata` (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
COMMENT='Métadonnées extensibles pour les documents';

-- Table d'historique des accès aux documents (audit trail)
DROP TABLE IF EXISTS `documents_acces_log`;
CREATE TABLE `documents_acces_log` (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
COMMENT='Journal des accès aux documents (audit)';

-- Vue pour les statistiques par catégorie
CREATE OR REPLACE VIEW `v_documents_stats` AS
SELECT
    d.categorie,
    COUNT(*) AS nombre_documents,
    SUM(d.taille_octets) AS taille_totale_octets,
    ROUND(SUM(d.taille_octets) / 1024 / 1024, 2) AS taille_totale_mb,
    COUNT(DISTINCT d.operateur_id) AS nombre_employes
FROM documents_rh d
WHERE d.archive = 0
GROUP BY d.categorie;

-- Vue pour les documents par employé avec infos complètes
CREATE OR REPLACE VIEW `v_documents_employes` AS
SELECT
    d.id,
    d.operateur_id,
    CONCAT(o.nom, ' ', o.prenom) AS nom_complet,
    o.statut AS statut_employe,
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
INNER JOIN operateurs o ON d.operateur_id = o.id;

-- Vue pour les documents expirant bientôt (alertes)
CREATE OR REPLACE VIEW `v_documents_expiration_alerte` AS
SELECT
    d.id,
    d.operateur_id,
    CONCAT(o.nom, ' ', o.prenom) AS nom_complet,
    d.nom_fichier,
    d.categorie,
    d.date_expiration,
    DATEDIFF(d.date_expiration, CURDATE()) AS jours_restants
FROM documents_rh d
INNER JOIN operateurs o ON d.operateur_id = o.id
WHERE
    d.archive = 0
    AND d.date_expiration IS NOT NULL
    AND d.date_expiration > CURDATE()
    AND d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 60 DAY)
ORDER BY d.date_expiration ASC;

-- Insertion de données de test (optionnel, à commenter en production)
/*
-- Exemple d'insertion (nécessite des operateurs existants)
INSERT INTO documents_rh (
    operateur_id,
    nom_fichier,
    nom_stockage,
    categorie,
    type_mime,
    taille_octets,
    extension,
    chemin_relatif,
    description,
    date_document
) VALUES
(2, 'Contrat_AGUERRE_Stephane_2024.pdf', 'doc_20251205_120145_abc123.pdf', 'Contrat', 'application/pdf', 245678, '.pdf', 'uploads/2/contrats/doc_20251205_120145_abc123.pdf', 'Contrat CDI signé le 15/01/2024', '2024-01-15'),
(2, 'Formation_Securite_2024.pdf', 'doc_20251205_130234_def456.pdf', 'Formation', 'application/pdf', 189432, '.pdf', 'uploads/2/formations/doc_20251205_130234_def456.pdf', 'Formation sécurité incendie', '2024-03-10');
*/

-- =======================================================================
-- FIN DE LA MIGRATION
-- =======================================================================
