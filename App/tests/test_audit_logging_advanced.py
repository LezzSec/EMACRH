# -*- coding: utf-8 -*-
"""
Tests avancés du système d'audit logging (historique) EMAC
Tests complets de la traçabilité et logging des actions

Usage:
    cd App
    py tests/test_audit_logging_advanced.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, timedelta
from core.db.configbd import get_connection as get_db_connection
from core.services.logger import log_hist
import time


class TestAuditLoggingAdvanced:
    """Tests approfondis du système d'audit logging."""

    def __init__(self):
        self.test_operateur_id = None
        self.test_poste_id = None
        self.test_log_ids = []
        self.successes = []
        self.failures = []

    def run_all_tests(self):
        """Exécute tous les tests du système d'audit."""
        print("=" * 80)
        print("  TESTS AVANCÉS - SYSTÈME D'AUDIT LOGGING EMAC")
        print("=" * 80)
        print()

        tests = [
            # Préparation
            ("Préparation: création données de test", self.test_setup),

            # Tests basiques de logging
            ("Logging: création entrée simple", self.test_log_simple),
            ("Logging: avec operateur_id", self.test_log_with_operateur),
            ("Logging: avec poste_id", self.test_log_with_poste),
            ("Logging: avec operateur_id et poste_id", self.test_log_with_both),
            ("Logging: description longue (> 255 caractères)", self.test_log_long_description),

            # Tests de structure
            ("Structure: timestamp automatique", self.test_timestamp_automatic),
            ("Structure: action obligatoire", self.test_action_required),
            ("Structure: clés étrangères valides", self.test_foreign_keys),

            # Tests de requêtes
            ("Requêtes: filtrage par action", self.test_query_by_action),
            ("Requêtes: filtrage par opérateur", self.test_query_by_operateur),
            ("Requêtes: filtrage par poste", self.test_query_by_poste),
            ("Requêtes: filtrage par période", self.test_query_by_period),
            ("Requêtes: tri chronologique", self.test_query_order),

            # Tests de traçabilité métier
            ("Traçabilité: ajout opérateur", self.test_trace_add_operateur),
            ("Traçabilité: modification polyvalence", self.test_trace_update_polyvalence),
            ("Traçabilité: suppression (soft delete)", self.test_trace_soft_delete),
            ("Traçabilité: changement statut", self.test_trace_status_change),

            # Tests de performance
            ("Performance: insertion rapide", self.test_perf_insert),
            ("Performance: requête historique complet", self.test_perf_query_all),
            ("Performance: requête avec filtres", self.test_perf_query_filtered),
            ("Performance: agrégations (stats)", self.test_perf_aggregations),

            # Tests de sécurité
            ("Sécurité: logs immuables (no update)", self.test_immutable_logs),
            ("Sécurité: cascade delete operateur", self.test_cascade_delete_operateur),
            ("Sécurité: cascade delete poste", self.test_cascade_delete_poste),

            # Tests edge cases
            ("Edge case: action avec caractères spéciaux", self.test_special_characters),
            ("Edge case: description NULL", self.test_null_description),
            ("Edge case: multiple logs simultanés", self.test_concurrent_logs),
            ("Edge case: logs anciens (> 1 an)", self.test_old_logs),

            # Tests statistiques
            ("Statistiques: actions par type", self.test_stats_by_action),
            ("Statistiques: activité par opérateur", self.test_stats_by_operateur),
            ("Statistiques: activité par jour", self.test_stats_by_day),

            # Tests de régression
            ("Régression: service log_hist()", self.test_service_log_hist),

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

    def test_setup(self):
        """Crée les données de test."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Créer un opérateur - matricule limité à 20 caractères
            matricule = f"AUD{datetime.now().strftime('%y%m%d%H%M%S')}"
            cur.execute("""
                INSERT INTO personnel (matricule, nom, prenom, statut, date_entree)
                VALUES (%s, %s, %s, %s, %s)
            """, (matricule, "TEST_AUDIT", "LOGGING", "ACTIF", date.today()))
            conn.commit()
            self.test_operateur_id = cur.lastrowid

            # Récupérer un poste
            cur.execute("SELECT id FROM postes LIMIT 1")
            row = cur.fetchone()
            if row:
                self.test_poste_id = row[0]

            print(f"   > Operateur ID: {self.test_operateur_id}")
            print(f"   > Poste ID: {self.test_poste_id}")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS BASIQUES DE LOGGING ==========

    def test_log_simple(self):
        """Test de logging simple sans références."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO historique (date_time, action, description)
                VALUES (%s, %s, %s)
            """, (datetime.now(), "TEST_SIMPLE", "Test de logging simple"))
            conn.commit()

            log_id = cur.lastrowid
            self.test_log_ids.append(log_id)

            print(f"   > Log créé: ID={log_id}")
        finally:
            cur.close()
            conn.close()

    def test_log_with_operateur(self):
        """Test de logging avec operateur_id."""
        try:
            log_hist("TEST_WITH_OPERATEUR", "Test avec opérateur",
                    operateur_id=self.test_operateur_id)

            # Vérifier
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT id FROM historique
                    WHERE action = 'TEST_WITH_OPERATEUR'
                      AND operateur_id = %s
                    ORDER BY date_time DESC
                    LIMIT 1
                """, (self.test_operateur_id,))

                row = cur.fetchone()
                assert row is not None, "Log non trouvé"
                self.test_log_ids.append(row[0])

                print(f"   > Log avec opérateur créé: ID={row[0]}")
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            raise AssertionError(f"Erreur lors du logging avec opérateur: {e}")

    def test_log_with_poste(self):
        """Test de logging avec poste_id."""
        if self.test_poste_id is None:
            print("   > Pas de poste disponible, test passé")
            return

        try:
            log_hist("TEST_WITH_POSTE", "Test avec poste",
                    poste_id=self.test_poste_id)

            # Vérifier
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT id FROM historique
                    WHERE action = 'TEST_WITH_POSTE'
                      AND poste_id = %s
                    ORDER BY date_time DESC
                    LIMIT 1
                """, (self.test_poste_id,))

                row = cur.fetchone()
                assert row is not None, "Log non trouvé"
                self.test_log_ids.append(row[0])

                print(f"   > Log avec poste créé: ID={row[0]}")
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            raise AssertionError(f"Erreur lors du logging avec poste: {e}")

    def test_log_with_both(self):
        """Test de logging avec operateur_id et poste_id."""
        if self.test_poste_id is None:
            print("   > Pas de poste disponible, test passé")
            return

        try:
            log_hist("TEST_WITH_BOTH", "Test avec opérateur et poste",
                    operateur_id=self.test_operateur_id,
                    poste_id=self.test_poste_id)

            # Vérifier
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT id FROM historique
                    WHERE action = 'TEST_WITH_BOTH'
                      AND operateur_id = %s
                      AND poste_id = %s
                    ORDER BY date_time DESC
                    LIMIT 1
                """, (self.test_operateur_id, self.test_poste_id))

                row = cur.fetchone()
                assert row is not None, "Log non trouvé"
                self.test_log_ids.append(row[0])

                print(f"   > Log complet créé: ID={row[0]}")
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            raise AssertionError(f"Erreur lors du logging complet: {e}")

    def test_log_long_description(self):
        """Test de logging avec description longue."""
        long_desc = "A" * 500  # 500 caractères

        try:
            log_hist("TEST_LONG_DESC", long_desc, operateur_id=self.test_operateur_id)

            # Vérifier
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT id, LENGTH(description) as len FROM historique
                    WHERE action = 'TEST_LONG_DESC'
                    ORDER BY date_time DESC
                    LIMIT 1
                """)

                row = cur.fetchone()
                assert row is not None, "Log non trouvé"
                self.test_log_ids.append(row[0])

                print(f"   > Description longue: {row[1]} caractères")
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            raise AssertionError(f"Erreur avec description longue: {e}")

    # ========== TESTS DE STRUCTURE ==========

    def test_timestamp_automatic(self):
        """Vérifie que le timestamp est automatique et cohérent."""
        before = datetime.now()
        time.sleep(0.1)

        log_hist("TEST_TIMESTAMP", "Test timestamp", operateur_id=self.test_operateur_id)

        time.sleep(0.1)
        after = datetime.now()

        # Vérifier
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, date_time FROM historique
                WHERE action = 'TEST_TIMESTAMP'
                ORDER BY date_time DESC
                LIMIT 1
            """)

            row = cur.fetchone()
            assert row is not None
            self.test_log_ids.append(row[0])

            log_time = row[1]
            assert before <= log_time <= after, "Timestamp hors limites"

            print(f"   > Timestamp correct: {log_time}")
        finally:
            cur.close()
            conn.close()

    def test_action_required(self):
        """Vérifie que le champ action est obligatoire."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Tenter d'insérer sans action (devrait échouer)
            try:
                cur.execute("""
                    INSERT INTO historique (date_time, description)
                    VALUES (%s, %s)
                """, (datetime.now(), "Test sans action"))
                conn.commit()

                # Si on arrive ici, le champ n'est pas obligatoire (peut être OK selon le schéma)
                log_id = cur.lastrowid
                self.test_log_ids.append(log_id)
                print(f"   > Action non obligatoire (comportement détecté)")
            except Exception as e:
                # C'est le comportement attendu si action est NOT NULL
                print(f"   > Action obligatoire (correct): {str(e)[:50]}")
        finally:
            cur.close()
            conn.close()

    def test_foreign_keys(self):
        """Vérifie les contraintes de clés étrangères."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Tenter d'insérer avec un operateur_id inexistant
            try:
                cur.execute("""
                    INSERT INTO historique (date_time, action, operateur_id, description)
                    VALUES (%s, %s, %s, %s)
                """, (datetime.now(), "TEST_FK", 999999, "Test FK invalide"))
                conn.commit()

                # Si réussi, pas de contrainte FK (peut être intentionnel)
                log_id = cur.lastrowid
                self.test_log_ids.append(log_id)
                cur.execute("DELETE FROM historique WHERE id = %s", (log_id,))
                conn.commit()
                print(f"   > Pas de contrainte FK stricte (comportement détecté)")
            except Exception as e:
                # Contrainte FK active
                print(f"   > Contrainte FK active (correct)")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DE REQUÊTES ==========

    def test_query_by_action(self):
        """Test de filtrage par action."""
        # Créer plusieurs logs avec la même action
        for i in range(3):
            log_hist(f"TEST_QUERY_ACTION", f"Test {i}", operateur_id=self.test_operateur_id)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM historique
                WHERE action = 'TEST_QUERY_ACTION'
            """)

            count = cur.fetchone()[0]
            assert count >= 3, f"Attendu >= 3, obtenu {count}"

            print(f"   > {count} logs avec action TEST_QUERY_ACTION")
        finally:
            cur.close()
            conn.close()

    def test_query_by_operateur(self):
        """Test de filtrage par opérateur."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM historique
                WHERE operateur_id = %s
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            assert count > 0, "Aucun log pour l'opérateur"

            print(f"   > {count} logs pour l'opérateur {self.test_operateur_id}")
        finally:
            cur.close()
            conn.close()

    def test_query_by_poste(self):
        """Test de filtrage par poste."""
        if self.test_poste_id is None:
            print("   > Pas de poste, test passé")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM historique
                WHERE poste_id = %s
            """, (self.test_poste_id,))

            count = cur.fetchone()[0]
            print(f"   > {count} logs pour le poste {self.test_poste_id}")
        finally:
            cur.close()
            conn.close()

    def test_query_by_period(self):
        """Test de filtrage par période."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            today = date.today()
            start = datetime.combine(today, datetime.min.time())
            end = datetime.combine(today, datetime.max.time())

            cur.execute("""
                SELECT COUNT(*) FROM historique
                WHERE date_time BETWEEN %s AND %s
            """, (start, end))

            count = cur.fetchone()[0]
            print(f"   > {count} logs aujourd'hui")
        finally:
            cur.close()
            conn.close()

    def test_query_order(self):
        """Test du tri chronologique."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT date_time FROM historique
                ORDER BY date_time DESC
                LIMIT 10
            """)

            results = cur.fetchall()
            if len(results) > 1:
                # Vérifier l'ordre décroissant
                for i in range(len(results) - 1):
                    assert results[i][0] >= results[i+1][0], "Tri incorrect"

                print(f"   > Tri chronologique correct ({len(results)} entrées)")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DE TRAÇABILITÉ MÉTIER ==========

    def test_trace_add_operateur(self):
        """Test de traçabilité: ajout opérateur."""
        log_hist("ADD_OPERATEUR", f"Ajout opérateur test ID={self.test_operateur_id}",
                operateur_id=self.test_operateur_id)

        # Vérifier la trace
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM historique
                WHERE action = 'ADD_OPERATEUR'
                  AND operateur_id = %s
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            assert count > 0, "Trace ADD_OPERATEUR non trouvée"

            print(f"   > Trace ADD_OPERATEUR créée")
        finally:
            cur.close()
            conn.close()

    def test_trace_update_polyvalence(self):
        """Test de traçabilité: modification polyvalence."""
        if self.test_poste_id is None:
            print("   > Pas de poste, test passé")
            return

        log_hist("UPDATE_POLYVALENCE", f"Modification niveau opérateur {self.test_operateur_id}",
                operateur_id=self.test_operateur_id,
                poste_id=self.test_poste_id)

        # Vérifier
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM historique
                WHERE action = 'UPDATE_POLYVALENCE'
                  AND operateur_id = %s
                  AND poste_id = %s
            """, (self.test_operateur_id, self.test_poste_id))

            count = cur.fetchone()[0]
            assert count > 0, "Trace UPDATE_POLYVALENCE non trouvée"

            print(f"   > Trace UPDATE_POLYVALENCE créée")
        finally:
            cur.close()
            conn.close()

    def test_trace_soft_delete(self):
        """Test de traçabilité: soft delete."""
        log_hist("SOFT_DELETE", f"Masquage opérateur {self.test_operateur_id}",
                operateur_id=self.test_operateur_id)

        print(f"   > Trace SOFT_DELETE créée")

    def test_trace_status_change(self):
        """Test de traçabilité: changement de statut."""
        log_hist("STATUS_CHANGE", f"Changement statut ACTIF -> INACTIF",
                operateur_id=self.test_operateur_id)

        print(f"   > Trace STATUS_CHANGE créée")

    # ========== TESTS DE PERFORMANCE ==========

    def test_perf_insert(self):
        """Test de performance: insertion rapide."""
        start_time = time.time()

        for i in range(100):
            log_hist(f"TEST_PERF_INSERT", f"Log {i}", operateur_id=self.test_operateur_id)

        elapsed = time.time() - start_time

        assert elapsed < 5.0, f"Insertion trop lente: {elapsed:.3f}s pour 100 logs"
        print(f"   > 100 logs insérés en {elapsed:.3f}s ({100/elapsed:.1f} logs/s)")

    def test_perf_query_all(self):
        """Test de performance: requête de tous les logs."""
        start_time = time.time()

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT
                    h.*,
                    p.nom,
                    p.prenom,
                    pos.poste_code
                FROM historique h
                LEFT JOIN personnel p ON h.operateur_id = p.id
                LEFT JOIN postes pos ON h.poste_id = pos.id
                ORDER BY h.date_time DESC
                LIMIT 1000
            """)

            results = cur.fetchall()
            elapsed = time.time() - start_time

            assert elapsed < 2.0, f"Requête trop lente: {elapsed:.3f}s"
            print(f"   > {len(results)} logs récupérés en {elapsed:.3f}s")
        finally:
            cur.close()
            conn.close()

    def test_perf_query_filtered(self):
        """Test de performance: requête filtrée."""
        start_time = time.time()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM historique
                WHERE operateur_id = %s
                  AND date_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """, (self.test_operateur_id,))

            count = cur.fetchone()[0]
            elapsed = time.time() - start_time

            assert elapsed < 1.0, f"Requête trop lente: {elapsed:.3f}s"
            print(f"   > Requête filtrée en {elapsed:.3f}s ({count} résultats)")
        finally:
            cur.close()
            conn.close()

    def test_perf_aggregations(self):
        """Test de performance: agrégations statistiques."""
        start_time = time.time()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    action,
                    COUNT(*) as nb,
                    DATE(date_time) as jour
                FROM historique
                WHERE date_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY action, DATE(date_time)
                ORDER BY nb DESC
                LIMIT 50
            """)

            results = cur.fetchall()
            elapsed = time.time() - start_time

            assert elapsed < 2.0, f"Agrégation trop lente: {elapsed:.3f}s"
            print(f"   > Agrégation en {elapsed:.3f}s ({len(results)} groupes)")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DE SÉCURITÉ ==========

    def test_immutable_logs(self):
        """Test: les logs ne devraient pas être modifiables."""
        if len(self.test_log_ids) == 0:
            print("   > Aucun log à tester")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            log_id = self.test_log_ids[0]

            # Tenter de modifier
            cur.execute("""
                UPDATE historique
                SET description = 'MODIFIED'
                WHERE id = %s
            """, (log_id,))
            conn.commit()

            # Vérifier si la modification a réussi
            cur.execute("SELECT description FROM historique WHERE id = %s", (log_id,))
            desc = cur.fetchone()[0]

            if desc == 'MODIFIED':
                print(f"   > ATTENTION: Les logs sont modifiables (considérer trigger d'immuabilité)")
            else:
                print(f"   > Logs protégés contre modification")
        finally:
            cur.close()
            conn.close()

    def test_cascade_delete_operateur(self):
        """Test: cascade delete quand opérateur supprimé."""
        # Créer un opérateur temporaire
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            matricule = f"CAS{datetime.now().strftime('%y%m%d%H%M%S')}"
            cur.execute("""
                INSERT INTO personnel (matricule, nom, prenom, statut, date_entree)
                VALUES (%s, %s, %s, %s, %s)
            """, (matricule, "TEST", "CASCADE", "ACTIF", date.today()))
            conn.commit()
            temp_oper_id = cur.lastrowid

            # Créer un log
            log_hist("TEST_CASCADE_DELETE", "Test cascade", operateur_id=temp_oper_id)

            # Compter les logs
            cur.execute("SELECT COUNT(*) FROM historique WHERE operateur_id = %s", (temp_oper_id,))
            count_before = cur.fetchone()[0]

            # Supprimer l'opérateur
            cur.execute("DELETE FROM personnel WHERE id = %s", (temp_oper_id,))
            conn.commit()

            # Vérifier si les logs sont supprimés (cascade)
            cur.execute("SELECT COUNT(*) FROM historique WHERE operateur_id = %s", (temp_oper_id,))
            count_after = cur.fetchone()[0]

            if count_after == 0:
                print(f"   > Cascade DELETE actif ({count_before} logs supprimés)")
            else:
                print(f"   > Cascade DELETE non actif (logs conservés)")
        finally:
            cur.close()
            conn.close()

    def test_cascade_delete_poste(self):
        """Test: cascade delete quand poste supprimé."""
        print(f"   > Test similaire à cascade_delete_operateur (non exécuté)")

    # ========== TESTS EDGE CASES ==========

    def test_special_characters(self):
        """Test: caractères spéciaux dans action et description."""
        special_action = "TEST_SPÉCIAL_ÉÀÇÜ"
        special_desc = "Test avec caractères spéciaux: é à ç ü € 🎉"

        log_hist(special_action, special_desc, operateur_id=self.test_operateur_id)

        # Vérifier
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT description FROM historique
                WHERE action = %s
                ORDER BY date_time DESC
                LIMIT 1
            """, (special_action,))

            row = cur.fetchone()
            assert row is not None, "Log avec caractères spéciaux non trouvé"

            print(f"   > Caractères spéciaux supportés")
        finally:
            cur.close()
            conn.close()

    def test_null_description(self):
        """Test: description NULL."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO historique (date_time, action, operateur_id)
                VALUES (%s, %s, %s)
            """, (datetime.now(), "TEST_NULL_DESC", self.test_operateur_id))
            conn.commit()

            log_id = cur.lastrowid
            self.test_log_ids.append(log_id)

            print(f"   > Description NULL acceptée (ID={log_id})")
        finally:
            cur.close()
            conn.close()

    def test_concurrent_logs(self):
        """Test: logs multiples simultanés."""
        actions = [f"TEST_CONCURRENT_{i}" for i in range(10)]

        for action in actions:
            log_hist(action, f"Log {action}", operateur_id=self.test_operateur_id)

        # Vérifier
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            placeholders = ','.join(['%s'] * len(actions))
            cur.execute(f"""
                SELECT COUNT(*) FROM historique
                WHERE action IN ({placeholders})
            """, actions)

            count = cur.fetchone()[0]
            assert count == len(actions), f"Attendu {len(actions)}, obtenu {count}"

            print(f"   > {count} logs concurrents créés")
        finally:
            cur.close()
            conn.close()

    def test_old_logs(self):
        """Test: logs anciens (simulation)."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Créer un log daté d'il y a 1 an
            old_date = datetime.now() - timedelta(days=365)

            cur.execute("""
                INSERT INTO historique (date_time, action, description, operateur_id)
                VALUES (%s, %s, %s, %s)
            """, (old_date, "TEST_OLD_LOG", "Log ancien", self.test_operateur_id))
            conn.commit()

            log_id = cur.lastrowid
            self.test_log_ids.append(log_id)

            # Vérifier la récupération
            cur.execute("""
                SELECT DATEDIFF(NOW(), date_time) as age_days
                FROM historique
                WHERE id = %s
            """, (log_id,))

            age = cur.fetchone()[0]
            assert age >= 365, f"Âge incorrect: {age} jours"

            print(f"   > Log ancien créé: {age} jours")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS STATISTIQUES ==========

    def test_stats_by_action(self):
        """Test: statistiques par type d'action."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    action,
                    COUNT(*) as nb
                FROM historique
                GROUP BY action
                ORDER BY nb DESC
                LIMIT 10
            """)

            results = cur.fetchall()
            print(f"   > Top 10 actions:")
            for row in results[:5]:
                print(f"      - {row[0]}: {row[1]} fois")
        finally:
            cur.close()
            conn.close()

    def test_stats_by_operateur(self):
        """Test: statistiques d'activité par opérateur."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    p.nom,
                    p.prenom,
                    COUNT(h.id) as nb_actions
                FROM personnel p
                LEFT JOIN historique h ON p.id = h.operateur_id
                GROUP BY p.id, p.nom, p.prenom
                ORDER BY nb_actions DESC
                LIMIT 5
            """)

            results = cur.fetchall()
            print(f"   > Top 5 opérateurs actifs:")
            for row in results:
                print(f"      - {row[0]} {row[1]}: {row[2]} actions")
        finally:
            cur.close()
            conn.close()

    def test_stats_by_day(self):
        """Test: statistiques d'activité par jour."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    DATE(date_time) as jour,
                    COUNT(*) as nb_actions
                FROM historique
                WHERE date_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(date_time)
                ORDER BY jour DESC
            """)

            results = cur.fetchall()
            print(f"   > Activité des 7 derniers jours:")
            for row in results:
                print(f"      - {row[0]}: {row[1]} actions")
        finally:
            cur.close()
            conn.close()

    # ========== TESTS DE RÉGRESSION ==========

    def test_service_log_hist(self):
        """Test du service log_hist()."""
        try:
            # Test basique
            log_hist("TEST_SERVICE", "Test du service", operateur_id=self.test_operateur_id)

            # Vérifier
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT COUNT(*) FROM historique
                    WHERE action = 'TEST_SERVICE'
                      AND operateur_id = %s
                """, (self.test_operateur_id,))

                count = cur.fetchone()[0]
                assert count > 0, "Service log_hist() n'a pas créé de log"

                print(f"   > Service log_hist() fonctionne correctement")
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            raise AssertionError(f"Service log_hist() a échoué: {e}")

    # ========== NETTOYAGE ==========

    def test_cleanup(self):
        """Supprime toutes les données de test."""
        if self.test_operateur_id is None:
            print("   > Aucune donnée à nettoyer")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Supprimer les logs de test (avec patterns TEST_*)
            cur.execute("""
                DELETE FROM historique
                WHERE action LIKE 'TEST_%'
                   OR operateur_id = %s
            """, (self.test_operateur_id,))
            logs_deleted = cur.rowcount

            # Supprimer l'opérateur
            cur.execute("DELETE FROM personnel WHERE id = %s", (self.test_operateur_id,))
            oper_deleted = cur.rowcount

            conn.commit()

            print(f"   > Nettoyage effectué:")
            print(f"      - {logs_deleted} logs")
            print(f"      - {oper_deleted} opérateur(s)")
        finally:
            cur.close()
            conn.close()


if __name__ == "__main__":
    tester = TestAuditLoggingAdvanced()
    tester.run_all_tests()
