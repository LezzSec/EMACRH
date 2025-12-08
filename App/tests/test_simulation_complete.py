# -*- coding: utf-8 -*-
"""
Test de simulation complète de l'application EMAC
Teste tous les modules principaux pour détecter les erreurs potentielles
"""

import sys
import os
from datetime import datetime, timedelta

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Imports de test
import traceback
from typing import List, Dict, Tuple

# Couleurs pour l'affichage terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class TestResult:
    """Classe pour stocker les résultats de tests"""
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_warnings = 0
        self.errors: List[Tuple[str, str]] = []
        self.warnings: List[Tuple[str, str]] = []

    def add_pass(self):
        self.tests_passed += 1

    def add_fail(self, test_name: str, error: str):
        self.tests_failed += 1
        self.errors.append((test_name, error))

    def add_warning(self, test_name: str, warning: str):
        self.tests_warnings += 1
        self.warnings.append((test_name, warning))

    def print_summary(self):
        """Affiche un résumé des tests"""
        total = self.tests_passed + self.tests_failed + self.tests_warnings
        print("\n" + "="*70)
        print(f"{Colors.BOLD}RÉSUMÉ DES TESTS{Colors.RESET}")
        print("="*70)
        print(f"Total de tests exécutés: {total}")
        print(f"{Colors.GREEN}✓ Tests réussis: {self.tests_passed}{Colors.RESET}")
        print(f"{Colors.YELLOW}⚠ Avertissements: {self.tests_warnings}{Colors.RESET}")
        print(f"{Colors.RED}✗ Tests échoués: {self.tests_failed}{Colors.RESET}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}AVERTISSEMENTS:{Colors.RESET}")
            for test_name, warning in self.warnings:
                print(f"{Colors.YELLOW}  ⚠ {test_name}:{Colors.RESET} {warning}")

        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}ERREURS:{Colors.RESET}")
            for test_name, error in self.errors:
                print(f"{Colors.RED}  ✗ {test_name}:{Colors.RESET}")
                print(f"    {error}")

        print("="*70)

        if self.tests_failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ TOUS LES TESTS SONT PASSÉS !{Colors.RESET}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ CERTAINS TESTS ONT ÉCHOUÉ{Colors.RESET}")
        print("="*70 + "\n")


def print_test_header(section: str):
    """Affiche un en-tête de section"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}")
    print(f"  {section}")
    print(f"{'='*70}{Colors.RESET}\n")


def test_database_connection(result: TestResult):
    """Test de la connexion à la base de données"""
    print_test_header("TEST 1: CONNEXION À LA BASE DE DONNÉES")

    try:
        from core.db.configbd import get_connection

        print("  → Tentative de connexion...")
        conn = get_connection()
        cur = conn.cursor()

        # Test de requête simple
        cur.execute("SELECT 1")
        cur.fetchone()

        cur.close()
        conn.close()

        print(f"  {Colors.GREEN}✓ Connexion réussie{Colors.RESET}")
        result.add_pass()
        return True

    except Exception as e:
        error_msg = f"Erreur de connexion: {str(e)}\n{traceback.format_exc()}"
        print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
        result.add_fail("Connexion base de données", error_msg)
        return False


def test_database_schema(result: TestResult):
    """Test de l'intégrité du schéma de la base de données"""
    print_test_header("TEST 2: INTÉGRITÉ DU SCHÉMA")

    try:
        from core.db.configbd import get_connection

        conn = get_connection()
        cur = conn.cursor()

        # Tables requises
        required_tables = [
            'personnel', 'operateurs', 'postes', 'atelier',
            'polyvalence', 'historique', 'contrats',
            'absences', 'type_absence', 'soldes_conges'
        ]

        print("  → Vérification des tables...")
        cur.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cur.fetchall()]

        missing_tables = []
        for table in required_tables:
            if table in existing_tables:
                print(f"  {Colors.GREEN}✓{Colors.RESET} Table '{table}' trouvée")
            else:
                print(f"  {Colors.RED}✗{Colors.RESET} Table '{table}' manquante")
                missing_tables.append(table)

        if missing_tables:
            result.add_fail("Schéma de base de données",
                          f"Tables manquantes: {', '.join(missing_tables)}")
        else:
            result.add_pass()

        # Vérification de la cohérence personnel/operateurs
        print("\n  → Vérification cohérence personnel/operateurs...")
        cur.execute("SELECT COUNT(*) FROM personnel")
        count_personnel = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM operateurs")
        count_operateurs = cur.fetchone()[0]

        print(f"    Personnel: {count_personnel} enregistrements")
        print(f"    Operateurs: {count_operateurs} enregistrements")

        if count_personnel != count_operateurs:
            result.add_warning("Tables personnel/operateurs",
                             f"Nombre différent d'enregistrements (personnel: {count_personnel}, operateurs: {count_operateurs})")
        else:
            result.add_pass()

        cur.close()
        conn.close()

    except Exception as e:
        error_msg = f"Erreur lors du test du schéma: {str(e)}\n{traceback.format_exc()}"
        print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
        result.add_fail("Schéma de base de données", error_msg)


