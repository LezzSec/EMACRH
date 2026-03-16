-- =====================================================================
-- Migration 030 : Renommage operateur_id → personnel_id dans toutes les tables
-- Date : 2026-03-16
-- Raison : Harmonisation complète de la nomenclature — "personnel_id" est
--          cohérent avec la table `personnel` (anciennement `operateurs`).
--          Concerne 14 tables + 6 vues.
-- Tables : declaration, formation, historique, historique_polyvalence,
--          medical, medical_accident_travail, medical_maladie_pro,
--          medical_visite, polyvalence, validite, vie_salarie_alcoolemie,
--          vie_salarie_entretien, vie_salarie_sanction, vie_salarie_test_salivaire
-- Vues   : v_alertes_entretiens, v_alertes_medicales, v_documents_stats_operateur,
--          v_historique_polyvalence_complet, v_suivi_medical, v_vie_salarie_recap,
--          v_contrat_anciennete, v_contrats_fin_proche
-- =====================================================================

USE emac_db;

SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================
-- 1. TABLE declaration (anciennement absences_conges)
-- =====================================================================

ALTER TABLE `declaration`
    DROP FOREIGN KEY `fk_absences_conges_operateur`,
    DROP INDEX `idx_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_personnel` (`personnel_id`),
    ADD CONSTRAINT `fk_declaration_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 2. TABLE formation
-- =====================================================================

ALTER TABLE `formation`
    DROP FOREIGN KEY `fk_formation_operateur`,
    DROP INDEX `idx_operateur`,
    DROP INDEX `idx_formation_operateur_dates`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_personnel` (`personnel_id`),
    ADD INDEX `idx_formation_personnel_dates` (`personnel_id`, `date_debut`, `date_fin`),
    ADD CONSTRAINT `fk_formation_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 3. TABLE historique
-- =====================================================================

ALTER TABLE `historique`
    DROP FOREIGN KEY `historique_ibfk_1`,
    DROP INDEX `operateur_id`,
    DROP INDEX `idx_historique_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT DEFAULT NULL,
    ADD INDEX `personnel_id` (`personnel_id`),
    ADD INDEX `idx_historique_personnel` (`personnel_id`),
    ADD CONSTRAINT `historique_ibfk_1`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 4. TABLE historique_polyvalence
-- =====================================================================

ALTER TABLE `historique_polyvalence`
    DROP FOREIGN KEY `historique_polyvalence_ibfk_1`,
    DROP INDEX `idx_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_personnel` (`personnel_id`),
    ADD CONSTRAINT `historique_polyvalence_ibfk_1`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 5. TABLE medical
-- =====================================================================

ALTER TABLE `medical`
    DROP FOREIGN KEY `fk_medical_operateur`,
    DROP INDEX `uk_medical_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD UNIQUE INDEX `uk_medical_personnel` (`personnel_id`),
    ADD CONSTRAINT `fk_medical_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 6. TABLE medical_accident_travail
-- =====================================================================

ALTER TABLE `medical_accident_travail`
    DROP FOREIGN KEY `fk_at_operateur`,
    DROP INDEX `idx_at_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_at_personnel` (`personnel_id`),
    ADD CONSTRAINT `fk_at_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 7. TABLE medical_maladie_pro
-- =====================================================================

ALTER TABLE `medical_maladie_pro`
    DROP FOREIGN KEY `fk_mp_operateur`,
    DROP INDEX `idx_mp_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_mp_personnel` (`personnel_id`),
    ADD CONSTRAINT `fk_mp_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 8. TABLE medical_visite
-- =====================================================================

ALTER TABLE `medical_visite`
    DROP FOREIGN KEY `fk_visite_operateur`,
    DROP INDEX `idx_visite_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_visite_personnel` (`personnel_id`),
    ADD CONSTRAINT `fk_visite_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 9. TABLE polyvalence
-- =====================================================================

ALTER TABLE `polyvalence`
    DROP FOREIGN KEY `polyvalence_ibfk_1`,
    DROP INDEX `operateur_id`,
    DROP INDEX `idx_polyvalence_operateur`,
    DROP INDEX `idx_polyvalence_eval_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `personnel_id` (`personnel_id`),
    ADD INDEX `idx_polyvalence_personnel` (`personnel_id`),
    ADD INDEX `idx_polyvalence_eval_personnel` (`personnel_id`, `prochaine_evaluation`),
    ADD CONSTRAINT `polyvalence_ibfk_1`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 10. TABLE validite
-- =====================================================================

