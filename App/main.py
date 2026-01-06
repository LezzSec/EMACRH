# -*- coding: utf-8 -*-
"""
Point d'entrée principal pour l'application EMAC
Ce fichier configure le PYTHONPATH et lance l'application
"""

import sys
import os

# Déterminer si nous sommes en mode exécutable compilé (frozen) ou script Python
if getattr(sys, 'frozen', False):
    # En mode exécutable (PyInstaller)
    application_path = os.path.dirname(sys.executable)
else:
    # En mode script Python normal
    application_path = os.path.dirname(os.path.abspath(__file__))

# Ajouter le chemin de l'application au PYTHONPATH
if application_path not in sys.path:
    sys.path.insert(0, application_path)

# Importer et lancer l'application
if __name__ == "__main__":
    import traceback
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import qInstallMessageHandler, QtMsgType

    try:
        # Handler de messages Qt (copié depuis main_qt.py)
        def qt_message_handler(msg_type, context, message):
            if msg_type == QtMsgType.QtDebugMsg:
                print(f"Qt Debug: {message}")
            elif msg_type == QtMsgType.QtWarningMsg:
                print(f"Qt Warning: {message}")
            elif msg_type == QtMsgType.QtCriticalMsg:
                print(f"Qt Critical: {message}")
            elif msg_type == QtMsgType.QtFatalMsg:
                print(f"Qt Fatal: {message}")

        qInstallMessageHandler(qt_message_handler)

        app = QApplication(sys.argv)

        # Charger et appliquer le thème
        print("Chargement du thème...")
        from core.gui.ui_theme import EmacTheme
        EmacTheme.apply(app)
        print("Thème appliqué avec succès")

        # Login
        print("Affichage de la fenêtre de login...")
        from core.gui.login_dialog import LoginDialog
        login_dialog = LoginDialog()

        if login_dialog.exec_() == LoginDialog.Accepted:
            print("Login accepté, chargement de la fenêtre principale...")
            from core.gui.main_qt import MainWindow
            win = MainWindow()
            print("Fenêtre principale créée, affichage...")
            win.show()
            print("Fenêtre affichée, lancement de la boucle d'événements...")
            sys.exit(app.exec_())
        else:
            print("Login annulé")
            sys.exit(0)

    except Exception as e:
        print("\n" + "="*60)
        print("ERREUR CRITIQUE:")
        print("="*60)
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print("\nTraceback complet:")
        traceback.print_exc()
        print("="*60)

        # Afficher aussi une boîte de dialogue si possible
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Erreur EMAC",
                f"Une erreur critique est survenue:\n\n{type(e).__name__}: {str(e)}\n\nConsultez la console pour plus de détails."
            )
        except:
            pass

        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)