def test_services(result: TestResult):
    """Test des services principaux"""
    print_test_header("TEST 3: SERVICES MÉTIER")

    # Test evaluation_service
    try:
        print("  → Test evaluation_service...")
        from core.services.evaluation_service import (
            get_evaluations_en_retard,
            get_prochaines_evaluations
        )

        retard = get_evaluations_en_retard()
        print(f"    Évaluations en retard: {len(retard)}")

        prochaines = get_prochaines_evaluations(30)
        print(f"    Prochaines évaluations (30j): {len(prochaines)}")

        print(f"  {Colors.GREEN}✓ evaluation_service OK{Colors.RESET}")
        result.add_pass()

    except Exception as e:
        error_msg = f"Erreur evaluation_service: {str(e)}\n{traceback.format_exc()}"
        print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
        result.add_fail("evaluation_service", error_msg)

    # Test calendrier_service
    try:
        print("\n  → Test calendrier_service...")
        from core.services.calendrier_service import calculer_prochaine_evaluation

        test_date = datetime.now()
        for niveau in [1, 2, 3, 4]:
            prochaine = calculer_prochaine_evaluation(test_date, niveau)
            print(f"    Niveau {niveau}: prochaine évaluation dans {(prochaine - test_date).days} jours")

        print(f"  {Colors.GREEN}✓ calendrier_service OK{Colors.RESET}")
        result.add_pass()

    except Exception as e:
        error_msg = f"Erreur calendrier_service: {str(e)}\n{traceback.format_exc()}"
        print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
        result.add_fail("calendrier_service", error_msg)

    # Test contrat_service
    try:
        print("\n  → Test contrat_service...")
        from core.services.contrat_service import (
            get_contrats_expirant_bientot,
            get_tous_contrats
        )

        contrats_urgent = get_contrats_expirant_bientot(30)
        print(f"    Contrats expirant bientôt (30j): {len(contrats_urgent)}")

        tous_contrats = get_tous_contrats()
        print(f"    Total des contrats: {len(tous_contrats)}")

        print(f"  {Colors.GREEN}✓ contrat_service OK{Colors.RESET}")
        result.add_pass()

    except Exception as e:
        error_msg = f"Erreur contrat_service: {str(e)}\n{traceback.format_exc()}"
        print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
        result.add_fail("contrat_service", error_msg)

    # Test absence_service
    try:
        print("\n  → Test absence_service...")
        from core.services.absence_service import (
            get_absences_actuelles,
            get_solde_conges
        )

        absences = get_absences_actuelles()
        print(f"    Absences actuelles: {len(absences)}")

        print(f"  {Colors.GREEN}✓ absence_service OK{Colors.RESET}")
        result.add_pass()

    except Exception as e:
        error_msg = f"Erreur absence_service: {str(e)}\n{traceback.format_exc()}"
        print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
        result.add_fail("absence_service", error_msg)

    # Test matricule_service
    try:
        print("\n  → Test matricule_service...")
        from core.services.matricule_service import generer_matricule

        matricule = generer_matricule("Test", "User")
        print(f"    Matricule généré: {matricule}")

        if not matricule or len(matricule) < 3:
            result.add_fail("matricule_service", "Matricule invalide généré")
        else:
            print(f"  {Colors.GREEN}✓ matricule_service OK{Colors.RESET}")
            result.add_pass()

    except Exception as e:
        error_msg = f"Erreur matricule_service: {str(e)}\n{traceback.format_exc()}"
        print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
        result.add_fail("matricule_service", error_msg)

    # Test logger
    try:
        print("\n  → Test logger...")
        from core.services.logger import log_hist

        # Test d'écriture de log
        log_hist("TEST_SIMULATION", "Test de simulation automatique", None, None)

        print(f"  {Colors.GREEN}✓ logger OK{Colors.RESET}")
        result.add_pass()

    except Exception as e:
        error_msg = f"Erreur logger: {str(e)}\n{traceback.format_exc()}"
        print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
        result.add_fail("logger", error_msg)


