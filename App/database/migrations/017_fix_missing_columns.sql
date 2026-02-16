-- Migration 017: Corrections de colonnes manquantes identifiées par audit code vs DB
-- Date: 2026-02-12
-- Description: Ajoute les colonnes 'details' et 'source' manquantes dans historique,
--              et crée la table logs_tentatives_connexion si absente.

USE emac_db;

-- ============================================================================
-- 1. Table historique : ajouter colonnes 'details' et 'source'
--    (table_name, record_id, utilisateur existent déjà dans la DB live)
-- ============================================================================

ALTER TABLE historique
ADD COLUMN IF NOT EXISTS details TEXT DEFAULT NULL
COMMENT 'Données JSON complémentaires' AFTER description;

ALTER TABLE historique
ADD COLUMN IF NOT EXISTS source VARCHAR(255) DEFAULT NULL
COMMENT 'Module source (ex: planning, GUI/gestion_evaluation)' AFTER details;

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_historique_source ON historique(source);

-- ============================================================================
-- 2. Table logs_tentatives_connexion (migration 012 non appliquée)
-- ============================================================================

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

-- ============================================================================
-- 3. Vérification
-- ============================================================================

-- Afficher les colonnes ajoutées
SELECT 'historique' as table_name, COLUMN_NAME, COLUMN_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'emac_db' AND TABLE_NAME = 'historique'
AND COLUMN_NAME IN ('details', 'source')
ORDER BY ORDINAL_POSITION;

SELECT 'logs_tentatives_connexion' as table_name, COUNT(*) as nb_columns
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'emac_db' AND TABLE_NAME = 'logs_tentatives_connexion';
