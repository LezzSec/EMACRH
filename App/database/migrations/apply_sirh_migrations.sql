-- ============================================================
-- Script d'application des migrations SIRH
-- Date: 2026-01-22
--
-- Ce script applique les migrations 006, 007, 008 pour
-- compléter la base de données selon le fichier Tableau SIRH.xlsx
--
-- ATTENTION: Exécuter ce script une seule fois !
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- MIGRATION 006: Compléter la table contrat
-- ============================================================

-- Motif du contrat/CDD
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `motif` TEXT DEFAULT NULL
COMMENT 'Motif du contrat ou du CDD'
AFTER `type_cdd`;

-- Date de sortie effective
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `date_sortie` DATE DEFAULT NULL
COMMENT 'Date de sortie effective'
AFTER `date_fin`;

-- Date d'embauche en CDI (si passage CDD -> CDI)
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `date_embauche_cdi` DATE DEFAULT NULL
COMMENT 'Date d''embauche en CDI (passage CDD -> CDI)'
AFTER `date_sortie`;

-- Motif de sortie
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `motif_sortie` VARCHAR(100) DEFAULT NULL
COMMENT 'Motif de sortie (démission, licenciement, fin CDD, retraite, etc.)'
AFTER `date_embauche_cdi`;

-- Typologie de statut horaire
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `typologie_statut_horaire` ENUM(
    'Cadre forfait jour',
    'Cadre décompte horaire',
    'Non-cadre',
    'Temps partiel'
) DEFAULT NULL
COMMENT 'Typologie du statut horaire'
AFTER `categorie`;

-- Niveau dans la grille
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `niveau` VARCHAR(20) DEFAULT NULL
COMMENT 'Niveau dans la grille'
AFTER `echelon`;

-- Coefficient salarial
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `coefficient` INT DEFAULT NULL
COMMENT 'Coefficient salarial'
AFTER `niveau`;

-- Salaire annuel brut
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `salaire_annuel` DECIMAL(12,2) DEFAULT NULL
COMMENT 'Salaire brut annuel'
AFTER `salaire`;

-- Type de prime
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `type_prime` VARCHAR(100) DEFAULT NULL
COMMENT 'Type de prime (ancienneté, performance, etc.)'
AFTER `salaire_annuel`;

-- Montant prime mensuel brut
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `prime_mensuelle` DECIMAL(10,2) DEFAULT NULL
COMMENT 'Montant prime mensuel brut'
AFTER `type_prime`;

-- Total prime annuel brut
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `prime_annuelle` DECIMAL(12,2) DEFAULT NULL
COMMENT 'Total prime annuel brut'
AFTER `prime_mensuelle`;

-- Table de référence pour les motifs de sortie
CREATE TABLE IF NOT EXISTS `ref_motif_sortie` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `libelle` VARCHAR(100) NOT NULL,
    `actif` TINYINT(1) DEFAULT 1,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_libelle` (`libelle`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT IGNORE INTO `ref_motif_sortie` (`libelle`) VALUES
    ('Démission'),
    ('Licenciement économique'),
    ('Licenciement pour faute'),
    ('Licenciement pour inaptitude'),
    ('Fin de CDD'),
    ('Fin de période d''essai'),
    ('Rupture conventionnelle'),
    ('Retraite'),
    ('Décès'),
    ('Mutation'),
    ('Fin de mission intérim'),
    ('Fin de stage'),
    ('Fin d''apprentissage');

-- Index pour contrat
CREATE INDEX IF NOT EXISTS `idx_contrat_motif_sortie` ON `contrat` (`motif_sortie`);
CREATE INDEX IF NOT EXISTS `idx_contrat_date_sortie` ON `contrat` (`date_sortie`);

SELECT 'Migration 006 (contrat) appliquée' AS status;

-- ============================================================
-- MIGRATION 007: Tables médicales
-- ============================================================

-- Table principale medical
CREATE TABLE IF NOT EXISTS `medical` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `operateur_id` INT NOT NULL,
    `type_suivi_vip` ENUM('SIA', 'SIR', 'SI') DEFAULT NULL
        COMMENT 'Type de suivi: SIA (Adapté), SIR (Renforcé), SI (Individuel)',
    `periodicite_vip_mois` INT DEFAULT 24
        COMMENT 'Périodicité des visites en mois',
    `date_electrocardiogramme` DATE DEFAULT NULL,
    `maladie_pro` TINYINT(1) DEFAULT 0
        COMMENT '1 si maladie professionnelle reconnue',
    `taux_professionnel` DECIMAL(5,2) DEFAULT NULL
        COMMENT 'Taux professionnel en pourcentage',
    `besoins_adaptation` TEXT DEFAULT NULL
        COMMENT 'Description des besoins d''adaptation au poste',
    `demande_reconnaissance_atmp_en_cours` TINYINT(1) DEFAULT 0
        COMMENT '1 si demande de reconnaissance AT/MP en cours',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_medical_operateur` (`operateur_id`),
    CONSTRAINT `fk_medical_operateur` FOREIGN KEY (`operateur_id`)
        REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Table historique des visites médicales (VIP)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Table historique des reconnaissances MP (Maladie Professionnelle)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Table historique des accidents du travail (AT)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Table des prolongations d'arrêt
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

