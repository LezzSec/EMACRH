# -*- coding: utf-8 -*-
"""
Dialogues de saisie RH extraits de gestion_rh.py.
Contient les 12 formulaires Edit*/Ajouter* utilisés par GestionRHDialog.
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QWidget, QFormLayout, QDateEdit, QComboBox, QTextEdit,
    QDoubleSpinBox, QCheckBox, QGroupBox, QFileDialog
)
from PyQt5.QtCore import Qt, QDate

from core.gui.components.ui_theme import EmacButton
from core.gui.components.emac_dialog import EmacFormDialog
from core.services.rh_service import (
    update_infos_generales,
    create_contrat, update_contrat,
    create_formation, update_formation,
    create_declaration, update_declaration,
    create_competence_personnel,
    get_categories_documents, CATEGORIE_TO_DOMAINE, DomaineRH,
    is_matricule_disponible,
)
from core.services.declaration_service_crud import DeclarationServiceCRUD as _DeclSvc
from core.services import competences_service as _competences_service
get_types_declaration = _DeclSvc.get_types_declaration
get_catalogue_competences = _competences_service.get_all_competences
update_competence_personnel = _competences_service.update_assignment
from core.services.medical_service import (
    create_visite, update_visite,
    create_accident, update_accident,
)
from core.services.mutuelle_service import create_mutuelle, update_mutuelle
from core.services.vie_salarie_service import (
    create_sanction, update_sanction,
    create_controle_alcool, create_test_salivaire,
    create_entretien, update_entretien,
    get_types_sanction, get_types_entretien, get_managers_liste,
)


class JustificatifMixin:
    """
    Mixin qui ajoute un champ de document justificatif obligatoire (création uniquement).
    À mélanger avec EmacFormDialog : class MonDialog(JustificatifMixin, EmacFormDialog).
    Appeler _ajouter_section_justificatif() dans init_ui(), puis :
      - _valider_justificatif() dans validate()
      - _sauvegarder_justificatif(operateur_id, categorie_nom) dans save_to_db()
    """

    def _ajouter_section_justificatif(self, categorie_nom_hint: str = ""):
        """Ajoute le groupe UI 'Document justificatif' à self.content_layout."""
        from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel
        self._justificatif_path = None
        self._justificatif_categorie_nom = categorie_nom_hint

        group = QGroupBox("📎 Document justificatif (obligatoire)")
        group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #f59e0b;
                border-radius: 6px;
                margin-top: 10px;
                padding: 10px 8px 8px 8px;
                font-weight: bold;
                color: #92400e;
                background: #fffbeb;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(6)

        note = QLabel("Un document justificatif (attestation, certificat, contrat signé…) "
                      "est requis pour valider cette saisie.")
        note.setStyleSheet("color: #78350f; font-size: 11px; font-style: italic;")
        note.setWordWrap(True)
        group_layout.addWidget(note)

        file_row = QHBoxLayout()
        self._justificatif_label = QLineEdit()
        self._justificatif_label.setReadOnly(True)
        self._justificatif_label.setPlaceholderText("Aucun fichier sélectionné…")
        self._justificatif_label.setStyleSheet("background: white;")
        file_row.addWidget(self._justificatif_label)

        btn = EmacButton("Parcourir…", variant="ghost")
        btn.setFixedWidth(100)
        btn.clicked.connect(self._parcourir_justificatif)
        file_row.addWidget(btn)
        group_layout.addLayout(file_row)

        self.content_layout.addWidget(group)

    def _parcourir_justificatif(self):
        from PyQt5.QtWidgets import QFileDialog
        fichier, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le document justificatif",
            "",
            "Tous les fichiers (*);;Documents PDF (*.pdf);;Images (*.png *.jpg *.jpeg);;Documents Word (*.docx *.doc)"
        )
        if fichier:
            self._justificatif_path = fichier
            self._justificatif_label.setText(fichier)

    def _valider_justificatif(self):
        """Retourne (True, '') si un fichier est sélectionné, sinon (False, message)."""
        if not getattr(self, '_justificatif_path', None):
            return False, "Un document justificatif est obligatoire pour cette saisie."
        return True, ""

    def _sauvegarder_justificatif(self, operateur_id: int):
        """
        Upload le justificatif en document DMS après création du record.
        Cherche la catégorie dont le nom contient self._justificatif_categorie_nom.
        """
        path = getattr(self, '_justificatif_path', None)
        if not path:
            return
        import os
        from core.services.document_service import DocumentService
        from core.services.auth_service import get_current_user
        from core.services.rh_service import get_categories_documents

        categorie_nom_hint = getattr(self, '_justificatif_categorie_nom', '')
        categories = get_categories_documents()

        # Cherche la catégorie la plus proche du hint
        categorie_id = None
        for cat in categories:
            if categorie_nom_hint and categorie_nom_hint.lower() in cat['nom'].lower():
                categorie_id = cat['id']
                break
        if categorie_id is None and categories:
            categorie_id = categories[0]['id']

        user = get_current_user()
        uploaded_by = user.get('nom_complet', 'Utilisateur') if user else 'Utilisateur'
        nom_affichage = os.path.basename(path)

        try:
            doc_service = DocumentService()
            doc_service.add_document(
                personnel_id=operateur_id,
                categorie_id=categorie_id,
                fichier_source=path,
                nom_affichage=nom_affichage,
                uploaded_by=uploaded_by,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Justificatif non sauvegardé pour operateur {operateur_id}: {e}"
            )


class EditInfosGeneralesDialog(EmacFormDialog):
    """Formulaire d'édition des informations générales."""

    def __init__(self, operateur_id: int, donnees: dict, parent=None):
        self.operateur_id = operateur_id
        self.donnees = donnees
        super().__init__(
            title="Modifier les informations générales",
            min_width=500,
            min_height=500,
            add_title_bar=False,
            parent=parent
        )

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(12)

        # --- Section Identité ---
        identite_group = QGroupBox("Identité")
        identite_layout = QFormLayout(identite_group)

        self.nom = QLineEdit(self.donnees.get('nom') or '')
        identite_layout.addRow("Nom:", self.nom)

        self.prenom = QLineEdit(self.donnees.get('prenom') or '')
        identite_layout.addRow("Prénom:", self.prenom)

        self.matricule = QLineEdit(self.donnees.get('matricule') or '')
        self.matricule.setPlaceholderText("Ex: M000001")
        identite_layout.addRow("Matricule:", self.matricule)

        self.content_layout.addWidget(identite_group)

        # --- Section Informations personnelles ---
        self.sexe_combo = QComboBox()
        self.sexe_combo.addItems(['', 'M', 'F'])
        if self.donnees.get('sexe'):
            idx = self.sexe_combo.findText(self.donnees['sexe'])
            if idx >= 0:
                self.sexe_combo.setCurrentIndex(idx)
        form.addRow("Sexe:", self.sexe_combo)

        self.date_naissance = QDateEdit()
        self.date_naissance.setCalendarPopup(True)
        self.date_naissance.setDisplayFormat("dd/MM/yyyy")
        self.date_naissance.setSpecialValueText("Non renseignée")
        if self.donnees.get('date_naissance'):
            d = self.donnees['date_naissance']
            self.date_naissance.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de naissance:", self.date_naissance)

        self.date_entree = QDateEdit()
        self.date_entree.setCalendarPopup(True)
        self.date_entree.setDisplayFormat("dd/MM/yyyy")
        self.date_entree.setSpecialValueText("Non renseignée")
        if self.donnees.get('date_entree'):
            d = self.donnees['date_entree']
            self.date_entree.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date d'entrée:", self.date_entree)

        self.nationalite = QLineEdit(self.donnees.get('nationalite') or '')
        form.addRow("Nationalité:", self.nationalite)

        self.numero_ss = QLineEdit(self.donnees.get('numero_ss') or '')
        self.numero_ss.setPlaceholderText("Ex: 1 93 02 75 108 136 23")
        form.addRow("N° Sécurité Sociale:", self.numero_ss)

        self.adresse1 = QLineEdit(self.donnees.get('adresse1') or '')
        form.addRow("Adresse:", self.adresse1)

        self.adresse2 = QLineEdit(self.donnees.get('adresse2') or '')
        form.addRow("Adresse (suite):", self.adresse2)

        cp_ville = QHBoxLayout()
        self.cp = QLineEdit(self.donnees.get('cp_adresse') or '')
        self.cp.setMaximumWidth(80)
        self.ville = QLineEdit(self.donnees.get('ville_adresse') or '')
        cp_ville.addWidget(self.cp)
        cp_ville.addWidget(self.ville)
        form.addRow("CP / Ville:", cp_ville)

        self.telephone = QLineEdit(self.donnees.get('telephone') or '')
        form.addRow("Téléphone:", self.telephone)

        self.email = QLineEdit(self.donnees.get('email') or '')
        form.addRow("Email:", self.email)

        self.pays_adresse = QLineEdit(self.donnees.get('pays_adresse') or '')
        self.pays_adresse.setPlaceholderText("Ex: France")
        form.addRow("Pays:", self.pays_adresse)

        # --- Section Situation professionnelle ---
        profil_group = QGroupBox("Situation professionnelle")
        profil_layout = QFormLayout(profil_group)
        profil_layout.setSpacing(10)

        self.categorie_combo = QComboBox()
        self.categorie_combo.addItems([
            '', 'O - Ouvrier', 'E - Employé', 'T - Technicien', 'C - Cadre'
        ])
        cat = self.donnees.get('categorie') or ''
        cat_map = {'O': 'O - Ouvrier', 'E': 'E - Employé', 'T': 'T - Technicien', 'C': 'C - Cadre'}
        if cat in cat_map:
            idx = self.categorie_combo.findText(cat_map[cat])
            if idx >= 0:
                self.categorie_combo.setCurrentIndex(idx)
        profil_layout.addRow("Catégorie:", self.categorie_combo)

        self.numposte_combo = QComboBox()
        self.numposte_combo.setEditable(True)
        self.numposte_combo.addItems([
            '', 'Production', 'Administratif', 'Labo', 'R&D', 'Méthode', 'Maintenance', 'Logistique'
        ])
        svc = self.donnees.get('numposte') or ''
        if svc:
            idx = self.numposte_combo.findText(svc)
            if idx >= 0:
                self.numposte_combo.setCurrentIndex(idx)
            else:
                self.numposte_combo.setCurrentText(svc)
        profil_layout.addRow("Service / Poste:", self.numposte_combo)

        self.content_layout.addWidget(profil_group)

        # --- Section Naissance ---
        naissance_group = QGroupBox("Lieu de naissance")
        naissance_layout = QFormLayout(naissance_group)

        self.ville_naissance = QLineEdit(self.donnees.get('ville_naissance') or '')
        self.ville_naissance.setPlaceholderText("Ex: Paris")
        naissance_layout.addRow("Ville:", self.ville_naissance)

        self.pays_naissance = QLineEdit(self.donnees.get('pays_naissance') or '')
        self.pays_naissance.setPlaceholderText("Ex: France")
        naissance_layout.addRow("Pays:", self.pays_naissance)

        self.content_layout.addWidget(naissance_group)
        self.content_layout.addLayout(form)

    def validate(self):
        if not self.nom.text().strip():
            return False, "Le nom est obligatoire."
        if not self.prenom.text().strip():
            return False, "Le prénom est obligatoire."

        nouveau_matricule = self.matricule.text().strip()
        if nouveau_matricule:
            if not is_matricule_disponible(nouveau_matricule, self.operateur_id):
                return False, f"Le matricule '{nouveau_matricule}' est déjà utilisé par un autre opérateur."

        # Récupérer les dates saisies (None si non renseignées)
        dn = self.date_naissance.date().toPyDate() if self.date_naissance.date().year() > 1900 else None
        de = self.date_entree.date().toPyDate() if self.date_entree.date().year() > 1900 else None

        from datetime import date as _date
        if dn and de:
            # La date d'entrée ne peut pas être antérieure à la naissance
            if de < dn:
                return False, "La date d'entrée dans l'entreprise ne peut pas être antérieure à la date de naissance."

        if dn and dn > _date.today():
            return False, "La date de naissance ne peut pas être dans le futur."

        if de and de > _date.today():
            return False, "La date d'entrée ne peut pas être dans le futur."

        return True, ""

    def save_to_db(self):
        data = {
            'nom': self.nom.text().strip(),
            'prenom': self.prenom.text().strip(),
            'matricule': self.matricule.text().strip() or self.donnees.get('matricule'),
            'sexe': self.sexe_combo.currentText() or None,
            'date_naissance': self.date_naissance.date().toPyDate() if self.date_naissance.date().year() > 1900 else None,
            'date_entree': self.date_entree.date().toPyDate() if self.date_entree.date().year() > 1900 else None,
            'nationalite': self.nationalite.text().strip(),
            'numero_ss': self.numero_ss.text().strip(),
            'adresse1': self.adresse1.text().strip(),
            'adresse2': self.adresse2.text().strip(),
            'cp_adresse': self.cp.text().strip(),
            'ville_adresse': self.ville.text().strip(),
            'pays_adresse': self.pays_adresse.text().strip(),
            'ville_naissance': self.ville_naissance.text().strip(),
            'pays_naissance': self.pays_naissance.text().strip(),
            'telephone': self.telephone.text().strip(),
            'email': self.email.text().strip(),
            'categorie': self.categorie_combo.currentText()[:1] or None,
            'numposte': self.numposte_combo.currentText().strip() or None,
        }

        success, message = update_infos_generales(self.operateur_id, data)
        if not success:
            raise Exception(message)


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


