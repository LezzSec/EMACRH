-- Migration 045 : Feature permission pour la mobilite
-- Date : 2026-04-13

INSERT IGNORE INTO features (key_code, label, module, description, display_order) VALUES
('rh.mobilite.edit', 'Gérer Mobilité', 'RH', 'Saisir et modifier le véhicule et la distance domicile-entreprise', 53);

-- Admin (ID=1) et RH (ID=3)
INSERT IGNORE INTO role_features (role_id, feature_key) VALUES
(1, 'rh.mobilite.edit'),
(3, 'rh.mobilite.edit');
