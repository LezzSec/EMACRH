# -*- coding: utf-8 -*-
"""
Service de gestion des modules de l'application.

Un module représente une section de navigation (RH, Production, Planning…).
L'administrateur peut activer/désactiver chaque module depuis le panel
Administration > Modules de l'application.

Les changements sont persistés en base et appliqués au prochain rechargement
du drawer dans la fenêtre principale.
"""

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.logging_config import get_logger
from infrastructure.logging.optimized_db_logger import log_hist_async

logger = get_logger(__name__)

_TABLE = "app_modules"


def get_all_modules() -> list[dict]:
    """Retourne tous les modules triés par display_order."""
    return QueryExecutor.fetch_all(
        "SELECT id, code, label, description, is_enabled, display_order "
        "FROM app_modules ORDER BY display_order",
        dictionary=True
    ) or []


def get_enabled_codes() -> set[str]:
    """Retourne l'ensemble des codes de modules activés."""
    rows = QueryExecutor.fetch_all(
        "SELECT code FROM app_modules WHERE is_enabled = TRUE",
        dictionary=True
    ) or []
    return {r["code"] for r in rows}


def set_module_enabled(code: str, enabled: bool) -> bool:
    """
    Active ou désactive un module.
    Retourne True si la mise à jour a réussi, False sinon.
    """
    allowed_codes = {"rh", "production", "planning", "documents", "historique"}
    if code not in allowed_codes:
        logger.warning(f"module_service: code inconnu '{code}'")
        return False

    try:
        affected = QueryExecutor.execute_write(
            "UPDATE app_modules SET is_enabled = %s WHERE code = %s",
            (enabled, code)
        )
        state_label = "activé" if enabled else "désactivé"
        log_hist_async(
            "MODULE_TOGGLE",
            f"Module '{code}' {state_label} par l'administrateur"
        )
        logger.info(f"Module '{code}' {state_label}")
        return affected > 0
    except Exception as e:
        logger.exception(f"Erreur lors du toggle du module '{code}': {e}")
        return False
