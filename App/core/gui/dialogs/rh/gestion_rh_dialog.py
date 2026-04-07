# -*- coding: utf-8 -*-
"""
Écran RH Opérateur — dialog principal.
Assemble les sous-widgets et connecte les signaux du ViewModel.
"""
import logging
import os
import subprocess

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QStackedWidget,
    QLabel, QPushButton, QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication as _QApp
from PyQt5.QtGui import QFont

from core.gui.components.ui_theme import EmacButton
from core.gui.components.emac_ui_kit import add_custom_title_bar
from core.gui.view_models.gestion_rh_view_model import GestionRHViewModel, DomaineRH
from core.services.permission_manager import can

from .rh_selection_panel import RhSelectionPanel
from .rh_header_widget import RhHeaderWidget
from .rh_documents_panel import RhDocumentsPanel
from .domaines.domaine_general import DomaineGeneral
from .domaines.domaine_contrat import DomaineContrat
from .domaines.domaine_declaration import DomaineDeclaration
from .domaines.domaine_competences import DomaineCompetences
from .domaines.domaine_formation import DomaineFormation
from .domaines.domaine_medical import DomaineMedical
from .domaines.domaine_vie_salarie import DomaineVieSalarie
from .domaines.domaine_polyvalence import DomainePolyvalence
from .domaines.domaine_mutuelle import DomaineMutuelle

logger = logging.getLogger(__name__)


