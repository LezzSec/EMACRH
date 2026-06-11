# -*- coding: utf-8 -*-
"""
Module de Planning des Absences
Interface simple : calendrier + liste des absents
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QWidget, QDateEdit, QComboBox,
    QTextEdit, QMessageBox, QHeaderView, QRadioButton, QButtonGroup,
    QGroupBox, QCalendarWidget, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QBrush
from datetime import datetime, timedelta, date as date_type

from domain.services.planning.absence_service_crud import AbsenceServiceCRUD, calculer_jours_ouvres
from domain.services.planning.planning_service import get_evaluations_mois, get_documents_expirant
from domain.repositories.personnel_repo import PersonnelRepository
from gui.components.emac_ui_kit import add_custom_title_bar
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)
from application.permission_manager import can
from infrastructure.config.date_format import format_date


class PlanningAbsencesDialog(QDialog):
    """Planning des absences - Vue calendrier simple"""

    data_changed = pyqtSignal()

    def __init__(self, personnel_id=None, parent=None):
        super().__init__(parent)
        self.personnel_id = personnel_id
        self.absences_by_date = {}
        self.evaluations_by_date = {}
        self.sirh_by_date = {}

        self.setWindowTitle("Planning des Absences & Évaluations")
        self.setGeometry(100, 100, 1200, 800)
        self.setModal(False)

        self.init_ui()
        self.load_absences_month()
        self.load_evaluations_month()
        self.load_sirh_month()
        self.load_documents_expirant()

    def init_ui(self):
        """Initialise l'interface"""
        _NAV_BTN = """
            QPushButton {
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                color: #374151;
            }
            QPushButton:hover { background: #e5e7eb; }
            QPushButton:pressed { background: #d1d5db; }
        """
        _TODAY_BTN = """
            QPushButton {
                background: #2563eb;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover { background: #1d4ed8; }
        """
        _SECTION_LABEL = """
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #6b7280;
                text-transform: uppercase;
                letter-spacing: 1px;
                padding: 4px 0 2px 0;
            }
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = add_custom_title_bar(self, "Planning des Absences & Evaluations")
        main_layout.addWidget(title_bar)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: #f9fafb;")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #e5e7eb; width: 1px; }")

        # === PARTIE GAUCHE : CALENDRIER ===
        left_widget = QWidget()
        left_widget.setStyleSheet("background: white; border-radius: 8px;")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        # Navigation mois
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(6)

        btn_prev_month = QPushButton("◀ Mois precedent")
        btn_prev_month.setStyleSheet(_NAV_BTN)
        btn_prev_month.clicked.connect(self.previous_month)
        nav_layout.addWidget(btn_prev_month)

        self.current_month_label = QLabel()
        self.current_month_label.setFont(QFont("Arial", 13, QFont.Bold))
        self.current_month_label.setAlignment(Qt.AlignCenter)
        self.current_month_label.setStyleSheet("color: #111827; background: transparent;")
        nav_layout.addWidget(self.current_month_label, 1)

        btn_next_month = QPushButton("Mois suivant ▶")
        btn_next_month.setStyleSheet(_NAV_BTN)
        btn_next_month.clicked.connect(self.next_month)
        nav_layout.addWidget(btn_next_month)

        btn_today = QPushButton("Aujourd'hui")
        btn_today.setStyleSheet(_TODAY_BTN)
        btn_today.clicked.connect(self.goto_today)
        nav_layout.addWidget(btn_today)

        left_layout.addLayout(nav_layout)

        # Calendrier
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget QAbstractItemView {
                selection-background-color: #2563eb;
                selection-color: white;
                font-size: 12px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: transparent;
            }
        """)
        self.calendar.clicked.connect(self.date_selected)
        self.calendar.activated.connect(self.show_day_detail)
        self.calendar.currentPageChanged.connect(self.month_changed)
        left_layout.addWidget(self.calendar)

        # Légende
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)

        lbl_leg = QLabel("Legende :")
        lbl_leg.setStyleSheet("color: #6b7280; font-size: 11px; background: transparent;")
        legend_layout.addWidget(lbl_leg)

        dot_absence = QLabel()
        dot_absence.setFixedSize(12, 12)
        dot_absence.setStyleSheet("background: #e74c3c; border-radius: 6px;")
        legend_layout.addWidget(dot_absence)
        lbl_abs = QLabel("Absence")
        lbl_abs.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px; background: transparent;")
        legend_layout.addWidget(lbl_abs)

        dot_eval = QLabel()
        dot_eval.setFixedSize(12, 12)
        dot_eval.setStyleSheet("background: #f39c12; border-radius: 6px;")
        legend_layout.addWidget(dot_eval)
        lbl_eval = QLabel("Evaluation")
        lbl_eval.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 11px; background: transparent;")
        legend_layout.addWidget(lbl_eval)

        dot_sirh = QLabel()
        dot_sirh.setFixedSize(12, 12)
        dot_sirh.setStyleSheet("background: #2563eb; border-radius: 6px;")
        legend_layout.addWidget(dot_sirh)
        lbl_sirh = QLabel("Absence SIRH")
        lbl_sirh.setStyleSheet("color: #2563eb; font-weight: bold; font-size: 11px; background: transparent;")
        legend_layout.addWidget(lbl_sirh)

        legend_layout.addStretch()
        left_layout.addLayout(legend_layout)

        splitter.addWidget(left_widget)

        # === PARTIE DROITE : DÉTAILS ===
        right_widget = QWidget()
        right_widget.setStyleSheet("background: white; border-radius: 8px;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(10)

        # Date sélectionnée
        self.selected_date_label = QLabel("Selectionnez une date")
        self.selected_date_label.setFont(QFont("Arial", 13, QFont.Bold))
        self.selected_date_label.setAlignment(Qt.AlignCenter)
        self.selected_date_label.setStyleSheet("""
            padding: 10px 16px;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 8px;
            color: #1e40af;
        """)
        right_layout.addWidget(self.selected_date_label)

        # === Zone 1 : Absences + Evaluations côte à côte ===
        day_sections_layout = QHBoxLayout()
        day_sections_layout.setSpacing(8)

        # -- Panel Absences --
        abs_panel = QFrame()
        abs_panel.setStyleSheet("background: #fff5f5; border-radius: 8px; border: 1px solid #fecaca;")
        abs_layout = QVBoxLayout(abs_panel)
        abs_layout.setContentsMargins(0, 0, 0, 0)
        abs_layout.setSpacing(0)

        self.abs_header_label = QLabel("  ABSENCES — 0")
        self.abs_header_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.abs_header_label.setStyleSheet("""
            background: #dc2626;
            color: white;
            padding: 6px 10px;
            border-radius: 7px 7px 0 0;
        """)
        abs_layout.addWidget(self.abs_header_label)

        self.absents_table = QTableWidget()
        self.absents_table.setColumnCount(4)
        self.absents_table.setHorizontalHeaderLabels(["Nom Prenom", "Type", "Du", "Au"])
        self.absents_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.absents_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.absents_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.absents_table.setAlternatingRowColors(True)
        self.absents_table.setStyleSheet("""
            QTableWidget { border: none; background: transparent; }
            QHeaderView::section { background: #fee2e2; font-weight: bold; font-size: 10px; color: #991b1b; border: none; padding: 4px; }
            QTableWidget::item { padding: 3px; }
        """)
        abs_layout.addWidget(self.absents_table)
        day_sections_layout.addWidget(abs_panel)

        # -- Panel Evaluations --
        eval_panel = QFrame()
        eval_panel.setStyleSheet("background: #fffbeb; border-radius: 8px; border: 1px solid #fde68a;")
        eval_layout = QVBoxLayout(eval_panel)
        eval_layout.setContentsMargins(0, 0, 0, 0)
        eval_layout.setSpacing(0)

        self.eval_header_label = QLabel("  EVALUATIONS — 0")
        self.eval_header_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.eval_header_label.setStyleSheet("""
            background: #d97706;
            color: white;
            padding: 6px 10px;
            border-radius: 7px 7px 0 0;
        """)
        eval_layout.addWidget(self.eval_header_label)

        self.evaluations_table = QTableWidget()
        self.evaluations_table.setColumnCount(3)
        self.evaluations_table.setHorizontalHeaderLabels(["Nom Prenom", "Poste", "Niveau"])
        self.evaluations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.evaluations_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.evaluations_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.evaluations_table.setAlternatingRowColors(True)
        self.evaluations_table.setStyleSheet("""
            QTableWidget { border: none; background: transparent; }
            QHeaderView::section { background: #fef3c7; font-weight: bold; font-size: 10px; color: #92400e; border: none; padding: 4px; }
            QTableWidget::item { padding: 3px; }
        """)
        eval_layout.addWidget(self.evaluations_table)
        day_sections_layout.addWidget(eval_panel)

        right_layout.addLayout(day_sections_layout)

        # === Zone 2 : Alertes du mois ===
        docs_panel = QFrame()
        docs_panel.setStyleSheet("background: #f5f3ff; border-radius: 8px; border: 1px solid #ddd6fe;")
        docs_layout = QVBoxLayout(docs_panel)
        docs_layout.setContentsMargins(0, 0, 0, 0)
        docs_layout.setSpacing(0)

        self.docs_header_label = QLabel("  ALERTES DU MOIS — Documents expirant (30 j)  —  0")
        self.docs_header_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.docs_header_label.setStyleSheet("""
            background: #7c3aed;
            color: white;
            padding: 6px 10px;
            border-radius: 7px 7px 0 0;
        """)
        docs_layout.addWidget(self.docs_header_label)

        self.docs_table = QTableWidget()
        self.docs_table.setColumnCount(3)
        self.docs_table.setHorizontalHeaderLabels(["Nom Prenom", "Document", "J. restants"])
        self.docs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.docs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.docs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.docs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.docs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.docs_table.setAlternatingRowColors(True)
        self.docs_table.setMaximumHeight(130)
        self.docs_table.setStyleSheet("""
            QTableWidget { border: none; background: transparent; }
            QHeaderView::section { background: #ede9fe; font-weight: bold; font-size: 10px; color: #5b21b6; border: none; padding: 4px; }
            QTableWidget::item { padding: 3px; }
        """)
        docs_layout.addWidget(self.docs_table)
        right_layout.addWidget(docs_panel)

        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 65)
        splitter.setStretchFactor(1, 35)

        layout.addWidget(splitter)

        # Barre du bas
        bottom_layout = QHBoxLayout()

        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                color: #374151;
            }
            QPushButton:hover { background: #e5e7eb; }
        """)
        btn_refresh.clicked.connect(self.refresh_data)
        bottom_layout.addWidget(btn_refresh)

        btn_sync_sirh = QPushButton("Synchroniser SIRH")
        btn_sync_sirh.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
            }
            QPushButton:hover { background: #047857; }
        """)
        btn_sync_sirh.clicked.connect(self._sync_sirh)
        bottom_layout.addWidget(btn_sync_sirh)

        bottom_layout.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 20px;
                font-size: 12px;
                color: #374151;
            }
            QPushButton:hover { background: #f3f4f6; }
        """)
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)

        layout.addLayout(bottom_layout)

        main_layout.addWidget(content_widget)

        self.update_month_label()
        today = QDate.currentDate()
        self.date_selected(today)

    def update_month_label(self):
        """Met à jour le label du mois courant"""
        year = self.calendar.yearShown()
        month = self.calendar.monthShown()
        qdate = QDate(year, month, 1)
        month_name = qdate.toString("MMMM yyyy")
        self.current_month_label.setText(month_name.capitalize())


    def previous_month(self):
        """Mois précédent"""
        current = self.calendar.selectedDate()
        new_date = current.addMonths(-1)
        self.calendar.setSelectedDate(new_date)
        self.month_changed(new_date.year(), new_date.month())

    def next_month(self):
        """Mois suivant"""
        current = self.calendar.selectedDate()
        new_date = current.addMonths(1)
        self.calendar.setSelectedDate(new_date)
        self.month_changed(new_date.year(), new_date.month())

    def goto_today(self):
        """Retour à aujourd'hui"""
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.date_selected(today)

    def month_changed(self, year, month):
        """Chargement quand on change de mois (flèches ou molette)"""
        self.update_month_label()
        self.load_absences_month(year, month)
        self.load_evaluations_month(year, month)
        self.load_sirh_month(year, month)


    def load_absences_month(self, year=None, month=None):
        """Charge toutes les absences du mois visible"""
        if year is None or month is None:
            year = self.calendar.yearShown()
            month = self.calendar.monthShown()

        first_day = QDate(year, month, 1)
        last_day = QDate(year, month, first_day.daysInMonth())

        absences = AbsenceServiceCRUD.get_validees_pour_mois(
            first_day.toString("yyyy-MM-dd"),
            last_day.toString("yyyy-MM-dd")
        )

        self.absences_by_date = {}

        for absence in absences:
            debut = absence['date_debut']
            fin = absence['date_fin']

            current_date = debut
            while current_date <= fin:
                date_key = current_date.strftime('%Y-%m-%d')
                if date_key not in self.absences_by_date:
                    self.absences_by_date[date_key] = []

                self.absences_by_date[date_key].append({
                    'nom': absence['nom_complet'],
                    'type': absence['type_libelle'],
                    'debut': debut,
                    'fin': fin
                })
                current_date += timedelta(days=1)

        self.update_calendar_colors()


    def load_evaluations_month(self, year=None, month=None):
        """Charge toutes les évaluations du mois visible"""
        if year is None or month is None:
            year = self.calendar.yearShown()
            month = self.calendar.monthShown()

        first_day = QDate(year, month, 1)
        last_day = QDate(year, month, first_day.daysInMonth())

        evaluations = get_evaluations_mois(
            first_day.toString("yyyy-MM-dd"),
            last_day.toString("yyyy-MM-dd")
        )

        self.evaluations_by_date = {}

        for evaluation in evaluations:
            date_eval = evaluation['prochaine_evaluation']
            date_key = date_eval.strftime('%Y-%m-%d')

            if date_key not in self.evaluations_by_date:
                self.evaluations_by_date[date_key] = []

            self.evaluations_by_date[date_key].append({
                'nom': evaluation['nom_complet'],
                'poste': evaluation['poste_code'],
                'niveau': evaluation['niveau']
            })

        self.update_calendar_colors()


    def update_calendar_colors(self):
        """Colore les jours avec absences et évaluations dans le calendrier"""
        year = self.calendar.yearShown()
        month = self.calendar.monthShown()
        first_day = QDate(year, month, 1)

        default_format = QTextCharFormat()

        # Réinitialiser tous les jours du mois
        for day in range(1, first_day.daysInMonth() + 1):
            qdate = QDate(year, month, day)
            self.calendar.setDateTextFormat(qdate, default_format)

        # Formats
        format_absence = QTextCharFormat()
        format_absence.setBackground(QBrush(QColor(231, 76, 60, 100)))
        format_absence.setForeground(QBrush(QColor(255, 255, 255)))

        format_evaluation = QTextCharFormat()
        format_evaluation.setBackground(QBrush(QColor(243, 156, 18, 100)))
        format_evaluation.setForeground(QBrush(QColor(255, 255, 255)))

        format_both = QTextCharFormat()
        format_both.setBackground(QBrush(QColor(155, 89, 182, 100)))
        format_both.setForeground(QBrush(QColor(255, 255, 255)))

        format_sirh = QTextCharFormat()
        format_sirh.setBackground(QBrush(QColor(37, 99, 235, 80)))
        format_sirh.setForeground(QBrush(QColor(255, 255, 255)))

        all_dates = (
            set(self.absences_by_date.keys())
            | set(self.evaluations_by_date.keys())
            | set(self.sirh_by_date.keys())
        )

        for date_key in all_dates:
            date_obj = datetime.strptime(date_key, '%Y-%m-%d').date()
            qdate = QDate(date_obj.year, date_obj.month, date_obj.day)

            has_absence = bool(self.absences_by_date.get(date_key))
            has_evaluation = bool(self.evaluations_by_date.get(date_key))
            has_sirh = bool(self.sirh_by_date.get(date_key))

            if has_absence and has_evaluation:
                self.calendar.setDateTextFormat(qdate, format_both)
            elif has_absence:
                self.calendar.setDateTextFormat(qdate, format_absence)
            elif has_evaluation:
                self.calendar.setDateTextFormat(qdate, format_evaluation)
            elif has_sirh:
                self.calendar.setDateTextFormat(qdate, format_sirh)


    def date_selected(self, qdate):
        """Affiche les absences et évaluations pour la date sélectionnée"""
        date_str = qdate.toString("dddd dd MMMM yyyy")
        self.selected_date_label.setText(date_str.capitalize())

        date_key = qdate.toString("yyyy-MM-dd")
        absences = self.absences_by_date.get(date_key, [])
        sirh = self.sirh_by_date.get(date_key, [])
        evaluations = self.evaluations_by_date.get(date_key, [])

        self.abs_header_label.setText(f"  ABSENCES — {len(absences) + len(sirh)}")
        self.eval_header_label.setText(f"  EVALUATIONS — {len(evaluations)}")

        # Table absences : lignes EMAC (blanc) puis lignes SIRH (bleu clair)
        self.absents_table.setRowCount(len(absences) + len(sirh))

        for row, absence in enumerate(absences):
            self.absents_table.setItem(row, 0, QTableWidgetItem(absence["nom"]))
            self.absents_table.setItem(row, 1, QTableWidgetItem(absence["type"]))
            self.absents_table.setItem(row, 2, QTableWidgetItem(format_date(absence["debut"])))
            self.absents_table.setItem(row, 3, QTableWidgetItem(format_date(absence["fin"])))

        sirh_color = QColor("#dbeafe")
        for i, s in enumerate(sirh):
            row = len(absences) + i
            items = [
                QTableWidgetItem(s["nom"]),
                QTableWidgetItem(f"SIRH : {s['type']}"),
                QTableWidgetItem(format_date(s["debut"])),
                QTableWidgetItem(format_date(s["fin"])),
            ]
            for col, item in enumerate(items):
                item.setBackground(sirh_color)
                self.absents_table.setItem(row, col, item)

        # Table évaluations
        self.evaluations_table.setRowCount(len(evaluations))

        for row, evaluation in enumerate(evaluations):
            self.evaluations_table.setItem(row, 0, QTableWidgetItem(evaluation["nom"]))
            self.evaluations_table.setItem(row, 1, QTableWidgetItem(evaluation["poste"]))
            self.evaluations_table.setItem(row, 2, QTableWidgetItem(f"Niveau {evaluation['niveau']}"))

    def load_sirh_month(self, year=None, month=None):
        """Charge les absences SIRH du mois depuis absences_sirh (MySQL)."""
        if year is None or month is None:
            year = self.calendar.yearShown()
            month = self.calendar.monthShown()

        first_day = QDate(year, month, 1)
        last_day = QDate(year, month, first_day.daysInMonth())

        try:
            from domain.services.external.absences_sirh_import_service import (
                get_sirh_absences_pour_mois,
            )
            periods = get_sirh_absences_pour_mois(
                first_day.toString("yyyy-MM-dd"),
                last_day.toString("yyyy-MM-dd"),
            )
        except Exception:
            logger.warning("Absences SIRH non disponibles (table manquante ou sync non effectuée)")
            self.sirh_by_date = {}
            return

        self.sirh_by_date = {}
        month_start = first_day.toPyDate()
        month_end = last_day.toPyDate()
        for r in periods:
            debut = r["date_debut"]
            fin = r["date_fin"]
            current = debut
            while current <= min(fin, month_end):
                if current >= month_start:
                    date_key = current.strftime("%Y-%m-%d")
                    self.sirh_by_date.setdefault(date_key, []).append({
                        "nom": r["nom_complet"],
                        "type": r["type_libelle"],
                        "debut": debut,
                        "fin": fin,
                    })
                current += timedelta(days=1)

        self.update_calendar_colors()

    def load_documents_expirant(self):
        """Charge les documents expirant dans les 30 prochains jours."""
        try:
            rows = get_documents_expirant(30)
            self.docs_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                jours = r.get('jours_restants') or 0
                nom_complet = f"{r.get('nom', '')} {r.get('prenom', '')}".strip()
                nom_doc = r.get('nom_document') or r.get('nom_fichier') or ""

                item_nom = QTableWidgetItem(nom_complet)
                item_doc = QTableWidgetItem(nom_doc)
                item_j = QTableWidgetItem(f"{jours} j")
                item_j.setTextAlignment(Qt.AlignCenter)

                if jours <= 7:
                    color = QColor("#fee2e2")
                    fg = QColor("#991b1b")
                elif jours <= 15:
                    color = QColor("#ffedd5")
                    fg = QColor("#9a3412")
                else:
                    color = QColor("#fef9c3")
                    fg = QColor("#713f12")

                for item in (item_nom, item_doc, item_j):
                    item.setBackground(color)
                    item.setForeground(fg)

                self.docs_table.setItem(i, 0, item_nom)
                self.docs_table.setItem(i, 1, item_doc)
                self.docs_table.setItem(i, 2, item_j)

            self.docs_header_label.setText(f"  ALERTES DU MOIS — Documents expirant (30 j)  —  {len(rows)}")
        except Exception:
            logger.exception("Erreur chargement documents expirant")
            self.docs_table.setRowCount(0)

    def refresh_data(self):
        """Actualise les données"""
        self.load_absences_month()
        self.load_evaluations_month()
        self.load_sirh_month()
        self.load_documents_expirant()
        current_date = self.calendar.selectedDate()
        self.date_selected(current_date)
        QMessageBox.information(self, "Actualisation", "Données actualisées avec succès")

    def _sync_sirh(self):
        """Lance une synchronisation incrémentale depuis HOPHABS."""
        from domain.services.external.absences_sirh_import_service import sync_absences_sirh
        try:
            inserted, updated, skipped = sync_absences_sirh(incremental=True)
            QMessageBox.information(
                self, "Synchronisation terminée",
                f"{inserted} insérés, {updated} mis à jour, {skipped} ignorés."
            )
            self.load_sirh_month()
            self.date_selected(self.calendar.selectedDate())
        except Exception as e:
            logger.exception(f"Erreur sync SIRH: {e}")
            QMessageBox.warning(
                self, "Erreur",
                "Synchronisation impossible.\n"
                "Vérifiez la connexion au serveur SIRH (variables EMAC_EXT_SS_*)."
            )

    def show_day_detail(self, qdate):
        """Ouvre le récap détaillé du jour (double-clic sur le calendrier)."""
        date_key = qdate.toString("yyyy-MM-dd")
        absences = self.absences_by_date.get(date_key, [])
        sirh = self.sirh_by_date.get(date_key, [])
        evaluations = self.evaluations_by_date.get(date_key, [])

        if not absences and not sirh and not evaluations:
            return

        dialog = DayDetailDialog(qdate, absences, sirh, evaluations, parent=self)
        dialog.exec_()

    def show_nouvelle_demande(self):
        """Ouvre le dialogue de nouvelle demande"""
        if not self.personnel_id:
            QMessageBox.warning(self, "Erreur", "Personnel non identifié")
            return

        dialog = NouvelleDemande(self.personnel_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_data()
            self.data_changed.emit()

    def show_mes_demandes(self):
        """Ouvre le dialogue de consultation des demandes"""
        if not self.personnel_id:
            QMessageBox.warning(self, "Erreur", "Personnel non identifié")
            return

        dialog = MesDemandesDialog(self.personnel_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_data()
            self.data_changed.emit()


class DayDetailDialog(QDialog):
    """Récap complet d'une journée : absences EMAC, absences SIRH, évaluations."""

    def __init__(self, qdate, absences, sirh, evaluations, parent=None):
        super().__init__(parent)
        date_str = qdate.toString("dddd dd MMMM yyyy").capitalize()
        self.setWindowTitle(f"Détail — {date_str}")
        self.setMinimumSize(820, 560)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Titre
        title = QLabel(date_str)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #111827;")
        layout.addWidget(title)

        # ── Absences (EMAC + SIRH) ────────────────────────────────────
        layout.addWidget(self._section_header(
            f"Absences  ({len(absences) + len(sirh)})",
            bg="#dc2626", text_color="white"
        ))
        tbl_abs = self._make_table(["Nom / Prénom", "Type", "Du", "Au"])
        for a in absences:
            self._add_row(tbl_abs, [
                a.get("nom", ""),
                a.get("type", ""),
                format_date(a.get("debut")),
                format_date(a.get("fin")),
            ], bg="#fff5f5")
        for s in sirh:
            self._add_row(tbl_abs, [
                s.get("nom", ""),
                s.get("type", ""),
                format_date(s.get("debut")),
                format_date(s.get("fin")),
            ], bg="#eff6ff")
        tbl_abs.setMinimumHeight(max(tbl_abs.rowCount() * 28 + 30, 55))
        layout.addWidget(tbl_abs, max(tbl_abs.rowCount(), 1))

        # ── Évaluations ────────────────────────────────────────────────
        layout.addWidget(self._section_header(
            f"Évaluations prévues  ({len(evaluations)})",
            bg="#d97706", text_color="white"
        ))
        tbl_eval = self._make_table(["Nom / Prénom", "Poste", "Niveau actuel"])
        for e in evaluations:
            self._add_row(tbl_eval, [
                e.get("nom", ""),
                e.get("poste", ""),
                f"Niveau {e.get('niveau', '')}",
            ], bg="#fffbeb")
        tbl_eval.setMinimumHeight(max(tbl_eval.rowCount() * 28 + 30, 55))
        layout.addWidget(tbl_eval, max(tbl_eval.rowCount(), 1))

        # Bouton fermer
        btn_close = QPushButton("Fermer")
        btn_close.setFixedWidth(100)
        btn_close.setStyleSheet(
            "QPushButton { background: #f3f4f6; border: 1px solid #d1d5db; "
            "border-radius: 6px; padding: 6px 16px; color: #374151; }"
            "QPushButton:hover { background: #e5e7eb; }"
        )
        btn_close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn_close)
        layout.addLayout(row)

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _section_header(text: str, bg: str, text_color: str) -> QLabel:
        lbl = QLabel(f"  {text}")
        lbl.setFont(QFont("Arial", 10, QFont.Bold))
        lbl.setFixedHeight(30)
        lbl.setStyleSheet(
            f"background: {bg}; color: {text_color}; "
            "border-radius: 6px 6px 0 0; padding-left: 8px;"
        )
        return lbl

    @staticmethod
    def _make_table(headers: list) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.verticalHeader().setVisible(False)
        t.setStyleSheet(
            "QTableWidget { border: 1px solid #e5e7eb; border-top: none; }"
            "QHeaderView::section { background: #f9fafb; font-weight: bold; "
            "font-size: 11px; color: #374151; border: none; "
            "border-bottom: 1px solid #e5e7eb; padding: 4px; }"
        )
        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Interactive)
        t.setColumnWidth(0, 175)
        if len(headers) > 1:
            hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, len(headers)):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        return t

    @staticmethod
    def _add_row(table: QTableWidget, values: list, bg: str):
        row = table.rowCount()
        table.insertRow(row)
        color = QColor(bg)
        for col, val in enumerate(values):
            item = QTableWidgetItem(str(val))
            item.setBackground(color)
            table.setItem(row, col, item)


