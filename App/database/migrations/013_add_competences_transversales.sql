-- Migration: Système de compétences transversales
-- Date: 2026-02-02
-- Description: Ajout des tables pour gérer les compétences transversales et leurs assignations au personnel

-- ============================================================
-- Table competences_catalogue: Catalogue des compétences
-- ============================================================
CREATE TABLE IF NOT EXISTS `competences_catalogue` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) NOT NULL COMMENT 'Code unique de la compétence',
  `libelle` varchar(255) NOT NULL COMMENT 'Libellé affiché',
  `description` text DEFAULT NULL,
  `categorie` varchar(100) DEFAULT NULL COMMENT 'Ex: Managérial, Sécurité, Technique, Habilitation',
  `duree_validite_mois` int DEFAULT NULL COMMENT 'Durée de validité en mois (NULL = permanent)',
  `actif` tinyint(1) DEFAULT 1,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_competence_code` (`code`),
  KEY `idx_competence_categorie` (`categorie`),
  KEY `idx_competence_actif` (`actif`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
COMMENT = 'Catalogue des compétences transversales disponibles';

-- ============================================================
-- Table personnel_competences: Assignation compétences au personnel
-- ============================================================
CREATE TABLE IF NOT EXISTS `personnel_competences` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `competence_id` int NOT NULL,
  `date_acquisition` date NOT NULL COMMENT 'Date d''acquisition de la compétence',
  `date_expiration` date DEFAULT NULL COMMENT 'Date d''expiration (NULL = permanent)',
  `commentaire` text DEFAULT NULL,
  `document_id` int DEFAULT NULL COMMENT 'Certificat ou attestation liée',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personnel_competence` (`personnel_id`, `competence_id`),
  KEY `idx_pc_personnel_id` (`personnel_id`),
  KEY `idx_pc_competence_id` (`competence_id`),
  KEY `idx_pc_date_expiration` (`date_expiration`),
  CONSTRAINT `fk_pc_personnel` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pc_competence` FOREIGN KEY (`competence_id`) REFERENCES `competences_catalogue` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
COMMENT = 'Compétences assignées au personnel avec dates';

-- Note: La contrainte fk_pc_document sur documents sera ajoutée seulement si la table documents existe
-- ALTER TABLE `personnel_competences` ADD CONSTRAINT `fk_pc_document` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE SET NULL;

-- ============================================================
-- Données initiales: Compétences exemple
-- ============================================================
INSERT IGNORE INTO `competences_catalogue` (`code`, `libelle`, `categorie`, `duree_validite_mois`, `description`) VALUES
-- Compétences managériales (permanentes)
('MGT_LEADER', 'Leadership d''équipe', 'Managérial', NULL, 'Compétence de leadership et gestion d''équipe'),
('MGT_EVAL', 'Conduite d''entretiens', 'Managérial', NULL, 'Capacité à mener des entretiens d''évaluation'),
('MGT_FORM', 'Tuteur/Formateur', 'Managérial', NULL, 'Capacité à former et accompagner les nouveaux'),

-- Compétences sécurité (avec validité)
('SEC_INCENDIE', 'Équipier de première intervention', 'Sécurité', 24, 'Formation EPI - lutte contre l''incendie'),
('SEC_SST', 'Sauveteur Secouriste du Travail', 'Sécurité', 24, 'Formation SST - premiers secours'),
('SEC_EVACUATION', 'Guide d''évacuation', 'Sécurité', 24, 'Formation guide et serre-file évacuation'),

-- Habilitations (avec validité)
('HAB_ELEC_B0', 'Habilitation électrique B0', 'Habilitation', 36, 'Habilitation travaux non électriques BT'),
('HAB_ELEC_B1', 'Habilitation électrique B1', 'Habilitation', 36, 'Habilitation exécutant BT'),
('HAB_ELEC_B2', 'Habilitation électrique B2', 'Habilitation', 36, 'Habilitation chargé de travaux BT'),
('HAB_CACES_1', 'CACES R489 cat. 1', 'Habilitation', 60, 'Chariot transpalettes à conducteur porté'),
('HAB_CACES_3', 'CACES R489 cat. 3', 'Habilitation', 60, 'Chariot élévateur frontal'),
('HAB_CACES_5', 'CACES R489 cat. 5', 'Habilitation', 60, 'Chariot élévateur à mât rétractable'),
('HAB_PONT', 'Autorisation pont roulant', 'Habilitation', 60, 'Autorisation conduite pont roulant'),

-- Compétences techniques (permanentes)
('TECH_QUAL', 'Contrôle qualité', 'Technique', NULL, 'Compétence en contrôle qualité produit'),
('TECH_MAINT', 'Maintenance niveau 1', 'Technique', NULL, 'Compétence maintenance premier niveau');

-- ============================================================
-- Features (permissions) pour le système de compétences
-- ============================================================
INSERT IGNORE INTO `features` (`key_code`, `label`, `module`) VALUES
('rh.competences.view', 'Voir les compétences du personnel', 'RH'),
('rh.competences.edit', 'Assigner/modifier les compétences', 'RH'),
('rh.competences.delete', 'Retirer les compétences', 'RH'),
('rh.competences.catalogue', 'Gérer le catalogue de compétences', 'RH');

-- Assigner les features aux rôles existants (admin et rh)
INSERT IGNORE INTO `role_features` (`role_id`, `feature_key`)
SELECT r.id, 'rh.competences.view' FROM roles r WHERE r.nom IN ('admin', 'rh', 'manager');

INSERT IGNORE INTO `role_features` (`role_id`, `feature_key`)
SELECT r.id, 'rh.competences.edit' FROM roles r WHERE r.nom IN ('admin', 'rh');

INSERT IGNORE INTO `role_features` (`role_id`, `feature_key`)
SELECT r.id, 'rh.competences.delete' FROM roles r WHERE r.nom IN ('admin', 'rh');

INSERT IGNORE INTO `role_features` (`role_id`, `feature_key`)
SELECT r.id, 'rh.competences.catalogue' FROM roles r WHERE r.nom = 'admin';
