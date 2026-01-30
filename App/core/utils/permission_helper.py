# -*- coding: utf-8 -*-
"""
Helper pour gérer les permissions dans les interfaces.
Utilise le nouveau système de features (perm.can).

Migration 2026-01-28: Passage de has_permission() vers perm.can()
"""

from PyQt5.QtWidgets import QWidget
from typing import List
from core.services.permission_manager import can


def set_widget_permission(
    widget: QWidget,
    feature_key: str,
    disable_if_no_permission: bool = True
):
    """
    Configure un widget en fonction des permissions de l'utilisateur.

    Args:
        widget: Widget à configurer (QPushButton, QAction, etc.)
        feature_key: Clé de la feature (ex: 'rh.personnel.edit')
        disable_if_no_permission: Si True, désactive le widget; sinon le cache
    """
    has_perm = can(feature_key)

    if not has_perm:
        if disable_if_no_permission:
            widget.setEnabled(False)
            if hasattr(widget, 'setToolTip'):
                widget.setToolTip("Vous n'avez pas les permissions nécessaires pour cette action")
        else:
            widget.setVisible(False)


def set_widgets_permission(
    widgets: List[QWidget],
    feature_key: str,
    disable_if_no_permission: bool = True
):
    """
    Configure plusieurs widgets avec la même permission.

    Args:
        widgets: Liste de widgets à configurer
        feature_key: Clé de la feature
        disable_if_no_permission: Si True, désactive; sinon cache
    """
    for widget in widgets:
        set_widget_permission(widget, feature_key, disable_if_no_permission)


def set_readonly_if_no_permission(widget: QWidget, feature_key: str):
    """
    Rend un widget en lecture seule si l'utilisateur n'a pas la permission.

    Args:
        widget: Widget à configurer
        feature_key: Clé de la feature d'édition (ex: 'rh.personnel.edit')
    """
    has_write_perm = can(feature_key)

    if not has_write_perm:
        if hasattr(widget, 'setReadOnly'):
            widget.setReadOnly(True)
        elif hasattr(widget, 'setEnabled'):
            widget.setEnabled(False)


def check_permission_with_message(feature_key: str) -> tuple[bool, str]:
    """
    Vérifie une permission et retourne un message d'erreur si refusée.

    Args:
        feature_key: Clé de la feature

    Returns:
        tuple: (has_permission, error_message)
    """
    has_perm = can(feature_key)

    if not has_perm:
        return False, f"Vous n'avez pas les permissions nécessaires pour cette action ({feature_key})."

    return True, ""


def can_view(module: str) -> bool:
    """
    Raccourci pour vérifier la permission de lecture d'un module.

    Args:
        module: 'rh', 'production', 'planning', 'admin'
    """
    return can(f"{module}.view")


def can_edit(module: str, submodule: str) -> bool:
    """
    Raccourci pour vérifier la permission d'édition.

    Args:
        module: 'rh', 'production', 'planning', 'admin'
        submodule: 'personnel', 'contrats', 'evaluations', etc.
    """
    return can(f"{module}.{submodule}.edit")


def can_delete(module: str, submodule: str) -> bool:
    """
    Raccourci pour vérifier la permission de suppression.

    Args:
        module: 'rh', 'production', 'planning', 'admin'
        submodule: 'personnel', 'contrats', etc.
    """
    return can(f"{module}.{submodule}.delete")


# =============================================================================
# Compatibilité avec l'ancien système (deprecated)
# =============================================================================

# Mapping ancien système → nouveau système features
_LEGACY_PERMISSION_MAP = {
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


def legacy_to_feature(module: str, action: str = 'lecture') -> str:
    """
    Convertit une permission ancien système vers une feature_key.

    DEPRECATED: Utiliser directement les feature_keys.

    Args:
        module: Ancien nom de module ('personnel', 'contrats', etc.)
        action: Ancienne action ('lecture', 'ecriture', 'suppression')

    Returns:
        feature_key correspondante ou None
    """
    return _LEGACY_PERMISSION_MAP.get((module, action))


def check_legacy_permission(module: str, action: str = 'lecture') -> bool:
    """
    DEPRECATED: Utiliser can(feature_key) directement.

    Vérifie une permission en utilisant l'ancien format (module, action).
    """
    feature_key = legacy_to_feature(module, action)
    if feature_key:
        return can(feature_key)
    return False
