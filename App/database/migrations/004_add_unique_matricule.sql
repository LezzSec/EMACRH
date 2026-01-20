-- ============================================================================
-- Migration 004: Ajout contrainte UNIQUE sur le matricule
-- ============================================================================
-- Cette migration ajoute une contrainte d'unicité sur le champ matricule
-- de la table personnel pour éviter les doublons.
--
-- IMPORTANT: Avant d'exécuter cette migration, vérifiez qu'il n'y a pas
-- de doublons existants avec la requête:
--   SELECT matricule, COUNT(*) as cnt
--   FROM personnel
--   WHERE matricule IS NOT NULL
--   GROUP BY matricule
--   HAVING cnt > 1;
-- ============================================================================

-- Vérifier les doublons existants (à exécuter manuellement d'abord)
-- SELECT matricule, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
-- FROM personnel
-- WHERE matricule IS NOT NULL
-- GROUP BY matricule
-- HAVING cnt > 1;

-- Ajouter l'index UNIQUE sur matricule (autorise les NULL multiples)
ALTER TABLE personnel
ADD UNIQUE INDEX idx_personnel_matricule_unique (matricule);

-- Vérification
-- SHOW INDEX FROM personnel WHERE Key_name = 'idx_personnel_matricule_unique';
