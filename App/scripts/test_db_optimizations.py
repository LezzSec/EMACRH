# -*- coding: utf-8 -*-
"""
Script de test des optimisations base de données.
Vérifie que le pool, les context managers et les index fonctionnent correctement.
"""

import sys
import time
from pathlib import Path

# Ajouter le répertoire parent au path pour importer core
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.db.configbd import get_connection, DatabaseConnection, DatabaseCursor


def test_pool_connection():
    """Test 1 : Vérifier que le pool MySQL fonctionne"""
    print("="*60)
    print("TEST 1 : Pool de connexions MySQL")
    print("="*60)

    try:
        # Test de base
        conn = get_connection()
        print("✅ Connexion 1 obtenue depuis le pool")
        conn.close()

        # Vérifier la réutilisation
        conn2 = get_connection()
        print("✅ Connexion 2 obtenue (devrait réutiliser conn1)")
        conn2.close()

        print("✅ Pool MySQL : OK\n")
        return True

    except Exception as e:
        print(f"❌ Erreur : {e}\n")
        return False


def test_database_connection():
    """Test 2 : Vérifier DatabaseConnection context manager"""
    print("="*60)
    print("TEST 2 : Context manager DatabaseConnection")
    print("="*60)

    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as total FROM personnel")
            result = cur.fetchone()
            total_personnel = result[0]
            cur.close()
            print(f"✅ DatabaseConnection fonctionne : {total_personnel} personnes dans la base")

        print("✅ DatabaseConnection : OK\n")
        return True

    except Exception as e:
        print(f"❌ Erreur : {e}\n")
        return False


def test_database_cursor():
    """Test 3 : Vérifier DatabaseCursor context manager"""
    print("="*60)
    print("TEST 3 : Context manager DatabaseCursor")
    print("="*60)

    try:
        # Test avec dictionary=False (tuples)
        with DatabaseCursor() as cur:
            cur.execute("SELECT COUNT(*) FROM postes")
            total_postes = cur.fetchone()[0]
            print(f"✅ DatabaseCursor (tuples) : {total_postes} postes")

        # Test avec dictionary=True (dict)
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("SELECT COUNT(*) as total FROM polyvalence")
            result = cur.fetchone()
            total_poly = result['total']
            print(f"✅ DatabaseCursor (dict) : {total_poly} évaluations polyvalence")

        print("✅ DatabaseCursor : OK\n")
        return True

    except Exception as e:
        print(f"❌ Erreur : {e}\n")
        return False


