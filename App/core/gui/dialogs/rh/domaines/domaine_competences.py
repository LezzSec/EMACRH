# -*- coding: utf-8 -*-
"""
Domaine RH : Compétences transversales.
"""
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QMessageBox
from PyQt5.QtCore import Qt

from core.gui.components.ui_theme import EmacCard, EmacButton
from core.gui.components.emac_ui_kit import EmacAlert
from core.gui.dialogs.gestion_rh_dialogs import EditCompetenceDialog, ConsulterDetailDialog
from application.permission_manager import can
from .domaine_base import DomaineWidget


class DomaineCompetences(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        btn_add = EmacButton("+ Nouvelle compétence", variant="primary")
        btn_add.setVisible(can("rh.competences.edit"))
        btn_add.clicked.connect(self._add_competence)
        self._layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})

        if stats.get('expirees', 0) > 0:
            self._layout.addWidget(EmacAlert(f"{stats['expirees']} compétence(s) expirée(s) !", variant="error"))

        if stats.get('expire_bientot_30j', 0) > 0:
            self._layout.addWidget(EmacAlert(
                f"{stats['expire_bientot_30j']} compétence(s) expirant dans les 30 jours", variant="warning"
            ))

        card_stats = EmacCard("Statistiques")
        stats_layout = QHBoxLayout()
        for label, key in [("Valides", 'valides'), ("Expirées", 'expirees'), ("Total", 'total')]:
            badge = QLabel(f"{label}: {stats.get(key, 0)}")
            badge.setStyleSheet("background: #f1f5f9; color: #475569; padding: 8px 16px; border-radius: 6px; font-size: 13px;")
            stats_layout.addWidget(badge)
        stats_layout.addStretch()
        card_stats.body.addLayout(stats_layout)
        self._layout.addWidget(card_stats)

        competences = donnees.get('competences', [])
        card_list = EmacCard(f"Compétences ({len(competences)})")

        if competences:
            for comp in competences:
                frame = QFrame()
                frame.setStyleSheet("QFrame { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; }")
                row = QHBoxLayout(frame)
                row.setContentsMargins(12, 10, 12, 10)
                row.setSpacing(8)

                statut = comp.get('statut', 'valide')
                if statut == 'expiree':
                    indicator, color = "X", "#ef4444"
                elif statut == 'expire_bientot':
                    indicator, color = "!", "#f97316"
                elif statut == 'attention':
                    indicator, color = "~", "#eab308"
                else:
                    indicator, color = "O", "#22c55e"

                status_label = QLabel(indicator)
                status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px; background: transparent;")
                status_label.setFixedWidth(20)
                row.addWidget(status_label)

                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                libelle = comp.get('libelle', 'N/A')
                if comp.get('categorie'):
                    libelle = f"{libelle} [{comp['categorie']}]"
                label_nom = QLabel(libelle)
                label_nom.setStyleSheet("font-weight: 500; background: transparent;")
                info_layout.addWidget(label_nom)

                date_text = f"Acquis le: {self._format_date(comp.get('date_acquisition'))}"
                if comp.get('date_expiration'):
                    date_text += f" - Expire le: {self._format_date(comp['date_expiration'])}"
                else:
                    date_text += " - Permanent"
                label_dates = QLabel(date_text)
                label_dates.setStyleSheet("color: #64748b; font-size: 12px;")
                info_layout.addWidget(label_dates)

                if statut in ('expire_bientot', 'attention', 'expiree') and comp.get('statut_label'):
                    label_statut = QLabel(comp['statut_label'])
                    label_statut.setStyleSheet(f"color: {color}; font-size: 11px; font-style: italic;")
                    info_layout.addWidget(label_statut)

                row.addLayout(info_layout)
                row.addStretch()

                btn_consult = EmacButton("Consulter", variant="ghost")
                btn_consult.clicked.connect(lambda checked, c=comp: ConsulterDetailDialog(
                    "Détail de la compétence", [
                        ("Libellé", c.get('libelle')),
                        ("Catégorie", c.get('categorie')),
                        ("Date d'acquisition", self._format_date(c.get('date_acquisition'))),
                        ("Date d'expiration", self._format_date(c.get('date_expiration')) or "Permanente"),
                        ("Statut", c.get('statut_label') or c.get('statut')),
                        ("Commentaire", c.get('commentaire')),
                    ], self))
                row.addWidget(btn_consult)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.competences.edit"))
                btn_edit.clicked.connect(lambda checked, c=comp: self._edit_competence(c))
                row.addWidget(btn_edit)

                btn_delete = EmacButton("Retirer", variant="danger")
                btn_delete.setVisible(can("rh.competences.delete"))
                btn_delete.clicked.connect(lambda checked, c=comp: self._delete_competence(c))
                row.addWidget(btn_delete)

                card_list.body.addWidget(frame)
        else:
            card_list.body.addWidget(QLabel("Aucune compétence assignée"))

        self._layout.addWidget(card_list)

    def _add_competence(self):
        if not self._operateur:
            return
        dialog = EditCompetenceDialog(self._operateur['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _edit_competence(self, competence: dict):
        dialog = EditCompetenceDialog(self._operateur['id'], competence, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _delete_competence(self, competence: dict):
        libelle = competence.get('libelle', 'cette compétence')
        reply = QMessageBox.question(
            self, "Confirmer le retrait",
            f"Voulez-vous vraiment retirer la compétence '{libelle}' ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._vm.supprimer_competence(competence['assignment_id'])
