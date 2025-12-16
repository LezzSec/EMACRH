-- Migration: Renommer table operateurs en personnel
-- Date: 2025-12-15
-- Description: Consolide la nomenclature sur 'personnel' au lieu de 'operateurs'

-- 1. Supprimer les foreign keys existantes qui référencent operateurs
ALTER TABLE `historique` DROP FOREIGN KEY `historique_ibfk_1`;
ALTER TABLE `polyvalence` DROP FOREIGN KEY `polyvalence_ibfk_1`;

-- 2. Renommer la table operateurs en personnel
RENAME TABLE `operateurs` TO `personnel`;

-- 3. Recréer les foreign keys vers personnel
ALTER TABLE `historique`
  ADD CONSTRAINT `historique_ibfk_1`
  FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

ALTER TABLE `polyvalence`
  ADD CONSTRAINT `polyvalence_ibfk_1`
  FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- 4. Vérification
SELECT 'Migration terminée!' AS Status;
SELECT COUNT(*) AS NombrePersonnel FROM personnel;
