# -*- coding: utf-8 -*-
"""
EditDeclarationDialog — formulaire d'édition/création de déclaration.
"""

from PyQt5.QtWidgets import QFormLayout, QComboBox, QDateEdit, QTextEdit
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
        min_h = 350 if self.is_edit else 490
        super().__init__(title=title, min_width=400, min_height=min_h, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(12)

        self.type_combo = QComboBox()
        self.type_combo.addItems(get_types_declaration())
        if self.declaration and self.declaration.get('type_declaration'):
            idx = self.type_combo.findText(self.declaration['type_declaration'])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        form.addRow("Type:", self.type_combo)

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setDate(QDate.currentDate())
        if self.declaration and self.declaration.get('date_debut'):
            d = self.declaration['date_debut']
            self.date_debut.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de début:", self.date_debut)

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setDate(QDate.currentDate())
        if self.declaration and self.declaration.get('date_fin'):
            d = self.declaration['date_fin']
            self.date_fin.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de fin:", self.date_fin)

        self.motif = QTextEdit()
        self.motif.setMaximumHeight(80)
        if self.declaration and self.declaration.get('motif'):
            self.motif.setText(self.declaration['motif'])
        form.addRow("Motif:", self.motif)

        self.content_layout.addLayout(form)

        if not self.is_edit:
            self._ajouter_section_justificatif("Attestations")

    def validate(self):
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
            success, message, _ = create_declaration(self.operateur_id, data)
            if success:
                self._sauvegarder_justificatif(self.operateur_id)

        if not success:
            raise Exception(message)
