-- Migration: Renommer operateur_id en personnel_id dans personnel_infos
-- Date: 2026-02-05
-- Raison: Cohérence avec la table personnel (anciennement operateurs)

-- ============================================================
-- Renommer la colonne operateur_id en personnel_id
-- ============================================================

-- Supprimer d'abord la contrainte de clé étrangère existante
ALTER TABLE `personnel_infos` DROP FOREIGN KEY `fk_personnel_infos_operateur`;

-- Renommer la colonne
ALTER TABLE `personnel_infos` CHANGE COLUMN `operateur_id` `personnel_id` INT NOT NULL;

-- Recréer la contrainte de clé étrangère avec le nouveau nom
ALTER TABLE `personnel_infos`
ADD CONSTRAINT `fk_personnel_infos_personnel`
FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- ============================================================
-- Rollback (à exécuter manuellement si nécessaire)
-- ============================================================
-- ALTER TABLE `personnel_infos` DROP FOREIGN KEY `fk_personnel_infos_personnel`;
-- ALTER TABLE `personnel_infos` CHANGE COLUMN `personnel_id` `operateur_id` INT NOT NULL;
-- ALTER TABLE `personnel_infos` ADD CONSTRAINT `fk_personnel_infos_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;
