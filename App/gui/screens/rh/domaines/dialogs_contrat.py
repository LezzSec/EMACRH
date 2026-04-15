# -*- coding: utf-8 -*-
"""
EditContratDialog — formulaire d'édition/création de contrat.
"""

from PyQt5.QtWidgets import QFormLayout, QComboBox, QDateEdit, QDoubleSpinBox, QLineEdit
from PyQt5.QtCore import QDate

from gui.components.emac_dialog import EmacFormDialog
from gui.screens.rh.domaines.dialogs_shared import JustificatifMixin
from domain.services.rh.rh_service import create_contrat, update_contrat


class EditContratDialog(JustificatifMixin, EmacFormDialog):
    """Formulaire d'édition/création de contrat."""

    def __init__(self, operateur_id: int, contrat: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.contrat = contrat
        self.is_edit = contrat is not None
        title = "Modifier le contrat" if self.is_edit else "Nouveau contrat"
        min_h = 400 if self.is_edit else 530
        super().__init__(title=title, min_width=450, min_height=min_h, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(12)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            'CDI', 'CDD', 'Intérimaire', 'Apprentissage', 'Stagiaire',
            'Mise à disposition GE', 'Etranger hors UE', 'Temps partiel',
            'CIFRE', 'Avenant contrat'
        ])
        if self.contrat and self.contrat.get('type_contrat'):
            idx = self.type_combo.findText(self.contrat['type_contrat'])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        form.addRow("Type de contrat:", self.type_combo)

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setDate(QDate.currentDate())
        if self.contrat and self.contrat.get('date_debut'):
            d = self.contrat['date_debut']
            self.date_debut.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de début:", self.date_debut)

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setSpecialValueText("Indéterminée (CDI)")
        self.date_fin.setMinimumDate(QDate(1900, 1, 1))
        if self.contrat and self.contrat.get('date_fin'):
            d = self.contrat['date_fin']
            self.date_fin.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_fin.setDate(QDate(1900, 1, 1))
        form.addRow("Date de fin:", self.date_fin)

        self.etp = QDoubleSpinBox()
        self.etp.setRange(0.01, 1.0)
        self.etp.setSingleStep(0.1)
        self.etp.setValue(float(self.contrat.get('etp', 1.0)) if self.contrat else 1.0)
        form.addRow("ETP:", self.etp)

        self.categorie = QLineEdit(self.contrat.get('categorie', '') if self.contrat else '')
        form.addRow("Catégorie:", self.categorie)

        self.emploi = QLineEdit(self.contrat.get('emploi', '') if self.contrat else '')
        form.addRow("Emploi:", self.emploi)

        self.salaire = QDoubleSpinBox()
        self.salaire.setRange(0, 999999.99)
        self.salaire.setSuffix(" €")
        if self.contrat and self.contrat.get('salaire'):
            self.salaire.setValue(float(self.contrat['salaire']))
        form.addRow("Salaire brut:", self.salaire)

        self.content_layout.addLayout(form)

        if not self.is_edit:
            self._ajouter_section_justificatif("Contrats de travail")

    def validate(self):
        if not self.is_edit:
            ok, msg = self._valider_justificatif()
            if not ok:
                return False, msg
        return True, ""

    def save_to_db(self):
        date_fin = self.date_fin.date()
        data = {
            'type_contrat': self.type_combo.currentText(),
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': date_fin.toPyDate() if date_fin.year() > 1900 else None,
            'etp': self.etp.value(),
            'categorie': self.categorie.text().strip() or None,
            'emploi': self.emploi.text().strip() or None,
            'salaire': self.salaire.value() if self.salaire.value() > 0 else None,
        }

        if self.is_edit:
            success, message = update_contrat(self.contrat['id'], data)
        else:
            success, message, _ = create_contrat(self.operateur_id, data)
            if success:
                self._sauvegarder_justificatif(self.operateur_id)

        if not success:
            raise Exception(message)
