# -*- coding: utf-8 -*-
"""
Dialogs mobilité : véhicule et distance domicile-entreprise.
"""

from PyQt5.QtWidgets import QFormLayout, QComboBox, QLineEdit, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit
from PyQt5.QtCore import QDate

from gui.components.emac_dialog import EmacFormDialog
from domain.services.rh.mobilite_service import (
    create_vehicule, update_vehicule,
    create_mobilite, update_mobilite,
    calculer_prime, calculer_ik,
)


class EditVehiculeDialog(EmacFormDialog):
    """Formulaire pour ajouter ou modifier le véhicule d'un salarié."""

    ENERGIES = ['essence', 'diesel', 'electrique', 'hybride', 'autre']
    ENERGIES_LABELS = {
        'essence': 'Essence',
        'diesel': 'Diesel',
        'electrique': 'Électrique',
        'hybride': 'Hybride',
        'autre': 'Autre',
    }

    def __init__(self, personnel_id: int, vehicule: dict = None, parent=None):
        self.personnel_id = personnel_id
        self.vehicule = vehicule or {}
        self.is_edit = bool(vehicule)
        title = "Modifier le véhicule" if self.is_edit else "Ajouter un véhicule"
        super().__init__(title=title, min_width=420, min_height=360, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(10)

        self.marque = QLineEdit(self.vehicule.get('marque') or '')
        self.marque.setPlaceholderText("Ex: Renault, Peugeot...")
        form.addRow("Marque :", self.marque)

        self.modele = QLineEdit(self.vehicule.get('modele') or '')
        self.modele.setPlaceholderText("Ex: Clio, 208...")
        form.addRow("Modèle :", self.modele)

        self.immatriculation = QLineEdit(self.vehicule.get('immatriculation') or '')
        self.immatriculation.setPlaceholderText("Ex: AB-123-CD")
        form.addRow("Immatriculation :", self.immatriculation)

        self.annee = QSpinBox()
        self.annee.setRange(1990, 2100)
        self.annee.setSpecialValueText("Non définie")
        self.annee.setValue(self.vehicule.get('annee') or 1990)
        form.addRow("Année :", self.annee)

        self.cv_fiscaux = QSpinBox()
        self.cv_fiscaux.setRange(1, 30)
        self.cv_fiscaux.setValue(self.vehicule.get('cv_fiscaux') or 5)
        self.cv_fiscaux.setSuffix(" CV fiscaux")
        form.addRow("Puissance fiscale :", self.cv_fiscaux)

        self.energie_combo = QComboBox()
        for val in self.ENERGIES:
            self.energie_combo.addItem(self.ENERGIES_LABELS[val], val)
        energie_actuelle = self.vehicule.get('energie', 'essence')
        idx = self.energie_combo.findData(energie_actuelle)
        if idx >= 0:
            self.energie_combo.setCurrentIndex(idx)
        form.addRow("Énergie :", self.energie_combo)

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        d = self.vehicule.get('date_debut')
        if d:
            self.date_debut.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_debut.setDate(QDate.currentDate())
        form.addRow("Utilisé depuis :", self.date_debut)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("Notes libres")
        self.notes.setText(self.vehicule.get('notes') or '')
        form.addRow("Notes :", self.notes)

        self.content_layout.addLayout(form)

    def validate(self):
        if self.cv_fiscaux.value() < 1:
            return False, "La puissance fiscale est obligatoire."
        return True, ""

    def save_to_db(self):
        d = self.date_debut.date()
        data = {
            'marque': self.marque.text().strip() or None,
            'modele': self.modele.text().strip() or None,
            'immatriculation': self.immatriculation.text().strip() or None,
            'annee': self.annee.value() if self.annee.value() > 1990 else None,
            'cv_fiscaux': self.cv_fiscaux.value(),
            'energie': self.energie_combo.currentData(),
            'date_debut': d.toPyDate() if d.isValid() else None,
            'actif': True,
            'notes': self.notes.toPlainText().strip() or None,
        }
        if self.is_edit:
            success, message = update_vehicule(self.vehicule['id'], data)
        else:
            success, message, _ = create_vehicule(self.personnel_id, data)
        if not success:
            raise Exception(message)


class EditMobiliteDialog(EmacFormDialog):
    """Formulaire pour saisir la distance domicile-entreprise d'un salarié."""

    MODES = ['voiture', 'velo', 'transport_commun', 'covoiturage', 'autre']
    MODES_LABELS = {
        'voiture': 'Voiture',
        'velo': 'Vélo',
        'transport_commun': 'Transport en commun',
        'covoiturage': 'Covoiturage',
        'autre': 'Autre',
    }
    METHODES = ['manuel', 'google_maps', 'ign', 'autre']
    METHODES_LABELS = {
        'manuel': 'Saisie manuelle',
        'google_maps': 'Google Maps',
        'ign': 'IGN',
        'autre': 'Autre',
    }

    def __init__(self, personnel_id: int, mobilite: dict = None, vehicule: dict = None, parent=None):
        self.personnel_id = personnel_id
        self.mobilite = mobilite or {}
        self.vehicule = vehicule or {}
        self.is_edit = bool(mobilite)
        title = "Modifier la mobilité" if self.is_edit else "Déclarer la mobilité"
        super().__init__(title=title, min_width=440, min_height=380, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(10)

        self.distance = QDoubleSpinBox()
        self.distance.setRange(0, 999)
        self.distance.setDecimals(1)
        self.distance.setSuffix(" km")
        self.distance.setValue(float(self.mobilite.get('distance_km') or 0))
        self.distance.valueChanged.connect(self._update_apercu)
        form.addRow("Distance aller (km) :", self.distance)

        self.mode_combo = QComboBox()
        for val in self.MODES:
            self.mode_combo.addItem(self.MODES_LABELS[val], val)
        mode_actuel = self.mobilite.get('mode_transport', 'voiture')
        idx = self.mode_combo.findData(mode_actuel)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        form.addRow("Mode de transport :", self.mode_combo)

        # CV pré-remplis depuis le véhicule actif si disponible
        self.cv_fiscaux = QSpinBox()
        self.cv_fiscaux.setRange(0, 30)
        self.cv_fiscaux.setSpecialValueText("Non renseigné")
        self.cv_fiscaux.setSuffix(" CV fiscaux")
        cv = self.mobilite.get('cv_fiscaux') or self.vehicule.get('cv_fiscaux') or 0
        self.cv_fiscaux.setValue(cv)
        self.cv_fiscaux.valueChanged.connect(self._update_apercu)
        form.addRow("Puissance fiscale :", self.cv_fiscaux)

        self.adresse = QLineEdit(self.mobilite.get('adresse_depart') or '')
        self.adresse.setPlaceholderText("Si différente de l'adresse enregistrée")
        form.addRow("Adresse de départ :", self.adresse)

        self.cp = QLineEdit(self.mobilite.get('cp_depart') or '')
        self.cp.setPlaceholderText("Code postal")
        form.addRow("Code postal :", self.cp)

        self.ville = QLineEdit(self.mobilite.get('ville_depart') or '')
        self.ville.setPlaceholderText("Ville")
        form.addRow("Ville :", self.ville)

        self.methode_combo = QComboBox()
        for val in self.METHODES:
            self.methode_combo.addItem(self.METHODES_LABELS[val], val)
        form.addRow("Méthode de calcul :", self.methode_combo)

        self.date_effet = QDateEdit()
        self.date_effet.setCalendarPopup(True)
        self.date_effet.setDisplayFormat("dd/MM/yyyy")
        d = self.mobilite.get('date_effet')
        if d:
            self.date_effet.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_effet.setDate(QDate.currentDate())
        form.addRow("Date d'effet :", self.date_effet)

        self.content_layout.addLayout(form)

        # Aperçu de la prime calculée
        from PyQt5.QtWidgets import QLabel
        self._apercu = QLabel()
        self._apercu.setStyleSheet(
            "padding: 8px 12px; background: #f0fdf4; border: 1px solid #86efac; "
            "border-radius: 6px; color: #166534;"
        )
        self._apercu.setWordWrap(True)
        self.content_layout.addWidget(self._apercu)
        self._update_apercu()

    def _update_apercu(self):
        dist = self.distance.value()
        cv = self.cv_fiscaux.value()
        lines = []
        if dist > 0:
            prime = calculer_prime(dist)
            if prime:
                lines.append(f"Prime mobilité : <b>{prime['taux_journalier']} €/jour</b>  ({prime['description']})")
            else:
                lines.append("Prime mobilité : aucun palier applicable")
        if cv > 0:
            ik = calculer_ik(cv)
            if ik:
                lines.append(f"IK véhicule : <b>{ik['taux_km']} €/km</b>  ({ik['description']})")
        if lines:
            self._apercu.setText("<br/>".join(lines))
            self._apercu.setVisible(True)
        else:
            self._apercu.setVisible(False)

    def validate(self):
        if self.distance.value() <= 0:
            return False, "La distance doit être supérieure à 0 km."
        return True, ""

    def save_to_db(self):
        d = self.date_effet.date()
        data = {
            'distance_km': self.distance.value(),
            'mode_transport': self.mode_combo.currentData(),
            'cv_fiscaux': self.cv_fiscaux.value() or None,
            'adresse_depart': self.adresse.text().strip() or None,
            'cp_depart': self.cp.text().strip() or None,
            'ville_depart': self.ville.text().strip() or None,
            'methode_calcul': self.methode_combo.currentData(),
            'date_effet': d.toPyDate() if d.isValid() else None,
        }
        if self.is_edit:
            success, message = update_mobilite(self.mobilite['id'], data)
        else:
            success, message, _ = create_mobilite(self.personnel_id, data)
        if not success:
            raise Exception(message)
