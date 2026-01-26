# -*- coding: utf-8 -*-
"""
Runner de tests principal pour l'application EMAC

Exécute tous les tests unitaires et d'intégration.

Usage:
    # Tous les tests
    python run_all_tests.py

    # Tests unitaires uniquement
    python run_all_tests.py --unit

    # Tests d'intégration uniquement (nécessite DB)
    python run_all_tests.py --integration

    # Tests avec couverture de code
    python run_all_tests.py --coverage

    # Tests avec verbosité
    python run_all_tests.py -v
"""

import sys
import os
import argparse
from datetime import datetime

# Ajouter le répertoire App au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests(args):
    """Exécute les tests avec pytest"""
    try:
        import pytest
    except ImportError:
        print("pytest n'est pas installé. Installez-le avec: pip install pytest")
        return 1

    # Construction des arguments pytest
    pytest_args = []

    # Verbosité
    if args.verbose:
        pytest_args.append('-v')

    # Couverture de code
    if args.coverage:
        try:
            import pytest_cov
            pytest_args.extend(['--cov=core', '--cov-report=html', '--cov-report=term'])
        except ImportError:
            print("pytest-cov n'est pas installé pour la couverture. Installez-le avec: pip install pytest-cov")

    # Sélection des tests
    test_dir = os.path.dirname(os.path.abspath(__file__))

    if args.unit:
        pytest_args.append(os.path.join(test_dir, 'unit'))
        pytest_args.extend(['-m', 'not integration'])
    elif args.integration:
        pytest_args.append(os.path.join(test_dir, 'integration'))
        pytest_args.extend(['-m', 'integration'])
    else:
        pytest_args.append(test_dir)
        # Par défaut, exclure les tests d'intégration qui nécessitent la DB
        if not args.with_integration:
            pytest_args.extend(['-m', 'not integration'])

    # Tests spécifiques
    if args.test:
        pytest_args.extend(['-k', args.test])

    # Sortie colorée
    pytest_args.append('--color=yes')

    # Arrêter au premier échec
    if args.fail_fast:
        pytest_args.append('-x')

    # Rapport JUnit XML
    if args.junit:
        pytest_args.extend(['--junitxml', 'test-results.xml'])

    print("=" * 60)
    print(f"EMAC - Exécution des tests")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Arguments pytest: {' '.join(pytest_args)}")
    print("-" * 60)

    # Exécuter pytest
    exit_code = pytest.main(pytest_args)

    print("-" * 60)
    if exit_code == 0:
        print("Tous les tests sont passés avec succès!")
    else:
        print(f"Certains tests ont échoué (code: {exit_code})")
    print("=" * 60)

    return exit_code


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="Runner de tests pour l'application EMAC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python run_all_tests.py                    # Tous les tests unitaires
  python run_all_tests.py --unit             # Tests unitaires uniquement
  python run_all_tests.py --integration      # Tests d'intégration (nécessite DB)
  python run_all_tests.py --coverage -v      # Avec couverture et verbosité
  python run_all_tests.py -k "test_auth"     # Tests contenant "test_auth"
        """
    )

    parser.add_argument(
        '--unit',
        action='store_true',
        help='Exécuter uniquement les tests unitaires'
    )

    parser.add_argument(
        '--integration',
        action='store_true',
        help='Exécuter uniquement les tests d\'intégration (nécessite DB configurée)'
    )

    parser.add_argument(
        '--with-integration',
        action='store_true',
        help='Inclure les tests d\'intégration avec les tests unitaires'
    )

    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Générer un rapport de couverture de code'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mode verbeux'
    )

    parser.add_argument(
        '-k', '--test',
        type=str,
        help='Exécuter uniquement les tests correspondant au pattern'
    )

    parser.add_argument(
        '-x', '--fail-fast',
        action='store_true',
        help='Arrêter au premier échec'
    )

    parser.add_argument(
        '--junit',
        action='store_true',
        help='Générer un rapport JUnit XML'
    )

    args = parser.parse_args()

    return run_tests(args)


if __name__ == '__main__':
    sys.exit(main())
