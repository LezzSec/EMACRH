-- Migration: Ajout des tables RH (personnel_infos, contrat, declaration, formation)
-- Date: 2026-01-19

-- ============================================================
-- Table personnel_infos: Informations personnelles des opérateurs
-- ============================================================
CREATE TABLE IF NOT EXISTS `personnel_infos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `sexe` ENUM('M', 'F') DEFAULT NULL,
  `date_naissance` date DEFAULT NULL,
  `date_entree` date DEFAULT NULL,
  `nationalite` varchar(100) DEFAULT NULL,
  `adresse1` varchar(255) DEFAULT NULL,
  `adresse2` varchar(255) DEFAULT NULL,
  `cp_adresse` varchar(10) DEFAULT NULL,
  `ville_adresse` varchar(100) DEFAULT NULL,
  `pays_adresse` varchar(100) DEFAULT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `ville_naissance` varchar(100) DEFAULT NULL,
  `pays_naissance` varchar(100) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_operateur` (`operateur_id`),
  CONSTRAINT `fk_personnel_infos_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Table contrat: Contrats des opérateurs
-- ============================================================
CREATE TABLE IF NOT EXISTS `contrat` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `type_contrat` varchar(50) NOT NULL COMMENT 'CDI, CDD, Intérim, Apprentissage, etc.',
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL COMMENT 'NULL pour CDI',
  `etp` decimal(3,2) DEFAULT 1.00 COMMENT 'Équivalent Temps Plein (0.00 à 1.00)',
  `categorie` varchar(50) DEFAULT NULL,
  `echelon` varchar(50) DEFAULT NULL,
  `emploi` varchar(255) DEFAULT NULL,
  `salaire` decimal(10,2) DEFAULT NULL,
  `actif` tinyint(1) DEFAULT 1,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_contrat_operateur` (`operateur_id`),
  KEY `idx_contrat_dates` (`date_debut`, `date_fin`),
  KEY `idx_contrat_actif` (`actif`),
  CONSTRAINT `fk_contrat_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Table declaration: Déclarations (arrêts maladie, congés, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS `declaration` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `type_declaration` varchar(50) NOT NULL COMMENT 'Arrêt maladie, Congé payé, RTT, etc.',
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `commentaire` text DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_declaration_operateur` (`operateur_id`),
  KEY `idx_declaration_dates` (`date_debut`, `date_fin`),
  KEY `idx_declaration_type` (`type_declaration`),
  CONSTRAINT `fk_declaration_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Table formation: Formations suivies par les opérateurs
-- ============================================================
CREATE TABLE IF NOT EXISTS `formation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `intitule` varchar(255) NOT NULL COMMENT 'Nom de la formation',
  `organisme` varchar(255) DEFAULT NULL COMMENT 'Organisme formateur',
  `date_debut` date DEFAULT NULL,
  `date_fin` date DEFAULT NULL,
  `duree_heures` int DEFAULT NULL COMMENT 'Durée en heures',
  `statut` ENUM('Planifiée', 'En cours', 'Terminée', 'Annulée') DEFAULT 'Planifiée',
  `certificat_obtenu` tinyint(1) DEFAULT 0,
  `commentaire` text DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_formation_operateur` (`operateur_id`),
  KEY `idx_formation_statut` (`statut`),
  KEY `idx_formation_dates` (`date_debut`, `date_fin`),
  CONSTRAINT `fk_formation_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
