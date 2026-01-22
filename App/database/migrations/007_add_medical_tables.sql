-- Migration: Création des tables médicales SIRH
-- Date: 2026-01-21
-- Source: Tableau SIRH.xlsx - Feuille "Medical"
--
-- NOTE: La table validite existe déjà pour RQTH/OETH avec les champs:
--   - type_validite (ENUM 'RQTH', 'OETH')
--   - date_debut, date_fin, periodicite, taux_incapacite
--   - document_justificatif, commentaire
-- Cette migration ne recrée PAS ces champs mais les utilise via des vues.

-- ============================================================
-- Table principale medical : Suivi médical des salariés
-- (Données qui ne sont pas dans validite)
-- ============================================================
CREATE TABLE IF NOT EXISTS `medical` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `operateur_id` INT NOT NULL,

    -- Visite médicale (VIP)
    `type_suivi_vip` ENUM('SIA', 'SIR', 'SI') DEFAULT NULL
        COMMENT 'Type de suivi: SIA (Adapté), SIR (Renforcé), SI (Individuel)',
    `periodicite_vip_mois` INT DEFAULT 24
        COMMENT 'Périodicité des visites en mois',

    -- Électrocardiogramme
    `date_electrocardiogramme` DATE DEFAULT NULL,

    -- Maladie professionnelle (flag, détails dans medical_maladie_pro)
    `maladie_pro` TINYINT(1) DEFAULT 0
        COMMENT '1 si maladie professionnelle reconnue',

    -- Taux professionnel (différent du taux_incapacite dans validite)
    `taux_professionnel` DECIMAL(5,2) DEFAULT NULL
        COMMENT 'Taux professionnel en pourcentage',

    -- Besoins d'adaptation
    `besoins_adaptation` TEXT DEFAULT NULL
        COMMENT 'Description des besoins d''adaptation au poste',

    -- Demandes en cours
    `demande_reconnaissance_atmp_en_cours` TINYINT(1) DEFAULT 0
        COMMENT '1 si demande de reconnaissance AT/MP en cours',

    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_medical_operateur` (`operateur_id`),
    CONSTRAINT `fk_medical_operateur` FOREIGN KEY (`operateur_id`)
        REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Table historique des visites médicales (VIP)
-- ============================================================
CREATE TABLE IF NOT EXISTS `medical_visite` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `operateur_id` INT NOT NULL,
    `date_visite` DATE NOT NULL,
    `type_visite` ENUM('Embauche', 'Périodique', 'Reprise', 'À la demande', 'Pré-reprise') DEFAULT 'Périodique',
    `resultat` ENUM('Apte', 'Apte avec restrictions', 'Inapte temporaire', 'Inapte définitif') DEFAULT NULL,
    `restrictions` TEXT DEFAULT NULL
        COMMENT 'Détail des restrictions si applicable',
    `medecin` VARCHAR(255) DEFAULT NULL,
    `commentaire` TEXT DEFAULT NULL,
    `prochaine_visite` DATE DEFAULT NULL
        COMMENT 'Date de la prochaine visite programmée',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_visite_operateur` (`operateur_id`),
    KEY `idx_visite_date` (`date_visite`),
    KEY `idx_visite_prochaine` (`prochaine_visite`),
    CONSTRAINT `fk_visite_operateur` FOREIGN KEY (`operateur_id`)
        REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Table historique des reconnaissances MP (Maladie Professionnelle)
-- ============================================================
CREATE TABLE IF NOT EXISTS `medical_maladie_pro` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `operateur_id` INT NOT NULL,
    `date_reconnaissance` DATE NOT NULL,
    `numero_tableau` VARCHAR(20) DEFAULT NULL
        COMMENT 'Numéro du tableau des maladies professionnelles',
    `designation` VARCHAR(255) DEFAULT NULL,
    `taux_ipp` DECIMAL(5,2) DEFAULT NULL
        COMMENT 'Taux d''Incapacité Permanente Partielle',
    `commentaire` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_mp_operateur` (`operateur_id`),
    KEY `idx_mp_date` (`date_reconnaissance`),
    CONSTRAINT `fk_mp_operateur` FOREIGN KEY (`operateur_id`)
        REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Table historique des accidents du travail (AT)
-- ============================================================
CREATE TABLE IF NOT EXISTS `medical_accident_travail` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `operateur_id` INT NOT NULL,
    `date_accident` DATE NOT NULL,
    `heure_accident` TIME DEFAULT NULL,
    `jour_semaine` ENUM('Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche') DEFAULT NULL,
    `horaires` VARCHAR(50) DEFAULT NULL
        COMMENT 'Horaires de travail au moment de l''accident',
    `circonstances` TEXT DEFAULT NULL,
    `siege_lesions` VARCHAR(255) DEFAULT NULL
        COMMENT 'Partie du corps touchée',
    `nature_lesions` VARCHAR(255) DEFAULT NULL
        COMMENT 'Type de lésion (fracture, brûlure, etc.)',
    `avec_arret` TINYINT(1) DEFAULT 0
        COMMENT '1 si accident avec arrêt de travail',
    `date_reconnaissance_at` DATE DEFAULT NULL,
    `date_debut_arret` DATE DEFAULT NULL,
    `date_fin_arret_initial` DATE DEFAULT NULL,
    `date_fin_prolongation` DATE DEFAULT NULL
        COMMENT 'Dernière date de fin de prolongation',
    `nb_jours_absence` INT DEFAULT NULL
        COMMENT 'Nombre total de jours d''absence (calculé)',
    `commentaire` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_at_operateur` (`operateur_id`),
    KEY `idx_at_date` (`date_accident`),
    KEY `idx_at_avec_arret` (`avec_arret`),
    CONSTRAINT `fk_at_operateur` FOREIGN KEY (`operateur_id`)
        REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Table des prolongations d'arrêt (pour gérer plusieurs prolongations)
