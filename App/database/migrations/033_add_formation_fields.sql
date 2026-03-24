-- Migration 033: Ajout des champs lieu, objectif, formateur dans formation
-- Date: 2026-03-23
-- Contexte: Nouveau flux de génération documentaire (saisie → document pré-rempli)
--   - lieu : lieu où se déroule la formation
--   - objectif : objectif pédagogique de la formation
--   - formateur : nom du formateur / intervenant

USE emac_db;

ALTER TABLE formation
  ADD COLUMN IF NOT EXISTS lieu VARCHAR(255) DEFAULT NULL
    COMMENT 'Lieu de déroulement de la formation'
    AFTER organisme,
  ADD COLUMN IF NOT EXISTS objectif TEXT DEFAULT NULL
    COMMENT 'Objectif pédagogique de la formation'
    AFTER lieu,
  ADD COLUMN IF NOT EXISTS formateur VARCHAR(255) DEFAULT NULL
    COMMENT 'Nom du formateur / intervenant'
    AFTER objectif;

-- Vérification
SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'emac_db'
  AND TABLE_NAME = 'formation'
  AND COLUMN_NAME IN ('lieu', 'objectif', 'formateur')
ORDER BY ORDINAL_POSITION;
