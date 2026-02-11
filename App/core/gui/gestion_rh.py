# -*- coding: utf-8 -*-
"""
Écran RH Opérateur & Documents
Permet de consulter et gérer les données RH d'un opérateur par domaine.

Structure:
- Zone gauche: Recherche et sélection d'opérateur
- Zone droite: Navigation par domaines RH + résumé + documents
"""

import logging

logger = logging.getLogger(__name__)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QWidget, QFrame, QScrollArea,
    QStackedWidget, QSizePolicy, QSpacerItem, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QFormLayout, QDateEdit, QComboBox, QTextEdit,
    QDoubleSpinBox, QCheckBox, QGroupBox, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor

from core.gui.ui_theme import EmacTheme, EmacCard, EmacButton
from core.gui.emac_ui_kit import EmacBadge, EmacAlert, EmacChip, add_custom_title_bar, show_error_message
from core.gui.emac_dialog import EmacFormDialog
from core.db.query_executor import QueryExecutor
# ✅ MIGRATION COMPLÈTE VERS VERSION REFACTORISÉE (2026-02-10)
from core.services.rh_service_refactored import (
    rechercher_operateurs,
    get_operateur_by_id,
    get_donnees_domaine,
    DomaineRH,
    update_infos_generales,
    create_contrat,
    update_contrat,
    delete_contrat,
    create_formation,
    update_formation,
    delete_formation,
    create_declaration,
    update_declaration,
    delete_declaration,
    get_types_declaration,
    get_catalogue_competences,
    create_competence_personnel,
    update_competence_personnel,
    delete_competence_personnel,
    get_documents_domaine,
    get_documents_archives_operateur,
    get_resume_operateur,
    get_domaines_rh,
    get_categories_documents,
    CATEGORIE_TO_DOMAINE,
)
from core.services.medical_service import (
    get_visites, create_visite, update_visite, delete_visite,
    get_accidents, create_accident, update_accident, delete_accident,
    get_validites, create_validite, update_validite, delete_validite,
    get_alertes_medicales
)
from core.services.vie_salarie_service import (
    get_sanctions, create_sanction, update_sanction, delete_sanction,
    get_controles_alcool, create_controle_alcool, delete_controle_alcool,
    get_tests_salivaires, create_test_salivaire, delete_test_salivaire,
    get_entretiens, create_entretien, update_entretien, delete_entretien,
    get_types_sanction, get_types_entretien, get_managers_liste
)
from core.services.permission_manager import can


# ============================================================
# FORMULAIRES D'ÉDITION
# ============================================================

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

        # Validation unicité matricule
        nouveau_matricule = self.matricule.text().strip()
        if nouveau_matricule:
            existing = QueryExecutor.fetch_one(
                "SELECT id FROM personnel WHERE matricule = %s AND id != %s",
                (nouveau_matricule, self.operateur_id),
                dictionary=True
            )
            if existing:
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

        # Sélection du fichier
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

        # Date d'expiration (optionnel)
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


