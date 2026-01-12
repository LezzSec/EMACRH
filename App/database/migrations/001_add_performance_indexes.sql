-- =====================================================================
-- Migration 001 : Ajout des index de performance
-- Date : 2026-01-07
-- Description : Ajout d'index sur les colonnes fréquemment utilisées
--               dans les WHERE, JOIN et ORDER BY pour améliorer les performances
-- =====================================================================

USE emac_db;

-- =====================================================================
-- 1. INDEX SUR LA TABLE personnel
-- =====================================================================

-- Index sur le statut (très utilisé pour filtrer ACTIF/INACTIF)
-- Exemple : WHERE statut = 'ACTIF'
CREATE INDEX IF NOT EXISTS idx_personnel_statut
    ON personnel(statut);

-- Index sur le matricule (recherche fréquente)
-- Exemple : WHERE matricule = 'ABC123'
CREATE INDEX IF NOT EXISTS idx_personnel_matricule
    ON personnel(matricule);

-- Index composite pour les recherches nom/prénom
-- Exemple : WHERE nom LIKE '%Dupont%' AND prenom LIKE '%Jean%'
CREATE INDEX IF NOT EXISTS idx_personnel_nom_prenom
    ON personnel(nom, prenom);


-- =====================================================================
-- 2. INDEX SUR LA TABLE polyvalence (CRITIQUES POUR PERFORMANCE)
-- =====================================================================

-- Index sur operateur_id (très utilisé dans les JOIN et WHERE)
-- Exemple : JOIN polyvalence p ON p.operateur_id = personnel.id
CREATE INDEX IF NOT EXISTS idx_polyvalence_operateur_id
    ON polyvalence(operateur_id);

-- Index sur poste_id (très utilisé dans les JOIN)
-- Exemple : JOIN polyvalence p ON p.poste_id = postes.id
CREATE INDEX IF NOT EXISTS idx_polyvalence_poste_id
    ON polyvalence(poste_id);

-- Index sur prochaine_evaluation (TRI et FILTRE des évaluations en retard)
-- Exemple : WHERE prochaine_evaluation < CURDATE() ORDER BY prochaine_evaluation
CREATE INDEX IF NOT EXISTS idx_polyvalence_prochaine_eval
    ON polyvalence(prochaine_evaluation);

-- Index sur date_evaluation (pour historique et tris)
-- Exemple : ORDER BY date_evaluation DESC
CREATE INDEX IF NOT EXISTS idx_polyvalence_date_eval
    ON polyvalence(date_evaluation);

-- Index composite pour les requêtes combinées
-- Exemple : WHERE operateur_id = 5 AND prochaine_evaluation < CURDATE()
CREATE INDEX IF NOT EXISTS idx_polyvalence_operateur_prochaine
    ON polyvalence(operateur_id, prochaine_evaluation);

-- Index pour les recherches par poste et niveau
-- Exemple : WHERE poste_id = 10 AND niveau >= 3
CREATE INDEX IF NOT EXISTS idx_polyvalence_poste_niveau
    ON polyvalence(poste_id, niveau);


-- =====================================================================
-- 3. INDEX SUR LA TABLE postes
-- =====================================================================

-- Index sur poste_code (recherche par code de poste)
-- Exemple : WHERE poste_code = '0506'
CREATE INDEX IF NOT EXISTS idx_postes_code
    ON postes(poste_code);

-- Index sur atelier_id (JOIN avec table atelier)
-- Exemple : WHERE atelier_id = 5
CREATE INDEX IF NOT EXISTS idx_postes_atelier_id
    ON postes(atelier_id);

-- Index sur statut (filtrage des postes actifs/inactifs)
-- Exemple : WHERE statut = 'ACTIF'
CREATE INDEX IF NOT EXISTS idx_postes_statut
    ON postes(statut);


-- =====================================================================
-- 4. INDEX SUR LA TABLE historique (logs)
-- =====================================================================

-- Index sur date_action (pour filtrer par période)
-- Exemple : WHERE date_action BETWEEN '2024-01-01' AND '2024-12-31'
CREATE INDEX IF NOT EXISTS idx_historique_date_action
    ON historique(date_action);

-- Index sur table_name (pour filtrer les actions sur une table)
-- Exemple : WHERE table_name = 'personnel'
CREATE INDEX IF NOT EXISTS idx_historique_table_name
    ON historique(table_name);

-- Index sur utilisateur (pour voir l'historique d'un utilisateur)
-- Exemple : WHERE utilisateur = 'admin'
CREATE INDEX IF NOT EXISTS idx_historique_utilisateur
    ON historique(utilisateur);

-- Index composite pour requêtes courantes
-- Exemple : WHERE table_name = 'personnel' AND date_action > '2024-01-01' ORDER BY date_action DESC
CREATE INDEX IF NOT EXISTS idx_historique_table_date
    ON historique(table_name, date_action);


-- =====================================================================
-- 5. INDEX SUR LA TABLE contrats
-- =====================================================================

-- Index sur operateur_id (JOIN avec personnel)
-- Exemple : WHERE operateur_id = 5
CREATE INDEX IF NOT EXISTS idx_contrats_operateur_id
    ON contrats(operateur_id);

-- Index sur date_fin (pour les contrats arrivant à échéance)
-- Exemple : WHERE date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
CREATE INDEX IF NOT EXISTS idx_contrats_date_fin
    ON contrats(date_fin);