ALTER TABLE `validite`
    DROP FOREIGN KEY `fk_validite_operateur`,
    DROP INDEX `idx_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_personnel` (`personnel_id`),
    ADD CONSTRAINT `fk_validite_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 11. TABLE vie_salarie_alcoolemie
-- =====================================================================

ALTER TABLE `vie_salarie_alcoolemie`
    DROP FOREIGN KEY `fk_alcool_operateur`,
    DROP INDEX `idx_alcool_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_alcool_personnel` (`personnel_id`),
    ADD CONSTRAINT `fk_alcool_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 12. TABLE vie_salarie_entretien
-- =====================================================================

ALTER TABLE `vie_salarie_entretien`
    DROP FOREIGN KEY `fk_entretien_operateur`,
    DROP INDEX `idx_entretien_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_entretien_personnel` (`personnel_id`),
    ADD CONSTRAINT `fk_entretien_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 13. TABLE vie_salarie_sanction
-- =====================================================================

ALTER TABLE `vie_salarie_sanction`
    DROP FOREIGN KEY `fk_sanction_operateur`,
    DROP INDEX `idx_sanction_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_sanction_personnel` (`personnel_id`),
    ADD CONSTRAINT `fk_sanction_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

-- =====================================================================
-- 14. TABLE vie_salarie_test_salivaire
-- =====================================================================

ALTER TABLE `vie_salarie_test_salivaire`
    DROP FOREIGN KEY `fk_salivaire_operateur`,
    DROP INDEX `idx_salivaire_operateur`,
    CHANGE COLUMN `operateur_id` `personnel_id` INT(11) NOT NULL,
    ADD INDEX `idx_salivaire_personnel` (`personnel_id`),
    ADD CONSTRAINT `fk_salivaire_personnel`
        FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- VUES : Drop & Recreate avec personnel_id
-- =====================================================================

-- =====================================================================
-- VUE v_alertes_entretiens
-- =====================================================================

DROP VIEW IF EXISTS `v_alertes_entretiens`;
CREATE VIEW `v_alertes_entretiens` AS
SELECT
    `p`.`id` AS `personnel_id`,
    `p`.`nom` AS `nom`,
    `p`.`prenom` AS `prenom`,
    `p`.`matricule` AS `matricule`,
    'EPP en retard' AS `type_alerte`,
    COALESCE(
        (SELECT MAX(`e`.`date_entretien`) FROM `vie_salarie_entretien` `e`
         WHERE `e`.`personnel_id` = `p`.`id` AND `e`.`type_entretien` = 'EPP'),
        `pi`.`date_entree`
    ) AS `derniere_date`,
    TO_DAYS(CURDATE()) - TO_DAYS(
        COALESCE(
            (SELECT MAX(`e`.`date_entretien`) FROM `vie_salarie_entretien` `e`
             WHERE `e`.`personnel_id` = `p`.`id` AND `e`.`type_entretien` = 'EPP'),
            `pi`.`date_entree`
        ) + INTERVAL 2 YEAR
    ) AS `jours_retard`
FROM `personnel` `p`
LEFT JOIN `personnel_infos` `pi` ON `p`.`id` = `pi`.`personnel_id`
WHERE `p`.`statut` = 'ACTIF'
AND TO_DAYS(CURDATE()) - TO_DAYS(
    COALESCE(
        (SELECT MAX(`e`.`date_entretien`) FROM `vie_salarie_entretien` `e`
         WHERE `e`.`personnel_id` = `p`.`id` AND `e`.`type_entretien` = 'EPP'),
        `pi`.`date_entree`
    ) + INTERVAL 2 YEAR
) > 0

UNION ALL

SELECT
    `p`.`id` AS `personnel_id`,
    `p`.`nom` AS `nom`,
    `p`.`prenom` AS `prenom`,
    `p`.`matricule` AS `matricule`,
    'EAP en retard' AS `type_alerte`,
    (SELECT MAX(`e`.`date_entretien`) FROM `vie_salarie_entretien` `e`
     WHERE `e`.`personnel_id` = `p`.`id` AND `e`.`type_entretien` = 'EAP') AS `derniere_date`,
    TO_DAYS(CURDATE()) - TO_DAYS(
        (SELECT MAX(`e`.`date_entretien`) FROM `vie_salarie_entretien` `e`
         WHERE `e`.`personnel_id` = `p`.`id` AND `e`.`type_entretien` = 'EAP') + INTERVAL 1 YEAR
    ) AS `jours_retard`
