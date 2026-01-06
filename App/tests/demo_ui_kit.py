# -*- coding: utf-8 -*-
"""
Démonstration des nouveaux composants du UI Kit EMAC
Lance ce fichier pour voir les nouveaux composants : EmacBadge, EmacAlert, EmacChip
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from core.gui.emac_ui_kit import EmacBadge, EmacAlert, EmacChip, get_stylesheet, Card

class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Démo UI Kit EMAC - Nouveaux Composants")
        self.setGeometry(100, 100, 900, 700)

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ========== Section 1: EmacBadge ==========
        card1 = Card("EmacBadge", "Compteurs et notifications")

        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(10)

        # Différents variants
        variants = [
            ("12", "error"),
            ("5", "warning"),
            ("Nouveau", "success"),
            ("3/4", "info"),
            ("Admin", "primary"),
            ("99+", "default"),
        ]

        for text, variant in variants:
            badge = EmacBadge(text, variant=variant)
            badges_layout.addWidget(badge)

        badges_layout.addStretch()
        card1.body_layout.addLayout(badges_layout)

        # Exemple d'utilisation avec label
        example_layout = QHBoxLayout()
        label = QLabel("Retards d'évaluation")
        badge_retard = EmacBadge("3", variant="error")
        example_layout.addWidget(label)
        example_layout.addWidget(badge_retard)
        example_layout.addStretch()
        card1.body_layout.addLayout(example_layout)

        main_layout.addWidget(card1)

        # ========== Section 2: EmacAlert ==========
        card2 = Card("EmacAlert", "Bandeaux d'information")

        # Différents types d'alertes
        alert_success = EmacAlert("✓ Données sauvegardées avec succès !", variant="success", dismissible=True)
        card2.body_layout.addWidget(alert_success)

        alert_warning = EmacAlert("⚠ Contrat de Jean Dupont expire dans 5 jours", variant="warning", dismissible=True)
        card2.body_layout.addWidget(alert_warning)

        alert_error = EmacAlert("✕ Impossible de se connecter à la base de données", variant="error", dismissible=True)
        card2.body_layout.addWidget(alert_error)

        alert_info = EmacAlert("ℹ 12 évaluations à planifier cette semaine", variant="info", dismissible=True)
        card2.body_layout.addWidget(alert_info)

        main_layout.addWidget(card2)

        # ========== Section 3: EmacChip ==========
        card3 = Card("EmacChip", "Tags et catégories")

        # Chips de niveaux
        niveaux_layout = QHBoxLayout()
        niveaux_layout.setSpacing(8)

        niveaux_label = QLabel("Niveaux de compétence:")
        niveaux_layout.addWidget(niveaux_label)

        chip_n1 = EmacChip("Niveau 1", variant="niveau1")
        chip_n2 = EmacChip("Niveau 2", variant="niveau2")
        chip_n3 = EmacChip("Niveau 3", variant="niveau3")
        chip_n4 = EmacChip("Niveau 4", variant="niveau4")

        niveaux_layout.addWidget(chip_n1)
        niveaux_layout.addWidget(chip_n2)
        niveaux_layout.addWidget(chip_n3)
        niveaux_layout.addWidget(chip_n4)
        niveaux_layout.addStretch()

        card3.body_layout.addLayout(niveaux_layout)

        # Chips avec fermeture
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(8)

        tags_label = QLabel("Tags (closable):")
        tags_layout.addWidget(tags_label)

        chip_formation = EmacChip("Formation", variant="info", closable=True)
        chip_urgent = EmacChip("Urgent", variant="error", closable=True)
        chip_actif = EmacChip("Actif", variant="success", closable=True)

        chip_formation.closed.connect(lambda: print("Chip 'Formation' fermé"))
        chip_urgent.closed.connect(lambda: print("Chip 'Urgent' fermé"))
        chip_actif.closed.connect(lambda: print("Chip 'Actif' fermé"))

        tags_layout.addWidget(chip_formation)
        tags_layout.addWidget(chip_urgent)
        tags_layout.addWidget(chip_actif)
        tags_layout.addStretch()

        card3.body_layout.addLayout(tags_layout)

        # Autres variants
        autres_layout = QHBoxLayout()
        autres_layout.setSpacing(8)

        autres_label = QLabel("Autres styles:")
        autres_layout.addWidget(autres_label)

        chip_default = EmacChip("Default", variant="default")
        chip_primary = EmacChip("Primary", variant="primary")
        chip_warning = EmacChip("Warning", variant="warning")

        autres_layout.addWidget(chip_default)
        autres_layout.addWidget(chip_primary)
        autres_layout.addWidget(chip_warning)
        autres_layout.addStretch()

        card3.body_layout.addLayout(autres_layout)

        main_layout.addWidget(card3)

        main_layout.addStretch()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet("light"))

    window = DemoWindow()
    window.show()

    sys.exit(app.exec_())