class NouvelleDemande(QDialog):
    """Dialogue simple pour créer une nouvelle demande"""

    def __init__(self, personnel_id, parent=None):
        super().__init__(parent)
        self.personnel_id = personnel_id

        self.setWindowTitle("Nouvelle demande d'absence")
        self.setFixedSize(500, 450)

        self.init_ui()
        self.load_types()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Titre
        title = QLabel("Nouvelle demande d'absence")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Type
        layout.addWidget(QLabel("Type d'absence:"))
        self.type_combo = QComboBox()
        layout.addWidget(self.type_combo)

        # Date début
        layout.addWidget(QLabel("Date de début:"))
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.dateChanged.connect(self.update_nb_jours)
        layout.addWidget(self.date_debut)

        # Demi-journée début
        demi_debut_layout = QHBoxLayout()
        self.demi_debut_group = QButtonGroup()
        self.demi_debut_journee = QRadioButton("Journée complète")
        self.demi_debut_matin = QRadioButton("Matin uniquement")
        self.demi_debut_aprem = QRadioButton("Après-midi uniquement")
        self.demi_debut_journee.setChecked(True)
        self.demi_debut_group.addButton(self.demi_debut_journee, 0)
        self.demi_debut_group.addButton(self.demi_debut_matin, 1)
        self.demi_debut_group.addButton(self.demi_debut_aprem, 2)
        self.demi_debut_group.buttonClicked.connect(self.update_nb_jours)
        demi_debut_layout.addWidget(self.demi_debut_journee)
        demi_debut_layout.addWidget(self.demi_debut_matin)
        demi_debut_layout.addWidget(self.demi_debut_aprem)
        layout.addLayout(demi_debut_layout)

        # Date fin
        layout.addWidget(QLabel("Date de fin:"))
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.dateChanged.connect(self.update_nb_jours)
        layout.addWidget(self.date_fin)

        # Demi-journée fin
        demi_fin_layout = QHBoxLayout()
        self.demi_fin_group = QButtonGroup()
        self.demi_fin_journee = QRadioButton("Journée complète")
        self.demi_fin_matin = QRadioButton("Matin uniquement")
        self.demi_fin_aprem = QRadioButton("Après-midi uniquement")
        self.demi_fin_journee.setChecked(True)
        self.demi_fin_group.addButton(self.demi_fin_journee, 0)
        self.demi_fin_group.addButton(self.demi_fin_matin, 1)
        self.demi_fin_group.addButton(self.demi_fin_aprem, 2)
        self.demi_fin_group.buttonClicked.connect(self.update_nb_jours)
        demi_fin_layout.addWidget(self.demi_fin_journee)
        demi_fin_layout.addWidget(self.demi_fin_matin)
        demi_fin_layout.addWidget(self.demi_fin_aprem)
        layout.addLayout(demi_fin_layout)

        # Nombre de jours
        nb_layout = QHBoxLayout()
        nb_layout.addWidget(QLabel("Nombre de jours ouvrés:"))
        self.nb_jours_label = QLabel("0")
        self.nb_jours_label.setFont(QFont("Arial", 12, QFont.Bold))
        nb_layout.addWidget(self.nb_jours_label)
        nb_layout.addStretch()
        layout.addLayout(nb_layout)

        # Motif
        layout.addWidget(QLabel("Motif (optionnel):"))
        self.motif_text = QTextEdit()
        self.motif_text.setMaximumHeight(60)
        layout.addWidget(self.motif_text)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_valider = QPushButton("✓ Envoyer la demande")
        btn_valider.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; font-weight: bold;")
        btn_valider.clicked.connect(self.valider)
        btn_layout.addWidget(btn_valider)

        btn_annuler = QPushButton("✗ Annuler")
        btn_annuler.clicked.connect(self.reject)
        btn_layout.addWidget(btn_annuler)

        layout.addLayout(btn_layout)

    def load_types(self):
        try:
            types = AbsenceServiceCRUD.get_types_absence()
            for t in types:
                self.type_combo.addItem(f"{t['libelle']}", t['id'])
        except Exception:
            pass

    def update_nb_jours(self):
        try:
            date_debut = self.date_debut.date().toPyDate()
            date_fin = self.date_fin.date().toPyDate()
            demi_debut = self.get_demi_journee(self.demi_debut_group)
            demi_fin = self.get_demi_journee(self.demi_fin_group)

            nb_jours = calculer_jours_ouvres(date_debut, date_fin, demi_debut, demi_fin)
            self.nb_jours_label.setText(str(nb_jours))
        except Exception:
            self.nb_jours_label.setText("0")

    def get_demi_journee(self, button_group):
        button_id = button_group.checkedId()
        if button_id == 0:
            return 'JOURNEE'
        elif button_id == 1:
            return 'MATIN'
        else:
            return 'APRES_MIDI'

    def valider(self):
        type_id = self.type_combo.currentData()
        date_debut = self.date_debut.date().toPyDate()
        date_fin = self.date_fin.date().toPyDate()
        demi_debut = self.get_demi_journee(self.demi_debut_group)
        demi_fin = self.get_demi_journee(self.demi_fin_group)
        motif = self.motif_text.toPlainText()

        try:
            nb_jours = calculer_jours_ouvres(date_debut, date_fin, demi_debut, demi_fin)
            success, msg, demande_id = AbsenceServiceCRUD.create(
                personnel_id=self.personnel_id,
                type_absence_id=type_id,
                date_debut=date_debut,
                date_fin=date_fin,
                demi_journee_debut=demi_debut,
                demi_journee_fin=demi_fin,
                nb_jours=nb_jours,
                motif=motif,
                statut='EN_ATTENTE'
            )
            if not success:
                raise Exception(msg)

            QMessageBox.information(self, "Succès",
                f"Demande créée avec succès\n\n"
                f"Nombre de jours: {self.nb_jours_label.text()}\n"
                f"Statut: En attente de validation"
            )
            self.accept()

        except Exception as e:
            logger.exception(f"Erreur création demande absence: {e}")
            QMessageBox.critical(self, "Erreur", "Impossible de créer la demande. Consultez les logs pour plus de détails.")