FROM `personnel` `p`
WHERE `p`.`statut` = 'ACTIF'
AND (SELECT MAX(`e`.`date_entretien`) FROM `vie_salarie_entretien` `e`
     WHERE `e`.`personnel_id` = `p`.`id` AND `e`.`type_entretien` = 'EAP') IS NOT NULL
AND TO_DAYS(CURDATE()) - TO_DAYS(
    (SELECT MAX(`e`.`date_entretien`) FROM `vie_salarie_entretien` `e`
     WHERE `e`.`personnel_id` = `p`.`id` AND `e`.`type_entretien` = 'EAP') + INTERVAL 1 YEAR
) > 0;

-- =====================================================================
-- VUE v_alertes_medicales
-- =====================================================================

DROP VIEW IF EXISTS `v_alertes_medicales`;
CREATE VIEW `v_alertes_medicales` AS
SELECT
    `p`.`id` AS `personnel_id`,
    `p`.`nom` AS `nom`,
    `p`.`prenom` AS `prenom`,
    `p`.`matricule` AS `matricule`,
    'Visite médicale en retard' AS `type_alerte`,
    `mv`.`prochaine_visite` AS `date_alerte`,
    TO_DAYS(CURDATE()) - TO_DAYS(`mv`.`prochaine_visite`) AS `jours_retard`
FROM `personnel` `p`
JOIN `medical_visite` `mv` ON `p`.`id` = `mv`.`personnel_id`
WHERE `p`.`statut` = 'ACTIF'
AND `mv`.`prochaine_visite` < CURDATE()
AND `mv`.`id` = (SELECT MAX(`medical_visite`.`id`) FROM `medical_visite`
                 WHERE `medical_visite`.`personnel_id` = `p`.`id`)

UNION ALL

SELECT
    `p`.`id` AS `personnel_id`,
    `p`.`nom` AS `nom`,
    `p`.`prenom` AS `prenom`,
    `p`.`matricule` AS `matricule`,
    'RQTH expirant bientôt' AS `type_alerte`,
    `v`.`date_fin` AS `date_alerte`,
    TO_DAYS(`v`.`date_fin`) - TO_DAYS(CURDATE()) AS `jours_retard`
FROM `personnel` `p`
JOIN `validite` `v` ON `p`.`id` = `v`.`personnel_id`
WHERE `p`.`statut` = 'ACTIF'
AND `v`.`type_validite` = 'RQTH'
AND `v`.`date_fin` BETWEEN CURDATE() AND CURDATE() + INTERVAL 90 DAY;

-- =====================================================================
-- VUE v_documents_stats_operateur (alias inchangé volontairement pour
-- compatibilité — seul le nom de colonne de table change)
-- =====================================================================

DROP VIEW IF EXISTS `v_documents_stats_operateur`;
CREATE VIEW `v_documents_stats_operateur` AS
SELECT
    `p`.`id` AS `personnel_id`,
    `p`.`matricule` AS `matricule`,
    CONCAT(`p`.`prenom`, ' ', `p`.`nom`) AS `operateur_nom`,
    COUNT(`d`.`id`) AS `total_documents`,
    SUM(CASE WHEN `d`.`statut` = 'actif' THEN 1 ELSE 0 END) AS `documents_actifs`,
    SUM(CASE WHEN `d`.`statut` = 'expire' THEN 1 ELSE 0 END) AS `documents_expires`,
    SUM(CASE WHEN `d`.`date_expiration` IS NOT NULL
             AND `d`.`date_expiration` <= CURDATE() + INTERVAL 30 DAY
             AND `d`.`date_expiration` >= CURDATE() THEN 1 ELSE 0 END) AS `documents_expire_bientot`,
    SUM(`d`.`taille_octets`) AS `taille_totale_octets`,
    ROUND(SUM(`d`.`taille_octets`) / 1048576, 2) AS `taille_totale_mo`,
    MAX(`d`.`date_upload`) AS `derniere_mise_a_jour`
FROM `personnel` `p`
LEFT JOIN `documents` `d` ON `p`.`id` = `d`.`personnel_id`
GROUP BY `p`.`id`, `p`.`matricule`, `p`.`prenom`, `p`.`nom`;

-- =====================================================================
-- VUE v_historique_polyvalence_complet
-- =====================================================================

