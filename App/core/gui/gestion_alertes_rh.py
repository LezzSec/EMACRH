# -*- coding: utf-8 -*-
"""
Gestion des Alertes RH - Dialog principal

Ce module fournit une interface centralisée pour visualiser et gérer
toutes les alertes RH (contrats, personnel).
"""

import logging
from datetime import date
from typing import List, Set, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QComboBox,
    QLineEdit, QCheckBox, QAbstractItemView, QFileDialog, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont

from core.services.alert_service import AlertService, TypeAlerte
from core.models import Alert
from core.services.permission_manager import can

logger = logging.getLogger(__name__)

# Import du thème et des composants
try:
    from core.gui.emac_ui_kit import add_custom_title_bar, show_error_message
    from core.gui.db_worker import DbWorker, DbThreadPool
    THEME_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Theme components not available: {e}")
    THEME_AVAILABLE = False
    show_error_message = None


# ===========================
# Styles communs
# ===========================

FILTER_INPUT_STYLE = """
    QLineEdit, QComboBox {
        background: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 13px;
        color: #374151;
    }
    QLineEdit:focus, QComboBox:focus {
        border-color: #3b82f6;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: white;
        border: 1px solid #d1d5db;
        selection-background-color: #3b82f6;
        selection-color: white;
    }
"""

FILTER_LABEL_STYLE = """
    QLabel {
        color: #6b7280;
        font-size: 13px;
    }
"""

CHECKBOX_STYLE = """
    QCheckBox {
        color: #6b7280;
        font-size: 13px;
    }
"""


# ===========================
# Onglet de base pour alertes
# ===========================

