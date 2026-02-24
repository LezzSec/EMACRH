-- Migration: Règles de déclenchement de documents pour les évaluations à planifier
-- Date: 2026-02-24
-- Description: Quand l'évaluation d'un opérateur est à planifier (prochaine_evaluation
--              dans le futur proche), proposer le document de formation du poste concerné.
--              Même logique que evaluation.overdue mais pour les évaluations à venir.

-- Lier les templates de contexte 'POSTE' à l'événement 'evaluation.planned'
-- La condition JSON filtre sur le code poste pour n'afficher que le document du bon poste.
INSERT INTO document_event_rules
    (event_name, template_id, execution_mode, condition_json, priority, description)
SELECT
    'evaluation.planned',
    id,
    'PROPOSED',
    JSON_OBJECT('postes', postes_associes),
    ordre_affichage,
    CONCAT('Document poste évaluation à planifier: ', nom)
FROM documents_templates
WHERE contexte = 'POSTE'
  AND actif = TRUE
  AND postes_associes IS NOT NULL
ON DUPLICATE KEY UPDATE description = VALUES(description);
