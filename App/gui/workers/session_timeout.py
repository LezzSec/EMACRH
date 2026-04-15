# -*- coding: utf-8 -*-
"""
SessionTimeoutManager - Gestion du timeout de session pour inactivité

Sécurité:
- Déconnexion automatique après période d'inactivité (configurable)
- Avertissement avant déconnexion (5 minutes par défaut)
- Détection d'activité via événements souris/clavier
- Log de sécurité des déconnexions automatiques

Usage:
    from gui.workers.session_timeout import SessionTimeoutManager

    # Dans MainWindow.__init__()
    self.timeout_manager = SessionTimeoutManager(self)
    self.timeout_manager.timeout_logout.connect(self.force_logout)
    self.timeout_manager.start()

Configuration:
    - SESSION_TIMEOUT_MINUTES: Durée d'inactivité avant déconnexion (défaut: 30)
    - WARNING_BEFORE_MINUTES: Avertissement avant déconnexion (défaut: 5)
    - CHECK_INTERVAL_SECONDS: Intervalle de vérification (défaut: 30)

Date: 2026-02-04
"""

import logging
from datetime import datetime, timedelta

from PyQt5.QtCore import QObject, QTimer, pyqtSignal, Qt, QEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

logger = logging.getLogger(__name__)

# Configuration du timeout (en minutes)
SESSION_TIMEOUT_MINUTES = 30  # Déconnexion après 30 minutes d'inactivité
WARNING_BEFORE_MINUTES = 5    # Avertissement 5 minutes avant
CHECK_INTERVAL_SECONDS = 30   # Vérification toutes les 30 secondes


class TimeoutWarningDialog(QDialog):
    """
    Dialog d'avertissement affiché avant le timeout.
    Permet à l'utilisateur de prolonger sa session ou de se déconnecter.
    """

    def __init__(self, remaining_seconds: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Session expirante")
        self.setModal(True)
        self.setFixedSize(400, 200)
        self.remaining_seconds = remaining_seconds

        # Empêcher la fermeture par X (force le choix)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Icône et titre
        title = QLabel("Session inactive")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e67e22;")
        layout.addWidget(title)

        # Message
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("font-size: 13px;")
        self._update_message()
        layout.addWidget(self.message_label)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_extend = QPushButton("Prolonger la session")
        self.btn_extend.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_extend.clicked.connect(self.accept)

        self.btn_logout = QPushButton("Se déconnecter maintenant")
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_logout.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_extend)
        btn_layout.addWidget(self.btn_logout)
        layout.addLayout(btn_layout)

        # Timer pour mettre à jour le compteur
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._countdown_tick)
        self.countdown_timer.start(1000)  # Toutes les secondes

    def _update_message(self):
        """Met à jour le message avec le temps restant."""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.message_label.setText(
            f"Votre session va expirer dans <b>{minutes}:{seconds:02d}</b> "
            f"en raison d'inactivité.\n\n"
            f"Cliquez sur 'Prolonger' pour continuer à travailler."
        )

    def _countdown_tick(self):
        """Décrémente le compteur."""
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self.countdown_timer.stop()
            self.reject()  # Force logout
        else:
            self._update_message()


