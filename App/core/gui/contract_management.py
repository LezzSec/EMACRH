"""
Interface de gestion des contrats
Permet de visualiser, ajouter, modifier et supprimer les contrats
"""

import sys
from datetime import datetime, date
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QHeaderView, QComboBox, QWidget,
    QDateEdit, QLineEdit, QDoubleSpinBox, QTextEdit, QFormLayout, QGroupBox,
    QScrollArea, QTabWidget, QFileDialog, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont

from core.services.contrat_service import (
    get_all_active_contracts, get_expiring_contracts, delete_contract,
    create_contract, update_contract, get_contract_by_id, get_contract_types,
    get_categories
)
from core.db.configbd import get_connection as get_db_connection

# Nouvelle interface RH (widget embeddable)
from core.gui.gestion_rh import GestionRHWidget

# Import du service documentaire pour les documents contractuels
try:
    from core.services.document_service import DocumentService
    DOCUMENTS_AVAILABLE = True
except ImportError:
    DOCUMENTS_AVAILABLE = False

try:
    from core.gui.ui_theme import EmacCard, EmacButton, EmacStatusCard
    from core.gui.emac_ui_kit import add_custom_title_bar
    THEME_AVAILABLE = True
    print(f"[CONTRACT_MANAGEMENT] THEME_AVAILABLE = {THEME_AVAILABLE}")
except ImportError as e:
    THEME_AVAILABLE = False
    print(f"[CONTRACT_MANAGEMENT] THEME_AVAILABLE = False, erreur: {e}")


