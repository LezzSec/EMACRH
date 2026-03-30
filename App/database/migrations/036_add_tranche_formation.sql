-- Migration 036 : Table de référence des tranches de formation + code dans formation
-- Date : 2026-03-25
-- Logique : formations numérotées par tranches de 1000
--   1000-1999 → Santé & Sécurité
--   2000-2999 → Technique & Perfectionnement
--   3000+     → Au poste en interne

USE emac_db;

-- Table de référence des tranches (modifiable directement en base)
CREATE TABLE IF NOT EXISTS `tranche_formation` (
    `id`           INT           NOT NULL AUTO_INCREMENT,
    `tranche_min`  INT           NOT NULL COMMENT 'Code minimum de la tranche (inclus)',
    `tranche_max`  INT           DEFAULT NULL COMMENT 'Code maximum de la tranche (inclus, NULL = pas de limite)',
    `libelle`      VARCHAR(100)  NOT NULL COMMENT 'Libellé affiché pour cette tranche',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_tranche_min` (`tranche_min`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Tranches de numérotation des formations et leurs libellés';

-- Valeurs initiales
INSERT INTO `tranche_formation` (`tranche_min`, `tranche_max`, `libelle`) VALUES
    (1000, 1999, 'Santé & Sécurité'),
    (2000, 2999, 'Technique & Perfectionnement'),
    (3000, 3999, 'Au poste en interne')
ON DUPLICATE KEY UPDATE `libelle` = VALUES(`libelle`);

-- Code numérique de la formation dans la table formation
ALTER TABLE formation
  ADD COLUMN IF NOT EXISTS code_formation INT DEFAULT NULL
    COMMENT 'Code numérique de la formation (détermine la tranche/catégorie)'
    AFTER type_formation;

-- Vérification
SELECT t.tranche_min, t.tranche_max, t.libelle FROM tranche_formation t ORDER BY t.tranche_min;
