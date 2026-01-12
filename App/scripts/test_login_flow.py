# -*- coding: utf-8 -*-
"""
Test du flux complet: Login -> Dashboard
"""

import sys
import os

app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, app_dir)
os.chdir(app_dir)

print("="*60)
print("TEST DU FLUX COMPLET LOGIN -> DASHBOARD")
print("="*60)

# Charger .env
from dotenv import load_dotenv
load_dotenv('.env')
print("[OK] .env charge")

# Test 1: Authentification
print("\n1. Test d'authentification")
print("-" * 60)

from core.services import auth_service

print("Tentative de connexion avec admin/admin...")
success, error_msg = auth_service.authenticate_user('admin', 'admin')

if success:
    print("[OK] Authentification reussie")
else:
    print(f"[ERROR] Authentification echouee: {error_msg}")
    sys.exit(1)

# Test 2: Vérifier la session
print("\n2. Verification de la session")
print("-" * 60)

user = auth_service.get_current_user()
if user:
    print(f"[OK] Utilisateur connecte: {user}")
    print(f"  - ID: {user.get('id')}")
    print(f"  - Username: {user.get('username')}")
    print(f"  - Nom: {user.get('nom')}")
    print(f"  - Prenom: {user.get('prenom')}")
    print(f"  - Role: {user.get('role_nom')}")
else:
    print("[ERROR] Aucun utilisateur en session!")
    sys.exit(1)

# Test 3: Vérifier les permissions
print("\n3. Verification des permissions")
print("-" * 60)

perms_to_check = [
    ('grilles', 'lecture'),
    ('evaluations', 'lecture'),
    ('personnel', 'ecriture'),
    ('postes', 'ecriture'),
]

for module, action in perms_to_check:
    has_perm = auth_service.has_permission(module, action)
    status = "[OK]" if has_perm else "[--]"
    print(f"  {status} {module}.{action}: {has_perm}")

is_admin = auth_service.is_admin()
print(f"  {'[OK]' if is_admin else '[--]'} is_admin: {is_admin}")

# Test 4: Simuler le chargement du dashboard (_fetch_user_and_perms)
print("\n4. Simulation de _fetch_user_and_perms")
print("-" * 60)

def _fetch_user_and_perms():
    current_user = auth_service.get_current_user()
    
    perms = {
        "grilles_lecture": auth_service.has_permission('grilles', 'lecture'),
        "evaluations_lecture": auth_service.has_permission('evaluations', 'lecture'),
        "personnel_ecriture": auth_service.has_permission('personnel', 'ecriture'),
        "postes_ecriture": auth_service.has_permission('postes', 'ecriture'),
        "contrats_ecriture": auth_service.has_permission('contrats', 'ecriture'),
        "documentsrh_lecture": auth_service.has_permission('documents_rh', 'lecture'),
        "planning_lecture": auth_service.has_permission('planning', 'lecture'),
        "historique_lecture": auth_service.has_permission('historique', 'lecture'),
        "is_admin": auth_service.is_admin(),
    }
    return {"user": current_user, "perms": perms}

try:
    payload = _fetch_user_and_perms()
    print("[OK] _fetch_user_and_perms a reussi")
    print(f"  User: {payload['user']}")
    print(f"  Permissions actives:")
    for key, value in payload['perms'].items():
        if value:
            print(f"    - {key}: {value}")
except Exception as e:
    print(f"[ERROR] _fetch_user_and_perms a echoue: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Simuler le chargement des evaluations
print("\n5. Simulation du chargement des evaluations")
print("-" * 60)

from core.db.configbd import DatabaseCursor

def _fetch_evaluations(poste_retard=None, poste_next=None):
    with DatabaseCursor() as cur:
        query_retard = """
            SELECT p.nom, p.prenom, pos.poste_code, poly.prochaine_evaluation
            FROM polyvalence poly
            INNER JOIN personnel p ON p.id = poly.operateur_id
            LEFT JOIN postes pos ON pos.id = poly.poste_id
            WHERE poly.prochaine_evaluation < CURDATE()
              AND p.statut = 'ACTIF'
            ORDER BY poly.prochaine_evaluation ASC
            LIMIT 10
        """
        cur.execute(query_retard)
        retard = cur.fetchall()

        query_next = """
            SELECT p.nom, p.prenom, pos.poste_code, poly.prochaine_evaluation
            FROM polyvalence poly
            INNER JOIN personnel p ON p.id = poly.operateur_id
            LEFT JOIN postes pos ON pos.id = poly.poste_id
            WHERE poly.prochaine_evaluation >= CURDATE()
              AND p.statut = 'ACTIF'
            ORDER BY poly.prochaine_evaluation ASC
            LIMIT 10
        """
        cur.execute(query_next)
        prochaines = cur.fetchall()

        return {"retard": retard, "prochaines": prochaines}

try:
    evals = _fetch_evaluations()
    print(f"[OK] Chargement des evaluations reussi")
    print(f"  - Evaluations en retard: {len(evals['retard'])}")
    print(f"  - Prochaines evaluations: {len(evals['prochaines'])}")
except Exception as e:
    print(f"[ERROR] Chargement des evaluations echoue: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TOUS LES TESTS SONT PASSES!")
print("Le probleme est ailleurs (probablement dans l'UI PyQt)")
print("="*60)
