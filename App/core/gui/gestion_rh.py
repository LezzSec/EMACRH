# -*- coding: utf-8 -*-
"""
Module de Gestion RH Complète - Interface Moderne et Épurée
Interface combinant calendriers d'évaluation, absences/congés, planning et contrats
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QWidget,
    QDateEdit, QComboBox, QTextEdit, QMessageBox, QHeaderView,
    QRadioButton, QButtonGroup, QGroupBox, QCalendarWidget,
    QScrollArea, QFrame, QListWidget, QListWidgetItem, QSplitter,
    QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon
from datetime import datetime, date, timedelta

from core.services import absence_service
from core.services import evaluation_service, calendrier_service
from core.services import formation_service
from core.db.configbd import get_connection
from core.gui.ui_theme import EmacCard, EmacButton


class GestionRHDialog(QDialog):
    """Dialogue principal de gestion RH complète"""

    data_changed = pyqtSignal()

    def __init__(self, personnel_id=None, parent=None):
        super().__init__(parent)
        self.personnel_id = personnel_id
        self.annee_courante = datetime.now().year

        self.setWindowTitle("Gestion RH - Interface Moderne")
        self.setGeometry(100, 100, 1500, 850)
        self.setModal(False)

        # Appliquer un style moderne
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: white;
                color: #64748b;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: #3b82f6;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #e2e8f0;
            }
        """)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialise l'interface moderne avec onglets"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # En-tête moderne avec icône
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title = QLabel("🏢 Gestion des Ressources Humaines")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #1e293b; padding: 10px 0;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Bouton d'aide
        btn_help = QPushButton("?")
        btn_help.setFixedSize(36, 36)
        btn_help.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border-radius: 18px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        btn_help.setToolTip("Aide et documentation")
        header_layout.addWidget(btn_help)

        layout.addLayout(header_layout)

        # Sous-titre avec info utilisateur
        subtitle = QLabel("Gérez vos évaluations, absences, congés et contrats")
        subtitle.setStyleSheet("color: #64748b; font-size: 13px; padding-bottom: 10px;")
        layout.addWidget(subtitle)

        # Onglets modernes
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)

        # Onglet 1: Vue d'ensemble (Dashboard)
        self.tab_dashboard = self.create_tab_dashboard_modern()
        self.tabs.addTab(self.tab_dashboard, "📊  Vue d'ensemble")

        # Onglet 2: Mes Évaluations
        self.tab_eval_calendar = self.create_tab_evaluations_modern()
        self.tabs.addTab(self.tab_eval_calendar, "📋  Mes Évaluations")

        # Onglet 3: Mes absences/congés
        self.tab_absences = self.create_tab_absences_modern()
        self.tabs.addTab(self.tab_absences, "🏖️  Absences & Congés")

        # Onglet 4: Planning d'équipe
        self.tab_planning = self.create_tab_planning_modern()
        self.tabs.addTab(self.tab_planning, "📆  Planning Équipe")

        # Onglet 5: Validation (si manager)
        self.tab_validation = self.create_tab_validation_modern()
        self.tabs.addTab(self.tab_validation, "✅  Validation")

        # Pied de page avec boutons
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        btn_refresh = EmacButton("🔄 Actualiser", variant='ghost')
        btn_refresh.clicked.connect(self.load_data)
        footer_layout.addWidget(btn_refresh)

        footer_layout.addStretch()

        btn_close = EmacButton("Fermer", variant='ghost')
        btn_close.clicked.connect(self.accept)
        footer_layout.addWidget(btn_close)

        layout.addLayout(footer_layout)

    def create_tab_dashboard_modern(self):
        """Onglet tableau de bord moderne avec vue d'ensemble"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Layout en grille pour les KPI cards
        grid = QGridLayout()
        grid.setSpacing(15)

        # KPI 1: Évaluations en retard (rouge)
        retard_card = self._create_kpi_card(
            "⚠️", "Évaluations en Retard",
            "0", "À réaliser d'urgence",
            "#ef4444", "#fef2f2"
        )
        self.retard_count_label = retard_card.findChild(QLabel, "value_label")
        self.retard_list_widget = QListWidget()
        self.retard_list_widget.setMaximumHeight(120)
        self.retard_list_widget.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #fee2e2;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #fef2f2;
            }
        """)
        retard_card.body.addWidget(self.retard_list_widget)

        btn_voir_retards = EmacButton("→ Voir tout", variant='ghost')
        btn_voir_retards.clicked.connect(lambda: self._ouvrir_gestion_evaluations("En retard"))
        retard_card.body.addWidget(btn_voir_retards)

        grid.addWidget(retard_card, 0, 0)

        # KPI 2: Prochaines évaluations (vert)
        next_card = self._create_kpi_card(
            "📅", "Prochaines Évaluations",
            "0", "30 prochains jours",
            "#10b981", "#f0fdf4"
        )
        self.next_count_label = next_card.findChild(QLabel, "value_label")
        self.next_eval_list_widget = QListWidget()
        self.next_eval_list_widget.setMaximumHeight(120)
        self.next_eval_list_widget.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #d1fae5;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f0fdf4;
            }
        """)
        next_card.body.addWidget(self.next_eval_list_widget)

        btn_voir_prochaines = EmacButton("→ Voir tout", variant='ghost')
        btn_voir_prochaines.clicked.connect(lambda: self._ouvrir_gestion_evaluations("À planifier (30j)"))
        next_card.body.addWidget(btn_voir_prochaines)

        grid.addWidget(next_card, 0, 1)

        # KPI 3: Mes soldes de congés (bleu)
        solde_card = self._create_kpi_card(
            "🏖️", "Mes Soldes de Congés",
            "", f"Année {self.annee_courante}",
            "#3b82f6", "#eff6ff"
        )

        solde_grid = QGridLayout()
        solde_grid.setSpacing(10)

        # CP
        cp_label = QLabel("Congés Payés")
        cp_label.setStyleSheet("font-weight: bold; color: #1e40af; font-size: 11px;")
        self.cp_value = QLabel("0 jours")
        self.cp_value.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.cp_value.setStyleSheet("color: #1e40af;")
        solde_grid.addWidget(cp_label, 0, 0)
        solde_grid.addWidget(self.cp_value, 1, 0)

        # RTT
        rtt_label = QLabel("RTT")
        rtt_label.setStyleSheet("font-weight: bold; color: #1e40af; font-size: 11px;")
        self.rtt_value = QLabel("0 jours")
        self.rtt_value.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.rtt_value.setStyleSheet("color: #1e40af;")
        solde_grid.addWidget(rtt_label, 0, 1)
        solde_grid.addWidget(self.rtt_value, 1, 1)

        solde_card.body.addLayout(solde_grid)
        grid.addWidget(solde_card, 1, 0)

        # KPI 4: Mes demandes récentes (violet)
        demandes_card = self._create_kpi_card(
            "📝", "Mes Demandes Récentes",
            "", "Dernières demandes d'absence",
            "#8b5cf6", "#f5f3ff"
        )

        self.demandes_list_widget = QListWidget()
        self.demandes_list_widget.setMaximumHeight(150)
        self.demandes_list_widget.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #e9d5ff;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f5f3ff;
            }
        """)
        demandes_card.body.addWidget(self.demandes_list_widget)

        btn_nouvelle = EmacButton("➕ Nouvelle Demande", variant='primary')
        btn_nouvelle.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        demandes_card.body.addWidget(btn_nouvelle)

        grid.addWidget(demandes_card, 1, 1)

        # KPI 5: Formations (cyan)
        formations_card = self._create_kpi_card(
            "🎓", "Formations",
            "0", "En cours cette année",
            "#06b6d4", "#ecfeff"
        )
        self.formations_count_label = formations_card.findChild(QLabel, "value_label")

        self.formations_list_widget = QListWidget()
        self.formations_list_widget.setMaximumHeight(100)
        self.formations_list_widget.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #a5f3fc;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #ecfeff;
            }
        """)
        formations_card.body.addWidget(self.formations_list_widget)

        btn_formations = EmacButton("→ Voir tout", variant='ghost')
        btn_formations.clicked.connect(self._ouvrir_gestion_formations)
        formations_card.body.addWidget(btn_formations)

        grid.addWidget(formations_card, 2, 0, 1, 2)  # Prend toute la largeur

        layout.addLayout(grid)

        # Note: on garde les références pour compatibilité
        self.retard_list = self.retard_list_widget
        self.next_eval_list = self.next_eval_list_widget
        self.demandes_list = self.demandes_list_widget

        return widget

    def _create_kpi_card(self, icon, title, value, subtitle, color, bg_color):
        """Crée une KPI card moderne"""
        card = EmacCard()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border-left: 4px solid {color};
            }}
        """)

        # En-tête avec icône
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 24))
        header.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title_label.setStyleSheet(f"color: {color};")
        title_layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #64748b; font-size: 10px;")
            title_layout.addWidget(subtitle_label)

        header.addLayout(title_layout)
        header.addStretch()
        card.body.addLayout(header)

        # Valeur principale
        if value:
            value_label = QLabel(value)
            value_label.setObjectName("value_label")
            value_label.setFont(QFont("Segoe UI", 32, QFont.Bold))
            value_label.setStyleSheet(f"color: {color};")
            value_label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(value_label)

        return card

    def create_tab_dashboard(self):
        """Ancienne méthode - redirige vers la nouvelle"""
        return self.create_tab_dashboard_modern()

    def create_tab_evaluations_modern(self):
        """Onglet évaluations moderne et épuré"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Colonne gauche: Évaluations
        left_col = QVBoxLayout()

        # Card: Évaluations en retard
        retard_card = self.create_info_card(
            "⚠️ Évaluations en Retard",
            "#e74c3c",
            "Évaluations devant être réalisées"
        )
        self.retard_count_label = QLabel("0")
        self.retard_count_label.setFont(QFont("Arial", 32, QFont.Bold))
        self.retard_count_label.setStyleSheet("color: white;")
        self.retard_count_label.setAlignment(Qt.AlignCenter)
        retard_card.layout().addWidget(self.retard_count_label)

        self.retard_list = QListWidget()
        self.retard_list.setMaximumHeight(180)
        self.retard_list.setStyleSheet("background-color: white;")
        retard_card.layout().addWidget(self.retard_list)

        # Bouton pour voir le détail des retards
        btn_voir_retards = QPushButton("→ Voir le récapitulatif complet")
        btn_voir_retards.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 5px 10px;
                text-align: left;
                font-size: 11px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #fce4e4;
            }
        """)
        btn_voir_retards.setCursor(Qt.PointingHandCursor)
        btn_voir_retards.clicked.connect(lambda: self._ouvrir_gestion_evaluations("En retard"))
        retard_card.layout().addWidget(btn_voir_retards)

        left_col.addWidget(retard_card)

        # Card: Prochaines évaluations
        next_card = self.create_info_card(
            "📅 Prochaines Évaluations",
            "#27ae60",
            "30 prochains jours"
        )
        self.next_count_label = QLabel("0")
        self.next_count_label.setFont(QFont("Arial", 32, QFont.Bold))
        self.next_count_label.setStyleSheet("color: white;")
        self.next_count_label.setAlignment(Qt.AlignCenter)
        next_card.layout().addWidget(self.next_count_label)

        self.next_eval_list = QListWidget()
        self.next_eval_list.setMaximumHeight(180)
        self.next_eval_list.setStyleSheet("background-color: white;")
        next_card.layout().addWidget(self.next_eval_list)

        # Bouton pour voir le détail des prochaines évaluations
        btn_voir_prochaines = QPushButton("→ Voir le récapitulatif complet")
        btn_voir_prochaines.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 5px 10px;
                text-align: left;
                font-size: 11px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #e8f8f0;
            }
        """)
        btn_voir_prochaines.setCursor(Qt.PointingHandCursor)
        btn_voir_prochaines.clicked.connect(lambda: self._ouvrir_gestion_evaluations("À planifier (30j)"))
        next_card.layout().addWidget(btn_voir_prochaines)

        left_col.addWidget(next_card)

        main_layout.addLayout(left_col)

        # Colonne droite: Absences et congés
        right_col = QVBoxLayout()

        # Card: Mes soldes de congés
        solde_card = self.create_info_card(
            "Mes Soldes de Congés",
            "#3498db",
            f"Année {self.annee_courante}"
        )

        solde_layout = QHBoxLayout()

        # CP
        cp_frame = QFrame()
        cp_layout = QVBoxLayout(cp_frame)
        cp_label = QLabel("Congés Payés")
        cp_label.setStyleSheet("color: white; font-weight: bold;")
        cp_layout.addWidget(cp_label)
        self.cp_value = QLabel("0")
        self.cp_value.setFont(QFont("Arial", 24, QFont.Bold))
        self.cp_value.setStyleSheet("color: white;")
        self.cp_value.setAlignment(Qt.AlignCenter)
        cp_layout.addWidget(self.cp_value)
        cp_subtitle = QLabel("jours restants")
        cp_subtitle.setStyleSheet("color: white;")
        cp_subtitle.setAlignment(Qt.AlignCenter)
        cp_layout.addWidget(cp_subtitle)
        solde_layout.addWidget(cp_frame)

        # RTT
        rtt_frame = QFrame()
        rtt_layout = QVBoxLayout(rtt_frame)
        rtt_label = QLabel("RTT")
        rtt_label.setStyleSheet("color: white; font-weight: bold;")
        rtt_layout.addWidget(rtt_label)
        self.rtt_value = QLabel("0")
        self.rtt_value.setFont(QFont("Arial", 24, QFont.Bold))
        self.rtt_value.setStyleSheet("color: white;")
        self.rtt_value.setAlignment(Qt.AlignCenter)
        rtt_layout.addWidget(self.rtt_value)
        rtt_subtitle = QLabel("jours restants")
        rtt_subtitle.setStyleSheet("color: white;")
        rtt_subtitle.setAlignment(Qt.AlignCenter)
        rtt_layout.addWidget(rtt_subtitle)
        solde_layout.addWidget(rtt_frame)

        solde_card.layout().addLayout(solde_layout)

        right_col.addWidget(solde_card)

        # Card: Mes demandes récentes
        demandes_card = self.create_info_card(
            "📝 Mes Demandes Récentes",
            "#9b59b6",
            "Dernières demandes d'absence"
        )

        self.demandes_list = QListWidget()
        self.demandes_list.setMaximumHeight(300)
        self.demandes_list.setStyleSheet("background-color: white;")
        demandes_card.layout().addWidget(self.demandes_list)

        btn_nouvelle = QPushButton("➕ Nouvelle Demande")
        btn_nouvelle.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #9b59b6;
                padding: 8px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        btn_nouvelle.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        demandes_card.layout().addWidget(btn_nouvelle)

        right_col.addWidget(demandes_card)

        main_layout.addLayout(right_col)

        layout.addLayout(main_layout)

        # Bouton refresh
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.load_dashboard_data)
        layout.addWidget(btn_refresh)

        return widget

    def _ouvrir_gestion_evaluations(self, filtre_statut):
        """Ouvre le dialogue de gestion des évaluations avec un filtre pré-appliqué"""
        try:
            from core.gui.gestion_evaluation import GestionEvaluationDialog

            dialog = GestionEvaluationDialog()

            # Appliquer le filtre de statut
            if hasattr(dialog, 'status_filter'):
                index = dialog.status_filter.findText(filtre_statut)
                if index >= 0:
                    dialog.status_filter.setCurrentIndex(index)

            dialog.exec_()

            # Recharger les données après fermeture
            self.load_data()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir la gestion des évaluations :\n{e}")

    def _ouvrir_gestion_formations(self):
        """Ouvre le dialogue de gestion des formations"""
        try:
            from core.gui.gestion_formations import GestionFormationsDialog
            dialog = GestionFormationsDialog(self)
            dialog.exec_()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir la gestion des formations :\n{e}")

    def create_info_card(self, title, color, subtitle=""):
        """Crée une card d'information colorée"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 13, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
            layout.addWidget(subtitle_label)

        return frame

        # Titre et filtres dans une card
        filter_card = EmacCard()

        title_row = QHBoxLayout()
        title = QLabel("📋 Mes Évaluations")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        title_row.addWidget(title)
        title_row.addStretch()
        filter_card.body.addLayout(title_row)

        # Filtres compacts
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        # Filtre poste
        filter_layout.addWidget(QLabel("📍 Poste:"))
        self.eval_poste_filter = QComboBox()
        self.eval_poste_filter.addItem("Tous les postes", "")
        self.eval_poste_filter.currentIndexChanged.connect(self.load_evaluations_calendar)
        self.eval_poste_filter.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: white;
                min-width: 150px;
            }
        """)
        filter_layout.addWidget(self.eval_poste_filter)

        filter_layout.addSpacing(20)

        # Filtre période
        filter_layout.addWidget(QLabel("⏰ Période:"))
        self.eval_periode_filter = QComboBox()
        self.eval_periode_filter.addItem("⚠️ En retard", "retard")
        self.eval_periode_filter.addItem("📅 30 prochains jours", "30j")
        self.eval_periode_filter.addItem("📆 90 prochains jours", "90j")
        self.eval_periode_filter.addItem("📊 Toutes", "all")
        self.eval_periode_filter.currentIndexChanged.connect(self.load_evaluations_calendar)
        self.eval_periode_filter.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: white;
                min-width: 180px;
            }
        """)
        filter_layout.addWidget(self.eval_periode_filter)

        filter_layout.addStretch()
        filter_card.body.addLayout(filter_layout)

        layout.addWidget(filter_card)

        # Table moderne des évaluations
        table_card = EmacCard()
        table_layout = QVBoxLayout()

        self.eval_table = QTableWidget()
        self.eval_table.setColumnCount(7)
        self.eval_table.setHorizontalHeaderLabels([
            "Opérateur", "Poste", "Atelier", "Niveau", "Dernière Éval.", "Prochaine Éval.", "Jours Restants"
        ])
        self.eval_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.eval_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.eval_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.eval_table.setAlternatingRowColors(True)
        self.eval_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8fafc;
                gridline-color: #e2e8f0;
                border: none;
                font-size: 11px;
            }
            QHeaderView::section {
                background: #f1f5f9;
                color: #475569;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f1f5f9;
            }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #1e293b;
            }
        """)
        table_layout.addWidget(self.eval_table)

        # Boutons d'action
        btn_layout = QHBoxLayout()
        btn_planifier = EmacButton("📅 Planifier Évaluation", variant='primary')
        btn_planifier.clicked.connect(self.planifier_evaluation)
        btn_layout.addWidget(btn_planifier)

        btn_export = EmacButton("📤 Exporter", variant='ghost')
        btn_layout.addWidget(btn_export)

        btn_layout.addStretch()
        table_layout.addLayout(btn_layout)

        table_card.body.addLayout(table_layout)
        layout.addWidget(table_card)

        return widget

    def create_tab_eval_calendar(self):
        """Ancienne méthode - redirige vers la nouvelle"""
        return self.create_tab_evaluations_modern()

    def create_tab_absences_modern(self):
        """Onglet absences moderne et simplifié"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Titre principal
        header_layout = QHBoxLayout()
        title = QLabel("🏖️ Absences & Congés")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Bouton nouvelle demande proéminent
        btn_nouvelle = EmacButton("➕ Nouvelle Demande", variant='primary')
        btn_nouvelle.clicked.connect(self._show_nouvelle_demande_dialog)
        btn_nouvelle.setMinimumHeight(40)
        header_layout.addWidget(btn_nouvelle)

        layout.addLayout(header_layout)

        # Layout horizontal: Mes soldes à gauche, Mes demandes à droite
        main_horizontal = QHBoxLayout()
        main_horizontal.setSpacing(15)

        # === GAUCHE: Mes Soldes ===
        soldes_card = EmacCard()
        soldes_layout = QVBoxLayout()

        soldes_title = QLabel("💳 Mes Soldes")
        soldes_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        soldes_title.setStyleSheet("color: #1e293b;")
        soldes_layout.addWidget(soldes_title)

        # Sélection année
        annee_layout = QHBoxLayout()
        annee_layout.addWidget(QLabel("Année:"))
        self.solde_annee_combo = QComboBox()
        annee = datetime.now().year
        for i in range(annee - 2, annee + 2):
            self.solde_annee_combo.addItem(str(i), i)
        self.solde_annee_combo.setCurrentText(str(annee))
        self.solde_annee_combo.currentIndexChanged.connect(self.load_soldes)
        self.solde_annee_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: white;
            }
        """)
        annee_layout.addWidget(self.solde_annee_combo)
        annee_layout.addStretch()
        soldes_layout.addLayout(annee_layout)

        # Cards des soldes (CP et RTT)
        soldes_grid = QHBoxLayout()
        soldes_grid.setSpacing(10)

        # CP Card
        self.cp_card = self._create_solde_mini_card("Congés Payés", "#10b981")
        soldes_grid.addWidget(self.cp_card)

        # RTT Card
        self.rtt_card = self._create_solde_mini_card("RTT", "#3b82f6")
        soldes_grid.addWidget(self.rtt_card)

        soldes_layout.addLayout(soldes_grid)

        # Détails
        self.solde_details_label = QLabel()
        self.solde_details_label.setWordWrap(True)
        self.solde_details_label.setStyleSheet("""
            QLabel {
                background: #f8fafc;
                padding: 12px;
                border-radius: 6px;
                font-size: 11px;
                color: #475569;
                border: 1px solid #e2e8f0;
            }
        """)
        soldes_layout.addWidget(self.solde_details_label)

        soldes_card.body.addLayout(soldes_layout)
        main_horizontal.addWidget(soldes_card, 1)

        # === DROITE: Mes Demandes ===
        demandes_card = EmacCard()
        demandes_layout = QVBoxLayout()

        demandes_title = QLabel("📝 Mes Demandes")
        demandes_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        demandes_title.setStyleSheet("color: #1e293b;")
        demandes_layout.addWidget(demandes_title)

        # Filtres
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("Année:"))
        self.annee_filter = QComboBox()
        for i in range(annee - 2, annee + 2):
            self.annee_filter.addItem(str(i), i)
        self.annee_filter.setCurrentText(str(annee))
        self.annee_filter.currentIndexChanged.connect(self.load_mes_demandes)
        self.annee_filter.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: white;
            }
        """)
        filter_row.addWidget(self.annee_filter)

        filter_row.addSpacing(10)

        filter_row.addWidget(QLabel("Statut:"))
        self.statut_filter = QComboBox()
        self.statut_filter.addItem("Tous", None)
        self.statut_filter.addItem("⏳ En attente", "EN_ATTENTE")
        self.statut_filter.addItem("✅ Validées", "VALIDEE")
        self.statut_filter.addItem("❌ Refusées", "REFUSEE")
        self.statut_filter.currentIndexChanged.connect(self.load_mes_demandes)
        self.statut_filter.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: white;
            }
        """)
        filter_row.addWidget(self.statut_filter)

        filter_row.addStretch()
        demandes_layout.addLayout(filter_row)

        # Table des demandes
        self.table_demandes = QTableWidget()
        self.table_demandes.setColumnCount(9)
        self.table_demandes.setHorizontalHeaderLabels([
            "ID", "Type", "Début", "Fin", "Nb jours", "Motif", "Statut", "Validateur", "Date valid."
        ])
        self.table_demandes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_demandes.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_demandes.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_demandes.setAlternatingRowColors(True)
        self.table_demandes.setColumnHidden(0, True)  # Cacher l'ID
        self.table_demandes.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8fafc;
                gridline-color: #e2e8f0;
                border: none;
                font-size: 11px;
            }
            QHeaderView::section {
                background: #f1f5f9;
                color: #475569;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f5f9;
            }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #1e293b;
            }
        """)
        demandes_layout.addWidget(self.table_demandes)

        # Bouton annuler
        btn_cancel = EmacButton("🗑️ Annuler la demande", variant='ghost')
        btn_cancel.clicked.connect(self.annuler_demande)
        demandes_layout.addWidget(btn_cancel)

        demandes_card.body.addLayout(demandes_layout)
        main_horizontal.addWidget(demandes_card, 2)

        layout.addLayout(main_horizontal)

        return widget

    def _create_solde_mini_card(self, titre, couleur):
        """Crée une mini card pour afficher un solde"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {couleur}, stop:1 {self._darken_color(couleur)});
                border-radius: 10px;
                padding: 15px;
                min-height: 120px;
            }}
        """)

        layout = QVBoxLayout(frame)

        title_label = QLabel(titre)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(title_label)

        layout.addStretch()

        value_label = QLabel("0")
        value_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        value_label.setStyleSheet("color: white; background: transparent;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        subtitle_label = QLabel("jours restants")
        subtitle_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 10px; background: transparent;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)

        # Stocker les labels pour mise à jour
        if "CP" in titre or "Congés" in titre:
            self.cp_value_label = value_label
        else:
            self.rtt_value_label = value_label

        return frame

    def _darken_color(self, hex_color):
        """Assombrit une couleur hexadécimale"""
        color_map = {
            "#10b981": "#059669",
            "#3b82f6": "#2563eb",
            "#ef4444": "#dc2626",
            "#8b5cf6": "#7c3aed",
        }
        return color_map.get(hex_color, hex_color)

    def _show_nouvelle_demande_dialog(self):
        """Affiche un dialogue pour créer une nouvelle demande"""
        from core.gui.gestion_absences import NouvelleDemandeDialog
        dialog = NouvelleDemandeDialog(self.personnel_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_mes_demandes()
            self.load_soldes()
            self.load_dashboard_data()
            self.data_changed.emit()

    def create_tab_absences(self):
        """Ancienne méthode - redirige vers la nouvelle"""
        return self.create_tab_absences_modern()

    def create_subtab_mes_demandes(self):
        """Sous-onglet listant les demandes du personnel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filtres
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Année:"))
        self.annee_filter = QComboBox()
        annee = datetime.now().year
        for i in range(annee - 2, annee + 2):
            self.annee_filter.addItem(str(i), i)
        self.annee_filter.setCurrentText(str(annee))
        self.annee_filter.currentIndexChanged.connect(self.load_mes_demandes)
        filter_layout.addWidget(self.annee_filter)

        filter_layout.addWidget(QLabel("Statut:"))
        self.statut_filter = QComboBox()
        self.statut_filter.addItem("Tous", None)
        self.statut_filter.addItem("En attente", "EN_ATTENTE")
        self.statut_filter.addItem("Validées", "VALIDEE")
        self.statut_filter.addItem("Refusées", "REFUSEE")
        self.statut_filter.currentIndexChanged.connect(self.load_mes_demandes)
        filter_layout.addWidget(self.statut_filter)

        filter_layout.addStretch()

        btn_refresh = QPushButton("Actualiser")
        btn_refresh.clicked.connect(self.load_mes_demandes)
        filter_layout.addWidget(btn_refresh)

        layout.addLayout(filter_layout)

        # Table des demandes
        self.table_demandes = QTableWidget()
        self.table_demandes.setColumnCount(9)
        self.table_demandes.setHorizontalHeaderLabels([
            "ID", "Type", "Début", "Fin", "Nb jours", "Motif", "Statut", "Validateur", "Date valid."
        ])
        self.table_demandes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_demandes.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_demandes.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_demandes)

        # Boutons d'action
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Annuler la demande")
        btn_cancel.clicked.connect(self.annuler_demande)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def create_subtab_nouvelle_demande(self):
        """Sous-onglet de création d'une nouvelle demande"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Formulaire
        form = QGroupBox("Nouvelle demande d'absence")
        form_layout = QVBoxLayout()

        # Type d'absence
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type d'absence:"))
        self.type_combo = QComboBox()
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        form_layout.addLayout(type_layout)

        # Dates
        dates_layout = QHBoxLayout()

        # Date début
        debut_group = QVBoxLayout()
        debut_group.addWidget(QLabel("Date de début:"))
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.dateChanged.connect(self.update_nb_jours)
        debut_group.addWidget(self.date_debut)

        # Demi-journée début
        self.demi_debut_group = QButtonGroup()
        demi_debut_layout = QHBoxLayout()
        self.demi_debut_journee = QRadioButton("Journée")
        self.demi_debut_matin = QRadioButton("Matin")
        self.demi_debut_aprem = QRadioButton("Après-midi")
        self.demi_debut_journee.setChecked(True)
        self.demi_debut_group.addButton(self.demi_debut_journee, 0)
        self.demi_debut_group.addButton(self.demi_debut_matin, 1)
        self.demi_debut_group.addButton(self.demi_debut_aprem, 2)
        self.demi_debut_group.buttonClicked.connect(self.update_nb_jours)
        demi_debut_layout.addWidget(self.demi_debut_journee)
        demi_debut_layout.addWidget(self.demi_debut_matin)
        demi_debut_layout.addWidget(self.demi_debut_aprem)
        debut_group.addLayout(demi_debut_layout)

        dates_layout.addLayout(debut_group)

        # Date fin
        fin_group = QVBoxLayout()
        fin_group.addWidget(QLabel("Date de fin:"))
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.dateChanged.connect(self.update_nb_jours)
        fin_group.addWidget(self.date_fin)

        # Demi-journée fin
        self.demi_fin_group = QButtonGroup()
        demi_fin_layout = QHBoxLayout()
        self.demi_fin_journee = QRadioButton("Journée")
        self.demi_fin_matin = QRadioButton("Matin")
        self.demi_fin_aprem = QRadioButton("Après-midi")
        self.demi_fin_journee.setChecked(True)
        self.demi_fin_group.addButton(self.demi_fin_journee, 0)
        self.demi_fin_group.addButton(self.demi_fin_matin, 1)
        self.demi_fin_group.addButton(self.demi_fin_aprem, 2)
        self.demi_fin_group.buttonClicked.connect(self.update_nb_jours)
        demi_fin_layout.addWidget(self.demi_fin_journee)
        demi_fin_layout.addWidget(self.demi_fin_matin)
        demi_fin_layout.addWidget(self.demi_fin_aprem)
        fin_group.addLayout(demi_fin_layout)

        dates_layout.addLayout(fin_group)

        form_layout.addLayout(dates_layout)

        # Nombre de jours calculé
        nb_jours_layout = QHBoxLayout()
        nb_jours_layout.addWidget(QLabel("Nombre de jours ouvrés:"))
        self.nb_jours_label = QLabel("0")
        self.nb_jours_label.setFont(QFont("Arial", 12, QFont.Bold))
        nb_jours_layout.addWidget(self.nb_jours_label)
        nb_jours_layout.addStretch()
        form_layout.addLayout(nb_jours_layout)

        # Motif
        form_layout.addWidget(QLabel("Motif (optionnel):"))
        self.motif_text = QTextEdit()
        self.motif_text.setMaximumHeight(80)
        form_layout.addWidget(self.motif_text)

        form.setLayout(form_layout)
        layout.addWidget(form)

        # Bouton soumettre
        btn_soumettre = QPushButton("Soumettre la demande")
        btn_soumettre.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_soumettre.clicked.connect(self.soumettre_demande)
        layout.addWidget(btn_soumettre)

        layout.addStretch()

        return widget

    def create_subtab_mes_soldes(self):
        """Sous-onglet affichage des soldes de congés"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Sélection année
        annee_layout = QHBoxLayout()
        annee_layout.addWidget(QLabel("Année:"))
        self.solde_annee_combo = QComboBox()
        annee = datetime.now().year
        for i in range(annee - 2, annee + 2):
            self.solde_annee_combo.addItem(str(i), i)
        self.solde_annee_combo.setCurrentText(str(annee))
        self.solde_annee_combo.currentIndexChanged.connect(self.load_soldes)
        annee_layout.addWidget(self.solde_annee_combo)
        annee_layout.addStretch()
        layout.addLayout(annee_layout)

        # Cards de soldes
        soldes_layout = QHBoxLayout()

        # Card CP
        self.cp_card = self.create_solde_card("Congés Payés", "#27ae60")
        soldes_layout.addWidget(self.cp_card)

        # Card RTT
        self.rtt_card = self.create_solde_card("RTT", "#3498db")
        soldes_layout.addWidget(self.rtt_card)

        layout.addLayout(soldes_layout)

        # Détails
        details_group = QGroupBox("Détails")
        details_layout = QVBoxLayout()
        self.solde_details_label = QLabel()
        self.solde_details_label.setWordWrap(True)
        details_layout.addWidget(self.solde_details_label)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        layout.addStretch()

        return widget

    def create_solde_card(self, titre, couleur):
        """Crée une card pour afficher un solde"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {couleur};
                border-radius: 10px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(frame)

        title_label = QLabel(titre)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        layout.addWidget(title_label)

        value_label = QLabel("0")
        value_label.setFont(QFont("Arial", 24, QFont.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        subtitle_label = QLabel("jours restants")
        subtitle_label.setStyleSheet("color: white;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)

        # Stocker les labels pour mise à jour
        if "CP" in titre or "Congés" in titre:
            self.cp_value_label = value_label
        else:
            self.rtt_value_label = value_label

        return frame

    def create_tab_planning_modern(self):
        """Onglet planning d'équipe moderne"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Titre
        title = QLabel("📆 Planning d'Équipe")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        layout.addWidget(title)

        # Layout horizontal: Calendrier + Détails
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)

        # Card calendrier
        calendar_card = EmacCard()
        calendar_layout = QVBoxLayout()

        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.afficher_absences_jour)
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background: white;
                border-radius: 8px;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #f8fafc;
            }
            QCalendarWidget QToolButton {
                background: #3b82f6;
                color: white;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QCalendarWidget QToolButton:hover {
                background: #2563eb;
            }
            QCalendarWidget QAbstractItemView:enabled {
                selection-background-color: #3b82f6;
                selection-color: white;
            }
        """)
        calendar_layout.addWidget(self.calendar)
        calendar_card.body.addLayout(calendar_layout)

        main_layout.addWidget(calendar_card, 2)

        # Card détails du jour
        details_card = EmacCard()
        details_layout = QVBoxLayout()

        details_title = QLabel("📋 Absences du jour sélectionné")
        details_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        details_title.setStyleSheet("color: #1e293b;")
        details_layout.addWidget(details_title)

        self.absences_jour_list = QTableWidget()
        self.absences_jour_list.setColumnCount(4)
        self.absences_jour_list.setHorizontalHeaderLabels(["Nom", "Type", "Du", "Au"])
        self.absences_jour_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.absences_jour_list.setAlternatingRowColors(True)
        self.absences_jour_list.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8fafc;
                gridline-color: #e2e8f0;
                border: none;
                font-size: 11px;
            }
            QHeaderView::section {
                background: #f1f5f9;
                color: #475569;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f5f9;
            }
        """)
        details_layout.addWidget(self.absences_jour_list)

        details_card.body.addLayout(details_layout)
        main_layout.addWidget(details_card, 3)

        layout.addLayout(main_layout)

        return widget

    def create_tab_planning(self):
        """Ancienne méthode - redirige vers la nouvelle"""
        return self.create_tab_planning_modern()

    def create_tab_validation(self):
        """Onglet de validation des demandes (pour managers)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Demandes en attente de validation:"))

        # Table des demandes à valider
        self.table_validation = QTableWidget()
        self.table_validation.setColumnCount(7)
        self.table_validation.setHorizontalHeaderLabels([
            "ID", "Personnel", "Type", "Du", "Au", "Nb jours", "Motif"
        ])
        self.table_validation.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_validation)

        # Boutons de validation
        btn_layout = QHBoxLayout()
        btn_valider = QPushButton("Valider")
        btn_valider.setStyleSheet("background-color: #27ae60; color: white; padding: 8px;")
        btn_valider.clicked.connect(lambda: self.valider_demande_selectionnee(True))
        btn_layout.addWidget(btn_valider)

        btn_refuser = QPushButton("Refuser")
        btn_refuser.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px;")
        btn_refuser.clicked.connect(lambda: self.valider_demande_selectionnee(False))
        btn_layout.addWidget(btn_refuser)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    # Méthodes de chargement des données
    def load_data(self):
        """Charge toutes les données"""
        self.load_postes_filter()
        self.load_dashboard_data()
        self.load_types_absence()
        self.load_mes_demandes()
        self.load_soldes()
        self.load_demandes_validation()

    def load_postes_filter(self):
        """Charge les postes pour le filtre"""
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        try:
            cur.execute("""
                SELECT DISTINCT p.id, p.poste_code, a.nom as atelier
                FROM postes p
                LEFT JOIN atelier a ON p.atelier_id = a.id
                ORDER BY a.nom, p.poste_code
            """)

            postes = cur.fetchall()
            self.eval_poste_filter.clear()
            self.eval_poste_filter.addItem("Tous les postes", "")

            for poste in postes:
                label = f"{poste['poste_code']} - {poste['atelier']}"
                self.eval_poste_filter.addItem(label, poste['id'])

        finally:
            cur.close()
            conn.close()

    def load_dashboard_data(self):
        """Charge les données du tableau de bord"""
        self.load_retard_evaluations()
        self.load_next_evaluations()
        self.load_soldes_dashboard()
        self.load_demandes_recentes()
        self.load_formations_dashboard()

    def load_retard_evaluations(self):
        """Charge les évaluations en retard"""
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        try:
            cur.execute("""
                SELECT
                    CONCAT(o.prenom, ' ', o.nom) as operateur,
                    p.poste_code as poste,
                    a.nom as atelier,
                    poly.niveau,
                    poly.prochaine_evaluation,
                    DATEDIFF(CURDATE(), poly.prochaine_evaluation) as jours_retard
                FROM polyvalence poly
                JOIN personnel o ON poly.operateur_id = o.id
                JOIN postes p ON poly.poste_id = p.id
                LEFT JOIN atelier a ON p.atelier_id = a.id
                WHERE o.statut = 'ACTIF'
                AND poly.prochaine_evaluation < CURDATE()
                ORDER BY jours_retard DESC
                LIMIT 10
            """)

            evaluations = cur.fetchall()
            self.retard_count_label.setText(str(len(evaluations)))
            self.retard_list.clear()

            for ev in evaluations:
                item_text = f"{ev['operateur']} - {ev['poste']} ({ev['atelier']}) - Retard: {ev['jours_retard']} jours"
                item = QListWidgetItem(item_text)
                item.setForeground(QColor("#e74c3c"))
                self.retard_list.addItem(item)

        finally:
            cur.close()
            conn.close()

    def load_next_evaluations(self):
        """Charge les prochaines évaluations"""
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        try:
            cur.execute("""
                SELECT
                    CONCAT(o.prenom, ' ', o.nom) as operateur,
                    p.poste_code as poste,
                    a.nom as atelier,
                    poly.niveau,
                    poly.prochaine_evaluation,
                    DATEDIFF(poly.prochaine_evaluation, CURDATE()) as jours_restants
                FROM polyvalence poly
                JOIN personnel o ON poly.operateur_id = o.id
                JOIN postes p ON poly.poste_id = p.id
                LEFT JOIN atelier a ON p.atelier_id = a.id
                WHERE o.statut = 'ACTIF'
                AND poly.prochaine_evaluation >= CURDATE()
                AND poly.prochaine_evaluation <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                ORDER BY poly.prochaine_evaluation ASC
                LIMIT 10
            """)

            evaluations = cur.fetchall()
            self.next_count_label.setText(str(len(evaluations)))
            self.next_eval_list.clear()

            for ev in evaluations:
                item_text = f"{ev['operateur']} - {ev['poste']} ({ev['atelier']}) - Dans {ev['jours_restants']} jours"
                item = QListWidgetItem(item_text)
                item.setForeground(QColor("#27ae60"))
                self.next_eval_list.addItem(item)

        finally:
            cur.close()
            conn.close()

    def load_soldes_dashboard(self):
        """Charge les soldes pour le dashboard"""
        if not self.personnel_id:
            return

        try:
            solde = absence_service.get_solde_conges(self.personnel_id, self.annee_courante)
            self.cp_value.setText(str(solde['cp_restant']))
            self.rtt_value.setText(str(solde['rtt_restant']))
        except:
            self.cp_value.setText("N/A")
            self.rtt_value.setText("N/A")

    def load_demandes_recentes(self):
        """Charge les demandes récentes"""
        if not self.personnel_id:
            return

        try:
            demandes = absence_service.get_demandes_personnel(self.personnel_id, self.annee_courante, None)
            self.demandes_list.clear()

            for demande in demandes[:5]:  # Limiter à 5
                status_color = {
                    'EN_ATTENTE': '#f39c12',
                    'VALIDEE': '#27ae60',
                    'REFUSEE': '#e74c3c',
                    'ANNULEE': '#95a5a6'
                }.get(demande['statut'], '#000000')

                item_text = f"{demande['type_libelle']} - {demande['date_debut'].strftime('%d/%m')} au {demande['date_fin'].strftime('%d/%m')} - {demande['statut']}"
                item = QListWidgetItem(item_text)
                item.setForeground(QColor(status_color))
                self.demandes_list.addItem(item)
        except:
            pass

    def load_formations_dashboard(self):
        """Charge les formations pour le dashboard"""
        try:
            stats = formation_service.get_formations_stats()

            # Mettre à jour le compteur
            if hasattr(self, 'formations_count_label') and self.formations_count_label:
                self.formations_count_label.setText(str(stats.get('en_cours', 0)))

            # Charger les formations récentes
            if hasattr(self, 'formations_list_widget'):
                self.formations_list_widget.clear()
                formations = formation_service.get_all_formations(statut='En cours')

                for f in formations[:5]:
                    item_text = f"{f.get('nom_complet', '')} - {f.get('intitule', '')}"
                    item = QListWidgetItem(item_text)
                    item.setForeground(QColor("#06b6d4"))
                    self.formations_list_widget.addItem(item)

                # Si pas de formations en cours, afficher les planifiées
                if not formations:
                    formations = formation_service.get_all_formations(statut='Planifiée')
                    for f in formations[:3]:
                        item_text = f"{f.get('nom_complet', '')} - {f.get('intitule', '')} (planifiée)"
                        item = QListWidgetItem(item_text)
                        item.setForeground(QColor("#64748b"))
                        self.formations_list_widget.addItem(item)
        except Exception as e:
            print(f"Erreur load_formations_dashboard: {e}")

    def load_evaluations_calendar(self):
        """Charge les évaluations dans le calendrier"""
        poste_id = self.eval_poste_filter.currentData()
        periode = self.eval_periode_filter.currentData()

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        try:
            # Construire la requête selon le filtre
            query = """
                SELECT
                    CONCAT(o.prenom, ' ', o.nom) as operateur,
                    p.poste_code as poste,
                    a.nom as atelier,
                    poly.niveau,
                    poly.date_evaluation,
                    poly.prochaine_evaluation,
                    DATEDIFF(poly.prochaine_evaluation, CURDATE()) as jours_restants
                FROM polyvalence poly
                JOIN personnel o ON poly.operateur_id = o.id
                JOIN postes p ON poly.poste_id = p.id
                LEFT JOIN atelier a ON p.atelier_id = a.id
                WHERE o.statut = 'ACTIF'
            """

            params = []

            if poste_id:
                query += " AND p.id = %s"
                params.append(poste_id)

            if periode == 'retard':
                query += " AND poly.prochaine_evaluation < CURDATE()"
            elif periode == '30j':
                query += " AND poly.prochaine_evaluation >= CURDATE() AND poly.prochaine_evaluation <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)"
            elif periode == '90j':
                query += " AND poly.prochaine_evaluation >= CURDATE() AND poly.prochaine_evaluation <= DATE_ADD(CURDATE(), INTERVAL 90 DAY)"

            query += " ORDER BY poly.prochaine_evaluation ASC"

            cur.execute(query, params)
            evaluations = cur.fetchall()

            self.eval_table.setRowCount(len(evaluations))

            for row, ev in enumerate(evaluations):
                self.eval_table.setItem(row, 0, QTableWidgetItem(ev['operateur']))
                self.eval_table.setItem(row, 1, QTableWidgetItem(ev['poste']))
                self.eval_table.setItem(row, 2, QTableWidgetItem(ev['atelier'] or ''))
                self.eval_table.setItem(row, 3, QTableWidgetItem(str(ev['niveau'])))
                self.eval_table.setItem(row, 4, QTableWidgetItem(ev['date_evaluation'].strftime('%d/%m/%Y') if ev['date_evaluation'] else ''))
                self.eval_table.setItem(row, 5, QTableWidgetItem(ev['prochaine_evaluation'].strftime('%d/%m/%Y') if ev['prochaine_evaluation'] else ''))
                self.eval_table.setItem(row, 6, QTableWidgetItem(str(ev['jours_restants'])))

                # Colorer selon le retard
                if ev['jours_restants'] < 0:
                    for col in range(7):
                        self.eval_table.item(row, col).setBackground(QColor(231, 76, 60, 50))
                elif ev['jours_restants'] <= 30:
                    for col in range(7):
                        self.eval_table.item(row, col).setBackground(QColor(243, 156, 18, 50))

        finally:
            cur.close()
            conn.close()

    def load_types_absence(self):
        """Charge les types d'absence"""
        try:
            types = absence_service.get_types_absence()
            self.type_combo.clear()
            for t in types:
                self.type_combo.addItem(f"{t['libelle']} ({t['code']})", t['code'])
        except:
            pass

    def load_mes_demandes(self):
        """Charge les demandes du personnel connecté"""
        if not self.personnel_id:
            return

        try:
            annee = self.annee_filter.currentData()
            statut = self.statut_filter.currentData()

            demandes = absence_service.get_demandes_personnel(self.personnel_id, annee, statut)

            self.table_demandes.setRowCount(len(demandes))

            for row, demande in enumerate(demandes):
                self.table_demandes.setItem(row, 0, QTableWidgetItem(str(demande['id'])))
                self.table_demandes.setItem(row, 1, QTableWidgetItem(demande['type_libelle']))
                self.table_demandes.setItem(row, 2, QTableWidgetItem(demande['date_debut'].strftime('%d/%m/%Y')))
                self.table_demandes.setItem(row, 3, QTableWidgetItem(demande['date_fin'].strftime('%d/%m/%Y')))
                self.table_demandes.setItem(row, 4, QTableWidgetItem(str(demande['nb_jours'])))
                self.table_demandes.setItem(row, 5, QTableWidgetItem(demande['motif'] or ''))
                self.table_demandes.setItem(row, 6, QTableWidgetItem(demande['statut']))
                self.table_demandes.setItem(row, 7, QTableWidgetItem(demande['validateur'] or ''))
                date_val = demande['date_validation'].strftime('%d/%m/%Y %H:%M') if demande['date_validation'] else ''
                self.table_demandes.setItem(row, 8, QTableWidgetItem(date_val))

                # Colorer selon le statut
                if demande['statut'] == 'VALIDEE':
                    for col in range(9):
                        self.table_demandes.item(row, col).setBackground(QColor(39, 174, 96, 50))
                elif demande['statut'] == 'REFUSEE':
                    for col in range(9):
                        self.table_demandes.item(row, col).setBackground(QColor(231, 76, 60, 50))
        except Exception as e:
            print(f"Erreur chargement demandes: {e}")

    def load_soldes(self):
        """Charge les soldes de congés"""
        if not self.personnel_id:
            return

        try:
            annee = self.solde_annee_combo.currentData()
            solde = absence_service.get_solde_conges(self.personnel_id, annee)

            # Mettre à jour les cards
            self.cp_value_label.setText(str(solde['cp_restant']))
            self.rtt_value_label.setText(str(solde['rtt_restant']))

            # Détails
            details = f"""
            <b>Congés Payés:</b><br>
            - Acquis: {solde['cp_acquis']} jours<br>
            - Reportés N-1: {solde['cp_n_1']} jours<br>
            - Pris: {solde['cp_pris']} jours<br>
            - <b>Restant: {solde['cp_restant']} jours</b><br><br>

            <b>RTT:</b><br>
            - Acquis: {solde['rtt_acquis']} jours<br>
            - Pris: {solde['rtt_pris']} jours<br>
            - <b>Restant: {solde['rtt_restant']} jours</b>
            """
            self.solde_details_label.setText(details)
        except Exception as e:
            print(f"Erreur chargement soldes: {e}")

    def load_demandes_validation(self):
        """Charge les demandes en attente de validation"""
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        try:
            cur.execute("""
                SELECT
                    da.id,
                    CONCAT(p.prenom, ' ', p.nom) as nom_complet,
                    ta.libelle as type_libelle,
                    da.date_debut,
                    da.date_fin,
                    da.nb_jours,
                    da.motif
                FROM demande_absence da
                JOIN personnel p ON da.personnel_id = p.id
                JOIN type_absence ta ON da.type_absence_id = ta.id
                WHERE da.statut = 'EN_ATTENTE'
                AND p.statut = 'ACTIF'
                ORDER BY da.date_creation ASC
            """)

            demandes = cur.fetchall()
            self.table_validation.setRowCount(len(demandes))

            for row, demande in enumerate(demandes):
                self.table_validation.setItem(row, 0, QTableWidgetItem(str(demande['id'])))
                self.table_validation.setItem(row, 1, QTableWidgetItem(demande['nom_complet']))
                self.table_validation.setItem(row, 2, QTableWidgetItem(demande['type_libelle']))
                self.table_validation.setItem(row, 3, QTableWidgetItem(demande['date_debut'].strftime('%d/%m/%Y')))
                self.table_validation.setItem(row, 4, QTableWidgetItem(demande['date_fin'].strftime('%d/%m/%Y')))
                self.table_validation.setItem(row, 5, QTableWidgetItem(str(demande['nb_jours'])))
                self.table_validation.setItem(row, 6, QTableWidgetItem(demande['motif'] or ''))

        except Exception as e:
            print(f"Erreur chargement validation: {e}")
        finally:
            cur.close()
            conn.close()

    # Méthodes d'action
    def update_nb_jours(self):
        """Calcule et affiche le nombre de jours ouvrés"""
        try:
            date_debut = self.date_debut.date().toPyDate()
            date_fin = self.date_fin.date().toPyDate()

            # Récupérer les demi-journées
            demi_debut = self.get_demi_journee(self.demi_debut_group)
            demi_fin = self.get_demi_journee(self.demi_fin_group)

            nb_jours = absence_service.calculer_jours_ouvres(
                date_debut, date_fin, demi_debut, demi_fin
            )

            self.nb_jours_label.setText(str(nb_jours))
        except:
            self.nb_jours_label.setText("0")

    def get_demi_journee(self, button_group):
        """Retourne le type de demi-journée sélectionné"""
        button_id = button_group.checkedId()
        if button_id == 0:
            return 'JOURNEE'
        elif button_id == 1:
            return 'MATIN'
        else:
            return 'APRES_MIDI'

    def soumettre_demande(self):
        """Soumet une nouvelle demande d'absence"""
        if not self.personnel_id:
            QMessageBox.warning(self, "Erreur", "Personnel non identifié")
            return

        type_code = self.type_combo.currentData()
        date_debut = self.date_debut.date().toPyDate()
        date_fin = self.date_fin.date().toPyDate()
        demi_debut = self.get_demi_journee(self.demi_debut_group)
        demi_fin = self.get_demi_journee(self.demi_fin_group)
        motif = self.motif_text.toPlainText()

        try:
            demande_id = absence_service.creer_demande_absence(
                self.personnel_id, type_code, date_debut, date_fin,
                demi_debut, demi_fin, motif
            )

            QMessageBox.information(
                self,
                "Succès",
                f"Demande créée avec succès (ID: {demande_id})\n\n"
                f"Nombre de jours: {self.nb_jours_label.text()}\n"
                f"Statut: En attente de validation"
            )

            # Réinitialiser le formulaire
            self.motif_text.clear()
            self.load_mes_demandes()
            self.load_dashboard_data()

            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de créer la demande:\n{str(e)}")

    def annuler_demande(self):
        """Annule une demande sélectionnée"""
        selected = self.table_demandes.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une demande")
            return

        row = selected[0].row()
        demande_id = int(self.table_demandes.item(row, 0).text())
        statut = self.table_demandes.item(row, 6).text()

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
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("UPDATE demande_absence SET statut = 'ANNULEE' WHERE id = %s", (demande_id,))
                conn.commit()
                cur.close()
                conn.close()

                QMessageBox.information(self, "Succès", "Demande annulée")
                self.load_mes_demandes()
                self.load_dashboard_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")

    def valider_demande_selectionnee(self, valide):
        """Valide ou refuse une demande"""
        selected = self.table_validation.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une demande")
            return

        row = selected[0].row()
        demande_id = int(self.table_validation.item(row, 0).text())

        action = "valider" if valide else "refuser"
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment {action} cette demande ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # TODO: Récupérer l'ID du validateur (personnel connecté)
                validateur_id = 1  # À remplacer par l'ID réel

                absence_service.valider_demande(demande_id, validateur_id, valide)

                msg = "validée" if valide else "refusée"
                QMessageBox.information(self, "Succès", f"Demande {msg}")

                self.load_demandes_validation()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")

    def afficher_absences_jour(self, date):
        """Affiche les absences pour un jour donné"""
        # TODO: Implémenter l'affichage des absences du jour
        pass

    def planifier_evaluation(self):
        """Ouvre la gestion des évaluations"""
        QMessageBox.information(self, "Info", "Ouverture de la gestion des évaluations...")
        # TODO: Intégrer avec GestionEvaluationDialog


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Test avec le premier personnel actif
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM personnel WHERE statut = 'ACTIF' LIMIT 1")
    result = cur.fetchone()
    personnel_id = result[0] if result else None
    cur.close()
    conn.close()

    dialog = GestionRHDialog(personnel_id=personnel_id)
    dialog.show()

    sys.exit(app.exec_())
