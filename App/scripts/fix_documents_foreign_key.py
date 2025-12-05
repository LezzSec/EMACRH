# -*- coding: utf-8 -*-
"""
Script de correction de la clé étrangère de la table documents
Change la référence de 'operateurs' vers 'personnel'
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier parent au PATH pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.configbd import get_connection


def fix_foreign_key():
    """
    Corrige la clé étrangère de la table documents
    pour qu'elle pointe vers 'personnel' au lieu de 'operateurs'
    """

    print("="*70)
    print("  Correction de la clé étrangère - Table documents")
    print("="*70)
    print()

    conn = None
    cur = None

    try:
        print("Connexion a la base de donnees...")
        conn = get_connection()
        cur = conn.cursor()
        print("OK - Connexion reussie\n")

        # Vérifier si la table documents existe
        print("Verification de l'existence de la table 'documents'...")
        cur.execute("SHOW TABLES LIKE 'documents'")
        if not cur.fetchone():
            print("ATTENTION - La table 'documents' n'existe pas encore.")
            print("   Veuillez d'abord executer le script d'installation :")
            print("   python install_gestion_documentaire.py")
            return

        print("OK - Table 'documents' trouvee\n")

        # Vérifier les contraintes existantes
        print("Verification des contraintes de cles etrangeres...")
        cur.execute("""
            SELECT CONSTRAINT_NAME, REFERENCED_TABLE_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'emac_db'
            AND TABLE_NAME = 'documents'
            AND REFERENCED_TABLE_NAME IS NOT NULL
            AND COLUMN_NAME = 'operateur_id'
        """)
        constraints = cur.fetchall()

        if not constraints:
            print("ATTENTION - Aucune contrainte de cle etrangere trouvee sur 'operateur_id'\n")
        else:
            for constraint in constraints:
                constraint_name = constraint[0]
                referenced_table = constraint[1]
                print(f"   Contrainte trouvee: {constraint_name} -> {referenced_table}")

                # Supprimer la contrainte existante
                print(f"Suppression de la contrainte '{constraint_name}'...")
                cur.execute(f"""
                    ALTER TABLE documents
                    DROP FOREIGN KEY {constraint_name}
                """)
                print(f"OK - Contrainte '{constraint_name}' supprimee\n")

        # Vérifier que la table personnel existe
        print("Verification de l'existence de la table 'personnel'...")
        cur.execute("SHOW TABLES LIKE 'personnel'")
        if not cur.fetchone():
            print("ERREUR: La table 'personnel' n'existe pas!")
            print("   Impossible de creer la contrainte de cle etrangere.")
            return

        print("OK - Table 'personnel' trouvee\n")

        # Créer la nouvelle contrainte
        print("Creation de la nouvelle contrainte 'fk_documents_personnel'...")
        try:
            cur.execute("""
                ALTER TABLE documents
                ADD CONSTRAINT fk_documents_personnel
                    FOREIGN KEY (operateur_id)
                    REFERENCES personnel(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            """)
            print("OK - Contrainte 'fk_documents_personnel' creee\n")
        except Exception as e:
            if "Duplicate key" in str(e) or "already exists" in str(e):
                print("ATTENTION - La contrainte 'fk_documents_personnel' existe deja\n")
            else:
                raise

        # Commit des changements
        conn.commit()

        print("="*70)
        print("OK - Correction terminee avec succes!")
        print("="*70)
        print()
        print("La table 'documents' utilise maintenant la table 'personnel'")
        print("comme reference pour les employes.")
        print()

    except Exception as e:
        print(f"\nERREUR lors de la correction: {e}")
        if conn:
            conn.rollback()
        raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    try:
        fix_foreign_key()
        print("Appuyez sur Entree pour quitter...")
        input()
    except KeyboardInterrupt:
        print("\n\nCorrection annulee par l'utilisateur")
    except Exception as e:
        print(f"\nErreur fatale: {e}")
        print("\nAppuyez sur Entree pour quitter...")
        input()
