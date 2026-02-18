-- ============================================================================
-- Migration 021: Création du compte MySQL dédié pour l'application EMAC
-- Date: 2026-02-18
-- Description: Remplace l'utilisation du compte root par un compte applicatif
--              avec les privilèges minimaux nécessaires (principe du moindre
--              privilège).
--
-- USAGE:
--   Exécuter une seule fois en tant qu'administrateur MySQL (root) :
--   mysql -u root -p < 021_create_app_user.sql
--
-- APRÈS L'EXÉCUTION:
--   Mettre à jour App/.env :
--     EMAC_DB_USER=emac_app
--     EMAC_DB_PASSWORD=<mot_de_passe_choisi>
-- ============================================================================

-- 1. Choisir un mot de passe fort ici avant d'exécuter
SET @emac_password = 'CHANGER_CE_MOT_DE_PASSE';

-- 2. Créer le compte applicatif (localhost uniquement = pas d'accès réseau externe)
CREATE USER IF NOT EXISTS 'emac_app'@'localhost' IDENTIFIED BY 'CHANGER_CE_MOT_DE_PASSE';

-- 3. Révoquer tous les privilèges existants (nettoyage)
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'emac_app'@'localhost';

-- 4. Accorder uniquement les privilèges DML sur emac_db
--    SELECT + INSERT + UPDATE + DELETE = tout ce que l'application utilise
--    Pas de CREATE, ALTER, DROP, TRUNCATE, LOCK TABLES, etc.
GRANT SELECT, INSERT, UPDATE, DELETE ON emac_db.* TO 'emac_app'@'localhost';

-- 5. Accès information_schema en lecture seule
--    Utilisé par event_rule_service.py et template_service.py
--    pour vérifier l'existence de tables (SELECT COUNT(*) FROM information_schema.tables)
--    Note: information_schema est accessible en SELECT par défaut pour tout utilisateur,
--    pas besoin de GRANT explicite sur MySQL 8.0+

-- 6. Appliquer
FLUSH PRIVILEGES;

-- 7. Vérification
SELECT
    User,
    Host,
    Select_priv,
    Insert_priv,
    Update_priv,
    Delete_priv,
    Create_priv,
    Drop_priv,
    Alter_priv,
    Super_priv,
    Grant_priv,
    File_priv
FROM mysql.user
WHERE User = 'emac_app';

-- Résultat attendu:
-- Select_priv = N (couvert par GRANT sur emac_db.*)
-- Insert_priv = N (couvert par GRANT sur emac_db.*)
-- Update_priv = N (couvert par GRANT sur emac_db.*)
-- Delete_priv = N (couvert par GRANT sur emac_db.*)
-- Create_priv = N  ← pas de DDL
-- Drop_priv   = N  ← pas de DDL
-- Alter_priv  = N  ← pas de DDL
-- Super_priv  = N  ← pas de super-user
-- Grant_priv  = N  ← ne peut pas modifier les permissions
-- File_priv   = N  ← pas d'accès système de fichiers
