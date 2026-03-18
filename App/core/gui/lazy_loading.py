# -*- coding: utf-8 -*-
"""
Module de composants pour le lazy-loading et la pagination.

Fournit des widgets optimisés pour charger les données à la demande,
réduisant le temps de démarrage et l'utilisation mémoire.

Usage:
    from core.gui.lazy_loading import LazyTabWidget, PaginatedTableWidget

    # Onglets lazy-loaded
    tabs = LazyTabWidget()
    tabs.add_lazy_tab("Personnel", lambda: PersonnelTab())
    tabs.add_lazy_tab("Contrats", lambda: ContratsTab())

    # Table avec pagination
    table = PaginatedTableWidget(
        fetch_fn=lambda offset, limit: PersonnelRepository.get_paginated(offset, limit),
        columns=["Nom", "Prénom", "Statut"],
        page_size=50
    )
"""

import logging
from typing import Callable, Optional, List, Dict, Any, Tuple
from PyQt5.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QAbstractItemView, QFrame, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

logger = logging.getLogger(__name__)


# ===========================
# Lazy Tab Widget
# ===========================

class LazyTabWidget(QTabWidget):
    """
    QTabWidget avec chargement différé des onglets.

    Les onglets sont créés uniquement lorsque l'utilisateur clique dessus
    pour la première fois, réduisant le temps de démarrage.

    Usage:
        tabs = LazyTabWidget()

        # Ajouter un onglet lazy (la factory n'est appelée qu'au premier clic)
        tabs.add_lazy_tab("Personnel", lambda: PersonnelWidget())
        tabs.add_lazy_tab("Contrats", lambda: ContratsWidget(parent=self))

        # Onglet normal (créé immédiatement)
        tabs.addTab(MyWidget(), "Déjà chargé")

        # Forcer le chargement d'un onglet
        tabs.load_tab(0)
    """

    # Signal émis quand un onglet est chargé pour la première fois
    tab_loaded = pyqtSignal(int, str)  # (index, nom_onglet)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Factories pour créer les onglets à la demande
        self._factories: Dict[int, Callable[[], QWidget]] = {}

        # Onglets déjà chargés
        self._loaded: set = set()

        # Placeholders
        self._placeholders: Dict[int, QWidget] = {}

        # Connecter le signal de changement d'onglet
        self.currentChanged.connect(self._on_tab_changed)

    def add_lazy_tab(self, title: str, factory: Callable[[], QWidget],
                     icon=None) -> int:
        """
        Ajoute un onglet lazy-loaded.

        Args:
            title: Titre de l'onglet
            factory: Fonction qui retourne le widget à afficher
            icon: Icône optionnelle

        Returns:
            Index de l'onglet ajouté
        """
        # Créer un placeholder léger
        placeholder = self._create_placeholder(title)

        if icon:
            index = self.addTab(placeholder, icon, title)
        else:
            index = self.addTab(placeholder, title)

        # Stocker la factory et le placeholder
        self._factories[index] = factory
        self._placeholders[index] = placeholder

        return index

    def _create_placeholder(self, title: str) -> QWidget:
        """Crée un widget placeholder léger."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(f"Chargement de {title}...")
        label.setStyleSheet("color: #6b7280; font-size: 14px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        return widget

    def _on_tab_changed(self, index: int):
        """Charge l'onglet s'il n'est pas encore chargé."""
        if index in self._factories and index not in self._loaded:
            # Charger en différé pour permettre l'animation de l'onglet
            QTimer.singleShot(10, lambda: self._load_tab(index))

    def _load_tab(self, index: int):
        """Charge réellement l'onglet."""
        if index not in self._factories or index in self._loaded:
            return

        try:
            # Créer le widget via la factory
            factory = self._factories[index]
            widget = factory()

            # Remplacer le placeholder
            title = self.tabText(index)
            icon = self.tabIcon(index)

            self.removeTab(index)

            if icon and not icon.isNull():
                self.insertTab(index, widget, icon, title)
            else:
                self.insertTab(index, widget, title)

            # Marquer comme chargé
            self._loaded.add(index)
            self.setCurrentIndex(index)

            # Émettre le signal
            self.tab_loaded.emit(index, title)

            logger.debug(f"Onglet '{title}' chargé (index {index})")

        except Exception as e:
            logger.error(f"Erreur chargement onglet {index}: {e}")
            # Afficher l'erreur dans le placeholder
            if index in self._placeholders:
                placeholder = self._placeholders[index]
                for child in placeholder.findChildren(QLabel):
                    child.setText(f"Erreur: {e}")
                    child.setStyleSheet("color: #dc2626;")

    def load_tab(self, index: int):
        """Force le chargement d'un onglet."""
        self._load_tab(index)

    def is_loaded(self, index: int) -> bool:
        """Vérifie si un onglet est chargé."""
        return index in self._loaded

    def preload_all(self):
        """Précharge tous les onglets (en background)."""
        for index in self._factories.keys():
            if index not in self._loaded:
                QTimer.singleShot(100 * index, lambda i=index: self._load_tab(i))


