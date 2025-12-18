# -*- coding: utf-8 -*-
"""
Script pour appliquer la migration du système de gestion des utilisateurs
"""

import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.configbd import get_connection


def apply_migration():
    """Applique la migration pour créer les tables de gestion des utilisateurs"""
    print("🚀 Application de la migration du système de gestion des utilisateurs...")

    # Lire le fichier de migration
    migration_file = os.path.join(
        os.path.dirname(__file__),
        '..',
        'database',
        'migrations',
        '001_add_user_management.sql'
    )

    if not os.path.exists(migration_file):
        print(f"❌ Fichier de migration introuvable: {migration_file}")
        return False

    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    # Connexion à la base de données
    conn = get_connection()
    if not conn:
        print("❌ Erreur de connexion à la base de données")
        return False

    cursor = conn.cursor()

    try:
        # Séparer les commandes SQL
        # Note: Cette approche simple fonctionne pour la plupart des cas
        # mais peut ne pas fonctionner avec des procédures stockées complexes
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

        # Exécuter chaque commande
        for i, statement in enumerate(statements, 1):
            if statement.strip():
                try:
                    print(f"⏳ Exécution de la commande {i}/{len(statements)}...")
                    cursor.execute(statement)
                    conn.commit()
                    print(f"✅ Commande {i}/{len(statements)} exécutée avec succès")
                except Exception as e:
                    # Certaines commandes peuvent échouer si les tables existent déjà
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"⚠️  Commande {i} ignorée (table/donnée existante)")
                    else:
                        print(f"❌ Erreur lors de l'exécution de la commande {i}: {e}")
                        raise

        print("\n✅ Migration appliquée avec succès!")
        print("\n📝 Informations importantes:")
        print("   - Utilisateur admin créé")
        print("   - Username: admin")
        print("   - Mot de passe: admin123")
        print("   - ⚠️  IMPORTANT: Changez ce mot de passe lors de la première connexion!")
        print("\n🎯 Rôles disponibles:")
        print("   1. admin - Accès complet")
        print("   2. gestion_production - Évaluations et polyvalence (contrats en lecture seule)")
        print("   3. gestion_rh - Contrats et documents RH (polyvalence en lecture seule)")

        return True

    except Exception as e:
        print(f"\n❌ Erreur lors de l'application de la migration: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("MIGRATION: Système de Gestion des Utilisateurs")
    print("=" * 70)
    print()

    success = apply_migration()

    print()
    print("=" * 70)

    if success:
        print("✅ Migration terminée avec succès!")
        sys.exit(0)
    else:
        print("❌ La migration a échoué")
        sys.exit(1)
