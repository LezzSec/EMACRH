# -*- coding: utf-8 -*-
"""
Test de la barre de titre personnalisée avec boutons de contrôle Windows
"""

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Ajouter le chemin parent pour les imports
sys.path.insert(0, '..')

from core.gui.emac_ui_kit import add_custom_title_bar


class TestDialog(QDialog):
    """Dialog de test avec barre de titre personnalisée."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Barre de Titre Personnalisée")
        self.setGeometry(200, 200, 700, 500)

        # Layout principal avec marges nulles
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Ajouter la barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "🎨 Test Barre de Titre Personnalisée")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        from PyQt5.QtWidgets import QWidget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        # Titre
        title = QLabel("Barre de Titre Personnalisée")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)

        # Description
        description = QLabel(
            "Cette fenêtre utilise une barre de titre personnalisée avec :\n\n"
            "• Bouton Minimiser (―)\n"
            "• Bouton Plein écran / Maximiser (⛶)\n"
            "• Bouton Fermer (✕)\n\n"
            "Fonctionnalités :\n"
            "• Cliquez sur la barre de titre pour déplacer la fenêtre\n"
            "• Double-cliquez sur la barre de titre pour maximiser/restaurer\n"
            "• Appuyez sur F11 pour basculer en plein écran\n"
            "• Le bouton fermer passe en rouge au survol"
        )
        description.setStyleSheet("color: #6b7280; line-height: 1.6;")
        description.setWordWrap(True)
        content_layout.addWidget(description)

        # Zone de texte pour tester
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Zone de texte pour tester l'interaction...")
        content_layout.addWidget(text_edit)

        # Boutons de test
        from PyQt5.QtWidgets import QHBoxLayout
        buttons = QHBoxLayout()

        btn_test1 = QPushButton("Bouton Test 1")
        btn_test1.clicked.connect(lambda: text_edit.append("Bouton 1 cliqué !"))
        buttons.addWidget(btn_test1)

        btn_test2 = QPushButton("Bouton Test 2")
        btn_test2.clicked.connect(lambda: text_edit.append("Bouton 2 cliqué !"))
        buttons.addWidget(btn_test2)

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        buttons.addWidget(btn_close)

        content_layout.addLayout(buttons)

        # Ajouter le contenu au layout principal
        main_layout.addWidget(content)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Appliquer un style moderne
    app.setStyleSheet("""
        QDialog {
            background: #f9fafb;
        }
        QPushButton {
            background: #3b82f6;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: #2563eb;
        }
        QTextEdit {
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            padding: 8px;
            background: white;
        }
    """)

    dialog = TestDialog()
    dialog.show()

    sys.exit(app.exec_())
