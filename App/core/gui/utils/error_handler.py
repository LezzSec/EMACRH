# -*- coding: utf-8 -*-
"""
Décorateur @handle_ui_error — gestion centralisée des erreurs dans les dialogs.

Usage :
    from core.gui.utils.error_handler import handle_ui_error

    class MonDialog(QDialog):

        @handle_ui_error("Erreur de sauvegarde")
        def _save(self):
            self._vm.save(self._get_form_data())

        @handle_ui_error()
        def _load(self):
            self._vm.load()

Le décorateur :
- Laisse passer les retours normaux (return value préservé)
- Intercepte PermissionError → titre "Permission refusée", message de l'exception
- Intercepte toutes les autres exceptions → log complet + message générique à l'utilisateur
- N'affiche JAMAIS le traceback à l'utilisateur (sécurité)
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Callable

from core.gui.components.emac_ui_kit import show_error_message

logger = logging.getLogger(__name__)


def handle_ui_error(titre: str = "Erreur") -> Callable:
    """
    Décorateur pour les méthodes de dialog.

    Args:
        titre: Titre de la boîte d'erreur affichée à l'utilisateur.

    Returns:
        Décorateur applicable à une méthode d'instance (self comme premier argument).

    Exemple :
        @handle_ui_error("Erreur d'export")
        def _export_pdf(self):
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            try:
                return fn(self, *args, **kwargs)
            except PermissionError as e:
                logger.warning(f"Permission refusée dans {fn.__qualname__}: {e}")
                show_error_message(self, "Permission refusée", str(e))
            except Exception as e:
                logger.exception(f"Erreur dans {fn.__qualname__}")
                show_error_message(self, titre, "Une erreur est survenue.", e)
        return wrapper
    return decorator