class GestionRHDialog(QDialog):
    """
    Fenêtre principale de gestion RH.
    Zone gauche : sélection opérateur.
    Zone droite : navigation par domaines + contenu + documents.
    """

    data_changed = pyqtSignal()

    def __init__(self, parent=None, preselect_personnel_id: int = None):
        super().__init__(parent)
        self.setWindowTitle("Gestion RH")
        screen = _QApp.primaryScreen().availableGeometry()
        w = min(1400, screen.width() - 40)
        h = min(800, screen.height() - 60)
        self.setMinimumSize(min(1000, w), min(650, h))
        self.resize(w, h)

        self.operateur_selectionne = None
        self.domaine_actif = DomaineRH.GENERAL

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._executer_recherche)

        self._vm = GestionRHViewModel(parent=self)
        self._setup_ui()
        self._connect_all()

        if preselect_personnel_id is not None:
            QTimer.singleShot(200, lambda: self._vm.selectionner_operateur(preselect_personnel_id))

    # =========================================================================
    # UI SETUP
    # =========================================================================

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(add_custom_title_bar(self, "Gestion RH"))

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._selection_panel = RhSelectionPanel()
        content_layout.addWidget(self._selection_panel)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("background-color: #e5e7eb;")
        sep.setFixedWidth(1)
        content_layout.addWidget(sep)

        content_layout.addWidget(self._creer_zone_droite(), 1)

        main_layout.addWidget(content, 1)
        main_layout.addWidget(self._creer_footer())

    def _creer_zone_droite(self) -> QWidget:
        zone = QWidget()
        layout = QVBoxLayout(zone)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack_details = QStackedWidget()

        # Page 0: placeholder
        self._stack_details.addWidget(self._creer_placeholder())

        # Page 1: contenu RH
        self._stack_details.addWidget(self._creer_contenu_rh())

        layout.addWidget(self._stack_details)
        return zone

    def _creer_placeholder(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("👤")
        icon.setFont(QFont("Segoe UI", 48))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        message = QLabel("Sélectionnez une personne")
        message.setFont(QFont("Segoe UI", 18, QFont.Bold))
        message.setStyleSheet("color: #6b7280;")
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)

        sous_message = QLabel("Utilisez la zone de recherche à gauche\npour trouver une personne")
        sous_message.setStyleSheet("color: #9ca3af;")
        sous_message.setAlignment(Qt.AlignCenter)
        layout.addWidget(sous_message)

        return widget

    def _creer_contenu_rh(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        self._header = RhHeaderWidget()
        layout.addWidget(self._header)

        scroll_container = QWidget()
        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(16)

        self._domain_stack = QStackedWidget()
        self._domaine_widgets = {}
        for domaine_cls, domaine_key in [
            (DomaineGeneral, DomaineRH.GENERAL),
            (DomaineContrat, DomaineRH.CONTRAT),
            (DomaineDeclaration, DomaineRH.DECLARATION),
            (DomaineCompetences, DomaineRH.COMPETENCES),
            (DomaineFormation, DomaineRH.FORMATION),
            (DomaineMedical, DomaineRH.MEDICAL),
            (DomaineVieSalarie, DomaineRH.VIE_SALARIE),
            (DomainePolyvalence, DomaineRH.POLYVALENCE),
            (DomaineMutuelle, DomaineRH.MUTUELLE),
        ]:
            widget_domaine = domaine_cls(self._vm)
            widget_domaine.refresh_requested.connect(self._charger_contenu_domaine)
            self._domain_stack.addWidget(widget_domaine)
            self._domaine_widgets[domaine_key] = widget_domaine

        inner_layout.addWidget(self._domain_stack)

        self._docs_panel = RhDocumentsPanel(self._vm)
        self._docs_panel.refresh_requested.connect(self._on_document_action)
        self._docs_panel.setVisible(False)
        inner_layout.addWidget(self._docs_panel)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)

        return widget

    def _creer_footer(self) -> QWidget:
        footer = QWidget()
        footer.setStyleSheet("background: #f9fafb; border-top: 1px solid #e5e7eb;")

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 12, 20, 12)

        btn_bulk = QPushButton("Actions en masse")
        btn_bulk.setToolTip("Assigner formations, absences ou visites médicales à plusieurs employés")
        btn_bulk.setCursor(Qt.PointingHandCursor)
        btn_bulk.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #a855f7);
                color: white; padding: 10px 24px; border-radius: 8px;
                border: none; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #9333ea);
            }
            QPushButton:pressed { background: #5b21b6; }
        """)
        btn_bulk.clicked.connect(self._open_bulk_assignment_dialog)
        btn_bulk.setVisible(can("rh.personnel.edit"))
        layout.addWidget(btn_bulk)

        layout.addStretch()

        btn_fermer = EmacButton("Fermer", variant="ghost")
        btn_fermer.clicked.connect(self.close)
        layout.addWidget(btn_fermer)

        return footer

    # =========================================================================
    # CONNEXIONS
    # =========================================================================

    def _connect_all(self):
        self._selection_panel.search_changed.connect(self._on_search_changed)
        self._selection_panel.operateur_selected.connect(
            lambda op_id: self._vm.selectionner_operateur(op_id)
        )
        self._header.domaine_changed.connect(self._on_domaine_change)
        self._header.archives_clicked.connect(self._on_archives_click)

        self._vm.resultats_loaded.connect(self._on_resultats_loaded)
        self._vm.operateur_loaded.connect(self._on_operateur_loaded)
        self._vm.domaine_loaded.connect(self._on_domaine_loaded)
        self._vm.archives_loaded.connect(self._on_archives_loaded)
        self._vm.document_path_ready.connect(self._on_document_path_ready)
        self._vm.dossier_formation_ready.connect(self._on_dossier_formation_ready)
        self._vm.action_succeeded.connect(lambda msg: QMessageBox.information(self, "Succès", msg))
        self._vm.error_occurred.connect(lambda msg: QMessageBox.critical(self, "Erreur", msg))
        self._vm.permission_denied.connect(lambda msg: QMessageBox.warning(self, "Accès refusé", msg))

        QTimer.singleShot(100, self._executer_recherche)

    # =========================================================================
    # HANDLERS
    # =========================================================================

    def _on_search_changed(self, text: str):
        self._search_timer.stop()
        self._search_timer.start(300)

    def _executer_recherche(self):
        texte = self._selection_panel.search_input.text().strip()
        self._selection_panel.show_loading()
        self._vm.rechercher(texte if texte else None)

    def _on_resultats_loaded(self, resultats: list):
        self._selection_panel.show_results(resultats)

    def _on_operateur_loaded(self, operateur: dict):
        self.operateur_selectionne = operateur
        self._selection_panel.highlight(operateur['id'])
        self._header.refresh(operateur)
        self.domaine_actif = DomaineRH.GENERAL
        self._domain_stack.setCurrentWidget(self._domaine_widgets[DomaineRH.GENERAL])
        self._charger_contenu_domaine()
        self._vm.charger_archives()
        self._stack_details.setCurrentIndex(1)

    def _on_domaine_change(self, code_domaine: str):
        self.domaine_actif = DomaineRH(code_domaine)
        self._header.set_domaine(code_domaine)
        self._domain_stack.setCurrentWidget(self._domaine_widgets[self.domaine_actif])
        if self.operateur_selectionne:
            self._charger_contenu_domaine()

    def _on_archives_click(self):
        self._docs_panel.setVisible(False)
        if self.operateur_selectionne:
            self._vm.charger_archives()

    def _charger_contenu_domaine(self):
        if not self.operateur_selectionne:
            return
        self._vm.charger_domaine(self.domaine_actif)

    def _on_domaine_loaded(self, donnees, documents: list, domaine):
        widget = self._domaine_widgets.get(domaine)
        if widget:
            widget.refresh(self.operateur_selectionne, donnees, documents)

        show_docs = (
            domaine != DomaineRH.CONTRAT
            and self._domaine_a_contenu(donnees, domaine)
        )
        if show_docs:
            self._docs_panel.set_context(self.operateur_selectionne, self.domaine_actif)
            self._docs_panel.refresh(documents)
            self._docs_panel.setVisible(True)
        else:
            self._docs_panel.setVisible(False)

        self.data_changed.emit()

    def _on_archives_loaded(self, archives: list):
        self._header.update_archives_count(len(archives))
        if self._header.archives_actif:
            self._docs_panel.show_archives(archives)
            self._docs_panel.setVisible(True)

    def _on_document_action(self):
        self._charger_contenu_domaine()
        self._vm.charger_archives()

    def _on_document_path_ready(self, path: str):
        if os.name == 'nt':
            os.startfile(path)
        else:
            subprocess.run(['xdg-open', path])

    def _on_dossier_formation_ready(self, success: bool, msg: str, path: str):
        if success and path:
            reply = QMessageBox.information(
                self, "Documents générés",
                f"Dossier de formation généré :\n{path}\n\nOuvrir le fichier ?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._on_document_path_ready(path)
        else:
            QMessageBox.warning(self, "Génération échouée", msg)

    def _open_bulk_assignment_dialog(self):
        from core.gui.dialogs.bulk_assignment import BulkAssignmentDialog
        dialog = BulkAssignmentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            if self.operateur_selectionne:
                self._charger_contenu_domaine()

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _domaine_a_contenu(self, donnees: dict, domaine) -> bool:
        if domaine == DomaineRH.DECLARATION:
            return bool(donnees.get('declarations'))
        if domaine == DomaineRH.COMPETENCES:
            return bool(donnees.get('competences'))
        if domaine == DomaineRH.FORMATION:
            return bool(donnees.get('formations'))
        if domaine == DomaineRH.MEDICAL:
            return bool(donnees.get('visites') or donnees.get('accidents'))
        if domaine == DomaineRH.VIE_SALARIE:
            return bool(
                donnees.get('sanctions_liste')
                or donnees.get('controles_alcool_liste')
                or donnees.get('tests_salivaires_liste')
                or donnees.get('entretiens_liste')
            )
        if domaine == DomaineRH.MUTUELLE:
            return bool(donnees.get('mutuelle'))
        return False
