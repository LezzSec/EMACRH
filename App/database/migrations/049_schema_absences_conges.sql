-- ============================================================
-- MODULE GESTION DES ABSENCES ET CONGÉS
-- ============================================================

-- Table des types d'absence
CREATE TABLE IF NOT EXISTS type_absence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    libelle VARCHAR(100) NOT NULL,
    decompte_solde BOOLEAN DEFAULT TRUE COMMENT 'Si TRUE, décompte du solde de congés',
    couleur VARCHAR(7) DEFAULT '#3498db' COMMENT 'Couleur pour le calendrier (format hex)',
    actif BOOLEAN DEFAULT TRUE,
    INDEX idx_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertion des types d'absence standards
INSERT INTO type_absence (code, libelle, decompte_solde, couleur) VALUES
('CP', 'Congés Payés', TRUE, '#27ae60'),
('RTT', 'RTT', TRUE, '#3498db'),
('MALADIE', 'Arrêt Maladie', FALSE, '#e74c3c'),
('SANS_SOLDE', 'Congé Sans Solde', FALSE, '#95a5a6'),
('MATERNITE', 'Congé Maternité', FALSE, '#e91e63'),
('PATERNITE', 'Congé Paternité', FALSE, '#9c27b0'),
('FORMATION', 'Formation', FALSE, '#ff9800'),
('EVENEMENT', 'Événement Familial', FALSE, '#00bcd4'),
('AUTRE', 'Autre', FALSE, '#607d8b')
ON DUPLICATE KEY UPDATE libelle=VALUES(libelle);

-- Table des soldes de congés par personne
CREATE TABLE IF NOT EXISTS solde_conges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personnel_id INT NOT NULL,
    annee INT NOT NULL,
    cp_acquis DECIMAL(5,2) DEFAULT 0 COMMENT 'CP acquis dans l année',
    cp_n_1 DECIMAL(5,2) DEFAULT 0 COMMENT 'CP reportés de N-1',
    cp_pris DECIMAL(5,2) DEFAULT 0 COMMENT 'CP déjà pris',
    rtt_acquis DECIMAL(5,2) DEFAULT 0,
    rtt_pris DECIMAL(5,2) DEFAULT 0,
    date_maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE,
    UNIQUE KEY uk_personnel_annee (personnel_id, annee),
    INDEX idx_annee (annee)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des demandes d'absence
CREATE TABLE IF NOT EXISTS demande_absence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personnel_id INT NOT NULL,
    type_absence_id INT NOT NULL,
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    demi_journee_debut ENUM('MATIN', 'APRES_MIDI', 'JOURNEE') DEFAULT 'JOURNEE',
    demi_journee_fin ENUM('MATIN', 'APRES_MIDI', 'JOURNEE') DEFAULT 'JOURNEE',
    nb_jours DECIMAL(4,2) NOT NULL COMMENT 'Nombre de jours ouvrés',
    motif TEXT,
    statut ENUM('EN_ATTENTE', 'VALIDEE', 'REFUSEE', 'ANNULEE') DEFAULT 'EN_ATTENTE',
    validateur_id INT COMMENT 'ID du personnel qui a validé/refusé',
    date_validation DATETIME,
    commentaire_validation TEXT,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE,
    FOREIGN KEY (type_absence_id) REFERENCES type_absence(id),
    FOREIGN KEY (validateur_id) REFERENCES personnel(id) ON DELETE SET NULL,
    INDEX idx_personnel (personnel_id),
    INDEX idx_dates (date_debut, date_fin),
    INDEX idx_statut (statut)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des jours fériés
CREATE TABLE IF NOT EXISTS jours_feries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_ferie DATE NOT NULL UNIQUE,
    libelle VARCHAR(100) NOT NULL,
    fixe BOOLEAN DEFAULT TRUE COMMENT 'TRUE si date fixe chaque année',
    INDEX idx_date (date_ferie)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertion des jours fériés français 2025
INSERT INTO jours_feries (date_ferie, libelle, fixe) VALUES
('2025-01-01', 'Jour de l''An', TRUE),
('2025-04-21', 'Lundi de Pâques', FALSE),
('2025-05-01', 'Fête du Travail', TRUE),
('2025-05-08', 'Victoire 1945', TRUE),
('2025-05-29', 'Ascension', FALSE),
('2025-06-09', 'Lundi de Pentecôte', FALSE),
('2025-07-14', 'Fête Nationale', TRUE),
('2025-08-15', 'Assomption', TRUE),
('2025-11-01', 'Toussaint', TRUE),
('2025-11-11', 'Armistice 1918', TRUE),
('2025-12-25', 'Noël', TRUE)
ON DUPLICATE KEY UPDATE libelle=VALUES(libelle);

-- Vue pour les absences avec détails
CREATE OR REPLACE VIEW v_absences_details AS
SELECT
    da.id,
    da.personnel_id,
    CONCAT(p.prenom, ' ', p.nom) as nom_complet,
    p.matricule,
    ta.code as type_code,
    ta.libelle as type_libelle,
    ta.couleur,
    da.date_debut,
    da.date_fin,
    da.demi_journee_debut,
    da.demi_journee_fin,
    da.nb_jours,
    da.motif,
    da.statut,
    CASE
        WHEN da.validateur_id IS NOT NULL
        THEN CONCAT(v.prenom, ' ', v.nom)
        ELSE NULL
    END as validateur,
    da.date_validation,
    da.commentaire_validation,
    da.date_creation
FROM demande_absence da
JOIN personnel p ON da.personnel_id = p.id
JOIN type_absence ta ON da.type_absence_id = ta.id
LEFT JOIN personnel v ON da.validateur_id = v.id
WHERE p.statut = 'ACTIF';

-- Vue pour les soldes disponibles
CREATE OR REPLACE VIEW v_soldes_disponibles AS
SELECT
    sc.id,
    sc.personnel_id,
    CONCAT(p.prenom, ' ', p.nom) as nom_complet,
    p.matricule,
    sc.annee,
    sc.cp_acquis,
    sc.cp_n_1,
    sc.cp_pris,
    (sc.cp_acquis + sc.cp_n_1 - sc.cp_pris) as cp_restant,
    sc.rtt_acquis,
    sc.rtt_pris,
    (sc.rtt_acquis - sc.rtt_pris) as rtt_restant,
    sc.date_maj
FROM solde_conges sc
JOIN personnel p ON sc.personnel_id = p.id
WHERE p.statut = 'ACTIF';

-- Vue statistiques des absences
CREATE OR REPLACE VIEW v_stats_absences AS
SELECT
    p.id as personnel_id,
    CONCAT(p.prenom, ' ', p.nom) as nom_complet,
    YEAR(da.date_debut) as annee,
    ta.libelle as type_absence,
    COUNT(*) as nb_demandes,
    SUM(da.nb_jours) as total_jours,
    SUM(CASE WHEN da.statut = 'VALIDEE' THEN da.nb_jours ELSE 0 END) as jours_valides,
    SUM(CASE WHEN da.statut = 'EN_ATTENTE' THEN da.nb_jours ELSE 0 END) as jours_en_attente
FROM demande_absence da
JOIN personnel p ON da.personnel_id = p.id
JOIN type_absence ta ON da.type_absence_id = ta.id
WHERE p.statut = 'ACTIF'
GROUP BY p.id, YEAR(da.date_debut), ta.libelle;
