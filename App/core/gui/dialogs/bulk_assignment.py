# -*- coding: utf-8 -*-
"""
Module de gestion des opérations en masse.
Permet d'assigner des formations, absences, visites médicales à plusieurs employés.
"""

from typing import List, Dict, Optional, Callable

from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox,
    QCheckBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QGroupBox, QTextEdit, QMessageBox,
    QAbstractItemView, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QColor

from core.gui.workers.db_worker import DbWorker, DbThreadPool
from core.gui.components.loading_components import ProgressWidget
from core.repositories.personnel_repo import PersonnelRepository
from core.services.absence_service_crud import AbsenceServiceCRUD
from core.services.formation_service_crud import FormationServiceCRUD
from core.utils.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================
# SÉCURITÉ: VALIDATION DES FICHIERS UPLOADÉS
# ============================================================

# Taille max des fichiers (10 MB)
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Extensions autorisées
ALLOWED_EXTENSIONS = frozenset(['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg'])


def validate_uploaded_file(file_path: str) -> tuple[bool, str]:
    """
    Valide un fichier uploadé (taille et extension).

    Args:
        file_path: Chemin du fichier

    Returns:
        (valide, message_erreur)
    """
    import os

    if not os.path.exists(file_path):
        return False, "Fichier introuvable"

    # Vérifier l'extension
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Extension non autorisée: {ext}\nExtensions acceptées: {', '.join(sorted(ALLOWED_EXTENSIONS))}"

    # Vérifier la taille
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return False, f"Fichier trop volumineux: {size_mb:.1f} MB\nTaille max: {MAX_FILE_SIZE_MB} MB"

    return True, ""


# ============================================================
# 1. WIDGET DE SÉLECTION DU PERSONNEL
# ============================================================

class PersonnelSelectionWidget(QWidget):
    """
    Widget réutilisable pour la sélection multiple de personnel.
    Utilise QTableWidget avec checkboxes.
    """

    selection_changed = pyqtSignal(list)  # Émis quand la sélection change

    def __init__(self, parent=None):
        super().__init__(parent)
        self._personnel_data = []
        self._setup_ui()
        self._load_personnel()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === Filtres ===
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(12)

        # Recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un employé...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 13px;
                background: white;
                color: #111827;
            }
            QLineEdit:focus {
                border: 2px solid #7c3aed;
                padding: 7px 11px;
            }
        """)
        self.search_input.textChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.search_input, 2)

        # Filtre statut
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tous", "TOUS")
        self.status_combo.addItem("Actifs", "ACTIF")
        self.status_combo.addItem("Inactifs", "INACTIF")
        self.status_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 13px;
                background: white;
                color: #111827;
                min-width: 100px;
            }
            QComboBox:focus {
                border: 2px solid #7c3aed;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
        """)
        self.status_combo.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.status_combo, 1)

        layout.addLayout(filters_layout)

        # === Table du personnel ===
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "Nom", "Prénom", "Matricule", "Statut"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                gridline-color: #f3f4f6;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 6px 8px;
            }
            QTableWidget::item:selected {
                background: #ede9fe;
                color: #5b21b6;
            }
            QHeaderView::section {
                background: #f9fafb;
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                font-weight: bold;
                color: #374151;
            }
        """)
        layout.addWidget(self.table, 1)  # La table prend tout l'espace disponible

        # === Boutons d'action ===
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        btn_select_all = QPushButton("Tout sélectionner")
        btn_select_all.setCursor(Qt.PointingHandCursor)
        btn_select_all.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                padding: 6px 14px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e5e7eb;
                border-color: #9ca3af;
            }
        """)
        btn_select_all.clicked.connect(self._select_all)
        actions_layout.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("Tout désélectionner")
        btn_deselect_all.setCursor(Qt.PointingHandCursor)
        btn_deselect_all.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                padding: 6px 14px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e5e7eb;
                border-color: #9ca3af;
            }
        """)
        btn_deselect_all.clicked.connect(self._deselect_all)
        actions_layout.addWidget(btn_deselect_all)

        actions_layout.addStretch()

        self.count_label = QLabel("Sélectionnés: 0")
        self.count_label.setStyleSheet("""
            font-weight: bold;
            color: #7c3aed;
            font-size: 13px;
            padding: 4px 12px;
            background: #ede9fe;
            border-radius: 12px;
        """)
        actions_layout.addWidget(self.count_label)

        layout.addLayout(actions_layout)

    def _load_personnel(self):
        """Charge la liste du personnel depuis la base de données."""
        try:
            self._personnel_data = PersonnelRepository.get_all_as_dicts()
            self._populate_table()
        except Exception as e:
            logger.error(f"Erreur chargement personnel: {e}")

    def _populate_table(self):
        """Remplit la table avec les données."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for row_data in self._personnel_data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Checkbox
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            checkbox.setCheckState(Qt.Unchecked)
            checkbox.setData(Qt.UserRole, row_data['id'])
            self.table.setItem(row, 0, checkbox)

            # Données (non éditables)
            nom_item = QTableWidgetItem(row_data.get('nom', ''))
            nom_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 1, nom_item)

            prenom_item = QTableWidgetItem(row_data.get('prenom', ''))
            prenom_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 2, prenom_item)

            matricule_item = QTableWidgetItem(row_data.get('matricule', ''))
            matricule_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 3, matricule_item)

            statut = row_data.get('statut', '')
            statut_item = QTableWidgetItem(statut)
            if statut == 'ACTIF':
                statut_item.setForeground(QColor('#2e7d32'))
            else:
                statut_item.setForeground(QColor('#c62828'))
            self.table.setItem(row, 4, statut_item)

        self.table.blockSignals(False)
        self._apply_filters()

    def _apply_filters(self):
        """Applique les filtres de recherche et statut."""
        search_text = self.search_input.text().lower()
        status_filter = self.status_combo.currentData()

        for row in range(self.table.rowCount()):
            # Récupérer les données de la ligne
            nom = self.table.item(row, 1).text().lower() if self.table.item(row, 1) else ""
            prenom = self.table.item(row, 2).text().lower() if self.table.item(row, 2) else ""
            matricule = self.table.item(row, 3).text().lower() if self.table.item(row, 3) else ""
            statut = self.table.item(row, 4).text() if self.table.item(row, 4) else ""

            # Appliquer les filtres
            match_search = (
                search_text in nom or
                search_text in prenom or
                search_text in matricule
            )
            match_status = status_filter == "TOUS" or statut == status_filter

            self.table.setRowHidden(row, not (match_search and match_status))

        # Get selected IDs once to avoid inconsistency
        selected_ids = self.get_selected_ids()
        self._update_count_with_ids(selected_ids)
        # Emit signal to update button text (filtering changes visible selection)
        self.selection_changed.emit(selected_ids)

    def _on_item_changed(self, item):
        """Appelé quand un item change (checkbox)."""
        if item.column() == 0:
            # Get selected IDs once to avoid inconsistency
            selected_ids = self.get_selected_ids()
            self._update_count_with_ids(selected_ids)
            self.selection_changed.emit(selected_ids)

    def _select_all(self):
        """Sélectionne tous les éléments visibles."""
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                item = self.table.item(row, 0)
                if item:
                    item.setCheckState(Qt.Checked)
        self.table.blockSignals(False)
        # Get selected IDs once to avoid inconsistency
        selected_ids = self.get_selected_ids()
        self._update_count_with_ids(selected_ids)
        self.selection_changed.emit(selected_ids)

    def _deselect_all(self):
        """Désélectionne tous les éléments."""
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.Unchecked)
        self.table.blockSignals(False)
        # Get selected IDs once to avoid inconsistency
        selected_ids = self.get_selected_ids()
        self._update_count_with_ids(selected_ids)
        self.selection_changed.emit(selected_ids)

    def _update_count(self):
        """Met à jour le compteur de sélection."""
        selected_ids = self.get_selected_ids()
        self._update_count_with_ids(selected_ids)

    def _update_count_with_ids(self, selected_ids: List[int]):
        """Met à jour le compteur avec une liste d'IDs fournie."""
        count = len(selected_ids)
        visible_count = sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))
        self.count_label.setText(f"Sélectionnés: {count} / {visible_count}")

    def get_selected_ids(self) -> List[int]:
        """Retourne les IDs des personnels sélectionnés."""
        selected = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked and not self.table.isRowHidden(row):
                personnel_id = item.data(Qt.UserRole)
                if personnel_id:
                    selected.append(personnel_id)
        return selected

    def get_selected_count(self) -> int:
        """Retourne le nombre de personnels sélectionnés."""
        return len(self.get_selected_ids())


