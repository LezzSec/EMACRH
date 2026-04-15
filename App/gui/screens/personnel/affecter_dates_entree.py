# -*- coding: utf-8 -*-
"""
AffecterDatesEntreeDialog — dialogue d'affectation des dates d'entrée.
"""

from infrastructure.logging.logging_config import get_logger
logger = get_logger(__name__)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QDateEdit,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from domain.repositories.personnel_repo import PersonnelRepository
from infrastructure.logging.optimized_db_logger import log_hist
from gui.components.emac_ui_kit import show_error_message


class AffecterDatesEntreeDialog(QDialog):
    """Dialogue pour affecter les dates d'entrée aux employés sans date"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Affectation des dates d'entrée")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(600)

        self.date_widgets = {}  # Dictionnaire pour stocker les QDateEdit par operateur_id
        self.init_ui()
        self.load_personnel_sans_date()

    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("Affectation des dates d'entrée")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Saisissez la date d'entrée pour chaque employé puis cliquez sur 'Enregistrer'")
        subtitle.setStyleSheet("color: #6b7280; font-style: italic;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #3b82f6; font-weight: bold; padding: 10px;")
        self.stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_label)

        # Table des employés
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Nom", "Prénom", "Matricule", "Statut", "Date d'entrée", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 120)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9fafb;
                gridline-color: #e5e7eb;
                border: 1px solid #d1d5db;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                color: #374151;
                font-weight: 600;
                padding: 8px;
                border: none;
            }
        """)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Boutons d'actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.close_btn = QPushButton("Fermer")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def load_personnel_sans_date(self):
        """Charge les employés sans date d'entrée"""
        try:
            personnel = PersonnelRepository.get_personnel_sans_date_entree()

            self.stats_label.setText(f"{len(personnel)} employé(s) sans date d'entrée")

            self.table.setRowCount(len(personnel))
            self.date_widgets.clear()

            for row, emp in enumerate(personnel):
                operateur_id = emp['id']

                nom_item = QTableWidgetItem(emp['nom'])
                nom_item.setData(Qt.UserRole, operateur_id)
                self.table.setItem(row, 0, nom_item)

                self.table.setItem(row, 1, QTableWidgetItem(emp['prenom']))
                self.table.setItem(row, 2, QTableWidgetItem(emp['matricule'] or "—"))

                statut = emp['statut']
                statut_item = QTableWidgetItem(statut)
                if statut == "ACTIF":
                    statut_item.setForeground(QColor("#10b981"))
                else:
                    statut_item.setForeground(QColor("#6b7280"))
                self.table.setItem(row, 3, statut_item)

                date_edit = QDateEdit()
                date_edit.setCalendarPopup(True)
                date_edit.setDate(QDate.currentDate())
                date_edit.setDisplayFormat("dd/MM/yyyy")
                date_edit.setMinimumDate(QDate(1950, 1, 1))
                date_edit.setMaximumDate(QDate.currentDate())
                date_edit.setStyleSheet("""
                    QDateEdit {
                        padding: 6px;
                        border: 1px solid #d1d5db;
                        border-radius: 4px;
                    }
                    QDateEdit:focus {
                        border-color: #3b82f6;
                    }
                """)
                self.table.setCellWidget(row, 4, date_edit)
                self.date_widgets[operateur_id] = date_edit

                btn_enregistrer = QPushButton("Enregistrer")
                btn_enregistrer.setStyleSheet("""
                    QPushButton {
                        background: #10b981;
                        color: white;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #059669;
                    }
                """)
                btn_enregistrer.clicked.connect(
                    lambda checked, oid=operateur_id, r=row: self.enregistrer_date(oid, r)
                )
                self.table.setCellWidget(row, 5, btn_enregistrer)

        except Exception as e:
            logger.exception(f"Erreur chargement: {e}")
            show_error_message(self, "Erreur", "Erreur lors du chargement", e)

    def enregistrer_date(self, operateur_id, row):
        """Enregistre la date d'entrée pour un employé spécifique"""
        try:
            date_widget = self.date_widgets.get(operateur_id)

            current_row = None
            for r in range(self.table.rowCount()):
                item = self.table.item(r, 0)
                if item and item.data(Qt.UserRole) == operateur_id:
                    current_row = r
                    break
            if current_row is None:
                current_row = row

            nom = self.table.item(current_row, 0).text() if self.table.item(current_row, 0) else ""
            prenom = self.table.item(current_row, 1).text() if self.table.item(current_row, 1) else ""

            if not date_widget:
                return

            date_entree = date_widget.date().toString("yyyy-MM-dd")
            date_display = date_widget.date().toString("dd/MM/yyyy")

            reply = QMessageBox.question(
                self,
                "Confirmation",
                f"Affecter la date {date_display} à {nom} {prenom} ?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

            try:
                PersonnelRepository.save_date_entree(operateur_id, date_entree)

                log_hist(
                    "AFFECTATION_DATE_ENTREE",
                    f"Date d'entrée affectée: {date_display}",
                    operateur_id,
                    None
                )

                QMessageBox.information(
                    self,
                    "Succès",
                    f"Date d'entrée enregistrée pour {nom} {prenom}"
                )

                self.table.removeRow(current_row)
                del self.date_widgets[operateur_id]

                nb_restants = self.table.rowCount()
                self.stats_label.setText(f"{nb_restants} employé(s) sans date d'entrée")

                if nb_restants == 0:
                    QMessageBox.information(
                        self,
                        "Terminé",
                        "Tous les employés ont maintenant une date d'entrée!"
                    )
                    self.close()

            except Exception as e:
                logger.exception(f"Erreur enregistrement: {e}")
                show_error_message(self, "Erreur", "Erreur lors de l'enregistrement", e)

        except Exception as e:
            logger.exception(f"Erreur: {e}")
            show_error_message(self, "Erreur", "Une erreur est survenue", e)
