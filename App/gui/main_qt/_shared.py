# -*- coding: utf-8 -*-
"""Utilitaires partagés entre les mixins de MainWindow."""

_theme_cache = None


def _lazy_auth():
    from domain.services.admin import auth_service
    return auth_service


def _lazy_theme():
    from gui.components import ui_theme
    return ui_theme


def get_theme_components():
    global _theme_cache
    if _theme_cache is None:
        theme_module = _lazy_theme()
        _theme_cache = {
            'EmacTheme': theme_module.EmacTheme,
            'EmacButton': theme_module.EmacButton,
            'EmacCard': theme_module.EmacCard,
            'EmacStatusCard': theme_module.EmacStatusCard,
            'HamburgerButton': theme_module.HamburgerButton,
        }
    return _theme_cache