# ============================================================
# 2. ONGLET FORMATIONS
# ============================================================

class FormationBulkTab(QWidget):
    """Onglet pour l'ajout de formation en masse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Style commun pour les champs
        input_style = """
            QLineEdit, QDateEdit, QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit {
                padding: 6px 10px;
                border: 1px solid #d1d5db;
                border-radius: 5px;
                font-size: 13px;
                background: white;
                color: #111827;
                min-height: 18px;
            }
            QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
                border: 2px solid #7c3aed;
                padding: 5px 9px;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
            QDateEdit::drop-down, QComboBox::drop-down {
                border: none;
                padding-right: 6px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
            }
        """
        label_style = "color: #374151; font-size: 13px;"
        required_style = "color: #374151; font-size: 13px; font-weight: 500;"

        # === Formulaire ===
        form_group = QGroupBox("Informations de la formation")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #7c3aed;
                border: none;
                margin-top: 8px;
                padding-top: 4px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0;
            }
        """)
        form_layout = QGridLayout(form_group)
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(12)

        # Intitulé
        lbl_intitule = QLabel("Intitulé *:")
        lbl_intitule.setStyleSheet(required_style)
        form_layout.addWidget(lbl_intitule, 0, 0)
        self.intitule_input = QLineEdit()
        self.intitule_input.setPlaceholderText("Ex: Formation Sécurité 2026")
        self.intitule_input.setStyleSheet(input_style)
        form_layout.addWidget(self.intitule_input, 0, 1, 1, 3)

        # Organisme
        lbl_organisme = QLabel("Organisme:")
        lbl_organisme.setStyleSheet(label_style)
        form_layout.addWidget(lbl_organisme, 1, 0)
        self.organisme_input = QLineEdit()
        self.organisme_input.setPlaceholderText("Ex: APAVE, AFPA...")
        self.organisme_input.setStyleSheet(input_style)
        form_layout.addWidget(self.organisme_input, 1, 1, 1, 3)

        # Dates
        lbl_date_debut = QLabel("Date début *:")
        lbl_date_debut.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_debut, 2, 0)
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setStyleSheet(input_style)
        form_layout.addWidget(self.date_debut, 2, 1)

        lbl_date_fin = QLabel("Date fin *:")
        lbl_date_fin.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_fin, 2, 2)
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setStyleSheet(input_style)
        form_layout.addWidget(self.date_fin, 2, 3)

        # Durée et coût
        lbl_duree = QLabel("Durée (heures):")
        lbl_duree.setStyleSheet(label_style)
        form_layout.addWidget(lbl_duree, 3, 0)
        self.duree_input = QDoubleSpinBox()
        self.duree_input.setRange(0, 1000)
        self.duree_input.setDecimals(1)
        self.duree_input.setStyleSheet(input_style)
        form_layout.addWidget(self.duree_input, 3, 1)

        lbl_cout = QLabel("Coût:")
        lbl_cout.setStyleSheet(label_style)
        form_layout.addWidget(lbl_cout, 3, 2)
        self.cout_input = QDoubleSpinBox()
        self.cout_input.setRange(0, 100000)
        self.cout_input.setDecimals(2)
        self.cout_input.setSuffix(" EUR")
        self.cout_input.setStyleSheet(input_style)
        form_layout.addWidget(self.cout_input, 3, 3)

        # Statut et certificat
        lbl_statut = QLabel("Statut:")
        lbl_statut.setStyleSheet(label_style)
        form_layout.addWidget(lbl_statut, 4, 0)
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(["Planifiée", "En cours", "Terminée", "Annulée"])
        self.statut_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.statut_combo, 4, 1)

        self.certificat_check = QCheckBox("Certificat obtenu")
        self.certificat_check.setStyleSheet("color: #374151; font-size: 13px;")
        form_layout.addWidget(self.certificat_check, 4, 2, 1, 2)

        # Commentaire
        lbl_commentaire = QLabel("Commentaire:")
        lbl_commentaire.setStyleSheet(label_style)
        form_layout.addWidget(lbl_commentaire, 5, 0)
        self.commentaire_input = QTextEdit()
        self.commentaire_input.setMaximumHeight(45)
        self.commentaire_input.setStyleSheet(input_style)
        form_layout.addWidget(self.commentaire_input, 5, 1, 1, 3)

        # Document / Attestation
        lbl_document = QLabel("Document:")
        lbl_document.setStyleSheet(label_style)
        form_layout.addWidget(lbl_document, 6, 0)

        doc_layout = QHBoxLayout()
        doc_layout.setSpacing(8)
        self.document_path_input = QLineEdit()
        self.document_path_input.setPlaceholderText("Aucun document sélectionné")
        self.document_path_input.setReadOnly(True)
        self.document_path_input.setStyleSheet(input_style)
        doc_layout.addWidget(self.document_path_input, 1)

        btn_browse = QPushButton("Parcourir...")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                padding: 8px 16px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #e5e7eb;
                border-color: #9ca3af;
            }
        """)
        btn_browse.clicked.connect(self._browse_document)
        doc_layout.addWidget(btn_browse)

        btn_clear = QPushButton("X")
        btn_clear.setFixedWidth(32)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setToolTip("Supprimer le document")
        btn_clear.setStyleSheet("""
            QPushButton {
                background: #fee2e2;
                color: #dc2626;
                padding: 8px;
                border: 1px solid #fecaca;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #fecaca;
            }
        """)
        btn_clear.clicked.connect(self._clear_document)
        doc_layout.addWidget(btn_clear)

        form_layout.addLayout(doc_layout, 6, 1, 1, 3)

        # Stocker le chemin du document
        self._document_path = None

        layout.addWidget(form_group)
        layout.addStretch()

    def _browse_document(self):
        """Ouvre un dialogue pour sélectionner un document."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un document",
            "",
            "Documents (*.pdf *.doc *.docx *.xls *.xlsx *.png *.jpg *.jpeg);;Tous les fichiers (*)"
        )
        if file_path:
            # SÉCURITÉ: Valider le fichier (taille et extension)
            valid, error_msg = validate_uploaded_file(file_path)
            if not valid:
                QMessageBox.warning(self, "Fichier invalide", error_msg)
                return

            self._document_path = file_path
            # Afficher juste le nom du fichier
            import os
            self.document_path_input.setText(os.path.basename(file_path))

    def _clear_document(self):
        """Supprime le document sélectionné."""
        self._document_path = None
        self.document_path_input.clear()

    def get_data(self) -> Dict:
        """Retourne les données du formulaire."""
        return {
            'intitule': self.intitule_input.text().strip(),
            'organisme': self.organisme_input.text().strip() or None,
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': self.date_fin.date().toPyDate(),
            'duree_heures': self.duree_input.value() or None,
            'cout': self.cout_input.value() or None,
            'statut': self.statut_combo.currentText(),
            'certificat_obtenu': self.certificat_check.isChecked(),
            'commentaire': self.commentaire_input.toPlainText().strip() or None,
            'document_path': self._document_path  # Chemin du document à joindre
        }

    def validate(self) -> tuple:
        """Valide les données du formulaire."""
        data = self.get_data()

        if not data['intitule']:
            return False, "L'intitulé est obligatoire"

        if data['date_debut'] > data['date_fin']:
            return False, "La date de début doit être antérieure à la date de fin"

        return True, ""