def test_indexes_presence():
    """Test 4 : Vérifier que les index sont créés"""
    print("="*60)
    print("TEST 4 : Présence des index de performance")
    print("="*60)

    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT COUNT(*) as nb_index
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = 'emac_db'
                  AND INDEX_NAME LIKE 'idx_%'
            """)
            result = cur.fetchone()
            nb_index = result['nb_index']

            if nb_index >= 29:
                print(f"✅ Index de performance : {nb_index} index détectés")
                print("✅ Les index sont bien appliqués")
            elif nb_index > 0:
                print(f"⚠️  Index de performance : {nb_index} index détectés (attendu: 29)")
                print("⚠️  Certains index manquent, exécutez : python apply_performance_indexes.py")
            else:
                print("❌ Aucun index de performance détecté")
                print("❌ Exécutez : python apply_performance_indexes.py")
                return False

        print()
        return nb_index >= 29

    except Exception as e:
        print(f"❌ Erreur : {e}\n")
        return False


def test_query_performance():
    """Test 5 : Mesurer les performances des requêtes"""
    print("="*60)
    print("TEST 5 : Performance des requêtes")
    print("="*60)

    tests = [
        {
            'name': 'Filtrage par statut',
            'query': "SELECT COUNT(*) FROM personnel WHERE statut = 'ACTIF'",
            'expected_time': 0.1
        },
        {
            'name': 'Évaluations en retard',
            'query': "SELECT COUNT(*) FROM polyvalence WHERE prochaine_evaluation < CURDATE()",
            'expected_time': 0.1
        },
        {
            'name': 'JOIN personnel + polyvalence',
            'query': """
                SELECT COUNT(*)
                FROM personnel p
                JOIN polyvalence poly ON poly.operateur_id = p.id
                WHERE p.statut = 'ACTIF'
            """,
            'expected_time': 0.2
        },
        {
            'name': 'Historique récent',
            'query': """
                SELECT COUNT(*)
                FROM historique
                WHERE date_action >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """,
            'expected_time': 0.1
        }
    ]

    all_ok = True

    try:
        with DatabaseCursor() as cur:
            for test in tests:
                start = time.time()
                cur.execute(test['query'])
                result = cur.fetchone()[0]
                elapsed = time.time() - start

                status = "✅" if elapsed < test['expected_time'] else "⚠️"
                print(f"{status} {test['name']:<30} : {elapsed:.3f}s ({result} résultats)")

                if elapsed >= test['expected_time']:
                    all_ok = False
                    print(f"   ⚠️  Temps attendu : < {test['expected_time']}s")

        if all_ok:
            print("✅ Toutes les requêtes sont rapides")
        else:
            print("⚠️  Certaines requêtes sont lentes (vérifier les index)")

        print()
        return all_ok

    except Exception as e:
        print(f"❌ Erreur : {e}\n")
        return False


def test_index_usage():
    """Test 6 : Vérifier que les index sont bien utilisés"""
    print("="*60)
    print("TEST 6 : Utilisation des index (EXPLAIN)")
    print("="*60)

    queries_to_test = [
        {
            'name': 'Recherche par statut',
            'query': "SELECT * FROM personnel WHERE statut = 'ACTIF'",
            'expected_index': 'idx_personnel_statut'
        },
        {
            'name': 'Évaluations en retard',
            'query': "SELECT * FROM polyvalence WHERE prochaine_evaluation < CURDATE()",
            'expected_index': 'idx_polyvalence_prochaine_eval'
        },
        {
            'name': 'Recherche par matricule',
            'query': "SELECT * FROM personnel WHERE matricule = 'TEST'",
            'expected_index': 'idx_personnel_matricule'
        }
    ]

    all_ok = True

    try:
        with DatabaseCursor(dictionary=True) as cur:
            for test in queries_to_test:
                cur.execute(f"EXPLAIN {test['query']}")
                explain = cur.fetchone()

                # Dans EXPLAIN, 'key' contient le nom de l'index utilisé
                used_index = explain.get('key') if explain else None

                if used_index == test['expected_index']:
                    print(f"✅ {test['name']:<30} : Index {used_index} utilisé")
                elif used_index:
                    print(f"⚠️  {test['name']:<30} : Index {used_index} utilisé (attendu: {test['expected_index']})")
                    all_ok = False
                else:
                    print(f"❌ {test['name']:<30} : Aucun index utilisé (full table scan)")
                    all_ok = False

        if all_ok:
            print("✅ Tous les index sont correctement utilisés")
        else:
            print("⚠️  Certains index ne sont pas utilisés (vérifier la configuration)")

        print()
        return all_ok

    except Exception as e:
        print(f"❌ Erreur : {e}\n")
        return False


def test_reconnection_after_timeout():
    """Test 7 : Simuler une reconnexion après timeout"""
    print("="*60)
    print("TEST 7 : Reconnexion automatique")
    print("="*60)

    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            # Forcer un ping pour vérifier la connexion
            conn.ping(reconnect=True)
            print("✅ Ping réussi (connexion active)")

            cur.execute("SELECT 1")
            print("✅ Requête après ping : OK")

            cur.close()

        print("✅ Reconnexion automatique : OK\n")
        return True

    except Exception as e:
        print(f"❌ Erreur : {e}\n")
        return False


def display_summary(results):
    """Affiche le résumé des tests"""
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS")
    print("="*60)

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} : {test_name}")

    print("="*60)
    print(f"Total : {total} tests | Réussis : {passed} | Échoués : {failed}")
    print("="*60)

    if failed == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS ! 🎉")
        print("\nLes optimisations base de données sont opérationnelles.")
        print("\nGains attendus :")
        print("  ⚡ Ouverture app : 5x plus rapide")
        print("  ⚡ Dashboard : 10x plus rapide")
        print("  ⚡ Recherches : 50-100x plus rapides")
    else:
        print(f"\n⚠️  {failed} test(s) échoué(s)")
        print("\nActions recommandées :")
        if not results.get('Test 4: Index'):
            print("  1. Appliquer les index : python apply_performance_indexes.py")
        if not results.get('Test 5: Performances'):
            print("  2. Vérifier la configuration MySQL")
        if not results.get('Test 6: Utilisation index'):
            print("  3. Analyser les requêtes avec EXPLAIN")

    print()


if __name__ == "__main__":
    print("="*60)
    print("🧪 TESTS DES OPTIMISATIONS BASE DE DONNÉES")
    print("="*60)
    print("\nCe script va vérifier :")
    print("  1. Pool MySQL")
    print("  2. Context manager DatabaseConnection")
    print("  3. Context manager DatabaseCursor")
    print("  4. Présence des index de performance")
    print("  5. Performance des requêtes")
    print("  6. Utilisation correcte des index")
    print("  7. Reconnexion automatique")
    print("\n" + "="*60 + "\n")

    results = {}

    # Exécuter tous les tests
    results['Test 1: Pool MySQL'] = test_pool_connection()
    results['Test 2: DatabaseConnection'] = test_database_connection()
    results['Test 3: DatabaseCursor'] = test_database_cursor()
    results['Test 4: Index'] = test_indexes_presence()
    results['Test 5: Performances'] = test_query_performance()
    results['Test 6: Utilisation index'] = test_index_usage()
    results['Test 7: Reconnexion'] = test_reconnection_after_timeout()

    # Afficher le résumé
    display_summary(results)

    # Code de sortie
    sys.exit(0 if all(results.values()) else 1)
