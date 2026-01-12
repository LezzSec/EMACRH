# -*- coding: utf-8 -*-
"""Script de diagnostic rapide pour la connexion DB"""

import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(app_dir))

print("="*60)
print("DIAGNOSTIC DB - Context Managers")
print("="*60)

# Test 1: Import
print("\n[1] Test import configbd...")
try:
    from core.db.configbd import DatabaseCursor, DatabaseConnection, get_connection
    print("    [OK] Imports reussis")
except Exception as e:
    print(f"    [ERREUR] {e}")
    sys.exit(1)

# Test 2: get_connection() direct
print("\n[2] Test get_connection() direct...")
try:
    conn = get_connection()
    print(f"    [OK] Connexion obtenue: {type(conn)}")
    conn.close()
except Exception as e:
    print(f"    [ERREUR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: DatabaseCursor avec dictionary=True
print("\n[3] Test DatabaseCursor(dictionary=True)...")
try:
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("SELECT COUNT(*) as total FROM personnel WHERE statut='ACTIF'")
        result = cur.fetchone()
        print(f"    [OK] Resultat: {result}")
        print(f"    [OK] Type: {type(result)}")
        if isinstance(result, dict):
            print(f"    [OK] Personnel actifs: {result.get('total', 'N/A')}")
        else:
            print(f"    [WARN] Resultat n'est pas un dict!")
except Exception as e:
    print(f"    [ERREUR] {e}")
    import traceback
    traceback.print_exc()

# Test 4: DatabaseCursor sans dictionary
print("\n[4] Test DatabaseCursor() sans dictionary...")
try:
    with DatabaseCursor(dictionary=False) as cur:
        cur.execute("SELECT COUNT(*) FROM personnel WHERE statut='ACTIF'")
        result = cur.fetchone()
        print(f"    [OK] Resultat: {result}")
        print(f"    [OK] Type: {type(result)}")
except Exception as e:
    print(f"    [ERREUR] {e}")
    import traceback
    traceback.print_exc()

# Test 5: DatabaseConnection
print("\n[5] Test DatabaseConnection()...")
try:
    with DatabaseConnection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) as total FROM personnel WHERE statut='ACTIF'")
        result = cur.fetchone()
        cur.close()
        print(f"    [OK] Resultat: {result}")
except Exception as e:
    print(f"    [ERREUR] {e}")
    import traceback
    traceback.print_exc()

# Test 6: Service evaluation_service
print("\n[6] Test evaluation_service.get_evaluations_en_retard()...")
try:
    from core.services import evaluation_service
    result = evaluation_service.get_evaluations_en_retard()
    print(f"    [OK] Type retour: {type(result)}")
    print(f"    [OK] Nombre resultats: {len(result)}")
    if result:
        print(f"    [OK] Premier element: {type(result[0])}")
        if isinstance(result[0], dict):
            print(f"    [OK] Cles: {list(result[0].keys())[:5]}")
except Exception as e:
    print(f"    [ERREUR] {e}")
    import traceback
    traceback.print_exc()

# Test 7: Service evaluation_service.get_statistiques_evaluations
print("\n[7] Test evaluation_service.get_statistiques_evaluations()...")
try:
    from core.services import evaluation_service
    stats = evaluation_service.get_statistiques_evaluations()
    print(f"    [OK] Type retour: {type(stats)}")
    print(f"    [OK] Cles: {list(stats.keys())}")
    print(f"    [OK] Total: {stats.get('total', 'N/A')}")
    print(f"    [OK] En retard: {stats.get('en_retard', 'N/A')}")
except Exception as e:
    print(f"    [ERREUR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("DIAGNOSTIC TERMINE")
print("="*60)
