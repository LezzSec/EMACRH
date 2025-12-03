# -*- coding: utf-8 -*-
"""
Script de test pour le système d'historique de polyvalence
Ajoute des données de test pour vérifier le fonctionnement
"""

from core.services.polyvalence_logger import (
    log_polyvalence_ajout,
    log_polyvalence_modification,
    log_polyvalence_suppression,
    log_polyvalence_action,
    get_historique_operateur,
    get_statistiques_operateur
)
from core.db.configbd import get_connection
from datetime import datetime, date, timedelta


def get_first_operateur_and_poste():
    """Récupère le premier opérateur et premier poste pour les tests."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Récupérer premier opérateur
    cur.execute("SELECT id, nom, prenom FROM personnel LIMIT 1")
    operateur = cur.fetchone()

    # Récupérer premier poste
    cur.execute("SELECT id, poste_code FROM postes WHERE visible = 1 LIMIT 1")
    poste = cur.fetchone()

    cur.close()
    conn.close()

    return operateur, poste


def test_ajout_historique():
    """Teste l'ajout d'actions dans l'historique."""
    print("=" * 70)
    print("Test du système d'historique de polyvalence")
    print("=" * 70)

    # Récupérer un opérateur et un poste pour les tests
    operateur, poste = get_first_operateur_and_poste()

    if not operateur or not poste:
        print("[ERREUR] Aucun opérateur ou poste trouvé dans la base de données")
        return False

    operateur_id = operateur['id']
    poste_id = poste['id']

    print(f"\n[INFO] Opérateur de test : {operateur['prenom']} {operateur['nom']} (ID: {operateur_id})")
    print(f"[INFO] Poste de test : {poste['poste_code']} (ID: {poste_id})")

    # Test 1: Import manuel d'une ancienne action (2020)
    print("\n[TEST 1] Import manuel d'une action de 2020...")
    try:
        date_action_2020 = datetime(2020, 3, 15, 10, 30, 0)
        hist_id = log_polyvalence_action(
            action_type='IMPORT_MANUEL',
            operateur_id=operateur_id,
            poste_id=poste_id,
            polyvalence_id=None,
            nouveau_niveau=2,
            nouvelle_date_evaluation=date(2020, 3, 15),
            nouvelle_prochaine_evaluation=date(2030, 3, 15),
            utilisateur="Test Script",
            commentaire="Import de données historiques - Formation initiale niveau 2",
            source="IMPORT_MANUEL",
            import_batch_id="TEST_BATCH_001",
            date_action=date_action_2020
        )
        print(f"[OK] Import manuel enregistré (ID: {hist_id})")
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

    # Test 2: Import manuel d'une modification (2021)
    print("\n[TEST 2] Import manuel d'une modification de 2021...")
    try:
        date_action_2021 = datetime(2021, 6, 20, 14, 0, 0)
        hist_id = log_polyvalence_action(
            action_type='IMPORT_MANUEL',
            operateur_id=operateur_id,
            poste_id=poste_id,
            polyvalence_id=None,
            ancien_niveau=2,
            ancienne_date_evaluation=date(2020, 3, 15),
            nouveau_niveau=3,
            nouvelle_date_evaluation=date(2021, 6, 20),
            nouvelle_prochaine_evaluation=date(2031, 6, 20),
            utilisateur="Test Script",
            commentaire="Montée en compétence - Passage niveau 3",
            source="IMPORT_MANUEL",
            import_batch_id="TEST_BATCH_001",
            date_action=date_action_2021
        )
        print(f"[OK] Modification importée (ID: {hist_id})")
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

    # Test 3: Import manuel d'une autre action (2023)
    print("\n[TEST 3] Import manuel d'une action récente de 2023...")
    try:
        date_action_2023 = datetime(2023, 11, 10, 9, 15, 0)
        hist_id = log_polyvalence_action(
            action_type='IMPORT_MANUEL',
            operateur_id=operateur_id,
            poste_id=poste_id,
            polyvalence_id=None,
            ancien_niveau=3,
            ancienne_date_evaluation=date(2021, 6, 20),
            nouveau_niveau=4,
            nouvelle_date_evaluation=date(2023, 11, 10),
            nouvelle_prochaine_evaluation=date(2033, 11, 10),
            utilisateur="Test Script",
            commentaire="Promotion niveau 4 - Référent du poste",
            source="IMPORT_MANUEL",
            import_batch_id="TEST_BATCH_002",
            date_action=date_action_2023
        )
        print(f"[OK] Action récente importée (ID: {hist_id})")
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

    # Test 4: Ajout d'une action actuelle (simulation)
    print("\n[TEST 4] Simulation d'un ajout actuel (sans polyvalence_id)...")
    try:
        # Simuler un ajout via l'application
        # Note: polyvalence_id=None car c'est un test (pas de vraie polyvalence créée)
        hist_id = log_polyvalence_ajout(
            operateur_id=operateur_id,
            poste_id=poste_id,
            polyvalence_id=None,  # None pour import/test
            niveau=1,
            date_evaluation=date.today(),
            prochaine_evaluation=date.today() + timedelta(days=3650),  # +10 ans
            utilisateur="Test GUI",
            source="GUI_TEST"
        )
        print(f"[OK] Ajout actuel simulé (ID: {hist_id})")
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

    # Test 5: Afficher l'historique complet
    print("\n[TEST 5] Récupération de l'historique...")
    try:
        historique = get_historique_operateur(operateur_id)
        print(f"[OK] {len(historique)} action(s) trouvée(s) pour cet opérateur")

        if historique:
            print("\nDétail des actions :")
            print("-" * 70)
            for action in historique[:5]:  # Afficher les 5 premières
                print(f"  • {action['date_action']} - {action['action_type']} - N{action.get('nouveau_niveau', '?')}")
                print(f"    Poste: {action.get('poste_code', 'Inconnu')}")
                if action.get('commentaire'):
                    print(f"    Commentaire: {action['commentaire'][:60]}...")
                print()
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

    # Test 6: Statistiques
    print("\n[TEST 6] Statistiques de l'opérateur...")
    try:
        stats = get_statistiques_operateur(operateur_id)
        print(f"[OK] Statistiques récupérées :")
        print(f"  • Total d'actions : {stats['total_actions']}")
        print(f"  • Ajouts : {stats['nb_ajouts']}")
        print(f"  • Modifications : {stats['nb_modifications']}")
        print(f"  • Suppressions : {stats['nb_suppressions']}")
        print(f"  • Imports manuels : {stats['nb_imports']}")
        print(f"  • Postes touchés : {stats['nb_postes_touches']}")
        if stats['premiere_action']:
            print(f"  • Première action : {stats['premiere_action']}")
        if stats['derniere_action']:
            print(f"  • Dernière action : {stats['derniere_action']}")
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

    print("\n" + "=" * 70)
    print("[OK] Tous les tests sont passés avec succès !")
    print("=" * 70)
    print("\n💡 Vous pouvez maintenant :")
    print("  1. Ouvrir l'application EMAC")
    print(f"  2. Aller dans 'Gestion du Personnel' et sélectionner {operateur['prenom']} {operateur['nom']}")
    print("  3. Cliquer sur l'onglet 'Historique'")
    print("  4. Vous devriez voir les actions de test affichées")
    print("  5. Cliquer sur le bouton '📥 Import manuel' pour ajouter d'autres données")

    return True


if __name__ == "__main__":
    import sys
    success = test_ajout_historique()
    sys.exit(0 if success else 1)
