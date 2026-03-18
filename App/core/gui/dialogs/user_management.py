# -*- coding: utf-8 -*-
"""
Interface de gestion des utilisateurs (Administrateur uniquement)
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QLineEdit,
    QComboBox, QHeaderView, QWidget
)
from PyQt5.QtCore import Qt
from core.gui.components.ui_theme import EmacButton, EmacCard
from core.services.auth_service import (
    get_all_users, create_user, update_user_status,
    change_password, get_roles, is_admin, count_active_admins, delete_user, get_current_user, validate_password, get_password_requirements
)


class UserManagementDialog(QDialog):
    """Dialogue de gestion des utilisateurs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Utilisateurs")
        self.setModal(True)
        self.setMinimumSize(900, 600)

        # Vérifier les permissions
        if not is_admin():
            QMessageBox.critical(self, "Accès refusé", "Seuls les administrateurs peuvent accéder à cette fonctionnalité.")
            self.reject()
            return

        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        """Initialise l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Titre
        title = QLabel("Gestion des Utilisateurs")
        title.setProperty('class', 'h1')
        main_layout.addWidget(title)

        # Boutons d'action
        btn_layout = QHBoxLayout()
        self.btn_add_user = EmacButton("➕ Nouvel Utilisateur", variant='primary')
        self.btn_add_user.clicked.connect(self.show_add_user_dialog)
        btn_layout.addWidget(self.btn_add_user)

        # Bouton pour gérer les permissions (système features)
        self.btn_permissions = EmacButton("🔐 Gérer les Permissions", variant='ghost')
        self.btn_permissions.clicked.connect(self.show_feature_editor)
        btn_layout.addWidget(self.btn_permissions)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # Table des utilisateurs
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Nom d'utilisateur", "Nom", "Prénom", "Rôle", "Statut", "Actions"
        ])

        # Configuration de la table
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setAlternatingRowColors(True)

        main_layout.addWidget(self.users_table)

        # Bouton de fermeture
        close_btn = EmacButton("Fermer", variant='ghost')
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn, alignment=Qt.AlignRight)

    def load_users(self):
        """Charge la liste des utilisateurs"""
        users = get_all_users()
        self.users_table.setRowCount(len(users))

        # Compter les administrateurs actifs pour la sécurité
        active_admins_count = count_active_admins()

        for row, user in enumerate(users):
            # ID
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))

            # Username
            self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))

            # Nom
            self.users_table.setItem(row, 2, QTableWidgetItem(user['nom']))

            # Prénom
            self.users_table.setItem(row, 3, QTableWidgetItem(user['prenom']))

            # Rôle
            self.users_table.setItem(row, 4, QTableWidgetItem(user['role_nom']))

            # Statut
            statut_text = "Actif" if user['actif'] else "Inactif"
            statut_item = QTableWidgetItem(statut_text)
            if user['actif']:
                statut_item.setForeground(Qt.darkGreen)
            else:
                statut_item.setForeground(Qt.red)
            self.users_table.setItem(row, 5, statut_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            # Vérifier si c'est le dernier admin actif
            is_last_admin = (user['actif'] and
                           user['role_nom'] == 'admin' and
                           active_admins_count <= 1)

            # Bouton activer/désactiver
            if user['actif']:
                btn_toggle = QPushButton("Désactiver")
                if is_last_admin:
                    # Désactiver le bouton pour le dernier admin
                    btn_toggle.setEnabled(False)
                    btn_toggle.setStyleSheet("background-color: #bdbdbd; color: #757575; padding: 4px 8px; border-radius: 4px; cursor: not-allowed;")
                    btn_toggle.setToolTip("Impossible de désactiver le dernier administrateur actif")
                else:
                    btn_toggle.setStyleSheet("background-color: #f44336; color: white; padding: 4px 8px; border-radius: 4px;")
            else:
                btn_toggle = QPushButton("Activer")
                btn_toggle.setStyleSheet("background-color: #4caf50; color: white; padding: 4px 8px; border-radius: 4px;")

            btn_toggle.clicked.connect(lambda checked, uid=user['id'], active=user['actif']: self.toggle_user_status(uid, not active))
            actions_layout.addWidget(btn_toggle)

            # Bouton changer mot de passe
            btn_password = QPushButton("Changer MDP")
            btn_password.setStyleSheet("background-color: #2196f3; color: white; padding: 4px 8px; border-radius: 4px;")
            btn_password.clicked.connect(lambda checked, uid=user['id']: self.show_change_password_dialog(uid))
            actions_layout.addWidget(btn_password)

            # Bouton supprimer (désactivé pour le compte actuel et le dernier admin)
            current_user = get_current_user()
            is_current_user = current_user and current_user['id'] == user['id']

            btn_delete = QPushButton("Supprimer")
            if is_current_user or is_last_admin:
                btn_delete.setEnabled(False)
                btn_delete.setStyleSheet("background-color: #bdbdbd; color: #757575; padding: 4px 8px; border-radius: 4px;")
                if is_current_user:
                    btn_delete.setToolTip("Vous ne pouvez pas supprimer votre propre compte")
                else:
                    btn_delete.setToolTip("Impossible de supprimer le dernier administrateur")
            else:
                btn_delete.setStyleSheet("background-color: #dc2626; color: white; padding: 4px 8px; border-radius: 4px;")
                btn_delete.clicked.connect(lambda checked, uid=user['id'], uname=user['username']: self.confirm_delete_user(uid, uname))
            actions_layout.addWidget(btn_delete)

            self.users_table.setCellWidget(row, 6, actions_widget)

    def show_add_user_dialog(self):
        """Affiche le dialogue pour ajouter un nouvel utilisateur"""
        dialog = AddUserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()  # Recharger la liste

    def toggle_user_status(self, user_id: int, new_status: bool):
        """Active ou désactive un utilisateur"""
        action = "activer" if new_status else "désactiver"
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment {action} cet utilisateur?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, error = update_user_status(user_id, new_status)
            if success:
                QMessageBox.information(self, "Succès", f"Utilisateur {action} avec succès.")
                self.load_users()  # Recharger la liste
            else:
                QMessageBox.critical(self, "Erreur", error or "Une erreur est survenue.")

    def show_change_password_dialog(self, user_id: int):
        """Affiche le dialogue pour changer le mot de passe"""
        dialog = ChangePasswordDialog(user_id, self)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Succès", "Mot de passe modifié avec succès.")

    def confirm_delete_user(self, user_id: int, username: str):
        """Demande confirmation avant de supprimer un utilisateur"""
        reply = QMessageBox.warning(
            self,
            "Confirmation de suppression",
            f"Voulez-vous vraiment supprimer définitivement l'utilisateur '{username}' ?\n\n"
            "Cette action est irréversible et supprimera également l'historique de connexion de cet utilisateur.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, error = delete_user(user_id)
            if success:
                QMessageBox.information(self, "Succès", f"L'utilisateur '{username}' a été supprimé.")
                self.load_users()
            else:
                QMessageBox.critical(self, "Erreur", error or "Une erreur est survenue.")

    def show_feature_editor(self):
        """Affiche l'éditeur de permissions (système features)"""
        from core.gui.dialogs.feature_puzzle import FeatureEditorDialog

        dialog = FeatureEditorDialog(self)
        dialog.exec_()


