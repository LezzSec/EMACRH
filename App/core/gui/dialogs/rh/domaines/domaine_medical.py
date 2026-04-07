# -*- coding: utf-8 -*-
"""
Domaine RH : Suivi médical (visites, accidents, RQTH/OETH).
"""
from datetime import date as date_class

from PyQt5.QtWidgets import (
    QDialog, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout

from core.gui.components.ui_theme import EmacCard, EmacButton
from core.gui.dialogs.gestion_rh_dialogs import (
    EditVisiteDialog, EditAccidentDialog, ConsulterDetailDialog,
)
from core.services.permission_manager import can
from .domaine_base import DomaineWidget


class DomaineMedical(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        if donnees.get('error'):
            error_card = EmacCard("Erreur")
            error_card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            self._layout.addWidget(error_card)
            return

        medical_info = donnees.get('medical') or {}
        visites = donnees.get('visites') or []
        accidents = donnees.get('accidents') or []
        validites = donnees.get('validites') or []
        alertes = donnees.get('alertes') or []

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

        card_medical = EmacCard("Suivi Médical")
        grid = QGridLayout()
        grid.setSpacing(12)
        type_suivi = medical_info.get('type_suivi_vip') or "Non défini"
        periodicite = medical_info.get('periodicite_vip_mois') or 24
        infos = [
            ("Type de suivi VIP", type_suivi),
            ("Périodicité", f"{periodicite} mois"),
            ("Maladie professionnelle", "Oui" if medical_info.get('maladie_pro') else "Non"),
            ("Taux professionnel", f"{medical_info.get('taux_professionnel', 0)}%" if medical_info.get('taux_professionnel') else "-"),
        ]
        if medical_info.get('besoins_adaptation'):
            infos.append(("Besoins d'adaptation", medical_info['besoins_adaptation']))
        for i, (label, valeur) in enumerate(infos):
            r, c = divmod(i, 2)
            lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
            lbl.setStyleSheet("padding: 8px 12px; background: #f0f4f8; border: 1px solid #cbd5e1; border-radius: 6px;")
            lbl.setWordWrap(True)
            grid.addWidget(lbl, r, c)
        card_medical.body.addLayout(grid)
        self._layout.addWidget(card_medical)

        rqth_validites = [v for v in validites if v.get('type_validite') == 'RQTH']
        oeth_validites = [v for v in validites if v.get('type_validite') == 'OETH']
        card_rqth = EmacCard("RQTH / OETH")
        rqth_layout = QHBoxLayout()

        for label, items_list, bg in [("RQTH", rqth_validites, "#f0fdf4"), ("OETH", oeth_validites, "#eff6ff")]:
            frame = QFrame()
            frame.setStyleSheet(f"padding: 8px; background: {bg}; border-radius: 6px;")
            inner = QVBoxLayout(frame)
            inner.addWidget(QLabel(f"<b>{label}</b>"))
            if items_list:
                latest = items_list[0]
                date_fin = latest.get('date_fin')
                statut = "Active" if date_fin and date_fin >= date_class.today() else "Expirée"
                inner.addWidget(QLabel(f"Statut: {statut}"))
                inner.addWidget(QLabel(f"Fin: {self._format_date(date_fin)}"))
                if label == "RQTH" and latest.get('taux_incapacite'):
                    inner.addWidget(QLabel(f"Taux: {latest['taux_incapacite']}%"))
            else:
                inner.addWidget(QLabel("Non applicable"))
            rqth_layout.addWidget(frame)

        card_rqth.body.addLayout(rqth_layout)
        self._layout.addWidget(card_rqth)

        card_visites = EmacCard(f"Visites médicales ({len(visites)})")
        btn_add_visite = EmacButton("+ Nouvelle visite", variant="primary")
        btn_add_visite.setVisible(can("rh.medical.edit"))
        btn_add_visite.clicked.connect(self._add_visite)
        card_visites.body.addWidget(btn_add_visite, alignment=Qt.AlignLeft)

        if visites:
            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["Date", "Type", "Résultat", "Médecin", "Prochaine", "Actions"])
            table.setRowCount(len(visites))
            hh = table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.Fixed); table.setColumnWidth(0, 100)
            hh.setSectionResizeMode(1, QHeaderView.Stretch)
            hh.setSectionResizeMode(2, QHeaderView.Fixed); table.setColumnWidth(2, 110)
            hh.setSectionResizeMode(3, QHeaderView.Stretch)
            hh.setSectionResizeMode(4, QHeaderView.Fixed); table.setColumnWidth(4, 100)
            hh.setSectionResizeMode(5, QHeaderView.Fixed); table.setColumnWidth(5, 220)
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.verticalHeader().setDefaultSectionSize(52)

            for row_idx, visite in enumerate(visites):
                table.setItem(row_idx, 0, QTableWidgetItem(self._format_date(visite.get('date_visite'))))
                table.setItem(row_idx, 1, QTableWidgetItem(visite.get('type_visite', '-')))
                table.setItem(row_idx, 2, QTableWidgetItem(visite.get('resultat', '-')))
                table.setItem(row_idx, 3, QTableWidgetItem(visite.get('medecin', '-')))
                table.setItem(row_idx, 4, QTableWidgetItem(self._format_date(visite.get('prochaine_visite'))))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(4, 4, 4, 4)
                btn_layout_inner.setSpacing(6)

                btn_consult = EmacButton("Consulter", variant="ghost")
                btn_consult.clicked.connect(lambda checked, v=visite: ConsulterDetailDialog(
                    "Détail de la visite médicale", [
                        ("Date", self._format_date(v.get('date_visite'))),
                        ("Type", v.get('type_visite')),
                        ("Résultat", v.get('resultat')),
                        ("Médecin", v.get('medecin')),
                        ("Prochaine visite", self._format_date(v.get('prochaine_visite'))),
                        ("Restrictions", v.get('restrictions')),
                        ("Commentaire", v.get('commentaire')),
                    ], self))
                btn_layout_inner.addWidget(btn_consult)
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.medical.edit"))
                btn_edit.clicked.connect(lambda checked, v=visite: self._edit_visite(v))
                btn_layout_inner.addWidget(btn_edit)
                btn_del = EmacButton("Suppr.", variant="danger")
                btn_del.setVisible(can("rh.medical.edit"))
                btn_del.clicked.connect(lambda checked, v=visite: self._delete_visite(v))
                btn_layout_inner.addWidget(btn_del)
                table.setCellWidget(row_idx, 5, btn_widget)

            table.setFixedHeight(min(len(visites) * 52 + 32, 420))
            card_visites.body.addWidget(table)
        else:
            card_visites.body.addWidget(QLabel("Aucune visite enregistrée"))
        self._layout.addWidget(card_visites)

        card_accidents = EmacCard(f"Accidents du travail ({len(accidents)})")
        btn_add_accident = EmacButton("+ Nouvel accident", variant="primary")
        btn_add_accident.setVisible(can("rh.medical.edit"))
        btn_add_accident.clicked.connect(self._add_accident)
        card_accidents.body.addWidget(btn_add_accident, alignment=Qt.AlignLeft)

        if accidents:
            for acc in accidents:
                frame = QFrame()
                frame.setStyleSheet("QFrame { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; }")
                frame_layout = QVBoxLayout(frame)
                frame_layout.setContentsMargins(12, 8, 12, 8)
                frame_layout.setSpacing(4)

                header_row = QHBoxLayout()
                header_row.addWidget(QLabel(f"<b>{self._format_date(acc.get('date_accident'))}</b>"))
                avec_arret = acc.get('avec_arret')
                arret_style = (
                    "padding: 2px 8px; border-radius: 10px; font-size: 11px; background: #fef3c7; color: #92400e;"
                    if avec_arret else
                    "padding: 2px 8px; border-radius: 10px; font-size: 11px; background: #f0fdf4; color: #166534;"
                )
                arret_lbl = QLabel("Avec arrêt" if avec_arret else "Sans arrêt")
                arret_lbl.setStyleSheet(arret_style)
                header_row.addWidget(arret_lbl)
                if acc.get('nb_jours_absence'):
                    jours_lbl = QLabel(f"{acc['nb_jours_absence']} jour(s) d'absence")
                    jours_lbl.setStyleSheet("color: #64748b; font-size: 12px;")
                    header_row.addWidget(jours_lbl)
                header_row.addStretch()
                frame_layout.addLayout(header_row)

                details = []
                if acc.get('siege_lesions'):
                    details.append(f"Siège : {acc['siege_lesions']}")
                if acc.get('nature_lesions'):
                    details.append(f"Nature : {acc['nature_lesions']}")
                if details:
                    detail_lbl = QLabel("  ·  ".join(details))
                    detail_lbl.setStyleSheet("color: #475569; font-size: 12px;")
                    frame_layout.addWidget(detail_lbl)

                actions_row = QHBoxLayout()
                actions_row.addStretch()
                btn_consult = EmacButton("Consulter", variant="ghost")
                btn_consult.clicked.connect(lambda checked, a=acc: ConsulterDetailDialog(
                    "Détail de l'accident", [
                        ("Date", self._format_date(a.get('date_accident'))),
                        ("Avec arrêt", "Oui" if a.get('avec_arret') else "Non"),
                        ("Nb jours d'absence", a.get('nb_jours_absence')),
                        ("Siège des lésions", a.get('siege_lesions')),
                        ("Nature des lésions", a.get('nature_lesions')),
                        ("Description", a.get('description')),
                        ("Commentaire", a.get('commentaire')),
                    ], self))
                actions_row.addWidget(btn_consult)
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.medical.edit"))
                btn_edit.clicked.connect(lambda checked, a=acc: self._edit_accident(a))
                actions_row.addWidget(btn_edit)
                btn_del = EmacButton("Supprimer", variant="danger")
                btn_del.setVisible(can("rh.medical.edit"))
                btn_del.clicked.connect(lambda checked, a=acc: self._delete_accident(a))
                actions_row.addWidget(btn_del)
                frame_layout.addLayout(actions_row)
                card_accidents.body.addWidget(frame)
        else:
            card_accidents.body.addWidget(QLabel("Aucun accident enregistré"))
        self._layout.addWidget(card_accidents)

    def _add_visite(self):
        if not self._operateur:
            return
        dialog = EditVisiteDialog(self._operateur['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _edit_visite(self, visite: dict):
        if not self._operateur:
            return
        dialog = EditVisiteDialog(self._operateur['id'], visite, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _delete_visite(self, visite: dict):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la visite du {self._format_date(visite.get('date_visite'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._vm.supprimer_visite(visite['id'])

    def _add_accident(self):
        if not self._operateur:
            return
        dialog = EditAccidentDialog(self._operateur['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _edit_accident(self, accident: dict):
        if not self._operateur:
            return
        dialog = EditAccidentDialog(self._operateur['id'], accident, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _delete_accident(self, accident: dict):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'accident du {self._format_date(accident.get('date_accident'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._vm.supprimer_accident(accident['id'])
