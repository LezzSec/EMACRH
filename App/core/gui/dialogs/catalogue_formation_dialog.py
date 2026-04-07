# -*- coding: utf-8 -*-
"""
Dialog de consultation et gestion du catalogue des formations.
Permet de feuilleter, rechercher et administrer les libellés officiels.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QWidget, QMessageBox, QSpinBox,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from core.services.formation_service_crud import FormationServiceCRUD
from core.gui.workers.lazy_loading import PaginatedTableWidget
from core.gui.components.emac_ui_kit import add_custom_title_bar, show_error_message
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

from core.gui.components.ui_theme import EmacButton, EmacCard

THEME_AVAILABLE = True  # toujours disponible — conservé pour compat branches existantes


def _btn(label, style='primary'):
    return EmacButton(label, style)


class CatalogueFormationDialog(QDialog):
    """
    Dialog feuilletable du catalogue des formations.
    Utilisable en mode consultation ou en mode sélection (signal entry_selected).
    """

    entry_selected = pyqtSignal(dict)  # émis quand l'utilisateur choisit une entrée

    def __init__(self, parent=None, selection_mode=False):
        super().__init__(parent)
        self._selection_mode = selection_mode
        self.setWindowTitle("Catalogue des formations")
        self.setMinimumSize(900, 600)
        self._init_ui()
        QTimer.singleShot(100, self._table.refresh)

    # ------------------------------------------------------------------
    # Construction UI
    # ------------------------------------------------------------------

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(add_custom_title_bar(self, "Catalogue des formations"))

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        layout.addLayout(self._build_filters())
        layout.addWidget(self._build_table())
        layout.addLayout(self._build_actions())

        main_layout.addWidget(content)

    def _build_filters(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        # Recherche texte
        self._search = QLineEdit()
        self._search.setPlaceholderText("Rechercher un libellé...")
        self._search.setMinimumWidth(250)
        self._search.textChanged.connect(self._on_filter_changed)
        row.addWidget(QLabel("Recherche :"))
        row.addWidget(self._search)

        # Filtre tranche
        self._combo_tranche = QComboBox()
        self._combo_tranche.setMinimumWidth(220)
        self._combo_tranche.addItem("Toutes les tranches", None)
        for t in FormationServiceCRUD.get_tranches():
            label = f"{t['tranche_min']} – {t['libelle']}"
            self._combo_tranche.addItem(label, t['tranche_min'])
        self._combo_tranche.currentIndexChanged.connect(self._on_filter_changed)
        row.addWidget(QLabel("Tranche :"))
        row.addWidget(self._combo_tranche)

        row.addStretch()

        btn_add = _btn("+ Ajouter", 'primary')
        btn_add.clicked.connect(self._add_entry)
        row.addWidget(btn_add)

        return row

    def _build_table(self):
        self._table = PaginatedTableWidget(
            fetch_fn=self._fetch,
            columns=["Code", "Libellé", "Tranche"],
            page_size=25,
        )
        self._table.setMinimumHeight(400)

        # Largeurs colonnes appliquées après création via signal
        self._table.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        if self._selection_mode:
            self._table.row_double_clicked.connect(self._on_select)

        return self._table

    def _build_actions(self):
        row = QHBoxLayout()
        row.addStretch()

        if self._selection_mode:
            btn_select = _btn("Sélectionner", 'primary')
            btn_select.clicked.connect(self._select_current)
            row.addWidget(btn_select)

        btn_close = _btn("Fermer", 'ghost')
        btn_close.clicked.connect(self.reject)
        row.addWidget(btn_close)

        return row

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------

    def _fetch(self, offset: int, limit: int, filters: dict):
        query = filters.get('search', '')
        tranche_min = filters.get('tranche_min')

        rows = FormationServiceCRUD.search_catalogue(query=query, code=tranche_min)
        total = len(rows)
        page = rows[offset:offset + limit]

        table_rows = [
            {
                'Code': str(r['code']),
                'Libellé': r['intitule'],
                'Tranche': r.get('libelle_tranche', ''),
                '_raw': r,
            }
            for r in page
        ]
        return table_rows, total

    def _on_filter_changed(self):
        self._table.set_filters({
            'search': self._search.text().strip(),
            'tranche_min': self._combo_tranche.currentData(),
        })

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _add_entry(self):
        dlg = _AddEntryDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._table.refresh()

    def _on_select(self, _row_index, row_data):
        self.entry_selected.emit(row_data.get('_raw', {}))
        self.accept()

    def _select_current(self):
        selected = self._table.get_selected_rows()
        if not selected:
            QMessageBox.information(self, "Sélection", "Sélectionnez une formation dans la liste.")
            return
        self.entry_selected.emit(selected[0].get('_raw', {}))
        self.accept()


# ------------------------------------------------------------------
# Mini-dialog d'ajout d'une entrée au catalogue
# ------------------------------------------------------------------

class _AddEntryDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter au catalogue")
        self.setFixedSize(400, 160)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        row_code = QHBoxLayout()
        row_code.addWidget(QLabel("Code :"))
        self._code = QSpinBox()
        self._code.setRange(1000, 99999)
        self._code.setValue(1000)
        row_code.addWidget(self._code)
        layout.addLayout(row_code)

        row_lib = QHBoxLayout()
        row_lib.addWidget(QLabel("Libellé :"))
        self._intitule = QLineEdit()
        self._intitule.setPlaceholderText("Intitulé officiel de la formation")
        row_lib.addWidget(self._intitule)
        layout.addLayout(row_lib)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_save = _btn("Enregistrer", 'primary')
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_save)
        btn_cancel = _btn("Annuler", 'ghost')
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def _save(self):
        intitule = self._intitule.text().strip()
        if not intitule:
            QMessageBox.warning(self, "Validation", "Le libellé est obligatoire.")
            return
        ok, msg, _ = FormationServiceCRUD.add_catalogue_entry(
            code=self._code.value(),
            intitule=intitule,
        )
        if ok:
            self.accept()
        else:
            show_error_message(self, "Erreur", "Impossible d'ajouter l'entrée.", msg)
