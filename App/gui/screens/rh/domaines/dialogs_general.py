# -*- coding: utf-8 -*-
"""
EditInfosGeneralesDialog — formulaire d'édition des informations générales d'un opérateur.
"""

from PyQt5.QtWidgets import (
    QFormLayout, QLineEdit, QComboBox, QGroupBox, QHBoxLayout, QDateEdit
)
from PyQt5.QtCore import QDate

from gui.components.emac_dialog import EmacFormDialog
from domain.services.rh.rh_service import update_infos_generales, is_matricule_disponible


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
        self.numero_ss.setMaxLength(21)
        form.addRow("N° Sécurité Sociale:", self.numero_ss)

        # Adresse avec bouton de recherche
        self.adresse1 = QLineEdit(self.donnees.get('adresse1') or '')
        self.adresse1.setPlaceholderText("Ex: 12 Rue de la Paix")
        form.addRow("Adresse:", self.adresse1)

        self.adresse2 = QLineEdit(self.donnees.get('adresse2') or '')
        form.addRow("Adresse (suite):", self.adresse2)

        cp_ville = QHBoxLayout()
        self.cp = QLineEdit(self.donnees.get('cp_adresse') or '')
        self.cp.setMaximumWidth(80)
        self.cp.setPlaceholderText("64270")
        self.cp.textChanged.connect(self._geo_from_cp)
        self.ville = QLineEdit(self.donnees.get('ville_adresse') or '')
        self.ville.setPlaceholderText("Ville")
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
        self.ville_naissance.setPlaceholderText("Ex: Bayonne")
        naissance_layout.addRow("Ville:", self.ville_naissance)

        self.pays_naissance = QLineEdit(self.donnees.get('pays_naissance') or '')
        self.pays_naissance.setPlaceholderText("Ex: France")
        naissance_layout.addRow("Pays:", self.pays_naissance)

        self.content_layout.addWidget(naissance_group)
        self.content_layout.addLayout(form)

    def _geo_from_cp(self, text: str):
        """Déclenché à chaque frappe dans le CP. Remplit Ville+Pays dès 5 chiffres.
        Si plusieurs communes correspondent, propose un choix à l'utilisateur."""
        cp = text.strip()
        if len(cp) != 5 or not cp.isdigit():
            return
        from domain.services.geo.address_service import get_cities_by_postal_code
        cities = get_cities_by_postal_code(cp)
        if not cities:
            return

        if len(cities) == 1:
            ville_choisie = cities[0]
        else:
            from PyQt5.QtWidgets import QInputDialog
            ville_choisie, ok = QInputDialog.getItem(
                self,
                "Plusieurs communes",
                f"Le code postal {cp} correspond à plusieurs communes :",
                cities,
                0,
                False,
            )
            if not ok:
                return

        if not self.ville.text().strip():
            self.ville.setText(ville_choisie)
        if not self.pays_adresse.text().strip():
            self.pays_adresse.setText("France")


    def _setup_city_autocomplete(self):
        pass

    def validate(self):
        if not self.nom.text().strip():
            return False, "Le nom est obligatoire."
        if not self.prenom.text().strip():
            return False, "Le prénom est obligatoire."

        nouveau_matricule = self.matricule.text().strip()
        if nouveau_matricule:
            if not is_matricule_disponible(nouveau_matricule, self.operateur_id):
                return False, f"Le matricule '{nouveau_matricule}' est déjà utilisé par un autre opérateur."

        dn = self.date_naissance.date().toPyDate() if self.date_naissance.date().year() > 1900 else None
        de = self.date_entree.date().toPyDate() if self.date_entree.date().year() > 1900 else None

        from datetime import date as _date
        if dn and de:
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
            'numero_ss': self.numero_ss.text().replace(' ', '').strip()[:15] or None,
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
