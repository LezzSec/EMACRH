# -*- coding: utf-8 -*-
"""
Service d'authentification et de gestion des utilisateurs
Gère la connexion, déconnexion, et vérification des permissions

OPTIMISATIONS APPLIQUÉES:
- Monitoring du temps de login (détection régressions)
- Cache pour get_roles() (1000x plus rapide)
- Logs DB optimisés (async, non-bloquant)

SÉCURITÉ:
- Politique de mot de passe renforcée (8 chars, complexité)
"""

import bcrypt
import re
import logging
import os
import socket
from datetime import datetime

logger = logging.getLogger(__name__)
from typing import Optional, Dict, List, Tuple
from infrastructure.db.configbd import DatabaseConnection
from infrastructure.db.query_executor import QueryExecutor

from infrastructure.config.performance_monitor import monitor_login_time, monitor_query
from infrastructure.cache.emac_cache import get_cached_roles
from infrastructure.logging.optimized_db_logger import log_hist_async


# =============================================================================
# CONFIGURATION BCRYPT
# =============================================================================
# Cost par défaut : 12 (2^12 = 4096 itérations ~250ms sur CPU moderne).
# À augmenter tous les 2-3 ans. Valeur configurable via EMAC_BCRYPT_COST.
# IMPORTANT : tout bump de cette valeur déclenche un rehash automatique
# au prochain login réussi des comptes concernés.
_BCRYPT_COST = int(os.getenv('EMAC_BCRYPT_COST', '12'))

# Garde-fous : cost < 10 est non-sûr, > 15 rend le login insupportable
if not 10 <= _BCRYPT_COST <= 15:
    import logging as _logging_guard
    _logging_guard.getLogger(__name__).warning(
        f"EMAC_BCRYPT_COST={_BCRYPT_COST} hors plage recommandée [10-15]. "
        f"Valeur corrigée à 12."
    )
    _BCRYPT_COST = 12


def _get_client_ip() -> str:
    """Récupère l'adresse IP ou le hostname de la machine cliente."""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return f"{hostname}/{ip_address}"
    except Exception:
        return "unknown"


def _log_failed_attempt(username: str, reason: str) -> None:
    """
    Log une tentative de connexion échouée dans la table d'audit.

    Args:
        username: Nom d'utilisateur tenté
        reason: Raison de l'échec (user_not_found, wrong_password, account_inactive)
    """
    try:
        QueryExecutor.execute_write(
            "INSERT INTO logs_tentatives_connexion (username, ip_address, reason, attempt_time) VALUES (%s, %s, %s, %s)",
            (username, _get_client_ip(), reason, datetime.now()),
            return_lastrowid=False
        )
    except Exception as e:
        # Ne pas bloquer si la table n'existe pas encore
        logger.debug(f"Impossible de logger la tentative échouée: {e}")


# Paliers de blocage progressifs : (nb_tentatives, durée_blocage_minutes)
# Palier 1 : 5 erreurs → 1 minute ; Palier 2 : 10 erreurs → 5 minutes
_RATE_LIMIT_TIERS = [(5, 1), (10, 5)]
# Fenêtre de recherche : assez large pour couvrir le palier le plus long
_RATE_LIMIT_SEARCH_WINDOW_MINUTES = 60


def _remaining_seconds_for_tier(column_filter: str, value: str, nth: int, lockout_minutes: int) -> int:
    """
    Calcule les secondes restantes avant expiration du blocage pour un palier donné.
    Trouve la Nème tentative la plus récente et vérifie si lockout_minutes n'est pas encore écoulé.
    """
    from datetime import timedelta
    window_start = datetime.now() - timedelta(minutes=_RATE_LIMIT_SEARCH_WINDOW_MINUTES)
    rows = QueryExecutor.fetch_all(
        f"SELECT attempt_time FROM logs_tentatives_connexion"
        f" WHERE {column_filter} = %s AND attempt_time >= %s"
        f" ORDER BY attempt_time DESC",
        (value, window_start),
    )
    if not rows or len(rows) < nth:
        return 0
    nth_attempt = rows[nth - 1][0] if isinstance(rows[nth - 1], (list, tuple)) else rows[nth - 1]['attempt_time']
    expires = nth_attempt + timedelta(minutes=lockout_minutes)
    remaining = int((expires - datetime.now()).total_seconds())
    return max(0, remaining)


