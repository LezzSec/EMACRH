# -*- coding: utf-8 -*-
"""
Système de monitoring des performances EMAC.
Mesure et alerte sur les opérations lentes (> seuil configuré).

Fonctionnalités:
- Mesure temps de login
- Mesure temps des requêtes DB clés
- Mesure temps d'ouverture des dialogs
- Alertes si > seuil (200ms par défaut)
- Statistiques agrégées
- Export des métriques

Inspiré des pratiques des "grosses boîtes" (Google, Facebook, etc.)
"""

import time
import threading
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from functools import wraps


# ===========================
# Configuration
# ===========================

class PerformanceConfig:
    """Configuration du monitoring"""

    # Seuil d'alerte (ms)
    SLOW_THRESHOLD_MS = 200

    # Seuils par type d'opération
    THRESHOLDS = {
        'login': 500,  # Login peut être plus lent
        'query': 100,  # Requêtes DB doivent être rapides
        'dialog': 300,  # Ouverture dialog
        'cache': 10,  # Cache hit doit être instantané
        'export': 2000,  # Export peut prendre du temps
    }

    # Activer/désactiver le monitoring
    ENABLED = True

    # Activer logs console
    CONSOLE_LOGS = True

    # Activer logs fichier
    FILE_LOGS = True

    # Collecter statistiques
    COLLECT_STATS = True


# ===========================
# Mesure de performance
# ===========================

@dataclass
class PerformanceMetric:
    """Métrique de performance individuelle"""
    operation: str
    category: str  # login, query, dialog, etc.
    duration_ms: float
    threshold_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Optional[Dict] = None
    is_slow: bool = False

    def __post_init__(self):
        self.is_slow = self.duration_ms > self.threshold_ms


# ===========================
# Collecteur de métriques
# ===========================