DROP VIEW IF EXISTS `v_historique_polyvalence_complet`;
CREATE VIEW `v_historique_polyvalence_complet` AS
SELECT
    `hp`.`id` AS `id`,
    `hp`.`date_action` AS `date_action`,
    `hp`.`action_type` AS `action_type`,
    `pers`.`nom` AS `operateur_nom`,
    `pers`.`prenom` AS `operateur_prenom`,
    `pers`.`matricule` AS `operateur_matricule`,
    `hp`.`personnel_id` AS `personnel_id`,
    `pos`.`poste_code` AS `poste_code`,
    `hp`.`poste_id` AS `poste_id`,
    `hp`.`ancien_niveau` AS `ancien_niveau`,
    `hp`.`ancienne_date_evaluation` AS `ancienne_date_evaluation`,
    `hp`.`ancienne_prochaine_evaluation` AS `ancienne_prochaine_evaluation`,
    `hp`.`ancien_statut` AS `ancien_statut`,
    `hp`.`nouveau_niveau` AS `nouveau_niveau`,
    `hp`.`nouvelle_date_evaluation` AS `nouvelle_date_evaluation`,
    `hp`.`nouvelle_prochaine_evaluation` AS `nouvelle_prochaine_evaluation`,
    `hp`.`nouveau_statut` AS `nouveau_statut`,
    `hp`.`utilisateur` AS `utilisateur`,
    `hp`.`commentaire` AS `commentaire`,
    `hp`.`source` AS `source`,
    `hp`.`import_batch_id` AS `import_batch_id`,
    `hp`.`metadata_json` AS `metadata_json`,
    CASE
        WHEN `hp`.`action_type` = 'AJOUT' THEN CONCAT('Ajout niveau ', `hp`.`nouveau_niveau`)
        WHEN `hp`.`action_type` = 'MODIFICATION' THEN CONCAT('Modification : N', `hp`.`ancien_niveau`, ' -> N', `hp`.`nouveau_niveau`)
        WHEN `hp`.`action_type` = 'SUPPRESSION' THEN CONCAT('Suppression niveau ', `hp`.`ancien_niveau`)
        WHEN `hp`.`action_type` = 'IMPORT_MANUEL' THEN CONCAT('Import manuel : ', COALESCE(`hp`.`commentaire`, ''))
    END AS `resume`
FROM `historique_polyvalence` `hp`
LEFT JOIN `personnel` `pers` ON `hp`.`personnel_id` = `pers`.`id`
LEFT JOIN `postes` `pos` ON `hp`.`poste_id` = `pos`.`id`
ORDER BY `hp`.`date_action` DESC;

-- =====================================================================
-- VUE v_suivi_medical
-- =====================================================================