class ContractFormDialog(QDialog):
    """Formulaire pour créer/modifier un contrat."""

    def __init__(self, parent=None, operateur_id=None, contract_id=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.contract_id = contract_id
        self.is_edit_mode = contract_id is not None

        self.setWindowTitle("Modifier le contrat" if self.is_edit_mode else "Nouveau contrat")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        self.init_ui()
        if self.is_edit_mode:
            self.load_contract_data()
        elif self.operateur_id:
            self.load_operator_info()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Scroll area pour le formulaire
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Informations opérateur
        if not self.is_edit_mode:
            info_group = QGroupBox("Opérateur")
            info_layout = QFormLayout()

            self.operator_combo = QComboBox()
            self.load_operators()
            if self.operateur_id:
                # Sélectionner l'opérateur
                for i in range(self.operator_combo.count()):
                    if self.operator_combo.itemData(i) == self.operateur_id:
                        self.operator_combo.setCurrentIndex(i)
                        break

            info_layout.addRow("Opérateur :", self.operator_combo)
            info_group.setLayout(info_layout)
            scroll_layout.addWidget(info_group)

        # Informations générales du contrat
        general_group = QGroupBox("Informations générales")
        general_layout = QFormLayout()

        self.type_combo = QComboBox()
        for contract_type in get_contract_types():
            self.type_combo.addItem(contract_type)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        general_layout.addRow("Type de contrat * :", self.type_combo)

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        general_layout.addRow("Date de début * :", self.date_debut)

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate().addYears(1))
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setSpecialValueText("Indéterminée (CDI)")
        self.date_fin.setMinimumDate(QDate(1900, 1, 1))
        general_layout.addRow("Date de fin :", self.date_fin)

        self.etp_spin = QDoubleSpinBox()
        self.etp_spin.setRange(0.01, 1.0)
        self.etp_spin.setValue(1.0)
        self.etp_spin.setSingleStep(0.1)
        self.etp_spin.setDecimals(2)
        general_layout.addRow("ETP :", self.etp_spin)

        general_group.setLayout(general_layout)
        scroll_layout.addWidget(general_group)

        # Classification
        classification_group = QGroupBox("Classification")
        classification_layout = QFormLayout()

        self.categorie_combo = QComboBox()
        self.categorie_combo.addItem("-- Non spécifiée --", None)
        for cat in get_categories():
            self.categorie_combo.addItem(cat, cat)
        classification_layout.addRow("Catégorie :", self.categorie_combo)

        self.echelon_input = QLineEdit()
        self.echelon_input.setPlaceholderText("Ex: Niveau II, Échelon 3")
        classification_layout.addRow("Échelon :", self.echelon_input)

        self.emploi_input = QLineEdit()
        self.emploi_input.setPlaceholderText("Ex: Technicien de maintenance")
        classification_layout.addRow("Emploi :", self.emploi_input)

        self.salaire_spin = QDoubleSpinBox()
        self.salaire_spin.setRange(0, 999999.99)
        self.salaire_spin.setSuffix(" €")
        self.salaire_spin.setDecimals(2)
        classification_layout.addRow("Salaire brut :", self.salaire_spin)

        classification_group.setLayout(classification_layout)
        scroll_layout.addWidget(classification_group)

        # Champs conditionnels selon le type de contrat
        self.apprentice_group = QGroupBox("Informations Apprenti/Stagiaire")
        apprentice_layout = QFormLayout()

        self.nom_tuteur_input = QLineEdit()
        apprentice_layout.addRow("Nom du tuteur :", self.nom_tuteur_input)

        self.prenom_tuteur_input = QLineEdit()
        apprentice_layout.addRow("Prénom du tuteur :", self.prenom_tuteur_input)

        self.ecole_input = QLineEdit()
        apprentice_layout.addRow("École :", self.ecole_input)

        self.apprentice_group.setLayout(apprentice_layout)
        self.apprentice_group.setVisible(False)
        scroll_layout.addWidget(self.apprentice_group)

        # Intérimaire
        self.interim_group = QGroupBox("Informations ETT (Intérimaire)")
        interim_layout = QFormLayout()

        self.nom_ett_input = QLineEdit()
        interim_layout.addRow("Nom de l'ETT :", self.nom_ett_input)

        self.adresse_ett_input = QTextEdit()
        self.adresse_ett_input.setMaximumHeight(60)
        interim_layout.addRow("Adresse de l'ETT :", self.adresse_ett_input)

        self.interim_group.setLayout(interim_layout)
        self.interim_group.setVisible(False)
        scroll_layout.addWidget(self.interim_group)

        # Mise à disposition GE
        self.ge_group = QGroupBox("Informations GE (Mise à disposition)")
        ge_layout = QFormLayout()

        self.nom_ge_input = QLineEdit()
        ge_layout.addRow("Nom du GE :", self.nom_ge_input)

        self.adresse_ge_input = QTextEdit()
        self.adresse_ge_input.setMaximumHeight(60)
        ge_layout.addRow("Adresse du GE :", self.adresse_ge_input)

        self.ge_group.setLayout(ge_layout)
        self.ge_group.setVisible(False)
        scroll_layout.addWidget(self.ge_group)

        # Étranger hors UE
        self.foreign_group = QGroupBox("Autorisation de travail (Étranger hors UE)")
        foreign_layout = QFormLayout()

        self.type_titre_input = QLineEdit()
        self.type_titre_input.setPlaceholderText("Ex: Carte de séjour, Visa")
        foreign_layout.addRow("Type de titre :", self.type_titre_input)

        self.numero_autorisation_input = QLineEdit()
        foreign_layout.addRow("Numéro d'autorisation :", self.numero_autorisation_input)

        self.date_demande = QDateEdit()
        self.date_demande.setCalendarPopup(True)
        self.date_demande.setDisplayFormat("dd/MM/yyyy")
        self.date_demande.setSpecialValueText("Non renseignée")
        foreign_layout.addRow("Date de demande :", self.date_demande)

        self.date_autorisation = QDateEdit()
        self.date_autorisation.setCalendarPopup(True)
        self.date_autorisation.setDisplayFormat("dd/MM/yyyy")
        self.date_autorisation.setSpecialValueText("Non renseignée")
        foreign_layout.addRow("Date d'autorisation :", self.date_autorisation)

        self.date_limite_autorisation = QDateEdit()
        self.date_limite_autorisation.setCalendarPopup(True)
        self.date_limite_autorisation.setDisplayFormat("dd/MM/yyyy")
        self.date_limite_autorisation.setSpecialValueText("Non renseignée")
        foreign_layout.addRow("Date limite :", self.date_limite_autorisation)

        self.foreign_group.setLayout(foreign_layout)
        self.foreign_group.setVisible(False)
        scroll_layout.addWidget(self.foreign_group)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Boutons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        if THEME_AVAILABLE:
            save_btn = EmacButton("Enregistrer", 'primary')
            cancel_btn = EmacButton("Annuler", 'ghost')
        else:
            save_btn = QPushButton("Enregistrer")
            cancel_btn = QPushButton("Annuler")

        save_btn.clicked.connect(self.save_contract)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def on_type_changed(self, contract_type):
        """Affiche/masque les champs conditionnels selon le type."""
        is_apprentice = contract_type in ['Stagiaire', 'Apprentissage']
        is_interim = contract_type == 'Intérimaire'
        is_ge = contract_type == 'Mise à disposition GE'
        is_foreign = contract_type == 'Etranger hors UE'

        self.apprentice_group.setVisible(is_apprentice)
        self.interim_group.setVisible(is_interim)
        self.ge_group.setVisible(is_ge)
        self.foreign_group.setVisible(is_foreign)

        # Ajuster date de fin selon CDI/CDD
        if contract_type == 'CDI':
            self.date_fin.setDate(QDate(1900, 1, 1))  # Valeur spéciale pour "indéterminée"

    def load_operators(self):
        """Charge la liste des opérateurs actifs."""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT id, nom, prenom, matricule
                FROM personnel
                WHERE statut = 'ACTIF'
                ORDER BY nom, prenom
            """)

            for row in cursor.fetchall():
                operator_id, nom, prenom, matricule = row
                display = f"{nom} {prenom} ({matricule})"
                self.operator_combo.addItem(display, operator_id)

            cursor.close()
            connection.close()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les opérateurs : {e}")

    def load_operator_info(self):
        """Charge les infos de l'opérateur sélectionné."""
        # Optionnel : afficher des infos supplémentaires
        pass

    def load_contract_data(self):
        """Charge les données du contrat à modifier."""
        contract = get_contract_by_id(self.contract_id)
        if not contract:
            QMessageBox.critical(self, "Erreur", "Contrat introuvable")
            self.reject()
            return

        # Type de contrat
        type_index = self.type_combo.findText(contract['type_contrat'])
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)

        # Dates
        if contract['date_debut']:
            qdate = QDate(contract['date_debut'].year, contract['date_debut'].month, contract['date_debut'].day)
            self.date_debut.setDate(qdate)

        if contract['date_fin']:
            qdate = QDate(contract['date_fin'].year, contract['date_fin'].month, contract['date_fin'].day)
            self.date_fin.setDate(qdate)
        else:
            self.date_fin.setDate(QDate(1900, 1, 1))

        # ETP
        if contract.get('etp'):
            self.etp_spin.setValue(float(contract['etp']))

        # Classification
        if contract.get('categorie'):
            cat_index = self.categorie_combo.findData(contract['categorie'])
            if cat_index >= 0:
                self.categorie_combo.setCurrentIndex(cat_index)

        if contract.get('echelon'):
            self.echelon_input.setText(contract['echelon'])

        if contract.get('emploi'):
            self.emploi_input.setText(contract['emploi'])

        if contract.get('salaire'):
            self.salaire_spin.setValue(float(contract['salaire']))

        # Champs conditionnels
        if contract.get('nom_tuteur'):
            self.nom_tuteur_input.setText(contract['nom_tuteur'])
        if contract.get('prenom_tuteur'):
            self.prenom_tuteur_input.setText(contract['prenom_tuteur'])
        if contract.get('ecole'):
            self.ecole_input.setText(contract['ecole'])

        if contract.get('nom_ett'):
            self.nom_ett_input.setText(contract['nom_ett'])
        if contract.get('adresse_ett'):
            self.adresse_ett_input.setText(contract['adresse_ett'])

        if contract.get('nom_ge'):
            self.nom_ge_input.setText(contract['nom_ge'])
        if contract.get('adresse_ge'):
            self.adresse_ge_input.setText(contract['adresse_ge'])

        if contract.get('type_titre_autorisation'):
            self.type_titre_input.setText(contract['type_titre_autorisation'])
        if contract.get('numero_autorisation_travail'):
            self.numero_autorisation_input.setText(contract['numero_autorisation_travail'])

    def save_contract(self):
        """Enregistre le contrat."""
        data = self.collect_data()
        if not data:
            return

        if self.is_edit_mode:
            success, message = update_contract(self.contract_id, data)
        else:
            success, message, contract_id = create_contract(data)

        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", message)

    def collect_data(self) -> dict:
        """Collecte les données du formulaire."""
        # Opérateur
        if self.is_edit_mode:
            contract = get_contract_by_id(self.contract_id)
            operateur_id = contract['operateur_id']
        else:
            operateur_id = self.operator_combo.currentData()
            if not operateur_id:
                QMessageBox.warning(self, "Attention", "Veuillez sélectionner un opérateur")
                return None

        # Dates
        date_debut = self.date_debut.date().toPyDate()

        date_fin_qdate = self.date_fin.date()
        if date_fin_qdate.year() == 1900:  # Indéterminée
            date_fin = None
        else:
            date_fin = date_fin_qdate.toPyDate()

        # Type
        type_contrat = self.type_combo.currentText()

        # Catégorie
        categorie = self.categorie_combo.currentData()

        data = {
            'operateur_id': operateur_id,
            'type_contrat': type_contrat,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'etp': self.etp_spin.value(),
            'categorie': categorie,
            'echelon': self.echelon_input.text().strip() or None,
            'emploi': self.emploi_input.text().strip() or None,
            'salaire': self.salaire_spin.value() if self.salaire_spin.value() > 0 else None,
            'actif': 1,
        }

        # Champs conditionnels
        if self.apprentice_group.isVisible():
            data['nom_tuteur'] = self.nom_tuteur_input.text().strip() or None
            data['prenom_tuteur'] = self.prenom_tuteur_input.text().strip() or None
            data['ecole'] = self.ecole_input.text().strip() or None

        if self.interim_group.isVisible():
            data['nom_ett'] = self.nom_ett_input.text().strip() or None
            data['adresse_ett'] = self.adresse_ett_input.toPlainText().strip() or None

        if self.ge_group.isVisible():
            data['nom_ge'] = self.nom_ge_input.text().strip() or None
            data['adresse_ge'] = self.adresse_ge_input.toPlainText().strip() or None

        if self.foreign_group.isVisible():
            data['type_titre_autorisation'] = self.type_titre_input.text().strip() or None
            data['numero_autorisation_travail'] = self.numero_autorisation_input.text().strip() or None

            # Dates autorisation
            date_demande_q = self.date_demande.date()
            data['date_demande_autorisation'] = date_demande_q.toPyDate() if date_demande_q.year() != 1900 else None

            date_auto_q = self.date_autorisation.date()
            data['date_autorisation_travail'] = date_auto_q.toPyDate() if date_auto_q.year() != 1900 else None

            date_limite_q = self.date_limite_autorisation.date()
            data['date_limite_autorisation'] = date_limite_q.toPyDate() if date_limite_q.year() != 1900 else None

        return data


