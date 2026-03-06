-- =======================================================================
-- Migration 028 : Dossiers de formation pour les niveaux de polyvalence
-- Version : 1.0
-- Date : 2026-03-05
-- Description : Table pour stocker les documents de formation associes
--               a un poste et/ou un niveau de polyvalence (1-4).
--               Ces documents sont lisibles par tous les utilisateurs
--               et geres par les administrateurs/responsables.
-- =======================================================================

USE emac_db;

CREATE TABLE IF NOT EXISTS `documents_formation_polyvalence` (
  `id`              INT          NOT NULL AUTO_INCREMENT,
  `poste_id`        INT          NOT NULL   COMMENT 'Poste concerne',
  `niveau`          INT          NULL       COMMENT 'Niveau polyvalence (1-4). NULL = applicable a tous les niveaux',
  `nom_affichage`   VARCHAR(255) NOT NULL   COMMENT 'Titre du document affiche a l utilisateur',
  `nom_fichier`     VARCHAR(255) NOT NULL   COMMENT 'Nom du fichier original',
  `contenu_fichier` LONGBLOB     NULL       COMMENT 'Contenu binaire du fichier (BLOB)',
  `type_mime`       VARCHAR(100) DEFAULT NULL,
  `taille_octets`   BIGINT       DEFAULT NULL,
  `description`     TEXT         DEFAULT NULL,
  `date_ajout`      DATETIME     NOT NULL   DEFAULT CURRENT_TIMESTAMP,
  `ajoute_par`      VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_dfp_poste`        (`poste_id`),
  KEY `idx_dfp_poste_niveau` (`poste_id`, `niveau`),
  CONSTRAINT `fk_dfp_poste`
    FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `chk_dfp_niveau` CHECK (`niveau` IS NULL OR `niveau` BETWEEN 1 AND 4)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Dossiers de formation de competences pour les niveaux de polyvalence';

SELECT 'Migration 028 : table documents_formation_polyvalence creee avec succes !' AS message;