DROP VIEW IF EXISTS `v_suivi_medical`;
CREATE VIEW `v_suivi_medical` AS
SELECT
    `p`.`id` AS `personnel_id`,
    `p`.`nom` AS `nom`,
    `p`.`prenom` AS `prenom`,
    `p`.`matricule` AS `matricule`,
    `p`.`statut` AS `statut`,
    `m`.`type_suivi_vip` AS `type_suivi_vip`,
    `m`.`periodicite_vip_mois` AS `periodicite_vip_mois`,
    (SELECT MAX(`mv`.`date_visite`) FROM `medical_visite` `mv`
     WHERE `mv`.`personnel_id` = `p`.`id`) AS `derniere_visite`,
    (SELECT `mv`.`prochaine_visite` FROM `medical_visite` `mv`
     WHERE `mv`.`personnel_id` = `p`.`id`
     ORDER BY `mv`.`date_visite` DESC LIMIT 1) AS `prochaine_visite`,
    CASE
        WHEN (SELECT `mv`.`prochaine_visite` FROM `medical_visite` `mv`
              WHERE `mv`.`personnel_id` = `p`.`id`
              ORDER BY `mv`.`date_visite` DESC LIMIT 1) < CURDATE() THEN 'En retard'
        WHEN (SELECT `mv`.`prochaine_visite` FROM `medical_visite` `mv`
              WHERE `mv`.`personnel_id` = `p`.`id`
              ORDER BY `mv`.`date_visite` DESC LIMIT 1) <= CURDATE() + INTERVAL 30 DAY THEN 'A planifier'
        ELSE 'OK'
    END AS `statut_visite`,
    (SELECT `v`.`date_debut` FROM `validite` `v`
     WHERE `v`.`personnel_id` = `p`.`id` AND `v`.`type_validite` = 'RQTH'
     ORDER BY `v`.`date_debut` DESC LIMIT 1) AS `date_debut_rqth`,
    (SELECT `v`.`date_fin` FROM `validite` `v`
     WHERE `v`.`personnel_id` = `p`.`id` AND `v`.`type_validite` = 'RQTH'
     ORDER BY `v`.`date_debut` DESC LIMIT 1) AS `date_fin_rqth`,
    CASE
        WHEN (SELECT `v`.`date_fin` FROM `validite` `v`
              WHERE `v`.`personnel_id` = `p`.`id` AND `v`.`type_validite` = 'RQTH'
              ORDER BY `v`.`date_debut` DESC LIMIT 1) IS NOT NULL
         AND (SELECT `v`.`date_fin` FROM `validite` `v`
              WHERE `v`.`personnel_id` = `p`.`id` AND `v`.`type_validite` = 'RQTH'
              ORDER BY `v`.`date_debut` DESC LIMIT 1) >= CURDATE() THEN 'Active'
        WHEN (SELECT `v`.`date_fin` FROM `validite` `v`
              WHERE `v`.`personnel_id` = `p`.`id` AND `v`.`type_validite` = 'RQTH'
              ORDER BY `v`.`date_debut` DESC LIMIT 1) IS NOT NULL
         AND (SELECT `v`.`date_fin` FROM `validite` `v`
              WHERE `v`.`personnel_id` = `p`.`id` AND `v`.`type_validite` = 'RQTH'
              ORDER BY `v`.`date_debut` DESC LIMIT 1) < CURDATE() THEN 'Expiree'
        ELSE 'Non applicable'
    END AS `statut_rqth`,
    (SELECT `v`.`date_debut` FROM `validite` `v`
     WHERE `v`.`personnel_id` = `p`.`id` AND `v`.`type_validite` = 'OETH'
     ORDER BY `v`.`date_debut` DESC LIMIT 1) AS `date_debut_oeth`,
    (SELECT `v`.`date_fin` FROM `validite` `v`
     WHERE `v`.`personnel_id` = `p`.`id` AND `v`.`type_validite` = 'OETH'
     ORDER BY `v`.`date_debut` DESC LIMIT 1) AS `date_fin_oeth`,
    (SELECT `v`.`taux_incapacite` FROM `validite` `v`
     WHERE `v`.`personnel_id` = `p`.`id`
     ORDER BY `v`.`date_debut` DESC LIMIT 1) AS `taux_incapacite`,
    `m`.`maladie_pro` AS `maladie_pro`,
    (SELECT COUNT(0) FROM `medical_accident_travail` `at`
     WHERE `at`.`personnel_id` = `p`.`id`) AS `nb_accidents`
FROM `personnel` `p`
LEFT JOIN `medical` `m` ON `p`.`id` = `m`.`personnel_id`
WHERE `p`.`statut` = 'ACTIF';

-- =====================================================================
-- VUE v_vie_salarie_recap
-- =====================================================================

DROP VIEW IF EXISTS `v_vie_salarie_recap`;
CREATE VIEW `v_vie_salarie_recap` AS
SELECT
    `p`.`id` AS `personnel_id`,
    `p`.`nom` AS `nom`,
    `p`.`prenom` AS `prenom`,
    `p`.`statut` AS `statut`,
    (SELECT COUNT(0) FROM `vie_salarie_sanction` `s`
     WHERE `s`.`personnel_id` = `p`.`id`) AS `nb_sanctions`,
    (SELECT MAX(`s`.`date_sanction`) FROM `vie_salarie_sanction` `s`
     WHERE `s`.`personnel_id` = `p`.`id`) AS `derniere_sanction`,
    (SELECT COUNT(0) FROM `vie_salarie_alcoolemie` `a`
     WHERE `a`.`personnel_id` = `p`.`id`) AS `nb_controles_alcool`,
    (SELECT COUNT(0) FROM `vie_salarie_alcoolemie` `a`
     WHERE `a`.`personnel_id` = `p`.`id` AND `a`.`resultat` = 'Positif') AS `nb_positifs_alcool`,
    (SELECT COUNT(0) FROM `vie_salarie_test_salivaire` `t`
     WHERE `t`.`personnel_id` = `p`.`id`) AS `nb_tests_salivaires`,
    (SELECT COUNT(0) FROM `vie_salarie_test_salivaire` `t`
     WHERE `t`.`personnel_id` = `p`.`id` AND `t`.`resultat` = 'Positif') AS `nb_positifs_salivaire`,
    (SELECT MAX(`e`.`date_entretien`) FROM `vie_salarie_entretien` `e`
     WHERE `e`.`personnel_id` = `p`.`id` AND `e`.`type_entretien` = 'EPP') AS `dernier_epp`,
    (SELECT MAX(`e`.`date_entretien`) FROM `vie_salarie_entretien` `e`
     WHERE `e`.`personnel_id` = `p`.`id` AND `e`.`type_entretien` = 'EAP') AS `dernier_eap`,
    (SELECT `e`.`prochaine_date` FROM `vie_salarie_entretien` `e`
     WHERE `e`.`personnel_id` = `p`.`id`
     ORDER BY `e`.`date_entretien` DESC LIMIT 1) AS `prochain_entretien`
