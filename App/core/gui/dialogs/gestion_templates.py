# -*- coding: utf-8 -*-
"""
Interface de gestion des documents templates.

Permet de visualiser, générer et ouvrir les templates de documents
(consignes, formulaires d'évaluation, etc.) avec pré-remplissage automatique.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QWidget,
    QMessageBox, QGroupBox, QCheckBox, QGridLayout, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from core.gui.components.emac_ui_kit import add_custom_title_bar
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

from core.gui.components.ui_theme import EmacCard, EmacButton

THEME_AVAILABLE = True  # toujours disponible — conservé pour compat branches existantes


class GestionTemplatesDialog(QDialog):
    """Fenêtre principale de gestion des templates de documents."""

    template_generated = pyqtSignal(str)  # Signal émis avec le chemin du fichier généré

    def __init__(self, operateur_id=None, operateur_nom="", operateur_prenom="", parent=None):
        """
        Initialise la fenêtre de gestion des templates.

        Args:
            operateur_id: ID de l'opérateur (optionnel, pour filtrer par poste)
            operateur_nom: Nom de l'opérateur pour pré-remplissage
            operateur_prenom: Prénom de l'opérateur pour pré-remplissage
            parent: Widget parent
        """
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.operateur_nom = operateur_nom
        self.operateur_prenom = operateur_prenom
        self.templates_data = []

        self.setWindowTitle("Documents Templates")
        self.setGeometry(100, 100, 1000, 600)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        self.init_ui()
        self.load_templates()

    def init_ui(self):
        """Initialise l'interface utilisateur."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Documents Templates")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(16)

        # === En-tête avec infos opérateur ===
        self._create_header(layout)

        # === Filtres ===
        self._create_filters(layout)

        # === Table des templates ===
        self._create_table(layout)

        # === Boutons d'action ===
        self._create_action_buttons(layout)

        main_layout.addWidget(content_widget)

    def _create_header(self, layout):
        """Crée l'en-tête avec les infos de l'opérateur."""
        if THEME_AVAILABLE:
            header_card = EmacCard()
            header_layout = QHBoxLayout()

            # Info opérateur si spécifié
            if self.operateur_nom or self.operateur_prenom:
                op_label = QLabel(f"Opérateur: {self.operateur_prenom} {self.operateur_nom}")
                op_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
                op_label.setStyleSheet("color: #1e293b;")
                header_layout.addWidget(op_label)
            else:
                info_label = QLabel("Sélectionnez un template pour le générer")
                info_label.setFont(QFont("Segoe UI", 10))
                info_label.setStyleSheet("color: #64748b;")
                header_layout.addWidget(info_label)

            header_layout.addStretch()

            # Champ auditeur
            aud_label = QLabel("Auditeur:")
            aud_label.setStyleSheet("color: #475569; font-weight: 600;")
            header_layout.addWidget(aud_label)

            self.auditeur_input = QLineEdit()
            self.auditeur_input.setPlaceholderText("Nom de l'auditeur (optionnel)")
            self.auditeur_input.setMinimumWidth(200)
            self.auditeur_input.setStyleSheet("""
                QLineEdit {
                    padding: 8px 12px;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    background: white;
                }
            """)
            header_layout.addWidget(self.auditeur_input)

            header_card.body.addLayout(header_layout)
            layout.addWidget(header_card)
        else:
            # Fallback simple
            header_layout = QHBoxLayout()

            if self.operateur_nom or self.operateur_prenom:
                op_label = QLabel(f"Opérateur: {self.operateur_prenom} {self.operateur_nom}")
                op_label.setFont(QFont("Arial", 10, QFont.Bold))
                header_layout.addWidget(op_label)

            header_layout.addStretch()

            aud_label = QLabel("Auditeur:")
            header_layout.addWidget(aud_label)

            self.auditeur_input = QLineEdit()
            self.auditeur_input.setPlaceholderText("Nom de l'auditeur")
            self.auditeur_input.setMinimumWidth(200)
            header_layout.addWidget(self.auditeur_input)

            layout.addLayout(header_layout)

    def _create_filters(self, layout):
        """Crée les filtres de contexte."""
        if THEME_AVAILABLE:
            filters_card = EmacCard()
            filters_layout = QHBoxLayout()

            # Filtre contexte
            ctx_label = QLabel("Contexte:")
            ctx_label.setStyleSheet("color: #475569; font-weight: 600;")
            filters_layout.addWidget(ctx_label)

            self.contexte_combo = QComboBox()
            self.contexte_combo.addItem("Tous les contextes", "")
            self.contexte_combo.addItem("Nouvel opérateur", "NOUVEL_OPERATEUR")
            self.contexte_combo.addItem("Passage niveau 3", "NIVEAU_3")
            self.contexte_combo.addItem("Par poste", "POSTE")
            self.contexte_combo.setMinimumWidth(180)
            self.contexte_combo.currentIndexChanged.connect(self.filter_templates)
            self.contexte_combo.setStyleSheet("""
                QComboBox {
                    padding: 8px 12px;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    background: white;
                }
            """)
            filters_layout.addWidget(self.contexte_combo)

            filters_layout.addSpacing(20)

            # Recherche
            search_label = QLabel("Rechercher:")
            search_label.setStyleSheet("color: #475569; font-weight: 600;")
            filters_layout.addWidget(search_label)

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Nom du document...")
            self.search_input.setMinimumWidth(200)
            self.search_input.textChanged.connect(self.filter_templates)
            self.search_input.setStyleSheet("""
                QLineEdit {
                    padding: 8px 12px;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    background: white;
                }
            """)
            filters_layout.addWidget(self.search_input)

            filters_layout.addStretch()

            # Checkbox pour afficher uniquement les templates du poste
            if self.operateur_id:
                self.show_poste_only = QCheckBox("Mes postes uniquement")
                self.show_poste_only.setStyleSheet("color: #475569;")
                self.show_poste_only.stateChanged.connect(self.filter_templates)
                filters_layout.addWidget(self.show_poste_only)

            filters_card.body.addLayout(filters_layout)
            layout.addWidget(filters_card)
        else:
            # Fallback simple
            filters_layout = QHBoxLayout()

            filters_layout.addWidget(QLabel("Contexte:"))
            self.contexte_combo = QComboBox()
            self.contexte_combo.addItem("Tous", "")
            self.contexte_combo.addItem("Nouvel opérateur", "NOUVEL_OPERATEUR")
            self.contexte_combo.addItem("Niveau 3", "NIVEAU_3")
            self.contexte_combo.addItem("Par poste", "POSTE")
            self.contexte_combo.currentIndexChanged.connect(self.filter_templates)
            filters_layout.addWidget(self.contexte_combo)

            filters_layout.addWidget(QLabel("Rechercher:"))
            self.search_input = QLineEdit()
            self.search_input.textChanged.connect(self.filter_templates)
            filters_layout.addWidget(self.search_input)

            filters_layout.addStretch()

            if self.operateur_id:
                self.show_poste_only = QCheckBox("Mes postes")
                self.show_poste_only.stateChanged.connect(self.filter_templates)
                filters_layout.addWidget(self.show_poste_only)

            layout.addLayout(filters_layout)

    def _create_table(self, layout):
        """Crée la table des templates."""
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom du document", "Contexte", "Postes associés", "Obligatoire", "Stockage", "Actions"
        ])

        # Style de la table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #f1f5f9;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f5f9;
            }
            QTableWidget::item:selected {
                background-color: #e0f2fe;
                color: #0369a1;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: bold;
                color: #334155;
            }
        """)

        # Configuration des colonnes
        header = self.table.horizontalHeader()
        self.table.setColumnHidden(0, True)  # Cacher ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Contexte
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Postes
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Obligatoire
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Stockage
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # Actions
        self.table.setColumnWidth(6, 220)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table)

    def _create_action_buttons(self, layout):
        """Crée les boutons d'action en bas."""
        buttons_layout = QHBoxLayout()

        if THEME_AVAILABLE:
            btn_refresh = EmacButton("Actualiser", 'ghost')
            btn_refresh.clicked.connect(self.load_templates)
            buttons_layout.addWidget(btn_refresh)

            btn_import_new = QPushButton("Importer un template")
            btn_import_new.setStyleSheet("""
                QPushButton {
                    background-color: #10b981; color: white; font-weight: bold;
                    padding: 10px 20px; border-radius: 6px; font-size: 13px;
                }
                QPushButton:hover { background-color: #059669; }
            """)
            btn_import_new.clicked.connect(self._open_import_dialog)
            buttons_layout.addWidget(btn_import_new)

            buttons_layout.addStretch()

            btn_generate_selected = EmacButton("Générer les sélectionnés", 'primary')
            btn_generate_selected.clicked.connect(self.generate_selected_templates)
            buttons_layout.addWidget(btn_generate_selected)

            btn_close = EmacButton("Fermer", 'ghost')
            btn_close.clicked.connect(self.close)
            buttons_layout.addWidget(btn_close)
        else:
            btn_refresh = QPushButton("Actualiser")
            btn_refresh.clicked.connect(self.load_templates)
            buttons_layout.addWidget(btn_refresh)

            btn_import_new = QPushButton("Importer un template")
            btn_import_new.setStyleSheet("""
                QPushButton {
                    background-color: #10b981; color: white; font-weight: bold;
                    padding: 10px 20px; border-radius: 6px;
                }
                QPushButton:hover { background-color: #059669; }
            """)
            btn_import_new.clicked.connect(self._open_import_dialog)
            buttons_layout.addWidget(btn_import_new)

            buttons_layout.addStretch()

            btn_generate_selected = QPushButton("Générer les sélectionnés")
            btn_generate_selected.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 6px;
                }
                QPushButton:hover { background-color: #2563eb; }
            """)
            btn_generate_selected.clicked.connect(self.generate_selected_templates)
            buttons_layout.addWidget(btn_generate_selected)

            btn_close = QPushButton("Fermer")
            btn_close.clicked.connect(self.close)
            buttons_layout.addWidget(btn_close)

        layout.addLayout(buttons_layout)

    def _open_import_dialog(self):
        """Ouvre le dialog d'import de nouveau template."""
        dialog = ImportTemplateDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_templates()

    def load_templates(self):
        """Charge les templates depuis la base de données."""
        try:
            from domain.services.documents.template_service import (
                get_all_templates, check_templates_table_exists,
                get_postes_for_operateur
            )

            if not check_templates_table_exists():
                QMessageBox.warning(
                    self,
                    "Table non trouvée",
                    "La table 'documents_templates' n'existe pas.\n"
                    "Veuillez exécuter la migration SQL correspondante."
                )
                return

            self.templates_data = get_all_templates()

            # Récupérer les postes de l'opérateur si spécifié
            self.operateur_postes = []
            if self.operateur_id:
                self.operateur_postes = get_postes_for_operateur(self.operateur_id)

            self.filter_templates()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors du chargement des templates:\n{str(e)}"
            )

    def filter_templates(self):
        """Filtre les templates selon les critères sélectionnés."""
        filtered = self.templates_data.copy()

        # Filtre par contexte
        contexte_filter = self.contexte_combo.currentData()
        if contexte_filter:
            filtered = [t for t in filtered if t['contexte'] == contexte_filter]

        # Filtre par recherche
        search_text = self.search_input.text().lower().strip()
        if search_text:
            filtered = [t for t in filtered if search_text in t['nom'].lower()]

        # Filtre par postes de l'opérateur
        if self.operateur_id and hasattr(self, 'show_poste_only') and self.show_poste_only.isChecked():
            new_filtered = []
            for t in filtered:
                if t['contexte'] != 'POSTE':
                    new_filtered.append(t)
                elif any(p in self.operateur_postes for p in t.get('postes_associes', [])):
                    new_filtered.append(t)
            filtered = new_filtered

        self.display_templates(filtered)

    def display_templates(self, templates):
        """Affiche les templates dans la table."""
        self.table.setRowCount(0)

        contexte_labels = {
            'NOUVEL_OPERATEUR': 'Nouvel opérateur',
            'NIVEAU_3': 'Niveau 3',
            'POSTE': 'Par poste'
        }

        contexte_colors = {
            'NOUVEL_OPERATEUR': '#10b981',  # Vert
            'NIVEAU_3': '#8b5cf6',  # Violet
            'POSTE': '#3b82f6'  # Bleu
        }

        for row, template in enumerate(templates):
            self.table.insertRow(row)

            # ID (caché)
            self.table.setItem(row, 0, QTableWidgetItem(str(template['id'])))

            # Nom avec checkbox
            name_widget = QWidget()
            name_layout = QHBoxLayout(name_widget)
            name_layout.setContentsMargins(5, 0, 5, 0)

            checkbox = QCheckBox()
            checkbox.setProperty('template_id', template['id'])
            name_layout.addWidget(checkbox)

            name_label = QLabel(template['nom'])
            name_label.setStyleSheet("color: #1e293b; font-weight: 500;")
            name_layout.addWidget(name_label)
            name_layout.addStretch()

            self.table.setCellWidget(row, 1, name_widget)

            # Contexte avec badge coloré
            ctx_label = contexte_labels.get(template['contexte'], template['contexte'])
            ctx_color = contexte_colors.get(template['contexte'], '#64748b')
            ctx_widget = QLabel(ctx_label)
            ctx_widget.setAlignment(Qt.AlignCenter)
            ctx_widget.setStyleSheet(f"""
                background-color: {ctx_color}20;
                color: {ctx_color};
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: 600;
            """)
            self.table.setCellWidget(row, 2, ctx_widget)

            # Postes associés
            postes = template.get('postes_associes', [])
            postes_text = ", ".join(postes) if postes else "-"
            if len(postes_text) > 30:
                postes_text = postes_text[:27] + "..."
            postes_item = QTableWidgetItem(postes_text)
            postes_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, postes_item)

            # Obligatoire
            oblig_text = "Oui" if template.get('obligatoire') else "Non"
            oblig_item = QTableWidgetItem(oblig_text)
            oblig_item.setTextAlignment(Qt.AlignCenter)
            if template.get('obligatoire'):
                oblig_item.setForeground(QColor('#dc2626'))
            self.table.setItem(row, 4, oblig_item)

            # Stockage (BLOB ou FILESYSTEM)
            stockage = template.get('stockage_type', 'FILESYSTEM')
            stockage_label = QLabel("En base" if stockage == 'BLOB' else "Fichier")
            stockage_label.setAlignment(Qt.AlignCenter)
            if stockage == 'BLOB':
                stockage_label.setStyleSheet("""
                    background-color: #10b98120;
                    color: #10b981;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-weight: 600;
                """)
            else:
                stockage_label.setStyleSheet("""
                    background-color: #f59e0b20;
                    color: #f59e0b;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-weight: 600;
                """)
            self.table.setCellWidget(row, 5, stockage_label)

            # Boutons d'action
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 2, 5, 2)
            action_layout.setSpacing(4)

            btn_generate = QPushButton("Generer")
            btn_generate.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    padding: 5px 12px;
                    border-radius: 4px;
                    font-weight: 500;
                }
                QPushButton:hover { background-color: #2563eb; }
            """)
            btn_generate.clicked.connect(lambda checked, t=template: self.generate_template(t))
            action_layout.addWidget(btn_generate)

            btn_upload = QPushButton("Importer")
            btn_upload.setToolTip("Importer/remplacer le fichier template depuis votre PC")
            btn_upload.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-weight: 500;
                }
                QPushButton:hover { background-color: #059669; }
            """)
            btn_upload.clicked.connect(lambda checked, t=template: self.upload_template_file(t))
            action_layout.addWidget(btn_upload)

            self.table.setCellWidget(row, 6, action_widget)

            self.table.setRowHeight(row, 45)

    def upload_template_file(self, template):
        """Importe un fichier template depuis le PC et le stocke en BLOB dans la base."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Importer le fichier pour '{template['nom']}'",
            "",
            "Fichiers Excel (*.xlsx *.xlsm *.xls);;Fichiers Word (*.docx);;Tous les fichiers (*.*)"
        )

        if not file_path:
            return

        try:
            from domain.services.documents.template_service import upload_template

            success, message = upload_template(template['id'], file_path)

            if success:
                QMessageBox.information(self, "Succes", message)
                self.load_templates()
            else:
                QMessageBox.warning(self, "Erreur", message)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de l'import:\n{str(e)}"
            )

    def generate_template(self, template):
        """Génère un template individuel."""
        try:
            from domain.services.documents.template_service import generate_filled_template, open_template_file

            success, message, file_path = generate_filled_template(
                template_id=template['id'],
                operateur_nom=self.operateur_nom,
                operateur_prenom=self.operateur_prenom,
                auditeur_nom=self.auditeur_input.text().strip()
            )

            if success and file_path:
                # Ouvrir le fichier
                open_success, open_msg = open_template_file(file_path)
                if open_success:
                    self.template_generated.emit(file_path)
                    QMessageBox.information(
                        self,
                        "Succès",
                        f"Le document '{template['nom']}' a été généré et ouvert.\n\n"
                        f"Emplacement: {file_path}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Attention",
                        f"Le document a été généré mais n'a pas pu être ouvert:\n{open_msg}\n\n"
                        f"Emplacement: {file_path}"
                    )
            else:
                QMessageBox.warning(self, "Erreur", message)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la génération:\n{str(e)}"
            )

    def generate_selected_templates(self):
        """Génère tous les templates sélectionnés."""
        # Trouver les checkboxes cochées
        selected_ids = []
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 1)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    template_id = checkbox.property('template_id')
                    selected_ids.append(template_id)

        if not selected_ids:
            QMessageBox.information(
                self,
                "Aucune sélection",
                "Veuillez cocher au moins un document à générer."
            )
            return

        # Générer chaque template
        generated = []
        errors = []

        try:
            from domain.services.documents.template_service import generate_filled_template, open_template_file

            for template_id in selected_ids:
                template = next((t for t in self.templates_data if t['id'] == template_id), None)
                if template:
                    success, message, file_path = generate_filled_template(
                        template_id=template_id,
                        operateur_nom=self.operateur_nom,
                        operateur_prenom=self.operateur_prenom,
                        auditeur_nom=self.auditeur_input.text().strip()
                    )

                    if success and file_path:
                        open_template_file(file_path)
                        generated.append(template['nom'])
                    else:
                        errors.append(f"{template['nom']}: {message}")

            # Afficher le résultat
            if generated:
                msg = f"Documents générés et ouverts ({len(generated)}):\n"
                msg += "\n".join(f"  - {name}" for name in generated)

                if errors:
                    msg += f"\n\nErreurs ({len(errors)}):\n"
                    msg += "\n".join(f"  - {err}" for err in errors)

                QMessageBox.information(self, "Génération terminée", msg)
            else:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Aucun document n'a pu être généré:\n" + "\n".join(errors)
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la génération:\n{str(e)}"
            )


class TemplateSelectionDialog(QDialog):
    """
    Dialog simplifié pour sélectionner et générer des templates dans un contexte spécifique.
    Utilisé lors de l'ajout d'un opérateur, passage niveau 3, etc.
    """

    def __init__(
        self,
        contexte: str,
        operateur_nom: str = "",
        operateur_prenom: str = "",
        code_poste: str = None,
        parent=None
    ):
        """
        Args:
            contexte: 'NOUVEL_OPERATEUR', 'NIVEAU_3', ou 'POSTE'
            operateur_nom: Nom de l'opérateur
            operateur_prenom: Prénom de l'opérateur
            code_poste: Code du poste (pour contexte POSTE)
            parent: Widget parent
        """
        super().__init__(parent)
        self.contexte = contexte
        self.operateur_nom = operateur_nom
        self.operateur_prenom = operateur_prenom
        self.code_poste = code_poste
        self.templates = []

        self.setWindowTitle("Documents à générer")
        self.setMinimumWidth(500)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        self.init_ui()
        self.load_templates()

    def init_ui(self):
        """Initialise l'interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Titre
        contexte_titles = {
            'NOUVEL_OPERATEUR': "Documents pour le nouvel opérateur",
            'NIVEAU_3': "Documents pour le passage au niveau 3",
            'POSTE': f"Documents pour le poste {self.code_poste or ''}"
        }
        title = QLabel(contexte_titles.get(self.contexte, "Documents"))
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        layout.addWidget(title)

        # Info opérateur
        if self.operateur_nom or self.operateur_prenom:
            info = QLabel(f"Opérateur: {self.operateur_prenom} {self.operateur_nom}")
            info.setStyleSheet("color: #64748b;")
            layout.addWidget(info)

        # Séparateur
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e2e8f0;")
        layout.addWidget(line)

        # Liste des templates avec checkboxes
        self.checkboxes_layout = QVBoxLayout()
        layout.addLayout(self.checkboxes_layout)

        # Champ auditeur
        aud_layout = QHBoxLayout()
        aud_label = QLabel("Auditeur (optionnel):")
        aud_layout.addWidget(aud_label)
        self.auditeur_input = QLineEdit()
        self.auditeur_input.setPlaceholderText("Nom de l'auditeur")
        aud_layout.addWidget(self.auditeur_input)
        layout.addLayout(aud_layout)

        # Boutons
        buttons_layout = QHBoxLayout()

        btn_select_all = QPushButton("Tout sélectionner")
        btn_select_all.clicked.connect(self.select_all)
        buttons_layout.addWidget(btn_select_all)

        buttons_layout.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_generate = QPushButton("Générer et ouvrir")
        btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        btn_generate.clicked.connect(self.generate_selected)
        buttons_layout.addWidget(btn_generate)

        layout.addLayout(buttons_layout)

    def load_templates(self):
        """Charge les templates pour le contexte donné."""
        try:
            from domain.services.documents.template_service import (
                get_templates_by_contexte, get_templates_for_poste,
                check_templates_table_exists
            )

            if not check_templates_table_exists():
                return

            if self.contexte == 'POSTE' and self.code_poste:
                self.templates = get_templates_for_poste(self.code_poste)
            else:
                self.templates = get_templates_by_contexte(self.contexte)

            # Créer les checkboxes
            self.checkboxes = []
            for template in self.templates:
                checkbox = QCheckBox(template['nom'])
                if template.get('obligatoire'):
                    checkbox.setChecked(True)
                    checkbox.setStyleSheet("font-weight: bold; color: #1e293b;")
                else:
                    checkbox.setStyleSheet("color: #475569;")

                checkbox.setProperty('template_id', template['id'])
                self.checkboxes.append(checkbox)
                self.checkboxes_layout.addWidget(checkbox)

            if not self.templates:
                no_template = QLabel("Aucun document disponible pour ce contexte.")
                no_template.setStyleSheet("color: #64748b; font-style: italic;")
                self.checkboxes_layout.addWidget(no_template)

        except Exception as e:
            error_label = QLabel(f"Erreur: {str(e)}")
            error_label.setStyleSheet("color: #dc2626;")
            self.checkboxes_layout.addWidget(error_label)

    def select_all(self):
        """Sélectionne/désélectionne toutes les checkboxes."""
        all_checked = all(cb.isChecked() for cb in self.checkboxes)
        for cb in self.checkboxes:
            cb.setChecked(not all_checked)

    def generate_selected(self):
        """Génère les templates sélectionnés."""
        selected_ids = [
            cb.property('template_id')
            for cb in self.checkboxes
            if cb.isChecked()
        ]

        if not selected_ids:
            QMessageBox.information(
                self,
                "Aucune sélection",
                "Veuillez sélectionner au moins un document."
            )
            return

        try:
            from domain.services.documents.template_service import generate_filled_template, open_template_file

            generated = []
            for template_id in selected_ids:
                template = next((t for t in self.templates if t['id'] == template_id), None)
                if template:
                    success, message, file_path = generate_filled_template(
                        template_id=template_id,
                        operateur_nom=self.operateur_nom,
                        operateur_prenom=self.operateur_prenom,
                        auditeur_nom=self.auditeur_input.text().strip()
                    )

                    if success and file_path:
                        open_template_file(file_path)
                        generated.append(template['nom'])

            if generated:
                self.accept()
            else:
                QMessageBox.warning(self, "Erreur", "Aucun document n'a pu être généré.")

        except Exception as e:
            logger.exception(f"Erreur génération template: {e}")
            QMessageBox.critical(self, "Erreur", "Impossible de générer le document. Consultez les logs pour plus de détails.")


