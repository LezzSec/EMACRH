-- Migration: Compléter la table contrat avec les champs SIRH manquants
-- Date: 2026-01-21
-- Source: Tableau SIRH.xlsx - Feuille "Contrat"
--
-- NOTE: La table contrat existe déjà avec les champs:
--   - type_contrat (ENUM existant)
--   - date_debut, date_fin, etp, categorie, echelon, emploi, salaire, actif
--   - nom_tuteur, prenom_tuteur, ecole (pour apprentis)
--   - nom_ett, adresse_ett (pour intérimaires)
--   - nom_ge, adresse_ge (pour mise à disposition)
--   - date_autorisation_travail, date_demande_autorisation, type_titre_autorisation,
--     numero_autorisation_travail, date_limite_autorisation (pour étrangers)
--
-- Cette migration ajoute les champs manquants du SIRH.

-- ============================================================
-- Ajout des colonnes manquantes
-- ============================================================

-- Type de CDD (remplacement / accroissement) - si CDD
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `type_cdd` ENUM('Remplacement', 'Accroissement', 'Saisonnier', 'Usage') DEFAULT NULL
COMMENT 'Type de CDD (si type_contrat = CDD)'
AFTER `type_contrat`;

-- Motif du contrat/CDD
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `motif` TEXT DEFAULT NULL
COMMENT 'Motif du contrat ou du CDD'
AFTER `type_cdd`;

-- Date de sortie effective (peut être différente de date_fin pour CDI)
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `date_sortie` DATE DEFAULT NULL
COMMENT 'Date de sortie effective'
AFTER `date_fin`;

-- Date d'embauche en CDI (si passage CDD -> CDI)
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `date_embauche_cdi` DATE DEFAULT NULL
COMMENT 'Date d''embauche en CDI (passage CDD -> CDI)'
AFTER `date_sortie`;

-- Motif de sortie
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `motif_sortie` VARCHAR(100) DEFAULT NULL
COMMENT 'Motif de sortie (démission, licenciement, fin CDD, retraite, etc.)'
AFTER `date_embauche_cdi`;

-- Typologie de statut horaire
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `typologie_statut_horaire` ENUM(
    'Cadre forfait jour',
    'Cadre décompte horaire',
    'Non-cadre',
    'Temps partiel'
) DEFAULT NULL
COMMENT 'Typologie du statut horaire'
AFTER `categorie`;

-- Niveau dans la grille
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `niveau` VARCHAR(20) DEFAULT NULL
COMMENT 'Niveau dans la grille'
AFTER `echelon`;

-- Coefficient salarial
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `coefficient` INT DEFAULT NULL
COMMENT 'Coefficient salarial'
AFTER `niveau`;

-- Salaire annuel brut
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `salaire_annuel` DECIMAL(12,2) DEFAULT NULL
COMMENT 'Salaire brut annuel'
AFTER `salaire`;

-- Type de prime
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `type_prime` VARCHAR(100) DEFAULT NULL
COMMENT 'Type de prime (ancienneté, performance, etc.)'
AFTER `salaire_annuel`;

-- Montant prime mensuel brut
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `prime_mensuelle` DECIMAL(10,2) DEFAULT NULL
COMMENT 'Montant prime mensuel brut'
AFTER `type_prime`;

-- Total prime annuel brut
ALTER TABLE `contrat`
ADD COLUMN IF NOT EXISTS `prime_annuelle` DECIMAL(12,2) DEFAULT NULL
COMMENT 'Total prime annuel brut'
AFTER `prime_mensuelle`;

-- ============================================================
-- Table de référence pour les motifs de sortie
-- ============================================================
CREATE TABLE IF NOT EXISTS `ref_motif_sortie` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `libelle` VARCHAR(100) NOT NULL,
    `actif` TINYINT(1) DEFAULT 1,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_libelle` (`libelle`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insertion des valeurs de référence (IGNORE si existe déjà)
INSERT IGNORE INTO `ref_motif_sortie` (`libelle`) VALUES
    ('Démission'),
    ('Licenciement économique'),
    ('Licenciement pour faute'),
    ('Licenciement pour inaptitude'),
    ('Fin de CDD'),
    ('Fin de période d''essai'),
    ('Rupture conventionnelle'),
    ('Retraite'),
    ('Décès'),
    ('Mutation'),
    ('Fin de mission intérim'),
    ('Fin de stage'),
    ('Fin d''apprentissage');

-- ============================================================
-- Table de référence pour les emplois (si pas existante)
-- ============================================================
CREATE TABLE IF NOT EXISTS `ref_emploi` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `libelle` VARCHAR(100) NOT NULL,
    `categorie_defaut` ENUM('Ouvrier','Ouvrier qualifié','Employé','Agent de maîtrise','Cadre') DEFAULT NULL,
    `actif` TINYINT(1) DEFAULT 1,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_libelle` (`libelle`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Vue pour l'ancienneté par contrat
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
-- Index pour optimiser les recherches
-- ============================================================
CREATE INDEX IF NOT EXISTS `idx_contrat_type_cdd` ON `contrat` (`type_cdd`);
CREATE INDEX IF NOT EXISTS `idx_contrat_motif_sortie` ON `contrat` (`motif_sortie`);
CREATE INDEX IF NOT EXISTS `idx_contrat_date_sortie` ON `contrat` (`date_sortie`);

-- ============================================================
-- Rollback (à exécuter manuellement si nécessaire)
-- ============================================================
ALTER TABLE `contrat` DROP COLUMN `type_cdd`;
ALTER TABLE `contrat` DROP COLUMN `motif`;
ALTER TABLE `contrat` DROP COLUMN `date_sortie`;
ALTER TABLE `contrat` DROP COLUMN `date_embauche_cdi`;
ALTER TABLE `contrat` DROP COLUMN `motif_sortie`;
ALTER TABLE `contrat` DROP COLUMN `typologie_statut_horaire`;
ALTER TABLE `contrat` DROP COLUMN `niveau`;
ALTER TABLE `contrat` DROP COLUMN `coefficient`;
ALTER TABLE `contrat` DROP COLUMN `salaire_annuel`;
ALTER TABLE `contrat` DROP COLUMN `type_prime`;
ALTER TABLE `contrat` DROP COLUMN `prime_mensuelle`;
ALTER TABLE `contrat` DROP COLUMN `prime_annuelle`;
DROP TABLE IF EXISTS `ref_motif_sortie`;
DROP TABLE IF EXISTS `ref_emploi`;
DROP VIEW IF EXISTS `v_contrat_anciennete`;
DROP VIEW IF EXISTS `v_contrats_fin_proche`;
