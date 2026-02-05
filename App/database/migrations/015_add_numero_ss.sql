-- Migration: Ajout du numéro de sécurité sociale à personnel_infos
-- Date: 2026-02-05

-- ============================================================
-- Ajout de la colonne numero_ss
-- ============================================================
-- NOTE: Le numéro de sécurité sociale est une donnée sensible.
-- Pour une sécurité maximale, considérer le chiffrement côté application
-- ou l'utilisation de colonnes chiffrées (nir_chiffre/nir_nonce/nir_tag).

ALTER TABLE `personnel_infos`
ADD COLUMN `numero_ss` VARCHAR(15) DEFAULT NULL
COMMENT 'Numéro de sécurité sociale (format: 1 93 02 75 108 136 23)'
AFTER `commentaire`;

-- Index pour recherche (optionnel, décommenter si nécessaire)
-- CREATE INDEX idx_personnel_infos_numero_ss ON personnel_infos(numero_ss);

-- ============================================================
-- Rollback (à exécuter manuellement si nécessaire)
-- ============================================================
-- ALTER TABLE `personnel_infos` DROP COLUMN `numero_ss`;
