# -*- coding: utf-8 -*-
"""
Domaine RH : Contrat de travail.
"""
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QGridLayout, QFrame
from PyQt5.QtGui import QFont

from gui.components.ui_theme import EmacCard, EmacButton
from gui.components.emac_ui_kit import EmacAlert
from gui.screens.rh.gestion_rh_dialogs import (
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

            card = EmacCard("Contrat actif")

            header = QHBoxLayout()
            header.addStretch()
            btn_consult = EmacButton("Consulter", variant="ghost")
            btn_consult.clicked.connect(
                lambda checked, c=contrat: ConsulterDetailDialog(
                    "Détail du contrat",
                    self._detail_fields(c),
                    self,
                )
            )
            header.addWidget(btn_consult)

            btn_edit = EmacButton("Modifier", variant="ghost")
            btn_edit.setVisible(can("rh.contrats.edit"))
            btn_edit.clicked.connect(lambda: self._edit_contrat(contrat))
            header.addWidget(btn_edit)
            card.body.addLayout(header)

            infos = self._summary_fields(contrat, jours)
            grid = QGridLayout()
            grid.setSpacing(12)
            for i, (label, valeur) in enumerate(infos):
                row, col = divmod(i, 2)
                lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
                lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
                lbl.setWordWrap(True)
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
                    card.body.addWidget(self._build_doc_row(doc))

            self._layout.addWidget(card)
        else:
            alert = EmacAlert("Aucun contrat actif", variant="info")
            self._layout.addWidget(alert)

    def _detail_fields(self, c: dict) -> list:
        return [
            ("Type", c.get('type_contrat')),
            ("Date début", self._format_date(c.get('date_debut'))),
            ("Date fin", self._format_date(c.get('date_fin')) or "Indéterminée"),
            ("Jours restants", c.get('jours_restants')),
            ("ETP", c.get('etp', 1.0)),
            ("Catégorie", c.get('categorie')),
            ("Échelon", c.get('echelon')),
            ("Emploi", c.get('emploi')),
            ("Salaire brut", self._format_money(c.get('salaire'))),
            ("Tuteur / école", self._format_tuteur(c)),
            ("Organisme", self._format_organisme(c)),
            ("Autorisation travail", c.get('numero_autorisation_travail')),
            ("Limite autorisation", self._format_date(c.get('date_limite_autorisation'))),
            ("Commentaire", c.get('commentaire')),
        ]

    def _summary_fields(self, contrat: dict, jours) -> list:
        infos = [
            ("Type", contrat.get('type_contrat', '-')),
            ("Date début", self._format_date(contrat.get('date_debut'))),
            ("Date fin", self._format_date(contrat.get('date_fin')) or "Indéterminée"),
            ("Jours restants", str(jours) if jours is not None else "N/A"),
            ("ETP", str(contrat.get('etp', 1.0))),
            ("Catégorie", contrat.get('categorie', '-') or '-'),
            ("Échelon", contrat.get('echelon') or '-'),
            ("Emploi", contrat.get('emploi') or '-'),
            ("Salaire brut", self._format_money(contrat.get('salaire'))),
        ]

        type_contrat = contrat.get('type_contrat')
        if type_contrat in ('Apprentissage', 'Stagiaire', 'CIFRE'):
            infos.append(("Tuteur / école", self._format_tuteur(contrat)))
        if type_contrat == 'Intérimaire':
            infos.append(("ETT", contrat.get('nom_ett') or '-'))
        if type_contrat == 'Mise à disposition GE':
            infos.append(("Groupement employeur", contrat.get('nom_ge') or '-'))
        if type_contrat == 'Etranger hors UE':
            infos.append(("Autorisation travail", contrat.get('numero_autorisation_travail') or '-'))
            if contrat.get('date_limite_autorisation'):
                infos.append(("Limite autorisation", self._format_date(contrat.get('date_limite_autorisation'))))

        return infos

    def _build_doc_row(self, doc: dict) -> QFrame:
        """Construit une ligne de document avec bouton Ouvrir."""
        row_widget = QFrame()
        row_widget.setStyleSheet("""
            QFrame {
                background: #f9fafb; border: 1px solid #e5e7eb;
                border-radius: 6px; padding: 6px; margin: 2px 0;
            }
            QFrame:hover { background: #f3f4f6; border-color: #3b82f6; }
        """)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(8)

        details = f"Ajouté le {self._format_date(doc.get('date_upload'))}"
        if doc.get('date_expiration'):
            details += f" - expire le {self._format_date(doc.get('date_expiration'))}"
        info = QLabel(
            f"<b>{doc.get('nom_affichage', '-')}</b>"
            f"<span style='color:#6b7280; font-size:11px;'>  -  {details}</span>"
        )
        info.setStyleSheet("background: transparent;")
        info.setWordWrap(True)
        row_layout.addWidget(info, 1)

        doc_id = doc.get('id')
        btn_ouvrir = EmacButton("Ouvrir", variant="ghost")
        btn_ouvrir.clicked.connect(lambda checked, d=doc_id: self._vm.ouvrir_document(d))
        row_layout.addWidget(btn_ouvrir)

        return row_widget

    def _format_money(self, value) -> str:
        if value in (None, ''):
            return '-'
        try:
            return f"{float(value):,.2f} €".replace(",", " ").replace(".", ",")
        except (TypeError, ValueError):
            return str(value)

    def _format_tuteur(self, contrat: dict) -> str:
        parts = [contrat.get('prenom_tuteur'), contrat.get('nom_tuteur')]
        nom = " ".join([p for p in parts if p])
        ecole = contrat.get('ecole')
        if nom and ecole:
            return f"{nom} ({ecole})"
        return nom or ecole or '-'

    def _format_organisme(self, contrat: dict) -> str:
        type_contrat = contrat.get('type_contrat')
        if type_contrat == 'Intérimaire':
            return contrat.get('nom_ett') or '-'
        if type_contrat == 'Mise à disposition GE':
            return contrat.get('nom_ge') or '-'
        return '-'

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
        from gui.view_models.gestion_rh_view_model import DomaineRH
        dialog = AjouterDocumentDialog(
            operateur_id=self._operateur['id'],
            domaine=DomaineRH.CONTRAT,
            parent=self,
        )
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()
