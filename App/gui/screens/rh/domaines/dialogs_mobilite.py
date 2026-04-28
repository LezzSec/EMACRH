# -*- coding: utf-8 -*-
"""
Dialogs mobilité : véhicule et distance domicile-entreprise.
"""

from PyQt5.QtWidgets import QFormLayout, QComboBox, QLineEdit, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QGroupBox
from PyQt5.QtCore import QDate

from gui.components.emac_dialog import EmacFormDialog
from domain.services.rh.mobilite_service import (
    create_vehicule, update_vehicule,
    create_mobilite, update_mobilite,
    calculer_prime, calculer_ik, normaliser_distance_palier,
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
        vehicule_group = QGroupBox("Véhicule utilisé")
        form = QFormLayout(vehicule_group)
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

        self.content_layout.addWidget(vehicule_group)

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

    def __init__(self, personnel_id: int, mobilite: dict = None, vehicule: dict = None,
                 distance_auto: float = None, duree_auto: int = None, parent=None):
        self.personnel_id = personnel_id
        self.mobilite = mobilite or {}
        self.vehicule = vehicule or {}
        self.is_edit = bool(mobilite)
        self.distance_auto = distance_auto
        self.duree_auto = duree_auto
        title = "Modifier la mobilité" if self.is_edit else "Déclarer la mobilité"
        super().__init__(title=title, min_width=440, min_height=380, add_title_bar=False, parent=parent)

    def init_ui(self):
        # Bannière distance calculée automatiquement
        if self.distance_auto is not None and not self.is_edit:
            from PyQt5.QtWidgets import QLabel, QHBoxLayout, QWidget, QPushButton
            banner = QWidget()
            banner.setStyleSheet(
                "background: #eff6ff; border: 1px solid #93c5fd; border-radius: 6px;"
            )
            banner_layout = QHBoxLayout(banner)
            banner_layout.setContentsMargins(10, 8, 10, 8)
            duree_txt = f" ({self.duree_auto} min)" if self.duree_auto else ""
            lbl = QLabel(f"Distance calculée depuis l'adresse : <b>{self.distance_auto} km{duree_txt}</b>")
            lbl.setStyleSheet("color: #1e40af; border: none; background: transparent;")
            banner_layout.addWidget(lbl, 1)
            btn_use = QPushButton("Utiliser cette distance")
            btn_use.setStyleSheet(
                "QPushButton { background: #3b82f6; color: white; border: none; "
                "border-radius: 4px; padding: 4px 10px; font-size: 12px; }"
                "QPushButton:hover { background: #2563eb; }"
            )
            btn_use.clicked.connect(lambda: self.distance.setValue(float(self.distance_auto)))
            banner_layout.addWidget(btn_use)
            self.content_layout.addWidget(banner)

        mobilite_group = QGroupBox("Distance et mode de transport")
        form = QFormLayout(mobilite_group)
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
        methode_actuelle = self.mobilite.get('methode_calcul', 'manuel')
        idx = self.methode_combo.findData(methode_actuelle)
        if idx >= 0:
            self.methode_combo.setCurrentIndex(idx)
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

        self.content_layout.addWidget(mobilite_group)

        # Bouton recalcul distance
        from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QWidget, QLabel as _QLabel
        recalc_widget = QWidget()
        recalc_layout = QHBoxLayout(recalc_widget)
        recalc_layout.setContentsMargins(0, 4, 0, 0)
        self._recalc_btn = QPushButton("Recalculer la distance (OSM)")
        self._recalc_btn.setStyleSheet(
            "QPushButton { background: #f0f9ff; color: #0369a1; border: 1px solid #7dd3fc; "
            "border-radius: 4px; padding: 4px 10px; font-size: 12px; }"
            "QPushButton:hover { background: #e0f2fe; }"
            "QPushButton:disabled { background: #f1f5f9; color: #94a3b8; border-color: #cbd5e1; }"
        )
        self._recalc_btn.clicked.connect(self._recalculer_distance)
        self._recalc_status = _QLabel("")
        self._recalc_status.setStyleSheet("font-size: 11px; color: #64748b;")
        recalc_layout.addWidget(self._recalc_btn)
        recalc_layout.addWidget(self._recalc_status, 1)
        self.content_layout.addWidget(recalc_widget)

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
                distance_palier = normaliser_distance_palier(dist)
                lines.append(
                    f"Prime mobilité : <b>{prime['taux_journalier']} €/jour</b>  "
                    f"({prime['description']} — palier calculé sur {distance_palier} km)"
                )
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

    def _recalculer_distance(self):
        from gui.workers.db_worker import DbWorker, DbThreadPool
        from domain.services.geo.distance_service import compute_distances_for_commune

        cp = self.cp.text().strip() or self.mobilite.get('cp_depart', '')
        ville = self.ville.text().strip() or self.mobilite.get('ville_depart', '')

        if not cp or not ville:
            self._recalc_status.setText("Renseignez le code postal et la ville d'abord.")
            self._recalc_status.setStyleSheet("font-size: 11px; color: #dc2626;")
            return

        self._recalc_btn.setEnabled(False)
        self._recalc_status.setText("Calcul en cours...")
        self._recalc_status.setStyleSheet("font-size: 11px; color: #64748b;")

        worker = DbWorker(lambda **_: compute_distances_for_commune(cp, ville))
        worker.signals.result.connect(self._on_recalc_result)
        worker.signals.error.connect(self._on_recalc_error)
        DbThreadPool.start(worker)

    def _on_recalc_result(self, result):
        self._recalc_btn.setEnabled(True)
        if result is None:
            self._recalc_status.setText("Commune introuvable — vérifiez CP et ville.")
            self._recalc_status.setStyleSheet("font-size: 11px; color: #dc2626;")
            return

        dist = result.get('distance_mairie_km') or result.get('distance_commune_km')
        duree = result.get('duree_trajet_mairie_min') or result.get('duree_trajet_commune_min')
        if dist is None:
            self._recalc_status.setText("Distance non calculable (API indisponible).")
            self._recalc_status.setStyleSheet("font-size: 11px; color: #d97706;")
            return

        self.distance.setValue(float(dist))
        duree_txt = f" ({duree} min)" if duree else ""
        self._recalc_status.setText(f"Mis à jour : {dist} km{duree_txt}")
        self._recalc_status.setStyleSheet("font-size: 11px; color: #16a34a;")
        self._update_apercu()

    def _on_recalc_error(self, error_msg):
        from infrastructure.logging.logging_config import get_logger
        get_logger(__name__).error(f"Recalcul distance échoué : {error_msg}")
        self._recalc_btn.setEnabled(True)
        self._recalc_status.setText(f"Erreur : {error_msg}")
        self._recalc_status.setStyleSheet("font-size: 11px; color: #dc2626;")
        self._recalc_status.setToolTip(str(error_msg))

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
