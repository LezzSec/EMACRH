-- ============================================================================
-- Migration 011: Ajout des tables pour le suivi des opérations en masse
-- Date: 2026-01-28
-- Description: Tables pour tracker les opérations batch (formations, absences,
--              visites médicales assignées à plusieurs employés)
-- ============================================================================

-- Table principale de suivi des opérations en masse
CREATE TABLE IF NOT EXISTS batch_operations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_type ENUM('ABSENCE', 'FORMATION', 'VISITE_MEDICALE', 'DOCUMENT') NOT NULL,
    description TEXT COMMENT 'Description de l''opération (ex: nom de la formation)',
    nb_personnel INT DEFAULT 0 COMMENT 'Nombre de personnel ciblé',
    nb_success INT DEFAULT 0 COMMENT 'Nombre de succès',
    nb_errors INT DEFAULT 0 COMMENT 'Nombre d''erreurs',
    created_by VARCHAR(100) COMMENT 'Utilisateur ayant lancé l''opération',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL COMMENT 'Date de fin de l''opération',
    status ENUM('EN_COURS', 'TERMINE', 'ERREUR', 'ANNULE') DEFAULT 'EN_COURS',

    INDEX idx_batch_status (status),
    INDEX idx_batch_type (operation_type),
    INDEX idx_batch_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Suivi des opérations en masse (assignation formations, absences, etc.)';

-- Table de détail par personnel pour chaque opération batch
CREATE TABLE IF NOT EXISTS batch_operation_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL COMMENT 'Référence vers batch_operations',
    personnel_id INT NOT NULL COMMENT 'Personnel concerné',
    status ENUM('SUCCES', 'ERREUR', 'IGNORE') DEFAULT 'SUCCES',
    error_message TEXT NULL COMMENT 'Message d''erreur si échec',
    record_id INT NULL COMMENT 'ID de l''enregistrement créé (formation_id, absence_id, etc.)',
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (batch_id) REFERENCES batch_operations(id) ON DELETE CASCADE,
    FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE,

    INDEX idx_detail_batch (batch_id),
    INDEX idx_detail_personnel (personnel_id),
    INDEX idx_detail_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Détails par personnel pour chaque opération batch';

-- ============================================================================
-- Ajout des features pour les permissions
-- ============================================================================

INSERT IGNORE INTO features (feature_key, description, module) VALUES
('rh.bulk_operations', 'Accès aux opérations en masse', 'RH'),
('rh.bulk_operations.formations', 'Assignation formations en masse', 'RH'),
('rh.bulk_operations.absences', 'Assignation absences en masse', 'RH'),
('rh.bulk_operations.medical', 'Assignation visites médicales en masse', 'RH');

-- Attribuer les features aux rôles admin et RH par défaut
INSERT IGNORE INTO role_features (role_id, feature_id, allowed)
SELECT r.id, f.id, TRUE
FROM roles r
CROSS JOIN features f
WHERE r.nom IN ('admin', 'administrateur', 'rh', 'responsable_rh')
  AND f.feature_key LIKE 'rh.bulk_operations%';

-- ============================================================================
-- Vue pour les statistiques des opérations batch
-- ============================================================================

CREATE OR REPLACE VIEW v_batch_operations_stats AS
SELECT
    bo.id,
    bo.operation_type,
    bo.description,
    bo.nb_personnel,
    bo.nb_success,
    bo.nb_errors,
    bo.created_by,
    bo.created_at,
    bo.completed_at,
    bo.status,
    TIMESTAMPDIFF(SECOND, bo.created_at, COALESCE(bo.completed_at, NOW())) as duration_seconds,
    ROUND(bo.nb_success * 100.0 / NULLIF(bo.nb_personnel, 0), 1) as success_rate
FROM batch_operations bo
ORDER BY bo.created_at DESC;