class AlertTabBase(QWidget):
    """Widget de base pour un onglet d'alertes."""

    row_double_clicked = pyqtSignal(int, dict)
    data_changed = pyqtSignal()

    def __init__(self, columns: List[str], parent=None):
        super().__init__(parent)
        self.columns = columns
        self._alerts: List[Alert] = []
        self._handled_ids: Set[str] = set()
        self._show_handled = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        # Barre de filtres
        self.filter_bar = self._create_filter_bar()
        layout.addWidget(self.filter_bar)

        # Cartes résumé
        self.summary_frame = self._create_summary_frame()
        layout.addWidget(self.summary_frame)

        # Table des alertes
        self.table = self._create_table()
        layout.addWidget(self.table, 1)

        # Placeholder amélioré
        self.empty_placeholder = self._create_empty_placeholder()
        self.empty_placeholder.hide()
        layout.addWidget(self.empty_placeholder)

    def _create_empty_placeholder(self) -> QWidget:
        """Cree un placeholder pour l'etat vide."""
        label = QLabel("Aucune alerte a afficher")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #9ca3af; font-size: 14px; padding: 40px;")
        return label

    def _create_filter_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(FILTER_INPUT_STYLE + FILTER_LABEL_STYLE + CHECKBOX_STYLE)

        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(12)

        lbl_urgence = QLabel("Urgence:")
        bar_layout.addWidget(lbl_urgence)

        self.urgency_filter = QComboBox()
        self.urgency_filter.addItems(["Toutes", "Critique", "Avertissement", "Info"])
        self.urgency_values = ["", "CRITIQUE", "AVERTISSEMENT", "INFO"]
        self.urgency_filter.currentIndexChanged.connect(self._apply_filters)
        self.urgency_filter.setMinimumWidth(130)
        self.urgency_filter.setFixedHeight(32)
        bar_layout.addWidget(self.urgency_filter)

        bar_layout.addSpacing(8)

        lbl_recherche = QLabel("Recherche:")
        bar_layout.addWidget(lbl_recherche)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom, prenom...")
        self.search_input.textChanged.connect(self._apply_filters)
        self.search_input.setMinimumWidth(200)
        self.search_input.setFixedHeight(32)
        bar_layout.addWidget(self.search_input)

        bar_layout.addStretch()

        self.show_handled_cb = QCheckBox("Afficher masques")
        self.show_handled_cb.stateChanged.connect(self._on_show_handled_changed)
        bar_layout.addWidget(self.show_handled_cb)

        return bar

    def _create_summary_frame(self) -> QWidget:
        frame = QWidget()
        frame.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.card_critique = self._create_summary_card("Critiques", "0", "#dc2626")
        layout.addWidget(self.card_critique)

        self.card_avert = self._create_summary_card("Avertissements", "0", "#f59e0b")
        layout.addWidget(self.card_avert)

        self.card_info = self._create_summary_card("Infos", "0", "#3b82f6")
        layout.addWidget(self.card_info)

        layout.addStretch()
        return frame

    def _create_summary_card(self, title: str, value: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(150, 70)
        card.setStyleSheet(f"""
            QFrame {{
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-left: 3px solid {accent_color};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            color: #6b7280;
            font-size: 12px;
            font-weight: 500;
            border: none;
            background: transparent;
        """)
        layout.addWidget(title_lbl)

        value_lbl = QLabel(value)
        value_lbl.setObjectName("value_label")
        value_lbl.setStyleSheet("""
            color: #1f2937;
            font-size: 24px;
            font-weight: 700;
            border: none;
            background: transparent;
        """)
        layout.addWidget(value_lbl)

        return card

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(self.columns) + 1)
        table.setHorizontalHeaderLabels(self.columns + ["Actions"])

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(len(self.columns), QHeaderView.ResizeToContents)

        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.doubleClicked.connect(self._on_table_double_click)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(48)

        table.setStyleSheet("""
            QTableWidget {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                gridline-color: #f3f4f6;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 6px 10px;
                border-bottom: 1px solid #f3f4f6;
            }
            QTableWidget::item:selected {
                background: #3b82f6;
                color: white;
            }
            QHeaderView::section {
                background: #f9fafb;
                color: #374151;
                padding: 10px 8px;
                border: none;
                border-bottom: 1px solid #e5e7eb;
                font-weight: 600;
                font-size: 12px;
            }
        """)
        return table

    def set_alerts(self, alerts: List[Alert]):
        self._alerts = alerts
        self._apply_filters()
        self._update_summary()

    def _apply_filters(self):
        idx = self.urgency_filter.currentIndex()
        urgency = self.urgency_values[idx] if idx < len(self.urgency_values) else ""
        search = self.search_input.text().lower().strip()

        filtered = []
        for alert in self._alerts:
            alert_key = f"{alert.categorie}_{alert.type_alerte}_{alert.id}"
            if alert_key in self._handled_ids and not self._show_handled:
                continue
            if urgency and alert.urgence != urgency:
                continue
            if search:
                searchable = f"{alert.personnel_nom} {alert.personnel_prenom}".lower()
                if search not in searchable:
                    continue
            filtered.append(alert)
        self._display_alerts(filtered)

    def _display_alerts(self, alerts: List[Alert]):
        self.table.setRowCount(0)
        if not alerts:
            self.table.hide()
            self.empty_placeholder.show()
            return

        self.empty_placeholder.hide()
        self.table.show()
        self.table.setRowCount(len(alerts))

        for row, alert in enumerate(alerts):
            self._populate_row(row, alert)

    def _populate_row(self, row: int, alert: Alert):
        pass

    def _add_action_buttons(self, row: int, alert: Alert):
        """Ajoute les boutons d'action."""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # Bouton Voir
        btn_view = QPushButton("Voir")
        btn_view.setCursor(Qt.PointingHandCursor)
        btn_view.setFixedSize(60, 28)
        btn_view.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border-radius: 4px;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        btn_view.clicked.connect(lambda checked, a=alert: self._on_view_click(a))
        layout.addWidget(btn_view)

        # Bouton Masquer/Afficher
        alert_key = f"{alert.categorie}_{alert.type_alerte}_{alert.id}"
        is_handled = alert_key in self._handled_ids

        btn_handle = QPushButton("Afficher" if is_handled else "Masquer")
        btn_handle.setCursor(Qt.PointingHandCursor)
        btn_handle.setFixedSize(70, 28)

        if is_handled:
            btn_handle.setStyleSheet("""
                QPushButton {
                    background: #10b981;
                    color: white;
                    border-radius: 4px;
                    border: none;
                    font-size: 12px;
                }
                QPushButton:hover { background: #059669; }
            """)
        else:
            btn_handle.setStyleSheet("""
                QPushButton {
                    background: #6b7280;
                    color: white;
                    border-radius: 4px;
                    border: none;
                    font-size: 12px;
                }
                QPushButton:hover { background: #4b5563; }
            """)

        btn_handle.clicked.connect(lambda checked, a=alert: self._toggle_handled(a))
        layout.addWidget(btn_handle)

        layout.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row, len(self.columns), widget)

    def _update_summary(self):
        critiques = len([a for a in self._alerts if a.urgence == "CRITIQUE"])
        avertissements = len([a for a in self._alerts if a.urgence == "AVERTISSEMENT"])
        infos = len([a for a in self._alerts if a.urgence == "INFO"])

        self.card_critique.findChild(QLabel, "value_label").setText(str(critiques))
        self.card_avert.findChild(QLabel, "value_label").setText(str(avertissements))
        self.card_info.findChild(QLabel, "value_label").setText(str(infos))

    def _on_table_double_click(self, index):
        row = index.row()
        visible_alerts = self.get_visible_alerts()
        if 0 <= row < len(visible_alerts):
            self._on_view_click(visible_alerts[row])

    def _on_view_click(self, alert: Alert):
        self.row_double_clicked.emit(alert.id, alert.to_dict())

    def _toggle_handled(self, alert: Alert):
        alert_key = f"{alert.categorie}_{alert.type_alerte}_{alert.id}"
        if alert_key in self._handled_ids:
            self._handled_ids.discard(alert_key)
        else:
            self._handled_ids.add(alert_key)
        self._apply_filters()
        self.data_changed.emit()

    def _on_show_handled_changed(self, state):
        self._show_handled = state == Qt.Checked
        self._apply_filters()

    def get_visible_alerts(self) -> List[Alert]:
        idx = self.urgency_filter.currentIndex()
        urgency = self.urgency_values[idx] if idx < len(self.urgency_values) else ""
        search = self.search_input.text().lower().strip()

        filtered = []
        for alert in self._alerts:
            alert_key = f"{alert.categorie}_{alert.type_alerte}_{alert.id}"
            if alert_key in self._handled_ids and not self._show_handled:
                continue
            if urgency and alert.urgence != urgency:
                continue
            if search:
                searchable = f"{alert.personnel_nom} {alert.personnel_prenom}".lower()
                if search not in searchable:
                    continue
            filtered.append(alert)
        return filtered


