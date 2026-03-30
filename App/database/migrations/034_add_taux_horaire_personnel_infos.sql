-- Migration 034 : Taux horaire dans personnel_infos + coût salarial stocké dans formation
-- Date : 2026-03-25
-- Contexte : Le coût salarial est calculé à la création/modification d'une formation
--            (duree_heures * taux_horaire du salarié) puis stocké dans formation.cout_salarial.
--            Valeur modifiable directement en base à tout moment.

USE emac_db;

-- Taux horaire chargé propre à chaque salarié
ALTER TABLE personnel_infos
  ADD COLUMN IF NOT EXISTS taux_horaire DECIMAL(8, 2) DEFAULT NULL
    COMMENT 'Taux horaire chargé en € propre au salarié'
    AFTER categorie;

-- Coût salarial stocké dans la formation (calculé puis modifiable)
ALTER TABLE formation
  ADD COLUMN IF NOT EXISTS cout_salarial DECIMAL(10, 2) DEFAULT NULL
    COMMENT 'Coût salarial de la formation = duree_heures * taux_horaire salarié (modifiable)'
    AFTER cout;

-- Vérification
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'emac_db'
  AND ((TABLE_NAME = 'personnel_infos' AND COLUMN_NAME = 'taux_horaire')
    OR (TABLE_NAME = 'formation'       AND COLUMN_NAME = 'cout_salarial'))
ORDER BY TABLE_NAME, ORDINAL_POSITION;
