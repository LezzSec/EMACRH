# -*- coding: utf-8 -*-
"""
Classe de base pour tous les widgets de domaine RH.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QFrame, QHBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal

from gui.components.ui_theme import EmacButton
from infrastructure.config.date_format import format_date


class DomaineWidget(QWidget):
    """
    Widget autonome pour un domaine RH.

    Reçoit le ViewModel en paramètre.
    Émet refresh_requested quand une action modifie des données.
    """

    refresh_requested = pyqtSignal()

    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self._vm = vm
        self._operateur = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    @property
    def operateur_id(self):
        return self._operateur['id'] if self._operateur else None

    def refresh(self, operateur: dict, donnees: dict, documents: list = None):
        self._operateur = operateur
        self._clear()
        self._build(donnees, documents or [])
        self._layout.addStretch(1)
        self.updateGeometry()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()

    def _format_date(self, date_val) -> str:
        return format_date(date_val) if date_val else '-'

    def _documents_for_entity(self, documents: list, link_field: str, entity_id: int) -> list:
        """Filtre les documents DMS lies a une entite RH quand le lien est disponible."""
        return [
            doc for doc in (documents or [])
            if doc.get(link_field) == entity_id and doc.get('statut') != 'archive'
        ]

    def _build_document_row(self, doc: dict) -> QFrame:
        row_widget = QFrame()
        row_widget.setStyleSheet("""
            QFrame {
                background: #f9fafb; border: 1px solid #e5e7eb;
                border-radius: 6px; padding: 6px; margin: 2px 0;
            }
            QFrame:hover { background: #f3f4f6; border-color: #3b82f6; }
        """)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(8)

        details = f"Ajoute le {self._format_date(doc.get('date_upload'))}"
        if doc.get('date_expiration'):
            details += f" - expire le {self._format_date(doc.get('date_expiration'))}"
        info = QLabel(
            f"<b>{doc.get('nom_affichage', '-')}</b>"
            f"<span style='color:#6b7280; font-size:11px;'>  -  {details}</span>"
        )
        info.setStyleSheet("background: transparent;")
        info.setWordWrap(True)
        row_layout.addWidget(info, 1)

        btn_ouvrir = EmacButton("Ouvrir", variant="ghost")
        btn_ouvrir.clicked.connect(lambda checked, d=doc.get('id'): self._vm.ouvrir_document(d))
        row_layout.addWidget(btn_ouvrir)
        return row_widget

    def _build(self, donnees: dict, documents: list):
        raise NotImplementedError