class SessionTimeoutManager(QObject):
    """
    Gestionnaire de timeout de session.

    Surveille l'activité utilisateur et déclenche une déconnexion
    automatique après une période d'inactivité.

    Signals:
        timeout_logout: Émis quand l'utilisateur doit être déconnecté
        activity_detected: Émis quand une activité est détectée
        warning_shown: Émis quand l'avertissement est affiché
    """

    timeout_logout = pyqtSignal()
    activity_detected = pyqtSignal()
    warning_shown = pyqtSignal(int)  # secondes restantes

    def __init__(self, parent_window, timeout_minutes: int = SESSION_TIMEOUT_MINUTES):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.timeout_minutes = timeout_minutes
        self.warning_minutes = WARNING_BEFORE_MINUTES

        self._last_activity = datetime.now()
        self._warning_shown = False
        self._enabled = True

        # Timer de vérification périodique
        self._check_timer = QTimer(self)
        self._check_timer.timeout.connect(self._check_timeout)

        # Installer l'event filter sur QApplication pour capturer l'activité
        # dans TOUS les widgets (dialogs inclus), pas seulement la fenêtre principale
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

        logger.info(f"SessionTimeoutManager initialisé: timeout={timeout_minutes}min, warning={self.warning_minutes}min")

    def start(self):
        """Démarre la surveillance du timeout."""
        if not self._enabled:
            return

        self._last_activity = datetime.now()
        self._warning_shown = False
        self._check_timer.start(CHECK_INTERVAL_SECONDS * 1000)
        logger.debug("Surveillance timeout démarrée")

    def stop(self):
        """Arrête la surveillance du timeout."""
        self._check_timer.stop()
        logger.debug("Surveillance timeout arrêtée")

    def reset(self):
        """Réinitialise le timer d'activité."""
        self._last_activity = datetime.now()
        self._warning_shown = False

        # Mettre à jour UserSession
        try:
            from domain.services.admin.auth_service import UserSession
            UserSession.update_activity()
        except Exception:
            pass

    def set_enabled(self, enabled: bool):
        """Active ou désactive le timeout."""
        self._enabled = enabled
        if not enabled:
            self.stop()
        else:
            self.start()

    def is_enabled(self) -> bool:
        """Retourne True si le timeout est actif."""
        return self._enabled

    def get_remaining_seconds(self) -> int:
        """Retourne le nombre de secondes restantes avant timeout."""
        elapsed = datetime.now() - self._last_activity
        timeout_delta = timedelta(minutes=self.timeout_minutes)
        remaining = timeout_delta - elapsed
        return max(0, int(remaining.total_seconds()))

    def eventFilter(self, obj, event) -> bool:
        """
        Filtre les événements pour détecter l'activité utilisateur.

        Détecte: mouvements souris, clics, touches clavier.
        """
        if not self._enabled:
            return False

        # Événements d'activité
        activity_events = {
            QEvent.MouseMove,
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.KeyPress,
            QEvent.KeyRelease,
            QEvent.Wheel,
        }

        if event.type() in activity_events:
            self._on_activity()

        return False  # Ne pas bloquer l'événement

    def _on_activity(self):
        """Appelé quand une activité utilisateur est détectée."""
        old_remaining = self.get_remaining_seconds()
        self._last_activity = datetime.now()
        self._warning_shown = False

        # Mettre à jour UserSession
        try:
            from domain.services.admin.auth_service import UserSession
            UserSession.update_activity()
        except Exception:
            pass

        self.activity_detected.emit()

    def _check_timeout(self):
        """Vérifie périodiquement si le timeout est atteint."""
        if not self._enabled:
            return

        remaining_seconds = self.get_remaining_seconds()
        warning_threshold = self.warning_minutes * 60

        # Timeout atteint
        if remaining_seconds <= 0:
            logger.warning("Session expirée par inactivité")
            self._force_logout()
            return

        # Avertissement avant timeout
        if remaining_seconds <= warning_threshold and not self._warning_shown:
            self._show_warning(remaining_seconds)

    def _show_warning(self, remaining_seconds: int):
        """Affiche l'avertissement de timeout."""
        self._warning_shown = True
        self.warning_shown.emit(remaining_seconds)

        logger.info(f"Avertissement timeout: {remaining_seconds}s restantes")

        # Afficher le dialog d'avertissement
        dialog = TimeoutWarningDialog(remaining_seconds, self.parent_window)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            # Utilisateur a prolongé la session
            logger.info("Session prolongée par l'utilisateur")
            self.reset()
        else:
            # Utilisateur a choisi de se déconnecter ou timeout du dialog
            logger.info("Déconnexion choisie/forcée depuis l'avertissement")
            self._force_logout()

    def _force_logout(self):
        """Force la déconnexion de l'utilisateur."""
        self.stop()

        # Log de sécurité
        try:
            from domain.services.admin.auth_service import UserSession, get_current_user
            from infrastructure.logging.optimized_db_logger import log_hist_async

            user = get_current_user()
            if user:
                log_hist_async(
                    action="LOGOUT_TIMEOUT",
                    table_name="utilisateurs",
                    record_id=user.get('id'),
                    description=f"Déconnexion automatique par timeout ({self.timeout_minutes}min inactivité)",
                    utilisateur=user.get('username')
                )
        except Exception as e:
            logger.warning(f"Erreur log timeout: {e}")

        # Émettre le signal de déconnexion
        self.timeout_logout.emit()


def get_session_timeout_config() -> dict:
    """
    Retourne la configuration actuelle du timeout de session.

    Returns:
        dict avec timeout_minutes, warning_minutes, check_interval_seconds
    """
    return {
        'timeout_minutes': SESSION_TIMEOUT_MINUTES,
        'warning_minutes': WARNING_BEFORE_MINUTES,
        'check_interval_seconds': CHECK_INTERVAL_SECONDS,
    }