# ===========================
# Paginated Table Widget
# ===========================

class PaginatedTableWidget(QWidget):
    """
    Table avec pagination intégrée.

    Charge les données par pages pour éviter de charger des milliers
    de lignes en mémoire.

    Usage:
        def fetch_data(offset, limit, filters):
            # Retourne (rows, total_count)
            return PersonnelRepository.get_paginated(offset, limit, **filters)

        table = PaginatedTableWidget(
            fetch_fn=fetch_data,
            columns=["Nom", "Prénom", "Statut", "Postes"],
            page_size=50
        )

        # Appliquer des filtres
        table.set_filters({"statut": "ACTIF"})

        # Rafraîchir
        table.refresh()
    """

    # Signal émis quand une ligne est double-cliquée
    row_double_clicked = pyqtSignal(int, dict)  # (row_index, row_data)

    # Signal émis quand la sélection change
    selection_changed = pyqtSignal(list)  # [row_data, ...]

    # Signal émis quand les données sont chargées
    data_loaded = pyqtSignal(int, int)  # (page, total)

    def __init__(self, fetch_fn: Callable, columns: List[str],
                 page_size: int = 50, parent=None):
        """
        Args:
            fetch_fn: Fonction (offset, limit, filters) -> (rows, total_count)
            columns: Liste des noms de colonnes
            page_size: Nombre de lignes par page
        """
        super().__init__(parent)

        self.fetch_fn = fetch_fn
        self.columns = columns
        self.page_size = page_size

        # État
        self.current_page = 0
        self.total_rows = 0
        self.total_pages = 0
        self.filters: Dict[str, Any] = {}
        self._data_cache: List[Dict] = []

        self._setup_ui()

    def _setup_ui(self):
        """Construit l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_double_click)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.table, 1)

        # Barre de pagination
        pagination = QFrame()
        pagination.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 4px;
            }
        """)

        pag_layout = QHBoxLayout(pagination)
        pag_layout.setContentsMargins(8, 4, 8, 4)
        pag_layout.setSpacing(12)

        # Bouton première page
        self.btn_first = QPushButton("⏮")
        self.btn_first.setFixedWidth(32)
        self.btn_first.setToolTip("Première page")
        self.btn_first.clicked.connect(self.go_first)
        pag_layout.addWidget(self.btn_first)

        # Bouton précédent
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedWidth(32)
        self.btn_prev.setToolTip("Page précédente")
        self.btn_prev.clicked.connect(self.go_previous)
        pag_layout.addWidget(self.btn_prev)

        # Indicateur de page
        self.page_label = QLabel("Page 1 / 1")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setMinimumWidth(100)
        pag_layout.addWidget(self.page_label)

        # Bouton suivant
        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedWidth(32)
        self.btn_next.setToolTip("Page suivante")
        self.btn_next.clicked.connect(self.go_next)
        pag_layout.addWidget(self.btn_next)

        # Bouton dernière page
        self.btn_last = QPushButton("⏭")
        self.btn_last.setFixedWidth(32)
        self.btn_last.setToolTip("Dernière page")
        self.btn_last.clicked.connect(self.go_last)
        pag_layout.addWidget(self.btn_last)

        pag_layout.addStretch()

        # Sélecteur de taille de page
        pag_layout.addWidget(QLabel("Lignes:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["25", "50", "100", "200"])
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        pag_layout.addWidget(self.page_size_combo)

        # Total
        self.total_label = QLabel("0 résultats")
        self.total_label.setStyleSheet("color: #6b7280;")
        pag_layout.addWidget(self.total_label)

        layout.addWidget(pagination)

    def _on_page_size_changed(self, value: str):
        """Change la taille de page."""
        self.page_size = int(value)
        self.current_page = 0
        self.refresh()

    def _update_pagination_ui(self):
        """Met à jour les boutons de pagination."""
        self.total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)

        self.page_label.setText(f"Page {self.current_page + 1} / {self.total_pages}")
        self.total_label.setText(f"{self.total_rows} résultats")

        # Activer/désactiver les boutons
        self.btn_first.setEnabled(self.current_page > 0)
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < self.total_pages - 1)
        self.btn_last.setEnabled(self.current_page < self.total_pages - 1)

    def set_filters(self, filters: Dict[str, Any]):
        """Définit les filtres et rafraîchit."""
        self.filters = filters
        self.current_page = 0
        self.refresh()

    def refresh(self):
        """Recharge les données de la page courante."""
        try:
            offset = self.current_page * self.page_size

            # Appeler la fonction de fetch
            result = self.fetch_fn(offset, self.page_size, self.filters)

            if isinstance(result, tuple) and len(result) == 2:
                rows, total = result
            else:
                rows = result
                total = len(rows)

            self._data_cache = rows
            self.total_rows = total

            self._populate_table(rows)
            self._update_pagination_ui()

            self.data_loaded.emit(self.current_page, total)

        except Exception as e:
            logger.error(f"Erreur chargement données: {e}")
            self.table.setRowCount(0)
            self.total_label.setText(f"Erreur: {e}")

    def _populate_table(self, rows: List[Dict]):
        """Remplit la table avec les données."""
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            for col_idx, col_name in enumerate(self.columns):
                # Chercher la valeur (nom de colonne ou clé dict)
                value = row_data.get(col_name) or row_data.get(col_name.lower(), "")

                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setData(Qt.UserRole, row_data)  # Stocker les données complètes
                self.table.setItem(row_idx, col_idx, item)

    def _on_double_click(self, index):
        """Émet le signal de double-clic."""
        row = index.row()
        if row < len(self._data_cache):
            self.row_double_clicked.emit(row, self._data_cache[row])

    def _on_selection_changed(self):
        """Émet le signal de changement de sélection."""
        selected_rows = []
        for item in self.table.selectedItems():
            if item.column() == 0:  # Première colonne seulement
                data = item.data(Qt.UserRole)
                if data:
                    selected_rows.append(data)
        self.selection_changed.emit(selected_rows)

    def get_selected_rows(self) -> List[Dict]:
        """Retourne les données des lignes sélectionnées."""
        selected = []
        for row in set(item.row() for item in self.table.selectedItems()):
            if row < len(self._data_cache):
                selected.append(self._data_cache[row])
        return selected

    # Navigation
    def go_first(self):
        self.current_page = 0
        self.refresh()

    def go_previous(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def go_next(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.refresh()

    def go_last(self):
        self.current_page = self.total_pages - 1
        self.refresh()


# ===========================
# Load More Widget
# ===========================

class LoadMoreListWidget(QWidget):
    """
    Liste avec chargement incrémental "Load More".

    Charge un nombre initial d'éléments puis permet d'en charger plus
    avec un bouton "Charger plus".

    Usage:
        def fetch_items(offset, limit):
            return PersonnelRepository.search(query, offset=offset, limit=limit)

        list_widget = LoadMoreListWidget(
            fetch_fn=fetch_items,
            render_fn=lambda item: f"{item['nom']} {item['prenom']}",
            initial_count=20,
            load_more_count=20
        )
    """

    item_clicked = pyqtSignal(dict)

    def __init__(self, fetch_fn: Callable, render_fn: Callable[[Dict], str],
                 initial_count: int = 20, load_more_count: int = 20,
                 parent=None):
        super().__init__(parent)

        self.fetch_fn = fetch_fn
        self.render_fn = render_fn
        self.initial_count = initial_count
        self.load_more_count = load_more_count

        self._items: List[Dict] = []
        self._offset = 0
        self._has_more = True

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Liste
        from PyQt5.QtWidgets import QListWidget
        self.list = QListWidget()
        self.list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list, 1)

        # Bouton "Charger plus"
        self.btn_load_more = QPushButton("Charger plus...")
        self.btn_load_more.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 8px;
                color: #475569;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        self.btn_load_more.clicked.connect(self.load_more)
        self.btn_load_more.hide()
        layout.addWidget(self.btn_load_more)

    def load_initial(self):
        """Charge les éléments initiaux."""
        self._items = []
        self._offset = 0
        self._has_more = True
        self.list.clear()
        self._load_batch(self.initial_count)

    def load_more(self):
        """Charge plus d'éléments."""
        self._load_batch(self.load_more_count)

    def _load_batch(self, count: int):
        """Charge un batch d'éléments."""
        try:
            items = self.fetch_fn(self._offset, count)

            if not items or len(items) < count:
                self._has_more = False

            for item in items:
                self._items.append(item)
                text = self.render_fn(item)
                list_item = self.list.addItem(text)

            self._offset += len(items)
            self.btn_load_more.setVisible(self._has_more)

        except Exception as e:
            logger.error(f"Erreur load_batch: {e}")

    def _on_item_clicked(self, item):
        row = self.list.row(item)
        if row < len(self._items):
            self.item_clicked.emit(self._items[row])

    def clear(self):
        """Vide la liste."""
        self._items = []
        self._offset = 0
        self._has_more = True
        self.list.clear()
        self.btn_load_more.hide()
