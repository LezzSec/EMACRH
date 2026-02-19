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
from PyQt5.QtGui import QFont

from core.gui.ui_theme import EmacButton
from core.gui.emac_dialog import EmacFormDialog
from core.services.rh_service_refactored import (
    update_infos_generales,
    create_contrat, update_contrat,
    create_formation, update_formation,
    create_declaration, update_declaration,
    get_types_declaration,
    get_catalogue_competences,
    create_competence_personnel, update_competence_personnel,
    get_categories_documents, CATEGORIE_TO_DOMAINE, DomaineRH,
    is_matricule_disponible,
)
from core.services.medical_service import (
    create_visite, update_visite,
    create_accident, update_accident,
)
from core.services.vie_salarie_service import (
    create_sanction, update_sanction,
    create_controle_alcool, create_test_salivaire,
    create_entretien, update_entretien,
    get_types_sanction, get_types_entretien, get_managers_liste,
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

        return True, ""

    def save_to_db(self):
        data = {
            'nom': self.nom.text().strip(),
            'prenom': self.prenom.text().strip(),
            'matricule': self.matricule.text().strip() or None,
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
        }

        success, message = update_infos_generales(self.operateur_id, data)
        if not success:
            raise Exception(message)


class EditContratDialog(EmacFormDialog):
    """Formulaire d'édition/création de contrat."""

    def __init__(self, operateur_id: int, contrat: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.contrat = contrat
        self.is_edit = contrat is not None
        title = "Modifier le contrat" if self.is_edit else "Nouveau contrat"
        super().__init__(title=title, min_width=450, min_height=400, add_title_bar=False, parent=parent)

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

        if not success:
            raise Exception(message)


class EditDeclarationDialog(EmacFormDialog):
    """Formulaire d'édition/création de déclaration."""

    def __init__(self, operateur_id: int, declaration: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.declaration = declaration
        self.is_edit = declaration is not None
        title = "Modifier la déclaration" if self.is_edit else "Nouvelle déclaration"
        super().__init__(title=title, min_width=400, min_height=350, add_title_bar=False, parent=parent)

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


class EditFormationDialog(EmacFormDialog):
    """Formulaire d'édition/création de formation."""

    def __init__(self, operateur_id: int, formation: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.formation = formation
        self.is_edit = formation is not None
        title = "Modifier la formation" if self.is_edit else "Nouvelle formation"
        super().__init__(title=title, min_width=450, min_height=450, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(12)

        self.intitule = QLineEdit(self.formation.get('intitule', '') if self.formation else '')
        form.addRow("Intitulé:", self.intitule)

        self.organisme = QLineEdit(self.formation.get('organisme', '') if self.formation else '')
        form.addRow("Organisme:", self.organisme)

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
            self.date_fin.setDate(QDate(1900, 1, 1))
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

    def validate(self):
        if not self.intitule.text().strip():
            return False, "L'intitulé est obligatoire"
        return True, ""

    def save_to_db(self):
        date_fin = self.date_fin.date()
        data = {
            'intitule': self.intitule.text().strip(),
            'organisme': self.organisme.text().strip() or None,
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': date_fin.toPyDate() if date_fin.year() > 1900 else None,
            'duree_heures': self.duree.value() if self.duree.value() > 0 else None,
            'statut': self.statut_combo.currentText(),
            'certificat_obtenu': self.certificat.isChecked(),
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_formation(self.formation['id'], data)
        else:
            success, message, _ = create_formation(self.operateur_id, data)

        if not success:
            raise Exception(message)


# ============================================================
# FORMULAIRES MEDICAL
# ============================================================

class EditVisiteDialog(EmacFormDialog):
    """Formulaire pour ajouter/modifier une visite médicale."""

    def __init__(self, operateur_id: int, visite: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.visite = visite
        self.is_edit = visite is not None
        title = "Modifier la visite" if self.is_edit else "Nouvelle visite médicale"
        super().__init__(title=title, min_width=450, min_height=450, add_title_bar=False, parent=parent)

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

        if not success:
            raise Exception(message)


class EditAccidentDialog(EmacFormDialog):
    """Formulaire pour ajouter/modifier un accident du travail."""

    def __init__(self, operateur_id: int, accident: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.accident = accident
        self.is_edit = accident is not None
        title = "Modifier l'accident" if self.is_edit else "Nouvel accident du travail"
        super().__init__(title=title, min_width=500, min_height=500, add_title_bar=False, parent=parent)

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

        if not success:
            raise Exception(message)


# ============================================================
# FORMULAIRES VIE DU SALARIE
# ============================================================

class EditSanctionDialog(EmacFormDialog):
    """Formulaire pour ajouter/modifier une sanction."""

    def __init__(self, operateur_id: int, sanction: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.sanction = sanction
        self.is_edit = sanction is not None
        title = "Modifier la sanction" if self.is_edit else "Nouvelle sanction"
        super().__init__(title=title, min_width=450, min_height=400, add_title_bar=False, parent=parent)

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
        """Charge les catégories de documents."""
        from core.services.contrat_service import get_contract_types

        self.categorie_combo.clear()

        if self.domaine == DomaineRH.CONTRAT:
            types_contrat = get_contract_types()
            for type_contrat in types_contrat:
                self.categorie_combo.addItem(type_contrat, type_contrat)
            return

        categories = get_categories_documents()

        for cat in categories:
            if self.domaine:
                cat_domaine = CATEGORIE_TO_DOMAINE.get(cat['nom'], DomaineRH.GENERAL)
                if cat_domaine != self.domaine:
                    continue
            self.categorie_combo.addItem(cat['nom'], cat['id'])

        if self.categorie_combo.count() == 0:
            for cat in categories:
                self.categorie_combo.addItem(cat['nom'], cat['id'])

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
            operateur_id=self.operateur_id,
            categorie_id=categorie_id,
            fichier_source=self.fichier_path,
            nom_affichage=nom,
            date_expiration=date_exp,
            notes=notes,
            uploaded_by=uploaded_by
        )

        if not success:
            raise Exception(message)
