-- Migration: Règles de déclenchement de documents pour le passage au niveau 1
-- Date: 2026-02-24
-- Description: Quand un opérateur est affecté ou revient au niveau 1 sur un poste,
--              proposer l'impression du document de formation spécifique à ce poste.
--              Niveau 1 = opérateur en apprentissage ou réinitialisé.

-- Lier les templates de contexte 'POSTE' à l'événement 'polyvalence.niveau_1_reached'
-- La condition JSON filtre sur le code poste pour n'afficher que le document du bon poste.
INSERT INTO document_event_rules
    (event_name, template_id, execution_mode, condition_json, priority, description)
SELECT
    'polyvalence.niveau_1_reached',
    id,
    'PROPOSED',
    JSON_OBJECT('postes', postes_associes),
    ordre_affichage,
    CONCAT('Document poste niveau 1: ', nom)
FROM documents_templates
WHERE contexte = 'POSTE'
  AND actif = TRUE
  AND postes_associes IS NOT NULL
ON DUPLICATE KEY UPDATE description = VALUES(description);
