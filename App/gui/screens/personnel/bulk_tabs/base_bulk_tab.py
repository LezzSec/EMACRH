# -*- coding: utf-8 -*-
"""
Classe de base pour les onglets d'opérations en masse.

Factorise les méthodes communes : section document (Parcourir / Supprimer),
styles partagés, et le pattern de validation des fichiers.
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# ── Sécurité fichiers ──────────────────────────────────────────
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = frozenset(['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg'])

# Filtre de fichiers standard utilisé par la majorité des onglets
_FILE_FILTER_DOCS = "Documents (*.pdf *.doc *.docx *.png *.jpg *.jpeg);;Tous les fichiers (*)"
_FILE_FILTER_ALL = "Documents (*.pdf *.doc *.docx *.xls *.xlsx *.png *.jpg *.jpeg);;Tous les fichiers (*)"

# ── Styles QSS partagés ────────────────────────────────────────
INPUT_STYLE_SM = """
    QLineEdit, QDateEdit, QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit {
        padding: 6px 10px;
        border: 1px solid #d1d5db;
        border-radius: 5px;
        font-size: 13px;
        background: white;
        color: #111827;
        min-height: 18px;
    }
    QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
        border: 2px solid #7c3aed;
        padding: 5px 9px;
    }
    QLineEdit::placeholder { color: #9ca3af; }
    QDateEdit::drop-down, QComboBox::drop-down { border: none; padding-right: 6px; }
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
    QSpinBox::up-button, QSpinBox::down-button { width: 18px; }
"""

INPUT_STYLE_LG = """
    QLineEdit, QDateEdit, QComboBox, QTextEdit {
        padding: 8px 12px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 14px;
        background: white;
        color: #111827;
        min-height: 20px;
    }
    QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {
        border: 2px solid #7c3aed;
        padding: 7px 11px;
    }
    QLineEdit::placeholder { color: #9ca3af; }
    QDateEdit::drop-down, QComboBox::drop-down { border: none; padding-right: 8px; }
"""

LABEL_STYLE_SM = "color: #374151; font-size: 13px;"
LABEL_STYLE_LG = "color: #374151; font-size: 14px;"
REQUIRED_STYLE = "color: #374151; font-size: 13px; font-weight: 500;"

GROUPBOX_STYLE = """
    QGroupBox {
        font-weight: bold;
        font-size: 13px;
        color: #7c3aed;
        border: none;
        margin-top: 8px;
        padding-top: 4px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 0px;
        padding: 0;
    }
"""

BTN_BROWSE_STYLE = """
    QPushButton {
        background: #f3f4f6;
        color: #374151;
        padding: 8px 16px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-weight: 500;
        font-size: 13px;
    }
    QPushButton:hover {
        background: #e5e7eb;
        border-color: #9ca3af;
    }
"""

BTN_CLEAR_STYLE = """
    QPushButton {
        background: #fee2e2;
        color: #dc2626;
        padding: 8px;
        border: 1px solid #fecaca;
        border-radius: 6px;
        font-weight: bold;
    }
    QPushButton:hover {
        background: #fecaca;
    }
"""


def _validate_uploaded_file(file_path: str) -> tuple:
    """
    Valide un fichier uploadé (taille et extension).

    Returns:
        (valide, message_erreur)
    """
    if not os.path.exists(file_path):
        return False, "Fichier introuvable"

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Extension non autorisée: {ext}\nExtensions acceptées: {', '.join(sorted(ALLOWED_EXTENSIONS))}"

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return False, f"Fichier trop volumineux: {size_mb:.1f} MB\nTaille max: {MAX_FILE_SIZE_MB} MB"

    return True, ""


class BulkTabBase(QWidget):
    """
    Classe de base pour les onglets d'opérations en masse.

    Fournit :
      - Gestion du document joint (_document_path, document_path_input)
      - _browse_document(title, filters) — ouvre un QFileDialog avec validation
      - _clear_document() — efface le document
      - _build_doc_section(input_style) — construit le QHBoxLayout de la section document
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._document_path = None
        self.document_path_input = None  # initialisé par _build_doc_section()

    def _build_doc_section(self, input_style: str) -> QHBoxLayout:
        """
        Construit la section document (chemin + boutons Parcourir/Supprimer).
        Initialise self.document_path_input et connecte les boutons.

        Returns:
            QHBoxLayout à intégrer dans le formulaire.
        """
        doc_layout = QHBoxLayout()
        doc_layout.setSpacing(8)

        self.document_path_input = QLineEdit()
        self.document_path_input.setPlaceholderText("Aucun document sélectionné")
        self.document_path_input.setReadOnly(True)
        self.document_path_input.setStyleSheet(input_style)
        doc_layout.addWidget(self.document_path_input, 1)

        btn_browse = QPushButton("Parcourir...")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setStyleSheet(BTN_BROWSE_STYLE)
        btn_browse.clicked.connect(self._browse_document)
        doc_layout.addWidget(btn_browse)

        btn_clear = QPushButton("X")
        btn_clear.setFixedWidth(32)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setToolTip("Supprimer le document")
        btn_clear.setStyleSheet(BTN_CLEAR_STYLE)
        btn_clear.clicked.connect(self._clear_document)
        doc_layout.addWidget(btn_clear)

        return doc_layout

    def _browse_document(self):
        """Ouvre un dialogue pour sélectionner un document. À surcharger pour personnaliser le titre/filtre."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un document",
            "",
            _FILE_FILTER_DOCS
        )
        self._handle_file_selection(file_path)

    def _handle_file_selection(self, file_path: str):
        """Valide et enregistre le fichier sélectionné."""
        if not file_path:
            return
        valid, error_msg = _validate_uploaded_file(file_path)
        if not valid:
            QMessageBox.warning(self, "Fichier invalide", error_msg)
            return
        self._document_path = file_path
        self.document_path_input.setText(os.path.basename(file_path))

    def _clear_document(self):
        """Supprime le document sélectionné."""
        self._document_path = None
        self.document_path_input.clear()
