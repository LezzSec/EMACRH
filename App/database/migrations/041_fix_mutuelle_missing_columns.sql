-- Migration 041: Ajout des colonnes manquantes dans la table mutuelle
-- Cause : La migration 032 utilisait CREATE TABLE IF NOT EXISTS, donc ignoree
-- car la table existait deja avec un schema anterieur.

ALTER TABLE `mutuelle`
    ADD COLUMN IF NOT EXISTS `due_signee` BOOLEAN NOT NULL DEFAULT FALSE
        AFTER `statut_adhesion`,
    ADD COLUMN IF NOT EXISTS `type_formule` ENUM('SIMPLE', 'TURBO') NULL
        AFTER `due_signee`,
    ADD COLUMN IF NOT EXISTS `situation_familiale` ENUM('ISOLE', 'DUO', 'FAMILLE') NULL
        AFTER `type_formule`,
    ADD COLUMN IF NOT EXISTS `justificatif_validite` DATE NULL
        COMMENT 'Date de validite du justificatif de dispense (renouvellement annuel)'
        AFTER `type_dispense`;
