# -*- coding: utf-8 -*-
"""
Système de cache mémoire pour EMAC.
Permet de stocker en mémoire des données fréquemment utilisées avec TTL.

✅ Utilisation :
    - Postes (rarement modifiés)
    - Permissions / User (changent peu)
    - Listes statiques (rôles, types, etc.)
    - État des écrans (dialog state)

✅ Avantages :
    - Évite les requêtes DB répétées
    - Gains 100-1000x sur données cachées
    - TTL automatique (expiration)
    - Invalidation propre
"""

import time
from typing import Any, Optional, Callable, Dict
from dataclasses import dataclass
from datetime import datetime
from threading import RLock


# ===========================
# Cache Entry
# ===========================

@dataclass
class CacheEntry:
    """Entrée de cache avec métadonnées"""
    key: str
    value: Any
    timestamp: float  # time.time()
    ttl: Optional[float]  # TTL en secondes (None = infini)
    hits: int = 0  # Nombre d'accès

    def is_expired(self) -> bool:
        """Vérifie si l'entrée a expiré"""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def get_age(self) -> float:
        """Retourne l'âge de l'entrée en secondes"""
        return time.time() - self.timestamp


# ===========================
# Cache Manager
# ===========================

class CacheManager:
    """
    Gestionnaire de cache mémoire thread-safe avec TTL.

    ✅ Features :
        - TTL par clé
        - Invalidation manuelle ou automatique
        - Thread-safe (RLock)
        - Statistiques (hits, misses)
        - Namespaces (pour séparer les types de données)

    Usage :
        cache = CacheManager.get_instance()

        # Stocker
        cache.set('postes', postes_data, ttl=300)  # 5 minutes

        # Récupérer
        postes = cache.get('postes')
        if postes is None:
            # Cache miss, charger depuis DB
            postes = load_from_db()
            cache.set('postes', postes, ttl=300)

        # Invalider
        cache.invalidate('postes')
    """

    _instance = None
    _lock = RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CacheManager, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialise le cache"""
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
        self._namespaces: Dict[str, set] = {}  # namespace -> set de clés

    @classmethod
    def get_instance(cls) -> 'CacheManager':
        """Retourne l'instance singleton"""
        if cls._instance is None:
            cls()
        return cls._instance

    def set(self, key: str, value: Any, ttl: Optional[float] = None, namespace: Optional[str] = None):
        """
        Stocke une valeur dans le cache.

        Args:
            key: Clé unique
            value: Valeur à stocker
            ttl: Durée de vie en secondes (None = infini)
            namespace: Namespace optionnel pour regroupement
        """
        with self._lock:
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl,
                hits=0
            )
            self._cache[key] = entry

            # Ajouter au namespace
            if namespace:
                if namespace not in self._namespaces:
                    self._namespaces[namespace] = set()
                self._namespaces[namespace].add(key)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur du cache.

        Args:
            key: Clé
            default: Valeur par défaut si absent ou expiré

        Returns:
            La valeur cachée ou default
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return default

            # Vérifier expiration
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return default

            # Hit !
            entry.hits += 1
            self._hits += 1
            return entry.value

    def get_or_set(self, key: str, factory: Callable, ttl: Optional[float] = None,
                   namespace: Optional[str] = None) -> Any:
        """
        Récupère une valeur du cache, ou la crée si absente.

        Args:
            key: Clé
            factory: Fonction pour créer la valeur si absente
            ttl: TTL en secondes
            namespace: Namespace optionnel

        Returns:
            La valeur (cachée ou nouvellement créée)

        Example:
            def load_postes():
                # ... requête DB ...
                return postes

            postes = cache.get_or_set('postes', load_postes, ttl=300)
        """
        value = self.get(key)
        if value is not None:
            return value

        # Cache miss, créer la valeur
        value = factory()
        self.set(key, value, ttl=ttl, namespace=namespace)
        return value

    def invalidate(self, key: str):
        """
        Invalide une clé du cache.

        Args:
            key: Clé à invalider
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

                # Retirer des namespaces
                for ns_keys in self._namespaces.values():
                    ns_keys.discard(key)

    def invalidate_namespace(self, namespace: str):
        """
        Invalide toutes les clés d'un namespace.

        Args:
            namespace: Namespace à invalider

        Example:
            # Invalider toutes les permissions
            cache.invalidate_namespace('permissions')
        """
        with self._lock:
            if namespace in self._namespaces:
                keys = list(self._namespaces[namespace])
                for key in keys:
                    if key in self._cache:
                        del self._cache[key]
                self._namespaces[namespace].clear()

    def invalidate_pattern(self, pattern: str):
        """
        Invalide toutes les clés contenant un pattern.

        Args:
            pattern: Pattern à chercher (substring)

        Example:
            # Invalider tous les caches d'un utilisateur
            cache.invalidate_pattern('user:123')
        """
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]

                # Retirer des namespaces
                for ns_keys in self._namespaces.values():
                    ns_keys.discard(key)

    def clear(self):
        """Vide complètement le cache"""
        with self._lock:
            self._cache.clear()
            self._namespaces.clear()
            self._hits = 0
            self._misses = 0

    def cleanup_expired(self):
        """
        Nettoie les entrées expirées.
        Appelé automatiquement si nécessaire, mais peut être appelé manuellement.
        """
        with self._lock:
            expired_keys = [k for k, e in self._cache.items() if e.is_expired()]
            for key in expired_keys:
                del self._cache[key]

                # Retirer des namespaces
                for ns_keys in self._namespaces.values():
                    ns_keys.discard(key)

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache.

        Returns:
            Dict avec hits, misses, hit_rate, size, etc.
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0

            return {
                'hits': self._hits,
                'misses': self._misses,
                'total_requests': total,
                'hit_rate': f"{hit_rate:.1f}%",
                'size': len(self._cache),
                'namespaces': len(self._namespaces),
            }

    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retourne les infos d'une entrée du cache.

        Returns:
            Dict avec timestamp, age, hits, ttl, etc. ou None si absent
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            return {
                'key': entry.key,
                'timestamp': datetime.fromtimestamp(entry.timestamp).isoformat(),
                'age_seconds': entry.get_age(),
                'ttl_seconds': entry.ttl,
                'hits': entry.hits,
                'is_expired': entry.is_expired(),
                'value_type': type(entry.value).__name__,
                'value_size': len(entry.value) if hasattr(entry.value, '__len__') else None,
            }

    def list_keys(self, namespace: Optional[str] = None) -> list:
        """
        Liste toutes les clés du cache.

        Args:
            namespace: Si fourni, liste uniquement les clés de ce namespace

        Returns:
            Liste des clés
        """
        with self._lock:
            if namespace:
                return list(self._namespaces.get(namespace, set()))
            return list(self._cache.keys())


# ===========================
# Décorateur @cached
# ===========================

def cached(ttl: Optional[float] = None, namespace: Optional[str] = None, key_prefix: str = ""):
    """
    Décorateur pour cacher automatiquement le résultat d'une fonction.

    Args:
        ttl: TTL en secondes
        namespace: Namespace optionnel
        key_prefix: Préfixe pour la clé (par défaut: nom de la fonction)

    Example:
        @cached(ttl=300, namespace='postes')
        def get_all_postes():
            with DatabaseCursor() as cur:
                cur.execute("SELECT * FROM postes")
                return cur.fetchall()

        # Premier appel → DB query
        postes = get_all_postes()

        # Appels suivants dans les 5 minutes → cache
        postes = get_all_postes()  # Instantané !
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            cache = CacheManager.get_instance()

            # Générer la clé du cache
            key = f"{key_prefix or func.__name__}"

            # Ajouter les args dans la clé si présents
            if args:
                key += f":{':'.join(str(a) for a in args)}"
            if kwargs:
                key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"

            # Récupérer depuis le cache
            result = cache.get(key)
            if result is not None:
                return result

            # Cache miss, exécuter la fonction
            result = func(*args, **kwargs)
            cache.set(key, result, ttl=ttl, namespace=namespace)
            return result

        return wrapper
    return decorator