class GestionRHDialog(QDialog):
    """
    Fenêtre principale de gestion RH.
    Divisée en deux zones: sélection opérateur (gauche) et détails RH (droite).
    """

    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion RH")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        # État
        self.operateur_selectionne = None
        self.domaine_actif = DomaineRH.GENERAL
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._executer_recherche)

        self._setup_ui()

    def _setup_ui(self):
        """Construit l'interface utilisateur."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre
        title_bar = add_custom_title_bar(self, "Gestion RH")
        main_layout.addWidget(title_bar)

        # Contenu principal
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Zone gauche: Sélection opérateur
        self.zone_gauche = self._creer_zone_selection()
        content_layout.addWidget(self.zone_gauche)

        # Séparateur vertical
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #e5e7eb;")
        separator.setFixedWidth(1)
        content_layout.addWidget(separator)

        # Zone droite: Détails RH
        self.zone_droite = self._creer_zone_details()
        content_layout.addWidget(self.zone_droite, 1)

        main_layout.addWidget(content, 1)

        # Boutons de bas de page
        footer = self._creer_footer()
        main_layout.addWidget(footer)

    # =========================================================================
    # ZONE GAUCHE - Sélection opérateur
    # =========================================================================

    def _creer_zone_selection(self) -> QWidget:
        """Crée la zone de recherche et sélection d'opérateur."""
        zone = QWidget()
        zone.setFixedWidth(320)
        zone.setStyleSheet("background-color: #f8fafc;")

        layout = QVBoxLayout(zone)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Titre + Bouton Actions en masse
        header_layout = QHBoxLayout()
        titre = QLabel("Sélection Opérateur")
        titre.setFont(QFont("Segoe UI", 14, QFont.Bold))
        titre.setStyleSheet("color: #111827;")
        header_layout.addWidget(titre)
        header_layout.addStretch()

        btn_bulk = QPushButton("Actions en masse")
        btn_bulk.setToolTip("Assigner formations, absences ou visites médicales à plusieurs employés")
        btn_bulk.setCursor(Qt.PointingHandCursor)
        btn_bulk.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #a855f7);
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #9333ea);
            }
            QPushButton:pressed {
                background: #5b21b6;
            }
        """)
        btn_bulk.clicked.connect(self._open_bulk_assignment_dialog)
        header_layout.addWidget(btn_bulk)

        layout.addLayout(header_layout)

        # Champ de recherche
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)

        # Label
        search_label = QLabel("Rechercher par nom, prénom ou matricule")
        search_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        search_layout.addWidget(search_label)

        # Input de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tapez pour rechercher...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)

        layout.addWidget(search_container)

        # Liste des résultats
        results_label = QLabel("Résultats")
        results_label.setStyleSheet("color: #374151; font-weight: 600; margin-top: 8px;")
        layout.addWidget(results_label)

        self.liste_operateurs = QListWidget()
        self.liste_operateurs.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: white;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f3f4f6;
            }
            QListWidget::item:selected {
                background-color: #eff6ff;
                color: #1e40af;
            }
            QListWidget::item:hover {
                background-color: #f9fafb;
            }
        """)
        self.liste_operateurs.itemClicked.connect(self._on_operateur_selectionne)
        layout.addWidget(self.liste_operateurs, 1)

        # Compteur de résultats
        self.compteur_resultats = QLabel("0 opérateur(s)")
        self.compteur_resultats.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(self.compteur_resultats)

        # Charger les opérateurs actifs par défaut
        QTimer.singleShot(100, lambda: self._executer_recherche())

        return zone

    def _on_search_changed(self, text: str):
        """Déclenche une recherche avec délai (debounce)."""
        self._search_timer.stop()
        self._search_timer.start(300)  # 300ms de délai

    def _executer_recherche(self):
        """Exécute la recherche d'opérateurs."""
        recherche = self.search_input.text().strip()
        resultats = rechercher_operateurs(recherche=recherche if recherche else None)

        self.liste_operateurs.clear()
        for op in resultats:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, op['id'])

            # Texte formaté
            nom_complet = op.get('nom_complet', f"{op.get('prenom', '')} {op.get('nom', '')}")
            matricule = op.get('matricule', '-')
            statut = op.get('statut', 'ACTIF')

            item.setText(f"{nom_complet}\n{matricule}")
            item.setToolTip(f"ID: {op['id']} | Statut: {statut}")

            self.liste_operateurs.addItem(item)

        self.compteur_resultats.setText(f"{len(resultats)} opérateur(s)")

    def _on_operateur_selectionne(self, item: QListWidgetItem):
        """Appelé quand un opérateur est sélectionné dans la liste."""
        operateur_id = item.data(Qt.UserRole)
        self.operateur_selectionne = get_operateur_by_id(operateur_id)

        if self.operateur_selectionne:
            self._afficher_details_operateur()

    def _selectionner_operateur_par_id(self, operateur_id: int):
        """Sélectionne automatiquement un opérateur par son ID."""
        # Charger l'opérateur directement
        self.operateur_selectionne = get_operateur_by_id(operateur_id)

        if self.operateur_selectionne:
            # Afficher les détails
            self._afficher_details_operateur()

            # Sélectionner dans la liste si présent
            for i in range(self.liste_operateurs.count()):
                item = self.liste_operateurs.item(i)
                if item.data(Qt.UserRole) == operateur_id:
                    self.liste_operateurs.setCurrentItem(item)
                    break

    # =========================================================================
    # ZONE DROITE - Détails RH
    # =========================================================================

    def _creer_zone_details(self) -> QWidget:
        """Crée la zone d'affichage des détails RH."""
        zone = QWidget()
        layout = QVBoxLayout(zone)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stack pour basculer entre placeholder et contenu
        self.stack_details = QStackedWidget()

        # Page 0: Placeholder (aucun opérateur sélectionné)
        self.placeholder = self._creer_placeholder()
        self.stack_details.addWidget(self.placeholder)

        # Page 1: Contenu RH
        self.contenu_rh = self._creer_contenu_rh()
        self.stack_details.addWidget(self.contenu_rh)

        layout.addWidget(self.stack_details)

        return zone

    def _creer_placeholder(self) -> QWidget:
        """Crée le placeholder affiché quand aucun opérateur n'est sélectionné."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        # Icône
        icon = QLabel("👤")
        icon.setFont(QFont("Segoe UI", 48))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        # Message
        message = QLabel("Sélectionnez un opérateur")
        message.setFont(QFont("Segoe UI", 18, QFont.Bold))
        message.setStyleSheet("color: #6b7280;")
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)

        # Sous-message
        sous_message = QLabel("Utilisez la zone de recherche à gauche\npour trouver un opérateur")
        sous_message.setStyleSheet("color: #9ca3af;")
        sous_message.setAlignment(Qt.AlignCenter)
        layout.addWidget(sous_message)

        return widget

    def _creer_contenu_rh(self) -> QWidget:
        """Crée le contenu RH (affiché quand un opérateur est sélectionné)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # En-tête avec infos opérateur
        self.header_operateur = self._creer_header_operateur()
        layout.addWidget(self.header_operateur)

        # Barre de navigation des domaines RH
        self.nav_domaines = self._creer_navigation_domaines()
        layout.addWidget(self.nav_domaines)

        # Zone de contenu scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Container pour résumé + documents
        self.container_domaine = QWidget()
        self.layout_domaine = QVBoxLayout(self.container_domaine)
        self.layout_domaine.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.setSpacing(16)

        # Zone résumé des données
        self.zone_resume = QWidget()
        self.layout_resume = QVBoxLayout(self.zone_resume)
        self.layout_resume.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.addWidget(self.zone_resume)

        # Zone documents
        self.zone_documents = QWidget()
        self.layout_documents = QVBoxLayout(self.zone_documents)
        self.layout_documents.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.addWidget(self.zone_documents)

        # Spacer
        self.layout_domaine.addStretch()

        scroll.setWidget(self.container_domaine)
        layout.addWidget(scroll, 1)

        return widget

    def _creer_header_operateur(self) -> QWidget:
        """Crée l'en-tête compact avec les infos de l'opérateur sélectionné."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: #1e40af;
                border-radius: 8px;
            }
        """)
        header.setFixedHeight(50)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)

        # Nom
        self.label_nom_operateur = QLabel("Nom Prénom")
        self.label_nom_operateur.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.label_nom_operateur.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(self.label_nom_operateur)

        # Séparateur
        sep = QLabel("•")
        sep.setStyleSheet("color: #93c5fd; background: transparent; margin: 0 8px;")
        layout.addWidget(sep)

        # Matricule
        self.label_matricule = QLabel("-")
        self.label_matricule.setStyleSheet("color: #bfdbfe; background: transparent; font-size: 13px;")
        layout.addWidget(self.label_matricule)

        layout.addStretch()

        # Badge statut
        self.badge_statut = QLabel("ACTIF")
        self.badge_statut.setStyleSheet("""
            background: #10b981;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 11px;
        """)
        layout.addWidget(self.badge_statut)

        return header

    def _creer_navigation_domaines(self) -> QWidget:
        """Crée la barre de navigation entre les domaines RH."""
        nav = QWidget()
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.boutons_domaines = {}
        domaines = get_domaines_rh()

        for domaine in domaines:
            btn = QPushButton(domaine['nom'])
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty('domaine', domaine['code'])
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 16px;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    background: white;
                    color: #374151;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: #f9fafb;
                    border-color: #d1d5db;
                }
                QPushButton:checked {
                    background: #1e40af;
                    color: white;
                    border-color: #1e40af;
                }
            """)
            btn.clicked.connect(lambda checked, d=domaine['code']: self._on_domaine_change(d))
            layout.addWidget(btn)
            self.boutons_domaines[domaine['code']] = btn

        # Bouton Archives (caché par défaut, affiché si documents archivés)
        self.btn_archives = QPushButton("📦 Archives")
        self.btn_archives.setCheckable(True)
        self.btn_archives.setCursor(Qt.PointingHandCursor)
        self.btn_archives.setStyleSheet("""
            QPushButton {
                padding: 10px 16px;
                border: 1px solid #f59e0b;
                border-radius: 8px;
                background: #fffbeb;
                color: #92400e;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #fef3c7;
                border-color: #d97706;
            }
            QPushButton:checked {
                background: #f59e0b;
                color: white;
                border-color: #f59e0b;
            }
        """)
        self.btn_archives.clicked.connect(self._on_archives_click)
        self.btn_archives.setVisible(False)  # Caché par défaut
        layout.addWidget(self.btn_archives)

        layout.addStretch()

        return nav

    def _update_archives_tab(self):
        """Met à jour la visibilité et le compteur de l'onglet Archives."""
        if not self.operateur_selectionne:
            if hasattr(self, 'btn_archives'):
                self.btn_archives.setVisible(False)
            return

        archives = get_documents_archives_operateur(self.operateur_selectionne['id'])
        if archives:
            self.btn_archives.setText(f"📦 Archives ({len(archives)})")
            self.btn_archives.setVisible(True)
        else:
            self.btn_archives.setVisible(False)

    def _on_archives_click(self):
        """Appelé quand l'utilisateur clique sur l'onglet Archives."""
        # Décocher tous les autres boutons
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(False)
        self.btn_archives.setChecked(True)

        # Afficher les archives
        self._charger_contenu_archives()

    def _on_domaine_change(self, code_domaine: str):
        """Appelé quand l'utilisateur change de domaine RH."""
        # Mettre à jour l'état des boutons
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == code_domaine)

        # Mettre à jour le domaine actif
        self.domaine_actif = DomaineRH(code_domaine)

        # Recharger le contenu
        if self.operateur_selectionne:
            self._charger_contenu_domaine()

    def _afficher_details_operateur(self):
        """Affiche les détails de l'opérateur sélectionné."""
        if not self.operateur_selectionne:
            return

        op = self.operateur_selectionne

        # Mettre à jour l'en-tête
        nom_complet = op.get('nom_complet', f"{op.get('prenom', '')} {op.get('nom', '')}")
        self.label_nom_operateur.setText(nom_complet)
        self.label_matricule.setText(op.get('matricule', '-'))

        # Badge statut
        statut = op.get('statut', 'ACTIF')
        if statut == 'ACTIF':
            self.badge_statut.setText("ACTIF")
            self.badge_statut.setStyleSheet("""
                background: #10b981;
                color: white;
                padding: 6px 12px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            """)
        else:
            self.badge_statut.setText("INACTIF")
            self.badge_statut.setStyleSheet("""
                background: #6b7280;
                color: white;
                padding: 6px 12px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            """)

        # Activer le premier domaine par défaut
        self.domaine_actif = DomaineRH.GENERAL
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == DomaineRH.GENERAL.value)
        self.btn_archives.setChecked(False)

        # Charger le contenu du domaine
        self._charger_contenu_domaine()

        # Mettre à jour l'onglet Archives
        self._update_archives_tab()

        # Afficher la zone de contenu
        self.stack_details.setCurrentIndex(1)

    def _charger_contenu_domaine(self):
        """Charge le contenu du domaine RH actif."""
        if not self.operateur_selectionne:
            return

        operateur_id = self.operateur_selectionne['id']

        # Vider les zones
        self._vider_layout(self.layout_resume)
        self._vider_layout(self.layout_documents)

        # Charger les données du domaine
        donnees = get_donnees_domaine(operateur_id, self.domaine_actif)

        # Créer la zone de résumé selon le domaine
        widget_resume = self._creer_widget_resume(donnees)
        if widget_resume:
            self.layout_resume.addWidget(widget_resume)

        # Charger les documents du domaine (inclut les archives pour pouvoir les afficher si demandé)
        documents = get_documents_domaine(operateur_id, self.domaine_actif, include_archives=True)
        widget_documents = self._creer_widget_documents(documents)
        self.layout_documents.addWidget(widget_documents)

        # Émettre le signal de changement de données
        self.data_changed.emit()

    def _creer_widget_resume(self, donnees: dict) -> QWidget:
        """Crée le widget de résumé selon le domaine actif."""
        if self.domaine_actif == DomaineRH.GENERAL:
            return self._creer_resume_general(donnees)
        elif self.domaine_actif == DomaineRH.CONTRAT:
            return self._creer_resume_contrat(donnees)
        elif self.domaine_actif == DomaineRH.DECLARATION:
            return self._creer_resume_declaration(donnees)
        elif self.domaine_actif == DomaineRH.COMPETENCES:
            return self._creer_resume_competences(donnees)
        elif self.domaine_actif == DomaineRH.FORMATION:
            return self._creer_resume_formation(donnees)
        elif self.domaine_actif == DomaineRH.MEDICAL:
            return self._creer_resume_medical(donnees)
        elif self.domaine_actif == DomaineRH.VIE_SALARIE:
            return self._creer_resume_vie_salarie(donnees)
        return None

    def _creer_resume_general(self, donnees: dict) -> QWidget:
        """Crée le résumé des données générales."""
        self._donnees_generales = donnees  # Stocker pour édition

        card = EmacCard("Informations Générales")

        if donnees.get('error'):
            card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            return card

        # Bouton modifier en haut à droite
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        btn_edit = EmacButton("Modifier", variant="ghost")
        btn_edit.clicked.connect(self._edit_infos_generales)
        header_layout.addWidget(btn_edit)
        card.body.addLayout(header_layout)

        # Grille d'informations
        grid = QGridLayout()
        grid.setSpacing(12)

        # Helper pour gérer les valeurs None
        def val(key, default='-'):
            v = donnees.get(key)
            return v if v is not None and v != '' else default

        # Construire l'adresse complète
        adresse_parts = []
        if donnees.get('adresse1'):
            adresse_parts.append(donnees['adresse1'])
        if donnees.get('adresse2'):
            adresse_parts.append(donnees['adresse2'])
        adresse = ', '.join(adresse_parts) if adresse_parts else '-'

        # Construire ville + CP
        ville_parts = []
        if donnees.get('cp_adresse'):
            ville_parts.append(donnees['cp_adresse'])
        if donnees.get('ville_adresse'):
            ville_parts.append(donnees['ville_adresse'])
        ville = ' '.join(ville_parts) if ville_parts else '-'

        # Lieu de naissance
        naissance_parts = []
        if donnees.get('ville_naissance'):
            naissance_parts.append(donnees['ville_naissance'])
        if donnees.get('pays_naissance'):
            naissance_parts.append(f"({donnees['pays_naissance']})")
        lieu_naissance = ' '.join(naissance_parts) if naissance_parts else '-'

        infos = [
            ("Nom", val('nom')),
            ("Prénom", val('prenom')),
            ("Matricule", val('matricule')),
            ("Statut", val('statut')),
            ("Sexe", "Homme" if donnees.get('sexe') == 'M' else "Femme" if donnees.get('sexe') == 'F' else '-'),
            ("Nationalité", val('nationalite')),
            ("N° Sécurité Sociale", val('numero_ss')),
            ("Date de naissance", self._format_date(donnees.get('date_naissance'))),
            ("Lieu de naissance", lieu_naissance),
            ("Âge", f"{donnees.get('age')} ans" if donnees.get('age') else '-'),
            ("Date d'entrée", self._format_date(donnees.get('date_entree'))),
            ("Ancienneté", val('anciennete')),
            ("Téléphone", val('telephone')),
            ("Email", val('email')),
            ("Adresse", adresse),
            ("Ville", ville),
            ("Pays", val('pays_adresse')),
        ]

        for i, (label, valeur) in enumerate(infos):
            row, col = divmod(i, 2)
            lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
            lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
            grid.addWidget(lbl, row, col)

        card.body.addLayout(grid)
        return card

    def _edit_infos_generales(self):
        """Ouvre le formulaire d'édition des infos générales."""
        if not self.operateur_selectionne:
            return
        dialog = EditInfosGeneralesDialog(
            self.operateur_selectionne['id'],
            self._donnees_generales,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _creer_resume_contrat(self, donnees: dict) -> QWidget:
        """Crée le résumé du contrat."""
        self._donnees_contrat = donnees  # Stocker pour édition

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Boutons d'action
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        btn_add = EmacButton("+ Nouveau contrat", variant="primary")
        btn_add.clicked.connect(self._add_contrat)
        actions_layout.addWidget(btn_add)
        layout.addLayout(actions_layout)

        contrat = donnees.get('contrat_actif')

        if contrat:
            # Alerte si contrat expire bientôt
            jours = contrat.get('jours_restants')
            if jours is not None and jours <= 30:
                if jours < 0:
                    alert = EmacAlert(f"Contrat expiré depuis {abs(jours)} jour(s) !", variant="error")
                elif jours == 0:
                    alert = EmacAlert("Contrat expire aujourd'hui !", variant="error")
                else:
                    alert = EmacAlert(f"Contrat expire dans {jours} jour(s)", variant="warning")
                layout.addWidget(alert)

            # Carte contrat actif
            card = EmacCard("Contrat Actif")

            # Bouton modifier
            header = QHBoxLayout()
            header.addStretch()
            btn_edit = EmacButton("Modifier", variant="ghost")
            btn_edit.clicked.connect(lambda: self._edit_contrat(contrat))
            header.addWidget(btn_edit)
            card.body.addLayout(header)

            grid = QGridLayout()
            grid.setSpacing(12)

            infos = [
                ("Type", contrat.get('type_contrat', '-')),
                ("Date début", self._format_date(contrat.get('date_debut'))),
                ("Date fin", self._format_date(contrat.get('date_fin')) or "Indéterminée"),
                ("Jours restants", str(jours) if jours else "N/A"),
                ("ETP", str(contrat.get('etp', 1.0))),
                ("Catégorie", contrat.get('categorie', '-')),
                ("Emploi", contrat.get('emploi', '-')),
            ]

            for i, (label, valeur) in enumerate(infos):
                row, col = divmod(i, 2)
                lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
                lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
                grid.addWidget(lbl, row, col)

            card.body.addLayout(grid)
            layout.addWidget(card)
        else:
            alert = EmacAlert("Aucun contrat actif", variant="info")
            layout.addWidget(alert)

        return container

    def _add_contrat(self):
        """Ouvre le formulaire de création de contrat."""
        if not self.operateur_selectionne:
            return
        dialog = EditContratDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_contrat(self, contrat: dict):
        """Ouvre le formulaire d'édition de contrat."""
        if not self.operateur_selectionne:
            return
        dialog = EditContratDialog(self.operateur_selectionne['id'], contrat, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_declaration(self):
        """Ouvre le formulaire d'ajout de déclaration."""
        if not self.operateur_selectionne:
            return
        dialog = EditDeclarationDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_declaration(self, declaration: dict):
        """Ouvre le formulaire d'édition de déclaration."""
        if not self.operateur_selectionne:
            return
        dialog = EditDeclarationDialog(self.operateur_selectionne['id'], declaration, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_formation(self):
        """Ouvre le formulaire d'ajout de formation."""
        if not self.operateur_selectionne:
            return
        dialog = EditFormationDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_formation(self, formation: dict):
        """Ouvre le formulaire d'édition de formation."""
        if not self.operateur_selectionne:
            return
        dialog = EditFormationDialog(self.operateur_selectionne['id'], formation, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_declaration(self, declaration: dict):
        """Supprime une déclaration après confirmation."""
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette déclaration ?\n{declaration.get('type_declaration')} du {self._format_date(declaration.get('date_debut'))}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_declaration(declaration['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _delete_formation(self, formation: dict):
        """Supprime une formation après confirmation."""
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette formation ?\n{formation.get('intitule', 'N/A')}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_formation(formation['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _creer_resume_declaration(self, donnees: dict) -> QWidget:
        """Crée le résumé des déclarations."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Bouton ajouter en haut
        btn_add = EmacButton("+ Nouvelle déclaration", variant="primary")
        btn_add.clicked.connect(self._add_declaration)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        # Déclaration en cours
        en_cours = donnees.get('en_cours')
        if en_cours:
            alert = EmacAlert(
                f"Déclaration en cours: {en_cours.get('type_declaration')} "
                f"du {self._format_date(en_cours.get('date_debut'))} "
                f"au {self._format_date(en_cours.get('date_fin'))}",
                variant="info"
            )
            layout.addWidget(alert)

        # Statistiques
        stats = donnees.get('statistiques', {})
        if stats:
            card = EmacCard("Statistiques des déclarations")
            stats_layout = QHBoxLayout()

            for type_decl, data in stats.items():
                chip = EmacChip(f"{type_decl}: {data.get('nombre', 0)}", variant="info")
                stats_layout.addWidget(chip)

            stats_layout.addStretch()
            card.body.addLayout(stats_layout)
            layout.addWidget(card)

        # Liste des déclarations
        declarations = donnees.get('declarations', [])
        card = EmacCard(f"Déclarations ({len(declarations)})")
        if declarations:
            for decl in declarations:
                row = QHBoxLayout()
                info_text = f"{decl.get('type_declaration', 'N/A')} - {self._format_date(decl.get('date_debut'))} au {self._format_date(decl.get('date_fin'))}"
                row.addWidget(QLabel(info_text))
                row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.clicked.connect(lambda checked, d=decl: self._edit_declaration(d))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="ghost")
                btn_delete.clicked.connect(lambda checked, d=decl: self._delete_declaration(d))
                row.addWidget(btn_delete)
                card.body.addLayout(row)
        else:
            card.body.addWidget(QLabel("Aucune déclaration"))
        layout.addWidget(card)

        return container

    def _creer_resume_competences(self, donnees: dict) -> QWidget:
        """Crée le résumé des compétences transversales."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Bouton ajouter en haut
        btn_add = EmacButton("+ Nouvelle compétence", variant="primary")
        btn_add.clicked.connect(self._add_competence)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})

        # Alertes expirations
        expirees = stats.get('expirees', 0)
        if expirees > 0:
            alert = EmacAlert(f"{expirees} compétence(s) expirée(s) !", variant="error")
            layout.addWidget(alert)

        expire_bientot = stats.get('expire_bientot_30j', 0)
        if expire_bientot > 0:
            alert = EmacAlert(f"{expire_bientot} compétence(s) expirant dans les 30 jours", variant="warning")
            layout.addWidget(alert)

        # Carte statistiques
        card = EmacCard("Statistiques")
        stats_layout = QHBoxLayout()

        items = [
            ("Valides", stats.get('valides', 0)),
            ("Expirées", stats.get('expirees', 0)),
            ("Total", stats.get('total', 0)),
        ]

        for label, count in items:
            badge = QLabel(f"{label}: {count}")
            badge.setStyleSheet("""
                background: #f1f5f9;
                color: #475569;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            """)
            stats_layout.addWidget(badge)

        stats_layout.addStretch()
        card.body.addLayout(stats_layout)
        layout.addWidget(card)

        # Liste des compétences
        competences = donnees.get('competences', [])
        card_list = EmacCard(f"Compétences ({len(competences)})")

        if competences:
            for comp in competences:
                row = QHBoxLayout()

                # Indicateur de statut
                statut = comp.get('statut', 'valide')
                if statut == 'expiree':
                    indicator = "X"
                    color = "#ef4444"
                elif statut == 'expire_bientot':
                    indicator = "!"
                    color = "#f97316"
                elif statut == 'attention':
                    indicator = "~"
                    color = "#eab308"
                else:
                    indicator = "O"
                    color = "#22c55e"

                status_label = QLabel(indicator)
                status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
                status_label.setFixedWidth(20)
                row.addWidget(status_label)

                # Info compétence
                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                libelle = comp.get('libelle', 'N/A')
                categorie = comp.get('categorie', '')
                if categorie:
                    libelle = f"{libelle} [{categorie}]"
                label_nom = QLabel(libelle)
                label_nom.setStyleSheet("font-weight: 500;")
                info_layout.addWidget(label_nom)

                # Dates
                date_acq = comp.get('date_acquisition')
                date_exp = comp.get('date_expiration')
                date_text = f"Acquis le: {self._format_date(date_acq)}"
                if date_exp:
                    date_text += f" - Expire le: {self._format_date(date_exp)}"
                else:
                    date_text += " - Permanent"

                label_dates = QLabel(date_text)
                label_dates.setStyleSheet("color: #64748b; font-size: 12px;")
                info_layout.addWidget(label_dates)

                # Message de statut si besoin
                if statut in ('expire_bientot', 'attention', 'expiree'):
                    statut_label = comp.get('statut_label', '')
                    if statut_label:
                        label_statut = QLabel(statut_label)
                        label_statut.setStyleSheet(f"color: {color}; font-size: 11px; font-style: italic;")
                        info_layout.addWidget(label_statut)

                row.addLayout(info_layout)
                row.addStretch()

                # Boutons
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.clicked.connect(lambda checked, c=comp: self._edit_competence(c))
                row.addWidget(btn_edit)

                btn_delete = EmacButton("Retirer", variant="ghost")
                btn_delete.clicked.connect(lambda checked, c=comp: self._delete_competence(c))
                row.addWidget(btn_delete)

                card_list.body.addLayout(row)

                # Séparateur
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet("background: #e2e8f0;")
                card_list.body.addWidget(sep)
        else:
            card_list.body.addWidget(QLabel("Aucune compétence assignée"))

        layout.addWidget(card_list)

        return container

    def _add_competence(self):
        """Ouvre le formulaire d'ajout de compétence."""
        if not self.operateur_id:
            return
        dialog = EditCompetenceDialog(self.operateur_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_competence(self, competence: dict):
        """Ouvre le formulaire de modification de compétence."""
        dialog = EditCompetenceDialog(self.operateur_id, competence, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_competence(self, competence: dict):
        """Retire une compétence après confirmation."""
        libelle = competence.get('libelle', 'cette compétence')
        reply = QMessageBox.question(
            self,
            "Confirmer le retrait",
            f"Voulez-vous vraiment retirer la compétence '{libelle}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_competence_personnel(competence['assignment_id'])
            if success:
                QMessageBox.information(self, "Succès", message)
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _creer_resume_formation(self, donnees: dict) -> QWidget:
        """Crée le résumé des formations."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Bouton ajouter en haut
        btn_add = EmacButton("+ Nouvelle formation", variant="primary")
        btn_add.clicked.connect(self._add_formation)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})

        # Carte statistiques
        card = EmacCard("Statistiques Formations")
        stats_layout = QHBoxLayout()

        items = [
            ("Total", stats.get('total', 0)),
            ("Terminées", stats.get('terminees', 0)),
            ("En cours", stats.get('en_cours', 0)),
            ("Planifiées", stats.get('planifiees', 0)),
            ("Avec certificat", stats.get('avec_certificat', 0)),
        ]

        for label, count in items:
            badge = QLabel(f"{label}: {count}")
            badge.setStyleSheet("""
                background: #f1f5f9;
                color: #475569;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            """)
            stats_layout.addWidget(badge)

        stats_layout.addStretch()
        card.body.addLayout(stats_layout)
        layout.addWidget(card)

        # Liste des formations
        formations = donnees.get('formations', [])
        card_list = EmacCard(f"Formations ({len(formations)})")
        if formations:
            for form in formations:
                row = QHBoxLayout()
                info_text = f"{form.get('intitule', 'N/A')} - {form.get('statut', 'N/A')}"
                if form.get('date_debut'):
                    info_text += f" ({self._format_date(form.get('date_debut'))})"
                row.addWidget(QLabel(info_text))
                row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.clicked.connect(lambda checked, f=form: self._edit_formation(f))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="ghost")
                btn_delete.clicked.connect(lambda checked, f=form: self._delete_formation(f))
                row.addWidget(btn_delete)
                card_list.body.addLayout(row)
        else:
            card_list.body.addWidget(QLabel("Aucune formation enregistrée"))
        layout.addWidget(card_list)

        return container

    def _creer_resume_medical(self, donnees: dict) -> QWidget:
        """Crée le résumé du suivi médical."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if donnees.get('error'):
            error_card = EmacCard("Erreur")
            error_card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            layout.addWidget(error_card)
            return container

        medical_info = donnees.get('medical') or {}
        visites = donnees.get('visites') or []
        accidents = donnees.get('accidents') or []
        validites = donnees.get('validites') or []
        alertes = donnees.get('alertes') or []

        self._donnees_medical = donnees

        # ===== Alertes médicales =====
        if alertes:
            alertes_card = EmacCard("Alertes")
            for alerte in alertes:
                alert_widget = QFrame()
                alert_widget.setStyleSheet("""
                    QFrame {
                        background: #fef2f2;
                        border: 1px solid #fecaca;
                        border-radius: 6px;
                        padding: 8px 12px;
                        margin-bottom: 4px;
                    }
                """)
                alert_layout = QHBoxLayout(alert_widget)
                alert_layout.setContentsMargins(8, 4, 8, 4)
                lbl = QLabel(alerte.get('message', str(alerte)))
                lbl.setStyleSheet("color: #dc2626; font-weight: 500;")
                alert_layout.addWidget(lbl)
                alertes_card.body.addWidget(alert_widget)
            layout.addWidget(alertes_card)

        # ===== Suivi médical principal =====
        card_medical = EmacCard("Suivi Médical")
        grid = QGridLayout()
        grid.setSpacing(12)

        type_suivi = medical_info.get('type_suivi_vip') or "Non défini"
        periodicite = medical_info.get('periodicite_vip_mois') or 24

        infos = [
            ("Type de suivi VIP", type_suivi),
            ("Périodicité", f"{periodicite} mois"),
            ("Maladie professionnelle", "Oui" if medical_info.get('maladie_pro') else "Non"),
            ("Taux professionnel", f"{medical_info.get('taux_professionnel', 0)}%" if medical_info.get('taux_professionnel') else "-"),
        ]

        if medical_info.get('besoins_adaptation'):
            infos.append(("Besoins d'adaptation", medical_info.get('besoins_adaptation')))

        for i, (label, valeur) in enumerate(infos):
            r, c = divmod(i, 2)
            lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
            lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
            grid.addWidget(lbl, r, c)

        card_medical.body.addLayout(grid)
        layout.addWidget(card_medical)

        # ===== RQTH / OETH =====
        from datetime import date as date_class
        rqth_validites = [v for v in validites if v.get('type_validite') == 'RQTH']
        oeth_validites = [v for v in validites if v.get('type_validite') == 'OETH']

        card_rqth = EmacCard("RQTH / OETH")
        rqth_layout = QHBoxLayout()

        rqth_frame = QFrame()
        rqth_frame.setStyleSheet("padding: 8px; background: #f0fdf4; border-radius: 6px;")
        rqth_inner = QVBoxLayout(rqth_frame)
        rqth_inner.addWidget(QLabel("<b>RQTH</b>"))
        if rqth_validites:
            latest_rqth = rqth_validites[0]
            date_fin = latest_rqth.get('date_fin')
            statut = "Active" if date_fin and date_fin >= date_class.today() else "Expirée"
            rqth_inner.addWidget(QLabel(f"Statut: {statut}"))
            rqth_inner.addWidget(QLabel(f"Fin: {self._format_date(date_fin)}"))
            if latest_rqth.get('taux_incapacite'):
                rqth_inner.addWidget(QLabel(f"Taux: {latest_rqth.get('taux_incapacite')}%"))
        else:
            rqth_inner.addWidget(QLabel("Non applicable"))
        rqth_layout.addWidget(rqth_frame)

        oeth_frame = QFrame()
        oeth_frame.setStyleSheet("padding: 8px; background: #eff6ff; border-radius: 6px;")
        oeth_inner = QVBoxLayout(oeth_frame)
        oeth_inner.addWidget(QLabel("<b>OETH</b>"))
        if oeth_validites:
            latest_oeth = oeth_validites[0]
            date_fin = latest_oeth.get('date_fin')
            statut = "Active" if date_fin and date_fin >= date_class.today() else "Expirée"
            oeth_inner.addWidget(QLabel(f"Statut: {statut}"))
            oeth_inner.addWidget(QLabel(f"Fin: {self._format_date(date_fin)}"))
        else:
            oeth_inner.addWidget(QLabel("Non applicable"))
        rqth_layout.addWidget(oeth_frame)

        card_rqth.body.addLayout(rqth_layout)
        layout.addWidget(card_rqth)

        # ===== Visites médicales =====
        card_visites = EmacCard(f"Visites médicales ({len(visites)})")

        btn_add_visite = EmacButton("+ Nouvelle visite", variant="primary")
        btn_add_visite.clicked.connect(self._add_visite)
        card_visites.body.addWidget(btn_add_visite, alignment=Qt.AlignLeft)

        if visites:
            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["Date", "Type", "Résultat", "Médecin", "Prochaine", "Actions"])
            table.setRowCount(len(visites))
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)

            for row_idx, visite in enumerate(visites):
                table.setItem(row_idx, 0, QTableWidgetItem(self._format_date(visite.get('date_visite'))))
                table.setItem(row_idx, 1, QTableWidgetItem(visite.get('type_visite', '-')))
                table.setItem(row_idx, 2, QTableWidgetItem(visite.get('resultat', '-')))
                table.setItem(row_idx, 3, QTableWidgetItem(visite.get('medecin', '-')))
                table.setItem(row_idx, 4, QTableWidgetItem(self._format_date(visite.get('prochaine_visite'))))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(2, 2, 2, 2)
                btn_layout_inner.setSpacing(4)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setFixedHeight(28)
                btn_edit.clicked.connect(lambda checked, v=visite: self._edit_visite(v))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="ghost")
                btn_del.setFixedHeight(28)
                btn_del.clicked.connect(lambda checked, v=visite: self._delete_visite(v))
                btn_layout_inner.addWidget(btn_del)

                table.setCellWidget(row_idx, 5, btn_widget)

            table.setMaximumHeight(200)
            card_visites.body.addWidget(table)
        else:
            card_visites.body.addWidget(QLabel("Aucune visite enregistrée"))

        layout.addWidget(card_visites)

        # ===== Accidents du travail =====
        card_accidents = EmacCard(f"Accidents du travail ({len(accidents)})")

        btn_add_accident = EmacButton("+ Nouvel accident", variant="primary")
        btn_add_accident.clicked.connect(self._add_accident)
        card_accidents.body.addWidget(btn_add_accident, alignment=Qt.AlignLeft)

        if accidents:
            table_acc = QTableWidget()
            table_acc.setColumnCount(6)
            table_acc.setHorizontalHeaderLabels(["Date", "Avec arrêt", "Jours absence", "Siège lésions", "Nature", "Actions"])
            table_acc.setRowCount(len(accidents))
            table_acc.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_acc.setAlternatingRowColors(True)
            table_acc.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_acc.setEditTriggers(QAbstractItemView.NoEditTriggers)

            for row_idx, acc in enumerate(accidents):
                table_acc.setItem(row_idx, 0, QTableWidgetItem(self._format_date(acc.get('date_accident'))))
                table_acc.setItem(row_idx, 1, QTableWidgetItem("Oui" if acc.get('avec_arret') else "Non"))
                table_acc.setItem(row_idx, 2, QTableWidgetItem(str(acc.get('nb_jours_absence', '-'))))
                table_acc.setItem(row_idx, 3, QTableWidgetItem(acc.get('siege_lesions', '-')))
                table_acc.setItem(row_idx, 4, QTableWidgetItem(acc.get('nature_lesions', '-')))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(2, 2, 2, 2)
                btn_layout_inner.setSpacing(4)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setFixedHeight(28)
                btn_edit.clicked.connect(lambda checked, a=acc: self._edit_accident(a))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="ghost")
                btn_del.setFixedHeight(28)
                btn_del.clicked.connect(lambda checked, a=acc: self._delete_accident(a))
                btn_layout_inner.addWidget(btn_del)

                table_acc.setCellWidget(row_idx, 5, btn_widget)

            table_acc.setMaximumHeight(200)
            card_accidents.body.addWidget(table_acc)
        else:
            card_accidents.body.addWidget(QLabel("Aucun accident enregistré"))

        layout.addWidget(card_accidents)

        return container

    def _creer_resume_vie_salarie(self, donnees: dict) -> QWidget:
        """Crée le résumé de la vie du salarié."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if donnees.get('error'):
            error_card = EmacCard("Erreur")
            error_card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            layout.addWidget(error_card)
            return container

        sanctions_data = donnees.get('sanctions', {})
        alcoolemie_data = donnees.get('alcoolemie', {})
        salivaire_data = donnees.get('tests_salivaires', {})
        entretiens_data = donnees.get('entretiens', {})
        alertes = donnees.get('alertes', [])

        self._donnees_vie_salarie = donnees

        # ===== Alertes =====
        if alertes:
            alertes_card = EmacCard("Alertes")
            for alerte in alertes:
                alert_widget = QFrame()
                alert_widget.setStyleSheet("""
                    QFrame {
                        background: #fef2f2;
                        border: 1px solid #fecaca;
                        border-radius: 6px;
                        padding: 8px 12px;
                        margin-bottom: 4px;
                    }
                """)
                alert_layout = QHBoxLayout(alert_widget)
                alert_layout.setContentsMargins(8, 4, 8, 4)
                lbl = QLabel(alerte.get('message', str(alerte)))
                lbl.setStyleSheet("color: #dc2626; font-weight: 500;")
                alert_layout.addWidget(lbl)
                alertes_card.body.addWidget(alert_widget)
            layout.addWidget(alertes_card)

        # ===== Carte récapitulative =====
        card_recap = EmacCard("Récapitulatif")
        recap_layout = QHBoxLayout()

        sanctions_frame = QFrame()
        sanctions_frame.setStyleSheet("padding: 12px; background: #fef3c7; border-radius: 8px;")
        sanctions_inner = QVBoxLayout(sanctions_frame)
        sanctions_inner.addWidget(QLabel("<b>Sanctions</b>"))
        nb_sanctions = sanctions_data.get('total', 0) if isinstance(sanctions_data, dict) else 0
        sanctions_inner.addWidget(QLabel(f"Total: {nb_sanctions}"))
        if isinstance(sanctions_data, dict) and sanctions_data.get('derniere_sanction'):
            sanctions_inner.addWidget(QLabel(f"Dernière: {self._format_date(sanctions_data.get('derniere_sanction'))}"))
        recap_layout.addWidget(sanctions_frame)

        alcool_frame = QFrame()
        alcool_frame.setStyleSheet("padding: 12px; background: #dbeafe; border-radius: 8px;")
        alcool_inner = QVBoxLayout(alcool_frame)
        alcool_inner.addWidget(QLabel("<b>Contrôles alcool</b>"))
        nb_alcool = alcoolemie_data.get('total', 0) if isinstance(alcoolemie_data, dict) else 0
        nb_positifs = alcoolemie_data.get('positifs', 0) if isinstance(alcoolemie_data, dict) else 0
        alcool_inner.addWidget(QLabel(f"Total: {nb_alcool}"))
        alcool_inner.addWidget(QLabel(f"Positifs: {nb_positifs}"))
        recap_layout.addWidget(alcool_frame)

        salivaire_frame = QFrame()
        salivaire_frame.setStyleSheet("padding: 12px; background: #f3e8ff; border-radius: 8px;")
        salivaire_inner = QVBoxLayout(salivaire_frame)
        salivaire_inner.addWidget(QLabel("<b>Tests salivaires</b>"))
        nb_salivaire = salivaire_data.get('total', 0) if isinstance(salivaire_data, dict) else 0
        nb_positifs_sal = salivaire_data.get('positifs', 0) if isinstance(salivaire_data, dict) else 0
        salivaire_inner.addWidget(QLabel(f"Total: {nb_salivaire}"))
        salivaire_inner.addWidget(QLabel(f"Positifs: {nb_positifs_sal}"))
        recap_layout.addWidget(salivaire_frame)

        entretiens_frame = QFrame()
        entretiens_frame.setStyleSheet("padding: 12px; background: #dcfce7; border-radius: 8px;")
        entretiens_inner = QVBoxLayout(entretiens_frame)
        entretiens_inner.addWidget(QLabel("<b>Entretiens</b>"))
        dernier_epp = entretiens_data.get('dernier_epp') if isinstance(entretiens_data, dict) else None
        dernier_eap = entretiens_data.get('dernier_eap') if isinstance(entretiens_data, dict) else None
        entretiens_inner.addWidget(QLabel(f"EPP: {self._format_date(dernier_epp) if dernier_epp else '-'}"))
        entretiens_inner.addWidget(QLabel(f"EAP: {self._format_date(dernier_eap) if dernier_eap else '-'}"))
        recap_layout.addWidget(entretiens_frame)

        card_recap.body.addLayout(recap_layout)
        layout.addWidget(card_recap)

        # ===== Sanctions détaillées =====
        sanctions_list = donnees.get('sanctions_liste', [])
        card_sanctions = EmacCard(f"Sanctions disciplinaires ({len(sanctions_list)})")

        btn_add_sanction = EmacButton("+ Nouvelle sanction", variant="primary")
        btn_add_sanction.clicked.connect(self._add_sanction)
        card_sanctions.body.addWidget(btn_add_sanction, alignment=Qt.AlignLeft)

        if sanctions_list:
            table_sanctions = QTableWidget()
            table_sanctions.setColumnCount(5)
            table_sanctions.setHorizontalHeaderLabels(["Date", "Type", "Durée (jours)", "Motif", "Actions"])
            table_sanctions.setRowCount(len(sanctions_list))
            table_sanctions.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_sanctions.setAlternatingRowColors(True)
            table_sanctions.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_sanctions.setEditTriggers(QAbstractItemView.NoEditTriggers)

            for row_idx, sanc in enumerate(sanctions_list):
                table_sanctions.setItem(row_idx, 0, QTableWidgetItem(self._format_date(sanc.get('date_sanction'))))
                table_sanctions.setItem(row_idx, 1, QTableWidgetItem(sanc.get('type_sanction', '-')))
                table_sanctions.setItem(row_idx, 2, QTableWidgetItem(str(sanc.get('duree_jours', '-')) if sanc.get('duree_jours') else '-'))
                motif = sanc.get('motif', '-')
                if motif and len(motif) > 50:
                    motif = motif[:50] + "..."
                table_sanctions.setItem(row_idx, 3, QTableWidgetItem(motif))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(2, 2, 2, 2)
                btn_layout_inner.setSpacing(4)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setFixedHeight(28)
                btn_edit.clicked.connect(lambda checked, s=sanc: self._edit_sanction(s))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="ghost")
                btn_del.setFixedHeight(28)
                btn_del.clicked.connect(lambda checked, s=sanc: self._delete_sanction(s))
                btn_layout_inner.addWidget(btn_del)

                table_sanctions.setCellWidget(row_idx, 4, btn_widget)

            table_sanctions.setMaximumHeight(180)
            card_sanctions.body.addWidget(table_sanctions)
        else:
            card_sanctions.body.addWidget(QLabel("Aucune sanction enregistrée"))

        layout.addWidget(card_sanctions)

        # ===== Contrôles (Alcool + Salivaire) =====
        controles_alcool = donnees.get('controles_alcool_liste', [])
        controles_salivaire = donnees.get('tests_salivaires_liste', [])

        card_controles = EmacCard("Contrôles (Alcool / Salivaire)")

        btn_layout_ctrl = QHBoxLayout()
        btn_add_alcool = EmacButton("+ Contrôle alcool", variant="primary")
        btn_add_alcool.clicked.connect(self._add_controle_alcool)
        btn_layout_ctrl.addWidget(btn_add_alcool)

        btn_add_salivaire = EmacButton("+ Test salivaire", variant="primary")
        btn_add_salivaire.clicked.connect(self._add_test_salivaire)
        btn_layout_ctrl.addWidget(btn_add_salivaire)
        btn_layout_ctrl.addStretch()
        card_controles.body.addLayout(btn_layout_ctrl)

        tables_layout = QHBoxLayout()

        alcool_container = QVBoxLayout()
        alcool_container.addWidget(QLabel("<b>Alcoolémie</b>"))
        if controles_alcool:
            table_alcool = QTableWidget()
            table_alcool.setColumnCount(3)
            table_alcool.setHorizontalHeaderLabels(["Date", "Résultat", "Taux"])
            table_alcool.setRowCount(min(5, len(controles_alcool)))
            table_alcool.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for row_idx, ctrl in enumerate(controles_alcool[:5]):
                table_alcool.setItem(row_idx, 0, QTableWidgetItem(self._format_datetime(ctrl.get('date_controle'))))
                table_alcool.setItem(row_idx, 1, QTableWidgetItem(ctrl.get('resultat', '-')))
                table_alcool.setItem(row_idx, 2, QTableWidgetItem(f"{ctrl.get('taux', '-')} g/L" if ctrl.get('taux') else '-'))
            table_alcool.setMaximumHeight(150)
            alcool_container.addWidget(table_alcool)
        else:
            alcool_container.addWidget(QLabel("Aucun contrôle"))
        tables_layout.addLayout(alcool_container)

        salivaire_container = QVBoxLayout()
        salivaire_container.addWidget(QLabel("<b>Tests salivaires</b>"))
        if controles_salivaire:
            table_salivaire = QTableWidget()
            table_salivaire.setColumnCount(2)
            table_salivaire.setHorizontalHeaderLabels(["Date", "Résultat"])
            table_salivaire.setRowCount(min(5, len(controles_salivaire)))
            table_salivaire.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for row_idx, test in enumerate(controles_salivaire[:5]):
                table_salivaire.setItem(row_idx, 0, QTableWidgetItem(self._format_datetime(test.get('date_test'))))
                table_salivaire.setItem(row_idx, 1, QTableWidgetItem(test.get('resultat', '-')))
            table_salivaire.setMaximumHeight(150)
            salivaire_container.addWidget(table_salivaire)
        else:
            salivaire_container.addWidget(QLabel("Aucun test"))
        tables_layout.addLayout(salivaire_container)

        card_controles.body.addLayout(tables_layout)
        layout.addWidget(card_controles)

        # ===== Entretiens professionnels =====
        entretiens_liste = donnees.get('entretiens_liste', [])
        card_entretiens = EmacCard(f"Entretiens professionnels ({len(entretiens_liste)})")

        btn_add_entretien = EmacButton("+ Nouvel entretien", variant="primary")
        btn_add_entretien.clicked.connect(self._add_entretien)
        card_entretiens.body.addWidget(btn_add_entretien, alignment=Qt.AlignLeft)

        if entretiens_liste:
            table_entretiens = QTableWidget()
            table_entretiens.setColumnCount(5)
            table_entretiens.setHorizontalHeaderLabels(["Date", "Type", "Manager", "Prochaine", "Actions"])
            table_entretiens.setRowCount(len(entretiens_liste))
            table_entretiens.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_entretiens.setAlternatingRowColors(True)
            table_entretiens.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_entretiens.setEditTriggers(QAbstractItemView.NoEditTriggers)

            for row_idx, ent in enumerate(entretiens_liste):
                table_entretiens.setItem(row_idx, 0, QTableWidgetItem(self._format_date(ent.get('date_entretien'))))
                table_entretiens.setItem(row_idx, 1, QTableWidgetItem(ent.get('type_entretien', '-')))
                table_entretiens.setItem(row_idx, 2, QTableWidgetItem(ent.get('manager_nom', '-')))
                table_entretiens.setItem(row_idx, 3, QTableWidgetItem(self._format_date(ent.get('prochaine_date'))))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(2, 2, 2, 2)
                btn_layout_inner.setSpacing(4)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setFixedHeight(28)
                btn_edit.clicked.connect(lambda checked, e=ent: self._edit_entretien(e))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="ghost")
                btn_del.setFixedHeight(28)
                btn_del.clicked.connect(lambda checked, e=ent: self._delete_entretien(e))
                btn_layout_inner.addWidget(btn_del)

                table_entretiens.setCellWidget(row_idx, 4, btn_widget)

            table_entretiens.setMaximumHeight(180)
            card_entretiens.body.addWidget(table_entretiens)
        else:
            card_entretiens.body.addWidget(QLabel("Aucun entretien enregistré"))

        layout.addWidget(card_entretiens)

        return container

    def _format_datetime(self, dt) -> str:
        """Formate une datetime pour affichage."""
        if not dt:
            return "-"
        try:
            if hasattr(dt, 'strftime'):
                return dt.strftime('%d/%m/%Y %H:%M')
            return str(dt)
        except Exception:
            return str(dt)

    # ===== Handlers Medical =====
    def _add_visite(self):
        """Ajoute une nouvelle visite médicale."""
        if not self.operateur_selectionne:
            return
        dialog = EditVisiteDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_visite(self, visite: dict):
        """Modifie une visite médicale."""
        if not self.operateur_selectionne:
            return
        dialog = EditVisiteDialog(self.operateur_selectionne['id'], visite, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_visite(self, visite: dict):
        """Supprime une visite médicale."""
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la visite du {self._format_date(visite.get('date_visite'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_visite(visite['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    def _add_accident(self):
        """Ajoute un nouvel accident du travail."""
        if not self.operateur_selectionne:
            return
        dialog = EditAccidentDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_accident(self, accident: dict):
        """Modifie un accident du travail."""
        if not self.operateur_selectionne:
            return
        dialog = EditAccidentDialog(self.operateur_selectionne['id'], accident, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_accident(self, accident: dict):
        """Supprime un accident du travail."""
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'accident du {self._format_date(accident.get('date_accident'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_accident(accident['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    # ===== Handlers Vie du salarié =====
    def _add_sanction(self):
        """Ajoute une nouvelle sanction."""
        if not self.operateur_selectionne:
            return
        dialog = EditSanctionDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_sanction(self, sanction: dict):
        """Modifie une sanction."""
        if not self.operateur_selectionne:
            return
        dialog = EditSanctionDialog(self.operateur_selectionne['id'], sanction, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_sanction(self, sanction: dict):
        """Supprime une sanction."""
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la sanction du {self._format_date(sanction.get('date_sanction'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_sanction(sanction['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    def _add_controle_alcool(self):
        """Ajoute un contrôle d'alcoolémie."""
        if not self.operateur_selectionne:
            return
        dialog = EditControleAlcoolDialog(self.operateur_selectionne['id'], self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_test_salivaire(self):
        """Ajoute un test salivaire."""
        if not self.operateur_selectionne:
            return
        dialog = EditTestSalivaireDialog(self.operateur_selectionne['id'], self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_entretien(self):
        """Ajoute un entretien professionnel."""
        if not self.operateur_selectionne:
            return
        dialog = EditEntretienDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_entretien(self, entretien: dict):
        """Modifie un entretien professionnel."""
        if not self.operateur_selectionne:
            return
        dialog = EditEntretienDialog(self.operateur_selectionne['id'], entretien, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_entretien(self, entretien: dict):
        """Supprime un entretien professionnel."""
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'entretien du {self._format_date(entretien.get('date_entretien'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_entretien(entretien['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    def _creer_widget_documents(self, documents: list) -> QWidget:
        """Crée le widget affichant les documents du domaine (actifs uniquement)."""
        # Filtrer seulement les documents actifs
        docs_actifs = [d for d in documents if d.get('statut') != 'archive']

        card = EmacCard(f"Documents associés ({len(docs_actifs)})")

        # Boutons d'action
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 10)

        btn_ajouter = EmacButton("+ Ajouter un document", variant="primary")
        btn_ajouter.clicked.connect(self._ajouter_document)
        btn_layout.addWidget(btn_ajouter)

        btn_layout.addStretch()
        card.body.addLayout(btn_layout)

        if not docs_actifs:
            label = QLabel("Aucun document pour ce domaine")
            label.setStyleSheet("color: #9ca3af; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(label)
        else:
            for doc in docs_actifs:
                doc_widget = QFrame()
                doc_widget.setStyleSheet("""
                    QFrame {
                        background: #f9fafb;
                        border: 1px solid #e5e7eb;
                        border-radius: 8px;
                        padding: 10px;
                        margin: 2px 0;
                    }
                    QFrame:hover {
                        background: #f3f4f6;
                        border-color: #3b82f6;
                    }
                """)

                doc_layout = QHBoxLayout(doc_widget)
                doc_layout.setContentsMargins(10, 8, 10, 8)

                # Infos du document
                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                nom_label = QLabel(doc.get('nom_affichage', '-'))
                nom_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
                nom_label.setStyleSheet("color: #1f2937; background: transparent;")
                info_layout.addWidget(nom_label)

                details = f"{doc.get('categorie_nom', '-')} • Ajouté le {self._format_date(doc.get('date_upload'))}"
                if doc.get('date_expiration'):
                    details += f" • Expire le {self._format_date(doc.get('date_expiration'))}"
                details_label = QLabel(details)
                details_label.setStyleSheet("color: #6b7280; font-size: 11px; background: transparent;")
                info_layout.addWidget(details_label)

                doc_layout.addLayout(info_layout, 1)

                doc_id = doc.get('id')

                # Bouton Archiver
                btn_archiver = QPushButton("📦 Archiver")
                btn_archiver.setCursor(Qt.PointingHandCursor)
                btn_archiver.setStyleSheet("""
                    QPushButton {
                        background: #f59e0b;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #d97706;
                    }
                """)
                btn_archiver.clicked.connect(lambda checked, d=doc_id: self._archiver_document_par_id(d))
                doc_layout.addWidget(btn_archiver)

                # Bouton Ouvrir
                btn_ouvrir = QPushButton("📂 Ouvrir")
                btn_ouvrir.setCursor(Qt.PointingHandCursor)
                btn_ouvrir.setStyleSheet("""
                    QPushButton {
                        background: #3b82f6;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #2563eb;
                    }
                """)
                btn_ouvrir.clicked.connect(lambda checked, d=doc_id: self._ouvrir_document_par_id(d))
                doc_layout.addWidget(btn_ouvrir)

                card.body.addWidget(doc_widget)

        return card

    def _restaurer_document_par_id(self, doc_id: int):
        """Restaure un document archivé."""
        from core.services.document_service import DocumentService

        reply = QMessageBox.question(
            self,
            "Confirmer la restauration",
            "Voulez-vous restaurer ce document ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            try:
                doc_service = DocumentService()
                success, message = doc_service.restore_document(doc_id)

                if success:
                    QMessageBox.information(self, "Succès", "Document restauré avec succès")
                    # Recharger et mettre à jour l'onglet archives
                    self._charger_contenu_domaine()
                    self._update_archives_tab()
                else:
                    QMessageBox.warning(self, "Erreur", message)
            except Exception as e:
                logger.exception(f"Erreur restauration document: {e}")
                QMessageBox.critical(self, "Erreur", "Impossible de restaurer le document")

    def _ouvrir_document_par_id(self, doc_id: int):
        """Ouvre un document par son ID."""
        from core.services.document_service import DocumentService
        doc_service = DocumentService()
        doc_path = doc_service.get_document_path(doc_id)

        if doc_path and doc_path.exists():
            import os
            if os.name == 'nt':  # Windows
                os.startfile(str(doc_path))
            else:  # Linux/Mac
                import subprocess
                subprocess.run(['xdg-open', str(doc_path)])
        else:
            QMessageBox.warning(self, "Erreur", "Le fichier n'a pas été trouvé sur le disque")

    def _archiver_document_par_id(self, doc_id: int):
        """Archive un document après confirmation."""
        from core.services.document_service import DocumentService

        # Confirmation
        reply = QMessageBox.question(
            self,
            "Confirmer l'archivage",
            "Voulez-vous archiver ce document ?\n\nIl ne sera plus visible dans la liste mais pourra être restauré via l'onglet Archives.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                doc_service = DocumentService()
                success, message = doc_service.archive_document(doc_id)

                if success:
                    QMessageBox.information(self, "Succès", "Document archivé avec succès")
                    # Rafraîchir l'affichage
                    self._charger_contenu_domaine()
                    # Mettre à jour l'onglet Archives
                    self._update_archives_tab()
                else:
                    QMessageBox.warning(self, "Erreur", message)
            except Exception as e:
                logger.exception(f"Erreur archivage document: {e}")

    def _charger_contenu_archives(self):
        """Charge et affiche les documents archivés."""
        if not self.operateur_selectionne:
            return

        operateur_id = self.operateur_selectionne['id']

        # Vider les zones
        self._vider_layout(self.layout_resume)
        self._vider_layout(self.layout_documents)

        # Récupérer les documents archivés
        archives = get_documents_archives_operateur(operateur_id)

        # Créer le widget des archives
        card = EmacCard(f"📦 Documents archivés ({len(archives)})")

        if not archives:
            label = QLabel("Aucun document archivé")
            label.setStyleSheet("color: #9ca3af; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(label)
        else:
            for doc in archives:
                doc_widget = QFrame()
                doc_widget.setStyleSheet("""
                    QFrame {
                        background: #f3f4f6;
                        border: 1px dashed #9ca3af;
                        border-radius: 8px;
                        padding: 10px;
                        margin: 2px 0;
                    }
                    QFrame:hover {
                        background: #e5e7eb;
                        border-color: #6b7280;
                    }
                """)

                doc_layout = QHBoxLayout(doc_widget)
                doc_layout.setContentsMargins(10, 8, 10, 8)

                # Infos du document
                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                nom_label = QLabel(f"📦 {doc.get('nom_affichage', '-')}")
                nom_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
                nom_label.setStyleSheet("color: #6b7280; background: transparent;")
                info_layout.addWidget(nom_label)

                details = f"{doc.get('categorie_nom', '-')} • Ajouté le {self._format_date(doc.get('date_upload'))}"
                details_label = QLabel(details)
                details_label.setStyleSheet("color: #9ca3af; font-size: 11px; background: transparent;")
                info_layout.addWidget(details_label)

                doc_layout.addLayout(info_layout, 1)

                doc_id = doc.get('id')

                # Bouton Restaurer
                btn_restaurer = QPushButton("🔄 Restaurer")
                btn_restaurer.setCursor(Qt.PointingHandCursor)
                btn_restaurer.setStyleSheet("""
                    QPushButton {
                        background: #10b981;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #059669;
                    }
                """)
                btn_restaurer.clicked.connect(lambda checked, d=doc_id: self._restaurer_document_par_id(d))
                doc_layout.addWidget(btn_restaurer)

                # Bouton Ouvrir
                btn_ouvrir = QPushButton("📂 Ouvrir")
                btn_ouvrir.setCursor(Qt.PointingHandCursor)
                btn_ouvrir.setStyleSheet("""
                    QPushButton {
                        background: #3b82f6;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #2563eb;
                    }
                """)
                btn_ouvrir.clicked.connect(lambda checked, d=doc_id: self._ouvrir_document_par_id(d))
                doc_layout.addWidget(btn_ouvrir)

                card.body.addWidget(doc_widget)

        self.layout_resume.addWidget(card)

    def _ajouter_document(self):
        """Ouvre le dialogue pour ajouter un document."""
        if not self.operateur_selectionne:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un opérateur")
            return

        dialog = AjouterDocumentDialog(
            operateur_id=self.operateur_selectionne['id'],
            domaine=self.domaine_actif,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            # Rafraîchir l'affichage
            self._afficher_details_operateur()

    def _ouvrir_document(self):
        """Ouvre le document sélectionné."""
        if not hasattr(self, 'documents_table'):
            return

        current_row = self.documents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un document")
            return

        doc_id = int(self.documents_table.item(current_row, 0).text())

        # Récupérer le chemin du document
        from core.services.document_service import DocumentService
        doc_service = DocumentService()
        doc_path = doc_service.get_document_path(doc_id)

        if doc_path and doc_path.exists():
            import os
            import subprocess
            # Ouvrir avec l'application par défaut du système
            if os.name == 'nt':  # Windows
                os.startfile(str(doc_path))
            elif os.name == 'posix':  # Linux/Mac
                subprocess.run(['xdg-open', str(doc_path)])
        else:
            QMessageBox.warning(self, "Erreur", "Le fichier n'a pas été trouvé sur le disque")

    # =========================================================================
    # FOOTER
    # =========================================================================

    def _creer_footer(self) -> QWidget:
        """Crée le pied de page avec les boutons d'action."""
        footer = QWidget()
        footer.setStyleSheet("background: #f9fafb; border-top: 1px solid #e5e7eb;")

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 12, 20, 12)

        # Bouton Actions en masse
        btn_bulk = QPushButton("Actions en masse")
        btn_bulk.setToolTip("Assigner formations, absences ou visites médicales à plusieurs employés")
        btn_bulk.setCursor(Qt.PointingHandCursor)
        btn_bulk.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #a855f7);
                color: white;
                padding: 10px 24px;
                border-radius: 8px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #9333ea);
            }
            QPushButton:pressed {
                background: #5b21b6;
            }
        """)
        btn_bulk.clicked.connect(self._open_bulk_assignment_dialog)
        layout.addWidget(btn_bulk)

        layout.addStretch()

        btn_fermer = EmacButton("Fermer", variant="ghost")
        btn_fermer.clicked.connect(self.close)
        layout.addWidget(btn_fermer)

        return footer

    def _open_bulk_assignment_dialog(self):
        """Ouvre le dialogue d'actions en masse."""
        from core.gui.bulk_assignment import BulkAssignmentDialog
        dialog = BulkAssignmentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Rafraîchir l'affichage si un opérateur est sélectionné
            if self.operateur_selectionne:
                self._charger_domaine(self.domaine_actif)

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _vider_layout(self, layout):
        """Supprime tous les widgets d'un layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._vider_layout(item.layout())

    def _format_date(self, date_val) -> str:
        """Formate une date pour l'affichage."""
        if not date_val:
            return '-'
        if hasattr(date_val, 'strftime'):
            return date_val.strftime('%d/%m/%Y')
        return str(date_val)


class GestionRHWidget(QWidget):
    """
    Widget RH (sans fenêtre) pour intégration dans d'autres dialogues.
    Version embarquable de GestionRHDialog.
    """

    data_changed = pyqtSignal()

    def __init__(self, parent=None, operateur_id=None):
        super().__init__(parent)

        # État
        self.operateur_selectionne = None
        self.domaine_actif = DomaineRH.GENERAL
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._executer_recherche)
        self._initial_operateur_id = operateur_id

        self._setup_ui()

        # Si un operateur_id est fourni, le sélectionner automatiquement après init
        if operateur_id:
            QTimer.singleShot(100, lambda: self._selectionner_operateur_par_id(operateur_id))

    def _setup_ui(self):
        """Construit l'interface utilisateur."""
        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Zone gauche: Sélection opérateur
        self.zone_gauche = self._creer_zone_selection()
        main_layout.addWidget(self.zone_gauche)

        # Séparateur vertical
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #e5e7eb;")
        separator.setFixedWidth(1)
        main_layout.addWidget(separator)

        # Zone droite: Détails RH
        self.zone_droite = self._creer_zone_details()
        main_layout.addWidget(self.zone_droite, 1)

    # =========================================================================
    # ZONE GAUCHE - Sélection opérateur
    # =========================================================================

    def _creer_zone_selection(self) -> QWidget:
        """Crée la zone de recherche et sélection d'opérateur."""
        zone = QWidget()
        zone.setFixedWidth(320)
        zone.setStyleSheet("background-color: #f8fafc;")

        layout = QVBoxLayout(zone)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Titre + Bouton Actions en masse
        header_layout = QHBoxLayout()
        titre = QLabel("Sélection Opérateur")
        titre.setFont(QFont("Segoe UI", 14, QFont.Bold))
        titre.setStyleSheet("color: #111827;")
        header_layout.addWidget(titre)
        header_layout.addStretch()

        btn_bulk = QPushButton("Actions en masse")
        btn_bulk.setToolTip("Assigner formations, absences ou visites médicales à plusieurs employés")
        btn_bulk.setCursor(Qt.PointingHandCursor)
        btn_bulk.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #a855f7);
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #9333ea);
            }
            QPushButton:pressed {
                background: #5b21b6;
            }
        """)
        btn_bulk.clicked.connect(self._open_bulk_assignment_dialog)
        header_layout.addWidget(btn_bulk)

        layout.addLayout(header_layout)

        # Champ de recherche
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)

        # Label
        search_label = QLabel("Rechercher par nom, prénom ou matricule")
        search_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        search_layout.addWidget(search_label)

        # Input de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tapez pour rechercher...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)

        layout.addWidget(search_container)

        # Liste des résultats
        results_label = QLabel("Résultats")
        results_label.setStyleSheet("color: #374151; font-weight: 600; margin-top: 8px;")
        layout.addWidget(results_label)

        self.liste_operateurs = QListWidget()
        self.liste_operateurs.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: white;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f3f4f6;
            }
            QListWidget::item:selected {
                background-color: #eff6ff;
                color: #1e40af;
            }
            QListWidget::item:hover {
                background-color: #f9fafb;
            }
        """)
        self.liste_operateurs.itemClicked.connect(self._on_operateur_selectionne)
        layout.addWidget(self.liste_operateurs, 1)

        # Compteur de résultats
        self.compteur_resultats = QLabel("0 opérateur(s)")
        self.compteur_resultats.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(self.compteur_resultats)

        # Charger les opérateurs actifs par défaut
        QTimer.singleShot(100, lambda: self._executer_recherche())

        return zone

    def _on_search_changed(self, text: str):
        """Déclenche une recherche avec délai (debounce)."""
        self._search_timer.stop()
        self._search_timer.start(300)  # 300ms de délai

    def _executer_recherche(self):
        """Exécute la recherche d'opérateurs."""
        recherche = self.search_input.text().strip()
        resultats = rechercher_operateurs(recherche=recherche if recherche else None)

        self.liste_operateurs.clear()
        for op in resultats:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, op['id'])

            # Texte formaté
            nom_complet = op.get('nom_complet', f"{op.get('prenom', '')} {op.get('nom', '')}")
            matricule = op.get('matricule', '-')
            statut = op.get('statut', 'ACTIF')

            item.setText(f"{nom_complet}\n{matricule}")
            item.setToolTip(f"ID: {op['id']} | Statut: {statut}")

            self.liste_operateurs.addItem(item)

        self.compteur_resultats.setText(f"{len(resultats)} opérateur(s)")

    def _on_operateur_selectionne(self, item: QListWidgetItem):
        """Appelé quand un opérateur est sélectionné dans la liste."""
        operateur_id = item.data(Qt.UserRole)
        self.operateur_selectionne = get_operateur_by_id(operateur_id)

        if self.operateur_selectionne:
            self._afficher_details_operateur()

    def _selectionner_operateur_par_id(self, operateur_id: int):
        """Sélectionne automatiquement un opérateur par son ID."""
        # Charger l'opérateur directement
        self.operateur_selectionne = get_operateur_by_id(operateur_id)

        if self.operateur_selectionne:
            # Afficher les détails
            self._afficher_details_operateur()

            # Sélectionner dans la liste si présent
            for i in range(self.liste_operateurs.count()):
                item = self.liste_operateurs.item(i)
                if item.data(Qt.UserRole) == operateur_id:
                    self.liste_operateurs.setCurrentItem(item)
                    break

    # =========================================================================
    # ZONE DROITE - Détails RH
    # =========================================================================

    def _creer_zone_details(self) -> QWidget:
        """Crée la zone d'affichage des détails RH."""
        zone = QWidget()
        layout = QVBoxLayout(zone)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stack pour basculer entre placeholder et contenu
        self.stack_details = QStackedWidget()

        # Page 0: Placeholder (aucun opérateur sélectionné)
        self.placeholder = self._creer_placeholder()
        self.stack_details.addWidget(self.placeholder)

        # Page 1: Contenu RH
        self.contenu_rh = self._creer_contenu_rh()
        self.stack_details.addWidget(self.contenu_rh)

        layout.addWidget(self.stack_details)

        return zone

    def _creer_placeholder(self) -> QWidget:
        """Crée le placeholder affiché quand aucun opérateur n'est sélectionné."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        # Icône
        icon = QLabel("👤")
        icon.setFont(QFont("Segoe UI", 48))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        # Message
        message = QLabel("Sélectionnez un opérateur")
        message.setFont(QFont("Segoe UI", 18, QFont.Bold))
        message.setStyleSheet("color: #6b7280;")
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)

        # Sous-message
        sous_message = QLabel("Utilisez la zone de recherche à gauche\npour trouver un opérateur")
        sous_message.setStyleSheet("color: #9ca3af;")
        sous_message.setAlignment(Qt.AlignCenter)
        layout.addWidget(sous_message)

        return widget

    def _creer_contenu_rh(self) -> QWidget:
        """Crée le contenu RH (affiché quand un opérateur est sélectionné)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # En-tête avec infos opérateur
        self.header_operateur = self._creer_header_operateur()
        layout.addWidget(self.header_operateur)

        # Barre de navigation des domaines RH
        self.nav_domaines = self._creer_navigation_domaines()
        layout.addWidget(self.nav_domaines)

        # Zone de contenu scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Container pour résumé + documents
        self.container_domaine = QWidget()
        self.layout_domaine = QVBoxLayout(self.container_domaine)
        self.layout_domaine.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.setSpacing(16)

        # Zone résumé des données
        self.zone_resume = QWidget()
        self.layout_resume = QVBoxLayout(self.zone_resume)
        self.layout_resume.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.addWidget(self.zone_resume)

        # Zone documents
        self.zone_documents = QWidget()
        self.layout_documents = QVBoxLayout(self.zone_documents)
        self.layout_documents.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.addWidget(self.zone_documents)

        # Spacer
        self.layout_domaine.addStretch()

        scroll.setWidget(self.container_domaine)
        layout.addWidget(scroll, 1)

        return widget

    def _creer_header_operateur(self) -> QWidget:
        """Crée l'en-tête compact avec les infos de l'opérateur sélectionné."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: #1e40af;
                border-radius: 8px;
            }
        """)
        header.setFixedHeight(50)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)

        # Nom
        self.label_nom_operateur = QLabel("Nom Prénom")
        self.label_nom_operateur.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.label_nom_operateur.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(self.label_nom_operateur)

        # Séparateur
        sep = QLabel("•")
        sep.setStyleSheet("color: #93c5fd; background: transparent; margin: 0 8px;")
        layout.addWidget(sep)

        # Matricule
        self.label_matricule = QLabel("-")
        self.label_matricule.setStyleSheet("color: #bfdbfe; background: transparent; font-size: 13px;")
        layout.addWidget(self.label_matricule)

        layout.addStretch()

        # Badge statut
        self.badge_statut = QLabel("ACTIF")
        self.badge_statut.setStyleSheet("""
            background: #10b981;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 11px;
        """)
        layout.addWidget(self.badge_statut)

        return header

    def _creer_navigation_domaines(self) -> QWidget:
        """Crée la barre de navigation entre les domaines RH."""
        nav = QWidget()
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.boutons_domaines = {}
        domaines = get_domaines_rh()

        for domaine in domaines:
            btn = QPushButton(domaine['nom'])
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty('domaine', domaine['code'])
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 16px;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    background: white;
                    color: #374151;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: #f9fafb;
                    border-color: #d1d5db;
                }
                QPushButton:checked {
                    background: #1e40af;
                    color: white;
                    border-color: #1e40af;
                }
            """)
            btn.clicked.connect(lambda checked, d=domaine['code']: self._on_domaine_change(d))
            layout.addWidget(btn)
            self.boutons_domaines[domaine['code']] = btn

        # Bouton Archives (caché par défaut, affiché si documents archivés)
        self.btn_archives = QPushButton("📦 Archives")
        self.btn_archives.setCheckable(True)
        self.btn_archives.setCursor(Qt.PointingHandCursor)
        self.btn_archives.setStyleSheet("""
            QPushButton {
                padding: 10px 16px;
                border: 1px solid #f59e0b;
                border-radius: 8px;
                background: #fffbeb;
                color: #92400e;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #fef3c7;
                border-color: #d97706;
            }
            QPushButton:checked {
                background: #f59e0b;
                color: white;
                border-color: #f59e0b;
            }
        """)
        self.btn_archives.clicked.connect(self._on_archives_click)
        self.btn_archives.setVisible(False)  # Caché par défaut
        layout.addWidget(self.btn_archives)

        layout.addStretch()

        return nav

    def _update_archives_tab(self):
        """Met à jour la visibilité et le compteur de l'onglet Archives."""
        if not self.operateur_selectionne:
            if hasattr(self, 'btn_archives'):
                self.btn_archives.setVisible(False)
            return

        archives = get_documents_archives_operateur(self.operateur_selectionne['id'])
        if archives:
            self.btn_archives.setText(f"📦 Archives ({len(archives)})")
            self.btn_archives.setVisible(True)
        else:
            self.btn_archives.setVisible(False)

    def _on_archives_click(self):
        """Appelé quand l'utilisateur clique sur l'onglet Archives."""
        # Décocher tous les autres boutons
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(False)
        self.btn_archives.setChecked(True)

        # Afficher les archives
        self._charger_contenu_archives()

    def _on_domaine_change(self, code_domaine: str):
        """Appelé quand l'utilisateur change de domaine RH."""
        # Mettre à jour l'état des boutons
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == code_domaine)

        # Mettre à jour le domaine actif
        self.domaine_actif = DomaineRH(code_domaine)

        # Recharger le contenu
        if self.operateur_selectionne:
            self._charger_contenu_domaine()

    def _afficher_details_operateur(self):
        """Affiche les détails de l'opérateur sélectionné."""
        if not self.operateur_selectionne:
            return

        op = self.operateur_selectionne

        # Mettre à jour l'en-tête
        nom_complet = op.get('nom_complet', f"{op.get('prenom', '')} {op.get('nom', '')}")
        self.label_nom_operateur.setText(nom_complet)
        self.label_matricule.setText(op.get('matricule', '-'))

        # Badge statut
        statut = op.get('statut', 'ACTIF')
        if statut == 'ACTIF':
            self.badge_statut.setText("ACTIF")
            self.badge_statut.setStyleSheet("""
                background: #10b981;
                color: white;
                padding: 6px 12px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            """)
        else:
            self.badge_statut.setText("INACTIF")
            self.badge_statut.setStyleSheet("""
                background: #6b7280;
                color: white;
                padding: 6px 12px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            """)

        # Activer le premier domaine par défaut
        self.domaine_actif = DomaineRH.GENERAL
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == DomaineRH.GENERAL.value)
        self.btn_archives.setChecked(False)

        # Charger le contenu du domaine
        self._charger_contenu_domaine()

        # Mettre à jour l'onglet Archives
        self._update_archives_tab()

        # Afficher la zone de contenu
        self.stack_details.setCurrentIndex(1)

    def _charger_contenu_domaine(self):
        """Charge le contenu du domaine RH actif."""
        if not self.operateur_selectionne:
            return

        operateur_id = self.operateur_selectionne['id']

        # Vider les zones
        self._vider_layout(self.layout_resume)
        self._vider_layout(self.layout_documents)

        # Charger les données du domaine
        donnees = get_donnees_domaine(operateur_id, self.domaine_actif)

        # Créer la zone de résumé selon le domaine
        widget_resume = self._creer_widget_resume(donnees)
        if widget_resume:
            self.layout_resume.addWidget(widget_resume)

        # Charger les documents du domaine (inclut les archives pour pouvoir les afficher si demandé)
        documents = get_documents_domaine(operateur_id, self.domaine_actif, include_archives=True)
        widget_documents = self._creer_widget_documents(documents)
        self.layout_documents.addWidget(widget_documents)

        # Émettre le signal de changement de données
        self.data_changed.emit()

    def _creer_widget_resume(self, donnees: dict) -> QWidget:
        """Crée le widget de résumé selon le domaine actif."""
        if self.domaine_actif == DomaineRH.GENERAL:
            return self._creer_resume_general(donnees)
        elif self.domaine_actif == DomaineRH.CONTRAT:
            return self._creer_resume_contrat(donnees)
        elif self.domaine_actif == DomaineRH.DECLARATION:
            return self._creer_resume_declaration(donnees)
        elif self.domaine_actif == DomaineRH.COMPETENCES:
            return self._creer_resume_competences(donnees)
        elif self.domaine_actif == DomaineRH.FORMATION:
            return self._creer_resume_formation(donnees)
        elif self.domaine_actif == DomaineRH.MEDICAL:
            return self._creer_resume_medical(donnees)
        elif self.domaine_actif == DomaineRH.VIE_SALARIE:
            return self._creer_resume_vie_salarie(donnees)
        return None

    def _creer_resume_general(self, donnees: dict) -> QWidget:
        """Crée le résumé des données générales."""
        self._donnees_generales = donnees  # Stocker pour édition

        card = EmacCard("Informations Générales")

        if donnees.get('error'):
            card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            return card

        # Bouton modifier en haut à droite
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        btn_edit = EmacButton("Modifier", variant="ghost")
        btn_edit.clicked.connect(self._edit_infos_generales)
        header_layout.addWidget(btn_edit)
        card.body.addLayout(header_layout)

        # Grille d'informations
        grid = QGridLayout()
        grid.setSpacing(12)

        # Helper pour gérer les valeurs None
        def val(key, default='-'):
            v = donnees.get(key)
            return v if v is not None and v != '' else default

        # Construire l'adresse complète
        adresse_parts = []
        if donnees.get('adresse1'):
            adresse_parts.append(donnees['adresse1'])
        if donnees.get('adresse2'):
            adresse_parts.append(donnees['adresse2'])
        adresse = ', '.join(adresse_parts) if adresse_parts else '-'

        # Construire ville + CP
        ville_parts = []
        if donnees.get('cp_adresse'):
            ville_parts.append(donnees['cp_adresse'])
        if donnees.get('ville_adresse'):
            ville_parts.append(donnees['ville_adresse'])
        ville = ' '.join(ville_parts) if ville_parts else '-'

        # Lieu de naissance
        naissance_parts = []
        if donnees.get('ville_naissance'):
            naissance_parts.append(donnees['ville_naissance'])
        if donnees.get('pays_naissance'):
            naissance_parts.append(f"({donnees['pays_naissance']})")
        lieu_naissance = ' '.join(naissance_parts) if naissance_parts else '-'

        infos = [
            ("Nom", val('nom')),
            ("Prénom", val('prenom')),
            ("Matricule", val('matricule')),
            ("Statut", val('statut')),
            ("Sexe", "Homme" if donnees.get('sexe') == 'M' else "Femme" if donnees.get('sexe') == 'F' else '-'),
            ("Nationalité", val('nationalite')),
            ("N° Sécurité Sociale", val('numero_ss')),
            ("Date de naissance", self._format_date(donnees.get('date_naissance'))),
            ("Lieu de naissance", lieu_naissance),
            ("Âge", f"{donnees.get('age')} ans" if donnees.get('age') else '-'),
            ("Date d'entrée", self._format_date(donnees.get('date_entree'))),
            ("Ancienneté", val('anciennete')),
            ("Téléphone", val('telephone')),
            ("Email", val('email')),
            ("Adresse", adresse),
            ("Ville", ville),
            ("Pays", val('pays_adresse')),
        ]

        for i, (label, valeur) in enumerate(infos):
            row, col = divmod(i, 2)
            lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
            lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
            grid.addWidget(lbl, row, col)

        card.body.addLayout(grid)
        return card

    def _edit_infos_generales(self):
        """Ouvre le formulaire d'édition des infos générales."""
        if not self.operateur_selectionne:
            return
        dialog = EditInfosGeneralesDialog(
            self.operateur_selectionne['id'],
            self._donnees_generales,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _creer_resume_contrat(self, donnees: dict) -> QWidget:
        """Crée le résumé du contrat."""
        self._donnees_contrat = donnees  # Stocker pour édition

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Boutons d'action
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        btn_add = EmacButton("+ Nouveau contrat", variant="primary")
        btn_add.clicked.connect(self._add_contrat)
        actions_layout.addWidget(btn_add)
        layout.addLayout(actions_layout)

        contrat = donnees.get('contrat_actif')

        if contrat:
            # Alerte si contrat expire bientôt
            jours = contrat.get('jours_restants')
            if jours is not None and jours <= 30:
                if jours < 0:
                    alert = EmacAlert(f"Contrat expiré depuis {abs(jours)} jour(s) !", variant="error")
                elif jours == 0:
                    alert = EmacAlert("Contrat expire aujourd'hui !", variant="error")
                else:
                    alert = EmacAlert(f"Contrat expire dans {jours} jour(s)", variant="warning")
                layout.addWidget(alert)

            # Carte contrat actif
            card = EmacCard("Contrat Actif")

            # Bouton modifier
            header = QHBoxLayout()
            header.addStretch()
            btn_edit = EmacButton("Modifier", variant="ghost")
            btn_edit.clicked.connect(lambda: self._edit_contrat(contrat))
            header.addWidget(btn_edit)
            card.body.addLayout(header)

            grid = QGridLayout()
            grid.setSpacing(12)

            infos = [
                ("Type", contrat.get('type_contrat', '-')),
                ("Date début", self._format_date(contrat.get('date_debut'))),
                ("Date fin", self._format_date(contrat.get('date_fin')) or "Indéterminée"),
                ("Jours restants", str(jours) if jours else "N/A"),
                ("ETP", str(contrat.get('etp', 1.0))),
                ("Catégorie", contrat.get('categorie', '-')),
                ("Emploi", contrat.get('emploi', '-')),
            ]

            for i, (label, valeur) in enumerate(infos):
                row, col = divmod(i, 2)
                lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
                lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
                grid.addWidget(lbl, row, col)

            card.body.addLayout(grid)
            layout.addWidget(card)
        else:
            alert = EmacAlert("Aucun contrat actif", variant="info")
            layout.addWidget(alert)

        return container

    def _add_contrat(self):
        """Ouvre le formulaire de création de contrat."""
        if not self.operateur_selectionne:
            return
        dialog = EditContratDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_contrat(self, contrat: dict):
        """Ouvre le formulaire d'édition de contrat."""
        if not self.operateur_selectionne:
            return
        dialog = EditContratDialog(self.operateur_selectionne['id'], contrat, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_declaration(self):
        """Ouvre le formulaire d'ajout de déclaration."""
        if not self.operateur_selectionne:
            return
        dialog = EditDeclarationDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_declaration(self, declaration: dict):
        """Ouvre le formulaire d'édition de déclaration."""
        if not self.operateur_selectionne:
            return
        dialog = EditDeclarationDialog(self.operateur_selectionne['id'], declaration, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_formation(self):
        """Ouvre le formulaire d'ajout de formation."""
        if not self.operateur_selectionne:
            return
        dialog = EditFormationDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_formation(self, formation: dict):
        """Ouvre le formulaire d'édition de formation."""
        if not self.operateur_selectionne:
            return
        dialog = EditFormationDialog(self.operateur_selectionne['id'], formation, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_declaration(self, declaration: dict):
        """Supprime une déclaration après confirmation."""
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette déclaration ?\n{declaration.get('type_declaration')} du {self._format_date(declaration.get('date_debut'))}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_declaration(declaration['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _delete_formation(self, formation: dict):
        """Supprime une formation après confirmation."""
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette formation ?\n{formation.get('intitule', 'N/A')}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_formation(formation['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _creer_resume_declaration(self, donnees: dict) -> QWidget:
        """Crée le résumé des déclarations."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Bouton ajouter en haut
        btn_add = EmacButton("+ Nouvelle déclaration", variant="primary")
        btn_add.clicked.connect(self._add_declaration)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        # Déclaration en cours
        en_cours = donnees.get('en_cours')
        if en_cours:
            alert = EmacAlert(
                f"Déclaration en cours: {en_cours.get('type_declaration')} "
                f"du {self._format_date(en_cours.get('date_debut'))} "
                f"au {self._format_date(en_cours.get('date_fin'))}",
                variant="info"
            )
            layout.addWidget(alert)

        # Statistiques
        stats = donnees.get('statistiques', {})
        if stats:
            card = EmacCard("Statistiques des déclarations")
            stats_layout = QHBoxLayout()

            for type_decl, data in stats.items():
                chip = EmacChip(f"{type_decl}: {data.get('nombre', 0)}", variant="info")
                stats_layout.addWidget(chip)

            stats_layout.addStretch()
            card.body.addLayout(stats_layout)
            layout.addWidget(card)

        # Liste des déclarations
        declarations = donnees.get('declarations', [])
        card = EmacCard(f"Déclarations ({len(declarations)})")
        if declarations:
            for decl in declarations:
                row = QHBoxLayout()
                info_text = f"{decl.get('type_declaration', 'N/A')} - {self._format_date(decl.get('date_debut'))} au {self._format_date(decl.get('date_fin'))}"
                row.addWidget(QLabel(info_text))
                row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.clicked.connect(lambda checked, d=decl: self._edit_declaration(d))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="ghost")
                btn_delete.clicked.connect(lambda checked, d=decl: self._delete_declaration(d))
                row.addWidget(btn_delete)
                card.body.addLayout(row)
        else:
            card.body.addWidget(QLabel("Aucune déclaration"))
        layout.addWidget(card)

        return container

    def _creer_resume_competences(self, donnees: dict) -> QWidget:
        """Crée le résumé des compétences transversales."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Bouton ajouter en haut
        btn_add = EmacButton("+ Nouvelle compétence", variant="primary")
        btn_add.clicked.connect(self._add_competence)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})

        # Alertes expirations
        expirees = stats.get('expirees', 0)
        if expirees > 0:
            alert = EmacAlert(f"{expirees} compétence(s) expirée(s) !", variant="error")
            layout.addWidget(alert)

        expire_bientot = stats.get('expire_bientot_30j', 0)
        if expire_bientot > 0:
            alert = EmacAlert(f"{expire_bientot} compétence(s) expirant dans les 30 jours", variant="warning")
            layout.addWidget(alert)

        # Carte statistiques
        card = EmacCard("Statistiques")
        stats_layout = QHBoxLayout()

        items = [
            ("Valides", stats.get('valides', 0)),
            ("Expirées", stats.get('expirees', 0)),
            ("Total", stats.get('total', 0)),
        ]

        for label, count in items:
            badge = QLabel(f"{label}: {count}")
            badge.setStyleSheet("""
                background: #f1f5f9;
                color: #475569;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            """)
            stats_layout.addWidget(badge)

        stats_layout.addStretch()
        card.body.addLayout(stats_layout)
        layout.addWidget(card)

        # Liste des compétences
        competences = donnees.get('competences', [])
        card_list = EmacCard(f"Compétences ({len(competences)})")

        if competences:
            for comp in competences:
                row = QHBoxLayout()

                # Indicateur de statut
                statut = comp.get('statut', 'valide')
                if statut == 'expiree':
                    indicator = "X"
                    color = "#ef4444"
                elif statut == 'expire_bientot':
                    indicator = "!"
                    color = "#f97316"
                elif statut == 'attention':
                    indicator = "~"
                    color = "#eab308"
                else:
                    indicator = "O"
                    color = "#22c55e"

                status_label = QLabel(indicator)
                status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
                status_label.setFixedWidth(20)
                row.addWidget(status_label)

                # Info compétence
                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                libelle = comp.get('libelle', 'N/A')
                categorie = comp.get('categorie', '')
                if categorie:
                    libelle = f"{libelle} [{categorie}]"
                label_nom = QLabel(libelle)
                label_nom.setStyleSheet("font-weight: 500;")
                info_layout.addWidget(label_nom)

                # Dates
                date_acq = comp.get('date_acquisition')
                date_exp = comp.get('date_expiration')
                date_text = f"Acquis le: {self._format_date(date_acq)}"
                if date_exp:
                    date_text += f" - Expire le: {self._format_date(date_exp)}"
                else:
                    date_text += " - Permanent"

                label_dates = QLabel(date_text)
                label_dates.setStyleSheet("color: #64748b; font-size: 12px;")
                info_layout.addWidget(label_dates)

                # Message de statut si besoin
                if statut in ('expire_bientot', 'attention', 'expiree'):
                    statut_label = comp.get('statut_label', '')
                    if statut_label:
                        label_statut = QLabel(statut_label)
                        label_statut.setStyleSheet(f"color: {color}; font-size: 11px; font-style: italic;")
                        info_layout.addWidget(label_statut)

                row.addLayout(info_layout)
                row.addStretch()

                # Boutons
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.clicked.connect(lambda checked, c=comp: self._edit_competence(c))
                row.addWidget(btn_edit)

                btn_delete = EmacButton("Retirer", variant="ghost")
                btn_delete.clicked.connect(lambda checked, c=comp: self._delete_competence(c))
                row.addWidget(btn_delete)

                card_list.body.addLayout(row)

                # Séparateur
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet("background: #e2e8f0;")
                card_list.body.addWidget(sep)
        else:
            card_list.body.addWidget(QLabel("Aucune compétence assignée"))

        layout.addWidget(card_list)

        return container

    def _add_competence(self):
        """Ouvre le formulaire d'ajout de compétence."""
        if not self.operateur_id:
            return
        dialog = EditCompetenceDialog(self.operateur_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_competence(self, competence: dict):
        """Ouvre le formulaire de modification de compétence."""
        dialog = EditCompetenceDialog(self.operateur_id, competence, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_competence(self, competence: dict):
        """Retire une compétence après confirmation."""
        libelle = competence.get('libelle', 'cette compétence')
        reply = QMessageBox.question(
            self,
            "Confirmer le retrait",
            f"Voulez-vous vraiment retirer la compétence '{libelle}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_competence_personnel(competence['assignment_id'])
            if success:
                QMessageBox.information(self, "Succès", message)
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _creer_resume_formation(self, donnees: dict) -> QWidget:
        """Crée le résumé des formations."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Bouton ajouter en haut
        btn_add = EmacButton("+ Nouvelle formation", variant="primary")
        btn_add.clicked.connect(self._add_formation)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})

        # Carte statistiques
        card = EmacCard("Statistiques Formations")
        stats_layout = QHBoxLayout()

        items = [
            ("Total", stats.get('total', 0)),
            ("Terminées", stats.get('terminees', 0)),
            ("En cours", stats.get('en_cours', 0)),
            ("Planifiées", stats.get('planifiees', 0)),
            ("Avec certificat", stats.get('avec_certificat', 0)),
        ]

        for label, count in items:
            badge = QLabel(f"{label}: {count}")
            badge.setStyleSheet("""
                background: #f1f5f9;
                color: #475569;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            """)
            stats_layout.addWidget(badge)

        stats_layout.addStretch()
        card.body.addLayout(stats_layout)
        layout.addWidget(card)

        # Liste des formations
        formations = donnees.get('formations', [])
        card_list = EmacCard(f"Formations ({len(formations)})")
        if formations:
            for form in formations:
                row = QHBoxLayout()
                info_text = f"{form.get('intitule', 'N/A')} - {form.get('statut', 'N/A')}"
                if form.get('date_debut'):
                    info_text += f" ({self._format_date(form.get('date_debut'))})"
                row.addWidget(QLabel(info_text))
                row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.clicked.connect(lambda checked, f=form: self._edit_formation(f))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="ghost")
                btn_delete.clicked.connect(lambda checked, f=form: self._delete_formation(f))
                row.addWidget(btn_delete)
                card_list.body.addLayout(row)
        else:
            card_list.body.addWidget(QLabel("Aucune formation enregistrée"))
        layout.addWidget(card_list)

        return container

    def _creer_resume_medical(self, donnees: dict) -> QWidget:
        """Crée le résumé du suivi médical."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if donnees.get('error'):
            error_card = EmacCard("Erreur")
            error_card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            layout.addWidget(error_card)
            return container

        medical_info = donnees.get('medical') or {}
        visites = donnees.get('visites') or []
        accidents = donnees.get('accidents') or []
        validites = donnees.get('validites') or []
        alertes = donnees.get('alertes') or []

        self._donnees_medical = donnees

        # ===== Alertes médicales =====
        if alertes:
            alertes_card = EmacCard("Alertes")
            for alerte in alertes:
                alert_widget = QFrame()
                alert_widget.setStyleSheet("""
                    QFrame {
                        background: #fef2f2;
                        border: 1px solid #fecaca;
                        border-radius: 6px;
                        padding: 8px 12px;
                        margin-bottom: 4px;
                    }
                """)
                alert_layout = QHBoxLayout(alert_widget)
                alert_layout.setContentsMargins(8, 4, 8, 4)
                lbl = QLabel(alerte.get('message', str(alerte)))
                lbl.setStyleSheet("color: #dc2626; font-weight: 500;")
                alert_layout.addWidget(lbl)
                alertes_card.body.addWidget(alert_widget)
            layout.addWidget(alertes_card)

        # ===== Suivi médical principal =====
        card_medical = EmacCard("Suivi Médical")
        grid = QGridLayout()
        grid.setSpacing(12)

        type_suivi = medical_info.get('type_suivi_vip') or "Non défini"
        periodicite = medical_info.get('periodicite_vip_mois') or 24

        infos = [
            ("Type de suivi VIP", type_suivi),
            ("Périodicité", f"{periodicite} mois"),
            ("Maladie professionnelle", "Oui" if medical_info.get('maladie_pro') else "Non"),
            ("Taux professionnel", f"{medical_info.get('taux_professionnel', 0)}%" if medical_info.get('taux_professionnel') else "-"),
        ]

        if medical_info.get('besoins_adaptation'):
            infos.append(("Besoins d'adaptation", medical_info.get('besoins_adaptation')))

        for i, (label, valeur) in enumerate(infos):
            r, c = divmod(i, 2)
            lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
            lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
            grid.addWidget(lbl, r, c)

        card_medical.body.addLayout(grid)
        layout.addWidget(card_medical)

        # ===== RQTH / OETH =====
        from datetime import date as date_class
        rqth_validites = [v for v in validites if v.get('type_validite') == 'RQTH']
        oeth_validites = [v for v in validites if v.get('type_validite') == 'OETH']

        card_rqth = EmacCard("RQTH / OETH")
        rqth_layout = QHBoxLayout()

        rqth_frame = QFrame()
        rqth_frame.setStyleSheet("padding: 8px; background: #f0fdf4; border-radius: 6px;")
        rqth_inner = QVBoxLayout(rqth_frame)
        rqth_inner.addWidget(QLabel("<b>RQTH</b>"))
        if rqth_validites:
            latest_rqth = rqth_validites[0]
            date_fin = latest_rqth.get('date_fin')
            statut = "Active" if date_fin and date_fin >= date_class.today() else "Expirée"
            rqth_inner.addWidget(QLabel(f"Statut: {statut}"))
            rqth_inner.addWidget(QLabel(f"Fin: {self._format_date(date_fin)}"))
            if latest_rqth.get('taux_incapacite'):
                rqth_inner.addWidget(QLabel(f"Taux: {latest_rqth.get('taux_incapacite')}%"))
        else:
            rqth_inner.addWidget(QLabel("Non applicable"))
        rqth_layout.addWidget(rqth_frame)

        oeth_frame = QFrame()
        oeth_frame.setStyleSheet("padding: 8px; background: #eff6ff; border-radius: 6px;")
        oeth_inner = QVBoxLayout(oeth_frame)
        oeth_inner.addWidget(QLabel("<b>OETH</b>"))
        if oeth_validites:
            latest_oeth = oeth_validites[0]
            date_fin = latest_oeth.get('date_fin')
            statut = "Active" if date_fin and date_fin >= date_class.today() else "Expirée"
            oeth_inner.addWidget(QLabel(f"Statut: {statut}"))
            oeth_inner.addWidget(QLabel(f"Fin: {self._format_date(date_fin)}"))
        else:
            oeth_inner.addWidget(QLabel("Non applicable"))
        rqth_layout.addWidget(oeth_frame)

        card_rqth.body.addLayout(rqth_layout)
        layout.addWidget(card_rqth)

        # ===== Visites médicales =====
        card_visites = EmacCard(f"Visites médicales ({len(visites)})")

        btn_add_visite = EmacButton("+ Nouvelle visite", variant="primary")
        btn_add_visite.clicked.connect(self._add_visite)
        card_visites.body.addWidget(btn_add_visite, alignment=Qt.AlignLeft)

        if visites:
            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["Date", "Type", "Résultat", "Médecin", "Prochaine", "Actions"])
            table.setRowCount(len(visites))
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)

            for row_idx, visite in enumerate(visites):
                table.setItem(row_idx, 0, QTableWidgetItem(self._format_date(visite.get('date_visite'))))
                table.setItem(row_idx, 1, QTableWidgetItem(visite.get('type_visite', '-')))
                table.setItem(row_idx, 2, QTableWidgetItem(visite.get('resultat', '-')))
                table.setItem(row_idx, 3, QTableWidgetItem(visite.get('medecin', '-')))
                table.setItem(row_idx, 4, QTableWidgetItem(self._format_date(visite.get('prochaine_visite'))))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(2, 2, 2, 2)
                btn_layout_inner.setSpacing(4)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setFixedHeight(28)
                btn_edit.clicked.connect(lambda checked, v=visite: self._edit_visite(v))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="ghost")
                btn_del.setFixedHeight(28)
                btn_del.clicked.connect(lambda checked, v=visite: self._delete_visite(v))
                btn_layout_inner.addWidget(btn_del)

                table.setCellWidget(row_idx, 5, btn_widget)

            table.setMaximumHeight(200)
            card_visites.body.addWidget(table)
        else:
            card_visites.body.addWidget(QLabel("Aucune visite enregistrée"))

        layout.addWidget(card_visites)

        # ===== Accidents du travail =====
        card_accidents = EmacCard(f"Accidents du travail ({len(accidents)})")

        btn_add_accident = EmacButton("+ Nouvel accident", variant="primary")
        btn_add_accident.clicked.connect(self._add_accident)
        card_accidents.body.addWidget(btn_add_accident, alignment=Qt.AlignLeft)

        if accidents:
            table_acc = QTableWidget()
            table_acc.setColumnCount(6)
            table_acc.setHorizontalHeaderLabels(["Date", "Avec arrêt", "Jours absence", "Siège lésions", "Nature", "Actions"])
            table_acc.setRowCount(len(accidents))
            table_acc.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_acc.setAlternatingRowColors(True)
            table_acc.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_acc.setEditTriggers(QAbstractItemView.NoEditTriggers)

            for row_idx, acc in enumerate(accidents):
                table_acc.setItem(row_idx, 0, QTableWidgetItem(self._format_date(acc.get('date_accident'))))
                table_acc.setItem(row_idx, 1, QTableWidgetItem("Oui" if acc.get('avec_arret') else "Non"))
                table_acc.setItem(row_idx, 2, QTableWidgetItem(str(acc.get('nb_jours_absence', '-'))))
                table_acc.setItem(row_idx, 3, QTableWidgetItem(acc.get('siege_lesions', '-')))
                table_acc.setItem(row_idx, 4, QTableWidgetItem(acc.get('nature_lesions', '-')))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(2, 2, 2, 2)
                btn_layout_inner.setSpacing(4)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setFixedHeight(28)
                btn_edit.clicked.connect(lambda checked, a=acc: self._edit_accident(a))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="ghost")
                btn_del.setFixedHeight(28)
                btn_del.clicked.connect(lambda checked, a=acc: self._delete_accident(a))
                btn_layout_inner.addWidget(btn_del)

                table_acc.setCellWidget(row_idx, 5, btn_widget)

            table_acc.setMaximumHeight(200)
            card_accidents.body.addWidget(table_acc)
        else:
            card_accidents.body.addWidget(QLabel("Aucun accident enregistré"))

        layout.addWidget(card_accidents)

        return container

    def _creer_resume_vie_salarie(self, donnees: dict) -> QWidget:
        """Crée le résumé de la vie du salarié."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if donnees.get('error'):
            error_card = EmacCard("Erreur")
            error_card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            layout.addWidget(error_card)
            return container

        sanctions_data = donnees.get('sanctions', {})
        alcoolemie_data = donnees.get('alcoolemie', {})
        salivaire_data = donnees.get('tests_salivaires', {})
        entretiens_data = donnees.get('entretiens', {})
        alertes = donnees.get('alertes', [])

        self._donnees_vie_salarie = donnees

        # ===== Alertes =====
        if alertes:
            alertes_card = EmacCard("Alertes")
            for alerte in alertes:
                alert_widget = QFrame()
                alert_widget.setStyleSheet("""
                    QFrame {
                        background: #fef2f2;
                        border: 1px solid #fecaca;
                        border-radius: 6px;
                        padding: 8px 12px;
                        margin-bottom: 4px;
                    }
                """)
                alert_layout = QHBoxLayout(alert_widget)
                alert_layout.setContentsMargins(8, 4, 8, 4)
                lbl = QLabel(alerte.get('message', str(alerte)))
                lbl.setStyleSheet("color: #dc2626; font-weight: 500;")
                alert_layout.addWidget(lbl)
                alertes_card.body.addWidget(alert_widget)
            layout.addWidget(alertes_card)

        # ===== Carte récapitulative =====
        card_recap = EmacCard("Récapitulatif")
        recap_layout = QHBoxLayout()

        sanctions_frame = QFrame()
        sanctions_frame.setStyleSheet("padding: 12px; background: #fef3c7; border-radius: 8px;")
        sanctions_inner = QVBoxLayout(sanctions_frame)
        sanctions_inner.addWidget(QLabel("<b>Sanctions</b>"))
        nb_sanctions = sanctions_data.get('total', 0) if isinstance(sanctions_data, dict) else 0
        sanctions_inner.addWidget(QLabel(f"Total: {nb_sanctions}"))
        if isinstance(sanctions_data, dict) and sanctions_data.get('derniere_sanction'):
            sanctions_inner.addWidget(QLabel(f"Dernière: {self._format_date(sanctions_data.get('derniere_sanction'))}"))
        recap_layout.addWidget(sanctions_frame)

        alcool_frame = QFrame()
        alcool_frame.setStyleSheet("padding: 12px; background: #dbeafe; border-radius: 8px;")
        alcool_inner = QVBoxLayout(alcool_frame)
        alcool_inner.addWidget(QLabel("<b>Contrôles alcool</b>"))
        nb_alcool = alcoolemie_data.get('total', 0) if isinstance(alcoolemie_data, dict) else 0
        nb_positifs = alcoolemie_data.get('positifs', 0) if isinstance(alcoolemie_data, dict) else 0
        alcool_inner.addWidget(QLabel(f"Total: {nb_alcool}"))
        alcool_inner.addWidget(QLabel(f"Positifs: {nb_positifs}"))
        recap_layout.addWidget(alcool_frame)

        salivaire_frame = QFrame()
        salivaire_frame.setStyleSheet("padding: 12px; background: #f3e8ff; border-radius: 8px;")
        salivaire_inner = QVBoxLayout(salivaire_frame)
        salivaire_inner.addWidget(QLabel("<b>Tests salivaires</b>"))
        nb_salivaire = salivaire_data.get('total', 0) if isinstance(salivaire_data, dict) else 0
        nb_positifs_sal = salivaire_data.get('positifs', 0) if isinstance(salivaire_data, dict) else 0
        salivaire_inner.addWidget(QLabel(f"Total: {nb_salivaire}"))
        salivaire_inner.addWidget(QLabel(f"Positifs: {nb_positifs_sal}"))
        recap_layout.addWidget(salivaire_frame)

        entretiens_frame = QFrame()
        entretiens_frame.setStyleSheet("padding: 12px; background: #dcfce7; border-radius: 8px;")
        entretiens_inner = QVBoxLayout(entretiens_frame)
        entretiens_inner.addWidget(QLabel("<b>Entretiens</b>"))
        dernier_epp = entretiens_data.get('dernier_epp') if isinstance(entretiens_data, dict) else None
        dernier_eap = entretiens_data.get('dernier_eap') if isinstance(entretiens_data, dict) else None
        entretiens_inner.addWidget(QLabel(f"EPP: {self._format_date(dernier_epp) if dernier_epp else '-'}"))
        entretiens_inner.addWidget(QLabel(f"EAP: {self._format_date(dernier_eap) if dernier_eap else '-'}"))
        recap_layout.addWidget(entretiens_frame)

        card_recap.body.addLayout(recap_layout)
        layout.addWidget(card_recap)

        # ===== Sanctions détaillées =====
        sanctions_list = donnees.get('sanctions_liste', [])
        card_sanctions = EmacCard(f"Sanctions disciplinaires ({len(sanctions_list)})")

        btn_add_sanction = EmacButton("+ Nouvelle sanction", variant="primary")
        btn_add_sanction.clicked.connect(self._add_sanction)
        card_sanctions.body.addWidget(btn_add_sanction, alignment=Qt.AlignLeft)

        if sanctions_list:
            table_sanctions = QTableWidget()
            table_sanctions.setColumnCount(5)
            table_sanctions.setHorizontalHeaderLabels(["Date", "Type", "Durée (jours)", "Motif", "Actions"])
            table_sanctions.setRowCount(len(sanctions_list))
            table_sanctions.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_sanctions.setAlternatingRowColors(True)
            table_sanctions.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_sanctions.setEditTriggers(QAbstractItemView.NoEditTriggers)

            for row_idx, sanc in enumerate(sanctions_list):
                table_sanctions.setItem(row_idx, 0, QTableWidgetItem(self._format_date(sanc.get('date_sanction'))))
                table_sanctions.setItem(row_idx, 1, QTableWidgetItem(sanc.get('type_sanction', '-')))
                table_sanctions.setItem(row_idx, 2, QTableWidgetItem(str(sanc.get('duree_jours', '-')) if sanc.get('duree_jours') else '-'))
                motif = sanc.get('motif', '-')
                if motif and len(motif) > 50:
                    motif = motif[:50] + "..."
                table_sanctions.setItem(row_idx, 3, QTableWidgetItem(motif))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(2, 2, 2, 2)
                btn_layout_inner.setSpacing(4)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setFixedHeight(28)
                btn_edit.clicked.connect(lambda checked, s=sanc: self._edit_sanction(s))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="ghost")
                btn_del.setFixedHeight(28)
                btn_del.clicked.connect(lambda checked, s=sanc: self._delete_sanction(s))
                btn_layout_inner.addWidget(btn_del)

                table_sanctions.setCellWidget(row_idx, 4, btn_widget)

            table_sanctions.setMaximumHeight(180)
            card_sanctions.body.addWidget(table_sanctions)
        else:
            card_sanctions.body.addWidget(QLabel("Aucune sanction enregistrée"))

        layout.addWidget(card_sanctions)

        # ===== Contrôles (Alcool + Salivaire) =====
        controles_alcool = donnees.get('controles_alcool_liste', [])
        controles_salivaire = donnees.get('tests_salivaires_liste', [])

        card_controles = EmacCard("Contrôles (Alcool / Salivaire)")

        btn_layout_ctrl = QHBoxLayout()
        btn_add_alcool = EmacButton("+ Contrôle alcool", variant="primary")
        btn_add_alcool.clicked.connect(self._add_controle_alcool)
        btn_layout_ctrl.addWidget(btn_add_alcool)

        btn_add_salivaire = EmacButton("+ Test salivaire", variant="primary")
        btn_add_salivaire.clicked.connect(self._add_test_salivaire)
        btn_layout_ctrl.addWidget(btn_add_salivaire)
        btn_layout_ctrl.addStretch()
        card_controles.body.addLayout(btn_layout_ctrl)

        tables_layout = QHBoxLayout()

        alcool_container = QVBoxLayout()
        alcool_container.addWidget(QLabel("<b>Alcoolémie</b>"))
        if controles_alcool:
            table_alcool = QTableWidget()
            table_alcool.setColumnCount(3)
            table_alcool.setHorizontalHeaderLabels(["Date", "Résultat", "Taux"])
            table_alcool.setRowCount(min(5, len(controles_alcool)))
            table_alcool.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for row_idx, ctrl in enumerate(controles_alcool[:5]):
                table_alcool.setItem(row_idx, 0, QTableWidgetItem(self._format_datetime(ctrl.get('date_controle'))))
                table_alcool.setItem(row_idx, 1, QTableWidgetItem(ctrl.get('resultat', '-')))
                table_alcool.setItem(row_idx, 2, QTableWidgetItem(f"{ctrl.get('taux', '-')} g/L" if ctrl.get('taux') else '-'))
            table_alcool.setMaximumHeight(150)
            alcool_container.addWidget(table_alcool)
        else:
            alcool_container.addWidget(QLabel("Aucun contrôle"))
        tables_layout.addLayout(alcool_container)

        salivaire_container = QVBoxLayout()
        salivaire_container.addWidget(QLabel("<b>Tests salivaires</b>"))
        if controles_salivaire:
            table_salivaire = QTableWidget()
            table_salivaire.setColumnCount(2)
            table_salivaire.setHorizontalHeaderLabels(["Date", "Résultat"])
            table_salivaire.setRowCount(min(5, len(controles_salivaire)))
            table_salivaire.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for row_idx, test in enumerate(controles_salivaire[:5]):
                table_salivaire.setItem(row_idx, 0, QTableWidgetItem(self._format_datetime(test.get('date_test'))))
                table_salivaire.setItem(row_idx, 1, QTableWidgetItem(test.get('resultat', '-')))
            table_salivaire.setMaximumHeight(150)
            salivaire_container.addWidget(table_salivaire)
        else:
            salivaire_container.addWidget(QLabel("Aucun test"))
        tables_layout.addLayout(salivaire_container)

        card_controles.body.addLayout(tables_layout)
        layout.addWidget(card_controles)

        # ===== Entretiens professionnels =====
        entretiens_liste = donnees.get('entretiens_liste', [])
        card_entretiens = EmacCard(f"Entretiens professionnels ({len(entretiens_liste)})")

        btn_add_entretien = EmacButton("+ Nouvel entretien", variant="primary")
        btn_add_entretien.clicked.connect(self._add_entretien)
        card_entretiens.body.addWidget(btn_add_entretien, alignment=Qt.AlignLeft)

        if entretiens_liste:
            table_entretiens = QTableWidget()
            table_entretiens.setColumnCount(5)
            table_entretiens.setHorizontalHeaderLabels(["Date", "Type", "Manager", "Prochaine", "Actions"])
            table_entretiens.setRowCount(len(entretiens_liste))
            table_entretiens.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_entretiens.setAlternatingRowColors(True)
            table_entretiens.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_entretiens.setEditTriggers(QAbstractItemView.NoEditTriggers)

            for row_idx, ent in enumerate(entretiens_liste):
                table_entretiens.setItem(row_idx, 0, QTableWidgetItem(self._format_date(ent.get('date_entretien'))))
                table_entretiens.setItem(row_idx, 1, QTableWidgetItem(ent.get('type_entretien', '-')))
                table_entretiens.setItem(row_idx, 2, QTableWidgetItem(ent.get('manager_nom', '-')))
                table_entretiens.setItem(row_idx, 3, QTableWidgetItem(self._format_date(ent.get('prochaine_date'))))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(2, 2, 2, 2)
                btn_layout_inner.setSpacing(4)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setFixedHeight(28)
                btn_edit.clicked.connect(lambda checked, e=ent: self._edit_entretien(e))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="ghost")
                btn_del.setFixedHeight(28)
                btn_del.clicked.connect(lambda checked, e=ent: self._delete_entretien(e))
                btn_layout_inner.addWidget(btn_del)

                table_entretiens.setCellWidget(row_idx, 4, btn_widget)

            table_entretiens.setMaximumHeight(180)
            card_entretiens.body.addWidget(table_entretiens)
        else:
            card_entretiens.body.addWidget(QLabel("Aucun entretien enregistré"))

        layout.addWidget(card_entretiens)

        return container

    def _format_datetime(self, dt) -> str:
        """Formate une datetime pour affichage."""
        if not dt:
            return "-"
        try:
            if hasattr(dt, 'strftime'):
                return dt.strftime('%d/%m/%Y %H:%M')
            return str(dt)
        except Exception:
            return str(dt)

    # ===== Handlers Medical =====
    def _add_visite(self):
        """Ajoute une nouvelle visite médicale."""
        if not self.operateur_selectionne:
            return
        dialog = EditVisiteDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_visite(self, visite: dict):
        """Modifie une visite médicale."""
        if not self.operateur_selectionne:
            return
        dialog = EditVisiteDialog(self.operateur_selectionne['id'], visite, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_visite(self, visite: dict):
        """Supprime une visite médicale."""
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la visite du {self._format_date(visite.get('date_visite'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_visite(visite['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    def _add_accident(self):
        """Ajoute un nouvel accident du travail."""
        if not self.operateur_selectionne:
            return
        dialog = EditAccidentDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_accident(self, accident: dict):
        """Modifie un accident du travail."""
        if not self.operateur_selectionne:
            return
        dialog = EditAccidentDialog(self.operateur_selectionne['id'], accident, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_accident(self, accident: dict):
        """Supprime un accident du travail."""
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'accident du {self._format_date(accident.get('date_accident'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_accident(accident['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    # ===== Handlers Vie du salarié =====
    def _add_sanction(self):
        """Ajoute une nouvelle sanction."""
        if not self.operateur_selectionne:
            return
        dialog = EditSanctionDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_sanction(self, sanction: dict):
        """Modifie une sanction."""
        if not self.operateur_selectionne:
            return
        dialog = EditSanctionDialog(self.operateur_selectionne['id'], sanction, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_sanction(self, sanction: dict):
        """Supprime une sanction."""
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la sanction du {self._format_date(sanction.get('date_sanction'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_sanction(sanction['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    def _add_controle_alcool(self):
        """Ajoute un contrôle d'alcoolémie."""
        if not self.operateur_selectionne:
            return
        dialog = EditControleAlcoolDialog(self.operateur_selectionne['id'], self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_test_salivaire(self):
        """Ajoute un test salivaire."""
        if not self.operateur_selectionne:
            return
        dialog = EditTestSalivaireDialog(self.operateur_selectionne['id'], self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_entretien(self):
        """Ajoute un entretien professionnel."""
        if not self.operateur_selectionne:
            return
        dialog = EditEntretienDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_entretien(self, entretien: dict):
        """Modifie un entretien professionnel."""
        if not self.operateur_selectionne:
            return
        dialog = EditEntretienDialog(self.operateur_selectionne['id'], entretien, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_entretien(self, entretien: dict):
        """Supprime un entretien professionnel."""
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'entretien du {self._format_date(entretien.get('date_entretien'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_entretien(entretien['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    def _creer_widget_documents(self, documents: list) -> QWidget:
        """Crée le widget affichant les documents du domaine (actifs uniquement)."""
        # Filtrer seulement les documents actifs
        docs_actifs = [d for d in documents if d.get('statut') != 'archive']

        card = EmacCard(f"Documents associés ({len(docs_actifs)})")

        # Boutons d'action
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 10)

        btn_ajouter = EmacButton("+ Ajouter un document", variant="primary")
        btn_ajouter.clicked.connect(self._ajouter_document)
        btn_layout.addWidget(btn_ajouter)

        btn_layout.addStretch()
        card.body.addLayout(btn_layout)

        if not docs_actifs:
            label = QLabel("Aucun document pour ce domaine")
            label.setStyleSheet("color: #9ca3af; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(label)
        else:
            for doc in docs_actifs:
                doc_widget = QFrame()
                doc_widget.setStyleSheet("""
                    QFrame {
                        background: #f9fafb;
                        border: 1px solid #e5e7eb;
                        border-radius: 8px;
                        padding: 10px;
                        margin: 2px 0;
                    }
                    QFrame:hover {
                        background: #f3f4f6;
                        border-color: #3b82f6;
                    }
                """)

                doc_layout = QHBoxLayout(doc_widget)
                doc_layout.setContentsMargins(10, 8, 10, 8)

                # Infos du document
                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                nom_label = QLabel(doc.get('nom_affichage', '-'))
                nom_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
                nom_label.setStyleSheet("color: #1f2937; background: transparent;")
                info_layout.addWidget(nom_label)

                details = f"{doc.get('categorie_nom', '-')} • Ajouté le {self._format_date(doc.get('date_upload'))}"
                if doc.get('date_expiration'):
                    details += f" • Expire le {self._format_date(doc.get('date_expiration'))}"
                details_label = QLabel(details)
                details_label.setStyleSheet("color: #6b7280; font-size: 11px; background: transparent;")
                info_layout.addWidget(details_label)

                doc_layout.addLayout(info_layout, 1)

                doc_id = doc.get('id')

                # Bouton Archiver
                btn_archiver = QPushButton("📦 Archiver")
                btn_archiver.setCursor(Qt.PointingHandCursor)
                btn_archiver.setStyleSheet("""
                    QPushButton {
                        background: #f59e0b;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #d97706;
                    }
                """)
                btn_archiver.clicked.connect(lambda checked, d=doc_id: self._archiver_document_par_id(d))
                doc_layout.addWidget(btn_archiver)

                # Bouton Ouvrir
                btn_ouvrir = QPushButton("📂 Ouvrir")
                btn_ouvrir.setCursor(Qt.PointingHandCursor)
                btn_ouvrir.setStyleSheet("""
                    QPushButton {
                        background: #3b82f6;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #2563eb;
                    }
                """)
                btn_ouvrir.clicked.connect(lambda checked, d=doc_id: self._ouvrir_document_par_id(d))
                doc_layout.addWidget(btn_ouvrir)

                card.body.addWidget(doc_widget)

        return card

    def _restaurer_document_par_id(self, doc_id: int):
        """Restaure un document archivé."""
        from core.services.document_service import DocumentService

        reply = QMessageBox.question(
            self,
            "Confirmer la restauration",
            "Voulez-vous restaurer ce document ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            try:
                doc_service = DocumentService()
                success, message = doc_service.restore_document(doc_id)

                if success:
                    QMessageBox.information(self, "Succès", "Document restauré avec succès")
                    # Recharger et mettre à jour l'onglet archives
                    self._charger_contenu_domaine()
                    self._update_archives_tab()
                else:
                    QMessageBox.warning(self, "Erreur", message)
            except Exception as e:
                logger.exception(f"Erreur restauration document: {e}")
                QMessageBox.critical(self, "Erreur", "Impossible de restaurer le document")

    def _ouvrir_document_par_id(self, doc_id: int):
        """Ouvre un document par son ID."""
        from core.services.document_service import DocumentService
        doc_service = DocumentService()
        doc_path = doc_service.get_document_path(doc_id)

        if doc_path and doc_path.exists():
            import os
            if os.name == 'nt':  # Windows
                os.startfile(str(doc_path))
            else:  # Linux/Mac
                import subprocess
                subprocess.run(['xdg-open', str(doc_path)])
        else:
            QMessageBox.warning(self, "Erreur", "Le fichier n'a pas été trouvé sur le disque")

    def _archiver_document_par_id(self, doc_id: int):
        """Archive un document après confirmation."""
        from core.services.document_service import DocumentService

        # Confirmation
        reply = QMessageBox.question(
            self,
            "Confirmer l'archivage",
            "Voulez-vous archiver ce document ?\n\nIl ne sera plus visible dans la liste mais pourra être restauré via l'onglet Archives.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                doc_service = DocumentService()
                success, message = doc_service.archive_document(doc_id)

                if success:
                    QMessageBox.information(self, "Succès", "Document archivé avec succès")
                    # Rafraîchir l'affichage
                    self._charger_contenu_domaine()
                    # Mettre à jour l'onglet Archives
                    self._update_archives_tab()
                else:
                    QMessageBox.warning(self, "Erreur", message)
            except Exception as e:
                logger.exception(f"Erreur archivage document: {e}")

    def _charger_contenu_archives(self):
        """Charge et affiche les documents archivés."""
        if not self.operateur_selectionne:
            return

        operateur_id = self.operateur_selectionne['id']

        # Vider les zones
        self._vider_layout(self.layout_resume)
        self._vider_layout(self.layout_documents)

        # Récupérer les documents archivés
        archives = get_documents_archives_operateur(operateur_id)

        # Créer le widget des archives
        card = EmacCard(f"📦 Documents archivés ({len(archives)})")

        if not archives:
            label = QLabel("Aucun document archivé")
            label.setStyleSheet("color: #9ca3af; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(label)
        else:
            for doc in archives:
                doc_widget = QFrame()
                doc_widget.setStyleSheet("""
                    QFrame {
                        background: #f3f4f6;
                        border: 1px dashed #9ca3af;
                        border-radius: 8px;
                        padding: 10px;
                        margin: 2px 0;
                    }
                    QFrame:hover {
                        background: #e5e7eb;
                        border-color: #6b7280;
                    }
                """)

                doc_layout = QHBoxLayout(doc_widget)
                doc_layout.setContentsMargins(10, 8, 10, 8)

                # Infos du document
                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                nom_label = QLabel(f"📦 {doc.get('nom_affichage', '-')}")
                nom_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
                nom_label.setStyleSheet("color: #6b7280; background: transparent;")
                info_layout.addWidget(nom_label)

                details = f"{doc.get('categorie_nom', '-')} • Ajouté le {self._format_date(doc.get('date_upload'))}"
                details_label = QLabel(details)
                details_label.setStyleSheet("color: #9ca3af; font-size: 11px; background: transparent;")
                info_layout.addWidget(details_label)

                doc_layout.addLayout(info_layout, 1)

                doc_id = doc.get('id')

                # Bouton Restaurer
                btn_restaurer = QPushButton("🔄 Restaurer")
                btn_restaurer.setCursor(Qt.PointingHandCursor)
                btn_restaurer.setStyleSheet("""
                    QPushButton {
                        background: #10b981;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #059669;
                    }
                """)
                btn_restaurer.clicked.connect(lambda checked, d=doc_id: self._restaurer_document_par_id(d))
                doc_layout.addWidget(btn_restaurer)

                # Bouton Ouvrir
                btn_ouvrir = QPushButton("📂 Ouvrir")
                btn_ouvrir.setCursor(Qt.PointingHandCursor)
                btn_ouvrir.setStyleSheet("""
                    QPushButton {
                        background: #3b82f6;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #2563eb;
                    }
                """)
                btn_ouvrir.clicked.connect(lambda checked, d=doc_id: self._ouvrir_document_par_id(d))
                doc_layout.addWidget(btn_ouvrir)

                card.body.addWidget(doc_widget)

        self.layout_resume.addWidget(card)

    def _ajouter_document(self):
        """Ouvre le dialogue pour ajouter un document."""
        if not self.operateur_selectionne:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un opérateur")
            return

        dialog = AjouterDocumentDialog(
            operateur_id=self.operateur_selectionne['id'],
            domaine=self.domaine_actif,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            # Rafraîchir l'affichage
            self._afficher_details_operateur()

    def _ouvrir_document(self):
        """Ouvre le document sélectionné."""
        if not hasattr(self, 'documents_table'):
            return

        current_row = self.documents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un document")
            return

        doc_id = int(self.documents_table.item(current_row, 0).text())

        # Récupérer le chemin du document
        from core.services.document_service import DocumentService
        doc_service = DocumentService()
        doc_path = doc_service.get_document_path(doc_id)

        if doc_path and doc_path.exists():
            import os
            import subprocess
            # Ouvrir avec l'application par défaut du système
            if os.name == 'nt':  # Windows
                os.startfile(str(doc_path))
            elif os.name == 'posix':  # Linux/Mac
                subprocess.run(['xdg-open', str(doc_path)])
        else:
            QMessageBox.warning(self, "Erreur", "Le fichier n'a pas été trouvé sur le disque")

    # =========================================================================
    # ACTIONS EN MASSE
    # =========================================================================

    def _open_bulk_assignment_dialog(self):
        """Ouvre le dialogue d'actions en masse."""
        from core.gui.bulk_assignment import BulkAssignmentDialog
        dialog = BulkAssignmentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Rafraîchir l'affichage si un opérateur est sélectionné
            if self.operateur_selectionne:
                self._charger_contenu_domaine()

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _vider_layout(self, layout):
        """Supprime tous les widgets d'un layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._vider_layout(item.layout())

    def _format_date(self, date_val) -> str:
        """Formate une date pour l'affichage."""
        if not date_val:
            return '-'
        if hasattr(date_val, 'strftime'):
            return date_val.strftime('%d/%m/%Y')
        return str(date_val)


# Pour compatibilité avec l'ancien code qui pourrait importer ce module
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = GestionRHDialog()
    dialog.show()
    sys.exit(app.exec_())
