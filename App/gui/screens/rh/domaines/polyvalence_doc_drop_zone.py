# -*- coding: utf-8 -*-
"""
Widget zone de dépôt pour un document d'évaluation de polyvalence.

Deux états :
  - Vide   : cadre pointillé + texte + bouton Parcourir
  - Rempli : nom du doc + bouton Ouvrir + bouton Retirer

Supporte le drag & drop de fichier en plus du clic/parcourir.
"""
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent


class PolyvalenceDocDropZone(QFrame):
    """
    Zone de dépôt compacte pour attacher un document d'évaluation à une polyvalence.

    Signaux :
        file_chosen(str)   — chemin local du fichier sélectionné
        open_requested()   — l'utilisateur veut ouvrir le doc existant
        remove_requested() — l'utilisateur veut retirer le doc existant
    """

    file_chosen = pyqtSignal(str)
    open_requested = pyqtSignal()
    remove_requested = pyqtSignal()

    def __init__(self, existing_doc_nom: str = None, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._has_doc = bool(existing_doc_nom)
        self._build(existing_doc_nom)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build(self, doc_nom: str = None):
        self.setFixedHeight(44)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        if doc_nom:
            self.setStyleSheet(
                "QFrame { background: #f0fdf4; border: 1px solid #86efac;"
                " border-radius: 6px; }"
            )
            lbl = QLabel(f"  {doc_nom}")
            lbl.setStyleSheet("color: #15803d; font-size: 12px; background: transparent;")
            lbl.setToolTip(doc_nom)
            layout.addWidget(lbl, 1)

            btn_open = QPushButton("Ouvrir")
            btn_open.setFixedHeight(28)
            btn_open.setStyleSheet(
                "QPushButton { background: #22c55e; color: white; border: none;"
                " border-radius: 4px; padding: 2px 10px; font-size: 11px; }"
                "QPushButton:hover { background: #16a34a; }"
            )
            btn_open.clicked.connect(self.open_requested)
            layout.addWidget(btn_open)

            btn_remove = QPushButton("Archiver")
            btn_remove.setFixedHeight(28)
            btn_remove.setStyleSheet(
                "QPushButton { background: transparent; color: #dc2626; border: none;"
                " font-size: 11px; }"
                "QPushButton:hover { text-decoration: underline; }"
            )
            btn_remove.clicked.connect(self.remove_requested)
            layout.addWidget(btn_remove)
        else:
            self.setStyleSheet(
                "QFrame { background: #f8fafc; border: 1px dashed #94a3b8;"
                " border-radius: 6px; }"
                "QFrame:hover { border-color: #3b82f6; background: #eff6ff; }"
            )
            lbl = QLabel("  Deposer le document d'evaluation ici")
            lbl.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
            layout.addWidget(lbl, 1)

            btn_browse = QPushButton("Parcourir...")
            btn_browse.setFixedHeight(28)
            btn_browse.setStyleSheet(
                "QPushButton { background: #3b82f6; color: white; border: none;"
                " border-radius: 4px; padding: 2px 10px; font-size: 11px; }"
                "QPushButton:hover { background: #2563eb; }"
            )
            btn_browse.clicked.connect(self._browse_file)
            layout.addWidget(btn_browse)

    # ------------------------------------------------------------------
    # Drag & drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self.file_chosen.emit(path)
        event.acceptProposedAction()

    # ------------------------------------------------------------------
    # Clic
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if not self._has_doc:
            self._browse_file()
        else:
            super().mousePressEvent(event)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selectionner un document d'evaluation", "",
            "Tous les fichiers (*);;PDF (*.pdf);;Word (*.docx *.doc);;Images (*.png *.jpg)"
        )
        if path:
            self.file_chosen.emit(path)