# ===========================
# Fonctions helper
# ===========================

def get_cache() -> CacheManager:
    """
    Raccourci pour obtenir l'instance du cache.

    Returns:
        L'instance CacheManager
    """
    return CacheManager.get_instance()


def invalidate_on_change(namespace: str):
    """
    Décorateur pour invalider un namespace après l'exécution d'une fonction.
    Utile pour les fonctions de modification (INSERT, UPDATE, DELETE).

    Example:
        @invalidate_on_change('postes')
        def update_poste(poste_id, data):
            # ... UPDATE poste ...
            pass

        # Après l'exécution, le cache 'postes' est invalidé
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Invalider après l'exécution
            cache = CacheManager.get_instance()
            cache.invalidate_namespace(namespace)
            return result
        return wrapper
    return decorator


def print_cache_stats():
    """Affiche les statistiques du cache (debug)"""
    cache = CacheManager.get_instance()
    stats = cache.get_stats()

    print("="*60)
    print("📊 Cache Statistics")
    print("="*60)
    print(f"Hits          : {stats['hits']}")
    print(f"Misses        : {stats['misses']}")
    print(f"Total requests: {stats['total_requests']}")
    print(f"Hit rate      : {stats['hit_rate']}")
    print(f"Size          : {stats['size']} entries")
    print(f"Namespaces    : {stats['namespaces']}")
    print("="*60)


# ===========================
# TTL Constants (recommandés)
# ===========================

class CacheTTL:
    """Constantes de TTL recommandées"""
    # Très courte durée (données volatiles)
    VERY_SHORT = 30  # 30 secondes

    # Courte durée (données fréquemment modifiées)
    SHORT = 60  # 1 minute
    MINUTE_5 = 300  # 5 minutes

    # Durée moyenne (données modifiées occasionnellement)
    MEDIUM = 600  # 10 minutes
    MINUTE_30 = 1800  # 30 minutes

    # Longue durée (données rarement modifiées)
    LONG = 3600  # 1 heure
    HOUR_6 = 21600  # 6 heures

    # Très longue durée (données quasi-statiques)
    VERY_LONG = 86400  # 24 heures
    WEEK = 604800  # 1 semaine

    # Infini (jamais expiré, nécessite invalidation manuelle)
    INFINITE = None