def _check_rate_limit(username: str, ip_address: str) -> Tuple[bool, int, str]:
    """
    Vérifie si la tentative de connexion doit être bloquée (paliers progressifs).

    Returns:
        (blocked, seconds_to_wait, reason)
    """
    try:
        from datetime import timedelta
        window_start = datetime.now() - timedelta(minutes=_RATE_LIMIT_SEARCH_WINDOW_MINUTES)

        row = QueryExecutor.fetch_one(
            """SELECT
                 SUM(CASE WHEN username = %s THEN 1 ELSE 0 END) AS by_user,
                 SUM(CASE WHEN ip_address = %s THEN 1 ELSE 0 END) AS by_ip
               FROM logs_tentatives_connexion
               WHERE attempt_time >= %s""",
            (username, ip_address, window_start),
            dictionary=True,
        )
        by_user = int(row['by_user'] or 0) if row else 0
        by_ip = int(row['by_ip'] or 0) if row else 0

        # Évaluation du palier le plus élevé applicable (de haut en bas)
        for (threshold, lockout_min) in reversed(_RATE_LIMIT_TIERS):
            if by_user >= threshold:
                wait = _remaining_seconds_for_tier('username', username, threshold, lockout_min)
                if wait > 0:
                    return True, wait, "Trop de tentatives échouées pour ce compte."
            if by_ip >= threshold:
                wait = _remaining_seconds_for_tier('ip_address', ip_address, threshold, lockout_min)
                if wait > 0:
                    return True, wait, "Trop de tentatives échouées depuis ce poste."

        return False, 0, ""
    except Exception as e:
        # En cas d'erreur SQL on NE bloque PAS (disponibilité > sécurité stricte ici)
        logger.warning(f"check_rate_limit a échoué, bypass: {e}")
        return False, 0, ""


# =============================================================================
# VALIDATION MOT DE PASSE
# =============================================================================

# Mots de passe courants qui passent les règles de complexité mais sont triviaux.
# La normalisation leet-speak (voir _normalize_password) élargit la couverture.
_COMMON_PASSWORDS: frozenset = frozenset({
    # Variantes EMAC (application)
    "emac", "emac1", "emac12", "emac123", "emac1234", "emac12345",
    "emac2024", "emac2025", "emac2026",
    "emacadmin", "emacuser", "emacpass", "emacgestion",
    # Génériques FR très utilisés
    "motdepasse", "mdp", "password", "passw0rd", "p@ssword", "p@ssw0rd",
    "azerty", "azertyui", "azerty123", "azerty1234",
    "qwerty", "qwerty123", "qwerty1234",
    "admin", "admin123", "admin1234", "administrateur",
    "bonjour", "bienvenue", "bienvenu",
    "123456", "1234567", "12345678", "123456789",
    "abcdefgh", "abcd1234",
    # Patterns clavier
    "qsdfgh", "wxcvbn", "azertyuiop", "qsdfghjklm",
    "aaaaaa", "aaaaaaa", "aaaaaaaa",
    "zzzzzz", "zzzzzzz", "zzzzzzzz",
    # Prénoms courants FR
    "thomas", "nicolas", "alexandre", "jean", "pierre", "marie", "sophie",
    "julien", "antoine", "maxime", "kevin", "jeremy", "romain", "quentin",
    "camille", "sarah", "laura", "pauline", "chloe", "lea", "manon",
    "lucas", "hugo", "mathieu", "clement", "florian", "baptiste", "guillaume",
    # Noms de famille courants FR
    "martin", "dupont", "bernard", "richard", "durand", "leroy", "moreau",
    "simon", "laurent", "lefebvre", "michel", "garcia", "david", "bertrand",
    # Mois / jours
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche",
    # Couleurs
    "rouge", "bleu", "vert", "noir", "blanc", "jaune", "orange", "violet",
    "gris", "rose", "marron",
    # Animaux
    "chien", "chat", "cheval", "lapin", "tigre", "lion", "loup", "aigle",
    "requin", "cobra", "viper", "falcon", "eagle",
    # Sports / culture populaire FR
    "football", "arsenal", "psg", "paris", "marseille", "lyon", "bordeaux",
    "nantes", "lille", "strasbourg", "rennes", "monaco",
    "mbappé", "mbappe", "zidane", "platini", "henry", "benzema",
    "ronaldo", "messi", "neymar",
    # Mots du quotidien trop prévisibles
    "soleil", "chocolat", "amour", "secret", "securite", "secure",
    "vacances", "famille", "maison", "travail", "bureau", "entreprise",
    "voiture", "moto", "musique", "cinema", "voyage", "nature", "montagne",
    "plage", "mer", "ocean", "riviere", "foret", "jardin", "fleur",
    "bonheur", "liberte", "espoir", "courage", "force", "puissance",
    "argent", "richesse", "success", "winner", "champion", "victoire",
    "numero", "premier", "dernier", "nouveau", "facile", "simple",
    "important", "special", "unique", "super", "mega", "ultra", "hyper",
    # Anglais courants
    "welcome", "letmein", "monkey", "dragon", "master", "superman",
    "batman", "iloveyou", "sunshine", "princess", "shadow",
    "trustno1", "access", "login", "test", "guest", "hello", "world",
    "cheese", "coffee", "server", "network", "computer", "internet",
    "baseball", "soccer", "hockey", "jordan", "ranger", "hunter",
    "killer", "hacker", "manager", "office", "windows", "android",
    "apple", "google", "amazon", "facebook", "twitter", "instagram",
    "samsung", "iphone", "macbook",
})

