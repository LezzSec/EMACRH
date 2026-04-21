# -*- coding: utf-8 -*-
# Rétrocompatibilité totale — rien ne doit casser
from gui.components.ui_kit.layout import Card, TopBar, SideNav, SideNavButton
from gui.components.ui_kit.title_bar import CustomTitleBar, add_custom_title_bar, add_fullscreen_button
from gui.components.ui_kit.feedback import EmacBadge, EmacAlert, EmacChip
from gui.components.ui_kit.toast import ToastNotification, ToastManager
from gui.components.ui_kit.widgets import LoadingButton, SearchBar
from gui.components.ui_kit.messages import show_error_message, show_warning_message
from gui.components.ui_kit.stylesheet import get_stylesheet

__all__ = [
    'Card', 'TopBar', 'SideNav', 'SideNavButton',
    'CustomTitleBar', 'add_custom_title_bar', 'add_fullscreen_button',
    'EmacBadge', 'EmacAlert', 'EmacChip',
    'ToastNotification', 'ToastManager',
    'LoadingButton', 'SearchBar',
    'show_error_message', 'show_warning_message',
    'get_stylesheet',
]
