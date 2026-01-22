-- Migration: Création des tables "Vie du salarié" SIRH
-- Date: 2026-01-21
-- Source: Tableau SIRH.xlsx - Feuille "Vie du salarié"

-- ============================================================
-- Table des sanctions disciplinaires
-- ============================================================
CREATE TABLE IF NOT EXISTS `vie_salarie_sanction` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `operateur_id` INT NOT NULL,
    `type_sanction` ENUM(
        'Observation verbale',
        'Observation écrite',
        'Avertissement',
        'Mise à pied disciplinaire',
        'Mise à pied conservatoire'
    ) NOT NULL,
    `date_sanction` DATE NOT NULL,
    `duree_jours` INT DEFAULT NULL
        COMMENT 'Durée en jours (pour les mises à pied)',
    `motif` TEXT DEFAULT NULL,
    `document_reference` VARCHAR(255) DEFAULT NULL
        COMMENT 'Référence du document associé',
    `commentaire` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_sanction_operateur` (`operateur_id`),
    KEY `idx_sanction_date` (`date_sanction`),
    KEY `idx_sanction_type` (`type_sanction`),
    CONSTRAINT `fk_sanction_operateur` FOREIGN KEY (`operateur_id`)
        REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Table des contrôles d'alcoolémie
-- ============================================================
CREATE TABLE IF NOT EXISTS `vie_salarie_alcoolemie` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `operateur_id` INT NOT NULL,
    `date_controle` DATETIME NOT NULL,
    `resultat` ENUM('Négatif', 'Positif') NOT NULL,
    `taux` DECIMAL(4,2) DEFAULT NULL
        COMMENT 'Taux en g/L si positif',
    `type_controle` ENUM('Aléatoire', 'Ciblé', 'Accident') DEFAULT 'Aléatoire',
    `commentaire` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_alcool_operateur` (`operateur_id`),
    KEY `idx_alcool_date` (`date_controle`),
    KEY `idx_alcool_resultat` (`resultat`),
    CONSTRAINT `fk_alcool_operateur` FOREIGN KEY (`operateur_id`)
        REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Table des tests salivaires (stupéfiants)
