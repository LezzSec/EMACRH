# -*- coding: utf-8 -*-
"""
Module de gestion des workers DB pour PyQt5.
Permet d'exécuter des requêtes DB en background sans bloquer l'UI.

✅ Utilisation recommandée :
    - Toutes les requêtes DB doivent passer par DbWorker
    - Jamais de DB dans le thread principal (UI)
    - Limiter la concurrence avec QThreadPool configuré

✅ Fonctionnalités :
    - Cancellation logique (ignore résultats si widget détruit)
    - Timeout configurable pour opérations longues
    - Tracking des workers actifs
"""

import traceback
import threading
import time
from typing import Callable, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from weakref import WeakSet
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# Timeout par défaut pour les opérations DB (30 secondes)
DEFAULT_OPERATION_TIMEOUT = 30.0


# ===========================
# Signals
# ===========================

class WorkerSignals(QObject):
    """
    Signaux émis par les workers pour communiquer avec le thread principal.
    """
    # Émis quand le worker termine avec succès
    result = pyqtSignal(object)

    # Émis en cas d'erreur
    error = pyqtSignal(str)

    # Émis pour indiquer la progression (optionnel)
    progress = pyqtSignal(int, str)  # (pourcentage, message)

    # Émis au démarrage du worker
    started = pyqtSignal()

    # Émis à la fin (succès ou échec)
    finished = pyqtSignal()

    # Émis en cas de timeout
    timeout = pyqtSignal()

    # Émis si annulé
    cancelled = pyqtSignal()


# ===========================
# Worker DB générique
# ===========================

class DbWorker(QRunnable):
    """
    Worker générique pour exécuter des opérations DB en background.

    ✅ Utilisation :
        worker = DbWorker(ma_fonction_db, arg1, arg2, kwarg1=val1)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    ✅ Avec cancellation (ignore résultat si widget détruit) :
        worker = DbWorker(ma_fonction_db)
        worker.signals.result.connect(on_success)
        DbThreadPool.start(worker)

        # Plus tard, si l'utilisateur change d'onglet :
        worker.cancel()  # Le résultat sera ignoré

    ✅ Avec timeout :
        worker = DbWorker(ma_fonction_db, timeout=10.0)  # 10 secondes max
        worker.signals.timeout.connect(on_timeout)
        DbThreadPool.start(worker)

    ✅ Avec progress :
        def ma_fonction(progress_callback=None):
            for i in range(100):
                if progress_callback:
                    progress_callback.emit(i, f"Étape {i}/100")
                # ... traitement ...

        worker = DbWorker(ma_fonction)
        worker.signals.progress.connect(on_progress)
        worker.signals.result.connect(on_success)
        DbThreadPool.start(worker)
    """

    # Tracking des workers actifs (pour debug/monitoring)
    _active_workers: WeakSet = WeakSet()
    _workers_lock = threading.Lock()

    def __init__(self, fn: Callable, *args, timeout: Optional[float] = None, **kwargs):
        """
        Args:
            fn: Fonction à exécuter (doit retourner un résultat)
            *args: Arguments positionnels
            timeout: Timeout en secondes (None = pas de timeout)
            **kwargs: Arguments nommés
        """
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.timeout = timeout

        # Support de cancellation
        self._cancelled = False
        self._cancel_lock = threading.Lock()

        # Injecter le signal progress dans kwargs si la fonction l'accepte
        if 'progress_callback' not in self.kwargs:
            self.kwargs['progress_callback'] = self.signals.progress

        # Tracking
        with DbWorker._workers_lock:
            DbWorker._active_workers.add(self)

    def cancel(self):
        """
        Annule le worker (logiquement).
        Le résultat sera ignoré, mais l'opération peut continuer en background.
        Utile quand l'utilisateur change d'onglet / ferme un dialog.
        """
        with self._cancel_lock:
            self._cancelled = True
        logger.debug(f"Worker cancelled: {self.fn.__name__ if hasattr(self.fn, '__name__') else 'anonymous'}")

    def is_cancelled(self) -> bool:
        """Vérifie si le worker a été annulé"""
        with self._cancel_lock:
            return self._cancelled

    def run(self):
        """Exécute la fonction en background"""
        start_time = time.time()

        try:
            self.signals.started.emit()

            # Exécuter la fonction
            result = self.fn(*self.args, **self.kwargs)

            # Vérifier timeout
            elapsed = time.time() - start_time
            if self.timeout and elapsed > self.timeout:
                logger.warning(f"Worker timeout: {elapsed:.1f}s > {self.timeout}s")
                if not self.is_cancelled():
                    self.signals.timeout.emit()
                return

            # Émettre le résultat seulement si non annulé
            if not self.is_cancelled():
                self.signals.result.emit(result)
            else:
                self.signals.cancelled.emit()
                logger.debug("Worker result ignored (cancelled)")

        except Exception as e:
            if not self.is_cancelled():
                error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
                self.signals.error.emit(error_msg)
            else:
                logger.debug(f"Worker error ignored (cancelled): {e}")

        finally:
            self.signals.finished.emit()
            # Cleanup tracking
            with DbWorker._workers_lock:
                DbWorker._active_workers.discard(self)

    @classmethod
    def get_active_count(cls) -> int:
        """Retourne le nombre de workers actifs"""
        with cls._workers_lock:
            return len(cls._active_workers)

    @classmethod
    def cancel_all(cls):
        """Annule tous les workers actifs (utile à la fermeture de l'app)"""
        with cls._workers_lock:
            for worker in list(cls._active_workers):
                worker.cancel()
        logger.info("All active workers cancelled")


