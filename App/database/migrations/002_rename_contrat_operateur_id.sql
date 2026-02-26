-- =====================================================================
-- Migration 002 : Renommage contrat.operateur_id → contrat.personnel_id
-- Date : 2026-02-26
-- Raison : Harmonisation de la nomenclature — "personnel_id" est plus
--          générique et cohérent avec les autres tables (personnel_infos,
--          documents, etc.). La table polyvalence garde "operateur_id"
--          car elle est centrée sur le rôle opérateur de production.
-- =====================================================================

USE emac_db;

ALTER TABLE contrat
    DROP FOREIGN KEY fk_contrat_operateur,
    DROP INDEX idx_operateur,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX idx_personnel (personnel_id),
    ADD CONSTRAINT fk_contrat_personnel
        FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE;

-- Vérification
SELECT 'Migration 002 appliquée : contrat.operateur_id renommé en personnel_id' AS statut;

SHOW INDEX FROM contrat WHERE Key_name IN ('idx_personnel', 'fk_contrat_personnel');
