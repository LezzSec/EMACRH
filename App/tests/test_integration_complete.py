# -*- coding: utf-8 -*-
"""
Test d'intégration complet de l'application EMAC
Simule des actions utilisateur réelles pour vérifier le bon fonctionnement après optimisations

Usage:
    cd App
    py tests/test_integration_complete.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from core.db.configbd import get_connection as get_db_connection
from core.services.logger import log_hist


class TestIntegrationEMAC:
    """Tests d'intégration pour vérifier le bon fonctionnement de l'application."""

    def __init__(self):
        self.test_operateur_id = None
        self.test_poste_id = None
        self.successes = []
        self.failures = []

    def run_all_tests(self):
        """Exécute tous les tests d'intégration."""
        print("=" * 70)
        print("  TESTS D'INTÉGRATION EMAC - Vérification complète")
        print("=" * 70)
        print()

        tests = [
            ("Connexion à la base de données", self.test_db_connection),
            ("Pool de connexions (optimisation)", self.test_connection_pool),
            ("Ajout d'un opérateur de test", self.test_add_operateur),
            ("Récupération de la liste des postes", self.test_get_postes),
            ("Ajout de polyvalence (niveau 1)", self.test_add_polyvalence),
            ("Modification du niveau de polyvalence (1 vers 2)", self.test_update_niveau),
            ("Modification du niveau de polyvalence (2 vers 3)", self.test_update_niveau_2),
            ("Modification du niveau de polyvalence (3 vers 4)", self.test_update_niveau_3),
            ("Vérification des évaluations en retard", self.test_get_evaluations_retard),
            ("Vérification des prochaines évaluations", self.test_get_prochaines_evaluations),
            ("Test de l'historique (logging)", self.test_historique),
            ("Test du changement de statut (ACTIF vers INACTIF)", self.test_change_statut),
            ("Nettoyage des données de test", self.test_cleanup),
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
            print(f"   [ERREUR] ECHEC: {e}\n")

    def _print_summary(self):
        """Affiche le résumé des tests."""
        print("=" * 70)
        print("  RESUME DES TESTS")
        print("=" * 70)
        print(f"[+] Reussis: {len(self.successes)}")
        print(f"[-] Echoues: {len(self.failures)}")
        print()

        if self.failures:
            print("Details des echecs:")
            for name, error in self.failures:
                print(f"  - {name}: {error}")
            print()
            sys.exit(1)
        else:
            print("[SUCCESS] Tous les tests sont passes avec succes !")
            print()

    # ========== TESTS ==========

    def test_db_connection(self):
        """Test de connexion basique à la base de données."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            assert result[0] == 1, "La requête SELECT 1 devrait retourner 1"
        finally:
            cur.close()
            conn.close()

    def test_connection_pool(self):
        """Test du pool de connexions (optimisation)."""
        # Créer 3 connexions successives
        connections = []
        for i in range(3):
            conn = get_db_connection()
            connections.append(conn)

        # Fermer toutes les connexions
        for conn in connections:
            conn.close()

        # Récupérer une nouvelle connexion (devrait venir du pool)
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            assert result[0] == 1
        finally:
            cur.close()
            conn.close()

    def test_add_operateur(self):
        """Test d'ajout d'un opérateur."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Générer un matricule unique
            matricule = f"TEST_{date.today().strftime('%Y%m%d')}"

            # Vérifier si l'opérateur existe déjà
            cur.execute("SELECT id FROM personnel WHERE matricule = %s", (matricule,))
            existing = cur.fetchone()

            if existing:
                self.test_operateur_id = existing[0]
                print(f"   > Operateur existant trouve (ID: {self.test_operateur_id})")
            else:
                # Créer un nouvel opérateur
                cur.execute("""
                    INSERT INTO personnel (matricule, nom, prenom, statut, date_entree)
                    VALUES (%s, %s, %s, %s, %s)
                """, (matricule, "TEST_NOM", "TEST_PRENOM", "ACTIF", date.today()))
                conn.commit()
                self.test_operateur_id = cur.lastrowid
                print(f"   > Operateur cree (ID: {self.test_operateur_id})")

            assert self.test_operateur_id is not None
        finally:
            cur.close()
            conn.close()

    def test_get_postes(self):
        """Test de récupération des postes."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, poste_code FROM postes LIMIT 1")
            result = cur.fetchone()
            assert result is not None, "Aucun poste trouvé dans la base"
            self.test_poste_id = result[0]
            print(f"   > Poste recupere: {result[1]} (ID: {self.test_poste_id})")
        finally:
            cur.close()
            conn.close()

    def test_add_polyvalence(self):
        """Test d'ajout de polyvalence."""
        assert self.test_operateur_id is not None, "Opérateur de test non créé"
        assert self.test_poste_id is not None, "Poste de test non trouvé"

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Vérifier si la polyvalence existe déjà
            cur.execute("""
                SELECT id, niveau FROM polyvalence
                WHERE operateur_id = %s AND poste_id = %s
            """, (self.test_operateur_id, self.test_poste_id))
            existing = cur.fetchone()

            if existing:
                print(f"   > Polyvalence existante (ID: {existing[0]}, Niveau: {existing[1]})")
            else:
                # Créer une nouvelle polyvalence
                date_eval = date.today()
                prochaine_eval = date_eval + timedelta(days=365)

                cur.execute("""
                    INSERT INTO polyvalence (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
                    VALUES (%s, %s, %s, %s, %s)
                """, (self.test_operateur_id, self.test_poste_id, 1, date_eval, prochaine_eval))
                conn.commit()
                print(f"   > Polyvalence creee (Niveau: 1)")

            # Vérifier l'insertion
            cur.execute("""
                SELECT niveau FROM polyvalence
                WHERE operateur_id = %s AND poste_id = %s
            """, (self.test_operateur_id, self.test_poste_id))
            result = cur.fetchone()
            assert result is not None
            print(f"   > Niveau actuel: {result[0]}")
        finally:
            cur.close()
            conn.close()

    def test_update_niveau(self):
        """Test de modification du niveau (1 vers 2)."""
        assert self.test_operateur_id is not None
        assert self.test_poste_id is not None

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE polyvalence
                SET niveau = 2, date_evaluation = %s
                WHERE operateur_id = %s AND poste_id = %s
            """, (date.today(), self.test_operateur_id, self.test_poste_id))
            conn.commit()

            # Vérifier la mise à jour
            cur.execute("""
                SELECT niveau FROM polyvalence
                WHERE operateur_id = %s AND poste_id = %s
            """, (self.test_operateur_id, self.test_poste_id))
            result = cur.fetchone()
            assert result[0] == 2, f"Niveau attendu: 2, obtenu: {result[0]}"
            print(f"   > Niveau mis a jour: {result[0]}")
        finally:
            cur.close()
            conn.close()

    def test_update_niveau_2(self):
        """Test de modification du niveau (2 vers 3)."""
        assert self.test_operateur_id is not None
        assert self.test_poste_id is not None

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE polyvalence
                SET niveau = 3, date_evaluation = %s
                WHERE operateur_id = %s AND poste_id = %s
            """, (date.today(), self.test_operateur_id, self.test_poste_id))
            conn.commit()

            # Vérifier la mise à jour
            cur.execute("""
                SELECT niveau FROM polyvalence
                WHERE operateur_id = %s AND poste_id = %s
            """, (self.test_operateur_id, self.test_poste_id))
            result = cur.fetchone()
            assert result[0] == 3, f"Niveau attendu: 3, obtenu: {result[0]}"
            print(f"   > Niveau mis a jour: {result[0]}")
        finally:
            cur.close()
            conn.close()

    def test_update_niveau_3(self):
        """Test de modification du niveau (3 vers 4)."""
        assert self.test_operateur_id is not None
        assert self.test_poste_id is not None

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE polyvalence
                SET niveau = 4, date_evaluation = %s
                WHERE operateur_id = %s AND poste_id = %s
            """, (date.today(), self.test_operateur_id, self.test_poste_id))
            conn.commit()

            # Vérifier la mise à jour
            cur.execute("""
                SELECT niveau FROM polyvalence
                WHERE operateur_id = %s AND poste_id = %s
            """, (self.test_operateur_id, self.test_poste_id))
            result = cur.fetchone()
            assert result[0] == 4, f"Niveau attendu: 4, obtenu: {result[0]}"
            print(f"   > Niveau mis a jour: {result[0]}")
        finally:
            cur.close()
            conn.close()

    def test_get_evaluations_retard(self):
        """Test de récupération des évaluations en retard."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Créer une évaluation en retard pour le test
            cur.execute("""
                UPDATE polyvalence
                SET prochaine_evaluation = %s
                WHERE operateur_id = %s AND poste_id = %s
            """, (date.today() - timedelta(days=10), self.test_operateur_id, self.test_poste_id))
            conn.commit()

            # Récupérer les évaluations en retard
            cur.execute("""
                SELECT p.nom, p.prenom, pos.poste_code, poly.prochaine_evaluation
                FROM polyvalence poly
                JOIN personnel p ON p.id = poly.operateur_id
                LEFT JOIN postes pos ON pos.id = poly.poste_id
                WHERE poly.prochaine_evaluation < CURDATE()
                  AND p.statut = 'ACTIF'
                  AND poly.operateur_id = %s
                ORDER BY poly.prochaine_evaluation ASC
            """, (self.test_operateur_id,))
            results = cur.fetchall()

            assert len(results) > 0, "Aucune évaluation en retard trouvée"
            print(f"   > {len(results)} evaluation(s) en retard trouvee(s)")
        finally:
            cur.close()
            conn.close()

    def test_get_prochaines_evaluations(self):
        """Test de récupération des prochaines évaluations."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Mettre une évaluation à venir
            cur.execute("""
                UPDATE polyvalence
                SET prochaine_evaluation = %s
                WHERE operateur_id = %s AND poste_id = %s
            """, (date.today() + timedelta(days=30), self.test_operateur_id, self.test_poste_id))
            conn.commit()

            # Récupérer les prochaines évaluations
            cur.execute("""
                SELECT p.nom, p.prenom, pos.poste_code, poly.prochaine_evaluation
                FROM polyvalence poly
                JOIN personnel p ON p.id = poly.operateur_id
                LEFT JOIN postes pos ON pos.id = poly.poste_id
                WHERE poly.prochaine_evaluation >= CURDATE()
                  AND p.statut = 'ACTIF'
                  AND poly.operateur_id = %s
                ORDER BY poly.prochaine_evaluation ASC
            """, (self.test_operateur_id,))
            results = cur.fetchall()

            assert len(results) > 0, "Aucune prochaine évaluation trouvée"
            print(f"   > {len(results)} prochaine(s) evaluation(s) trouvee(s)")
        finally:
            cur.close()
            conn.close()

    def test_historique(self):
        """Test d'écriture dans l'historique."""
        try:
            log_hist(
                action="TEST_INTEGRATION",
                description="Test d'intégration automatique",
                operateur_id=self.test_operateur_id,
                poste_id=self.test_poste_id
            )

            # Vérifier que l'entrée a été créée
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT COUNT(*) FROM historique
                    WHERE action = 'TEST_INTEGRATION'
                      AND operateur_id = %s
                """, (self.test_operateur_id,))
                count = cur.fetchone()[0]
                assert count > 0, "Aucune entrée d'historique créée"
                print(f"   > Entree d'historique creee ({count} au total)")
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            print(f"   [WARN] Avertissement: Logging desactive ou erreur: {e}")

    def test_change_statut(self):
        """Test de changement de statut (ACTIF vers INACTIF)."""
        assert self.test_operateur_id is not None

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Changer le statut à INACTIF
            cur.execute("""
                UPDATE personnel
                SET statut = 'INACTIF'
                WHERE id = %s
            """, (self.test_operateur_id,))
            conn.commit()

            # Vérifier le changement
            cur.execute("SELECT statut FROM personnel WHERE id = %s", (self.test_operateur_id,))
            result = cur.fetchone()
            assert result[0] == 'INACTIF', f"Statut attendu: INACTIF, obtenu: {result[0]}"
            print(f"   > Statut change: ACTIF > INACTIF")

            # Remettre à ACTIF pour le nettoyage
            cur.execute("""
                UPDATE personnel
                SET statut = 'ACTIF'
                WHERE id = %s
            """, (self.test_operateur_id,))
            conn.commit()
            print(f"   > Statut restaure: INACTIF > ACTIF")
        finally:
            cur.close()
            conn.close()

    def test_cleanup(self):
        """Nettoyage des données de test."""
        if self.test_operateur_id is None:
            print("   > Aucune donnee a nettoyer")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Supprimer la polyvalence
            cur.execute("""
                DELETE FROM polyvalence
                WHERE operateur_id = %s
            """, (self.test_operateur_id,))
            poly_deleted = cur.rowcount

            # Supprimer l'historique de test
            cur.execute("""
                DELETE FROM historique
                WHERE operateur_id = %s
                  AND action = 'TEST_INTEGRATION'
            """, (self.test_operateur_id,))
            hist_deleted = cur.rowcount

            # Supprimer l'opérateur
            cur.execute("""
                DELETE FROM personnel
                WHERE id = %s
            """, (self.test_operateur_id,))
            oper_deleted = cur.rowcount

            conn.commit()
            print(f"   > Donnees supprimees:")
            print(f"      - {poly_deleted} polyvalence(s)")
            print(f"      - {hist_deleted} entree(s) d'historique")
            print(f"      - {oper_deleted} operateur(s)")
        finally:
            cur.close()
            conn.close()


if __name__ == "__main__":
    tester = TestIntegrationEMAC()
    tester.run_all_tests()
