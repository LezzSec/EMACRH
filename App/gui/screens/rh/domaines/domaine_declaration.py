# -*- coding: utf-8 -*-
"""
Domaine RH : Déclarations (arrêts, maladie, AT, congés, etc.) + Absences.
"""
from PyQt5.QtWidgets import (
    QDialog, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from gui.components.ui_theme import EmacCard, EmacButton
from gui.components.emac_ui_kit import EmacAlert, EmacChip
from gui.screens.rh.gestion_rh_dialogs import EditDeclarationDialog, ConsulterDetailDialog
from application.permission_manager import can
from .domaine_base import DomaineWidget


_STATUT_COLOR = {
    'EN_ATTENTE': ('#b45309', '#fef3c7'),
    'VALIDEE':    ('#065f46', '#d1fae5'),
    'REFUSEE':    ('#991b1b', '#fee2e2'),
    'ANNULEE':    ('#374151', '#f3f4f6'),
}
_STATUT_LABEL = {
    'EN_ATTENTE': 'En attente',
    'VALIDEE':    'Validée',
    'REFUSEE':    'Refusée',
    'ANNULEE':    'Annulée',
}


class DomaineDeclaration(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        self._build_declarations(donnees, documents)
        self._build_absences(donnees)

    # -------------------------------------------------------------------------
    # Section : Déclarations
    # -------------------------------------------------------------------------

    def _build_declarations(self, donnees: dict, documents: list):
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

    # -------------------------------------------------------------------------
    # Section : Absences
    # -------------------------------------------------------------------------

    def _build_absences(self, donnees: dict):
        absences = donnees.get('absences', [])
        absences_sirh = donnees.get('absences_sirh', [])

        btn_add = EmacButton("+ Nouvelle absence", variant="primary")
        btn_add.setVisible(can("planning.absences.edit"))
        btn_add.clicked.connect(self._add_absence)
        self._layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        # --- Historique SIRH ---
        sirh_card = EmacCard(f"Historique des absences ({len(absences_sirh)} périodes)")
        if absences_sirh:
            sirh_table = self._make_absence_table(
                absences_sirh,
                columns=["Type", "Début", "Fin", "Jours"],
                row_fn=self._sirh_row,
            )
            sirh_card.body.addWidget(sirh_table)
        else:
            sirh_card.body.addWidget(QLabel("Aucune absence enregistrée"))
        self._layout.addWidget(sirh_card)

        # --- Demandes locales ---
        local_card = EmacCard(f"Demandes d'absence ({len(absences)})")
        if absences:
            nb_validees = sum(1 for a in absences if a.get('statut') == 'VALIDEE')
            nb_attente = sum(1 for a in absences if a.get('statut') == 'EN_ATTENTE')
            total_jours = sum(float(a.get('nb_jours') or 0) for a in absences if a.get('statut') == 'VALIDEE')
            stats_widget = QWidget()
            stats_row = QHBoxLayout(stats_widget)
            stats_row.setContentsMargins(0, 0, 0, 0)
            for label, value in [
                ("Total", str(len(absences))),
                ("Validées", str(nb_validees)),
                ("En attente", str(nb_attente)),
                ("Jours validés", f"{total_jours:g}"),
            ]:
                frame = QFrame()
                frame.setStyleSheet("QFrame { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; }")
                frame.setFixedWidth(90)
                fl = QVBoxLayout(frame)
                fl.setContentsMargins(4, 6, 4, 6)
                fl.setSpacing(2)
                v_lbl = QLabel(value)
                v_lbl.setAlignment(Qt.AlignCenter)
                v_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #1e293b; background: transparent;")
                k_lbl = QLabel(label)
                k_lbl.setAlignment(Qt.AlignCenter)
                k_lbl.setStyleSheet("font-size: 11px; color: #64748b; background: transparent;")
                fl.addWidget(v_lbl)
                fl.addWidget(k_lbl)
                stats_row.addWidget(frame)
            stats_row.addStretch()
            local_card.body.addWidget(stats_widget)
            local_table = self._make_absence_table(
                absences,
                columns=["Type", "Début", "Fin", "Jours", "Statut", "Motif"],
                row_fn=self._local_row,
            )
            local_card.body.addWidget(local_table)
        else:
            local_card.body.addWidget(QLabel("Aucune demande enregistrée"))
        self._layout.addWidget(local_card)

    def _make_absence_table(self, rows: list, columns: list, row_fn) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        for i in range(len(columns) - 1):
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(len(columns) - 1, QHeaderView.Stretch)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("QTableWidget { border: 1px solid #e2e8f0; border-radius: 6px; }")
        table.setRowCount(len(rows))
        for row_idx, data in enumerate(rows):
            row_fn(table, row_idx, data)
        row_height = 28
        max_visible = 8
        table.setFixedHeight(row_height * min(len(rows), max_visible) + table.horizontalHeader().height() + 4)
        return table

    def _sirh_row(self, table: QTableWidget, row: int, ab: dict):
        for col, val in enumerate([
            ab.get('type_libelle') or ab.get('motif', '-'),
            self._format_date(ab.get('date_debut')),
            self._format_date(ab.get('date_fin')),
            str(ab.get('nb_jours', '-')),
        ]):
            item = QTableWidgetItem(val)
            item.setForeground(QColor('#374151'))
            table.setItem(row, col, item)

    def _local_row(self, table: QTableWidget, row: int, ab: dict):
        statut = ab.get('statut', '')
        fg, bg = _STATUT_COLOR.get(statut, ('#374151', '#f3f4f6'))
        for col, val in enumerate([
            ab.get('type_libelle', '-'),
            self._format_date(ab.get('date_debut')),
            self._format_date(ab.get('date_fin')),
            (f"{float(ab['nb_jours']):g}" if ab.get('nb_jours') is not None else '-'),
            _STATUT_LABEL.get(statut, statut),
            ab.get('motif') or '-',
        ]):
            item = QTableWidgetItem(val)
            item.setForeground(QColor(fg if col == 4 else '#374151'))
            if col == 4:
                item.setBackground(QColor(bg))
                item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, col, item)

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

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

    def _add_absence(self):
        if not self._operateur:
            return
        from gui.screens.planning.planning_absences import NouvelleDemande
        dialog = NouvelleDemande(self._operateur['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _jours_declaration(self, declaration: dict):
        debut = declaration.get('date_debut')
        fin = declaration.get('date_fin')
        if not debut or not fin:
            return None
        try:
            return (fin - debut).days + 1
        except Exception:
            return None
