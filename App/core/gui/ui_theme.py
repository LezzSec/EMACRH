# -*- coding: utf-8 -*-
"""
Thème visuel EMAC – Variante CLAIRE (Light) et SOMBRE (Dark)
• Fond clair, cartes blanches, contrasts lisibles
• Widgets : EmacButton, EmacCard, EmacHeader, EmacStatusCard, HamburgerButton

Usage :
from core.gui.ui_theme import EmacTheme, EmacDarkTheme, EmacButton, ...
EmacTheme.apply(app)
"""
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QPalette, QPainterPath
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame,
    QToolButton, QGraphicsDropShadowEffect
)


# === THÈME CLAIR ===
class EmacTheme:
    """Palette + QSS centralisés (version claire)."""
    # Palette claire (neutres + accents)
    BG = "#f6f7fb"          # fond application
    BG_CARD = "#ffffff"     # cartes
    BG_ELEV = "#fafbff"     # surfaces élevées
    BG_TABLE = "#ffffff"     # listes/tableaux

    TXT = "#111827"         # texte principal
    TXT_DIM = "#6b7280"     # texte secondaire

    BDR = "#e5e7eb"         # bordures
    BDR_STRONG = "#d1d5db"  # bordures fortes (en-têtes)

    PRI = "#0f172a"         # anthracite (primary)
    PRI_H = "#0b1220"

    ACC = "#059669"         # succès (vert)
    WARN = "#d97706"        # Avertissement (orange)
    ERR = "#dc2626"         # Erreur (rouge)

    @classmethod
    def qss(cls) -> str:
        return f'''
        QWidget {{
            color: {cls.TXT};
            background: {cls.BG};
            font-family: 'Segoe UI', Roboto, Arial;
            font-size: 14px;
        }}

        /* Cartes */
        QFrame#card {{
            background: {cls.BG_CARD};
            border: 1px solid {cls.BDR};
            border-radius: 14px;
        }}

        /* Titres */
        QLabel[class="h1"] {{ font-size: 24px; font-weight: 700; }}
        QLabel[class="h2"] {{ font-size: 18px; font-weight: 600; color: {cls.TXT}; }}
        QLabel[class="muted"] {{ color: {cls.TXT_DIM}; }}

        /* Boutons */
        QPushButton {{
            background: {cls.BG_CARD};
            border: 1px solid {cls.BDR};
            border-radius: 10px;
            padding: 10px 14px;
            color: {cls.TXT};
            text-align: center;
        }}
        QPushButton:hover {{
            border-color: {cls.BDR_STRONG};
            background: #f9fafb;
        }}
        QPushButton:pressed {{ background: #f3f4f6; }}

        /* Variantes */
        QPushButton[class="primary"] {{
            background: {cls.PRI};
            color: #ffffff;
            border: 1px solid {cls.PRI};
            font-weight: 600;
        }}
        QPushButton[class="primary"]:hover {{ background: {cls.PRI_H}; border-color: {cls.PRI_H}; }}

        QPushButton[class="ghost"] {{
            background: #ffffff;
            border: 1px solid {cls.BDR};
            color: {cls.TXT};
        }}
        QPushButton[class="ghost"]:hover {{ background: #f8fafc; }}

        /* Inputs & listes */
        QComboBox, QListWidget, QLineEdit {{
            background: {cls.BG_TABLE};
            border: 1px solid {cls.BDR};
            border-radius: 10px;
            padding: 6px 8px;
            color: {cls.TXT}; 
        }}
        QListWidget::item {{ padding: 8px 10px; height: 28px; }}
        QListWidget::item:selected {{ background: #e8eefc; color: {cls.TXT}; }}
        QListView::item {{ border-bottom: 1px solid #f1f5f9; }}

        /* Tables / QAbstractItemView */
        QAbstractItemView {{
            background: {cls.BG_TABLE};
            color: {cls.TXT};
            gridline-color: {cls.BDR};
            selection-background-color: #e8eefc;
            selection-color: {cls.TXT};
        }}
        QHeaderView::section {{
            background: #f3f4f6;
            color: {cls.TXT};
            border: 1px solid {cls.BDR_STRONG};
            padding: 6px 10px;
        }}
        
        /* Calendrier FIX */
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: {cls.BG_CARD}; 
            border-bottom: 1px solid {cls.BDR_STRONG};
        }}
        QCalendarWidget QToolButton {{
            color: {cls.TXT};
        }}


        /* Scrollbars fines */
        QScrollBar:vertical {{ width: 10px; background: transparent; }}
        QScrollBar::handle:vertical {{ min-height: 24px; background: #e5e7eb; border-radius: 6px; }}
        QScrollBar::handle:vertical:hover {{ background: #d1d5db; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        '''

    @classmethod
    def apply(cls, app):
        # Police par défaut
        app.setFont(QFont('Segoe UI', 10))
        # Palette Qt (widgets natifs)
        pal = app.palette()
        pal.setColor(QPalette.Window, QColor(cls.BG))
        pal.setColor(QPalette.WindowText, QColor(cls.TXT))
        pal.setColor(QPalette.Base, QColor(cls.BG_TABLE))
        pal.setColor(QPalette.Text, QColor(cls.TXT))
        pal.setColor(QPalette.Button, QColor(cls.BG_CARD))
        pal.setColor(QPalette.ButtonText, QColor(cls.TXT))
        pal.setColor(QPalette.Highlight, QColor("#3b82f6")) # pour la sélection
        pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        # Couleurs spécifiques au calendrier
        pal.setColor(QPalette.Light, QColor(cls.BG_TABLE)) # Fond des jours
        pal.setColor(QPalette.Midlight, QColor(cls.BG_TABLE))
        app.setPalette(pal)
        # QSS global
        app.setStyleSheet(cls.qss())


