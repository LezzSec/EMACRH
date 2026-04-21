# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox,
    QTableWidget, QTableWidgetItem, QHBoxLayout,
    QLabel, QComboBox, QHeaderView, QAbstractItemView,
)
from PyQt5.QtGui import QColor

from domain.services.planning.planning_service import get_documents_expirant
from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date
from gui.components.emac_ui_kit import show_error_message

logger = get_logger(__name__)


class DocsExpirationTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Horizon (jours) :"))
        self.docs_horizon_combo = QComboBox()
        self.docs_horizon_combo.addItems(["30", "60", "90"])
        self.docs_horizon_combo.currentIndexChanged.connect(self.load_data)
        filter_row.addWidget(self.docs_horizon_combo)
        filter_row.addStretch()

        refresh_btn = QPushButton("Actualiser")
        refresh_btn.clicked.connect(self.load_data)
        filter_row.addWidget(refresh_btn)
        layout.addLayout(filter_row)

        self.docs_expiration_table = QTableWidget()
        self.docs_expiration_table.setColumnCount(6)
        self.docs_expiration_table.setHorizontalHeaderLabels([
            "Nom", "Prénom", "Document", "Catégorie", "Date expiration", "Jours restants"
        ])
        hdr = self.docs_expiration_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.docs_expiration_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.docs_expiration_table.setAlternatingRowColors(True)
        self.docs_expiration_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.docs_expiration_table.setProperty("personnel_ids", [])
        layout.addWidget(self.docs_expiration_table, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        open_rh_btn = QPushButton("Voir dossier RH")
        open_rh_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        open_rh_btn.clicked.connect(self._open_rh_for_selected)
        btn_row.addWidget(open_rh_btn)
        layout.addLayout(btn_row)

    def load_data(self):
        try:
            jours = int(self.docs_horizon_combo.currentText())
            rows = get_documents_expirant(jours)

            self.docs_expiration_table.setRowCount(0)
            personnel_ids = []

            for r in rows:
                row_pos = self.docs_expiration_table.rowCount()
                self.docs_expiration_table.insertRow(row_pos)

                jours_restants = r.get('jours_restants') or 0

                if jours_restants <= 7:
                    bg, fg = QColor("#fee2e2"), QColor("#991b1b")
                elif jours_restants <= 30:
                    bg, fg = QColor("#ffedd5"), QColor("#9a3412")
                else:
                    bg, fg = QColor("#fef9c3"), QColor("#713f12")

                def _item(text, background=bg, foreground=fg):
                    it = QTableWidgetItem(text)
                    it.setBackground(background)
                    it.setForeground(foreground)
                    return it

                self.docs_expiration_table.setItem(row_pos, 0, _item(r.get('nom') or ""))
                self.docs_expiration_table.setItem(row_pos, 1, _item(r.get('prenom') or ""))
                self.docs_expiration_table.setItem(row_pos, 2, _item(r.get('nom_document') or ""))
                self.docs_expiration_table.setItem(row_pos, 3, _item(r.get('categorie') or ""))

                date_exp = r.get('date_expiration')
                date_exp_str = format_date(date_exp) if date_exp and not isinstance(date_exp, str) else (date_exp or "")
                self.docs_expiration_table.setItem(row_pos, 4, _item(date_exp_str))
                self.docs_expiration_table.setItem(row_pos, 5, _item(str(jours_restants) + " j"))

                personnel_ids.append(r.get('personnel_id'))

            self.docs_expiration_table.setProperty("personnel_ids", personnel_ids)

        except Exception as e:
            logger.exception(f"Erreur chargement documents expirant: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les documents expirant", e)

    def _open_rh_for_selected(self):
        row = self.docs_expiration_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un document dans la liste.")
            return

        personnel_ids = self.docs_expiration_table.property("personnel_ids") or []
        if row >= len(personnel_ids) or personnel_ids[row] is None:
            return

        personnel_id = personnel_ids[row]
        try:
            from gui.screens.rh.gestion_rh_dialog import GestionRHDialog
            dlg = GestionRHDialog(parent=self, preselect_personnel_id=personnel_id)
            dlg.exec_()
        except Exception as e:
            logger.exception(f"Erreur ouverture dossier RH pour personnel {personnel_id}: {e}")
            show_error_message(self, "Erreur", "Impossible d'ouvrir le dossier RH", e)
