# core/services/logger.py
# Shim de compatibilité — tout le code est dans optimized_db_logger.py
from core.services.optimized_db_logger import (
    log_hist,
    _to_json_str,
    _get_current_username,
)

__all__ = ["log_hist"]