class PerformanceMonitor:
    """
    Singleton qui collecte et agrège les métriques de performance.

    Thread-safe.
    Statistiques en temps réel.
    Alertes automatiques.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PerformanceMonitor, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.metrics: List[PerformanceMetric] = []
        self.stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_ms': 0,
            'min_ms': float('inf'),
            'max_ms': 0,
            'slow_count': 0
        })
        self.metrics_lock = threading.Lock()

    def record(
        self,
        operation: str,
        duration_ms: float,
        category: str = 'other',
        details: Optional[Dict] = None
    ):
        """
        Enregistre une métrique de performance.

        Args:
            operation: Nom de l'opération (ex: "Login", "Load Personnel")
            duration_ms: Durée en millisecondes
            category: Catégorie (login, query, dialog, cache, export)
            details: Détails additionnels
        """
        if not PerformanceConfig.ENABLED:
            return

        # Déterminer le seuil
        threshold = PerformanceConfig.THRESHOLDS.get(
            category,
            PerformanceConfig.SLOW_THRESHOLD_MS
        )

        # Créer la métrique
        metric = PerformanceMetric(
            operation=operation,
            category=category,
            duration_ms=duration_ms,
            threshold_ms=threshold,
            details=details
        )

        # Enregistrer
        with self.metrics_lock:
            self.metrics.append(metric)

            # Mettre à jour les stats
            if PerformanceConfig.COLLECT_STATS:
                self._update_stats(metric)

        # Alerter si lent
        if metric.is_slow:
            self._alert_slow(metric)

    def _update_stats(self, metric: PerformanceMetric):
        """Met à jour les statistiques agrégées"""
        key = f"{metric.category}:{metric.operation}"
        stats = self.stats[key]

        stats['count'] += 1
        stats['total_ms'] += metric.duration_ms
        stats['min_ms'] = min(stats['min_ms'], metric.duration_ms)
        stats['max_ms'] = max(stats['max_ms'], metric.duration_ms)
        if metric.is_slow:
            stats['slow_count'] += 1

    def _alert_slow(self, metric: PerformanceMetric):
        """Alerte sur une opération lente"""
        message = (
            f"[SLOW] {metric.category.upper()}: "
            f"{metric.operation} took {metric.duration_ms:.1f}ms "
            f"(threshold: {metric.threshold_ms}ms)"
        )

        # Console
        if PerformanceConfig.CONSOLE_LOGS:
            print(message)

        # Fichier log
        if PerformanceConfig.FILE_LOGS:
            try:
                from infrastructure.logging.logging_config import get_logger
                logger = get_logger('performance')
                logger.warning(message)
            except Exception:
                pass

    def get_stats(self, category: Optional[str] = None) -> Dict:
        """
        Retourne les statistiques agrégées.

        Args:
            category: Filtrer par catégorie (None = toutes)

        Returns:
            Dict avec les stats par opération
        """
        with self.metrics_lock:
            if category:
                return {
                    k: v for k, v in self.stats.items()
                    if k.startswith(f"{category}:")
                }
            return dict(self.stats)

    def get_summary(self) -> Dict:
        """Retourne un résumé global des performances"""
        with self.metrics_lock:
            total_ops = len(self.metrics)
            slow_ops = sum(1 for m in self.metrics if m.is_slow)

            if total_ops == 0:
                return {
                    'total_operations': 0,
                    'slow_operations': 0,
                    'slow_percentage': 0
                }

            return {
                'total_operations': total_ops,
                'slow_operations': slow_ops,
                'slow_percentage': (slow_ops / total_ops) * 100,
                'by_category': self._summary_by_category()
            }

    def _summary_by_category(self) -> Dict:
        """Résumé par catégorie"""
        summary = defaultdict(lambda: {
            'count': 0,
            'avg_ms': 0,
            'slow_count': 0
        })

        for metric in self.metrics:
            cat = metric.category
            summary[cat]['count'] += 1
            if metric.is_slow:
                summary[cat]['slow_count'] += 1

        # Calculer les moyennes
        for key, stats in self.stats.items():
            category = key.split(':')[0]
            if stats['count'] > 0:
                avg = stats['total_ms'] / stats['count']
                summary[category]['avg_ms'] = avg

        return dict(summary)

    def clear(self):
        """Vide toutes les métriques (utile pour tests)"""
        with self.metrics_lock:
            self.metrics.clear()
            self.stats.clear()


# ===========================
# Instance globale
# ===========================

_monitor = PerformanceMonitor()


# ===========================
# Décorateurs de monitoring
# ===========================

def monitor_performance(
    operation: Optional[str] = None,
    category: str = 'other',
    threshold_ms: Optional[float] = None
):
    """
    Décorateur pour monitorer automatiquement une fonction.

    Usage:
        @monitor_performance('Login', category='login')
        def login(username, password):
            # ...
            return user

    Args:
        operation: Nom de l'opération (None = nom fonction)
        category: Catégorie (login, query, dialog, etc.)
        threshold_ms: Seuil personnalisé (None = utiliser config)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not PerformanceConfig.ENABLED:
                return func(*args, **kwargs)

            op_name = operation or func.__name__

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Override threshold si fourni
                if threshold_ms:
                    old_threshold = PerformanceConfig.THRESHOLDS.get(category)
                    PerformanceConfig.THRESHOLDS[category] = threshold_ms

                _monitor.record(op_name, duration_ms, category)

                # Restaurer threshold
                if threshold_ms and old_threshold:
                    PerformanceConfig.THRESHOLDS[category] = old_threshold

        return wrapper
    return decorator


def monitor_query(query_name: Optional[str] = None):
    """
    Décorateur spécialisé pour les requêtes DB.

    Usage:
        @monitor_query('Load Personnel')
        def load_personnel():
            with DatabaseCursor() as cur:
                cur.execute("SELECT * FROM personnel")
                return cur.fetchall()
    """
    return monitor_performance(query_name, category='query', threshold_ms=100)


def monitor_dialog(dialog_name: Optional[str] = None):
    """
    Décorateur spécialisé pour l'ouverture de dialogs.

    Usage:
        @monitor_dialog('Personnel Dialog')
        def open_personnel_dialog(self):
            dialog = GestionPersonnelDialog(self)
            dialog.exec_()
    """
    return monitor_performance(dialog_name, category='dialog', threshold_ms=300)


# ===========================
# Context Manager
# ===========================

class PerformanceTimer:
    """
    Context manager pour mesurer des blocs de code.

    Usage:
        with PerformanceTimer('Load Data', category='query'):
            data = load_data_from_db()
    """

    def __init__(
        self,
        operation: str,
        category: str = 'other',
        details: Optional[Dict] = None
    ):
        self.operation = operation
        self.category = category
        self.details = details
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        _monitor.record(
            self.operation,
            duration_ms,
            self.category,
            self.details
        )
        return False


# ===========================
# Helpers spécialisés
# ===========================

