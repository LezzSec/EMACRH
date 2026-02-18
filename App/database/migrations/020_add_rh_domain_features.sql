-- ============================================================================
-- Migration 020: Ajout des features granulaires pour les domaines RH
-- Date: 2026-02-17
-- Description: Ajoute des features spécifiques pour déclarations, médical
--              et vie salarié afin de permettre un contrôle fin des permissions
--              (ex: gestion_production peut modifier le personnel mais pas
--              les contrats, déclarations, médical, etc.)
-- ============================================================================

-- Nouvelles features RH
INSERT IGNORE INTO features (key_code, label, module, description, display_order) VALUES
('rh.declarations.edit', 'Gérer Déclarations', 'RH', 'Créer et modifier les déclarations (absences, AT, etc.)', 50),
('rh.medical.edit', 'Gérer Médical', 'RH', 'Gérer visites médicales et accidents du travail', 51),
('rh.vie_salarie.edit', 'Gérer Vie salarié', 'RH', 'Gérer sanctions, contrôles alcool/salivaire, entretiens', 52);

-- Assigner au rôle Admin (ID=1)
INSERT IGNORE INTO role_features (role_id, feature_key) VALUES
(1, 'rh.declarations.edit'),
(1, 'rh.medical.edit'),
(1, 'rh.vie_salarie.edit');

-- Assigner au rôle RH (ID=3)
INSERT IGNORE INTO role_features (role_id, feature_key) VALUES
(3, 'rh.declarations.edit'),
(3, 'rh.medical.edit'),
(3, 'rh.vie_salarie.edit');

-- NOTE: Le rôle gestion_production (ID=2) ne reçoit PAS ces features
-- → gprod pourra modifier le personnel mais PAS les déclarations/médical/vie salarié
