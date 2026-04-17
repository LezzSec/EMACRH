# -*- coding: utf-8 -*-
"""
Domaine RH : Informations générales.
"""
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QGridLayout, QMessageBox

from gui.components.ui_theme import EmacCard, EmacButton
from application.permission_manager import can
from gui.screens.rh.gestion_rh_dialogs import EditInfosGeneralesDialog
from .domaine_base import DomaineWidget
from .dialogs_mobilite import EditVehiculeDialog, EditMobiliteDialog
from domain.services.rh.mobilite_service import delete_vehicule


class DomaineGeneral(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        self._donnees = donnees
        card = EmacCard("Informations Générales")

        if donnees.get('error'):
            card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            self._layout.addWidget(card)
            return

        header_layout = QHBoxLayout()
        header_layout.addStretch()
        btn_edit = EmacButton("Modifier", variant="ghost")
        btn_edit.setVisible(can("rh.personnel.edit"))
        btn_edit.clicked.connect(self._edit_infos_generales)
        header_layout.addWidget(btn_edit)
        card.body.addLayout(header_layout)

        grid = QGridLayout()
        grid.setSpacing(12)

        def val(key, default='-'):
            v = donnees.get(key)
            return v if v is not None and v != '' else default

        adresse_parts = [donnees[k] for k in ('adresse1', 'adresse2') if donnees.get(k)]
        adresse = ', '.join(adresse_parts) or '-'

        ville_parts = [donnees[k] for k in ('cp_adresse', 'ville_adresse') if donnees.get(k)]
        ville = ' '.join(ville_parts) or '-'

        naissance_parts = []
        if donnees.get('ville_naissance'):
            naissance_parts.append(donnees['ville_naissance'])
        if donnees.get('pays_naissance'):
            naissance_parts.append(f"({donnees['pays_naissance']})")
        lieu_naissance = ' '.join(naissance_parts) or '-'

        cat_map = {'O': 'O - Ouvrier', 'E': 'E - Employé', 'T': 'T - Technicien', 'C': 'C - Cadre'}
        categorie_display = cat_map.get(donnees.get('categorie', ''), val('categorie'))

        if donnees.get('distance_domicile_km') is not None:
            dist_km = donnees['distance_domicile_km']
            duree = donnees.get('duree_trajet_min')
            distance_display = f"{dist_km} km ({duree} min)" if duree else f"{dist_km} km"
        else:
            distance_display = None

        infos = [
            ("Nom", val('nom')),
            ("Prénom", val('prenom')),
            ("Matricule", val('matricule')),
            ("Statut", val('statut')),
            ("Sexe", "Homme" if donnees.get('sexe') == 'M' else "Femme" if donnees.get('sexe') == 'F' else '-'),
            ("Nationalité", val('nationalite')),
            ("Catégorie", categorie_display),
            ("Service / Poste", val('numposte')),
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
        if distance_display:
            infos.append(("Distance domicile", distance_display))

        for i, (label, valeur) in enumerate(infos):
            row, col = divmod(i, 3)
            lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
            lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
            grid.addWidget(lbl, row, col)

        card.body.addLayout(grid)
        self._layout.addWidget(card)

        # --- Carte Véhicule ---
        self._build_card_vehicule(donnees)

        # --- Carte Mobilité ---
        self._build_card_mobilite(donnees)

    def _build_card_vehicule(self, donnees: dict):
        vehicule = donnees.get('vehicule') or {}
        card = EmacCard("Véhicule")

        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 0, 0, 8)
        if vehicule:
            btn_edit = EmacButton("Modifier", variant="outline")
            btn_edit.setVisible(can("rh.mobilite.edit"))
            btn_edit.clicked.connect(lambda: self._edit_vehicule(vehicule))
            btn_bar.addWidget(btn_edit)
            btn_del = EmacButton("Supprimer", variant="danger")
            btn_del.setVisible(can("rh.mobilite.edit"))
            btn_del.clicked.connect(lambda: self._delete_vehicule(vehicule))
            btn_bar.addWidget(btn_del)
        else:
            btn_add = EmacButton("+ Ajouter un véhicule", variant="primary")
            btn_add.setVisible(can("rh.mobilite.edit"))
            btn_add.clicked.connect(self._add_vehicule)
            btn_bar.addWidget(btn_add)
        btn_bar.addStretch()
        card.body.addLayout(btn_bar)

        if vehicule:
            energies = {'essence': 'Essence', 'diesel': 'Diesel', 'electrique': 'Électrique',
                        'hybride': 'Hybride', 'autre': 'Autre'}
            infos = []
            if vehicule.get('marque') or vehicule.get('modele'):
                infos.append(("Véhicule", f"{vehicule.get('marque', '')} {vehicule.get('modele', '')}".strip()))
            if vehicule.get('immatriculation'):
                infos.append(("Immatriculation", vehicule['immatriculation']))
            if vehicule.get('annee'):
                infos.append(("Année", str(vehicule['annee'])))
            infos.append(("Puissance fiscale", f"{vehicule.get('cv_fiscaux', '-')} CV"))
            infos.append(("Énergie", energies.get(vehicule.get('energie', ''), vehicule.get('energie', '-'))))

            grid = QGridLayout()
            grid.setSpacing(10)
            for i, (lbl_txt, val) in enumerate(infos):
                lbl = QLabel(f"<b>{lbl_txt}</b><br/>{val}")
                lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
                grid.addWidget(lbl, i // 3, i % 3)
            card.body.addLayout(grid)
        else:
            no_data = QLabel("Aucun véhicule enregistré.")
            no_data.setStyleSheet("color: #9ca3af; padding: 8px 0;")
            card.body.addWidget(no_data)

        self._layout.addWidget(card)

    def _build_card_mobilite(self, donnees: dict):
        mobilite = donnees.get('mobilite') or {}
        prime = donnees.get('prime_mobilite') or {}
        vehicule = donnees.get('vehicule') or {}
        card = EmacCard("Mobilité & Primes")

        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 0, 0, 8)
        if mobilite:
            btn_edit = EmacButton("Modifier", variant="outline")
            btn_edit.setVisible(can("rh.mobilite.edit"))
            btn_edit.clicked.connect(lambda: self._edit_mobilite(mobilite, vehicule))
            btn_bar.addWidget(btn_edit)
        else:
            btn_add = EmacButton("+ Déclarer la distance", variant="primary")
            btn_add.setVisible(can("rh.mobilite.edit"))
            btn_add.clicked.connect(lambda: self._add_mobilite(vehicule))
            btn_bar.addWidget(btn_add)
        btn_bar.addStretch()
        card.body.addLayout(btn_bar)

        if mobilite or prime:
            modes = {'voiture': 'Voiture', 'velo': 'Vélo', 'transport_commun': 'Transport en commun',
                     'covoiturage': 'Covoiturage', 'autre': 'Autre'}
            infos = []
            if mobilite.get('distance_km') is not None:
                infos.append(("Distance domicile-entreprise",
                               f"{mobilite['distance_km']} km ({modes.get(mobilite.get('mode_transport', ''), '-')})"))
            if mobilite.get('ville_depart'):
                infos.append(("Ville de départ", mobilite['ville_depart']))
            if prime.get('prime_journaliere') is not None:
                infos.append(("Prime mobilité", f"{prime['prime_journaliere']} €/jour — {prime.get('palier_libelle', '')}"))
            if prime.get('ik_taux_km') is not None:
                infos.append(("Indemnité kilométrique", f"{prime['ik_taux_km']} €/km — {prime.get('ik_libelle', '')}"))

            grid = QGridLayout()
            grid.setSpacing(10)
            for i, (lbl_txt, val) in enumerate(infos):
                lbl = QLabel(f"<b>{lbl_txt}</b><br/>{val}")
                lbl.setStyleSheet("padding: 8px; background: #f0fdf4; border-radius: 6px;")
                lbl.setWordWrap(True)
                grid.addWidget(lbl, i // 2, i % 2)
            card.body.addLayout(grid)
        else:
            no_data = QLabel("Aucune information de mobilité enregistrée.")
            no_data.setStyleSheet("color: #9ca3af; padding: 8px 0;")
            card.body.addWidget(no_data)

        self._layout.addWidget(card)

    def _edit_infos_generales(self):
        if not self._operateur:
            return
        dialog = EditInfosGeneralesDialog(self._operateur['id'], self._donnees, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _add_vehicule(self):
        if not self._operateur:
            return
        dialog = EditVehiculeDialog(self._operateur['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _edit_vehicule(self, vehicule: dict):
        if not self._operateur:
            return
        dialog = EditVehiculeDialog(self._operateur['id'], vehicule, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _delete_vehicule(self, vehicule: dict):
        if not self._operateur:
            return
        rep = QMessageBox.question(
            self, "Supprimer le véhicule",
            "Supprimer ce véhicule ? Cette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if rep != QMessageBox.Yes:
            return
        ok, msg = delete_vehicule(vehicule['id'])
        if ok:
            self.refresh_requested.emit()
        else:
            QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le véhicule : {msg}")

    def _add_mobilite(self, vehicule: dict):
        if not self._operateur:
            return
        dialog = EditMobiliteDialog(
            self._operateur['id'],
            vehicule=vehicule,
            distance_auto=self._donnees.get('distance_domicile_km'),
            duree_auto=self._donnees.get('duree_trajet_min'),
            parent=self,
        )
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _edit_mobilite(self, mobilite: dict, vehicule: dict):
        if not self._operateur:
            return
        dialog = EditMobiliteDialog(self._operateur['id'], mobilite=mobilite, vehicule=vehicule, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()
