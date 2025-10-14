# -*- coding: utf-8 -*-
"""
EMAC UI KIT – PyQt5
Composants et thèmes réutilisables pour garder la même identité visuelle partout.

Contenu :
- get_stylesheet(theme="light"|"dark") → QSS prêt à appliquer sur QApplication ou un widget racine
- Card(QFrame) → carte avec coins arrondis, header (title/subtitle) et body
- TopBar(QFrame) → barre supérieure avec titre, champ de recherche, actions
- SideNav(QFrame) → barre latérale avec boutons de navigation checkables
# apply_shadow(widget, radius=24, y_offset=8, alpha=40) → Rétiré

Usage minimal :

    from PyQt5 import QtWidgets
    from emac_ui_kit import get_stylesheet, Card, TopBar, SideNav

    app = QtWidgets.QApplication([])
    app.setStyleSheet(get_stylesheet("light"))

    # ... construire votre fenêtre et placer les composants

Notes :
- Labels/entêtes sont visuellement en haut de section (conforme préférence).
- Tous les noms d'objets sont stables (#Card, #TitleLabel, etc.) pour styliser plus finement si besoin.
"""

from PyQt5 import QtWidgets, QtGui, QtCore

# =============================
# Thèmes
# =============================
_THEME_BASE = """
* { font-family: 'Segoe UI', 'Roboto', 'Helvetica', 'Arial'; }

QMainWindow { background: {BG}; }

/* FIX: Ajout de QDialog pour que les fenêtres secondaires s'inversent en Dark Mode. */
QWidget, QDialog { 
    color: {TXT};
    background: {BG};
}

QComboBox, QLineEdit {
    background: {BG_INPUT};
    border: 1px solid {BDR};
    border-radius: 8px;
    padding: 6px 8px;
    color: {TXT};
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
    border-left-color: {BDR};
    border-left-style: solid;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}
QComboBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiN7VFhUfSIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iNiA5IDEyIDE1IDE4IDkiPjwvcG9seWxpbmU+PC9zdmc+);
    subcontrol-position: center;
    width: 16px;
    height: 16px;
}
QComboBox:on { /* style de QComboBox lorsque la liste est déroulée */
    padding-top: 2px;
    padding-left: 9px;
}

QListWidget {
    background: {BG_INPUT};
    border: 1px solid {BDR};
    border-radius: 8px;
}
QListWidget::item { padding: 6px; }
QListWidget::item:selected { 
    background: {ACC_BG}; 
    color: {ACC_TXT};
}
QListWidget::item:hover { background: {HOVER}; }

/* Boutons */
QPushButton {
    background: {BG_INPUT};
    border: 1px solid {BDR};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TXT};
}
QPushButton:hover {
    background: {HOVER};
    border-color: {BDR_STRONG};
}
QPushButton:pressed { background: {BDR}; }

/* Bouton Primaire (Couleur forte) */
QPushButton[class="primary"] {
    background: {PRI};
    color: #ffffff;
    border: 1px solid {PRI};
    font-weight: 600;
}
QPushButton[class="primary"]:hover { background: {PRI_H}; border-color: {PRI_H}; }

/* Barre de défilement (Scrollbar) */
QScrollBar:vertical { width: 10px; background: transparent; }
QScrollBar::handle:vertical { min-height: 24px; background: {BDR}; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: {BDR_STRONG}; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
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
}

_THEME_DARK = {
    # Palette sombre utilisée pour la désactivation de l'ombre
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
}

def get_stylesheet(theme="light"):
    """
    Retourne la chaîne QSS pour le thème demandé (light ou dark).
    """
    if theme == "dark":
        colors = _THEME_DARK
    else:
        colors = _THEME_LIGHT
    
    # Remplacer {TXT} dans l'icône de la flèche du QComboBox avec la couleur du thème
    arrow_svg_template = "image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5uZy92ZzIwMDAvc3ZnIiB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIje1RYVH0iIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjYgOSAxMiAxNSAxOCA5Ij48L3BvbHlsaW5lPjwvc3ZnPg==);"
    arrow_svg = arrow_svg_template.replace('{TXT}', colors['TXT'].lstrip('#'))

    # NOTE: J'ai retiré le placeholder commenté du QSS pour éviter toute confusion lors du formatage.
    return _THEME_BASE.format(**colors).replace("image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiN7VFhUfSIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iNiA5IDEyIDE1IDE4IDkiPjwvcG9seWxpbmU+PC9zdmc+);", arrow_svg)


# =============================
# Composants de Base
# =============================

# La fonction apply_shadow a été retirée.
# L'importation de QGraphicsDropShadowEffect n'est plus nécessaire mais est laissée pour compatibilité.

class Card(QtWidgets.QFrame):
    """Conteneur carte avec coins arrondis."""
    def __init__(self, title: str = None, subtitle: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        
        # Suppression de l'appel à apply_shadow :
        # apply_shadow(self, radius=22, y_offset=4, alpha=36) 
        
        # Layout principal de la carte
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        
        # Layout pour le contenu (Body)
        self.body_layout = QtWidgets.QVBoxLayout()
        self.body_layout.setSpacing(8)
        bodyw = QtWidgets.QWidget()
        bodyw.setLayout(self.body_layout)
        
        if title:
            # Création du Header
            header = QtWidgets.QHBoxLayout(); header.setSpacing(8)
            lbl = QtWidgets.QLabel(title); lbl.setObjectName('TitleLabel')
            header.addWidget(lbl)
            header.addStretch(1)
            if subtitle:
                sub = QtWidgets.QLabel(subtitle); sub.setObjectName('SubtitleLabel')
                header.addWidget(sub, 0, QtCore.Qt.AlignRight)
            wrap = QtWidgets.QWidget(); wrap.setLayout(header)
            lay.addWidget(wrap)
        
        lay.addWidget(bodyw)
        # Référence au layout principal pour insertion facile
        self.layout = lay


class TopBar(QtWidgets.QFrame):
    """Barre supérieure pour la navigation et les actions globales."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(64)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(16, 0, 16, 0)
        root.setSpacing(10)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("TopBarTitle") # Pour cibler par QSS

        root.addWidget(self.title_label)
        root.addStretch(1)

        self.actions = QtWidgets.QHBoxLayout()
        self.actions.setSpacing(8)
        root.addLayout(self.actions)

    def add_action(self, widget: QtWidgets.QWidget):
        self.actions.addWidget(widget)


