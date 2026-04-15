# -*- coding: utf-8 -*-
"""
Onglet formations pour les opérations en masse.
"""

from typing import Dict

from PyQt5.QtWidgets import (
    QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox,
    QDateEdit, QDoubleSpinBox, QCheckBox, QTextEdit, QGroupBox,
)
from PyQt5.QtCore import QDate

from .base_bulk_tab import BulkTabBase, INPUT_STYLE_SM, LABEL_STYLE_SM, REQUIRED_STYLE, GROUPBOX_STYLE, _FILE_FILTER_ALL


class FormationBulkTab(BulkTabBase):
    """Onglet pour l'ajout de formation en masse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        input_style = INPUT_STYLE_SM
        label_style = LABEL_STYLE_SM
        required_style = REQUIRED_STYLE

        # === Formulaire ===
        form_group = QGroupBox("Informations de la formation")
        form_group.setStyleSheet(GROUPBOX_STYLE)
        form_layout = QGridLayout(form_group)
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(12)

        # Intitulé
        lbl_intitule = QLabel("Intitulé *:")
        lbl_intitule.setStyleSheet(required_style)
        form_layout.addWidget(lbl_intitule, 0, 0)
        self.intitule_input = QLineEdit()
        self.intitule_input.setPlaceholderText("Ex: Formation Sécurité 2026")
        self.intitule_input.setStyleSheet(input_style)
        form_layout.addWidget(self.intitule_input, 0, 1, 1, 3)

        # Organisme
        lbl_organisme = QLabel("Organisme:")
        lbl_organisme.setStyleSheet(label_style)
        form_layout.addWidget(lbl_organisme, 1, 0)
        self.organisme_input = QLineEdit()
        self.organisme_input.setPlaceholderText("Ex: APAVE, AFPA...")
        self.organisme_input.setStyleSheet(input_style)
        form_layout.addWidget(self.organisme_input, 1, 1, 1, 3)

        # Dates
        lbl_date_debut = QLabel("Date début *:")
        lbl_date_debut.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_debut, 2, 0)
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setStyleSheet(input_style)
        form_layout.addWidget(self.date_debut, 2, 1)

        lbl_date_fin = QLabel("Date fin *:")
        lbl_date_fin.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_fin, 2, 2)
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setStyleSheet(input_style)
        form_layout.addWidget(self.date_fin, 2, 3)

        # Durée et coût
        lbl_duree = QLabel("Durée (heures):")
        lbl_duree.setStyleSheet(label_style)
        form_layout.addWidget(lbl_duree, 3, 0)
        self.duree_input = QDoubleSpinBox()
        self.duree_input.setRange(0, 1000)
        self.duree_input.setDecimals(1)
        self.duree_input.setStyleSheet(input_style)
        form_layout.addWidget(self.duree_input, 3, 1)

        lbl_cout = QLabel("Coût:")
        lbl_cout.setStyleSheet(label_style)
        form_layout.addWidget(lbl_cout, 3, 2)
        self.cout_input = QDoubleSpinBox()
        self.cout_input.setRange(0, 100000)
        self.cout_input.setDecimals(2)
        self.cout_input.setSuffix(" EUR")
        self.cout_input.setStyleSheet(input_style)
        form_layout.addWidget(self.cout_input, 3, 3)

        # Statut et certificat
        lbl_statut = QLabel("Statut:")
        lbl_statut.setStyleSheet(label_style)
        form_layout.addWidget(lbl_statut, 4, 0)
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(["Planifiée", "En cours", "Terminée", "Annulée"])
        self.statut_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.statut_combo, 4, 1)

        self.certificat_check = QCheckBox("Certificat obtenu")
        self.certificat_check.setStyleSheet("color: #374151; font-size: 13px;")
        form_layout.addWidget(self.certificat_check, 4, 2, 1, 2)

        # Commentaire
        lbl_commentaire = QLabel("Commentaire:")
        lbl_commentaire.setStyleSheet(label_style)
        form_layout.addWidget(lbl_commentaire, 5, 0)
        self.commentaire_input = QTextEdit()
        self.commentaire_input.setMaximumHeight(45)
        self.commentaire_input.setStyleSheet(input_style)
        form_layout.addWidget(self.commentaire_input, 5, 1, 1, 3)

        # Document / Attestation
        lbl_document = QLabel("Document:")
        lbl_document.setStyleSheet(label_style)
        form_layout.addWidget(lbl_document, 6, 0)
        form_layout.addLayout(self._build_doc_section(input_style), 6, 1, 1, 3)

        layout.addWidget(form_group)
        layout.addStretch()

    def _browse_document(self):
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un document", "", _FILE_FILTER_ALL
        )
        self._handle_file_selection(file_path)

    def get_data(self) -> Dict:
        """Retourne les données du formulaire."""
        return {
            'intitule': self.intitule_input.text().strip(),
            'organisme': self.organisme_input.text().strip() or None,
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': self.date_fin.date().toPyDate(),
            'duree_heures': self.duree_input.value() or None,
            'cout': self.cout_input.value() or None,
            'statut': self.statut_combo.currentText(),
            'certificat_obtenu': self.certificat_check.isChecked(),
            'commentaire': self.commentaire_input.toPlainText().strip() or None,
            'document_path': self._document_path
        }

    def validate(self) -> tuple:
        """Valide les données du formulaire."""
        data = self.get_data()
        if not data['intitule']:
            return False, "L'intitulé est obligatoire"
        if data['date_debut'] > data['date_fin']:
            return False, "La date de début doit être antérieure à la date de fin"
        return True, ""