# Substitutions leet-speak inversées pour normaliser avant la vérification
_LEET_TABLE = str.maketrans({
    '0': 'o', '1': 'i', '3': 'e', '4': 'a',
    '5': 's', '7': 't', '@': 'a', '$': 's', '!': 'i',
})


def _normalize_password(password: str) -> str:
    """Normalise un mot de passe pour détecter les variantes leet-speak."""
    return re.sub(r'[^a-z]', '', password.lower().translate(_LEET_TABLE))


_COMMON_PASSWORDS_CACHE: Optional[set] = None


def _is_common_password(password: str) -> bool:
    """
    Vérifie si un mot de passe figure dans la wordlist des plus courants.

    Double vérification :
    1. Fichier config/common_passwords.txt (~10 000 MDP, source SecLists) — case-insensitive
    2. Frozenset in-memory avec détection leet-speak (variantes normalisées)
    """
    global _COMMON_PASSWORDS_CACHE

    if _COMMON_PASSWORDS_CACHE is None:
        try:
            from pathlib import Path
            base = Path(__file__).resolve().parents[3]  # …/services/admin → App/
            wordlist_path = base / "config" / "common_passwords.txt"
            if wordlist_path.exists():
                with open(wordlist_path, encoding='utf-8', errors='ignore') as f:
                    _COMMON_PASSWORDS_CACHE = {
                        line.strip().lower() for line in f if line.strip()
                    }
                logger.info(f"Wordlist chargée : {len(_COMMON_PASSWORDS_CACHE)} MDP courants")
            else:
                logger.warning(f"Wordlist introuvable : {wordlist_path} — check fichier désactivé")
                _COMMON_PASSWORDS_CACHE = set()
        except Exception as e:
            logger.error(f"Erreur chargement wordlist : {e}")
            _COMMON_PASSWORDS_CACHE = set()

    lower = password.lower()
    normalized = _normalize_password(password)

    # Check fichier (10k mots)
    if lower in _COMMON_PASSWORDS_CACHE:
        return True

    # Check frozenset in-memory avec leet-speak
    for word in _COMMON_PASSWORDS:
        if lower == word:
            return True
        if word and normalized == word:
            return True
        if word and re.fullmatch(rf'{re.escape(word)}[\d!@#$%^&*_\-+=.]*', lower):
            return True
        if word and re.fullmatch(rf'[\d!@#$%^&*_\-+=.]*{re.escape(word)}[\d!@#$%^&*_\-+=.]*', normalized):
            return True

    return False


