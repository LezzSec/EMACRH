# -*- coding: utf-8 -*-
"""
Panneau gauche : recherche et sélection d'opérateur.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class RhSelectionPanel(QWidget):
    """Zone gauche de l'écran RH : champ de recherche + liste de résultats."""

    operateur_selected = pyqtSignal(int)
    search_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setStyleSheet("background-color: #f8fafc;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        titre = QLabel("Sélection Personnel")
        titre.setFont(QFont("Segoe UI", 14, QFont.Bold))
        titre.setStyleSheet("color: #111827;")
        layout.addWidget(titre)

        search_label = QLabel("Rechercher par nom, prénom ou matricule")
        search_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tapez pour rechercher...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        self.search_input.textChanged.connect(self.search_changed)
        layout.addWidget(self.search_input)

        results_label = QLabel("Résultats")
        results_label.setStyleSheet("color: #374151; font-weight: 600; margin-top: 8px;")
        layout.addWidget(results_label)

        self.liste_operateurs = QListWidget()
        self.liste_operateurs.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.liste_operateurs.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: white;
            }
            QListWidget::item {
                padding: 5px 10px;
                border-bottom: 1px solid #f3f4f6;
                font-size: 12px;
            }
            QListWidget::item:selected {
                background-color: #eff6ff;
                color: #1e40af;
            }
            QListWidget::item:hover {
                background-color: #f9fafb;
            }
        """)
        self.liste_operateurs.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.liste_operateurs, 1)

        self.compteur_resultats = QLabel("0 personne(s)")
        self.compteur_resultats.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(self.compteur_resultats)

    def show_results(self, resultats: list):
        self.liste_operateurs.clear()
        for op in resultats:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, op['id'])
            nom = (op.get('nom') or '').upper()
            prenom = op.get('prenom') or ''
            item.setText(f"{nom} {prenom}")
            item.setToolTip(f"ID: {op['id']} | Statut: {op.get('statut', 'ACTIF')}")
            self.liste_operateurs.addItem(item)
        self.compteur_resultats.setText(f"{len(resultats)} personne(s)")

    def show_loading(self):
        self.liste_operateurs.clear()
        self.liste_operateurs.addItem("Recherche en cours…")
        self.compteur_resultats.setText("…")

    def highlight(self, operateur_id: int):
        for i in range(self.liste_operateurs.count()):
            item = self.liste_operateurs.item(i)
            if item.data(Qt.UserRole) == operateur_id:
                self.liste_operateurs.setCurrentItem(item)
                break

    def _on_item_clicked(self, item: QListWidgetItem):
        self.operateur_selected.emit(item.data(Qt.UserRole))