class ImportTemplateDialog(QDialog):
    """Dialog pour importer un nouveau template dans le catalogue."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer un nouveau template")
        self.setMinimumWidth(550)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self._file_path = None
        self.created_template_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Titre
        title = QLabel("Importer un nouveau template")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        layout.addWidget(title)

        # === Informations principales ===
        main_group = QGroupBox("Informations du document")
        main_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; color: #334155;
                border: 1px solid #e2e8f0; border-radius: 8px;
                margin-top: 10px; padding-top: 18px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; }
        """)
        form = QGridLayout(main_group)
        form.setVerticalSpacing(8)
        form.setHorizontalSpacing(10)

        input_style = """
            QLineEdit, QComboBox {
                padding: 8px 12px; border: 1px solid #cbd5e1;
                border-radius: 6px; background: white; font-size: 13px;
            }
        """

        # Nom
        form.addWidget(QLabel("Nom du document *:"), 0, 0)
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Ex: Fiche sécurité poste 506")
        self.nom_input.setStyleSheet(input_style)
        form.addWidget(self.nom_input, 0, 1, 1, 2)

        # Fichier
        form.addWidget(QLabel("Fichier *:"), 1, 0)
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        self.file_input.setPlaceholderText("Aucun fichier sélectionné")
        self.file_input.setStyleSheet(input_style)
        form.addWidget(self.file_input, 1, 1)

        btn_browse = QPushButton("Parcourir...")
        btn_browse.setStyleSheet("""
            QPushButton {
                background: #f3f4f6; color: #374151; padding: 8px 14px;
                border: 1px solid #d1d5db; border-radius: 6px; font-weight: 500;
            }
            QPushButton:hover { background: #e5e7eb; }
        """)
        btn_browse.clicked.connect(self._browse_file)
        form.addWidget(btn_browse, 1, 2)

        # Contexte
        form.addWidget(QLabel("Contexte *:"), 2, 0)
        self.contexte_combo = QComboBox()
        self.contexte_combo.addItem("Nouvel opérateur", "NOUVEL_OPERATEUR")
        self.contexte_combo.addItem("Niveau 3", "NIVEAU_3")
        self.contexte_combo.addItem("Par poste", "POSTE")
        self.contexte_combo.setStyleSheet(input_style)
        self.contexte_combo.currentIndexChanged.connect(self._on_contexte_changed)
        form.addWidget(self.contexte_combo, 2, 1, 1, 2)

        # Postes associés
        self.lbl_postes = QLabel("Postes associés:")
        form.addWidget(self.lbl_postes, 3, 0)
        self.postes_input = QLineEdit()
        self.postes_input.setPlaceholderText("Codes postes séparés par virgule (506, 507, 901...)")
        self.postes_input.setStyleSheet(input_style)
        form.addWidget(self.postes_input, 3, 1, 1, 2)

        # Obligatoire
        self.obligatoire_cb = QCheckBox("Document obligatoire")
        self.obligatoire_cb.setStyleSheet("color: #475569;")
        form.addWidget(self.obligatoire_cb, 4, 1)

        layout.addWidget(main_group)

        # === Règle d'impression (optionnel) ===
        rule_group = QGroupBox("Règle d'impression automatique (optionnel)")
        rule_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; color: #334155;
                border: 1px solid #e2e8f0; border-radius: 8px;
                margin-top: 10px; padding-top: 18px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; }
        """)
        rule_form = QGridLayout(rule_group)
        rule_form.setVerticalSpacing(8)

        rule_form.addWidget(QLabel("Événement déclencheur:"), 0, 0)
        self.event_combo = QComboBox()
        self.event_combo.addItem("Aucun (pas de règle)", "")
        self.event_combo.addItem("Nouvel opérateur créé", "personnel.created")
        self.event_combo.addItem("Passage au niveau 3", "polyvalence.niveau_3_reached")
        self.event_combo.addItem("Affectation à un poste", "polyvalence.created")
        self.event_combo.addItem("Niveau changé", "polyvalence.niveau_changed")
        self.event_combo.addItem("Évaluation terminée", "evaluation.completed")
        self.event_combo.addItem("Contrat créé", "contrat.created")
        self.event_combo.addItem("Renouvellement contrat", "contrat.renewed")
        self.event_combo.setStyleSheet(input_style)
        self.event_combo.currentIndexChanged.connect(self._on_event_changed)
        rule_form.addWidget(self.event_combo, 0, 1, 1, 2)

        self.lbl_mode = QLabel("Mode d'exécution:")
        rule_form.addWidget(self.lbl_mode, 1, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Proposé (demande confirmation)", "PROPOSED")
        self.mode_combo.addItem("Automatique (génère directement)", "AUTO")
        self.mode_combo.addItem("Silencieux (log uniquement)", "SILENT")
        self.mode_combo.setStyleSheet(input_style)
        rule_form.addWidget(self.mode_combo, 1, 1, 1, 2)

        self.lbl_condition = QLabel("Condition (JSON):")
        rule_form.addWidget(self.lbl_condition, 2, 0)
        self.condition_input = QLineEdit()
        self.condition_input.setPlaceholderText('Ex: {"niveau": 3} ou laisser vide')
        self.condition_input.setStyleSheet(input_style)
        rule_form.addWidget(self.condition_input, 2, 1, 1, 2)

        # Info helper
        info_label = QLabel(
            'Exemples: {"niveau": 3}, {"type_contrat": {"in": ["CDD","CDI"]}}, '
            '{"postes": ["506","507"]}'
        )
        info_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-style: italic;")
        info_label.setWordWrap(True)
        rule_form.addWidget(info_label, 3, 0, 1, 3)

        layout.addWidget(rule_group)

        # Affichage initial
        self._on_contexte_changed()
        self._on_event_changed()

        # === Boutons ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setStyleSheet("""
            QPushButton {
                padding: 10px 20px; border: 1px solid #d1d5db;
                border-radius: 6px; color: #475569; font-weight: 500;
            }
            QPushButton:hover { background: #f3f4f6; }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_import = QPushButton("Importer")
        btn_import.setStyleSheet("""
            QPushButton {
                background-color: #10b981; color: white; padding: 10px 24px;
                border-radius: 6px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_import.clicked.connect(self._do_import)
        btn_layout.addWidget(btn_import)

        layout.addLayout(btn_layout)

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner le fichier template", "",
            "Fichiers Excel (*.xlsx *.xlsm *.xls);;Fichiers Word (*.docx);;PDF (*.pdf);;Tous (*.*)"
        )
        if file_path:
            self._file_path = file_path
            self.file_input.setText(file_path)

    def _on_contexte_changed(self):
        is_poste = self.contexte_combo.currentData() == "POSTE"
        self.lbl_postes.setVisible(is_poste)
        self.postes_input.setVisible(is_poste)

    def _on_event_changed(self):
        has_event = bool(self.event_combo.currentData())
        self.lbl_mode.setVisible(has_event)
        self.mode_combo.setVisible(has_event)
        self.lbl_condition.setVisible(has_event)
        self.condition_input.setVisible(has_event)

        # Auto-remplir le contexte selon l'événement
        event_to_contexte = {
            'personnel.created': 'NOUVEL_OPERATEUR',
            'polyvalence.niveau_3_reached': 'NIVEAU_3',
            'polyvalence.created': 'POSTE',
            'polyvalence.niveau_changed': 'POSTE',
            'evaluation.completed': 'POSTE',
            'contrat.created': 'NOUVEL_OPERATEUR',
            'contrat.renewed': 'NOUVEL_OPERATEUR',
        }
        event_name = self.event_combo.currentData()
        if event_name and event_name in event_to_contexte:
            target_contexte = event_to_contexte[event_name]
            idx = self.contexte_combo.findData(target_contexte)
            if idx >= 0:
                self.contexte_combo.setCurrentIndex(idx)

    def _do_import(self):
        """Valide et importe le template."""
        # Validation
        nom = self.nom_input.text().strip()
        if not nom:
            QMessageBox.warning(self, "Champ requis", "Le nom du document est obligatoire.")
            return

        if not self._file_path:
            QMessageBox.warning(self, "Champ requis", "Veuillez sélectionner un fichier.")
            return

        contexte = self.contexte_combo.currentData()

        # Postes
        postes = None
        if contexte == "POSTE":
            postes_text = self.postes_input.text().strip()
            if postes_text:
                postes = [p.strip() for p in postes_text.split(",") if p.strip()]

        # Condition JSON
        condition_json = None
        condition_text = self.condition_input.text().strip()
        if condition_text:
            try:
                import json
                condition_json = json.loads(condition_text)
            except json.JSONDecodeError:
                QMessageBox.warning(
                    self, "Format invalide",
                    "La condition JSON est mal formatée.\n"
                    "Exemple valide: {\"niveau\": 3}"
                )
                return

        try:
            from domain.services.documents.template_service import add_template

            success, message, template_id = add_template(
                nom=nom,
                fichier_source=self._file_path,
                contexte=contexte,
                postes_associes=postes,
                champ_operateur=None,
                champ_auditeur=None,
                champ_date=None,
                obligatoire=self.obligatoire_cb.isChecked(),
                description=f"Importé manuellement"
            )

            if not success:
                QMessageBox.warning(self, "Erreur", message)
                return

            self.created_template_id = template_id

            # Créer la règle d'impression si un événement est sélectionné
            event_name = self.event_combo.currentData()
            if event_name and template_id:
                from core.services.event_rule_service import create_rule

                rule_success, rule_msg, rule_id = create_rule(
                    event_name=event_name,
                    template_id=template_id,
                    execution_mode=self.mode_combo.currentData(),
                    condition_json=condition_json,
                    description=f"Règle pour '{nom}'"
                )

                if rule_success:
                    QMessageBox.information(
                        self, "Succès",
                        f"Template '{nom}' importé avec succès.\n"
                        f"Règle d'impression créée: {event_name} → {self.mode_combo.currentData()}"
                    )
                else:
                    QMessageBox.warning(
                        self, "Import partiel",
                        f"Template importé, mais la règle n'a pas pu être créée:\n{rule_msg}"
                    )
            else:
                QMessageBox.information(self, "Succès", f"Template '{nom}' importé avec succès.")

            self.accept()

        except Exception as e:
            logger.exception(f"Erreur import template: {e}")
            QMessageBox.critical(self, "Erreur", "Impossible d'importer le template. Consultez les logs pour plus de détails.")
