# -*- coding: utf-8 -*-
"""
Domaine RH : Vie du salarié (sanctions, contrôles, entretiens).
"""
from PyQt5.QtWidgets import (
    QDialog, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QWidget,
)
from PyQt5.QtCore import Qt

from core.gui.components.ui_theme import EmacCard, EmacButton
from core.gui.dialogs.gestion_rh_dialogs import (
    EditSanctionDialog, EditControleAlcoolDialog, EditTestSalivaireDialog,
    EditEntretienDialog, ConsulterDetailDialog,
)
from application.permission_manager import can
from .domaine_base import DomaineWidget

_ROW_H = 30


class DomaineVieSalarie(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        if donnees.get('error'):
            error_card = EmacCard("Erreur")
            error_card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            self._layout.addWidget(error_card)
            return

        sanctions_data = donnees.get('sanctions', {})
        alcoolemie_data = donnees.get('alcoolemie', {})
        salivaire_data = donnees.get('tests_salivaires', {})
        entretiens_data = donnees.get('entretiens', {})
        alertes = donnees.get('alertes', [])

        if alertes:
            alertes_card = EmacCard("Alertes")
            for alerte in alertes:
                alert_widget = QFrame()
                alert_widget.setStyleSheet("""
                    QFrame {
                        background: #fef2f2; border: 1px solid #fecaca;
                        border-radius: 6px; padding: 8px 12px; margin-bottom: 4px;
                    }
                """)
                alert_layout = QHBoxLayout(alert_widget)
                alert_layout.setContentsMargins(8, 4, 8, 4)
                lbl = QLabel(alerte.get('message', str(alerte)))
                lbl.setStyleSheet("color: #dc2626; font-weight: 500;")
                alert_layout.addWidget(lbl)
                alertes_card.body.addWidget(alert_widget)
            self._layout.addWidget(alertes_card)

        card_recap = EmacCard("Récapitulatif")
        recap_layout = QHBoxLayout()
        for label, data, bg, extra in [
            ("Sanctions", sanctions_data, "#fef3c7", lambda d: (f"Total: {d.get('total', 0)}", f"Dernière: {self._format_date(d.get('derniere_sanction'))}" if d.get('derniere_sanction') else None)),
            ("Contrôles alcool", alcoolemie_data, "#dbeafe", lambda d: (f"Total: {d.get('total', 0)}", f"Positifs: {d.get('positifs', 0)}")),
            ("Tests salivaires", salivaire_data, "#f3e8ff", lambda d: (f"Total: {d.get('total', 0)}", f"Positifs: {d.get('positifs', 0)}")),
        ]:
            frame = QFrame()
            frame.setStyleSheet(f"padding: 12px; background: {bg}; border-radius: 8px;")
            inner = QVBoxLayout(frame)
            inner.addWidget(QLabel(f"<b>{label}</b>"))
            d = data if isinstance(data, dict) else {}
            lines = extra(d)
            for line in lines:
                if line:
                    inner.addWidget(QLabel(line))
            recap_layout.addWidget(frame)

        entretiens_frame = QFrame()
        entretiens_frame.setStyleSheet("padding: 12px; background: #dcfce7; border-radius: 8px;")
        entretiens_inner = QVBoxLayout(entretiens_frame)
        entretiens_inner.addWidget(QLabel("<b>Entretiens</b>"))
        ed = entretiens_data if isinstance(entretiens_data, dict) else {}
        entretiens_inner.addWidget(QLabel(f"EPP: {self._format_date(ed.get('dernier_epp')) if ed.get('dernier_epp') else '-'}"))
        entretiens_inner.addWidget(QLabel(f"EAP: {self._format_date(ed.get('dernier_eap')) if ed.get('dernier_eap') else '-'}"))
        recap_layout.addWidget(entretiens_frame)

        card_recap.body.addLayout(recap_layout)
        self._layout.addWidget(card_recap)

        sanctions_list = donnees.get('sanctions_liste', [])
        card_sanctions = EmacCard(f"Sanctions disciplinaires ({len(sanctions_list)})")
        btn_add_sanction = EmacButton("+ Nouvelle sanction", variant="primary")
        btn_add_sanction.setVisible(can("rh.vie_salarie.edit"))
        btn_add_sanction.clicked.connect(self._add_sanction)
        card_sanctions.body.addWidget(btn_add_sanction, alignment=Qt.AlignLeft)

        if sanctions_list:
            table_sanctions = QTableWidget()
            table_sanctions.setColumnCount(5)
            table_sanctions.setHorizontalHeaderLabels(["Date", "Type", "Durée", "Motif", "Actions"])
            table_sanctions.setRowCount(len(sanctions_list))
            hh_s = table_sanctions.horizontalHeader()
            hh_s.setSectionResizeMode(0, QHeaderView.Fixed); table_sanctions.setColumnWidth(0, 100)
            hh_s.setSectionResizeMode(1, QHeaderView.Fixed); table_sanctions.setColumnWidth(1, 150)
            hh_s.setSectionResizeMode(2, QHeaderView.Fixed); table_sanctions.setColumnWidth(2, 70)
            hh_s.setSectionResizeMode(3, QHeaderView.Stretch)
            hh_s.setSectionResizeMode(4, QHeaderView.Fixed); table_sanctions.setColumnWidth(4, 220)
            table_sanctions.setAlternatingRowColors(True)
            table_sanctions.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_sanctions.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table_sanctions.verticalHeader().setDefaultSectionSize(52)

            for row_idx, sanc in enumerate(sanctions_list):
                table_sanctions.setItem(row_idx, 0, QTableWidgetItem(self._format_date(sanc.get('date_sanction'))))
                table_sanctions.setItem(row_idx, 1, QTableWidgetItem(sanc.get('type_sanction', '-')))
                table_sanctions.setItem(row_idx, 2, QTableWidgetItem(str(sanc.get('duree_jours', '-')) if sanc.get('duree_jours') else '-'))
                motif = sanc.get('motif', '-')
                if motif and len(motif) > 50:
                    motif = motif[:50] + "..."
                table_sanctions.setItem(row_idx, 3, QTableWidgetItem(motif))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(4, 4, 4, 4)
                btn_layout_inner.setSpacing(6)
                btn_consult = EmacButton("Consulter", variant="ghost")
                btn_consult.clicked.connect(lambda checked, s=sanc: ConsulterDetailDialog(
                    "Détail de la sanction", [
                        ("Date", self._format_date(s.get('date_sanction'))),
                        ("Type", s.get('type_sanction')),
                        ("Durée (jours)", s.get('duree_jours')),
                        ("Motif", s.get('motif')),
                        ("Commentaire", s.get('commentaire')),
                    ], self))
                btn_layout_inner.addWidget(btn_consult)
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.vie_salarie.edit"))
                btn_edit.clicked.connect(lambda checked, s=sanc: self._edit_sanction(s))
                btn_layout_inner.addWidget(btn_edit)
                btn_del = EmacButton("Suppr.", variant="danger")
                btn_del.setVisible(can("rh.vie_salarie.edit"))
                btn_del.clicked.connect(lambda checked, s=sanc: self._delete_sanction(s))
                btn_layout_inner.addWidget(btn_del)
                table_sanctions.setCellWidget(row_idx, 4, btn_widget)

            table_sanctions.setFixedHeight(min(len(sanctions_list) * 52 + 32, 420))
            card_sanctions.body.addWidget(table_sanctions)
        else:
            card_sanctions.body.addWidget(QLabel("Aucune sanction enregistrée"))
        self._layout.addWidget(card_sanctions)

        controles_alcool = donnees.get('controles_alcool_liste', [])
        controles_salivaire = donnees.get('tests_salivaires_liste', [])
        card_controles = EmacCard("Contrôles (Alcool / Salivaire)")
        btn_layout_ctrl = QHBoxLayout()
        btn_add_alcool = EmacButton("+ Contrôle alcool", variant="primary")
        btn_add_alcool.setVisible(can("rh.vie_salarie.edit"))
        btn_add_alcool.clicked.connect(self._add_controle_alcool)
        btn_layout_ctrl.addWidget(btn_add_alcool)
        btn_add_salivaire = EmacButton("+ Test salivaire", variant="primary")
        btn_add_salivaire.setVisible(can("rh.vie_salarie.edit"))
        btn_add_salivaire.clicked.connect(self._add_test_salivaire)
        btn_layout_ctrl.addWidget(btn_add_salivaire)
        btn_layout_ctrl.addStretch()
        card_controles.body.addLayout(btn_layout_ctrl)

        tables_layout = QHBoxLayout()

        alcool_container = QVBoxLayout()
        alcool_container.addWidget(QLabel("<b>Alcoolémie</b>"))
        if controles_alcool:
            table_alcool = QTableWidget()
            table_alcool.setColumnCount(3)
            table_alcool.setHorizontalHeaderLabels(["Date", "Résultat", "Taux"])
            table_alcool.setRowCount(len(controles_alcool))
            hh_a = table_alcool.horizontalHeader()
            hh_a.setSectionResizeMode(0, QHeaderView.Fixed); table_alcool.setColumnWidth(0, 95)
            hh_a.setSectionResizeMode(1, QHeaderView.Stretch)
            hh_a.setSectionResizeMode(2, QHeaderView.Fixed); table_alcool.setColumnWidth(2, 80)
            table_alcool.setAlternatingRowColors(True)
            table_alcool.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table_alcool.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_alcool.verticalHeader().setDefaultSectionSize(_ROW_H)
            for row_idx, ctrl in enumerate(controles_alcool):
                table_alcool.setItem(row_idx, 0, QTableWidgetItem(self._format_date(ctrl.get('date_controle'))))
                table_alcool.setItem(row_idx, 1, QTableWidgetItem(ctrl.get('resultat', '-')))
                table_alcool.setItem(row_idx, 2, QTableWidgetItem(f"{ctrl.get('taux')} g/L" if ctrl.get('taux') else '-'))
            table_alcool.setFixedHeight(min(len(controles_alcool), 8) * _ROW_H + 32)
            alcool_container.addWidget(table_alcool)
        else:
            alcool_container.addWidget(QLabel("Aucun contrôle"))
        tables_layout.addLayout(alcool_container)

        salivaire_container = QVBoxLayout()
        salivaire_container.addWidget(QLabel("<b>Tests salivaires</b>"))
        if controles_salivaire:
            table_salivaire = QTableWidget()
            table_salivaire.setColumnCount(2)
            table_salivaire.setHorizontalHeaderLabels(["Date", "Résultat"])
            table_salivaire.setRowCount(len(controles_salivaire))
            table_salivaire.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_salivaire.setAlternatingRowColors(True)
            table_salivaire.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table_salivaire.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_salivaire.verticalHeader().setDefaultSectionSize(_ROW_H)
            for row_idx, test in enumerate(controles_salivaire):
                table_salivaire.setItem(row_idx, 0, QTableWidgetItem(self._format_date(test.get('date_test'))))
                table_salivaire.setItem(row_idx, 1, QTableWidgetItem(test.get('resultat', '-')))
            table_salivaire.setFixedHeight(min(len(controles_salivaire), 8) * _ROW_H + 32)
            salivaire_container.addWidget(table_salivaire)
        else:
            salivaire_container.addWidget(QLabel("Aucun test"))
        tables_layout.addLayout(salivaire_container)

        card_controles.body.addLayout(tables_layout)
        self._layout.addWidget(card_controles)

        entretiens_liste = donnees.get('entretiens_liste', [])
        card_entretiens = EmacCard(f"Entretiens professionnels ({len(entretiens_liste)})")
        btn_add_entretien = EmacButton("+ Nouvel entretien", variant="primary")
        btn_add_entretien.setVisible(can("rh.vie_salarie.edit"))
        btn_add_entretien.clicked.connect(self._add_entretien)
        card_entretiens.body.addWidget(btn_add_entretien, alignment=Qt.AlignLeft)

        if entretiens_liste:
            table_entretiens = QTableWidget()
            table_entretiens.setColumnCount(5)
            table_entretiens.setHorizontalHeaderLabels(["Date", "Type", "Manager", "Prochaine", "Actions"])
            table_entretiens.setRowCount(len(entretiens_liste))
            hh_e = table_entretiens.horizontalHeader()
            hh_e.setSectionResizeMode(0, QHeaderView.Fixed); table_entretiens.setColumnWidth(0, 100)
            hh_e.setSectionResizeMode(1, QHeaderView.Stretch)
            hh_e.setSectionResizeMode(2, QHeaderView.Stretch)
            hh_e.setSectionResizeMode(3, QHeaderView.Fixed); table_entretiens.setColumnWidth(3, 100)
            hh_e.setSectionResizeMode(4, QHeaderView.Fixed); table_entretiens.setColumnWidth(4, 220)
            table_entretiens.setAlternatingRowColors(True)
            table_entretiens.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_entretiens.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table_entretiens.verticalHeader().setDefaultSectionSize(52)

            for row_idx, ent in enumerate(entretiens_liste):
                table_entretiens.setItem(row_idx, 0, QTableWidgetItem(self._format_date(ent.get('date_entretien'))))
                table_entretiens.setItem(row_idx, 1, QTableWidgetItem(ent.get('type_entretien', '-')))
                table_entretiens.setItem(row_idx, 2, QTableWidgetItem(ent.get('manager_nom', '-')))
                table_entretiens.setItem(row_idx, 3, QTableWidgetItem(self._format_date(ent.get('prochaine_date'))))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(4, 4, 4, 4)
                btn_layout_inner.setSpacing(6)
                btn_consult = EmacButton("Consulter", variant="ghost")
                btn_consult.clicked.connect(lambda checked, e=ent: ConsulterDetailDialog(
                    "Détail de l'entretien", [
                        ("Date", self._format_date(e.get('date_entretien'))),
                        ("Type", e.get('type_entretien')),
                        ("Manager", e.get('manager_nom')),
                        ("Prochaine date", self._format_date(e.get('prochaine_date'))),
                        ("Objectifs", e.get('objectifs')),
                        ("Commentaire", e.get('commentaire')),
                    ], self))
                btn_layout_inner.addWidget(btn_consult)
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.vie_salarie.edit"))
                btn_edit.clicked.connect(lambda checked, e=ent: self._edit_entretien(e))
                btn_layout_inner.addWidget(btn_edit)
                btn_del = EmacButton("Suppr.", variant="danger")
                btn_del.setVisible(can("rh.vie_salarie.edit"))
                btn_del.clicked.connect(lambda checked, e=ent: self._delete_entretien(e))
                btn_layout_inner.addWidget(btn_del)
                table_entretiens.setCellWidget(row_idx, 4, btn_widget)

            table_entretiens.setFixedHeight(min(len(entretiens_liste) * 52 + 32, 420))
            card_entretiens.body.addWidget(table_entretiens)
        else:
            card_entretiens.body.addWidget(QLabel("Aucun entretien enregistré"))
        self._layout.addWidget(card_entretiens)

    def _add_sanction(self):
        if not self._operateur:
            return
        dialog = EditSanctionDialog(self._operateur['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _edit_sanction(self, sanction: dict):
        if not self._operateur:
            return
        dialog = EditSanctionDialog(self._operateur['id'], sanction, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _delete_sanction(self, sanction: dict):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la sanction du {self._format_date(sanction.get('date_sanction'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._vm.supprimer_sanction(sanction['id'])

    def _add_controle_alcool(self):
        if not self._operateur:
            return
        dialog = EditControleAlcoolDialog(self._operateur['id'], self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _add_test_salivaire(self):
        if not self._operateur:
            return
        dialog = EditTestSalivaireDialog(self._operateur['id'], self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _add_entretien(self):
        if not self._operateur:
            return
        dialog = EditEntretienDialog(self._operateur['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _edit_entretien(self, entretien: dict):
        if not self._operateur:
            return
        dialog = EditEntretienDialog(self._operateur['id'], entretien, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _delete_entretien(self, entretien: dict):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'entretien du {self._format_date(entretien.get('date_entretien'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._vm.supprimer_entretien(entretien['id'])
