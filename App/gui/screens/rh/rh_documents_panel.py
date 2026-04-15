# -*- coding: utf-8 -*-
"""
Panneau de documents : documents actifs + archives d'un opérateur par domaine.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from gui.components.ui_theme import EmacCard, EmacButton
from gui.screens.rh.gestion_rh_dialogs import AjouterDocumentDialog
from application.permission_manager import can
from infrastructure.config.date_format import format_date


class RhDocumentsPanel(QWidget):
    """
    Affiche les documents actifs d'un domaine RH.
    Gère l'ajout, l'ouverture, l'archivage et la restauration.
    """

    refresh_requested = pyqtSignal()
    show_archives_requested = pyqtSignal()  # émis après archivage pour activer la vue archives

    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self._vm = vm
        self._operateur = None
        self._domaine = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def set_context(self, operateur: dict, domaine):
        self._operateur = operateur
        self._domaine = domaine

    def refresh(self, documents: list):
        self._clear()
        docs_actifs = [d for d in documents if d.get('statut') != 'archive']
        card = EmacCard(f"Documents associés ({len(docs_actifs)})")

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 10)
        btn_ajouter = EmacButton("+ Ajouter un document", variant="primary")
        btn_ajouter.setVisible(can("rh.documents.edit"))
        btn_ajouter.clicked.connect(self._ajouter_document)
        btn_layout.addWidget(btn_ajouter)
        btn_layout.addStretch()
        card.body.addLayout(btn_layout)

        if not docs_actifs:
            label = QLabel("Aucun document pour ce domaine")
            label.setStyleSheet("color: #9ca3af; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(label)
        else:
            for doc in docs_actifs:
                card.body.addWidget(self._build_doc_row(doc, archived=False))

        self._layout.addWidget(card)

    def show_archives(self, archives: list):
        self._clear()
        card = EmacCard(f"Documents archivés ({len(archives)})")

        if not archives:
            label = QLabel("Aucun document archivé")
            label.setStyleSheet("color: #9ca3af; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(label)
        else:
            for doc in archives:
                card.body.addWidget(self._build_doc_row(doc, archived=True))

        self._layout.addWidget(card)

    def _build_doc_row(self, doc: dict, archived: bool) -> QFrame:
        doc_widget = QFrame()
        if archived:
            doc_widget.setStyleSheet("""
                QFrame {
                    background: #f3f4f6; border: 1px dashed #9ca3af;
                    border-radius: 8px; padding: 10px; margin: 2px 0;
                }
                QFrame:hover { background: #e5e7eb; border-color: #6b7280; }
            """)
        else:
            doc_widget.setStyleSheet("""
                QFrame {
                    background: #f9fafb; border: 1px solid #e5e7eb;
                    border-radius: 8px; padding: 10px; margin: 2px 0;
                }
                QFrame:hover { background: #f3f4f6; border-color: #3b82f6; }
            """)

        doc_layout = QHBoxLayout(doc_widget)
        doc_layout.setContentsMargins(10, 8, 10, 8)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        prefix = ""
        nom_label = QLabel(f"{prefix}{doc.get('nom_affichage', '-')}")
        nom_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        nom_label.setStyleSheet(f"color: {'#6b7280' if archived else '#1f2937'}; background: transparent;")
        info_layout.addWidget(nom_label)

        details = f"{doc.get('categorie_nom', '-')} • Ajouté le {format_date(doc.get('date_upload')) if doc.get('date_upload') else '-'}"
        if not archived and doc.get('date_expiration'):
            details += f" • Expire le {format_date(doc['date_expiration'])}"
        details_label = QLabel(details)
        details_label.setStyleSheet("color: #6b7280; font-size: 11px; background: transparent;")
        info_layout.addWidget(details_label)
        doc_layout.addLayout(info_layout, 1)

        doc_id = doc.get('id')

        if archived:
            btn_restaurer = EmacButton("Restaurer", variant="ghost")
            btn_restaurer.setVisible(can("rh.documents.edit"))
            btn_restaurer.clicked.connect(lambda checked, d=doc_id: self._restaurer_document(d))
            doc_layout.addWidget(btn_restaurer)
        else:
            btn_archiver = EmacButton("Archiver", variant="ghost")
            btn_archiver.setVisible(can("rh.documents.edit"))
            btn_archiver.clicked.connect(lambda checked, d=doc_id: self._archiver_document(d))
            doc_layout.addWidget(btn_archiver)

        btn_ouvrir = EmacButton("Ouvrir", variant="ghost")
        btn_ouvrir.clicked.connect(lambda checked, d=doc_id: self._vm.ouvrir_document(d))
        doc_layout.addWidget(btn_ouvrir)

        return doc_widget

    def _ajouter_document(self):
        if not self._operateur:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une personne")
            return
        from PyQt5.QtWidgets import QDialog
        dialog = AjouterDocumentDialog(
            operateur_id=self._operateur['id'],
            domaine=self._domaine,
            parent=self,
        )
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_requested.emit()

    def _archiver_document(self, doc_id: int):
        reply = QMessageBox.question(
            self, "Confirmer l'archivage",
            "Voulez-vous archiver ce document ?\n\nIl ne sera plus visible mais pourra être restauré via Archives.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.show_archives_requested.emit()
            self._vm.archiver_document(doc_id)

    def _restaurer_document(self, doc_id: int):
        reply = QMessageBox.question(
            self, "Confirmer la restauration",
            "Voulez-vous restaurer ce document ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self._vm.restaurer_document(doc_id)

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()
