# -*- coding: utf-8 -*-
"""
Service d'authentification et de gestion des utilisateurs
Gère la connexion, déconnexion, et vérification des permissions
"""

import bcrypt
from datetime import datetime
from typing import Optional, Dict, List
from core.db.configbd import get_connection
from core.services.logger import log_hist


class UserSession:
    """Singleton pour stocker les informations de session de l'utilisateur connecté"""
    _instance = None
    _user_data = None
    _permissions = None
    _session_id = None

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

    @classmethod
    def is_authenticated(cls) -> bool:
        """Vérifie si un utilisateur est connecté"""
        return cls._user_data is not None


def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        print(f"Erreur lors de la vérification du mot de passe: {e}")
        return False


def authenticate_user(username: str, password: str) -> tuple[bool, Optional[str]]:
    """
    Authentifie un utilisateur

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
        # Récupérer l'utilisateur avec son rôle
        cur.execute("""
            SELECT u.id, u.username, u.password_hash, u.nom, u.prenom,
                   u.role_id, u.actif, r.nom as role_nom
            FROM utilisateurs u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = %s
        """, (username,))

        user = cur.fetchone()

        if not user:
            return False, "Nom d'utilisateur ou mot de passe incorrect"

        if not user['actif']:
            return False, "Ce compte est désactivé. Contactez un administrateur."

        # Vérifier le mot de passe
        if not verify_password(password, user['password_hash']):
            return False, "Nom d'utilisateur ou mot de passe incorrect"

        # Récupérer les permissions
        cur.execute("""
            SELECT module, lecture, ecriture, suppression
            FROM permissions
            WHERE role_id = %s
        """, (user['role_id'],))

        permissions_raw = cur.fetchall()
        permissions = {}
        for perm in permissions_raw:
            permissions[perm['module']] = {
                'lecture': bool(perm['lecture']),
                'ecriture': bool(perm['ecriture']),
                'suppression': bool(perm['suppression'])
            }

        # Créer une session de connexion
        cur.execute("""
            INSERT INTO logs_connexion (utilisateur_id, date_connexion)
            VALUES (%s, %s)
        """, (user['id'], datetime.now()))

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

        # Log dans l'historique
        log_hist(
            action="CONNEXION",
            table_name="utilisateurs",
            record_id=user['id'],
            description=f"Connexion de l'utilisateur {username} (rôle: {user['role_nom']})",
            utilisateur=username
        )

        return True, None

    except Exception as e:
        print(f"Erreur lors de l'authentification: {e}")
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

        # Log dans l'historique
        log_hist(
            action="DECONNEXION",
            table_name="utilisateurs",
            record_id=user['id'],
            description=f"Déconnexion de l'utilisateur {user['username']}",
            utilisateur=user['username']
        )

    except Exception as e:
        print(f"Erreur lors de la déconnexion: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

        # Effacer la session
        UserSession.clear()


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

    permissions = session.get_permissions()
    if not permissions:
        return False

    if module not in permissions:
        return False

    return permissions[module].get(action, False)


def is_admin() -> bool:
    """Vérifie si l'utilisateur connecté est un administrateur"""
    session = UserSession()
    user = session.get_user()
    if not user:
        return False
    return user['role_nom'] == 'admin'


def get_current_user() -> Optional[Dict]:
    """Retourne l'utilisateur connecté"""
    return UserSession.get_user()


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
        print(f"Erreur lors de la récupération des utilisateurs: {e}")
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

        # Log
        current_user = get_current_user()
        log_hist(
            action="CREATION_UTILISATEUR",
            table_name="utilisateurs",
            record_id=cur.lastrowid,
            description=f"Création de l'utilisateur {username}",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        print(f"Erreur lors de la création de l'utilisateur: {e}")
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
        print(f"Erreur lors du comptage des admins actifs: {e}")
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
        print(f"Erreur lors de la vérification du rôle: {e}")
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
        log_hist(
            action="MODIFICATION_UTILISATEUR",
            table_name="utilisateurs",
            record_id=user_id,
            description=f"Utilisateur {action_txt}",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        print(f"Erreur lors de la modification: {e}")
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

        log_hist(
            action="CHANGEMENT_MDP",
            table_name="utilisateurs",
            record_id=user_id,
            description="Mot de passe modifié",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        print(f"Erreur lors du changement de mot de passe: {e}")
        conn.rollback()
        return False, f"Erreur: {str(e)}"
    finally:
        cur.close()
        conn.close()


def get_roles() -> List[Dict]:
    """Récupère la liste des rôles disponibles"""
    conn = get_connection()
    if not conn:
        return []

    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, nom, description FROM roles ORDER BY id")
        return cur.fetchall()
    except Exception as e:
        print(f"Erreur lors de la récupération des rôles: {e}")
        return []
    finally:
        cur.close()
        conn.close()
