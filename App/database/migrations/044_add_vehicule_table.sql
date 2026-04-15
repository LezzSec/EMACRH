-- Migration 044 : Table vehicule du personnel
-- Date : 2026-04-13
-- Contexte : Stocker les informations vehicule de chaque salarie pour
--            calculer les indemnites kilometriques selon la puissance fiscale.

USE emac_db;

-- ============================================================
-- Table personnel_vehicule
-- ============================================================

CREATE TABLE IF NOT EXISTS `personnel_vehicule` (
  `id`              INT NOT NULL AUTO_INCREMENT,
  `personnel_id`    INT NOT NULL
                        COMMENT 'FK vers personnel.id',
  `immatriculation` VARCHAR(20) DEFAULT NULL,
  `marque`          VARCHAR(100) DEFAULT NULL,
  `modele`          VARCHAR(100) DEFAULT NULL,
  `annee`           SMALLINT DEFAULT NULL
                        COMMENT 'Annee de mise en circulation',
  `cv_fiscaux`      INT NOT NULL
                        COMMENT 'Puissance fiscale en chevaux (determine le taux IK)',
  `energie`         ENUM('essence', 'diesel', 'electrique', 'hybride', 'autre')
                        NOT NULL DEFAULT 'essence',
  `actif`           TINYINT(1) NOT NULL DEFAULT 1
                        COMMENT '1 = vehicule actuellement utilise',
  `date_debut`      DATE DEFAULT NULL
                        COMMENT 'Date a partir de laquelle ce vehicule est utilise',
  `date_fin`        DATE DEFAULT NULL
                        COMMENT 'NULL = vehicule toujours en cours',
  `notes`           TEXT DEFAULT NULL,
  `created_at`      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at`      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_pv_personnel` (`personnel_id`),
  KEY `idx_pv_actif`     (`actif`),
  CONSTRAINT `fk_pv_personnel`
      FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Vehicules des salaries (source de la puissance fiscale pour calcul IK)';


-- ============================================================
-- Lien optionnel depuis personnel_mobilite vers personnel_vehicule
-- ============================================================
-- vehicule_id est nullable : on peut saisir cv_fiscaux manuellement
-- OU choisir un vehicule existant (qui auto-renseigne cv_fiscaux).

ALTER TABLE `personnel_mobilite`
    ADD COLUMN IF NOT EXISTS `vehicule_id` INT DEFAULT NULL
        COMMENT 'FK optionnelle vers personnel_vehicule (auto-renseigne cv_fiscaux)'
        AFTER `cv_fiscaux`,
    ADD CONSTRAINT `fk_pm_vehicule`
        FOREIGN KEY IF NOT EXISTS (`vehicule_id`)
        REFERENCES `personnel_vehicule` (`id`)
        ON DELETE SET NULL;


-- ============================================================
-- Rollback
-- ============================================================
-- ALTER TABLE `personnel_mobilite` DROP FOREIGN KEY IF EXISTS `fk_pm_vehicule`;
-- ALTER TABLE `personnel_mobilite` DROP COLUMN IF EXISTS `vehicule_id`;
-- DROP TABLE IF EXISTS `personnel_vehicule`;