def test_data_integrity(result: TestResult):
    """Test de l'intégrité des données"""
    print_test_header("TEST 4: INTÉGRITÉ DES DONNÉES")

    try:
        from core.db.configbd import get_connection

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # Test 1: Vérifier les polyvalences sans employé
        print("  → Vérification polyvalences orphelines...")
        cur.execute("""
            SELECT COUNT(*) as count
            FROM polyvalence p
            LEFT JOIN personnel pers ON p.operateur_id = pers.id
            WHERE pers.id IS NULL
        """)
        orphan_poly = cur.fetchone()['count']

        if orphan_poly > 0:
            result.add_warning("Polyvalences orphelines",
                             f"{orphan_poly} polyvalences sans employé associé")
            print(f"  {Colors.YELLOW}⚠ {orphan_poly} polyvalences orphelines trouvées{Colors.RESET}")
        else:
            print(f"  {Colors.GREEN}✓ Pas de polyvalences orphelines{Colors.RESET}")
            result.add_pass()

        # Test 2: Vérifier les postes sans atelier
        print("\n  → Vérification postes sans atelier...")
        cur.execute("""
            SELECT COUNT(*) as count
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            WHERE a.id IS NULL
        """)
        orphan_postes = cur.fetchone()['count']

        if orphan_postes > 0:
            result.add_warning("Postes orphelins",
                             f"{orphan_postes} postes sans atelier associé")
            print(f"  {Colors.YELLOW}⚠ {orphan_postes} postes orphelins trouvés{Colors.RESET}")
        else:
            print(f"  {Colors.GREEN}✓ Tous les postes ont un atelier{Colors.RESET}")
            result.add_pass()

        # Test 3: Vérifier les dates d'évaluation cohérentes
        print("\n  → Vérification dates d'évaluation...")
        cur.execute("""
            SELECT COUNT(*) as count
            FROM polyvalence
            WHERE prochaine_evaluation < date_evaluation
        """)
        invalid_dates = cur.fetchone()['count']

        if invalid_dates > 0:
            result.add_fail("Dates d'évaluation incohérentes",
                          f"{invalid_dates} enregistrements avec prochaine_evaluation < date_evaluation")
            print(f"  {Colors.RED}✗ {invalid_dates} dates incohérentes{Colors.RESET}")
        else:
            print(f"  {Colors.GREEN}✓ Toutes les dates sont cohérentes{Colors.RESET}")
            result.add_pass()

        # Test 4: Vérifier les niveaux de compétence valides
        print("\n  → Vérification niveaux de compétence...")
        cur.execute("""
            SELECT COUNT(*) as count
            FROM polyvalence
            WHERE niveau NOT IN (1, 2, 3, 4)
        """)
        invalid_levels = cur.fetchone()['count']

        if invalid_levels > 0:
            result.add_fail("Niveaux invalides",
                          f"{invalid_levels} niveaux de compétence hors plage (1-4)")
            print(f"  {Colors.RED}✗ {invalid_levels} niveaux invalides{Colors.RESET}")
        else:
            print(f"  {Colors.GREEN}✓ Tous les niveaux sont valides (1-4){Colors.RESET}")
            result.add_pass()

        # Test 5: Vérifier les doublons de polyvalence
        print("\n  → Vérification doublons de polyvalence...")
        cur.execute("""
            SELECT operateur_id, poste_id, COUNT(*) as count
            FROM polyvalence
            GROUP BY operateur_id, poste_id
            HAVING count > 1
        """)
        duplicates = cur.fetchall()

        if duplicates:
            result.add_warning("Doublons de polyvalence",
                             f"{len(duplicates)} paires employé-poste en double")
            print(f"  {Colors.YELLOW}⚠ {len(duplicates)} doublons trouvés{Colors.RESET}")
        else:
            print(f"  {Colors.GREEN}✓ Pas de doublons de polyvalence{Colors.RESET}")
            result.add_pass()

        # Test 6: Vérifier les contrats sans date de fin
        print("\n  → Vérification contrats...")
        cur.execute("""
            SELECT COUNT(*) as count
            FROM contrats
            WHERE date_fin IS NULL
        """)
        no_end_date = cur.fetchone()['count']

        if no_end_date > 0:
            print(f"  {Colors.BLUE}ℹ {no_end_date} contrats sans date de fin (CDI probablement){Colors.RESET}")
            result.add_pass()
        else:
            print(f"  {Colors.GREEN}✓ Tous les contrats ont une date de fin{Colors.RESET}")
            result.add_pass()

        cur.close()
        conn.close()

    except Exception as e:
        error_msg = f"Erreur lors du test d'intégrité: {str(e)}\n{traceback.format_exc()}"
        print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
        result.add_fail("Intégrité des données", error_msg)


