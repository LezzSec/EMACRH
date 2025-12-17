# -*- coding: utf-8 -*-
"""
Script simplifie pour appliquer la migration (compatible Windows console)
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.configbd import get_connection


def apply_migration():
    """Applique la migration pour creer les tables de gestion des utilisateurs"""
    print(">> Application de la migration du systeme de gestion des utilisateurs...")

    # Lire le fichier de migration
    migration_file = os.path.join(
        os.path.dirname(__file__),
        '..',
        'database',
        'migrations',
        '001_add_user_management.sql'
    )

    if not os.path.exists(migration_file):
        print(f"[ERREUR] Fichier de migration introuvable: {migration_file}")
        return False

    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    # Connexion a la base de donnees
    conn = get_connection()
    if not conn:
        print("[ERREUR] Impossible de se connecter a la base de donnees")
        return False

    cursor = conn.cursor()

    try:
        # Separer les commandes SQL
        statements = []
        current_statement = []

        for line in migration_sql.split('\n'):
            # Ignorer les commentaires
            if line.strip().startswith('--') or line.strip().startswith('/*') or line.strip().startswith('*/'):
                continue

            # Ignorer les lignes de configuration MySQL
            if line.strip().startswith('/*!'):
                continue

            current_statement.append(line)

            # Si la ligne se termine par un point-virgule, c'est la fin d'une commande
            if line.strip().endswith(';'):
                statement = '\n'.join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []

        # Executer chaque commande
        for i, statement in enumerate(statements, 1):
            if statement.strip():
                try:
                    print(f"[INFO] Execution de la commande {i}/{len(statements)}...")
                    cursor.execute(statement)
                    conn.commit()
                    print(f"[OK] Commande {i}/{len(statements)} executee avec succes")
                except Exception as e:
                    # Certaines commandes peuvent echouer si les tables existent deja
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"[INFO] Commande {i} ignoree (table/donnee existante)")
                    else:
                        print(f"[ERREUR] Erreur lors de l'execution de la commande {i}: {e}")
                        raise

        print("\n[SUCCES] Migration appliquee avec succes!")
        print("\n[INFO] Informations importantes:")
        print("   - Utilisateur admin cree")
        print("   - Username: admin")
        print("   - Mot de passe: admin123")
        print("   - IMPORTANT: Changez ce mot de passe lors de la premiere connexion!")
        print("\n[INFO] Roles disponibles:")
        print("   1. admin - Acces complet")
        print("   2. gestion_production - Evaluations et polyvalence (contrats en lecture seule)")
        print("   3. gestion_rh - Contrats et documents RH (polyvalence en lecture seule)")

        return True

    except Exception as e:
        print(f"\n[ERREUR] Erreur lors de l'application de la migration: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("MIGRATION: Systeme de Gestion des Utilisateurs")
    print("=" * 70)
    print()

    success = apply_migration()

    print()
    print("=" * 70)

    if success:
        print("[SUCCES] Migration terminee avec succes!")
        sys.exit(0)
    else:
        print("[ERREUR] La migration a echoue")
        sys.exit(1)
