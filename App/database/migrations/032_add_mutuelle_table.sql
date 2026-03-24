-- Migration 032: Ajout de la table mutuelle
-- Gestion de la complémentaire santé (mutuelle) des salariés

CREATE TABLE IF NOT EXISTS mutuelle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personnel_id INT NOT NULL,
    statut_adhesion ENUM('ADHERENT', 'DISPENSE', 'EN_ATTENTE', 'NON_COUVERT') NOT NULL DEFAULT 'NON_COUVERT',
    due_signee BOOLEAN NOT NULL DEFAULT FALSE,
    type_formule ENUM('SIMPLE', 'TURBO') NULL,
    situation_familiale ENUM('ISOLE', 'DUO', 'FAMILLE') NULL,
    type_dispense VARCHAR(100) NULL COMMENT 'CDD, temps_partiel, ayant_droit, autre',
    justificatif_validite DATE NULL COMMENT 'Date de validite du justificatif de dispense (renouvellement annuel)',
    organisme VARCHAR(150) NULL,
    numero_adherent VARCHAR(50) NULL,
    date_adhesion DATE NULL,
    date_fin DATE NULL,
    commentaire TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_mutuelle_personnel FOREIGN KEY (personnel_id)
        REFERENCES personnel(id) ON DELETE CASCADE,
    INDEX idx_mutuelle_personnel (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Catégorie de documents pour le domaine Mutuelle
INSERT IGNORE INTO `categories_documents`
    (`nom`, `description`, `couleur`, `exige_date_expiration`, `ordre_affichage`)
VALUES
    ('Documents mutuelle', 'Attestations, dispenses, justificatifs de complémentaire santé', '#0891b2', 0, 15);
