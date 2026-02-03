-- Migration: Ajout des features pour les formations
-- Date: 2026-02-03
-- Description: Ajoute les permissions pour la gestion des formations

-- ============================================================================
-- Ajout des features formations au catalogue
-- ============================================================================

INSERT IGNORE INTO features (key_code, label, module, description, display_order) VALUES
('rh.formations.view', 'Voir Formations', 'RH', 'Consulter les formations du personnel', 40),
('rh.formations.edit', 'Gérer Formations', 'RH', 'Ajouter et modifier les formations', 41),
('rh.formations.delete', 'Supprimer Formations', 'RH', 'Supprimer des formations', 42);

-- ============================================================================
-- Attribuer au rôle Admin (ID=1) - toutes les nouvelles features
-- ============================================================================

INSERT IGNORE INTO role_features (role_id, feature_key) VALUES
(1, 'rh.formations.view'),
(1, 'rh.formations.edit'),
(1, 'rh.formations.delete');

-- ============================================================================
-- Attribuer au rôle gestion_rh (ID=3) - accès complet formations
-- ============================================================================

INSERT IGNORE INTO role_features (role_id, feature_key) VALUES
(3, 'rh.formations.view'),
(3, 'rh.formations.edit'),
(3, 'rh.formations.delete');

-- ============================================================================
-- Attribuer au rôle gestion_production (ID=2) - lecture seule
-- ============================================================================

INSERT IGNORE INTO role_features (role_id, feature_key) VALUES
(2, 'rh.formations.view');

-- ============================================================================
-- Commit
-- ============================================================================

COMMIT;
