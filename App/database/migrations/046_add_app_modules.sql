-- Migration 046 : Table app_modules
-- Permet à l'administrateur d'activer/désactiver les modules de navigation
-- depuis le panel Administration > Modules de l'application
--
-- NOTE : Appliquer via mysql CLI ou un script Python qui commit explicitement.
--   mysql -u root -p emac_db < 046_add_app_modules.sql

CREATE TABLE IF NOT EXISTS app_modules (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    code         VARCHAR(50)  NOT NULL UNIQUE,
    label        VARCHAR(100) NOT NULL,
    description  TEXT,
    is_enabled   BOOLEAN      NOT NULL DEFAULT TRUE,
    display_order INT         NOT NULL DEFAULT 0,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_enabled (is_enabled),
    INDEX idx_order   (display_order)
);

INSERT IGNORE INTO app_modules (code, label, description, is_enabled, display_order) VALUES
('rh',          'Ressources Humaines',   'Gestion des contrats, alertes RH et ajout de personnel',                          TRUE, 10),
('production',  'Production',            'Grilles de polyvalence, évaluations des opérateurs et gestion des postes',        TRUE, 20),
('planning',    'Planning',              'Gestion des absences, congés et plannings',                                       TRUE, 30),
('documents',   'Documents',             'Gestion documentaire, modèles et archivage des documents RH',                     TRUE, 40),
('historique',  'Historique',            'Journal d\'audit des actions et logs de connexion',                                TRUE, 50);
