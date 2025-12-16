-- ROLLBACK: Revenir de personnel vers operateurs
-- À utiliser UNIQUEMENT si la migration a échoué
-- Date: 2025-12-15

-- =============================================================================
-- ATTENTION: Ce script fait l'opération INVERSE de la migration
-- =============================================================================

-- Supprimer les foreign keys
ALTER TABLE `historique` DROP FOREIGN KEY `historique_ibfk_1`;
ALTER TABLE `polyvalence` DROP FOREIGN KEY `polyvalence_ibfk_1`;

-- Renommer personnel -> operateurs
RENAME TABLE `personnel` TO `operateurs`;

-- Recréer les foreign keys vers operateurs
ALTER TABLE `historique`
  ADD CONSTRAINT `historique_ibfk_1`
  FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`)
  ON DELETE CASCADE;

ALTER TABLE `polyvalence`
  ADD CONSTRAINT `polyvalence_ibfk_1`
  FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`)
  ON DELETE CASCADE;

SELECT 'ROLLBACK TERMINÉ - Table renommée en operateurs' AS Status;
SELECT COUNT(*) AS NombreOperateurs FROM operateurs;
