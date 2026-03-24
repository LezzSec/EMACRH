# -*- coding: utf-8 -*-
"""
Interface de gestion des formations
Permet de visualiser, ajouter, modifier et supprimer des formations
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QComboBox, QMessageBox,
    QWidget, QTextEdit, QDateEdit, QGroupBox, QAbstractItemView, QMenu,
    QCheckBox, QDoubleSpinBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor


from core.services.formation_service_crud import FormationServiceCRUD as formation_service
from core.services.document_service import DocumentService as _DocumentService
from core.gui.components.emac_ui_kit import add_custom_title_bar, show_error_message
from core.utils.logging_config import get_logger
from core.utils.date_format import format_date

_doc_service = _DocumentService()

logger = get_logger(__name__)

# Import des composants modernes EMAC
try:
    from core.gui.components.ui_theme import EmacCard, EmacButton
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False


class GestionFormationsDialog(QDialog):
    """Fenetre principale de gestion des formations"""

    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Gestion des Formations")
        self.setGeometry(100, 100, 1300, 750)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialise l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisee
        title_bar = add_custom_title_bar(self, "Gestion des Formations")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(16)

        # === En-tete avec filtres ===
        self._create_header(layout)

        # === Filtres ===
        self._create_filters(layout)

        # === Tableau des formations ===
        self._create_table(layout)

        # === Statistiques ===
        self._create_stats(layout)

        # === Boutons d'action ===
        self._create_action_buttons(layout)

        main_layout.addWidget(content_widget)

    def _create_header(self, layout):
        """Cree l'en-tete avec boutons principaux"""
        if THEME_AVAILABLE:
            header_card = EmacCard()
            header_layout = QHBoxLayout()

            title = QLabel("Liste des formations")
            title.setFont(QFont("Segoe UI", 14, QFont.Bold))
            title.setStyleSheet("color: #1e293b;")
            header_layout.addWidget(title)

            header_layout.addStretch()

            btn_refresh = EmacButton("Actualiser", 'ghost')
            btn_refresh.clicked.connect(self.load_data)
            header_layout.addWidget(btn_refresh)

            btn_add = EmacButton("+ Nouvelle formation", 'primary')
            btn_add.clicked.connect(self.add_formation)
            header_layout.addWidget(btn_add)

            header_card.body.addLayout(header_layout)
            layout.addWidget(header_card)
        else:
            header_layout = QHBoxLayout()

            title = QLabel("Liste des formations")
            title.setFont(QFont("Arial", 12, QFont.Bold))
            header_layout.addWidget(title)

            header_layout.addStretch()

            btn_refresh = QPushButton("Actualiser")
            btn_refresh.clicked.connect(self.load_data)
            header_layout.addWidget(btn_refresh)

            btn_add = QPushButton("+ Nouvelle formation")
            btn_add.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #2563eb; }
            """)
            btn_add.clicked.connect(self.add_formation)
            header_layout.addWidget(btn_add)

            layout.addLayout(header_layout)

    def _create_filters(self, layout):
        """Cree la barre de filtres"""
        if THEME_AVAILABLE:
            filters_card = EmacCard()
            filters_layout = QHBoxLayout()

            # Filtre employe
            emp_label = QLabel("Employe:")
            emp_label.setStyleSheet("color: #475569; font-weight: 600;")
            filters_layout.addWidget(emp_label)

            self.operateur_filter = QComboBox()
            self.operateur_filter.setMinimumWidth(200)
            self.operateur_filter.currentIndexChanged.connect(self.apply_filters)
            self.operateur_filter.setStyleSheet("""
                QComboBox {
                    padding: 6px 12px;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    background: white;
                }
            """)
            filters_layout.addWidget(self.operateur_filter)

            filters_layout.addSpacing(15)

            # Filtre statut
            statut_label = QLabel("Statut:")
            statut_label.setStyleSheet("color: #475569; font-weight: 600;")
            filters_layout.addWidget(statut_label)

            self.statut_filter = QComboBox()
            self.statut_filter.addItems(["Tous", "Planifiee", "En cours", "Terminee", "Annulee"])
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
            search_label = QLabel("Recherche:")
            search_label.setStyleSheet("color: #475569; font-weight: 600;")
            filters_layout.addWidget(search_label)

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Intitule, organisme...")
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
            filters_group = QGroupBox("Filtres")
            filters_layout = QHBoxLayout()

            filters_layout.addWidget(QLabel("Employe:"))
            self.operateur_filter = QComboBox()
            self.operateur_filter.setMinimumWidth(200)
            self.operateur_filter.currentIndexChanged.connect(self.apply_filters)
            filters_layout.addWidget(self.operateur_filter)

            filters_layout.addWidget(QLabel("Statut:"))
            self.statut_filter = QComboBox()
            self.statut_filter.addItems(["Tous", "Planifiee", "En cours", "Terminee", "Annulee"])
            self.statut_filter.currentIndexChanged.connect(self.apply_filters)
            filters_layout.addWidget(self.statut_filter)

            filters_layout.addWidget(QLabel("Recherche:"))
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Intitule, organisme...")
            self.search_input.textChanged.connect(self.apply_filters)
            filters_layout.addWidget(self.search_input)

            filters_layout.addStretch()
            filters_group.setLayout(filters_layout)
            layout.addWidget(filters_group)

    def _create_table(self, layout):
        """Cree le tableau des formations"""
        if THEME_AVAILABLE:
            table_card = EmacCard()
            table_layout = QVBoxLayout()
        else:
            table_layout = layout

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "Employe", "Intitule", "Organisme", "Date debut",
            "Date fin", "Duree (h)", "Statut", "Certificat", "Attestation", "Cout"
        ])

        # Configuration
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Largeurs des colonnes
        self.table.setColumnWidth(0, 50)   # ID
        self.table.setColumnWidth(1, 140)  # Employe
        self.table.setColumnWidth(2, 180)  # Intitule
        self.table.setColumnWidth(3, 120)  # Organisme
        self.table.setColumnWidth(4, 90)   # Date debut
        self.table.setColumnWidth(5, 90)   # Date fin
        self.table.setColumnWidth(6, 60)   # Duree
        self.table.setColumnWidth(7, 90)   # Statut
        self.table.setColumnWidth(8, 70)   # Certificat
        self.table.setColumnWidth(9, 80)   # Attestation
        self.table.setColumnWidth(10, 70)  # Cout

        # Style moderne
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

        # Double-clic pour modifier
        self.table.doubleClicked.connect(self.edit_formation)

        if THEME_AVAILABLE:
            table_layout.addWidget(self.table)
            table_card.body.addLayout(table_layout)
            layout.addWidget(table_card)
        else:
            layout.addWidget(self.table)

    def _create_stats(self, layout):
        """Cree la barre de statistiques"""
        if THEME_AVAILABLE:
            stats_card = EmacCard()
            stats_layout = QHBoxLayout()

            self.lbl_total = QLabel("Total : 0")
            self.lbl_total.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.lbl_total.setStyleSheet("color: #3b82f6;")
            stats_layout.addWidget(self.lbl_total)

            stats_layout.addSpacing(20)

            self.lbl_en_cours = QLabel("En cours : 0")
            self.lbl_en_cours.setFont(QFont("Segoe UI", 10))
            self.lbl_en_cours.setStyleSheet("color: #f59e0b;")
            stats_layout.addWidget(self.lbl_en_cours)

            stats_layout.addSpacing(20)

            self.lbl_terminees = QLabel("Terminees : 0")
            self.lbl_terminees.setFont(QFont("Segoe UI", 10))
            self.lbl_terminees.setStyleSheet("color: #10b981;")
            stats_layout.addWidget(self.lbl_terminees)

            stats_layout.addSpacing(20)

            self.lbl_planifiees = QLabel("Planifiees : 0")
            self.lbl_planifiees.setFont(QFont("Segoe UI", 10))
            self.lbl_planifiees.setStyleSheet("color: #64748b;")
            stats_layout.addWidget(self.lbl_planifiees)

            stats_layout.addStretch()
            stats_card.body.addLayout(stats_layout)
            layout.addWidget(stats_card)
        else:
            stats_layout = QHBoxLayout()

            self.lbl_total = QLabel("Total : 0")
            self.lbl_total.setFont(QFont("Arial", 9, QFont.Bold))
            stats_layout.addWidget(self.lbl_total)

            self.lbl_en_cours = QLabel("En cours : 0")
            stats_layout.addWidget(self.lbl_en_cours)

            self.lbl_terminees = QLabel("Terminees : 0")
            stats_layout.addWidget(self.lbl_terminees)

            self.lbl_planifiees = QLabel("Planifiees : 0")
            stats_layout.addWidget(self.lbl_planifiees)

            stats_layout.addStretch()
            layout.addLayout(stats_layout)

    def _create_action_buttons(self, layout):
        """Cree les boutons d'action en bas"""
        btn_layout = QHBoxLayout()

        if THEME_AVAILABLE:
            btn_edit = EmacButton("Modifier", 'ghost')
            btn_edit.clicked.connect(self.edit_formation)
            btn_layout.addWidget(btn_edit)

            btn_docs = EmacButton("Generer documents", 'secondary')
            btn_docs.clicked.connect(self.generate_documents)
            btn_layout.addWidget(btn_docs)

            btn_delete = EmacButton("Supprimer", 'ghost')
            btn_delete.setStyleSheet("""
                QPushButton {
                    color: #dc2626;
                    border: 1px solid #dc2626;
                }
                QPushButton:hover {
                    background-color: #fef2f2;
                }
            """)
            btn_delete.clicked.connect(self.delete_formation)
            btn_layout.addWidget(btn_delete)

            btn_layout.addStretch()

            btn_close = EmacButton("Fermer", 'ghost')
            btn_close.clicked.connect(self.accept)
            btn_layout.addWidget(btn_close)
        else:
            btn_edit = QPushButton("Modifier")
            btn_edit.clicked.connect(self.edit_formation)
            btn_layout.addWidget(btn_edit)

            btn_docs = QPushButton("Generer documents")
            btn_docs.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    font-weight: bold;
                    padding: 6px 14px;
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #059669; }
            """)
            btn_docs.clicked.connect(self.generate_documents)
            btn_layout.addWidget(btn_docs)

            btn_delete = QPushButton("Supprimer")
            btn_delete.setStyleSheet("color: #dc2626;")
            btn_delete.clicked.connect(self.delete_formation)
            btn_layout.addWidget(btn_delete)

            btn_layout.addStretch()

            btn_close = QPushButton("Fermer")
            btn_close.clicked.connect(self.accept)
            btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def load_data(self):
        """Charge les donnees"""
        self._load_operateurs()
        self._load_formations()
        self._update_stats()

    def _load_operateurs(self):
        """Charge la liste des operateurs"""
        self.operateur_filter.blockSignals(True)
        self.operateur_filter.clear()
        self.operateur_filter.addItem("Tous les employes", None)

        operateurs = formation_service.get_personnel_list()
        for op in operateurs:
            self.operateur_filter.addItem(
                f"{op['nom_complet']} ({op['matricule']})",
                op['id']
            )

        self.operateur_filter.blockSignals(False)

    def _load_formations(self):
        """Charge les formations dans le tableau"""
        # Recuperer les filtres
        operateur_id = self.operateur_filter.currentData()
        statut_text = self.statut_filter.currentText()
        statut = None if statut_text == "Tous" else statut_text

        # Charger les formations
        formations = formation_service.get_all_formations(
            statut=statut,
            operateur_id=operateur_id
        )

        # Appliquer le filtre de recherche
        search_text = self.search_input.text().lower().strip()
        if search_text:
            formations = [
                f for f in formations
                if search_text in (f.get('intitule') or '').lower()
                or search_text in (f.get('organisme') or '').lower()
                or search_text in (f.get('nom_complet') or '').lower()
            ]

        # Remplir le tableau
        self.table.setRowCount(len(formations))

        for row, formation in enumerate(formations):
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(formation['id'])))

            # Employe
            self.table.setItem(row, 1, QTableWidgetItem(formation.get('nom_complet', '')))

            # Intitule
            self.table.setItem(row, 2, QTableWidgetItem(formation.get('intitule', '')))

            # Organisme
            self.table.setItem(row, 3, QTableWidgetItem(formation.get('organisme') or ''))

            # Date debut
            date_debut = formation.get('date_debut')
            if date_debut:
                if isinstance(date_debut, str):
                    date_str = date_debut
                else:
                    date_str = format_date(date_debut)
                self.table.setItem(row, 4, QTableWidgetItem(date_str))
            else:
                self.table.setItem(row, 4, QTableWidgetItem(''))

            # Date fin
            date_fin = formation.get('date_fin')
            if date_fin:
                if isinstance(date_fin, str):
                    date_str = date_fin
                else:
                    date_str = format_date(date_fin)
                self.table.setItem(row, 5, QTableWidgetItem(date_str))
            else:
                self.table.setItem(row, 5, QTableWidgetItem(''))

            # Duree
            duree = formation.get('duree_heures')
            if duree:
                self.table.setItem(row, 6, QTableWidgetItem(f"{duree:.1f}"))
            else:
                self.table.setItem(row, 6, QTableWidgetItem(''))

            # Statut avec couleur
            statut_item = QTableWidgetItem(formation.get('statut', ''))
            statut_val = formation.get('statut', '')
            if statut_val == 'Terminee' or statut_val == 'Terminée':
                statut_item.setForeground(QColor('#10b981'))
            elif statut_val == 'En cours':
                statut_item.setForeground(QColor('#f59e0b'))
            elif statut_val == 'Annulee' or statut_val == 'Annulée':
                statut_item.setForeground(QColor('#dc2626'))
            else:  # Planifiee
                statut_item.setForeground(QColor('#64748b'))
            self.table.setItem(row, 7, statut_item)

            # Certificat
            cert = formation.get('certificat_obtenu', False)
            cert_text = "Oui" if cert else "Non"
            cert_item = QTableWidgetItem(cert_text)
            if cert:
                cert_item.setForeground(QColor('#10b981'))
            self.table.setItem(row, 8, cert_item)

            # Attestation (document joint)
            attestation_nom = formation.get('attestation_nom')
            if attestation_nom:
                att_item = QTableWidgetItem("📄 Oui")
                att_item.setForeground(QColor('#10b981'))
                att_item.setToolTip(attestation_nom)
            else:
                att_item = QTableWidgetItem("-")
                att_item.setForeground(QColor('#94a3b8'))
            self.table.setItem(row, 9, att_item)

            # Cout
            cout = formation.get('cout')
            if cout:
                self.table.setItem(row, 10, QTableWidgetItem(f"{cout:.2f} EUR"))
            else:
                self.table.setItem(row, 10, QTableWidgetItem(''))

    def _update_stats(self):
        """Met a jour les statistiques"""
        stats = formation_service.get_formations_stats()

        self.lbl_total.setText(f"Total : {stats.get('total', 0)}")
        self.lbl_en_cours.setText(f"En cours : {stats.get('en_cours', 0)}")
        self.lbl_terminees.setText(f"Terminees : {stats.get('terminees_cette_annee', 0)}")
        self.lbl_planifiees.setText(f"Planifiees : {stats.get('planifiees', 0)}")

    def apply_filters(self):
        """Applique les filtres"""
        self._load_formations()

    def show_context_menu(self, position):
        """Affiche le menu contextuel"""
        if self.table.selectedItems():
            menu = QMenu()
            menu.addAction("Modifier", self.edit_formation)
            menu.addSeparator()
            menu.addAction("Generer les documents", self.generate_documents)
            menu.addSeparator()
            menu.addAction("Supprimer", self.delete_formation)
            menu.exec_(self.table.viewport().mapToGlobal(position))

    def get_selected_formation_id(self):
        """Retourne l'ID de la formation selectionnee"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            id_item = self.table.item(row, 0)
            if id_item:
                return int(id_item.text())
        return None

    def add_formation(self):
        """Ouvre le dialogue d'ajout"""
        dialog = AddEditFormationDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
            self.data_changed.emit()

    def edit_formation(self):
        """Ouvre le dialogue de modification"""
        formation_id = self.get_selected_formation_id()
        if not formation_id:
            QMessageBox.warning(self, "Selection", "Veuillez selectionner une formation.")
            return

        formation = formation_service.get_formation_by_id(formation_id)
        if formation:
            dialog = AddEditFormationDialog(formation=formation, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_data()
                self.data_changed.emit()

    def generate_documents(self):
        """Genere les documents officiels pré-remplis pour la formation selectionnee"""
        formation_id = self.get_selected_formation_id()
        if not formation_id:
            QMessageBox.warning(self, "Selection", "Veuillez selectionner une formation.")
            return

        try:
            from core.services.formation_export_service import FormationExportService
            data = formation_service.get_formation_by_id(formation_id)
            if not data:
                QMessageBox.warning(self, "Erreur", "Formation introuvable.")
                return

            success, msg, path = FormationExportService.generate_dossier_formation(data)
            if success and path:
                reply = QMessageBox.information(
                    self, "Documents generés",
                    f"Dossier de formation généré :\n{path}\n\nOuvrir le fichier ?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    FormationExportService.open_file(path)
            else:
                QMessageBox.warning(self, "Generation echouee", msg)
        except Exception as e:
            logger.exception(f"Erreur génération documents: {e}")
            show_error_message(self, "Erreur", "Impossible de générer les documents", e)

    def delete_formation(self):
        """Supprime la formation selectionnee"""
        formation_id = self.get_selected_formation_id()
        if not formation_id:
            QMessageBox.warning(self, "Selection", "Veuillez selectionner une formation.")
            return

        reply = QMessageBox.question(
            self, "Confirmation",
            "Etes-vous sur de vouloir supprimer cette formation ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, message = formation_service.delete_formation(formation_id)
            if success:
                QMessageBox.information(self, "Succes", message)
                self.load_data()
                self.data_changed.emit()
            else:
                QMessageBox.critical(self, "Erreur", message)


class AddEditFormationDialog(QDialog):
    """Dialogue d'ajout/modification de formation"""

    def __init__(self, formation=None, parent=None):
        super().__init__(parent)
        self.formation = formation
        self.is_edit = formation is not None
        self.document_id = formation.get('document_id') if formation else None

        self.setWindowTitle("Modifier la formation" if self.is_edit else "Nouvelle formation")
        self.setFixedSize(640, 820)

        self.init_ui()

        if self.is_edit:
            self.load_formation_data()

    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Titre
        title = QLabel("Modifier la formation" if self.is_edit else "Nouvelle formation")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        layout.addWidget(title)

        # Formulaire
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Employe
        self.operateur_combo = QComboBox()
        self.operateur_combo.setMinimumWidth(300)
        self._load_operateurs()
        form_layout.addRow("Employe *:", self.operateur_combo)

        # Intitule
        self.intitule_input = QLineEdit()
        self.intitule_input.setPlaceholderText("Ex: Formation securite incendie")
        form_layout.addRow("Intitule *:", self.intitule_input)

        # Organisme
        self.organisme_input = QLineEdit()
        self.organisme_input.setPlaceholderText("Ex: AFPA, CNAM...")
        form_layout.addRow("Organisme:", self.organisme_input)

        # Lieu
        self.lieu_input = QLineEdit()
        self.lieu_input.setPlaceholderText("Ex: Salle de formation Bat A, site externe...")
        form_layout.addRow("Lieu:", self.lieu_input)

        # Formateur
        self.formateur_input = QLineEdit()
        self.formateur_input.setPlaceholderText("Nom du formateur / intervenant")
        form_layout.addRow("Formateur:", self.formateur_input)

        # Objectif
        self.objectif_text = QTextEdit()
        self.objectif_text.setMaximumHeight(65)
        self.objectif_text.setPlaceholderText("Objectif pédagogique de la formation...")
        form_layout.addRow("Objectif:", self.objectif_text)

        # Dates
        dates_layout = QHBoxLayout()

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        dates_layout.addWidget(QLabel("Debut *:"))
        dates_layout.addWidget(self.date_debut)

        dates_layout.addSpacing(20)

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        dates_layout.addWidget(QLabel("Fin *:"))
        dates_layout.addWidget(self.date_fin)

        dates_layout.addStretch()
        form_layout.addRow("Dates:", dates_layout)

        # Duree en heures
        self.duree_spin = QDoubleSpinBox()
        self.duree_spin.setRange(0, 9999)
        self.duree_spin.setDecimals(1)
        self.duree_spin.setSuffix(" h")
        form_layout.addRow("Duree:", self.duree_spin)

        # Statut
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(["Planifiee", "En cours", "Terminee", "Annulee"])
        form_layout.addRow("Statut:", self.statut_combo)

        # Certificat obtenu
        self.certificat_check = QCheckBox("Certificat obtenu")
        form_layout.addRow("", self.certificat_check)

        # Cout
        self.cout_spin = QDoubleSpinBox()
        self.cout_spin.setRange(0, 999999)
        self.cout_spin.setDecimals(2)
        self.cout_spin.setSuffix(" EUR")
        form_layout.addRow("Cout:", self.cout_spin)

        # Commentaire
        self.commentaire_text = QTextEdit()
        self.commentaire_text.setMaximumHeight(80)
        self.commentaire_text.setPlaceholderText("Notes ou commentaires...")
        form_layout.addRow("Commentaire:", self.commentaire_text)

        layout.addLayout(form_layout)

        # === Section Attestation ===
        attestation_group = QGroupBox("Attestation / Certificat")
        attestation_layout = QVBoxLayout()

        # Label affichant le document lié
        self.attestation_label = QLabel("Aucune attestation jointe")
        self.attestation_label.setStyleSheet("color: #64748b; font-style: italic;")
        attestation_layout.addWidget(self.attestation_label)

        # Boutons
        btn_attestation_layout = QHBoxLayout()

        self.btn_joindre = QPushButton("Joindre une attestation...")
        self.btn_joindre.clicked.connect(self.joindre_attestation)
        self.btn_joindre.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_attestation_layout.addWidget(self.btn_joindre)

        self.btn_voir = QPushButton("Voir")
        self.btn_voir.clicked.connect(self.voir_attestation)
        self.btn_voir.setEnabled(False)
        btn_attestation_layout.addWidget(self.btn_voir)

        self.btn_supprimer_doc = QPushButton("Retirer")
        self.btn_supprimer_doc.clicked.connect(self.retirer_attestation)
        self.btn_supprimer_doc.setEnabled(False)
        self.btn_supprimer_doc.setStyleSheet("color: #dc2626;")
        btn_attestation_layout.addWidget(self.btn_supprimer_doc)

        btn_attestation_layout.addStretch()
        attestation_layout.addLayout(btn_attestation_layout)

        attestation_group.setLayout(attestation_layout)
        layout.addWidget(attestation_group)

        layout.addStretch()

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Enregistrer")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        btn_save.clicked.connect(self.save_formation)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _load_operateurs(self):
        """Charge la liste des operateurs"""
        operateurs = formation_service.get_personnel_list()
        for op in operateurs:
            self.operateur_combo.addItem(
                f"{op['nom_complet']} ({op['matricule']})",
                op['id']
            )

    def load_formation_data(self):
        """Charge les donnees de la formation a modifier"""
        if not self.formation:
            return

        # Operateur
        operateur_id = self.formation.get('operateur_id')
        for i in range(self.operateur_combo.count()):
            if self.operateur_combo.itemData(i) == operateur_id:
                self.operateur_combo.setCurrentIndex(i)
                break

        # Intitule
        self.intitule_input.setText(self.formation.get('intitule', ''))

        # Organisme
        self.organisme_input.setText(self.formation.get('organisme') or '')

        # Lieu
        self.lieu_input.setText(self.formation.get('lieu') or '')

        # Formateur
        self.formateur_input.setText(self.formation.get('formateur') or '')

        # Objectif
        self.objectif_text.setPlainText(self.formation.get('objectif') or '')

        # Dates
        date_debut = self.formation.get('date_debut')
        if date_debut:
            if isinstance(date_debut, str):
                self.date_debut.setDate(QDate.fromString(date_debut, "yyyy-MM-dd"))
            else:
                self.date_debut.setDate(QDate(date_debut.year, date_debut.month, date_debut.day))

        date_fin = self.formation.get('date_fin')
        if date_fin:
            if isinstance(date_fin, str):
                self.date_fin.setDate(QDate.fromString(date_fin, "yyyy-MM-dd"))
            else:
                self.date_fin.setDate(QDate(date_fin.year, date_fin.month, date_fin.day))

        # Duree
        duree = self.formation.get('duree_heures')
        if duree:
            self.duree_spin.setValue(float(duree))

        # Statut
        statut = self.formation.get('statut', 'Planifiee')
        # Normaliser le statut (enlever les accents pour la comparaison)
        statut_map = {
            'Planifiée': 'Planifiee',
            'Terminée': 'Terminee',
            'Annulée': 'Annulee',
            'En cours': 'En cours'
        }
        statut_normalized = statut_map.get(statut, statut)
        index = self.statut_combo.findText(statut_normalized)
        if index >= 0:
            self.statut_combo.setCurrentIndex(index)

        # Certificat
        self.certificat_check.setChecked(bool(self.formation.get('certificat_obtenu')))

        # Cout
        cout = self.formation.get('cout')
        if cout:
            self.cout_spin.setValue(float(cout))

        # Commentaire
        self.commentaire_text.setText(self.formation.get('commentaire') or '')

        # Attestation
        self.document_id = self.formation.get('document_id')
        attestation_nom = self.formation.get('attestation_nom')
        if self.document_id and attestation_nom:
            self.attestation_label.setText(f"📄 {attestation_nom}")
            self.attestation_label.setStyleSheet("color: #10b981; font-weight: bold;")
            self.btn_voir.setEnabled(True)
            self.btn_supprimer_doc.setEnabled(True)

    def joindre_attestation(self):
        """Ouvre le dialogue pour joindre une attestation"""
        operateur_id = self.operateur_combo.currentData()
        if not operateur_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord selectionner un employe.")
            return

        try:
            from core.gui.dialogs.gestion_documentaire import AddDocumentDialog

            # Ouvrir le dialogue d'ajout de document
            dialog = AddDocumentDialog(operateur_id=operateur_id, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                # Récupérer l'ID du document créé
                if hasattr(dialog, 'created_document_id') and dialog.created_document_id:
                    self.document_id = dialog.created_document_id
                    self._update_attestation_display()
                    QMessageBox.information(self, "Succes", "Attestation jointe avec succes.")
        except Exception as e:
            logger.exception(f"Erreur joindre attestation: {e}")
            show_error_message(self, "Erreur", "Impossible de joindre l'attestation", e)

    def voir_attestation(self):
        """Ouvre l'attestation jointe"""
        if not self.document_id:
            return

        try:
            import os
            import sys
            import subprocess

            file_path = _doc_service.get_document_path(self.document_id)

            if file_path and file_path.exists():
                if sys.platform == 'win32':
                    os.startfile(str(file_path))
                elif sys.platform == 'darwin':
                    subprocess.run(['open', str(file_path)])
                else:
                    subprocess.run(['xdg-open', str(file_path)])
            else:
                QMessageBox.warning(self, "Erreur", "Fichier introuvable.")
        except Exception as e:
            logger.exception(f"Erreur voir attestation: {e}")
            show_error_message(self, "Erreur", "Impossible d'ouvrir l'attestation", e)

    def retirer_attestation(self):
        """Retire le lien vers l'attestation (ne supprime pas le fichier)"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Retirer le lien vers cette attestation ?\n(Le document restera dans la base)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.document_id = None
            self.attestation_label.setText("Aucune attestation jointe")
            self.attestation_label.setStyleSheet("color: #64748b; font-style: italic;")
            self.btn_voir.setEnabled(False)
            self.btn_supprimer_doc.setEnabled(False)

    def _update_attestation_display(self):
        """Met à jour l'affichage de l'attestation"""
        if self.document_id:
            try:
                nom_fichier = _doc_service.get_document_nom(self.document_id)

                if nom_fichier:
                    self.attestation_label.setText(f"📄 {nom_fichier}")
                    self.attestation_label.setStyleSheet("color: #10b981; font-weight: bold;")
                    self.btn_voir.setEnabled(True)
                    self.btn_supprimer_doc.setEnabled(True)
            except Exception:
                pass

    def save_formation(self):
        """Enregistre la formation"""
        # Validation
        operateur_id = self.operateur_combo.currentData()
        if not operateur_id:
            QMessageBox.warning(self, "Validation", "Veuillez selectionner un employe.")
            return

        intitule = self.intitule_input.text().strip()
        if not intitule:
            QMessageBox.warning(self, "Validation", "L'intitule est obligatoire.")
            return

        # Recuperer les valeurs
        organisme = self.organisme_input.text().strip() or None
        lieu = self.lieu_input.text().strip() or None
        formateur = self.formateur_input.text().strip() or None
        objectif = self.objectif_text.toPlainText().strip() or None
        date_debut = self.date_debut.date().toPyDate()
        date_fin = self.date_fin.date().toPyDate()

        if date_fin < date_debut:
            QMessageBox.warning(self, "Validation", "La date de fin doit etre posterieure a la date de debut.")
            return

        duree_heures = self.duree_spin.value() if self.duree_spin.value() > 0 else None

        # Mapper le statut vers les valeurs de la base (avec accents)
        statut_text = self.statut_combo.currentText()
        statut_map = {
            'Planifiee': 'Planifiée',
            'Terminee': 'Terminée',
            'Annulee': 'Annulée',
            'En cours': 'En cours'
        }
        statut = statut_map.get(statut_text, statut_text)

        certificat_obtenu = self.certificat_check.isChecked()
        cout = self.cout_spin.value() if self.cout_spin.value() > 0 else None
        commentaire = self.commentaire_text.toPlainText().strip() or None

        saved_formation_id = None

        if self.is_edit:
            success, message = formation_service.update_formation(
                self.formation['id'],
                operateur_id=operateur_id,
                intitule=intitule,
                organisme=organisme,
                lieu=lieu,
                objectif=objectif,
                formateur=formateur,
                date_debut=date_debut,
                date_fin=date_fin,
                duree_heures=duree_heures,
                statut=statut,
                certificat_obtenu=certificat_obtenu,
                cout=cout,
                commentaire=commentaire,
                document_id=self.document_id
            )
            if success:
                saved_formation_id = self.formation['id']
        else:
            success, message, formation_id = formation_service.add_formation(
                operateur_id=operateur_id,
                intitule=intitule,
                organisme=organisme,
                lieu=lieu,
                objectif=objectif,
                formateur=formateur,
                date_debut=date_debut,
                date_fin=date_fin,
                duree_heures=duree_heures,
                statut=statut,
                certificat_obtenu=certificat_obtenu,
                cout=cout,
                commentaire=commentaire
            )
            if success:
                saved_formation_id = formation_id
                if self.document_id and formation_id:
                    formation_service.update_formation(formation_id, document_id=self.document_id)

        if success:
            reply = QMessageBox.question(
                self, "Formation enregistree",
                f"{message}\n\nVoulez-vous générer les documents de formation pré-remplis ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes and saved_formation_id:
                self._generate_documents(saved_formation_id)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", message)

    def _generate_documents(self, formation_id: int):
        """Génère les documents officiels de formation pré-remplis."""
        try:
            from core.services.formation_export_service import FormationExportService
            data = formation_service.get_formation_by_id(formation_id)
            if not data:
                QMessageBox.warning(self, "Erreur", "Formation introuvable pour la génération.")
                return

            success, msg, path = FormationExportService.generate_dossier_formation(data)
            if success and path:
                reply = QMessageBox.information(
                    self, "Documents générés",
                    f"Dossier de formation généré :\n{path}\n\nOuvrir le fichier ?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    FormationExportService.open_file(path)
            else:
                QMessageBox.warning(self, "Génération échouée", msg)
        except Exception as e:
            logger.exception(f"Erreur génération documents formation: {e}")
            show_error_message(self, "Erreur", "Impossible de générer les documents", e)
