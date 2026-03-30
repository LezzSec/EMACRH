-- Migration 035 : Ajout du type de formation dans la table formation
-- Date : 2026-03-25
-- Valeurs : Réglementaire | Technique/Perfectionnement | Poste

USE emac_db;

ALTER TABLE formation
  ADD COLUMN IF NOT EXISTS type_formation ENUM('Réglementaire', 'Technique/Perfectionnement', 'Poste') DEFAULT NULL
    COMMENT 'Catégorie de la formation'
    AFTER intitule;

-- Vérification
SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'emac_db'
  AND TABLE_NAME = 'formation'
  AND COLUMN_NAME = 'type_formation';
