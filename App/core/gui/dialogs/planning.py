# regularisation.py – Planning & Absences
# Gestion des absences, congés et planning du personnel

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QDateEdit, QComboBox,
    QHeaderView, QAbstractItemView, QGroupBox, QFormLayout, QTextEdit,
    QTabWidget, QWidget, QCalendarWidget, QListWidget, QListWidgetItem, QLineEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QTextCharFormat
from datetime import date, datetime, timedelta
from domain.services.planning.planning_service import (
    get_absents_du_jour, get_personnel_actif_liste, creer_declaration,
    get_absences_du_mois, get_absences_du_jour, get_postes_avec_polyvalences,
    get_evaluations_dates_du_mois, get_evaluations_du_jour,
    get_historique_declarations, supprimer_declaration,
    get_documents_expirant,
)
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)
from core.gui.components.emac_ui_kit import add_custom_title_bar, show_error_message
from infrastructure.config.date_format import format_date



class RegularisationDialog(QDialog):
    """
    Fenêtre de gestion du Planning & Absences.
    Permet de déclarer les absences/congés et voir qui est absent.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Planning & Absences")
        self.setGeometry(150, 150, 1200, 800)

        # Layout principal avec marges nulles
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Planning & Absences")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # === En-tête ===
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

        # === Onglets ===
        self.tabs = QTabWidget()

        # Onglet 1: Qui est absent aujourd'hui
        self.absents_tab = self.create_absents_tab()
        self.tabs.addTab(self.absents_tab, "📋 Absents Aujourd'hui")

        # Onglet 2: Déclarer une absence
        self.declare_tab = self.create_declare_tab()
        self.tabs.addTab(self.declare_tab, "➕ Déclarer une Absence")

        # Onglet 3: Calendrier Absences
        self.calendar_tab = self.create_calendar_tab()
        self.tabs.addTab(self.calendar_tab, "📅 Calendrier Absences")

        # Onglet 4: Calendrier Évaluations
        self.eval_calendar_tab = self.create_eval_calendar_tab()
        self.tabs.addTab(self.eval_calendar_tab, "📆 Calendrier Évaluations")

        # Onglet 5: Documents expirant
        self.docs_expiration_tab = self.create_docs_expiration_tab()
        self.tabs.addTab(self.docs_expiration_tab, "⚠️ Documents expirant")

        # Onglet 6: Historique
        self.history_tab = self.create_history_tab()
        self.tabs.addTab(self.history_tab, "📊 Historique")

        layout.addWidget(self.tabs)

        # === Boutons d'action ===
        action_row = QHBoxLayout()
        action_row.addStretch()

        refresh_btn = QPushButton("🔄 Actualiser")
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

        # Ajouter le widget de contenu au layout principal
        main_layout.addWidget(content_widget)

        # Charger les données initiales
        self.refresh_all()

    # ==================== ONGLET 1: ABSENTS AUJOURD'HUI ====================

    def create_absents_tab(self):
        """Crée l'onglet 'Qui est absent aujourd'hui'."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info date
        today_label = QLabel(f"📅 Absences du {format_date(date.today())}")
        today_label.setFont(QFont("Arial", 14, QFont.Bold))
        today_label.setStyleSheet("color: #1f2937; padding: 10px;")
        layout.addWidget(today_label)

        # Statistiques
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

        # Table des absents
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

        return widget

    def load_absents_today(self):
        """Charge la liste des absents aujourd'hui."""
        try:
            today = date.today()

            rows = get_absents_du_jour(today)

            self.absents_table.setRowCount(0)

            total_absents = len(rows)
            conges_count = 0
            maladie_count = 0

            for r in rows:
                row_pos = self.absents_table.rowCount()
                self.absents_table.insertRow(row_pos)

                type_decl = r['type_declaration']

                # Compter les types
                if type_decl in ['CongePaye', 'RTT']:
                    conges_count += 1
                elif type_decl in ['Maladie', 'ArretTravail', 'AccidentTravail', 'AccidentTrajet']:
                    maladie_count += 1

                # Nom
                self.absents_table.setItem(row_pos, 0, QTableWidgetItem(r['nom'] or ""))

                # Prénom
                self.absents_table.setItem(row_pos, 1, QTableWidgetItem(r['prenom'] or ""))

                # Type
                type_item = QTableWidgetItem(self.format_type_declaration(type_decl))
                type_item.setBackground(QColor(self.get_type_color(type_decl)))
                type_item.setForeground(QColor("white"))
                self.absents_table.setItem(row_pos, 2, type_item)

                # Date début
                date_debut = r['date_debut']
                if isinstance(date_debut, str):
                    date_debut_str = date_debut
                else:
                    date_debut_str = format_date(date_debut)
                self.absents_table.setItem(row_pos, 3, QTableWidgetItem(date_debut_str))

                # Date fin
                date_fin = r['date_fin']
                if isinstance(date_fin, str):
                    date_fin_str = date_fin
                else:
                    date_fin_str = format_date(date_fin)
                self.absents_table.setItem(row_pos, 4, QTableWidgetItem(date_fin_str))

                # Motif
                self.absents_table.setItem(row_pos, 5, QTableWidgetItem(r['motif'] or ""))

            # Mettre à jour les stats
            self.total_absents_label.setText(f"Total absents : {total_absents}")
            self.conges_label.setText(f"Congés : {conges_count}")
            self.maladie_label.setText(f"Maladie : {maladie_count}")

        except Exception as e:
            logger.exception(f"Erreur chargement absents: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les absents", e)

    # ==================== ONGLET 2: DÉCLARER UNE ABSENCE ====================

    def create_declare_tab(self):
        """Crée l'onglet de déclaration d'absence."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_label = QLabel("Remplissez le formulaire ci-dessous pour déclarer une absence")
        info_label.setStyleSheet("color: #6b7280; font-size: 12px; padding: 10px;")
        layout.addWidget(info_label)

        form_group = QGroupBox("Formulaire de déclaration")
        form_layout = QFormLayout()

        # Sélection du personnel
        self.personnel_combo = QComboBox()
        self.personnel_combo.setEditable(True)
        form_layout.addRow("Personnel :", self.personnel_combo)

        # Type de déclaration
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "CongePaye",
            "RTT",
            "SansSolde",
            "Maladie",
            "AccidentTravail",
            "AccidentTrajet",
            "ArretTravail",
            "CongeNaissance",
            "Formation",
            "Autorisation",
            "Autre"
        ])
        form_layout.addRow("Type :", self.type_combo)

        # Date début
        self.date_debut_edit = QDateEdit()
        self.date_debut_edit.setDate(QDate.currentDate())
        self.date_debut_edit.setCalendarPopup(True)
        self.date_debut_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Date début :", self.date_debut_edit)

        # Date fin
        self.date_fin_edit = QDateEdit()
        self.date_fin_edit.setDate(QDate.currentDate())
        self.date_fin_edit.setCalendarPopup(True)
        self.date_fin_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Date fin :", self.date_fin_edit)

        # Motif
        self.motif_edit = QTextEdit()
        self.motif_edit.setPlaceholderText("Saisissez un motif optionnel...")
        self.motif_edit.setMaximumHeight(80)
        form_layout.addRow("Motif :", self.motif_edit)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Bouton de validation
        submit_btn = QPushButton("✅ Enregistrer la déclaration")
        submit_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        submit_btn.clicked.connect(self.submit_declaration)
        layout.addWidget(submit_btn)

        layout.addStretch()

        return widget

    def load_personnel_combo(self):
        """Charge la liste du personnel dans le combo."""
        try:
            rows = get_personnel_actif_liste()

            self.personnel_combo.clear()

            for r in rows:
                display = f"{r['nom']} {r['prenom']}"
                if r.get('matricule'):
                    display += f" ({r['matricule']})"
                self.personnel_combo.addItem(display, r['id'])

        except Exception as e:
            logger.exception(f"Erreur chargement personnel: {e}")
            show_error_message(self, "Erreur", "Impossible de charger le personnel", e)

    def submit_declaration(self):
        """Enregistre une nouvelle déclaration d'absence."""
        # Validation
        if self.personnel_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un membre du personnel.")
            return

        operateur_id = self.personnel_combo.currentData()
        type_decl = self.type_combo.currentText()
        date_debut = self.date_debut_edit.date().toPyDate()
        date_fin = self.date_fin_edit.date().toPyDate()
        motif = self.motif_edit.toPlainText().strip()

        # Vérifier cohérence des dates
        if date_fin < date_debut:
            QMessageBox.warning(self, "Attention", "La date de fin ne peut pas être antérieure à la date de début.")
            return

        try:
            new_id = creer_declaration(operateur_id, type_decl, date_debut, date_fin, motif)
            if new_id is None:
                raise RuntimeError("Échec de l'enregistrement")

            QMessageBox.information(
                self, "Succès",
                f"✅ Déclaration enregistrée avec succès !\n\n"
                f"Type : {type_decl}\n"
                f"Du {format_date(date_debut)} au {format_date(date_fin)}"
            )

            # Réinitialiser le formulaire
            self.date_debut_edit.setDate(QDate.currentDate())
            self.date_fin_edit.setDate(QDate.currentDate())
            self.motif_edit.clear()

            # Rafraîchir les données
            self.refresh_all()

        except Exception as e:
            logger.exception(f"Erreur enregistrement declaration: {e}")
            show_error_message(self, "Erreur", "Impossible d'enregistrer la déclaration", e)

    # ==================== ONGLET 3: CALENDRIER ====================

    def create_calendar_tab(self):
        """Crée l'onglet calendrier."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Split horizontal
        h_layout = QHBoxLayout()

        # Calendrier
        cal_group = QGroupBox("Calendrier des absences")
        cal_layout = QVBoxLayout()

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_calendar_date_clicked)
        cal_layout.addWidget(self.calendar)

        cal_group.setLayout(cal_layout)
        h_layout.addWidget(cal_group, 2)

        # Détails du jour sélectionné
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

        return widget

    def load_calendar_absences(self):
        """Charge les absences pour le mois affiché dans le calendrier et les marque."""
        try:
            # Récupérer le mois affiché
            current_date = self.calendar.selectedDate().toPyDate()
            first_day = date(current_date.year, current_date.month, 1)

            # Dernier jour du mois
            if current_date.month == 12:
                last_day = date(current_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(current_date.year, current_date.month + 1, 1) - timedelta(days=1)

            rows = get_absences_du_mois(first_day, last_day)

            # Réinitialiser le format
            default_format = QTextCharFormat()
            default_format.setBackground(QColor("white"))

            # Marquer les dates avec absences
            absence_format = QTextCharFormat()
            absence_format.setBackground(QColor("#fef3c7"))  # Jaune pâle
            absence_format.setForeground(QColor("#92400e"))  # Texte marron

            for r in rows:
                date_debut = r['date_debut']
                date_fin = r['date_fin']

                if isinstance(date_debut, str):
                    date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
                if isinstance(date_fin, str):
                    date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()

                # Marquer chaque jour de l'absence
                current = date_debut
                while current <= date_fin:
                    if first_day <= current <= last_day:
                        qdate = QDate(current.year, current.month, current.day)
                        self.calendar.setDateTextFormat(qdate, absence_format)
                    current += timedelta(days=1)

        except Exception as e:
            logger.error(f"Erreur lors du chargement du calendrier : {e}")

    def on_calendar_date_clicked(self, qdate):
        """Affiche les absences du jour sélectionné."""
        selected = qdate.toPyDate()
        self.selected_date_label.setText(f"📅 Absences du {format_date(selected)}")

        try:
            rows = get_absences_du_jour(selected)

            self.calendar_absents_list.clear()

            if not rows:
                item = QListWidgetItem("✅ Aucune absence ce jour")
                item.setForeground(QColor("#10b981"))
                self.calendar_absents_list.addItem(item)
            else:
                for r in rows:
                    nom = r['nom'] or ""
                    prenom = r['prenom'] or ""
                    type_decl = self.format_type_declaration(r['type_declaration'])
                    motif = r['motif'] or ""

                    text = f"{nom} {prenom} - {type_decl}"
                    if motif:
                        text += f" ({motif})"

                    item = QListWidgetItem(text)
                    item.setForeground(QColor(self.get_type_color(r['type_declaration'])))
                    self.calendar_absents_list.addItem(item)

        except Exception as e:
            logger.exception(f"Erreur chargement absences: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les absences", e)

    # ==================== ONGLET 4: CALENDRIER ÉVALUATIONS ====================

    def create_eval_calendar_tab(self):
        """Crée l'onglet calendrier des évaluations."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filtres en haut
        filters = QHBoxLayout()

        self.eval_search = QLineEdit()
        self.eval_search.setPlaceholderText("Rechercher opérateur (nom/prénom)...")
        self.eval_search.textChanged.connect(self.load_eval_calendar_data)
        filters.addWidget(self.eval_search, stretch=1)

        filters.addWidget(QLabel("Poste :"))
        self.eval_poste_filter = QComboBox()
        self.eval_poste_filter.addItem("(Tous)")
        self.eval_poste_filter.currentIndexChanged.connect(self.load_eval_calendar_data)
        filters.addWidget(self.eval_poste_filter)

        refresh_eval_btn = QPushButton("🔄 Actualiser")
        refresh_eval_btn.clicked.connect(self.load_eval_calendar_data)
        filters.addWidget(refresh_eval_btn)

        layout.addLayout(filters)

        # Split horizontal: Calendrier + Liste
        h_layout = QHBoxLayout()

        # Calendrier
        cal_group = QGroupBox("Calendrier des évaluations")
        cal_layout = QVBoxLayout()

        self.eval_calendar = QCalendarWidget()
        self.eval_calendar.setGridVisible(True)
        self.eval_calendar.clicked.connect(self.on_eval_calendar_date_clicked)
        self.eval_calendar.currentPageChanged.connect(self.load_eval_calendar_markings)

        # Forcer le rafraîchissement lors de l'affichage (fix scroll bug)
        self.eval_calendar.selectionChanged.connect(self.refresh_calendar_display)

        cal_layout.addWidget(self.eval_calendar)

        cal_group.setLayout(cal_layout)
        h_layout.addWidget(cal_group, 2)

        # Détails du jour sélectionné
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

        # Charger les postes dans le filtre
        self.load_eval_postes_filter()

        # Charger les données initiales
        self.load_eval_calendar_markings()

        return widget

    def load_eval_postes_filter(self):
        """Charge la liste des postes pour le filtre d'évaluations."""
        try:
            rows = get_postes_avec_polyvalences()

            self.eval_poste_filter.clear()
            self.eval_poste_filter.addItem("(Tous)", None)

            for r in rows:
                self.eval_poste_filter.addItem(r['poste_code'], r['id'])

        except Exception as e:
            logger.error(f"Erreur lors du chargement des postes : {e}")

    def load_eval_calendar_markings(self):
        """Marque les jours avec des évaluations prévues dans le calendrier."""
        try:
            # Utiliser le mois affiché, pas la date sélectionnée
            year = self.eval_calendar.yearShown()
            month = self.eval_calendar.monthShown()
            first_day = date(year, month, 1)

            # Dernier jour du mois
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)

            rows = get_evaluations_dates_du_mois(first_day, last_day)

            self.eval_dates_cache = set()
            for r in rows:
                eval_date = r['eval_date']
                if eval_date:
                    if isinstance(eval_date, str):
                        eval_date = datetime.strptime(eval_date, '%Y-%m-%d').date()
                    self.eval_dates_cache.add(eval_date)

            # Appliquer les formats
            self._apply_calendar_formats(first_day, last_day)

        except Exception as e:
            logger.error(f"Erreur lors du marquage du calendrier : {e}")


    def _apply_calendar_formats(self, first_day, last_day):
        """Applique les formats au calendrier (méthode séparée pour réutilisation)."""
        # Réinitialiser le format
        default_format = QTextCharFormat()
        default_format.setBackground(QColor("white"))

        # Appliquer le format par défaut à toutes les dates du mois
        current = first_day
        while current <= last_day:
            qdate = QDate(current.year, current.month, current.day)
            self.eval_calendar.setDateTextFormat(qdate, default_format)
            current += timedelta(days=1)

        # Marquer les dates avec évaluations
        eval_format = QTextCharFormat()
        eval_format.setBackground(QColor("#dbeafe"))  # Bleu pâle
        eval_format.setForeground(QColor("#1e40af"))  # Texte bleu foncé
        eval_format.setFontWeight(QFont.Bold)

        if hasattr(self, 'eval_dates_cache'):
            for eval_date in self.eval_dates_cache:
                qdate = QDate(eval_date.year, eval_date.month, eval_date.day)
                self.eval_calendar.setDateTextFormat(qdate, eval_format)

    def refresh_calendar_display(self):
        """Rafraîchit l'affichage du calendrier pour corriger le bug de scroll."""
        try:
            year = self.eval_calendar.yearShown()
            month = self.eval_calendar.monthShown()
            first_day = date(year, month, 1)
    
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)
    
            if hasattr(self, 'eval_dates_cache'):
                self._apply_calendar_formats(first_day, last_day)
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement du calendrier : {e}")


    def on_eval_calendar_date_clicked(self, qdate):
        """Affiche les évaluations du jour sélectionné."""
        selected = qdate.toPyDate()
        self.eval_selected_date_label.setText(f"📆 Évaluations du {format_date(selected)}")

        try:
            search_text = self.eval_search.text().lower()
            poste_id = self.eval_poste_filter.currentData()

            rows = get_evaluations_du_jour(selected, poste_id=poste_id)

            self.eval_calendar_list.clear()

            if not rows:
                item = QListWidgetItem("✅ Aucune évaluation prévue ce jour")
                item.setForeground(QColor("#10b981"))
                self.eval_calendar_list.addItem(item)
            else:
                for r in rows:
                    nom = r['nom'] or ""
                    prenom = r['prenom'] or ""
                    poste = r['poste_code'] or ""
                    niveau = r['niveau'] or "N/A"

                    # Filtrer par recherche
                    if search_text:
                        searchable = f"{nom} {prenom} {poste}".lower()
                        if search_text not in searchable:
                            continue

                    text = f"{nom} {prenom} - {poste} (Niveau {niveau})"

                    item = QListWidgetItem(text)
                    # Couleur selon niveau
                    if niveau == 1:
                        item.setForeground(QColor("#dc2626"))  # Rouge
                    elif niveau == 2:
                        item.setForeground(QColor("#d97706"))  # Orange
                    elif niveau == 3:
                        item.setForeground(QColor("#059669"))  # Vert
                    elif niveau == 4:
                        item.setForeground(QColor("#0369a1"))  # Bleu

                    self.eval_calendar_list.addItem(item)

        except Exception as e:
            logger.exception(f"Erreur chargement evaluations: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les évaluations", e)

    def load_eval_calendar_data(self):
        """Recharge les marquages et les données du calendrier d'évaluations."""
        self.load_eval_calendar_markings()
        if hasattr(self, 'eval_calendar'):
            selected = self.eval_calendar.selectedDate()
            self.on_eval_calendar_date_clicked(selected)

    # ==================== ONGLET 5: HISTORIQUE ====================

    def create_history_tab(self):
        """Crée l'onglet historique des déclarations."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filtres
        filter_group = QGroupBox("Filtres")
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Type :"))
        self.history_type_combo = QComboBox()
        self.history_type_combo.addItems([
            "Tous",
            "CongePaye",
            "RTT",
            "Maladie",
            "AccidentTravail",
            "ArretTravail",
            "Formation",
            "Autre"
        ])
        self.history_type_combo.currentIndexChanged.connect(self.load_history)
        filter_layout.addWidget(self.history_type_combo)

        filter_layout.addWidget(QLabel("Période :"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "30 derniers jours",
            "3 derniers mois",
            "6 derniers mois",
            "Cette année",
            "Tout"
        ])
        self.period_combo.currentIndexChanged.connect(self.load_history)
        filter_layout.addWidget(self.period_combo)

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Table historique
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

        # Boutons d'actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        delete_btn = QPushButton("🗑️ Supprimer")
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
        delete_btn.clicked.connect(self.delete_selected_declaration)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

        return widget

    def load_history(self):
        """Charge l'historique des déclarations."""
        try:
            # Construire la requête selon les filtres
            type_filter = self.history_type_combo.currentText()
            period = self.period_combo.currentText()

            rows = get_historique_declarations(type_filter=type_filter, period=period)

            self.history_table.setRowCount(0)

            for r in rows:
                row_pos = self.history_table.rowCount()
                self.history_table.insertRow(row_pos)

                # ID (caché)
                self.history_table.setItem(row_pos, 0, QTableWidgetItem(str(r['id'])))

                # Nom
                self.history_table.setItem(row_pos, 1, QTableWidgetItem(r['nom'] or ""))

                # Prénom
                self.history_table.setItem(row_pos, 2, QTableWidgetItem(r['prenom'] or ""))

                # Type
                type_item = QTableWidgetItem(self.format_type_declaration(r['type_declaration']))
                type_item.setForeground(QColor(self.get_type_color(r['type_declaration'])))
                self.history_table.setItem(row_pos, 3, type_item)

                # Date début
                date_debut = r['date_debut']
                if isinstance(date_debut, str):
                    date_debut_str = date_debut
                else:
                    date_debut_str = format_date(date_debut)
                self.history_table.setItem(row_pos, 4, QTableWidgetItem(date_debut_str))

                # Date fin
                date_fin = r['date_fin']
                if isinstance(date_fin, str):
                    date_fin_str = date_fin
                else:
                    date_fin_str = format_date(date_fin)
                self.history_table.setItem(row_pos, 5, QTableWidgetItem(date_fin_str))

                # Motif
                self.history_table.setItem(row_pos, 6, QTableWidgetItem(r['motif'] or ""))

        except Exception as e:
            logger.exception(f"Erreur chargement historique: {e}")
            show_error_message(self, "Erreur", "Impossible de charger l'historique", e)

    def delete_selected_declaration(self):
        """Supprime la déclaration sélectionnée."""
        selected = self.history_table.selectedItems()
        if not selected:
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

            QMessageBox.information(self, "Succès", "✅ Déclaration supprimée avec succès.")

            self.refresh_all()

        except Exception as e:
            logger.exception(f"Erreur suppression declaration: {e}")
            show_error_message(self, "Erreur", "Impossible de supprimer la déclaration", e)

    # ==================== ONGLET 5: DOCUMENTS EXPIRANT ====================

    def create_docs_expiration_tab(self):
        """Crée l'onglet des documents RH qui expirent bientôt."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Barre de filtres
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Horizon (jours) :"))
        self.docs_horizon_combo = QComboBox()
        self.docs_horizon_combo.addItems(["30", "60", "90"])
        self.docs_horizon_combo.currentIndexChanged.connect(self.load_docs_expiration)
        filter_row.addWidget(self.docs_horizon_combo)
        filter_row.addStretch()

        refresh_docs_btn = QPushButton("🔄 Actualiser")
        refresh_docs_btn.clicked.connect(self.load_docs_expiration)
        filter_row.addWidget(refresh_docs_btn)

        layout.addLayout(filter_row)

        # Table
        self.docs_expiration_table = QTableWidget()
        self.docs_expiration_table.setColumnCount(6)
        self.docs_expiration_table.setHorizontalHeaderLabels([
            "Nom", "Prénom", "Document", "Catégorie", "Date expiration", "Jours restants"
        ])
        hdr = self.docs_expiration_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.docs_expiration_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.docs_expiration_table.setAlternatingRowColors(True)
        self.docs_expiration_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Stocke personnel_id par ligne pour l'action
        self.docs_expiration_table.setProperty("personnel_ids", [])
        layout.addWidget(self.docs_expiration_table, 1)

        # Bouton ouvrir fiche RH
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        open_rh_btn = QPushButton("Voir dossier RH")
        open_rh_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        open_rh_btn.clicked.connect(self.open_rh_for_selected_doc)
        btn_row.addWidget(open_rh_btn)
        layout.addLayout(btn_row)

        return widget

    def load_docs_expiration(self):
        """Charge les documents expirant bientôt et les affiche."""
        try:
            jours = int(self.docs_horizon_combo.currentText())
            rows = get_documents_expirant(jours)

            self.docs_expiration_table.setRowCount(0)
            personnel_ids = []

            for r in rows:
                row_pos = self.docs_expiration_table.rowCount()
                self.docs_expiration_table.insertRow(row_pos)

                jours_restants = r.get('jours_restants') or 0

                # Couleur selon urgence
                if jours_restants <= 7:
                    bg = QColor("#fee2e2")   # rouge pâle
                    fg = QColor("#991b1b")
                elif jours_restants <= 30:
                    bg = QColor("#ffedd5")   # orange pâle
                    fg = QColor("#9a3412")
                else:
                    bg = QColor("#fef9c3")   # jaune pâle
                    fg = QColor("#713f12")

                def _item(text, background=bg, foreground=fg):
                    it = QTableWidgetItem(text)
                    it.setBackground(background)
                    it.setForeground(foreground)
                    return it

                self.docs_expiration_table.setItem(row_pos, 0, _item(r.get('nom') or ""))
                self.docs_expiration_table.setItem(row_pos, 1, _item(r.get('prenom') or ""))
                self.docs_expiration_table.setItem(row_pos, 2, _item(r.get('nom_document') or ""))
                self.docs_expiration_table.setItem(row_pos, 3, _item(r.get('categorie') or ""))

                date_exp = r.get('date_expiration')
                if date_exp and not isinstance(date_exp, str):
                    date_exp_str = format_date(date_exp)
                else:
                    date_exp_str = date_exp or ""
                self.docs_expiration_table.setItem(row_pos, 4, _item(date_exp_str))

                self.docs_expiration_table.setItem(row_pos, 5, _item(str(jours_restants) + " j"))

                personnel_ids.append(r.get('personnel_id'))

            self.docs_expiration_table.setProperty("personnel_ids", personnel_ids)

        except Exception as e:
            logger.exception(f"Erreur chargement documents expirant: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les documents expirant", e)

    def open_rh_for_selected_doc(self):
        """Ouvre le dossier RH de la personne sélectionnée dans la table documents."""
        row = self.docs_expiration_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un document dans la liste.")
            return

        personnel_ids = self.docs_expiration_table.property("personnel_ids") or []
        if row >= len(personnel_ids) or personnel_ids[row] is None:
            return

        personnel_id = personnel_ids[row]
        try:
            from core.gui.dialogs.gestion_rh import GestionRHDialog
            dlg = GestionRHDialog(parent=self, preselect_personnel_id=personnel_id)
            dlg.exec_()
        except Exception as e:
            logger.exception(f"Erreur ouverture dossier RH pour personnel {personnel_id}: {e}")
            show_error_message(self, "Erreur", "Impossible d'ouvrir le dossier RH", e)

    # ==================== HELPERS ====================

    def refresh_all(self):
        """Rafraîchit toutes les données."""
        self.load_absents_today()
        self.load_personnel_combo()
        self.load_calendar_absences()
        self.load_docs_expiration()
        self.load_history()

    def format_type_declaration(self, type_decl):
        """Formate le type de déclaration pour l'affichage."""
        formats = {
            'CongePaye': 'Congé Payé',
            'RTT': 'RTT',
            'SansSolde': 'Sans Solde',
            'Maladie': 'Maladie',
            'AccidentTravail': 'Accident Travail',
            'AccidentTrajet': 'Accident Trajet',
            'ArretTravail': 'Arrêt Travail',
            'CongeNaissance': 'Congé Naissance',
            'Formation': 'Formation',
            'Autorisation': 'Autorisation',
            'Autre': 'Autre'
        }
        return formats.get(type_decl, type_decl)

    def get_type_color(self, type_decl):
        """Retourne la couleur associée à un type de déclaration."""
        colors = {
            'CongePaye': '#10b981',
            'RTT': '#3b82f6',
            'SansSolde': '#6b7280',
            'Maladie': '#8b5cf6',
            'AccidentTravail': '#dc2626',
            'AccidentTrajet': '#dc2626',
            'ArretTravail': '#f59e0b',
            'CongeNaissance': '#ec4899',
            'Formation': '#06b6d4',
            'Autorisation': '#14b8a6',
            'Autre': '#64748b'
        }
        return colors.get(type_decl, '#6b7280')


# Test autonome
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = RegularisationDialog()
    dialog.show()
    sys.exit(app.exec_())
