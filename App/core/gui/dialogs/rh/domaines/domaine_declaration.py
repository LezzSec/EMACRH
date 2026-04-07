# -*- coding: utf-8 -*-
"""
Domaine RH : Déclarations (AT, maladie, etc.).
"""
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QFrame, QMessageBox
from PyQt5.QtCore import Qt

from core.gui.components.ui_theme import EmacCard, EmacButton
from core.gui.components.emac_ui_kit import EmacAlert, EmacChip
from core.gui.dialogs.gestion_rh_dialogs import EditDeclarationDialog, ConsulterDetailDialog
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
                f"Déclaration en cours: {en_cours.get('type_declaration')} "
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
                row = QHBoxLayout(frame)
                row.setContentsMargins(12, 10, 12, 10)
                row.setSpacing(8)
                info_text = (
                    f"{decl.get('type_declaration', 'N/A')} - "
                    f"{self._format_date(decl.get('date_debut'))} au {self._format_date(decl.get('date_fin'))}"
                )
                lbl = QLabel(info_text)
                lbl.setStyleSheet("background: transparent;")
                row.addWidget(lbl)
                row.addStretch()
                btn_consult = EmacButton("Consulter", variant="ghost")
                btn_consult.clicked.connect(lambda checked, d=decl: ConsulterDetailDialog(
                    "Détail de la déclaration", [
                        ("Type", d.get('type_declaration')),
                        ("Date début", self._format_date(d.get('date_debut'))),
                        ("Date fin", self._format_date(d.get('date_fin'))),
                        ("Commentaire", d.get('commentaire')),
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
