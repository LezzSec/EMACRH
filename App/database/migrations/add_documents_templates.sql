-- Migration: Création de la table documents_templates
-- Date: 2026-01-15
-- Description: Système de gestion des documents modèles (templates) pour les opérateurs

-- Table des templates de documents
CREATE TABLE IF NOT EXISTS documents_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(255) NOT NULL COMMENT 'Nom affiché du document',
    fichier_source VARCHAR(500) NOT NULL COMMENT 'Chemin relatif vers le fichier template',
    contexte ENUM('NOUVEL_OPERATEUR', 'NIVEAU_3', 'POSTE') NOT NULL COMMENT 'Contexte de déclenchement',
    postes_associes JSON DEFAULT NULL COMMENT 'Liste des codes postes associés (pour contexte POSTE)',
    champ_operateur VARCHAR(10) DEFAULT NULL COMMENT 'Cellule Excel pour le nom opérateur (ex: D7)',
    champ_auditeur VARCHAR(10) DEFAULT NULL COMMENT 'Cellule Excel pour le nom auditeur (ex: J7)',
    champ_date VARCHAR(10) DEFAULT NULL COMMENT 'Cellule Excel pour la date',
    obligatoire BOOLEAN DEFAULT FALSE COMMENT 'Document obligatoire pour ce contexte',
    description TEXT DEFAULT NULL COMMENT 'Description du document',
    ordre_affichage INT DEFAULT 0 COMMENT 'Ordre d affichage dans les listes',
    actif BOOLEAN DEFAULT TRUE COMMENT 'Template actif ou désactivé',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_contexte (contexte),
    INDEX idx_actif (actif)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertion des templates existants

-- 1. Documents pour NOUVEL_OPERATEUR
INSERT INTO documents_templates (nom, fichier_source, contexte, postes_associes, champ_operateur, champ_auditeur, obligatoire, ordre_affichage, description) VALUES
('Consignes générales', 'templates/Consignes generales.xlsm', 'NOUVEL_OPERATEUR', NULL, 'D7', 'J7', TRUE, 1, 'Document de consignes générales de sécurité et règles de l''entreprise'),
('Formation initiale - Activité mélangeage', 'templates/EQ 07 02 12 rev3 Formation initiale_activite melangeage.xls', 'NOUVEL_OPERATEUR', NULL, 'D7', 'J7', TRUE, 2, 'Formulaire de formation initiale pour tous les nouveaux opérateurs');

-- 2. Documents pour NIVEAU_3
INSERT INTO documents_templates (nom, fichier_source, contexte, postes_associes, champ_operateur, champ_auditeur, obligatoire, ordre_affichage, description) VALUES
('Questionnaire Qualité EMAC', 'templates/EQ 07 02 16 rev1 Questionnaire Qualite EMAC.docx', 'NIVEAU_3', NULL, NULL, NULL, TRUE, 1, 'Questionnaire qualité pour les opérateurs passant au niveau 3');

-- 3. Documents par POSTE
INSERT INTO documents_templates (nom, fichier_source, contexte, postes_associes, champ_operateur, champ_auditeur, obligatoire, ordre_affichage, description) VALUES
('Mélangeur Interne', 'templates/Melangeur Interne 506-923-1401-1101-907-901.xlsm', 'POSTE', '["506", "923", "1401", "1101", "907", "901"]', 'C7', 'I7', TRUE, 1, 'Formation poste mélangeur interne'),
('Mélangeur à cylindre', 'templates/Melangeur a cylindre 507-509-510-1402-1404-940-924-902-920.xlsm', 'POSTE', '["507", "509", "510", "1402", "1404", "940", "924", "902", "920"]', 'C7', 'I7', TRUE, 2, 'Formation poste mélangeur à cylindre'),
('Extrusion à chaud', 'templates/Extrusion a chaud 515.xlsm', 'POSTE', '["515"]', 'C7', 'I7', TRUE, 3, 'Formation poste extrusion à chaud'),
('Extrusion - Pompe à engrenage', 'templates/Extrusion -Pompe a engrenage 830-516-912-930.xlsm', 'POSTE', '["830", "516", "912", "930"]', 'C7', 'I7', TRUE, 4, 'Formation poste extrusion pompe à engrenage'),
('Granulatrice - Broyeur', 'templates/Granulatrice - Broyeur 526-560-511-1121-1103.xlsm', 'POSTE', '["526", "560", "511", "1121", "1103"]', 'C7', 'I7', TRUE, 5, 'Formation poste granulatrice et broyeur'),
('Conditionnement', 'templates/Conditionnement 514-1406-942-1405.xlsm', 'POSTE', '["514", "1406", "942", "1405"]', 'C7', 'I7', TRUE, 6, 'Formation poste conditionnement'),
('Calandre 3 cylindres', 'templates/Calandre 3 cylindres 903-941.xlsm', 'POSTE', '["903", "941"]', 'C7', 'I7', TRUE, 7, 'Formation poste calandre 3 cylindres'),
('Préparation - Pesée', 'templates/Preparation -Pesee 900-1412-910-1100.xlsm', 'POSTE', '["900", "1412", "910", "1100"]', 'C7', 'I7', TRUE, 8, 'Formation poste préparation et pesée'),
('Refroidisseur, Découpe, Bobinage', 'templates/Refroidisseur, Decoupe, Bobinage 904-905-906.xlsm', 'POSTE', '["904", "905", "906"]', 'C7', 'I7', TRUE, 9, 'Formation poste refroidisseur, découpe et bobinage'),
('Moulage', 'templates/Moulage.xlsm', 'POSTE', '["1007"]', 'C7', 'I7', TRUE, 10, 'Formation poste moulage'),
('Ponceuse - Découpe', 'templates/Ponceuse -Decoupe.xlsm', 'POSTE', '["1007"]', 'C7', 'I7', TRUE, 11, 'Formation poste ponceuse et découpe'),
('Contrôleur délégué', 'templates/Controleur delegue.xlsm', 'POSTE', '["1007"]', 'C7', 'I7', TRUE, 12, 'Formation contrôleur délégué');
