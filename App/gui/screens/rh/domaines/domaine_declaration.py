# -*- coding: utf-8 -*-
"""
Domaine RH : Déclarations (arrêts, maladie, AT, congés, etc.).
"""
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QMessageBox
from PyQt5.QtCore import Qt

from gui.components.ui_theme import EmacCard, EmacButton
from gui.components.emac_ui_kit import EmacAlert, EmacChip
from gui.screens.rh.gestion_rh_dialogs import EditDeclarationDialog, ConsulterDetailDialog
from application.permission_manager import can
from .domaine_base import DomaineWidget


class DomaineDeclaration(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        btn_add = EmacButton("+ Nouvelle déclaration", variant="primary")
        btn_add.setVisible(can("rh.declarations.edit"))
        btn_add.clicked.connect(self._add_declaration)
        self._layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        en_cours = donnees.get('en_cours')
        if en_cours:
            alert = EmacAlert(
                f"Déclaration en cours : {en_cours.get('type_declaration')} "
                f"du {self._format_date(en_cours.get('date_debut'))} "
                f"au {self._format_date(en_cours.get('date_fin'))}",
                variant="info"
            )
            self._layout.addWidget(alert)

        stats = donnees.get('statistiques', {})
        if stats:
            card = EmacCard("Statistiques des déclarations")
            stats_layout = QHBoxLayout()
            for type_decl, data in stats.items():
                count = data if isinstance(data, int) else data.get('nombre', 0)
                chip = EmacChip(f"{type_decl}: {count}", variant="info")
                stats_layout.addWidget(chip)
            stats_layout.addStretch()
            card.body.addLayout(stats_layout)
            self._layout.addWidget(card)

        declarations = donnees.get('declarations', [])
        card = EmacCard(f"Déclarations ({len(declarations)})")
        if declarations:
            for decl in declarations:
                frame = QFrame()
                frame.setStyleSheet("QFrame { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; }")
                wrapper = QVBoxLayout(frame)
                wrapper.setContentsMargins(12, 10, 12, 10)
                wrapper.setSpacing(8)

                row = QHBoxLayout()
                row.setSpacing(8)
                info = QVBoxLayout()
                info.setSpacing(3)

                title = QLabel(f"<b>{decl.get('type_declaration', 'N/A')}</b>")
                title.setStyleSheet("background: transparent;")
                info.addWidget(title)

                jours = self._jours_declaration(decl)
                subtitle = QLabel(
                    f"{self._format_date(decl.get('date_debut'))} au "
                    f"{self._format_date(decl.get('date_fin'))}"
                    f"{f' - {jours} jour(s)' if jours else ''}"
                )
                subtitle.setStyleSheet("color: #64748b; font-size: 12px; background: transparent;")
                info.addWidget(subtitle)

                if decl.get('motif'):
                    motif = decl['motif']
                    if len(motif) > 120:
                        motif = motif[:120] + "..."
                    motif_lbl = QLabel(motif)
                    motif_lbl.setStyleSheet("color: #475569; font-size: 12px; background: transparent;")
                    motif_lbl.setWordWrap(True)
                    info.addWidget(motif_lbl)

                row.addLayout(info, 1)

                btn_consult = EmacButton("Consulter", variant="ghost")
                btn_consult.clicked.connect(lambda checked, d=decl: ConsulterDetailDialog(
                    "Détail de la déclaration", [
                        ("Type", d.get('type_declaration')),
                        ("Date début", self._format_date(d.get('date_debut'))),
                        ("Date fin", self._format_date(d.get('date_fin'))),
                        ("Durée", f"{self._jours_declaration(d)} jour(s)" if self._jours_declaration(d) else "-"),
                        ("Motif", d.get('motif')),
                    ], self))
                row.addWidget(btn_consult)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.declarations.edit"))
                btn_edit.clicked.connect(lambda checked, d=decl: self._edit_declaration(d))
                row.addWidget(btn_edit)

                btn_delete = EmacButton("Supprimer", variant="danger")
                btn_delete.setVisible(can("rh.declarations.edit"))
                btn_delete.clicked.connect(lambda checked, d=decl: self._delete_declaration(d))
                row.addWidget(btn_delete)
                wrapper.addLayout(row)

                docs_decl = self._documents_for_entity(documents, 'declaration_id', decl.get('id'))
                if docs_decl:
                    docs_label = QLabel(f"Document(s) associé(s) : {len(docs_decl)}")
                    docs_label.setStyleSheet("color: #475569; font-size: 11px; font-weight: 600;")
                    wrapper.addWidget(docs_label)
                    for doc in docs_decl:
                        wrapper.addWidget(self._build_document_row(doc))

                card.body.addWidget(frame)
        else:
            card.body.addWidget(QLabel("Aucune déclaration"))
        self._layout.addWidget(card)

    def _add_declaration(self):
        if not self._operateur:
            return
        dialog = EditDeclarationDialog(self._operateur['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _edit_declaration(self, declaration: dict):
        if not self._operateur:
            return
        dialog = EditDeclarationDialog(self._operateur['id'], declaration, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _delete_declaration(self, declaration: dict):
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette déclaration ?\n"
            f"{declaration.get('type_declaration')} du {self._format_date(declaration.get('date_debut'))}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._vm.supprimer_declaration(declaration['id'])

    def _jours_declaration(self, declaration: dict):
        debut = declaration.get('date_debut')
        fin = declaration.get('date_fin')
        if not debut or not fin:
            return None
        try:
            return (fin - debut).days + 1
        except Exception:
            return None
