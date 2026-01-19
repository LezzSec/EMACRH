-- ============================================================
-- Migration : Liens documents vers entités RH
-- Version : 1.0
-- Date : 2026-01-19
-- Description : Ajoute les colonnes pour lier un document
--               à un contrat, une formation ou une déclaration
-- ============================================================

USE emac_db;

-- Ajouter les colonnes de liaison (si elles n'existent pas)
DELIMITER $$

CREATE PROCEDURE add_document_entity_links()
BEGIN
    -- Vérifier et ajouter la colonne 'contrat_id'
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'emac_db'
        AND TABLE_NAME = 'documents'
        AND COLUMN_NAME = 'contrat_id'
    ) THEN
        ALTER TABLE `documents`
        ADD COLUMN `contrat_id` INT NULL AFTER `categorie_id`,
        ADD CONSTRAINT `fk_documents_contrat`
            FOREIGN KEY (`contrat_id`) REFERENCES `contrat`(`id`)
            ON DELETE SET NULL;
    END IF;

    -- Vérifier et ajouter la colonne 'formation_id'
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'emac_db'
        AND TABLE_NAME = 'documents'
        AND COLUMN_NAME = 'formation_id'
    ) THEN
        ALTER TABLE `documents`
        ADD COLUMN `formation_id` INT NULL AFTER `contrat_id`,
        ADD CONSTRAINT `fk_documents_formation`
            FOREIGN KEY (`formation_id`) REFERENCES `formation`(`id`)
            ON DELETE SET NULL;
    END IF;

    -- Vérifier et ajouter la colonne 'declaration_id'
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'emac_db'
        AND TABLE_NAME = 'documents'
        AND COLUMN_NAME = 'declaration_id'
    ) THEN
        ALTER TABLE `documents`
        ADD COLUMN `declaration_id` INT NULL AFTER `formation_id`,
        ADD CONSTRAINT `fk_documents_declaration`
            FOREIGN KEY (`declaration_id`) REFERENCES `declaration`(`id`)
            ON DELETE SET NULL;
    END IF;

    -- Index pour les recherches par entité
    IF NOT EXISTS (
        SELECT * FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = 'emac_db'
        AND TABLE_NAME = 'documents'
        AND INDEX_NAME = 'idx_documents_contrat'
    ) THEN
        CREATE INDEX `idx_documents_contrat` ON `documents`(`contrat_id`);
    END IF;

    IF NOT EXISTS (
        SELECT * FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = 'emac_db'
        AND TABLE_NAME = 'documents'
        AND INDEX_NAME = 'idx_documents_formation'
    ) THEN
        CREATE INDEX `idx_documents_formation` ON `documents`(`formation_id`);
    END IF;

    IF NOT EXISTS (
        SELECT * FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = 'emac_db'
        AND TABLE_NAME = 'documents'
        AND INDEX_NAME = 'idx_documents_declaration'
    ) THEN
        CREATE INDEX `idx_documents_declaration` ON `documents`(`declaration_id`);
    END IF;
END$$

DELIMITER ;

-- Exécuter la procédure
CALL add_document_entity_links();

-- Supprimer la procédure après utilisation
DROP PROCEDURE IF EXISTS add_document_entity_links;

-- ============================================================
-- Mapping catégories → domaines RH (pour référence)
-- ============================================================
-- Ce mapping est géré en Python (rh_service.py)
-- Catégorie                    → Domaine RH
-- ----------------------------------------
-- Contrats de travail          → CONTRAT
-- Certificats médicaux         → DECLARATION
-- Diplômes et formations       → FORMATION / COMPETENCES
-- Autorisations de travail     → CONTRAT
-- Pièces d'identité            → GENERAL
-- Attestations diverses        → GENERAL
-- Documents administratifs     → GENERAL
-- Autres                       → GENERAL

SELECT 'Migration 002_add_document_entity_links terminée avec succès!' as message;
