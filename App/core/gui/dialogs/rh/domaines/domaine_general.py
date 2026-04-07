# -*- coding: utf-8 -*-
"""
Domaine RH : Informations générales.
"""
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QGridLayout

from core.gui.components.ui_theme import EmacCard, EmacButton
from core.services.permission_manager import can
from core.gui.dialogs.gestion_rh_dialogs import EditInfosGeneralesDialog
from .domaine_base import DomaineWidget


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

        cat_map = {'O': 'O - Ouvrier', 'E': 'E - Employé', 'L': 'L - Leader', 'C': 'C - Cadre'}
        categorie_display = cat_map.get(donnees.get('categorie', ''), val('categorie'))

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

        for i, (label, valeur) in enumerate(infos):
            row, col = divmod(i, 3)
            lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
            lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
            grid.addWidget(lbl, row, col)

        card.body.addLayout(grid)
        self._layout.addWidget(card)

    def _edit_infos_generales(self):
        if not self._operateur:
            return
        dialog = EditInfosGeneralesDialog(self._operateur['id'], self._donnees, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()