# ============================================================
# 3. ONGLET ABSENCES
# ============================================================

class AbsenceBulkTab(QWidget):
    """Onglet pour l'ajout d'absence en masse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._types_absence = []
        self._setup_ui()
        self._load_types_absence()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Style commun
        input_style = """
            QLineEdit, QDateEdit, QComboBox, QTextEdit {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                color: #111827;
                min-height: 20px;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 2px solid #7c3aed;
                padding: 7px 11px;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
            QDateEdit::drop-down, QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
        """
        label_style = "color: #374151; font-size: 14px;"
        required_style = "color: #374151; font-size: 13px; font-weight: 500;"

        # === Formulaire ===
        form_group = QGroupBox("Informations de l'absence")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #7c3aed;
                border: none;
                margin-top: 8px;
                padding-top: 4px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0;
            }
        """)
        form_layout = QGridLayout(form_group)
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(12)

        # Type d'absence
        lbl_type = QLabel("Type d'absence *:")
        lbl_type.setStyleSheet(required_style)
        form_layout.addWidget(lbl_type, 0, 0)
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.type_combo, 0, 1, 1, 3)

        # Dates
        lbl_date_debut = QLabel("Date début *:")
        lbl_date_debut.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_debut, 1, 0)
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setStyleSheet(input_style)
        form_layout.addWidget(self.date_debut, 1, 1)

        lbl_date_fin = QLabel("Date fin *:")
        lbl_date_fin.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_fin, 1, 2)
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setStyleSheet(input_style)
        form_layout.addWidget(self.date_fin, 1, 3)

        # Demi-journées
        lbl_demi_debut = QLabel("Début:")
        lbl_demi_debut.setStyleSheet(label_style)
        form_layout.addWidget(lbl_demi_debut, 2, 0)
        self.demi_debut_combo = QComboBox()
        self.demi_debut_combo.addItem("Journée complète", "JOURNEE")
        self.demi_debut_combo.addItem("Matin uniquement", "MATIN")
        self.demi_debut_combo.addItem("Après-midi uniquement", "APRES_MIDI")
        self.demi_debut_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.demi_debut_combo, 2, 1)

        lbl_demi_fin = QLabel("Fin:")
        lbl_demi_fin.setStyleSheet(label_style)
        form_layout.addWidget(lbl_demi_fin, 2, 2)
        self.demi_fin_combo = QComboBox()
        self.demi_fin_combo.addItem("Journée complète", "JOURNEE")
        self.demi_fin_combo.addItem("Matin uniquement", "MATIN")
        self.demi_fin_combo.addItem("Après-midi uniquement", "APRES_MIDI")
        self.demi_fin_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.demi_fin_combo, 2, 3)

        # Statut
        lbl_statut = QLabel("Statut:")
        lbl_statut.setStyleSheet(label_style)
        form_layout.addWidget(lbl_statut, 3, 0)
        self.statut_combo = QComboBox()
        self.statut_combo.addItem("En attente de validation", "EN_ATTENTE")
        self.statut_combo.addItem("Validée directement", "VALIDEE")
        self.statut_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.statut_combo, 3, 1)

        # Motif
        lbl_motif = QLabel("Motif:")
        lbl_motif.setStyleSheet(label_style)
        form_layout.addWidget(lbl_motif, 4, 0)
        self.motif_input = QTextEdit()
        self.motif_input.setMaximumHeight(60)
        self.motif_input.setStyleSheet(input_style)
        form_layout.addWidget(self.motif_input, 4, 1, 1, 3)

        # Document / Justificatif
        lbl_document = QLabel("Justificatif:")
        lbl_document.setStyleSheet(label_style)
        form_layout.addWidget(lbl_document, 5, 0)

        doc_layout = QHBoxLayout()
        doc_layout.setSpacing(8)
        self.document_path_input = QLineEdit()
        self.document_path_input.setPlaceholderText("Aucun document sélectionné")
        self.document_path_input.setReadOnly(True)
        self.document_path_input.setStyleSheet(input_style)
        doc_layout.addWidget(self.document_path_input, 1)

        btn_browse = QPushButton("Parcourir...")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                padding: 8px 16px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #e5e7eb;
                border-color: #9ca3af;
            }
        """)
        btn_browse.clicked.connect(self._browse_document)
        doc_layout.addWidget(btn_browse)

        btn_clear = QPushButton("X")
        btn_clear.setFixedWidth(32)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setToolTip("Supprimer le document")
        btn_clear.setStyleSheet("""
            QPushButton {
                background: #fee2e2;
                color: #dc2626;
                padding: 8px;
                border: 1px solid #fecaca;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #fecaca;
            }
        """)
        btn_clear.clicked.connect(self._clear_document)
        doc_layout.addWidget(btn_clear)

        form_layout.addLayout(doc_layout, 5, 1, 1, 3)

        # Stocker le chemin du document
        self._document_path = None

        layout.addWidget(form_group)
        layout.addStretch()

    def _browse_document(self):
        """Ouvre un dialogue pour sélectionner un document."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un justificatif",
            "",
            "Documents (*.pdf *.doc *.docx *.png *.jpg *.jpeg);;Tous les fichiers (*)"
        )
        if file_path:
            # SÉCURITÉ: Valider le fichier (taille et extension)
            valid, error_msg = validate_uploaded_file(file_path)
            if not valid:
                QMessageBox.warning(self, "Fichier invalide", error_msg)
                return

            self._document_path = file_path
            import os
            self.document_path_input.setText(os.path.basename(file_path))

    def _clear_document(self):
        """Supprime le document sélectionné."""
        self._document_path = None
        self.document_path_input.clear()

    def _load_types_absence(self):
        """Charge les types d'absence depuis la base de données."""
        def fetch(progress_callback=None):
            return AbsenceServiceCRUD.get_types_absence()

        def on_result(data):
            self._types_absence = data
            self.type_combo.clear()
            for ta in data:
                self.type_combo.addItem(f"{ta['code']} - {ta['libelle']}", ta['code'])

        def on_error(error):
            logger.error(f"Erreur chargement types absence: {error}")

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def get_data(self) -> Dict:
        """Retourne les données du formulaire."""
        return {
            'type_absence_code': self.type_combo.currentData(),
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': self.date_fin.date().toPyDate(),
            'demi_journee_debut': self.demi_debut_combo.currentData(),
            'demi_journee_fin': self.demi_fin_combo.currentData(),
            'statut': self.statut_combo.currentData(),
            'motif': self.motif_input.toPlainText().strip(),
            'document_path': self._document_path  # Chemin du justificatif
        }

    def validate(self) -> tuple:
        """Valide les données du formulaire."""
        data = self.get_data()

        if not data['type_absence_code']:
            return False, "Le type d'absence est obligatoire"

        if data['date_debut'] > data['date_fin']:
            return False, "La date de début doit être antérieure à la date de fin"

        return True, ""


