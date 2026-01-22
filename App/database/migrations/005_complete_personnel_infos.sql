-- Migration: Compléter la table personnel_infos avec les champs SIRH manquants
-- Date: 2026-01-21
-- Source: Tableau SIRH.xlsx - Feuille "Infos administratives"
--
-- NOTE: Cette migration n'ajoute que les champs qui n'existent pas encore.
-- Les champs suivants sont déjà gérés ailleurs:
--   - numero_ss → nir_chiffre/nir_nonce/nir_tag (chiffré)
--   - cp_naissance → déjà présent dans personnel_infos
--   - autorisation_travail → dans la table contrat (lié au contrat, pas à la personne)

-- ============================================================
-- Vérification et ajout des colonnes manquantes
-- ============================================================

-- Tranche d'âge (référence vers table existante)
-- Note: La table tranche_age existe déjà, on ajoute juste la FK si besoin

-- ============================================================
-- Vue pour calculer l'âge et la tranche d'âge
-- (Utilise la table tranche_age existante)
-- ============================================================
DROP VIEW IF EXISTS `v_personnel_age`;
CREATE VIEW `v_personnel_age` AS
SELECT
    p.id,
    p.nom,
    p.prenom,
    p.matricule,
    p.statut,
    pi.date_naissance,
    TIMESTAMPDIFF(YEAR, pi.date_naissance, CURDATE()) AS age,
    ta.libelle AS tranche_age
FROM personnel p
LEFT JOIN personnel_infos pi ON p.id = pi.operateur_id
LEFT JOIN tranche_age ta ON (
    TIMESTAMPDIFF(YEAR, pi.date_naissance, CURDATE()) >= ta.age_min
    AND (ta.age_max IS NULL OR TIMESTAMPDIFF(YEAR, pi.date_naissance, CURDATE()) <= ta.age_max)
);

-- ============================================================
-- Vue pour calculer l'ancienneté
-- ============================================================
DROP VIEW IF EXISTS `v_personnel_anciennete`;
CREATE VIEW `v_personnel_anciennete` AS
SELECT
    p.id,
    p.nom,
    p.prenom,
    p.matricule,
    p.statut,
    pi.date_entree,
    TIMESTAMPDIFF(YEAR, pi.date_entree, CURDATE()) AS anciennete_annees,
    TIMESTAMPDIFF(MONTH, pi.date_entree, CURDATE()) % 12 AS anciennete_mois,
    DATEDIFF(CURDATE(), pi.date_entree) AS anciennete_jours,
    CONCAT(
        TIMESTAMPDIFF(YEAR, pi.date_entree, CURDATE()), ' ans ',
        TIMESTAMPDIFF(MONTH, pi.date_entree, CURDATE()) % 12, ' mois'
    ) AS anciennete_texte
FROM personnel p
LEFT JOIN personnel_infos pi ON p.id = pi.operateur_id
WHERE pi.date_entree IS NOT NULL;

-- ============================================================
-- Rollback (à exécuter manuellement si nécessaire)
-- ============================================================
-- DROP VIEW IF EXISTS `v_personnel_age`;
-- DROP VIEW IF EXISTS `v_personnel_anciennete`;
