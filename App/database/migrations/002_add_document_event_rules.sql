-- Migration: Création de la table document_event_rules
-- Date: 2026-01-27
-- Description: Système de règles pour le déclenchement automatique de documents
--              basé sur des événements métier (personnel.created, contrat.renewed, etc.)

-- Table des règles événement -> document
CREATE TABLE IF NOT EXISTS document_event_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(100) NOT NULL COMMENT 'Nom de l''événement (ex: personnel.created, contrat.renewed)',
    template_id INT NOT NULL COMMENT 'FK vers documents_templates',
    execution_mode ENUM('AUTO', 'PROPOSED', 'SILENT') DEFAULT 'PROPOSED'
        COMMENT 'AUTO=génère automatiquement, PROPOSED=affiche dialog, SILENT=log seulement',
    condition_json JSON DEFAULT NULL
        COMMENT 'Conditions additionnelles en JSON (ex: {"niveau": 3})',
    priority INT DEFAULT 0 COMMENT 'Ordre de traitement (0 = premier)',
    actif BOOLEAN DEFAULT TRUE COMMENT 'Règle active ou désactivée',
    description TEXT DEFAULT NULL COMMENT 'Description de la règle',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (template_id) REFERENCES documents_templates(id) ON DELETE CASCADE,
    INDEX idx_event_name (event_name),
    INDEX idx_actif (actif),
    UNIQUE KEY uk_event_template (event_name, template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Règles initiales basées sur le contexte existant dans documents_templates
-- ============================================================================

-- 1. Événement: personnel.created (Nouvel opérateur)
-- Lie les templates avec contexte='NOUVEL_OPERATEUR' à l'événement personnel.created
INSERT INTO document_event_rules (event_name, template_id, execution_mode, priority, description)
SELECT
    'personnel.created',
    id,
    'PROPOSED',
    ordre_affichage,
    CONCAT('Document pour nouvel opérateur: ', nom)
FROM documents_templates
WHERE contexte = 'NOUVEL_OPERATEUR' AND actif = TRUE
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- 2. Événement: polyvalence.niveau_3_reached (Passage au niveau 3)
-- Lie les templates avec contexte='NIVEAU_3' à l'événement polyvalence.niveau_3_reached
INSERT INTO document_event_rules (event_name, template_id, execution_mode, condition_json, priority, description)
SELECT
    'polyvalence.niveau_3_reached',
    id,
    'PROPOSED',
    '{"niveau": 3}',
    ordre_affichage,
    CONCAT('Questionnaire niveau 3: ', nom)
FROM documents_templates
WHERE contexte = 'NIVEAU_3' AND actif = TRUE
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- 3. Événement: polyvalence.created (Affectation à un poste)
-- Pour les templates liés à des postes spécifiques
-- Note: la condition JSON contient les codes postes pour filtrage dynamique
INSERT INTO document_event_rules (event_name, template_id, execution_mode, condition_json, priority, description)
SELECT
    'polyvalence.created',
    id,
    'PROPOSED',
    JSON_OBJECT('postes', postes_associes),
    ordre_affichage,
    CONCAT('Formation poste: ', nom)
FROM documents_templates
WHERE contexte = 'POSTE' AND actif = TRUE AND postes_associes IS NOT NULL
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- ============================================================================
-- Vue pour faciliter les requêtes (optionnel mais utile)
-- ============================================================================

CREATE OR REPLACE VIEW v_document_rules_with_templates AS
SELECT
    r.id as rule_id,
    r.event_name,
    r.execution_mode,
    r.condition_json,
    r.priority,
    r.actif as rule_actif,
    t.id as template_id,
    t.nom as template_nom,
    t.fichier_source,
    t.contexte,
    t.postes_associes,
    t.champ_operateur,
    t.champ_auditeur,
    t.champ_date,
    t.obligatoire,
    t.description as template_description
FROM document_event_rules r
JOIN documents_templates t ON r.template_id = t.id
WHERE r.actif = TRUE AND t.actif = TRUE
ORDER BY r.event_name, r.priority;
