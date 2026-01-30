-- Migration 012: Table pour logger les tentatives de connexion échouées
-- Date: 2026-01-30
-- Sécurité: Audit des tentatives de connexion

-- Table pour logger les tentatives de connexion échouées
CREATE TABLE IF NOT EXISTS logs_tentatives_connexion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL COMMENT 'Nom d''utilisateur tenté',
    ip_address VARCHAR(100) DEFAULT NULL COMMENT 'Adresse IP / hostname source',
    attempt_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(50) NOT NULL COMMENT 'Raison: user_not_found, wrong_password, account_inactive',
    INDEX idx_username (username),
    INDEX idx_attempt_time (attempt_time),
    INDEX idx_ip_address (ip_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Historique des tentatives de connexion échouées';
