# -*- coding: utf-8 -*-
"""
Module de Planning des Absences
Interface simple : calendrier + liste des absents
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QWidget, QDateEdit, QComboBox,
    QTextEdit, QMessageBox, QHeaderView, QRadioButton, QButtonGroup,
    QGroupBox, QCalendarWidget, QSplitter
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QBrush
from datetime import datetime, timedelta

from core.services.absence_service_crud import AbsenceServiceCRUD, calculer_jours_ouvres
from core.services.planning_service import get_evaluations_mois
from core.repositories.personnel_repo import PersonnelRepository
from core.gui.emac_ui_kit import add_custom_title_bar
from core.utils.logging_config import get_logger

logger = get_logger(__name__)
from core.services.permission_manager import can
from core.utils.date_format import format_date


class PlanningAbsencesDialog(QDialog):
    """Planning des absences - Vue calendrier simple"""

    data_changed = pyqtSignal()

    def __init__(self, personnel_id=None, parent=None):
        super().__init__(parent)
        self.personnel_id = personnel_id
        self.absences_by_date = {}  # Cache des absences par date
        self.evaluations_by_date = {}  # Cache des évaluations par date

        self.setWindowTitle("Planning des Absences & Évaluations")
        self.setGeometry(100, 100, 1200, 800)
        self.setModal(False)

        self.init_ui()
        self.load_absences_month()
        self.load_evaluations_month()

    def init_ui(self):
        """Initialise l'interface"""
        # Layout principal avec marges nulles
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Planning des Absences & Évaluations")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Titre
        title = QLabel("Planning des Absences & Évaluations")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Splitter horizontal : Calendrier | Détails
        splitter = QSplitter(Qt.Horizontal)

        # === PARTIE GAUCHE : CALENDRIER ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Contrôles de navigation
        nav_layout = QHBoxLayout()

        btn_prev_month = QPushButton("◀ Mois précédent")
        btn_prev_month.clicked.connect(self.previous_month)
        nav_layout.addWidget(btn_prev_month)

        self.current_month_label = QLabel()
        self.current_month_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.current_month_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.current_month_label)

        btn_next_month = QPushButton("Mois suivant ▶")
        btn_next_month.clicked.connect(self.next_month)
        nav_layout.addWidget(btn_next_month)

        btn_today = QPushButton("Aujourd'hui")
        btn_today.clicked.connect(self.goto_today)
        nav_layout.addWidget(btn_today)

        left_layout.addLayout(nav_layout)

        # Calendrier
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.date_selected)
        self.calendar.currentPageChanged.connect(self.month_changed)
        left_layout.addWidget(self.calendar)

        # Légende
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Légende:"))

        legend_absence = QLabel("  ■  Absence")
        legend_absence.setStyleSheet("QLabel { color: #e74c3c; font-weight: bold; }")
        legend_layout.addWidget(legend_absence)

        legend_evaluation = QLabel("  ■  Évaluation")
        legend_evaluation.setStyleSheet("QLabel { color: #f39c12; font-weight: bold; }")
        legend_layout.addWidget(legend_evaluation)

        legend_layout.addStretch()
        left_layout.addLayout(legend_layout)

        splitter.addWidget(left_widget)

        # === PARTIE DROITE : DÉTAILS + ACTIONS ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Date sélectionnée
        self.selected_date_label = QLabel("Sélectionnez une date")
        self.selected_date_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.selected_date_label.setAlignment(Qt.AlignCenter)
        self.selected_date_label.setStyleSheet("padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        right_layout.addWidget(self.selected_date_label)

        # Statistiques du jour
        stats_layout = QHBoxLayout()

        self.nb_absents_label = QLabel("0 absent(s)")
        self.nb_absents_label.setFont(QFont("Arial", 12))
        self.nb_absents_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        stats_layout.addWidget(self.nb_absents_label)

        self.nb_evaluations_label = QLabel("0 évaluation(s)")
        self.nb_evaluations_label.setFont(QFont("Arial", 12))
        self.nb_evaluations_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        stats_layout.addWidget(self.nb_evaluations_label)

        stats_layout.addStretch()
        right_layout.addLayout(stats_layout)

        # Table des absents
        right_layout.addWidget(QLabel("🔴 Personnes absentes ce jour:"))

        self.absents_table = QTableWidget()
        self.absents_table.setColumnCount(4)
        self.absents_table.setHorizontalHeaderLabels([
            "Nom Prénom", "Type", "Du", "Au"
        ])
        self.absents_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.absents_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.absents_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.absents_table.setAlternatingRowColors(True)
        self.absents_table.setMaximumHeight(150)
        right_layout.addWidget(self.absents_table)

        # Table des évaluations
        right_layout.addWidget(QLabel("🟠 Évaluations prévues ce jour:"))

        self.evaluations_table = QTableWidget()
        self.evaluations_table.setColumnCount(3)
        self.evaluations_table.setHorizontalHeaderLabels([
            "Nom Prénom", "Poste", "Niveau"
        ])
        self.evaluations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.evaluations_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.evaluations_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.evaluations_table.setAlternatingRowColors(True)
        self.evaluations_table.setMaximumHeight(150)
        right_layout.addWidget(self.evaluations_table)

        # Section: Mes actions
        actions_group = QGroupBox("Mes demandes d'absence")
        actions_layout = QVBoxLayout()

        # Bouton "Nouvelle demande" uniquement si permission d'écriture sur planning
        if can('planning.absences.edit'):
            btn_nouvelle_demande = QPushButton("➕ Nouvelle demande d'absence")
            btn_nouvelle_demande.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 10px;
                    font-size: 13px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            btn_nouvelle_demande.clicked.connect(self.show_nouvelle_demande)
            actions_layout.addWidget(btn_nouvelle_demande)

        btn_mes_demandes = QPushButton("📋 Voir mes demandes")
        btn_mes_demandes.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_mes_demandes.clicked.connect(self.show_mes_demandes)
        actions_layout.addWidget(btn_mes_demandes)

        actions_group.setLayout(actions_layout)
        right_layout.addWidget(actions_group)

        right_layout.addStretch()

        splitter.addWidget(right_widget)

        # Ratio 60/40
        splitter.setStretchFactor(0, 60)
        splitter.setStretchFactor(1, 40)

        layout.addWidget(splitter)

        # Boutons en bas
        bottom_layout = QHBoxLayout()

        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_data)
        bottom_layout.addWidget(btn_refresh)

        bottom_layout.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)

        layout.addLayout(bottom_layout)

        # Ajouter le widget de contenu au layout principal
        main_layout.addWidget(content_widget)

        # Initialiser la date sélectionnée
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
        self.update_month_label()      # s'appuie sur yearShown/monthShown
        self.load_absences_month(year, month)
        self.load_evaluations_month(year, month)


    def load_absences_month(self, year=None, month=None):
        """Charge toutes les absences du mois visible"""
        # ✅ Si pas de param, on prend le mois AFFICHÉ
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
        # ✅ Utiliser le mois affiché
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

        all_dates = set(self.absences_by_date.keys()) | set(self.evaluations_by_date.keys())

        for date_key in all_dates:
            date_obj = datetime.strptime(date_key, '%Y-%m-%d').date()
            qdate = QDate(date_obj.year, date_obj.month, date_obj.day)

            has_absence = date_key in self.absences_by_date and self.absences_by_date[date_key]
            has_evaluation = date_key in self.evaluations_by_date and self.evaluations_by_date[date_key]

            if has_absence and has_evaluation:
                self.calendar.setDateTextFormat(qdate, format_both)
            elif has_absence:
                self.calendar.setDateTextFormat(qdate, format_absence)
            elif has_evaluation:
                self.calendar.setDateTextFormat(qdate, format_evaluation)


    def date_selected(self, qdate):
        """Affiche les absences et évaluations pour la date sélectionnée"""
        # Mettre à jour le label
        date_str = qdate.toString("dddd dd MMMM yyyy")
        self.selected_date_label.setText(date_str.capitalize())

        # Récupérer les absences et évaluations de cette date
        date_key = qdate.toString("yyyy-MM-dd")
        absences = self.absences_by_date.get(date_key, [])
        evaluations = self.evaluations_by_date.get(date_key, [])

        # Mettre à jour les stats
        self.nb_absents_label.setText(f"{len(absences)} absent(s)")
        self.nb_evaluations_label.setText(f"{len(evaluations)} évaluation(s)")

        # Remplir la table des absences
        self.absents_table.setRowCount(len(absences))

        for row, absence in enumerate(absences):
            self.absents_table.setItem(row, 0, QTableWidgetItem(absence['nom']))
            self.absents_table.setItem(row, 1, QTableWidgetItem(absence['type']))
            self.absents_table.setItem(row, 2, QTableWidgetItem(format_date(absence['debut'])))
            self.absents_table.setItem(row, 3, QTableWidgetItem(format_date(absence['fin'])))

        # Remplir la table des évaluations
        self.evaluations_table.setRowCount(len(evaluations))

        for row, evaluation in enumerate(evaluations):
            self.evaluations_table.setItem(row, 0, QTableWidgetItem(evaluation['nom']))
            self.evaluations_table.setItem(row, 1, QTableWidgetItem(evaluation['poste']))
            self.evaluations_table.setItem(row, 2, QTableWidgetItem(f"Niveau {evaluation['niveau']}"))

    def refresh_data(self):
        """Actualise les données"""
        self.load_absences_month()
        self.load_evaluations_month()
        current_date = self.calendar.selectedDate()
        self.date_selected(current_date)
        QMessageBox.information(self, "Actualisation", "Données actualisées avec succès")

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
                self.type_combo.addItem(f"{t['libelle']}", t['code'])
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
        type_code = self.type_combo.currentData()
        date_debut = self.date_debut.date().toPyDate()
        date_fin = self.date_fin.date().toPyDate()
        demi_debut = self.get_demi_journee(self.demi_debut_group)
        demi_fin = self.get_demi_journee(self.demi_fin_group)
        motif = self.motif_text.toPlainText()

        try:
            nb_jours = calculer_jours_ouvres(date_debut, date_fin, demi_debut, demi_fin)
            success, msg, demande_id = AbsenceServiceCRUD.create(
                personnel_id=self.personnel_id,
                type_absence_code=type_code,
                date_debut=date_debut,
                date_fin=date_fin,
                demi_debut=demi_debut,
                demi_fin=demi_fin,
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
