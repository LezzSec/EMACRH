# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox,
    QTableWidget, QTableWidgetItem, QGroupBox, QHBoxLayout,
    QLabel, QComboBox, QHeaderView, QAbstractItemView,
)
from PyQt5.QtGui import QColor

from domain.services.planning.planning_service import (
    get_historique_declarations, supprimer_declaration,
)
from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date
from gui.components.emac_ui_kit import show_error_message
from gui.screens.planning.regularisation.utils import format_type_declaration, get_type_color

logger = get_logger(__name__)


class HistoriqueTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        filter_group = QGroupBox("Filtres")
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Type :"))
        self.history_type_combo = QComboBox()
        self.history_type_combo.addItems([
            "Tous", "CongePaye", "RTT", "Maladie",
            "AccidentTravail", "ArretTravail", "Formation", "Autre",
        ])
        self.history_type_combo.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.history_type_combo)

        filter_layout.addWidget(QLabel("Période :"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "30 derniers jours", "3 derniers mois",
            "6 derniers mois", "Cette année", "Tout",
        ])
        self.period_combo.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.period_combo)

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Prénom", "Type", "Date Début", "Date Fin", "Motif"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.history_table.setColumnHidden(0, True)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.history_table, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        delete_btn = QPushButton("Supprimer")
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #dc2626;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #b91c1c;
            }
        """)
        delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)

    def load_data(self):
        try:
            type_filter = self.history_type_combo.currentText()
            period = self.period_combo.currentText()
            rows = get_historique_declarations(type_filter=type_filter, period=period)

            self.history_table.setRowCount(0)
            for r in rows:
                row_pos = self.history_table.rowCount()
                self.history_table.insertRow(row_pos)

                self.history_table.setItem(row_pos, 0, QTableWidgetItem(str(r['id'])))
                self.history_table.setItem(row_pos, 1, QTableWidgetItem(r['nom'] or ""))
                self.history_table.setItem(row_pos, 2, QTableWidgetItem(r['prenom'] or ""))

                type_item = QTableWidgetItem(format_type_declaration(r['type_declaration']))
                type_item.setForeground(QColor(get_type_color(r['type_declaration'])))
                self.history_table.setItem(row_pos, 3, type_item)

                date_debut = r['date_debut']
                date_debut_str = date_debut if isinstance(date_debut, str) else format_date(date_debut)
                self.history_table.setItem(row_pos, 4, QTableWidgetItem(date_debut_str))

                date_fin = r['date_fin']
                date_fin_str = date_fin if isinstance(date_fin, str) else format_date(date_fin)
                self.history_table.setItem(row_pos, 5, QTableWidgetItem(date_fin_str))

                self.history_table.setItem(row_pos, 6, QTableWidgetItem(r['motif'] or ""))

        except Exception as e:
            logger.exception(f"Erreur chargement historique: {e}")
            show_error_message(self, "Erreur", "Impossible de charger l'historique", e)

    def _delete_selected(self):
        if not self.history_table.selectedItems():
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une déclaration à supprimer.")
            return

        row = self.history_table.currentRow()
        decl_id = int(self.history_table.item(row, 0).text())
        nom = self.history_table.item(row, 1).text()
        prenom = self.history_table.item(row, 2).text()

        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer la déclaration de {nom} {prenom} ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        try:
            if not supprimer_declaration(decl_id):
                raise RuntimeError("Échec de la suppression")
            QMessageBox.information(self, "Succès", "Déclaration supprimée avec succès.")
            self.load_data()
        except Exception as e:
            logger.exception(f"Erreur suppression declaration: {e}")
            show_error_message(self, "Erreur", "Impossible de supprimer la déclaration", e)
