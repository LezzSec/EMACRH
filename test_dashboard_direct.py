# -*- coding: utf-8 -*-
"""
Test direct du dashboard sans authentification
"""

import sys
import os

# Ajouter le répertoire App au PYTHONPATH
app_dir = os.path.join(os.path.dirname(__file__), 'App')
sys.path.insert(0, app_dir)
os.chdir(app_dir)

print("="*60)
print("TEST DIRECT DU DASHBOARD")
print("="*60)
print(f"Répertoire de travail: {os.getcwd()}")

# Charger .env
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
    print("✓ .env chargé")
except Exception as e:
    print(f"⚠️ Erreur chargement .env: {e}")

# Créer l'application Qt
from PyQt5.QtWidgets import QApplication

print("\nCréation de l'application Qt...")
app = QApplication(sys.argv)

# Appliquer le thème
print("Application du thème...")
from core.gui.main_qt import get_theme_components
theme = get_theme_components()
theme['EmacTheme'].apply(app)
print("✓ Thème appliqué")

# Simuler un utilisateur connecté pour les tests
print("\nSimulation de l'authentification...")
from core.services import auth_service

# Connexion avec un utilisateur admin par défaut
try:
    # Tenter de se connecter avec admin/admin
    if auth_service.authenticate_user('admin', 'admin'):
        print("✓ Authentification réussie avec admin/admin")
    else:
        # Sinon, définir manuellement la session
        print("⚠️ Authentification admin/admin échouée, simulation manuelle")
        auth_service._current_user_id = 1  # Forcer l'ID utilisateur
except Exception as e:
    print(f"⚠️ Erreur authentification: {e}")
    print("   On continue quand même pour tester l'UI")

# Créer et afficher la fenêtre principale
print("\nCréation du dashboard...")
from core.gui.main_qt import MainWindow

window = MainWindow()
print("✓ Fenêtre créée")

print("\nAffichage de la fenêtre...")
window.show()
print("✓ Fenêtre affichée")

print("\nVérification de l'état des listes...")
print(f"  - Retard: {window.retard_list.count()} éléments")
print(f"  - Prochaines: {window.next_eval_list.count()} éléments")

print("\nLancement de l'application...")
print("Surveillez la console pour les messages [DEBUG] et [ERROR]")
print("="*60)

sys.exit(app.exec_())
