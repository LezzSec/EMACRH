-- Migration pour ajouter le système de gestion des utilisateurs
-- Date: 2025-12-17
-- Description: Ajout des tables pour gérer les utilisateurs et leurs rôles

-- Table des rôles
CREATE TABLE IF NOT EXISTS `roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(50) NOT NULL UNIQUE,
  `description` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS `utilisateurs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL UNIQUE,
  `password_hash` varchar(255) NOT NULL,
  `nom` varchar(255) NOT NULL,
  `prenom` varchar(255) NOT NULL,
  `role_id` int NOT NULL,
  `actif` tinyint(1) DEFAULT 1,
  `date_creation` datetime DEFAULT CURRENT_TIMESTAMP,
  `derniere_connexion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `utilisateurs_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table des permissions
CREATE TABLE IF NOT EXISTS `permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_id` int NOT NULL,
  `module` varchar(100) NOT NULL,
  `lecture` tinyint(1) DEFAULT 1,
  `ecriture` tinyint(1) DEFAULT 0,
  `suppression` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `permissions_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table des logs de connexion
CREATE TABLE IF NOT EXISTS `logs_connexion` (
  `id` int NOT NULL AUTO_INCREMENT,
  `utilisateur_id` int NOT NULL,
  `date_connexion` datetime NOT NULL,
  `date_deconnexion` datetime DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `utilisateur_id` (`utilisateur_id`),
  CONSTRAINT `logs_connexion_ibfk_1` FOREIGN KEY (`utilisateur_id`) REFERENCES `utilisateurs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insertion des rôles de base
INSERT INTO `roles` (`nom`, `description`) VALUES
('admin', 'Administrateur - Accès complet à toutes les fonctionnalités'),
('gestion_production', 'Gestion Production - Accès aux évaluations et polyvalence (lecture seule sur les contrats)'),
('gestion_rh', 'Gestion RH - Accès aux contrats et documents administratifs (lecture seule sur la polyvalence)');

-- Configuration des permissions pour le rôle admin
INSERT INTO `permissions` (`role_id`, `module`, `lecture`, `ecriture`, `suppression`) VALUES
(1, 'personnel', 1, 1, 1),
(1, 'evaluations', 1, 1, 1),
(1, 'polyvalence', 1, 1, 1),
(1, 'contrats', 1, 1, 1),
(1, 'documents_rh', 1, 1, 1),
(1, 'planning', 1, 1, 1),
(1, 'postes', 1, 1, 1),
(1, 'historique', 1, 1, 1),
(1, 'grilles', 1, 1, 1),
(1, 'gestion_utilisateurs', 1, 1, 1);

-- Configuration des permissions pour le rôle gestion_production
INSERT INTO `permissions` (`role_id`, `module`, `lecture`, `ecriture`, `suppression`) VALUES
(2, 'personnel', 1, 1, 1),
(2, 'evaluations', 1, 1, 1),
(2, 'polyvalence', 1, 1, 1),
(2, 'contrats', 1, 0, 0),  -- Lecture seule pour les contrats
(2, 'documents_rh', 0, 0, 0),  -- Pas d'accès aux documents RH
(2, 'planning', 1, 0, 0),  -- Lecture seule sur le planning (pas d'intervention sur absences)
(2, 'postes', 1, 1, 1),
(2, 'historique', 1, 0, 0),  -- Lecture seule
(2, 'grilles', 1, 1, 1),
(2, 'gestion_utilisateurs', 0, 0, 0);

-- Configuration des permissions pour le rôle gestion_rh
INSERT INTO `permissions` (`role_id`, `module`, `lecture`, `ecriture`, `suppression`) VALUES
(3, 'personnel', 1, 1, 1),  -- Accès complet pour ajouter et gérer les employés
(3, 'evaluations', 0, 0, 0),  -- Pas d'accès
(3, 'polyvalence', 1, 0, 0),  -- Lecture seule, pas d'intervention
(3, 'contrats', 1, 1, 1),  -- Accès complet
(3, 'documents_rh', 1, 1, 1),  -- Accès complet
(3, 'planning', 0, 0, 0),  -- Pas d'accès
(3, 'postes', 1, 0, 0),  -- Lecture seule
(3, 'historique', 1, 0, 0),  -- Lecture seule
(3, 'grilles', 0, 0, 0),  -- Pas d'accès (pas nécessaire pour gestion RH)
(3, 'gestion_utilisateurs', 0, 0, 0);

-- Création d'un utilisateur admin par défaut
-- Mot de passe par défaut: "admin123" (à changer lors de la première connexion)
-- Hash généré avec bcrypt
INSERT INTO `utilisateurs` (`username`, `password_hash`, `nom`, `prenom`, `role_id`, `actif`) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5yrOvnN6G/mFa', 'Administrateur', 'Système', 1, 1);

COMMIT;
