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


# =============================
# Barre de titre personnalisée
# =============================

class CustomTitleBar(QtWidgets.QWidget):
    """
    Barre de titre personnalisée avec boutons de contrôle Windows.
    """
    def __init__(self, parent_dialog, title="", parent=None):
        super().__init__(parent)
        self.parent_dialog = parent_dialog
        self.setFixedHeight(32)
        self.setStyleSheet("""
            QWidget {
                background: white;
                border-bottom: 1px solid #e5e7eb;
            }
        """)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)

        # Titre
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet("color: #000000; font-size: 12px; border: none;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Boutons de contrôle (style Windows 11)
        btn_size = 46
        btn_height = 32

        # Bouton Minimiser
        self.btn_minimize = QtWidgets.QPushButton("―")
        self.btn_minimize.setFixedSize(btn_size, btn_height)
        self.btn_minimize.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #000000;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #f3f4f6;
            }
        """)
        self.btn_minimize.clicked.connect(lambda: parent_dialog.showMinimized())
        layout.addWidget(self.btn_minimize)

        # Bouton Maximiser/Plein écran
        self.btn_maximize = QtWidgets.QPushButton("⛶")
        self.btn_maximize.setFixedSize(btn_size, btn_height)
        self.btn_maximize.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #000000;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #f3f4f6;
            }
        """)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_maximize.setToolTip("Plein écran (F11)")
        layout.addWidget(self.btn_maximize)

        # Bouton Fermer
        self.btn_close = QtWidgets.QPushButton("✕")
        self.btn_close.setFixedSize(btn_size, btn_height)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #000000;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #e81123;
                color: white;
            }
        """)
        self.btn_close.clicked.connect(lambda: parent_dialog.close())
        layout.addWidget(self.btn_close)

        # Pour le drag de la fenêtre
        self.dragging = False
        self.offset = None

    def toggle_maximize(self):
        """Bascule entre fenêtre normale et plein écran."""
        if self.parent_dialog.isMaximized() or self.parent_dialog.isFullScreen():
            self.parent_dialog.showNormal()
            self.btn_maximize.setText("⛶")
        else:
            self.parent_dialog.showMaximized()
            self.btn_maximize.setText("❐")

    def mousePressEvent(self, event):
        """Permet de déplacer la fenêtre en cliquant sur la barre de titre."""
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPos() - self.parent_dialog.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """Déplace la fenêtre."""
        if self.dragging and self.offset:
            self.parent_dialog.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        """Arrête le déplacement."""
        self.dragging = False

    def mouseDoubleClickEvent(self, event):
        """Double-clic pour maximiser/restaurer."""
        if event.button() == QtCore.Qt.LeftButton:
            self.toggle_maximize()


def add_custom_title_bar(dialog, title=None):
    """
    Version simplifiée : on utilise UNIQUEMENT la barre de titre système.

    - Plus de FramelessWindowHint
    - Plus de barre de titre personnalisée
    - On renvoie un petit widget vide pour ne pas casser les layouts existants
    """

    # 1) On remet une fenêtre classique avec barre système
    flags = QtCore.Qt.Window | QtCore.Qt.WindowSystemMenuHint \
            | QtCore.Qt.WindowMinimizeButtonHint \
            | QtCore.Qt.WindowMaximizeButtonHint \
            | QtCore.Qt.WindowCloseButtonHint

    dialog.setWindowFlags(flags)

    # Optionnel : on met à jour le titre de la fenêtre s'il est fourni
    if title is not None:
        dialog.setWindowTitle(title)

    # 2) On ne force pas d'attributs de rendu spéciaux
    dialog.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)
    dialog.setAttribute(QtCore.Qt.WA_OpaquePaintEvent, False)

    # 3) On renvoie un widget vide pour que:
    #    main_layout.addWidget(title_bar)
    #    ne casse rien mais n'affiche rien
    placeholder = QtWidgets.QWidget(dialog)
    placeholder.setFixedHeight(0)
    placeholder.setSizePolicy(
        QtWidgets.QSizePolicy.Expanding,
        QtWidgets.QSizePolicy.Fixed
    )

    return placeholder


# =============================
# Bouton Plein Écran
# =============================

def add_fullscreen_button(dialog, button_parent=None, style="compact"):
    """
    Ajoute un bouton plein écran à un QDialog et retourne le bouton créé.

    Args:
        dialog: Le QDialog auquel ajouter la fonctionnalité plein écran
        button_parent: (Optionnel) Le layout ou widget parent où ajouter le bouton
                      Si None, retourne juste le bouton sans l'ajouter
        style: "compact" (style Windows, petit) ou "rounded" (avec bordure arrondie)

    Returns:
        QPushButton: Le bouton plein écran créé

    Usage:
        # Dans un coin en haut à droite (style Windows)
        fullscreen_btn = add_fullscreen_button(self, header_layout, style="compact")

        # Avec style arrondi
        fullscreen_btn = add_fullscreen_button(self, header_layout, style="rounded")
    """

    if style == "compact":
        # Style compact type Windows (comme le screenshot)
        fullscreen_btn = QtWidgets.QPushButton("⛶")
        fullscreen_btn.setToolTip("Plein écran (F11)")
        fullscreen_btn.setFixedSize(46, 32)
        fullscreen_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #000000;
                font-size: 14px;
                font-weight: normal;
            }
            QPushButton:hover {
                background: #f3f4f6;
            }
            QPushButton:pressed {
                background: #e5e7eb;
                color: #6b7280;
            }
        """)
    else:
        # Style arrondi avec bordure
        fullscreen_btn = QtWidgets.QPushButton("⛶")
        fullscreen_btn.setToolTip("Basculer en plein écran (F11)")
        fullscreen_btn.setFixedSize(32, 32)
        fullscreen_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                font-size: 16px;
                color: #6b7280;
            }
            QPushButton:hover {
                background: #f3f4f6;
                border-color: #d1d5db;
                color: #111827;
            }
            QPushButton:pressed {
                background: #e5e7eb;
            }
        """)

    # Variable pour stocker l'état du plein écran
    dialog._is_fullscreen = False
    dialog._previous_geometry = None

    def toggle_fullscreen():
        """Bascule entre le mode plein écran et le mode fenêtré."""
        if not dialog._is_fullscreen:
            # Sauvegarder la géométrie actuelle
            dialog._previous_geometry = dialog.geometry()
            # Passer en plein écran
            dialog.showFullScreen()
            dialog._is_fullscreen = True
            fullscreen_btn.setText("⛶")
            fullscreen_btn.setToolTip("Quitter le plein écran (F11 ou Echap)")
        else:
            # Restaurer la fenêtre normale
            dialog.showNormal()
            if dialog._previous_geometry:
                dialog.setGeometry(dialog._previous_geometry)
            dialog._is_fullscreen = False
            fullscreen_btn.setText("⛶")
            fullscreen_btn.setToolTip("Basculer en plein écran (F11)")

    fullscreen_btn.clicked.connect(toggle_fullscreen)

    # Ajouter un raccourci clavier F11
    shortcut_f11 = QtWidgets.QShortcut(QtGui.QKeySequence("F11"), dialog)
    shortcut_f11.activated.connect(toggle_fullscreen)

    # Ajouter un raccourci Echap pour quitter le plein écran
    shortcut_esc = QtWidgets.QShortcut(QtGui.QKeySequence("Esc"), dialog)
    shortcut_esc.activated.connect(lambda: toggle_fullscreen() if dialog._is_fullscreen else None)

    # Ajouter le bouton au parent si spécifié
    if button_parent:
        if isinstance(button_parent, QtWidgets.QLayout):
            button_parent.addWidget(fullscreen_btn)
        else:
            # Supposer que c'est un widget avec un layout
            if hasattr(button_parent, 'layout') and button_parent.layout():
                button_parent.layout().addWidget(fullscreen_btn)

    return fullscreen_btn


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