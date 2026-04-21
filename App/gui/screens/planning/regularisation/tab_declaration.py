# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox,
    QGroupBox, QFormLayout, QTextEdit, QComboBox, QDateEdit,
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal

from domain.services.planning.planning_service import (
    get_personnel_actif_liste, creer_declaration,
)
from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date
from gui.components.emac_ui_kit import show_error_message

logger = get_logger(__name__)


class DeclarationTab(QWidget):
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        info_label = QLabel("Remplissez le formulaire ci-dessous pour déclarer une absence")
        info_label.setStyleSheet("color: #6b7280; font-size: 12px; padding: 10px;")
        layout.addWidget(info_label)

        form_group = QGroupBox("Formulaire de déclaration")
        form_layout = QFormLayout()

        self.personnel_combo = QComboBox()
        self.personnel_combo.setEditable(True)
        form_layout.addRow("Personnel :", self.personnel_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "CongePaye", "RTT", "SansSolde", "Maladie",
            "AccidentTravail", "AccidentTrajet", "ArretTravail",
            "CongeNaissance", "Formation", "Autorisation", "Autre",
        ])
        form_layout.addRow("Type :", self.type_combo)

        self.date_debut_edit = QDateEdit()
        self.date_debut_edit.setDate(QDate.currentDate())
        self.date_debut_edit.setCalendarPopup(True)
        self.date_debut_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Date début :", self.date_debut_edit)

        self.date_fin_edit = QDateEdit()
        self.date_fin_edit.setDate(QDate.currentDate())
        self.date_fin_edit.setCalendarPopup(True)
        self.date_fin_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Date fin :", self.date_fin_edit)

        self.motif_edit = QTextEdit()
        self.motif_edit.setPlaceholderText("Saisissez un motif optionnel...")
        self.motif_edit.setMaximumHeight(80)
        form_layout.addRow("Motif :", self.motif_edit)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        submit_btn = QPushButton("Enregistrer la déclaration")
        submit_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        submit_btn.clicked.connect(self._submit_declaration)
        layout.addWidget(submit_btn)

        layout.addStretch()

    def load_data(self):
        try:
            rows = get_personnel_actif_liste()
            self.personnel_combo.clear()
            for r in rows:
                display = f"{r['nom']} {r['prenom']}"
                if r.get('matricule'):
                    display += f" ({r['matricule']})"
                self.personnel_combo.addItem(display, r['id'])
        except Exception as e:
            logger.exception(f"Erreur chargement personnel: {e}")
            show_error_message(self, "Erreur", "Impossible de charger le personnel", e)

    def _submit_declaration(self):
        if self.personnel_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un membre du personnel.")
            return

        operateur_id = self.personnel_combo.currentData()
        type_decl = self.type_combo.currentText()
        date_debut = self.date_debut_edit.date().toPyDate()
        date_fin = self.date_fin_edit.date().toPyDate()
        motif = self.motif_edit.toPlainText().strip()

        if date_fin < date_debut:
            QMessageBox.warning(self, "Attention", "La date de fin ne peut pas être antérieure à la date de début.")
            return

        try:
            new_id = creer_declaration(operateur_id, type_decl, date_debut, date_fin, motif)
            if new_id is None:
                raise RuntimeError("Échec de l'enregistrement")

            QMessageBox.information(
                self, "Succès",
                f"Déclaration enregistrée avec succès !\n\n"
                f"Type : {type_decl}\n"
                f"Du {format_date(date_debut)} au {format_date(date_fin)}"
            )

            self.date_debut_edit.setDate(QDate.currentDate())
            self.date_fin_edit.setDate(QDate.currentDate())
            self.motif_edit.clear()

            self.refresh_requested.emit()

        except Exception as e:
            logger.exception(f"Erreur enregistrement declaration: {e}")
            show_error_message(self, "Erreur", "Impossible d'enregistrer la déclaration", e)