# -------------------------------------------------------------------
# === THÈME SOMBRE ===
class EmacDarkTheme(EmacTheme):
    """Palette + QSS centralisés (version sombre) avec FIX généralisé."""
    # Palette sombre (neutres + accents)
    BG = "#111827"          # fond application
    BG_CARD = "#1f2937"     # cartes (légèrement plus clair pour la profondeur)
    BG_ELEV = "#1f2937"     # surfaces élevées
    BG_TABLE = "#0f172a"    # listes/tableaux (plus sombre pour les listes)

    TXT = "#f3f4f6"         # texte principal (gris très clair)
    TXT_DIM = "#9ca3af"     # texte secondaire (gris moyen)

    BDR = "#374151"         # bordures
    BDR_STRONG = "#4b5563"  # bordures fortes (en-têtes)

    PRI = "#4f46e5"         # Bleu Indigo (primary)
    PRI_H = "#4338ca"

    ACC = "#10b981"         # succès (vert)
    WARN = "#f59e0b"        # Avertissement (jaune/orange)
    ERR = "#ef4444"         # Erreur (rouge)

    @classmethod
    def qss(cls) -> str:
        return f'''
        QWidget {{
            color: {cls.TXT};
            background: {cls.BG};
            font-family: 'Segoe UI', Roboto, Arial;
            font-size: 14px;
        }}

        /* Cartes */
        QFrame#card {{
            background: {cls.BG_CARD};
            border: 1px solid {cls.BDR};
            border-radius: 14px;
        }}
        
        /* Titres */
        QLabel[class="h1"] {{ font-size: 24px; font-weight: 700; }}
        QLabel[class="h2"] {{ font-size: 18px; font-weight: 600; color: {cls.TXT}; }}
        QLabel[class="muted"] {{ color: {cls.TXT_DIM}; }}

        /* Boutons */
        QPushButton {{
            background: {cls.BG_TABLE};
            border: 1px solid {cls.BDR};
            border-radius: 10px;
            padding: 10px 14px;
            color: {cls.TXT};
            text-align: center;
        }}
        QPushButton:hover {{
            border-color: {cls.BDR_STRONG};
            background: #1f2937;
        }}
        QPushButton:pressed {{ background: #273444; }}

        /* Variantes */
        QPushButton[class="primary"] {{
            background: {cls.PRI};
            color: #ffffff;
            border: 1px solid {cls.PRI};
            font-weight: 600;
        }}
        QPushButton[class="primary"]:hover {{ background: {cls.PRI_H}; border-color: {cls.PRI_H}; }}

        QPushButton[class="ghost"] {{
            background: {cls.BG_TABLE}; 
            border: 1px solid {cls.BDR};
            color: {cls.TXT};
        }}
        QPushButton[class="ghost"]:hover {{ background: #1f2937; border-color: {cls.BDR_STRONG};}}
        
        /* Inputs & listes */
        QComboBox, QListWidget, QLineEdit {{
            background: {cls.BG_TABLE};
            border: 1px solid {cls.BDR};
            border-radius: 10px;
            padding: 6px 8px;
            color: {cls.TXT}; 
        }}
        QListWidget::item {{ padding: 8px 10px; height: 28px; }}
        QListWidget::item:selected {{ background: #374151; color: {cls.TXT}; }}
        QListView::item {{ border-bottom: 1px solid {cls.BDR}; }}

        /* Tables / QAbstractItemView */
        QAbstractItemView {{
            background: {cls.BG_TABLE};
            color: {cls.TXT};
            gridline-color: {cls.BDR_STRONG};
            selection-background-color: #374151;
            selection-color: {cls.TXT};
        }}
        QHeaderView::section {{
            background: {cls.BG_CARD};
            color: {cls.TXT};
            border: 1px solid {cls.BDR_STRONG};
            padding: 6px 10px;
        }}

        /* Scrollbars fines */
        QScrollBar:vertical {{ width: 10px; background: transparent; }}
        QScrollBar::handle:vertical {{ min-height: 24px; background: {cls.BDR}; border-radius: 6px; }}
        QScrollBar::handle:vertical:hover {{ background: {cls.BDR_STRONG}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

        /* 💥 FIX CALENDRIER pour Thème Sombre 💥 (Navigation) */
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: {cls.BG_CARD}; 
            border-bottom: 1px solid {cls.BDR_STRONG};
        }}
        QCalendarWidget QToolButton {{
            color: {cls.TXT}; /* Flèches et boutons de navigation */
            background: transparent;
            font-size: 16px;
        }}
        QCalendarWidget QToolButton:hover {{
            background: {cls.BG_CARD};
            border-radius: 4px;
        }}
        
        '''

    @classmethod
    def apply(cls, app):
        # Police par défaut
        app.setFont(QFont('Segoe UI', 10))
        # Palette Qt (widgets natifs)
        pal = app.palette()
        pal.setColor(QPalette.Window, QColor(cls.BG))
        pal.setColor(QPalette.WindowText, QColor(cls.TXT))
        pal.setColor(QPalette.Base, QColor(cls.BG_TABLE))
        pal.setColor(QPalette.Text, QColor(cls.TXT))
        pal.setColor(QPalette.Button, QColor(cls.BG_CARD))
        pal.setColor(QPalette.ButtonText, QColor(cls.TXT))
        pal.setColor(QPalette.Highlight, QColor(cls.PRI)) # pour la sélection
        pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        
        # FIX CRITIQUE POUR CALENDRIER ET AUTRES WIDGETS NATIFS (QPalette.Light/Midlight)
        # Ces couleurs définissent l'arrière-plan des jours du calendrier.
        pal.setColor(QPalette.Light, QColor(cls.BG_TABLE)) 
        pal.setColor(QPalette.Midlight, QColor(cls.BG_TABLE))
        
        app.setPalette(pal)
        # QSS global
        app.setStyleSheet(cls.qss())


