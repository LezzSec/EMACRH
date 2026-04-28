# -*- coding: utf-8 -*-
"""
Domaine RH : Formations.
"""
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QMessageBox
from PyQt5.QtCore import Qt

from gui.components.ui_theme import EmacCard, EmacButton
from gui.screens.rh.gestion_rh_dialogs import EditFormationDialog, ConsulterFormationDialog
from application.permission_manager import can
from .domaine_base import DomaineWidget


class DomaineFormation(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        btn_add = EmacButton("+ Nouvelle formation", variant="primary")
        btn_add.setVisible(can("rh.formations.edit"))
        btn_add.clicked.connect(self._add_formation)
        self._layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})
        card_stats = EmacCard("Statistiques formations")
        stats_layout = QHBoxLayout()
        for label, key in [
            ("Total", 'total'), ("Terminées", 'terminees'), ("En cours", 'en_cours'),
            ("Planifiées", 'planifiees'), ("Avec certificat", 'avec_certificat'),
        ]:
            badge = QLabel(f"{label}: {stats.get(key, 0)}")
            badge.setStyleSheet("background: #f1f5f9; color: #475569; padding: 8px 16px; border-radius: 6px; font-size: 13px;")
            stats_layout.addWidget(badge)
        stats_layout.addStretch()
        card_stats.body.addLayout(stats_layout)
        self._layout.addWidget(card_stats)

        formations = donnees.get('formations', [])
        card_list = EmacCard(f"Formations ({len(formations)})")
        if formations:
            for form in formations:
                frame = QFrame()
                frame.setStyleSheet("QFrame { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; }")
                wrapper = QVBoxLayout(frame)
                wrapper.setContentsMargins(12, 10, 12, 10)
                wrapper.setSpacing(8)

                row = QHBoxLayout()
                row.setSpacing(8)
                info = QVBoxLayout()
                info.setSpacing(3)

                title = QLabel(f"<b>{form.get('intitule', 'N/A')}</b>")
                title.setStyleSheet("background: transparent;")
                info.addWidget(title)

                meta = []
                if form.get('type_formation'):
                    meta.append(form['type_formation'])
                if form.get('statut'):
                    meta.append(form['statut'])
                if form.get('organisme'):
                    meta.append(form['organisme'])
                subtitle = QLabel(" - ".join(meta) or "-")
                subtitle.setStyleSheet("color: #64748b; font-size: 12px; background: transparent;")
                info.addWidget(subtitle)

                dates = f"{self._format_date(form.get('date_debut'))} au {self._format_date(form.get('date_fin'))}"
                extras = []
                if form.get('duree_heures'):
                    extras.append(f"{form['duree_heures']} h")
                if form.get('certificat_obtenu'):
                    extras.append("certificat obtenu")
                if form.get('cout'):
                    extras.append(self._format_money(form.get('cout')))
                detail = QLabel(f"{dates}{' - ' + ' - '.join(extras) if extras else ''}")
                detail.setStyleSheet("color: #475569; font-size: 12px; background: transparent;")
                info.addWidget(detail)

                if form.get('objectif'):
                    objectif = form['objectif']
                    if len(objectif) > 130:
                        objectif = objectif[:130] + "..."
                    objectif_lbl = QLabel(objectif)
                    objectif_lbl.setWordWrap(True)
                    objectif_lbl.setStyleSheet("color: #475569; font-size: 12px; background: transparent;")
                    info.addWidget(objectif_lbl)

                row.addLayout(info, 1)

                btn_consult = EmacButton("Consulter", variant="ghost")
                btn_consult.clicked.connect(lambda checked, f=form: ConsulterFormationDialog(f, self))
                row.addWidget(btn_consult)
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.formations.edit"))
                btn_edit.clicked.connect(lambda checked, f=form: self._edit_formation(f))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="danger")
                btn_delete.setVisible(can("rh.formations.delete"))
                btn_delete.clicked.connect(lambda checked, f=form: self._delete_formation(f))
                row.addWidget(btn_delete)
                wrapper.addLayout(row)

                docs_form = self._documents_for_entity(documents, 'formation_id', form.get('id'))
                if docs_form:
                    docs_label = QLabel(f"Document(s) associé(s) : {len(docs_form)}")
                    docs_label.setStyleSheet("color: #475569; font-size: 11px; font-weight: 600;")
                    wrapper.addWidget(docs_label)
                    for doc in docs_form:
                        wrapper.addWidget(self._build_document_row(doc))

                card_list.body.addWidget(frame)
        else:
            card_list.body.addWidget(QLabel("Aucune formation enregistrée"))
        self._layout.addWidget(card_list)

    def _format_money(self, value) -> str:
        if value in (None, ''):
            return '-'
        try:
            return f"{float(value):,.2f} €".replace(",", " ").replace(".", ",")
        except (TypeError, ValueError):
            return str(value)

    def _add_formation(self):
        if not self._operateur:
            return
        dialog = EditFormationDialog(self._operateur['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            if getattr(dialog, '_justificatif_manquant', False):
                QMessageBox.information(
                    self, "Rappel - Document justificatif",
                    "La formation a été enregistrée.\n\n"
                    "N'oubliez pas d'ajouter le document justificatif "
                    "(attestation, certificat...) dès qu'il sera disponible, "
                    "via l'onglet Documents du profil salarié."
                )
            if getattr(dialog, '_saved_id', None):
                self._proposer_generation_documents(dialog._saved_id)
            self.refresh_requested.emit()

    def _edit_formation(self, formation: dict):
        if not self._operateur:
            return
        dialog = EditFormationDialog(self._operateur['id'], formation, self)
        if dialog.exec_() == QDialog.Accepted:
            if getattr(dialog, '_saved_id', None):
                self._proposer_generation_documents(dialog._saved_id)
            self.refresh_requested.emit()

    def _delete_formation(self, formation: dict):
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette formation ?\n{formation.get('intitule', 'N/A')}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._vm.supprimer_formation(formation['id'])

    def _proposer_generation_documents(self, formation_id: int):
        reply = QMessageBox.question(
            self, "Générer les documents",
            "Voulez-vous générer les documents de formation pré-remplis ?\n"
            "(Demande, Feuille d'émargement, Fiche de suivi)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self._vm.generer_dossier_formation(formation_id)
