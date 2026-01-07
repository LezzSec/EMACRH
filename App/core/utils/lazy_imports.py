# -*- coding: utf-8 -*-
"""
Module de gestion des imports lazy (paresseux).
Réduit le temps de démarrage en chargeant les modules seulement quand nécessaire.

✅ Principe :
- Au démarrage : charger uniquement PyQt5 + essentiels
- À la demande : charger DB, services, exporters quand utilisés

Gain attendu : 30-50% de réduction du temps de démarrage
"""

import sys
from typing import Any, Callable, Optional


# ===========================
# Cache des modules importés
# ===========================

_module_cache = {}


# ===========================
# Lazy Importers
# ===========================

def lazy_import_db():
    """Import lazy du module DB"""
    if 'db' not in _module_cache:
        from core.db import configbd
        _module_cache['db'] = configbd
    return _module_cache['db']


def lazy_import_auth():
    """Import lazy du service d'authentification"""
    if 'auth' not in _module_cache:
        from core.services import auth_service
        _module_cache['auth'] = auth_service
    return _module_cache['auth']


def lazy_import_logger():
    """Import lazy du logger"""
    if 'logger' not in _module_cache:
        from core.services import logger
        _module_cache['logger'] = logger
    return _module_cache['logger']


def lazy_import_excel_exporter():
    """Import lazy de l'exporteur Excel (lourd)"""
    if 'excel_exporter' not in _module_cache:
        from core.exporters import excel_export
        _module_cache['excel_exporter'] = excel_export
    return _module_cache['excel_exporter']


def lazy_import_pdf_exporter():
    """Import lazy de l'exporteur PDF"""
    if 'pdf_exporter' not in _module_cache:
        from core.exporters import pdf_export
        _module_cache['pdf_exporter'] = pdf_export
    return _module_cache['pdf_exporter']


def lazy_import_calendar_service():
    """Import lazy du service calendrier"""
    if 'calendar_service' not in _module_cache:
        from core.services import calendrier_service
        _module_cache['calendar_service'] = calendrier_service
    return _module_cache['calendar_service']


def lazy_import_evaluation_service():
    """Import lazy du service évaluation"""
    if 'evaluation_service' not in _module_cache:
        from core.services import evaluation_service
        _module_cache['evaluation_service'] = evaluation_service
    return _module_cache['evaluation_service']


def lazy_import_contract_service():
    """Import lazy du service contrat"""
    if 'contract_service' not in _module_cache:
        from core.services import contrat_service
        _module_cache['contract_service'] = contrat_service
    return _module_cache['contract_service']


def lazy_import_absence_service():
    """Import lazy du service absence"""
    if 'absence_service' not in _module_cache:
        from core.services import absence_service
        _module_cache['absence_service'] = absence_service
    return _module_cache['absence_service']


# ===========================
# Cache EMAC (optimisations)
# ===========================

def lazy_import_cache():
    """Import lazy du système de cache"""
    if 'cache' not in _module_cache:
        from core.utils import emac_cache
        _module_cache['cache'] = emac_cache
    return _module_cache['cache']


# ===========================
# Wrapper générique
# ===========================

class LazyModule:
    """
    Wrapper pour import lazy générique.

    Usage:
        # Au lieu de:
        from core.services import evaluation_service

        # Utiliser:
        evaluation_service = LazyModule('core.services.evaluation_service')
        # Le module sera importé lors du premier accès à un attribut
    """

    def __init__(self, module_name: str):
        self._module_name = module_name
        self._module = None

    def _load_module(self):
        """Charge le module si pas encore chargé"""
        if self._module is None:
            if self._module_name in _module_cache:
                self._module = _module_cache[self._module_name]
            else:
                # Import dynamique
                parts = self._module_name.split('.')
                module = __import__(self._module_name, fromlist=[parts[-1]])
                self._module = module
                _module_cache[self._module_name] = module

        return self._module

    def __getattr__(self, name):
        """Charge le module au premier accès"""
        module = self._load_module()
        return getattr(module, name)

    def __call__(self, *args, **kwargs):
        """Permet d'appeler le module si c'est une fonction"""
        module = self._load_module()
        return module(*args, **kwargs)


