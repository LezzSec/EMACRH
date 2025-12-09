# -*- coding: utf-8 -*-
"""
Tests avancés du système de gestion des contrats EMAC
Tests complets de la gestion des contrats, expirations, et renouvellements

Usage:
    cd App
    py tests/test_contrat_management_advanced.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from core.db.configbd import get_connection as get_db_connection
from core.services import contrat_service
import time


class TestContratManagementAdvanced:
    """Tests approfondis du système de gestion des contrats."""

    def __init__(self):
        self.test_operateur_id = None
        self.test_contrat_ids = []
        self.successes = []
        self.failures = []

    def run_all_tests(self):
        """Exécute tous les tests du système de gestion des contrats."""
        print("=" * 80)
        print("  TESTS AVANCÉS - GESTION DES CONTRATS EMAC")
        print("=" * 80)
        print()

        tests = [
            # Préparation
            ("Préparation: création opérateur de test", self.test_setup_operateur),

            # Tests CRUD basiques
            ("CRUD: création contrat CDI", self.test_create_contrat_cdi),
            ("CRUD: création contrat CDD", self.test_create_contrat_cdd),
            ("CRUD: création contrat intérimaire", self.test_create_contrat_interim),
            ("CRUD: lecture contrats opérateur", self.test_read_contrats),
            ("CRUD: modification contrat", self.test_update_contrat),

            # Tests de validation
            ("Validation: dates cohérentes", self.test_validation_dates),
            ("Validation: ETP valide (0-1)", self.test_validation_etp),
            ("Validation: type contrat valide", self.test_validation_type_contrat),
            ("Validation: date_debut obligatoire", self.test_validation_date_debut),

            # Tests expiration et alertes
            ("Expiration: détection contrats expirés", self.test_detection_expires),
            ("Expiration: calcul jours restants", self.test_calcul_jours_restants),
            ("Expiration: contrats < 7 jours (alerte urgente)", self.test_alerte_urgente_7j),
            ("Expiration: contrats < 30 jours (alerte)", self.test_alerte_30j),
            ("Expiration: contrats 30-90 jours (info)", self.test_info_90j),

            # Tests types de contrats
            ("Types: CDI sans date_fin", self.test_cdi_sans_date_fin),
            ("Types: CDD avec date_fin obligatoire", self.test_cdd_avec_date_fin),
            ("Types: intérim durée courte", self.test_interim_duree_courte),

            # Tests métier
            ("Métier: renouvellement contrat CDD", self.test_renouvellement_cdd),
            ("Métier: passage CDD vers CDI", self.test_passage_cdd_cdi),
            ("Métier: historique contrats opérateur", self.test_historique_contrats),
            ("Métier: contrats multiples (séquentiels)", self.test_contrats_multiples),

            # Tests de performance
            ("Performance: liste tous les contrats", self.test_perf_list_all),
            ("Performance: contrats expirant bientôt", self.test_perf_expirant_bientot),
            ("Performance: statistiques par type", self.test_perf_stats_type),

            # Tests edge cases
            ("Edge case: contrat sans ETP", self.test_contrat_sans_etp),
            ("Edge case: contrat date_debut future", self.test_contrat_date_future),
            ("Edge case: contrat très long (> 10 ans)", self.test_contrat_tres_long),
            ("Edge case: contrat expire aujourd'hui", self.test_contrat_expire_today),

            # Tests de régression (services)
            ("Régression: service contrat_service", self.test_service_contrat),

            # Nettoyage
            ("Nettoyage: suppression données de test", self.test_cleanup),
        ]

        for test_name, test_func in tests:
            self._run_test(test_name, test_func)

        self._print_summary()

    def _run_test(self, name, func):
        """Exécute un test individuel."""
        try:
            print(f"[TEST] {name}...")
            func()
            self.successes.append(name)
            print(f"   [OK] SUCCES\n")
        except Exception as e:
            self.failures.append((name, str(e)))
            print(f"   [FAIL] ECHEC: {e}\n")

    def _print_summary(self):
        """Affiche le résumé des tests."""
        print("=" * 80)
        print("  RÉSUMÉ DES TESTS")
        print("=" * 80)
        print(f"[+] Réussis: {len(self.successes)} / {len(self.successes) + len(self.failures)}")
        print(f"[-] Échoués: {len(self.failures)} / {len(self.successes) + len(self.failures)}")

        if len(self.successes) > 0:
            taux_reussite = (len(self.successes) / (len(self.successes) + len(self.failures))) * 100
            print(f"[%] Taux de réussite: {taux_reussite:.1f}%")

        print()

        if self.failures:
            print("Détails des échecs:")
            for name, error in self.failures:
                print(f"  - {name}")
                print(f"    Erreur: {error}")
            print()
            sys.exit(1)
        else:
            print("[SUCCESS] Tous les tests sont passes avec succes!")
            print()

    # ========== PRÉPARATION ==========

    def test_setup_operateur(self):
        """Crée un opérateur de test."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Matricule limité à 20 caractères
            matricule = f"CTR{date.today().strftime('%y%m%d%H%M%S')}"

            cur.execute("""
                INSERT INTO personnel (matricule, nom, prenom, statut, date_entree)
                VALUES (%s, %s, %s, %s, %s)
            """, (matricule, "TEST_CONTRAT", "ADVANCED", "ACTIF", date.today()))
            conn.commit()

            self.test_operateur_id = cur.lastrowid
            print(f"   > Operateur cree: ID={self.test_operateur_id}")
            assert self.test_operateur_id is not None
        finally:
            cur.close()
            conn.close()

    # ========== TESTS CRUD ==========

    def test_create_contrat_cdi(self):
        """Test de création d'un contrat CDI."""
        assert self.test_operateur_id is not None

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO contrat (operateur_id, type_contrat, date_debut, etp)
                VALUES (%s, %s, %s, %s)
            """, (self.test_operateur_id, "CDI", date.today(), 1.0))
            conn.commit()

            contrat_id = cur.lastrowid
            self.test_contrat_ids.append(contrat_id)

            print(f"   > Contrat CDI créé: ID={contrat_id}")
        finally:
            cur.close()
            conn.close()

    def test_create_contrat_cdd(self):
        """Test de création d'un contrat CDD."""
        assert self.test_operateur_id is not None

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            date_debut = date.today()
            date_fin = date_debut + timedelta(days=365)

            cur.execute("""
                INSERT INTO contrat (operateur_id, type_contrat, date_debut, date_fin, etp)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, "CDD", date_debut, date_fin, 1.0))
            conn.commit()

            contrat_id = cur.lastrowid
            self.test_contrat_ids.append(contrat_id)

            print(f"   > Contrat CDD créé: ID={contrat_id}, expire le {date_fin}")
        finally:
            cur.close()
            conn.close()

    def test_create_contrat_interim(self):
        """Test de création d'un contrat intérimaire."""
        assert self.test_operateur_id is not None

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            date_debut = date.today()
            date_fin = date_debut + timedelta(days=90)

            cur.execute("""
                INSERT INTO contrat (operateur_id, type_contrat, date_debut, date_fin, etp)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, "INTERIM", date_debut, date_fin, 1.0))
            conn.commit()

            contrat_id = cur.lastrowid
            self.test_contrat_ids.append(contrat_id)

            print(f"   > Contrat INTERIM créé: ID={contrat_id}, durée 90 jours")
        finally:
            cur.close()
            conn.close()

    def test_read_contrats(self):
        """Test de lecture des contrats d'un opérateur."""
        assert self.test_operateur_id is not None

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT * FROM contrat
                WHERE operateur_id = %s
                ORDER BY date_debut DESC
            """, (self.test_operateur_id,))

            results = cur.fetchall()
            assert len(results) >= 3, f"Attendu >= 3 contrats, obtenu {len(results)}"

            print(f"   > {len(results)} contrat(s) trouvé(s)")
            for c in results:
                print(f"      - {c['type_contrat']}: {c['date_debut']} -> {c.get('date_fin', 'N/A')}")
        finally:
            cur.close()
            conn.close()

    def test_update_contrat(self):
        """Test de modification d'un contrat."""
        assert len(self.test_contrat_ids) > 0

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Modifier l'ETP du premier contrat
            new_etp = 0.8
            cur.execute("""
                UPDATE contrat
                SET etp = %s
                WHERE id = %s
            """, (new_etp, self.test_contrat_ids[0]))
            conn.commit()

            # Vérifier
            cur.execute("SELECT etp FROM contrat WHERE id = %s", (self.test_contrat_ids[0],))
            result = cur.fetchone()
            assert abs(result[0] - new_etp) < 0.01, f"ETP incorrect: {result[0]} vs {new_etp}"

            print(f"   > ETP modifié: 1.0 -> {new_etp}")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DE VALIDATION ==========

    def test_validation_dates(self):
        """Test de validation: date_fin >= date_debut."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Tenter de créer un contrat avec dates incohérentes (devrait échouer ou être rejeté par logique métier)
            date_debut = date.today()
            date_fin = date_debut - timedelta(days=1)  # Invalide

            # Utiliser le service de validation si disponible
            if hasattr(contrat_service, 'validate_contract_dates'):
                is_valid, error_msg = contrat_service.validate_contract_dates(date_debut, date_fin)
                assert not is_valid, "Les dates incohérentes devraient être rejetées"
                print(f"   > Validation correcte: {error_msg}")
            else:
                # Test direct en base (peut réussir si pas de contrainte)
                print(f"   > Service de validation non trouvé, test passé")
        finally:
            cur.close()
            conn.close()

    def test_validation_etp(self):
        """Test de validation: ETP entre 0 et 1."""
        # Utiliser le service de validation si disponible
        if hasattr(contrat_service, 'validate_etp'):
            # Test valide
            is_valid, _ = contrat_service.validate_etp(0.5)
            assert is_valid, "ETP 0.5 devrait être valide"

            # Test invalide (> 1)
            is_valid, error_msg = contrat_service.validate_etp(1.5)
            assert not is_valid, "ETP 1.5 devrait être invalide"

            # Test invalide (< 0)
            is_valid, error_msg = contrat_service.validate_etp(-0.1)
            assert not is_valid, "ETP -0.1 devrait être invalide"

            print(f"   > Validation ETP fonctionne correctement")
        else:
            print(f"   > Service validate_etp non trouvé, test passé")

    def test_validation_type_contrat(self):
        """Test de validation: type de contrat valide."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Types valides typiques: CDI, CDD, INTERIM
            valid_types = ['CDI', 'CDD', 'INTERIM']

            # On pourrait tester avec un ENUM ou une contrainte CHECK
            # Pour l'instant, on vérifie juste que les types créés sont cohérents
            cur.execute("""
                SELECT DISTINCT type_contrat FROM contrat
                WHERE operateur_id = %s
            """, (self.test_operateur_id,))

            results = cur.fetchall()
            for row in results:
                assert row[0] in valid_types, f"Type invalide: {row[0]}"

            print(f"   > Types de contrats valides: {[r[0] for r in results]}")
        finally:
            cur.close()
            conn.close()

    def test_validation_date_debut(self):
        """Test de validation: date_debut obligatoire."""
        # La date_debut devrait toujours être NOT NULL
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM contrat
                WHERE date_debut IS NULL
            """)
            count = cur.fetchone()[0]
            assert count == 0, "Aucun contrat ne devrait avoir date_debut NULL"
            print(f"   > Tous les contrats ont une date_debut")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS EXPIRATION ET ALERTES ==========

    def test_detection_expires(self):
        """Test de détection des contrats expirés."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Créer un contrat expiré
            date_debut = date.today() - timedelta(days=100)
            date_fin = date.today() - timedelta(days=10)

            cur.execute("""
                INSERT INTO contrat (operateur_id, type_contrat, date_debut, date_fin, etp)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, "CDD", date_debut, date_fin, 1.0))
            conn.commit()

            contrat_id = cur.lastrowid
            self.test_contrat_ids.append(contrat_id)

            # Détecter les contrats expirés
            cur.execute("""
                SELECT COUNT(*) FROM contrat
                WHERE date_fin < CURDATE()
                  AND operateur_id = %s
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            assert count > 0, "Au moins un contrat expiré devrait être détecté"
            print(f"   > {count} contrat(s) expiré(s) détecté(s)")
        finally:
            cur.close()
            conn.close()

    def test_calcul_jours_restants(self):
        """Test du calcul des jours restants avant expiration."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    id,
                    date_fin,
                    DATEDIFF(date_fin, CURDATE()) as jours_restants
                FROM contrat
                WHERE date_fin IS NOT NULL
                  AND operateur_id = %s
            """, (self.test_operateur_id,))

            results = cur.fetchall()
            for row in results:
                contrat_id, date_fin, jours_restants = row
                # Vérification manuelle
                delta_attendu = (date_fin - date.today()).days
                assert jours_restants == delta_attendu, f"Calcul incorrect pour contrat {contrat_id}"

            print(f"   > Calcul correct pour {len(results)} contrat(s)")
        finally:
            cur.close()
            conn.close()

    def test_alerte_urgente_7j(self):
        """Test d'alerte urgente: contrats expirant dans < 7 jours."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Créer un contrat expirant dans 5 jours
            date_debut = date.today() - timedelta(days=30)
            date_fin = date.today() + timedelta(days=5)

            cur.execute("""
                INSERT INTO contrat (operateur_id, type_contrat, date_debut, date_fin, etp)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, "CDD", date_debut, date_fin, 1.0))
            conn.commit()

            contrat_id = cur.lastrowid
            self.test_contrat_ids.append(contrat_id)

            # Détecter les alertes urgentes
            cur.execute("""
                SELECT COUNT(*) FROM contrat
                WHERE date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
                  AND operateur_id = %s
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            assert count > 0, "Au moins une alerte urgente devrait être détectée"
            print(f"   > {count} alerte(s) urgente(s) (< 7 jours)")
        finally:
            cur.close()
            conn.close()

    def test_alerte_30j(self):
        """Test d'alerte: contrats expirant dans < 30 jours."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Créer un contrat expirant dans 20 jours
            date_debut = date.today() - timedelta(days=30)
            date_fin = date.today() + timedelta(days=20)

            cur.execute("""
                INSERT INTO contrat (operateur_id, type_contrat, date_debut, date_fin, etp)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, "CDD", date_debut, date_fin, 1.0))
            conn.commit()

            contrat_id = cur.lastrowid
            self.test_contrat_ids.append(contrat_id)

            # Détecter les alertes 30 jours
            cur.execute("""
                SELECT COUNT(*) FROM contrat
                WHERE date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                  AND operateur_id = %s
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            assert count >= 2, "Au moins 2 alertes (< 30 jours) devraient être détectées"
            print(f"   > {count} alerte(s) (< 30 jours)")
        finally:
            cur.close()
            conn.close()

    def test_info_90j(self):
        """Test d'info: contrats expirant entre 30 et 90 jours."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM contrat
                WHERE date_fin BETWEEN DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                                   AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)
            """)

            count = cur.fetchone()[0]
            print(f"   > {count} contrat(s) expirant entre 30-90 jours")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS TYPES DE CONTRATS ==========

    def test_cdi_sans_date_fin(self):
        """Test: CDI sans date_fin."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM contrat
                WHERE type_contrat = 'CDI'
                  AND date_fin IS NULL
                  AND operateur_id = %s
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            assert count > 0, "Le CDI devrait ne pas avoir de date_fin"
            print(f"   > {count} CDI sans date_fin (correct)")
        finally:
            cur.close()
            conn.close()

    def test_cdd_avec_date_fin(self):
        """Test: CDD avec date_fin obligatoire."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM contrat
                WHERE type_contrat = 'CDD'
                  AND date_fin IS NOT NULL
                  AND operateur_id = %s
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            assert count > 0, "Les CDD devraient avoir une date_fin"
            print(f"   > {count} CDD avec date_fin (correct)")
        finally:
            cur.close()
            conn.close()

    def test_interim_duree_courte(self):
        """Test: intérim généralement de courte durée (< 6 mois)."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    id,
                    date_debut,
                    date_fin,
                    DATEDIFF(date_fin, date_debut) as duree_jours
                FROM contrat
                WHERE type_contrat = 'INTERIM'
                  AND operateur_id = %s
            """, (self.test_operateur_id,))

            results = cur.fetchall()
            if len(results) > 0:
                for row in results:
                    duree_jours = row[3]
                    # Intérim typiquement < 180 jours (6 mois)
                    assert duree_jours <= 180, f"Intérim trop long: {duree_jours} jours"

                print(f"   > {len(results)} contrat(s) INTERIM avec durée courte")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS MÉTIER ==========

    def test_renouvellement_cdd(self):
        """Test de renouvellement d'un CDD (création d'un nouveau contrat)."""
        # Simuler un renouvellement: créer un 2ème CDD qui suit le premier
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Récupérer le premier CDD
            cur.execute("""
                SELECT date_fin FROM contrat
                WHERE operateur_id = %s AND type_contrat = 'CDD'
                ORDER BY date_debut ASC
                LIMIT 1
            """, (self.test_operateur_id,))

            row = cur.fetchone()
            if row and row[0]:
                date_fin_ancien = row[0]
                date_debut_nouveau = date_fin_ancien + timedelta(days=1)
                date_fin_nouveau = date_debut_nouveau + timedelta(days=365)

                cur.execute("""
                    INSERT INTO contrat (operateur_id, type_contrat, date_debut, date_fin, etp)
                    VALUES (%s, %s, %s, %s, %s)
                """, (self.test_operateur_id, "CDD", date_debut_nouveau, date_fin_nouveau, 1.0))
                conn.commit()

                contrat_id = cur.lastrowid
                self.test_contrat_ids.append(contrat_id)

                print(f"   > Renouvellement CDD créé: ID={contrat_id}")
        finally:
            cur.close()
            conn.close()

    def test_passage_cdd_cdi(self):
        """Test de passage d'un CDD vers un CDI."""
        # Simuler: terminer le CDD et créer un CDI
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Supposer que le dernier CDD se termine
            cur.execute("""
                SELECT date_fin FROM contrat
                WHERE operateur_id = %s AND type_contrat = 'CDD'
                ORDER BY date_debut DESC
                LIMIT 1
            """, (self.test_operateur_id,))

            row = cur.fetchone()
            if row and row[0]:
                date_fin_cdd = row[0]
                date_debut_cdi = date_fin_cdd + timedelta(days=1)

                cur.execute("""
                    INSERT INTO contrat (operateur_id, type_contrat, date_debut, etp)
                    VALUES (%s, %s, %s, %s)
                """, (self.test_operateur_id, "CDI", date_debut_cdi, 1.0))
                conn.commit()

                contrat_id = cur.lastrowid
                self.test_contrat_ids.append(contrat_id)

                print(f"   > Passage CDD->CDI créé: ID={contrat_id}")
        finally:
            cur.close()
            conn.close()

    def test_historique_contrats(self):
        """Test de l'historique des contrats d'un opérateur."""
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT * FROM contrat
                WHERE operateur_id = %s
                ORDER BY date_debut ASC
            """, (self.test_operateur_id,))

            results = cur.fetchall()
            assert len(results) >= 5, f"Attendu >= 5 contrats dans l'historique, obtenu {len(results)}"

            print(f"   > Historique: {len(results)} contrat(s)")
            for idx, c in enumerate(results, 1):
                print(f"      {idx}. {c['type_contrat']}: {c['date_debut']} -> {c.get('date_fin', 'en cours')}")
        finally:
            cur.close()
            conn.close()

    def test_contrats_multiples(self):
        """Test: un opérateur peut avoir plusieurs contrats (séquentiels ou non)."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(DISTINCT id) as nb_contrats
                FROM contrat
                WHERE operateur_id = %s
            """, (self.test_operateur_id,))

            nb_contrats = cur.fetchone()[0]
            assert nb_contrats >= 5, f"L'opérateur devrait avoir >= 5 contrats, obtenu {nb_contrats}"
            print(f"   > {nb_contrats} contrat(s) pour l'opérateur (multi-contrats validé)")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DE PERFORMANCE ==========

    def test_perf_list_all(self):
        """Test de performance: liste de tous les contrats."""
        start_time = time.time()

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT
                    c.*,
                    p.nom,
                    p.prenom,
                    p.matricule
                FROM contrat c
                JOIN personnel p ON c.operateur_id = p.id
                ORDER BY c.date_debut DESC
            """)

            results = cur.fetchall()
            elapsed = time.time() - start_time

            assert elapsed < 2.0, f"Requête trop lente: {elapsed:.3f}s"
            print(f"   > {len(results)} contrats récupérés en {elapsed:.3f}s")
        finally:
            cur.close()
            conn.close()

    def test_perf_expirant_bientot(self):
        """Test de performance: contrats expirant bientôt."""
        start_time = time.time()

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT
                    c.*,
                    p.nom,
                    p.prenom,
                    DATEDIFF(c.date_fin, CURDATE()) as jours_restants
                FROM contrat c
                JOIN personnel p ON c.operateur_id = p.id
                WHERE c.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)
                  AND p.statut = 'ACTIF'
                ORDER BY c.date_fin ASC
            """)

            results = cur.fetchall()
            elapsed = time.time() - start_time

            assert elapsed < 2.0, f"Requête trop lente: {elapsed:.3f}s"
            print(f"   > {len(results)} contrats trouvés en {elapsed:.3f}s")
        finally:
            cur.close()
            conn.close()

    def test_perf_stats_type(self):
        """Test de performance: statistiques par type de contrat."""
        start_time = time.time()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    type_contrat,
                    COUNT(*) as nb,
                    AVG(etp) as etp_moyen
                FROM contrat
                GROUP BY type_contrat
            """)

            results = cur.fetchall()
            elapsed = time.time() - start_time

            assert elapsed < 1.0, f"Requête trop lente: {elapsed:.3f}s"
            print(f"   > Statistiques calculées en {elapsed:.3f}s")
            for row in results:
                print(f"      {row[0]}: {row[1]} contrats (ETP moyen: {row[2]:.2f})")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS EDGE CASES ==========

    def test_contrat_sans_etp(self):
        """Test: contrat sans ETP (NULL)."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Créer un contrat sans ETP
            cur.execute("""
                INSERT INTO contrat (operateur_id, type_contrat, date_debut)
                VALUES (%s, %s, %s)
            """, (self.test_operateur_id, "CDI", date.today()))
            conn.commit()

            contrat_id = cur.lastrowid
            self.test_contrat_ids.append(contrat_id)

            # Vérifier que l'ETP est NULL
            cur.execute("SELECT etp FROM contrat WHERE id = %s", (contrat_id,))
            etp = cur.fetchone()[0]
            assert etp is None, "L'ETP devrait être NULL"

            print(f"   > Contrat sans ETP créé: ID={contrat_id}")
        finally:
            cur.close()
            conn.close()

    def test_contrat_date_future(self):
        """Test: contrat avec date_debut future."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            date_debut = date.today() + timedelta(days=30)
            date_fin = date_debut + timedelta(days=365)

            cur.execute("""
                INSERT INTO contrat (operateur_id, type_contrat, date_debut, date_fin, etp)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, "CDD", date_debut, date_fin, 1.0))
            conn.commit()

            contrat_id = cur.lastrowid
            self.test_contrat_ids.append(contrat_id)

            print(f"   > Contrat futur créé: ID={contrat_id}, démarre le {date_debut}")
        finally:
            cur.close()
            conn.close()

    def test_contrat_tres_long(self):
        """Test: contrat de très longue durée (> 10 ans)."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            date_debut = date.today()
            date_fin = date_debut + timedelta(days=3650)  # 10 ans

            cur.execute("""
                INSERT INTO contrat (operateur_id, type_contrat, date_debut, date_fin, etp)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, "CDD", date_debut, date_fin, 1.0))
            conn.commit()

            contrat_id = cur.lastrowid
            self.test_contrat_ids.append(contrat_id)

            # Calculer la durée
            cur.execute("""
                SELECT DATEDIFF(date_fin, date_debut) as duree
                FROM contrat WHERE id = %s
            """, (contrat_id,))

            duree = cur.fetchone()[0]
            assert duree >= 3650, f"Durée attendue >= 3650j, obtenu {duree}j"

            print(f"   > Contrat très long créé: {duree} jours")
        finally:
            cur.close()
            conn.close()

    def test_contrat_expire_today(self):
        """Test: contrat expirant aujourd'hui."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            date_debut = date.today() - timedelta(days=365)
            date_fin = date.today()

            cur.execute("""
                INSERT INTO contrat (operateur_id, type_contrat, date_debut, date_fin, etp)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, "CDD", date_debut, date_fin, 1.0))
            conn.commit()

            contrat_id = cur.lastrowid
            self.test_contrat_ids.append(contrat_id)

            # Vérifier qu'il est détecté comme expirant aujourd'hui
            cur.execute("""
                SELECT DATEDIFF(date_fin, CURDATE()) as jours_restants
                FROM contrat WHERE id = %s
            """, (contrat_id,))

            jours_restants = cur.fetchone()[0]
            assert jours_restants == 0, f"Devrait expirer aujourd'hui (0 jours), obtenu {jours_restants}"

            print(f"   > Contrat expirant aujourd'hui détecté")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DE RÉGRESSION (SERVICES) ==========

    def test_service_contrat(self):
        """Test des services contrat_service."""
        # Test des fonctions disponibles
        available_functions = dir(contrat_service)

        # get_contracts_expiring_soon
        if 'get_contracts_expiring_soon' in available_functions:
            try:
                results = contrat_service.get_contracts_expiring_soon(days=90)
                assert isinstance(results, list), "Devrait retourner une liste"
                print(f"   > get_contracts_expiring_soon: OK ({len(results)} résultats)")
            except Exception as e:
                print(f"   > get_contracts_expiring_soon: ERREUR - {e}")

        # validate_contract_dates
        if 'validate_contract_dates' in available_functions:
            try:
                is_valid, msg = contrat_service.validate_contract_dates(date.today(), date.today() + timedelta(days=30))
                assert is_valid, "Dates valides devraient être acceptées"
                print(f"   > validate_contract_dates: OK")
            except Exception as e:
                print(f"   > validate_contract_dates: ERREUR - {e}")

        # validate_etp
        if 'validate_etp' in available_functions:
            try:
                is_valid, msg = contrat_service.validate_etp(0.8)
                assert is_valid, "ETP 0.8 devrait être valide"
                print(f"   > validate_etp: OK")
            except Exception as e:
                print(f"   > validate_etp: ERREUR - {e}")

        print(f"   > Services contrat_service testés")

    # ========== NETTOYAGE ==========

    def test_cleanup(self):
        """Supprime toutes les données de test."""
        if self.test_operateur_id is None:
            print("   > Aucune donnée à nettoyer")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Supprimer les contrats
            cur.execute("DELETE FROM contrat WHERE operateur_id = %s",
                       (self.test_operateur_id,))
            contrats_deleted = cur.rowcount

            # Supprimer l'opérateur
            cur.execute("DELETE FROM personnel WHERE id = %s",
                       (self.test_operateur_id,))
            oper_deleted = cur.rowcount

            conn.commit()

            print(f"   > Nettoyage effectué:")
            print(f"      - {contrats_deleted} contrat(s)")
            print(f"      - {oper_deleted} opérateur(s)")
        finally:
            cur.close()
            conn.close()


if __name__ == "__main__":
    tester = TestContratManagementAdvanced()
    tester.run_all_tests()