# ============================================================
# 4. ONGLET MÉDICAL
# ============================================================

class MedicalBulkTab(QWidget):
    """Onglet pour l'ajout de visite médicale en masse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Style commun
        input_style = """
            QLineEdit, QDateEdit, QComboBox, QTextEdit {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                color: #111827;
                min-height: 20px;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 2px solid #7c3aed;
                padding: 7px 11px;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
            QDateEdit::drop-down, QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
        """
        label_style = "color: #374151; font-size: 14px;"
        required_style = "color: #374151; font-size: 13px; font-weight: 500;"

        # === Formulaire ===
        form_group = QGroupBox("Informations de la visite médicale")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #7c3aed;
                border: none;
                margin-top: 8px;
                padding-top: 4px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0;
            }
        """)
        form_layout = QGridLayout(form_group)
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(12)

        # Type de visite
        lbl_type = QLabel("Type de visite *:")
        lbl_type.setStyleSheet(required_style)
        form_layout.addWidget(lbl_type, 0, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Périodique",
            "Embauche",
            "Reprise",
            "À la demande",
            "Pré-reprise"
        ])
        self.type_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.type_combo, 0, 1)

        # Date de visite
        lbl_date_visite = QLabel("Date de visite *:")
        lbl_date_visite.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_visite, 0, 2)
        self.date_visite = QDateEdit()
        self.date_visite.setDate(QDate.currentDate())
        self.date_visite.setCalendarPopup(True)
        self.date_visite.setDisplayFormat("dd/MM/yyyy")
        self.date_visite.setStyleSheet(input_style)
        form_layout.addWidget(self.date_visite, 0, 3)

        # Médecin
        lbl_medecin = QLabel("Médecin:")
        lbl_medecin.setStyleSheet(label_style)
        form_layout.addWidget(lbl_medecin, 1, 0)
        self.medecin_input = QLineEdit()
        self.medecin_input.setPlaceholderText("Nom du médecin")
        self.medecin_input.setStyleSheet(input_style)
        form_layout.addWidget(self.medecin_input, 1, 1, 1, 3)

        # Résultat
        lbl_resultat = QLabel("Résultat:")
        lbl_resultat.setStyleSheet(label_style)
        form_layout.addWidget(lbl_resultat, 2, 0)
        self.resultat_combo = QComboBox()
        self.resultat_combo.addItems([
            "",
            "Apte",
            "Apte avec restrictions",
            "Inapte temporaire",
            "Inapte définitif"
        ])
        self.resultat_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.resultat_combo, 2, 1)

        # Prochaine visite
        lbl_prochaine = QLabel("Prochaine visite:")
        lbl_prochaine.setStyleSheet(label_style)
        form_layout.addWidget(lbl_prochaine, 2, 2)
        self.prochaine_visite = QDateEdit()
        self.prochaine_visite.setDate(QDate.currentDate().addYears(1))
        self.prochaine_visite.setCalendarPopup(True)
        self.prochaine_visite.setDisplayFormat("dd/MM/yyyy")
        self.prochaine_visite.setStyleSheet(input_style)
        form_layout.addWidget(self.prochaine_visite, 2, 3)

        # Restrictions
        lbl_restrictions = QLabel("Restrictions:")
        lbl_restrictions.setStyleSheet(label_style)
        form_layout.addWidget(lbl_restrictions, 3, 0)
        self.restrictions_input = QTextEdit()
        self.restrictions_input.setMaximumHeight(60)
        self.restrictions_input.setPlaceholderText("Restrictions éventuelles...")
        self.restrictions_input.setStyleSheet(input_style)
        form_layout.addWidget(self.restrictions_input, 3, 1, 1, 3)

        # Commentaire
        lbl_commentaire = QLabel("Commentaire:")
        lbl_commentaire.setStyleSheet(label_style)
        form_layout.addWidget(lbl_commentaire, 4, 0)
        self.commentaire_input = QTextEdit()
        self.commentaire_input.setMaximumHeight(50)
        self.commentaire_input.setStyleSheet(input_style)
        form_layout.addWidget(self.commentaire_input, 4, 1, 1, 3)

        # Document / Fiche aptitude
        lbl_document = QLabel("Document:")
        lbl_document.setStyleSheet(label_style)
        form_layout.addWidget(lbl_document, 5, 0)

        doc_layout = QHBoxLayout()
        doc_layout.setSpacing(8)
        self.document_path_input = QLineEdit()
        self.document_path_input.setPlaceholderText("Aucun document sélectionné")
        self.document_path_input.setReadOnly(True)
        self.document_path_input.setStyleSheet(input_style)
        doc_layout.addWidget(self.document_path_input, 1)

        btn_browse = QPushButton("Parcourir...")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                padding: 8px 16px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #e5e7eb;
                border-color: #9ca3af;
            }
        """)
        btn_browse.clicked.connect(self._browse_document)
        doc_layout.addWidget(btn_browse)

        btn_clear = QPushButton("X")
        btn_clear.setFixedWidth(32)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setToolTip("Supprimer le document")
        btn_clear.setStyleSheet("""
            QPushButton {
                background: #fee2e2;
                color: #dc2626;
                padding: 8px;
                border: 1px solid #fecaca;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #fecaca;
            }
        """)
        btn_clear.clicked.connect(self._clear_document)
        doc_layout.addWidget(btn_clear)

        form_layout.addLayout(doc_layout, 5, 1, 1, 3)

        # Stocker le chemin du document
        self._document_path = None

        layout.addWidget(form_group)
        layout.addStretch()

    def _browse_document(self):
        """Ouvre un dialogue pour sélectionner un document."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un document médical",
            "",
            "Documents (*.pdf *.doc *.docx *.png *.jpg *.jpeg);;Tous les fichiers (*)"
        )
        if file_path:
            # SÉCURITÉ: Valider le fichier (taille et extension)
            valid, error_msg = validate_uploaded_file(file_path)
            if not valid:
                QMessageBox.warning(self, "Fichier invalide", error_msg)
                return

            self._document_path = file_path
            import os
            self.document_path_input.setText(os.path.basename(file_path))

    def _clear_document(self):
        """Supprime le document sélectionné."""
        self._document_path = None
        self.document_path_input.clear()

    def get_data(self) -> Dict:
        """Retourne les données du formulaire."""
        return {
            'type_visite': self.type_combo.currentText(),
            'date_visite': self.date_visite.date().toPyDate(),
            'medecin': self.medecin_input.text().strip() or None,
            'resultat': self.resultat_combo.currentText() or None,
            'prochaine_visite': self.prochaine_visite.date().toPyDate(),
            'restrictions': self.restrictions_input.toPlainText().strip() or None,
            'commentaire': self.commentaire_input.toPlainText().strip() or None,
            'document_path': self._document_path  # Chemin du document médical
        }

    def validate(self) -> tuple:
        """Valide les données du formulaire."""
        data = self.get_data()

        if not data['type_visite']:
            return False, "Le type de visite est obligatoire"

        return True, ""


