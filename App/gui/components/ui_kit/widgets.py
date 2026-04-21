# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore


class LoadingButton(QtWidgets.QPushButton):
    """
    Bouton avec état de chargement intégré.

    Usage:
        btn = LoadingButton("Enregistrer", variant="primary")
        btn.set_loading(True)
        btn.set_loading(False)
    """
    def __init__(self, text: str, variant: str = None, loading_text: str = "Patientez", parent=None):
        super().__init__(text, parent)
        self._original_text = text
        self._loading_text = loading_text
        self._dot_count = 0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._animate_dots)
        self.setFixedHeight(44)
        if variant:
            self.setProperty('class', variant)

    def set_loading(self, loading: bool):
        self.setEnabled(not loading)
        if loading:
            self._dot_count = 0
            self._timer.start(400)
            self._animate_dots()
        else:
            self._timer.stop()
            self.setText(self._original_text)

    def _animate_dots(self):
        dots = "." * (self._dot_count % 4)
        self.setText(f"{self._loading_text}{dots}")
        self._dot_count += 1


class SearchBar(QtWidgets.QLineEdit):
    """
    Barre de recherche avec filtrage en temps réel sur QTableWidget ou QListWidget.

    Usage:
        search = SearchBar("Rechercher un employé...")
        search.filter_table(my_table, columns=[0, 1, 2])
    """
    def __init__(self, placeholder: str = "Rechercher...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(f"  {placeholder}")
        self.setMinimumHeight(36)
        self.setClearButtonEnabled(True)
        self.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #e5e7eb;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
                background: white;
                color: #111827;
            }
            QLineEdit:focus { border-color: #3b82f6; }
        """)
        self._targets = []
        self.textChanged.connect(self._apply_filter)

    def filter_table(self, table, columns: list = None):
        self._targets.append(('table', table, columns))

    def filter_list(self, list_widget):
        self._targets.append(('list', list_widget, None))

    def _apply_filter(self, text: str):
        text_lower = text.strip().lower()
        for kind, widget, columns in self._targets:
            if kind == 'table':
                self._filter_table(widget, text_lower, columns)
            elif kind == 'list':
                self._filter_list(widget, text_lower)

    def _filter_table(self, table, text: str, columns):
        for row in range(table.rowCount()):
            if not text:
                table.setRowHidden(row, False)
                continue
            cols = columns if columns is not None else range(table.columnCount())
            match = any(
                (item := table.item(row, col)) and text in item.text().lower()
                for col in cols
            )
            table.setRowHidden(row, not match)

    def _filter_list(self, list_widget, text: str):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item.setHidden(bool(text) and text not in item.text().lower())