SELECT 'Migration 007 (medical) appliquée' AS status;

-- ============================================================
-- MIGRATION 008: Tables Vie du salarié
-- ============================================================

-- Table des sanctions disciplinaires
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Table des contrôles d'alcoolémie
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Table des tests salivaires (stupéfiants)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Table des entretiens professionnels (EPP, EAP)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

SELECT 'Migration 008 (vie_salarie) appliquée' AS status;

-- ============================================================
-- VUES UTILES
-- ============================================================

-- Vue pour l'ancienneté par contrat
DROP VIEW IF EXISTS `v_contrat_anciennete`;
CREATE VIEW `v_contrat_anciennete` AS
SELECT
    c.id,
    c.operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    c.type_contrat,
    c.date_debut,
    c.date_fin,
    c.date_sortie,
    c.actif,
    ROUND(
        DATEDIFF(
            COALESCE(c.date_sortie, CURDATE()),
            c.date_debut
        ) / 365.25,
        2
    ) AS anciennete_annees,
    CONCAT(
        TIMESTAMPDIFF(YEAR, c.date_debut, COALESCE(c.date_sortie, CURDATE())),
        ' ans ',
        MOD(TIMESTAMPDIFF(MONTH, c.date_debut, COALESCE(c.date_sortie, CURDATE())), 12),
        ' mois'
    ) AS anciennete_detail,
    CASE
        WHEN c.type_contrat IN ('CDD', 'Intérimaire', 'Stagiaire', 'Apprentissage')
             AND c.date_fin IS NOT NULL
             AND c.date_sortie IS NULL
        THEN DATEDIFF(c.date_fin, CURDATE())
        ELSE NULL
    END AS jours_restants
FROM contrat c
JOIN personnel p ON c.operateur_id = p.id;

-- Vue pour les contrats à fin proche
DROP VIEW IF EXISTS `v_contrats_fin_proche`;
CREATE VIEW `v_contrats_fin_proche` AS
SELECT
    c.id,
    c.operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    c.type_contrat,
    c.date_debut,
    c.date_fin,
    DATEDIFF(c.date_fin, CURDATE()) AS jours_restants,
    CASE
        WHEN DATEDIFF(c.date_fin, CURDATE()) < 0 THEN 'EXPIRE'
        WHEN DATEDIFF(c.date_fin, CURDATE()) <= 7 THEN 'URGENT'
        WHEN DATEDIFF(c.date_fin, CURDATE()) <= 30 THEN 'ATTENTION'
        ELSE 'OK'
    END AS statut_alerte
FROM contrat c
JOIN personnel p ON c.operateur_id = p.id
WHERE c.actif = 1
  AND c.date_fin IS NOT NULL
  AND c.date_sortie IS NULL
  AND DATEDIFF(c.date_fin, CURDATE()) <= 60
ORDER BY c.date_fin;

-- Vue récapitulative vie du salarié
DROP VIEW IF EXISTS `v_vie_salarie_recap`;
CREATE VIEW `v_vie_salarie_recap` AS
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.statut,
    (SELECT COUNT(*) FROM vie_salarie_sanction s WHERE s.operateur_id = p.id) AS nb_sanctions,
    (SELECT MAX(date_sanction) FROM vie_salarie_sanction s WHERE s.operateur_id = p.id) AS derniere_sanction,
    (SELECT COUNT(*) FROM vie_salarie_alcoolemie a WHERE a.operateur_id = p.id) AS nb_controles_alcool,
    (SELECT COUNT(*) FROM vie_salarie_alcoolemie a WHERE a.operateur_id = p.id AND a.resultat = 'Positif') AS nb_positifs_alcool,
    (SELECT COUNT(*) FROM vie_salarie_test_salivaire t WHERE t.operateur_id = p.id) AS nb_tests_salivaires,
    (SELECT COUNT(*) FROM vie_salarie_test_salivaire t WHERE t.operateur_id = p.id AND t.resultat = 'Positif') AS nb_positifs_salivaire,
    (SELECT MAX(date_entretien) FROM vie_salarie_entretien e WHERE e.operateur_id = p.id AND e.type_entretien = 'EPP') AS dernier_epp,
    (SELECT MAX(date_entretien) FROM vie_salarie_entretien e WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP') AS dernier_eap,
    (SELECT prochaine_date FROM vie_salarie_entretien e
     WHERE e.operateur_id = p.id
     ORDER BY date_entretien DESC LIMIT 1) AS prochain_entretien
FROM personnel p;

SELECT 'Vues créées avec succès' AS status;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- FIN DU SCRIPT
-- ============================================================
SELECT '✅ Toutes les migrations SIRH ont été appliquées !' AS resultat;
