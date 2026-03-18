# -*- coding: utf-8 -*-
"""
Cache EMAC - Wrappers spécifiques pour EMAC.
Fournit des fonctions de cache pour les cas d'usage courants.
"""

from typing import Optional, List, Dict, Any
from core.utils.cache import CacheManager, CacheTTL, cached


# ===========================
# Cache Postes
# ===========================

@cached(ttl=CacheTTL.MEDIUM, namespace='postes', key_prefix='postes:all')
def get_cached_postes() -> List[Dict]:
    """
    Retourne tous les postes depuis le cache ou DB.

    TTL : 10 minutes (les postes changent rarement)

    Returns:
        Liste des postes avec leurs infos
    """
    from core.db.configbd import DatabaseCursor

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT p.id, p.poste_code, p.nom, p.atelier_id, p.statut,
                   a.nom as atelier_nom
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            WHERE p.statut = 'ACTIF'
            ORDER BY p.poste_code
        """)
        return cur.fetchall()


@cached(ttl=CacheTTL.MEDIUM, namespace='postes', key_prefix='postes:actifs')
def get_cached_postes_actifs() -> List[Dict]:
    """
    Retourne les postes actifs depuis le cache ou DB.

    TTL : 10 minutes

    Returns:
        Liste des postes actifs
    """
    from core.db.configbd import DatabaseCursor

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT id, poste_code, nom, atelier_id
            FROM postes
            WHERE statut = 'ACTIF'
            ORDER BY poste_code
        """)
        return cur.fetchall()


@cached(ttl=CacheTTL.MEDIUM, namespace='postes', key_prefix='poste:by_id')
def get_cached_poste_by_id(poste_id: int) -> Optional[Dict]:
    """
    Retourne un poste par ID depuis le cache ou DB.

    Args:
        poste_id: ID du poste

    Returns:
        Dictionnaire du poste ou None
    """
    from core.db.configbd import DatabaseCursor

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT p.id, p.poste_code, p.nom, p.atelier_id, p.statut,
                   a.nom as atelier_nom
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            WHERE p.id = %s
        """, (poste_id,))
        return cur.fetchone()


def invalidate_postes_cache():
    """Invalide tout le cache des postes"""
    cache = CacheManager.get_instance()
    cache.invalidate_namespace('postes')


# ===========================
# Cache Permissions / User
# ===========================

@cached(ttl=CacheTTL.SHORT, namespace='permissions', key_prefix='user:current')
def get_cached_current_user() -> Optional[Dict]:
    """
    Retourne l'utilisateur courant depuis le cache ou session.

    TTL : 1 minute (pour détecter changements de session rapidement)

    Returns:
        Dictionnaire de l'utilisateur ou None
    """
    from core.services.auth_service import get_current_user
    return get_current_user()


@cached(ttl=CacheTTL.MINUTE_5, namespace='permissions', key_prefix='permissions:user')
def get_cached_user_permissions(user_id: Optional[int] = None) -> Dict[str, Dict[str, bool]]:
    """
    Retourne les permissions d'un utilisateur depuis le cache ou DB.

    TTL : 5 minutes

    Args:
        user_id: ID de l'utilisateur (None = utilisateur courant)

    Returns:
        Dict {module: {lecture, ecriture, suppression}}
    """
    from core.services.auth_service import UserSession

    session = UserSession()
    perms = session.get_permissions()

    if perms:
        return perms

    # Fallback si pas de session
    return {}


def invalidate_user_cache(reload_current_user: bool = True):
    """
    Invalide tout le cache utilisateur.

    Args:
        reload_current_user: Si True, recharge aussi les permissions du singleton
                            PermissionManager pour l'utilisateur courant.
                            Ceci est CRITIQUE pour éviter les race conditions TOCTOU.
    """
    cache = CacheManager.get_instance()
    cache.invalidate_namespace('permissions')

    # SÉCURITÉ: Recharger les permissions du PermissionManager singleton
    # pour éviter les race conditions où le cache est invalidé mais le
    # singleton garde les anciennes permissions en mémoire.
    if reload_current_user:
        try:
            from core.services.permission_manager import perm
            if perm.is_loaded():
                perm.reload()
                import logging
                logging.getLogger(__name__).debug("PermissionManager rechargé après invalidation cache")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Erreur reload PermissionManager: {e}")


# ===========================
# Cache Listes Statiques
# ===========================

@cached(ttl=CacheTTL.LONG, namespace='static', key_prefix='roles:all')
def get_cached_roles() -> List[Dict]:
    """
    Retourne tous les rôles depuis le cache ou DB.

    TTL : 1 heure (les rôles changent très rarement)

    Returns:
        Liste des rôles
    """
    from core.db.configbd import DatabaseCursor

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("SELECT id, nom, description FROM roles ORDER BY id")
        return cur.fetchall()


@cached(ttl=CacheTTL.LONG, namespace='static', key_prefix='ateliers:all')
def get_cached_ateliers() -> List[Dict]:
    """
    Retourne tous les ateliers depuis le cache ou DB.

    TTL : 1 heure

    Returns:
        Liste des ateliers
    """
    from core.db.configbd import DatabaseCursor

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("SELECT id, nom FROM atelier ORDER BY nom")
        return cur.fetchall()


@cached(ttl=CacheTTL.LONG, namespace='static', key_prefix='types_contrat:all')
def get_cached_types_contrat() -> List[str]:
    """
    Retourne les types de contrat depuis le cache ou DB.

    TTL : 1 heure

    Returns:
        Liste des types de contrat
    """
    # Les types de contrat sont généralement fixes
    return ['CDI', 'CDD', 'Intérim', 'Apprentissage', 'Stage']


def invalidate_static_lists_cache():
    """Invalide tout le cache des listes statiques"""
    cache = CacheManager.get_instance()
    cache.invalidate_namespace('static')


# ===========================
# Cache Écran (Dialog State)
# ===========================

class ScreenCache:
    """
    Gestionnaire de cache d'écran (dialog state).
    Permet de sauvegarder l'état d'un dialog et de le restaurer à la réouverture.

    Usage:
        # Sauvegarder l'état
        ScreenCache.save_state('gestion_personnel', {
            'filter': 'ACTIF',
            'selected_id': 123,
            'scroll_position': 450
        })

        # Restaurer l'état
        state = ScreenCache.get_state('gestion_personnel')
        if state:
            self.filter_combo.setCurrentText(state.get('filter', ''))
            # ... etc
    """

    @staticmethod
    def save_state(screen_name: str, state: Dict[str, Any], ttl: Optional[float] = CacheTTL.MINUTE_30):
        """
        Sauvegarde l'état d'un écran.

        Args:
            screen_name: Nom unique de l'écran
            state: Dictionnaire avec l'état à sauvegarder
            ttl: TTL (par défaut 30 minutes)
        """
        cache = CacheManager.get_instance()
        key = f"screen:{screen_name}:state"
        cache.set(key, state, ttl=ttl, namespace='screen_state')

    @staticmethod
    def get_state(screen_name: str, default: Optional[Dict] = None) -> Optional[Dict]:
        """
        Récupère l'état d'un écran.

        Args:
            screen_name: Nom unique de l'écran
            default: État par défaut si absent

        Returns:
            Dictionnaire de l'état ou None
        """
        cache = CacheManager.get_instance()
        key = f"screen:{screen_name}:state"
        return cache.get(key, default)

    @staticmethod
    def invalidate_state(screen_name: str):
        """Invalide l'état d'un écran"""
        cache = CacheManager.get_instance()
        key = f"screen:{screen_name}:state"
        cache.invalidate(key)

    @staticmethod
    def clear_all_states():
        """Invalide tous les états d'écran"""
        cache = CacheManager.get_instance()
        cache.invalidate_namespace('screen_state')


