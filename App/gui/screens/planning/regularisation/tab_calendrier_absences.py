# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QHBoxLayout,
    QCalendarWidget, QListWidget, QListWidgetItem,
)
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QFont, QColor, QTextCharFormat

from domain.services.planning.planning_service import get_absences_du_mois, get_absences_du_jour
from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date
from gui.components.emac_ui_kit import show_error_message
from gui.screens.planning.regularisation.utils import format_type_declaration, get_type_color

logger = get_logger(__name__)


class CalendrierAbsencesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        h_layout = QHBoxLayout()

        cal_group = QGroupBox("Calendrier des absences")
        cal_layout = QVBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self._on_date_clicked)
        cal_layout.addWidget(self.calendar)
        cal_group.setLayout(cal_layout)
        h_layout.addWidget(cal_group, 2)

        details_group = QGroupBox("Absences du jour sélectionné")
        details_layout = QVBoxLayout()
        self.selected_date_label = QLabel("Sélectionnez une date")
        self.selected_date_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.selected_date_label.setStyleSheet("color: #1f2937; padding: 10px;")
        details_layout.addWidget(self.selected_date_label)
        self.calendar_absents_list = QListWidget()
        details_layout.addWidget(self.calendar_absents_list)
        details_group.setLayout(details_layout)
        h_layout.addWidget(details_group, 1)

        layout.addLayout(h_layout)

    def load_data(self):
        try:
            current_date = self.calendar.selectedDate().toPyDate()
            first_day = date(current_date.year, current_date.month, 1)
            if current_date.month == 12:
                last_day = date(current_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(current_date.year, current_date.month + 1, 1) - timedelta(days=1)

            rows = get_absences_du_mois(first_day, last_day)

            default_format = QTextCharFormat()
            default_format.setBackground(QColor("white"))

            absence_format = QTextCharFormat()
            absence_format.setBackground(QColor("#fef3c7"))
            absence_format.setForeground(QColor("#92400e"))

            for r in rows:
                date_debut = r['date_debut']
                date_fin = r['date_fin']
                if isinstance(date_debut, str):
                    date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
                if isinstance(date_fin, str):
                    date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()

                current = date_debut
                while current <= date_fin:
                    if first_day <= current <= last_day:
                        qdate = QDate(current.year, current.month, current.day)
                        self.calendar.setDateTextFormat(qdate, absence_format)
                    current += timedelta(days=1)

        except Exception as e:
            logger.error(f"Erreur lors du chargement du calendrier : {e}")

    def _on_date_clicked(self, qdate):
        selected = qdate.toPyDate()
        self.selected_date_label.setText(f"Absences du {format_date(selected)}")

        try:
            rows = get_absences_du_jour(selected)
            self.calendar_absents_list.clear()

            if not rows:
                item = QListWidgetItem("Aucune absence ce jour")
                item.setForeground(QColor("#10b981"))
                self.calendar_absents_list.addItem(item)
            else:
                for r in rows:
                    type_decl = r['type_declaration']
                    text = f"{r['nom'] or ''} {r['prenom'] or ''} - {format_type_declaration(type_decl)}"
                    if r['motif']:
                        text += f" ({r['motif']})"
                    item = QListWidgetItem(text)
                    item.setForeground(QColor(get_type_color(type_decl)))
                    self.calendar_absents_list.addItem(item)

        except Exception as e:
            logger.exception(f"Erreur chargement absences: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les absences", e)
