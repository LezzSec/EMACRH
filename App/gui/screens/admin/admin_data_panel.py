# -*- coding: utf-8 -*-
"""
Panel d'administration des données de référence.

Accessible uniquement aux administrateurs, permet de gérer toutes les tables
de paramétrage depuis l'interface :

  Ateliers · Services · Types d'absence · Jours fériés · Compétences ·
  Catégories documents · Motifs de sortie · Tranches d'âge · Rôles

Usage (depuis main_qt.py) :
    from gui.screens.admin.admin_data_panel import AdminDataPanelDialog
    dlg = AdminDataPanelDialog(parent=self)
    dlg.exec_()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QMessageBox, QPushButton, QListWidget, QListWidgetItem, QStackedWidget,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from infrastructure.logging.logging_config import get_logger
from .config_tabs import (
    AteliersTab, ServicesTab, TranchesAgeTab, MotifsortieTab,
    TypesAbsenceTab, JoursFeriesTab, SoldeCongesTab, DemandeAbsenceTab,
    CompetencesTab, PolyvalenceAdminTab,
    CategoriesDocsTab, DocumentEventRulesTab,
    RolesTab, HistoriqueAdminTab, LogsConnexionTab,
    ModulesApplicationTab,
)

logger = get_logger(__name__)


class AdminDataPanelDialog(QDialog):
    """
    Panel d'administration des données de référence.
    Accessible aux administrateurs uniquement.
    """

    modules_changed = pyqtSignal()   # émis quand la configuration des modules change

    def __init__(self, parent=None):
        super().__init__(parent)

        # Vérification des droits admin (fresh check en DB)
        from domain.services.admin.auth_service import is_admin
        if not is_admin():
            QMessageBox.critical(
                self, "Accès refusé",
                "Seuls les administrateurs peuvent accéder à cette fonctionnalité."
            )
            # On ferme immédiatement après l'affichage du message
            QTimer.singleShot(0, self.reject)
            return

        self.setWindowTitle("Administration — Paramètres de l'application")
        self.setMinimumSize(1100, 680)
        self.setModal(True)

        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── En-tête coloré ────────────────────────────────────────
        hdr = QWidget()
        hdr.setStyleSheet("background: #1b2f4e;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(24, 14, 20, 14)
        hdr_lay.setSpacing(10)

        ttl = QLabel("Administration — Paramètres de l'application")
        ttl.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        hdr_lay.addWidget(ttl)

        hdr_lay.addSpacing(16)
        sub = QLabel("· Modifications tracées dans l'historique")
        sub.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px;")
        hdr_lay.addWidget(sub)

        hdr_lay.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close.setStyleSheet(
            "color: white; background: rgba(255,255,255,0.15); "
            "border: 1px solid rgba(255,255,255,0.3); border-radius: 6px; "
            "padding: 6px 18px; font-size: 12px;"
        )
        btn_close.clicked.connect(self.accept)
        hdr_lay.addWidget(btn_close)
        outer.addWidget(hdr)

        # ── Corps : sidebar + contenu ──────────────────────────────
        body = QHBoxLayout()
        body.setSpacing(0)
        body.setContentsMargins(0, 0, 0, 0)

        # -- Sidebar --
        self._nav = QListWidget()
        self._nav.setFixedWidth(200)
        self._nav.setStyleSheet("""
            QListWidget {
                background: #f5f6f8;
                border: none;
                border-right: 1px solid #dde0e6;
                outline: none;
                padding: 8px 0;
            }
            QListWidget::item {
                padding: 8px 0 8px 22px;
                color: #374151;
                font-size: 12px;
                border: none;
            }
            QListWidget::item:selected {
                background: #dbeafe;
                color: #1e40af;
                font-weight: 600;
                border-left: 3px solid #2563eb;
                padding-left: 19px;
            }
            QListWidget::item:hover:!selected {
                background: #eceef2;
            }
        """)

        # -- Stack --
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: white;")

        # -- Construction nav + stack avec groupes thématiques --
        self._factories = {}     # nav_row → factory fn
        self._nav_widgets = {}   # nav_row → widget dans le stack (placeholder ou réel)
        self._created = set()    # nav_rows dont le widget est déjà instancié

        _GROUPS = [
            ("RH", [
                ("Ateliers",           lambda: AteliersTab()),
                ("Services",           lambda: ServicesTab()),
                ("Tranches d'âge",     lambda: TranchesAgeTab()),
                ("Motifs de sortie",   lambda: MotifsortieTab()),
            ]),
            ("Absences", [
                ("Types d'absence",    lambda: TypesAbsenceTab()),
                ("Jours fériés",       lambda: JoursFeriesTab()),
                ("Soldes de congés",   lambda: SoldeCongesTab()),
                ("Demandes",           lambda: DemandeAbsenceTab()),
            ]),
            ("Production", [
                ("Compétences",        lambda: CompetencesTab()),
                ("Polyvalence",        lambda: PolyvalenceAdminTab()),
            ]),
            ("Documents", [
                ("Catégories",         lambda: CategoriesDocsTab()),
                ("Règles événements",  lambda: DocumentEventRulesTab()),
            ]),
            ("Système", [
                ("Rôles",              lambda: RolesTab()),
                ("Historique",         lambda: HistoriqueAdminTab()),
                ("Logs connexion",     lambda: LogsConnexionTab()),
            ]),
            ("Application", [
                ("Modules",            lambda: ModulesApplicationTab()),
            ]),
        ]

        first_nav_row = None
        for group_label, items in _GROUPS:
            # En-tête de groupe (non sélectionnable)
            h_item = QListWidgetItem(group_label.upper())
            h_item.setFlags(Qt.NoItemFlags)
            h_item.setForeground(QColor("#9ca3af"))
            fnt = QFont()
            fnt.setPointSize(8)
            fnt.setBold(True)
            h_item.setFont(fnt)
            self._nav.addItem(h_item)

            for label, factory in items:
                nav_row = self._nav.count()
                self._nav.addItem(QListWidgetItem("  " + label))
                self._factories[nav_row] = factory
                # Placeholder dans le stack
                ph = QWidget()
                ph.setStyleSheet("background: white;")
                self._stack.addWidget(ph)
                self._nav_widgets[nav_row] = ph
                if first_nav_row is None:
                    first_nav_row = nav_row

            # Petit espacement visuel entre groupes
            spacer_item = QListWidgetItem()
            spacer_item.setFlags(Qt.NoItemFlags)
            spacer_item.setSizeHint(spacer_item.sizeHint().__class__(0, 6))
            self._nav.addItem(spacer_item)

        self._nav.currentRowChanged.connect(self._on_nav_changed)

        body.addWidget(self._nav)
        body.addWidget(self._stack, 1)
        outer.addLayout(body)

        # Sélection du premier élément
        if first_nav_row is not None:
            self._nav.setCurrentRow(first_nav_row)

    def _update_nav_badge(self, widget, count: int):
        """Met à jour le badge de comptage dans la sidebar pour un onglet donné."""
        for nav_row, w in self._nav_widgets.items():
            if w is widget:
                item = self._nav.item(nav_row)
                if item is None:
                    return
                text = item.text().strip()
                # Retirer un éventuel badge précédent (format "Label  [N]")
                if '  [' in text:
                    text = text[:text.index('  [')]
                item.setText(f"  {text.strip()}  [{count}]")
                break

    def _on_nav_changed(self, nav_row: int):
        if nav_row not in self._factories:
            return
        if nav_row not in self._created:
            new_widget = self._factories[nav_row]()
            # Connecter le signal modules_changed si c'est l'onglet Modules
            if isinstance(new_widget, ModulesApplicationTab):
                new_widget.modules_changed.connect(self.modules_changed)
            old = self._nav_widgets[nav_row]
            idx = self._stack.indexOf(old)
            self._stack.insertWidget(idx, new_widget)
            self._stack.removeWidget(old)
            old.deleteLater()
            self._nav_widgets[nav_row] = new_widget
            self._created.add(nav_row)
        self._stack.setCurrentWidget(self._nav_widgets[nav_row])
