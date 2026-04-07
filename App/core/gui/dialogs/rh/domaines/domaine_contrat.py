# -*- coding: utf-8 -*-
"""
Domaine RH : Contrat de travail.
"""
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QGridLayout, QFrame
from PyQt5.QtGui import QFont

from core.gui.components.ui_theme import EmacCard, EmacButton
from core.gui.components.emac_ui_kit import EmacAlert
from core.gui.dialogs.gestion_rh_dialogs import (
    EditContratDialog, AjouterDocumentDialog, ConsulterDetailDialog,
)
from application.permission_manager import can
from .domaine_base import DomaineWidget


class DomaineContrat(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        self._donnees = donnees

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        btn_add = EmacButton("+ Nouveau contrat", variant="primary")
        btn_add.setVisible(can("rh.contrats.edit"))
        btn_add.clicked.connect(self._add_contrat)
        actions_layout.addWidget(btn_add)
        self._layout.addLayout(actions_layout)

        contrat = donnees.get('contrat_actif')

        if contrat:
            jours = contrat.get('jours_restants')
            if jours is not None and jours <= 30:
                if jours < 0:
                    alert = EmacAlert(f"Contrat expiré depuis {abs(jours)} jour(s) !", variant="error")
                elif jours == 0:
                    alert = EmacAlert("Contrat expire aujourd'hui !", variant="error")
                else:
                    alert = EmacAlert(f"Contrat expire dans {jours} jour(s)", variant="warning")
                self._layout.addWidget(alert)

            card = EmacCard("Contrat Actif")

            header = QHBoxLayout()
            header.addStretch()
            btn_consult = EmacButton("Consulter", variant="ghost")
            btn_consult.clicked.connect(lambda checked, c=contrat: ConsulterDetailDialog(
                "Détail du contrat", [
                    ("Type", c.get('type_contrat')),
                    ("Date début", self._format_date(c.get('date_debut'))),
                    ("Date fin", self._format_date(c.get('date_fin')) or "Indéterminée"),
                    ("Jours restants", c.get('jours_restants')),
                    ("ETP", c.get('etp', 1.0)),
                    ("Catégorie", c.get('categorie')),
                    ("Emploi", c.get('emploi')),
                    ("Commentaire", c.get('commentaire')),
                ], self))
            header.addWidget(btn_consult)
            btn_edit = EmacButton("Modifier", variant="ghost")
            btn_edit.setVisible(can("rh.contrats.edit"))
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

            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("background: #e5e7eb; margin: 8px 0;")
            card.body.addWidget(sep)

            docs_actifs = [d for d in documents if d.get('statut') != 'archive']
            doc_header_layout = QHBoxLayout()
            doc_title_lbl = QLabel(f"Documents ({len(docs_actifs)})")
            doc_title_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
            doc_title_lbl.setStyleSheet("color: #374151; background: transparent;")
            doc_header_layout.addWidget(doc_title_lbl)
            doc_header_layout.addStretch()
            btn_ajouter_doc = EmacButton("+ Ajouter un document", variant="secondary")
            btn_ajouter_doc.setVisible(can("rh.documents.edit"))
            btn_ajouter_doc.clicked.connect(self._ajouter_document)
            doc_header_layout.addWidget(btn_ajouter_doc)
            card.body.addLayout(doc_header_layout)

            if not docs_actifs:
                no_doc_lbl = QLabel("Aucun document joint")
                no_doc_lbl.setStyleSheet("color: #9ca3af; padding: 4px 0; background: transparent;")
                card.body.addWidget(no_doc_lbl)
            else:
                for doc in docs_actifs:
                    doc_lbl = QLabel(
                        f"<b>{doc.get('nom_affichage', '-')}</b>"
                        f"<span style='color:#6b7280; font-size:11px;'>"
                        f"  •  Ajouté le {self._format_date(doc.get('date_upload'))}</span>"
                    )
                    doc_lbl.setStyleSheet("padding: 3px 0; background: transparent;")
                    card.body.addWidget(doc_lbl)

            self._layout.addWidget(card)
        else:
            alert = EmacAlert("Aucun contrat actif", variant="info")
            self._layout.addWidget(alert)

    def _add_contrat(self):
        if not self._operateur:
            return
        dialog = EditContratDialog(self._operateur['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _edit_contrat(self, contrat: dict):
        if not self._operateur:
            return
        dialog = EditContratDialog(self._operateur['id'], contrat, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _ajouter_document(self):
        if not self._operateur:
            return
        from core.gui.view_models.gestion_rh_view_model import DomaineRH
        dialog = AjouterDocumentDialog(
            operateur_id=self._operateur['id'],
            domaine=DomaineRH.CONTRAT,
            parent=self,
        )
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()