def validate_password(password: str, check_common: bool = True) -> Tuple[bool, str]:
    """
    Valide la robustesse d'un mot de passe (NIST SP 800-63B compatible).

    Règles (2026+) :
    - Minimum 12 caractères
    - Au moins 2 types de caractères distincts parmi : minuscules, majuscules, chiffres, spéciaux
    - Pas dans la liste des 10 000 mots de passe les plus courants

    La complexité artificielle (1 maj + 1 chiffre + 1 spécial) est relâchée
    car elle pousse à des patterns prévisibles ("Password1!" reste faible).
    """
    if len(password) < 12:
        return False, "Le mot de passe doit contenir au moins 12 caractères."

    types = 0
    if re.search(r'[a-z]', password):
        types += 1
    if re.search(r'[A-Z]', password):
        types += 1
    if re.search(r'\d', password):
        types += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~ /]', password):
        types += 1

    if types < 2:
        return False, (
            "Le mot de passe doit combiner au moins 2 types de caractères "
            "parmi : minuscules, majuscules, chiffres, caractères spéciaux."
        )

    if check_common and _is_common_password(password):
        return False, (
            "Ce mot de passe fait partie des plus courants et est facile à deviner. "
            "Choisissez une phrase de passe ou un mot de passe unique."
        )

    return True, ""


def get_password_requirements() -> str:
    """Retourne les exigences de mot de passe pour affichage UI"""
    return (
        "Le mot de passe doit :\n"
        "• Contenir au moins 12 caractères\n"
        "• Combiner au moins 2 types parmi : minuscules, majuscules, chiffres, caractères spéciaux\n"
        "• Ne pas figurer dans la liste des mots de passe les plus courants\n"
        "\n"
        "Conseil : une phrase de passe comme « piano bleu vendredi 42 » est "
        "plus sûre qu'un mot complexe comme « P@ssw0rd! »."
    )


class UserSession:
    """Singleton pour stocker les informations de session de l'utilisateur connecté"""
    _instance = None
    _user_data = None
    _permissions = None
    _session_id = None
    _last_activity = None

    # Timeout de session en minutes (configurable via EMAC_SESSION_TIMEOUT_MINUTES)
    import os as _os
    SESSION_TIMEOUT_MINUTES = int(_os.getenv('EMAC_SESSION_TIMEOUT_MINUTES', '30'))

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserSession, cls).__new__(cls)
        return cls._instance

    @classmethod
    def set_user(cls, user_data: Dict, permissions: Dict, session_id: int):
        """Définit l'utilisateur connecté"""
        cls._user_data = user_data
        cls._permissions = permissions
        cls._session_id = session_id
        cls._last_activity = datetime.now()

    @classmethod
    def get_user(cls) -> Optional[Dict]:
        """Retourne les données de l'utilisateur connecté"""
        return cls._user_data

    @classmethod
    def get_permissions(cls) -> Optional[Dict]:
        """Retourne les permissions de l'utilisateur connecté"""
        return cls._permissions

    @classmethod
    def get_session_id(cls) -> Optional[int]:
        """Retourne l'ID de session"""
        return cls._session_id

    @classmethod
    def clear(cls):
        """Efface la session"""
        cls._user_data = None
        cls._permissions = None
        cls._session_id = None
        cls._last_activity = None

    @classmethod
    def is_authenticated(cls) -> bool:
        """Vérifie si un utilisateur est connecté"""
        return cls._user_data is not None

    @classmethod
    def update_activity(cls):
        """Met à jour le timestamp de dernière activité"""
        if cls._user_data is not None:
            cls._last_activity = datetime.now()

    @classmethod
    def is_session_expired(cls) -> bool:
        """Vérifie si la session a expiré par inactivité"""
        if cls._user_data is None or cls._last_activity is None:
            return False

        from datetime import timedelta
        timeout = timedelta(minutes=cls.SESSION_TIMEOUT_MINUTES)
        return datetime.now() - cls._last_activity > timeout

    @classmethod
    def get_remaining_time(cls) -> Optional[int]:
        """Retourne le temps restant avant expiration en minutes, ou None si pas de session"""
        if cls._user_data is None or cls._last_activity is None:
            return None

        from datetime import timedelta
        timeout = timedelta(minutes=cls.SESSION_TIMEOUT_MINUTES)
        elapsed = datetime.now() - cls._last_activity
        remaining = timeout - elapsed

        if remaining.total_seconds() <= 0:
            return 0
        return int(remaining.total_seconds() / 60)