# -------------------------------------------------------------------
# === Classes de Composants ===
# -------------------------------------------------------------------

def apply_soft_shadow(widget, radius=22, alpha=36):
    """Applique un effet d'ombre douce (à utiliser sur les QFrame#card)."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(radius)
    shadow.setXOffset(0)
    shadow.setYOffset(4)
    # L'ombre est moins opaque en mode sombre. Tente de détecter le thème.
    try:
        # Tente de deviner le thème à partir du QStyleSheet de l'application
        is_dark = QApplication.instance().styleSheet().find(EmacDarkTheme.BG) != -1
    except:
        # En cas d'erreur ou si l'app n'est pas encore lancée, suppose le thème clair
        is_dark = False

    color = "#000000" if not is_dark else "#000000"
    shadow.setColor(QColor(color).lighter(100).darker(30).lighter(100 - alpha))
    widget.setGraphicsEffect(shadow)


class EmacCard(QFrame):
    """Conteneur carte avec entête optionnelle."""
    def __init__(self, title: str = None, subtitle: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        apply_soft_shadow(self, radius=22, alpha=36)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        
        # Layout de la carte (body)
        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        bodyw = QWidget()
        bodyw.setLayout(self.body)
        
        if title:
            # Création du Header
            header = QHBoxLayout(); header.setSpacing(8)
            lbl = QLabel(title); lbl.setProperty('class', 'h2')
            header.addWidget(lbl)
            header.addStretch(1)
            if subtitle:
                sub = QLabel(subtitle); sub.setProperty('class', 'muted')
                header.addWidget(sub, 0, Qt.AlignRight)
            wrap = QWidget(); wrap.setLayout(header)
            lay.addWidget(wrap)
        
        lay.addWidget(bodyw)
        # Référence au layout principal pour insertion facile
        self.layout = lay


class EmacStatusCard(EmacCard):
    """Carte avec bandeau coloré type alerte/succès, style pastel."""
    COLORS = {
        'danger': { 'bg': '#fee2e2', 'txt': '#991b1b', 'chip': '#fecaca', 'icon': '⚠️' },
        'success': { 'bg': '#dcfce7', 'txt': '#065f46', 'chip': '#bbf7d0', 'icon': '📅' },
        'info': { 'bg': '#e0f2fe', 'txt': '#075985', 'chip': '#bae6fd', 'icon': 'ℹ️' },
    }

    def __init__(self, title: str, variant: str = 'info', subtitle: str = None, parent=None):
        # Appelle le constructeur de EmacCard sans titre pour gérer l'entête soi-même
        super().__init__(None, None, parent) 
        
        c = self.COLORS.get(variant, self.COLORS['info'])
        header = QHBoxLayout(); header.setSpacing(8)
        
        # Détermination du thème pour le texte (même si le fond est fixe)
        try:
            ThemeCls = EmacDarkTheme if QApplication.instance().styleSheet().find(EmacDarkTheme.BG) != -1 else EmacTheme
        except:
            ThemeCls = EmacTheme
            
        pill = QLabel(f" {c['icon']}  {title}")
        pill.setStyleSheet(
            f"background:{c['bg']}; color:{ThemeCls.TXT}; font-weight:600; padding:6px 10px; border-radius:8px;")
        header.addWidget(pill, 0, Qt.AlignLeft)
        header.addStretch(1)
        if subtitle:
            sub = QLabel(subtitle); sub.setStyleSheet("color:#6b7280;")
            header.addWidget(sub, 0, Qt.AlignRight)
        w = QWidget(); w.setLayout(header)
        
        # Insérer l'entête avant le body
        self.layout.insertWidget(0, w)


    @staticmethod
    def small_tag(text: str) -> QLabel:
        tag = QLabel(text)
        tag.setStyleSheet("background:#eef2f7; color:#374151; padding:4px 8px; border-radius:8px; font-size:12px;")
        return tag


class EmacHeader(QWidget):
    """Barre de titre avec actions à droite."""
    def __init__(self, title: str, subtitle: str = None, parent=None):
        super().__init__(parent)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 8)  # plus compact

        left = QVBoxLayout(); left.setSpacing(2)
        h1 = QLabel(title); h1.setProperty('class', 'h1')
        left.addWidget(h1)
        if subtitle:
            sub = QLabel(subtitle); sub.setProperty('class', 'muted')
            left.addWidget(sub)
        root.addLayout(left, 1)

        self.actions = QHBoxLayout(); self.actions.setSpacing(6)
        root.addLayout(self.actions)

    def add_action(self, btn: QPushButton):
        self.actions.addWidget(btn)


class EmacButton(QPushButton):
    """Bouton avec tailles uniformes et variantes (primary/ghost)."""
    def __init__(self, text: str, variant: str = None, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(44)
        if variant in ('primary', 'ghost'):
            self.setProperty('class', variant)


class HamburgerButton(QToolButton):
    """Bouton menu 'hamburger' (3 barres) – look moderne, hover/pressed.
    S'utilise comme un bouton normal (signal clicked).
    """
    def __init__(self, parent=None, diameter=40, bar_width=18, bar_height=3, gap=5, variant="primary"):
        super().__init__(parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setAutoRaise(True)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.setFixedSize(diameter, diameter)

        # Détermine le thème pour les couleurs des barres
        try:
            is_dark = QApplication.instance().styleSheet().find(EmacDarkTheme.BG) != -1
            ThemeCls = EmacDarkTheme if is_dark else EmacTheme
        except:
            ThemeCls = EmacTheme

        # ----- STYLE selon variante (utilisant le thème actuel) -----
        if variant == "primary":
            # Fond primary (Indigo ou Anthracite), barres blanches
            self.setStyleSheet(f"""
                QToolButton {{
                    background: {ThemeCls.PRI};
                    border: 1px solid {ThemeCls.PRI};
                    border-radius: 12px;
                }}
                QToolButton:hover {{ 
                    background: {ThemeCls.PRI_H}; 
                    border-color: {ThemeCls.PRI_H};
                }}
                QToolButton:pressed {{ 
                    background: {ThemeCls.PRI_H}; 
                }}
            """)
            self._color_normal = QtGui.QColor(255, 255, 255)
            self._color_hover  = QtGui.QColor(255, 255, 255)
        else:
            # Fond transparent ou BG_CARD, barres TXT
            bg = ThemeCls.BG_CARD if is_dark else "rgba(255,255,255,0.95)"
            bg_hover = ThemeCls.BG_ELEV if is_dark else "#f0f2f7"
            bdr = ThemeCls.BDR
            bdr_strong = ThemeCls.BDR_STRONG
            self.setStyleSheet(f"""
                QToolButton {{
                    background: {bg};
                    border: 1px solid {bdr};
                    border-radius: 12px;
                }}
                QToolButton:hover {{ 
                    background: {bg_hover}; 
                    border-color: {bdr_strong};
                }}
                QToolButton:pressed {{ background: {bg_hover}; }}
            """)
            self._color_normal = QtGui.QColor(ThemeCls.TXT)
            self._color_hover  = QtGui.QColor(ThemeCls.TXT)

        # Pictogramme
        self._bar_w = bar_width
        self._bar_h = bar_height
        self._gap   = gap
        self._hover = False
        self.setAttribute(QtCore.Qt.WA_Hover, True)
        
        # Ombre douce pour plus de visibilité
        if variant != 'primary':
            apply_soft_shadow(self, radius=12, alpha=24) 

    def enterEvent(self, e):
        self._hover = True; self.update(); return super().enterEvent(e)
    
    def leaveEvent(self, e):
        self._hover = False; self.update(); return super().leaveEvent(e)

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        color = self._color_hover if self._hover else self._color_normal
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(color)
        
        cx = self.width() // 2
        cy = self.height() // 2
        w = self._bar_w
        h = self._bar_h
        g = self._gap
        
        # Dessine les 3 barres horizontales (maintenant avec des arguments INT pour QRectF)
        for dy in (-h - g, 0, h + g):
            # Nous utilisons QRectF pour permettre des arguments float (bar_width, bar_height)
            # mais nous assurons que les positions sont centrées correctement.
            # On utilise QPainterPath pour garantir le bon rendu des bords arrondis (h/2)
            rect = QRectF(cx - w / 2, cy - h / 2 + dy, w, h)
            path = QPainterPath()
            path.addRoundedRect(rect, h / 2, h / 2) # h/2 pour un bord complètement arrondi
            p.drawPath(path)
        p.end()


def make_primary(text: str) -> EmacButton:
    return EmacButton(text, variant='primary')
