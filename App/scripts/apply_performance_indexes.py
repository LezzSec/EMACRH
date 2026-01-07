# -*- coding: utf-8 -*-
"""
Script d'application des index de performance.
Applique la migration 001_add_performance_indexes.sql
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer core
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.db.configbd import DatabaseConnection


def apply_performance_indexes():
    """Applique les index de performance à la base de données"""

    # Chemin du fichier SQL
    sql_file = Path(__file__).resolve().parents[1] / "database" / "migrations" / "001_add_performance_indexes.sql"

    if not sql_file.exists():
        print(f"❌ Fichier SQL introuvable : {sql_file}")
        return False

    print("📖 Lecture du fichier SQL...")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Séparer les commandes SQL (ignorer les commentaires et lignes vides)
    commands = []
    current_command = []

    for line in sql_content.split('\n'):
        # Ignorer les lignes de commentaires
        line_stripped = line.strip()
        if line_stripped.startswith('--') or not line_stripped:
            continue

        current_command.append(line)

        # Si la ligne se termine par ';', c'est la fin de la commande
        if line_stripped.endswith(';'):
            commands.append('\n'.join(current_command))
            current_command = []

    print(f"📊 {len(commands)} commandes SQL à exécuter...\n")

    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()

            success_count = 0
            skip_count = 0
            error_count = 0

            for i, command in enumerate(commands, 1):
                # Ignorer les commandes USE et SELECT (affichage)
                if command.strip().upper().startswith(('USE ', 'SELECT ')):
                    skip_count += 1
                    continue

                try:
                    cursor.execute(command)
                    success_count += 1

                    # Extraire le nom de l'index depuis la commande
                    if 'CREATE' in command and 'INDEX' in command:
                        # Extraire le nom de l'index
                        parts = command.split()
                        try:
                            idx_pos = parts.index('INDEX')
                            if idx_pos + 1 < len(parts):
                                index_name = parts[idx_pos + 1]
                                # Nettoyer le nom (enlever IF NOT EXISTS)
                                if index_name == 'IF':
                                    index_name = parts[idx_pos + 4]
                                print(f"  ✅ [{i}/{len(commands)}] Index créé : {index_name}")
                        except (ValueError, IndexError):
                            print(f"  ✅ [{i}/{len(commands)}] Commande exécutée")
                    else:
                        print(f"  ✅ [{i}/{len(commands)}] Commande exécutée")

                except Exception as e:
                    error_str = str(e)
                    # Si l'index existe déjà, ce n'est pas grave
                    if 'Duplicate key name' in error_str or 'already exists' in error_str:
                        print(f"  ⚠️  [{i}/{len(commands)}] Index déjà existant (ignoré)")
                        skip_count += 1
                    else:
                        print(f"  ❌ [{i}/{len(commands)}] Erreur : {e}")
                        error_count += 1

            cursor.close()

            print("\n" + "="*60)
            print(f"📊 RÉSUMÉ DE L'EXÉCUTION")
            print("="*60)
            print(f"  ✅ Succès      : {success_count}")
            print(f"  ⚠️  Ignorés     : {skip_count}")
            print(f"  ❌ Erreurs     : {error_count}")
            print(f"  📋 Total       : {len(commands)}")
            print("="*60)

            if error_count == 0:
                print("\n🎉 Migration appliquée avec succès !")
                print("\n💡 Les requêtes suivantes seront maintenant beaucoup plus rapides :")
                print("   - Filtrage par statut (personnel.statut = 'ACTIF')")
                print("   - Recherche d'évaluations en retard")
                print("   - Jointures polyvalence ↔ personnel ↔ postes")
                print("   - Historique des actions")
                print("   - Requêtes d'authentification")
                return True
            else:
                print(f"\n⚠️ Migration terminée avec {error_count} erreur(s)")
                return False

    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution : {e}")
        return False


def verify_indexes():
    """Vérifie que les index ont bien été créés"""
    print("\n" + "="*60)
    print("🔍 VÉRIFICATION DES INDEX CRÉÉS")
    print("="*60)

    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
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
                ORDER BY TABLE_NAME, INDEX_NAME
            """)

            indexes = cursor.fetchall()
            cursor.close()

            if not indexes:
                print("❌ Aucun index trouvé (problème potentiel)")
                return False

            print(f"\n📊 {len(indexes)} index de performance détectés :\n")

            current_table = None
            for idx in indexes:
                if current_table != idx['TABLE_NAME']:
                    current_table = idx['TABLE_NAME']
                    print(f"\n📋 Table : {current_table}")

                unique_str = " [UNIQUE]" if not idx['NON_UNIQUE'] else ""
                print(f"   ✓ {idx['INDEX_NAME']:<40} → {idx['COLUMNS']}{unique_str}")

            print("\n✅ Vérification terminée avec succès !")
            return True

    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("🚀 APPLICATION DES INDEX DE PERFORMANCE")
    print("="*60)
    print("\nCe script va créer des index sur les tables suivantes :")
    print("  • personnel (statut, matricule, nom/prénom)")
    print("  • polyvalence (operateur_id, poste_id, dates)")
    print("  • postes (code, atelier_id, statut)")
    print("  • historique (date, table, utilisateur)")
    print("  • contrats (operateur_id, dates)")
    print("  • absences (operateur_id, dates)")
    print("  • utilisateurs (username, role_id)")
    print("  • permissions (role_id, module)")
    print("  • documents (operateur_id, categorie)")
    print("\n⏱️  Impact : amélioration 10-100x des performances de lecture")
    print("💾 Espace disque : +5-10% de la taille actuelle de la base")
    print("")

    response = input("Continuer ? (o/n) : ").strip().lower()
    if response != 'o':
        print("❌ Opération annulée")
        sys.exit(0)

    print("")
    success = apply_performance_indexes()

    if success:
        print("")
        verify_indexes()

    print("\n" + "="*60)
    if success:
        print("✅ MIGRATION TERMINÉE AVEC SUCCÈS")
    else:
        print("⚠️ MIGRATION TERMINÉE AVEC AVERTISSEMENTS")
    print("="*60)