# ===========================
# Worker avec résultat directement passé au callback
# ===========================

class SimpleDbWorker(QRunnable):
    """
    Version simplifiée de DbWorker pour les cas simples.
    Le résultat est directement passé au callback fourni.

    ✅ Utilisation (plus concis) :
        def on_success(result):
            print(f"Résultat : {result}")

        SimpleDbWorker(ma_fonction_db, on_success, arg1, arg2)

    ⚠️ Note: Pour les cas nécessitant cancellation/timeout, utiliser DbWorker.
    """

    def __init__(self, fn: Callable, on_result: Optional[Callable] = None,
                 on_error: Optional[Callable] = None, *args, **kwargs):
        """
        Args:
            fn: Fonction à exécuter
            on_result: Callback appelé avec le résultat
            on_error: Callback appelé en cas d'erreur
            *args: Arguments pour fn
            **kwargs: Arguments nommés pour fn
        """
        super().__init__()
        self.fn = fn
        self.on_result = on_result
        self.on_error = on_error
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Connecter automatiquement les callbacks
        if on_result:
            self.signals.result.connect(on_result)
        if on_error:
            self.signals.error.connect(on_error)

        # Auto-start via DbThreadPool (utilise le pool configuré)
        DbThreadPool.start(self)

    def run(self):
        """Exécute la fonction en background"""
        try:
            self.signals.started.emit()
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.signals.error.emit(error_msg)
        finally:
            self.signals.finished.emit()


# ===========================
# Gestionnaire de pool de threads
# ===========================

