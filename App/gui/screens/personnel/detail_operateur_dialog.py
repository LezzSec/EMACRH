# -*- coding: utf-8 -*-
"""
DetailOperateurDialog — fiche détail d'un opérateur (View uniquement).

Toute la logique métier/données est dans DetailOperateurViewModel.
"""

from infrastructure.logging.logging_config import get_logger
logger = get_logger(__name__)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QWidget, QTabWidget,
    QMessageBox, QScrollArea, QFrame, QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from gui.components.emac_ui_kit import add_custom_title_bar, show_error_message
from gui.workers.db_worker import DbWorker, DbThreadPool
from gui.view_models.detail_operateur_view_model import DetailOperateurViewModel
from gui.screens.personnel.historique_personnel import HistoriquePersonnelTab
from application.permission_manager import require


class DetailOperateurDialog(QDialog):
    """Fenêtre modale affichant tous les détails d'un opérateur."""

    operateur_status_changed = pyqtSignal(int)

    def __init__(self, operateur_id, nom, prenom, statut, parent=None, is_production=True):
        super().__init__(parent)
        self.setWindowTitle(f"Détails - {nom} {prenom}")
        self.setGeometry(200, 150, 900, 600)

        self.vm = DetailOperateurViewModel(operateur_id, nom, prenom, statut, is_production)

        self._build_ui(nom, prenom)

        # Connexions ViewModel → View
        self.vm.profile_loaded.connect(self._render_profile)
        self.vm.polyvalences_loaded.connect(self._render_polyvalences)
        self.vm.status_changed.connect(self._on_status_changed)
        self.vm.error.connect(lambda msg: show_error_message(self, "Erreur", msg))

        # Chargement asynchrone
        worker = DbWorker(self.vm.load_all)
        worker.signals.result.connect(lambda _: None)
        worker.signals.error.connect(lambda e: self.vm.error.emit(str(e)))
        DbThreadPool.start(worker)

    # ------------------------------------------------------------------
    # Construction de l'UI
    # ------------------------------------------------------------------

    def _build_ui(self, nom: str, prenom: str):
        """Construit tous les widgets — aucune donnée chargée ici."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = add_custom_title_bar(self, f"Détails - {nom} {prenom}")
        main_layout.addWidget(title_bar)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # --- En-tête nom + statut ---
        header = QLabel(f"{nom} {prenom}")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.status_label = QLabel(f"Statut : {self.vm.statut}")
        self._update_status_label_style()
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # --- Onglets ---
        tabs = QTabWidget()

        # Onglet Polyvalences (production uniquement)
        poly_tab = QWidget()
        poly_layout = QVBoxLayout(poly_tab)

        poly_label = QLabel("Polyvalences et Compétences")
        poly_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        poly_layout.addWidget(poly_label)

        self.poly_table = QTableWidget()
        self.poly_table.setColumnCount(6)
        self.poly_table.setHorizontalHeaderLabels([
            "Poste", "Niveau", "Date Évaluation", "Prochaine Éval.", "Ancienneté", "Statut"
        ])
        self.poly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.poly_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        poly_layout.addWidget(self.poly_table)

        stats_box = QHBoxLayout()
        self.stat_n1    = self._create_mini_stat("N1", "0", "#ef4444")
        self.stat_n2    = self._create_mini_stat("N2", "0", "#f59e0b")
        self.stat_n3    = self._create_mini_stat("N3", "0", "#10b981")
        self.stat_n4    = self._create_mini_stat("N4", "0", "#3b82f6")
        self.stat_total = self._create_mini_stat("Total", "0", "#6b7280")
        for s in (self.stat_n1, self.stat_n2, self.stat_n3, self.stat_n4, self.stat_total):
            stats_box.addWidget(s)
        poly_layout.addLayout(stats_box)

        self._poly_tab_ref = poly_tab
        if self.vm.is_production:
            tabs.addTab(poly_tab, "Polyvalences")

        # Onglet Infos Complémentaires
        infos_tab = QWidget()
        infos_layout = QVBoxLayout(infos_tab)
        infos_layout.setSpacing(0)
        infos_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background-color: #f8fafc; border: none; }
            QScrollBar:vertical {
                background: #f1f5f9; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #94a3b8; }
        """)

        self.infos_container = QWidget()
        self.infos_container.setStyleSheet("background-color: #f8fafc;")
        self.infos_cards_layout = QVBoxLayout(self.infos_container)
        self.infos_cards_layout.setSpacing(16)
        self.infos_cards_layout.setContentsMargins(20, 20, 20, 20)
        self.infos_cards_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.infos_container)
        infos_layout.addWidget(scroll)
        tabs.addTab(infos_tab, "Infos Complémentaires")

        # Onglet Historique polyvalences
        if self.vm.is_production:
            self.history_tab = HistoriquePersonnelTab(
                operateur_id=self.vm.operateur_id,
                operateur_nom=self.vm.nom,
                operateur_prenom=self.vm.prenom,
                parent=self,
            )
            tabs.addTab(self.history_tab, "Historique Polyvalences")

        self.tabs_widget = tabs
        layout.addWidget(tabs)

        # --- Boutons d'action ---
        actions = QHBoxLayout()

        self.toggle_status_btn = QPushButton()
        self._update_toggle_btn_style()
        self.toggle_status_btn.clicked.connect(self._on_toggle_status_clicked)
        actions.addWidget(self.toggle_status_btn)

        actions.addStretch()

        self.export_btn = QPushButton("Exporter le profil")
        self.export_btn.clicked.connect(self.export_profile)
        actions.addWidget(self.export_btn)

        self.close_btn = QPushButton("Fermer")
        self.close_btn.clicked.connect(self.close)
        actions.addWidget(self.close_btn)

        layout.addLayout(actions)
        main_layout.addWidget(content_widget)

    # ------------------------------------------------------------------
    # Slots ViewModel → View
    # ------------------------------------------------------------------

    def _render_profile(self, data: dict):
        """Slot : reçoit les données profil du ViewModel et remplit les cartes."""
        self._clear_infos_cards()
        infos_data = data.get("infos_data", [])
        has_contrat    = data.get("has_contrat", False)
        has_formations = data.get("has_formations", False)

        icon_map = {
            "Informations Personnelles": ("", "#3b82f6", None),
            "Contrat Actuel":           ("", "#f59e0b", self._open_contract_management if has_contrat else None),
            "Formations":               ("", "#10b981", self._open_formation_rh if has_formations else None),
            "Validités":                ("", "#8b5cf6", None),
        }

        for section_title, items in infos_data:
            icon, color, on_click = icon_map.get(section_title, ("", "#3b82f6", None))
            self._add_info_card(section_title, items, icon_color=color, icon=icon, on_click=on_click)

        self.infos_cards_layout.addStretch()

    def _render_polyvalences(self, data: list):
        """Slot : reçoit la liste de polyvalences du ViewModel et remplit le tableau."""
        self.poly_table.setRowCount(0)

        # Séparer les stats du reste
        stats = None
        rows  = []
        for item in data:
            if item.get("__stats__"):
                stats = item
            else:
                rows.append(item)

        for r in rows:
            row = self.poly_table.rowCount()
            self.poly_table.insertRow(row)

            self.poly_table.setItem(row, 0, QTableWidgetItem(r["poste"]))

            niveau_item = QTableWidgetItem(r["niveau"])
            niveau_item.setBackground(QColor(r["bg_color"]))
            niveau_item.setForeground(QColor(r["fg_color"]))
            niveau_item.setTextAlignment(Qt.AlignCenter)
            self.poly_table.setItem(row, 1, niveau_item)

            self.poly_table.setItem(row, 2, QTableWidgetItem(r["date_evaluation"]))
            self.poly_table.setItem(row, 3, QTableWidgetItem(r["prochaine_evaluation"]))
            self.poly_table.setItem(row, 4, QTableWidgetItem(r["anciennete"]))

            statut_item = QTableWidgetItem(r["statut_eval"])
            if r["statut_eval"] == "En retard":
                statut_item.setForeground(QColor("#dc2626"))
            elif r["statut_eval"] == "À jour":
                statut_item.setForeground(QColor("#059669"))
            else:
                statut_item.setForeground(QColor("#d97706"))
            statut_item.setTextAlignment(Qt.AlignCenter)
            self.poly_table.setItem(row, 5, statut_item)

        if stats:
            self.stat_n1.value_label.setText(str(stats["n1"]))
            self.stat_n2.value_label.setText(str(stats["n2"]))
            self.stat_n3.value_label.setText(str(stats["n3"]))
            self.stat_n4.value_label.setText(str(stats["n4"]))
            self.stat_total.value_label.setText(str(stats["total"]))

    def _on_status_changed(self, new_statut: str):
        """Slot : met à jour l'UI après changement de statut."""
        self._update_status_label_style()
        self._update_toggle_btn_style()
        QMessageBox.information(
            self, "Statut modifié",
            f"Le statut a été changé à {new_statut} avec succès !"
        )
        self.operateur_status_changed.emit(self.vm.operateur_id)

    # ------------------------------------------------------------------
    # Actions utilisateur
    # ------------------------------------------------------------------

    def _on_toggle_status_clicked(self):
        """Demande confirmation puis délègue au ViewModel."""
        try:
            require('rh.personnel.edit')
        except PermissionError:
            QMessageBox.warning(
                self, "Accès refusé",
                "Vous n'avez pas les droits pour modifier le statut du personnel."
            )
            return

        new_statut = "INACTIF" if self.vm.statut == "ACTIF" else "ACTIF"
        action = "désactiver" if new_statut == "INACTIF" else "réactiver"

        reply = QMessageBox.question(
            self, f"Confirmer {action}",
            f"Êtes-vous sûr de vouloir {action} cette personne ?\n\n"
            f"Son statut passera à {new_statut}.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.vm.toggle_status()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_profile(self):
        """Demande le format puis lance PDF ou Excel."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Exporter le profil")
        dlg.setMinimumWidth(360)
        v = QVBoxLayout(dlg)
        v.addWidget(QLabel("Choisir le format d'export :"))
        btns = QHBoxLayout()
        b_pdf    = QPushButton("PDF")
        b_xlsx   = QPushButton("Excel")
        b_cancel = QPushButton("Annuler")
        b_pdf.clicked.connect(lambda: (setattr(dlg, "_choice", "pdf"), dlg.accept()))
        b_xlsx.clicked.connect(lambda: (setattr(dlg, "_choice", "xlsx"), dlg.accept()))
        b_cancel.clicked.connect(dlg.reject)
        btns.addStretch(1)
        for b in (b_pdf, b_xlsx, b_cancel):
            btns.addWidget(b)
        v.addLayout(btns)

        if dlg.exec_() != QDialog.Accepted or not getattr(dlg, "_choice", None):
            return
        if dlg._choice == "pdf":
            self.export_profile_pdf()
        else:
            self.export_profile_excel()

    def export_profile_pdf(self):
        """Collecte données + chemin via QFileDialog, délègue au service PDF."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import datetime as _dt

            row = None
            try:
                from domain.repositories.personnel_repo import PersonnelRepository
                row = PersonnelRepository.get_info_basique(self.vm.operateur_id)
            except Exception:
                pass

            nom       = row['nom']       if row else self.vm.nom
            prenom    = row['prenom']    if row else self.vm.prenom
            matricule = row['matricule'] if row else ""
            statut    = row['statut']    if row else self.vm.statut

            default_name = f"profil_{matricule or 'operateur'}_{_dt.date.today():%Y%m%d}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter en PDF", default_name, "PDF (*.pdf)"
            )
            if not file_path:
                return

            poly_export = [p for p in self.vm.polyvalences if not p.get("__stats__")]

            from domain.services.personnel.personnel_export_pdf import export_personnel_profile_pdf
            export_personnel_profile_pdf(
                operateur_id=self.vm.operateur_id,
                nom=nom, prenom=prenom, matricule=matricule, statut=statut,
                infos_data=self.vm.infos_data,
                polyvalences=poly_export,
                file_path=file_path,
            )
            QMessageBox.information(self, "Export réussi",
                                    f"Le profil a été exporté avec succès !\n\n{file_path}")
        except Exception as e:
            logger.exception(f"Erreur export PDF: {e}")
            show_error_message(self, "Erreur d'export", "Impossible de générer le PDF.", e)

    def export_profile_excel(self):
        """Collecte données + chemin via QFileDialog, délègue au service Excel."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import datetime as _dt

            row = None
            try:
                from domain.repositories.personnel_repo import PersonnelRepository
                row = PersonnelRepository.get_info_basique(self.vm.operateur_id)
            except Exception:
                pass

            nom       = row['nom']       if row else self.vm.nom
            prenom    = row['prenom']    if row else self.vm.prenom
            matricule = row['matricule'] if row else ""
            statut    = row['statut']    if row else self.vm.statut

            default_name = f"profil_{matricule or 'operateur'}_{_dt.date.today():%Y%m%d}.xlsx"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter le profil", default_name, "Excel Files (*.xlsx)"
            )
            if not file_path:
                return

            poly_export = [p for p in self.vm.polyvalences if not p.get("__stats__")]

            from domain.services.personnel.personnel_export_excel import export_personnel_profile_excel
            export_personnel_profile_excel(
                operateur_id=self.vm.operateur_id,
                nom=nom, prenom=prenom, matricule=matricule, statut=statut,
                infos_data=self.vm.infos_data,
                polyvalences=poly_export,
                file_path=file_path,
            )
            QMessageBox.information(self, "Export réussi",
                                    f"Profil exporté :\n{file_path}")
        except Exception as e:
            logger.exception(f"Erreur export Excel: {e}")
            show_error_message(self, "Erreur", "Impossible d'exporter le profil", e)

    # ------------------------------------------------------------------
    # Helpers UI
    # ------------------------------------------------------------------

    def _create_mini_stat(self, label: str, value: str, color: str) -> QWidget:
        """Crée une mini-carte de statistique colorée."""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{ background: {color}; border-radius: 6px; padding: 8px; }}
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        val_label = QLabel(value)
        val_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        val_label.setStyleSheet("color: white;")
        val_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(val_label)

        text_label = QLabel(label)
        text_label.setStyleSheet("color: white; font-size: 10px;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        widget.value_label = val_label
        return widget

    def _add_info_card(self, title: str, items: list,
                       icon_color: str = "#3b82f6", icon: str = "",
                       on_click=None):
        """Crée et ajoute une carte d'information au layout de l'onglet Infos."""
        card = QFrame()

        if on_click:
            card.setCursor(Qt.PointingHandCursor)
            card.setStyleSheet(f"""
                QFrame {{ background-color: white; border-radius: 12px; border: 1px solid #e2e8f0; }}
                QFrame:hover {{ border: 2px solid {icon_color}; background-color: #fafafa; }}
            """)
            card.mousePressEvent = lambda event: on_click()
        else:
            card.setStyleSheet(f"""
                QFrame {{ background-color: white; border-radius: 12px; border: 1px solid #e2e8f0; }}
                QFrame:hover {{ border: 1px solid {icon_color}; }}
            """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            f"background-color: {icon_color}20; border-radius: 18px; font-size: 16px;"
        )
        header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #1e293b; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()
        card_layout.addLayout(header)

        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e2e8f0;")
        card_layout.addWidget(separator)

        content_layout = QGridLayout()
        content_layout.setSpacing(8)
        content_layout.setColumnStretch(1, 1)

        for row, (label, value) in enumerate(items):
            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet("color: #64748b; background: transparent;")
            content_layout.addWidget(lbl, row, 0, Qt.AlignTop)

            val = QLabel(str(value) if value else "—")
            val.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
            val.setStyleSheet("color: #1e293b; background: transparent;")
            val.setWordWrap(True)
            content_layout.addWidget(val, row, 1, Qt.AlignTop)

        card_layout.addLayout(content_layout)

        if on_click:
            link_label = QLabel("Voir détails →")
            link_label.setFont(QFont("Segoe UI", 9))
            link_label.setStyleSheet(f"color: {icon_color}; background: transparent;")
            link_label.setAlignment(Qt.AlignRight)
            card_layout.addWidget(link_label)

        self.infos_cards_layout.addWidget(card)

    def _clear_infos_cards(self):
        """Supprime toutes les cartes existantes du layout."""
        while self.infos_cards_layout.count():
            item = self.infos_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _update_status_label_style(self):
        """Met à jour le style du label de statut."""
        if self.vm.statut == "ACTIF":
            self.status_label.setStyleSheet(
                "color: #10b981; font-weight: bold; font-size: 14px;"
            )
        else:
            self.status_label.setStyleSheet(
                "color: #dc2626; font-weight: bold; font-size: 14px;"
            )
        self.status_label.setText(f"Statut : {self.vm.statut}")

    def _update_toggle_btn_style(self):
        """Met à jour le texte et le style du bouton de changement de statut."""
        if self.vm.statut == "ACTIF":
            self.toggle_status_btn.setText("Désactiver")
            self.toggle_status_btn.setStyleSheet("""
                QPushButton {
                    background: #dc2626; color: white;
                    font-weight: bold; padding: 10px 20px; border-radius: 8px;
                }
                QPushButton:hover { background: #b91c1c; }
            """)
        else:
            self.toggle_status_btn.setText("Réactiver")
            self.toggle_status_btn.setStyleSheet("""
                QPushButton {
                    background: #10b981; color: white;
                    font-weight: bold; padding: 10px 20px; border-radius: 8px;
                }
                QPushButton:hover { background: #059669; }
            """)

    # ------------------------------------------------------------------
    # Navigation depuis les cartes
    # ------------------------------------------------------------------

    def _open_contract_management(self):
        """Ouvre la Gestion RH sur l'onglet Contrat."""
        from gui.screens.rh.gestion_rh_dialog import GestionRHDialog
        from domain.services.rh.rh_service import DomaineRH
        dialog = GestionRHDialog(self)
        dialog._selectionner_operateur_par_id(self.vm.operateur_id)
        dialog._on_domaine_change(DomaineRH.CONTRAT.value)
        dialog.exec_()
        # Recharger le profil après fermeture
        worker = DbWorker(self.vm.load_all)
        worker.signals.result.connect(lambda _: None)
        DbThreadPool.start(worker)

    def _open_formation_rh(self):
        """Ouvre la Gestion RH sur l'onglet Formation."""
        from gui.screens.rh.gestion_rh_dialog import GestionRHDialog
        from gui.view_models.gestion_rh_view_model import DomaineRH
        dialog = GestionRHDialog(self, preselect_personnel_id=self.vm.operateur_id)
        dialog._vm.operateur_loaded.connect(
            lambda _: dialog._on_domaine_change(DomaineRH.FORMATION.value)
        )
        dialog.exec_()
        worker = DbWorker(self.vm.load_all)
        worker.signals.result.connect(lambda _: None)
        DbThreadPool.start(worker)
