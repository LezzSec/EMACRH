# -*- coding: utf-8 -*-
"""
Onglet absences pour les opérations en masse.
"""

from typing import Dict

from PyQt5.QtWidgets import (
    QVBoxLayout, QGridLayout, QLabel, QComboBox,
    QDateEdit, QTextEdit, QGroupBox, QFileDialog,
)
from PyQt5.QtCore import QDate

from gui.workers.db_worker import DbWorker, DbThreadPool
from domain.services.planning.absence_service_crud import AbsenceServiceCRUD
from infrastructure.logging.logging_config import get_logger
from .base_bulk_tab import BulkTabBase, INPUT_STYLE_LG, LABEL_STYLE_LG, REQUIRED_STYLE, GROUPBOX_STYLE

logger = get_logger(__name__)


class AbsenceBulkTab(BulkTabBase):
    """Onglet pour l'ajout d'absence en masse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._types_absence = []
        self._setup_ui()
        self._load_types_absence()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        input_style = INPUT_STYLE_LG
        label_style = LABEL_STYLE_LG
        required_style = REQUIRED_STYLE

        # === Formulaire ===
        form_group = QGroupBox("Informations de l'absence")
        form_group.setStyleSheet(GROUPBOX_STYLE)
        form_layout = QGridLayout(form_group)
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(12)

        # Type d'absence
        lbl_type = QLabel("Type d'absence *:")
        lbl_type.setStyleSheet(required_style)
        form_layout.addWidget(lbl_type, 0, 0)
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.type_combo, 0, 1, 1, 3)

        # Dates
        lbl_date_debut = QLabel("Date début *:")
        lbl_date_debut.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_debut, 1, 0)
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setStyleSheet(input_style)
        form_layout.addWidget(self.date_debut, 1, 1)

        lbl_date_fin = QLabel("Date fin *:")
        lbl_date_fin.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_fin, 1, 2)
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setStyleSheet(input_style)
        form_layout.addWidget(self.date_fin, 1, 3)

        # Demi-journées
        lbl_demi_debut = QLabel("Début:")
        lbl_demi_debut.setStyleSheet(label_style)
        form_layout.addWidget(lbl_demi_debut, 2, 0)
        self.demi_debut_combo = QComboBox()
        self.demi_debut_combo.addItem("Journée complète", "JOURNEE")
        self.demi_debut_combo.addItem("Matin uniquement", "MATIN")
        self.demi_debut_combo.addItem("Après-midi uniquement", "APRES_MIDI")
        self.demi_debut_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.demi_debut_combo, 2, 1)

        lbl_demi_fin = QLabel("Fin:")
        lbl_demi_fin.setStyleSheet(label_style)
        form_layout.addWidget(lbl_demi_fin, 2, 2)
        self.demi_fin_combo = QComboBox()
        self.demi_fin_combo.addItem("Journée complète", "JOURNEE")
        self.demi_fin_combo.addItem("Matin uniquement", "MATIN")
        self.demi_fin_combo.addItem("Après-midi uniquement", "APRES_MIDI")
        self.demi_fin_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.demi_fin_combo, 2, 3)

        # Statut
        lbl_statut = QLabel("Statut:")
        lbl_statut.setStyleSheet(label_style)
        form_layout.addWidget(lbl_statut, 3, 0)
        self.statut_combo = QComboBox()
        self.statut_combo.addItem("En attente de validation", "EN_ATTENTE")
        self.statut_combo.addItem("Validée directement", "VALIDEE")
        self.statut_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.statut_combo, 3, 1)

        # Motif
        lbl_motif = QLabel("Motif:")
        lbl_motif.setStyleSheet(label_style)
        form_layout.addWidget(lbl_motif, 4, 0)
        self.motif_input = QTextEdit()
        self.motif_input.setMaximumHeight(60)
        self.motif_input.setStyleSheet(input_style)
        form_layout.addWidget(self.motif_input, 4, 1, 1, 3)

        # Document / Justificatif
        lbl_document = QLabel("Justificatif:")
        lbl_document.setStyleSheet(label_style)
        form_layout.addWidget(lbl_document, 5, 0)
        form_layout.addLayout(self._build_doc_section(input_style), 5, 1, 1, 3)

        layout.addWidget(form_group)
        layout.addStretch()

    def _browse_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un justificatif", "",
            "Documents (*.pdf *.doc *.docx *.png *.jpg *.jpeg);;Tous les fichiers (*)"
        )
        self._handle_file_selection(file_path)

    def _load_types_absence(self):
        """Charge les types d'absence depuis la base de données."""
        def fetch(progress_callback=None):
            return AbsenceServiceCRUD.get_types_absence()

        def on_result(data):
            self._types_absence = data
            self.type_combo.clear()
            for ta in data:
                self.type_combo.addItem(f"{ta['code']} - {ta['libelle']}", ta['code'])

        def on_error(error):
            logger.error(f"Erreur chargement types absence: {error}")

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def get_data(self) -> Dict:
        """Retourne les données du formulaire."""
        return {
            'type_absence_code': self.type_combo.currentData(),
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': self.date_fin.date().toPyDate(),
            'demi_journee_debut': self.demi_debut_combo.currentData(),
            'demi_journee_fin': self.demi_fin_combo.currentData(),
            'statut': self.statut_combo.currentData(),
            'motif': self.motif_input.toPlainText().strip(),
            'document_path': self._document_path
        }

    def validate(self) -> tuple:
        """Valide les données du formulaire."""
        data = self.get_data()
        if not data['type_absence_code']:
            return False, "Le type d'absence est obligatoire"
        if data['date_debut'] > data['date_fin']:
            return False, "La date de début doit être antérieure à la date de fin"
        return True, ""