# ============================================================
# 5. ONGLET COMPÉTENCES
# ============================================================

class CompetenceBulkTab(QWidget):
    """Onglet pour l'ajout de compétence en masse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._catalogue = []
        self._setup_ui()
        self._load_catalogue()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Style commun
        input_style = """
            QLineEdit, QDateEdit, QComboBox, QTextEdit {
                padding: 6px 10px;
                border: 1px solid #d1d5db;
                border-radius: 5px;
                font-size: 13px;
                background: white;
                color: #111827;
                min-height: 18px;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 2px solid #7c3aed;
                padding: 5px 9px;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
            QDateEdit::drop-down, QComboBox::drop-down {
                border: none;
                padding-right: 6px;
            }
        """
        label_style = "color: #374151; font-size: 13px;"
        required_style = "color: #374151; font-size: 13px; font-weight: 500;"

        # === Formulaire ===
        form_group = QGroupBox("Informations de la compétence")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #7c3aed;
                border: none;
                margin-top: 8px;
                padding-top: 4px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0;
            }
        """)
        form_layout = QGridLayout(form_group)
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(12)

        # Compétence
        lbl_competence = QLabel("Compétence *:")
        lbl_competence.setStyleSheet(required_style)
        form_layout.addWidget(lbl_competence, 0, 0)
        self.competence_combo = QComboBox()
        self.competence_combo.setEditable(True)
        self.competence_combo.setMinimumWidth(300)
        self.competence_combo.setStyleSheet(input_style)
        self.competence_combo.setInsertPolicy(QComboBox.NoInsert)
        self.competence_combo.completer().setCompletionMode(
            self.competence_combo.completer().PopupCompletion
        )
        self.competence_combo.lineEdit().setPlaceholderText("Saisir ou sélectionner une compétence...")
        self.competence_combo.currentIndexChanged.connect(self._on_competence_changed)
        form_layout.addWidget(self.competence_combo, 0, 1, 1, 3)

        # Date d'acquisition
        lbl_date_acq = QLabel("Date d'acquisition *:")
        lbl_date_acq.setStyleSheet(required_style)
        form_layout.addWidget(lbl_date_acq, 1, 0)
        self.date_acquisition = QDateEdit()
        self.date_acquisition.setDate(QDate.currentDate())
        self.date_acquisition.setCalendarPopup(True)
        self.date_acquisition.setDisplayFormat("dd/MM/yyyy")
        self.date_acquisition.setStyleSheet(input_style)
        self.date_acquisition.dateChanged.connect(self._update_expiration_date)
        form_layout.addWidget(self.date_acquisition, 1, 1)

        # Date d'expiration
        lbl_date_exp = QLabel("Date d'expiration:")
        lbl_date_exp.setStyleSheet(label_style)
        form_layout.addWidget(lbl_date_exp, 1, 2)
        self.date_expiration = QDateEdit()
        self.date_expiration.setCalendarPopup(True)
        self.date_expiration.setDisplayFormat("dd/MM/yyyy")
        self.date_expiration.setSpecialValueText("Permanent")
        self.date_expiration.setMinimumDate(QDate(1900, 1, 1))
        self.date_expiration.setDate(QDate(1900, 1, 1))
        self.date_expiration.setStyleSheet(input_style)
        form_layout.addWidget(self.date_expiration, 1, 3)

        # Info validité
        self.validite_info = QLabel("")
        self.validite_info.setStyleSheet("color: #64748b; font-style: italic; font-size: 12px;")
        form_layout.addWidget(self.validite_info, 2, 1, 1, 3)

        # Commentaire
        lbl_commentaire = QLabel("Commentaire:")
        lbl_commentaire.setStyleSheet(label_style)
        form_layout.addWidget(lbl_commentaire, 3, 0)
        self.commentaire_input = QTextEdit()
        self.commentaire_input.setMaximumHeight(50)
        self.commentaire_input.setPlaceholderText("Commentaire optionnel...")
        self.commentaire_input.setStyleSheet(input_style)
        form_layout.addWidget(self.commentaire_input, 3, 1, 1, 3)

        # Document / Attestation
        lbl_document = QLabel("Document:")
        lbl_document.setStyleSheet(label_style)
        form_layout.addWidget(lbl_document, 4, 0)

        doc_layout = QHBoxLayout()
        doc_layout.setSpacing(8)
        self.document_path_input = QLineEdit()
        self.document_path_input.setPlaceholderText("Aucun document sélectionné")
        self.document_path_input.setReadOnly(True)
        self.document_path_input.setStyleSheet(input_style)
        doc_layout.addWidget(self.document_path_input, 1)

        btn_browse = QPushButton("Parcourir...")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                padding: 8px 16px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #e5e7eb;
                border-color: #9ca3af;
            }
        """)
        btn_browse.clicked.connect(self._browse_document)
        doc_layout.addWidget(btn_browse)

        btn_clear = QPushButton("X")
        btn_clear.setFixedWidth(32)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setToolTip("Supprimer le document")
        btn_clear.setStyleSheet("""
            QPushButton {
                background: #fee2e2;
                color: #dc2626;
                padding: 8px;
                border: 1px solid #fecaca;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #fecaca;
            }
        """)
        btn_clear.clicked.connect(self._clear_document)
        doc_layout.addWidget(btn_clear)

        form_layout.addLayout(doc_layout, 4, 1, 1, 3)

        # Stocker le chemin du document
        self._document_path = None

        layout.addWidget(form_group)
        layout.addStretch()

    def _browse_document(self):
        """Ouvre un dialogue pour sélectionner un document."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un document (attestation, certificat...)",
            "",
            "Documents (*.pdf *.doc *.docx *.png *.jpg *.jpeg);;Tous les fichiers (*)"
        )
        if file_path:
            # SÉCURITÉ: Valider le fichier (taille et extension)
            valid, error_msg = validate_uploaded_file(file_path)
            if not valid:
                QMessageBox.warning(self, "Fichier invalide", error_msg)
                return

            self._document_path = file_path
            import os
            self.document_path_input.setText(os.path.basename(file_path))

    def _clear_document(self):
        """Supprime le document sélectionné."""
        self._document_path = None
        self.document_path_input.clear()

    def _load_catalogue(self):
        """Charge le catalogue des compétences."""
        def fetch(progress_callback=None):
            return FormationServiceCRUD.get_catalogue_competences()

        def on_result(data):
            self._catalogue = data
            self.competence_combo.clear()
            self.competence_combo.setCurrentIndex(-1)
            self.competence_combo.lineEdit().clear()

            # Grouper par catégorie
            categories = {}
            for comp in data:
                cat = comp.get('categorie') or 'Autre'
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(comp)

            for cat in sorted(categories.keys()):
                # Séparateur catégorie
                self.competence_combo.addItem(f"── {cat} ──", None)
                idx = self.competence_combo.count() - 1
                self.competence_combo.model().item(idx).setEnabled(False)

                for comp in categories[cat]:
                    label = comp['libelle']
                    if comp.get('duree_validite_mois'):
                        label += f" ({comp['duree_validite_mois']} mois)"
                    self.competence_combo.addItem(label, comp)

        def on_error(error):
            logger.error(f"Erreur chargement catalogue compétences: {error}")

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def _on_competence_changed(self):
        """Met à jour l'info validité quand la compétence change."""
        comp_data = self.competence_combo.currentData()
        if isinstance(comp_data, dict) and comp_data.get('duree_validite_mois'):
            mois = comp_data['duree_validite_mois']
            self.validite_info.setText(f"Validité standard: {mois} mois")
            self._update_expiration_date()
        else:
            self.validite_info.setText("Compétence permanente (pas d'expiration)")
            self.date_expiration.setDate(QDate(1900, 1, 1))

    def _update_expiration_date(self):
        """Calcule automatiquement la date d'expiration."""
        comp_data = self.competence_combo.currentData()
        if isinstance(comp_data, dict) and comp_data.get('duree_validite_mois'):
            from dateutil.relativedelta import relativedelta
            date_acq = self.date_acquisition.date().toPyDate()
            date_exp = date_acq + relativedelta(months=comp_data['duree_validite_mois'])
            self.date_expiration.setDate(QDate(date_exp.year, date_exp.month, date_exp.day))

    def get_data(self) -> Dict:
        """Retourne les données du formulaire."""
        comp_data = self.competence_combo.currentData()
        free_text = self.competence_combo.currentText().strip()
        date_exp = self.date_expiration.date()

        # Si une compétence du catalogue est sélectionnée
        if comp_data and isinstance(comp_data, dict):
            comp_id = comp_data['id']
            comp_libelle = comp_data['libelle']
        else:
            # Saisie libre
            comp_id = None
            comp_libelle = free_text if free_text else None

        return {
            'competence_id': comp_id,
            'competence_libelle': comp_libelle,
            'date_acquisition': self.date_acquisition.date().toPyDate(),
            'date_expiration': date_exp.toPyDate() if date_exp.year() > 1900 else None,
            'commentaire': self.commentaire_input.toPlainText().strip() or None,
            'document_path': self._document_path  # Chemin du document à joindre
        }

    def validate(self) -> tuple:
        """Valide les données du formulaire."""
        data = self.get_data()

        if not data['competence_id'] and not data['competence_libelle']:
            return False, "Veuillez sélectionner ou saisir une compétence"

        return True, ""


