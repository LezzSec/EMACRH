-- Migration 029: Ajout des catégories de documents manquantes pour tous les domaines RH
-- Date: 2026-03-10
-- Objectif: Chaque onglet RH (Absence, Compétences, Formation, Médical, Vie du salarié, Polyvalence)
--           dispose d'au moins une catégorie pour que les documents y soient visibles.

INSERT IGNORE INTO `categories_documents`
    (`nom`, `description`, `couleur`, `exige_date_expiration`, `ordre_affichage`)
VALUES
    -- Absence (DomaineRH.DECLARATION)
    ('Documents d\'absence',       'Arrêts maladie, justificatifs de congé, accidents du travail', '#f97316', 1,  8),
    -- Compétences (DomaineRH.COMPETENCES)
    ('Documents de compétences',   'Habilitations, CACES, autorisations spécifiques',               '#0ea5e9', 1, 13),
    -- Médical (DomaineRH.MEDICAL)
    ('Documents médicaux',         'Certificats, ordonnances, documents de suivi médical',           '#f87171', 1, 12),
    -- Vie du salarié (DomaineRH.VIE_SALARIE)
    ('Sanctions disciplinaires',   'Avertissements, mises à pied, licenciements',                   '#dc2626', 0, 10),
    ('Entretiens professionnels',  'Entretiens annuels, bilans de compétences',                     '#7c3aed', 0, 11),
    -- Polyvalence (DomaineRH.POLYVALENCE)
    ('Documents de polyvalence',   'Dossiers de formation poste, fiches de polyvalence',            '#10b981', 0, 14);
