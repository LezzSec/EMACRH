# -*- coding: utf-8 -*-
"""
Gestion des Alertes RH - Dialog principal (v2 - Card-based design)

Vue unifiee avec cartes groupees par urgence (Critique > Avertissement > Info).
"""

import logging
from datetime import date
from typing import List, Dict, Set

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QFrame,
    QPushButton, QLineEdit, QCheckBox, QScrollArea,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QCursor

from core.services.alert_service import AlertService, TypeAlerte
from core.models import Alert
from core.services.permission_manager import can
from infrastructure.config.date_format import format_date

logger = logging.getLogger(__name__)

from core.gui.components.emac_ui_kit import add_custom_title_bar, show_error_message, EmacBadge
from core.gui.components.ui_theme import EmacButton
from core.gui.workers.db_worker import DbWorker, DbThreadPool
from core.gui.components.loading_components import EmptyStatePlaceholder

THEME_AVAILABLE = True  # toujours disponible — conservé pour compat branches existantes


# ===========================
# Constantes
# ===========================

URGENCY_CONFIG = {
    "CRITIQUE": {
        "accent": "#dc2626",
        "accent_hover": "#b91c1c",
        "bg_light": "#fef2f2",
        "text": "#991b1b",
        "icon": "!!",
        "label": "Critiques",
        "order": 0,
        "badge_variant": "error",
    },
    "AVERTISSEMENT": {
        "accent": "#f59e0b",
        "accent_hover": "#d97706",
        "bg_light": "#fffbeb",
        "text": "#92400e",
        "icon": "!",
        "label": "Avertissements",
        "order": 1,
        "badge_variant": "warning",
    },
    "INFO": {
        "accent": "#3b82f6",
        "accent_hover": "#2563eb",
        "bg_light": "#eff6ff",
        "text": "#1e40af",
        "icon": "i",
        "label": "Informations",
        "order": 2,
        "badge_variant": "info",
    },
}

TYPE_LABELS = {
    TypeAlerte.CONTRAT_EXPIRE: "Contrat expire",
    TypeAlerte.CONTRAT_EXPIRE_7J: "Expire < 7j",
    TypeAlerte.CONTRAT_EXPIRE_30J: "Expire < 30j",
    TypeAlerte.PERSONNEL_SANS_CONTRAT: "Sans contrat",
    TypeAlerte.PERSONNEL_SANS_COMPETENCES: "Sans competences",
    TypeAlerte.PERSONNEL_NOUVEAU_SANS_AFFECTATION: "Nouveau arrivant",
}




# ===========================
# AlertCard - Carte d'alerte
# ===========================

