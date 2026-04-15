# -*- coding: utf-8 -*-
"""
Dialogue de filtrage de la grille de polyvalence.
Sélection multi-critères : opérateurs et/ou postes.
"""

from typing import Dict, List, Optional, Set, Tuple

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QLineEdit, QWidget,
)
from PyQt5.QtCore import Qt


class GrillesFilterDialog(QDialog):
    """Dialogue de sélection des opérateurs et postes à afficher dans la grille."""

    def __init__(
        self,
        operateurs: List[Tuple[int, str]],
        postes: List[Tuple[int, str]],
        hidden_rows: Set[int],
        hidden_cols: Set[int],
        parent=None,
    ):
        """
        Args:
            operateurs: list[(id, nom_complet)] dans l'ordre d'affichage.
            postes: list[(id, poste_code)] dans l'ordre d'affichage.
            hidden_rows: ensemble des index de lignes actuellement masquées.
            hidden_cols: ensemble des index de colonnes actuellement masquées.
        """
        super().__init__(parent)
        self.setWindowTitle("Filtrer la grille")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        self._operateurs = operateurs
        self._postes = postes
        self._hidden_rows = hidden_rows
        self._hidden_cols = hidden_cols

        self._ops_list: Optional[QListWidget] = None
        self._postes_list: Optional[QListWidget] = None

        self._setup_ui()

    # ------------------------------------------------------------------ #
    # Construction UI                                                      #
    # ------------------------------------------------------------------ #

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        content = QHBoxLayout()

        content.addWidget(self._build_ops_panel())
        content.addWidget(self._build_postes_panel())
        layout.addLayout(content)
        layout.addLayout(self._build_buttons())

    def _build_ops_panel(self) -> QWidget:
        widget = QWidget()
        vbox = QVBoxLayout(widget)

        header = QLabel("Opérateurs")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        vbox.addWidget(header)

        ops_search = QLineEdit()
        ops_search.setPlaceholderText("Rechercher un opérateur...")
        vbox.addWidget(ops_search)

        self._ops_list = QListWidget()
        self._ops_list.setSelectionMode(QListWidget.MultiSelection)
        for idx, (op_id, op_name) in enumerate(self._operateurs):
            item = QListWidgetItem(op_name)
            item.setData(Qt.UserRole, idx)
            item.setSelected(idx not in self._hidden_rows)
            self._ops_list.addItem(item)

        ops_search.textChanged.connect(lambda t: self._filter_list(self._ops_list, t))
        vbox.addWidget(self._ops_list)
        return widget

    def _build_postes_panel(self) -> QWidget:
        widget = QWidget()
        vbox = QVBoxLayout(widget)

        header = QLabel("Postes")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        vbox.addWidget(header)

        postes_search = QLineEdit()
        postes_search.setPlaceholderText("Rechercher un poste...")
        vbox.addWidget(postes_search)

        self._postes_list = QListWidget()
        self._postes_list.setSelectionMode(QListWidget.MultiSelection)
        for idx, (poste_id, poste_code) in enumerate(self._postes):
            item = QListWidgetItem(poste_code)
            item.setData(Qt.UserRole, idx)
            item.setSelected(idx not in self._hidden_cols)
            self._postes_list.addItem(item)

        postes_search.textChanged.connect(lambda t: self._filter_list(self._postes_list, t))
        vbox.addWidget(self._postes_list)
        return widget

    def _build_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        btn_apply = QPushButton("Appliquer")
        btn_apply.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 8px; font-weight: bold;"
        )
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setStyleSheet("padding: 8px;")

        btn_apply.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        layout.addStretch()
        layout.addWidget(btn_apply)
        layout.addWidget(btn_cancel)
        return layout

    # ------------------------------------------------------------------ #
    # Logique de filtrage (utilitaire)                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _filter_list(list_widget: QListWidget, text: str) -> None:
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    # ------------------------------------------------------------------ #
    # Résultats                                                            #
    # ------------------------------------------------------------------ #

    def get_selected_op_rows(self) -> List[int]:
        """Retourne les index de lignes sélectionnées (opérateurs visibles)."""
        return [
            item.data(Qt.UserRole)
            for item in self._ops_list.selectedItems()
        ]

    def get_selected_poste_cols(self) -> List[int]:
        """Retourne les index de colonnes sélectionnées (postes visibles)."""
        return [
            item.data(Qt.UserRole)
            for item in self._postes_list.selectedItems()
        ]
