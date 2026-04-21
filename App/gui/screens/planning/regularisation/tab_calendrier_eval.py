# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QHBoxLayout,
    QCalendarWidget, QListWidget, QListWidgetItem, QLineEdit, QComboBox,
)
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QFont, QColor, QTextCharFormat

from domain.services.planning.planning_service import (
    get_postes_avec_polyvalences, get_evaluations_dates_du_mois, get_evaluations_du_jour,
)
from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date
from gui.components.emac_ui_kit import show_error_message

logger = get_logger(__name__)


class CalendrierEvalTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._eval_dates_cache: set = set()
        self._build_ui()
        self._load_postes_filter()
        self._load_markings()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.eval_search = QLineEdit()
        self.eval_search.setPlaceholderText("Rechercher opérateur (nom/prénom)...")
        self.eval_search.textChanged.connect(self._reload_all)
        filters.addWidget(self.eval_search, stretch=1)

        filters.addWidget(QLabel("Poste :"))
        self.eval_poste_filter = QComboBox()
        self.eval_poste_filter.addItem("(Tous)")
        self.eval_poste_filter.currentIndexChanged.connect(self._reload_all)
        filters.addWidget(self.eval_poste_filter)

        refresh_btn = QPushButton("Actualiser")
        refresh_btn.clicked.connect(self._reload_all)
        filters.addWidget(refresh_btn)
        layout.addLayout(filters)

        h_layout = QHBoxLayout()

        cal_group = QGroupBox("Calendrier des évaluations")
        cal_layout = QVBoxLayout()
        self.eval_calendar = QCalendarWidget()
        self.eval_calendar.setGridVisible(True)
        self.eval_calendar.clicked.connect(self._on_date_clicked)
        self.eval_calendar.currentPageChanged.connect(self._load_markings)
        self.eval_calendar.selectionChanged.connect(self._refresh_display)
        cal_layout.addWidget(self.eval_calendar)
        cal_group.setLayout(cal_layout)
        h_layout.addWidget(cal_group, 2)

        details_group = QGroupBox("Évaluations du jour sélectionné")
        details_layout = QVBoxLayout()
        self.eval_selected_date_label = QLabel("Sélectionnez une date")
        self.eval_selected_date_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.eval_selected_date_label.setStyleSheet("color: #1f2937; padding: 10px;")
        details_layout.addWidget(self.eval_selected_date_label)
        self.eval_calendar_list = QListWidget()
        details_layout.addWidget(self.eval_calendar_list)
        details_group.setLayout(details_layout)
        h_layout.addWidget(details_group, 1)

        layout.addLayout(h_layout)

    def _load_postes_filter(self):
        try:
            rows = get_postes_avec_polyvalences()
            self.eval_poste_filter.clear()
            self.eval_poste_filter.addItem("(Tous)", None)
            for r in rows:
                self.eval_poste_filter.addItem(r['poste_code'], r['id'])
        except Exception as e:
            logger.error(f"Erreur lors du chargement des postes : {e}")

    def _load_markings(self):
        try:
            year = self.eval_calendar.yearShown()
            month = self.eval_calendar.monthShown()
            first_day = date(year, month, 1)
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)

            rows = get_evaluations_dates_du_mois(first_day, last_day)

            self._eval_dates_cache = set()
            for r in rows:
                eval_date = r['eval_date']
                if eval_date:
                    if isinstance(eval_date, str):
                        eval_date = datetime.strptime(eval_date, '%Y-%m-%d').date()
                    self._eval_dates_cache.add(eval_date)

            self._apply_formats(first_day, last_day)

        except Exception as e:
            logger.error(f"Erreur lors du marquage du calendrier : {e}")

    def _apply_formats(self, first_day, last_day):
        default_format = QTextCharFormat()
        default_format.setBackground(QColor("white"))
        current = first_day
        while current <= last_day:
            self.eval_calendar.setDateTextFormat(
                QDate(current.year, current.month, current.day), default_format
            )
            current += timedelta(days=1)

        eval_format = QTextCharFormat()
        eval_format.setBackground(QColor("#dbeafe"))
        eval_format.setForeground(QColor("#1e40af"))
        eval_format.setFontWeight(QFont.Bold)

        for eval_date in self._eval_dates_cache:
            self.eval_calendar.setDateTextFormat(
                QDate(eval_date.year, eval_date.month, eval_date.day), eval_format
            )

    def _refresh_display(self):
        try:
            year = self.eval_calendar.yearShown()
            month = self.eval_calendar.monthShown()
            first_day = date(year, month, 1)
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)
            self._apply_formats(first_day, last_day)
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement du calendrier : {e}")

    def _reload_all(self):
        self._load_markings()
        selected = self.eval_calendar.selectedDate()
        self._on_date_clicked(selected)

    def _on_date_clicked(self, qdate):
        selected = qdate.toPyDate()
        self.eval_selected_date_label.setText(f"Évaluations du {format_date(selected)}")

        try:
            search_text = self.eval_search.text().lower()
            poste_id = self.eval_poste_filter.currentData()

            rows = get_evaluations_du_jour(selected, poste_id=poste_id)
            self.eval_calendar_list.clear()

            if not rows:
                item = QListWidgetItem("Aucune évaluation prévue ce jour")
                item.setForeground(QColor("#10b981"))
                self.eval_calendar_list.addItem(item)
            else:
                for r in rows:
                    nom = r['nom'] or ""
                    prenom = r['prenom'] or ""
                    poste = r['poste_code'] or ""
                    niveau = r['niveau'] or "N/A"

                    if search_text and search_text not in f"{nom} {prenom} {poste}".lower():
                        continue

                    item = QListWidgetItem(f"{nom} {prenom} - {poste} (Niveau {niveau})")
                    color_map = {1: "#dc2626", 2: "#d97706", 3: "#059669", 4: "#0369a1"}
                    if niveau in color_map:
                        item.setForeground(QColor(color_map[niveau]))
                    self.eval_calendar_list.addItem(item)

        except Exception as e:
            logger.exception(f"Erreur chargement evaluations: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les évaluations", e)

    def load_data(self):
        self._load_markings()
