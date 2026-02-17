-- =======================================================================
-- Migration 018 : Stockage des documents en BLOB dans la base de donnees
-- Version : 1.0
-- Date : 2026-02-16
-- Description : Ajoute une colonne LONGBLOB pour stocker le contenu des
--               fichiers directement en base, elimine la dependance au filesystem.
--               Limite recommandee : fichiers < 16 Mo
-- =======================================================================

USE emac_db;

-- -----------------------------------------------------------------------
-- 1. Ajouter la colonne contenu_fichier (LONGBLOB) a la table documents
-- -----------------------------------------------------------------------
-- LONGBLOB supporte jusqu'a 4 Go, mais on recommande < 16 Mo par fichier
-- pour les performances MySQL.

ALTER TABLE `documents`
    ADD COLUMN `contenu_fichier` LONGBLOB NULL
        COMMENT 'Contenu binaire du fichier (BLOB). NULL si stocke sur filesystem (legacy).'
        AFTER `chemin_fichier`,
    ADD COLUMN `stockage_type` ENUM('BLOB', 'FILESYSTEM') NOT NULL DEFAULT 'BLOB'
        COMMENT 'Type de stockage: BLOB (en base) ou FILESYSTEM (legacy, chemin_fichier)'
        AFTER `contenu_fichier`;

-- -----------------------------------------------------------------------
-- 2. Marquer les documents existants comme FILESYSTEM (legacy)
-- -----------------------------------------------------------------------
UPDATE `documents`
SET `stockage_type` = 'FILESYSTEM'
WHERE `contenu_fichier` IS NULL;

-- -----------------------------------------------------------------------
-- 3. Index sur stockage_type pour filtrage rapide
-- -----------------------------------------------------------------------
CREATE INDEX `idx_documents_stockage_type` ON `documents` (`stockage_type`);

-- -----------------------------------------------------------------------
-- 4. Mettre a jour la variable max_allowed_packet si necessaire
-- -----------------------------------------------------------------------
-- IMPORTANT: Executer cette commande en tant que root si les fichiers > 4 Mo:
-- SET GLOBAL max_allowed_packet = 67108864;  -- 64 Mo
-- Ou ajouter dans my.ini / my.cnf:
-- [mysqld]
-- max_allowed_packet=64M

-- =======================================================================
-- FIN DE LA MIGRATION
-- =======================================================================