def monitor_login_time(func: Callable) -> Callable:
    """
    Monitore spécifiquement le temps de login.

    Usage:
        @monitor_login_time
        def authenticate(username, password):
            # ...
            return user
    """
    return monitor_performance('Login', category='login', threshold_ms=500)(func)


def measure_query_time(query_name: str) -> PerformanceTimer:
    """
    Mesure le temps d'une requête DB.

    Usage:
        with measure_query_time('Load Personnel'):
            cur.execute("SELECT * FROM personnel")
            result = cur.fetchall()
    """
    return PerformanceTimer(query_name, category='query')


def measure_dialog_time(dialog_name: str) -> PerformanceTimer:
    """
    Mesure le temps d'ouverture d'un dialog.

    Usage:
        with measure_dialog_time('Personnel Dialog'):
            dialog = GestionPersonnelDialog(self)
            dialog.exec_()
    """
    return PerformanceTimer(dialog_name, category='dialog')


# ===========================
# Rapport de performance
# ===========================

def print_performance_report():
    """Affiche un rapport de performance dans la console"""
    summary = _monitor.get_summary()

    print("\n" + "=" * 80)
    print("RAPPORT DE PERFORMANCE EMAC")
    print("=" * 80)
    print(f"Total opérations      : {summary['total_operations']}")
    print(f"Opérations lentes     : {summary['slow_operations']}")
    print(f"Pourcentage lent      : {summary['slow_percentage']:.1f}%")
    print()

    print("Par catégorie:")
    print("-" * 80)
    for category, stats in summary.get('by_category', {}).items():
        print(f"  {category:15} : {stats['count']:4} ops, "
              f"avg {stats['avg_ms']:6.1f}ms, "
              f"{stats['slow_count']:3} slow")

    print("=" * 80 + "\n")


def export_performance_stats(filename: str = 'performance_stats.csv'):
    """
    Exporte les statistiques dans un fichier CSV.

    Args:
        filename: Nom du fichier de sortie
    """
    import csv
    from infrastructure.config.app_paths import get_exports_dir

    stats = _monitor.get_stats()

    # Dossier exports (créé uniquement lors de l'export explicite)
    exports_dir = get_exports_dir(create=True)

    filepath = exports_dir / filename

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Category', 'Operation', 'Count', 'Avg (ms)',
            'Min (ms)', 'Max (ms)', 'Slow Count'
        ])

        # Données
        for key, stat in sorted(stats.items()):
            category, operation = key.split(':', 1)
            avg_ms = stat['total_ms'] / stat['count'] if stat['count'] > 0 else 0

            writer.writerow([
                category,
                operation,
                stat['count'],
                f"{avg_ms:.2f}",
                f"{stat['min_ms']:.2f}",
                f"{stat['max_ms']:.2f}",
                stat['slow_count']
            ])

    print(f"Statistiques exportées: {filepath}")


# ===========================
# API publique
# ===========================

def record_metric(operation: str, duration_ms: float, category: str = 'other', details: Optional[Dict] = None):
    """Enregistre une métrique manuellement"""
    _monitor.record(operation, duration_ms, category, details)


def get_stats(category: Optional[str] = None) -> Dict:
    """Retourne les statistiques"""
    return _monitor.get_stats(category)


def get_summary() -> Dict:
    """Retourne le résumé"""
    return _monitor.get_summary()


def clear_metrics():
    """Vide les métriques"""
    _monitor.clear()


def enable_monitoring():
    """Active le monitoring"""
    PerformanceConfig.ENABLED = True


def disable_monitoring():
    """Désactive le monitoring"""
    PerformanceConfig.ENABLED = False


def set_threshold(category: str, threshold_ms: float):
    """Configure un seuil personnalisé"""
    PerformanceConfig.THRESHOLDS[category] = threshold_ms


# ===========================
# Exports
# ===========================

__all__ = [
    # Classes
    'PerformanceMonitor',
    'PerformanceTimer',
    'PerformanceConfig',
    'PerformanceMetric',

    # Décorateurs
    'monitor_performance',
    'monitor_query',
    'monitor_dialog',
    'monitor_login_time',

    # Context managers
    'measure_query_time',
    'measure_dialog_time',

    # Helpers
    'record_metric',
    'get_stats',
    'get_summary',
    'clear_metrics',
    'enable_monitoring',
    'disable_monitoring',
    'set_threshold',

    # Rapports
    'print_performance_report',
    'export_performance_stats',
]
