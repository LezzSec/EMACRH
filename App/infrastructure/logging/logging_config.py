# -*- coding: utf-8 -*-
"""
Configuration centralisée du logging EMAC.

Ce module configure le système de logging pour toute l'application.
À initialiser UNE SEULE FOIS au démarrage de l'application (dans main_qt.py).

Usage:
    from infrastructure.logging.logging_config import setup_logging, get_logger

    # Au démarrage de l'application
    setup_logging(production_mode=False)  # False = dev, True = prod

    # Dans chaque module
    logger = get_logger(__name__)
    logger.info("Message info")
    logger.error("Erreur", exc_info=True)  # Inclut traceback

Configuration:
    - DEV:  INFO level, logs vers console + fichier
    - PROD: WARNING level, logs vers fichier uniquement

Fichier de log: logs/emac.log (rotation à 10 MB, 5 backups)
"""

import logging
import sys
import threading
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# ===========================
# Configuration
# ===========================

_LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
_LOG_FORMAT_DETAILED = '%(asctime)s | %(levelname)-8s | %(name)s | [%(user_id)s] [%(screen)s] | %(message)s'
_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5
_LOG_FILENAME = 'emac.log'

_initialized = False
_production_mode = False
_logs_dir: Optional[Path] = None


# ===========================
# Context Filter (user_id, screen)
# ===========================

class ContextFilter(logging.Filter):
    """
    Filter qui ajoute le contexte (user_id, screen) aux logs.

    Ces valeurs peuvent être définies via set_log_context() depuis n'importe quel module.
    """

    def filter(self, record):
        # Ajouter les valeurs par défaut si non présentes
        if not hasattr(record, 'user_id'):
            record.user_id = _context.user_id or '-'
        if not hasattr(record, 'screen'):
            record.screen = _context.screen or '-'
        return True


class LogContext:
    """Stockage thread-local du contexte de logging"""

    def __init__(self):
        self._local = threading.local()

    @property
    def user_id(self) -> Optional[str]:
        return getattr(self._local, 'user_id', None)

    @user_id.setter
    def user_id(self, value: Optional[str]):
        self._local.user_id = value

    @property
    def screen(self) -> Optional[str]:
        return getattr(self._local, 'screen', None)

    @screen.setter
    def screen(self, value: Optional[str]):
        self._local.screen = value


_context = LogContext()


def set_log_context(user_id: Optional[str] = None, screen: Optional[str] = None):
    """
    Définit le contexte pour les logs (user_id, screen/action).

    Appeler cette fonction quand l'utilisateur se connecte ou change d'écran.

    Args:
        user_id: Identifiant de l'utilisateur connecté
        screen: Nom de l'écran/action en cours

    Usage:
        # À la connexion
        set_log_context(user_id="jdupont")

        # Lors d'un changement d'écran
        set_log_context(screen="GestionEvaluation")

        # Les deux
        set_log_context(user_id="jdupont", screen="Planning")
    """
    if user_id is not None:
        _context.user_id = user_id
    if screen is not None:
        _context.screen = screen


def clear_log_context():
    """Réinitialise le contexte de logging (à la déconnexion)"""
    _context.user_id = None
    _context.screen = None


# ===========================
# Setup principal
# ===========================

def _get_logs_dir() -> Path:
    """Détermine le dossier de logs"""
    global _logs_dir

    if _logs_dir is not None:
        return _logs_dir

    # Mode exécutable (PyInstaller)
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        # Mode développement: App/logs
        base_dir = Path(__file__).parent.parent.parent

    _logs_dir = base_dir / 'logs'
    _logs_dir.mkdir(parents=True, exist_ok=True)

    return _logs_dir


def setup_logging(production_mode: bool = False) -> None:
    """
    Configure le système de logging pour toute l'application.

    À appeler UNE SEULE FOIS au démarrage de l'application,
    AVANT de créer les loggers individuels.

    Args:
        production_mode: True = WARNING level, False = DEBUG level

    Usage:
        # Dans main_qt.py, au tout début
        from infrastructure.logging.logging_config import setup_logging
        setup_logging(production_mode=os.getenv('EMAC_ENV') == 'production')
    """
    global _initialized, _production_mode

    if _initialized:
        return

    _production_mode = production_mode

    # Niveau de log selon le mode
    root_level = logging.WARNING if production_mode else logging.DEBUG
    console_level = logging.WARNING if production_mode else logging.INFO
    file_level = logging.INFO if production_mode else logging.DEBUG

    # Configurer le root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(root_level)

    # Supprimer les handlers existants
    root_logger.handlers.clear()

    # Filter pour le contexte
    context_filter = ContextFilter()

    # Format avec contexte
    formatter = logging.Formatter(_LOG_FORMAT_DETAILED, _DATE_FORMAT)

    # Handler console (seulement WARNING+ en prod)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)
    root_logger.addHandler(console_handler)

    # Handler fichier avec rotation
    logs_dir = _get_logs_dir()
    log_file = logs_dir / _LOG_FILENAME

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=_MAX_FILE_SIZE,
        backupCount=_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)
    root_logger.addHandler(file_handler)

    # Réduire le bruit des bibliothèques tierces
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('mysql.connector').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

    _initialized = True

    # Log de démarrage
    startup_logger = logging.getLogger('emac.startup')
    mode_str = "PRODUCTION" if production_mode else "DEVELOPMENT"
    startup_logger.info(f"=== EMAC Logging initialisé en mode {mode_str} ===")
    startup_logger.info(f"Fichier de log: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger configuré pour le module donné.

    Args:
        name: Nom du logger (utiliser __name__ généralement)

    Returns:
        Logger configuré

    Usage:
        from infrastructure.logging.logging_config import get_logger

        logger = get_logger(__name__)
        logger.debug("Message debug (dev uniquement)")
        logger.info("Message info")
        logger.warning("Avertissement")
        logger.error("Erreur")
        logger.exception("Erreur avec traceback")  # Dans un bloc except
    """
    if not _initialized:
        # Auto-initialisation en mode dev si pas encore fait
        setup_logging(production_mode=False)

    return logging.getLogger(name)


def is_production_mode() -> bool:
    """Retourne True si le logging est en mode production"""
    return _production_mode


def get_log_file_path() -> Path:
    """Retourne le chemin du fichier de log"""
    return _get_logs_dir() / _LOG_FILENAME


def get_logs_dir() -> Path:
    """Retourne le dossier de logs (crée si nécessaire)"""
    return _get_logs_dir()


# ===========================
# Utilitaires
# ===========================

def log_exception(logger: logging.Logger, message: str, exc: Exception = None):
    """
    Log une exception avec son traceback complet.

    Alternative à traceback.print_exc() - utiliser logger.exception() à la place.

    Args:
        logger: Logger à utiliser
        message: Message descriptif
        exc: Exception (optionnel, utilise sys.exc_info() par défaut)

    Usage:
        try:
            something()
        except Exception as e:
            log_exception(logger, "Erreur lors de something", e)
    """
    if exc:
        logger.error(message, exc_info=(type(exc), exc, exc.__traceback__))
    else:
        logger.exception(message)


# ===========================
# Exports
# ===========================

__all__ = [
    'setup_logging',
    'get_logger',
    'set_log_context',
    'clear_log_context',
    'is_production_mode',
    'get_log_file_path',
    'get_logs_dir',
    'log_exception',
]