class AlertCard(QFrame):
    """Carte individuelle representant une alerte."""

    view_clicked = pyqtSignal(object)
    handle_clicked = pyqtSignal(object)

    def __init__(self, alert: Alert, is_handled: bool = False, parent=None):
        super().__init__(parent)
        self._alert = alert
        self._is_handled = is_handled
        cfg = URGENCY_CONFIG.get(alert.urgence, URGENCY_CONFIG["INFO"])

        self.setObjectName("alert_card")
        self.setFixedHeight(82)
        self.setStyleSheet(f"""
            QFrame#alert_card {{
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-left: 5px solid {cfg['accent']};
                border-radius: 10px;
            }}
            QFrame#alert_card:hover {{
                background: #f9fafb;
                border-color: {cfg['accent']};
                border-left: 5px solid {cfg['accent']};
            }}
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 10, 12, 10)
        main_layout.setSpacing(12)

        # Info section (gauche)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Ligne 1 : Nom + badge type
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        name = f"{alert.personnel_nom or ''} {alert.personnel_prenom or ''}".strip()
        name_label = QLabel(name)
        name_font = QFont()
        name_font.setPixelSize(14)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #111827; background: transparent; border: none;")
        top_row.addWidget(name_label)

        type_text = TYPE_LABELS.get(alert.type_alerte, alert.type_alerte)
        if THEME_AVAILABLE:
            badge = EmacBadge(type_text, variant=cfg["badge_variant"])
            top_row.addWidget(badge)
        else:
            type_label = QLabel(type_text)
            type_label.setStyleSheet(f"color: {cfg['text']}; font-size: 11px; font-weight: bold; background: transparent; border: none;")
            top_row.addWidget(type_label)

        top_row.addStretch()
        info_layout.addLayout(top_row)

        # Ligne 2 : Details
        detail_text = self._build_detail_text(alert)
        detail_label = QLabel(detail_text)
        detail_label.setStyleSheet("color: #6b7280; font-size: 13px; background: transparent; border: none;")
        info_layout.addWidget(detail_label)

        main_layout.addLayout(info_layout, 1)

        # Jours restants (centre-droit, si applicable)
        if alert.jours_restants is not None:
            days_text, days_color = self._format_days(alert.jours_restants)
            days_label = QLabel(days_text)
            days_font = QFont()
            days_font.setPixelSize(14)
            days_font.setBold(True)
            days_label.setFont(days_font)
            days_label.setStyleSheet(f"color: {days_color}; background: transparent; border: none;")
            days_label.setAlignment(Qt.AlignCenter)
            days_label.setMinimumWidth(80)
            main_layout.addWidget(days_label)

        # Boutons (droite)
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        btn_voir = QPushButton("Voir")
        btn_voir.setCursor(Qt.PointingHandCursor)
        btn_voir.setFixedSize(65, 30)
        btn_voir.setStyleSheet(f"""
            QPushButton {{
                background: {cfg['accent']};
                color: white;
                border-radius: 6px;
                border: none;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {cfg['accent_hover']}; }}
        """)
        btn_voir.clicked.connect(lambda: self.view_clicked.emit(self._alert))
        btn_layout.addWidget(btn_voir)

        handle_text = "Afficher" if is_handled else "Masquer"
        btn_handle = QPushButton(handle_text)
        btn_handle.setCursor(Qt.PointingHandCursor)
        btn_handle.setFixedSize(65, 26)
        btn_handle.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #6b7280;
                border: 1px solid #d1d5db;
                border-radius: 5px;
                font-size: 11px;
            }
            QPushButton:hover { background: #f3f4f6; color: #374151; }
        """)
        btn_handle.clicked.connect(lambda: self.handle_clicked.emit(self._alert))
        btn_layout.addWidget(btn_handle)

        main_layout.addLayout(btn_layout)

    @staticmethod
    def _build_detail_text(alert: Alert) -> str:
        parts = []
        type_contrat = alert.data.get('type_contrat')
        if type_contrat:
            parts.append(type_contrat)
        if alert.date_echeance:
            parts.append(f"Echeance: {format_date(alert.date_echeance)}")
        matricule = alert.data.get('matricule')
        if matricule:
            parts.append(f"Mat. {matricule}")
        if alert.description and not type_contrat:
            parts.append(alert.description)
        return "  ·  ".join(parts) if parts else alert.description or ""

    @staticmethod
    def _format_days(jours: int) -> tuple:
        if jours < 0:
            return f"{abs(jours)}j expire", "#dc2626"
        elif jours == 0:
            return "Aujourd'hui", "#dc2626"
        elif jours <= 7:
            return f"{jours}j", "#dc2626"
        elif jours <= 30:
            return f"{jours}j", "#f59e0b"
        else:
            return f"{jours}j", "#3b82f6"


# ===========================
# UrgencyGroupWidget
# ===========================

