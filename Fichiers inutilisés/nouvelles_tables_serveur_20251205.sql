-- =============================================
-- EMAC - Dump des nouvelles tables uniquement
-- Date: 2025-12-05 09:09:39
-- Nombre de tables: 2
-- =============================================
-- ATTENTION: Ce dump contient uniquement les nouvelles tables
-- qui n'existent pas sur le serveur.
-- Il peut etre execute en toute securite sans risque
-- d'ecraser les donnees existantes.
-- =============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =============================================
-- Nouvelle table: historique_polyvalence
-- =============================================

CREATE TABLE IF NOT EXISTS `historique_polyvalence` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date_action` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `action_type` enum('AJOUT','MODIFICATION','SUPPRESSION','IMPORT_MANUEL') COLLATE utf8mb4_unicode_ci NOT NULL,
  `operateur_id` int NOT NULL,
  `poste_id` int NOT NULL,
  `polyvalence_id` int DEFAULT NULL,
  `ancien_niveau` int DEFAULT NULL,
  `ancienne_date_evaluation` date DEFAULT NULL,
  `ancienne_prochaine_evaluation` date DEFAULT NULL,
  `ancien_statut` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nouveau_niveau` int DEFAULT NULL,
  `nouvelle_date_evaluation` date DEFAULT NULL,
  `nouvelle_prochaine_evaluation` date DEFAULT NULL,
  `nouveau_statut` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `utilisateur` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `commentaire` text COLLATE utf8mb4_unicode_ci,
  `source` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'SYSTEM',
  `import_batch_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `metadata_json` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_poste` (`poste_id`),
  KEY `idx_date` (`date_action`),
  KEY `idx_action` (`action_type`),
  KEY `idx_batch` (`import_batch_id`),
  KEY `polyvalence_id` (`polyvalence_id`),
  CONSTRAINT `historique_polyvalence_ibfk_1` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE,
  CONSTRAINT `historique_polyvalence_ibfk_2` FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `historique_polyvalence_ibfk_3` FOREIGN KEY (`polyvalence_id`) REFERENCES `polyvalence` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Pas de données à insérer (la table existe déjà avec des données sur le serveur)


-- =============================================
-- Nouvelle vue: v_historique_polyvalence_complet
-- =============================================

CREATE OR REPLACE VIEW `v_historique_polyvalence_complet` AS
SELECT
    hp.id,
    hp.date_action,
    hp.action_type,
    pers.nom AS operateur_nom,
    pers.prenom AS operateur_prenom,
    pers.matricule AS operateur_matricule,
    hp.operateur_id,
    pos.poste_code,
    hp.poste_id,
    hp.ancien_niveau,
    hp.ancienne_date_evaluation,
    hp.ancienne_prochaine_evaluation,
    hp.ancien_statut,
    hp.nouveau_niveau,
    hp.nouvelle_date_evaluation,
    hp.nouvelle_prochaine_evaluation,
    hp.nouveau_statut,
    hp.utilisateur,
    hp.commentaire,
    hp.source,
    hp.import_batch_id,
    hp.metadata_json,
    CASE
        WHEN hp.action_type = 'AJOUT' THEN CONCAT('Ajout niveau ', hp.nouveau_niveau)
        WHEN hp.action_type = 'MODIFICATION' THEN CONCAT('Modification : N', hp.ancien_niveau, ' → N', hp.nouveau_niveau)
        WHEN hp.action_type = 'SUPPRESSION' THEN CONCAT('Suppression niveau ', hp.ancien_niveau)
        WHEN hp.action_type = 'IMPORT_MANUEL' THEN CONCAT('Import manuel : ', COALESCE(hp.commentaire, ''))
    END AS resume
FROM historique_polyvalence hp
LEFT JOIN personnel pers ON hp.operateur_id = pers.id
LEFT JOIN postes pos ON hp.poste_id = pos.id
ORDER BY hp.date_action DESC;

-- Note: Les vues n'ont pas de données à insérer, elles affichent les données des tables sources


SET FOREIGN_KEY_CHECKS = 1;

-- Dump des nouvelles tables termine
