-- =============================================================================
-- Création de toutes les vues manquantes
-- Date: 2026-02-09
-- Description: Crée les vues manquantes pour contrats, médical et vie du salarié
-- Mis à jour: 2026-04-16 — utilise personnel_id (renommé par migration 030)
-- =============================================================================

-- ============================================================
-- Vue pour l'ancienneté des contrats
-- ============================================================
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

-- ============================================================
-- Vue pour les contrats à renouveler / fin proche
-- ============================================================
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

-- ============================================================
-- Vue pour le suivi médical complet
-- ============================================================
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

-- ============================================================
-- Vue récapitulative de la vie du salarié
-- ============================================================
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
