-- Migration 043 : Mise a jour des tables mobilite (suite migration 042)
-- Date : 2026-04-13
-- Contexte : La migration 042 a ete jouee avec l'ancienne structure.
--            Ce script aligne les tables existantes sur la structure cible.

USE emac_db;

-- ============================================================
-- 1. TABLE personnel_mobilite : ajout cv_fiscaux, suppression palier_id
-- ============================================================

-- Supprimer la FK sur palier_id avant de supprimer la colonne
ALTER TABLE `personnel_mobilite`
    DROP FOREIGN KEY IF EXISTS `fk_pm_palier`;

ALTER TABLE `personnel_mobilite`
    ADD COLUMN IF NOT EXISTS `cv_fiscaux` INT DEFAULT NULL
        COMMENT 'Puissance fiscale du vehicule en CV (pour calcul I.K.)'
        AFTER `distance_km`;

-- Supprimer la colonne palier_id (la prime est desormais resolue par la vue)
ALTER TABLE `personnel_mobilite`
    DROP COLUMN IF EXISTS `palier_id`;


-- ============================================================
-- 2. TABLE mobilite_palier : nettoyage colonnes + ajout date_fin_effet
-- ============================================================

ALTER TABLE `mobilite_palier`
    DROP COLUMN IF EXISTS `mode_transport`,
    DROP COLUMN IF EXISTS `montant_mensuel`,
    ADD COLUMN IF NOT EXISTS `date_fin_effet` DATE DEFAULT NULL
        COMMENT 'Date de fin de validite — NULL = bareme actuel'
        AFTER `date_effet`;

-- S'assurer que taux_journalier est NOT NULL (il etait DEFAULT NULL avant)
-- On met d'abord 0 sur les lignes NULL si besoin, puis on change le type
UPDATE `mobilite_palier` SET `taux_journalier` = 0 WHERE `taux_journalier` IS NULL;
ALTER TABLE `mobilite_palier`
    MODIFY COLUMN `taux_journalier` DECIMAL(6,3) NOT NULL
        COMMENT 'Prime par jour travaille en euros';

-- Supprimer les anciennes donnees d'amorcage (fausses tranches mensuelles)
DELETE FROM `mobilite_palier`;


-- ============================================================
-- 3. TABLE mobilite_ik : creation (si inexistante)
-- ============================================================

