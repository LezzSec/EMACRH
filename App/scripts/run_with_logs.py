# -*- coding: utf-8 -*-
"""
Lance l'application avec capture complète des logs
"""

import sys
import os

# Rediriger stdout et stderr vers un fichier
log_file = open('logs/app_debug.log', 'w', encoding='utf-8')
sys.stdout = log_file
sys.stderr = log_file

print("="*60)
print("DÉMARRAGE DE L'APPLICATION AVEC LOGS")
print("="*60)

# Lancer l'application
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, app_dir)

os.chdir(app_dir)

print(f"Répertoire de travail: {os.getcwd()}")
print(f"sys.path[0]: {sys.path[0]}")

try:
    # Charger .env
    from dotenv import load_dotenv
    load_dotenv('.env')
    print("✓ .env chargé")
except Exception as e:
    print(f"⚠️ Erreur chargement .env: {e}")

try:
    print("\nImport de main_qt...")
    from core.gui import main_qt
    print("✓ main_qt importé")

    print("\nCréation de QApplication...")
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    print("✓ QApplication créée")

    print("\nApplication du thème...")
    main_qt.get_theme_components()['EmacTheme'].apply(app)
    print("✓ Thème appliqué")

    print("\nCréation de la fenêtre principale...")
    window = main_qt.MainWindow()
    print("✓ Fenêtre créée")

    print("\nAffichage de la fenêtre...")
    window.show()
    print("✓ Fenêtre affichée")

    print("\nLancement de la boucle d'événements...")
    sys.exit(app.exec_())

except Exception as e:
    print(f"\n[ERREUR CRITIQUE] {e}")
    import traceback
    traceback.print_exc()
    input("Appuyez sur Entrée pour fermer...")
finally:
    log_file.close()
