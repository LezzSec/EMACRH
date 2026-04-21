# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from infrastructure.logging.logging_config import get_logger
from gui.components.emac_ui_kit import add_custom_title_bar
from gui.screens.planning.regularisation.tab_absents_jour import AbsentsJourTab
from gui.screens.planning.regularisation.tab_declaration import DeclarationTab
from gui.screens.planning.regularisation.tab_calendrier_absences import CalendrierAbsencesTab
from gui.screens.planning.regularisation.tab_calendrier_eval import CalendrierEvalTab
from gui.screens.planning.regularisation.tab_historique import HistoriqueTab
from gui.screens.planning.regularisation.tab_docs_expiration import DocsExpirationTab

logger = get_logger(__name__)


class RegularisationDialog(QDialog):
    """Fenêtre de gestion du Planning & Absences."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Planning & Absences")
        self.setGeometry(150, 150, 1200, 800)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = add_custom_title_bar(self, "Planning & Absences")
        main_layout.addWidget(title_bar)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        header_content = QVBoxLayout()
        header = QLabel("Planning & Absences")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header_content.addWidget(header)

        subtitle = QLabel("Déclarez les absences et consultez le planning du personnel")
        subtitle.setStyleSheet("color: #6b7280; font-size: 12px;")
        subtitle.setAlignment(Qt.AlignCenter)
        header_content.addWidget(subtitle)
        layout.addLayout(header_content)

        self.tabs = QTabWidget()

        self.tab_absents = AbsentsJourTab()
        self.tabs.addTab(self.tab_absents, "Absents Aujourd'hui")

        self.tab_declaration = DeclarationTab()
        self.tab_declaration.refresh_requested.connect(self.refresh_all)
        self.tabs.addTab(self.tab_declaration, "Déclarer une Absence")

        self.tab_calendrier = CalendrierAbsencesTab()
        self.tabs.addTab(self.tab_calendrier, "Calendrier Absences")

        self.tab_eval = CalendrierEvalTab()
        self.tabs.addTab(self.tab_eval, "Calendrier Évaluations")

        self.tab_docs = DocsExpirationTab()
        self.tabs.addTab(self.tab_docs, "Documents expirant")

        self.tab_historique = HistoriqueTab()
        self.tabs.addTab(self.tab_historique, "Historique")

        layout.addWidget(self.tabs)

        action_row = QHBoxLayout()
        action_row.addStretch()

        refresh_btn = QPushButton("Actualiser")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_all)
        action_row.addWidget(refresh_btn)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        action_row.addWidget(close_btn)

        layout.addLayout(action_row)
        main_layout.addWidget(content_widget)

        self.refresh_all()

    def refresh_all(self):
        self.tab_absents.load_data()
        self.tab_declaration.load_data()
        self.tab_calendrier.load_data()
        self.tab_docs.load_data()
        self.tab_historique.load_data()
