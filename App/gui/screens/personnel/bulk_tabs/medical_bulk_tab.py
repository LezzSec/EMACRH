# -*- coding: utf-8 -*-
"""
Onglet médical pour les opérations en masse.
"""

from typing import Dict

from PyQt5.QtWidgets import (
    QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox,
    QDateEdit, QTextEdit, QGroupBox, QFileDialog,
)
from PyQt5.QtCore import QDate

from .base_bulk_tab import BulkTabBase, INPUT_STYLE_LG, LABEL_STYLE_LG, REQUIRED_STYLE, GROUPBOX_STYLE


class MedicalBulkTab(BulkTabBase):
    """Onglet pour l'ajout de visite médicale en masse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        input_style = INPUT_STYLE_LG
        label_style = LABEL_STYLE_LG
        required_style = REQUIRED_STYLE

        # === Formulaire ===
        form_group = QGroupBox("Informations de la visite médicale")
        form_group.setStyleSheet(GROUPBOX_STYLE)
        form_layout = QGridLayout(form_group)
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(12)

        # Type de visite
        lbl_type = QLabel("Type de visite *:")
        lbl_type.setStyleSheet(required_style)
        form_layout.addWidget(lbl_type, 0, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Périodique", "Embauche", "Reprise", "À la demande", "Pré-reprise"
        ])
        self.type_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.type_combo, 0, 1)

        # Date de visite
        lbl_date_visite = QLabel("Date de visite *:")
        lbl_date_visite.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_visite, 0, 2)
        self.date_visite = QDateEdit()
        self.date_visite.setDate(QDate.currentDate())
        self.date_visite.setCalendarPopup(True)
        self.date_visite.setDisplayFormat("dd/MM/yyyy")
        self.date_visite.setStyleSheet(input_style)
        form_layout.addWidget(self.date_visite, 0, 3)

        # Médecin
        lbl_medecin = QLabel("Médecin:")
        lbl_medecin.setStyleSheet(label_style)
        form_layout.addWidget(lbl_medecin, 1, 0)
        self.medecin_input = QLineEdit()
        self.medecin_input.setPlaceholderText("Nom du médecin")
        self.medecin_input.setStyleSheet(input_style)
        form_layout.addWidget(self.medecin_input, 1, 1, 1, 3)

        # Résultat
        lbl_resultat = QLabel("Résultat:")
        lbl_resultat.setStyleSheet(label_style)
        form_layout.addWidget(lbl_resultat, 2, 0)
        self.resultat_combo = QComboBox()
        self.resultat_combo.addItems([
            "", "Apte", "Apte avec restrictions", "Inapte temporaire", "Inapte définitif"
        ])
        self.resultat_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.resultat_combo, 2, 1)

        # Prochaine visite
        lbl_prochaine = QLabel("Prochaine visite:")
        lbl_prochaine.setStyleSheet(label_style)
        form_layout.addWidget(lbl_prochaine, 2, 2)
        self.prochaine_visite = QDateEdit()
        self.prochaine_visite.setDate(QDate.currentDate().addYears(1))
        self.prochaine_visite.setCalendarPopup(True)
        self.prochaine_visite.setDisplayFormat("dd/MM/yyyy")
        self.prochaine_visite.setStyleSheet(input_style)
        form_layout.addWidget(self.prochaine_visite, 2, 3)

        # Restrictions
        lbl_restrictions = QLabel("Restrictions:")
        lbl_restrictions.setStyleSheet(label_style)
        form_layout.addWidget(lbl_restrictions, 3, 0)
        self.restrictions_input = QTextEdit()
        self.restrictions_input.setMaximumHeight(60)
        self.restrictions_input.setPlaceholderText("Restrictions éventuelles...")
        self.restrictions_input.setStyleSheet(input_style)
        form_layout.addWidget(self.restrictions_input, 3, 1, 1, 3)

        # Commentaire
        lbl_commentaire = QLabel("Commentaire:")
        lbl_commentaire.setStyleSheet(label_style)
        form_layout.addWidget(lbl_commentaire, 4, 0)
        self.commentaire_input = QTextEdit()
        self.commentaire_input.setMaximumHeight(50)
        self.commentaire_input.setStyleSheet(input_style)
        form_layout.addWidget(self.commentaire_input, 4, 1, 1, 3)

        # Document / Fiche aptitude
        lbl_document = QLabel("Document:")
        lbl_document.setStyleSheet(label_style)
        form_layout.addWidget(lbl_document, 5, 0)
        form_layout.addLayout(self._build_doc_section(input_style), 5, 1, 1, 3)

        layout.addWidget(form_group)
        layout.addStretch()

    def _browse_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un document médical", "",
            "Documents (*.pdf *.doc *.docx *.png *.jpg *.jpeg);;Tous les fichiers (*)"
        )
        self._handle_file_selection(file_path)

    def get_data(self) -> Dict:
        """Retourne les données du formulaire."""
        return {
            'type_visite': self.type_combo.currentText(),
            'date_visite': self.date_visite.date().toPyDate(),
            'medecin': self.medecin_input.text().strip() or None,
            'resultat': self.resultat_combo.currentText() or None,
            'prochaine_visite': self.prochaine_visite.date().toPyDate(),
            'restrictions': self.restrictions_input.toPlainText().strip() or None,
            'commentaire': self.commentaire_input.toPlainText().strip() or None,
            'document_path': self._document_path
        }

    def validate(self) -> tuple:
        """Valide les données du formulaire."""
        data = self.get_data()
        if not data['type_visite']:
            return False, "Le type de visite est obligatoire"
        return True, ""