-- ============================================================
CREATE TABLE IF NOT EXISTS `medical_prolongation_arret` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `accident_id` INT NOT NULL,
    `date_debut` DATE NOT NULL,
    `date_fin` DATE NOT NULL,
    `numero_prolongation` INT DEFAULT 1,
    `commentaire` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_prolongation_accident` (`accident_id`),
    CONSTRAINT `fk_prolongation_accident` FOREIGN KEY (`accident_id`)
        REFERENCES `medical_accident_travail` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Vue pour le suivi médical complet (intègre table validite existante)
-- ============================================================
DROP VIEW IF EXISTS `v_suivi_medical`;
CREATE VIEW `v_suivi_medical` AS
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    p.statut,
    m.type_suivi_vip,
    m.periodicite_vip_mois,
    -- Dernière visite
    (SELECT MAX(date_visite) FROM medical_visite mv WHERE mv.operateur_id = p.id) AS derniere_visite,
    -- Prochaine visite calculée
    (SELECT prochaine_visite FROM medical_visite mv
     WHERE mv.operateur_id = p.id
     ORDER BY date_visite DESC LIMIT 1) AS prochaine_visite,
    -- Statut visite
    CASE
        WHEN (SELECT prochaine_visite FROM medical_visite mv
              WHERE mv.operateur_id = p.id
              ORDER BY date_visite DESC LIMIT 1) < CURDATE()
        THEN 'En retard'
        WHEN (SELECT prochaine_visite FROM medical_visite mv
              WHERE mv.operateur_id = p.id
              ORDER BY date_visite DESC LIMIT 1) <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        THEN 'À planifier'
        ELSE 'OK'
    END AS statut_visite,
    -- RQTH depuis table validite existante
    (SELECT date_debut FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) AS date_debut_rqth,
    (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) AS date_fin_rqth,
    CASE
        WHEN (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) IS NOT NULL
             AND (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) >= CURDATE()
        THEN 'Active'
        WHEN (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) IS NOT NULL
             AND (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) < CURDATE()
        THEN 'Expirée'
        ELSE 'Non applicable'
    END AS statut_rqth,
    -- OETH depuis table validite existante
    (SELECT date_debut FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'OETH' ORDER BY date_debut DESC LIMIT 1) AS date_debut_oeth,
    (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'OETH' ORDER BY date_debut DESC LIMIT 1) AS date_fin_oeth,
    -- Taux d'incapacité depuis table validite
    (SELECT taux_incapacite FROM validite v WHERE v.operateur_id = p.id ORDER BY date_debut DESC LIMIT 1) AS taux_incapacite,
    -- Maladie pro
    m.maladie_pro,
    -- Nombre d'AT
    (SELECT COUNT(*) FROM medical_accident_travail at WHERE at.operateur_id = p.id) AS nb_accidents
FROM personnel p
LEFT JOIN medical m ON p.id = m.operateur_id
WHERE p.statut = 'ACTIF';

-- ============================================================
-- Vue alertes médicales (visites en retard, RQTH expirant)
-- ============================================================
DROP VIEW IF EXISTS `v_alertes_medicales`;
CREATE VIEW `v_alertes_medicales` AS
-- Visites en retard
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    'Visite médicale en retard' AS type_alerte,
    mv.prochaine_visite AS date_alerte,
    DATEDIFF(CURDATE(), mv.prochaine_visite) AS jours_retard
FROM personnel p
JOIN medical_visite mv ON p.id = mv.operateur_id
WHERE p.statut = 'ACTIF'
  AND mv.prochaine_visite < CURDATE()
  AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE operateur_id = p.id)

UNION ALL

-- RQTH expirant bientôt (utilise table validite existante)
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    'RQTH expirant bientôt' AS type_alerte,
    v.date_fin AS date_alerte,
    DATEDIFF(v.date_fin, CURDATE()) AS jours_retard
FROM personnel p
JOIN validite v ON p.id = v.operateur_id
WHERE p.statut = 'ACTIF'
  AND v.type_validite = 'RQTH'
  AND v.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 90 DAY);

-- ============================================================
-- Rollback (à exécuter manuellement si nécessaire)
-- ============================================================
-- DROP VIEW IF EXISTS `v_alertes_medicales`;
-- DROP VIEW IF EXISTS `v_suivi_medical`;
-- DROP TABLE IF EXISTS `medical_prolongation_arret`;
-- DROP TABLE IF EXISTS `medical_accident_travail`;
-- DROP TABLE IF EXISTS `medical_maladie_pro`;
-- DROP TABLE IF EXISTS `medical_visite`;
-- DROP TABLE IF EXISTS `medical`;
