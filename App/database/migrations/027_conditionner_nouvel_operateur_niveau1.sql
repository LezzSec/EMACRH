-- Migration: Conditionner les documents NOUVEL_OPERATEUR au premier passage niveau 1
-- Date: 2026-03-02
-- Description: Les documents "Consignes générales" et "Formation initiale" (contexte
--              NOUVEL_OPERATEUR) ne doivent être proposés que lors du PREMIER passage
--              au niveau 1 d'un opérateur (jamais eu de niveau 1 nulle part avant).
--              Pour un opérateur qui revient au niveau 1 (même poste ou autre poste),
--              seule la feuille d'évaluation de poste (contexte POSTE) est proposée.
--
-- Implémentation : ajout de la condition JSON {"is_premier_niveau_1": true} sur les
-- règles liant les templates NOUVEL_OPERATEUR à l'événement polyvalence.niveau_1_reached.
-- Le champ is_premier_niveau_1 est désormais injecté dans les données de l'événement
-- par evaluation_service.has_operateur_deja_eu_niveau_1().

UPDATE document_event_rules
SET condition_json = JSON_MERGE_PATCH(
    COALESCE(condition_json, '{}'),
    '{"is_premier_niveau_1": true}'
)
WHERE event_name = 'polyvalence.niveau_1_reached'
  AND template_id IN (
      SELECT id
      FROM documents_templates
      WHERE contexte = 'NOUVEL_OPERATEUR'
        AND actif = TRUE
  );
