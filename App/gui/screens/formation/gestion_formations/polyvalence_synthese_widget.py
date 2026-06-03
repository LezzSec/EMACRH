# -*- coding: utf-8 -*-
"""
Widget de synthèse des polyvalences avec leurs documents d'évaluation.

Affiché dans l'onglet Formation > "Synthèse polyvalences".
Présente toutes les polyvalences du personnel actif (sans filtre pour l'instant)
avec le document d'évaluation joint et la possibilité de le visualiser.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont

from gui.workers.db_worker import DbWorker, DbThreadPool
from gui.components.loading_components import LoadingLabel
from gui.components.ui_kit.stylesheet import get_colors
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class PolyvalenceSyntheseWidget(QWidget):
    """Tableau de synthèse polyvalences + documents d'évaluation (tous opérateurs actifs)."""

    # Colonnes visibles
    _COLS = ["Personnel", "Matricule", "Poste", "Atelier", "Niveau", "Date éval.", "Document éval."]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows_data = []
        self._loading = None
        self._colors = get_colors()
        self._init_ui()
        QTimer.singleShot(100, self._load_async)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)

        # Barre du haut
        bar = QHBoxLayout()
        title = QLabel("Synthèse des polyvalences et documents d'évaluation")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet(f"color: {self._colors['TXT']};")
        bar.addWidget(title)
        bar.addStretch()

        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {self._colors['INFO']}; border: 1px solid {self._colors['INFO']};"
            f" border-radius: 4px; padding: 4px 12px; }}"
            f"QPushButton:hover {{ background: {self._colors['INFO_BG']}; }}"
        )
        btn_refresh.clicked.connect(self.load_data)
        bar.addWidget(btn_refresh)
        layout.addLayout(bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self._COLS) + 1)  # +1 colonne action
        self.table.setHorizontalHeaderLabels(self._COLS + [""])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {self._colors['BDR']};
                border-radius: 6px;
                gridline-color: {self._colors['BG']};
            }}
            QHeaderView::section {{
                background: {self._colors['BG']};
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid {self._colors['BDR']};
                font-weight: bold;
                color: {self._colors['TXT']};
            }}
        """)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Personnel
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Matricule
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Poste
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Atelier
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Niveau
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Date éval.
        hdr.setSectionResizeMode(6, QHeaderView.Stretch)           # Document
        hdr.setSectionResizeMode(7, QHeaderView.Fixed)             # Bouton
        self.table.setColumnWidth(7, 70)
        layout.addWidget(self.table, 1)

        # Compteur
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(f"color: {self._colors['TXT_DIM']}; font-size: 11px;")
        layout.addWidget(self.lbl_count)

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def load_data(self):
        """Relance le chargement asynchrone (bouton Actualiser)."""
        self._load_async()

    def _load_async(self):
        if self._loading is None:
            self._loading = LoadingLabel("Chargement...")
            self.layout().insertWidget(1, self._loading)

        def fetch(progress_callback=None):
            from domain.services.documents.polyvalence_docs_service import get_polyvalences_synthese
            return get_polyvalences_synthese()

        def on_success(rows):
            if self._loading:
                self._loading.setVisible(False)
            self._populate(rows)

        def on_error(err):
            if self._loading:
                self._loading.setVisible(False)
            logger.error(f"Erreur chargement synthese polyvalences: {err}")
            QMessageBox.critical(self, "Erreur", "Impossible de charger la synthèse des polyvalences.")

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def _populate(self, rows: list):
        from gui.screens.rh.domaines.domaine_base import get_niveau_display_maps
        niveau_labels, niveau_colors = get_niveau_display_maps()

        self._rows_data = rows
        self.table.setRowCount(0)

        for row_idx, row in enumerate(rows):
            self.table.insertRow(row_idx)

            nom_complet = f"{row.get('prenom', '')} {row.get('nom', '')}".strip()
            self.table.setItem(row_idx, 0, QTableWidgetItem(nom_complet))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row.get('matricule') or ''))

            self.table.setItem(row_idx, 2, QTableWidgetItem(row.get('poste_code') or ''))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row.get('atelier_nom') or ''))

            niveau = row.get('niveau')
            niveau_txt = niveau_labels.get(niveau, f"N{niveau}") if niveau else '-'
            niveau_item = QTableWidgetItem(niveau_txt)
            if niveau and niveau in niveau_colors:
                niveau_item.setForeground(QColor(niveau_colors[niveau]))
            self.table.setItem(row_idx, 4, niveau_item)

            date_eval = row.get('date_evaluation')
            date_str = date_eval.strftime('%d/%m/%Y') if date_eval else '-'
            self.table.setItem(row_idx, 5, QTableWidgetItem(date_str))

            doc_nom = row.get('eval_doc_nom') or ''
            doc_item = QTableWidgetItem(doc_nom if doc_nom else 'Aucun document joint')
            if not doc_nom:
                doc_item.setForeground(QColor(self._colors['TXT_DIM']))
                doc_item.setFont(QFont("Segoe UI", 9, italic=True))
            self.table.setItem(row_idx, 6, doc_item)

            # Bouton Voir (seulement si doc exist)
            if row.get('eval_doc_id'):
                btn = QPushButton("Voir")
                btn.setFixedHeight(26)
                btn.setStyleSheet(
                    f"QPushButton {{ background: {self._colors['INFO']}; color: white; border: none;"
                    f" border-radius: 4px; font-size: 11px; }}"
                    f"QPushButton:hover {{ background: #2563eb; }}"
                )
                btn.clicked.connect(
                    lambda checked, did=row['eval_doc_id']: self._ouvrir_doc(did)
                )
                self.table.setCellWidget(row_idx, 7, btn)

        total = len(rows)
        avec_doc = sum(1 for r in rows if r.get('eval_doc_id'))
        self.lbl_count.setText(
            f"{total} polyvalence(s)  —  {avec_doc} avec document d'évaluation joint"
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _ouvrir_doc(self, doc_id: int):
        try:
            from infrastructure.storage.file_opener import open_file
            from domain.services.documents.document_service import DocumentService
            path = DocumentService().get_document_path(doc_id)
            if path and path.exists():
                ok, msg = open_file(str(path))
                if not ok:
                    QMessageBox.warning(self, "Erreur", msg)
            else:
                QMessageBox.warning(self, "Introuvable", "Le document est introuvable.")
        except Exception as e:
            logger.exception(f"Erreur ouverture doc eval polyvalence {doc_id}: {e}")
            QMessageBox.critical(self, "Erreur", "Impossible d'ouvrir le document.")