# ============================================================
# 6. DIALOGUE DE PROGRESSION
# ============================================================

class BulkOperationProgressDialog(QDialog):
    """Dialogue de progression pour les opérations longues."""

    operation_completed = pyqtSignal(int, int, list)  # success, errors, details

    def __init__(self, operation_type: str, data: Dict, personnel_ids: List[int],
                 created_by: str = None, parent=None):
        super().__init__(parent)
        self.operation_type = operation_type
        self.data = data
        self.personnel_ids = personnel_ids
        self.created_by = created_by
        self._cancelled = False
        self._worker = None

        self.setWindowTitle("Opération en cours")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Info
        info_label = QLabel(f"Traitement de {len(self.personnel_ids)} employé(s)...")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)

        # Progress
        self.progress_widget = ProgressWidget(f"Opération: {self.operation_type}")
        layout.addWidget(self.progress_widget)

        # Bouton annuler
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self._cancel)
        layout.addWidget(self.btn_cancel, alignment=Qt.AlignCenter)

    def start_operation(self):
        """Lance l'opération en background."""
        from core.services import bulk_service

        def do_operation(progress_callback=None):
            # DbWorker injecte automatiquement progress_callback, donc on doit l'accepter
            if self.operation_type == "FORMATION":
                return bulk_service.add_formation_batch(
                    self.personnel_ids,
                    self.data,
                    progress_callback=progress_callback,
                    created_by=self.created_by
                )
            elif self.operation_type == "ABSENCE":
                return bulk_service.add_absence_batch(
                    self.personnel_ids,
                    self.data,
                    progress_callback=progress_callback,
                    created_by=self.created_by
                )
            elif self.operation_type == "VISITE_MEDICALE":
                return bulk_service.add_visite_batch(
                    self.personnel_ids,
                    self.data,
                    progress_callback=progress_callback,
                    created_by=self.created_by
                )
            elif self.operation_type == "COMPETENCE":
                return bulk_service.add_competence_batch(
                    self.personnel_ids,
                    self.data,
                    progress_callback=progress_callback,
                    created_by=self.created_by
                )
            return 0, 0, []

        def on_result(result):
            nb_success, nb_errors, details = result
            self.operation_completed.emit(nb_success, nb_errors, details)
            self.accept()

        def on_error(error):
            logger.error(f"Erreur lors de l'opération bulk: {error}")
            QMessageBox.critical(self, "Erreur", "Une erreur est survenue lors de l'opération. Consultez les logs pour plus de détails.")
            self.reject()

        self._worker = DbWorker(do_operation)
        self._worker.signals.result.connect(on_result)
        self._worker.signals.error.connect(on_error)
        self._worker.signals.progress.connect(self._on_progress)
        DbThreadPool.start(self._worker)

    def _on_progress(self, percentage, message):
        """Met à jour la progression."""
        self.progress_widget.set_progress(percentage, message)

    def _cancel(self):
        """Annule l'opération."""
        self._cancelled = True
        if self._worker:
            self._worker.cancel()
        self.reject()


