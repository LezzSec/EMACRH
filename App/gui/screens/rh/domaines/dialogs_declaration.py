# -*- coding: utf-8 -*-
"""
EditDeclarationDialog - formulaire d'édition/création de déclaration.
"""

from PyQt5.QtWidgets import QFormLayout, QComboBox, QDateEdit, QTextEdit, QGroupBox, QLabel
from PyQt5.QtCore import QDate

from gui.components.emac_dialog import EmacFormDialog
from gui.screens.rh.domaines.dialogs_shared import JustificatifMixin
from domain.services.rh.declaration_service_crud import DeclarationServiceCRUD as _DeclSvc
from domain.services.rh.rh_service import create_declaration, update_declaration

get_types_declaration = _DeclSvc.get_types_declaration


class EditDeclarationDialog(JustificatifMixin, EmacFormDialog):
    """Formulaire d'édition/création de déclaration."""

    def __init__(self, operateur_id: int, declaration: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.declaration = declaration
        self.is_edit = declaration is not None
        title = "Modifier la déclaration" if self.is_edit else "Nouvelle déclaration"
        min_h = 440 if self.is_edit else 590
        super().__init__(title=title, min_width=460, min_height=min_h, add_title_bar=False, parent=parent)

    def init_ui(self):
        situation_group = QGroupBox("Nature de la déclaration")
        situation_form = QFormLayout(situation_group)
        situation_form.setSpacing(10)

        self.type_combo = QComboBox()
        self.type_combo.addItems(get_types_declaration())
        if self.declaration and self.declaration.get('type_declaration'):
            idx = self.type_combo.findText(self.declaration['type_declaration'])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        situation_form.addRow("Type :", self.type_combo)

        self.motif = QTextEdit()
        self.motif.setMaximumHeight(90)
        self.motif.setPlaceholderText("Motif, contexte ou référence interne")
        if self.declaration and self.declaration.get('motif'):
            self.motif.setText(self.declaration['motif'])
        situation_form.addRow("Motif :", self.motif)
        self.content_layout.addWidget(situation_group)

        periode_group = QGroupBox("Période concernée")
        periode_form = QFormLayout(periode_group)
        periode_form.setSpacing(10)

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setDate(QDate.currentDate())
        if self.declaration and self.declaration.get('date_debut'):
            d = self.declaration['date_debut']
            self.date_debut.setDate(QDate(d.year, d.month, d.day))
        self.date_debut.dateChanged.connect(self._update_apercu)
        periode_form.addRow("Début :", self.date_debut)

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setDate(QDate.currentDate())
        if self.declaration and self.declaration.get('date_fin'):
            d = self.declaration['date_fin']
            self.date_fin.setDate(QDate(d.year, d.month, d.day))
        self.date_fin.dateChanged.connect(self._update_apercu)
        periode_form.addRow("Fin :", self.date_fin)

        self.apercu = QLabel()
        self.apercu.setStyleSheet(
            "padding: 8px 10px; background: #f8fafc; border: 1px solid #e2e8f0; "
            "border-radius: 6px; color: #475569;"
        )
        periode_form.addRow("", self.apercu)
        self.content_layout.addWidget(periode_group)

        if not self.is_edit:
            self._ajouter_section_justificatif("Documents d'absence")

        self._update_apercu()

    def _update_apercu(self):
        debut = self.date_debut.date()
        fin = self.date_fin.date()
        jours = debut.daysTo(fin) + 1
        if jours <= 0:
            self.apercu.setText("La date de fin doit être postérieure ou égale au début.")
            self.apercu.setStyleSheet(
                "padding: 8px 10px; background: #fef2f2; border: 1px solid #fecaca; "
                "border-radius: 6px; color: #991b1b;"
            )
        else:
            self.apercu.setText(f"Période déclarée : {jours} jour(s) calendaires.")
            self.apercu.setStyleSheet(
                "padding: 8px 10px; background: #f8fafc; border: 1px solid #e2e8f0; "
                "border-radius: 6px; color: #475569;"
            )

    def validate(self):
        if self.date_fin.date() < self.date_debut.date():
            return False, "La date de fin doit être postérieure ou égale à la date de début."
        if not self.is_edit:
            ok, msg = self._valider_justificatif()
            if not ok:
                return False, msg
        return True, ""

    def save_to_db(self):
        data = {
            'type_declaration': self.type_combo.currentText(),
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': self.date_fin.date().toPyDate(),
            'motif': self.motif.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_declaration(self.declaration['id'], data)
        else:
            success, message, new_id = create_declaration(self.operateur_id, data)
            if success:
                self._sauvegarder_justificatif(self.operateur_id, declaration_id=new_id)

        if not success:
            raise Exception(message)