class MesDemandesDialog(QDialog):
    """Dialogue pour consulter ses demandes"""

    def __init__(self, personnel_id, parent=None):
        super().__init__(parent)
        self.personnel_id = personnel_id

        self.setWindowTitle("Mes demandes d'absence")
        self.setGeometry(150, 150, 900, 500)

        self.init_ui()
        self.load_demandes()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Titre
        title = QLabel("Mes demandes d'absence")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Filtres
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Année:"))
        self.annee_filter = QComboBox()
        annee = datetime.now().year
        for i in range(annee - 1, annee + 2):
            self.annee_filter.addItem(str(i), i)
        self.annee_filter.setCurrentText(str(annee))
        self.annee_filter.currentIndexChanged.connect(self.load_demandes)
        filter_layout.addWidget(self.annee_filter)

        filter_layout.addWidget(QLabel("Statut:"))
        self.statut_filter = QComboBox()
        self.statut_filter.addItem("Tous", None)
        self.statut_filter.addItem("En attente", "EN_ATTENTE")
        self.statut_filter.addItem("Validées", "VALIDEE")
        self.statut_filter.addItem("Refusées", "REFUSEE")
        self.statut_filter.currentIndexChanged.connect(self.load_demandes)
        filter_layout.addWidget(self.statut_filter)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Type", "Début", "Fin", "Nb jours", "Statut", "Motif"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Boutons
        btn_layout = QHBoxLayout()

        # Bouton d'annulation seulement si permission d'écriture
        if can('planning.absences.edit'):
            btn_annuler = QPushButton("Annuler la demande sélectionnée")
            btn_annuler.clicked.connect(self.annuler_demande)
            btn_layout.addWidget(btn_annuler)

        btn_layout.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def load_demandes(self):
        annee = self.annee_filter.currentData()
        statut = self.statut_filter.currentData()

        try:
            demandes = AbsenceServiceCRUD.get_demandes_personnel_details(self.personnel_id, annee, statut)

            self.table.setRowCount(len(demandes))

            for row, demande in enumerate(demandes):
                self.table.setItem(row, 0, QTableWidgetItem(str(demande['id'])))
                self.table.setItem(row, 1, QTableWidgetItem(demande['type_libelle']))
                self.table.setItem(row, 2, QTableWidgetItem(format_date(demande['date_debut'])))
                self.table.setItem(row, 3, QTableWidgetItem(format_date(demande['date_fin'])))
                self.table.setItem(row, 4, QTableWidgetItem(str(demande['nb_jours'])))
                self.table.setItem(row, 5, QTableWidgetItem(demande['statut']))
                self.table.setItem(row, 6, QTableWidgetItem(demande['motif'] or ''))

                # Couleur selon statut
                if demande['statut'] == 'VALIDEE':
                    for col in range(7):
                        self.table.item(row, col).setBackground(QColor(39, 174, 96, 50))
                elif demande['statut'] == 'REFUSEE':
                    for col in range(7):
                        self.table.item(row, col).setBackground(QColor(231, 76, 60, 50))
        except Exception:
            pass

    def annuler_demande(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une demande")
            return

        row = selected[0].row()
        demande_id = int(self.table.item(row, 0).text())
        statut = self.table.item(row, 5).text()

        if statut != 'EN_ATTENTE':
            QMessageBox.warning(self, "Attention", "Seules les demandes en attente peuvent être annulées")
            return

        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment annuler cette demande ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                AbsenceServiceCRUD.annuler(demande_id)

                QMessageBox.information(self, "Succès", "Demande annulée")
                self.load_demandes()

            except Exception as e:
                logger.exception(f"Erreur annulation demande absence: {e}")
                QMessageBox.critical(self, "Erreur", "Impossible d'annuler la demande. Consultez les logs pour plus de détails.")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Test avec le premier personnel actif
    personnel_id = PersonnelRepository.get_first_actif_id()

    dialog = PlanningAbsencesDialog(personnel_id=personnel_id)
    dialog.show()

    sys.exit(app.exec_())
