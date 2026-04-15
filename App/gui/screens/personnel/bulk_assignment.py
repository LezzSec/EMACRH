# -*- coding: utf-8 -*-
"""
Module de gestion des opérations en masse.
Permet d'assigner des formations, absences, visites médicales à plusieurs employés.
"""

from typing import List

from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QGroupBox, QMessageBox,
    QFrame,
)
from PyQt5.QtCore import Qt

from infrastructure.logging.logging_config import get_logger
from .personnel_selection_widget import PersonnelSelectionWidget
from .bulk_tabs import (
    FormationBulkTab, AbsenceBulkTab, MedicalBulkTab, CompetenceBulkTab,
    BulkOperationProgressDialog, BulkOperationResultsDialog,
)
from .bulk_tabs.base_bulk_tab import (
    _validate_uploaded_file,
    MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS,
)

logger = get_logger(__name__)

# Réexports pour compatibilité des imports externes éventuels
validate_uploaded_file = _validate_uploaded_file


class BulkAssignmentDialog(QDialog):
    """Dialogue principal pour les opérations en masse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Actions en masse")
        self.setMinimumSize(700, 820)
        self.resize(750, 880)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 16)

        # === Header avec gradient ===
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #a855f7);
                border-radius: 0px;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 14, 20, 14)
        header_layout.setSpacing(4)

        title = QLabel("Actions en masse")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        header_layout.addWidget(title)

        subtitle = QLabel("Assignez des formations, absences, visites médicales ou compétences à plusieurs employés")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 12px;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header, 0)

        # === Contenu principal ===
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 12, 16, 0)
        content_layout.setSpacing(12)

        # === Onglets stylisés ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                background: white;
                padding: 12px;
            }
            QTabBar::tab {
                background: #f3f4f6;
                color: #6b7280;
                padding: 8px 16px;
                margin-right: 3px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #7c3aed;
                border: 1px solid #e5e7eb;
                border-bottom: 2px solid #7c3aed;
            }
            QTabBar::tab:hover:!selected {
                background: #e5e7eb;
                color: #374151;
            }
        """)
        self.formation_tab = FormationBulkTab()
        self.absence_tab = AbsenceBulkTab()
        self.medical_tab = MedicalBulkTab()
        self.competence_tab = CompetenceBulkTab()

        self.tabs.addTab(self.formation_tab, "Formations")
        self.tabs.addTab(self.absence_tab, "Absences")
        self.tabs.addTab(self.medical_tab, "Médical")
        self.tabs.addTab(self.competence_tab, "Compétences")
        self.tabs.setMinimumHeight(310)
        content_layout.addWidget(self.tabs, 0)

        # === Sélection du personnel (commune) ===
        personnel_group = QGroupBox("Sélection du personnel")
        personnel_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #374151;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                background: white;
            }
        """)
        personnel_layout = QVBoxLayout(personnel_group)
        personnel_layout.setContentsMargins(12, 20, 12, 12)
        self.personnel_widget = PersonnelSelectionWidget()
        self.personnel_widget.selection_changed.connect(self._on_selection_changed)
        personnel_layout.addWidget(self.personnel_widget)
        personnel_group.setMinimumHeight(200)
        content_layout.addWidget(personnel_group, 1)

        layout.addWidget(content_widget, 1)

        # === Footer avec boutons ===
        footer = QFrame()
        footer.setStyleSheet("""
            QFrame {
                background: #f9fafb;
                border-top: 1px solid #e5e7eb;
            }
        """)
        btn_layout = QHBoxLayout(footer)
        btn_layout.setContentsMargins(20, 12, 20, 12)
        btn_layout.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: white;
                color: #374151;
                padding: 10px 24px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #f3f4f6;
                border-color: #9ca3af;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        self.btn_assign = QPushButton("Assigner à 0 personne(s)")
        self.btn_assign.setEnabled(False)
        self.btn_assign.setCursor(Qt.PointingHandCursor)
        self.btn_assign.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #a855f7);
                color: white;
                padding: 10px 28px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #9333ea);
            }
            QPushButton:disabled {
                background: #d1d5db;
                color: #9ca3af;
            }
        """)
        self.btn_assign.clicked.connect(self._execute_operation)
        btn_layout.addWidget(self.btn_assign)

        layout.addWidget(footer, 0)

    def _on_selection_changed(self, selected_ids: List[int]):
        """Met à jour le bouton selon la sélection."""
        count = len(selected_ids)
        self.btn_assign.setText(f"Assigner à {count} personne(s)")
        self.btn_assign.setEnabled(count > 0)

    def _execute_operation(self):
        """Exécute l'opération en masse."""
        selected_ids = self.personnel_widget.get_selected_ids()

        if not selected_ids:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner au moins un employé")
            return

        current_index = self.tabs.currentIndex()

        if current_index == 0:  # Formations
            valid, error = self.formation_tab.validate()
            if not valid:
                QMessageBox.warning(self, "Validation", error)
                return
            operation_type = "FORMATION"
            data = self.formation_tab.get_data()
            operation_name = data.get('intitule', 'Formation')

        elif current_index == 1:  # Absences
            valid, error = self.absence_tab.validate()
            if not valid:
                QMessageBox.warning(self, "Validation", error)
                return
            operation_type = "ABSENCE"
            data = self.absence_tab.get_data()
            operation_name = f"Absence {data.get('type_absence_code', '')}"

        elif current_index == 2:  # Médical
            valid, error = self.medical_tab.validate()
            if not valid:
                QMessageBox.warning(self, "Validation", error)
                return
            operation_type = "VISITE_MEDICALE"
            data = self.medical_tab.get_data()
            operation_name = f"Visite {data.get('type_visite', '')}"

        elif current_index == 3:  # Compétences
            valid, error = self.competence_tab.validate()
            if not valid:
                QMessageBox.warning(self, "Validation", error)
                return
            operation_type = "COMPETENCE"
            data = self.competence_tab.get_data()
            operation_name = data.get('competence_libelle', 'Compétence')

        else:
            return

        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir assigner '{operation_name}' à {len(selected_ids)} employé(s) ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        progress_dialog = BulkOperationProgressDialog(
            operation_type, data, selected_ids, parent=self
        )

        def on_completed(nb_success, nb_errors, details):
            results_dialog = BulkOperationResultsDialog(
                operation_type, nb_success, nb_errors, details, parent=self
            )
            results_dialog.exec_()
            if nb_errors == 0:
                self.accept()

        progress_dialog.operation_completed.connect(on_completed)
        progress_dialog.start_operation()
        progress_dialog.exec_()
