-- Migration 037 : Catalogue des formations de référence
-- Date : 2026-03-25
-- Objectif : Stocker les libellés officiels des formations pour faciliter
--            la recherche et la saisie (autocomplete / combo) dans l'application.
--            Une formation saisie peut pointer vers une entrée du catalogue.
--
-- La tranche (libellé) est déterminée dynamiquement via JOIN sur tranche_formation.

USE emac_db;

CREATE TABLE IF NOT EXISTS `catalogue_formation` (
    `id`       INT           NOT NULL AUTO_INCREMENT,
    `code`     INT           NOT NULL COMMENT 'Code numérique (ex: 1250, 2030) — détermine la tranche via tranche_formation',
    `intitule` VARCHAR(255)  NOT NULL COMMENT 'Libellé officiel de la formation',
    `actif`    TINYINT(1)    NOT NULL DEFAULT 1 COMMENT '0 = archivé',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_code_intitule` (`code`, `intitule`),
    KEY `idx_code` (`code`),
    KEY `idx_intitule` (`intitule`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Catalogue de référence des formations (libellés officiels par code/tranche)';

-- Lien optionnel dans formation vers le catalogue
-- (NULL si saisie libre, rempli si sélection depuis le catalogue)
ALTER TABLE formation
  ADD COLUMN IF NOT EXISTS catalogue_formation_id INT DEFAULT NULL
    COMMENT 'Référence au catalogue (NULL = intitulé saisi librement)'
    AFTER code_formation,
  ADD CONSTRAINT `fk_formation_catalogue`
    FOREIGN KEY (`catalogue_formation_id`) REFERENCES `catalogue_formation` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE;

-- Vérification
SELECT 'catalogue_formation créé' AS statut;
