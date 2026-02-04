# -*- coding: utf-8 -*-
"""
PermissionManager - Point d'entrée unique pour les vérifications de permissions

Architecture:
- Singleton qui charge les permissions au login
- Cache en mémoire avec TTL pour éviter les race conditions (TOCTOU)
- Vérification fraîche (bypass cache) pour les opérations critiques
- Résolution: user_features (override) > role_features > refusé

Usage:
    from core.services.permission_manager import perm

    if perm.can("rh.personnel.edit"):
        # Autoriser l'action (utilise le cache)
        ...

    perm.require("admin.permissions")  # Vérifie en DB pour les opérations critiques
    perm.require("rh.view", fresh=False)  # Utilise le cache (moins critique)

Sécurité (Race Condition TOCTOU):
    - Le cache a un TTL de 5 minutes (PERMISSION_CACHE_TTL_SECONDS)
    - require() vérifie en DB par défaut pour éviter les actions non autorisées
    - can() utilise le cache pour les vérifications UI (performance)
    - Après modification des permissions, invalidate_and_reload_permissions() force le reload
"""

import logging
import time
from typing import Set, List, Optional, Dict, Callable, TypeVar, Any

logger = logging.getLogger(__name__)

# TTL du cache des permissions (en secondes)
# Après ce délai, les permissions seront automatiquement rechargées
PERMISSION_CACHE_TTL_SECONDS = 300  # 5 minutes

T = TypeVar('T')


class PermissionError(Exception):
    """Exception levée quand une permission est refusée"""

    def __init__(self, feature_key: str, message: str = None):
        self.feature_key = feature_key
        self.message = message or f"Permission refusée: {feature_key}"
        super().__init__(self.message)


