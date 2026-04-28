# -*- coding: utf-8 -*-
"""
EditCompetenceDialog - formulaire d'édition/création d'une compétence assignée.
"""

from PyQt5.QtWidgets import QFormLayout, QComboBox, QDateEdit, QTextEdit, QLabel, QGroupBox
from PyQt5.QtCore import QDate

from gui.components.emac_dialog import EmacFormDialog
from gui.screens.rh.domaines.dialogs_shared import JustificatifMixin
from domain.services.rh import competences_service as _competences_service
from domain.services.rh.rh_service import create_competence_personnel

get_catalogue_competences = _competences_service.get_all_competences
update_competence_personnel = _competences_service.update_assignment


class EditCompetenceDialog(JustificatifMixin, EmacFormDialog):
    """Formulaire d'édition/création d'une compétence assignée."""

    def __init__(self, operateur_id: int, competence: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.competence = competence
        self.is_edit = competence is not None
        title = "Modifier la compétence" if self.is_edit else "Nouvelle compétence"
        super().__init__(title=title, min_width=500, min_height=560, add_title_bar=False, parent=parent)

    def init_ui(self):
        competence_group = QGroupBox("Compétence")
        competence_form = QFormLayout(competence_group)
        competence_form.setSpacing(10)

        self.competence_combo = QComboBox()
        self.competence_combo.setMinimumWidth(340)
        self._charger_catalogue()
        self.competence_combo.currentIndexChanged.connect(self._on_competence_changed)

        if self.is_edit:
            self.competence_combo.setEnabled(False)
            for i in range(self.competence_combo.count()):
                item_data = self.competence_combo.itemData(i)
                if item_data and item_data.get('id') == self.competence.get('competence_id'):
                    self.competence_combo.setCurrentIndex(i)
                    break

        competence_form.addRow("Compétence :", self.competence_combo)

        self.validite_info = QLabel("")
        self.validite_info.setStyleSheet(
            "padding: 8px 10px; background: #f8fafc; border: 1px solid #e2e8f0; "
            "border-radius: 6px; color: #475569;"
        )
        self.validite_info.setWordWrap(True)
        competence_form.addRow("", self.validite_info)
        self.content_layout.addWidget(competence_group)

        periode_group = QGroupBox("Dates et validité")
        periode_form = QFormLayout(periode_group)
        periode_form.setSpacing(10)

        self.date_acquisition = QDateEdit()
        self.date_acquisition.setCalendarPopup(True)
        self.date_acquisition.setDisplayFormat("dd/MM/yyyy")
        self.date_acquisition.setDate(QDate.currentDate())
        if self.competence and self.competence.get('date_acquisition'):
            d = self.competence['date_acquisition']
            self.date_acquisition.setDate(QDate(d.year, d.month, d.day))
        self.date_acquisition.dateChanged.connect(self._on_competence_changed)
        periode_form.addRow("Acquise le :", self.date_acquisition)

        self.date_expiration = QDateEdit()
        self.date_expiration.setCalendarPopup(True)
        self.date_expiration.setDisplayFormat("dd/MM/yyyy")
        self.date_expiration.setSpecialValueText("Permanente")
        self.date_expiration.setMinimumDate(QDate(1900, 1, 1))
        if self.competence and self.competence.get('date_expiration'):
            d = self.competence['date_expiration']
            self.date_expiration.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_expiration.setDate(QDate(1900, 1, 1))
        periode_form.addRow("Expire le :", self.date_expiration)
        self.content_layout.addWidget(periode_group)

        notes_group = QGroupBox("Commentaire")
        notes_form = QFormLayout(notes_group)
        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(90)
        self.commentaire.setPlaceholderText("Précision sur l'obtention, le périmètre ou le renouvellement")
        if self.competence and self.competence.get('commentaire'):
            self.commentaire.setText(self.competence['commentaire'])
        notes_form.addRow("Note :", self.commentaire)
        self.content_layout.addWidget(notes_group)

        self._ajouter_section_justificatif("Documents de compétences", optionnel=True)
        self._on_competence_changed()

    def _charger_catalogue(self):
        """Charge le catalogue des compétences dans le combo."""
        self.competence_combo.clear()
        self.competence_combo.addItem("-- Sélectionner une compétence --", None)

        catalogue = get_catalogue_competences(actif_only=True)
        categories = {}
        for comp in catalogue:
            cat = comp.get('categorie') or 'Autre'
            categories.setdefault(cat, []).append(comp)

        for cat in sorted(categories.keys()):
            self.competence_combo.addItem(f"--- {cat} ---", None)
            idx = self.competence_combo.count() - 1
            self.competence_combo.model().item(idx).setEnabled(False)

            for comp in categories[cat]:
                label = comp['libelle']
                if comp.get('code'):
                    label = f"{label} ({comp['code']})"
                if comp.get('duree_validite_mois'):
                    label += f" - {comp['duree_validite_mois']} mois"
                self.competence_combo.addItem(label, comp)

    def _on_competence_changed(self):
        """Met à jour l'info de validité quand la compétence ou la date change."""
        if not hasattr(self, 'validite_info') or not hasattr(self, 'date_acquisition'):
            return
        comp_data = self.competence_combo.currentData()
        if comp_data and comp_data.get('duree_validite_mois'):
            mois = comp_data['duree_validite_mois']
            self.validite_info.setText(
                f"Validité standard : {mois} mois. La date d'expiration est proposée automatiquement."
            )

            if not self.is_edit:
                date_acq = self.date_acquisition.date().toPyDate()
                from dateutil.relativedelta import relativedelta
                date_exp = date_acq + relativedelta(months=mois)
                self.date_expiration.setDate(QDate(date_exp.year, date_exp.month, date_exp.day))
        else:
            self.validite_info.setText("Compétence permanente : aucune date d'expiration obligatoire.")
            if not self.is_edit:
                self.date_expiration.setDate(QDate(1900, 1, 1))

    def validate(self):
        if not self.competence_combo.currentData():
            return False, "Veuillez sélectionner une compétence."
        exp = self.date_expiration.date()
        if exp.year() > 1900 and exp < self.date_acquisition.date():
            return False, "La date d'expiration doit être postérieure à la date d'acquisition."
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
            assignment_id = self.competence['assignment_id']
            success, message = update_competence_personnel(assignment_id, **data)
        else:
            success, message, assignment_id = create_competence_personnel(self.operateur_id, data)

        if success and getattr(self, '_justificatif_path', None):
            doc_id = self._sauvegarder_justificatif(
                self.operateur_id,
                date_expiration=data.get('date_expiration'),
                notes=f"Justificatif compétence - {comp_data.get('libelle')}",
            )
            if doc_id and assignment_id:
                update_competence_personnel(assignment_id, document_id=doc_id)

        if not success:
            raise Exception(message)
