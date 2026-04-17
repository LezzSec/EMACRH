-- Migration: Ajout du lien document pour les attestations de formation
-- Date: 2026-01-14

-- Ajouter la colonne document_id pour lier une attestation/certificat
ALTER TABLE formation
ADD COLUMN IF NOT EXISTS document_id INT DEFAULT NULL;

-- Ajouter la FK uniquement si elle n'existe pas déjà
-- (ADD CONSTRAINT n'a pas de IF NOT EXISTS en MariaDB/MySQL)
SET @fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = DATABASE()
      AND CONSTRAINT_NAME   = 'fk_formation_document'
      AND CONSTRAINT_TYPE   = 'FOREIGN KEY'
);

SET @sql = IF(
    @fk_exists = 0,
    'ALTER TABLE formation ADD CONSTRAINT fk_formation_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL',
    'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_formation_document ON formation(document_id);
