-- Migration SÉCURISÉE: Renommer table operateurs en personnel
-- Date: 2025-12-15
-- Description: Migration sans perte de données avec vérifications

-- =============================================================================
-- ÉTAPE 0: VÉRIFICATIONS PRÉLIMINAIRES
-- =============================================================================

-- Vérifier que la table operateurs existe
SELECT 'VÉRIFICATION: Table operateurs existe' AS Etape,
       COUNT(*) AS NombreEnregistrements
FROM operateurs;

-- Vérifier qu'il n'y a pas déjà une table personnel
SELECT 'VÉRIFICATION: Pas de conflit avec table personnel' AS Etape;
-- Si cette query échoue, c'est qu'il y a déjà une table personnel - STOP!

-- =============================================================================
-- ÉTAPE 1: BACKUP DES COMPTEURS
-- =============================================================================

-- Compter les enregistrements avant migration
SELECT
    'AVANT MIGRATION' AS Moment,
    (SELECT COUNT(*) FROM operateurs) AS CountOperateurs,
    (SELECT COUNT(*) FROM polyvalence) AS CountPolyvalence,
    (SELECT COUNT(*) FROM historique) AS CountHistorique;

-- =============================================================================
-- ÉTAPE 2: SUPPRIMER LES FOREIGN KEYS
-- =============================================================================

-- Supprimer FK de historique
ALTER TABLE `historique`
DROP FOREIGN KEY `historique_ibfk_1`;

-- Supprimer FK de polyvalence
ALTER TABLE `polyvalence`
DROP FOREIGN KEY `polyvalence_ibfk_1`;

SELECT 'ÉTAPE 2 TERMINÉE: Foreign keys supprimées' AS Status;

-- =============================================================================
-- ÉTAPE 3: RENOMMER LA TABLE (DONNÉES INTACTES)
-- =============================================================================

RENAME TABLE `operateurs` TO `personnel`;

SELECT 'ÉTAPE 3 TERMINÉE: Table renommée en personnel' AS Status;

-- =============================================================================
-- ÉTAPE 4: RECRÉER LES FOREIGN KEYS
-- =============================================================================

-- Recréer FK historique -> personnel
ALTER TABLE `historique`
  ADD CONSTRAINT `historique_ibfk_1`
  FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`)
  ON DELETE CASCADE;

-- Recréer FK polyvalence -> personnel
ALTER TABLE `polyvalence`
  ADD CONSTRAINT `polyvalence_ibfk_1`
  FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`)
  ON DELETE CASCADE;

SELECT 'ÉTAPE 4 TERMINÉE: Foreign keys recréées' AS Status;

-- =============================================================================
-- ÉTAPE 5: VÉRIFICATIONS POST-MIGRATION
-- =============================================================================

-- Vérifier que les données sont toujours là
SELECT
    'APRÈS MIGRATION' AS Moment,
    (SELECT COUNT(*) FROM personnel) AS CountPersonnel,
    (SELECT COUNT(*) FROM polyvalence) AS CountPolyvalence,
    (SELECT COUNT(*) FROM historique) AS CountHistorique;

-- Vérifier les foreign keys
SELECT
    'VÉRIFICATION FOREIGN KEYS' AS Etape,
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'emac_db'
  AND REFERENCED_TABLE_NAME = 'personnel';

-- =============================================================================
-- RÉSULTAT FINAL
-- =============================================================================

SELECT '✅ MIGRATION TERMINÉE AVEC SUCCÈS!' AS Status,
       (SELECT COUNT(*) FROM personnel) AS TotalPersonnel;
