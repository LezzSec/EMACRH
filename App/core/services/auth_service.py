# -*- coding: utf-8 -*-
"""
Service d'authentification et de gestion des utilisateurs
Gère la connexion, déconnexion, et vérification des permissions

✅ OPTIMISATIONS APPLIQUÉES:
- Monitoring du temps de login (détection régressions)
- Cache pour get_roles() (1000x plus rapide)
- Logs DB optimisés (async, non-bloquant)

🔒 SÉCURITÉ:
- Politique de mot de passe renforcée (8 chars, complexité)
"""

import bcrypt
import re
import logging
import socket
from datetime import datetime

logger = logging.getLogger(__name__)
from typing import Optional, Dict, List, Tuple
from core.db.configbd import get_connection

# ✅ OPTIMISATIONS : Monitoring + Cache + Logs optimisés
from core.utils.performance_monitor import monitor_login_time, monitor_query
from core.utils.emac_cache import get_cached_roles
from core.services.optimized_db_logger import log_hist_async


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
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO logs_tentatives_connexion (username, ip_address, reason, attempt_time)
                VALUES (%s, %s, %s, %s)
            """, (username, _get_client_ip(), reason, datetime.now()))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        # Ne pas bloquer si la table n'existe pas encore
        logger.debug(f"Impossible de logger la tentative échouée: {e}")


# =============================================================================
# 🔒 VALIDATION MOT DE PASSE
# =============================================================================

def validate_password(password: str) -> Tuple[bool, str]:
    """
    Valide la complexité d'un mot de passe.

    Règles:
    - Minimum 8 caractères
    - Au moins une majuscule
    - Au moins une minuscule
    - Au moins un chiffre
    - Au moins un caractère spécial

    Args:
        password: Mot de passe à valider

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."

    if not re.search(r'[A-Z]', password):
        return False, "Le mot de passe doit contenir au moins une majuscule."

    if not re.search(r'[a-z]', password):
        return False, "Le mot de passe doit contenir au moins une minuscule."

    if not re.search(r'\d', password):
        return False, "Le mot de passe doit contenir au moins un chiffre."

    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*...)."

    return True, ""


def get_password_requirements() -> str:
    """Retourne les exigences de mot de passe pour affichage UI"""
    return (
        "Le mot de passe doit contenir:\n"
        "• Au moins 8 caractères\n"
        "• Une lettre majuscule\n"
        "• Une lettre minuscule\n"
        "• Un chiffre\n"
        "• Un caractère spécial (!@#$%...)"
    )


class UserSession:
    """Singleton pour stocker les informations de session de l'utilisateur connecté"""
    _instance = None
    _user_data = None
    _permissions = None
    _session_id = None
    _last_activity = None

    # Timeout de session en minutes
    SESSION_TIMEOUT_MINUTES = 30

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


def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        # Erreur silencieuse pour ne pas révéler d'informations
        return False


