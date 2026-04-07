# -*- coding: utf-8 -*-
"""
Classe de base pour tous les widgets de domaine RH.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal

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

    @property
    def operateur_id(self):
        return self._operateur['id'] if self._operateur else None

    def refresh(self, operateur: dict, donnees: dict, documents: list = None):
        self._operateur = operateur
        self._clear()
        self._build(donnees, documents or [])

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()

    def _format_date(self, date_val) -> str:
        return format_date(date_val) if date_val else '-'

    def _build(self, donnees: dict, documents: list):
        raise NotImplementedError
