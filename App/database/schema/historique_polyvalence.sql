-- ============================================================================
-- Table historique_polyvalence
-- ============================================================================
-- Table dédiée pour stocker l'historique détaillé des polyvalences
-- Permet de tracer toutes les actions sur les compétences (ajout, modification, suppression)
-- avec conservation des anciennes et nouvelles valeurs
--
-- Cette table complète la table "historique" en fournissant un stockage
-- structuré spécifiquement pour les polyvalences
-- ============================================================================

CREATE TABLE IF NOT EXISTS historique_polyvalence (
    -- Identification
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_action DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Type d'action
    action_type ENUM('AJOUT', 'MODIFICATION', 'SUPPRESSION', 'IMPORT_MANUEL') NOT NULL,

    -- Références
    operateur_id INT NOT NULL,
    poste_id INT NOT NULL,
    polyvalence_id INT NULL,  -- NULL si suppression ou import manuel

    -- Données avant modification (pour MODIFICATION et SUPPRESSION)
    ancien_niveau INT NULL,
    ancienne_date_evaluation DATE NULL,
    ancienne_prochaine_evaluation DATE NULL,
    ancien_statut VARCHAR(50) NULL,

    -- Données après modification (pour AJOUT et MODIFICATION)
    nouveau_niveau INT NULL,
    nouvelle_date_evaluation DATE NULL,
    nouvelle_prochaine_evaluation DATE NULL,
    nouveau_statut VARCHAR(50) NULL,

    -- Métadonnées
    utilisateur VARCHAR(100) NULL,  -- Qui a fait l'action (utilisateur système ou import)
    commentaire TEXT NULL,  -- Commentaire libre pour import manuel
    source VARCHAR(100) NOT NULL DEFAULT 'SYSTEM',  -- SYSTEM, IMPORT_MANUEL, GUI, etc.
    import_batch_id VARCHAR(50) NULL,  -- Pour regrouper les imports par lot

    -- Données complémentaires (JSON pour flexibilité)
    metadata_json TEXT NULL,  -- Stockage JSON pour infos supplémentaires

    -- Index pour performance
    INDEX idx_operateur (operateur_id),
    INDEX idx_poste (poste_id),
    INDEX idx_date (date_action),
    INDEX idx_action (action_type),
    INDEX idx_batch (import_batch_id),

    -- Contraintes de clés étrangères
    FOREIGN KEY (operateur_id) REFERENCES personnel(id) ON DELETE CASCADE,
    FOREIGN KEY (poste_id) REFERENCES postes(id) ON DELETE CASCADE,
    FOREIGN KEY (polyvalence_id) REFERENCES polyvalence(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Vue pour faciliter les requêtes
-- ============================================================================
CREATE OR REPLACE VIEW v_historique_polyvalence_complet AS
SELECT
    hp.id,
    hp.date_action,
    hp.action_type,

    -- Informations opérateur
    pers.nom AS operateur_nom,
    pers.prenom AS operateur_prenom,
    pers.matricule AS operateur_matricule,
    hp.operateur_id,

    -- Informations poste
    pos.poste_code,
    pos.libelle AS poste_libelle,
    hp.poste_id,

    -- Anciennes valeurs
    hp.ancien_niveau,
    hp.ancienne_date_evaluation,
    hp.ancienne_prochaine_evaluation,
    hp.ancien_statut,

    -- Nouvelles valeurs
    hp.nouveau_niveau,
    hp.nouvelle_date_evaluation,
    hp.nouvelle_prochaine_evaluation,
    hp.nouveau_statut,

    -- Métadonnées
    hp.utilisateur,
    hp.commentaire,
    hp.source,
    hp.import_batch_id,
    hp.metadata_json,

    -- Calculs utiles
    CASE
        WHEN hp.action_type = 'AJOUT' THEN
            CONCAT('Ajout niveau ', hp.nouveau_niveau)
        WHEN hp.action_type = 'MODIFICATION' THEN
            CONCAT('Modification : N', hp.ancien_niveau, ' → N', hp.nouveau_niveau)
        WHEN hp.action_type = 'SUPPRESSION' THEN
            CONCAT('Suppression niveau ', hp.ancien_niveau)
        WHEN hp.action_type = 'IMPORT_MANUEL' THEN
            CONCAT('Import manuel : ', hp.commentaire)
    END AS resume

FROM historique_polyvalence hp
LEFT JOIN personnel pers ON hp.operateur_id = pers.id
LEFT JOIN postes pos ON hp.poste_id = pos.id
ORDER BY hp.date_action DESC;

-- ============================================================================
-- Trigger pour synchroniser avec la table historique principale
-- ============================================================================
DELIMITER $$

CREATE TRIGGER after_insert_historique_polyvalence
AFTER INSERT ON historique_polyvalence
FOR EACH ROW
BEGIN
    DECLARE resume_text VARCHAR(255);
    DECLARE description_json TEXT;

    -- Construire le résumé
    SET resume_text = CASE
        WHEN NEW.action_type = 'AJOUT' THEN
            CONCAT('Ajout niveau ', NEW.nouveau_niveau)
        WHEN NEW.action_type = 'MODIFICATION' THEN
            CONCAT('Modification : N', NEW.ancien_niveau, ' → N', NEW.nouveau_niveau)
        WHEN NEW.action_type = 'SUPPRESSION' THEN
            CONCAT('Suppression niveau ', NEW.ancien_niveau)
        WHEN NEW.action_type = 'IMPORT_MANUEL' THEN
            CONCAT('Import manuel')
    END;

    -- Construire le JSON de description
    SET description_json = JSON_OBJECT(
        'action_type', NEW.action_type,
        'ancien_niveau', NEW.ancien_niveau,
        'nouveau_niveau', NEW.nouveau_niveau,
        'ancienne_date_evaluation', NEW.ancienne_date_evaluation,
        'nouvelle_date_evaluation', NEW.nouvelle_date_evaluation,
        'source', NEW.source,
        'commentaire', NEW.commentaire
    );

    -- Insérer dans la table historique principale
    INSERT INTO historique (
        date_time,
        action,
        table_name,
        record_id,
        operateur_id,
        poste_id,
        description,
        utilisateur,
        source
    ) VALUES (
        NEW.date_action,
        NEW.action_type,
        'polyvalence',
        NEW.polyvalence_id,
        NEW.operateur_id,
        NEW.poste_id,
        description_json,
        NEW.utilisateur,
        CONCAT('historique_polyvalence/', NEW.source)
    );
END$$

DELIMITER ;

-- ============================================================================
-- Données de test (optionnel - à commenter en production)
-- ============================================================================
-- Exemple d'import manuel d'anciennes données
-- INSERT INTO historique_polyvalence (
--     date_action, action_type, operateur_id, poste_id,
--     nouveau_niveau, nouvelle_date_evaluation, nouvelle_prochaine_evaluation,
--     utilisateur, commentaire, source, import_batch_id
-- ) VALUES (
--     '2020-01-15 10:00:00', 'IMPORT_MANUEL', 1, 5,
--     2, '2020-01-15', '2030-01-15',
--     'admin', 'Import des données historiques de janvier 2020', 'IMPORT_MANUEL', 'BATCH_2020_01'
-- );
