# -*- coding: utf-8 -*-
"""
Composants partagés entre plusieurs dialogs RH.

  - JustificatifMixin  : mixin pour la sélection d'un document justificatif
  - ConsulterDetailDialog : fiche lecture seule générique
"""

from gui.components.ui_theme import EmacButton


class JustificatifMixin:
    """
    Mixin qui ajoute un champ de document justificatif obligatoire (création uniquement).
    À mélanger avec EmacFormDialog : class MonDialog(JustificatifMixin, EmacFormDialog).
    Appeler _ajouter_section_justificatif() dans init_ui(), puis :
      - _valider_justificatif() dans validate()
      - _sauvegarder_justificatif(operateur_id, ...) dans save_to_db()
    """

    def _ajouter_section_justificatif(self, categorie_nom_hint: str = "", optionnel: bool = False):
        """Ajoute le groupe UI 'Document justificatif' à self.content_layout."""
        from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel
        self._justificatif_path = None
        self._justificatif_categorie_nom = categorie_nom_hint

        titre = "Document justificatif (optionnel)" if optionnel else "Document justificatif (obligatoire)"
        group = QGroupBox(titre)
        if optionnel:
            group.setStyleSheet("""
                QGroupBox {
                    border: 1px solid #94a3b8;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding: 10px 8px 8px 8px;
                    font-weight: bold;
                    color: #475569;
                    background: #f8fafc;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 4px;
                }
            """)
        else:
            group.setStyleSheet("""
                QGroupBox {
                    border: 2px solid #f59e0b;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding: 10px 8px 8px 8px;
                    font-weight: bold;
                    color: #92400e;
                    background: #fffbeb;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 4px;
                }
            """)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(6)

        if optionnel:
            note = QLabel("Vous pouvez joindre un document justificatif (attestation MDPH, certificat médical…).")
        else:
            note = QLabel("Un document justificatif (attestation, certificat, contrat signé…) "
                          "est requis pour valider cette saisie.")
        note.setStyleSheet("color: #78350f; font-size: 11px; font-style: italic;" if not optionnel
                           else "color: #475569; font-size: 11px; font-style: italic;")
        note.setWordWrap(True)
        group_layout.addWidget(note)

        file_row = QHBoxLayout()
        self._justificatif_label = QLineEdit()
        self._justificatif_label.setReadOnly(True)
        self._justificatif_label.setPlaceholderText("Aucun fichier sélectionné…")
        self._justificatif_label.setStyleSheet("background: white;")
        file_row.addWidget(self._justificatif_label)

        btn = EmacButton("Parcourir…", variant="ghost")
        btn.setFixedWidth(100)
        btn.clicked.connect(self._parcourir_justificatif)
        file_row.addWidget(btn)
        group_layout.addLayout(file_row)

        self.content_layout.addWidget(group)

    def _parcourir_justificatif(self):
        from PyQt5.QtWidgets import QFileDialog
        fichier, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le document justificatif",
            "",
            "Tous les fichiers (*);;Documents PDF (*.pdf);;Images (*.png *.jpg *.jpeg);;Documents Word (*.docx *.doc)"
        )
        if fichier:
            self._justificatif_path = fichier
            self._justificatif_label.setText(fichier)

    def _valider_justificatif(self):
        """Retourne (True, '') si un fichier est sélectionné, sinon (False, message)."""
        if not getattr(self, '_justificatif_path', None):
            return False, "Un document justificatif est obligatoire pour cette saisie."
        return True, ""

    def _sauvegarder_justificatif(
        self,
        operateur_id: int,
        formation_id: int = None,
        contrat_id: int = None,
        declaration_id: int = None,
        date_expiration=None,
        notes: str = None,
    ):
        """
        Upload le justificatif en document DMS après création du record.
        Cherche la catégorie dont le nom contient self._justificatif_categorie_nom.
        """
        path = getattr(self, '_justificatif_path', None)
        if not path:
            return None
        import os
        from domain.services.documents.document_service import DocumentService
        from domain.services.admin.auth_service import get_current_user
        from domain.services.rh.rh_service import get_categories_documents

        categorie_nom_hint = getattr(self, '_justificatif_categorie_nom', '')
        categories = get_categories_documents()

        categorie_id = None
        for cat in categories:
            if categorie_nom_hint and categorie_nom_hint.lower() in cat['nom'].lower():
                categorie_id = cat['id']
                break
        if categorie_id is None and categories:
            categorie_id = categories[0]['id']

        user = get_current_user()
        uploaded_by = user.get('nom_complet', 'Utilisateur') if user else 'Utilisateur'
        nom_affichage = os.path.basename(path)

        try:
            doc_service = DocumentService()
            success, _, document_id = doc_service.add_document(
                personnel_id=operateur_id,
                categorie_id=categorie_id,
                fichier_source=path,
                nom_affichage=nom_affichage,
                date_expiration=date_expiration,
                notes=notes,
                uploaded_by=uploaded_by,
                formation_id=formation_id,
                contrat_id=contrat_id,
                declaration_id=declaration_id,
            )
            return document_id if success else None
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Justificatif non sauvegardé pour operateur {operateur_id}: {e}"
            )
        return None


class ConsulterDetailDialog:
    """Dialog générique lecture seule — affiche un enregistrement RH sous forme de fiche."""

    def __init__(self, title: str, fields: list, parent=None):
        """
        Args:
            title:  Titre de la fenêtre.
            fields: Liste de tuples (label, valeur) à afficher.
        """
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QFormLayout, QLabel, QPushButton,
            QScrollArea, QWidget, QFrame
        )
        from PyQt5.QtCore import Qt

        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(420)
        dialog.resize(460, min(120 + len(fields) * 32, 560))

        main = QVBoxLayout(dialog)
        main.setContentsMargins(20, 16, 20, 16)
        main.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        form = QFormLayout(content)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        for label, value in fields:
            key = QLabel(f"{label} :")
            key.setStyleSheet("color: #6b7280; font-weight: bold;")
            val = QLabel(str(value) if value not in (None, '') else '—')
            val.setWordWrap(True)
            val.setStyleSheet("color: #111827;")
            form.addRow(key, val)

        scroll.setWidget(content)
        main.addWidget(scroll, 1)

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setFixedHeight(36)
        btn_fermer.clicked.connect(dialog.accept)
        main.addWidget(btn_fermer, alignment=Qt.AlignRight)

        dialog.exec_()
