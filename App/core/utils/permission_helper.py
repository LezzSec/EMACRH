# -*- coding: utf-8 -*-
"""
Helper pour gérer les permissions dans les interfaces
"""

from PyQt5.QtWidgets import QWidget, QPushButton, QAction
from core.services.auth_service import has_permission


def set_widget_permission(widget: QWidget, module: str, action: str = 'ecriture', disable_if_no_permission: bool = True):
    """
    Configure un widget en fonction des permissions de l'utilisateur

    Args:
        widget: Widget à configurer (QPushButton, QAction, etc.)
        module: Module concerné (ex: 'contrats', 'personnel')
        action: Type d'action ('lecture', 'ecriture', 'suppression')
        disable_if_no_permission: Si True, désactive le widget; sinon le cache
    """
    has_perm = has_permission(module, action)

    if not has_perm:
        if disable_if_no_permission:
            widget.setEnabled(False)
            if hasattr(widget, 'setToolTip'):
                widget.setToolTip("Vous n'avez pas les permissions nécessaires pour cette action")
        else:
            widget.setVisible(False)


def set_readonly_if_no_permission(widget: QWidget, module: str):
    """
    Rend un widget en lecture seule si l'utilisateur n'a pas les permissions d'écriture

    Args:
        widget: Widget à configurer
        module: Module concerné
    """
    has_write_perm = has_permission(module, 'ecriture')

    if not has_write_perm:
        if hasattr(widget, 'setReadOnly'):
            widget.setReadOnly(True)
        elif hasattr(widget, 'setEnabled'):
            widget.setEnabled(False)


def check_permission_with_message(module: str, action: str = 'ecriture') -> tuple[bool, str]:
    """
    Vérifie une permission et retourne un message d'erreur si refusée

    Args:
        module: Module concerné
        action: Type d'action

    Returns:
        tuple: (has_permission, error_message)
    """
    has_perm = has_permission(module, action)

    if not has_perm:
        action_text = {
            'lecture': 'consulter',
            'ecriture': 'modifier',
            'suppression': 'supprimer'
        }.get(action, 'effectuer cette action sur')

        return False, f"Vous n'avez pas les permissions nécessaires pour {action_text} {module}."

    return True, ""