# ============================================================
# 6. DIALOGUE DE RÉSULTATS
# ============================================================

class BulkOperationResultsDialog(QDialog):
    """Dialogue pour afficher les résultats d'une opération."""

    def __init__(self, operation_type: str, nb_success: int, nb_errors: int,
                 details: List[Dict], parent=None):
        super().__init__(parent)
        self.operation_type = operation_type
        self.nb_success = nb_success
        self.nb_errors = nb_errors
        self.details = details

        self.setWindowTitle("Résultats de l'opération")
        self.setMinimumSize(600, 400)
        self._setup_ui()
        self._load_details()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # === Résumé ===
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background: #e8f5e9;
                border: 1px solid #a5d6a7;
                border-radius: 8px;
                padding: 12px;
            }
        """ if self.nb_errors == 0 else """
            QFrame {
                background: #fff3e0;
                border: 1px solid #ffcc80;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)

        icon = "OK" if self.nb_errors == 0 else "!"
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        summary_layout.addWidget(icon_label)

        summary_text = f"<b>{self.nb_success}</b> succès"
        if self.nb_errors > 0:
            summary_text += f", <b style='color: #d32f2f;'>{self.nb_errors}</b> erreur(s)"
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(summary_label)
        summary_layout.addStretch()

        layout.addWidget(summary_frame)

        # === Table des détails ===
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Statut", "Nom", "Prénom", "Détails"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # === Boutons ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        btn_close.setDefault(True)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _load_details(self):
        """Charge les détails dans la table."""
        # Récupérer les noms des personnels
        personnel_names = {}
        personnel_ids = [d['personnel_id'] for d in self.details]

        if personnel_ids:
            rows = PersonnelRepository.get_by_ids(personnel_ids)
            for row in rows:
                personnel_names[row['id']] = (row['nom'], row['prenom'])

        # Remplir la table
        self.table.setRowCount(len(self.details))
        for row, detail in enumerate(self.details):
            # Statut
            status = detail.get('status', '')
            status_item = QTableWidgetItem("OK" if status == 'SUCCES' else "X")
            if status == 'SUCCES':
                status_item.setForeground(QColor('#2e7d32'))
            else:
                status_item.setForeground(QColor('#d32f2f'))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, status_item)

            # Nom / Prénom
            names = personnel_names.get(detail['personnel_id'], ('?', '?'))
            self.table.setItem(row, 1, QTableWidgetItem(names[0]))
            self.table.setItem(row, 2, QTableWidgetItem(names[1]))

            # Détails
            if status == 'SUCCES':
                details_text = f"ID: {detail.get('record_id', '?')}"
            else:
                details_text = detail.get('error', 'Erreur inconnue')
            self.table.setItem(row, 3, QTableWidgetItem(details_text))


# ============================================================
# 7. DIALOGUE PRINCIPAL
# ============================================================

