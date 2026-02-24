-- Migration: Ajout des documents "Nouvel opérateur" pour le passage au niveau 1
-- Date: 2026-02-24
-- Description: Quand un opérateur repasse au niveau 1 (remise à zéro ou régression),
--              proposer également les documents d'accueil/formation initiale
--              (identiques à ceux proposés lors de l'arrivée d'un nouvel opérateur).

-- Lier les templates NOUVEL_OPERATEUR à l'événement 'polyvalence.niveau_1_reached'
-- Ces documents (consignes générales, formation initiale) sont pertinents
-- pour tout opérateur revenant au niveau 1, quel que soit son poste.
INSERT INTO document_event_rules
    (event_name, template_id, execution_mode, priority, description)
SELECT
    'polyvalence.niveau_1_reached',
    id,
    'PROPOSED',
    ordre_affichage + 100,
    CONCAT('Document nouvel opérateur (retour niveau 1): ', nom)
FROM documents_templates
WHERE contexte = 'NOUVEL_OPERATEUR'
  AND actif = TRUE
ON DUPLICATE KEY UPDATE description = VALUES(description);
