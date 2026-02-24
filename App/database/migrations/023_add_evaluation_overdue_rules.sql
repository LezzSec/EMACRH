-- Migration: Règles de déclenchement de documents pour les évaluations en retard
-- Date: 2026-02-24
-- Description: Quand l'évaluation d'un opérateur est en retard sur un poste,
--              proposer l'impression du document de formation spécifique à ce poste.
--              Cible les opérateurs (niveau 1 notamment) dont l'évaluation est en retard
--              et qui n'ont pas de document déclenché par niveau_2_reached / niveau_3_reached.

-- Lier les templates de contexte 'POSTE' à l'événement 'evaluation.overdue'
-- La condition JSON filtre sur le code poste pour n'afficher que le document du bon poste.
INSERT INTO document_event_rules
    (event_name, template_id, execution_mode, condition_json, priority, description)
SELECT
    'evaluation.overdue',
    id,
    'PROPOSED',
    JSON_OBJECT('postes', postes_associes),
    ordre_affichage,
    CONCAT('Document poste évaluation en retard: ', nom)
FROM documents_templates
WHERE contexte = 'POSTE'
  AND actif = TRUE
  AND postes_associes IS NOT NULL
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- Pour supprimer les règles NOUVEL_OPERATEUR ajoutées par erreur (si migration partielle exécutée)
DELETE r FROM document_event_rules r
JOIN documents_templates t ON r.template_id = t.id
WHERE r.event_name = 'evaluation.overdue'
  AND t.contexte = 'NOUVEL_OPERATEUR';
