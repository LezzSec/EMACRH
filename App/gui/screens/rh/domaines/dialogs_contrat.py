# -*- coding: utf-8 -*-
"""
EditContratDialog - formulaire d'édition/création de contrat.
"""

from pathlib import Path

from PyQt5.QtWidgets import (
    QFormLayout, QComboBox, QDateEdit, QDoubleSpinBox, QLineEdit,
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import QDate

from application.permission_manager import can
from gui.components.ui_theme import EmacButton
from gui.components.emac_dialog import EmacFormDialog
from domain.services.rh.rh_service import create_contrat, update_contrat


class EditContratDialog(EmacFormDialog):
    """Formulaire d'édition/création de contrat."""

    TYPES_CONTRAT = [
        'CDI',
        'CDD',
        'Intérimaire',
        'Apprentissage',
        'Stagiaire',
        'Mise à disposition GE',
        'Etranger hors UE',
        'Temps partiel',
        'CIFRE',
        'Avenant contrat',
    ]
    TYPE_HINTS = {
        'CDI': "Contrat sans date de fin : laissez la date de fin sur Indéterminée.",
        'CDD': "Renseignez une date de fin pour suivre les échéances et les alertes.",
        'Intérimaire': "Ajoutez l'entreprise de travail temporaire dans la section dédiée.",
        'Apprentissage': "Renseignez le tuteur et l'école si ces informations sont disponibles.",
        'Stagiaire': "Renseignez le tuteur et l'école si ces informations sont disponibles.",
        'Mise à disposition GE': "Renseignez le groupement employeur dans la section dédiée.",
        'Etranger hors UE': "Renseignez les informations d'autorisation de travail.",
        'Temps partiel': "Vérifiez l'ETP et la rémunération associée.",
        'CIFRE': "Renseignez l'école ou l'organisme de rattachement si nécessaire.",
        'Avenant contrat': "Utilisez ce type pour tracer une modification contractuelle.",
    }
    TYPES_DATE_FIN_ATTENDUE = {
        'CDD', 'Intérimaire', 'Apprentissage', 'Stagiaire',
        'Mise à disposition GE', 'Etranger hors UE', 'CIFRE',
    }
    CATEGORIES = [
        '',
        'Ouvrier',
        'Ouvrier qualifié',
        'Employé',
        'Agent de maîtrise',
        'Cadre',
    ]

    def __init__(self, operateur_id: int, contrat: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.contrat = contrat or {}
        self.is_edit = contrat is not None
        self.document_path = None
        self._uploaded_doc_id = None
        title = "Modifier le contrat" if self.is_edit else "Déclarer un contrat"
        super().__init__(title=title, min_width=660, min_height=720, add_title_bar=False, parent=parent)

    def init_ui(self):
        self.content_layout.setSpacing(12)

        self._build_general_section()
        self._build_classification_section()
        self._build_conditional_sections()
        self._build_document_section()

        self._on_type_changed(self.type_combo.currentText())

    # ------------------------------------------------------------------
    # Sections UI
    # ------------------------------------------------------------------

    def _build_general_section(self):
        group = QGroupBox("Contrat")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(10)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.TYPES_CONTRAT)
        current_type = self.contrat.get('type_contrat')
        if current_type:
            idx = self.type_combo.findText(current_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        form.addRow("Type de contrat:", self.type_combo)

        self.date_debut = self._build_date_edit(
            self.contrat.get('date_debut') or QDate.currentDate(),
            "Date obligatoire",
            allow_empty=False,
        )
        form.addRow("Date de début:", self.date_debut)

        self.date_fin = self._build_date_edit(
            self.contrat.get('date_fin'),
            "Indéterminée",
            allow_empty=True,
        )
        form.addRow("Date de fin:", self.date_fin)

        layout.addLayout(form)

        self.type_hint = QLabel()
        self.type_hint.setWordWrap(True)
        self.type_hint.setStyleSheet(
            "color: #475569; background: #f8fafc; border: 1px solid #e2e8f0; "
            "border-radius: 6px; padding: 8px 10px;"
        )
        layout.addWidget(self.type_hint)

        self.content_layout.addWidget(group)

    def _build_classification_section(self):
        group = QGroupBox("Temps de travail, classification et rémunération")
        form = QFormLayout(group)
        form.setSpacing(10)

        self.etp = QDoubleSpinBox()
        self.etp.setRange(0.01, 1.0)
        self.etp.setSingleStep(0.05)
        self.etp.setDecimals(2)
        self.etp.setValue(float(self.contrat.get('etp', 1.0)))
        form.addRow("ETP:", self.etp)

        self.categorie_combo = QComboBox()
        for cat in self.CATEGORIES:
            self.categorie_combo.addItem(cat if cat else '-', cat or None)
        self._select_combo_data(self.categorie_combo, self.contrat.get('categorie'))
        form.addRow("Catégorie:", self.categorie_combo)

        self.echelon = QLineEdit(self.contrat.get('echelon') or '')
        self.echelon.setPlaceholderText("Ex: N3P1, échelon 2...")
        form.addRow("Échelon:", self.echelon)

        self.emploi = QLineEdit(self.contrat.get('emploi') or '')
        self.emploi.setPlaceholderText("Intitulé du poste ou emploi contractuel")
        form.addRow("Emploi:", self.emploi)

        self.salaire = QDoubleSpinBox()
        self.salaire.setRange(0, 999999.99)
        self.salaire.setDecimals(2)
        self.salaire.setSingleStep(50)
        self.salaire.setSuffix(" €")
        if self.contrat.get('salaire'):
            self.salaire.setValue(float(self.contrat['salaire']))
        form.addRow("Salaire brut:", self.salaire)

        self.content_layout.addWidget(group)

    def _build_conditional_sections(self):
        self.apprentissage_group = QGroupBox("Formation / tutorat")
        form_apprentissage = QFormLayout(self.apprentissage_group)
        form_apprentissage.setSpacing(10)
        self.nom_tuteur = QLineEdit(self.contrat.get('nom_tuteur') or '')
        self.prenom_tuteur = QLineEdit(self.contrat.get('prenom_tuteur') or '')
        self.ecole = QLineEdit(self.contrat.get('ecole') or '')
        form_apprentissage.addRow("Nom tuteur:", self.nom_tuteur)
        form_apprentissage.addRow("Prénom tuteur:", self.prenom_tuteur)
        form_apprentissage.addRow("École:", self.ecole)
        self.content_layout.addWidget(self.apprentissage_group)

        self.interim_group = QGroupBox("Entreprise de travail temporaire")
        form_interim = QFormLayout(self.interim_group)
        form_interim.setSpacing(10)
        self.nom_ett = QLineEdit(self.contrat.get('nom_ett') or '')
        self.adresse_ett = QLineEdit(self.contrat.get('adresse_ett') or '')
        form_interim.addRow("Nom ETT:", self.nom_ett)
        form_interim.addRow("Adresse ETT:", self.adresse_ett)
        self.content_layout.addWidget(self.interim_group)

        self.ge_group = QGroupBox("Groupement employeur")
        form_ge = QFormLayout(self.ge_group)
        form_ge.setSpacing(10)
        self.nom_ge = QLineEdit(self.contrat.get('nom_ge') or '')
        self.adresse_ge = QLineEdit(self.contrat.get('adresse_ge') or '')
        form_ge.addRow("Nom GE:", self.nom_ge)
        form_ge.addRow("Adresse GE:", self.adresse_ge)
        self.content_layout.addWidget(self.ge_group)

        self.autorisation_group = QGroupBox("Autorisation de travail")
        form_aut = QFormLayout(self.autorisation_group)
        form_aut.setSpacing(10)
        self.type_titre_autorisation = QLineEdit(self.contrat.get('type_titre_autorisation') or '')
        self.numero_autorisation_travail = QLineEdit(self.contrat.get('numero_autorisation_travail') or '')
        self.date_demande_autorisation = self._build_date_edit(
            self.contrat.get('date_demande_autorisation'),
            "Non définie",
            allow_empty=True,
        )
        self.date_autorisation_travail = self._build_date_edit(
            self.contrat.get('date_autorisation_travail'),
            "Non définie",
            allow_empty=True,
        )
        self.date_limite_autorisation = self._build_date_edit(
            self.contrat.get('date_limite_autorisation'),
            "Non définie",
            allow_empty=True,
        )
        form_aut.addRow("Type de titre:", self.type_titre_autorisation)
        form_aut.addRow("N° autorisation:", self.numero_autorisation_travail)
        form_aut.addRow("Date demande:", self.date_demande_autorisation)
        form_aut.addRow("Date autorisation:", self.date_autorisation_travail)
        form_aut.addRow("Date limite:", self.date_limite_autorisation)
        self.content_layout.addWidget(self.autorisation_group)

    def _build_document_section(self):
        self.document_group = QGroupBox("Document du contrat")
        layout = QVBoxLayout(self.document_group)
        layout.setSpacing(8)

        self._can_add_document = can("rh.documents.edit")
        if not self._can_add_document:
            note = QLabel("L'ajout de document n'est pas disponible avec vos droits actuels.")
            note.setWordWrap(True)
            note.setStyleSheet("color: #64748b;")
            layout.addWidget(note)
            self.content_layout.addWidget(self.document_group)
            return

        note_text = (
            "Joignez le contrat signé ou un avenant. Le document sera ajouté aux documents "
            "du domaine Contrat et pourra être ouvert ensuite."
        )
        if not self.is_edit:
            note_text += " Un document est obligatoire lors de la création."
        note = QLabel(note_text)
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
        self.document_nom.setPlaceholderText("Nom affiché dans les documents")
        form.addRow("Nom du document:", self.document_nom)

        self.document_expiration_auto = QCheckBox("Utiliser la date de fin comme expiration du document")
        self.document_expiration_auto.setChecked(True)
        form.addRow("", self.document_expiration_auto)
        layout.addLayout(form)

        self.content_layout.addWidget(self.document_group)

    # ------------------------------------------------------------------
    # Comportement
    # ------------------------------------------------------------------

    def _on_type_changed(self, type_contrat: str):
        self.type_hint.setText(self.TYPE_HINTS.get(type_contrat, ""))

        is_apprentissage = type_contrat in ('Apprentissage', 'Stagiaire', 'CIFRE')
        is_interim = type_contrat == 'Intérimaire'
        is_ge = type_contrat == 'Mise à disposition GE'
        is_foreign = type_contrat == 'Etranger hors UE'

        self.apprentissage_group.setVisible(is_apprentissage)
        self.interim_group.setVisible(is_interim)
        self.ge_group.setVisible(is_ge)
        self.autorisation_group.setVisible(is_foreign)

        if type_contrat == 'CDI':
            self.date_fin.setDate(QDate(1900, 1, 1))
        elif (
            type_contrat in self.TYPES_DATE_FIN_ATTENDUE
            and not self.is_edit
            and self.date_fin.date().year() <= 1900
        ):
            self.date_fin.setDate(QDate.currentDate().addYears(1))

    def _parcourir_document(self):
        fichier, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le document du contrat",
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
        date_debut = self._date_value(self.date_debut)
        date_fin = self._date_value(self.date_fin)
        type_contrat = self.type_combo.currentText()

        if not date_debut:
            return False, "La date de début est obligatoire."
        if date_fin and date_fin < date_debut:
            return False, "La date de fin doit être postérieure à la date de début."
        if type_contrat in self.TYPES_DATE_FIN_ATTENDUE and not date_fin:
            return False, "La date de fin est attendue pour ce type de contrat."
        if type_contrat == 'Intérimaire' and not self.nom_ett.text().strip():
            return False, "Le nom de l'ETT est obligatoire pour un contrat intérimaire."
        if type_contrat == 'Mise à disposition GE' and not self.nom_ge.text().strip():
            return False, "Le nom du groupement employeur est obligatoire."
        if type_contrat == 'Etranger hors UE' and not self.numero_autorisation_travail.text().strip():
            return False, "Le numéro d'autorisation est obligatoire pour un salarié étranger hors UE."

        if not self.is_edit:
            if not self._can_add_document:
                return False, "Le document du contrat est obligatoire, mais vos droits ne permettent pas de l'ajouter."
            if not self.document_path:
                return False, "Veuillez sélectionner le document du contrat."

        if self.document_path and not Path(self.document_path).exists():
            return False, "Le document sélectionné est introuvable."

        return True, ""

    def save_to_db(self):
        data = self._collect_data()

        contract_id = self.contrat.get('id')
        if self.is_edit:
            success, message = update_contrat(contract_id, data)
        else:
            success, message, contract_id = create_contrat(self.operateur_id, data)

        if not success:
            raise Exception(message)

        self._sauvegarder_document_associe(contract_id)

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------

    def _collect_data(self):
        type_contrat = self.type_combo.currentText()

        data = {
            'type_contrat': type_contrat,
            'date_debut': self._date_value(self.date_debut),
            'date_fin': self._date_value(self.date_fin),
            'etp': self.etp.value(),
            'categorie': self.categorie_combo.currentData(),
            'echelon': self.echelon.text().strip() or None,
            'emploi': self.emploi.text().strip() or None,
            'salaire': self.salaire.value() if self.salaire.value() > 0 else None,
            'nom_tuteur': None,
            'prenom_tuteur': None,
            'ecole': None,
            'nom_ett': None,
            'adresse_ett': None,
            'nom_ge': None,
            'adresse_ge': None,
            'date_autorisation_travail': None,
            'date_demande_autorisation': None,
            'type_titre_autorisation': None,
            'numero_autorisation_travail': None,
            'date_limite_autorisation': None,
        }

        if type_contrat in ('Apprentissage', 'Stagiaire', 'CIFRE'):
            data.update({
                'nom_tuteur': self.nom_tuteur.text().strip() or None,
                'prenom_tuteur': self.prenom_tuteur.text().strip() or None,
                'ecole': self.ecole.text().strip() or None,
            })

        if type_contrat == 'Intérimaire':
            data.update({
                'nom_ett': self.nom_ett.text().strip() or None,
                'adresse_ett': self.adresse_ett.text().strip() or None,
            })

        if type_contrat == 'Mise à disposition GE':
            data.update({
                'nom_ge': self.nom_ge.text().strip() or None,
                'adresse_ge': self.adresse_ge.text().strip() or None,
            })

        if type_contrat == 'Etranger hors UE':
            data.update({
                'date_autorisation_travail': self._date_value(self.date_autorisation_travail),
                'date_demande_autorisation': self._date_value(self.date_demande_autorisation),
                'type_titre_autorisation': self.type_titre_autorisation.text().strip() or None,
                'numero_autorisation_travail': self.numero_autorisation_travail.text().strip() or None,
                'date_limite_autorisation': self._date_value(self.date_limite_autorisation),
            })

        return data

    def _document_expiration_date(self):
        if not getattr(self, 'document_expiration_auto', None):
            return None
        if not self.document_expiration_auto.isChecked():
            return None
        return self._date_value(self.date_fin)

    def _categorie_contrat_id(self):
        from domain.services.rh.rh_service import get_categories_documents

        categories = get_categories_documents()
        for cat in categories:
            if cat.get('nom') == 'Contrats de travail':
                return cat.get('id')

        for cat in categories:
            if 'contrat' in (cat.get('nom') or '').lower():
                return cat.get('id')

        return None

    def _sauvegarder_document_associe(self, contract_id: int):
        if not self.document_path:
            return

        categorie_id = self._categorie_contrat_id()
        if not categorie_id:
            QMessageBox.warning(
                self,
                "Document non ajouté",
                "Le contrat a été enregistré, mais la catégorie Contrats de travail est introuvable.",
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
            date_expiration=self._document_expiration_date(),
            notes="Document ajouté depuis la déclaration contrat",
            uploaded_by=uploaded_by,
            contrat_id=contract_id,
        )

        if success:
            self._uploaded_doc_id = doc_id
            return

        QMessageBox.warning(
            self,
            "Document non ajouté",
            f"Le contrat a été enregistré, mais le document n'a pas pu être ajouté.\n\n{message}",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _select_combo_data(combo: QComboBox, value):
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    @staticmethod
    def _to_qdate(value, allow_empty: bool = True) -> QDate:
        if isinstance(value, QDate):
            return value
        if not value:
            return QDate(1900, 1, 1) if allow_empty else QDate.currentDate()
        if isinstance(value, str):
            parsed = QDate.fromString(value, "yyyy-MM-dd")
            return parsed if parsed.isValid() else QDate(1900, 1, 1)
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            return QDate(value.year, value.month, value.day)
        return QDate(1900, 1, 1)

    def _build_date_edit(self, value, special_text: str, allow_empty: bool) -> QDateEdit:
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("dd/MM/yyyy")
        date_edit.setMinimumDate(QDate(1900, 1, 1))
        date_edit.setSpecialValueText(special_text)
        date_edit.setDate(self._to_qdate(value, allow_empty=allow_empty))
        return date_edit

    @staticmethod
    def _date_value(date_edit: QDateEdit):
        date_value = date_edit.date()
        if date_value.year() <= 1900:
            return None
        return date_value.toPyDate()
