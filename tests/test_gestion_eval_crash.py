# Test de diagnostic pour le crash de gestion_evaluation
# -*- coding: utf-8 -*-

import sys
import traceback
from PyQt5.QtWidgets import QApplication

def test_gestion_evaluation():
    """Test complet du module gestion_evaluation"""

    print("=" * 60)
    print("TEST GESTION ÉVALUATION - DIAGNOSTIC CRASH")
    print("=" * 60)

    # Test 1: Import du module
    print("\n[1/4] Test d'import du module...")
    try:
        sys.path.insert(0, 'App')
        from core.gui.gestion_evaluation import GestionEvaluationDialog
        print("[OK] Import reussi")
    except Exception as e:
        print(f"[ERREUR] Erreur d'import: {e}")
        traceback.print_exc()
        return

    # Test 2: Création QApplication
    print("\n[2/4] Test de creation QApplication...")
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        print("[OK] QApplication creee")
    except Exception as e:
        print(f"[ERREUR] Erreur QApplication: {e}")
        traceback.print_exc()
        return

    # Test 3: Création du dialogue (sans load_data automatique)
    print("\n[3/4] Test de creation du dialogue...")
    try:
        # Temporairement désactiver load_data dans __init__
        dialog = GestionEvaluationDialog()
        print("[OK] Dialogue cree")
        print(f"   - Titre: {dialog.windowTitle()}")
        print(f"   - Taille: {dialog.width()}x{dialog.height()}")
    except Exception as e:
        print(f"[ERREUR] Erreur de creation du dialogue: {e}")
        traceback.print_exc()
        return

    # Test 4: Test de load_data (c'est ici que ça crashe probablement)
    print("\n[4/4] Test de chargement des donnees (load_data)...")
    try:
        # Bloquer les signaux pour éviter les effets de bord
        dialog.table.blockSignals(True)
        dialog.load_data()
        dialog.table.blockSignals(False)

        print("[OK] Donnees chargees avec succes")
        print(f"   - Nombre d'evaluations: {len(dialog.all_evaluations)}")
        print(f"   - Lignes dans le tableau: {dialog.table.rowCount()}")

        # Afficher quelques détails
        if dialog.all_evaluations:
            print("\n   Exemple d'evaluation:")
            exemple = dialog.all_evaluations[0]
            print(f"      - Nom: {exemple.get('nom')} {exemple.get('prenom')}")
            print(f"      - Matricule: {exemple.get('matricule')}")
            print(f"      - Total polyvalences: {exemple.get('total')}")
            print(f"      - En retard: {exemple.get('retard')}")
            print(f"      - A planifier: {exemple.get('a_planifier')}")
            print(f"      - Statut: {exemple.get('statut')}")

    except Exception as e:
        print(f"[ERREUR] ERREUR lors du chargement des donnees:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {e}")
        print("\n   Stack trace complete:")
        traceback.print_exc()

        # Tenter de diagnostiquer plus précisément
        print("\n   Diagnostic supplementaire:")
        try:
            from core.db.configbd import get_connection as get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"      - Connexion DB: [OK] (MySQL {version[0]})")
            cursor.close()
            conn.close()
        except Exception as db_error:
            print(f"      - Connexion DB: [ERREUR] {db_error}")

        return

    print("\n" + "=" * 60)
    print("[OK] TOUS LES TESTS SONT PASSES")
    print("=" * 60)
    print("\nConclusion: Le module fonctionne correctement.")
    print("Si le crash persiste dans l'application, verifier:")
    print("  1. Les permissions de la base de donnees")
    print("  2. Les donnees dans la table 'personnel' et 'polyvalence'")
    print("  3. L'integration dans main_qt.py")

if __name__ == "__main__":
    test_gestion_evaluation()