# ===========================
# Décorateur pour fonctions nécessitant import lourd
# ===========================

def with_lazy_import(import_func: Callable):
    """
    Décorateur pour importer un module lourd uniquement quand la fonction est appelée.

    Example:
        @with_lazy_import(lazy_import_excel_exporter)
        def export_to_excel(data):
            excel_exporter = lazy_import_excel_exporter()
            return excel_exporter.export(data)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Import le module avant d'appeler la fonction
            import_func()
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ===========================
# Préchargement intelligent
# ===========================

def preload_common_modules():
    """
    Précharge les modules les plus couramment utilisés.
    À appeler après le démarrage de l'UI (QTimer.singleShot).

    ✅ Stratégie :
    - Ne PAS charger au démarrage (bloque l'UI)
    - Charger 500ms après l'affichage de la fenêtre
    - Charger en arrière-plan (QTimer)
    """
    print("🔄 Préchargement des modules courants...")

    try:
        # Modules légers d'abord
        lazy_import_db()
        lazy_import_auth()
        lazy_import_logger()
        lazy_import_cache()

        # Modules plus lourds ensuite
        lazy_import_calendar_service()
        lazy_import_evaluation_service()

        print(f"✅ {len(_module_cache)} modules préchargés")

    except Exception as e:
        print(f"⚠️ Erreur préchargement: {e}")


def preload_heavy_modules():
    """
    Précharge les modules lourds (exporters).
    À appeler après 2-3 secondes (QTimer.singleShot(3000)).

    ✅ Ces modules sont rarement utilisés au démarrage, on les charge en idle.
    """
    print("🔄 Préchargement des modules lourds...")

    try:
        lazy_import_excel_exporter()
        lazy_import_pdf_exporter()

        print(f"✅ Modules lourds préchargés (total: {len(_module_cache)})")

    except Exception as e:
        print(f"⚠️ Erreur préchargement lourds: {e}")


# ===========================
# Helpers pour debugging
# ===========================

def get_loaded_modules():
    """Retourne la liste des modules chargés en lazy"""
    return list(_module_cache.keys())


def clear_cache():
    """Vide le cache (debug)"""
    _module_cache.clear()


def get_cache_size():
    """Retourne le nombre de modules en cache"""
    return len(_module_cache)


# ===========================
# Intégration dans main_qt.py
# ===========================

def setup_lazy_imports():
    """
    Configure les imports lazy dans main_qt.py.

    À appeler AVANT de créer la fenêtre principale :

    Example dans main_qt.py:
        from core.utils.lazy_imports import setup_lazy_imports, preload_common_modules

        if __name__ == '__main__':
            app = QApplication(sys.argv)

            # ✅ Setup lazy imports
            setup_lazy_imports()

            # Créer et afficher la fenêtre
            window = MainWindow()
            window.show()

            # ✅ Précharger après 500ms
            QTimer.singleShot(500, preload_common_modules)
            QTimer.singleShot(3000, preload_heavy_modules)

            sys.exit(app.exec_())
    """
    # Rien à faire pour le moment, juste documenter l'usage
    pass


# ===========================
# Exports
# ===========================

__all__ = [
    'lazy_import_db',
    'lazy_import_auth',
    'lazy_import_logger',
    'lazy_import_excel_exporter',
    'lazy_import_pdf_exporter',
    'lazy_import_calendar_service',
    'lazy_import_evaluation_service',
    'lazy_import_contract_service',
    'lazy_import_absence_service',
    'lazy_import_cache',
    'LazyModule',
    'with_lazy_import',
    'preload_common_modules',
    'preload_heavy_modules',
    'setup_lazy_imports',
    'get_loaded_modules',
    'clear_cache',
    'get_cache_size',
]