CREATE TABLE IF NOT EXISTS `mobilite_ik` (
  `id`             INT NOT NULL AUTO_INCREMENT,
  `cv_min`         INT NOT NULL
                       COMMENT 'Puissance fiscale minimale (CV, incluse)',
  `cv_max`         INT DEFAULT NULL
                       COMMENT 'Puissance fiscale maximale (CV, incluse) — NULL = illimite',
  `taux_km`        DECIMAL(6,4) NOT NULL
                       COMMENT 'Indemnite en euros par km parcouru',
  `date_effet`     DATE NOT NULL
                       COMMENT 'Date de debut de validite',
  `date_fin_effet` DATE DEFAULT NULL
                       COMMENT 'Date de fin de validite — NULL = bareme actuel',
  `description`    VARCHAR(100) DEFAULT NULL,
  `actif`          TINYINT(1) NOT NULL DEFAULT 1,
  `created_at`     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at`     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_mik_date_effet` (`date_effet`),
  KEY `idx_mik_actif`      (`actif`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Bareme des indemnites kilometriques par puissance fiscale vehicule';


-- ============================================================
-- 4. Donnees : Bareme prime mobilite (taux journaliers reels)
-- ============================================================

INSERT INTO `mobilite_palier`
    (`distance_min_km`, `distance_max_km`, `taux_journalier`, `date_effet`, `date_fin_effet`, `description`)
VALUES
    -- Bareme au 01/07/2022
    ( 0.00,  6.00, 0.400, '2022-07-01', NULL,         'De 0 a 6 km — 0,40 €/jour'),
    ( 7.00, 13.00, 0.900, '2022-07-01', NULL,         'De 7 a 13 km — 0,90 €/jour'),
    (14.00, 20.00, 1.800, '2022-07-01', NULL,         'De 14 a 20 km — 1,80 €/jour'),
    (21.00, 40.00, 2.700, '2022-07-01', NULL,         'De 21 a 40 km — 2,70 €/jour'),
    (41.00,  NULL, 2.700, '2022-07-01', '2024-06-30', 'De 41 km et plus — 2,70 €/jour (jusqu au 30/06/2024)'),
    -- Nouveau taux 41+ km depuis le 01/07/2024
    (41.00,  NULL, 3.600, '2024-07-01', NULL,         'De 41 km et plus — 3,60 €/jour');


-- ============================================================
-- 5. Donnees : Bareme I.K. (Indemnites Kilometriques)
-- ============================================================

INSERT INTO `mobilite_ik`
    (`cv_min`, `cv_max`, `taux_km`, `date_effet`, `date_fin_effet`, `description`)
VALUES
    -- Bareme au 01/04/2023
    (3,    3, 0.5290, '2023-04-01', '2025-04-30', '3 CV — 0,529 €/km'),
    (4,    4, 0.6060, '2023-04-01', '2025-04-30', '4 CV — 0,606 €/km'),
    (5,    5, 0.6360, '2023-04-01', '2025-04-30', '5 CV — 0,636 €/km'),
    (6,    6, 0.6650, '2023-04-01', '2025-04-30', '6 CV — 0,665 €/km'),
    (7, NULL, 0.6970, '2023-04-01', '2025-04-30', '7 CV et plus — 0,697 €/km'),
    -- Bareme au 01/05/2025
    (3,    3, 0.5290, '2025-05-01', NULL, '3 CV — 0,529 €/km'),
    (4,    4, 0.6060, '2025-05-01', NULL, '4 CV — 0,606 €/km'),
    (5,    5, 0.6360, '2025-05-01', NULL, '5 CV — 0,636 €/km'),
    (6,    6, 0.6650, '2025-05-01', NULL, '6 CV — 0,665 €/km'),
    (7, NULL, 0.6970, '2025-05-01', NULL, '7 CV et plus — 0,697 €/km');


-- ============================================================
-- 6. Vue v_personnel_prime_mobilite (recree)
-- ============================================================

DROP VIEW IF EXISTS `v_personnel_prime_mobilite`;
DROP VIEW IF EXISTS `v_personnel_mobilite_prime`;

CREATE VIEW `v_personnel_prime_mobilite` AS
SELECT
    p.id                    AS personnel_id,
    p.nom,
    p.prenom,
    p.matricule,
    pm.mode_transport,
    pm.distance_km,
    pm.cv_fiscaux,
    pm.ville_depart,
    pm.cp_depart,
    pm.date_effet           AS date_effet_distance,
    mp.taux_journalier      AS prime_journaliere,
    mp.description          AS palier_libelle,
    mp.date_effet           AS date_effet_bareme,
    ik.taux_km              AS ik_taux_km,
    ik.description          AS ik_libelle
FROM personnel p
JOIN personnel_mobilite pm
    ON pm.personnel_id = p.id
    AND pm.actif = 1
    AND pm.date_fin IS NULL
-- Palier prime mobilite le plus recent applicable a la date du jour
LEFT JOIN mobilite_palier mp ON (
    mp.actif = 1
    AND pm.distance_km >= mp.distance_min_km
    AND (mp.distance_max_km IS NULL OR pm.distance_km <= mp.distance_max_km)
    AND mp.date_effet = (
        SELECT MAX(mp2.date_effet)
        FROM mobilite_palier mp2
        WHERE mp2.actif = 1
          AND mp2.date_effet <= CURDATE()
          AND pm.distance_km >= mp2.distance_min_km
          AND (mp2.distance_max_km IS NULL OR pm.distance_km <= mp2.distance_max_km)
    )
)
-- Bareme I.K. le plus recent applicable selon puissance fiscale
LEFT JOIN mobilite_ik ik ON (
    ik.actif = 1
    AND pm.cv_fiscaux IS NOT NULL
    AND pm.cv_fiscaux >= ik.cv_min
    AND (ik.cv_max IS NULL OR pm.cv_fiscaux <= ik.cv_max)
    AND ik.date_effet = (
        SELECT MAX(ik2.date_effet)
        FROM mobilite_ik ik2
        WHERE ik2.actif = 1
          AND ik2.date_effet <= CURDATE()
          AND pm.cv_fiscaux >= ik2.cv_min
          AND (ik2.cv_max IS NULL OR pm.cv_fiscaux <= ik2.cv_max)
    )
)
WHERE p.statut = 'ACTIF';


-- ============================================================
-- Rollback
-- ============================================================
-- DROP VIEW IF EXISTS `v_personnel_prime_mobilite`;
-- ALTER TABLE `personnel_mobilite` DROP COLUMN IF EXISTS `cv_fiscaux`;
-- ALTER TABLE `personnel_mobilite` ADD COLUMN `palier_id` INT DEFAULT NULL;
-- DROP TABLE IF EXISTS `mobilite_ik`;