class PermissionManager:
    """
    Gestionnaire centralisé des permissions basé sur les features.

    Règles de résolution:
    1. Si user_features contient la feature avec value=TRUE → autorisé
    2. Si user_features contient la feature avec value=FALSE → refusé
    3. Si role_features du rôle contient la feature → autorisé
    4. Sinon → refusé
    """

    _instance: Optional['PermissionManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Cache des permissions (set des feature_keys autorisées)
        self._allowed_features: Set[str] = set()

        # Cache des overrides utilisateur (pour savoir si c'est un override ou hérité)
        self._user_overrides: Dict[str, bool] = {}

        # Informations utilisateur
        self._user_id: Optional[int] = None
        self._role_id: Optional[int] = None

        # Flag indiquant si les permissions ont été chargées
        self._loaded = False

        # Timestamp du dernier chargement (pour TTL)
        self._cache_timestamp: float = 0.0

    @classmethod
    def get_instance(cls) -> 'PermissionManager':
        """Retourne l'instance singleton"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset le singleton (utile pour les tests)"""
        if cls._instance is not None:
            cls._instance._allowed_features.clear()
            cls._instance._user_overrides.clear()
            cls._instance._user_id = None
            cls._instance._role_id = None
            cls._instance._loaded = False
            cls._instance._cache_timestamp = 0.0

    def load_for_user(self, user_id: int, role_id: int) -> None:
        """
        Charge les permissions pour un utilisateur donné.
        Appelé au moment du login.

        Args:
            user_id: ID de l'utilisateur
            role_id: ID du rôle de l'utilisateur
        """
        from core.db.configbd import DatabaseCursor

        self._user_id = user_id
        self._role_id = role_id
        self._allowed_features.clear()
        self._user_overrides.clear()

        try:
            with DatabaseCursor(dictionary=True) as cur:
                # 1. Charger les features du rôle
                cur.execute("""
                    SELECT feature_key
                    FROM role_features
                    WHERE role_id = %s
                """, (role_id,))

                role_features = {row['feature_key'] for row in cur.fetchall()}
                logger.debug(f"Features du rôle {role_id}: {len(role_features)} features")

                # 2. Charger les overrides utilisateur
                cur.execute("""
                    SELECT feature_key, value
                    FROM user_features
                    WHERE user_id = %s
                """, (user_id,))

                for row in cur.fetchall():
                    self._user_overrides[row['feature_key']] = bool(row['value'])

                logger.debug(f"Overrides utilisateur {user_id}: {len(self._user_overrides)} overrides")

                # 3. Calculer les permissions effectives
                for feature_key in role_features:
                    # Override utilisateur ?
                    if feature_key in self._user_overrides:
                        if self._user_overrides[feature_key]:
                            self._allowed_features.add(feature_key)
                        # Si False, on n'ajoute pas (refusé explicitement)
                    else:
                        # Pas d'override → hérite du rôle
                        self._allowed_features.add(feature_key)

                # 4. Ajouter les overrides qui accordent des features non présentes dans le rôle
                for feature_key, value in self._user_overrides.items():
                    if value and feature_key not in self._allowed_features:
                        self._allowed_features.add(feature_key)

                self._loaded = True
                self._cache_timestamp = time.time()
                logger.info(f"Permissions chargées: {len(self._allowed_features)} features autorisées")

        except Exception as e:
            logger.warning(f"Système features non disponible (tables absentes?): {e}")
            # En cas d'erreur, on NE charge PAS les features → fallback vers ancien système
            self._allowed_features.clear()
            self._loaded = False  # Important: permet le fallback vers l'ancien système
            self._cache_timestamp = 0.0

    def reload(self) -> None:
        """Recharge les permissions (après modification)"""
        if self._user_id and self._role_id:
            self.load_for_user(self._user_id, self._role_id)

    def is_cache_stale(self) -> bool:
        """
        Vérifie si le cache des permissions est périmé (TTL dépassé).

        Returns:
            True si le cache doit être rafraîchi
        """
        if not self._loaded or self._cache_timestamp == 0.0:
            return True
        elapsed = time.time() - self._cache_timestamp
        return elapsed > PERMISSION_CACHE_TTL_SECONDS

    def _reload_if_stale(self) -> None:
        """Recharge automatiquement si le cache est périmé"""
        if self.is_cache_stale() and self._user_id and self._role_id:
            logger.debug("Cache permissions périmé, rechargement automatique...")
            self.reload()

    def _check_permission_fresh(self, feature_key: str) -> bool:
        """
        Vérifie une permission directement en base de données (bypass cache).
        Utilisé pour les opérations critiques où la sécurité prime sur la performance.

        Args:
            feature_key: Clé de la feature à vérifier

        Returns:
            True si autorisé, False sinon
        """
        if not self._user_id or not self._role_id:
            logger.warning("Vérification fraîche impossible: utilisateur non connecté")
            return False

        from core.db.configbd import DatabaseCursor

        try:
            with DatabaseCursor(dictionary=True) as cur:
                # 1. Vérifier si un override utilisateur existe
                cur.execute("""
                    SELECT value FROM user_features
                    WHERE user_id = %s AND feature_key = %s
                """, (self._user_id, feature_key))
                override = cur.fetchone()

                if override is not None:
                    # Override explicite: TRUE ou FALSE
                    return bool(override['value'])

                # 2. Pas d'override → vérifier si le rôle a cette feature
                cur.execute("""
                    SELECT 1 FROM role_features
                    WHERE role_id = %s AND feature_key = %s
                """, (self._role_id, feature_key))

                return cur.fetchone() is not None

        except Exception as e:
            logger.error(f"Erreur vérification fraîche permission '{feature_key}': {e}")
            # En cas d'erreur DB, refuser par sécurité
            return False

    def can(self, feature_key: str, fresh: bool = False) -> bool:
        """
        Vérifie si l'utilisateur a la permission.

        Note: Pour les vérifications UI (affichage de boutons, etc.), utiliser le cache
        est acceptable. Pour les actions critiques, utiliser require() qui vérifie en DB.

        Args:
            feature_key: Clé de la feature (ex: "rh.personnel.edit")
            fresh: Si True, vérifie directement en DB (bypass cache)

        Returns:
            True si autorisé, False sinon
        """
        if fresh:
            return self._check_permission_fresh(feature_key)

        if not self._loaded:
            logger.warning("Permissions non chargées, refus par défaut")
            return False

        # Auto-reload si cache périmé
        self._reload_if_stale()

        return feature_key in self._allowed_features

    def require(self, feature_key: str, fresh: bool = True) -> None:
        """
        Vérifie la permission et lève une exception si refusée.

        Par défaut, cette méthode vérifie TOUJOURS en base de données (fresh=True)
        pour éviter les race conditions TOCTOU où une permission a été révoquée
        mais le cache n'a pas été mis à jour.

        Args:
            feature_key: Clé de la feature
            fresh: Si True (défaut), vérifie en DB. Si False, utilise le cache.

        Raises:
            PermissionError: Si la permission est refusée
        """
        if not self.can(feature_key, fresh=fresh):
            logger.warning(f"Permission refusée (fresh={fresh}): {feature_key} pour user_id={self._user_id}")
            raise PermissionError(feature_key)

    def require_fresh(self, feature_key: str) -> None:
        """
        Vérifie la permission directement en DB (alias pour require(fresh=True)).

        Utiliser cette méthode pour les opérations critiques:
        - Création/modification/suppression de données
        - Opérations administratives
        - Actions irréversibles

        Args:
            feature_key: Clé de la feature

        Raises:
            PermissionError: Si la permission est refusée
        """
        self.require(feature_key, fresh=True)

    def can_any(self, *feature_keys: str) -> bool:
        """
        Vérifie si l'utilisateur a AU MOINS UNE des permissions.

        Args:
            feature_keys: Liste de clés de features

        Returns:
            True si au moins une est autorisée
        """
        return any(self.can(key) for key in feature_keys)

    def can_all(self, *feature_keys: str) -> bool:
        """
        Vérifie si l'utilisateur a TOUTES les permissions.

        Args:
            feature_keys: Liste de clés de features

        Returns:
            True si toutes sont autorisées
        """
        return all(self.can(key) for key in feature_keys)

    def filter_visible(self, items: List[T], key_fn: Callable[[T], str]) -> List[T]:
        """
        Filtre une liste d'items selon les permissions.

        Args:
            items: Liste d'items à filtrer
            key_fn: Fonction qui extrait la feature_key d'un item

        Returns:
            Liste des items autorisés
        """
        return [item for item in items if self.can(key_fn(item))]

    def get_allowed_features(self) -> Set[str]:
        """Retourne la copie du set des features autorisées"""
        return self._allowed_features.copy()

    def get_feature_source(self, feature_key: str) -> str:
        """
        Indique la source d'une permission.

        Returns:
            'override' si c'est un override utilisateur
            'role' si héritée du rôle
            'denied' si refusée
        """
        if feature_key in self._user_overrides:
            return 'override' if self._user_overrides[feature_key] else 'denied'
        elif feature_key in self._allowed_features:
            return 'role'
        else:
            return 'denied'

    def is_loaded(self) -> bool:
        """Indique si les permissions ont été chargées"""
        return self._loaded


# ============================================================================
# Instance globale (raccourci)
# ============================================================================

# Singleton accessible directement
perm = PermissionManager.get_instance()


# ============================================================================
# Fonctions utilitaires
# ============================================================================

def load_user_permissions(user_id: int, role_id: int) -> None:
    """Charge les permissions pour un utilisateur (appelé au login)"""
    perm.load_for_user(user_id, role_id)


def reload_permissions() -> None:
    """Recharge les permissions (après modification)"""
    perm.reload()


def can(feature_key: str, fresh: bool = False) -> bool:
    """
    Raccourci pour perm.can().

    Args:
        feature_key: Clé de la feature
        fresh: Si True, vérifie en DB (bypass cache)
    """
    return perm.can(feature_key, fresh=fresh)


def require(feature_key: str, fresh: bool = True) -> None:
    """
    Raccourci pour perm.require().

    Par défaut vérifie en DB pour éviter les race conditions.

    Args:
        feature_key: Clé de la feature
        fresh: Si True (défaut), vérifie en DB
    """
    perm.require(feature_key, fresh=fresh)


def require_fresh(feature_key: str) -> None:
    """
    Raccourci pour perm.require_fresh().

    Toujours vérifie en DB (pour opérations critiques).
    """
    perm.require_fresh(feature_key)


def invalidate_and_reload_permissions() -> None:
    """
    Invalide le cache et recharge les permissions pour l'utilisateur courant.

    Appeler cette fonction après modification des permissions d'un utilisateur
    pour s'assurer que les changements sont pris en compte immédiatement.
    """
    from core.utils.emac_cache import invalidate_user_cache
    invalidate_user_cache()
    perm.reload()
    logger.info("Permissions invalidées et rechargées")


# ============================================================================
# Service pour la gestion des features (CRUD)
# ============================================================================

def get_all_features() -> List[Dict]:
    """Récupère toutes les features du catalogue, groupées par module"""
    from core.db.configbd import DatabaseCursor

    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT id, key_code, label, module, description, display_order, is_active
                FROM features
                WHERE is_active = TRUE
                ORDER BY module, display_order, key_code
            """)
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Erreur get_all_features: {e}")
        return []


def get_features_by_module() -> Dict[str, List[Dict]]:
    """Récupère les features groupées par module"""
    features = get_all_features()
    by_module: Dict[str, List[Dict]] = {}

    for f in features:
        module = f['module']
        if module not in by_module:
            by_module[module] = []
        by_module[module].append(f)

    return by_module


def get_role_features(role_id: int) -> Set[str]:
    """Récupère les features d'un rôle"""
    from core.db.configbd import DatabaseCursor

    try:
        with DatabaseCursor() as cur:
            cur.execute("""
                SELECT feature_key FROM role_features WHERE role_id = %s
            """, (role_id,))
            return {row[0] for row in cur.fetchall()}
    except Exception as e:
        logger.error(f"Erreur get_role_features: {e}")
        return set()


def get_user_feature_overrides(user_id: int) -> Dict[str, bool]:
    """Récupère les overrides d'un utilisateur"""
    from core.db.configbd import DatabaseCursor

    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT feature_key, value FROM user_features WHERE user_id = %s
            """, (user_id,))
            return {row['feature_key']: bool(row['value']) for row in cur.fetchall()}
    except Exception as e:
        logger.error(f"Erreur get_user_feature_overrides: {e}")
        return {}


def save_role_features(role_id: int, feature_keys: Set[str]) -> tuple[bool, Optional[str]]:
    """
    Sauvegarde les features d'un rôle (remplace toutes les features existantes).

    Args:
        role_id: ID du rôle
        feature_keys: Set des feature_keys à assigner

    Returns:
        (success, error_message)
    """
    from core.db.configbd import get_connection
    from core.services.auth_service import is_admin, get_current_user
    from core.services.optimized_db_logger import log_hist_async

    if not is_admin():
        return False, "Seuls les administrateurs peuvent modifier les permissions"

    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor()
    try:
        # Supprimer les features existantes
        cur.execute("DELETE FROM role_features WHERE role_id = %s", (role_id,))

        # Insérer les nouvelles
        for key in feature_keys:
            cur.execute("""
                INSERT INTO role_features (role_id, feature_key)
                VALUES (%s, %s)
            """, (role_id, key))

        conn.commit()

        # Log
        current_user = get_current_user()
        log_hist_async(
            action="MODIFICATION_FEATURES_ROLE",
            table_name="role_features",
            record_id=role_id,
            description=f"Modification des features du rôle ID {role_id} ({len(feature_keys)} features)",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        logger.error(f"Erreur save_role_features: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


def save_user_feature_overrides(user_id: int, overrides: Dict[str, Optional[bool]]) -> tuple[bool, Optional[str]]:
    """
    Sauvegarde les overrides de features pour un utilisateur.

    Args:
        user_id: ID de l'utilisateur
        overrides: Dict {feature_key: True/False/None}
                   None = supprimer l'override (hériter du rôle)

    Returns:
        (success, error_message)
    """
    from core.db.configbd import get_connection
    from core.services.auth_service import is_admin, get_current_user
    from core.services.optimized_db_logger import log_hist_async
    from core.utils.emac_cache import invalidate_user_cache

    if not is_admin():
        return False, "Seuls les administrateurs peuvent modifier les permissions"

    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor()
    current_user = get_current_user()
    modifier_id = current_user['id'] if current_user else None

    try:
        for feature_key, value in overrides.items():
            if value is None:
                # Supprimer l'override
                cur.execute("""
                    DELETE FROM user_features
                    WHERE user_id = %s AND feature_key = %s
                """, (user_id, feature_key))
            else:
                # Upsert
                cur.execute("""
                    INSERT INTO user_features (user_id, feature_key, value, modifie_par)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        value = VALUES(value),
                        modifie_par = VALUES(modifie_par),
                        date_modification = CURRENT_TIMESTAMP
                """, (user_id, feature_key, value, modifier_id))

        conn.commit()

        # SÉCURITÉ: Invalider le cache ET recharger le PermissionManager
        # pour éviter les race conditions TOCTOU
        invalidate_user_cache(reload_current_user=True)

        # Log
        log_hist_async(
            action="MODIFICATION_FEATURES_UTILISATEUR",
            table_name="user_features",
            record_id=user_id,
            description=f"Modification des overrides de features pour l'utilisateur ID {user_id}",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        logger.error(f"Erreur save_user_feature_overrides: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


def reset_user_feature_overrides(user_id: int) -> tuple[bool, Optional[str]]:
    """Supprime tous les overrides d'un utilisateur"""
    from core.db.configbd import get_connection
    from core.services.auth_service import is_admin, get_current_user
    from core.services.optimized_db_logger import log_hist_async
    from core.utils.emac_cache import invalidate_user_cache

    if not is_admin():
        return False, "Seuls les administrateurs peuvent modifier les permissions"

    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM user_features WHERE user_id = %s", (user_id,))
        conn.commit()

        # SÉCURITÉ: Invalider le cache ET recharger le PermissionManager
        invalidate_user_cache(reload_current_user=True)

        current_user = get_current_user()
        log_hist_async(
            action="RESET_FEATURES_UTILISATEUR",
            table_name="user_features",
            record_id=user_id,
            description=f"Réinitialisation des overrides de features pour l'utilisateur ID {user_id}",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        logger.error(f"Erreur reset_user_feature_overrides: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()
