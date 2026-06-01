# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QInputDialog, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class FormationDocumentsWidget(QWidget):
    """Liste et gestion des fichiers joints à une formation."""

    def __init__(self, formation_id=None, operateur_id=None, parent=None):
        super().__init__(parent)
        self.formation_id = formation_id
        self.operateur_id = operateur_id
        self._doc_service = None
        self._categorie_id = None
        self._init_ui()
        if self.formation_id:
            self._load_categorie()
            self.load_documents()

    # ------------------------------------------------------------------
    # Helpers privés
    # ------------------------------------------------------------------

    def _get_doc_service(self):
        if self._doc_service is None:
            from domain.services.documents.document_service import DocumentService
            self._doc_service = DocumentService()
        return self._doc_service

    def _load_categorie(self):
        try:
            cats = self._get_doc_service().get_categories()
            for cat in cats:
                if 'formation' in (cat.get('nom') or '').lower():
                    self._categorie_id = cat['id']
                    return
            if cats:
                self._categorie_id = cats[0]['id']
        except Exception as e:
            logger.error(f"Erreur chargement categories: {e}")

    def _get_selected_doc_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    # ------------------------------------------------------------------
    # Construction UI
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        if not self.formation_id:
            lbl = QLabel("Enregistrez la formation pour pouvoir joindre des fichiers.")
            lbl.setStyleSheet("color: #94a3b8; font-style: italic;")
            layout.addWidget(lbl)
            return

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nom du fichier", "Taille", "Date"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumHeight(130)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("+ Ajouter un fichier")
        self.btn_add.setStyleSheet(
            "QPushButton { background-color: #10b981; color: white;"
            " padding: 5px 10px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #059669; }"
        )
        self.btn_add.clicked.connect(self._add_file)
        btn_layout.addWidget(self.btn_add)

        self.btn_open = QPushButton("Ouvrir")
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self._open_selected)
        btn_layout.addWidget(self.btn_open)

        self.btn_delete = QPushButton("Supprimer")
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet("color: #dc2626;")
        self.btn_delete.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.btn_delete)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Chargement des données
    # ------------------------------------------------------------------

    def load_documents(self):
        if not hasattr(self, 'table'):
            return
        try:
            from domain.repositories.document_repo import DocumentRepository
            docs = DocumentRepository.get_by_formation(self.formation_id)
            self.table.setRowCount(0)
            for doc in docs:
                row = self.table.rowCount()
                self.table.insertRow(row)

                nom_item = QTableWidgetItem(doc.get('nom_affichage') or doc.get('nom_fichier', ''))
                nom_item.setData(Qt.UserRole, doc['id'])
                self.table.setItem(row, 0, nom_item)

                taille = doc.get('taille_octets') or 0
                if taille >= 1024 * 1024:
                    taille_str = f"{taille / (1024 * 1024):.1f} Mo"
                elif taille >= 1024:
                    taille_str = f"{taille / 1024:.0f} Ko"
                else:
                    taille_str = f"{taille} o"
                self.table.setItem(row, 1, QTableWidgetItem(taille_str))

                date_up = doc.get('date_upload')
                date_str = date_up.strftime('%d/%m/%Y') if date_up else ''
                self.table.setItem(row, 2, QTableWidgetItem(date_str))
        except Exception as e:
            logger.error(f"Erreur chargement fichiers formation: {e}")

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_selection_changed(self):
        has_sel = self.table.currentRow() >= 0
        self.btn_open.setEnabled(has_sel)
        self.btn_delete.setEnabled(has_sel)

    def _add_file(self):
        if not self.operateur_id:
            QMessageBox.warning(self, "Attention", "Operateur non defini.")
            return
        if not self._categorie_id:
            QMessageBox.warning(self, "Attention", "Aucune categorie de document disponible.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selectionner un fichier", "",
            "Tous les fichiers (*);;PDF (*.pdf);;Word (*.docx *.doc);;Excel (*.xlsx *.xls)"
        )
        if not file_path:
            return

        import os
        default_name = os.path.basename(file_path)
        nom, ok = QInputDialog.getText(
            self, "Nom du fichier", "Nom d'affichage :", text=default_name
        )
        if not ok:
            return
        nom = nom.strip() or default_name

        try:
            success, msg, doc_id = self._get_doc_service().add_document(
                personnel_id=self.operateur_id,
                categorie_id=self._categorie_id,
                fichier_source=file_path,
                nom_affichage=nom,
                formation_id=self.formation_id,
            )
            if success:
                self.load_documents()
            else:
                QMessageBox.warning(self, "Erreur", msg)
        except Exception as e:
            logger.exception(f"Erreur ajout fichier formation: {e}")
            QMessageBox.critical(self, "Erreur", "Impossible d'ajouter le fichier.")

    def _open_selected(self):
        doc_id = self._get_selected_doc_id()
        if not doc_id:
            return
        try:
            path = self._get_doc_service().get_document_path(doc_id)
            if path:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            else:
                QMessageBox.warning(self, "Erreur", "Fichier introuvable.")
        except Exception as e:
            logger.exception(f"Erreur ouverture fichier: {e}")
            QMessageBox.critical(self, "Erreur", "Impossible d'ouvrir le fichier.")

    def _delete_selected(self):
        doc_id = self._get_selected_doc_id()
        if not doc_id:
            return
        reply = QMessageBox.question(
            self, "Confirmation",
            "Supprimer ce fichier definitivement ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            success, msg = self._get_doc_service().hard_delete_document(doc_id)
            if success:
                self.load_documents()
            else:
                QMessageBox.warning(self, "Erreur", msg)
        except Exception as e:
            logger.exception(f"Erreur suppression fichier: {e}")
            QMessageBox.critical(self, "Erreur", "Impossible de supprimer le fichier.")
