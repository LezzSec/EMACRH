# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets

_THEME_BASE = """
* {{ font-family: 'Segoe UI', 'Roboto', 'Helvetica', 'Arial'; }}

QMainWindow {{ background: {BG}; }}

/* FIX: Ajout de QDialog pour que les fenêtres secondaires s'inversent en Dark Mode. */
QWidget, QDialog {{
    color: {TXT};
    background: {BG};
}}

QComboBox, QLineEdit {{
    background: {BG_INPUT};
    border: 1px solid {BDR};
    border-radius: 8px;
    padding: 6px 8px;
    color: {TXT};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
    border-left-color: {BDR};
    border-left-style: solid;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}}
QComboBox::down-arrow {{
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiN7VFhUfSIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iNiA5IDEyIDE1IDE4IDkiPjwvcG9seWxpbmU+PC9zdmc+);
    subcontrol-position: center;
    width: 16px;
    height: 16px;
}}
QComboBox:on {{ /* style de QComboBox lorsque la liste est déroulée */
    padding-top: 2px;
    padding-left: 9px;
}}

QListWidget {{
    background: {BG_INPUT};
    border: 1px solid {BDR};
    border-radius: 8px;
}}
QListWidget::item {{ padding: 6px; }}
QListWidget::item:selected {{
    background: {ACC_BG};
    color: {ACC_TXT};
}}
QListWidget::item:hover {{ background: {HOVER}; }}

/* Boutons */
QPushButton {{
    background: {BG_INPUT};
    border: 1px solid {BDR};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TXT};
}}
QPushButton:hover {{
    background: {HOVER};
    border-color: {BDR_STRONG};
}}
QPushButton:pressed {{ background: {BDR}; }}

/* Bouton Primaire (Couleur forte) */
QPushButton[class="primary"] {{
    background: {PRI};
    color: #ffffff;
    border: 1px solid {PRI};
    font-weight: 600;
}}
QPushButton[class="primary"]:hover {{ background: {PRI_H}; border-color: {PRI_H}; }}

/* Barre de défilement (Scrollbar) */
QScrollBar:vertical {{ width: 10px; background: transparent; }}
QScrollBar::handle:vertical {{ min-height: 24px; background: {BDR}; border-radius: 5px; }}
QScrollBar::handle:vertical:hover {{ background: {BDR_STRONG}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{{{ height: 0; }}}}
"""

_THEME_LIGHT = {
    "BG": "#f6f7fb",
    "BG_CARD": "#ffffff",
    "BG_INPUT": "#ffffff",
    "TXT": "#111827",
    "TXT_DIM": "#6b7280",
    "BDR": "#e5e7eb",
    "BDR_STRONG": "#d1d5db",
    "HOVER": "#f3f4f6",
    "PRI": "#0f172a",
    "PRI_H": "#0b1220",
    "ACC_BG": "#e8eefc",
    "ACC_TXT": "#111827",
    "SUCCESS": "#10b981",
    "SUCCESS_BG": "#d1fae5",
    "WARNING": "#f59e0b",
    "WARNING_BG": "#fef3c7",
    "ERROR": "#ef4444",
    "ERROR_BG": "#fee2e2",
    "INFO": "#3b82f6",
    "INFO_BG": "#dbeafe",
}

_THEME_DARK = {
    "BG": "#121212",
    "BG_CARD": "#1e1e1e",
    "BG_INPUT": "#0a0a0a",
    "TXT": "#e0e0e0",
    "TXT_DIM": "#9c9c9c",
    "BDR": "#2c2c2c",
    "BDR_STRONG": "#3f3f3f",
    "HOVER": "#3f3f3f",
    "PRI": "#4f46e5",
    "PRI_H": "#4338ca",
    "ACC_BG": "#374151",
    "ACC_TXT": "#e0e0e0",
    "SUCCESS": "#10b981",
    "SUCCESS_BG": "#064e3b",
    "WARNING": "#f59e0b",
    "WARNING_BG": "#78350f",
    "ERROR": "#ef4444",
    "ERROR_BG": "#7f1d1d",
    "INFO": "#3b82f6",
    "INFO_BG": "#1e3a8a",
}


def get_stylesheet(theme="light"):
    """Retourne la chaîne QSS pour le thème demandé (light ou dark)."""
    colors = _THEME_DARK if theme == "dark" else _THEME_LIGHT

    stylesheet = _THEME_BASE.replace(
        "image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiN7VFhUfSIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iNiA5IDEyIDE1IDE4IDkiPjwvcG9seWxpbmU+PC9zdmc+);",
        "___SVG_ARROW___"
    )
    stylesheet = stylesheet.format(**colors)

    txt_color = colors['TXT'].lstrip('#')
    arrow_svg = f"image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMje3R4dF9jb2xvcn0iIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjYgOSAxMiAxNSAxOCA5Ij48L3BvbHlsaW5lPjwvc3ZnPg==);"
    arrow_svg = arrow_svg.replace("{txt_color}", txt_color)
    stylesheet = stylesheet.replace("___SVG_ARROW___", arrow_svg)

    return stylesheet
