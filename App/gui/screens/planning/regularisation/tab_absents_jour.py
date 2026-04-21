# -*- coding: utf-8 -*-
from datetime import date

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QGroupBox, QHBoxLayout, QHeaderView, QAbstractItemView,
)
from PyQt5.QtGui import QFont, QColor

from domain.services.planning.planning_service import get_absents_du_jour
from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date
from gui.components.emac_ui_kit import show_error_message
from gui.screens.planning.regularisation.utils import format_type_declaration, get_type_color

logger = get_logger(__name__)


class AbsentsJourTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        today_label = QLabel(f"Absences du {format_date(date.today())}")
        today_label.setFont(QFont("Arial", 14, QFont.Bold))
        today_label.setStyleSheet("color: #1f2937; padding: 10px;")
        layout.addWidget(today_label)

        stats_group = QGroupBox("Résumé")
        stats_layout = QHBoxLayout()

        self.total_absents_label = QLabel("Total absents : 0")
        self.total_absents_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #dc2626;")
        stats_layout.addWidget(self.total_absents_label)

        self.conges_label = QLabel("Congés : 0")
        self.conges_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f59e0b;")
        stats_layout.addWidget(self.conges_label)

        self.maladie_label = QLabel("Maladie : 0")
        self.maladie_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #8b5cf6;")
        stats_layout.addWidget(self.maladie_label)

        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        self.absents_table = QTableWidget()
        self.absents_table.setColumnCount(6)
        self.absents_table.setHorizontalHeaderLabels([
            "Nom", "Prénom", "Type", "Date Début", "Date Fin", "Motif"
        ])
        self.absents_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.absents_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.absents_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.absents_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.absents_table.setAlternatingRowColors(True)
        self.absents_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.absents_table, 1)

    def load_data(self):
        try:
            rows = get_absents_du_jour(date.today())
            self.absents_table.setRowCount(0)

            total_absents = len(rows)
            conges_count = 0
            maladie_count = 0

            for r in rows:
                row_pos = self.absents_table.rowCount()
                self.absents_table.insertRow(row_pos)

                type_decl = r['type_declaration']

                if type_decl in ['CongePaye', 'RTT']:
                    conges_count += 1
                elif type_decl in ['Maladie', 'ArretTravail', 'AccidentTravail', 'AccidentTrajet']:
                    maladie_count += 1

                self.absents_table.setItem(row_pos, 0, QTableWidgetItem(r['nom'] or ""))
                self.absents_table.setItem(row_pos, 1, QTableWidgetItem(r['prenom'] or ""))

                type_item = QTableWidgetItem(format_type_declaration(type_decl))
                type_item.setBackground(QColor(get_type_color(type_decl)))
                type_item.setForeground(QColor("white"))
                self.absents_table.setItem(row_pos, 2, type_item)

                date_debut = r['date_debut']
                date_debut_str = date_debut if isinstance(date_debut, str) else format_date(date_debut)
                self.absents_table.setItem(row_pos, 3, QTableWidgetItem(date_debut_str))

                date_fin = r['date_fin']
                date_fin_str = date_fin if isinstance(date_fin, str) else format_date(date_fin)
                self.absents_table.setItem(row_pos, 4, QTableWidgetItem(date_fin_str))

                self.absents_table.setItem(row_pos, 5, QTableWidgetItem(r['motif'] or ""))

            self.total_absents_label.setText(f"Total absents : {total_absents}")
            self.conges_label.setText(f"Congés : {conges_count}")
            self.maladie_label.setText(f"Maladie : {maladie_count}")

        except Exception as e:
            logger.exception(f"Erreur chargement absents: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les absents", e)
