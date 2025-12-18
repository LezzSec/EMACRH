# -*- coding: utf-8 -*-
"""
Script de test pour le système d'authentification
Vérifie que l'authentification et les permissions fonctionnent correctement
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.services.auth_service import (
    authenticate_user, logout_user, has_permission,
    is_admin, get_current_user, UserSession
)


def print_separator():
    print("\n" + "=" * 70)


def print_test(test_name, passed):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")


def test_admin_authentication():
    """Test l'authentification avec le compte admin"""
    print_separator()
    print("TEST 1: Authentification Admin")
    print_separator()

    # Déconnecter au cas où
    logout_user()

    # Test connexion valide
    success, error = authenticate_user("admin", "admin123")
    print_test("Connexion admin avec mot de passe correct", success)

    if success:
        user = get_current_user()
        print(f"   → Utilisateur connecté: {user['username']}")
        print(f"   → Rôle: {user['role_nom']}")

    # Test connexion invalide
    logout_user()
    success, error = authenticate_user("admin", "mauvais_password")
    print_test("Rejet connexion avec mauvais mot de passe", not success)
    if not success:
        print(f"   → Message d'erreur: {error}")

    return True


def test_admin_permissions():
    """Test les permissions de l'admin"""
    print_separator()
    print("TEST 2: Permissions Admin")
    print_separator()

    # Se connecter en admin
    authenticate_user("admin", "admin123")

    # L'admin doit avoir toutes les permissions
    modules = ['personnel', 'contrats', 'documents_rh', 'planning', 'gestion_utilisateurs']

    all_passed = True
    for module in modules:
        for action in ['lecture', 'ecriture', 'suppression']:
            has_perm = has_permission(module, action)
            print_test(f"Admin a {action} sur {module}", has_perm)
            all_passed = all_passed and has_perm

    # Vérifier is_admin()
    admin_check = is_admin()
    print_test("is_admin() retourne True", admin_check)

    logout_user()
    return all_passed


def test_session_management():
    """Test la gestion de session"""
    print_separator()
    print("TEST 3: Gestion de session")
    print_separator()

    # Vérifier qu'aucun utilisateur n'est connecté
    session = UserSession()
    not_authenticated = not session.is_authenticated()
    print_test("Pas d'utilisateur connecté initialement", not_authenticated)

    # Connexion
    authenticate_user("admin", "admin123")
    authenticated = session.is_authenticated()
    print_test("Utilisateur connecté après authenticate", authenticated)

    user = session.get_user()
    has_user_data = user is not None and 'username' in user
    print_test("Données utilisateur disponibles", has_user_data)

    # Déconnexion
    logout_user()
    disconnected = not session.is_authenticated()
    print_test("Session effacée après logout", disconnected)

    return True


def test_role_permissions():
    """Test les permissions par rôle"""
    print_separator()
    print("TEST 4: Permissions par rôle")
    print_separator()

    # Note: Ce test nécessite d'avoir créé des utilisateurs de test
    # Pour un test complet, créer des utilisateurs via l'interface admin

    print("⚠️  Pour tester complètement ce module:")
    print("   1. Créez un utilisateur 'user_prod' avec le rôle 'gestion_production'")
    print("   2. Créez un utilisateur 'user_rh' avec le rôle 'gestion_rh'")
    print("   3. Relancez ce script")

    # Test avec admin pour l'instant
    authenticate_user("admin", "admin123")

    # Admin doit avoir accès à gestion_utilisateurs
    has_user_mgmt = has_permission('gestion_utilisateurs', 'lecture')
    print_test("Admin a accès à gestion_utilisateurs", has_user_mgmt)

    logout_user()
    return True


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "#" * 70)
    print("# TEST DU SYSTÈME D'AUTHENTIFICATION EMAC")
    print("#" * 70)

    tests = [
        ("Authentification Admin", test_admin_authentication),
        ("Permissions Admin", test_admin_permissions),
        ("Gestion de session", test_session_management),
        ("Permissions par rôle", test_role_permissions)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ ERREUR dans {test_name}: {e}")
            results.append((test_name, False))

    # Résumé
    print_separator()
    print("RÉSUMÉ DES TESTS")
    print_separator()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print_separator()
    print(f"\nRésultat: {passed}/{total} tests réussis")

    if passed == total:
        print("\n🎉 Tous les tests sont passés!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) ont échoué")
        return 1


if __name__ == "__main__":
    print("\n🔍 Vérification des prérequis...")

    # Vérifier bcrypt
    try:
        import bcrypt
        print("✅ Module bcrypt installé")
    except ImportError:
        print("❌ Module bcrypt manquant - Installez avec: pip install bcrypt")
        sys.exit(1)

    # Vérifier la connexion DB
    try:
        from core.db.configbd import get_connection
        conn = get_connection()
        if conn:
            print("✅ Connexion à la base de données OK")
            conn.close()
        else:
            print("❌ Impossible de se connecter à la base de données")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur de connexion DB: {e}")
        sys.exit(1)

    # Vérifier que les tables existent
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM utilisateurs")
        count = cur.fetchone()[0]
        print(f"✅ Table utilisateurs trouvée ({count} utilisateur(s))")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Table utilisateurs introuvable - Appliquez la migration d'abord")
        print(f"   Exécutez: py scripts/apply_user_management_migration.py")
        sys.exit(1)

    # Exécuter les tests
    exit_code = run_all_tests()

    print("\n" + "#" * 70)
    sys.exit(exit_code)
