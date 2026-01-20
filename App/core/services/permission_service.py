# -*- coding: utf-8 -*-
"""
Service de gestion des permissions (système puzzle)
Gère les permissions par rôle ET les overrides par utilisateur

Architecture:
- Permissions de base: définies par rôle (table `permissions`)
- Overrides utilisateur: exceptions individuelles (table `permissions_utilisateur`)
- Permission effective = override si défini, sinon permission du rôle
"""

from typing import Optional, Dict, List
from core.db.configbd import get_connection, DatabaseCursor
from core.services.auth_service import get_current_user, is_admin
from core.services.optimized_db_logger import log_hist_async
from core.utils.emac_cache import invalidate_user_cache

# Liste des modules disponibles dans l'application
MODULES_DISPONIBLES = [
    {'code': 'personnel', 'nom': 'Personnel'},
    {'code': 'evaluations', 'nom': 'Évaluations'},
    {'code': 'polyvalence', 'nom': 'Polyvalence'},
    {'code': 'contrats', 'nom': 'Contrats'},
    {'code': 'documents_rh', 'nom': 'Documents RH'},
    {'code': 'planning', 'nom': 'Planning'},
    {'code': 'postes', 'nom': 'Postes'},
    {'code': 'historique', 'nom': 'Historique'},
    {'code': 'grilles', 'nom': 'Grilles'},
    {'code': 'gestion_utilisateurs', 'nom': 'Gestion Utilisateurs'},
]

# Actions disponibles
ACTIONS_DISPONIBLES = ['lecture', 'ecriture', 'suppression']


def get_all_roles() -> List[Dict]:
    """Récupère tous les rôles avec leurs descriptions"""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("SELECT id, nom, description FROM roles ORDER BY nom")
            return cur.fetchall()
    except Exception as e:
        print(f"Erreur get_all_roles: {e}")
        return []


def get_role_permissions(role_id: int) -> Dict[str, Dict[str, bool]]:
    """
    Récupère les permissions d'un rôle

    Returns:
        Dict structuré comme: {module: {lecture: bool, ecriture: bool, suppression: bool}}
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT module, lecture, ecriture, suppression
                FROM permissions
                WHERE role_id = %s
            """, (role_id,))

            permissions = {}
            for row in cur.fetchall():
                permissions[row['module']] = {
                    'lecture': bool(row['lecture']),
                    'ecriture': bool(row['ecriture']),
                    'suppression': bool(row['suppression'])
                }
            return permissions
    except Exception as e:
        print(f"Erreur get_role_permissions: {e}")
        return {}


def get_user_permission_overrides(user_id: int) -> Dict[str, Dict[str, Optional[bool]]]:
    """
    Récupère les overrides de permissions pour un utilisateur

    Returns:
        Dict structuré comme: {module: {lecture: bool|None, ecriture: bool|None, suppression: bool|None}}
        None signifie "hérite du rôle"
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT module, lecture, ecriture, suppression
                FROM permissions_utilisateur
                WHERE utilisateur_id = %s
            """, (user_id,))

            overrides = {}
            for row in cur.fetchall():
                overrides[row['module']] = {
                    'lecture': None if row['lecture'] is None else bool(row['lecture']),
                    'ecriture': None if row['ecriture'] is None else bool(row['ecriture']),
                    'suppression': None if row['suppression'] is None else bool(row['suppression'])
                }
            return overrides
    except Exception as e:
        print(f"Erreur get_user_permission_overrides: {e}")
        return {}


def get_effective_permissions(user_id: int, role_id: int) -> Dict[str, Dict]:
    """
    Calcule les permissions effectives d'un utilisateur
    Combine les permissions du rôle avec les overrides utilisateur

    Returns:
        Dict structuré comme: {
            module: {
                lecture: bool,
                ecriture: bool,
                suppression: bool,
                lecture_source: 'role'|'override',
                ecriture_source: 'role'|'override',
                suppression_source: 'role'|'override'
            }
        }
    """
    # Récupérer les permissions du rôle
    role_perms = get_role_permissions(role_id)

    # Récupérer les overrides utilisateur
    user_overrides = get_user_permission_overrides(user_id)

    # Fusionner
    effective = {}
    for module_info in MODULES_DISPONIBLES:
        module = module_info['code']
        role_perm = role_perms.get(module, {'lecture': False, 'ecriture': False, 'suppression': False})
        user_override = user_overrides.get(module, {})

        effective[module] = {}
        for action in ACTIONS_DISPONIBLES:
            override_value = user_override.get(action)
            if override_value is not None:
                # Override défini
                effective[module][action] = override_value
                effective[module][f'{action}_source'] = 'override'
            else:
                # Hérite du rôle
                effective[module][action] = role_perm.get(action, False)
                effective[module][f'{action}_source'] = 'role'

    return effective