class UrgencyGroupWidget(QWidget):
    """Section groupant les alertes d'un meme niveau d'urgence."""

    view_clicked = pyqtSignal(object)
    handle_clicked = pyqtSignal(object)

    def __init__(self, urgency_key: str, parent=None):
        super().__init__(parent)
        self._urgency = urgency_key
        self._cards: List[AlertCard] = []
        cfg = URGENCY_CONFIG[urgency_key]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        self._header = QFrame()
        self._header.setFixedHeight(40)
        self._header.setStyleSheet(f"""
            QFrame {{
                background: {cfg['bg_light']};
                border-radius: 8px;
            }}
        """)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        self._header_label = QLabel(f"{cfg['label']}")
        header_font = QFont()
        header_font.setPixelSize(14)
        header_font.setBold(True)
        self._header_label.setFont(header_font)
        self._header_label.setStyleSheet(f"color: {cfg['text']}; background: transparent; border: none;")
        header_layout.addWidget(self._header_label)

        header_layout.addStretch()

        self._count_badge = QLabel("0")
        self._count_badge.setAlignment(Qt.AlignCenter)
        self._count_badge.setFixedSize(28, 22)
        self._count_badge.setStyleSheet(f"""
            QLabel {{
                background: {cfg['accent']};
                color: white;
                border-radius: 11px;
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(self._count_badge)

        layout.addWidget(self._header)

        # Container pour les cartes
        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(6)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._cards_layout)

    def set_alerts(self, alerts: List[Alert], handled_ids: Set[str]):
        # Nettoyer
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        count = len(alerts)
        self._count_badge.setText(str(count))
        cfg = URGENCY_CONFIG[self._urgency]
        plural = "s" if count > 1 else ""
        self._header_label.setText(f"{cfg['label']} — {count} alerte{plural}")

        self.setVisible(count > 0)

        for alert in alerts:
            alert_key = f"{alert.categorie}_{alert.type_alerte}_{alert.id}"
            is_handled = alert_key in handled_ids
            card = AlertCard(alert, is_handled=is_handled)
            card.view_clicked.connect(lambda a: self.view_clicked.emit(a))
            card.handle_clicked.connect(lambda a: self.handle_clicked.emit(a))
            self._cards.append(card)
            self._cards_layout.addWidget(card)


# ===========================
# FilterBar - Pill buttons
# ===========================

def _pill_style(checked: bool, accent: str = "#0f172a") -> str:
    if checked:
        return (f"QPushButton {{ padding: 5px 14px; border-radius: 14px; background: {accent}; "
                f"color: white; font-size: 12px; font-weight: 600; border: 1px solid {accent}; }}")
    return ("QPushButton { padding: 5px 14px; border-radius: 14px; background: white; "
            "color: #374151; font-size: 12px; border: 1px solid #d1d5db; } "
            "QPushButton:hover { background: #f3f4f6; }")


class FilterBar(QWidget):
    """Barre de filtres avec boutons-pilules."""

    filters_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # --- Ligne 1 : Urgence + recherche + masqués ---
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self._urgency_btns: dict = {}
        urgency_items = [("Tous", None), ("Critiques", "CRITIQUE"), ("Avertissements", "AVERTISSEMENT"), ("Informations", "INFO")]
        for label, key in urgency_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key is None)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("urgency_key", key)
            btn.clicked.connect(self._on_urgency_clicked)
            accent = URGENCY_CONFIG[key]["accent"] if key else "#0f172a"
            btn.setProperty("accent", accent)
            self._urgency_btns[str(key)] = btn
            row1.addWidget(btn)

        row1.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom...")
        self.search_input.setFixedHeight(30)
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet(
            "border: 1px solid #d1d5db; border-radius: 14px; padding: 4px 12px; font-size: 12px; background: white;"
        )
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self.filters_changed.emit)
        self.search_input.textChanged.connect(lambda: self._search_timer.start())
        row1.addWidget(self.search_input)

        self.show_handled_cb = QCheckBox("Masqués")
        self.show_handled_cb.setStyleSheet("color: #6b7280; font-size: 12px; margin-left: 6px;")
        self.show_handled_cb.stateChanged.connect(lambda: self.filters_changed.emit())
        row1.addWidget(self.show_handled_cb)

        main_layout.addLayout(row1)

        # --- Ligne 2 : Types ---
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self._type_btns: dict = {}
        type_items = [("Tous les types", "")] + [(label, str(key)) for key, label in TYPE_LABELS.items()]
        for label, key in type_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == "")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("type_key", key)
            btn.clicked.connect(self._on_type_clicked)
            self._type_btns[key] = btn
            row2.addWidget(btn)

        row2.addStretch()
        main_layout.addLayout(row2)

        self._refresh_styles()

    def _on_urgency_clicked(self):
        key = self.sender().property("urgency_key")
        for k, btn in self._urgency_btns.items():
            btn.setChecked(btn.property("urgency_key") == key)
        self._refresh_styles()
        self.filters_changed.emit()

    def _on_type_clicked(self):
        key = self.sender().property("type_key")
        for k, btn in self._type_btns.items():
            btn.setChecked(btn.property("type_key") == key)
        self._refresh_styles()
        self.filters_changed.emit()

    def _refresh_styles(self):
        for btn in self._urgency_btns.values():
            accent = btn.property("accent") or "#0f172a"
            btn.setStyleSheet(_pill_style(btn.isChecked(), accent))
        for btn in self._type_btns.values():
            btn.setStyleSheet(_pill_style(btn.isChecked()))

    def update_urgency_counts(self, counts: dict):
        labels = {None: "Tous", "CRITIQUE": "Critiques", "AVERTISSEMENT": "Avertissements", "INFO": "Informations"}
        total = sum(counts.values())
        for key_str, btn in self._urgency_btns.items():
            real_key = btn.property("urgency_key")
            count = total if real_key is None else counts.get(real_key, 0)
            label = labels.get(real_key, "")
            btn.setText(f"{label} ({count})")
        self._refresh_styles()

    def get_filters(self) -> dict:
        urgency = None
        for btn in self._urgency_btns.values():
            if btn.isChecked():
                urgency = btn.property("urgency_key")
                break
        type_filter = ""
        for btn in self._type_btns.values():
            if btn.isChecked():
                type_filter = btn.property("type_key") or ""
                break
        return {
            "search": self.search_input.text().lower().strip(),
            "urgency": urgency,
            "type": type_filter,
            "show_handled": self.show_handled_cb.isChecked(),
        }


# ===========================
# Dialog Principal
# ===========================

class GestionAlertesRHDialog(QDialog):
    """Dialog principal des Alertes RH - Vue unifiee par cartes."""

    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alertes RH")
        self.resize(1200, 800)

        self._all_alerts: List[Alert] = []
        self._handled_ids: Set[str] = set()
        self._can_view_contrats = True
        self._can_view_personnel = True

        self._setup_ui()
        self._check_permissions()
        QTimer.singleShot(100, self._load_data_async)

    def _setup_ui(self):
        if THEME_AVAILABLE:
            add_custom_title_bar(self, "Alertes RH")

        self.setStyleSheet("QDialog { background: #f6f7fb; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 16)
        main_layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)

        title = QLabel("Alertes RH")
        title_font = QFont()
        title_font.setPixelSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #111827;")
        header.addWidget(title)

        header.addStretch()

        if THEME_AVAILABLE:
            btn_export = EmacButton("Exporter PDF", variant='ghost')
            btn_export.setFixedHeight(36)
            btn_export.clicked.connect(self._export_pdf)
            header.addWidget(btn_export)

            btn_refresh = EmacButton("Actualiser", variant='primary')
            btn_refresh.setFixedHeight(36)
            btn_refresh.clicked.connect(self._load_data_async)
            header.addWidget(btn_refresh)

            btn_close = EmacButton("Fermer", variant='ghost')
            btn_close.setFixedHeight(36)
            btn_close.clicked.connect(self.accept)
            header.addWidget(btn_close)
        else:
            for text, slot in [("Exporter PDF", self._export_pdf), ("Actualiser", self._load_data_async), ("Fermer", self.accept)]:
                btn = QPushButton(text)
                btn.clicked.connect(slot)
                header.addWidget(btn)

        main_layout.addLayout(header)

        # Filter bar (urgence + types + recherche)
        self._filter_bar = FilterBar()
        self._filter_bar.filters_changed.connect(self._apply_filters)
        main_layout.addWidget(self._filter_bar)

        # Scroll area avec les groupes d'urgence
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #f1f1f1;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self._scroll_layout = QVBoxLayout(scroll_content)
        self._scroll_layout.setContentsMargins(0, 0, 4, 0)
        self._scroll_layout.setSpacing(20)

        self._urgency_groups: Dict[str, UrgencyGroupWidget] = {}
        for urgency_key in ["CRITIQUE", "AVERTISSEMENT", "INFO"]:
            group = UrgencyGroupWidget(urgency_key)
            group.view_clicked.connect(self._on_view_alert)
            group.handle_clicked.connect(self._on_handle_alert)
            self._urgency_groups[urgency_key] = group
            self._scroll_layout.addWidget(group)

        # Empty state
        if THEME_AVAILABLE:
            self._empty_placeholder = EmptyStatePlaceholder(
                icon="✅",
                title="Aucune alerte",
                subtitle="Tout est en ordre, aucune alerte a afficher."
            )
        else:
            self._empty_placeholder = QLabel("Aucune alerte a afficher")
            self._empty_placeholder.setAlignment(Qt.AlignCenter)
            self._empty_placeholder.setStyleSheet("color: #9ca3af; font-size: 14px; padding: 60px;")
        self._empty_placeholder.hide()
        self._scroll_layout.addWidget(self._empty_placeholder)

        self._scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

    # ------- Permissions -------

    def _check_permissions(self):
        self._can_view_contrats = can('rh.contrats.view')
        self._can_view_personnel = can('rh.personnel.view')

        if not self._can_view_contrats and not self._can_view_personnel:
            QMessageBox.warning(self, "Acces refuse", "Permissions insuffisantes.")
            QTimer.singleShot(0, self.reject)

    # ------- Chargement async -------

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
        contract_alerts = AlertService.get_all_contract_alerts() if self._can_view_contrats else []
        personnel_alerts = AlertService.get_all_personnel_alerts() if self._can_view_personnel else []

        # Deduplication
        seen = set()
        merged = []
        for alert in contract_alerts + personnel_alerts:
            key = (alert.personnel_id, alert.type_alerte)
            if key not in seen:
                seen.add(key)
                merged.append(alert)

        return sorted(merged, key=lambda a: a.urgence_ordre)

    def _on_data_loaded(self, alerts: List[Alert]):
        self._all_alerts = alerts
        self._update_kpi_counts()
        self._apply_filters()

    def _on_load_error(self, error_msg):
        logger.error(f"Erreur chargement alertes: {error_msg}")
        if show_error_message:
            show_error_message(self, "Erreur", "Impossible de charger les alertes", Exception(error_msg))
        else:
            QMessageBox.critical(self, "Erreur", str(error_msg))

    # ------- KPI -------

    def _update_kpi_counts(self):
        counts = {"CRITIQUE": 0, "AVERTISSEMENT": 0, "INFO": 0}
        for alert in self._all_alerts:
            if alert.urgence in counts:
                counts[alert.urgence] += 1
        self._filter_bar.update_urgency_counts(counts)

    # ------- Filtrage -------

    def _apply_filters(self):
        filters = self._filter_bar.get_filters()
        search = filters["search"]
        urgency_filter = filters["urgency"]
        type_filter = filters["type"]
        show_handled = filters["show_handled"]

        grouped: Dict[str, List[Alert]] = {"CRITIQUE": [], "AVERTISSEMENT": [], "INFO": []}

        for alert in self._all_alerts:
            if urgency_filter and alert.urgence != urgency_filter:
                continue
            alert_key = f"{alert.categorie}_{alert.type_alerte}_{alert.id}"
            if alert_key in self._handled_ids and not show_handled:
                continue
            if type_filter and alert.type_alerte != type_filter:
                continue
            if search:
                searchable = f"{alert.personnel_nom} {alert.personnel_prenom}".lower()
                if search not in searchable:
                    continue
            if alert.urgence in grouped:
                grouped[alert.urgence].append(alert)

        total_visible = sum(len(v) for v in grouped.values())
        for urgency_key, group_widget in self._urgency_groups.items():
            group_widget.set_alerts(grouped.get(urgency_key, []), self._handled_ids)
        self._empty_placeholder.setVisible(total_visible == 0)

    # ------- Actions -------

    def _on_view_alert(self, alert: Alert):
        # Les alertes "sans contrat" doivent ouvrir la gestion RH (contrats), pas les détails polyvalence
        if alert.categorie == "CONTRAT" or alert.type_alerte == "PERSONNEL_SANS_CONTRAT":
            self._on_view_contract_detail(alert)
        else:
            self._on_view_personnel_detail(alert)

    def _on_view_contract_detail(self, alert: Alert):
        pid = alert.personnel_id
        if pid:
            from core.gui.dialogs.gestion_rh import GestionRHDialog
            from core.services.rh_service import DomaineRH
            dialog = GestionRHDialog(parent=self)
            dialog.data_changed.connect(self._on_sub_dialog_changed)
            dialog._selectionner_operateur_par_id(pid)
            # Naviguer directement vers l'onglet Contrats
            dialog._on_domaine_change(DomaineRH.CONTRAT.value)
            dialog.exec_()

    def _on_view_personnel_detail(self, alert: Alert):
        pid = alert.personnel_id
        if pid:
            try:
                from core.gui.dialogs.gestion_personnel import DetailOperateurDialog
                dialog = DetailOperateurDialog(
                    pid,
                    alert.personnel_nom or '',
                    alert.personnel_prenom or '',
                    'ACTIF',
                    parent=self
                )
                dialog.exec_()
            except Exception as e:
                logger.exception(f"Erreur ouverture DetailOperateurDialog pour id={pid}: {e}")
                show_error_message(self, "Erreur", "Impossible d'ouvrir le détail de l'opérateur.", e)

    def _on_handle_alert(self, alert: Alert):
        """Masque ou affiche une alerte."""
        alert_key = f"{alert.categorie}_{alert.type_alerte}_{alert.id}"
        if alert_key in self._handled_ids:
            self._handled_ids.discard(alert_key)
        else:
            self._handled_ids.add(alert_key)
        self._apply_filters()

    def _on_sub_dialog_changed(self):
        """Recharge les alertes et notifie le parent."""
        self._load_data_async()
        self.data_changed.emit()

    # ------- Export PDF -------

    def _export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter PDF", f"alertes_rh_{date.today()}.pdf", "PDF Files (*.pdf)"
            )
            if not file_path:
                return

            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
            elements = []
            styles = getSampleStyleSheet()

            elements.append(Paragraph(f"Rapport Alertes RH - {format_date(date.today())}", styles['Title']))
            elements.append(Spacer(1, 20))

            # Recuperer les alertes filtrees visibles
            filtered = self._get_filtered_alerts()

            headers = ["Nom", "Prenom", "Categorie", "Type", "Detail", "Urgence"]
            data = [headers]

            for a in filtered:
                type_text = TYPE_LABELS.get(a.type_alerte, a.type_alerte)
                detail = ""
                if a.date_echeance:
                    jours = f" ({a.jours_restants}j)" if a.jours_restants is not None else ""
                    detail = f"Fin: {format_date(a.date_echeance)}{jours}"
                elif a.description:
                    detail = a.description

                data.append([
                    a.personnel_nom or "",
                    a.personnel_prenom or "",
                    a.categorie,
                    type_text,
                    detail,
                    URGENCY_CONFIG.get(a.urgence, {}).get("label", a.urgence),
                ])

            if len(data) > 1:
                t = Table(data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(t)
            else:
                elements.append(Paragraph("Aucune alerte a afficher", styles['Normal']))

            doc.build(elements)
            QMessageBox.information(self, "Succes", f"Export termine:\n{file_path}")

        except Exception as e:
            logger.exception(f"Erreur export PDF: {e}")
            if show_error_message:
                show_error_message(self, "Erreur Export", "Impossible d'exporter le PDF", e)
            else:
                QMessageBox.critical(self, "Erreur Export", "Impossible d'exporter le PDF. Consultez les logs pour plus de détails.")

    def _get_filtered_alerts(self) -> List[Alert]:
        """Retourne la liste des alertes actuellement visibles apres filtrage."""
        filters = self._filter_bar.get_filters()
        search = filters["search"]
        urgency_filter = filters["urgency"]
        type_filter = filters["type"]
        show_handled = filters["show_handled"]

        result = []
        for alert in self._all_alerts:
            if urgency_filter and alert.urgence != urgency_filter:
                continue
            alert_key = f"{alert.categorie}_{alert.type_alerte}_{alert.id}"
            if alert_key in self._handled_ids and not show_handled:
                continue
            if type_filter and alert.type_alerte != type_filter:
                continue
            if search:
                searchable = f"{alert.personnel_nom} {alert.personnel_prenom}".lower()
                if search not in searchable:
                    continue
            result.append(alert)
        return result