class BulkAssignmentDialog(QDialog):
    """Dialogue principal pour les opérations en masse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Actions en masse")
        self.setMinimumSize(700, 820)
        self.resize(750, 880)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 16)

        # === Header avec gradient ===
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #a855f7);
                border-radius: 0px;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 14, 20, 14)
        header_layout.setSpacing(4)

        title = QLabel("Actions en masse")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        header_layout.addWidget(title)

        subtitle = QLabel("Assignez des formations, absences, visites médicales ou compétences à plusieurs employés")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 12px;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header, 0)  # Le header ne s'étend pas

        # === Contenu principal ===
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 12, 16, 0)
        content_layout.setSpacing(12)

        # === Onglets stylisés ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                background: white;
                padding: 12px;
            }
            QTabBar::tab {
                background: #f3f4f6;
                color: #6b7280;
                padding: 8px 16px;
                margin-right: 3px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #7c3aed;
                border: 1px solid #e5e7eb;
                border-bottom: 2px solid #7c3aed;
            }
            QTabBar::tab:hover:!selected {
                background: #e5e7eb;
                color: #374151;
            }
        """)
        self.tabs.addTab(self._create_formation_tab(), "Formations")
        self.tabs.addTab(self._create_absence_tab(), "Absences")
        self.tabs.addTab(self._create_medical_tab(), "Médical")
        self.tabs.addTab(self._create_competence_tab(), "Compétences")
        self.tabs.setMinimumHeight(310)  # Hauteur minimale pour bien voir le formulaire
        content_layout.addWidget(self.tabs, 0)  # Pas de stretch pour les onglets

        # === Sélection du personnel (commune) ===
        personnel_group = QGroupBox("Sélection du personnel")
        personnel_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #374151;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                background: white;
            }
        """)
        personnel_layout = QVBoxLayout(personnel_group)
        personnel_layout.setContentsMargins(12, 20, 12, 12)
        self.personnel_widget = PersonnelSelectionWidget()
        self.personnel_widget.selection_changed.connect(self._on_selection_changed)
        personnel_layout.addWidget(self.personnel_widget)
        personnel_group.setMinimumHeight(200)  # Hauteur minimale pour voir la liste
        content_layout.addWidget(personnel_group, 1)  # Stretch pour prendre l'espace restant

        layout.addWidget(content_widget, 1)  # Le contenu prend tout l'espace disponible

        # === Footer avec boutons ===
        footer = QFrame()
        footer.setStyleSheet("""
            QFrame {
                background: #f9fafb;
                border-top: 1px solid #e5e7eb;
            }
        """)
        btn_layout = QHBoxLayout(footer)
        btn_layout.setContentsMargins(20, 12, 20, 12)
        btn_layout.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: white;
                color: #374151;
                padding: 10px 24px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #f3f4f6;
                border-color: #9ca3af;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        self.btn_assign = QPushButton("Assigner à 0 personne(s)")
        self.btn_assign.setEnabled(False)
        self.btn_assign.setCursor(Qt.PointingHandCursor)
        self.btn_assign.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #a855f7);
                color: white;
                padding: 10px 28px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #9333ea);
            }
            QPushButton:disabled {
                background: #d1d5db;
                color: #9ca3af;
            }
        """)
        self.btn_assign.clicked.connect(self._execute_operation)
        btn_layout.addWidget(self.btn_assign)

        layout.addWidget(footer, 0)  # Le footer ne s'étend pas

    def _create_formation_tab(self) -> QWidget:
        """Crée l'onglet formations."""
        self.formation_tab = FormationBulkTab()
        return self.formation_tab

    def _create_absence_tab(self) -> QWidget:
        """Crée l'onglet absences."""
        self.absence_tab = AbsenceBulkTab()
        return self.absence_tab

    def _create_medical_tab(self) -> QWidget:
        """Crée l'onglet médical."""
        self.medical_tab = MedicalBulkTab()
        return self.medical_tab

    def _create_competence_tab(self) -> QWidget:
        """Crée l'onglet compétences."""
        self.competence_tab = CompetenceBulkTab()
        return self.competence_tab

    def _on_selection_changed(self, selected_ids: List[int]):
        """Met à jour le bouton selon la sélection."""
        count = len(selected_ids)
        self.btn_assign.setText(f"Assigner à {count} personne(s)")
        self.btn_assign.setEnabled(count > 0)

    def _execute_operation(self):
        """Exécute l'opération en masse."""
        selected_ids = self.personnel_widget.get_selected_ids()

        if not selected_ids:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner au moins un employé")
            return

        # Déterminer l'onglet actif
        current_index = self.tabs.currentIndex()

        if current_index == 0:  # Formations
            valid, error = self.formation_tab.validate()
            if not valid:
                QMessageBox.warning(self, "Validation", error)
                return
            operation_type = "FORMATION"
            data = self.formation_tab.get_data()
            operation_name = data.get('intitule', 'Formation')

        elif current_index == 1:  # Absences
            valid, error = self.absence_tab.validate()
            if not valid:
                QMessageBox.warning(self, "Validation", error)
                return
            operation_type = "ABSENCE"
            data = self.absence_tab.get_data()
            operation_name = f"Absence {data.get('type_absence_code', '')}"

        elif current_index == 2:  # Médical
            valid, error = self.medical_tab.validate()
            if not valid:
                QMessageBox.warning(self, "Validation", error)
                return
            operation_type = "VISITE_MEDICALE"
            data = self.medical_tab.get_data()
            operation_name = f"Visite {data.get('type_visite', '')}"

        elif current_index == 3:  # Compétences
            valid, error = self.competence_tab.validate()
            if not valid:
                QMessageBox.warning(self, "Validation", error)
                return
            operation_type = "COMPETENCE"
            data = self.competence_tab.get_data()
            operation_name = data.get('competence_libelle', 'Compétence')

        else:
            return

        # Confirmation
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir assigner '{operation_name}' à {len(selected_ids)} employé(s) ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Lancer l'opération
        progress_dialog = BulkOperationProgressDialog(
            operation_type, data, selected_ids, parent=self
        )

        def on_completed(nb_success, nb_errors, details):
            # Afficher les résultats
            results_dialog = BulkOperationResultsDialog(
                operation_type, nb_success, nb_errors, details, parent=self
            )
            results_dialog.exec_()

            # Fermer le dialogue principal si tout est OK
            if nb_errors == 0:
                self.accept()

        progress_dialog.operation_completed.connect(on_completed)
        progress_dialog.start_operation()
        progress_dialog.exec_()
