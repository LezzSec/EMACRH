# -*- coding: utf-8 -*-
"""
Dialogue de progression pour les opérations en masse.
"""

from typing import Dict, List

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal

from gui.workers.db_worker import DbWorker, DbThreadPool
from gui.components.loading_components import ProgressWidget
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class BulkOperationProgressDialog(QDialog):
    """Dialogue de progression pour les opérations longues."""

    operation_completed = pyqtSignal(int, int, list)  # success, errors, details

    def __init__(self, operation_type: str, data: Dict, personnel_ids: List[int],
                 created_by: str = None, parent=None):
        super().__init__(parent)
        self.operation_type = operation_type
        self.data = data
        self.personnel_ids = personnel_ids
        self.created_by = created_by
        self._cancelled = False
        self._worker = None

        self.setWindowTitle("Opération en cours")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        info_label = QLabel(f"Traitement de {len(self.personnel_ids)} employé(s)...")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)

        self.progress_widget = ProgressWidget(f"Opération: {self.operation_type}")
        layout.addWidget(self.progress_widget)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self._cancel)
        layout.addWidget(self.btn_cancel, alignment=Qt.AlignCenter)

    def start_operation(self):
        """Lance l'opération en background."""
        from domain.services.personnel import bulk_service

        def do_operation(progress_callback=None):
            if self.operation_type == "FORMATION":
                return bulk_service.add_formation_batch(
                    self.personnel_ids, self.data,
                    progress_callback=progress_callback, created_by=self.created_by
                )
            elif self.operation_type == "ABSENCE":
                return bulk_service.add_absence_batch(
                    self.personnel_ids, self.data,
                    progress_callback=progress_callback, created_by=self.created_by
                )
            elif self.operation_type == "VISITE_MEDICALE":
                return bulk_service.add_visite_batch(
                    self.personnel_ids, self.data,
                    progress_callback=progress_callback, created_by=self.created_by
                )
            elif self.operation_type == "COMPETENCE":
                return bulk_service.add_competence_batch(
                    self.personnel_ids, self.data,
                    progress_callback=progress_callback, created_by=self.created_by
                )
            return 0, 0, []

        def on_result(result):
            nb_success, nb_errors, details = result
            self.operation_completed.emit(nb_success, nb_errors, details)
            self.accept()

        def on_error(error):
            logger.error(f"Erreur lors de l'opération bulk: {error}")
            QMessageBox.critical(self, "Erreur", "Une erreur est survenue lors de l'opération. Consultez les logs pour plus de détails.")
            self.reject()

        self._worker = DbWorker(do_operation)
        self._worker.signals.result.connect(on_result)
        self._worker.signals.error.connect(on_error)
        self._worker.signals.progress.connect(self._on_progress)
        DbThreadPool.start(self._worker)

    def _on_progress(self, percentage, message):
        """Met à jour la progression."""
        self.progress_widget.set_progress(percentage, message)

    def _cancel(self):
        """Annule l'opération."""
        self._cancelled = True
        if self._worker:
            self._worker.cancel()
        self.reject()
