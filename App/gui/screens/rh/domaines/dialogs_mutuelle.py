# -*- coding: utf-8 -*-
"""
EditMutuelleDialog — formulaire pour ajouter ou modifier un enregistrement mutuelle.
"""

from PyQt5.QtWidgets import QFormLayout, QComboBox, QLineEdit, QDateEdit, QTextEdit
from PyQt5.QtCore import QDate

from gui.components.emac_dialog import EmacFormDialog
from domain.services.rh.mutuelle_service import create_mutuelle, update_mutuelle


class EditMutuelleDialog(EmacFormDialog):
    """Formulaire pour ajouter ou modifier un enregistrement mutuelle."""

    STATUTS = ['NON_COUVERT', 'ADHERENT', 'DISPENSE']
    STATUTS_LABELS = {
        'NON_COUVERT': 'Non couvert',
        'ADHERENT': 'Adhérent',
        'DISPENSE': 'Dispensé',
    }
    TYPES_DISPENSE = [
        '',
        'CDD',
        'Temps partiel',
        'Ayant droit',
        'Couverture personnelle',
        'Autre',
    ]
    REGIMES = ['', 'INDIVIDUEL', 'FAMILLE', 'ISOLE_ENFANT']
    REGIMES_LABELS = {
        '': '-',
        'INDIVIDUEL': 'Individuel',
        'FAMILLE': 'Famille',
        'ISOLE_ENFANT': 'Isolé + enfant(s)',
    }

    def __init__(self, operateur_id: int, mutuelle: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.mutuelle = mutuelle or {}
        self.is_edit = bool(mutuelle)
        title = "Modifier la mutuelle" if self.is_edit else "Nouvelle mutuelle"
        super().__init__(title=title, min_width=460, min_height=400, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(10)

        self.statut_combo = QComboBox()
        for val in self.STATUTS:
            self.statut_combo.addItem(self.STATUTS_LABELS[val], val)
        statut_actuel = self.mutuelle.get('statut_adhesion', 'NON_COUVERT')
        idx = self.statut_combo.findData(statut_actuel)
        if idx >= 0:
            self.statut_combo.setCurrentIndex(idx)
        self.statut_combo.currentIndexChanged.connect(self._on_statut_changed)
        form.addRow("Statut d'adhésion:", self.statut_combo)

        self.dispense_combo = QComboBox()
        for t in self.TYPES_DISPENSE:
            self.dispense_combo.addItem(t if t else '-', t)
        dispense_actuelle = self.mutuelle.get('type_dispense') or ''
        idx_d = self.dispense_combo.findData(dispense_actuelle)
        if idx_d >= 0:
            self.dispense_combo.setCurrentIndex(idx_d)
        form.addRow("Type de dispense:", self.dispense_combo)

        self.organisme = QLineEdit()
        self.organisme.setPlaceholderText("Ex: Harmonie Mutuelle, AG2R...")
        self.organisme.setText(self.mutuelle.get('organisme') or '')
        form.addRow("Organisme:", self.organisme)

        self.numero_adherent = QLineEdit()
        self.numero_adherent.setPlaceholderText("Numéro d'adhérent")
        self.numero_adherent.setText(self.mutuelle.get('numero_adherent') or '')
        form.addRow("N° adhérent:", self.numero_adherent)

        self.regime_combo = QComboBox()
        for val in self.REGIMES:
            self.regime_combo.addItem(self.REGIMES_LABELS[val], val)
        regime_actuel = self.mutuelle.get('regime') or ''
        idx_r = self.regime_combo.findData(regime_actuel)
        if idx_r >= 0:
            self.regime_combo.setCurrentIndex(idx_r)
        form.addRow("Régime:", self.regime_combo)

        self.date_adhesion = QDateEdit()
        self.date_adhesion.setCalendarPopup(True)
        self.date_adhesion.setDisplayFormat("dd/MM/yyyy")
        self.date_adhesion.setSpecialValueText("Non définie")
        d_adh = self.mutuelle.get('date_adhesion')
        if d_adh:
            self.date_adhesion.setDate(QDate(d_adh.year, d_adh.month, d_adh.day))
        form.addRow("Date d'adhésion:", self.date_adhesion)

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setSpecialValueText("Non définie")
        d_fin = self.mutuelle.get('date_fin')
        if d_fin:
            self.date_fin.setDate(QDate(d_fin.year, d_fin.month, d_fin.day))
        form.addRow("Date de fin:", self.date_fin)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(70)
        self.commentaire.setPlaceholderText("Commentaire libre")
        self.commentaire.setText(self.mutuelle.get('commentaire') or '')
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addLayout(form)
        self._on_statut_changed()

    def _on_statut_changed(self):
        statut = self.statut_combo.currentData()
        is_dispense = statut == 'DISPENSE'
        is_adherent = statut == 'ADHERENT'
        self.dispense_combo.setEnabled(is_dispense)
        self.organisme.setEnabled(is_adherent)
        self.numero_adherent.setEnabled(is_adherent)
        self.regime_combo.setEnabled(is_adherent)
        self.date_adhesion.setEnabled(is_adherent or is_dispense)
        self.date_fin.setEnabled(is_adherent or is_dispense)

    def validate(self):
        statut = self.statut_combo.currentData()
        if statut == 'ADHERENT' and not self.organisme.text().strip():
            return False, "L'organisme est obligatoire pour un adhérent."
        return True, ""

    def save_to_db(self):
        statut = self.statut_combo.currentData()
        d_adh = self.date_adhesion.date()
        d_fin = self.date_fin.date()
        data = {
            'statut_adhesion': statut,
            'type_dispense': self.dispense_combo.currentData() if statut == 'DISPENSE' else None,
            'organisme': self.organisme.text().strip() or None,
            'numero_adherent': self.numero_adherent.text().strip() or None,
            'regime': self.regime_combo.currentData() or None,
            'date_adhesion': d_adh.toPyDate() if d_adh.year() > 1900 else None,
            'date_fin': d_fin.toPyDate() if d_fin.year() > 1900 else None,
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_mutuelle(self.mutuelle['id'], data)
        else:
            success, message, _ = create_mutuelle(self.operateur_id, data)

        if not success:
            raise Exception(message)
