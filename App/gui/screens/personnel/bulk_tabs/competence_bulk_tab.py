# -*- coding: utf-8 -*-
"""
Onglet compétences pour les opérations en masse.
"""

from typing import Dict

from PyQt5.QtWidgets import (
    QVBoxLayout, QGridLayout, QLabel, QComboBox,
    QDateEdit, QTextEdit, QGroupBox, QFileDialog,
)
from PyQt5.QtCore import QDate

from gui.workers.db_worker import DbWorker, DbThreadPool
from domain.services.formation.formation_service_crud import FormationServiceCRUD
from infrastructure.logging.logging_config import get_logger
from .base_bulk_tab import BulkTabBase, INPUT_STYLE_SM, LABEL_STYLE_SM, REQUIRED_STYLE, GROUPBOX_STYLE

logger = get_logger(__name__)


class CompetenceBulkTab(BulkTabBase):
    """Onglet pour l'ajout de compétence en masse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._catalogue = []
        self._setup_ui()
        self._load_catalogue()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        input_style = INPUT_STYLE_SM
        label_style = LABEL_STYLE_SM
        required_style = REQUIRED_STYLE

        # === Formulaire ===
        form_group = QGroupBox("Informations de la compétence")
        form_group.setStyleSheet(GROUPBOX_STYLE)
        form_layout = QGridLayout(form_group)
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(12)

        # Compétence
        lbl_competence = QLabel("Compétence *:")
        lbl_competence.setStyleSheet(required_style)
        form_layout.addWidget(lbl_competence, 0, 0)
        self.competence_combo = QComboBox()
        self.competence_combo.setEditable(True)
        self.competence_combo.setMinimumWidth(300)
        self.competence_combo.setStyleSheet(input_style)
        self.competence_combo.setInsertPolicy(QComboBox.NoInsert)
        self.competence_combo.completer().setCompletionMode(
            self.competence_combo.completer().PopupCompletion
        )
        self.competence_combo.lineEdit().setPlaceholderText("Saisir ou sélectionner une compétence...")
        self.competence_combo.currentIndexChanged.connect(self._on_competence_changed)
        form_layout.addWidget(self.competence_combo, 0, 1, 1, 3)

        # Date d'acquisition
        lbl_date_acq = QLabel("Date d'acquisition *:")
        lbl_date_acq.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_acq, 1, 0)
        self.date_acquisition = QDateEdit()
        self.date_acquisition.setDate(QDate.currentDate())
        self.date_acquisition.setCalendarPopup(True)
        self.date_acquisition.setDisplayFormat("dd/MM/yyyy")
        self.date_acquisition.setStyleSheet(input_style)
        self.date_acquisition.dateChanged.connect(self._update_expiration_date)
        form_layout.addWidget(self.date_acquisition, 1, 1)

        # Date d'expiration
        lbl_date_exp = QLabel("Date d'expiration:")
        lbl_date_exp.setStyleSheet(label_style)
        form_layout.addWidget(lbl_date_exp, 1, 2)
        self.date_expiration = QDateEdit()
        self.date_expiration.setCalendarPopup(True)
        self.date_expiration.setDisplayFormat("dd/MM/yyyy")
        self.date_expiration.setSpecialValueText("Permanent")
        self.date_expiration.setMinimumDate(QDate(1900, 1, 1))
        self.date_expiration.setDate(QDate(1900, 1, 1))
        self.date_expiration.setStyleSheet(input_style)
        form_layout.addWidget(self.date_expiration, 1, 3)

        # Info validité
        self.validite_info = QLabel("")
        self.validite_info.setStyleSheet("color: #64748b; font-style: italic; font-size: 12px;")
        form_layout.addWidget(self.validite_info, 2, 1, 1, 3)

        # Commentaire
        lbl_commentaire = QLabel("Commentaire:")
        lbl_commentaire.setStyleSheet(label_style)
        form_layout.addWidget(lbl_commentaire, 3, 0)
        self.commentaire_input = QTextEdit()
        self.commentaire_input.setMaximumHeight(50)
        self.commentaire_input.setPlaceholderText("Commentaire optionnel...")
        self.commentaire_input.setStyleSheet(input_style)
        form_layout.addWidget(self.commentaire_input, 3, 1, 1, 3)

        # Document / Attestation
        lbl_document = QLabel("Document:")
        lbl_document.setStyleSheet(label_style)
        form_layout.addWidget(lbl_document, 4, 0)
        form_layout.addLayout(self._build_doc_section(input_style), 4, 1, 1, 3)

        layout.addWidget(form_group)
        layout.addStretch()

    def _browse_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un document (attestation, certificat...)", "",
            "Documents (*.pdf *.doc *.docx *.png *.jpg *.jpeg);;Tous les fichiers (*)"
        )
        self._handle_file_selection(file_path)

    def _load_catalogue(self):
        """Charge le catalogue des compétences."""
        def fetch(progress_callback=None):
            return FormationServiceCRUD.get_catalogue_competences()

        def on_result(data):
            self._catalogue = data
            self.competence_combo.clear()
            self.competence_combo.setCurrentIndex(-1)
            self.competence_combo.lineEdit().clear()

            categories = {}
            for comp in data:
                cat = comp.get('categorie') or 'Autre'
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(comp)

            for cat in sorted(categories.keys()):
                self.competence_combo.addItem(f"── {cat} ──", None)
                idx = self.competence_combo.count() - 1
                self.competence_combo.model().item(idx).setEnabled(False)

                for comp in categories[cat]:
                    label = comp['libelle']
                    if comp.get('duree_validite_mois'):
                        label += f" ({comp['duree_validite_mois']} mois)"
                    self.competence_combo.addItem(label, comp)

        def on_error(error):
            logger.error(f"Erreur chargement catalogue compétences: {error}")

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def _on_competence_changed(self):
        """Met à jour l'info validité quand la compétence change."""
        comp_data = self.competence_combo.currentData()
        if isinstance(comp_data, dict) and comp_data.get('duree_validite_mois'):
            mois = comp_data['duree_validite_mois']
            self.validite_info.setText(f"Validité standard: {mois} mois")
            self._update_expiration_date()
        else:
            self.validite_info.setText("Compétence permanente (pas d'expiration)")
            self.date_expiration.setDate(QDate(1900, 1, 1))

    def _update_expiration_date(self):
        """Calcule automatiquement la date d'expiration."""
        comp_data = self.competence_combo.currentData()
        if isinstance(comp_data, dict) and comp_data.get('duree_validite_mois'):
            from dateutil.relativedelta import relativedelta
            date_acq = self.date_acquisition.date().toPyDate()
            date_exp = date_acq + relativedelta(months=comp_data['duree_validite_mois'])
            self.date_expiration.setDate(QDate(date_exp.year, date_exp.month, date_exp.day))

    def get_data(self) -> Dict:
        """Retourne les données du formulaire."""
        comp_data = self.competence_combo.currentData()
        free_text = self.competence_combo.currentText().strip()
        date_exp = self.date_expiration.date()

        if comp_data and isinstance(comp_data, dict):
            comp_id = comp_data['id']
            comp_libelle = comp_data['libelle']
        else:
            comp_id = None
            comp_libelle = free_text if free_text else None

        return {
            'competence_id': comp_id,
            'competence_libelle': comp_libelle,
            'date_acquisition': self.date_acquisition.date().toPyDate(),
            'date_expiration': date_exp.toPyDate() if date_exp.year() > 1900 else None,
            'commentaire': self.commentaire_input.toPlainText().strip() or None,
            'document_path': self._document_path
        }

    def validate(self) -> tuple:
        """Valide les données du formulaire."""
        data = self.get_data()
        if not data['competence_id'] and not data['competence_libelle']:
            return False, "Veuillez sélectionner ou saisir une compétence"
        return True, ""
