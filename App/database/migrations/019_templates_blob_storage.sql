-- =======================================================================
-- Migration 019 : Stockage des templates en BLOB dans la base de donnees
-- Version : 1.0
-- Date : 2026-02-16
-- Description : Ajoute une colonne LONGBLOB a documents_templates pour
--               stocker le contenu des fichiers templates (Excel, Word)
--               directement en base. Elimine la dependance au dossier templates/.
-- =======================================================================

USE emac_db;

-- -----------------------------------------------------------------------
-- 1. Ajouter les colonnes pour le stockage BLOB
-- -----------------------------------------------------------------------

ALTER TABLE `documents_templates`
    ADD COLUMN `contenu_fichier` LONGBLOB NULL
        COMMENT 'Contenu binaire du fichier template. NULL si legacy (filesystem).'
        AFTER `fichier_source`,
    ADD COLUMN `type_mime` VARCHAR(100) NULL
        COMMENT 'Type MIME du fichier (application/vnd.ms-excel, etc.)'
        AFTER `contenu_fichier`,
    ADD COLUMN `taille_octets` BIGINT NULL
        COMMENT 'Taille du fichier en octets'
        AFTER `type_mime`,
    ADD COLUMN `stockage_type` ENUM('BLOB', 'FILESYSTEM') NOT NULL DEFAULT 'FILESYSTEM'
        COMMENT 'Type de stockage: BLOB (en base) ou FILESYSTEM (legacy)'
        AFTER `taille_octets`;

-- -----------------------------------------------------------------------
-- 2. Les templates existants restent en FILESYSTEM
-- -----------------------------------------------------------------------
UPDATE `documents_templates`
SET `stockage_type` = 'FILESYSTEM'
WHERE `contenu_fichier` IS NULL;

-- -----------------------------------------------------------------------
-- 3. Index
-- -----------------------------------------------------------------------
CREATE INDEX `idx_templates_stockage_type` ON `documents_templates` (`stockage_type`);

-- =======================================================================
-- FIN DE LA MIGRATION
-- =======================================================================
