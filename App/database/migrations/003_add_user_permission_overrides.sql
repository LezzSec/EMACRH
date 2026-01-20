-- Migration: Add user-level permission overrides
-- Date: 2026-01-20
-- Description: Permet des overrides de permissions par utilisateur (système puzzle)

-- Table pour les overrides de permissions par utilisateur
-- NULL = hérite du rôle, 0 = forcé désactivé, 1 = forcé activé
CREATE TABLE IF NOT EXISTS permissions_utilisateur (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    module VARCHAR(100) NOT NULL,
    lecture TINYINT(1) DEFAULT NULL COMMENT 'NULL=hérite du rôle, 0=refusé, 1=autorisé',
    ecriture TINYINT(1) DEFAULT NULL COMMENT 'NULL=hérite du rôle, 0=refusé, 1=autorisé',
    suppression TINYINT(1) DEFAULT NULL COMMENT 'NULL=hérite du rôle, 0=refusé, 1=autorisé',
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifie_par INT DEFAULT NULL COMMENT 'ID de l''admin qui a fait la modification',
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (modifie_par) REFERENCES utilisateurs(id) ON DELETE SET NULL,
    UNIQUE KEY unique_user_module (utilisateur_id, module),
    INDEX idx_utilisateur (utilisateur_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT = 'Overrides de permissions par utilisateur. Les valeurs NULL héritent du rôle.';

-- Note: La collation doit être utf8mb4_unicode_ci pour correspondre aux autres tables
