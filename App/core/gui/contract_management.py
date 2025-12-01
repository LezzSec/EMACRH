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
    QScrollArea
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor

from core.services.contrat_service import (
    get_all_active_contracts, get_expiring_contracts, delete_contract,
    create_contract, update_contract, get_contract_by_id, get_contract_types,
    get_categories
)
from core.db.configbd import get_connection as get_db_connection

try:
    from core.gui.ui_theme import EmacCard, EmacButton
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False


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
    """Dialogue de gestion des contrats."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Contrats")
        self.setGeometry(150, 150, 1200, 700)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # En-tête avec statistiques
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

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Opérateur", "Matricule", "Type", "Début", "Fin",
            "ETP", "Catégorie", "Emploi", "Jours restants"
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

        # Cacher colonne ID
        self.table.setColumnHidden(0, True)

        # Mettre à jour les statistiques
        self.update_statistics()

    def update_statistics(self):
        """Met à jour les statistiques affichées."""
        total = self.table.rowCount()
        self.total_label.setText(f"Total : {total}")

        expiring = get_expiring_contracts(30)
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