-- Index sur type_contrat (filtrage par type)
-- Exemple : WHERE type_contrat = 'CDI'
CREATE INDEX IF NOT EXISTS idx_contrats_type
    ON contrats(type_contrat);

-- Index composite pour requêtes d'alertes
-- Exemple : WHERE operateur_id = 5 AND date_fin < DATE_ADD(CURDATE(), INTERVAL 7 DAY)
CREATE INDEX IF NOT EXISTS idx_contrats_operateur_date_fin
    ON contrats(operateur_id, date_fin);


-- =====================================================================
-- 6. INDEX SUR LA TABLE absences
-- =====================================================================

-- Index sur operateur_id (JOIN avec personnel)
-- Exemple : WHERE operateur_id = 5
CREATE INDEX IF NOT EXISTS idx_absences_operateur_id
    ON absences(operateur_id);

-- Index sur date_debut (pour filtrer par période)
-- Exemple : WHERE date_debut >= '2024-01-01'
CREATE INDEX IF NOT EXISTS idx_absences_date_debut
    ON absences(date_debut);

-- Index sur date_fin (pour les absences en cours)
-- Exemple : WHERE date_fin IS NULL OR date_fin >= CURDATE()
CREATE INDEX IF NOT EXISTS idx_absences_date_fin
    ON absences(date_fin);

-- Index composite pour requêtes courantes
-- Exemple : WHERE operateur_id = 5 AND date_debut <= '2024-12-31' AND (date_fin IS NULL OR date_fin >= '2024-01-01')
CREATE INDEX IF NOT EXISTS idx_absences_operateur_dates
    ON absences(operateur_id, date_debut, date_fin);


-- =====================================================================
-- 7. INDEX SUR LA TABLE utilisateurs (système d'authentification)
-- =====================================================================

-- Index UNIQUE sur username (recherche login rapide + unicité)
-- Exemple : WHERE username = 'admin'
CREATE UNIQUE INDEX IF NOT EXISTS idx_utilisateurs_username
    ON utilisateurs(username);

-- Index sur role_id (JOIN avec roles)
-- Exemple : JOIN roles r ON u.role_id = r.id
CREATE INDEX IF NOT EXISTS idx_utilisateurs_role_id
    ON utilisateurs(role_id);

-- Index sur actif (filtrer utilisateurs actifs)
-- Exemple : WHERE actif = 1
CREATE INDEX IF NOT EXISTS idx_utilisateurs_actif
    ON utilisateurs(actif);


-- =====================================================================
-- 8. INDEX SUR LA TABLE permissions
-- =====================================================================

-- Index sur role_id (JOIN avec roles)
-- Exemple : WHERE role_id = 1
CREATE INDEX IF NOT EXISTS idx_permissions_role_id
    ON permissions(role_id);

-- Index composite pour les vérifications de permissions
-- Exemple : WHERE role_id = 1 AND module = 'personnel'
CREATE INDEX IF NOT EXISTS idx_permissions_role_module
    ON permissions(role_id, module);


-- =====================================================================
-- 9. INDEX SUR LA TABLE documents
-- =====================================================================

-- Index sur operateur_id (JOIN avec personnel)
-- Exemple : WHERE operateur_id = 5
CREATE INDEX IF NOT EXISTS idx_documents_operateur_id
    ON documents(operateur_id);

-- Index sur date_upload (tri par date)
-- Exemple : ORDER BY date_upload DESC
CREATE INDEX IF NOT EXISTS idx_documents_date_upload
    ON documents(date_upload);

-- Index sur categorie (filtrage par type de document)
-- Exemple : WHERE categorie = 'CONTRAT'
CREATE INDEX IF NOT EXISTS idx_documents_categorie
    ON documents(categorie);


-- =====================================================================
-- VÉRIFICATION : Afficher tous les index créés
-- =====================================================================

SELECT
    TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as COLUMNS,
    INDEX_TYPE,
    NON_UNIQUE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'emac_db'
  AND INDEX_NAME LIKE 'idx_%'
GROUP BY TABLE_NAME, INDEX_NAME, INDEX_TYPE, NON_UNIQUE
ORDER BY TABLE_NAME, INDEX_NAME;


-- =====================================================================
-- NOTES D'UTILISATION
-- =====================================================================

-- Pour appliquer cette migration :
-- 1. En ligne de commande :
--    mysql -u root -p emac_db < 001_add_performance_indexes.sql
--
-- 2. Via un script Python :
--    python App/scripts/apply_migration.py 001_add_performance_indexes.sql
--
-- 3. Vérifier les index créés :
--    SHOW INDEX FROM polyvalence;
--    SHOW INDEX FROM personnel;
--
-- 4. Analyser les requêtes avec EXPLAIN :
--    EXPLAIN SELECT * FROM polyvalence WHERE prochaine_evaluation < CURDATE();
--
-- =====================================================================
-- IMPACT ATTENDU
-- =====================================================================

-- ✅ Requêtes 10-100x plus rapides sur les tables avec beaucoup de données
-- ✅ Réduction de la charge CPU du serveur MySQL
-- ✅ Amélioration du temps de réponse de l'application (notamment au démarrage)
-- ✅ Meilleure scalabilité si le nombre d'opérateurs/évaluations augmente
--
-- ⚠️ Impact minime sur les INSERT/UPDATE (overhead négligeable)
-- ⚠️ Espace disque supplémentaire : environ 5-10% de la taille de la base
--
-- =====================================================================
