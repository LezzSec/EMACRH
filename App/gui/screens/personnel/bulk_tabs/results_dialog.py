# -*- coding: utf-8 -*-
"""
Dialogue de résultats pour les opérations en masse.
"""

from typing import List, Dict

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from domain.repositories.personnel_repo import PersonnelRepository


class BulkOperationResultsDialog(QDialog):
    """Dialogue pour afficher les résultats d'une opération."""

    def __init__(self, operation_type: str, nb_success: int, nb_errors: int,
                 details: List[Dict], parent=None):
        super().__init__(parent)
        self.operation_type = operation_type
        self.nb_success = nb_success
        self.nb_errors = nb_errors
        self.details = details

        self.setWindowTitle("Résultats de l'opération")
        self.setMinimumSize(600, 400)
        self._setup_ui()
        self._load_details()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # === Résumé ===
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background: #e8f5e9;
                border: 1px solid #a5d6a7;
                border-radius: 8px;
                padding: 12px;
            }
        """ if self.nb_errors == 0 else """
            QFrame {
                background: #fff3e0;
                border: 1px solid #ffcc80;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)

        icon = "OK" if self.nb_errors == 0 else "!"
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        summary_layout.addWidget(icon_label)

        summary_text = f"<b>{self.nb_success}</b> succès"
        if self.nb_errors > 0:
            summary_text += f", <b style='color: #d32f2f;'>{self.nb_errors}</b> erreur(s)"
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(summary_label)
        summary_layout.addStretch()

        layout.addWidget(summary_frame)

        # === Table des détails ===
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Statut", "Nom", "Prénom", "Détails"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # === Boutons ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        btn_close.setDefault(True)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _load_details(self):
        """Charge les détails dans la table."""
        personnel_names = {}
        personnel_ids = [d['personnel_id'] for d in self.details]

        if personnel_ids:
            rows = PersonnelRepository.get_by_ids(personnel_ids)
            for row in rows:
                personnel_names[row['id']] = (row['nom'], row['prenom'])

        self.table.setRowCount(len(self.details))
        for row, detail in enumerate(self.details):
            status = detail.get('status', '')
            status_item = QTableWidgetItem("OK" if status == 'SUCCES' else "X")
            if status == 'SUCCES':
                status_item.setForeground(QColor('#2e7d32'))
            else:
                status_item.setForeground(QColor('#d32f2f'))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, status_item)

            names = personnel_names.get(detail['personnel_id'], ('?', '?'))
            self.table.setItem(row, 1, QTableWidgetItem(names[0]))
            self.table.setItem(row, 2, QTableWidgetItem(names[1]))

            if status == 'SUCCES':
                details_text = f"ID: {detail.get('record_id', '?')}"
            else:
                details_text = detail.get('error', 'Erreur inconnue')
            self.table.setItem(row, 3, QTableWidgetItem(details_text))