class EditFormationDialog(JustificatifMixin, EmacFormDialog):
    """Formulaire d'édition/création de formation."""

    def __init__(self, operateur_id: int, formation: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.formation = formation
        self.is_edit = formation is not None
        self._saved_id = None
        title = "Modifier la formation" if self.is_edit else "Nouvelle formation"
        min_h = 560 if self.is_edit else 700
        super().__init__(title=title, min_width=480, min_height=min_h, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(12)

        self.intitule = QLineEdit(self.formation.get('intitule', '') if self.formation else '')
        form.addRow("Intitulé:", self.intitule)

        self.organisme = QLineEdit(self.formation.get('organisme', '') if self.formation else '')
        form.addRow("Organisme:", self.organisme)

        self.lieu = QLineEdit(self.formation.get('lieu', '') if self.formation else '')
        self.lieu.setPlaceholderText("Ex: Salle A, site externe...")
        form.addRow("Lieu:", self.lieu)

        self.formateur = QLineEdit(self.formation.get('formateur', '') if self.formation else '')
        self.formateur.setPlaceholderText("Nom du formateur / intervenant")
        form.addRow("Formateur:", self.formateur)

        self.objectif = QTextEdit()
        self.objectif.setMaximumHeight(65)
        self.objectif.setPlaceholderText("Objectif pédagogique de la formation...")
        if self.formation and self.formation.get('objectif'):
            self.objectif.setText(self.formation['objectif'])
        form.addRow("Objectif:", self.objectif)

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setDate(QDate.currentDate())
        if self.formation and self.formation.get('date_debut'):
            d = self.formation['date_debut']
            self.date_debut.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de début:", self.date_debut)

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setSpecialValueText("Non définie")
        self.date_fin.setMinimumDate(QDate(1900, 1, 1))
        if self.formation and self.formation.get('date_fin'):
            d = self.formation['date_fin']
            self.date_fin.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_fin.setDate(QDate.currentDate())
        form.addRow("Date de fin:", self.date_fin)

        self.duree = QDoubleSpinBox()
        self.duree.setRange(0, 9999)
        self.duree.setSuffix(" h")
        if self.formation and self.formation.get('duree_heures'):
            self.duree.setValue(float(self.formation['duree_heures']))
        form.addRow("Durée:", self.duree)

        self.statut_combo = QComboBox()
        self.statut_combo.addItems(['Planifiée', 'En cours', 'Terminée', 'Annulée'])
        if self.formation and self.formation.get('statut'):
            idx = self.statut_combo.findText(self.formation['statut'])
            if idx >= 0:
                self.statut_combo.setCurrentIndex(idx)
        form.addRow("Statut:", self.statut_combo)

        self.certificat = QCheckBox("Certificat obtenu")
        if self.formation and self.formation.get('certificat_obtenu'):
            self.certificat.setChecked(True)
        form.addRow("", self.certificat)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(80)
        if self.formation and self.formation.get('commentaire'):
            self.commentaire.setText(self.formation['commentaire'])
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addLayout(form)

        if not self.is_edit:
            self._ajouter_section_justificatif_facultatif("Diplômes et formations")

    def _ajouter_section_justificatif_facultatif(self, categorie_nom_hint: str = ""):
        """Section justificatif facultative — peut être ajouté ultérieurement."""
        from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout
        self._justificatif_path = None
        self._justificatif_categorie_nom = categorie_nom_hint

        group = QGroupBox("Document justificatif (facultatif)")
        group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                margin-top: 10px;
                padding: 10px 8px 8px 8px;
                font-weight: bold;
                color: #475569;
                background: #f8fafc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(6)

        note = QLabel(
            "Vous pouvez joindre dès maintenant l'attestation ou le certificat. "
            "Si le document n'est pas encore disponible, il pourra être ajouté "
            "ultérieurement via l'onglet Documents du profil salarié."
        )
        note.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        note.setWordWrap(True)
        group_layout.addWidget(note)

        file_row = QHBoxLayout()
        self._justificatif_label = QLineEdit()
        self._justificatif_label.setReadOnly(True)
        self._justificatif_label.setPlaceholderText("Aucun fichier sélectionné (facultatif)…")
        self._justificatif_label.setStyleSheet("background: white;")
        file_row.addWidget(self._justificatif_label)

        btn = EmacButton("Parcourir…", variant="ghost")
        btn.setFixedWidth(100)
        btn.clicked.connect(self._parcourir_justificatif)
        file_row.addWidget(btn)
        group_layout.addLayout(file_row)

        self.content_layout.addWidget(group)

    def validate(self):
        if not self.intitule.text().strip():
            return False, "L'intitulé est obligatoire"
        return True, ""

    def save_to_db(self):
        date_fin = self.date_fin.date()
        data = {
            'intitule': self.intitule.text().strip(),
            'organisme': self.organisme.text().strip() or None,
            'lieu': self.lieu.text().strip() or None,
            'formateur': self.formateur.text().strip() or None,
            'objectif': self.objectif.toPlainText().strip() or None,
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': date_fin.toPyDate() if date_fin.year() > 1900 else None,
            'duree_heures': self.duree.value() if self.duree.value() > 0 else None,
            'statut': self.statut_combo.currentText(),
            'certificat_obtenu': self.certificat.isChecked(),
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_formation(self.formation['id'], data)
            if success:
                self._saved_id = self.formation['id']
        else:
            success, message, new_id = create_formation(self.operateur_id, data)
            if success:
                self._saved_id = new_id
                if getattr(self, '_justificatif_path', None):
                    self._sauvegarder_justificatif(self.operateur_id)
                else:
                    self._justificatif_manquant = True

        if not success:
            raise Exception(message)


# ============================================================
# FORMULAIRES MEDICAL
# ============================================================

class EditVisiteDialog(JustificatifMixin, EmacFormDialog):
    """Formulaire pour ajouter/modifier une visite médicale."""

    def __init__(self, operateur_id: int, visite: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.visite = visite
        self.is_edit = visite is not None
        title = "Modifier la visite" if self.is_edit else "Nouvelle visite médicale"
        min_h = 450 if self.is_edit else 590
        super().__init__(title=title, min_width=450, min_height=min_h, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(10)

        self.date_visite = QDateEdit()
        self.date_visite.setCalendarPopup(True)
        self.date_visite.setDisplayFormat("dd/MM/yyyy")
        if self.is_edit and self.visite.get('date_visite'):
            d = self.visite['date_visite']
            self.date_visite.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_visite.setDate(QDate.currentDate())
        form.addRow("Date de visite:", self.date_visite)

        self.type_combo = QComboBox()
        self.type_combo.addItems(['Embauche', 'Périodique', 'Reprise', 'À la demande', 'Pré-reprise'])
        if self.is_edit and self.visite.get('type_visite'):
            idx = self.type_combo.findText(self.visite['type_visite'])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        form.addRow("Type de visite:", self.type_combo)

        self.resultat_combo = QComboBox()
        self.resultat_combo.addItems(['', 'Apte', 'Apte avec restrictions', 'Inapte temporaire', 'Inapte définitif'])
        if self.is_edit and self.visite.get('resultat'):
            idx = self.resultat_combo.findText(self.visite['resultat'])
            if idx >= 0:
                self.resultat_combo.setCurrentIndex(idx)
        form.addRow("Résultat:", self.resultat_combo)

        self.restrictions = QTextEdit()
        self.restrictions.setMaximumHeight(60)
        self.restrictions.setPlaceholderText("Détail des restrictions si applicable")
        if self.is_edit:
            self.restrictions.setText(self.visite.get('restrictions') or '')
        form.addRow("Restrictions:", self.restrictions)

        self.medecin = QLineEdit()
        self.medecin.setPlaceholderText("Nom du médecin")
        if self.is_edit:
            self.medecin.setText(self.visite.get('medecin') or '')
        form.addRow("Médecin:", self.medecin)

        self.prochaine_visite = QDateEdit()
        self.prochaine_visite.setCalendarPopup(True)
        self.prochaine_visite.setDisplayFormat("dd/MM/yyyy")
        self.prochaine_visite.setSpecialValueText("Non définie")
        if self.is_edit and self.visite.get('prochaine_visite'):
            d = self.visite['prochaine_visite']
            self.prochaine_visite.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Prochaine visite:", self.prochaine_visite)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(60)
        if self.is_edit:
            self.commentaire.setText(self.visite.get('commentaire') or '')
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addLayout(form)

        if not self.is_edit:
            self._ajouter_section_justificatif("Certificats médicaux")

    def validate(self):
        if not self.is_edit:
            ok, msg = self._valider_justificatif()
            if not ok:
                return False, msg
        return True, ""

    def save_to_db(self):
        prochaine = self.prochaine_visite.date()
        data = {
            'date_visite': self.date_visite.date().toPyDate(),
            'type_visite': self.type_combo.currentText(),
            'resultat': self.resultat_combo.currentText() or None,
            'restrictions': self.restrictions.toPlainText().strip() or None,
            'medecin': self.medecin.text().strip() or None,
            'prochaine_visite': prochaine.toPyDate() if prochaine.year() > 1900 else None,
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_visite(self.visite['id'], data)
        else:
            success, message, _ = create_visite(self.operateur_id, data)
            if success:
                self._sauvegarder_justificatif(self.operateur_id)

        if not success:
            raise Exception(message)


class EditAccidentDialog(JustificatifMixin, EmacFormDialog):
    """Formulaire pour ajouter/modifier un accident du travail."""

    def __init__(self, operateur_id: int, accident: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.accident = accident
        self.is_edit = accident is not None
        title = "Modifier l'accident" if self.is_edit else "Nouvel accident du travail"
        min_h = 500 if self.is_edit else 640
        super().__init__(title=title, min_width=500, min_height=min_h, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(10)

        self.date_accident = QDateEdit()
        self.date_accident.setCalendarPopup(True)
        self.date_accident.setDisplayFormat("dd/MM/yyyy")
        if self.is_edit and self.accident.get('date_accident'):
            d = self.accident['date_accident']
            self.date_accident.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_accident.setDate(QDate.currentDate())
        form.addRow("Date de l'accident:", self.date_accident)

        self.avec_arret = QCheckBox("Accident avec arrêt de travail")
        if self.is_edit:
            self.avec_arret.setChecked(self.accident.get('avec_arret', False))
        form.addRow("", self.avec_arret)

        self.circonstances = QTextEdit()
        self.circonstances.setMaximumHeight(80)
        self.circonstances.setPlaceholderText("Décrivez les circonstances de l'accident")
        if self.is_edit:
            self.circonstances.setText(self.accident.get('circonstances') or '')
        form.addRow("Circonstances:", self.circonstances)

        self.siege_lesions = QLineEdit()
        self.siege_lesions.setPlaceholderText("Ex: Main droite, Dos, Pied gauche")
        if self.is_edit:
            self.siege_lesions.setText(self.accident.get('siege_lesions') or '')
        form.addRow("Siège des lésions:", self.siege_lesions)

        self.nature_lesions = QLineEdit()
        self.nature_lesions.setPlaceholderText("Ex: Fracture, Brûlure, Contusion")
        if self.is_edit:
            self.nature_lesions.setText(self.accident.get('nature_lesions') or '')
        form.addRow("Nature des lésions:", self.nature_lesions)

        self.nb_jours = QDoubleSpinBox()
        self.nb_jours.setRange(0, 365)
        self.nb_jours.setDecimals(0)
        self.nb_jours.setSuffix(" jours")
        if self.is_edit and self.accident.get('nb_jours_absence'):
            self.nb_jours.setValue(self.accident['nb_jours_absence'])
        form.addRow("Jours d'absence:", self.nb_jours)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(60)
        if self.is_edit:
            self.commentaire.setText(self.accident.get('commentaire') or '')
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addLayout(form)

        if not self.is_edit:
            self._ajouter_section_justificatif("Documents médicaux")

    def validate(self):
        if not self.is_edit:
            ok, msg = self._valider_justificatif()
            if not ok:
                return False, msg
        return True, ""

    def save_to_db(self):
        data = {
            'date_accident': self.date_accident.date().toPyDate(),
            'avec_arret': self.avec_arret.isChecked(),
            'circonstances': self.circonstances.toPlainText().strip() or None,
            'siege_lesions': self.siege_lesions.text().strip() or None,
            'nature_lesions': self.nature_lesions.text().strip() or None,
            'nb_jours_absence': int(self.nb_jours.value()) if self.nb_jours.value() > 0 else None,
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_accident(self.accident['id'], data)
        else:
            success, message, _ = create_accident(self.operateur_id, data)
            if success:
                self._sauvegarder_justificatif(self.operateur_id)

        if not success:
            raise Exception(message)


# ============================================================
# FORMULAIRES VIE DU SALARIE
# ============================================================

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


class AjouterDocumentDialog(EmacFormDialog):
    """Formulaire pour ajouter un document à un opérateur."""

    def __init__(self, operateur_id: int, domaine: 'DomaineRH' = None, parent=None):
        self.operateur_id = operateur_id
        self.domaine = domaine
        self.fichier_path = None
        super().__init__(title="Ajouter un document", min_width=500, min_height=400, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(12)

        file_layout = QHBoxLayout()
        self.file_label = QLineEdit()
        self.file_label.setReadOnly(True)
        self.file_label.setPlaceholderText("Aucun fichier sélectionné...")
        file_layout.addWidget(self.file_label)

        btn_parcourir = EmacButton("Parcourir...", variant="ghost")
        btn_parcourir.clicked.connect(self._parcourir_fichier)
        file_layout.addWidget(btn_parcourir)
        form.addRow("Fichier:", file_layout)

        self.nom_affichage = QLineEdit()
        self.nom_affichage.setPlaceholderText("Nom qui sera affiché (optionnel)")
        form.addRow("Nom d'affichage:", self.nom_affichage)

        self.categorie_combo = QComboBox()
        self._charger_categories()
        form.addRow("Catégorie:", self.categorie_combo)

        exp_layout = QHBoxLayout()
        self.date_expiration = QDateEdit()
        self.date_expiration.setCalendarPopup(True)
        self.date_expiration.setDisplayFormat("dd/MM/yyyy")
        self.date_expiration.setSpecialValueText("Pas d'expiration")
        self.date_expiration.setMinimumDate(QDate(1900, 1, 1))
        self.date_expiration.setDate(QDate(1900, 1, 1))
        exp_layout.addWidget(self.date_expiration)

        self.chk_expiration = QCheckBox("Définir une date d'expiration")
        self.chk_expiration.toggled.connect(self.date_expiration.setEnabled)
        self.date_expiration.setEnabled(False)
        exp_layout.addWidget(self.chk_expiration)
        form.addRow("Expiration:", exp_layout)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Notes ou commentaires (optionnel)")
        form.addRow("Notes:", self.notes)

        self.content_layout.addLayout(form)

    def _charger_categories(self):
        """Charge les catégories de documents filtrées par domaine actif."""
        self.categorie_combo.clear()

        categories = get_categories_documents()

        # Filtrer uniquement les catégories du domaine actif
        cats_domaine = [
            cat for cat in categories
            if CATEGORIE_TO_DOMAINE.get(cat['nom'], DomaineRH.GENERAL) == self.domaine
        ] if self.domaine else categories

        for cat in cats_domaine:
            self.categorie_combo.addItem(cat['nom'], cat['id'])

        if self.categorie_combo.count() == 1:
            self.categorie_combo.setCurrentIndex(0)

    def _parcourir_fichier(self):
        """Ouvre le dialogue de sélection de fichier."""
        fichier, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un document",
            "",
            "Tous les fichiers (*);;Documents PDF (*.pdf);;Images (*.png *.jpg *.jpeg);;Documents Word (*.docx *.doc)"
        )
        if fichier:
            self.fichier_path = fichier
            self.file_label.setText(fichier)
            if not self.nom_affichage.text():
                import os
                self.nom_affichage.setText(os.path.basename(fichier))

    def validate(self):
        if not self.fichier_path:
            return False, "Veuillez sélectionner un fichier"
        if self.categorie_combo.currentIndex() < 0:
            return False, "Veuillez sélectionner une catégorie"
        return True, ""

    def save_to_db(self):
        categorie_id = self.categorie_combo.currentData()
        nom = self.nom_affichage.text().strip() or None

        date_exp = None
        if self.chk_expiration.isChecked() and self.date_expiration.date().year() > 1900:
            date_exp = self.date_expiration.date().toPyDate()

        notes = self.notes.toPlainText().strip() or None

        from core.services.document_service import DocumentService
        from core.services.auth_service import get_current_user

        user = get_current_user()
        uploaded_by = user.get('nom_complet', 'Utilisateur') if user else 'Utilisateur'

        doc_service = DocumentService()
        success, message, doc_id = doc_service.add_document(
            personnel_id=self.operateur_id,
            categorie_id=categorie_id,
            fichier_source=self.fichier_path,
            nom_affichage=nom,
            date_expiration=date_exp,
            notes=notes,
            uploaded_by=uploaded_by
        )

        if not success:
            raise Exception(message)


# ============================================================
# Dialog : Gestion des dossiers de formation (Polyvalence)
# ============================================================

class GestionDocsFormationDialog:
    """
    Dialog d'administration des dossiers de formation pour les niveaux de polyvalence.

    Permet aux responsables de :
    - Voir tous les postes et leurs documents de formation
    - Ajouter un document (PDF, Word, etc.) pour un poste + niveau
    - Supprimer un document
    """

    def __init__(self, parent=None):
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSplitter,
            QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
            QHeaderView, QAbstractItemView, QWidget, QLineEdit
        )
        from PyQt5.QtCore import Qt

        self._parent = parent
        self._dialog = QDialog(parent)
        self._dialog.setWindowTitle("Gestion des dossiers de formation – Polyvalence")
        self._dialog.setMinimumSize(900, 600)
        self._dialog.resize(1000, 650)

        self._poste_selectionne = None

        main_layout = QVBoxLayout(self._dialog)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        titre = QLabel("Dossiers de formation de compétences – Niveaux de polyvalence")
        titre.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        main_layout.addWidget(titre)

        sous_titre = QLabel(
            "Associez des documents (PDF, Word, etc.) à un poste et un niveau de polyvalence. "
            "Ils seront lisibles par tous les utilisateurs depuis l'onglet Polyvalence."
        )
        sous_titre.setStyleSheet("color: #64748b; font-size: 12px;")
        sous_titre.setWordWrap(True)
        main_layout.addWidget(sous_titre)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Panneau gauche : liste des postes
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        lbl_postes = QLabel("Postes :")
        lbl_postes.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(lbl_postes)

        self._search_poste = QLineEdit()
        self._search_poste.setPlaceholderText("Filtrer par code poste...")
        self._search_poste.textChanged.connect(self._filtrer_postes)
        left_layout.addWidget(self._search_poste)

        self._list_postes = QListWidget()
        self._list_postes.setMaximumWidth(220)
        self._list_postes.currentRowChanged.connect(self._on_poste_change)
        left_layout.addWidget(self._list_postes)

        splitter.addWidget(left_panel)

        # Panneau droit : tableau + ajout
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(8)

        toolbar = QHBoxLayout()
        self._lbl_poste_titre = QLabel("Sélectionnez un poste")
        self._lbl_poste_titre.setStyleSheet("font-size: 14px; font-weight: bold;")
        toolbar.addWidget(self._lbl_poste_titre)
        toolbar.addStretch()

        self._btn_ajouter = EmacButton("+ Ajouter un document", variant="primary")
        self._btn_ajouter.setEnabled(False)
        self._btn_ajouter.clicked.connect(self._ajouter_doc)
        toolbar.addWidget(self._btn_ajouter)
        right_layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Nom", "Niveau", "Taille", "Ajouté par", "Actions"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in [1, 2, 3]:
            self._table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        right_layout.addWidget(self._table)

        splitter.addWidget(right_panel)
        splitter.setSizes([220, 680])

        btn_fermer = EmacButton("Fermer", variant="ghost")
        btn_fermer.clicked.connect(self._dialog.accept)
        main_layout.addWidget(btn_fermer, alignment=Qt.AlignRight)

        self._tous_postes = []
        self._charger_postes()

    def exec_(self):
        return self._dialog.exec_()

    def _charger_postes(self):
        from core.services.polyvalence_docs_service import get_tous_les_postes_avec_docs
        self._tous_postes = get_tous_les_postes_avec_docs()
        self._remplir_liste_postes(self._tous_postes)

    def _remplir_liste_postes(self, postes):
        from PyQt5.QtWidgets import QListWidgetItem
        self._list_postes.clear()
        for p in postes:
            nb = p.get('nb_documents', 0)
            label = p['poste_code']
            if p.get('atelier_nom'):
                label = f"{p['atelier_nom']} / {label}"
            if nb:
                label += f"  ({nb})"
            item = QListWidgetItem(label)
            item.setData(32, p)  # Qt.UserRole = 32
            self._list_postes.addItem(item)

    def _filtrer_postes(self, texte):
        texte = texte.lower()
        filtered = [p for p in self._tous_postes if texte in p['poste_code'].lower()]
        self._remplir_liste_postes(filtered)

    def _on_poste_change(self, row):
        if row < 0:
            return
        item = self._list_postes.item(row)
        if not item:
            return
        self._poste_selectionne = item.data(32)
        self._lbl_poste_titre.setText(f"Poste {self._poste_selectionne['poste_code']}")
        self._btn_ajouter.setEnabled(True)
        self._charger_docs_poste()

    def _charger_docs_poste(self):
        from PyQt5.QtWidgets import QTableWidgetItem, QWidget, QHBoxLayout
        from core.services.polyvalence_docs_service import get_docs_pour_poste

        if not self._poste_selectionne:
            return

        docs = get_docs_pour_poste(self._poste_selectionne['poste_id'])
        self._table.setRowCount(len(docs))

        NIVEAU_LABELS = {None: "Tous niveaux", 1: "Niv. 1", 2: "Niv. 2", 3: "Niv. 3", 4: "Niv. 4"}

        for row_idx, doc in enumerate(docs):
            nom = doc.get('nom_affichage', doc.get('nom_fichier', '?'))
            self._table.setItem(row_idx, 0, QTableWidgetItem(nom))
            self._table.setItem(row_idx, 1, QTableWidgetItem(
                NIVEAU_LABELS.get(doc.get('niveau'), f"Niv. {doc['niveau']}")))
            taille = doc.get('taille_octets')
            self._table.setItem(row_idx, 2, QTableWidgetItem(
                f"{taille // 1024} Ko" if taille else "-"))
            self._table.setItem(row_idx, 3, QTableWidgetItem(doc.get('ajoute_par', '-')))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)

            btn_ouvrir = EmacButton("Ouvrir", variant="outline")
            btn_ouvrir.setFixedHeight(26)
            doc_id = doc['id']
            btn_ouvrir.clicked.connect(lambda checked, did=doc_id: self._ouvrir_doc(did))
            btn_layout.addWidget(btn_ouvrir)

            btn_suppr = EmacButton("Suppr.", variant="ghost")
            btn_suppr.setFixedHeight(26)
            btn_suppr.clicked.connect(lambda checked, did=doc_id, n=nom: self._supprimer_doc(did, n))
            btn_layout.addWidget(btn_suppr)

            self._table.setCellWidget(row_idx, 4, btn_widget)

    def _ajouter_doc(self):
        if not self._poste_selectionne:
            return
        dialog = AjouterDocFormationDialog(self._poste_selectionne, self._dialog)
        if dialog.exec_() == 1:
            self._charger_docs_poste()
            self._charger_postes()

    def _ouvrir_doc(self, doc_id: int):
        import os
        from core.services.polyvalence_docs_service import extraire_vers_fichier_temp
        temp_path = extraire_vers_fichier_temp(doc_id)
        if temp_path and temp_path.exists():
            if os.name == 'nt':
                os.startfile(str(temp_path))
            else:
                import subprocess
                subprocess.run(['xdg-open', str(temp_path)])
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self._dialog, "Erreur", "Le fichier n'a pas pu être extrait.")

    def _supprimer_doc(self, doc_id: int, nom: str):
        from PyQt5.QtWidgets import QMessageBox
        from core.services.polyvalence_docs_service import supprimer_document
        reply = QMessageBox.question(
            self._dialog,
            "Confirmer la suppression",
            f"Supprimer le document '{nom}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = supprimer_document(doc_id)
            if success:
                self._charger_docs_poste()
                self._charger_postes()
            else:
                QMessageBox.critical(self._dialog, "Erreur", message)


class AjouterDocFormationDialog:
    """
    Dialog pour ajouter un document de formation à un poste + niveau.
    """

    def __init__(self, poste_info: dict, parent=None):
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
            QFormLayout, QComboBox, QTextEdit
        )
        from PyQt5.QtCore import Qt

        self._poste_info = poste_info
        self._fichier_path = None

        self._dialog = QDialog(parent)
        self._dialog.setWindowTitle(f"Ajouter un dossier – Poste {poste_info['poste_code']}")
        self._dialog.setMinimumWidth(480)

        layout = QVBoxLayout(self._dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(10)

        # Fichier
        file_row = QHBoxLayout()
        self._file_label = QLineEdit()
        self._file_label.setReadOnly(True)
        self._file_label.setPlaceholderText("Aucun fichier sélectionné...")
        file_row.addWidget(self._file_label)
        btn_parcourir = EmacButton("Parcourir...", variant="ghost")
        btn_parcourir.clicked.connect(self._parcourir)
        file_row.addWidget(btn_parcourir)
        form.addRow("Fichier :", file_row)

        self._nom_input = QLineEdit()
        self._nom_input.setPlaceholderText("Titre du document (optionnel)")
        form.addRow("Titre :", self._nom_input)

        self._niveau_combo = QComboBox()
        self._niveau_combo.addItem("Tous les niveaux", None)
        self._niveau_combo.addItem("Niveau 1 – Apprentissage", 1)
        self._niveau_combo.addItem("Niveau 2 – En cours", 2)
        self._niveau_combo.addItem("Niveau 3 – Autonome", 3)
        self._niveau_combo.addItem("Niveau 4 – Expert / Formateur", 4)
        form.addRow("Niveau concerné :", self._niveau_combo)

        self._desc_input = QTextEdit()
        self._desc_input.setMaximumHeight(70)
        self._desc_input.setPlaceholderText("Description ou contexte (optionnel)")
        form.addRow("Description :", self._desc_input)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_annuler = EmacButton("Annuler", variant="ghost")
        btn_annuler.clicked.connect(self._dialog.reject)
        btn_row.addWidget(btn_annuler)
        btn_ok = EmacButton("Ajouter", variant="primary")
        btn_ok.clicked.connect(self._valider)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def exec_(self):
        return self._dialog.exec_()

    def _parcourir(self):
        from PyQt5.QtWidgets import QFileDialog
        from pathlib import Path
        path, _ = QFileDialog.getOpenFileName(
            self._dialog,
            "Sélectionner un fichier",
            "",
            "Documents (*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.odt *.png *.jpg *.jpeg);;Tous les fichiers (*)"
        )
        if path:
            self._fichier_path = path
            self._file_label.setText(Path(path).name)
            if not self._nom_input.text():
                self._nom_input.setText(Path(path).stem.replace('_', ' ').replace('-', ' '))

    def _valider(self):
        from PyQt5.QtWidgets import QMessageBox
        from core.services.polyvalence_docs_service import ajouter_document
        from core.services.auth_service import get_current_user

        if not self._fichier_path:
            QMessageBox.warning(self._dialog, "Fichier manquant", "Veuillez sélectionner un fichier.")
            return

        nom = self._nom_input.text().strip() or None
        niveau = self._niveau_combo.currentData()
        description = self._desc_input.toPlainText().strip() or None

        user = get_current_user()
        ajoute_par = user.get('nom_complet', 'Utilisateur') if user else 'Utilisateur'

        success, message, _ = ajouter_document(
            poste_id=self._poste_info['poste_id'],
            nom_affichage=nom,
            fichier_source=self._fichier_path,
            niveau=niveau,
            description=description,
            ajoute_par=ajoute_par
        )

        if success:
            self._dialog.accept()
        else:
            QMessageBox.critical(self._dialog, "Erreur", message)


# ============================================================
# MUTUELLE
# ============================================================

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
