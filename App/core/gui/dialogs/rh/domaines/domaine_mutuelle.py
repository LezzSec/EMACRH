# -*- coding: utf-8 -*-
"""
Domaine RH : Mutuelle / complémentaire santé.
"""
from PyQt5.QtWidgets import (
    QDialog, QLabel, QHBoxLayout, QGridLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)

from core.gui.components.ui_theme import EmacCard, EmacButton
from core.gui.dialogs.gestion_rh_dialogs import EditMutuelleDialog, ConsulterDetailDialog
from core.services.permission_manager import can
from .domaine_base import DomaineWidget

_STATUT_LABELS = {'ADHERENT': 'Adhérent', 'DISPENSE': 'Dispensé', 'NON_COUVERT': 'Non couvert'}
_STATUT_COLORS = {'ADHERENT': '#16a34a', 'DISPENSE': '#d97706', 'NON_COUVERT': '#6b7280'}
_REGIME_LABELS = {'INDIVIDUEL': 'Individuel', 'FAMILLE': 'Famille', 'ISOLE_ENFANT': 'Isolé + enfant(s)'}


class DomaineMutuelle(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        if donnees.get('error'):
            error_card = EmacCard("Erreur")
            error_card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            self._layout.addWidget(error_card)
            return

        mutuelle = donnees.get('mutuelle') or {}
        historique = donnees.get('historique') or []
        self._donnees = donnees

        card = EmacCard("Mutuelle / Complémentaire santé")

        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 0, 0, 8)
        if mutuelle:
            btn_consult = EmacButton("Consulter", variant="ghost")
            btn_consult.clicked.connect(lambda checked=False, m=mutuelle: ConsulterDetailDialog(
                "Détail de la mutuelle", [
                    ("Statut", m.get('statut_adhesion')),
                    ("Motif de dispense", m.get('type_dispense')),
                    ("Organisme", m.get('organisme')),
                    ("N° adhérent", m.get('numero_adherent')),
                    ("Régime", m.get('regime')),
                    ("Date d'adhésion", self._format_date(m.get('date_adhesion'))),
                    ("Date de fin", self._format_date(m.get('date_fin'))),
                    ("Commentaire", m.get('commentaire')),
                ], self))
            btn_bar.addWidget(btn_consult)
            btn_edit = EmacButton("Modifier", variant="outline")
            btn_edit.setVisible(can("rh.mutuelle.edit"))
            btn_edit.clicked.connect(lambda: self._edit_mutuelle(mutuelle))
            btn_bar.addWidget(btn_edit)
            btn_del = EmacButton("Supprimer", variant="danger")
            btn_del.setVisible(can("rh.mutuelle.edit"))
            btn_del.clicked.connect(lambda: self._delete_mutuelle(mutuelle))
            btn_bar.addWidget(btn_del)
        else:
            btn_add = EmacButton("+ Déclarer la mutuelle", variant="primary")
            btn_add.setVisible(can("rh.mutuelle.edit"))
            btn_add.clicked.connect(self._add_mutuelle)
            btn_bar.addWidget(btn_add)
        btn_bar.addStretch()
        card.body.addLayout(btn_bar)

        if mutuelle:
            statut = mutuelle.get('statut_adhesion', 'NON_COUVERT')
            color = _STATUT_COLORS.get(statut, '#6b7280')
            label_statut = _STATUT_LABELS.get(statut, statut)
            card.body.addWidget(QLabel(
                f"<b>Statut :</b> <span style='color:{color};font-weight:600'>{label_statut}</span>"
            ))

            grid = QGridLayout()
            grid.setSpacing(12)
            infos = []
            if statut == 'DISPENSE' and mutuelle.get('type_dispense'):
                infos.append(("Motif de dispense", mutuelle['type_dispense']))
            if statut == 'ADHERENT':
                if mutuelle.get('organisme'):
                    infos.append(("Organisme", mutuelle['organisme']))
                if mutuelle.get('numero_adherent'):
                    infos.append(("N° adhérent", mutuelle['numero_adherent']))
                if mutuelle.get('regime'):
                    infos.append(("Régime", _REGIME_LABELS.get(mutuelle['regime'], mutuelle['regime'])))
            if mutuelle.get('date_adhesion'):
                infos.append(("Date d'adhésion", self._format_date(mutuelle['date_adhesion'])))
            if mutuelle.get('date_fin'):
                infos.append(("Date de fin", self._format_date(mutuelle['date_fin'])))
            if mutuelle.get('commentaire'):
                infos.append(("Commentaire", mutuelle['commentaire']))

            for i, (lbl_txt, val) in enumerate(infos):
                r, c = divmod(i, 2)
                lbl = QLabel(f"<b>{lbl_txt}</b><br/>{val}")
                lbl.setStyleSheet("padding: 8px 12px; background: #f0f4f8; border: 1px solid #cbd5e1; border-radius: 6px;")
                lbl.setWordWrap(True)
                grid.addWidget(lbl, r, c)
            if infos:
                card.body.addLayout(grid)
        else:
            no_data = QLabel("Aucune information mutuelle enregistrée.")
            no_data.setStyleSheet("color: #9ca3af; padding: 12px 0;")
            card.body.addWidget(no_data)

        self._layout.addWidget(card)

        if len(historique) > 1:
            card_hist = EmacCard(f"Historique ({len(historique)} enregistrements)")
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Statut", "Organisme", "Régime", "Début", "Fin"])
            table.setRowCount(len(historique))
            hh = table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.Fixed); table.setColumnWidth(0, 110)
            hh.setSectionResizeMode(1, QHeaderView.Stretch)
            hh.setSectionResizeMode(2, QHeaderView.Fixed); table.setColumnWidth(2, 120)
            hh.setSectionResizeMode(3, QHeaderView.Fixed); table.setColumnWidth(3, 90)
            hh.setSectionResizeMode(4, QHeaderView.Fixed); table.setColumnWidth(4, 90)
            table.setAlternatingRowColors(True)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            for row_idx, rec in enumerate(historique):
                statut = rec.get('statut_adhesion', '-')
                table.setItem(row_idx, 0, QTableWidgetItem(_STATUT_LABELS.get(statut, statut)))
                table.setItem(row_idx, 1, QTableWidgetItem(rec.get('organisme') or '-'))
                regime = rec.get('regime') or ''
                table.setItem(row_idx, 2, QTableWidgetItem(_REGIME_LABELS.get(regime, regime) or '-'))
                table.setItem(row_idx, 3, QTableWidgetItem(self._format_date(rec.get('date_adhesion'))))
                table.setItem(row_idx, 4, QTableWidgetItem(self._format_date(rec.get('date_fin'))))
            card_hist.body.addWidget(table)
            self._layout.addWidget(card_hist)

    def _add_mutuelle(self):
        if not self._operateur:
            return
        dialog = EditMutuelleDialog(self._operateur['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _edit_mutuelle(self, mutuelle: dict):
        if not self._operateur:
            return
        dialog = EditMutuelleDialog(self._operateur['id'], mutuelle, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _delete_mutuelle(self, mutuelle: dict):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            "Voulez-vous vraiment supprimer cet enregistrement mutuelle ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._vm.supprimer_mutuelle(mutuelle['id'])