# ===========================
# Onglet Contrats
# ===========================

class ContratsAlertTab(AlertTabBase):
    def __init__(self, parent=None):
        columns = ["Nom", "Prenom", "Type", "Echeance", "Jours restants", "Urgence"]
        super().__init__(columns, parent)

    def _create_filter_bar(self) -> QWidget:
        bar = super()._create_filter_bar()
        layout = bar.layout()

        type_label = QLabel("Type:")
        self.type_filter = QComboBox()
        self.type_filter.addItems(["Tous", "CDI", "CDD", "INTERIM", "ALTERNANCE"])
        self.type_values = ["", "CDI", "CDD", "INTERIM", "ALTERNANCE"]
        self.type_filter.currentIndexChanged.connect(self._apply_filters)
        self.type_filter.setMinimumWidth(120)
        self.type_filter.setFixedHeight(36)

        layout.insertWidget(5, type_label)
        layout.insertWidget(6, self.type_filter)
        return bar

    def _apply_filters(self):
        super()._apply_filters()
        
        idx_urg = self.urgency_filter.currentIndex()
        urgency = self.urgency_values[idx_urg] if idx_urg < len(self.urgency_values) else ""
        idx_type = self.type_filter.currentIndex()
        type_contrat = self.type_values[idx_type] if idx_type < len(self.type_values) else ""
        search = self.search_input.text().lower().strip()

        filtered = []
        for alert in self._alerts:
            alert_key = f"{alert.categorie}_{alert.type_alerte}_{alert.id}"
            if alert_key in self._handled_ids and not self._show_handled: continue
            if urgency and alert.urgence != urgency: continue
            if search:
                if search not in f"{alert.personnel_nom} {alert.personnel_prenom}".lower(): continue
            if type_contrat and alert.data.get('type_contrat') != type_contrat:
                 if alert.type_alerte != TypeAlerte.PERSONNEL_SANS_CONTRAT: continue
            
            filtered.append(alert)
        self._display_alerts(filtered)

    def _populate_row(self, row: int, alert: Alert):
        self.table.setItem(row, 0, QTableWidgetItem(alert.personnel_nom or ""))
        self.table.setItem(row, 1, QTableWidgetItem(alert.personnel_prenom or ""))
        
        type_c = alert.data.get('type_contrat')
        item_type = QTableWidgetItem(type_c if type_c else "-")
        item_type.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 2, item_type)

        date_txt = alert.date_echeance.strftime('%d/%m/%Y') if alert.date_echeance else "-"
        item_date = QTableWidgetItem(date_txt)
        item_date.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 3, item_date)

        jours_txt = "-"
        if alert.jours_restants is not None:
            if alert.jours_restants < 0: days = f"{abs(alert.jours_restants)}j expiré"
            elif alert.jours_restants == 0: days = "Aujourd'hui"
            else: days = f"{alert.jours_restants}j"
            jours_txt = days
        
        item_jours = QTableWidgetItem(jours_txt)
        item_jours.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 4, item_jours)

        # Gestion des couleurs d'urgence
        colors = {
            'CRITIQUE': {'fg': '#991b1b', 'bg': '#fee2e2', 'label': 'Critique'},
            'AVERTISSEMENT': {'fg': '#92400e', 'bg': '#fef3c7', 'label': 'Avertissement'},
            'INFO': {'fg': '#1e40af', 'bg': '#dbeafe', 'label': 'Info'},
        }.get(alert.urgence, {})
        
        item_urg = QTableWidgetItem(colors.get('label', alert.urgence))
        item_urg.setTextAlignment(Qt.AlignCenter)
        item_urg.setForeground(QColor(colors.get('fg', '#000')))
        item_urg.setBackground(QColor(colors.get('bg', '#fff')))
        font = QFont()
        font.setBold(True)
        item_urg.setFont(font)
        self.table.setItem(row, 5, item_urg)

        self._add_action_buttons(row, alert)