class DbThreadPool:
    """
    Gestionnaire centralisé du pool de threads pour les opérations DB.

    ✅ Configure la concurrence maximale en fonction du pool MySQL
    ✅ Fournit des méthodes helper pour lancer des workers
    """

    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DbThreadPool, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialise le pool de threads"""
        DbThreadPool._pool = QThreadPool.globalInstance()

        # IMPORTANT : Limiter la concurrence en cohérence avec le pool MySQL
        # Si pool MySQL = 5, on limite à 5 threads DB maximum
        # Cela évite d'avoir 10 workers qui attendent une connexion
        from infrastructure.db.configbd import _get_db_config
        try:
            config = _get_db_config()
            pool_size = config.get('pool_size', 5)
            # On met légèrement moins pour laisser de la marge
            max_threads = max(2, pool_size - 1)
            DbThreadPool._pool.setMaxThreadCount(max_threads)
            logger.debug(f"DbThreadPool configuré : {max_threads} threads max (pool MySQL: {pool_size})")
        except Exception as e:
            logger.warning(f"Impossible de configurer DbThreadPool : {e}")
            # Par défaut, limiter à 4 threads
            DbThreadPool._pool.setMaxThreadCount(4)

    @classmethod
    def get_pool(cls) -> QThreadPool:
        """Retourne le pool de threads"""
        if cls._instance is None:
            cls()
        return cls._pool

    @classmethod
    def start(cls, worker: QRunnable):
        """
        Lance un worker dans le pool.

        Args:
            worker: Instance de DbWorker ou QRunnable
        """
        pool = cls.get_pool()
        pool.start(worker)

    @classmethod
    def run_async(cls, fn: Callable, on_result: Optional[Callable] = None,
                  on_error: Optional[Callable] = None,
                  on_timeout: Optional[Callable] = None,
                  timeout: Optional[float] = None,
                  *args, **kwargs) -> DbWorker:
        """
        Helper pour lancer une fonction DB en async.

        Args:
            fn: Fonction à exécuter
            on_result: Callback pour le résultat
            on_error: Callback pour les erreurs
            on_timeout: Callback si timeout dépassé
            timeout: Timeout en secondes (None = pas de timeout)
            *args, **kwargs: Arguments pour fn

        Returns:
            Le worker créé (utile pour annuler si besoin)

        Example:
            def fetch_personnel():
                from infrastructure.db.query_executor import QueryExecutor
                return QueryExecutor.fetch_all(
                    "SELECT * FROM personnel WHERE statut = 'ACTIF'",
                    dictionary=True
                )

            def on_success(results):
                print(f"Chargé {len(results)} personnes")

            # Avec timeout de 5 secondes
            worker = DbThreadPool.run_async(
                fetch_personnel, on_success,
                timeout=5.0, on_timeout=lambda: print("Trop lent!")
            )

            # Plus tard, pour annuler :
            worker.cancel()
        """
        worker = DbWorker(fn, *args, timeout=timeout, **kwargs)

        if on_result:
            worker.signals.result.connect(on_result)
        if on_error:
            worker.signals.error.connect(on_error)
        if on_timeout:
            worker.signals.timeout.connect(on_timeout)

        cls.start(worker)
        return worker

    @classmethod
    def get_active_thread_count(cls) -> int:
        """Retourne le nombre de threads actuellement actifs"""
        pool = cls.get_pool()
        return pool.activeThreadCount()

    @classmethod
    def get_max_thread_count(cls) -> int:
        """Retourne le nombre maximum de threads"""
        pool = cls.get_pool()
        return pool.maxThreadCount()

    @classmethod
    def wait_for_done(cls, timeout_ms: int = 30000) -> bool:
        """
        Attend que tous les workers soient terminés.

        Args:
            timeout_ms: Timeout en millisecondes

        Returns:
            True si tous les workers sont terminés, False si timeout
        """
        pool = cls.get_pool()
        return pool.waitForDone(timeout_ms)


# ===========================
# Fonctions helper pour simplifier l'usage
# ===========================

def run_in_background(fn: Callable, on_result: Optional[Callable] = None,
                      on_error: Optional[Callable] = None,
                      on_timeout: Optional[Callable] = None,
                      timeout: Optional[float] = None,
                      *args, **kwargs) -> DbWorker:
    """
    Fonction helper pour lancer une opération DB en background.

    C'est un alias de DbThreadPool.run_async() pour simplifier l'import.

    Example:
        from gui.workers.db_worker import run_in_background

        def fetch_data():
            # ... requête DB ...
            return results

        def on_success(results):
            print(f"Reçu {len(results)} résultats")

        # Simple
        run_in_background(fetch_data, on_success)

        # Avec timeout
        worker = run_in_background(fetch_data, on_success, timeout=5.0)

        # Annuler si l'utilisateur ferme le dialog
        worker.cancel()
    """
    return DbThreadPool.run_async(fn, on_result, on_error, on_timeout, timeout, *args, **kwargs)


def show_loading_placeholder(widget, text: str = "Chargement..."):
    """
    Helper pour afficher un placeholder de chargement dans un widget.

    Args:
        widget: QLabel, QListWidget, etc.
        text: Texte à afficher
    """
    from PyQt5.QtWidgets import QLabel, QListWidget

    if isinstance(widget, QLabel):
        widget.setText(f"⏳ {text}")
        widget.setStyleSheet("color: #999; font-style: italic;")
    elif isinstance(widget, QListWidget):
        widget.clear()
        widget.addItem(f"⏳ {text}")


def show_error_placeholder(widget, error_msg: str):
    """
    Helper pour afficher une erreur dans un widget.

    Args:
        widget: QLabel, QListWidget, etc.
        error_msg: Message d'erreur
    """
    from PyQt5.QtWidgets import QLabel, QListWidget

    if isinstance(widget, QLabel):
        widget.setText(f"[ERREUR] {error_msg}")
        widget.setStyleSheet("color: #d32f2f; font-style: italic;")
    elif isinstance(widget, QListWidget):
        widget.clear()
        widget.addItem(f"[ERREUR] {error_msg}")


# ===========================
# Décorateur pour fonctions DB
# ===========================

def async_db_operation(on_result: Optional[Callable] = None,
                       on_error: Optional[Callable] = None):
    """
    Décorateur pour transformer une fonction DB en opération async.

    Example:
        @async_db_operation(on_result=lambda x: print(f"Résultat: {x}"))
        def fetch_personnel():
            from infrastructure.db.query_executor import QueryExecutor
            return QueryExecutor.fetch_all(
                "SELECT * FROM personnel",
                dictionary=True
            )

        # Appel direct lance en background
        fetch_personnel()
    """
    def decorator(fn: Callable):
        def wrapper(*args, **kwargs):
            return run_in_background(fn, on_result, on_error, *args, **kwargs)
        return wrapper
    return decorator


# ===========================
# Debug / Monitoring
# ===========================

def get_pool_status() -> dict:
    """Retourne l'état actuel du pool de threads (debug)"""
    return {
        "active_threads": DbThreadPool.get_active_thread_count(),
        "max_threads": DbThreadPool.get_max_thread_count(),
        "active_workers": DbWorker.get_active_count()
    }


def cancel_all_workers():
    """Annule tous les workers actifs (utile à la fermeture de l'app)"""
    DbWorker.cancel_all()
