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
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import qInstallMessageHandler

    try:
        # Handler silencieux pour les messages Qt (supprime le spam console)
        qInstallMessageHandler(lambda *_: None)

        app = QApplication(sys.argv)
        from infrastructure.logging.optimized_db_logger import flush_db_logs, shutdown_db_logger
        app.aboutToQuit.connect(flush_db_logs)
        app.aboutToQuit.connect(shutdown_db_logger)

        # Charger et appliquer le thème
        from gui.components.ui_theme import EmacTheme
        EmacTheme.apply(app)

        # Login
        from gui.screens.admin.login_dialog import LoginDialog
        login_dialog = LoginDialog()

        if login_dialog.exec_() == LoginDialog.Accepted:
            from gui.main_qt import MainWindow
            win = MainWindow()
            win.show()
            sys.exit(app.exec_())
        else:
            sys.exit(0)

    except Exception as e:
        import logging
        logging.basicConfig()
        logging.getLogger(__name__).exception("Erreur critique au démarrage de l'application")

        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Erreur EMAC",
                "Une erreur inattendue est survenue au démarrage.\n\nConsultez le fichier de log pour les détails."
            )
        except Exception:
            pass

        sys.exit(1)
