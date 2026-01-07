# -*- coding: utf-8 -*-
"""
Script de test pour diagnostiquer le crash de gestion_evaluation
"""

import sys
import traceback
import os

# Ajouter le chemin App au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'App'))

print("="*60)
print("TEST GESTION EVALUATION - DIAGNOSTIC")
print("="*60)
print()

# Test 1: Import des modules
print("[1/5] Test des imports de base...")
try:
    from PyQt5.QtWidgets import QApplication, QDialog
    from PyQt5.QtCore import QDate, Qt
    from PyQt5.QtGui import QColor, QFont
    print("[OK] PyQt5 OK")
except Exception as e:
    print(f"[ERREUR] PyQt5: {e}")
    sys.exit(1)

# Test 2: Import ReportLab
print("[2/5] Test ReportLab...")
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    print("[OK] ReportLab OK")
except Exception as e:
    print(f"[ERREUR] ERREUR ReportLab: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Import du module DB
print("[3/5] Test connexion DB...")
try:
    from core.db.configbd import get_connection as get_db_connection
    print("[OK] Module DB OK")
except Exception as e:
    print(f"[ERREUR] ERREUR Module DB: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Import du thème
print("[4/5] Test thème UI...")
try:
    from core.gui.ui_theme import EmacButton, EmacCard, EmacHeader, get_current_theme
    from core.gui.emac_ui_kit import add_custom_title_bar
    print("[OK] Thème UI OK")
except Exception as e:
    print(f"[ERREUR] ERREUR Thème: {e}")
    traceback.print_exc()

# Test 5: Import gestion_evaluation
print("[5/5] Test import gestion_evaluation...")
try:
    from core.gui import gestion_evaluation
    print("[OK] Module gestion_evaluation OK")
except Exception as e:
    print(f"[ERREUR] ERREUR Import gestion_evaluation:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {str(e)}")
    print()
    print("Traceback complet:")
    traceback.print_exc()
    print()
    sys.exit(1)

# Test 6: Création de l'application et du dialogue
print()
print("[6/6] Test création du dialogue...")
try:
    app = QApplication(sys.argv)

    # Essayer de créer le dialogue (sans l'afficher)
    from core.gui.gestion_evaluation import GestionEvaluationDialog

    dialog = GestionEvaluationDialog()
    print("[OK] Dialogue créé avec succès!")
    print(f"   Titre: {dialog.windowTitle()}")
    print(f"   Taille: {dialog.size()}")

    # Ne pas afficher, juste créer
    # dialog.show()

except Exception as e:
    print(f"[ERREUR] ERREUR Création dialogue:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {str(e)}")
    print()
    print("Traceback complet:")
    traceback.print_exc()
    print()
    sys.exit(1)

print()
print("="*60)
print("TOUS LES TESTS PASSENT [OK]")
print("="*60)
print()
print("Le module fonctionne en mode test.")
print("Si l'application crash au runtime, le problème est probablement:")
print("  - Une erreur dans le chargement des données depuis la DB")
print("  - Un problème avec la connexion DB")
print("  - Une erreur dans un slot/signal PyQt")
print()

input("Appuyez sur Entrée pour fermer...")
