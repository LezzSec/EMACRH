-- Migration : Ajouter colonnes manquantes à la table historique
-- Date : 2025-12-03
-- Description : Ajoute les colonnes table_name, record_id, details, source, utilisateur

USE emac_db;

-- Vérifier et ajouter table_name
ALTER TABLE historique
ADD COLUMN IF NOT EXISTS table_name VARCHAR(100) DEFAULT NULL AFTER action;

-- Vérifier et ajouter record_id
ALTER TABLE historique
ADD COLUMN IF NOT EXISTS record_id VARCHAR(50) DEFAULT NULL AFTER table_name;

-- Vérifier et ajouter utilisateur
ALTER TABLE historique
ADD COLUMN IF NOT EXISTS utilisateur VARCHAR(100) DEFAULT NULL AFTER record_id;

-- Vérifier et ajouter details (pour JSON complémentaire)
ALTER TABLE historique
ADD COLUMN IF NOT EXISTS details TEXT DEFAULT NULL AFTER description;

-- Vérifier et ajouter source
ALTER TABLE historique
ADD COLUMN IF NOT EXISTS source VARCHAR(255) DEFAULT NULL AFTER details;

-- Ajouter index pour performances
CREATE INDEX IF NOT EXISTS idx_table_name ON historique(table_name);
CREATE INDEX IF NOT EXISTS idx_source ON historique(source);

-- Afficher la nouvelle structure
DESCRIBE historique;
