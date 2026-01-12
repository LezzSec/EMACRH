# -*- coding: utf-8 -*-
"""
Script de test pour valider la migration vers les context managers.
Teste les 3 services critiques migrés.
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path
app_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(app_dir))

def test_evaluation_service():
    """Teste evaluation_service.py"""
    print("\n[TEST] evaluation_service.py")
    print("-" * 50)

    try:
        from core.services import evaluation_service

        # Test 1: get_evaluations_en_retard
        print("  Test get_evaluations_en_retard()...", end=" ")
        result = evaluation_service.get_evaluations_en_retard()
        print(f"OK ({len(result)} évaluations en retard)")

        # Test 2: get_prochaines_evaluations
        print("  Test get_prochaines_evaluations()...", end=" ")
        result = evaluation_service.get_prochaines_evaluations(30)
        print(f"OK ({len(result)} évaluations à venir)")

        # Test 3: get_statistiques_evaluations
        print("  Test get_statistiques_evaluations()...", end=" ")
        stats = evaluation_service.get_statistiques_evaluations()
        print(f"OK (total: {stats.get('total', 0)})")

        print("  [OK] evaluation_service.py: TOUS LES TESTS PASSES")
        return True

    except Exception as e:
        print(f"\n  [ERREUR]: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_absence_service():
    """Teste absence_service.py"""
    print("\n[TEST] absence_service.py")
    print("-" * 50)

    try:
        from core.services import absence_service
        from datetime import date

        # Test 1: get_jours_feries
        print("  Test get_jours_feries()...", end=" ")
        result = absence_service.get_jours_feries(2024, 2026)
        print(f"OK ({len(result)} jours fériés)")

        # Test 2: get_types_absence
        print("  Test get_types_absence()...", end=" ")
        result = absence_service.get_types_absence()
        print(f"OK ({len(result)} types)")

        # Test 3: get_absences_periode
        print("  Test get_absences_periode()...", end=" ")
        date_debut = date(2024, 1, 1)
        date_fin = date(2024, 12, 31)
        result = absence_service.get_absences_periode(date_debut, date_fin)
        print(f"OK ({len(result)} absences)")

        print("  [OK] absence_service.py: TOUS LES TESTS PASSES")
        return True

    except Exception as e:
        print(f"\n  [ERREUR]: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_contrat_service():
    """Teste contrat_service.py"""
    print("\n[TEST] contrat_service.py")
    print("-" * 50)

    try:
        from core.services import contrat_service

        # Test 1: get_all_active_contracts
        print("  Test get_all_active_contracts()...", end=" ")
        result = contrat_service.get_all_active_contracts()
        print(f"OK ({len(result)} contrats actifs)")

        # Test 2: get_expiring_contracts
        print("  Test get_expiring_contracts()...", end=" ")
        result = contrat_service.get_expiring_contracts(30)
        print(f"OK ({len(result)} contrats expirant)")

        # Test 3: get_contract_statistics
        print("  Test get_contract_statistics()...", end=" ")
        stats = contrat_service.get_contract_statistics()
        print(f"OK (total: {stats.get('total_actifs', 0)})")

        print("  [OK] contrat_service.py: TOUS LES TESTS PASSES")
        return True

    except Exception as e:
        print(f"\n  [ERREUR]: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Lance tous les tests"""
    print("=" * 60)
    print("TEST DE MIGRATION DES CONTEXT MANAGERS")
    print("=" * 60)
    print("\nTests des 3 services critiques migrés...")

    results = []

    # Test des 3 services
    results.append(("evaluation_service", test_evaluation_service()))
    results.append(("absence_service", test_absence_service()))
    results.append(("contrat_service", test_contrat_service()))

    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for service_name, result in results:
        status = "[OK] PASSE" if result else "[ERREUR] ECHOUE"
        print(f"  {service_name:25s} : {status}")

    print("-" * 60)
    print(f"  TOTAL : {passed}/{total} services testes avec succes")
    print("=" * 60)

    if passed == total:
        print("\n[SUCCESS] MIGRATION REUSSIE - Tous les services fonctionnent correctement")
        return 0
    else:
        print(f"\n[WARN] ATTENTION - {total - passed} service(s) en erreur")
        return 1


if __name__ == "__main__":
    sys.exit(main())
