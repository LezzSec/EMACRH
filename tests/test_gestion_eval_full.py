# -*- coding: utf-8 -*-
"""
Test complet de gestion_evaluation avec connexion DB réelle
"""

import sys
import os
import traceback

# Ajouter le chemin App au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'App'))

print("="*60)
print("TEST GESTION EVALUATION - AVEC DB")
print("="*60)
print()

from PyQt5.QtWidgets import QApplication

# Test connexion DB
print("[1/3] Test connexion base de donnees...")
try:
    from core.db.configbd import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM personnel")
    count = cursor.fetchone()[0]
    print(f"[OK] Connexion DB OK - {count} personnel dans la base")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"[ERREUR] Connexion DB echouee:")
    print(f"  {type(e).__name__}: {e}")
    traceback.print_exc()
    print()
    print("Le crash est probablement du a un probleme de connexion DB.")
    print("Verifiez votre fichier .env et que MySQL est demarr�.")
    input("\nAppuyez sur Entree...")
    sys.exit(1)

# Créer l'application
print("[2/3] Creation de l'application PyQt...")
app = QApplication(sys.argv)

# Appliquer le thème
try:
    from core.gui.ui_theme import EmacTheme
    EmacTheme.apply(app)
    print("[OK] Theme applique")
except Exception as e:
    print(f"[ATTENTION] Theme non applique: {e}")

# Créer et afficher le dialogue
print("[3/3] Ouverture du dialogue gestion evaluation...")
try:
    from core.gui.gestion_evaluation import GestionEvaluationDialog

    dialog = GestionEvaluationDialog()
    print("[OK] Dialogue cree")

    print()
    print("="*60)
    print("DIALOGUE AFFICHE - Testez les fonctionnalites")
    print("="*60)
    print()
    print("Si le dialogue se ferme immediatement, regardez les erreurs ci-dessous.")
    print()

    dialog.show()
    sys.exit(app.exec_())

except Exception as e:
    print()
    print("[ERREUR] Crash lors de l'affichage du dialogue:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {e}")
    print()
    print("Traceback complet:")
    traceback.print_exc()
    print()
    print("="*60)
    input("\nAppuyez sur Entree...")
    sys.exit(1)
