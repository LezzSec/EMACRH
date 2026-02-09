-- =============================================================================
-- Création de toutes les vues manquantes
-- Date: 2026-02-09
-- Description: Crée les vues manquantes pour contrats, médical et vie du salarié
-- =============================================================================

-- ============================================================
-- Vue pour l'ancienneté des contrats
-- ============================================================
DROP VIEW IF EXISTS `v_contrat_anciennete`;
CREATE VIEW `v_contrat_anciennete` AS
SELECT
    c.id,
    c.operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    c.type_contrat,
    c.date_debut,
    c.date_fin,
    c.date_sortie,
    c.actif,
    -- Ancienneté en années (arrondi à 2 décimales)
    ROUND(
        DATEDIFF(
            COALESCE(c.date_sortie, CURDATE()),
            c.date_debut
        ) / 365.25,
        2
    ) AS anciennete_annees,
    -- Ancienneté détaillée
    CONCAT(
        TIMESTAMPDIFF(YEAR, c.date_debut, COALESCE(c.date_sortie, CURDATE())),
        ' ans ',
        MOD(TIMESTAMPDIFF(MONTH, c.date_debut, COALESCE(c.date_sortie, CURDATE())), 12),
        ' mois'
    ) AS anciennete_detail,
    -- Jours restants pour CDD
    CASE
        WHEN c.type_contrat IN ('CDD', 'Intérimaire', 'Stagiaire', 'Apprentissage')
             AND c.date_fin IS NOT NULL
             AND c.date_sortie IS NULL
        THEN DATEDIFF(c.date_fin, CURDATE())
        ELSE NULL
    END AS jours_restants
FROM contrat c
JOIN personnel p ON c.operateur_id = p.id;

-- ============================================================
-- Vue pour les contrats à renouveler / fin proche
-- ============================================================
DROP VIEW IF EXISTS `v_contrats_fin_proche`;
CREATE VIEW `v_contrats_fin_proche` AS
SELECT
    c.id,
    c.operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    c.type_contrat,
    c.date_debut,
    c.date_fin,
    DATEDIFF(c.date_fin, CURDATE()) AS jours_restants,
    CASE
        WHEN DATEDIFF(c.date_fin, CURDATE()) < 0 THEN 'EXPIRE'
        WHEN DATEDIFF(c.date_fin, CURDATE()) <= 7 THEN 'URGENT'
        WHEN DATEDIFF(c.date_fin, CURDATE()) <= 30 THEN 'ATTENTION'
        ELSE 'OK'
    END AS statut_alerte
FROM contrat c
JOIN personnel p ON c.operateur_id = p.id
WHERE c.actif = 1
  AND c.date_fin IS NOT NULL
  AND c.date_sortie IS NULL
  AND DATEDIFF(c.date_fin, CURDATE()) <= 60
ORDER BY c.date_fin;

-- ============================================================
-- Vue pour le suivi médical complet
-- ============================================================
DROP VIEW IF EXISTS `v_suivi_medical`;
CREATE VIEW `v_suivi_medical` AS
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    p.statut,
    m.type_suivi_vip,
    m.periodicite_vip_mois,
    -- Dernière visite
    (SELECT MAX(date_visite) FROM medical_visite mv WHERE mv.operateur_id = p.id) AS derniere_visite,
    -- Prochaine visite calculée
    (SELECT prochaine_visite FROM medical_visite mv
     WHERE mv.operateur_id = p.id
     ORDER BY date_visite DESC LIMIT 1) AS prochaine_visite,
    -- Statut visite
    CASE
        WHEN (SELECT prochaine_visite FROM medical_visite mv
              WHERE mv.operateur_id = p.id
              ORDER BY date_visite DESC LIMIT 1) < CURDATE()
        THEN 'En retard'
        WHEN (SELECT prochaine_visite FROM medical_visite mv
              WHERE mv.operateur_id = p.id
              ORDER BY date_visite DESC LIMIT 1) <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        THEN 'À planifier'
        ELSE 'OK'
    END AS statut_visite,
    -- RQTH depuis table validite existante
    (SELECT date_debut FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) AS date_debut_rqth,
    (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) AS date_fin_rqth,
    CASE
        WHEN (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) IS NOT NULL
             AND (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) >= CURDATE()
        THEN 'Active'
        WHEN (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) IS NOT NULL
             AND (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'RQTH' ORDER BY date_debut DESC LIMIT 1) < CURDATE()
        THEN 'Expirée'
        ELSE 'Non applicable'
    END AS statut_rqth,
    -- OETH depuis table validite existante
    (SELECT date_debut FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'OETH' ORDER BY date_debut DESC LIMIT 1) AS date_debut_oeth,
    (SELECT date_fin FROM validite v WHERE v.operateur_id = p.id AND v.type_validite = 'OETH' ORDER BY date_debut DESC LIMIT 1) AS date_fin_oeth,
    -- Taux d'incapacité depuis table validite
    (SELECT taux_incapacite FROM validite v WHERE v.operateur_id = p.id ORDER BY date_debut DESC LIMIT 1) AS taux_incapacite,
    -- Maladie pro
    m.maladie_pro,
    -- Nombre d'AT
    (SELECT COUNT(*) FROM medical_accident_travail at WHERE at.operateur_id = p.id) AS nb_accidents
FROM personnel p
LEFT JOIN medical m ON p.id = m.operateur_id
WHERE p.statut = 'ACTIF';

-- ============================================================
-- Vue récapitulative de la vie du salarié
-- ============================================================
DROP VIEW IF EXISTS `v_vie_salarie_recap`;
CREATE VIEW `v_vie_salarie_recap` AS
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.statut,
    -- Sanctions
    (SELECT COUNT(*) FROM vie_salarie_sanction s WHERE s.operateur_id = p.id) AS nb_sanctions,
    (SELECT MAX(date_sanction) FROM vie_salarie_sanction s WHERE s.operateur_id = p.id) AS derniere_sanction,
    -- Contrôles alcoolémie
    (SELECT COUNT(*) FROM vie_salarie_alcoolemie a WHERE a.operateur_id = p.id) AS nb_controles_alcool,
    (SELECT COUNT(*) FROM vie_salarie_alcoolemie a WHERE a.operateur_id = p.id AND a.resultat = 'Positif') AS nb_positifs_alcool,
    -- Tests salivaires
    (SELECT COUNT(*) FROM vie_salarie_test_salivaire t WHERE t.operateur_id = p.id) AS nb_tests_salivaires,
    (SELECT COUNT(*) FROM vie_salarie_test_salivaire t WHERE t.operateur_id = p.id AND t.resultat = 'Positif') AS nb_positifs_salivaire,
    -- Entretiens
    (SELECT MAX(date_entretien) FROM vie_salarie_entretien e WHERE e.operateur_id = p.id AND e.type_entretien = 'EPP') AS dernier_epp,
    (SELECT MAX(date_entretien) FROM vie_salarie_entretien e WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP') AS dernier_eap,
    (SELECT prochaine_date FROM vie_salarie_entretien e
     WHERE e.operateur_id = p.id
     ORDER BY date_entretien DESC LIMIT 1) AS prochain_entretien
FROM personnel p;
