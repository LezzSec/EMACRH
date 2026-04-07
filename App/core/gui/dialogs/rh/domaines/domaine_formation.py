# -*- coding: utf-8 -*-
"""
Domaine RH : Formations.
"""
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QFrame, QMessageBox
from PyQt5.QtCore import Qt

from core.gui.components.ui_theme import EmacCard, EmacButton
from core.gui.dialogs.gestion_rh_dialogs import EditFormationDialog, ConsulterFormationDialog
from core.services.permission_manager import can
from .domaine_base import DomaineWidget


class DomaineFormation(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        btn_add = EmacButton("+ Nouvelle formation", variant="primary")
        btn_add.setVisible(can("rh.formations.edit"))
        btn_add.clicked.connect(self._add_formation)
        self._layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})
        card_stats = EmacCard("Statistiques Formations")
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
                row = QHBoxLayout(frame)
                row.setContentsMargins(12, 10, 12, 10)
                row.setSpacing(8)
                info_text = f"{form.get('intitule', 'N/A')} - {form.get('statut', 'N/A')}"
                if form.get('date_debut'):
                    info_text += f" ({self._format_date(form.get('date_debut'))})"
                lbl = QLabel(info_text)
                lbl.setStyleSheet("background: transparent;")
                row.addWidget(lbl)
                row.addStretch()
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
                card_list.body.addWidget(frame)
        else:
            card_list.body.addWidget(QLabel("Aucune formation enregistrée"))
        self._layout.addWidget(card_list)

    def _add_formation(self):
        if not self._operateur:
            return
        dialog = EditFormationDialog(self._operateur['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            if getattr(dialog, '_justificatif_manquant', False):
                QMessageBox.information(
                    self, "Rappel — Document justificatif",
                    "La formation a été enregistrée.\n\n"
                    "N'oubliez pas d'ajouter le document justificatif "
                    "(attestation, certificat…) dès qu'il sera disponible, "
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
