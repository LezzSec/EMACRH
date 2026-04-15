# -*- coding: utf-8 -*-
"""
Dialogs vie du salarié :
  - EditSanctionDialog
  - EditControleAlcoolDialog
  - EditTestSalivaireDialog
  - EditEntretienDialog
"""

from PyQt5.QtWidgets import (
    QFormLayout, QComboBox, QDateEdit, QTextEdit, QDoubleSpinBox, QCheckBox
)
from PyQt5.QtCore import QDate

from gui.components.emac_dialog import EmacFormDialog
from gui.screens.rh.domaines.dialogs_shared import JustificatifMixin
from domain.services.rh.vie_salarie_service import (
    create_sanction, update_sanction,
    create_controle_alcool, create_test_salivaire,
    create_entretien, update_entretien,
    get_types_sanction, get_types_entretien, get_managers_liste,
)


class EditSanctionDialog(JustificatifMixin, EmacFormDialog):
    """Formulaire pour ajouter/modifier une sanction."""

    def __init__(self, operateur_id: int, sanction: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.sanction = sanction
        self.is_edit = sanction is not None
        title = "Modifier la sanction" if self.is_edit else "Nouvelle sanction"
        min_h = 400 if self.is_edit else 540
        super().__init__(title=title, min_width=450, min_height=min_h, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(10)

        self.date_sanction = QDateEdit()
        self.date_sanction.setCalendarPopup(True)
        self.date_sanction.setDisplayFormat("dd/MM/yyyy")
        if self.is_edit and self.sanction.get('date_sanction'):
            d = self.sanction['date_sanction']
            self.date_sanction.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_sanction.setDate(QDate.currentDate())
        form.addRow("Date:", self.date_sanction)

        self.type_combo = QComboBox()
        self.type_combo.addItems(get_types_sanction())
        if self.is_edit and self.sanction.get('type_sanction'):
            idx = self.type_combo.findText(self.sanction['type_sanction'])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        form.addRow("Type:", self.type_combo)

        self.duree = QDoubleSpinBox()
        self.duree.setRange(0, 30)
        self.duree.setDecimals(0)
        self.duree.setSuffix(" jours")
        if self.is_edit and self.sanction.get('duree_jours'):
            self.duree.setValue(self.sanction['duree_jours'])
        form.addRow("Durée (mise à pied):", self.duree)

        self.motif = QTextEdit()
        self.motif.setMaximumHeight(80)
        self.motif.setPlaceholderText("Motif de la sanction")
        if self.is_edit:
            self.motif.setText(self.sanction.get('motif') or '')
        form.addRow("Motif:", self.motif)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(60)
        if self.is_edit:
            self.commentaire.setText(self.sanction.get('commentaire') or '')
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addLayout(form)

        if not self.is_edit:
            self._ajouter_section_justificatif("Sanctions disciplinaires")

    def validate(self):
        if not self.is_edit:
            ok, msg = self._valider_justificatif()
            if not ok:
                return False, msg
        return True, ""

    def save_to_db(self):
        data = {
            'date_sanction': self.date_sanction.date().toPyDate(),
            'type_sanction': self.type_combo.currentText(),
            'duree_jours': int(self.duree.value()) if self.duree.value() > 0 else None,
            'motif': self.motif.toPlainText().strip() or None,
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_sanction(self.sanction['id'], data)
        else:
            success, message, _ = create_sanction(self.operateur_id, data)
            if success:
                self._sauvegarder_justificatif(self.operateur_id)

        if not success:
            raise Exception(message)


class EditControleAlcoolDialog(EmacFormDialog):
    """Formulaire pour ajouter un contrôle d'alcoolémie."""

    def __init__(self, operateur_id: int, parent=None):
        self.operateur_id = operateur_id
        super().__init__(title="Nouveau contrôle d'alcoolémie", min_width=400, min_height=350, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(10)

        self.date_controle = QDateEdit()
        self.date_controle.setCalendarPopup(True)
        self.date_controle.setDisplayFormat("dd/MM/yyyy")
        self.date_controle.setDate(QDate.currentDate())
        form.addRow("Date:", self.date_controle)

        self.resultat_combo = QComboBox()
        self.resultat_combo.addItems(['Négatif', 'Positif'])
        self.resultat_combo.currentTextChanged.connect(self._on_resultat_change)
        form.addRow("Résultat:", self.resultat_combo)

        self.taux = QDoubleSpinBox()
        self.taux.setRange(0, 5)
        self.taux.setDecimals(2)
        self.taux.setSuffix(" g/L")
        self.taux.setEnabled(False)
        form.addRow("Taux:", self.taux)

        self.type_combo = QComboBox()
        self.type_combo.addItems(['Aléatoire', 'Ciblé', 'Accident'])
        form.addRow("Type de contrôle:", self.type_combo)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(60)
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addLayout(form)

    def _on_resultat_change(self, text):
        self.taux.setEnabled(text == 'Positif')

    def save_to_db(self):
        from datetime import datetime
        date_val = self.date_controle.date().toPyDate()
        data = {
            'date_controle': datetime.combine(date_val, datetime.now().time()),
            'resultat': self.resultat_combo.currentText(),
            'taux': self.taux.value() if self.resultat_combo.currentText() == 'Positif' else None,
            'type_controle': self.type_combo.currentText(),
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        success, message, _ = create_controle_alcool(self.operateur_id, data)
        if not success:
            raise Exception(message)


class EditTestSalivaireDialog(EmacFormDialog):
    """Formulaire pour ajouter un test salivaire."""

    def __init__(self, operateur_id: int, parent=None):
        self.operateur_id = operateur_id
        super().__init__(title="Nouveau test salivaire", min_width=400, min_height=300, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(10)

        self.date_test = QDateEdit()
        self.date_test.setCalendarPopup(True)
        self.date_test.setDisplayFormat("dd/MM/yyyy")
        self.date_test.setDate(QDate.currentDate())
        form.addRow("Date:", self.date_test)

        self.resultat_combo = QComboBox()
        self.resultat_combo.addItems(['Négatif', 'Positif', 'Non concluant'])
        form.addRow("Résultat:", self.resultat_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(['Aléatoire', 'Ciblé', 'Accident'])
        form.addRow("Type de contrôle:", self.type_combo)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(60)
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addLayout(form)

    def save_to_db(self):
        from datetime import datetime
        date_val = self.date_test.date().toPyDate()
        data = {
            'date_test': datetime.combine(date_val, datetime.now().time()),
            'resultat': self.resultat_combo.currentText(),
            'type_controle': self.type_combo.currentText(),
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        success, message, _ = create_test_salivaire(self.operateur_id, data)
        if not success:
            raise Exception(message)


class EditEntretienDialog(EmacFormDialog):
    """Formulaire pour ajouter/modifier un entretien professionnel."""

    def __init__(self, operateur_id: int, entretien: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.entretien = entretien
        self.is_edit = entretien is not None
        title = "Modifier l'entretien" if self.is_edit else "Nouvel entretien"
        super().__init__(title=title, min_width=500, min_height=500, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(10)

        self.date_entretien = QDateEdit()
        self.date_entretien.setCalendarPopup(True)
        self.date_entretien.setDisplayFormat("dd/MM/yyyy")
        if self.is_edit and self.entretien.get('date_entretien'):
            d = self.entretien['date_entretien']
            self.date_entretien.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_entretien.setDate(QDate.currentDate())
        form.addRow("Date:", self.date_entretien)

        self.type_combo = QComboBox()
        self.type_combo.addItems(get_types_entretien())
        if self.is_edit and self.entretien.get('type_entretien'):
            idx = self.type_combo.findText(self.entretien['type_entretien'])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        form.addRow("Type:", self.type_combo)

        self.manager_combo = QComboBox()
        self.manager_combo.addItem("-- Sélectionner --", None)
        managers = get_managers_liste()
        for m in managers:
            self.manager_combo.addItem(m['nom_complet'], m['id'])
        if self.is_edit and self.entretien.get('manager_id'):
            for i in range(self.manager_combo.count()):
                if self.manager_combo.itemData(i) == self.entretien['manager_id']:
                    self.manager_combo.setCurrentIndex(i)
                    break
        form.addRow("Manager:", self.manager_combo)

        self.objectifs_atteints = QTextEdit()
        self.objectifs_atteints.setMaximumHeight(60)
        self.objectifs_atteints.setPlaceholderText("Évaluation des objectifs précédents")
        if self.is_edit:
            self.objectifs_atteints.setText(self.entretien.get('objectifs_atteints') or '')
        form.addRow("Objectifs atteints:", self.objectifs_atteints)

        self.objectifs_fixes = QTextEdit()
        self.objectifs_fixes.setMaximumHeight(60)
        self.objectifs_fixes.setPlaceholderText("Objectifs pour la période à venir")
        if self.is_edit:
            self.objectifs_fixes.setText(self.entretien.get('objectifs_fixes') or '')
        form.addRow("Objectifs fixés:", self.objectifs_fixes)

        self.besoins_formation = QTextEdit()
        self.besoins_formation.setMaximumHeight(50)
        if self.is_edit:
            self.besoins_formation.setText(self.entretien.get('besoins_formation') or '')
        form.addRow("Besoins formation:", self.besoins_formation)

        self.prochaine_date = QDateEdit()
        self.prochaine_date.setCalendarPopup(True)
        self.prochaine_date.setDisplayFormat("dd/MM/yyyy")
        self.prochaine_date.setSpecialValueText("Non définie")
        if self.is_edit and self.entretien.get('prochaine_date'):
            d = self.entretien['prochaine_date']
            self.prochaine_date.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Prochain entretien:", self.prochaine_date)

        self.content_layout.addLayout(form)

    def save_to_db(self):
        prochaine = self.prochaine_date.date()
        data = {
            'date_entretien': self.date_entretien.date().toPyDate(),
            'type_entretien': self.type_combo.currentText(),
            'manager_id': self.manager_combo.currentData(),
            'objectifs_atteints': self.objectifs_atteints.toPlainText().strip() or None,
            'objectifs_fixes': self.objectifs_fixes.toPlainText().strip() or None,
            'besoins_formation': self.besoins_formation.toPlainText().strip() or None,
            'prochaine_date': prochaine.toPyDate() if prochaine.year() > 1900 else None,
        }

        if self.is_edit:
            success, message = update_entretien(self.entretien['id'], data)
        else:
            success, message, _ = create_entretien(self.operateur_id, data)

        if not success:
            raise Exception(message)
