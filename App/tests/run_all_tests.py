# -*- coding: utf-8 -*-
"""
Script maître pour exécuter tous les tests EMAC
Génère un rapport complet de tests avec statistiques

Usage:
    cd App
    py tests/run_all_tests.py

    # Avec options:
    py tests/run_all_tests.py --verbose      # Mode verbeux
    py tests/run_all_tests.py --fast         # Tests rapides uniquement
    py tests/run_all_tests.py --suite=eval   # Suite spécifique
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import time
from datetime import datetime
from pathlib import Path


class TestRunner:
    """Gestionnaire d'exécution de tous les tests."""

    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results = []
        self.start_time = None
        self.end_time = None

        # Définition des suites de tests
        self.test_suites = {
            'integration': {
                'name': 'Tests d\'intégration',
                'files': [
                    'test_integration_complete.py',
                ],
                'description': 'Tests d\'intégration de base du système'
            },
            'evaluation': {
                'name': 'Système d\'évaluation',
                'files': [
                    'test_evaluation_system_advanced.py',
                ],
                'description': 'Tests complets du système d\'évaluation et polyvalence'
            },
            'contrat': {
                'name': 'Gestion des contrats',
                'files': [
                    'test_contrat_management_advanced.py',
                ],
                'description': 'Tests complets de la gestion des contrats'
            },
            'audit': {
                'name': 'Audit et logging',
                'files': [
                    'test_audit_logging_advanced.py',
                ],
                'description': 'Tests du système d\'audit et historique'
            },
            'database': {
                'name': 'Intégrité base de données',
                'files': [
                    'test_database_integrity.py',
                ],
                'description': 'Tests d\'intégrité et contraintes BDD'
            },
            'personnel': {
                'name': 'Gestion du personnel',
                'files': [
                    'test_add_operateur.py',
                    'test_masquage_operateur.py',
                    'test_personnel_non_production.py',
                    'test_matricule_service.py',
                ],
                'description': 'Tests de gestion des opérateurs et personnel'
            },
        }

    def run_all_suites(self, verbose=False, suite_filter=None):
        """Exécute toutes les suites de tests."""
        self.start_time = time.time()

        print("=" * 90)
        print("  EXÉCUTION COMPLÈTE DES TESTS EMAC")
        print("=" * 90)
        print(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Filtrer les suites si demandé
        if suite_filter:
            suites_to_run = {k: v for k, v in self.test_suites.items() if k == suite_filter}
            if not suites_to_run:
                print(f"⚠️  Suite '{suite_filter}' non trouvée!")
                print(f"Suites disponibles: {', '.join(self.test_suites.keys())}")
                return
        else:
            suites_to_run = self.test_suites

        # Exécuter chaque suite
        for suite_key, suite_info in suites_to_run.items():
            self._run_suite(suite_key, suite_info, verbose)

        self.end_time = time.time()
        self._print_final_report()

    def _run_suite(self, suite_key, suite_info, verbose):
        """Exécute une suite de tests."""
        print(f"\n{'-' * 90}")
        print(f"SUITE: {suite_info['name']}")
        print(f"   {suite_info['description']}")
        print(f"{'-' * 90}\n")

        suite_start = time.time()
        suite_results = []

        for test_file in suite_info['files']:
            test_path = self.test_dir / test_file

            if not test_path.exists():
                print(f"⚠️  Fichier non trouvé: {test_file}")
                suite_results.append({
                    'file': test_file,
                    'status': 'SKIP',
                    'time': 0,
                    'output': 'Fichier non trouvé'
                })
                continue

            result = self._run_test_file(test_path, verbose)
            suite_results.append(result)

        suite_elapsed = time.time() - suite_start

        # Résumé de la suite
        success_count = sum(1 for r in suite_results if r['status'] == 'OK')
        failed_count = sum(1 for r in suite_results if r['status'] == 'FAIL')
        skipped_count = sum(1 for r in suite_results if r['status'] == 'SKIP')

        print(f"\n{'-' * 90}")
        print(f"Resume suite '{suite_info['name']}':")
        print(f"  [+] Reussis: {success_count}")
        print(f"  [-] Echoues: {failed_count}")
        print(f"  [/] Ignores: {skipped_count}")
        print(f"  [T] Duree: {suite_elapsed:.2f}s")
        print(f"{'-' * 90}")

        self.results.append({
            'suite': suite_key,
            'suite_name': suite_info['name'],
            'results': suite_results,
            'time': suite_elapsed
        })

    def _run_test_file(self, test_path, verbose):
        """Exécute un fichier de test."""
        test_name = test_path.name
        print(f"\nExecution: {test_name}")

        start_time = time.time()

        try:
            # Exécuter le test en subprocess
            result = subprocess.run(
                [sys.executable, str(test_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes max par test
                cwd=self.test_dir.parent
            )

            elapsed = time.time() - start_time

            # Analyser le résultat
            if result.returncode == 0:
                status = 'OK'
                status_icon = '[OK]'
            else:
                status = 'FAIL'
                status_icon = '[FAIL]'

            print(f"   {status_icon} {status} - {elapsed:.2f}s")

            if verbose or status == 'FAIL':
                print(f"\n--- Output ---")
                print(result.stdout)
                if result.stderr:
                    print(f"\n--- Errors ---")
                    print(result.stderr)
                print(f"--- End ---\n")

            return {
                'file': test_name,
                'status': status,
                'time': elapsed,
                'output': result.stdout,
                'errors': result.stderr,
                'returncode': result.returncode
            }

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"   [TIMEOUT] - {elapsed:.2f}s")
            return {
                'file': test_name,
                'status': 'TIMEOUT',
                'time': elapsed,
                'output': 'Test timeout apres 5 minutes',
                'errors': '',
                'returncode': -1
            }

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   [ERROR] - {str(e)}")
            return {
                'file': test_name,
                'status': 'ERROR',
                'time': elapsed,
                'output': '',
                'errors': str(e),
                'returncode': -1
            }

    def _print_final_report(self):
        """Affiche le rapport final."""
        total_elapsed = self.end_time - self.start_time

        print("\n\n")
        print("=" * 90)
        print("  RAPPORT FINAL - TESTS EMAC")
        print("=" * 90)
        print()

        # Statistiques globales
        total_tests = 0
        total_success = 0
        total_failed = 0
        total_skipped = 0
        total_errors = 0

        for suite_result in self.results:
            for test_result in suite_result['results']:
                total_tests += 1
                if test_result['status'] == 'OK':
                    total_success += 1
                elif test_result['status'] == 'FAIL':
                    total_failed += 1
                elif test_result['status'] == 'SKIP':
                    total_skipped += 1
                else:
                    total_errors += 1

        print(f"STATISTIQUES GLOBALES")
        print(f"{'-' * 90}")
        print(f"  Total de tests executes:  {total_tests}")
        print(f"  [+] Tests reussis:        {total_success}")
        print(f"  [-] Tests echoues:        {total_failed}")
        print(f"  [/] Tests ignores:        {total_skipped}")
        print(f"  [!] Erreurs d'execution:  {total_errors}")
        print(f"  [T] Duree totale:         {total_elapsed:.2f}s ({total_elapsed/60:.1f}min)")

        if total_tests > 0:
            success_rate = (total_success / total_tests) * 100
            print(f"  [%] Taux de reussite:     {success_rate:.1f}%")

        print()

        # Détail par suite
        print(f"RESULTATS PAR SUITE")
        print(f"{'-' * 90}")

        for suite_result in self.results:
            suite_name = suite_result['suite_name']
            suite_time = suite_result['time']

            success = sum(1 for r in suite_result['results'] if r['status'] == 'OK')
            failed = sum(1 for r in suite_result['results'] if r['status'] == 'FAIL')
            total = len(suite_result['results'])

            status_icon = '[OK]' if failed == 0 else '[FAIL]'
            print(f"  {status_icon} {suite_name:30s}  {success}/{total} reussis  ({suite_time:.2f}s)")

        print()

        # Tests échoués
        if total_failed > 0 or total_errors > 0:
            print(f"TESTS ECHOUES / ERREURS")
            print(f"{'-' * 90}")

            for suite_result in self.results:
                for test_result in suite_result['results']:
                    if test_result['status'] in ['FAIL', 'ERROR', 'TIMEOUT']:
                        print(f"  [-] {test_result['file']}")
                        print(f"    Suite: {suite_result['suite_name']}")
                        print(f"    Statut: {test_result['status']}")
                        print(f"    Duree: {test_result['time']:.2f}s")

                        if test_result.get('errors'):
                            error_lines = test_result['errors'].split('\n')[:3]
                            print(f"    Erreur: {error_lines[0]}")

                        print()

        # Conclusion
        print(f"{'-' * 90}")

        if total_failed == 0 and total_errors == 0:
            print(f"[SUCCESS] SUCCES TOTAL! Tous les tests sont passes avec succes!")
        else:
            print(f"[WARNING] ATTENTION: {total_failed + total_errors} test(s) ont echoue.")
            print(f"   Veuillez corriger les problemes et relancer les tests.")

        print()
        print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 90)

        # Code de sortie
        if total_failed > 0 or total_errors > 0:
            sys.exit(1)

    def export_report(self, filename='test_report.txt'):
        """Exporte le rapport dans un fichier."""
        report_path = self.test_dir / filename

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 90 + "\n")
            f.write("  RAPPORT DE TESTS EMAC\n")
            f.write("=" * 90 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Statistiques
            total_tests = 0
            total_success = 0
            total_failed = 0

            for suite_result in self.results:
                for test_result in suite_result['results']:
                    total_tests += 1
                    if test_result['status'] == 'OK':
                        total_success += 1
                    elif test_result['status'] == 'FAIL':
                        total_failed += 1

            f.write(f"Total tests: {total_tests}\n")
            f.write(f"Réussis: {total_success}\n")
            f.write(f"Échoués: {total_failed}\n")
            f.write(f"Taux de réussite: {(total_success/total_tests*100):.1f}%\n\n")

            # Détails par suite
            for suite_result in self.results:
                f.write(f"\nSuite: {suite_result['suite_name']}\n")
                f.write("-" * 90 + "\n")

                for test_result in suite_result['results']:
                    f.write(f"  {test_result['file']}: {test_result['status']} ({test_result['time']:.2f}s)\n")

                    if test_result['status'] in ['FAIL', 'ERROR']:
                        f.write(f"    Output:\n")
                        for line in test_result['output'].split('\n')[:10]:
                            f.write(f"      {line}\n")

        print(f"\nRapport exporte: {report_path}")


def main():
    """Point d'entrée principal."""
    import argparse

    parser = argparse.ArgumentParser(description='Exécuter tous les tests EMAC')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mode verbeux (afficher tous les outputs)')
    parser.add_argument('--suite', '-s', type=str,
                       help='Exécuter une suite spécifique (integration, evaluation, contrat, audit, database, personnel)')
    parser.add_argument('--export', '-e', action='store_true',
                       help='Exporter le rapport dans un fichier')

    args = parser.parse_args()

    runner = TestRunner()
    runner.run_all_suites(verbose=args.verbose, suite_filter=args.suite)

    if args.export:
        runner.export_report()


if __name__ == "__main__":
    main()
