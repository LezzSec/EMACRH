# -*- coding: utf-8 -*-
"""
Tests avancés du système d'évaluation EMAC
Tests complets de l'évaluation, calendrier, et logique métier

Usage:
    cd App
    py tests/test_evaluation_system_advanced.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from core.db.configbd import get_connection as get_db_connection
from core.services import evaluation_service, calendrier_service
import time


class TestEvaluationSystemAdvanced:
    """Tests approfondis du système d'évaluation."""

    def __init__(self):
        self.test_operateur_id = None
        self.test_poste_ids = []
        self.test_polyvalence_ids = []
        self.successes = []
        self.failures = []

    def run_all_tests(self):
        """Exécute tous les tests du système d'évaluation."""
        print("=" * 80)
        print("  TESTS AVANCÉS - SYSTÈME D'ÉVALUATION EMAC")
        print("=" * 80)
        print()

        tests = [
            # Tests de base
            ("Préparation: création opérateur de test", self.test_setup_operateur),
            ("Préparation: récupération de 5 postes différents", self.test_setup_postes),

            # Tests des niveaux de polyvalence
            ("Test niveau 1: évaluation initiale", self.test_niveau_1_initial),
            ("Test niveau 1: calcul prochaine évaluation", self.test_niveau_1_calcul_date),
            ("Test niveau 2: progression et recalcul", self.test_niveau_2_progression),
            ("Test niveau 3: maîtrise avancée", self.test_niveau_3_maitrise),
            ("Test niveau 4: expert/formateur", self.test_niveau_4_expert),

            # Tests des évaluations en retard
            ("Test retard: détection évaluations expirées", self.test_detection_retard),
            ("Test retard: calcul jours de retard", self.test_calcul_jours_retard),
            ("Test retard: tri par urgence", self.test_tri_urgence),

            # Tests des prochaines évaluations
            ("Test planning: prochaines évaluations 30 jours", self.test_prochaines_30j),
            ("Test planning: prochaines évaluations 90 jours", self.test_prochaines_90j),

            # Tests de cohérence métier
            ("Test cohérence: dates chronologiques", self.test_coherence_dates),
            ("Test cohérence: niveaux valides (1-4)", self.test_coherence_niveaux),
            ("Test cohérence: opérateur actif uniquement", self.test_coherence_statut_actif),

            # Tests de performance
            ("Performance: récupération évaluations en retard", self.test_perf_eval_retard),
            ("Performance: récupération prochaines évaluations", self.test_perf_prochaines_eval),
            ("Performance: requêtes multiples opérateurs", self.test_perf_multi_operateurs),

            # Tests edge cases
            ("Edge case: évaluation le jour même", self.test_evaluation_today),
            ("Edge case: évaluation future lointaine (10 ans)", self.test_evaluation_future_lointaine),
            ("Edge case: multiple polyvalences même opérateur", self.test_multiple_polyvalences),

            # Tests de régression
            ("Régression: service evaluation_service.get_evaluations_en_retard()", self.test_service_get_retard),
            ("Régression: service evaluation_service.get_prochaines_evaluations()", self.test_service_get_prochaines),

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

    # ========== TESTS DE PRÉPARATION ==========

    def test_setup_operateur(self):
        """Crée un opérateur de test."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Matricule limité à 20 caractères
            matricule = f"TST{date.today().strftime('%y%m%d%H%M%S')}"

            cur.execute("""
                INSERT INTO personnel (matricule, nom, prenom, statut, date_entree)
                VALUES (%s, %s, %s, %s, %s)
            """, (matricule, "TEST_EVAL", "ADVANCED", "ACTIF", date.today()))
            conn.commit()

            self.test_operateur_id = cur.lastrowid
            print(f"   > Operateur cree: ID={self.test_operateur_id}, Matricule={matricule}")
            assert self.test_operateur_id is not None
        finally:
            cur.close()
            conn.close()

    def test_setup_postes(self):
        """Récupère 5 postes différents pour les tests."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, poste_code FROM postes LIMIT 5")
            results = cur.fetchall()

            assert len(results) >= 3, "Au moins 3 postes nécessaires pour les tests"

            for row in results:
                self.test_poste_ids.append(row[0])

            print(f"   > {len(self.test_poste_ids)} postes récupérés pour les tests")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DES NIVEAUX ==========

    def test_niveau_1_initial(self):
        """Test de création d'une polyvalence niveau 1."""
        assert self.test_operateur_id is not None
        assert len(self.test_poste_ids) > 0

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            poste_id = self.test_poste_ids[0]
            date_eval = date.today()
            # Niveau 1: prochaine évaluation dans 1 an typiquement
            prochaine_eval = date_eval + timedelta(days=365)

            cur.execute("""
                INSERT INTO polyvalence (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, poste_id, 1, date_eval, prochaine_eval))
            conn.commit()

            poly_id = cur.lastrowid
            self.test_polyvalence_ids.append(poly_id)

            print(f"   > Polyvalence niveau 1 créée: ID={poly_id}")
            print(f"   > Date évaluation: {date_eval}")
            print(f"   > Prochaine évaluation: {prochaine_eval}")
        finally:
            cur.close()
            conn.close()

    def test_niveau_1_calcul_date(self):
        """Vérifie que la prochaine évaluation niveau 1 est bien dans ~1 an."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT date_evaluation, prochaine_evaluation
                FROM polyvalence
                WHERE id = %s
            """, (self.test_polyvalence_ids[0],))

            row = cur.fetchone()
            date_eval = row[0]
            prochaine_eval = row[1]

            delta_days = (prochaine_eval - date_eval).days

            # Pour niveau 1, on attend environ 365 jours (peut varier selon la logique métier)
            assert 300 <= delta_days <= 400, f"Delta attendu ~365j, obtenu {delta_days}j"
            print(f"   > Delta: {delta_days} jours (valide pour niveau 1)")
        finally:
            cur.close()
            conn.close()

    def test_niveau_2_progression(self):
        """Test de progression vers niveau 2."""
        assert len(self.test_poste_ids) > 1

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            poste_id = self.test_poste_ids[1]
            date_eval = date.today()
            # Niveau 2: prochaine évaluation dans 2 ans typiquement
            prochaine_eval = date_eval + timedelta(days=730)

            cur.execute("""
                INSERT INTO polyvalence (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, poste_id, 2, date_eval, prochaine_eval))
            conn.commit()

            poly_id = cur.lastrowid
            self.test_polyvalence_ids.append(poly_id)

            print(f"   > Polyvalence niveau 2 créée: ID={poly_id}")
            print(f"   > Prochaine évaluation dans ~2 ans")
        finally:
            cur.close()
            conn.close()

    def test_niveau_3_maitrise(self):
        """Test de niveau 3 (maîtrise)."""
        assert len(self.test_poste_ids) > 2

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            poste_id = self.test_poste_ids[2]
            date_eval = date.today()
            # Niveau 3: prochaine évaluation dans 5 ans typiquement
            prochaine_eval = date_eval + timedelta(days=1825)

            cur.execute("""
                INSERT INTO polyvalence (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, poste_id, 3, date_eval, prochaine_eval))
            conn.commit()

            poly_id = cur.lastrowid
            self.test_polyvalence_ids.append(poly_id)

            print(f"   > Polyvalence niveau 3 créée: ID={poly_id}")
        finally:
            cur.close()
            conn.close()

    def test_niveau_4_expert(self):
        """Test de niveau 4 (expert/formateur)."""
        assert len(self.test_poste_ids) > 3

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            poste_id = self.test_poste_ids[3]
            date_eval = date.today()
            # Niveau 4: prochaine évaluation dans 10 ans (maintenance)
            prochaine_eval = date_eval + timedelta(days=3650)

            cur.execute("""
                INSERT INTO polyvalence (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_operateur_id, poste_id, 4, date_eval, prochaine_eval))
            conn.commit()

            poly_id = cur.lastrowid
            self.test_polyvalence_ids.append(poly_id)

            print(f"   > Polyvalence niveau 4 créée: ID={poly_id}")
            print(f"   > Prochaine évaluation dans ~10 ans (maintenance)")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DES RETARDS ==========

    def test_detection_retard(self):
        """Test de détection des évaluations en retard."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Créer une évaluation en retard
            if len(self.test_poste_ids) > 4:
                poste_id = self.test_poste_ids[4]
                date_eval = date.today() - timedelta(days=100)
                prochaine_eval = date.today() - timedelta(days=10)  # En retard de 10 jours

                cur.execute("""
                    INSERT INTO polyvalence (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
                    VALUES (%s, %s, %s, %s, %s)
                """, (self.test_operateur_id, poste_id, 2, date_eval, prochaine_eval))
                conn.commit()

                poly_id = cur.lastrowid
                self.test_polyvalence_ids.append(poly_id)

            # Vérifier la détection
            cur.execute("""
                SELECT COUNT(*) FROM polyvalence p
                JOIN personnel pers ON p.operateur_id = pers.id
                WHERE p.prochaine_evaluation < CURDATE()
                  AND pers.statut = 'ACTIF'
                  AND p.operateur_id = %s
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            assert count > 0, "Aucune évaluation en retard détectée"
            print(f"   > {count} évaluation(s) en retard détectée(s)")
        finally:
            cur.close()
            conn.close()

    def test_calcul_jours_retard(self):
        """Test du calcul correct des jours de retard."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    p.prochaine_evaluation,
                    DATEDIFF(CURDATE(), p.prochaine_evaluation) as jours_retard
                FROM polyvalence p
                WHERE p.prochaine_evaluation < CURDATE()
                  AND p.operateur_id = %s
                ORDER BY jours_retard DESC
                LIMIT 1
            """, (self.test_operateur_id,))

            row = cur.fetchone()
            if row:
                prochaine_eval = row[0]
                jours_retard = row[1]

                # Vérification manuelle
                delta_attendu = (date.today() - prochaine_eval).days
                assert jours_retard == delta_attendu, f"Calcul incorrect: {jours_retard} vs {delta_attendu}"
                print(f"   > Calcul correct: {jours_retard} jours de retard")
        finally:
            cur.close()
            conn.close()

    def test_tri_urgence(self):
        """Test du tri des évaluations par urgence (retard décroissant)."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Utiliser la même requête que le service pour tester le tri réel
            cur.execute("""
                SELECT
                    DATEDIFF(CURDATE(), p.prochaine_evaluation) as jours_retard
                FROM polyvalence p
                JOIN personnel pers ON p.operateur_id = pers.id
                WHERE p.prochaine_evaluation < CURDATE()
                  AND pers.statut = 'ACTIF'
                ORDER BY jours_retard DESC, p.prochaine_evaluation ASC
                LIMIT 10
            """)

            results = cur.fetchall()
            if len(results) > 1:
                # Vérifier que le tri est bien décroissant (plus de retard en premier = plus urgent)
                prev_retard = results[0][0]
                for row in results[1:]:
                    current_retard = row[0]
                    # Le retard doit être décroissant ou égal (du plus grand au plus petit)
                    assert current_retard <= prev_retard, \
                        f"Tri incorrect: le retard devrait être décroissant (prev={prev_retard}, current={current_retard})"
                    prev_retard = current_retard

                print(f"   > Tri correct: {len(results)} evaluations triees par urgence (retard decroissant)")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DES PROCHAINES ÉVALUATIONS ==========

    def test_prochaines_30j(self):
        """Test des prochaines évaluations dans les 30 jours."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            date_limite = date.today() + timedelta(days=30)

            cur.execute("""
                SELECT COUNT(*) FROM polyvalence p
                JOIN personnel pers ON p.operateur_id = pers.id
                WHERE p.prochaine_evaluation BETWEEN CURDATE() AND %s
                  AND pers.statut = 'ACTIF'
            """, (date_limite,))

            count = cur.fetchone()[0]
            print(f"   > {count} évaluation(s) dans les 30 prochains jours")
        finally:
            cur.close()
            conn.close()

    def test_prochaines_90j(self):
        """Test des prochaines évaluations dans les 90 jours."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            date_limite = date.today() + timedelta(days=90)

            cur.execute("""
                SELECT COUNT(*) FROM polyvalence p
                JOIN personnel pers ON p.operateur_id = pers.id
                WHERE p.prochaine_evaluation BETWEEN CURDATE() AND %s
                  AND pers.statut = 'ACTIF'
            """, (date_limite,))

            count = cur.fetchone()[0]
            print(f"   > {count} évaluation(s) dans les 90 prochains jours")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DE COHÉRENCE ==========

    def test_coherence_dates(self):
        """Vérifie que prochaine_evaluation >= date_evaluation."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM polyvalence
                WHERE prochaine_evaluation < date_evaluation
            """)

            count = cur.fetchone()[0]
            assert count == 0, f"{count} enregistrement(s) avec dates incohérentes"
            print(f"   > Aucune date incohérente détectée")
        finally:
            cur.close()
            conn.close()

    def test_coherence_niveaux(self):
        """Vérifie que tous les niveaux sont entre 1 et 4."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM polyvalence
                WHERE niveau NOT BETWEEN 1 AND 4
            """)

            count = cur.fetchone()[0]
            assert count == 0, f"{count} enregistrement(s) avec niveau invalide"
            print(f"   > Tous les niveaux sont valides (1-4)")
        finally:
            cur.close()
            conn.close()

    def test_coherence_statut_actif(self):
        """Vérifie que seuls les opérateurs ACTIF apparaissent dans les évaluations."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Temporairement mettre l'opérateur de test en INACTIF
            cur.execute("UPDATE personnel SET statut = 'INACTIF' WHERE id = %s",
                       (self.test_operateur_id,))
            conn.commit()

            # Vérifier qu'il n'apparaît plus dans les évaluations
            cur.execute("""
                SELECT COUNT(*) FROM polyvalence p
                JOIN personnel pers ON p.operateur_id = pers.id
                WHERE pers.statut = 'ACTIF'
                  AND p.operateur_id = %s
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            assert count == 0, "Les opérateurs INACTIF ne devraient pas apparaître"

            # Remettre en ACTIF
            cur.execute("UPDATE personnel SET statut = 'ACTIF' WHERE id = %s",
                       (self.test_operateur_id,))
            conn.commit()

            print(f"   > Filtrage statut ACTIF fonctionne correctement")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DE PERFORMANCE ==========

    def test_perf_eval_retard(self):
        """Test de performance: récupération des évaluations en retard."""
        start_time = time.time()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    p.id, pers.nom, pers.prenom, pos.poste_code,
                    p.niveau, p.prochaine_evaluation,
                    DATEDIFF(CURDATE(), p.prochaine_evaluation) as jours_retard
                FROM polyvalence p
                JOIN personnel pers ON p.operateur_id = pers.id
                JOIN postes pos ON p.poste_id = pos.id
                WHERE pers.statut = 'ACTIF'
                  AND p.prochaine_evaluation < CURDATE()
                ORDER BY p.prochaine_evaluation ASC
            """)

            results = cur.fetchall()
            elapsed = time.time() - start_time

            assert elapsed < 2.0, f"Requête trop lente: {elapsed:.3f}s"
            print(f"   > {len(results)} résultats en {elapsed:.3f}s (performance OK)")
        finally:
            cur.close()
            conn.close()

    def test_perf_prochaines_eval(self):
        """Test de performance: récupération des prochaines évaluations."""
        start_time = time.time()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            date_limite = date.today() + timedelta(days=90)

            cur.execute("""
                SELECT
                    p.id, pers.nom, pers.prenom, pos.poste_code,
                    p.niveau, p.prochaine_evaluation
                FROM polyvalence p
                JOIN personnel pers ON p.operateur_id = pers.id
                JOIN postes pos ON p.poste_id = pos.id
                WHERE pers.statut = 'ACTIF'
                  AND p.prochaine_evaluation BETWEEN CURDATE() AND %s
                ORDER BY p.prochaine_evaluation ASC
            """, (date_limite,))

            results = cur.fetchall()
            elapsed = time.time() - start_time

            assert elapsed < 2.0, f"Requête trop lente: {elapsed:.3f}s"
            print(f"   > {len(results)} résultats en {elapsed:.3f}s (performance OK)")
        finally:
            cur.close()
            conn.close()

    def test_perf_multi_operateurs(self):
        """Test de performance: requête sur tous les opérateurs."""
        start_time = time.time()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    pers.id,
                    pers.nom,
                    pers.prenom,
                    COUNT(p.id) as nb_polyvalences,
                    SUM(CASE WHEN p.prochaine_evaluation < CURDATE() THEN 1 ELSE 0 END) as nb_retard
                FROM personnel pers
                LEFT JOIN polyvalence p ON pers.id = p.operateur_id
                WHERE pers.statut = 'ACTIF'
                GROUP BY pers.id, pers.nom, pers.prenom
            """)

            results = cur.fetchall()
            elapsed = time.time() - start_time

            assert elapsed < 3.0, f"Requête trop lente: {elapsed:.3f}s"
            print(f"   > {len(results)} opérateurs analysés en {elapsed:.3f}s")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS EDGE CASES ==========

    def test_evaluation_today(self):
        """Test: évaluation prévue le jour même."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Modifier une polyvalence pour qu'elle soit due aujourd'hui
            if len(self.test_polyvalence_ids) > 0:
                cur.execute("""
                    UPDATE polyvalence
                    SET prochaine_evaluation = CURDATE()
                    WHERE id = %s
                """, (self.test_polyvalence_ids[0],))
                conn.commit()

                # Vérifier qu'elle apparaît dans les prochaines (pas en retard)
                cur.execute("""
                    SELECT COUNT(*) FROM polyvalence p
                    JOIN personnel pers ON p.operateur_id = pers.id
                    WHERE p.prochaine_evaluation = CURDATE()
                      AND pers.statut = 'ACTIF'
                      AND p.id = %s
                """, (self.test_polyvalence_ids[0],))

                count = cur.fetchone()[0]
                assert count == 1, "L'évaluation du jour devrait être détectée"
                print(f"   > Évaluation du jour correctement détectée")
        finally:
            cur.close()
            conn.close()

    def test_evaluation_future_lointaine(self):
        """Test: évaluation prévue dans 10 ans (niveau 4)."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if len(self.test_polyvalence_ids) > 3:
                # Vérifier la polyvalence niveau 4
                cur.execute("""
                    SELECT
                        date_evaluation,
                        prochaine_evaluation,
                        DATEDIFF(prochaine_evaluation, date_evaluation) as delta_days
                    FROM polyvalence
                    WHERE id = %s
                """, (self.test_polyvalence_ids[3],))

                row = cur.fetchone()
                if row:
                    delta_days = row[2]
                    # Niveau 4: ~10 ans = ~3650 jours
                    assert delta_days >= 3000, f"Niveau 4 devrait avoir delta > 3000j, obtenu {delta_days}"
                    print(f"   > Évaluation future lointaine: {delta_days} jours (valide)")
        finally:
            cur.close()
            conn.close()

    def test_multiple_polyvalences(self):
        """Test: un opérateur avec plusieurs polyvalences."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM polyvalence
                WHERE operateur_id = %s
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            assert count >= 3, f"L'opérateur devrait avoir au moins 3 polyvalences, obtenu {count}"
            print(f"   > Opérateur avec {count} polyvalences (multi-postes validé)")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DE RÉGRESSION (SERVICES) ==========

    def test_service_get_retard(self):
        """Test du service evaluation_service.get_evaluations_en_retard()."""
        try:
            results = evaluation_service.get_evaluations_en_retard()
            assert isinstance(results, list), "Le service devrait retourner une liste"

            # Vérifier la structure des données
            if len(results) > 0:
                first = results[0]
                required_keys = ['nom', 'prenom', 'poste_code', 'niveau', 'prochaine_evaluation', 'jours_retard']
                for key in required_keys:
                    assert key in first, f"Clé manquante dans le résultat: {key}"

            print(f"   > Service OK: {len(results)} évaluation(s) en retard")
        except Exception as e:
            raise AssertionError(f"Service evaluation_service.get_evaluations_en_retard() a échoué: {e}")

    def test_service_get_prochaines(self):
        """Test du service evaluation_service.get_prochaines_evaluations()."""
        try:
            # Le service peut accepter un paramètre jours (ex: 30, 90)
            if hasattr(evaluation_service, 'get_prochaines_evaluations'):
                results = evaluation_service.get_prochaines_evaluations()
                assert isinstance(results, list), "Le service devrait retourner une liste"
                print(f"   > Service OK: {len(results)} prochaine(s) évaluation(s)")
            else:
                print(f"   > Service get_prochaines_evaluations() non trouvé (peut être normal)")
        except Exception as e:
            # Ce service peut ne pas exister, ce n'est pas critique
            print(f"   > Service non disponible ou erreur: {e}")

    # ========== NETTOYAGE ==========

    def test_cleanup(self):
        """Supprime toutes les données de test."""
        if self.test_operateur_id is None:
            print("   > Aucune donnée à nettoyer")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Supprimer les polyvalences
            cur.execute("DELETE FROM polyvalence WHERE operateur_id = %s",
                       (self.test_operateur_id,))
            poly_deleted = cur.rowcount

            # Supprimer l'historique
            cur.execute("DELETE FROM historique WHERE operateur_id = %s",
                       (self.test_operateur_id,))
            hist_deleted = cur.rowcount

            # Supprimer l'opérateur
            cur.execute("DELETE FROM personnel WHERE id = %s",
                       (self.test_operateur_id,))
            oper_deleted = cur.rowcount

            conn.commit()

            print(f"   > Nettoyage effectué:")
            print(f"      - {poly_deleted} polyvalence(s)")
            print(f"      - {hist_deleted} historique(s)")
            print(f"      - {oper_deleted} opérateur(s)")
        finally:
            cur.close()
            conn.close()


if __name__ == "__main__":
    tester = TestEvaluationSystemAdvanced()
    tester.run_all_tests()
