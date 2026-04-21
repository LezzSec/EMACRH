# -*- coding: utf-8 -*-
import sys
import os

# Logging centralisé — doit être initialisé avant tout import d'infrastructure
from infrastructure.logging.logging_config import setup_logging, get_logger

_production_mode = os.getenv('EMAC_ENV', '').lower() == 'production'
setup_logging(production_mode=_production_mode)

# Path setup for cx_Freeze (frozen executables)
if getattr(sys, 'frozen', False):
    _app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, _app_dir)
else:
    _app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _app_dir not in sys.path:
        sys.path.insert(0, _app_dir)

# Initialiser le thread pool DB au démarrage
from gui.workers.db_worker import DbThreadPool
DbThreadPool.get_pool()

from gui.main_qt.main_window import MainWindow  # noqa: F401

__all__ = ['MainWindow']