def hash_password(password: str, rounds: Optional[int] = None) -> str:
    """Hash un mot de passe avec bcrypt au cost configuré."""
    salt = bcrypt.gensalt(rounds=rounds if rounds is not None else _BCRYPT_COST)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def _extract_bcrypt_cost(password_hash: str) -> Optional[int]:
    """
    Extrait le cost d'un hash bcrypt.
    Format : $2b$12$<salt+hash> → parts[2] = '12'
    """
    try:
        if not password_hash or not password_hash.startswith('$2'):
            return None
        parts = password_hash.split('$')
        if len(parts) < 4:
            return None
        return int(parts[2])
    except (ValueError, IndexError):
        return None


def _password_needs_rehash(password_hash: str) -> bool:
    """Retourne True si le hash doit être régénéré (cost actuel < cost cible)."""
    current_cost = _extract_bcrypt_cost(password_hash)
    if current_cost is None:
        return True
    return current_cost < _BCRYPT_COST


@monitor_login_time
def authenticate_user(username: str, password: str) -> tuple[bool, Optional[str], int]:
    """
    Authentifie un utilisateur.

    Args:
        username: Nom d'utilisateur
        password: Mot de passe en clair

    Returns:
        tuple: (succès, message d'erreur si échec, secondes_à_attendre)
    """
    try:
        # ─── Rate limiting pré-check ─────────────────────────────────────────
        client_ip = _get_client_ip()
        blocked, wait_seconds, reason = _check_rate_limit(username, client_ip)
        if blocked:
            _log_failed_attempt(username, "rate_limited")
            logger.warning(f"Login bloqué (rate limit): user={username}, ip={client_ip}")
            return False, reason, wait_seconds
        # ─────────────────────────────────────────────────────────────────────

        # Transaction mixte read+write (SELECT dict → INSERT → UPDATE) :
        # DatabaseConnection directe requise ici — ne pas convertir en QueryExecutor.
        with DatabaseConnection() as conn:
            cur = conn.cursor(dictionary=True)

            cur.execute("""
                SELECT
                    u.id, u.username, u.password_hash, u.nom, u.prenom,
                    u.role_id, u.actif, u.password_needs_upgrade,
                    r.nom as role_nom,
                    p.module,
                    COALESCE(pu.lecture, p.lecture) as lecture,
                    COALESCE(pu.ecriture, p.ecriture) as ecriture,
                    COALESCE(pu.suppression, p.suppression) as suppression
                FROM utilisateurs u
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN permissions p ON p.role_id = u.role_id
                LEFT JOIN permissions_utilisateur pu ON pu.utilisateur_id = u.id AND pu.module = p.module
                WHERE u.username = %s
            """, (username,))

            rows = cur.fetchall()

            if not rows:
                cur.close()
                _log_failed_attempt(username, "user_not_found")
                return False, "Nom d'utilisateur ou mot de passe incorrect", 0

            user = rows[0]

            if not user['actif']:
                cur.close()
                _log_failed_attempt(username, "account_inactive")
                return False, "Ce compte est désactivé. Contactez un administrateur.", 0

            if not verify_password(password, user['password_hash']):
                cur.close()
                _log_failed_attempt(username, "wrong_password")
                return False, "Nom d'utilisateur ou mot de passe incorrect", 0

            # ─── Rehash transparent si le cost est dépassé ───────────────────
            if _password_needs_rehash(user['password_hash']):
                try:
                    new_hash = hash_password(password)
                    cur.execute(
                        "UPDATE utilisateurs SET password_hash = %s WHERE id = %s",
                        (new_hash, user['id'])
                    )
                    logger.info(
                        f"Rehash bcrypt pour {username} : "
                        f"{_extract_bcrypt_cost(user['password_hash'])} → {_BCRYPT_COST}"
                    )
                except Exception as e:
                    logger.warning(f"Échec rehash bcrypt pour {username}: {e}")
            # ─────────────────────────────────────────────────────────────────

            # Construire le dictionnaire des permissions effectives (rôle + overrides)
            permissions = {}
            for row in rows:
                if row['module']:
                    permissions[row['module']] = {
                        'lecture': bool(row['lecture']) if row['lecture'] is not None else False,
                        'ecriture': bool(row['ecriture']) if row['ecriture'] is not None else False,
                        'suppression': bool(row['suppression']) if row['suppression'] is not None else False
                    }

            cur.execute(
                "INSERT INTO logs_connexion (utilisateur_id, date_connexion, ip_address) VALUES (%s, %s, %s)",
                (user['id'], datetime.now(), client_ip)
            )
            session_id = cur.lastrowid

            cur.execute(
                "UPDATE utilisateurs SET derniere_connexion = %s WHERE id = %s",
                (datetime.now(), user['id'])
            )
            cur.close()

        user_data = {
            'id': user['id'],
            'username': user['username'],
            'nom': user['nom'],
            'prenom': user['prenom'],
            'role_id': user['role_id'],
            'role_nom': user['role_nom'],
            'password_needs_upgrade': bool(user.get('password_needs_upgrade', False)),
        }

        UserSession.set_user(user_data, permissions, session_id)

        try:
            from application.permission_manager import load_user_permissions
            load_user_permissions(user['id'], user['role_id'])
            logger.debug(f"Features chargées pour l'utilisateur {username}")
        except Exception as e:
            logger.warning(f"Impossible de charger les features: {e}")

        log_hist_async(
            action="CONNEXION",
            table_name="utilisateurs",
            record_id=user['id'],
            description="Connexion réussie",
            utilisateur=username
        )

        return True, None, 0

    except Exception as e:
        logger.error(f"Erreur lors de l'authentification: {e}")
        return False, "Erreur de connexion. Veuillez réessayer ou contacter un administrateur.", 0


