# -*- coding: utf-8 -*-
"""
Écran de connexion pour l'application EMAC
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from gui.components.ui_theme import EmacButton, EmacCard
from domain.services.admin.auth_service import authenticate_user


class LoginDialog(QDialog):
    """Dialogue de connexion"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EMAC - Connexion")
        self.setModal(True)

        self.resize(450, 550)
        self.setMinimumSize(400, 450)

        self._countdown_seconds = 0
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._tick_countdown)
        self._rate_limit_message = ""

        self.setup_ui()

        self.login_successful = False

    def setup_ui(self):
        """Initialise l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Centrer verticalement
        main_layout.addStretch()

        # Logo / Titre
        title_label = QLabel("EMAC")
        title_label.setProperty('class', 'h1')
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        subtitle_label = QLabel("Gestion du Personnel")
        subtitle_label.setProperty('class', 'subtitle')
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)

        main_layout.addSpacing(20)

        # Carte de connexion
        login_card = EmacCard()
        card_layout = login_card.body

        # Titre de la carte
        card_title = QLabel("Connexion")
        card_title.setProperty('class', 'h2')
        card_title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(card_title)

        card_layout.addSpacing(20)

        # Champ nom d'utilisateur
        username_label = QLabel("Nom d'utilisateur")
        card_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Entrez votre nom d'utilisateur")
        self.username_input.setFixedHeight(40)
        self.username_input.returnPressed.connect(self.on_login)
        card_layout.addWidget(self.username_input)

        card_layout.addSpacing(10)

        # Champ mot de passe
        password_label = QLabel("Mot de passe")
        card_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Entrez votre mot de passe")
        self.password_input.setFixedHeight(40)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.on_login)
        card_layout.addWidget(self.password_input)

        card_layout.addSpacing(20)

        # Message d'erreur (caché par défaut)
        self.error_label = QLabel()
        self.error_label.setProperty('class', 'error')
        self.error_label.setStyleSheet("color: #d32f2f; padding: 8px; background-color: #ffebee; border-radius: 4px;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        # Bouton de connexion
        self.login_button = EmacButton("Se connecter", variant='primary')
        self.login_button.setFixedHeight(44)
        self.login_button.clicked.connect(self.on_login)
        card_layout.addWidget(self.login_button)

        main_layout.addWidget(login_card)

        main_layout.addStretch()

        # Focus sur le champ username
        self.username_input.setFocus()

    def on_login(self):
        """Gère la tentative de connexion"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Validation
        if not username:
            self.show_error("Veuillez entrer un nom d'utilisateur")
            return

        if not password:
            self.show_error("Veuillez entrer un mot de passe")
            return

        # Désactiver le bouton pendant l'authentification
        self.login_button.setEnabled(False)
        self.login_button.setText("Connexion en cours...")

        # Tentative d'authentification
        success, error_message, wait_seconds = authenticate_user(username, password)

        if success:
            self.login_successful = True
            self.accept()
        else:
            if wait_seconds > 0:
                self._start_countdown(error_message or "Accès temporairement bloqué.", wait_seconds)
            else:
                self.show_error(error_message or "Erreur de connexion")
                self.login_button.setEnabled(True)
                self.login_button.setText("Se connecter")
            self.password_input.clear()
            self.password_input.setFocus()

    def show_error(self, message: str):
        """Affiche un message d'erreur"""
        self.error_label.setText(message)
        self.error_label.show()
        self.error_label.setStyleSheet("""
            color: #d32f2f;
            padding: 8px;
            background-color: #ffebee;
            border-radius: 4px;
            border-left: 3px solid #d32f2f;
        """)

    def _start_countdown(self, base_message: str, seconds: int):
        """Lance le compte à rebours de blocage."""
        self._rate_limit_message = base_message
        self._countdown_seconds = seconds
        self._update_countdown_label()
        self.login_button.setEnabled(False)
        self._countdown_timer.start()

    def _tick_countdown(self):
        self._countdown_seconds -= 1
        if self._countdown_seconds <= 0:
            self._countdown_timer.stop()
            self.error_label.hide()
            self.login_button.setEnabled(True)
            self.login_button.setText("Se connecter")
        else:
            self._update_countdown_label()

    def _update_countdown_label(self):
        mins, secs = divmod(self._countdown_seconds, 60)
        if mins > 0:
            time_str = f"{mins} min {secs:02d} s"
        else:
            time_str = f"{self._countdown_seconds} s"
        self.error_label.setText(f"{self._rate_limit_message}\nRéessayez dans : {time_str}")
        self.error_label.show()
        self.error_label.setStyleSheet("""
            color: #e65100;
            padding: 8px;
            background-color: #fff3e0;
            border-radius: 4px;
            border-left: 3px solid #e65100;
        """)

    def keyPressEvent(self, event):
        if event.key() != Qt.Key_Escape:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        event.accept()
