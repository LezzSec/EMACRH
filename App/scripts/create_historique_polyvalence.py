# -*- coding: utf-8 -*-
"""
Script de création de la table historique_polyvalence
Permet de stocker l'historique détaillé des polyvalences avec possibilité d'import manuel
"""

from core.db.configbd import get_connection
import sys

def create_historique_polyvalence_table():
    """Crée la table historique_polyvalence et ses structures associées."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        print("=" * 70)
        print("Création de la table historique_polyvalence")
        print("=" * 70)

        # 1. Créer la table principale
        print("\n[1/4] Création de la table historique_polyvalence...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS historique_polyvalence (
                -- Identification
                id INT AUTO_INCREMENT PRIMARY KEY,
                date_action DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

                -- Type d'action
                action_type ENUM('AJOUT', 'MODIFICATION', 'SUPPRESSION', 'IMPORT_MANUEL') NOT NULL,

                -- Références
                operateur_id INT NOT NULL,
                poste_id INT NOT NULL,
                polyvalence_id INT NULL,

                -- Données avant modification
                ancien_niveau INT NULL,
                ancienne_date_evaluation DATE NULL,
                ancienne_prochaine_evaluation DATE NULL,
                ancien_statut VARCHAR(50) NULL,

                -- Données après modification
                nouveau_niveau INT NULL,
                nouvelle_date_evaluation DATE NULL,
                nouvelle_prochaine_evaluation DATE NULL,
                nouveau_statut VARCHAR(50) NULL,

                -- Métadonnées
                utilisateur VARCHAR(100) NULL,
                commentaire TEXT NULL,
                source VARCHAR(100) NOT NULL DEFAULT 'SYSTEM',
                import_batch_id VARCHAR(50) NULL,
                metadata_json TEXT NULL,

                -- Index
                INDEX idx_operateur (operateur_id),
                INDEX idx_poste (poste_id),
                INDEX idx_date (date_action),
                INDEX idx_action (action_type),
                INDEX idx_batch (import_batch_id),

                -- Contraintes
                FOREIGN KEY (operateur_id) REFERENCES personnel(id) ON DELETE CASCADE,
                FOREIGN KEY (poste_id) REFERENCES postes(id) ON DELETE CASCADE,
                FOREIGN KEY (polyvalence_id) REFERENCES polyvalence(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        conn.commit()
        print("[OK] Table historique_polyvalence créée")

        # 2. Créer la vue
        print("\n[2/4] Création de la vue v_historique_polyvalence_complet...")
        cur.execute("DROP VIEW IF EXISTS v_historique_polyvalence_complet")
        cur.execute("""
            CREATE VIEW v_historique_polyvalence_complet AS
            SELECT
                hp.id,
                hp.date_action,
                hp.action_type,

                pers.nom AS operateur_nom,
                pers.prenom AS operateur_prenom,
                pers.matricule AS operateur_matricule,
                hp.operateur_id,

                pos.poste_code,
                hp.poste_id,

                hp.ancien_niveau,
                hp.ancienne_date_evaluation,
                hp.ancienne_prochaine_evaluation,
                hp.ancien_statut,

                hp.nouveau_niveau,
                hp.nouvelle_date_evaluation,
                hp.nouvelle_prochaine_evaluation,
                hp.nouveau_statut,

                hp.utilisateur,
                hp.commentaire,
                hp.source,
                hp.import_batch_id,
                hp.metadata_json,

                CASE
                    WHEN hp.action_type = 'AJOUT' THEN
                        CONCAT('Ajout niveau ', hp.nouveau_niveau)
                    WHEN hp.action_type = 'MODIFICATION' THEN
                        CONCAT('Modification : N', hp.ancien_niveau, ' → N', hp.nouveau_niveau)
                    WHEN hp.action_type = 'SUPPRESSION' THEN
                        CONCAT('Suppression niveau ', hp.ancien_niveau)
                    WHEN hp.action_type = 'IMPORT_MANUEL' THEN
                        CONCAT('Import manuel : ', COALESCE(hp.commentaire, ''))
                END AS resume

            FROM historique_polyvalence hp
            LEFT JOIN personnel pers ON hp.operateur_id = pers.id
            LEFT JOIN postes pos ON hp.poste_id = pos.id
            ORDER BY hp.date_action DESC
        """)
        conn.commit()
        print("[OK] Vue v_historique_polyvalence_complet créée")

        # 3. Créer le trigger
        print("\n[3/4] Création du trigger de synchronisation...")
        cur.execute("DROP TRIGGER IF EXISTS after_insert_historique_polyvalence")
        cur.execute("""
            CREATE TRIGGER after_insert_historique_polyvalence
            AFTER INSERT ON historique_polyvalence
            FOR EACH ROW
            BEGIN
                DECLARE resume_text VARCHAR(255);
                DECLARE description_json TEXT;

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

                SET description_json = JSON_OBJECT(
                    'action_type', NEW.action_type,
                    'ancien_niveau', NEW.ancien_niveau,
                    'nouveau_niveau', NEW.nouveau_niveau,
                    'ancienne_date_evaluation', NEW.ancienne_date_evaluation,
                    'nouvelle_date_evaluation', NEW.nouvelle_date_evaluation,
                    'source', NEW.source,
                    'commentaire', NEW.commentaire
                );

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
            END
        """)
        conn.commit()
        print("[OK] Trigger after_insert_historique_polyvalence créé")

        # 4. Afficher la structure finale
        print("\n[4/4] Vérification de la structure...")
        cur.execute("DESCRIBE historique_polyvalence")
        rows = cur.fetchall()

        print("\n" + "=" * 70)
        print("Structure de la table historique_polyvalence :")
        print("=" * 70)
        for row in rows:
            print(f"  {row[0]:35s} {row[1]:25s} {row[2]}")

        print("\n" + "=" * 70)
        print("[OK] Table historique_polyvalence créée avec succès !")
        print("=" * 70)
        print("\nFonctionnalités disponibles :")
        print("  - Traçabilité automatique des modifications de polyvalences")
        print("  - Import manuel de données historiques")
        print("  - Vue complète avec jointures (v_historique_polyvalence_complet)")
        print("  - Synchronisation automatique avec la table historique")
        print("\nUtilisation :")
        print("  - Voir: scripts/import_historique_polyvalence.py")
        print("  - Service: core/services/polyvalence_logger.py")

    except Exception as e:
        print(f"[ERREUR] {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

    return True


if __name__ == "__main__":
    success = create_historique_polyvalence_table()
    sys.exit(0 if success else 1)
