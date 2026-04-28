# -*- coding: utf-8 -*-
"""
EditMutuelleDialog - formulaire pour ajouter ou modifier un enregistrement mutuelle.
"""

from pathlib import Path

from PyQt5.QtWidgets import (
    QFormLayout, QComboBox, QLineEdit, QDateEdit, QTextEdit, QGroupBox,
    QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QFileDialog, QMessageBox,
)
from PyQt5.QtCore import QDate

from application.permission_manager import can
from gui.components.ui_theme import EmacButton
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
    STATUT_HINTS = {
        'NON_COUVERT': "Aucune couverture ou dispense n'est déclarée pour le moment.",
        'ADHERENT': "Renseignez les informations présentes sur l'attestation ou le bulletin d'adhésion.",
        'DISPENSE': "Renseignez le motif de dispense et la date de validité du justificatif si elle existe.",
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
    FORMULES = ['', 'SIMPLE', 'TURBO']
    FORMULES_LABELS = {
        '': '-',
        'SIMPLE': 'Simple',
        'TURBO': 'Turbo',
    }
    SITUATIONS = ['', 'ISOLE', 'DUO', 'FAMILLE']
    SITUATIONS_LABELS = {
        '': '-',
        'ISOLE': 'Isolé',
        'DUO': 'Duo',
        'FAMILLE': 'Famille',
    }

    def __init__(self, operateur_id: int, mutuelle: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.mutuelle = mutuelle or {}
        self.is_edit = bool(mutuelle)
        self.document_path = None
        self._uploaded_doc_id = None
        title = "Modifier la mutuelle" if self.is_edit else "Déclarer une mutuelle"
        super().__init__(title=title, min_width=640, min_height=680, add_title_bar=False, parent=parent)

    def init_ui(self):
        self.content_layout.setSpacing(12)

        self._build_status_section()
        self._build_adherent_section()
        self._build_dispense_section()
        self._build_period_section()
        self._build_document_section()

        self._on_statut_changed()

    # ------------------------------------------------------------------
    # Sections UI
    # ------------------------------------------------------------------

    def _build_status_section(self):
        group = QGroupBox("Situation")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

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

        layout.addLayout(form)

        self.status_hint = QLabel()
        self.status_hint.setWordWrap(True)
        self.status_hint.setStyleSheet(
            "color: #475569; background: #f8fafc; border: 1px solid #e2e8f0; "
            "border-radius: 6px; padding: 8px 10px;"
        )
        layout.addWidget(self.status_hint)

        self.content_layout.addWidget(group)

    def _build_adherent_section(self):
        self.adherent_group = QGroupBox("Informations adhésion")
        form = QFormLayout(self.adherent_group)
        form.setSpacing(10)

        self.organisme = QLineEdit()
        self.organisme.setPlaceholderText("Ex: Harmonie Mutuelle, AG2R...")
        self.organisme.setText(self.mutuelle.get('organisme') or '')
        form.addRow("Organisme:", self.organisme)

        self.numero_adherent = QLineEdit()
        self.numero_adherent.setPlaceholderText("Numéro d'adhérent")
        self.numero_adherent.setText(self.mutuelle.get('numero_adherent') or '')
        form.addRow("N° adhérent:", self.numero_adherent)

        self.regime_combo = QComboBox()
        self._fill_combo(self.regime_combo, self.REGIMES, self.REGIMES_LABELS)
        self._select_combo_data(self.regime_combo, self.mutuelle.get('regime') or '')
        form.addRow("Régime:", self.regime_combo)

        self.formule_combo = QComboBox()
        self._fill_combo(self.formule_combo, self.FORMULES, self.FORMULES_LABELS)
        self._select_combo_data(self.formule_combo, self.mutuelle.get('type_formule') or '')
        form.addRow("Formule:", self.formule_combo)

        self.situation_combo = QComboBox()
        self._fill_combo(self.situation_combo, self.SITUATIONS, self.SITUATIONS_LABELS)
        self._select_combo_data(self.situation_combo, self.mutuelle.get('situation_familiale') or '')
        form.addRow("Situation familiale:", self.situation_combo)

        self.due_signee = QCheckBox("DUE signée / remise")
        self.due_signee.setChecked(bool(self.mutuelle.get('due_signee')))
        form.addRow("", self.due_signee)

        self.content_layout.addWidget(self.adherent_group)

    def _build_dispense_section(self):
        self.dispense_group = QGroupBox("Dispense")
        form = QFormLayout(self.dispense_group)
        form.setSpacing(10)

        self.dispense_combo = QComboBox()
        for t in self.TYPES_DISPENSE:
            self.dispense_combo.addItem(t if t else '-', t)
        self._select_combo_data(self.dispense_combo, self.mutuelle.get('type_dispense') or '')
        form.addRow("Motif de dispense:", self.dispense_combo)

        self.justificatif_validite = self._build_date_edit(
            self.mutuelle.get('justificatif_validite'),
            "Non définie",
        )
        form.addRow("Validité justificatif:", self.justificatif_validite)

        self.content_layout.addWidget(self.dispense_group)

    def _build_period_section(self):
        group = QGroupBox("Période et commentaire")
        form = QFormLayout(group)
        form.setSpacing(10)

        self.date_adhesion = self._build_date_edit(
            self.mutuelle.get('date_adhesion'),
            "Non définie",
        )
        form.addRow("Date d'adhésion:", self.date_adhesion)

        self.date_fin = self._build_date_edit(
            self.mutuelle.get('date_fin'),
            "Non définie",
        )
        form.addRow("Date de fin:", self.date_fin)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(76)
        self.commentaire.setPlaceholderText("Commentaire libre")
        self.commentaire.setText(self.mutuelle.get('commentaire') or '')
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addWidget(group)

    def _build_document_section(self):
        self.document_group = QGroupBox("Document associé")
        layout = QVBoxLayout(self.document_group)
        layout.setSpacing(8)

        if not can("rh.documents.edit"):
            note = QLabel("L'ajout de document n'est pas disponible avec vos droits actuels.")
            note.setWordWrap(True)
            note.setStyleSheet("color: #64748b;")
            layout.addWidget(note)
            self.document_group.setEnabled(False)
            self.content_layout.addWidget(self.document_group)
            return

        note = QLabel("Attestation, dispense, bulletin d'adhésion ou justificatif.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #475569;")
        layout.addWidget(note)

        file_row = QHBoxLayout()
        self.document_label = QLineEdit()
        self.document_label.setReadOnly(True)
        self.document_label.setPlaceholderText("Aucun document sélectionné")
        file_row.addWidget(self.document_label, 1)

        btn_browse = EmacButton("Parcourir...", variant="ghost")
        btn_browse.clicked.connect(self._parcourir_document)
        file_row.addWidget(btn_browse)

        btn_clear = EmacButton("Retirer", variant="ghost")
        btn_clear.clicked.connect(self._retirer_document)
        file_row.addWidget(btn_clear)
        layout.addLayout(file_row)

        form = QFormLayout()
        form.setSpacing(8)
        self.document_nom = QLineEdit()
        self.document_nom.setPlaceholderText("Nom affiché dans les documents mutuelle")
        form.addRow("Nom du document:", self.document_nom)

        self.document_expiration_auto = QCheckBox(
            "Utiliser la date de fin ou de validité comme expiration du document"
        )
        self.document_expiration_auto.setChecked(True)
        form.addRow("", self.document_expiration_auto)
        layout.addLayout(form)

        self.content_layout.addWidget(self.document_group)

    # ------------------------------------------------------------------
    # Comportement
    # ------------------------------------------------------------------

    def _on_statut_changed(self):
        statut = self.statut_combo.currentData()
        is_dispense = statut == 'DISPENSE'
        is_adherent = statut == 'ADHERENT'
        has_period = is_adherent or is_dispense

        self.adherent_group.setEnabled(is_adherent)
        self.dispense_group.setEnabled(is_dispense)
        self.date_adhesion.setEnabled(has_period)
        self.date_fin.setEnabled(has_period)

        self.status_hint.setText(self.STATUT_HINTS.get(statut, ""))

    def _parcourir_document(self):
        fichier, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un document mutuelle",
            "",
            "Documents (*.pdf *.png *.jpg *.jpeg *.docx *.doc);;Tous les fichiers (*)"
        )
        if not fichier:
            return

        self.document_path = fichier
        self.document_label.setText(fichier)
        if not self.document_nom.text().strip():
            self.document_nom.setText(Path(fichier).name)

    def _retirer_document(self):
        self.document_path = None
        self.document_label.clear()
        self.document_nom.clear()

    def validate(self):
        statut = self.statut_combo.currentData()

        if statut == 'ADHERENT' and not self.organisme.text().strip():
            return False, "L'organisme est obligatoire pour un adhérent."

        if statut == 'DISPENSE' and not self.dispense_combo.currentData():
            return False, "Le motif de dispense est obligatoire pour une dispense."

        date_adhesion = self._date_value(self.date_adhesion)
        date_fin = self._date_value(self.date_fin)
        if date_adhesion and date_fin and date_fin < date_adhesion:
            return False, "La date de fin doit être postérieure à la date d'adhésion."

        if self.document_path and not Path(self.document_path).exists():
            return False, "Le document sélectionné est introuvable."

        return True, ""

    def save_to_db(self):
        statut = self.statut_combo.currentData()
        is_adherent = statut == 'ADHERENT'
        is_dispense = statut == 'DISPENSE'
        has_period = is_adherent or is_dispense

        data = {
            'statut_adhesion': statut,
            'due_signee': self.due_signee.isChecked() if is_adherent else False,
            'type_formule': self.formule_combo.currentData() if is_adherent else None,
            'situation_familiale': self.situation_combo.currentData() if is_adherent else None,
            'type_dispense': self.dispense_combo.currentData() if is_dispense else None,
            'justificatif_validite': self._date_value(self.justificatif_validite) if is_dispense else None,
            'organisme': self.organisme.text().strip() if is_adherent else None,
            'numero_adherent': self.numero_adherent.text().strip() if is_adherent else None,
            'regime': self.regime_combo.currentData() if is_adherent else None,
            'date_adhesion': self._date_value(self.date_adhesion) if has_period else None,
            'date_fin': self._date_value(self.date_fin) if has_period else None,
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_mutuelle(self.mutuelle['id'], data)
        else:
            success, message, _ = create_mutuelle(self.operateur_id, data)

        if not success:
            raise Exception(message)

        self._sauvegarder_document_associe(statut)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fill_combo(combo: QComboBox, values: list, labels: dict):
        for val in values:
            combo.addItem(labels.get(val, val), val)

    @staticmethod
    def _select_combo_data(combo: QComboBox, value):
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    @staticmethod
    def _to_qdate(value) -> QDate:
        if not value:
            return QDate(1900, 1, 1)

        if isinstance(value, str):
            parsed = QDate.fromString(value, "yyyy-MM-dd")
            return parsed if parsed.isValid() else QDate(1900, 1, 1)

        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            return QDate(value.year, value.month, value.day)

        return QDate(1900, 1, 1)

    def _build_date_edit(self, value, special_text: str) -> QDateEdit:
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("dd/MM/yyyy")
        date_edit.setMinimumDate(QDate(1900, 1, 1))
        date_edit.setSpecialValueText(special_text)
        date_edit.setDate(self._to_qdate(value))
        return date_edit

    @staticmethod
    def _date_value(date_edit: QDateEdit):
        date_value = date_edit.date()
        if date_value.year() <= 1900:
            return None
        return date_value.toPyDate()

    def _document_expiration_date(self, statut: str):
        if not getattr(self, 'document_expiration_auto', None):
            return None
        if not self.document_expiration_auto.isChecked():
            return None

        if statut == 'DISPENSE':
            return self._date_value(self.justificatif_validite) or self._date_value(self.date_fin)
        if statut == 'ADHERENT':
            return self._date_value(self.date_fin)
        return None

    def _categorie_mutuelle_id(self):
        from domain.services.rh.rh_service import get_categories_documents

        categories = get_categories_documents()
        for cat in categories:
            if cat.get('nom') == 'Documents mutuelle':
                return cat.get('id')

        for cat in categories:
            if 'mutuelle' in (cat.get('nom') or '').lower():
                return cat.get('id')

        return None

    def _sauvegarder_document_associe(self, statut: str):
        if not self.document_path:
            return

        categorie_id = self._categorie_mutuelle_id()
        if not categorie_id:
            QMessageBox.warning(
                self,
                "Document non ajouté",
                "La mutuelle a été enregistrée, mais la catégorie Documents mutuelle est introuvable.",
            )
            return

        from domain.services.documents.document_service import DocumentService
        from domain.services.admin.auth_service import get_current_user

        user = get_current_user()
        uploaded_by = user.get('nom_complet', 'Utilisateur') if user else 'Utilisateur'
        nom_affichage = self.document_nom.text().strip() or Path(self.document_path).name

        doc_service = DocumentService()
        success, message, doc_id = doc_service.add_document(
            personnel_id=self.operateur_id,
            categorie_id=categorie_id,
            fichier_source=self.document_path,
            nom_affichage=nom_affichage,
            date_expiration=self._document_expiration_date(statut),
            notes="Document ajouté depuis la déclaration mutuelle",
            uploaded_by=uploaded_by,
        )

        if success:
            self._uploaded_doc_id = doc_id
            return

        QMessageBox.warning(
            self,
            "Document non ajouté",
            f"La mutuelle a été enregistrée, mais le document n'a pas pu être ajouté.\n\n{message}",
        )