# ===========================
# Cache Personnel
# ===========================

@cached(ttl=CacheTTL.SHORT, namespace='personnel', key_prefix='personnel:actifs')
def get_cached_personnel_actifs() -> List[Dict]:
    """
    Retourne le personnel actif depuis le cache ou DB.

    TTL : 1 minute (le personnel change souvent)

    Returns:
        Liste du personnel actif
    """
    from core.db.configbd import DatabaseCursor

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT id, nom, prenom, matricule, statut
            FROM personnel
            WHERE statut = 'ACTIF'
            ORDER BY nom, prenom
        """)
        return cur.fetchall()


@cached(ttl=CacheTTL.SHORT, namespace='personnel', key_prefix='personnel:count')
def get_cached_personnel_count() -> Dict[str, int]:
    """
    Retourne le nombre de personnel par statut depuis le cache ou DB.

    TTL : 1 minute

    Returns:
        Dict {statut: count}
    """
    from core.db.configbd import DatabaseCursor

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT statut, COUNT(*) as count
            FROM personnel
            GROUP BY statut
        """)
        rows = cur.fetchall()
        return {row['statut']: row['count'] for row in rows}


def invalidate_personnel_cache():
    """Invalide tout le cache personnel"""
    cache = CacheManager.get_instance()
    cache.invalidate_namespace('personnel')


# ===========================
# Helpers d'invalidation
# ===========================

def invalidate_all_caches():
    """
    Invalide TOUS les caches de l'application.
    À utiliser avec précaution (seulement si nécessaire).
    """
    cache = CacheManager.get_instance()
    cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    Retourne les statistiques du cache.

    Returns:
        Dict avec hits, misses, hit_rate, etc.
    """
    cache = CacheManager.get_instance()
    return cache.get_stats()


def warm_up_cache():
    """
    Préchauffe le cache en chargeant les données les plus courantes.
    À appeler au démarrage de l'application.
    """
    # Charger les données statiques
    get_cached_roles()
    get_cached_ateliers()
    get_cached_types_contrat()

    # Charger les postes actifs
    get_cached_postes_actifs()

    print("✅ Cache préchauffé avec succès")


# ===========================
# Décorateurs d'invalidation pour les services
# ===========================

def invalidate_postes_on_change(func):
    """
    Décorateur pour invalider le cache postes après modification.

    Example:
        @invalidate_postes_on_change
        def update_poste(poste_id, data):
            # ... UPDATE ...
            pass
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        invalidate_postes_cache()
        return result
    return wrapper


def invalidate_personnel_on_change(func):
    """
    Décorateur pour invalider le cache personnel après modification.

    Example:
        @invalidate_personnel_on_change
        def add_personnel(nom, prenom):
            # ... INSERT ...
            pass
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        invalidate_personnel_cache()
        return result
    return wrapper


def invalidate_permissions_on_change(func):
    """
    Décorateur pour invalider le cache permissions après modification.

    SÉCURITÉ: Ce décorateur invalide AUSSI le PermissionManager singleton
    pour éviter les race conditions TOCTOU.

    Example:
        @invalidate_permissions_on_change
        def update_user_role(user_id, new_role_id):
            # ... UPDATE ...
            pass
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        # reload_current_user=True pour recharger le PermissionManager
        invalidate_user_cache(reload_current_user=True)
        return result
    return wrapper
