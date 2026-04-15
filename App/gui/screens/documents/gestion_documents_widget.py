"""
Interface de gestion documentaire pour les opérateurs
Widget intégrable dans la fiche opérateur
"""

import sys
from pathlib import Path
from datetime import datetime, date

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QComboBox, QLabel,
    QDialog, QLineEdit, QTextEdit, QDateEdit, QHeaderView, QMenu,
    QAbstractItemView, QGroupBox
)
from PyQt5.QtCore import Qt, QDate, QUrl, pyqtSignal
from PyQt5.QtGui import QColor, QDesktopServices

# Import du service documentaire
from domain.services.documents.document_service import DocumentService


class DocumentWidget(QWidget):
    """Widget de gestion documentaire pour un opérateur"""
    
    # Signal émis quand un document est ajouté/modifié/supprimé
    documents_changed = pyqtSignal()
    
    def __init__(self, operateur_id: int, parent=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.doc_service = DocumentService()
        self.init_ui()
        self.load_documents()
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        
        # === Barre d'outils ===
        toolbar = QHBoxLayout()
        
        # Bouton Ajouter
        self.btn_add = QPushButton("Ajouter un document")
        self.btn_add.clicked.connect(self.add_document)
        toolbar.addWidget(self.btn_add)
        
        # Filtre par catégorie
        toolbar.addWidget(QLabel("Catégorie:"))
        self.combo_categorie = QComboBox()
        self.combo_categorie.addItem("Toutes", None)
        self.load_categories()
        self.combo_categorie.currentIndexChanged.connect(self.load_documents)
        toolbar.addWidget(self.combo_categorie)
        
        # Filtre par statut
        toolbar.addWidget(QLabel("Statut:"))
        self.combo_statut = QComboBox()
        self.combo_statut.addItem("Tous", None)
        self.combo_statut.addItem("Actifs", "actif")
        self.combo_statut.addItem("Expirés", "expire")
        self.combo_statut.addItem("Archivés", "archive")
        self.combo_statut.currentIndexChanged.connect(self.load_documents)
        toolbar.addWidget(self.combo_statut)
        
        toolbar.addStretch()
        
        # Bouton Rafraîchir
        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.clicked.connect(self.load_documents)
        toolbar.addWidget(self.btn_refresh)
        
        layout.addLayout(toolbar)
        
        # === GroupBox d'alertes ===
        self.alert_group = QGroupBox("Alertes")
        alert_layout = QVBoxLayout()
        self.alert_label = QLabel("Aucune alerte")
        self.alert_label.setStyleSheet("color: #059669; font-weight: bold;")
        alert_layout.addWidget(self.alert_label)
        self.alert_group.setLayout(alert_layout)
        layout.addWidget(self.alert_group)
        
        # === Tableau des documents ===
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Catégorie", "Nom du document", "Taille", 
            "Date d'ajout", "Date d'expiration", "Statut", "Notes", "Ajouté par"
        ])
        
        # Configuration du tableau
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.doubleClicked.connect(self.open_document)
        
        # Cacher la colonne ID
        self.table.setColumnHidden(0, True)
        
        layout.addWidget(self.table)
        
        # === Barre de statut ===
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.status_label)
    
    def load_categories(self):
        """Charge les catégories dans le combo"""
        categories = self.doc_service.get_categories()
        for cat in categories:
            self.combo_categorie.addItem(cat['nom'], cat['id'])
    
    def load_documents(self):
        """Charge les documents dans le tableau"""
        # Récupérer les filtres
        categorie_id = self.combo_categorie.currentData()
        statut = self.combo_statut.currentData()
        
        # Récupérer les documents
        documents = self.doc_service.get_documents_operateur(
            self.operateur_id,
            categorie_id=categorie_id,
            statut=statut
        )
        
        # Remplir le tableau
        self.table.setRowCount(len(documents))
        
        for row, doc in enumerate(documents):
            # ID (caché)
            self.table.setItem(row, 0, QTableWidgetItem(str(doc['id'])))
            
            # Catégorie avec couleur
            cat_item = QTableWidgetItem(doc['categorie_nom'])
            if doc['categorie_couleur']:
                cat_item.setBackground(QColor(doc['categorie_couleur'] + "20"))
                cat_item.setForeground(QColor(doc['categorie_couleur']))
            self.table.setItem(row, 1, cat_item)
            
            # Nom du document
            self.table.setItem(row, 2, QTableWidgetItem(doc['nom_affichage']))
            
            # Taille
            if doc['taille_mo'] and doc['taille_mo'] >= 1:
                taille = f"{doc['taille_mo']:.2f} Mo"
            else:
                taille = f"{doc['taille_ko']:.2f} Ko"
            self.table.setItem(row, 3, QTableWidgetItem(taille))
            
            # Date d'ajout
            date_upload = doc['date_upload']
            if isinstance(date_upload, datetime):
                date_str = date_upload.strftime("%d/%m/%Y %H:%M")
            else:
                date_str = str(date_upload)
            self.table.setItem(row, 4, QTableWidgetItem(date_str))
            
            # Date d'expiration avec alerte
            exp_item = QTableWidgetItem("")
            if doc['date_expiration']:
                date_exp = doc['date_expiration']
                if isinstance(date_exp, str):
                    date_exp = datetime.strptime(date_exp, "%Y-%m-%d").date()
                
                exp_item.setText(date_exp.strftime("%d/%m/%Y"))
                
                # Colorier selon l'alerte
                if doc['alerte_expiration'] == 'Expiré':
                    exp_item.setBackground(QColor("#fecaca"))
                    exp_item.setForeground(QColor("#991b1b"))
                elif doc['alerte_expiration'] == 'Expire bientôt':
                    exp_item.setBackground(QColor("#fed7aa"))
                    exp_item.setForeground(QColor("#9a3412"))
            
            self.table.setItem(row, 5, exp_item)
            
            # Statut
            statut_item = QTableWidgetItem(doc['statut'].capitalize())
            if doc['statut'] == 'actif':
                statut_item.setForeground(QColor("#059669"))
            elif doc['statut'] == 'expire':
                statut_item.setForeground(QColor("#dc2626"))
            else:  # archive
                statut_item.setForeground(QColor("#64748b"))
            self.table.setItem(row, 6, statut_item)
            
            # Notes (tronquées)
            notes = doc['notes'] or ""
            if len(notes) > 50:
                notes = notes[:50] + "..."
            notes_item = QTableWidgetItem(notes)
            notes_item.setToolTip(doc['notes'] or "")
            self.table.setItem(row, 7, notes_item)
            
            # Ajouté par
            self.table.setItem(row, 8, QTableWidgetItem(doc['uploaded_by'] or ""))
        
        # Ajuster les colonnes
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Mettre à jour le statut
        self.status_label.setText(f"{len(documents)} document(s) affiché(s)")
        
        # Mettre à jour les alertes
        self.update_alerts(documents)
    
    def update_alerts(self, documents):
        """Met à jour l'affichage des alertes"""
        expires = [d for d in documents if d.get('alerte_expiration') == 'Expiré']
        expire_bientot = [d for d in documents if d.get('alerte_expiration') == 'Expire bientôt']
        
        if expires or expire_bientot:
            messages = []
            if expires:
                messages.append(f"{len(expires)} document(s) expiré(s)")
            if expire_bientot:
                messages.append(f"{len(expire_bientot)} document(s) expire(nt) bientôt")
            
            self.alert_label.setText(" | ".join(messages))
            self.alert_label.setStyleSheet("color: #dc2626; font-weight: bold;")
        else:
            self.alert_label.setText("Aucune alerte")
            self.alert_label.setStyleSheet("color: #059669; font-weight: bold;")
    
    def add_document(self):
        """Ouvre le dialogue d'ajout de document"""
        dialog = AddDocumentDialog(self.operateur_id, self.doc_service, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_documents()
            self.documents_changed.emit()
    
    def open_document(self):
        """Ouvre le document selectionne (extrait depuis la base si BLOB)"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        doc_id = int(self.table.item(current_row, 0).text())
        file_path = self.doc_service.get_document_path(doc_id)

        if file_path and file_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))
        else:
            QMessageBox.warning(
                self,
                "Fichier introuvable",
                "Impossible de recuperer le contenu du document."
            )
    
    def show_context_menu(self, position):
        """Affiche le menu contextuel"""
        if self.table.currentRow() < 0:
            return
        
        menu = QMenu()

        action_open = menu.addAction("Ouvrir")
        action_download = menu.addAction("Telecharger")
        action_edit = menu.addAction("Modifier les informations")
        menu.addSeparator()
        action_archive = menu.addAction("Archiver")
        action_delete = menu.addAction("Supprimer")

        action = menu.exec_(self.table.viewport().mapToGlobal(position))

        if action == action_open:
            self.open_document()
        elif action == action_download:
            self.download_document()
        elif action == action_edit:
            self.edit_document()
        elif action == action_archive:
            self.archive_document()
        elif action == action_delete:
            self.delete_document()
    
    def edit_document(self):
        """Édite les informations d'un document"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        
        doc_id = int(self.table.item(current_row, 0).text())
        
        # Récupérer les infos actuelles
        documents = self.doc_service.get_documents_operateur(self.operateur_id)
        doc = next((d for d in documents if d['id'] == doc_id), None)
        
        if not doc:
            return
        
        dialog = EditDocumentDialog(doc, self.doc_service, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_documents()
            self.documents_changed.emit()
    
    def archive_document(self):
        """Archive le document sélectionné"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        
        doc_id = int(self.table.item(current_row, 0).text())
        nom = self.table.item(current_row, 2).text()
        
        reply = QMessageBox.question(
            self,
            "Archiver le document",
            f"Voulez-vous archiver le document '{nom}' ?\n\n"
            "Le document restera accessible mais ne sera plus affiché par défaut.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.doc_service.archive_document(doc_id)
            if success:
                QMessageBox.information(self, "Succès", message)
                self.load_documents()
                self.documents_changed.emit()
            else:
                QMessageBox.warning(self, "Erreur", message)
    
    def delete_document(self):
        """Supprime le document sélectionné"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        
        doc_id = int(self.table.item(current_row, 0).text())
        nom = self.table.item(current_row, 2).text()
        
        reply = QMessageBox.question(
            self,
            "Supprimer le document",
            f"Voulez-vous DÉFINITIVEMENT supprimer le document '{nom}' ?\n\n"
            "Cette action est irréversible !",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.doc_service.delete_document(doc_id)
            if success:
                QMessageBox.information(self, "Succès", message)
                self.load_documents()
                self.documents_changed.emit()
            else:
                QMessageBox.warning(self, "Erreur", message)


    def download_document(self):
        """Telecharge le document selectionne vers un emplacement choisi"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        doc_id = int(self.table.item(current_row, 0).text())
        nom = self.table.item(current_row, 2).text()

        # Ouvrir le dialogue de sauvegarde
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Telecharger le document",
            nom,
            "Tous les fichiers (*.*)"
        )

        if file_path:
            success, message = self.doc_service.download_document(doc_id, file_path)
            if success:
                QMessageBox.information(self, "Succes", message)
            else:
                QMessageBox.warning(self, "Erreur", message)


class AddDocumentDialog(QDialog):
    """Dialogue pour ajouter un document"""
    
    def __init__(self, operateur_id: int, doc_service: DocumentService, parent=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.doc_service = doc_service
        self.selected_file = None
        
        self.setWindowTitle("Ajouter un document")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Sélection du fichier
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Fichier:"))
        self.file_label = QLabel("Aucun fichier sélectionné")
        self.file_label.setStyleSheet("color: #64748b; font-style: italic;")
        file_layout.addWidget(self.file_label)
        file_layout.addStretch()
        self.btn_browse = QPushButton("Parcourir...")
        self.btn_browse.clicked.connect(self.browse_file)
        file_layout.addWidget(self.btn_browse)
        layout.addLayout(file_layout)
        
        # Nom d'affichage
        layout.addWidget(QLabel("Nom d'affichage:"))
        self.edit_nom = QLineEdit()
        self.edit_nom.setPlaceholderText("Nom du document tel qu'il apparaîtra")
        layout.addWidget(self.edit_nom)
        
        # Catégorie
        layout.addWidget(QLabel("Catégorie:"))
        self.combo_categorie = QComboBox()
        categories = self.doc_service.get_categories()
        for cat in categories:
            self.combo_categorie.addItem(cat['nom'], cat['id'])
        layout.addWidget(self.combo_categorie)
        
        # Date d'expiration
        layout.addWidget(QLabel("Date d'expiration (optionnelle):"))
        self.date_expiration = QDateEdit()
        self.date_expiration.setCalendarPopup(True)
        self.date_expiration.setDate(QDate.currentDate().addYears(1))
        self.date_expiration.setSpecialValueText("Aucune")
        self.date_expiration.setMinimumDate(QDate.currentDate())
        layout.addWidget(self.date_expiration)
        
        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.edit_notes = QTextEdit()
        self.edit_notes.setMaximumHeight(80)
        self.edit_notes.setPlaceholderText("Notes ou commentaires sur le document")
        layout.addWidget(self.edit_notes)
        
        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_ok = QPushButton("Ajouter")
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.accept_dialog)
        btn_layout.addWidget(self.btn_ok)
        
        layout.addLayout(btn_layout)
    
    def browse_file(self):
        """Ouvre le dialogue de sélection de fichier"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un document",
            "",
            "Tous les fichiers (*.*)"
        )
        
        if file_path:
            self.selected_file = file_path
            filename = Path(file_path).name
            self.file_label.setText(filename)
            self.file_label.setStyleSheet("color: #059669; font-weight: bold;")
            
            # Proposer le nom du fichier comme nom d'affichage
            if not self.edit_nom.text():
                self.edit_nom.setText(filename)
            
            self.btn_ok.setEnabled(True)
    
    def accept_dialog(self):
        """Valide et ajoute le document"""
        if not self.selected_file:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier")
            return
        
        nom_affichage = self.edit_nom.text().strip()
        if not nom_affichage:
            nom_affichage = Path(self.selected_file).name
        
        categorie_id = self.combo_categorie.currentData()
        
        # Date d'expiration
        date_exp = None
        if self.date_expiration.date() != QDate.currentDate():
            qdate = self.date_expiration.date()
            date_exp = date(qdate.year(), qdate.month(), qdate.day())
        
        notes = self.edit_notes.toPlainText().strip() or None
        
        # Ajouter le document
        success, message, doc_id = self.doc_service.add_document(
            personnel_id=self.operateur_id,
            categorie_id=categorie_id,
            fichier_source=self.selected_file,
            nom_affichage=nom_affichage,
            date_expiration=date_exp,
            notes=notes,
            uploaded_by="Utilisateur"  # À personnaliser selon votre système d'auth
        )
        
        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", message)


class EditDocumentDialog(QDialog):
    """Dialogue pour éditer les informations d'un document"""
    
    def __init__(self, document: dict, doc_service: DocumentService, parent=None):
        super().__init__(parent)
        self.document = document
        self.doc_service = doc_service
        
        self.setWindowTitle("Modifier les informations du document")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Nom d'affichage
        layout.addWidget(QLabel("Nom d'affichage:"))
        self.edit_nom = QLineEdit()
        self.edit_nom.setText(self.document['nom_affichage'])
        layout.addWidget(self.edit_nom)
        
        # Catégorie
        layout.addWidget(QLabel("Catégorie:"))
        self.combo_categorie = QComboBox()
        categories = self.doc_service.get_categories()
        for idx, cat in enumerate(categories):
            self.combo_categorie.addItem(cat['nom'], cat['id'])
            if cat['id'] == self.document['categorie_id']:
                self.combo_categorie.setCurrentIndex(idx)
        layout.addWidget(self.combo_categorie)
        
        # Date d'expiration
        layout.addWidget(QLabel("Date d'expiration:"))
        self.date_expiration = QDateEdit()
        self.date_expiration.setCalendarPopup(True)
        self.date_expiration.setSpecialValueText("Aucune")
        
        if self.document['date_expiration']:
            date_exp = self.document['date_expiration']
            if isinstance(date_exp, str):
                date_exp = datetime.strptime(date_exp, "%Y-%m-%d").date()
            self.date_expiration.setDate(QDate(date_exp.year, date_exp.month, date_exp.day))
        else:
            self.date_expiration.setDate(QDate.currentDate())
        
        layout.addWidget(self.date_expiration)
        
        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.edit_notes = QTextEdit()
        self.edit_notes.setMaximumHeight(100)
        if self.document['notes']:
            self.edit_notes.setPlainText(self.document['notes'])
        layout.addWidget(self.edit_notes)
        
        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_ok = QPushButton("Enregistrer")
        self.btn_ok.clicked.connect(self.accept_dialog)
        btn_layout.addWidget(self.btn_ok)
        
        layout.addLayout(btn_layout)
    
    def accept_dialog(self):
        """Valide et met à jour le document"""
        nom_affichage = self.edit_nom.text().strip()
        categorie_id = self.combo_categorie.currentData()
        
        # Date d'expiration
        date_exp = None
        qdate = self.date_expiration.date()
        if qdate != QDate.currentDate():
            date_exp = date(qdate.year(), qdate.month(), qdate.day())
        
        notes = self.edit_notes.toPlainText().strip() or None
        
        # Mettre à jour
        success, message = self.doc_service.update_document_info(
            document_id=self.document['id'],
            nom_affichage=nom_affichage,
            date_expiration=date_exp,
            notes=notes,
            categorie_id=categorie_id
        )
        
        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", message)


# ============================================================================
# WIDGET STANDALONE POUR TESTER
# ============================================================================

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test avec un opérateur ID fictif
    widget = DocumentWidget(operateur_id=1)
    widget.setWindowTitle("Test - Gestion Documentaire")
    widget.resize(1000, 600)
    widget.show()
    
    sys.exit(app.exec_())