# ===========================
# Onglet Personnel
# ===========================

class PersonnelAlertTab(AlertTabBase):
    def __init__(self, parent=None):
        columns = ["Nom", "Prenom", "Matricule", "Type alerte", "Detail", "Urgence"]
        super().__init__(columns, parent)

    def _create_filter_bar(self) -> QWidget:
        bar = super()._create_filter_bar()
        layout = bar.layout()

        type_label = QLabel("Type:")
        layout.insertWidget(5, type_label)

        self.alert_type_filter = QComboBox()
        self.alert_type_filter.addItem("Tous", "")
        self.alert_type_filter.addItem("Sans contrat", TypeAlerte.PERSONNEL_SANS_CONTRAT)
        self.alert_type_filter.addItem("Sans competences", TypeAlerte.PERSONNEL_SANS_COMPETENCES)
        self.alert_type_filter.addItem("Nouveau arrivant", TypeAlerte.PERSONNEL_NOUVEAU_SANS_AFFECTATION)
        self.alert_type_filter.currentIndexChanged.connect(self._apply_filters)
        self.alert_type_filter.setMinimumWidth(160)
        self.alert_type_filter.setFixedHeight(36)
        layout.insertWidget(6, self.alert_type_filter)

        return bar

    def _apply_filters(self):
        idx_urg = self.urgency_filter.currentIndex()
        urgency = self.urgency_values[idx_urg] if idx_urg < len(self.urgency_values) else ""
        alert_type = self.alert_type_filter.currentData()
        search = self.search_input.text().lower().strip()

        filtered = []
        for alert in self._alerts:
            alert_key = f"{alert.categorie}_{alert.type_alerte}_{alert.id}"
            if alert_key in self._handled_ids and not self._show_handled: continue
            if urgency and alert.urgence != urgency: continue
            if alert_type and alert.type_alerte != alert_type: continue
            if search:
                if search not in f"{alert.personnel_nom} {alert.personnel_prenom}".lower(): continue
            filtered.append(alert)
        self._display_alerts(filtered)

    def _populate_row(self, row: int, alert: Alert):
        self.table.setItem(row, 0, QTableWidgetItem(alert.personnel_nom or ""))
        self.table.setItem(row, 1, QTableWidgetItem(alert.personnel_prenom or ""))
        
        mat = alert.data.get('matricule')
        item_mat = QTableWidgetItem(mat if mat else "-")
        item_mat.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 2, item_mat)

        type_map = {
            TypeAlerte.PERSONNEL_SANS_CONTRAT: "Sans contrat",
            TypeAlerte.PERSONNEL_SANS_COMPETENCES: "Sans compétences",
            TypeAlerte.PERSONNEL_NOUVEAU_SANS_AFFECTATION: "Nouveau arrivant"
        }
        self.table.setItem(row, 3, QTableWidgetItem(type_map.get(alert.type_alerte, alert.type_alerte)))
        self.table.setItem(row, 4, QTableWidgetItem(alert.description))

        colors = {
            'CRITIQUE': {'fg': '#991b1b', 'bg': '#fee2e2', 'label': 'Critique'},
            'AVERTISSEMENT': {'fg': '#92400e', 'bg': '#fef3c7', 'label': 'Avertissement'},
            'INFO': {'fg': '#1e40af', 'bg': '#dbeafe', 'label': 'Info'},
        }.get(alert.urgence, {})

        item_urg = QTableWidgetItem(colors.get('label', alert.urgence))
        item_urg.setTextAlignment(Qt.AlignCenter)
        item_urg.setForeground(QColor(colors.get('fg', '#000')))
        item_urg.setBackground(QColor(colors.get('bg', '#fff')))
        font = QFont()
        font.setBold(True)
        item_urg.setFont(font)
        self.table.setItem(row, 5, item_urg)

        self._add_action_buttons(row, alert)


