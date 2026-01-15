-- Migration: Ajout du lien document pour les attestations de formation
-- Date: 2026-01-14

-- Ajouter la colonne document_id pour lier une attestation/certificat
ALTER TABLE formation
ADD COLUMN IF NOT EXISTS document_id INT DEFAULT NULL,
ADD CONSTRAINT fk_formation_document
    FOREIGN KEY (document_id) REFERENCES documents(id)
    ON DELETE SET NULL;

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_formation_document ON formation(document_id);