def get_user_with_role(user_id: int) -> Optional[Dict]:
    """Récupère un utilisateur avec son rôle"""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT u.id, u.username, u.nom, u.prenom, u.role_id, r.nom as role_nom
                FROM utilisateurs u
                JOIN roles r ON u.role_id = r.id
                WHERE u.id = %s
            """, (user_id,))
            return cur.fetchone()
    except Exception as e:
        print(f"Erreur get_user_with_role: {e}")
        return None


def save_role_permissions(role_id: int, permissions: Dict[str, Dict[str, bool]]) -> tuple[bool, Optional[str]]:
    """
    Sauvegarde les permissions d'un rôle

    Args:
        role_id: ID du rôle
        permissions: Dict {module: {lecture: bool, ecriture: bool, suppression: bool}}

    Returns:
        tuple: (succès, message d'erreur)
    """
    if not is_admin():
        return False, "Seuls les administrateurs peuvent modifier les permissions"

    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor()
    try:
        for module, perms in permissions.items():
            # Vérifier si la permission existe déjà
            cur.execute("""
                SELECT id FROM permissions WHERE role_id = %s AND module = %s
            """, (role_id, module))

            if cur.fetchone():
                # Update
                cur.execute("""
                    UPDATE permissions
                    SET lecture = %s, ecriture = %s, suppression = %s
                    WHERE role_id = %s AND module = %s
                """, (
                    perms.get('lecture', False),
                    perms.get('ecriture', False),
                    perms.get('suppression', False),
                    role_id,
                    module
                ))
            else:
                # Insert
                cur.execute("""
                    INSERT INTO permissions (role_id, module, lecture, ecriture, suppression)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    role_id,
                    module,
                    perms.get('lecture', False),
                    perms.get('ecriture', False),
                    perms.get('suppression', False)
                ))

        conn.commit()

        # Invalider le cache
        invalidate_user_cache()

        # Log
        current_user = get_current_user()
        log_hist_async(
            action="MODIFICATION_PERMISSIONS_ROLE",
            table_name="permissions",
            record_id=role_id,
            description=f"Modification des permissions du rôle ID {role_id}",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        print(f"Erreur save_role_permissions: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


def save_user_permission_overrides(user_id: int, overrides: Dict[str, Dict[str, Optional[bool]]]) -> tuple[bool, Optional[str]]:
    """
    Sauvegarde les overrides de permissions pour un utilisateur

    Args:
        user_id: ID de l'utilisateur
        overrides: Dict {module: {lecture: bool|None, ecriture: bool|None, suppression: bool|None}}
                   None = supprimer l'override (hériter du rôle)

    Returns:
        tuple: (succès, message d'erreur)
    """
    if not is_admin():
        return False, "Seuls les administrateurs peuvent modifier les permissions"

    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor()
    current_user = get_current_user()
    modifier_id = current_user['id'] if current_user else None

    try:
        for module, perms in overrides.items():
            # Vérifier si tous les overrides sont None (= supprimer la ligne)
            all_none = all(v is None for v in perms.values())

            if all_none:
                # Supprimer l'override
                cur.execute("""
                    DELETE FROM permissions_utilisateur
                    WHERE utilisateur_id = %s AND module = %s
                """, (user_id, module))
            else:
                # Upsert (INSERT ... ON DUPLICATE KEY UPDATE)
                cur.execute("""
                    INSERT INTO permissions_utilisateur
                    (utilisateur_id, module, lecture, ecriture, suppression, modifie_par)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        lecture = VALUES(lecture),
                        ecriture = VALUES(ecriture),
                        suppression = VALUES(suppression),
                        modifie_par = VALUES(modifie_par),
                        date_modification = CURRENT_TIMESTAMP
                """, (
                    user_id,
                    module,
                    perms.get('lecture'),  # Peut être None
                    perms.get('ecriture'),
                    perms.get('suppression'),
                    modifier_id
                ))

        conn.commit()

        # Invalider le cache
        invalidate_user_cache()

        # Log
        log_hist_async(
            action="MODIFICATION_PERMISSIONS_UTILISATEUR",
            table_name="permissions_utilisateur",
            record_id=user_id,
            description=f"Modification des overrides de permissions pour l'utilisateur ID {user_id}",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        print(f"Erreur save_user_permission_overrides: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


def reset_user_permissions(user_id: int) -> tuple[bool, Optional[str]]:
    """
    Supprime tous les overrides d'un utilisateur (revient aux permissions du rôle)

    Returns:
        tuple: (succès, message d'erreur)
    """
    if not is_admin():
        return False, "Seuls les administrateurs peuvent modifier les permissions"

    conn = get_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM permissions_utilisateur
            WHERE utilisateur_id = %s
        """, (user_id,))

        conn.commit()

        # Invalider le cache
        invalidate_user_cache()

        # Log
        current_user = get_current_user()
        log_hist_async(
            action="RESET_PERMISSIONS_UTILISATEUR",
            table_name="permissions_utilisateur",
            record_id=user_id,
            description=f"Réinitialisation des permissions utilisateur ID {user_id}",
            utilisateur=current_user['username'] if current_user else None
        )

        return True, None

    except Exception as e:
        print(f"Erreur reset_user_permissions: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


def has_user_overrides(user_id: int) -> bool:
    """Vérifie si un utilisateur a des overrides de permissions"""
    try:
        with DatabaseCursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM permissions_utilisateur
                WHERE utilisateur_id = %s
            """, (user_id,))
            result = cur.fetchone()
            return result[0] > 0 if result else False
    except Exception as e:
        print(f"Erreur has_user_overrides: {e}")
        return False
