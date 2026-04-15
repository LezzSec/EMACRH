-- Migration 042 : Tables mobilité (distance domicile-entreprise + barème primes)
-- Date : 2026-04-13
-- Contexte : Calcul des primes de mobilité et indemnités kilométriques (I.K.)
--            basées sur la distance domicile-entreprise et la puissance fiscale du véhicule.

USE emac_db;

-- ============================================================
-- Table mobilite_palier : Barème prime mobilité (€/jour par tranche km)
-- ============================================================
-- Tranches : 0-6 km | 7-13 km | 14-20 km | 21-40 km | 41+ km
-- Plusieurs barèmes coexistent via date_effet (historique).

CREATE TABLE IF NOT EXISTS `mobilite_palier` (
  `id`              INT NOT NULL AUTO_INCREMENT,
  `distance_min_km` DECIMAL(6,2) NOT NULL DEFAULT 0
                        COMMENT 'Borne inferieure de la tranche (km, incluse)',
  `distance_max_km` DECIMAL(6,2) DEFAULT NULL
                        COMMENT 'Borne superieure de la tranche (km, incluse) — NULL = illimite',
  `taux_journalier` DECIMAL(6,3) NOT NULL
                        COMMENT 'Prime par jour travaille en euros',
  `date_effet`      DATE NOT NULL
                        COMMENT 'Date de debut de validite de ce bareme',
  `date_fin_effet`  DATE DEFAULT NULL
                        COMMENT 'Date de fin de validite — NULL = bareme actuel',
  `description`     VARCHAR(255) DEFAULT NULL
                        COMMENT 'Libelle court affiche dans interface',
  `actif`           TINYINT(1) NOT NULL DEFAULT 1,
  `created_at`      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at`      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_mp_date_effet` (`date_effet`),
  KEY `idx_mp_actif`      (`actif`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Bareme des primes de mobilite par tranche kilometrique et date';


-- ============================================================
-- Table mobilite_ik : Indemnités kilométriques (barème fiscal par CV)
-- ============================================================
-- Taux en €/km selon la puissance fiscale du véhicule (chevaux fiscaux).

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
-- Table personnel_mobilite : Situation de chaque salarié
-- ============================================================

CREATE TABLE IF NOT EXISTS `personnel_mobilite` (
  `id`               INT NOT NULL AUTO_INCREMENT,
  `personnel_id`     INT NOT NULL
                         COMMENT 'FK vers personnel.id',
  `distance_km`      DECIMAL(6,2) NOT NULL
                         COMMENT 'Distance aller simple domicile-entreprise en km',
  `cv_fiscaux`       INT DEFAULT NULL
                         COMMENT 'Puissance fiscale du vehicule (pour calcul I.K.)',
  `mode_transport`   ENUM('voiture', 'velo', 'transport_commun', 'covoiturage', 'autre')
                         NOT NULL DEFAULT 'voiture',
  `adresse_depart`   VARCHAR(255) DEFAULT NULL
                         COMMENT 'Adresse utilisee (si differente de personnel_infos)',
  `cp_depart`        VARCHAR(10)  DEFAULT NULL,
  `ville_depart`     VARCHAR(100) DEFAULT NULL,
  `methode_calcul`   ENUM('manuel', 'google_maps', 'ign', 'autre') DEFAULT 'manuel',
  `date_effet`       DATE NOT NULL
                         COMMENT 'Date a partir de laquelle cette distance s\'applique',
  `date_fin`         DATE DEFAULT NULL
                         COMMENT 'NULL = en vigueur ; renseigner si le salarie a demenage',
  `actif`            TINYINT(1) NOT NULL DEFAULT 1,
  `notes`            TEXT DEFAULT NULL,
  `created_at`       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at`       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_pm_personnel`  (`personnel_id`),
  KEY `idx_pm_actif`      (`actif`),
  KEY `idx_pm_date_effet` (`date_effet`),
  CONSTRAINT `fk_pm_personnel`
      FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='Distance domicile-entreprise et mode de transport par salarie';


-- ============================================================
-- Vue v_personnel_prime_mobilite
-- ============================================================
-- Résout automatiquement le palier prime applicable à la date du jour.

DROP VIEW IF EXISTS `v_personnel_prime_mobilite`;
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
-- Palier prime mobilité le plus récent applicable
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
-- Barème I.K. le plus récent applicable (selon puissance fiscale)
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
-- Données : Barème prime mobilité
-- ============================================================

-- Barème en vigueur au 01/07/2022 (remplacé le 01/07/2024 pour la 5e tranche)
INSERT IGNORE INTO `mobilite_palier`
    (`distance_min_km`, `distance_max_km`, `taux_journalier`, `date_effet`, `date_fin_effet`, `description`)
VALUES
    ( 0.00,  6.00, 0.400, '2022-07-01', NULL,         'De 0 a 6 km — 0,40 €/jour'),
    ( 7.00, 13.00, 0.900, '2022-07-01', NULL,         'De 7 a 13 km — 0,90 €/jour'),
    (14.00, 20.00, 1.800, '2022-07-01', NULL,         'De 14 a 20 km — 1,80 €/jour'),
    (21.00, 40.00, 2.700, '2022-07-01', NULL,         'De 21 a 40 km — 2,70 €/jour'),
    (41.00,  NULL, 2.700, '2022-07-01', '2024-06-30', 'De 41 km et plus — 2,70 €/jour (jusqu au 30/06/2024)'),
    -- Nouveau taux 41+ km depuis le 01/07/2024
    (41.00,  NULL, 3.600, '2024-07-01', NULL,         'De 41 km et plus — 3,60 €/jour');


-- ============================================================
-- Données : Barème I.K. (Indemnités Kilométriques)
-- ============================================================

-- Barème au 01/04/2023
INSERT IGNORE INTO `mobilite_ik`
    (`cv_min`, `cv_max`, `taux_km`, `date_effet`, `date_fin_effet`, `description`)
VALUES
    (3, 3, 0.5290, '2023-04-01', '2025-04-30', '3 CV — 0,529 €/km'),
    (4, 4, 0.6060, '2023-04-01', '2025-04-30', '4 CV — 0,606 €/km'),
    (5, 5, 0.6360, '2023-04-01', '2025-04-30', '5 CV — 0,636 €/km'),
    (6, 6, 0.6650, '2023-04-01', '2025-04-30', '6 CV — 0,665 €/km'),
    (7, NULL, 0.6970, '2023-04-01', '2025-04-30', '7 CV et plus — 0,697 €/km');

-- Barème au 01/05/2025
INSERT IGNORE INTO `mobilite_ik`
    (`cv_min`, `cv_max`, `taux_km`, `date_effet`, `date_fin_effet`, `description`)
VALUES
    (3, 3, 0.5290, '2025-05-01', NULL, '3 CV — 0,529 €/km'),
    (4, 4, 0.6060, '2025-05-01', NULL, '4 CV — 0,606 €/km'),
    (5, 5, 0.6360, '2025-05-01', NULL, '5 CV — 0,636 €/km'),
    (6, 6, 0.6650, '2025-05-01', NULL, '6 CV — 0,665 €/km'),
    (7, NULL, 0.6970, '2025-05-01', NULL, '7 CV et plus — 0,697 €/km');


-- ============================================================
-- Rollback
-- ============================================================
-- DROP VIEW IF EXISTS `v_personnel_prime_mobilite`;
-- DROP TABLE IF EXISTS `personnel_mobilite`;
-- DROP TABLE IF EXISTS `mobilite_ik`;
-- DROP TABLE IF EXISTS `mobilite_palier`;
