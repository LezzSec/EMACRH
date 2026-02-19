# -*- coding: utf-8 -*-
"""
Interface de gestion documentaire RH
Permet d'ajouter, visualiser, télécharger et supprimer des documents RH
"""

import os
import sys
import logging
from datetime import datetime, date
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QFileDialog,
    QMessageBox, QWidget, QTabWidget, QTextEdit, QDateEdit, QGroupBox,
    QAbstractItemView, QMenu, QCheckBox, QGridLayout
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QUrl
from PyQt5.QtGui import QFont, QColor, QIcon, QDesktopServices

from core.services.document_service import DocumentService
from core.repositories.personnel_repo import PersonnelRepository
from core.services.logger import log_hist
from core.gui.emac_ui_kit import add_custom_title_bar, show_error_message
from core.utils.logging_config import get_logger

logger = get_logger(__name__)

# Import des composants modernes EMAC
try:
    from core.gui.ui_theme import EmacCard, EmacButton
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False


class GestionDocumentaireDialog(QDialog):
    """Fenêtre principale de gestion documentaire RH"""

    document_added = pyqtSignal()  # Signal émis lors de l'ajout d'un document

    def __init__(self, operateur_id=None, parent=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.doc_service = DocumentService()

        self.setWindowTitle("Gestion Documentaire RH")
        self.setGeometry(100, 100, 1200, 700)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialise l'interface utilisateur moderne"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Gestion Documentaire RH")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(16)

        # === En-tête avec sélection opérateur ===
        if THEME_AVAILABLE:
            header_card = EmacCard()
            header_layout = QHBoxLayout()

            # Sélection d'opérateur
            operateur_label = QLabel("👤 Employé:")
            operateur_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
            operateur_label.setStyleSheet("color: #1e293b;")
            header_layout.addWidget(operateur_label)

            self.operateur_combo = QComboBox()
            self.operateur_combo.setMinimumWidth(250)
            self.operateur_combo.currentIndexChanged.connect(self.on_operateur_changed)
            self.operateur_combo.setStyleSheet("""
                QComboBox {
                    padding: 8px 12px;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    background: white;
                }
            """)
            header_layout.addWidget(self.operateur_combo)

            header_layout.addStretch()

            # Boutons
            btn_refresh = EmacButton("🔄 Actualiser", 'ghost')
            btn_refresh.clicked.connect(self.load_data)
            header_layout.addWidget(btn_refresh)

            btn_add = EmacButton("➕ Ajouter un document", 'primary')
            btn_add.clicked.connect(self.add_document)
            header_layout.addWidget(btn_add)

            header_card.body.addLayout(header_layout)
            layout.addWidget(header_card)
        else:
            # Fallback simple
            header_layout = QHBoxLayout()

            operateur_label = QLabel("Employé :")
            operateur_label.setFont(QFont("Arial", 10, QFont.Bold))
            header_layout.addWidget(operateur_label)

            self.operateur_combo = QComboBox()
            self.operateur_combo.setMinimumWidth(250)
            self.operateur_combo.currentIndexChanged.connect(self.on_operateur_changed)
            header_layout.addWidget(self.operateur_combo)

            header_layout.addStretch()

            btn_refresh = QPushButton("🔄 Rafraîchir")
            btn_refresh.clicked.connect(self.load_data)
            header_layout.addWidget(btn_refresh)

            btn_add = QPushButton("➕ Ajouter un document")
            btn_add.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
            btn_add.clicked.connect(self.add_document)
            header_layout.addWidget(btn_add)

            layout.addLayout(header_layout)

        # === Filtres modernes ===
        if THEME_AVAILABLE:
            filters_card = EmacCard()
            filters_layout = QHBoxLayout()

            # Filtre catégorie
            cat_label = QLabel("📁 Catégorie:")
            cat_label.setStyleSheet("color: #475569; font-weight: 600;")
            filters_layout.addWidget(cat_label)

            self.categorie_filter = QComboBox()
            self.categorie_filter.addItem("Toutes les catégories", None)
            self.categorie_filter.currentIndexChanged.connect(self.apply_filters)
            self.categorie_filter.setStyleSheet("""
                QComboBox {
                    padding: 6px 12px;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    background: white;
                    min-width: 150px;
                }
            """)
            filters_layout.addWidget(self.categorie_filter)

            filters_layout.addSpacing(15)

            # Filtre statut
            statut_label = QLabel("📊 Statut:")
            statut_label.setStyleSheet("color: #475569; font-weight: 600;")
            filters_layout.addWidget(statut_label)

            self.statut_filter = QComboBox()
            self.statut_filter.addItems(["Tous", "Actif", "Expiré", "Archivé"])
            self.statut_filter.currentIndexChanged.connect(self.apply_filters)
            self.statut_filter.setStyleSheet("""
                QComboBox {
                    padding: 6px 12px;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    background: white;
                    min-width: 120px;
                }
            """)
            filters_layout.addWidget(self.statut_filter)

            filters_layout.addSpacing(15)

            # Recherche
            search_label = QLabel("🔍 Recherche:")
            search_label.setStyleSheet("color: #475569; font-weight: 600;")
            filters_layout.addWidget(search_label)

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Nom du fichier...")
            self.search_input.textChanged.connect(self.apply_filters)
            self.search_input.setStyleSheet("""
                QLineEdit {
                    padding: 6px 12px;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    background: white;
                    min-width: 200px;
                }
            """)
            filters_layout.addWidget(self.search_input)

            filters_layout.addStretch()
            filters_card.body.addLayout(filters_layout)
            layout.addWidget(filters_card)
        else:
            # Fallback
            filters_group = QGroupBox("Filtres")
            filters_layout = QHBoxLayout()

            cat_label = QLabel("Catégorie :")
            filters_layout.addWidget(cat_label)

            self.categorie_filter = QComboBox()
            self.categorie_filter.addItem("Toutes les catégories", None)
            self.categorie_filter.currentIndexChanged.connect(self.apply_filters)
            filters_layout.addWidget(self.categorie_filter)

            statut_label = QLabel("Statut :")
            filters_layout.addWidget(statut_label)

            self.statut_filter = QComboBox()
            self.statut_filter.addItems(["Tous", "Actif", "Expiré", "Archivé"])
            self.statut_filter.currentIndexChanged.connect(self.apply_filters)
            filters_layout.addWidget(self.statut_filter)

            search_label = QLabel("Recherche :")
            filters_layout.addWidget(search_label)

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Nom du fichier...")
            self.search_input.textChanged.connect(self.apply_filters)
            filters_layout.addWidget(self.search_input)

            filters_layout.addStretch()
            filters_group.setLayout(filters_layout)
            layout.addWidget(filters_group)

        # === Tableau moderne des documents ===
        if THEME_AVAILABLE:
            table_card = EmacCard()
            table_layout = QVBoxLayout()

            self.table = QTableWidget()
            self.table.setColumnCount(9)
            self.table.setHorizontalHeaderLabels([
                "ID", "Nom du fichier", "Catégorie", "Taille", "Date ajout",
                "Date expiration", "Statut", "Ajouté par", "Actions"
            ])

            # Configuration du tableau
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SingleSelection)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setAlternatingRowColors(True)
            self.table.horizontalHeader().setStretchLastSection(True)

            # Largeurs des colonnes
            self.table.setColumnWidth(0, 50)   # ID
            self.table.setColumnWidth(1, 250)  # Nom
            self.table.setColumnWidth(2, 150)  # Catégorie
            self.table.setColumnWidth(3, 80)   # Taille
            self.table.setColumnWidth(4, 120)  # Date ajout
            self.table.setColumnWidth(5, 120)  # Date expiration
            self.table.setColumnWidth(6, 100)  # Statut
            self.table.setColumnWidth(7, 120)  # Ajouté par

            # Style moderne EMAC
            self.table.setStyleSheet("""
                QTableWidget {
                    background-color: white;
                    alternate-background-color: #f8fafc;
                    gridline-color: #e2e8f0;
                    border: none;
                    font-size: 11px;
                }
                QHeaderView::section {
                    background: #f1f5f9;
                    color: #475569;
                    font-weight: bold;
                    padding: 10px;
                    border: none;
                    border-bottom: 2px solid #cbd5e1;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #f1f5f9;
                }
                QTableWidget::item:selected {
                    background: #dbeafe;
                    color: #1e293b;
                }
            """)

            # Menu contextuel
            self.table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.table.customContextMenuRequested.connect(self.show_context_menu)

            # Double-clic pour ouvrir
            self.table.doubleClicked.connect(self.open_document)

            table_layout.addWidget(self.table)
            table_card.body.addLayout(table_layout)
            layout.addWidget(table_card)
        else:
            # Fallback sans carte
            self.table = QTableWidget()
            self.table.setColumnCount(9)
            self.table.setHorizontalHeaderLabels([
                "ID", "Nom du fichier", "Catégorie", "Taille", "Date ajout",
                "Date expiration", "Statut", "Ajouté par", "Actions"
            ])

            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SingleSelection)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setAlternatingRowColors(True)
            self.table.horizontalHeader().setStretchLastSection(True)

            self.table.setColumnWidth(0, 50)
            self.table.setColumnWidth(1, 250)
            self.table.setColumnWidth(2, 150)
            self.table.setColumnWidth(3, 80)
            self.table.setColumnWidth(4, 120)
            self.table.setColumnWidth(5, 120)
            self.table.setColumnWidth(6, 100)
            self.table.setColumnWidth(7, 120)

            self.table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.table.customContextMenuRequested.connect(self.show_context_menu)
            self.table.doubleClicked.connect(self.open_document)

            layout.addWidget(self.table)

        # === Statistiques modernes ===
        if THEME_AVAILABLE:
            stats_card = EmacCard()
            stats_layout = QHBoxLayout()

            self.lbl_total = QLabel("📊 Total : 0")
            self.lbl_total.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.lbl_total.setStyleSheet("color: #3b82f6;")
            stats_layout.addWidget(self.lbl_total)

            stats_layout.addSpacing(20)

            self.lbl_size = QLabel("💾 Taille : 0 MB")
            self.lbl_size.setFont(QFont("Segoe UI", 10))
            self.lbl_size.setStyleSheet("color: #64748b;")
            stats_layout.addWidget(self.lbl_size)

            stats_layout.addSpacing(20)

            self.lbl_expired = QLabel("⚠️ Expirés : 0")
            self.lbl_expired.setFont(QFont("Segoe UI", 10))
            self.lbl_expired.setStyleSheet("color: #dc2626;")
            stats_layout.addWidget(self.lbl_expired)

            stats_layout.addStretch()
            stats_card.body.addLayout(stats_layout)
            layout.addWidget(stats_card)
        else:
            # Fallback simple
            stats_layout = QHBoxLayout()

            self.lbl_total = QLabel("Total : 0")
            self.lbl_total.setFont(QFont("Arial", 9, QFont.Bold))
            stats_layout.addWidget(self.lbl_total)

            self.lbl_size = QLabel("Taille : 0 MB")
            self.lbl_size.setFont(QFont("Arial", 9))
            stats_layout.addWidget(self.lbl_size)

            self.lbl_expired = QLabel("Expirés : 0")
            self.lbl_expired.setFont(QFont("Arial", 9))
            self.lbl_expired.setStyleSheet("color: #dc2626;")
            stats_layout.addWidget(self.lbl_expired)

            stats_layout.addStretch()
            layout.addLayout(stats_layout)

        main_layout.addWidget(content_widget)

    def load_data(self):
        """Charge les données (opérateurs et catégories)"""
        # Vérifier que les tables existent
        if not self.check_tables_exist():
            QMessageBox.warning(
                self,
                "Module non installé",
                "Le module de gestion documentaire n'est pas encore installé.\n\n"
                "Pour l'installer, exécutez :\n"
                "cd App/scripts\n"
                "python install_gestion_documentaire.py\n\n"
                "L'application va continuer mais certaines fonctionnalités seront limitées."
            )

        self.load_operateurs()
        self.load_categories()
        self.load_documents()

    def check_tables_exist(self):
        """Vérifie que les tables nécessaires existent"""
        return self.doc_service.check_module_installed()

    def load_operateurs(self):
        """Charge la liste des opérateurs"""
        try:
            operateurs = PersonnelRepository.get_all_actifs()

            self.operateur_combo.clear()
            self.operateur_combo.addItem("Tous les employés", None)

            for op in operateurs:
                display_name = f"{op.nom} {op.prenom}"
                self.operateur_combo.addItem(display_name, op.id)

            # Sélectionner l'opérateur si fourni
            if self.operateur_id:
                for i in range(self.operateur_combo.count()):
                    if self.operateur_combo.itemData(i) == self.operateur_id:
                        self.operateur_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            logger.exception(f"Erreur chargement operateurs: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les opérateurs", e)

    def load_categories(self):
        """Charge les catégories de documents (exclut les contrats car gérés dans module dédié)"""
        try:
            categories = self.doc_service.get_categories()

            self.categorie_filter.clear()
            self.categorie_filter.addItem("Toutes les catégories", None)

            # Exclure "Contrats de travail" car géré dans le module Gestion des Contrats
            for cat in categories:
                if cat['nom'] != 'Contrats de travail':
                    self.categorie_filter.addItem(cat['nom'], cat['id'])
        except Exception as e:
            # En cas d'erreur (table n'existe pas), continuer sans catégories
            self.categorie_filter.clear()
            self.categorie_filter.addItem("Toutes les catégories", None)
            logger.warning(f" Impossible de charger les catégories: {e}")

    def load_documents(self):
        """Charge les documents dans le tableau"""
        operateur_id = self.operateur_combo.currentData()

        # Récupérer les documents
        if operateur_id:
            documents = self.doc_service.get_documents_operateur(operateur_id)
        else:
            # Charger tous les documents
            documents = self.get_all_documents()

        self.display_documents(documents)
        self.update_stats(documents)

    def get_all_documents(self):
        """Récupère tous les documents de tous les opérateurs (sauf contrats)"""
        return self.doc_service.get_all_non_contrats()

    def display_documents(self, documents):
        """Affiche les documents dans le tableau"""
        self.table.setRowCount(0)

        for doc in documents:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(doc['id'])))

            # Nom du fichier
            self.table.setItem(row, 1, QTableWidgetItem(doc['nom_affichage']))

            # Catégorie
            cat_item = QTableWidgetItem(doc['categorie_nom'])
            if 'categorie_couleur' in doc:
                cat_item.setBackground(QColor(doc['categorie_couleur']))
                cat_item.setForeground(QColor("white"))
            self.table.setItem(row, 2, cat_item)

            # Taille
            taille_text = self.format_size(doc.get('taille_octets', 0))
            self.table.setItem(row, 3, QTableWidgetItem(taille_text))

            # Date ajout
            date_upload = doc.get('date_upload', '')
            if isinstance(date_upload, datetime):
                date_upload = date_upload.strftime('%d/%m/%Y')
            elif isinstance(date_upload, str):
                pass  # Déjà une chaîne
            else:
                date_upload = ''
            self.table.setItem(row, 4, QTableWidgetItem(date_upload))

            # Date expiration
            date_exp = doc.get('date_expiration', '')
            if date_exp:
                if isinstance(date_exp, (datetime, date)):
                    date_exp = date_exp.strftime('%d/%m/%Y')
            else:
                date_exp = "—"
            self.table.setItem(row, 5, QTableWidgetItem(str(date_exp)))

            # Statut
            statut_item = QTableWidgetItem(doc.get('statut', 'actif').capitalize())
            if doc.get('statut') == 'expire':
                statut_item.setForeground(QColor("#dc2626"))
                statut_item.setBackground(QColor("#fee2e2"))
            elif doc.get('alerte_expiration') == 'Expire bientôt':
                statut_item.setForeground(QColor("#d97706"))
                statut_item.setBackground(QColor("#fef3c7"))
            else:
                statut_item.setForeground(QColor("#059669"))

            self.table.setItem(row, 6, statut_item)

            # Ajouté par
            self.table.setItem(row, 7, QTableWidgetItem(doc.get('uploaded_by', '')))

            # Boutons d'actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            btn_open = QPushButton("📂")
            btn_open.setToolTip("Ouvrir le document")
            btn_open.setMaximumWidth(30)
            btn_open.clicked.connect(lambda checked, d=doc: self.open_document_by_id(d['id']))
            actions_layout.addWidget(btn_open)

            btn_download = QPushButton("💾")
            btn_download.setToolTip("Télécharger")
            btn_download.setMaximumWidth(30)
            btn_download.clicked.connect(lambda checked, d=doc: self.download_document(d['id']))
            actions_layout.addWidget(btn_download)

            btn_delete = QPushButton("🗑️")
            btn_delete.setToolTip("Supprimer")
            btn_delete.setMaximumWidth(30)
            btn_delete.setStyleSheet("QPushButton { color: #dc2626; }")
            btn_delete.clicked.connect(lambda checked, d=doc: self.delete_document(d['id']))
            actions_layout.addWidget(btn_delete)

            actions_layout.addStretch()
            self.table.setCellWidget(row, 8, actions_widget)

    def format_size(self, bytes):
        """Formate la taille d'un fichier"""
        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1024 * 1024:
            return f"{bytes / 1024:.1f} KB"
        else:
            return f"{bytes / (1024 * 1024):.1f} MB"

    def update_stats(self, documents):
        """Met à jour les statistiques"""
        total = len(documents)
        total_size = sum(doc.get('taille_octets', 0) for doc in documents)
        expired = sum(1 for doc in documents if doc.get('statut') == 'expire')

        self.lbl_total.setText(f"Total : {total}")
        self.lbl_size.setText(f"Taille : {total_size / (1024 * 1024):.2f} MB")
        self.lbl_expired.setText(f"Expirés : {expired}")

    def on_operateur_changed(self, index):
        """Appelé quand l'opérateur sélectionné change"""
        self.load_documents()

    def apply_filters(self):
        """Applique les filtres de recherche"""
        self.load_documents()

    def add_document(self):
        """Ouvre la fenêtre d'ajout de document"""
        operateur_id = self.operateur_combo.currentData()

        if not operateur_id:
            QMessageBox.warning(
                self,
                "Attention",
                "Veuillez sélectionner un employé avant d'ajouter un document."
            )
            return

        dialog = AddDocumentDialog(operateur_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_documents()
            self.document_added.emit()

    def open_document(self):
        """Ouvre le document sélectionné"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        doc_id_item = self.table.item(current_row, 0)
        if doc_id_item:
            doc_id = int(doc_id_item.text())
            self.open_document_by_id(doc_id)

    def open_document_by_id(self, doc_id):
        """Ouvre un document par son ID"""
        filepath = self.doc_service.get_document_path(doc_id)

        if filepath and filepath.exists():
            try:
                # Ouvrir avec l'application par défaut
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(filepath)))

                # Log
                log_hist("CONSULTATION_DOCUMENT", f"Consultation du document ID {doc_id}")
            except Exception as e:
                logger.exception(f"Erreur ouverture document: {e}")
                show_error_message(self, "Erreur", "Impossible d'ouvrir le document", e)
        else:
            QMessageBox.warning(self, "Erreur", "Fichier introuvable sur le disque.")

    def download_document(self, doc_id):
        """Télécharge (copie) un document vers un emplacement choisi"""
        filepath = self.doc_service.get_document_path(doc_id)

        if not filepath or not filepath.exists():
            QMessageBox.warning(self, "Erreur", "Fichier introuvable.")
            return

        # Demander l'emplacement de destination
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le document",
            filepath.name,
            "Tous les fichiers (*.*)"
        )

        if dest_path:
            try:
                import shutil
                shutil.copy2(filepath, dest_path)
                QMessageBox.information(self, "Succès", "Document téléchargé avec succès.")

                # Log
                log_hist("TELECHARGEMENT_DOCUMENT", f"Téléchargement du document ID {doc_id}")
            except Exception as e:
                logger.exception(f"Erreur telechargement document: {e}")
                show_error_message(self, "Erreur", "Erreur lors du téléchargement", e)

    def delete_document(self, doc_id):
        """Supprime un document après confirmation"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir supprimer ce document ?\n\nCette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, message = self.doc_service.delete_document(doc_id)

            if success:
                QMessageBox.information(self, "Succès", message)
                self.load_documents()

                # Log
                log_hist("SUPPRESSION_DOCUMENT", f"Suppression du document ID {doc_id}")
            else:
                QMessageBox.warning(self, "Erreur", message)

    def show_context_menu(self, position):
        """Affiche le menu contextuel"""
        menu = QMenu()

        open_action = menu.addAction("📂 Ouvrir")
        download_action = menu.addAction("💾 Télécharger")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Supprimer")

        action = menu.exec_(self.table.viewport().mapToGlobal(position))

        current_row = self.table.currentRow()
        if current_row < 0:
            return

        doc_id = int(self.table.item(current_row, 0).text())

        if action == open_action:
            self.open_document_by_id(doc_id)
        elif action == download_action:
            self.download_document(doc_id)
        elif action == delete_action:
            self.delete_document(doc_id)


class AddDocumentDialog(QDialog):
    """Fenêtre d'ajout d'un nouveau document"""

    def __init__(self, operateur_id, parent=None, filter_category=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.filter_category = filter_category  # Catégorie à filtrer ou présélectionner
        self.doc_service = DocumentService()
        self.selected_file = None
        self.created_document_id = None  # ID du document créé (pour récupération externe)

        self.setWindowTitle("Ajouter un document")
        self.setGeometry(200, 200, 600, 500)

        self.init_ui()

    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Titre
        title = QLabel("Ajouter un nouveau document")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Sélection du fichier
        file_group = QGroupBox("Fichier")
        file_layout = QVBoxLayout()

        file_btn_layout = QHBoxLayout()
        self.btn_select_file = QPushButton("📁 Sélectionner un fichier...")
        self.btn_select_file.clicked.connect(self.select_file)
        file_btn_layout.addWidget(self.btn_select_file)
        file_layout.addLayout(file_btn_layout)

        self.lbl_selected_file = QLabel("Aucun fichier sélectionné")
        self.lbl_selected_file.setStyleSheet("color: #6b7280; font-style: italic;")
        file_layout.addWidget(self.lbl_selected_file)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Catégorie
        cat_layout = QHBoxLayout()
        cat_label = QLabel("Catégorie* :")
        cat_label.setMinimumWidth(120)
        cat_layout.addWidget(cat_label)

        self.categorie_combo = QComboBox()
        self.load_categories()
        cat_layout.addWidget(self.categorie_combo)
        layout.addLayout(cat_layout)

        # Nom d'affichage
        name_layout = QHBoxLayout()
        name_label = QLabel("Nom d'affichage :")
        name_label.setMinimumWidth(120)
        name_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Laissez vide pour utiliser le nom du fichier")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Date d'expiration
        exp_layout = QHBoxLayout()
        exp_label = QLabel("Date d'expiration :")
        exp_label.setMinimumWidth(120)
        exp_layout.addWidget(exp_label)

        self.date_expiration = QDateEdit()
        self.date_expiration.setCalendarPopup(True)
        self.date_expiration.setDate(QDate.currentDate().addYears(1))
        self.date_expiration.setDisplayFormat("dd/MM/yyyy")
        exp_layout.addWidget(self.date_expiration)

        self.cb_no_expiration = QCheckBox("Pas de date d'expiration")
        self.cb_no_expiration.setChecked(True)
        self.cb_no_expiration.stateChanged.connect(self.toggle_expiration_date)
        exp_layout.addWidget(self.cb_no_expiration)

        layout.addLayout(exp_layout)

        # Date du document
        doc_date_layout = QHBoxLayout()
        doc_date_label = QLabel("Date du document :")
        doc_date_label.setMinimumWidth(120)
        doc_date_layout.addWidget(doc_date_label)

        self.date_document = QDateEdit()
        self.date_document.setCalendarPopup(True)
        self.date_document.setDate(QDate.currentDate())
        self.date_document.setDisplayFormat("dd/MM/yyyy")
        doc_date_layout.addWidget(self.date_document)

        self.cb_no_doc_date = QCheckBox("Pas de date")
        self.cb_no_doc_date.stateChanged.connect(self.toggle_doc_date)
        doc_date_layout.addWidget(self.cb_no_doc_date)

        layout.addLayout(doc_date_layout)

        # Notes
        notes_label = QLabel("Description / Notes :")
        layout.addWidget(notes_label)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setPlaceholderText("Notes optionnelles sur ce document...")
        layout.addWidget(self.notes_input)

        layout.addStretch()

        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Enregistrer")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        btn_save.clicked.connect(self.save_document)
        buttons_layout.addWidget(btn_save)

        layout.addLayout(buttons_layout)

        # Initialiser l'état
        self.toggle_expiration_date()
        self.toggle_doc_date()

    def load_categories(self):
        """Charge les catégories (exclut les contrats car gérés dans module dédié)"""
        try:
            categories = self.doc_service.get_categories()

            if not categories:
                # Si aucune catégorie, ajouter des catégories par défaut
                if self.filter_category == "Contrats de travail":
                    self.categorie_combo.addItem("Contrats de travail", None)
                else:
                    self.categorie_combo.addItem("Certificats médicaux", None)
                    self.categorie_combo.addItem("Diplômes et formations", None)
                    self.categorie_combo.addItem("Autres", None)
                return

            # Si filter_category est spécifié, charger uniquement cette catégorie
            if self.filter_category:
                for cat in categories:
                    if cat['nom'] == self.filter_category:
                        self.categorie_combo.addItem(cat['nom'], cat['id'])
                        break
            else:
                # Exclure "Contrats de travail" car géré dans le module Gestion des Contrats
                for cat in categories:
                    if cat['nom'] != 'Contrats de travail':
                        self.categorie_combo.addItem(cat['nom'], cat['id'])
        except Exception as e:
            # En cas d'erreur, afficher un message
            logger.exception(f"Erreur chargement categories: {e}")
            QMessageBox.warning(
                self,
                "Erreur",
                "Impossible de charger les catégories.\n\nVeuillez d'abord installer le module :\npython scripts/install_gestion_documentaire.py\n\nContactez l'administrateur si le problème persiste."
            )
            self.reject()  # Fermer la fenêtre

    def select_file(self):
        """Sélectionne un fichier"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un document",
            "",
            "Tous les fichiers (*.*);;Documents PDF (*.pdf);;Documents Word (*.doc *.docx);;Images (*.jpg *.jpeg *.png)"
        )

        if filepath:
            self.selected_file = filepath
            self.lbl_selected_file.setText(f"✓ {Path(filepath).name}")
            self.lbl_selected_file.setStyleSheet("color: #059669; font-weight: bold;")

            # Mettre le nom du fichier par défaut si vide
            if not self.name_input.text():
                self.name_input.setText(Path(filepath).name)

    def toggle_expiration_date(self):
        """Active/désactive la date d'expiration"""
        enabled = not self.cb_no_expiration.isChecked()
        self.date_expiration.setEnabled(enabled)

    def toggle_doc_date(self):
        """Active/désactive la date du document"""
        enabled = not self.cb_no_doc_date.isChecked()
        self.date_document.setEnabled(enabled)

    def save_document(self):
        """Enregistre le document"""
        # Validation
        if not self.selected_file:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un fichier.")
            return

        if not Path(self.selected_file).exists():
            QMessageBox.warning(self, "Erreur", "Le fichier sélectionné n'existe plus.")
            return

        categorie_id = self.categorie_combo.currentData()
        if not categorie_id:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une catégorie.")
            return

        # Récupérer les valeurs
        nom_affichage = self.name_input.text() or None
        notes = self.notes_input.toPlainText() or None

        date_exp = None
        if not self.cb_no_expiration.isChecked():
            qdate = self.date_expiration.date()
            date_exp = date(qdate.year(), qdate.month(), qdate.day())

        date_doc = None
        if not self.cb_no_doc_date.isChecked():
            qdate = self.date_document.date()
            date_doc = date(qdate.year(), qdate.month(), qdate.day())

        # Ajouter le document
        success, message, doc_id = self.doc_service.add_document(
            operateur_id=self.operateur_id,
            categorie_id=categorie_id,
            fichier_source=self.selected_file,
            nom_affichage=nom_affichage,
            date_expiration=date_exp,
            notes=notes,
            uploaded_by="Utilisateur"  # À adapter selon votre système d'authentification
        )

        if success:
            self.created_document_id = doc_id  # Exposer l'ID pour récupération
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", message)


# Test de l'interface
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = GestionDocumentaireDialog()
    dialog.show()

    sys.exit(app.exec_())