# ===========================
# Dialog Principal
# ===========================

class GestionAlertesRHDialog(QDialog):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Alertes RH")
        self.resize(1150, 750)
        self._setup_ui()
        self._check_permissions()
        QTimer.singleShot(100, self._load_data_async)

    def _setup_ui(self):
        if THEME_AVAILABLE:
            add_custom_title_bar(self, "Gestion des Alertes RH")

        # Style global du dialog
        self.setStyleSheet("QDialog { background: #f9fafb; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 20)
        main_layout.setSpacing(18)

        self.global_summary = self._create_global_summary()
        main_layout.addWidget(self.global_summary)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                background: #ffffff;
                top: -1px;
            }
            QTabBar::tab {
                background: #f3f4f6;
                color: #6b7280;
                padding: 10px 24px;
                border: 1px solid #e5e7eb;
                border-bottom: none;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 13px;
            }
            QTabBar::tab:hover:!selected {
                background: #e5e7eb;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #1f2937;
                font-weight: 600;
            }
        """)

        self.tab_contrats = ContratsAlertTab()
        self.tab_contrats.row_double_clicked.connect(self._on_view_contract_detail)
        self.tab_contrats.data_changed.connect(self._on_tab_data_changed)
        self.tabs.addTab(self.tab_contrats, "Contrats")

        self.tab_personnel = PersonnelAlertTab()
        self.tab_personnel.row_double_clicked.connect(self._on_view_personnel_detail)
        self.tab_personnel.data_changed.connect(self._on_tab_data_changed)
        self.tabs.addTab(self.tab_personnel, "Personnel")

        main_layout.addWidget(self.tabs, 1)

        btn_bar = self._create_button_bar()
        main_layout.addWidget(btn_bar)

    def _create_global_summary(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("HeaderBanner")
        frame.setStyleSheet("""
            #HeaderBanner {
                background: #1e293b;
                border-radius: 8px;
            }
            #HeaderBanner QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
            }
        """)
        frame.setFixedHeight(70)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(0)

        title = QLabel("Alertes RH")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        layout.addStretch()

        def create_stat(label, value_attr):
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            l = QHBoxLayout(container)
            l.setContentsMargins(20, 0, 20, 0)
            l.setSpacing(8)

            lbl_txt = QLabel(label)
            lbl_txt.setStyleSheet("color: #94a3b8; font-size: 13px;")
            l.addWidget(lbl_txt)

            lbl_val = QLabel("0")
            lbl_val.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 700;")
            setattr(self, value_attr, lbl_val)
            l.addWidget(lbl_val)

            return container

        layout.addWidget(create_stat("Critiques:", "lbl_critiques"))
        layout.addWidget(create_stat("Avertissements:", "lbl_avertissements"))
        layout.addWidget(create_stat("Infos:", "lbl_infos"))

        return frame

    def _create_button_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        # Bouton Export PDF
        btn_export = QPushButton("Exporter PDF")
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.setFixedHeight(36)
        btn_export.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                padding: 0 20px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background: #059669; }
        """)
        btn_export.clicked.connect(self._export_pdf)
        layout.addWidget(btn_export)

        layout.addStretch()

        # Bouton Actualiser
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setFixedHeight(36)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 0 20px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        btn_refresh.clicked.connect(self._load_data_async)
        layout.addWidget(btn_refresh)

        # Bouton Fermer
        btn_close = QPushButton("Fermer")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setFixedHeight(36)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                padding: 0 20px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #e5e7eb;
            }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        return bar

    def _check_permissions(self):
        can_view_contrats = can('rh.contrats.view')
        can_view_personnel = can('rh.personnel.view')

        if not can_view_contrats: self.tabs.setTabEnabled(0, False)
        if not can_view_personnel: self.tabs.setTabEnabled(1, False)

        if not can_view_contrats and not can_view_personnel:
            QMessageBox.warning(self, "Accès refusé", "Permissions insuffisantes.")
            QTimer.singleShot(0, self.reject)

    def _load_data_async(self):
        if THEME_AVAILABLE:
            worker = DbWorker(self._fetch_all_alerts)
            worker.signals.result.connect(self._on_data_loaded)
            worker.signals.error.connect(self._on_load_error)
            DbThreadPool.start(worker)
        else:
            try:
                self._on_data_loaded(self._fetch_all_alerts())
            except Exception as e:
                self._on_load_error(str(e))

    def _fetch_all_alerts(self, progress_callback=None):
        return {
            'contrats': AlertService.get_all_contract_alerts(),
            'personnel': AlertService.get_all_personnel_alerts(),
            'stats': AlertService.get_quick_counts()
        }

    def _on_data_loaded(self, data):
        self.tab_contrats.set_alerts(data['contrats'])
        self.tab_personnel.set_alerts(data['personnel'])
        stats = data['stats']
        self.lbl_critiques.setText(str(stats['critiques']))
        self.lbl_avertissements.setText(str(stats['avertissements']))
        self.lbl_infos.setText(str(stats['infos']))

    def _on_load_error(self, error_msg):
        logger.error(f"Erreur chargement alertes: {error_msg}")
        if show_error_message:
            show_error_message(self, "Erreur", "Impossible de charger les alertes", Exception(error_msg))
        else:
            QMessageBox.critical(self, "Erreur", error_msg)

    def _on_tab_data_changed(self):
        self.data_changed.emit()

    def _on_view_contract_detail(self, alert_id: int, alert_data: dict):
        """Ouvre la fenetre de gestion des contrats pour l'operateur."""
        pid = alert_data.get('personnel_id')
        if pid:
            try:
                from core.gui.contract_management import ContractManagementDialog
                dialog = ContractManagementDialog(parent=self, operateur_id=pid)
                dialog.data_changed.connect(self._load_data_async)
                dialog.exec_()
            except ImportError as e:
                logger.error(f"Erreur import ContractManagementDialog: {e}")
                QMessageBox.information(self, "Info", f"Contrat pour ID {pid}")

    def _on_view_personnel_detail(self, alert_id: int, alert_data: dict):
        """Ouvre la fenetre de details du personnel."""
        pid = alert_data.get('personnel_id')
        if pid:
            try:
                from core.gui.gestion_personnel import DetailOperateurDialog
                dialog = DetailOperateurDialog(
                    pid,
                    alert_data.get('personnel_nom', ''),
                    alert_data.get('personnel_prenom', ''),
                    'ACTIF',
                    parent=self
                )
                dialog.exec_()
            except ImportError as e:
                logger.error(f"Erreur import DetailOperateurDialog: {e}")
                QMessageBox.information(self, "Info", f"Detail ID {pid}")

    def _export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet

            file_path, _ = QFileDialog.getSaveFileName(self, "Exporter PDF", f"alertes_{date.today()}.pdf", "PDF Files (*.pdf)")
            if not file_path: return

            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
            elements = []
            styles = getSampleStyleSheet()

            elements.append(Paragraph(f"Rapport Alertes RH - {date.today()}", styles['Title']))
            elements.append(Spacer(1, 20))

            idx = self.tabs.currentIndex()
            tab_obj = self.tab_contrats if idx == 0 else self.tab_personnel
            alerts = tab_obj.get_visible_alerts()
            
            headers = ["Nom", "Prénom", "Info", "Détail", "Urgence"]
            data = [headers]
            
            for a in alerts:
                if idx == 0:
                    info = a.data.get('type_contrat', '-')
                    detail = f"Fin: {a.date_echeance} ({a.jours_restants}j)"
                else:
                    info = a.data.get('matricule', '-')
                    detail = a.description
                
                data.append([
                    a.personnel_nom, 
                    a.personnel_prenom, 
                    info, 
                    detail, 
                    a.urgence
                ])

            if len(data) > 1:
                t = Table(data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 1, colors.black)
                ]))
                elements.append(t)
            else:
                elements.append(Paragraph("Aucune donnée", styles['Normal']))

            doc.build(elements)
            QMessageBox.information(self, "Succès", "Export terminé")

        except Exception as e:
            QMessageBox.critical(self, "Erreur Export", str(e))