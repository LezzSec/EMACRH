# -*- coding: utf-8 -*-
"""
Module de gestion des workers DB pour PyQt5.
Permet d'exécuter des requêtes DB en background sans bloquer l'UI.

✅ Utilisation recommandée :
    - Toutes les requêtes DB doivent passer par DbWorker
    - Jamais de DB dans le thread principal (UI)
    - Limiter la concurrence avec QThreadPool configuré
"""

import traceback
from typing import Callable, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool


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
        QThreadPool.globalInstance().start(worker)

    ✅ Avec progress :
        def ma_fonction(progress_callback=None):
            for i in range(100):
                if progress_callback:
                    progress_callback.emit(i, f"Étape {i}/100")
                # ... traitement ...

        worker = DbWorker(ma_fonction)
        worker.signals.progress.connect(on_progress)
        worker.signals.result.connect(on_success)
        QThreadPool.globalInstance().start(worker)
    """

    def __init__(self, fn: Callable, *args, **kwargs):
        """
        Args:
            fn: Fonction à exécuter (doit retourner un résultat)
            *args: Arguments positionnels
            **kwargs: Arguments nommés
        """
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Injecter le signal progress dans kwargs si la fonction l'accepte
        if 'progress_callback' not in self.kwargs:
            self.kwargs['progress_callback'] = self.signals.progress

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

        # Auto-start dans le pool global
        QThreadPool.globalInstance().start(self)

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
        from core.db.configbd import _get_db_config
        try:
            config = _get_db_config()
            pool_size = config.get('pool_size', 5)
            # On met légèrement moins pour laisser de la marge
            max_threads = max(2, pool_size - 1)
            DbThreadPool._pool.setMaxThreadCount(max_threads)
            print(f"[OK] DbThreadPool configure : {max_threads} threads max (pool MySQL: {pool_size})")
        except Exception as e:
            print(f"[WARN] Impossible de configurer DbThreadPool : {e}")
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
                  on_error: Optional[Callable] = None, *args, **kwargs) -> DbWorker:
        """
        Helper pour lancer une fonction DB en async.

        Args:
            fn: Fonction à exécuter
            on_result: Callback pour le résultat
            on_error: Callback pour les erreurs
            *args, **kwargs: Arguments pour fn

        Returns:
            Le worker créé (utile pour connecter plus de signaux si besoin)

        Example:
            def fetch_personnel():
                from core.db.configbd import DatabaseCursor
                with DatabaseCursor(dictionary=True) as cur:
                    cur.execute("SELECT * FROM personnel WHERE statut = 'ACTIF'")
                    return cur.fetchall()

            def on_success(results):
                print(f"Chargé {len(results)} personnes")

            DbThreadPool.run_async(fetch_personnel, on_success)
        """
        worker = DbWorker(fn, *args, **kwargs)

        if on_result:
            worker.signals.result.connect(on_result)
        if on_error:
            worker.signals.error.connect(on_error)

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
                      on_error: Optional[Callable] = None, *args, **kwargs) -> DbWorker:
    """
    Fonction helper pour lancer une opération DB en background.

    C'est un alias de DbThreadPool.run_async() pour simplifier l'import.

    Example:
        from core.gui.db_worker import run_in_background

        def fetch_data():
            # ... requête DB ...
            return results

        def on_success(results):
            print(f"Reçu {len(results)} résultats")

        run_in_background(fetch_data, on_success)
    """
    return DbThreadPool.run_async(fn, on_result, on_error, *args, **kwargs)


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
            with DatabaseCursor(dictionary=True) as cur:
                cur.execute("SELECT * FROM personnel")
                return cur.fetchall()

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

def print_pool_status():
    """Affiche l'état actuel du pool de threads (debug)"""
    print("="*60)
    print("[DEBUG] DbThreadPool Status")
    print("="*60)
    print(f"Threads actifs : {DbThreadPool.get_active_thread_count()}")
    print(f"Threads max    : {DbThreadPool.get_max_thread_count()}")
    print("="*60)
