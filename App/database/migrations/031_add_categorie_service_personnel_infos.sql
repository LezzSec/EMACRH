-- Migration 031: Ajout du champ categorie dans personnel_infos
-- Date: 2026-03-18
-- Demande RH du 10/03/2026 :
--   - categorie (O/E/T/C) → ajouté dans personnel_infos
--   - service (Administratif, Labo, R&D...) → stocké dans personnel.numposte (déjà existant)
--     Règle : numposte = 'Production' pour les opérateurs de production,
--             numposte = nom du service pour les autres (Administratif, Labo, etc.)

USE emac_db;

ALTER TABLE personnel_infos
  ADD COLUMN IF NOT EXISTS categorie ENUM('O', 'E', 'T', 'C') DEFAULT NULL
    COMMENT 'Catégorie salarié : O=Ouvrier, E=Employé, T=Technicien, C=Cadre'
    AFTER commentaire;

CREATE INDEX IF NOT EXISTS idx_pi_categorie ON personnel_infos(categorie);

-- Vérification
SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'emac_db'
  AND TABLE_NAME = 'personnel_infos'
  AND COLUMN_NAME = 'categorie';
