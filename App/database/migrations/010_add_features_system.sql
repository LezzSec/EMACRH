-- Migration: Système de permissions par features
-- Date: 2026-01-27
-- Description: Nouveau système de permissions granulaire avec features atomiques

-- ============================================================================
-- TABLE: features (catalogue des permissions disponibles)
-- ============================================================================
CREATE TABLE IF NOT EXISTS features (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_code VARCHAR(100) NOT NULL UNIQUE COMMENT 'Clé unique ex: rh.personnel.edit',
    label VARCHAR(255) NOT NULL COMMENT 'Libellé affiché ex: Modifier Personnel',
    module VARCHAR(50) NOT NULL COMMENT 'Groupe/module ex: RH, Production, Admin',
    description TEXT COMMENT 'Description détaillée',
    display_order INT DEFAULT 0 COMMENT 'Ordre d''affichage dans l''UI',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Feature activée/désactivée globalement',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_module (module),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT = 'Catalogue des features/permissions disponibles dans l''application';

-- ============================================================================
-- TABLE: role_features (features assignées aux rôles)
-- ============================================================================
CREATE TABLE IF NOT EXISTS role_features (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL,
    feature_key VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY unique_role_feature (role_id, feature_key),
    INDEX idx_role (role_id),
    INDEX idx_feature (feature_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT = 'Features assignées à chaque rôle';

-- ============================================================================
-- TABLE: user_features (overrides par utilisateur)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_features (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    feature_key VARCHAR(100) NOT NULL,
    value BOOLEAN NOT NULL COMMENT 'TRUE=autorisé, FALSE=refusé (override du rôle)',
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifie_par INT DEFAULT NULL COMMENT 'Admin qui a fait la modification',
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (modifie_par) REFERENCES utilisateurs(id) ON DELETE SET NULL,
    UNIQUE KEY unique_user_feature (user_id, feature_key),
    INDEX idx_user (user_id),
    INDEX idx_feature (feature_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT = 'Overrides de permissions par utilisateur. Override > rôle.';

-- ============================================================================
-- SEED: Catalogue des features
-- ============================================================================

-- Module RH
INSERT INTO features (key_code, label, module, description, display_order) VALUES
('rh.view', 'Accès module RH', 'RH', 'Accès à l''onglet/menu RH', 10),
('rh.personnel.view', 'Voir Personnel', 'RH', 'Consulter la liste du personnel', 11),
('rh.personnel.create', 'Ajouter Personnel', 'RH', 'Créer un nouvel employé', 12),
('rh.personnel.edit', 'Modifier Personnel', 'RH', 'Modifier les informations d''un employé', 13),
('rh.personnel.delete', 'Supprimer Personnel', 'RH', 'Supprimer/désactiver un employé', 14),
('rh.contrats.view', 'Voir Contrats', 'RH', 'Consulter les contrats', 20),
('rh.contrats.edit', 'Modifier Contrats', 'RH', 'Créer et modifier les contrats', 21),
('rh.contrats.delete', 'Supprimer Contrats', 'RH', 'Supprimer des contrats', 22),
('rh.documents.view', 'Voir Documents RH', 'RH', 'Consulter les documents RH', 30),
('rh.documents.edit', 'Gérer Documents RH', 'RH', 'Ajouter/modifier des documents RH', 31),
('rh.documents.print', 'Imprimer Documents', 'RH', 'Générer et imprimer des documents', 32),
('rh.templates.view', 'Voir Templates', 'RH', 'Consulter les modèles de documents', 33),
('rh.templates.edit', 'Gérer Templates', 'RH', 'Créer/modifier des modèles de documents', 34);

-- Module Production
INSERT INTO features (key_code, label, module, description, display_order) VALUES
('production.view', 'Accès module Production', 'Production', 'Accès à l''onglet/menu Production', 100),
('production.evaluations.view', 'Voir Évaluations', 'Production', 'Consulter les évaluations', 110),
('production.evaluations.edit', 'Modifier Évaluations', 'Production', 'Planifier et modifier les évaluations', 111),
('production.polyvalence.view', 'Voir Polyvalence', 'Production', 'Consulter la matrice de polyvalence', 120),
('production.polyvalence.edit', 'Modifier Polyvalence', 'Production', 'Modifier les niveaux de compétence', 121),
('production.postes.view', 'Voir Postes', 'Production', 'Consulter la liste des postes', 130),
('production.postes.edit', 'Gérer Postes', 'Production', 'Créer/modifier/supprimer des postes', 131),
('production.grilles.view', 'Voir Grilles', 'Production', 'Consulter les grilles de compétences', 140),
('production.grilles.export', 'Exporter Grilles', 'Production', 'Exporter les grilles en Excel/PDF', 141);

-- Module Planning
INSERT INTO features (key_code, label, module, description, display_order) VALUES
('planning.view', 'Accès Planning', 'Planning', 'Voir le planning et les absences', 200),
('planning.absences.view', 'Voir Absences', 'Planning', 'Consulter les absences du personnel', 210),
('planning.absences.edit', 'Gérer Absences', 'Planning', 'Créer et modifier les absences', 211);

-- Module Admin
INSERT INTO features (key_code, label, module, description, display_order) VALUES
('admin.view', 'Accès Administration', 'Admin', 'Accès au menu administration', 300),
('admin.users.view', 'Voir Utilisateurs', 'Admin', 'Consulter la liste des utilisateurs', 310),
('admin.users.create', 'Créer Utilisateurs', 'Admin', 'Créer de nouveaux utilisateurs', 311),
('admin.users.edit', 'Modifier Utilisateurs', 'Admin', 'Modifier les utilisateurs existants', 312),
('admin.users.delete', 'Supprimer Utilisateurs', 'Admin', 'Supprimer des utilisateurs', 313),
('admin.permissions', 'Gérer Permissions', 'Admin', 'Accéder à l''éditeur de permissions', 320),
('admin.roles.edit', 'Gérer Rôles', 'Admin', 'Modifier les permissions des rôles', 321),
('admin.historique.view', 'Voir Historique', 'Admin', 'Consulter les logs d''activité', 330),
('admin.historique.export', 'Exporter Historique', 'Admin', 'Exporter les logs', 331);

-- ============================================================================
-- SEED: Features pour le rôle Admin (ID=1) - toutes les features
-- ============================================================================
INSERT INTO role_features (role_id, feature_key)
SELECT 1, key_code FROM features WHERE is_active = TRUE;

-- ============================================================================
-- SEED: Features pour le rôle gestion_production (ID=2)
-- ============================================================================
INSERT INTO role_features (role_id, feature_key) VALUES
-- RH (lecture seule)
(2, 'rh.view'),
(2, 'rh.personnel.view'),
(2, 'rh.contrats.view'),
-- Production (complet)
(2, 'production.view'),
(2, 'production.evaluations.view'),
(2, 'production.evaluations.edit'),
(2, 'production.polyvalence.view'),
(2, 'production.polyvalence.edit'),
(2, 'production.postes.view'),
(2, 'production.postes.edit'),
(2, 'production.grilles.view'),
(2, 'production.grilles.export'),
-- Planning (lecture)
(2, 'planning.view'),
(2, 'planning.absences.view');

-- ============================================================================
-- SEED: Features pour le rôle gestion_rh (ID=3)
-- ============================================================================
INSERT INTO role_features (role_id, feature_key) VALUES
-- RH (complet)
(3, 'rh.view'),
(3, 'rh.personnel.view'),
(3, 'rh.personnel.create'),
(3, 'rh.personnel.edit'),
(3, 'rh.personnel.delete'),
(3, 'rh.contrats.view'),
(3, 'rh.contrats.edit'),
(3, 'rh.contrats.delete'),
(3, 'rh.documents.view'),
(3, 'rh.documents.edit'),
(3, 'rh.documents.print'),
(3, 'rh.templates.view'),
(3, 'rh.templates.edit'),
-- Production (lecture seule)
(3, 'production.view'),
(3, 'production.polyvalence.view'),
(3, 'production.postes.view'),
(3, 'production.grilles.view'),
-- Planning (complet pour absences)
(3, 'planning.view'),
(3, 'planning.absences.view'),
(3, 'planning.absences.edit'),
-- Admin (historique lecture)
(3, 'admin.historique.view');

-- ============================================================================
-- Commit
-- ============================================================================
COMMIT;