def logout_user():
    """Déconnecte l'utilisateur actuel"""
    session = UserSession()
    user = session.get_user()
    session_id = session.get_session_id()

    if not user or not session_id:
        return

    try:
        QueryExecutor.execute_write(
            "UPDATE logs_connexion SET date_deconnexion = %s WHERE id = %s",
            (datetime.now(), session_id),
            return_lastrowid=False
        )
        log_hist_async(
            action="DECONNEXION",
            table_name="utilisateurs",
            record_id=user['id'],
            description=f"Déconnexion de l'utilisateur {user['username']}",
            utilisateur=user['username']
        )
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {e}")
    finally:
        UserSession.clear()
        try:
            from application.permission_manager import PermissionManager
            PermissionManager.reset()
        except Exception:
            pass


def has_permission(module: str, action: str = 'lecture') -> bool:
    """
    Vérifie si l'utilisateur a la permission pour une action sur un module

    Args:
        module: Nom du module (ex: 'contrats', 'personnel', etc.)
        action: Type d'action ('lecture', 'ecriture', 'suppression')

    Returns:
        bool: True si la permission est accordée
    """
    session = UserSession()
    if not session.is_authenticated():
        return False

    # Essayer d'abord le système features
    try:
        from application.permission_manager import perm
        if perm.is_loaded():
            # Mapping ancien système → features
            feature_key = _map_to_feature(module, action)
            if feature_key:
                return perm.can(feature_key)
    except Exception:
        pass  # Fallback vers l'ancien système

    # Ancien système (compatibilité)
    permissions = session.get_permissions()
    if not permissions:
        return False

    if module not in permissions:
        return False

    return permissions[module].get(action, False)


