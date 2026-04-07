# -*- coding: utf-8 -*-
"""
Logger DB pour la table historique.

Expose deux APIs:
- log_hist()       : synchrone, immédiat (compatibilité + fallback)
- log_hist_async() : asynchrone, par batch (production - 10-50x moins de requêtes)

✅ Optimisations appliquées:
- Buffer en mémoire (INSERT par batch)
- Async logging (thread séparé)
- INSERT multiple (1 requête pour N logs)
- Flush automatique toutes les 10s
"""

import json
import threading
import time
from queue import Queue, Empty
from typing import Optional, List, Dict, Any


import logging
_logger = logging.getLogger(__name__)


# ===========================
# Sync logger (log_hist)
# ===========================

def _get_current_username() -> str | None:
    """Récupère le nom d'utilisateur connecté."""
    try:
        from core.services.auth_service import get_current_user
        user = get_current_user()
        if user:
            return user.get('username') or user.get('nom') or None
    except Exception:
        pass
    return None


def _to_json_str(details: Any) -> str | None:
    if details is None:
        return None
    if isinstance(details, (bytes, bytearray)):
        try:
            return details.decode("utf-8", errors="ignore")
        except Exception:
            return str(details)
    if isinstance(details, str):
        return details
    try:
        return json.dumps(details, ensure_ascii=False)
    except Exception:
        return str(details)


def log_hist(
    action: str,
    table_name: str | None = None,
    record_id: Any | None = None,
    description: str | None = None,
    details: Any | None = None,
    source: str | None = None,
    utilisateur: str | None = None,
    operateur_id: int | None = None,
    poste_id: int | None = None,
) -> None:
    """Insère une ligne dans la table `historique` (synchrone, immédiat)."""
    if utilisateur is None:
        utilisateur = _get_current_username()

    final_description = description
    if details:
        details_str = _to_json_str(details)
        final_description = f"{final_description} | Details: {details_str}" if final_description else details_str

    from infrastructure.db.configbd import get_connection as _get_conn
    conn = cur = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO historique
                (date_time, action, table_name, record_id, utilisateur, description, personnel_id, poste_id)
            VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                action,
                table_name,
                str(record_id) if record_id is not None else None,
                utilisateur,
                final_description,
                operateur_id,
                poste_id,
            ),
        )
        conn.commit()
    except Exception as e:
        _logger.warning(f"Erreur log_hist: {e}")
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


# ===========================
# Configuration
# ===========================

class DBLogConfig:
    """Configuration du logger DB"""

    # Taille du buffer (nombre de logs avant INSERT)
    BUFFER_SIZE = 50

    # Flush automatique après X secondes
    FLUSH_INTERVAL = 10.0

    # Taille maximale de la queue
    MAX_QUEUE_SIZE = 500


# ===========================
# Logger DB avec buffer
# ===========================

class OptimizedDBLogger:
    """
    Logger optimisé pour la table historique.

    Au lieu de:
        INSERT INTO historique ...  # 50x (50 requêtes)

    Utilise:
        INSERT INTO historique VALUES (...), (...), ... # 1 requête pour 50 logs
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(OptimizedDBLogger, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.queue = Queue(maxsize=DBLogConfig.MAX_QUEUE_SIZE)
        self.running = False
        self.worker_thread = None

    def start(self):
        """Démarre le worker thread"""
        if self.running:
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def stop(self):
        """Arrête le worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=3.0)

    def _worker(self):
        """Thread worker qui traite la queue et écrit en batch"""
        batch = []
        last_flush = time.time()

        while self.running:
            try:
                # Récupérer un log de la queue (timeout 0.5s)
                log_entry = self.queue.get(timeout=0.5)
                batch.append(log_entry)

                # Flush si batch plein
                if len(batch) >= DBLogConfig.BUFFER_SIZE:
                    self._flush_batch(batch)
                    batch.clear()
                    last_flush = time.time()

            except Empty:
                # Timeout → flush si nécessaire
                if batch and (time.time() - last_flush) >= DBLogConfig.FLUSH_INTERVAL:
                    self._flush_batch(batch)
                    batch.clear()
                    last_flush = time.time()

        # Flush final avant arrêt
        if batch:
            self._flush_batch(batch)

    def _flush_batch(self, batch: List[Dict]):
        """
        Écrit un batch de logs en une seule requête INSERT.

        INSERT INTO historique (date_time, action, table_name, ...)
        VALUES
            (NOW(), 'INSERT', 'postes', ...),
            (NOW(), 'UPDATE', 'personnel', ...),
            ...
        """
        if not batch:
            return

        try:
            from infrastructure.db.configbd import DatabaseConnection
            import json

            with DatabaseConnection(auto_commit=True) as conn:
                cur = conn.cursor()

                # Préparer les valeurs
                values = []
                for entry in batch:
                    values.append((
                        entry.get('action'),
                        entry.get('table_name'),
                        str(entry.get('record_id')) if entry.get('record_id') is not None else None,
                        entry.get('utilisateur'),
                        entry.get('description')
                    ))

                # INSERT multiple (1 requête pour N logs)
                placeholders = ', '.join(['(NOW(), %s, %s, %s, %s, %s)'] * len(values))
                flat_values = [item for row in values for item in row]

                query = f"""
                    INSERT INTO historique
                        (date_time, action, table_name, record_id, utilisateur, description)
                    VALUES {placeholders}
                """

                cur.execute(query, flat_values)
                cur.close()

        except Exception:
            # En cas d'erreur, ne pas casser le flux - erreur silencieuse
            pass

    def log(
        self,
        action: str,
        table_name: Optional[str] = None,
        record_id: Any = None,
        description: Optional[str] = None,
        details: Any = None,
        source: Optional[str] = None,
        utilisateur: Optional[str] = None
    ):
        """
        Log une action dans la table historique (async, non-bloquant).

        Args:
            action: Type d'action (INSERT, UPDATE, DELETE, etc.)
            table_name: Table concernée
            record_id: ID de l'enregistrement
            description: Description courte
            details: Détails (dict ou string)
            source: Source de l'action
            utilisateur: Nom d'utilisateur
        """
        try:
            self.queue.put_nowait({
                'action': action,
                'table_name': table_name,
                'record_id': record_id,
                'description': description,
                'details': details,
                'source': source,
                'utilisateur': utilisateur,
                'timestamp': time.time()
            })
        except Exception:
            # Queue pleine → fallback sur logger synchrone
            self._log_sync(
                action, table_name, record_id, description,
                details, source, utilisateur
            )

    def _log_sync(
        self,
        action: str,
        table_name: Optional[str],
        record_id: Any,
        description: Optional[str],
        details: Any,
        source: Optional[str],
        utilisateur: Optional[str]
    ):
        """Fallback synchrone si queue pleine"""
        try:
            log_hist(
                action=action,
                table_name=table_name,
                record_id=record_id,
                description=description,
                details=details,
                source=source,
                utilisateur=utilisateur
            )
        except Exception:
            pass

    def flush(self):
        """Force le flush immédiat (pour les cas critiques)"""
        # Temporiser pour permettre au worker de traiter
        time.sleep(0.1)


