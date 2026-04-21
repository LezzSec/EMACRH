# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QComboBox, QMessageBox,
    QWidget, QAbstractItemView, QMenu, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from gui.components.emac_ui_kit import add_custom_title_bar
from gui.view_models.formation_view_model import FormationViewModel
from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date
from gui.components.ui_theme import EmacCard, EmacButton

logger = get_logger(__name__)

THEME_AVAILABLE = True


class GestionFormationsDialog(QDialog):
    """Fenetre principale de gestion des formations."""

    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Formations")
        self.setGeometry(100, 100, 1300, 750)

        self._vm = FormationViewModel(parent=self)
        self.init_ui()
        self._connect_viewmodel()
        self.load_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = add_custom_title_bar(self, "Gestion des Formations")
        main_layout.addWidget(title_bar)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(16)

        self._create_header(layout)
        self._create_filters(layout)
        self._create_table(layout)
        self._create_stats(layout)
        self._create_action_buttons(layout)

        main_layout.addWidget(content_widget)

    def _create_header(self, layout):
        if THEME_AVAILABLE:
            header_card = EmacCard()
            header_layout = QHBoxLayout()

            title = QLabel("Liste des formations")
            title.setFont(QFont("Segoe UI", 14, QFont.Bold))
            title.setStyleSheet("color: #1e293b;")
            header_layout.addWidget(title)
            header_layout.addStretch()

            btn_refresh = EmacButton("Actualiser", 'ghost')
            btn_refresh.clicked.connect(self.load_data)
            header_layout.addWidget(btn_refresh)

            btn_add = EmacButton("+ Nouvelle formation", 'primary')
            btn_add.clicked.connect(self.add_formation)
            header_layout.addWidget(btn_add)

            header_card.body.addLayout(header_layout)
            layout.addWidget(header_card)
        else:
            header_layout = QHBoxLayout()
            title = QLabel("Liste des formations")
            title.setFont(QFont("Arial", 12, QFont.Bold))
            header_layout.addWidget(title)
            header_layout.addStretch()

            btn_refresh = QPushButton("Actualiser")
            btn_refresh.clicked.connect(self.load_data)
            header_layout.addWidget(btn_refresh)

            btn_add = QPushButton("+ Nouvelle formation")
            btn_add.setStyleSheet("QPushButton { background-color: #3b82f6; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #2563eb; }")
            btn_add.clicked.connect(self.add_formation)
            header_layout.addWidget(btn_add)
            layout.addLayout(header_layout)

    def _create_filters(self, layout):
        field_style = "QComboBox, QLineEdit { padding: 6px 12px; border: 1px solid #cbd5e1; border-radius: 6px; background: white; }"

        if THEME_AVAILABLE:
            filters_card = EmacCard()
            filters_layout = QHBoxLayout()
        else:
            filters_group = QGroupBox("Filtres")
            filters_layout = QHBoxLayout()

        filters_layout.addWidget(QLabel("Employe:"))
        self.operateur_filter = QComboBox()
        self.operateur_filter.setMinimumWidth(200)
        self.operateur_filter.currentIndexChanged.connect(self.apply_filters)
        if THEME_AVAILABLE:
            self.operateur_filter.setStyleSheet(field_style)
        filters_layout.addWidget(self.operateur_filter)

        filters_layout.addSpacing(15)
        filters_layout.addWidget(QLabel("Statut:"))
        self.statut_filter = QComboBox()
        self.statut_filter.addItems(["Tous", "Planifiee", "En cours", "Terminee", "Annulee"])
        self.statut_filter.currentIndexChanged.connect(self.apply_filters)
        if THEME_AVAILABLE:
            self.statut_filter.setStyleSheet(field_style)
        filters_layout.addWidget(self.statut_filter)

        filters_layout.addSpacing(15)
        filters_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Intitule, organisme...")
        self.search_input.textChanged.connect(self.apply_filters)
        if THEME_AVAILABLE:
            self.search_input.setStyleSheet(field_style)
        filters_layout.addWidget(self.search_input)

        filters_layout.addStretch()

        if THEME_AVAILABLE:
            filters_card.body.addLayout(filters_layout)
            layout.addWidget(filters_card)
        else:
            filters_group.setLayout(filters_layout)
            layout.addWidget(filters_group)

    def _create_table(self, layout):
        if THEME_AVAILABLE:
            table_card = EmacCard()
            table_layout = QVBoxLayout()
        else:
            table_layout = layout

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "Employe", "Intitule", "Organisme", "Date debut",
            "Date fin", "Duree (h)", "Statut", "Certificat", "Attestation", "Cout"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)

        for col, w in [(0,50),(1,140),(2,180),(3,120),(4,90),(5,90),(6,60),(7,90),(8,70),(9,80),(10,70)]:
            self.table.setColumnWidth(col, w)

        self.table.setStyleSheet("""
            QTableWidget { background-color: white; alternate-background-color: #f8fafc;
                gridline-color: #e2e8f0; border: none; font-size: 11px; }
            QHeaderView::section { background: #f1f5f9; color: #475569; font-weight: bold;
                padding: 10px; border: none; border-bottom: 2px solid #cbd5e1; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #f1f5f9; }
            QTableWidget::item:selected { background: #dbeafe; color: #1e293b; }
        """)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.doubleClicked.connect(self.edit_formation)

        if THEME_AVAILABLE:
            table_layout.addWidget(self.table)
            table_card.body.addLayout(table_layout)
            layout.addWidget(table_card)
        else:
            layout.addWidget(self.table)

    def _create_stats(self, layout):
        if THEME_AVAILABLE:
            stats_card = EmacCard()
            stats_layout = QHBoxLayout()

            self.lbl_total = QLabel("Total : 0")
            self.lbl_total.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.lbl_total.setStyleSheet("color: #3b82f6;")
            stats_layout.addWidget(self.lbl_total)
            stats_layout.addSpacing(20)

            self.lbl_en_cours = QLabel("En cours : 0")
            self.lbl_en_cours.setStyleSheet("color: #f59e0b;")
            stats_layout.addWidget(self.lbl_en_cours)
            stats_layout.addSpacing(20)

            self.lbl_terminees = QLabel("Terminees : 0")
            self.lbl_terminees.setStyleSheet("color: #10b981;")
            stats_layout.addWidget(self.lbl_terminees)
            stats_layout.addSpacing(20)

            self.lbl_planifiees = QLabel("Planifiees : 0")
            self.lbl_planifiees.setStyleSheet("color: #64748b;")
            stats_layout.addWidget(self.lbl_planifiees)

            stats_layout.addStretch()
            stats_card.body.addLayout(stats_layout)
            layout.addWidget(stats_card)
        else:
            stats_layout = QHBoxLayout()
            self.lbl_total = QLabel("Total : 0")
            self.lbl_total.setFont(QFont("Arial", 9, QFont.Bold))
            stats_layout.addWidget(self.lbl_total)
            self.lbl_en_cours = QLabel("En cours : 0")
            stats_layout.addWidget(self.lbl_en_cours)
            self.lbl_terminees = QLabel("Terminees : 0")
            stats_layout.addWidget(self.lbl_terminees)
            self.lbl_planifiees = QLabel("Planifiees : 0")
            stats_layout.addWidget(self.lbl_planifiees)
            stats_layout.addStretch()
            layout.addLayout(stats_layout)

    def _create_action_buttons(self, layout):
        btn_layout = QHBoxLayout()

        if THEME_AVAILABLE:
            btn_edit = EmacButton("Modifier", 'ghost')
            btn_edit.clicked.connect(self.edit_formation)
            btn_layout.addWidget(btn_edit)

            btn_docs = EmacButton("Generer documents", 'secondary')
            btn_docs.clicked.connect(self.generate_documents)
            btn_layout.addWidget(btn_docs)

            btn_delete = EmacButton("Supprimer", 'ghost')
            btn_delete.setStyleSheet("QPushButton { color: #dc2626; border: 1px solid #dc2626; } QPushButton:hover { background-color: #fef2f2; }")
            btn_delete.clicked.connect(self.delete_formation)
            btn_layout.addWidget(btn_delete)

            btn_layout.addStretch()

            btn_close = EmacButton("Fermer", 'ghost')
            btn_close.clicked.connect(self.accept)
            btn_layout.addWidget(btn_close)
        else:
            btn_edit = QPushButton("Modifier")
            btn_edit.clicked.connect(self.edit_formation)
            btn_layout.addWidget(btn_edit)

            btn_docs = QPushButton("Generer documents")
            btn_docs.setStyleSheet("QPushButton { background-color: #10b981; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px; } QPushButton:hover { background-color: #059669; }")
            btn_docs.clicked.connect(self.generate_documents)
            btn_layout.addWidget(btn_docs)

            btn_delete = QPushButton("Supprimer")
            btn_delete.setStyleSheet("color: #dc2626;")
            btn_delete.clicked.connect(self.delete_formation)
            btn_layout.addWidget(btn_delete)

            btn_layout.addStretch()

            btn_close = QPushButton("Fermer")
            btn_close.clicked.connect(self.accept)
            btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _connect_viewmodel(self):
        self._vm.personnel_loaded.connect(self._on_personnel_loaded)
        self._vm.formations_loaded.connect(self._on_formations_loaded)
        self._vm.stats_loaded.connect(self._on_stats_loaded)
        self._vm.formation_loaded.connect(self._on_formation_loaded)
        self._vm.action_succeeded.connect(self._on_action_succeeded)
        self._vm.error_occurred.connect(lambda msg: QMessageBox.critical(self, "Erreur", msg))
        self._vm.dossier_generated.connect(self._on_dossier_generated)
        self._vm.document_path_ready.connect(lambda path: self._vm.open_file(path))
        self._vm.data_changed.connect(lambda: (self.load_data(), self.data_changed.emit()))

    def load_data(self):
        self._vm.load_personnel()
        self.apply_filters()
        self._vm.load_stats()

    def _on_personnel_loaded(self, operateurs: list):
        self.operateur_filter.blockSignals(True)
        self.operateur_filter.clear()
        self.operateur_filter.addItem("Tous les employes", None)
        for op in operateurs:
            self.operateur_filter.addItem(f"{op['nom_complet']} ({op['matricule']})", op['id'])
        self.operateur_filter.blockSignals(False)

    def _on_formations_loaded(self, formations: list):
        self.table.setRowCount(len(formations))
        for row, formation in enumerate(formations):
            self.table.setItem(row, 0, QTableWidgetItem(str(formation['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(formation.get('nom_complet', '')))
            self.table.setItem(row, 2, QTableWidgetItem(formation.get('intitule', '')))
            self.table.setItem(row, 3, QTableWidgetItem(formation.get('organisme') or ''))

            for col, key in [(4, 'date_debut'), (5, 'date_fin')]:
                val = formation.get(key)
                if val:
                    self.table.setItem(row, col, QTableWidgetItem(val if isinstance(val, str) else format_date(val)))
                else:
                    self.table.setItem(row, col, QTableWidgetItem(''))

            duree = formation.get('duree_heures')
            self.table.setItem(row, 6, QTableWidgetItem(f"{duree:.1f}" if duree else ''))

            statut_val = formation.get('statut', '')
            statut_item = QTableWidgetItem(statut_val)
            color_map = {
                'Terminee': '#10b981', 'Terminée': '#10b981',
                'En cours': '#f59e0b',
                'Annulee': '#dc2626', 'Annulée': '#dc2626',
            }
            statut_item.setForeground(QColor(color_map.get(statut_val, '#64748b')))
            self.table.setItem(row, 7, statut_item)

            cert = formation.get('certificat_obtenu', False)
            cert_item = QTableWidgetItem("Oui" if cert else "Non")
            if cert:
                cert_item.setForeground(QColor('#10b981'))
            self.table.setItem(row, 8, cert_item)

            attestation_nom = formation.get('attestation_nom')
            if attestation_nom:
                att_item = QTableWidgetItem("📄 Oui")
                att_item.setForeground(QColor('#10b981'))
                att_item.setToolTip(attestation_nom)
            else:
                att_item = QTableWidgetItem("-")
                att_item.setForeground(QColor('#94a3b8'))
            self.table.setItem(row, 9, att_item)

            cout = formation.get('cout')
            self.table.setItem(row, 10, QTableWidgetItem(f"{cout:.2f} EUR" if cout else ''))

    def _on_stats_loaded(self, stats: dict):
        self.lbl_total.setText(f"Total : {stats.get('total', 0)}")
        self.lbl_en_cours.setText(f"En cours : {stats.get('en_cours', 0)}")
        self.lbl_terminees.setText(f"Terminees : {stats.get('terminees_cette_annee', 0)}")
        self.lbl_planifiees.setText(f"Planifiees : {stats.get('planifiees', 0)}")

    def _on_action_succeeded(self, msg: str):
        QMessageBox.information(self, "Succès", msg)

    def _on_dossier_generated(self, success: bool, msg: str, path: str):
        if success and path:
            reply = QMessageBox.information(
                self, "Documents générés",
                f"Dossier de formation généré :\n{path}\n\nOuvrir le fichier ?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._vm.open_file(path)
        else:
            QMessageBox.warning(self, "Génération échouée", msg)

    def _on_formation_loaded(self, formation: dict):
        if '_saved_id' in formation:
            return
        from gui.screens.formation.gestion_formations.add_edit_formation_dialog import AddEditFormationDialog
        dialog = AddEditFormationDialog(formation=formation, vm=self._vm, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def apply_filters(self):
        operateur_id = self.operateur_filter.currentData()
        statut_text = self.statut_filter.currentText()
        statut = None if statut_text == "Tous" else statut_text
        search = self.search_input.text().strip() or None
        self._vm.load_formations(operateur_id=operateur_id, statut=statut, search=search)

    def show_context_menu(self, position):
        if self.table.selectedItems():
            menu = QMenu()
            menu.addAction("Modifier", self.edit_formation)
            menu.addSeparator()
            menu.addAction("Generer les documents", self.generate_documents)
            menu.addSeparator()
            menu.addAction("Supprimer", self.delete_formation)
            menu.exec_(self.table.viewport().mapToGlobal(position))

    def get_selected_formation_id(self):
        selected = self.table.selectedItems()
        if selected:
            id_item = self.table.item(selected[0].row(), 0)
            if id_item:
                return int(id_item.text())
        return None

    def add_formation(self):
        from gui.screens.formation.gestion_formations.add_edit_formation_dialog import AddEditFormationDialog
        dialog = AddEditFormationDialog(vm=self._vm, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def edit_formation(self):
        formation_id = self.get_selected_formation_id()
        if not formation_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une formation.")
            return
        self._vm.load_formation(formation_id)

    def generate_documents(self):
        formation_id = self.get_selected_formation_id()
        if not formation_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une formation.")
            return
        self._vm.generate_dossier(formation_id)

    def delete_formation(self):
        formation_id = self.get_selected_formation_id()
        if not formation_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une formation.")
            return
        reply = QMessageBox.question(
            self, "Confirmation",
            "Etes-vous sûr de vouloir supprimer cette formation ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._vm.delete_formation(formation_id)