FROM `personnel` `p`;

-- =====================================================================
-- VUES contrat (déjà cassées depuis migration 002 — on les recrée)
-- =====================================================================

DROP VIEW IF EXISTS `v_contrat_anciennete`;
CREATE VIEW `v_contrat_anciennete` AS
SELECT
    `c`.`id` AS `id`,
    `c`.`personnel_id` AS `personnel_id`,
    `p`.`nom` AS `nom`,
    `p`.`prenom` AS `prenom`,
    `p`.`matricule` AS `matricule`,
    `c`.`type_contrat` AS `type_contrat`,
    `c`.`date_debut` AS `date_debut`,
    `c`.`date_fin` AS `date_fin`,
    `c`.`date_sortie` AS `date_sortie`,
    `c`.`actif` AS `actif`,
    ROUND((TO_DAYS(COALESCE(`c`.`date_sortie`, CURDATE())) - TO_DAYS(`c`.`date_debut`)) / 365.25, 2) AS `anciennete_annees`,
    CONCAT(
        TIMESTAMPDIFF(YEAR, `c`.`date_debut`, COALESCE(`c`.`date_sortie`, CURDATE())), ' ans ',
        TIMESTAMPDIFF(MONTH, `c`.`date_debut`, COALESCE(`c`.`date_sortie`, CURDATE())) MOD 12, ' mois'
    ) AS `anciennete_detail`,
    CASE
        WHEN `c`.`type_contrat` IN ('CDD', 'Intérimaire', 'Stagiaire', 'Apprentissage')
         AND `c`.`date_fin` IS NOT NULL
         AND `c`.`date_sortie` IS NULL
        THEN TO_DAYS(`c`.`date_fin`) - TO_DAYS(CURDATE())
        ELSE NULL
    END AS `jours_restants`
FROM `contrat` `c`
JOIN `personnel` `p` ON `c`.`personnel_id` = `p`.`id`;

DROP VIEW IF EXISTS `v_contrats_fin_proche`;
CREATE VIEW `v_contrats_fin_proche` AS
SELECT
    `c`.`id` AS `id`,
    `c`.`personnel_id` AS `personnel_id`,
    `p`.`nom` AS `nom`,
    `p`.`prenom` AS `prenom`,
    `p`.`matricule` AS `matricule`,
    `c`.`type_contrat` AS `type_contrat`,
    `c`.`date_debut` AS `date_debut`,
    `c`.`date_fin` AS `date_fin`,
    TO_DAYS(`c`.`date_fin`) - TO_DAYS(CURDATE()) AS `jours_restants`,
    CASE
        WHEN TO_DAYS(`c`.`date_fin`) - TO_DAYS(CURDATE()) < 0 THEN 'EXPIRE'
        WHEN TO_DAYS(`c`.`date_fin`) - TO_DAYS(CURDATE()) <= 7 THEN 'URGENT'
        WHEN TO_DAYS(`c`.`date_fin`) - TO_DAYS(CURDATE()) <= 30 THEN 'ATTENTION'
        ELSE 'OK'
    END AS `statut_alerte`
FROM `contrat` `c`
JOIN `personnel` `p` ON `c`.`personnel_id` = `p`.`id`
WHERE `c`.`actif` = 1
AND `c`.`date_fin` IS NOT NULL
AND `c`.`date_sortie` IS NULL
AND TO_DAYS(`c`.`date_fin`) - TO_DAYS(CURDATE()) <= 60
ORDER BY `c`.`date_fin`;

-- =====================================================================
-- Vérification finale
-- =====================================================================

SELECT
    TABLE_NAME,
    COUNT(*) AS nb_colonnes_operateur_id
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'emac_db'
AND COLUMN_NAME = 'operateur_id'
AND TABLE_TYPE IS NULL  -- tables seulement (pas les vues)
GROUP BY TABLE_NAME;

SELECT 'Migration 030 terminée : operateur_id renommé en personnel_id dans 14 tables + 8 vues recréées' AS statut;
