-- =============================================================================
-- Création des vues manquantes pour les alertes médicales et entretiens
-- Date: 2026-02-09
-- Description: Crée les vues v_alertes_medicales et v_alertes_entretiens
-- =============================================================================

-- ============================================================
-- Vue alertes médicales (visites en retard, RQTH expirant)
-- ============================================================
DROP VIEW IF EXISTS `v_alertes_medicales`;
CREATE VIEW `v_alertes_medicales` AS
-- Visites en retard
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    'Visite médicale en retard' AS type_alerte,
    mv.prochaine_visite AS date_alerte,
    DATEDIFF(CURDATE(), mv.prochaine_visite) AS jours_retard
FROM personnel p
JOIN medical_visite mv ON p.id = mv.operateur_id
WHERE p.statut = 'ACTIF'
  AND mv.prochaine_visite < CURDATE()
  AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE operateur_id = p.id)

UNION ALL

-- RQTH expirant bientôt (utilise table validite existante)
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    'RQTH expirant bientôt' AS type_alerte,
    v.date_fin AS date_alerte,
    DATEDIFF(v.date_fin, CURDATE()) AS jours_retard
FROM personnel p
JOIN validite v ON p.id = v.operateur_id
WHERE p.statut = 'ACTIF'
  AND v.type_validite = 'RQTH'
  AND v.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 90 DAY);

-- ============================================================
-- Vue alertes entretiens (EPP/EAP en retard)
-- ============================================================
DROP VIEW IF EXISTS `v_alertes_entretiens`;
CREATE VIEW `v_alertes_entretiens` AS
-- EPP en retard (obligatoire tous les 2 ans)
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    'EPP en retard' AS type_alerte,
    COALESCE(
        (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
         WHERE e.operateur_id = p.id AND e.type_entretien = 'EPP'),
        pi.date_entree
    ) AS derniere_date,
    DATEDIFF(
        CURDATE(),
        DATE_ADD(
            COALESCE(
                (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
                 WHERE e.operateur_id = p.id AND e.type_entretien = 'EPP'),
                pi.date_entree
            ),
            INTERVAL 2 YEAR
        )
    ) AS jours_retard
FROM personnel p
LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
WHERE p.statut = 'ACTIF'
  AND DATEDIFF(
        CURDATE(),
        DATE_ADD(
            COALESCE(
                (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
                 WHERE e.operateur_id = p.id AND e.type_entretien = 'EPP'),
                pi.date_entree
            ),
            INTERVAL 2 YEAR
        )
    ) > 0

UNION ALL

-- EAP en retard (annuel)
SELECT
    p.id AS operateur_id,
    p.nom,
    p.prenom,
    p.matricule,
    'EAP en retard' AS type_alerte,
    (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
     WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP') AS derniere_date,
    DATEDIFF(
        CURDATE(),
        DATE_ADD(
            (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
             WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP'),
            INTERVAL 1 YEAR
        )
    ) AS jours_retard
FROM personnel p
WHERE p.statut = 'ACTIF'
  AND (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
       WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP') IS NOT NULL
  AND DATEDIFF(
        CURDATE(),
        DATE_ADD(
            (SELECT MAX(date_entretien) FROM vie_salarie_entretien e
             WHERE e.operateur_id = p.id AND e.type_entretien = 'EAP'),
            INTERVAL 1 YEAR
        )
    ) > 0;
