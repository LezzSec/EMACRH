# -*- coding: utf-8 -*-
"""
EditCompetenceDialog — formulaire d'édition/création d'une compétence assignée.
"""

from PyQt5.QtWidgets import QFormLayout, QComboBox, QDateEdit, QTextEdit, QLabel
from PyQt5.QtCore import QDate

from gui.components.emac_dialog import EmacFormDialog
from domain.services.rh import competences_service as _competences_service
from domain.services.rh.rh_service import create_competence_personnel

get_catalogue_competences = _competences_service.get_all_competences
update_competence_personnel = _competences_service.update_assignment


class EditCompetenceDialog(EmacFormDialog):
    """Formulaire d'édition/création d'une compétence assignée."""

    def __init__(self, operateur_id: int, competence: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.competence = competence
        self.is_edit = competence is not None
        title = "Modifier la compétence" if self.is_edit else "Nouvelle compétence"
        super().__init__(title=title, min_width=450, min_height=400, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(12)

        self.competence_combo = QComboBox()
        self.competence_combo.setMinimumWidth(300)
        self._charger_catalogue()
        self.competence_combo.currentIndexChanged.connect(self._on_competence_changed)

        if self.is_edit:
            self.competence_combo.setEnabled(False)
            for i in range(self.competence_combo.count()):
                if self.competence_combo.itemData(i) and \
                   self.competence_combo.itemData(i).get('id') == self.competence.get('competence_id'):
                    self.competence_combo.setCurrentIndex(i)
                    break

        form.addRow("Compétence:", self.competence_combo)

        self.date_acquisition = QDateEdit()
        self.date_acquisition.setCalendarPopup(True)
        self.date_acquisition.setDisplayFormat("dd/MM/yyyy")
        self.date_acquisition.setDate(QDate.currentDate())
        if self.competence and self.competence.get('date_acquisition'):
            d = self.competence['date_acquisition']
            self.date_acquisition.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date d'acquisition:", self.date_acquisition)

        self.date_expiration = QDateEdit()
        self.date_expiration.setCalendarPopup(True)
        self.date_expiration.setDisplayFormat("dd/MM/yyyy")
        self.date_expiration.setSpecialValueText("Permanent (pas d'expiration)")
        self.date_expiration.setMinimumDate(QDate(1900, 1, 1))
        if self.competence and self.competence.get('date_expiration'):
            d = self.competence['date_expiration']
            self.date_expiration.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_expiration.setDate(QDate(1900, 1, 1))
        form.addRow("Date d'expiration:", self.date_expiration)

        self.validite_info = QLabel("")
        self.validite_info.setStyleSheet("color: #64748b; font-style: italic;")
        form.addRow("", self.validite_info)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(80)
        self.commentaire.setPlaceholderText("Commentaire optionnel...")
        if self.competence and self.competence.get('commentaire'):
            self.commentaire.setText(self.competence['commentaire'])
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addLayout(form)
        self._on_competence_changed()

    def _charger_catalogue(self):
        """Charge le catalogue des compétences dans le combo."""
        self.competence_combo.clear()
        self.competence_combo.addItem("-- Sélectionner une compétence --", None)

        catalogue = get_catalogue_competences(actif_only=True)

        categories = {}
        for comp in catalogue:
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

    def _on_competence_changed(self):
        """Met à jour l'info de validité quand la compétence change."""
        comp_data = self.competence_combo.currentData()
        if comp_data and comp_data.get('duree_validite_mois'):
            mois = comp_data['duree_validite_mois']
            self.validite_info.setText(f"Validité standard: {mois} mois")

            if not self.is_edit:
                date_acq = self.date_acquisition.date().toPyDate()
                from dateutil.relativedelta import relativedelta
                date_exp = date_acq + relativedelta(months=mois)
                self.date_expiration.setDate(QDate(date_exp.year, date_exp.month, date_exp.day))
        else:
            self.validite_info.setText("Compétence permanente (pas d'expiration)")
            if not self.is_edit:
                self.date_expiration.setDate(QDate(1900, 1, 1))

    def validate(self):
        if not self.competence_combo.currentData():
            return False, "Veuillez sélectionner une compétence"
        return True, ""

    def save_to_db(self):
        comp_data = self.competence_combo.currentData()
        date_exp = self.date_expiration.date()
        data = {
            'competence_id': comp_data['id'],
            'date_acquisition': self.date_acquisition.date().toPyDate(),
            'date_expiration': date_exp.toPyDate() if date_exp.year() > 1900 else None,
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_competence_personnel(self.competence['assignment_id'], data)
        else:
            success, message, _ = create_competence_personnel(self.operateur_id, data)

        if not success:
            raise Exception(message)