class AddUserDialog(QDialog):
    """Dialogue pour ajouter un nouvel utilisateur"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouvel Utilisateur")
        self.setModal(True)
        self.resize(550, 650)
        self.setMinimumSize(500, 600)

        self.setup_ui()

    def setup_ui(self):
        """Initialise l'interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Titre
        title = QLabel("Créer un nouvel utilisateur")
        title.setProperty('class', 'h2')
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # Champs de formulaire
        form_card = EmacCard()
        form_layout = form_card.body
        form_layout.setSpacing(10)

        # Nom d'utilisateur
        label1 = QLabel("Nom d'utilisateur *")
        label1.setStyleSheet("font-size: 14px; font-weight: 500;")
        form_layout.addWidget(label1)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("ex: jdupont")
        self.username_input.setMinimumHeight(38)
        self.username_input.setStyleSheet("font-size: 14px; padding: 6px;")
        form_layout.addWidget(self.username_input)

        form_layout.addSpacing(8)

        # Mot de passe
        label2 = QLabel("Mot de passe *")
        label2.setStyleSheet("font-size: 14px; font-weight: 500;")
        form_layout.addWidget(label2)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("8+ caractères, majuscule, chiffre, spécial")
        self.password_input.setMinimumHeight(38)
        self.password_input.setStyleSheet("font-size: 14px; padding: 6px;")
        self.password_input.setToolTip(get_password_requirements())
        form_layout.addWidget(self.password_input)

        form_layout.addSpacing(8)

        # Confirmation mot de passe
        label3 = QLabel("Confirmer le mot de passe *")
        label3.setStyleSheet("font-size: 14px; font-weight: 500;")
        form_layout.addWidget(label3)
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setEchoMode(QLineEdit.Password)
        self.password_confirm_input.setPlaceholderText("Retapez le mot de passe")
        self.password_confirm_input.setMinimumHeight(38)
        self.password_confirm_input.setStyleSheet("font-size: 14px; padding: 6px;")
        form_layout.addWidget(self.password_confirm_input)

        form_layout.addSpacing(8)

        # Nom
        label4 = QLabel("Nom *")
        label4.setStyleSheet("font-size: 14px; font-weight: 500;")
        form_layout.addWidget(label4)
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("ex: Dupont")
        self.nom_input.setMinimumHeight(38)
        self.nom_input.setStyleSheet("font-size: 14px; padding: 6px;")
        form_layout.addWidget(self.nom_input)

        form_layout.addSpacing(8)

        # Prénom
        label5 = QLabel("Prénom *")
        label5.setStyleSheet("font-size: 14px; font-weight: 500;")
        form_layout.addWidget(label5)
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("ex: Jean")
        self.prenom_input.setMinimumHeight(38)
        self.prenom_input.setStyleSheet("font-size: 14px; padding: 6px;")
        form_layout.addWidget(self.prenom_input)

        form_layout.addSpacing(8)

        # Rôle
        label6 = QLabel("Rôle *")
        label6.setStyleSheet("font-size: 14px; font-weight: 500;")
        form_layout.addWidget(label6)
        self.role_combo = QComboBox()
        self.role_combo.setMinimumHeight(38)
        self.role_combo.setStyleSheet("font-size: 14px; padding: 6px;")
        roles = get_roles()
        for role in roles:
            self.role_combo.addItem(f"{role['nom']} - {role['description']}", role['id'])
        form_layout.addWidget(self.role_combo)

        main_layout.addWidget(form_card)

        main_layout.addSpacing(10)

        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        cancel_btn = EmacButton("Annuler", variant='ghost')
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setStyleSheet(cancel_btn.styleSheet() + "font-size: 14px;")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        create_btn = EmacButton("Créer", variant='primary')
        create_btn.setMinimumHeight(44)
        create_btn.setStyleSheet(create_btn.styleSheet() + "font-size: 14px;")
        create_btn.clicked.connect(self.create_user)
        buttons_layout.addWidget(create_btn)

        main_layout.addLayout(buttons_layout)

    def create_user(self):
        """Crée un nouvel utilisateur"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()
        nom = self.nom_input.text().strip()
        prenom = self.prenom_input.text().strip()
        role_id = self.role_combo.currentData()

        # Validation
        if not username or not password or not nom or not prenom:
            QMessageBox.warning(self, "Champs requis", "Tous les champs sont obligatoires.")
            return

        # 🔒 Validation renforcée du mot de passe
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            QMessageBox.warning(self, "Mot de passe invalide", error_msg)
            return

        if password != password_confirm:
            QMessageBox.warning(self, "Mot de passe", "Les mots de passe ne correspondent pas.")
            return

        # Créer l'utilisateur
        success, error = create_user(username, password, nom, prenom, role_id)

        if success:
            QMessageBox.information(self, "Succès", "Utilisateur créé avec succès!")
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", error or "Une erreur est survenue lors de la création.")


class ChangePasswordDialog(QDialog):
    """Dialogue pour changer le mot de passe d'un utilisateur"""

    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Changer le mot de passe")
        self.setModal(True)
        self.resize(500, 350)
        self.setMinimumSize(450, 300)

        self.setup_ui()

    def setup_ui(self):
        """Initialise l'interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Titre
        title = QLabel("Nouveau mot de passe")
        title.setProperty('class', 'h2')
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # Champs
        card = EmacCard()
        form_layout = card.body
        form_layout.setSpacing(12)

        # Label avec meilleure visibilité
        label1 = QLabel("Nouveau mot de passe *")
        label1.setStyleSheet("font-size: 14px; font-weight: 500; margin-top: 5px;")
        form_layout.addWidget(label1)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("8+ caractères, majuscule, chiffre, spécial")
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet("font-size: 14px; padding: 8px;")
        self.password_input.setToolTip(get_password_requirements())
        form_layout.addWidget(self.password_input)

        form_layout.addSpacing(10)

        label2 = QLabel("Confirmer le mot de passe *")
        label2.setStyleSheet("font-size: 14px; font-weight: 500; margin-top: 5px;")
        form_layout.addWidget(label2)

        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setEchoMode(QLineEdit.Password)
        self.password_confirm_input.setPlaceholderText("Retapez le mot de passe")
        self.password_confirm_input.setMinimumHeight(40)
        self.password_confirm_input.setStyleSheet("font-size: 14px; padding: 8px;")
        form_layout.addWidget(self.password_confirm_input)

        main_layout.addWidget(card)

        main_layout.addSpacing(10)

        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        cancel_btn = EmacButton("Annuler", variant='ghost')
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setStyleSheet(cancel_btn.styleSheet() + "font-size: 14px;")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = EmacButton("Enregistrer", variant='primary')
        save_btn.setMinimumHeight(44)
        save_btn.setStyleSheet(save_btn.styleSheet() + "font-size: 14px;")
        save_btn.clicked.connect(self.save_password)
        buttons_layout.addWidget(save_btn)

        main_layout.addLayout(buttons_layout)

    def save_password(self):
        """Enregistre le nouveau mot de passe"""
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()

        if not password:
            QMessageBox.warning(self, "Champ requis", "Veuillez saisir un mot de passe.")
            return

        # 🔒 Validation renforcée du mot de passe
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            QMessageBox.warning(self, "Mot de passe invalide", error_msg)
            return

        if password != password_confirm:
            QMessageBox.warning(self, "Mot de passe", "Les mots de passe ne correspondent pas.")
            return

        # Changer le mot de passe
        success, error = change_password(self.user_id, password)

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", error or "Une erreur est survenue.")