def test_crud_operations(result: TestResult):
    """Test des opérations CRUD de base"""
    print_test_header("TEST 5: OPÉRATIONS CRUD")

    try:
        from core.db.configbd import get_connection
        from core.services.logger import log_hist

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        test_data = {
            'nom': 'TEST_SIMULATION',
            'prenom': 'User',
            'matricule': 'SIM999',
            'statut': 'INACTIF'
        }

        # CREATE
        print("  → Test CREATE (insertion)...")
        try:
            cur.execute("""
                INSERT INTO personnel (nom, prenom, matricule, statut)
                VALUES (%(nom)s, %(prenom)s, %(matricule)s, %(statut)s)
            """, test_data)
            test_id = cur.lastrowid
            conn.commit()
            print(f"  {Colors.GREEN}✓ Insertion réussie (ID: {test_id}){Colors.RESET}")
            result.add_pass()
        except Exception as e:
            raise Exception(f"Échec CREATE: {str(e)}")

        # READ
        print("\n  → Test READ (lecture)...")
        try:
            cur.execute("SELECT * FROM personnel WHERE id = %s", (test_id,))
            read_data = cur.fetchone()

            if read_data and read_data['matricule'] == test_data['matricule']:
                print(f"  {Colors.GREEN}✓ Lecture réussie{Colors.RESET}")
                result.add_pass()
            else:
                raise Exception("Données lues ne correspondent pas")
        except Exception as e:
            raise Exception(f"Échec READ: {str(e)}")

        # UPDATE
        print("\n  → Test UPDATE (mise à jour)...")
        try:
            cur.execute("""
                UPDATE personnel
                SET statut = 'ACTIF'
                WHERE id = %s
            """, (test_id,))
            conn.commit()

            cur.execute("SELECT statut FROM personnel WHERE id = %s", (test_id,))
            updated_data = cur.fetchone()

            if updated_data['statut'] == 'ACTIF':
                print(f"  {Colors.GREEN}✓ Mise à jour réussie{Colors.RESET}")
                result.add_pass()
            else:
                raise Exception("Statut non mis à jour")
        except Exception as e:
            raise Exception(f"Échec UPDATE: {str(e)}")

        # DELETE
        print("\n  → Test DELETE (suppression)...")
        try:
            cur.execute("DELETE FROM personnel WHERE id = %s", (test_id,))
            conn.commit()

            cur.execute("SELECT * FROM personnel WHERE id = %s", (test_id,))
            deleted_check = cur.fetchone()

            if deleted_check is None:
                print(f"  {Colors.GREEN}✓ Suppression réussie{Colors.RESET}")
                result.add_pass()
            else:
                raise Exception("Enregistrement non supprimé")
        except Exception as e:
            raise Exception(f"Échec DELETE: {str(e)}")

        cur.close()
        conn.close()

    except Exception as e:
        error_msg = f"Erreur CRUD: {str(e)}\n{traceback.format_exc()}"
        print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
        result.add_fail("Opérations CRUD", error_msg)


def test_import_modules(result: TestResult):
    """Test de l'importation des modules GUI"""
    print_test_header("TEST 6: MODULES GUI")

    gui_modules = [
        'core.gui.ui_theme',
        'core.gui.emac_ui_kit',
        'core.gui.gestion_evaluation',
        'core.gui.gestion_personnel',
        'core.gui.gestion_absences',
        'core.gui.manage_operateur',
        'core.gui.liste_et_grilles',
        'core.gui.creation_modification_poste',
        'core.gui.historique',
        'core.gui.planning',
        'core.gui.contract_management'
    ]

    for module_name in gui_modules:
        try:
            print(f"  → Import {module_name}...")
            __import__(module_name)
            print(f"  {Colors.GREEN}✓ {module_name} OK{Colors.RESET}")
            result.add_pass()
        except Exception as e:
            error_msg = f"Erreur import {module_name}: {str(e)}"
            print(f"  {Colors.RED}✗ {error_msg}{Colors.RESET}")
            result.add_fail(f"Import {module_name}", error_msg)


def main():
    """Fonction principale de test"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*70)
    print("     TEST DE SIMULATION COMPLETE - APPLICATION EMAC")
    print(f"     Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*70)
    print(f"{Colors.RESET}\n")

    result = TestResult()

    # Exécution des tests
    if not test_database_connection(result):
        print(f"\n{Colors.RED}{Colors.BOLD}ERREUR CRITIQUE: Impossible de se connecter à la base de données.{Colors.RESET}")
        print(f"{Colors.RED}Les tests suivants sont annulés.{Colors.RESET}\n")
        result.print_summary()
        return

    test_database_schema(result)
    test_services(result)
    test_data_integrity(result)
    test_crud_operations(result)
    test_import_modules(result)

    # Affichage du résumé
    result.print_summary()

    # Code de sortie
    sys.exit(0 if result.tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