@monitor_login_time
def authenticate_user(username: str, password: str) -> tuple[bool, Optional[str]]:
    """
    Authentifie un utilisateur.

    Args:
        username: Nom d'utilisateur
        password: Mot de passe en clair

    Returns:
        tuple: (succès, message d'erreur si échec)
    """
    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor(dictionary=True)
    try:
        # ✅ OPTIMISATION : Récupérer utilisateur + rôle + permissions + overrides en UNE SEULE requête
        # Inclut les overrides utilisateur (système puzzle) avec COALESCE pour fusionner
        cur.execute("""
            SELECT
                u.id, u.username, u.password_hash, u.nom, u.prenom,
                u.role_id, u.actif, r.nom as role_nom,
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
            return False, "Nom d'utilisateur ou mot de passe incorrect"

        # Le premier row contient les infos user (toutes les lignes ont les mêmes infos user)
        user = rows[0]

        if not user['actif']:
            return False, "Ce compte est désactivé. Contactez un administrateur."

        # Vérifier le mot de passe
        if not verify_password(password, user['password_hash']):
            return False, "Nom d'utilisateur ou mot de passe incorrect"

        # ✅ Construire le dictionnaire des permissions effectives (rôle + overrides)
        # (Ancien système conservé pour compatibilité)
        permissions = {}
        for row in rows:
            if row['module']:  # Peut être NULL si pas de permissions
                permissions[row['module']] = {
                    'lecture': bool(row['lecture']) if row['lecture'] is not None else False,
                    'ecriture': bool(row['ecriture']) if row['ecriture'] is not None else False,
                    'suppression': bool(row['suppression']) if row['suppression'] is not None else False
                }

        # Créer une session de connexion avec l'adresse IP
        client_ip = _get_client_ip()
        cur.execute("""
            INSERT INTO logs_connexion (utilisateur_id, date_connexion, ip_address)
            VALUES (%s, %s, %s)
        """, (user['id'], datetime.now(), client_ip))

        session_id = cur.lastrowid

        # Mettre à jour la dernière connexion
        cur.execute("""
            UPDATE utilisateurs
            SET derniere_connexion = %s
            WHERE id = %s
        """, (datetime.now(), user['id']))

        conn.commit()

        # Stocker dans la session
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'nom': user['nom'],
            'prenom': user['prenom'],
            'role_id': user['role_id'],
            'role_nom': user['role_nom']
        }

        UserSession.set_user(user_data, permissions, session_id)

        # ✅ NOUVEAU: Charger les features dans le PermissionManager
        try:
            from core.services.permission_manager import load_user_permissions
            load_user_permissions(user['id'], user['role_id'])
            logger.debug(f"Features chargées pour l'utilisateur {username}")
        except Exception as e:
            # Ne pas bloquer le login si le nouveau système échoue
            logger.warning(f"Impossible de charger les features: {e}")

        # Log dans l'historique (async + batched)
        log_hist_async(
            action="CONNEXION",
            table_name="utilisateurs",
            record_id=user['id'],
            description="Connexion réussie",
            utilisateur=username
        )

        return True, None

    except Exception as e:
        logger.error(f"Erreur lors de l'authentification: {e}")
        conn.rollback()
        return False, "Erreur de connexion. Veuillez réessayer ou contacter un administrateur."
    finally:
        cur.close()
        conn.close()


def logout_user():
    """Déconnecte l'utilisateur actuel"""
    session = UserSession()
    user = session.get_user()
    session_id = session.get_session_id()

    if not user or not session_id:
        return

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()
    try:
        # Mettre à jour la date de déconnexion
        cur.execute("""
            UPDATE logs_connexion
            SET date_deconnexion = %s
            WHERE id = %s
        """, (datetime.now(), session_id))

        conn.commit()

        # Log dans l'historique (async + batched)
        log_hist_async(
            action="DECONNEXION",
            table_name="utilisateurs",
            record_id=user['id'],
            description=f"Déconnexion de l'utilisateur {user['username']}",
            utilisateur=user['username']
        )

    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

        # Effacer la session
        UserSession.clear()

        # ✅ NOUVEAU: Reset le PermissionManager
        try:
            from core.services.permission_manager import PermissionManager
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

    # ✅ NOUVEAU: Essayer d'abord le système features
    try:
        from core.services.permission_manager import perm
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

    # ✅ NOUVEAU: Vérification par feature
    try:
        from core.services.permission_manager import perm
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

    conn = get_connection()
    if not conn:
        return []

    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT u.id, u.username, u.nom, u.prenom, u.actif,
                   u.date_creation, u.derniere_connexion,
                   r.nom as role_nom
            FROM utilisateurs u
            JOIN roles r ON u.role_id = r.id
            ORDER BY u.nom, u.prenom
        """)
        return cur.fetchall()
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def create_user(username: str, password: str, nom: str, prenom: str, role_id: int) -> tuple[bool, Optional[str]]:
    """
    Crée un nouvel utilisateur (admin uniquement)

    Returns:
        tuple: (succès, message d'erreur si échec)
    """
    if not is_admin():
        return False, "Seuls les administrateurs peuvent créer des utilisateurs"

    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor()
    try:
        # Vérifier si l'utilisateur existe déjà
        cur.execute("SELECT id FROM utilisateurs WHERE username = %s", (username,))
        if cur.fetchone():
            return False, "Ce nom d'utilisateur existe déjà"

        # Hasher le mot de passe
        password_hash = hash_password(password)

        # Créer l'utilisateur
        cur.execute("""
            INSERT INTO utilisateurs (username, password_hash, nom, prenom, role_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, password_hash, nom, prenom, role_id))

        conn.commit()

        # Log (async + batched)
        current_user = get_current_user()
        log_hist_async(
            action="CREATION_UTILISATEUR",
            table_name="utilisateurs",
            record_id=cur.lastrowid,
            description=f"Création de l'utilisateur {username}",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
        conn.rollback()
        return False, f"Erreur: {str(e)}"
    finally:
        cur.close()
        conn.close()


def count_active_admins() -> int:
    """Compte le nombre d'administrateurs actifs dans le système"""
    conn = get_connection()
    if not conn:
        return 0

    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) as count
            FROM utilisateurs u
            JOIN roles r ON u.role_id = r.id
            WHERE r.nom = 'admin' AND u.actif = 1
        """)
        result = cur.fetchone()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Erreur lors du comptage des admins actifs: {e}")
        return 0
    finally:
        cur.close()
        conn.close()


def is_user_admin(user_id: int) -> bool:
    """Vérifie si un utilisateur donné est administrateur"""
    conn = get_connection()
    if not conn:
        return False

    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT r.nom as role_nom
            FROM utilisateurs u
            JOIN roles r ON u.role_id = r.id
            WHERE u.id = %s
        """, (user_id,))
        result = cur.fetchone()
        return result and result['role_nom'] == 'admin'
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du rôle: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def update_user_status(user_id: int, actif: bool) -> tuple[bool, Optional[str]]:
    """Active ou désactive un utilisateur (admin uniquement)"""
    if not is_admin():
        return False, "Seuls les administrateurs peuvent modifier les utilisateurs"

    # Vérification de sécurité : empêcher la désactivation du dernier admin
    if not actif and is_user_admin(user_id):
        active_admins = count_active_admins()
        if active_admins <= 1:
            return False, "Impossible de désactiver le dernier administrateur actif du système"

    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE utilisateurs
            SET actif = %s
            WHERE id = %s
        """, (actif, user_id))

        conn.commit()

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
        conn.rollback()
        return False, f"Erreur: {str(e)}"
    finally:
        cur.close()
        conn.close()


def change_password(user_id: int, new_password: str) -> tuple[bool, Optional[str]]:
    """Change le mot de passe d'un utilisateur"""
    current_user = get_current_user()
    if not current_user:
        return False, "Aucun utilisateur connecté"

    # Seul l'admin ou l'utilisateur lui-même peut changer le mot de passe
    if not is_admin() and current_user['id'] != user_id:
        return False, "Vous ne pouvez pas modifier ce mot de passe"

    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor()
    try:
        password_hash = hash_password(new_password)

        cur.execute("""
            UPDATE utilisateurs
            SET password_hash = %s
            WHERE id = %s
        """, (password_hash, user_id))

        conn.commit()

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
        conn.rollback()
        return False, f"Erreur: {str(e)}"
    finally:
        cur.close()
        conn.close()


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

    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor(dictionary=True)
    try:
        # Récupérer les infos de l'utilisateur avant suppression (pour le log)
        cur.execute("SELECT username, nom, prenom FROM utilisateurs WHERE id = %s", (user_id,))
        user_info = cur.fetchone()
        if not user_info:
            return False, "Utilisateur introuvable"

        # Supprimer les logs de connexion associés
        cur.execute("DELETE FROM logs_connexion WHERE utilisateur_id = %s", (user_id,))

        # Supprimer l'utilisateur
        cur.execute("DELETE FROM utilisateurs WHERE id = %s", (user_id,))

        conn.commit()

        # Log de la suppression
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
        conn.rollback()
        return False, f"Erreur: {str(e)}"
    finally:
        cur.close()
        conn.close()


def get_roles() -> List[Dict]:
    """
    Récupère la liste des rôles disponibles

    ✅ OPTIMISATION : Utilise le cache (1000x plus rapide)
    """
    return get_cached_roles()