class ContractManagementDialog(QDialog):
    """Dialogue de gestion RH - Contrats et Documents."""

    def __init__(self, parent=None, operateur_id=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion RH")
        self.setGeometry(150, 150, 1200, 700)
        self._operateur_id = operateur_id

        self.init_ui()

    def init_ui(self):
        """UI unique : affiche uniquement la nouvelle Gestion RH (GestionRHWidget).

        Remarque : le code legacy (onglets Contrats/Documents) est conservé dans init_ui_legacy()
        pour référence, mais n'est plus utilisé.
        """
        # Layout principal avec marges nulles
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        if THEME_AVAILABLE:
            title_bar = add_custom_title_bar(self, 'Gestion RH')
            main_layout.addWidget(title_bar)

        # Contenu : uniquement la nouvelle Gestion RH
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.gestion_rh_widget = GestionRHWidget(self, operateur_id=self._operateur_id)
        content_layout.addWidget(self.gestion_rh_widget, 1)

        main_layout.addWidget(content_widget, 1)


    def init_ui_legacy(self):
        # Layout principal avec marges nulles
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        if THEME_AVAILABLE:
            title_bar = add_custom_title_bar(self, "Gestion RH")
            main_layout.addWidget(title_bar)

        # Widget de contenu avec onglets
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        # Créer les onglets
        self.tabs = QTabWidget()

        # Onglet 1: Liste des contrats
        contracts_tab = QWidget()
        layout = QVBoxLayout(contracts_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # === KPI Cards modernes et centrées ===
        if THEME_AVAILABLE:
            kpi_layout = QHBoxLayout()
            kpi_layout.setSpacing(15)
            kpi_layout.addStretch()  # Ajouter stretch à gauche pour centrer

            # Card 1: Total contrats (bleu plus foncé)
            self.total_card = self._create_kpi_card(
                "📋", "Contrats Actifs", "0", "Total en cours",
                "#2563eb", "#dbeafe"
            )
            kpi_layout.addWidget(self.total_card)

            # Card 2: À renouveler (orange plus foncé)
            self.expiring_card = self._create_kpi_card(
                "⏰", "À Renouveler", "0", "Dans les 30 jours",
                "#d97706", "#fed7aa"
            )
            kpi_layout.addWidget(self.expiring_card)

            # Card 3: Expirés (rouge plus foncé)
            self.expired_card = self._create_kpi_card(
                "⚠️", "Expirés", "0", "Contrats terminés",
                "#b91c1c", "#fecaca"
            )
            kpi_layout.addWidget(self.expired_card)

            kpi_layout.addStretch()  # Ajouter stretch à droite pour centrer

            layout.addLayout(kpi_layout)
        else:
            # Fallback pour version sans thème
            stats_layout = QHBoxLayout()
            self.total_label = QLabel("Total : 0")
            self.expiring_label = QLabel("À renouveler (30j) : 0")
            self.expiring_label.setStyleSheet("color: orange; font-weight: bold;")
            stats_layout.addWidget(self.total_label)
            stats_layout.addWidget(self.expiring_label)
            stats_layout.addStretch()
            layout.addLayout(stats_layout)

        # Filtres
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Filtrer par type :"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("Tous les types", None)
        for contract_type in get_contract_types():
            self.type_filter.addItem(contract_type, contract_type)
        self.type_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.type_filter)

        filter_layout.addStretch()

        if THEME_AVAILABLE:
            add_btn = EmacButton("+ Nouveau contrat", 'primary')
            refresh_btn = EmacButton("🔄 Actualiser", 'ghost')
        else:
            add_btn = QPushButton("+ Nouveau contrat")
            refresh_btn = QPushButton("🔄 Actualiser")

        add_btn.clicked.connect(self.add_contract)
        refresh_btn.clicked.connect(self.load_data)

        filter_layout.addWidget(add_btn)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # === Table moderne avec EmacCard ===
        if THEME_AVAILABLE:
            table_card = EmacCard()
            table_layout = QVBoxLayout()

            self.table = QTableWidget()
            self.table.setColumnCount(11)
            self.table.setHorizontalHeaderLabels([
                "ID", "Opérateur", "Matricule", "Type", "Début", "Fin",
                "ETP", "Catégorie", "Emploi", "Jours restants", "📄 Docs"
            ])

            header = self.table.horizontalHeader()
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            header.setSectionResizeMode(8, QHeaderView.Stretch)

            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.table.doubleClicked.connect(self.edit_contract)
            self.table.setAlternatingRowColors(True)

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

            table_layout.addWidget(self.table)
            table_card.body.addLayout(table_layout)
            layout.addWidget(table_card)
        else:
            # Fallback sans carte
            self.table = QTableWidget()
            self.table.setColumnCount(11)
            self.table.setHorizontalHeaderLabels([
                "ID", "Opérateur", "Matricule", "Type", "Début", "Fin",
                "ETP", "Catégorie", "Emploi", "Jours restants", "📄 Docs"
            ])

            header = self.table.horizontalHeader()
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            header.setSectionResizeMode(8, QHeaderView.Stretch)

            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.table.doubleClicked.connect(self.edit_contract)

            layout.addWidget(self.table)

        # Boutons d'action
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        if THEME_AVAILABLE:
            edit_btn = EmacButton("✏️  Modifier", 'ghost')
            delete_btn = EmacButton("🗑️ Désactiver", 'ghost')
            close_btn = EmacButton("Fermer", 'ghost')
        else:
            edit_btn = QPushButton("✏️ Modifier")
            delete_btn = QPushButton("🗑️ Désactiver")
            close_btn = QPushButton("Fermer")

        edit_btn.clicked.connect(self.edit_contract)
        delete_btn.clicked.connect(self.delete_contract)
        close_btn.clicked.connect(self.accept)

        action_layout.addWidget(edit_btn)
        action_layout.addWidget(delete_btn)
        action_layout.addWidget(close_btn)

        layout.addLayout(action_layout)

        # Ajouter l'onglet Contrats
        self.tabs.addTab(contracts_tab, "📋 Contrats")

        # Onglet 2: Documents contractuels
        if DOCUMENTS_AVAILABLE:
            documents_tab = self.create_documents_tab()
            self.tabs.addTab(documents_tab, "📄 Documents")

        # Ajouter les onglets au layout de contenu
        content_layout.addWidget(self.tabs)

        # Ajouter le widget de contenu au layout principal
        main_layout.addWidget(content_widget)

    def load_data(self):
        """Charge les contrats actifs."""
        contracts = get_all_active_contracts()

        # Filtrer par type si nécessaire
        selected_type = self.type_filter.currentData()
        if selected_type:
            contracts = [c for c in contracts if c['type_contrat'] == selected_type]

        self.table.setRowCount(0)

        for contract in contracts:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID (caché)
            self.table.setItem(row, 0, QTableWidgetItem(str(contract['id'])))

            # Opérateur
            nom_complet = f"{contract['nom']} {contract['prenom']}"
            self.table.setItem(row, 1, QTableWidgetItem(nom_complet))

            # Matricule
            matricule = contract.get('matricule', '')
            self.table.setItem(row, 2, QTableWidgetItem(matricule or ''))

            # Type
            self.table.setItem(row, 3, QTableWidgetItem(contract['type_contrat']))

            # Date début
            date_debut_str = contract['date_debut'].strftime('%d/%m/%Y') if contract['date_debut'] else ''
            self.table.setItem(row, 4, QTableWidgetItem(date_debut_str))

            # Date fin
            date_fin_str = contract['date_fin'].strftime('%d/%m/%Y') if contract['date_fin'] else 'Indéterminée'
            date_fin_item = QTableWidgetItem(date_fin_str)

            # Coloration si proche de l'expiration
            if contract['date_fin']:
                days_remaining = (contract['date_fin'] - date.today()).days
                if days_remaining < 0:
                    date_fin_item.setBackground(QColor(220, 38, 38, 50))  # Rouge
                    date_fin_item.setForeground(QColor(220, 38, 38))
                elif days_remaining <= 30:
                    date_fin_item.setBackground(QColor(217, 119, 6, 50))  # Orange
                    date_fin_item.setForeground(QColor(217, 119, 6))

            self.table.setItem(row, 5, date_fin_item)

            # ETP
            etp_str = str(contract.get('etp', '1.0'))
            self.table.setItem(row, 6, QTableWidgetItem(etp_str))

            # Catégorie
            categorie = contract.get('categorie', '')
            self.table.setItem(row, 7, QTableWidgetItem(categorie or ''))

            # Emploi
            emploi = contract.get('emploi', '')
            self.table.setItem(row, 8, QTableWidgetItem(emploi or ''))

            # Jours restants
            if contract['date_fin']:
                days_remaining = (contract['date_fin'] - date.today()).days
                days_item = QTableWidgetItem(str(days_remaining))
                days_item.setTextAlignment(Qt.AlignCenter)

                if days_remaining < 0:
                    days_item.setForeground(QColor(220, 38, 38))
                elif days_remaining <= 30:
                    days_item.setForeground(QColor(217, 119, 6))

                self.table.setItem(row, 9, days_item)
            else:
                self.table.setItem(row, 9, QTableWidgetItem('—'))

            # Nombre de documents
            doc_count = self.count_documents_for_operator(contract['operateur_id'])
            doc_item = QTableWidgetItem(str(doc_count))
            doc_item.setTextAlignment(Qt.AlignCenter)

            # Coloration selon le nombre de documents
            if doc_count == 0:
                doc_item.setForeground(QColor(156, 163, 175))  # Gris
            else:
                doc_item.setForeground(QColor(16, 185, 129))  # Vert
                doc_item.setFont(QFont("Arial", 9, QFont.Bold))

            self.table.setItem(row, 10, doc_item)

        # Cacher colonne ID
        self.table.setColumnHidden(0, True)

        # Mettre à jour les statistiques
        self.update_statistics()

    def count_documents_for_operator(self, operateur_id):
        """Compte le nombre de documents contractuels pour un opérateur."""
        if not DOCUMENTS_AVAILABLE:
            return 0

        try:
            conn = get_db_connection()
            cur = conn.cursor(buffered=True)

            cur.execute("""
                SELECT COUNT(*) as count
                FROM documents d
                INNER JOIN categories_documents c ON d.categorie_id = c.id
                WHERE d.operateur_id = %s AND c.nom = 'Contrats de travail'
            """, (operateur_id,))

            result = cur.fetchone()
            cur.close()
            conn.close()

            return result[0] if result else 0

        except Exception:
            return 0

    def _create_kpi_card(self, icon, title, value, subtitle, color, bg_color):
        """Crée une KPI card SIMPLE - Rectangle plat avec nombre"""
        # Container simple
        container = QWidget()
        container.setFixedSize(220, 80)
        container.setStyleSheet(f"""
            QWidget {{
                background: {bg_color};
                border-radius: 8px;
            }}
        """)

        # Layout horizontal simple
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # Valeur à gauche
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 42, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)

        # Texte à droite
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet("color: #1e293b;")
        title_label.setWordWrap(True)
        text_layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setFont(QFont("Segoe UI", 9))
            subtitle_label.setStyleSheet("color: #64748b;")
            text_layout.addWidget(subtitle_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        # Stocker la référence
        container.value_label = value_label
        return container

    def update_statistics(self):
        """Met à jour les statistiques affichées."""
        total = self.table.rowCount()
        expiring = get_expiring_contracts(30)

        # Compter les contrats expirés
        expired_count = 0
        for row in range(self.table.rowCount()):
            jours_item = self.table.item(row, 9)
            if jours_item and jours_item.text().isdigit():
                jours = int(jours_item.text())
                if jours < 0:
                    expired_count += 1

        if THEME_AVAILABLE and hasattr(self, 'total_card'):
            self.total_card.value_label.setText(str(total))
            self.expiring_card.value_label.setText(str(len(expiring)))
            self.expired_card.value_label.setText(str(expired_count))
        else:
            # Fallback pour version sans thème
            if hasattr(self, 'total_label'):
                self.total_label.setText(f"Total : {total}")
                self.expiring_label.setText(f"À renouveler (30j) : {len(expiring)}")

    def add_contract(self):
        """Ouvre le formulaire pour ajouter un contrat."""
        dialog = ContractFormDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def edit_contract(self):
        """Modifie le contrat sélectionné."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un contrat")
            return

        contract_id = int(self.table.item(current_row, 0).text())
        dialog = ContractFormDialog(self, contract_id=contract_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def create_documents_tab(self):
        """Crée l'onglet pour tous les documents RH."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # === En-tête moderne ===
        if THEME_AVAILABLE:
            header_card = EmacCard()
            header_layout = QHBoxLayout()

            title = QLabel("📄 Documents RH")
            title.setFont(QFont("Segoe UI", 14, QFont.Bold))
            title.setStyleSheet("color: #1e293b;")
            header_layout.addWidget(title)

            header_layout.addStretch()

            add_doc_btn = EmacButton("➕ Ajouter", 'primary')
            refresh_doc_btn = EmacButton("🔄 Actualiser", 'ghost')

            add_doc_btn.clicked.connect(self.add_contract_document)
            refresh_doc_btn.clicked.connect(self.load_contract_documents)

            header_layout.addWidget(add_doc_btn)
            header_layout.addWidget(refresh_doc_btn)

            header_card.body.addLayout(header_layout)
            layout.addWidget(header_card)

            # === Filtres ===
            filter_card = EmacCard()
            filter_layout = QHBoxLayout()

            filter_layout.addWidget(QLabel("Catégorie:"))
            self.doc_categorie_filter = QComboBox()
            self.doc_categorie_filter.setMinimumWidth(200)
            self.doc_categorie_filter.currentIndexChanged.connect(self.load_contract_documents)
            filter_layout.addWidget(self.doc_categorie_filter)

            filter_layout.addSpacing(15)

            filter_layout.addWidget(QLabel("Employé:"))
            self.doc_employe_filter = QComboBox()
            self.doc_employe_filter.setMinimumWidth(200)
            self.doc_employe_filter.currentIndexChanged.connect(self.load_contract_documents)
            filter_layout.addWidget(self.doc_employe_filter)

            filter_layout.addStretch()
            filter_card.body.addLayout(filter_layout)
            layout.addWidget(filter_card)
        else:
            # Fallback simple
            header_layout = QHBoxLayout()
            header_layout.addWidget(QLabel("Documents RH"))
            header_layout.addStretch()

            add_doc_btn = QPushButton("+ Ajouter un document")
            refresh_doc_btn = QPushButton("🔄 Actualiser")

            add_doc_btn.clicked.connect(self.add_contract_document)
            refresh_doc_btn.clicked.connect(self.load_contract_documents)

            header_layout.addWidget(add_doc_btn)
            header_layout.addWidget(refresh_doc_btn)
            layout.addLayout(header_layout)

            # Filtres simples
            filter_layout = QHBoxLayout()
            filter_layout.addWidget(QLabel("Catégorie:"))
            self.doc_categorie_filter = QComboBox()
            self.doc_categorie_filter.currentIndexChanged.connect(self.load_contract_documents)
            filter_layout.addWidget(self.doc_categorie_filter)

            filter_layout.addWidget(QLabel("Employé:"))
            self.doc_employe_filter = QComboBox()
            self.doc_employe_filter.currentIndexChanged.connect(self.load_contract_documents)
            filter_layout.addWidget(self.doc_employe_filter)

            filter_layout.addStretch()
            layout.addLayout(filter_layout)

        # Charger les filtres
        self._load_document_filters()

        # === Table moderne avec EmacCard ===
        if THEME_AVAILABLE:
            table_card = EmacCard()
            table_layout = QVBoxLayout()

            self.docs_table = QTableWidget()
            self.docs_table.setColumnCount(8)
            self.docs_table.setHorizontalHeaderLabels([
                "ID", "Personnel", "Matricule", "Catégorie", "Nom du fichier",
                "Date d'ajout", "Date d'expiration", "Statut"
            ])

            header = self.docs_table.horizontalHeader()
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(4, QHeaderView.Stretch)

            self.docs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.docs_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.docs_table.doubleClicked.connect(self.open_document)
            self.docs_table.setAlternatingRowColors(True)

            # Style moderne EMAC
            self.docs_table.setStyleSheet("""
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

            table_layout.addWidget(self.docs_table)
            table_card.body.addLayout(table_layout)
            layout.addWidget(table_card)
        else:
            # Fallback sans carte
            self.docs_table = QTableWidget()
            self.docs_table.setColumnCount(8)
            self.docs_table.setHorizontalHeaderLabels([
                "ID", "Personnel", "Matricule", "Catégorie", "Nom du fichier",
                "Date d'ajout", "Date d'expiration", "Statut"
            ])

            header = self.docs_table.horizontalHeader()
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(4, QHeaderView.Stretch)

            self.docs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.docs_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.docs_table.doubleClicked.connect(self.open_document)

            layout.addWidget(self.docs_table)

        # Boutons d'action
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        if THEME_AVAILABLE:
            open_btn = EmacButton("📂 Ouvrir", 'ghost')
            delete_doc_btn = EmacButton("🗑️ Supprimer", 'ghost')
        else:
            open_btn = QPushButton("📂 Ouvrir")
            delete_doc_btn = QPushButton("🗑️ Supprimer")

        open_btn.clicked.connect(self.open_document)
        delete_doc_btn.clicked.connect(self.delete_document)

        action_layout.addWidget(open_btn)
        action_layout.addWidget(delete_doc_btn)
        layout.addLayout(action_layout)

        # Charger les documents
        self.load_contract_documents()

        return tab

    def _load_document_filters(self):
        """Charge les filtres pour les documents."""
        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True, buffered=True)

            # Charger les catégories
            self.doc_categorie_filter.blockSignals(True)
            self.doc_categorie_filter.clear()
            self.doc_categorie_filter.addItem("Toutes les catégories", None)

            cur.execute("SELECT id, nom FROM categories_documents ORDER BY ordre_affichage, nom")
            for cat in cur.fetchall():
                self.doc_categorie_filter.addItem(cat['nom'], cat['id'])
            self.doc_categorie_filter.blockSignals(False)

            # Charger les employés
            self.doc_employe_filter.blockSignals(True)
            self.doc_employe_filter.clear()
            self.doc_employe_filter.addItem("Tous les employés", None)

            cur.execute("""
                SELECT id, CONCAT(prenom, ' ', nom) as nom_complet, matricule
                FROM personnel WHERE statut = 'ACTIF' ORDER BY nom, prenom
            """)
            for emp in cur.fetchall():
                self.doc_employe_filter.addItem(f"{emp['nom_complet']} ({emp['matricule']})", emp['id'])
            self.doc_employe_filter.blockSignals(False)

            cur.close()
            conn.close()
        except Exception as e:
            print(f"Erreur chargement filtres documents: {e}")

    def load_contract_documents(self):
        """Charge tous les documents RH avec filtres."""
        if not DOCUMENTS_AVAILABLE:
            return

        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True, buffered=True)

            # Récupérer les filtres
            categorie_id = self.doc_categorie_filter.currentData() if hasattr(self, 'doc_categorie_filter') else None
            employe_id = self.doc_employe_filter.currentData() if hasattr(self, 'doc_employe_filter') else None

            # Construire la requête avec filtres
            query = """
                SELECT
                    d.id,
                    d.operateur_id,
                    p.nom,
                    p.prenom,
                    p.matricule,
                    c.nom as categorie,
                    d.nom_fichier,
                    d.date_upload,
                    d.date_expiration,
                    CASE
                        WHEN d.date_expiration IS NULL THEN 'Valide'
                        WHEN d.date_expiration < CURDATE() THEN 'Expiré'
                        WHEN d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 'Expire bientôt'
                        ELSE 'Valide'
                    END as statut
                FROM documents d
                INNER JOIN personnel p ON d.operateur_id = p.id
                INNER JOIN categories_documents c ON d.categorie_id = c.id
                WHERE 1=1
            """
            params = []

            if categorie_id:
                query += " AND d.categorie_id = %s"
                params.append(categorie_id)

            if employe_id:
                query += " AND d.operateur_id = %s"
                params.append(employe_id)

            query += " ORDER BY d.date_upload DESC"

            cur.execute(query, tuple(params))

            documents = cur.fetchall()
            cur.close()
            conn.close()

            self.docs_table.setRowCount(0)

            for doc in documents:
                row = self.docs_table.rowCount()
                self.docs_table.insertRow(row)

                # ID (caché)
                self.docs_table.setItem(row, 0, QTableWidgetItem(str(doc['id'])))

                # Personnel
                nom_complet = f"{doc['nom']} {doc['prenom']}"
                self.docs_table.setItem(row, 1, QTableWidgetItem(nom_complet))

                # Matricule
                self.docs_table.setItem(row, 2, QTableWidgetItem(doc['matricule'] or ''))

                # Catégorie
                self.docs_table.setItem(row, 3, QTableWidgetItem(doc['categorie']))

                # Nom du fichier
                self.docs_table.setItem(row, 4, QTableWidgetItem(doc['nom_fichier']))

                # Date d'ajout
                date_upload_str = doc['date_upload'].strftime('%d/%m/%Y') if doc['date_upload'] else ''
                self.docs_table.setItem(row, 5, QTableWidgetItem(date_upload_str))

                # Date d'expiration
                date_exp_str = doc['date_expiration'].strftime('%d/%m/%Y') if doc['date_expiration'] else 'N/A'
                date_exp_item = QTableWidgetItem(date_exp_str)

                # Coloration selon le statut
                statut = doc['statut']
                if statut == 'Expiré':
                    date_exp_item.setBackground(QColor(220, 38, 38, 50))
                    date_exp_item.setForeground(QColor(220, 38, 38))
                elif statut == 'Expire bientôt':
                    date_exp_item.setBackground(QColor(217, 119, 6, 50))
                    date_exp_item.setForeground(QColor(217, 119, 6))

                self.docs_table.setItem(row, 6, date_exp_item)

                # Statut
                statut_item = QTableWidgetItem(statut)
                if statut == 'Expiré':
                    statut_item.setForeground(QColor(220, 38, 38))
                elif statut == 'Expire bientôt':
                    statut_item.setForeground(QColor(217, 119, 6))
                else:
                    statut_item.setForeground(QColor(16, 185, 129))

                self.docs_table.setItem(row, 7, statut_item)

            # Cacher colonne ID
            self.docs_table.setColumnHidden(0, True)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des documents : {e}")

    def add_contract_document(self):
        """Ouvre la fenêtre pour ajouter un document RH."""
        try:
            from core.gui.gestion_documentaire import AddDocumentDialog

            # Ouvrir la fenêtre d'ajout de document (sans filtre de catégorie)
            dialog = AddDocumentDialog(operateur_id=None, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_contract_documents()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du formulaire : {e}")

    def open_document(self):
        """Ouvre le document sélectionné."""
        current_row = self.docs_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un document")
            return

        doc_id = int(self.docs_table.item(current_row, 0).text())

        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True, buffered=True)
            cur.execute("SELECT chemin_fichier FROM documents WHERE id = %s", (doc_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()

            if result and result['chemin_fichier']:
                import os
                import subprocess
                file_path = result['chemin_fichier']

                if os.path.exists(file_path):
                    # Ouvrir avec l'application par défaut
                    if sys.platform == 'win32':
                        os.startfile(file_path)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', file_path])
                    else:
                        subprocess.run(['xdg-open', file_path])
                else:
                    QMessageBox.warning(self, "Erreur", f"Le fichier n'existe pas : {file_path}")
            else:
                QMessageBox.warning(self, "Erreur", "Chemin du fichier non trouvé")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du document : {e}")

    def delete_document(self):
        """Supprime le document sélectionné."""
        current_row = self.docs_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un document")
            return

        doc_id = int(self.docs_table.item(current_row, 0).text())
        doc_name = self.docs_table.item(current_row, 4).text()

        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer le document '{doc_name}' ?\n\nCette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cur = conn.cursor(dictionary=True, buffered=True)

                # Récupérer le chemin du fichier
                cur.execute("SELECT chemin_fichier FROM documents WHERE id = %s", (doc_id,))
                result = cur.fetchone()

                if result and result['chemin_fichier']:
                    import os
                    file_path = result['chemin_fichier']

                    # Supprimer le fichier physique
                    if os.path.exists(file_path):
                        os.remove(file_path)

                # Supprimer l'entrée en base
                cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
                conn.commit()
                cur.close()
                conn.close()

                QMessageBox.information(self, "Succès", "Document supprimé avec succès")
                self.load_contract_documents()

            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression : {e}")

    def delete_contract(self):
        """Désactive le contrat sélectionné."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un contrat")
            return

        contract_id = int(self.table.item(current_row, 0).text())
        operator_name = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment désactiver le contrat de {operator_name} ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, message = delete_contract(contract_id)
            if success:
                QMessageBox.information(self, "Succès", message)
                self.load_data()
            else:
                QMessageBox.critical(self, "Erreur", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = ContractManagementDialog()
    dialog.show()
    sys.exit(app.exec_())
