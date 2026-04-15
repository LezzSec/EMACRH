# -*- coding: utf-8 -*-
"""
AjouterDocumentDialog — formulaire pour ajouter un document à un opérateur.
"""

from PyQt5.QtWidgets import (
    QFormLayout, QHBoxLayout, QLineEdit, QComboBox, QDateEdit, QCheckBox, QTextEdit
)
from PyQt5.QtCore import QDate

from gui.components.ui_theme import EmacButton
from gui.components.emac_dialog import EmacFormDialog
from domain.services.rh.rh_service import get_categories_documents, CATEGORIE_TO_DOMAINE, DomaineRH


class AjouterDocumentDialog(EmacFormDialog):
    """Formulaire pour ajouter un document à un opérateur."""

    def __init__(self, operateur_id: int, domaine: 'DomaineRH' = None, parent=None):
        self.operateur_id = operateur_id
        self.domaine = domaine
        self.fichier_path = None
        super().__init__(title="Ajouter un document", min_width=500, min_height=400, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(12)

        file_layout = QHBoxLayout()
        self.file_label = QLineEdit()
        self.file_label.setReadOnly(True)
        self.file_label.setPlaceholderText("Aucun fichier sélectionné...")
        file_layout.addWidget(self.file_label)

        btn_parcourir = EmacButton("Parcourir...", variant="ghost")
        btn_parcourir.clicked.connect(self._parcourir_fichier)
        file_layout.addWidget(btn_parcourir)
        form.addRow("Fichier:", file_layout)

        self.nom_affichage = QLineEdit()
        self.nom_affichage.setPlaceholderText("Nom qui sera affiché (optionnel)")
        form.addRow("Nom d'affichage:", self.nom_affichage)

        self.categorie_combo = QComboBox()
        self._charger_categories()
        form.addRow("Catégorie:", self.categorie_combo)

        exp_layout = QHBoxLayout()
        self.date_expiration = QDateEdit()
        self.date_expiration.setCalendarPopup(True)
        self.date_expiration.setDisplayFormat("dd/MM/yyyy")
        self.date_expiration.setSpecialValueText("Pas d'expiration")
        self.date_expiration.setMinimumDate(QDate(1900, 1, 1))
        self.date_expiration.setDate(QDate(1900, 1, 1))
        exp_layout.addWidget(self.date_expiration)

        self.chk_expiration = QCheckBox("Définir une date d'expiration")
        self.chk_expiration.toggled.connect(self.date_expiration.setEnabled)
        self.date_expiration.setEnabled(False)
        exp_layout.addWidget(self.chk_expiration)
        form.addRow("Expiration:", exp_layout)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Notes ou commentaires (optionnel)")
        form.addRow("Notes:", self.notes)

        self.content_layout.addLayout(form)

    def _charger_categories(self):
        """Charge les catégories de documents filtrées par domaine actif."""
        self.categorie_combo.clear()

        categories = get_categories_documents()

        cats_domaine = [
            cat for cat in categories
            if CATEGORIE_TO_DOMAINE.get(cat['nom'], DomaineRH.GENERAL) == self.domaine
        ] if self.domaine else categories

        for cat in cats_domaine:
            self.categorie_combo.addItem(cat['nom'], cat['id'])

        if self.categorie_combo.count() == 1:
            self.categorie_combo.setCurrentIndex(0)

    def _parcourir_fichier(self):
        """Ouvre le dialogue de sélection de fichier."""
        from PyQt5.QtWidgets import QFileDialog
        fichier, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un document",
            "",
            "Tous les fichiers (*);;Documents PDF (*.pdf);;Images (*.png *.jpg *.jpeg);;Documents Word (*.docx *.doc)"
        )
        if fichier:
            self.fichier_path = fichier
            self.file_label.setText(fichier)
            if not self.nom_affichage.text():
                import os
                self.nom_affichage.setText(os.path.basename(fichier))

    def validate(self):
        if not self.fichier_path:
            return False, "Veuillez sélectionner un fichier"
        if self.categorie_combo.currentIndex() < 0:
            return False, "Veuillez sélectionner une catégorie"
        return True, ""

    def save_to_db(self):
        categorie_id = self.categorie_combo.currentData()
        nom = self.nom_affichage.text().strip() or None

        date_exp = None
        if self.chk_expiration.isChecked() and self.date_expiration.date().year() > 1900:
            date_exp = self.date_expiration.date().toPyDate()

        notes = self.notes.toPlainText().strip() or None

        from domain.services.documents.document_service import DocumentService
        from domain.services.admin.auth_service import get_current_user

        user = get_current_user()
        uploaded_by = user.get('nom_complet', 'Utilisateur') if user else 'Utilisateur'

        doc_service = DocumentService()
        success, message, doc_id = doc_service.add_document(
            personnel_id=self.operateur_id,
            categorie_id=categorie_id,
            fichier_source=self.fichier_path,
            nom_affichage=nom,
            date_expiration=date_exp,
            notes=notes,
            uploaded_by=uploaded_by
        )

        if not success:
            raise Exception(message)
