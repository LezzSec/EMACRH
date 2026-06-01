# -*- coding: utf-8 -*-
"""
Domaine RH : Formations.
"""
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QMessageBox, QPushButton
from PyQt5.QtCore import Qt

from gui.components.ui_theme import EmacCard, EmacButton
from gui.screens.rh.gestion_rh_dialogs import EditFormationDialog, ConsulterFormationDialog
from application.permission_manager import can
from .domaine_base import DomaineWidget, get_niveau_display_maps


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

        # --- Carte synthèse polyvalences ---
        polyvalences = donnees.get('polyvalences', [])
        self._build_polyvalence_card(polyvalences)

    def _build_polyvalence_card(self, polyvalences: list):
        NIVEAU_LABELS, NIVEAU_COLORS = get_niveau_display_maps()

        card = EmacCard("Polyvalences et documents d'évaluation")

        if not polyvalences:
            card.body.addWidget(QLabel("Aucune polyvalence enregistrée."))
            self._layout.addWidget(card)
            return

        ateliers = {}
        for poly in polyvalences:
            atelier = poly.get('atelier_nom') or 'Sans atelier'
            ateliers.setdefault(atelier, []).append(poly)

        for atelier_nom, postes in ateliers.items():
            grp_label = QLabel(f"<b>{atelier_nom}</b>")
            grp_label.setStyleSheet("color: #374151; font-size: 12px; margin-top: 6px;")
            card.body.addWidget(grp_label)

            for poly in postes:
                row = QHBoxLayout()
                row.setSpacing(8)

                badge_poste = QLabel(f"<b>{poly.get('poste_code', '?')}</b>")
                badge_poste.setStyleSheet("font-size: 13px; min-width: 55px;")
                row.addWidget(badge_poste)

                niveau = poly.get('niveau')
                niveau_label = NIVEAU_LABELS.get(niveau, f"N{niveau}") if niveau else "Niveau non défini"
                color = NIVEAU_COLORS.get(niveau, "#6b7280")
                badge_niv = QLabel(niveau_label)
                badge_niv.setStyleSheet(
                    f"background: {color}20; color: {color}; border: 1px solid {color}60;"
                    " border-radius: 4px; padding: 2px 8px; font-size: 11px;"
                )
                row.addWidget(badge_niv)

                if poly.get('date_evaluation'):
                    lbl_date = QLabel(f"Éval : {self._format_date(poly['date_evaluation'])}")
                    lbl_date.setStyleSheet("color: #6b7280; font-size: 11px;")
                    row.addWidget(lbl_date)

                row.addStretch()

                eval_doc_id = poly.get('eval_doc_id')
                eval_doc_nom = poly.get('eval_doc_nom')
                if eval_doc_id and eval_doc_nom:
                    lbl_doc = QLabel(f"  {eval_doc_nom}")
                    lbl_doc.setStyleSheet("color: #15803d; font-size: 11px;")
                    lbl_doc.setToolTip(eval_doc_nom)
                    row.addWidget(lbl_doc)
                    btn_voir = QPushButton("Voir doc")
                    btn_voir.setFixedHeight(26)
                    btn_voir.setStyleSheet(
                        "QPushButton { background: #3b82f6; color: white; border: none;"
                        " border-radius: 4px; padding: 2px 10px; font-size: 11px; }"
                        "QPushButton:hover { background: #2563eb; }"
                    )
                    btn_voir.clicked.connect(
                        lambda checked, did=eval_doc_id: self._vm.ouvrir_doc_eval_polyvalence(did)
                    )
                    row.addWidget(btn_voir)
                else:
                    lbl_no = QLabel("Aucun doc d'éval.")
                    lbl_no.setStyleSheet("color: #9ca3af; font-size: 11px; font-style: italic;")
                    row.addWidget(lbl_no)

                card.body.addLayout(row)

            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("background: #e2e8f0; margin: 2px 0;")
            card.body.addWidget(sep)

        self._layout.addWidget(card)

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