# Mapping ancien système → nouveau système features
_PERMISSION_TO_FEATURE_MAP = {
    # Personnel
    ('personnel', 'lecture'): 'rh.personnel.view',
    ('personnel', 'ecriture'): 'rh.personnel.edit',
    ('personnel', 'suppression'): 'rh.personnel.delete',
    # Évaluations
    ('evaluations', 'lecture'): 'production.evaluations.view',
    ('evaluations', 'ecriture'): 'production.evaluations.edit',
    ('evaluations', 'suppression'): 'production.evaluations.edit',
    # Polyvalence
    ('polyvalence', 'lecture'): 'production.polyvalence.view',
    ('polyvalence', 'ecriture'): 'production.polyvalence.edit',
    ('polyvalence', 'suppression'): 'production.polyvalence.edit',
    # Contrats
    ('contrats', 'lecture'): 'rh.contrats.view',
    ('contrats', 'ecriture'): 'rh.contrats.edit',
    ('contrats', 'suppression'): 'rh.contrats.delete',
    # Documents RH
    ('documents_rh', 'lecture'): 'rh.documents.view',
    ('documents_rh', 'ecriture'): 'rh.documents.edit',
    ('documents_rh', 'suppression'): 'rh.documents.edit',
    # Planning
    ('planning', 'lecture'): 'planning.view',
    ('planning', 'ecriture'): 'planning.absences.edit',
    ('planning', 'suppression'): 'planning.absences.edit',
    # Postes
    ('postes', 'lecture'): 'production.postes.view',
    ('postes', 'ecriture'): 'production.postes.edit',
    ('postes', 'suppression'): 'production.postes.edit',
    # Historique
    ('historique', 'lecture'): 'admin.historique.view',
    ('historique', 'ecriture'): 'admin.historique.export',
    ('historique', 'suppression'): 'admin.historique.export',
    # Grilles
    ('grilles', 'lecture'): 'production.grilles.view',
    ('grilles', 'ecriture'): 'production.grilles.export',
    ('grilles', 'suppression'): 'production.grilles.export',
    # Gestion utilisateurs
    ('gestion_utilisateurs', 'lecture'): 'admin.users.view',
    ('gestion_utilisateurs', 'ecriture'): 'admin.users.edit',
    ('gestion_utilisateurs', 'suppression'): 'admin.users.delete',
}


def _map_to_feature(module: str, action: str) -> Optional[str]:
    """Convertit un couple (module, action) vers une feature_key"""
    return _PERMISSION_TO_FEATURE_MAP.get((module, action))


def is_admin() -> bool:
    """
    Vérifie si l'utilisateur connecté est un administrateur.

    Un utilisateur est admin si:
    - Son rôle est 'admin' OU
    - Il a la feature 'admin.permissions' (nouveau système)
    """
    session = UserSession()
    user = session.get_user()
    if not user:
        return False

    # Vérification par rôle (ancien système)
    if user['role_nom'] == 'admin':
        return True

    # Vérification par feature
    try:
        from application.permission_manager import perm
        if perm.is_loaded() and perm.can('admin.permissions'):
            return True
    except Exception:
        pass

    return False


def get_current_user() -> Optional[Dict]:
    """Retourne l'utilisateur connecté"""
    return UserSession.get_user()