-- ============================================================
CREATE TABLE IF NOT EXISTS `vie_salarie_test_salivaire` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `operateur_id` INT NOT NULL,
    `date_test` DATETIME NOT NULL,
    `resultat` ENUM('Négatif', 'Positif', 'Non concluant') NOT NULL,
    `type_controle` ENUM('Aléatoire', 'Ciblé', 'Accident') DEFAULT 'Aléatoire',
    `commentaire` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_salivaire_operateur` (`operateur_id`),
    KEY `idx_salivaire_date` (`date_test`),
    KEY `idx_salivaire_resultat` (`resultat`),
    CONSTRAINT `fk_salivaire_operateur` FOREIGN KEY (`operateur_id`)
        REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Table des entretiens professionnels (EPP, EAP)
-- ============================================================
CREATE TABLE IF NOT EXISTS `vie_salarie_entretien` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `operateur_id` INT NOT NULL,
    `type_entretien` ENUM('EPP', 'EAP', 'Bilan 6 ans', 'Entretien annuel', 'Autre') NOT NULL
        COMMENT 'EPP: Entretien Professionnel Périodique, EAP: Entretien Annuel de Performance',
    `date_entretien` DATE NOT NULL,
    `manager_id` INT DEFAULT NULL
        COMMENT 'ID du manager qui a conduit l''entretien',
    `objectifs_atteints` TEXT DEFAULT NULL
        COMMENT 'Évaluation des objectifs de la période précédente',
    `objectifs_fixes` TEXT DEFAULT NULL
        COMMENT 'Objectifs fixés pour la période à venir',
    `besoins_formation` TEXT DEFAULT NULL,
    `souhaits_evolution` TEXT DEFAULT NULL,
    `commentaire_salarie` TEXT DEFAULT NULL,
    `commentaire_manager` TEXT DEFAULT NULL,
    `document_reference` VARCHAR(255) DEFAULT NULL,
    `prochaine_date` DATE DEFAULT NULL
        COMMENT 'Date prévue du prochain entretien',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_entretien_operateur` (`operateur_id`),
    KEY `idx_entretien_date` (`date_entretien`),
    KEY `idx_entretien_type` (`type_entretien`),
    KEY `idx_entretien_manager` (`manager_id`),
    CONSTRAINT `fk_entretien_operateur` FOREIGN KEY (`operateur_id`)
        REFERENCES `personnel` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_entretien_manager` FOREIGN KEY (`manager_id`)
        REFERENCES `personnel` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Vue récapitulative de la vie du salarié
-- ============================================================
DROP VIEW IF EXISTS `v_vie_salarie_recap`;
CREATE VIEW `v_vie_salarie_recap` AS
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.statut,
    -- Sanctions
    (SELECT COUNT(*) FROM vie_salarie_sanction s WHERE s.operateur_id = p.id) AS nb_sanctions,
    (SELECT MAX(date_sanction) FROM vie_salarie_sanction s WHERE s.operateur_id = p.id) AS derniere_sanction,
    -- Contrôles alcoolémie
    (SELECT COUNT(*) FROM vie_salarie_alcoolemie a WHERE a.operateur_id = p.id) AS nb_controles_alcool,
    (SELECT COUNT(*) FROM vie_salarie_alcoolemie a WHERE a.operateur_id = p.id AND a.resultat = 'Positif') AS nb_positifs_alcool,
    -- Tests salivaires
    (SELECT COUNT(*) FROM vie_salarie_test_salivaire t WHERE t.operateur_id = p.id) AS nb_tests_salivaires,
    (SELECT COUNT(*) FROM vie_salarie_test_salivaire t WHERE t.operateur_id = p.id AND t.resultat = 'Positif') AS nb_positifs_salivaire,
    -- Entretiens
    (SELECT MAX(date_entretien) FROM vie_salarie_entretien e WHERE e.operateur_id = p.id AND e.type_entretien = 'EPP') AS dernier_epp,
    (SELECT MAX(date_entretien) FROM vie_salarie_entretien e WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP') AS dernier_eap,
    (SELECT prochaine_date FROM vie_salarie_entretien e
     WHERE e.operateur_id = p.id
     ORDER BY date_entretien DESC LIMIT 1) AS prochain_entretien
FROM personnel p;

-- ============================================================
-- Vue alertes entretiens (EPP/EAP en retard)
-- ============================================================
DROP VIEW IF EXISTS `v_alertes_entretiens`;
CREATE VIEW `v_alertes_entretiens` AS
-- EPP en retard (obligatoire tous les 2 ans)
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    'EPP en retard' AS type_alerte,
    COALESCE(
        (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
         WHERE e.operateur_id = p.id AND e.type_entretien = 'EPP'),
        pi.date_entree
    ) AS derniere_date,
    DATEDIFF(
        CURDATE(),
        DATE_ADD(
            COALESCE(
                (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
                 WHERE e.operateur_id = p.id AND e.type_entretien = 'EPP'),
                pi.date_entree
            ),
            INTERVAL 2 YEAR
        )
    ) AS jours_retard
FROM personnel p
LEFT JOIN personnel_infos pi ON p.id = pi.operateur_id
WHERE p.statut = 'ACTIF'
  AND DATEDIFF(
        CURDATE(),
        DATE_ADD(
            COALESCE(
                (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
                 WHERE e.operateur_id = p.id AND e.type_entretien = 'EPP'),
                pi.date_entree
            ),
            INTERVAL 2 YEAR
        )
    ) > 0

UNION ALL

-- EAP en retard (annuel)
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    'EAP en retard' AS type_alerte,
    (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
     WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP') AS derniere_date,
    DATEDIFF(
        CURDATE(),
        DATE_ADD(
            (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
             WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP'),
            INTERVAL 1 YEAR
        )
    ) AS jours_retard
FROM personnel p
WHERE p.statut = 'ACTIF'
  AND (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
       WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP') IS NOT NULL
  AND DATEDIFF(
        CURDATE(),
        DATE_ADD(
            (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
             WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP'),
            INTERVAL 1 YEAR
        )
    ) > 0;

-- ============================================================
-- Rollback (à exécuter manuellement si nécessaire)
-- ============================================================
-- DROP VIEW IF EXISTS `v_alertes_entretiens`;
-- DROP VIEW IF EXISTS `v_vie_salarie_recap`;
-- DROP TABLE IF EXISTS `vie_salarie_entretien`;
-- DROP TABLE IF EXISTS `vie_salarie_test_salivaire`;
-- DROP TABLE IF EXISTS `vie_salarie_alcoolemie`;
-- DROP TABLE IF EXISTS `vie_salarie_sanction`;