class SideNavButton(QtWidgets.QPushButton):
    """Bouton de navigation latérale (checkable)."""
    def __init__(self, text: str, icon_path: str = None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setObjectName("SideNavButton")
        self.setFixedHeight(48)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton#SideNavButton { 
                padding-left: 16px; 
                text-align: left; 
                border: none;
                border-radius: 8px;
            }
            QPushButton#SideNavButton:hover { 
                background: rgba(255, 255, 255, 0.1); 
            }
            QPushButton#SideNavButton:checked { 
                background: #4f46e5; 
                color: #ffffff;
            }
        """)


class SideNav(QtWidgets.QFrame):
    """Barre de navigation latérale pour les vues principales."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SideNav")
        self.setFixedWidth(240)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 16, 8, 16)
        root.setSpacing(4)
        
        self.nav_area = QtWidgets.QVBoxLayout()
        root.addLayout(self.nav_area)
        root.addStretch(1)
        
        self.actions_area = QtWidgets.QVBoxLayout()
        self.actions_area.setSpacing(4)
        root.addLayout(self.actions_area)

    def add_nav_button(self, btn: SideNavButton):
        """Ajoute un bouton à la section de navigation principale."""
        self.nav_area.addWidget(btn)

    def add_action_button(self, btn: SideNavButton):
        """Ajoute un bouton à la section d'actions (bas de la nav)."""
        self.actions_area.addWidget(btn)


if __name__ == "__main__":
    from PyQt5 import QtWidgets
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet("light")) # Test en light mode

    win = QtWidgets.QMainWindow()
    win.resize(1100, 720)

    wrapper = QtWidgets.QWidget(); root = QtWidgets.QHBoxLayout(wrapper); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

    sidenav = SideNav()
    sidenav.add_nav_button(SideNavButton("Tableau de bord"))
    sidenav.add_nav_button(SideNavButton("Personnel"))
    sidenav.add_nav_button(SideNavButton("Évaluations"))
    root.addWidget(sidenav)

    right = QtWidgets.QWidget(); rlay = QtWidgets.QVBoxLayout(right); rlay.setContentsMargins(0,0,0,0); rlay.setSpacing(0)

    top = TopBar("Démo UI Kit")
    rlay.addWidget(top)

    body = QtWidgets.QWidget(); blay = QtWidgets.QGridLayout(body); blay.setContentsMargins(16,16,16,16); blay.setHorizontalSpacing(16); blay.setVerticalSpacing(16)

    c1 = Card("Évaluations à venir", "Prochains postes / opérateurs"); c1.body_layout.addWidget(QtWidgets.QLabel("• 12 à planifier cette semaine"))
    c2 = Card("Retards", "Suivi des anomalies"); c2.body_layout.addWidget(QtWidgets.QLabel("• 3 opérateurs en retard"))
    c3 = Card("Activité récente"); c3.body_layout.addWidget(QtWidgets.QLabel("• 24 actions aujourd'hui"))

    blay.addWidget(c1, 0, 0)
    blay.addWidget(c2, 0, 1)
    blay.addWidget(c3, 1, 0)
    
    rlay.addWidget(body)
    root.addWidget(right, 1)

    win.setCentralWidget(wrapper)
    win.show()
    
    # Test d'une QDialog
    dialog = QtWidgets.QDialog(win)
    dialog.setWindowTitle("Test QDialog (Light)")
    dlay = QtWidgets.QVBoxLayout(dialog)
    dlay.addWidget(QtWidgets.QLabel("Ceci est une fenêtre modale."))
    dlay.addWidget(QtWidgets.QLineEdit("Champ de texte"))
    dlay.addWidget(QtWidgets.QPushButton("Bouton"))
    dialog.resize(300, 200)
    
    QtCore.QTimer.singleShot(100, dialog.show)


    sys.exit(app.exec_())