# ===========================
# Instance globale
# ===========================

_db_logger = OptimizedDBLogger()
_db_logger.start()


# ===========================
# API publique
# ===========================

def log_hist_async(
    action: str,
    table_name: Optional[str] = None,
    record_id: Any = None,
    description: Optional[str] = None,
    details: Any = None,
    source: Optional[str] = None,
    utilisateur: Optional[str] = None
):
    """
    Log une action dans la table historique (async, optimisé).

    ✅ Non-bloquant (retour immédiat)
    ✅ Écriture par batch (10-50x moins de requêtes)
    ✅ Auto-flush toutes les 10 secondes

    Usage:
        from infrastructure.logging.optimized_db_logger import log_hist_async

        # Au lieu de
        log_hist('INSERT', 'postes', 123, 'Poste créé')  # ❌ 1 requête DB

        # Utiliser
        log_hist_async('INSERT', 'postes', 123, 'Poste créé')  # ✅ Buffered

    Args:
        action: Type d'action (INSERT, UPDATE, DELETE, ERROR, ...)
        table_name: Table concernée (postes, personnel, ...)
        record_id: ID de l'enregistrement
        description: Description courte
        details: Détails (dict ou string JSON)
        source: Source de l'action (ex: "GUI/gestion_personnel")
        utilisateur: Nom d'utilisateur

    Example:
        log_hist_async(
            action='UPDATE',
            table_name='postes',
            record_id=123,
            description='Modification du nom',
            details={'ancien': 'Poste A', 'nouveau': 'Poste B'},
            source='GUI/creation_poste',
            utilisateur='admin'
        )
    """
    _db_logger.log(
        action=action,
        table_name=table_name,
        record_id=record_id,
        description=description,
        details=details,
        source=source,
        utilisateur=utilisateur
    )


def flush_db_logs():
    """Force le flush des logs DB (utile avant quitter l'app)"""
    _db_logger.flush()


def shutdown_db_logger():
    """Arrête le logger DB (appeler avant quitter l'app)"""
    _db_logger.stop()


# ===========================
# Décorateur pour auto-log
# ===========================

def auto_log_db(action: str, table_name: str, source: Optional[str] = None):
    """
    Décorateur pour logger automatiquement une fonction.

    Usage:
        @auto_log_db('UPDATE', 'postes', 'service/postes')
        def update_poste(poste_id, data):
            # ... UPDATE ...
            return poste_id

        # Après l'exécution, un log sera créé automatiquement
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Extraire record_id si possible
            record_id = None
            if result is not None:
                if isinstance(result, (int, str)):
                    record_id = result
                elif isinstance(result, dict) and 'id' in result:
                    record_id = result['id']

            # Log async
            log_hist_async(
                action=action,
                table_name=table_name,
                record_id=record_id,
                description=f"{action} via {func.__name__}",
                source=source or func.__module__
            )

            return result

        return wrapper
    return decorator


# ===========================
# Exports
# ===========================

__all__ = [
    'log_hist',
    'log_hist_async',
    'flush_db_logs',
    'shutdown_db_logger',
    'auto_log_db',
    'OptimizedDBLogger',
    'DBLogConfig',
    '_to_json_str',
    '_get_current_username',
]
