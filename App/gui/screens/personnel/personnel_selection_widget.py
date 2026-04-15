# -*- coding: utf-8 -*-
"""
Widget réutilisable de sélection multiple du personnel.
"""

from typing import List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from domain.repositories.personnel_repo import PersonnelRepository
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class PersonnelSelectionWidget(QWidget):
    """
    Widget réutilisable pour la sélection multiple de personnel.
    Utilise QTableWidget avec checkboxes.
    """

    selection_changed = pyqtSignal(list)  # Émis quand la sélection change

    def __init__(self, parent=None):
        super().__init__(parent)
        self._personnel_data = []
        self._setup_ui()
        self._load_personnel()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === Filtres ===
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(12)

        # Recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un employé...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 13px;
                background: white;
                color: #111827;
            }
            QLineEdit:focus {
                border: 2px solid #7c3aed;
                padding: 7px 11px;
            }
        """)
        self.search_input.textChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.search_input, 2)

        # Filtre statut
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tous", "TOUS")
        self.status_combo.addItem("Actifs", "ACTIF")
        self.status_combo.addItem("Inactifs", "INACTIF")
        self.status_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 13px;
                background: white;
                color: #111827;
                min-width: 100px;
            }
            QComboBox:focus {
                border: 2px solid #7c3aed;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
        """)
        self.status_combo.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.status_combo, 1)

        # Filtre service
        self.service_combo = QComboBox()
        self.service_combo.addItem("Tous les services", None)
        self.service_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 13px;
                background: white;
                color: #111827;
                min-width: 140px;
            }
            QComboBox:focus {
                border: 2px solid #7c3aed;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
        """)
        self.service_combo.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.service_combo, 1)

        layout.addLayout(filters_layout)

        # === Table du personnel ===
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "Nom", "Prénom", "Matricule", "Statut"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                gridline-color: #f3f4f6;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 6px 8px;
            }
            QTableWidget::item:selected {
                background: #ede9fe;
                color: #5b21b6;
            }
            QHeaderView::section {
                background: #f9fafb;
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                font-weight: bold;
                color: #374151;
            }
        """)
        layout.addWidget(self.table, 1)

        # === Boutons d'action ===
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        btn_select_all = QPushButton("Tout sélectionner")
        btn_select_all.setCursor(Qt.PointingHandCursor)
        btn_select_all.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                padding: 6px 14px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e5e7eb;
                border-color: #9ca3af;
            }
        """)
        btn_select_all.clicked.connect(self._select_all)
        actions_layout.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("Tout désélectionner")
        btn_deselect_all.setCursor(Qt.PointingHandCursor)
        btn_deselect_all.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                padding: 6px 14px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e5e7eb;
                border-color: #9ca3af;
            }
        """)
        btn_deselect_all.clicked.connect(self._deselect_all)
        actions_layout.addWidget(btn_deselect_all)

        actions_layout.addStretch()

        self.count_label = QLabel("Sélectionnés: 0")
        self.count_label.setStyleSheet("""
            font-weight: bold;
            color: #7c3aed;
            font-size: 13px;
            padding: 4px 12px;
            background: #ede9fe;
            border-radius: 12px;
        """)
        actions_layout.addWidget(self.count_label)

        layout.addLayout(actions_layout)

    def _load_personnel(self):
        """Charge la liste du personnel depuis la base de données."""
        try:
            self._personnel_data = PersonnelRepository.get_all_as_dicts()
            self._populate_service_combo()
            self._populate_table()
        except Exception as e:
            logger.error(f"Erreur chargement personnel: {e}")

    def _populate_service_combo(self):
        """Remplit le combo des services à partir des données chargées."""
        services = sorted(
            {p['nom_service'] for p in self._personnel_data if p.get('nom_service')}
        )
        self.service_combo.blockSignals(True)
        self.service_combo.clear()
        self.service_combo.addItem("Tous les services", None)
        for svc in services:
            self.service_combo.addItem(svc, svc)
        self.service_combo.blockSignals(False)

    def _populate_table(self):
        """Remplit la table avec les données."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for row_data in self._personnel_data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Checkbox
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            checkbox.setCheckState(Qt.Unchecked)
            checkbox.setData(Qt.UserRole, row_data['id'])
            self.table.setItem(row, 0, checkbox)

            # Données (non éditables)
            nom_item = QTableWidgetItem(row_data.get('nom', ''))
            nom_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 1, nom_item)

            prenom_item = QTableWidgetItem(row_data.get('prenom', ''))
            prenom_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 2, prenom_item)

            matricule_item = QTableWidgetItem(row_data.get('matricule', ''))
            matricule_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 3, matricule_item)

            statut = row_data.get('statut', '')
            statut_item = QTableWidgetItem(statut)
            if statut == 'ACTIF':
                statut_item.setForeground(QColor('#2e7d32'))
            else:
                statut_item.setForeground(QColor('#c62828'))
            self.table.setItem(row, 4, statut_item)

        self.table.blockSignals(False)
        self._apply_filters()

    def _apply_filters(self):
        """Applique les filtres de recherche, statut et service."""
        search_text = self.search_input.text().lower()
        status_filter = self.status_combo.currentData()
        service_filter = self.service_combo.currentData()

        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            personnel_id = checkbox_item.data(Qt.UserRole) if checkbox_item else None
            row_data = next((p for p in self._personnel_data if p['id'] == personnel_id), {})

            nom = (row_data.get('nom') or '').lower()
            prenom = (row_data.get('prenom') or '').lower()
            matricule = (row_data.get('matricule') or '').lower()
            statut = row_data.get('statut') or ''
            nom_service = row_data.get('nom_service') or ''

            match_search = (
                search_text in nom or
                search_text in prenom or
                search_text in matricule
            )
            match_status = status_filter == "TOUS" or statut == status_filter
            match_service = service_filter is None or nom_service == service_filter

            self.table.setRowHidden(row, not (match_search and match_status and match_service))

        selected_ids = self.get_selected_ids()
        self._update_count_with_ids(selected_ids)
        self.selection_changed.emit(selected_ids)

    def _on_item_changed(self, item):
        """Appelé quand un item change (checkbox)."""
        if item.column() == 0:
            selected_ids = self.get_selected_ids()
            self._update_count_with_ids(selected_ids)
            self.selection_changed.emit(selected_ids)

    def _select_all(self):
        """Sélectionne tous les éléments visibles."""
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                item = self.table.item(row, 0)
                if item:
                    item.setCheckState(Qt.Checked)
        self.table.blockSignals(False)
        selected_ids = self.get_selected_ids()
        self._update_count_with_ids(selected_ids)
        self.selection_changed.emit(selected_ids)

    def _deselect_all(self):
        """Désélectionne tous les éléments."""
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.Unchecked)
        self.table.blockSignals(False)
        selected_ids = self.get_selected_ids()
        self._update_count_with_ids(selected_ids)
        self.selection_changed.emit(selected_ids)

    def _update_count_with_ids(self, selected_ids: List[int]):
        """Met à jour le compteur avec une liste d'IDs fournie."""
        count = len(selected_ids)
        visible_count = sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))
        self.count_label.setText(f"Sélectionnés: {count} / {visible_count}")

    def get_selected_ids(self) -> List[int]:
        """Retourne les IDs des personnels sélectionnés."""
        selected = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked and not self.table.isRowHidden(row):
                personnel_id = item.data(Qt.UserRole)
                if personnel_id:
                    selected.append(personnel_id)
        return selected

    def get_selected_count(self) -> int:
        """Retourne le nombre de personnels sélectionnés."""
        return len(self.get_selected_ids())
