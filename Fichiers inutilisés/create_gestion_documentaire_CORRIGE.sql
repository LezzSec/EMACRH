-- ============================================================================
-- GESTION DOCUMENTAIRE - Tables et données initiales
-- VERSION CORRIGÉE pour table 'personnel' (au lieu de 'operateurs')
-- ============================================================================

-- Table: categories_documents
CREATE TABLE IF NOT EXISTS categories_documents (
    id INT NOT NULL AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    couleur VARCHAR(7) DEFAULT '#3b82f6',
    exige_date_expiration BOOLEAN DEFAULT FALSE,
    ordre_affichage INT DEFAULT 0,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_categorie_nom (nom)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Table: documents
CREATE TABLE IF NOT EXISTS documents (
    id INT NOT NULL AUTO_INCREMENT,
    operateur_id INT NOT NULL,
    categorie_id INT NOT NULL,
    nom_fichier VARCHAR(255) NOT NULL,
    nom_affichage VARCHAR(255) NOT NULL,
    chemin_fichier VARCHAR(500) NOT NULL,
    type_mime VARCHAR(100),
    taille_octets BIGINT DEFAULT 0,
    date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_expiration DATE NULL,
    statut ENUM('actif', 'expire', 'archive') DEFAULT 'actif',
    notes TEXT,
    uploaded_by VARCHAR(100),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_operateur (operateur_id),
    KEY idx_categorie (categorie_id),
    KEY idx_statut (statut),
    KEY idx_expiration (date_expiration),
    CONSTRAINT fk_documents_personnel 
        FOREIGN KEY (operateur_id) 
        REFERENCES personnel(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_documents_categorie 
        FOREIGN KEY (categorie_id) 
        REFERENCES categories_documents(id) 
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Trigger: Mise à jour automatique du statut selon la date d'expiration
DELIMITER $$
CREATE TRIGGER tg_documents_check_expiration_bi
BEFORE INSERT ON documents
FOR EACH ROW
BEGIN
    IF NEW.date_expiration IS NOT NULL AND NEW.date_expiration < CURDATE() THEN
        SET NEW.statut = 'expire';
    END IF;
END$$

CREATE TRIGGER tg_documents_check_expiration_bu
BEFORE UPDATE ON documents
FOR EACH ROW
BEGIN
    IF NEW.date_expiration IS NOT NULL AND NEW.date_expiration < CURDATE() THEN
        SET NEW.statut = 'expire';
    ELSEIF NEW.date_expiration IS NULL OR NEW.date_expiration >= CURDATE() THEN
        IF OLD.statut = 'expire' THEN
            SET NEW.statut = 'actif';
        END IF;
    END IF;
END$$
DELIMITER ;

-- ============================================================================
-- DONNÉES INITIALES - Catégories de documents
-- ============================================================================

INSERT INTO categories_documents (nom, description, couleur, exige_date_expiration, ordre_affichage) VALUES
('Contrats de travail', 'Contrats CDI, CDD, avenants', '#10b981', TRUE, 1),
('Certificats médicaux', 'Visites médicales, aptitudes, RQTH', '#ef4444', TRUE, 2),
('Diplômes et formations', 'Diplômes, certificats de formation, habilitations', '#8b5cf6', FALSE, 3),
('Autorisations de travail', 'Titres de séjour, autorisations de travail pour étrangers', '#f59e0b', TRUE, 4),
('Pièces d\'identité', 'CNI, passeport, permis de conduire', '#06b6d4', TRUE, 5),
('Attestations diverses', 'Attestations employeur, certificats de travail', '#6366f1', FALSE, 6),
('Documents administratifs', 'Fiches de paie, relevés, justificatifs', '#64748b', FALSE, 7),
('Autres', 'Documents non classés', '#9ca3af', FALSE, 99);

-- ============================================================================
-- Vue: Documents avec informations enrichies
-- ============================================================================

CREATE OR REPLACE VIEW v_documents_complet AS
SELECT 
    d.id,
    d.operateur_id,
    p.matricule,
    CONCAT(p.prenom, ' ', p.nom) AS operateur_nom,
    d.categorie_id,
    c.nom AS categorie_nom,
    c.couleur AS categorie_couleur,
    c.exige_date_expiration,
    d.nom_fichier,
    d.nom_affichage,
    d.chemin_fichier,
    d.type_mime,
    d.taille_octets,
    ROUND(d.taille_octets / 1024, 2) AS taille_ko,
    ROUND(d.taille_octets / 1048576, 2) AS taille_mo,
    d.date_upload,
    d.date_expiration,
    CASE 
        WHEN d.date_expiration IS NULL THEN NULL
        WHEN d.date_expiration < CURDATE() THEN 'Expiré'
        WHEN d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 'Expire bientôt'
        ELSE 'Valide'
    END AS alerte_expiration,
    DATEDIFF(d.date_expiration, CURDATE()) AS jours_avant_expiration,
    d.statut,
    d.notes,
    d.uploaded_by,
    d.date_creation,
    d.date_modification
FROM documents d
INNER JOIN personnel p ON d.operateur_id = p.id
INNER JOIN categories_documents c ON d.categorie_id = c.id;

-- ============================================================================
-- Vue: Statistiques par opérateur
-- ============================================================================

CREATE OR REPLACE VIEW v_documents_stats_operateur AS
SELECT 
    p.id AS operateur_id,
    p.matricule,
    CONCAT(p.prenom, ' ', p.nom) AS operateur_nom,
    COUNT(d.id) AS total_documents,
    SUM(CASE WHEN d.statut = 'actif' THEN 1 ELSE 0 END) AS documents_actifs,
    SUM(CASE WHEN d.statut = 'expire' THEN 1 ELSE 0 END) AS documents_expires,
    SUM(CASE WHEN d.date_expiration IS NOT NULL 
             AND d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
             AND d.date_expiration >= CURDATE() THEN 1 ELSE 0 END) AS documents_expire_bientot,
    SUM(d.taille_octets) AS taille_totale_octets,
    ROUND(SUM(d.taille_octets) / 1048576, 2) AS taille_totale_mo,
    MAX(d.date_upload) AS derniere_mise_a_jour
FROM personnel p
LEFT JOIN documents d ON p.id = d.operateur_id
GROUP BY p.id, p.matricule, p.prenom, p.nom;

-- ============================================================================
-- Vue: Documents expirant dans les 30 jours
-- ============================================================================

CREATE OR REPLACE VIEW v_documents_expiration_proche AS
SELECT 
    d.id,
    d.operateur_id,
    p.matricule,
    CONCAT(p.prenom, ' ', p.nom) AS operateur_nom,
    c.nom AS categorie_nom,
    d.nom_affichage,
    d.date_expiration,
    DATEDIFF(d.date_expiration, CURDATE()) AS jours_restants,
    d.statut
FROM documents d
INNER JOIN personnel p ON d.operateur_id = p.id
INNER JOIN categories_documents c ON d.categorie_id = c.id
WHERE d.date_expiration IS NOT NULL
  AND d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
  AND d.date_expiration >= CURDATE()
  AND d.statut = 'actif'
ORDER BY d.date_expiration ASC;