@monitor_query('Get All Users')
def get_all_users() -> List[Dict]:
    """Récupère la liste de tous les utilisateurs (admin uniquement)"""
    if not is_admin():
        return []

    try:
        return QueryExecutor.fetch_all(
            """SELECT u.id, u.username, u.nom, u.prenom, u.actif,
                      u.date_creation, u.derniere_connexion,
                      r.nom as role_nom
               FROM utilisateurs u
               JOIN roles r ON u.role_id = r.id
               ORDER BY u.nom, u.prenom""",
            dictionary=True
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
        return []


def create_user(username: str, password: str, nom: str, prenom: str, role_id: int) -> tuple[bool, Optional[str]]:
    """
    Crée un nouvel utilisateur (admin uniquement)

    Returns:
        tuple: (succès, message d'erreur si échec)
    """
    if not is_admin():
        return False, "Seuls les administrateurs peuvent créer des utilisateurs"

    try:
        if QueryExecutor.exists('utilisateurs', {'username': username}):
            return False, "Ce nom d'utilisateur existe déjà"

        password_hash = hash_password(password)
        new_id = QueryExecutor.execute_write(
            """INSERT INTO utilisateurs
               (username, password_hash, nom, prenom, role_id, password_needs_upgrade, password_changed_at)
               VALUES (%s, %s, %s, %s, %s, 0, NOW())""",
            (username, password_hash, nom, prenom, role_id)
        )

        current_user = get_current_user()
        log_hist_async(
            action="CREATION_UTILISATEUR",
            table_name="utilisateurs",
            record_id=new_id,
            description=f"Création de l'utilisateur {username}",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
        return False, f"Erreur: {str(e)}"


def count_active_admins() -> int:
    """Compte le nombre d'administrateurs actifs dans le système"""
    try:
        return QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM utilisateurs u JOIN roles r ON u.role_id = r.id WHERE r.nom = 'admin' AND u.actif = 1",
            default=0
        )
    except Exception as e:
        logger.error(f"Erreur lors du comptage des admins actifs: {e}")
        return 0


def is_user_admin(user_id: int) -> bool:
    """Vérifie si un utilisateur donné est administrateur"""
    try:
        result = QueryExecutor.fetch_one(
            "SELECT r.nom as role_nom FROM utilisateurs u JOIN roles r ON u.role_id = r.id WHERE u.id = %s",
            (user_id,),
            dictionary=True
        )
        return bool(result and result['role_nom'] == 'admin')
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du rôle: {e}")
        return False


def update_user_status(user_id: int, actif: bool) -> tuple[bool, Optional[str]]:
    """Active ou désactive un utilisateur (admin uniquement)"""
    if not is_admin():
        return False, "Seuls les administrateurs peuvent modifier les utilisateurs"

    # Vérification de sécurité : empêcher la désactivation du dernier admin
    if not actif and is_user_admin(user_id):
        active_admins = count_active_admins()
        if active_admins <= 1:
            return False, "Impossible de désactiver le dernier administrateur actif du système"

    try:
        QueryExecutor.execute_write(
            "UPDATE utilisateurs SET actif = %s WHERE id = %s",
            (actif, user_id), return_lastrowid=False
        )

        action_txt = "activé" if actif else "désactivé"
        current_user = get_current_user()
        log_hist_async(
            action="MODIFICATION_UTILISATEUR",
            table_name="utilisateurs",
            record_id=user_id,
            description=f"Utilisateur {action_txt}",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        logger.error(f"Erreur lors de la modification: {e}")
        return False, f"Erreur: {str(e)}"


def change_password(user_id: int, new_password: str) -> tuple[bool, Optional[str]]:
    """Change le mot de passe d'un utilisateur"""
    current_user = get_current_user()
    if not current_user:
        return False, "Aucun utilisateur connecté"

    if not is_admin() and current_user['id'] != user_id:
        return False, "Vous ne pouvez pas modifier ce mot de passe"

    # Validation de la politique (12+ chars, 2 types, wordlist)
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return False, error_msg

    try:
        password_hash = hash_password(new_password)
        QueryExecutor.execute_write(
            """UPDATE utilisateurs
               SET password_hash = %s, password_needs_upgrade = 0, password_changed_at = NOW()
               WHERE id = %s""",
            (password_hash, user_id), return_lastrowid=False
        )

        log_hist_async(
            action="CHANGEMENT_MDP",
            table_name="utilisateurs",
            record_id=user_id,
            description="Mot de passe modifié",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        logger.error(f"Erreur lors du changement de mot de passe: {e}")
        return False, f"Erreur: {str(e)}"


def delete_user(user_id: int) -> tuple[bool, Optional[str]]:
    """
    Supprime définitivement un utilisateur (admin uniquement)

    Args:
        user_id: ID de l'utilisateur à supprimer

    Returns:
        tuple: (succès, message d'erreur si échec)
    """
    if not is_admin():
        return False, "Seuls les administrateurs peuvent supprimer des utilisateurs"

    current_user = get_current_user()

    # Empêcher l'auto-suppression
    if current_user and current_user['id'] == user_id:
        return False, "Vous ne pouvez pas supprimer votre propre compte"

    # Vérifier si c'est le dernier admin actif
    if is_user_admin(user_id):
        active_admins = count_active_admins()
        if active_admins <= 1:
            return False, "Impossible de supprimer le dernier administrateur du système"

    try:
        user_info = QueryExecutor.fetch_one(
            "SELECT username, nom, prenom FROM utilisateurs WHERE id = %s",
            (user_id,), dictionary=True
        )
        if not user_info:
            return False, "Utilisateur introuvable"

        QueryExecutor.execute_transaction([
            ("DELETE FROM logs_connexion WHERE utilisateur_id = %s", (user_id,)),
            ("DELETE FROM utilisateurs WHERE id = %s", (user_id,)),
        ])

        log_hist_async(
            action="SUPPRESSION_UTILISATEUR",
            table_name="utilisateurs",
            record_id=user_id,
            description=f"Suppression de l'utilisateur {user_info['username']} ({user_info['nom']} {user_info['prenom']})",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'utilisateur: {e}")
        return False, f"Erreur: {str(e)}"


def get_roles() -> List[Dict]:
    """
    Récupère la liste des rôles disponibles

    OPTIMISATION : Utilise le cache (1000x plus rapide)
    """
    return get_cached_roles()
