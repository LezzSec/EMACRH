# -*- coding: utf-8 -*-
"""
Thème visuel EMAC – Variante CLAIRE (Light)
• Fond clair, cartes blanches, contrastes lisibles
• Widgets : EmacButton, EmacCard, EmacHeader, EmacStatusCard, HamburgerButton

Usage :
from gui.components.ui_theme import EmacTheme, EmacButton, ...
EmacTheme.apply(app)
"""
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QPalette, QPainterPath
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame,
    QToolButton
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

    PRI = "#2563eb"         # bleu moderne (primary)
    PRI_H = "#1d4ed8"

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
        QPushButton:disabled {{ color: #b0b8c4; background: #f8f9fa; border-color: #e2e8f0; }}

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
        QPushButton[class="ghost"]:disabled {{
            background: #f8f9fa;
            border: 1px solid #e2e8f0;
            color: #b0b8c4;
        }}

        QPushButton[class="secondary"] {{
            background: #f1f5f9;
            border: 1px solid #cbd5e1;
            color: #475569;
            font-weight: 500;
        }}
        QPushButton[class="secondary"]:hover {{ background: #e2e8f0; border-color: #94a3b8; }}

        QPushButton[class="outline"] {{
            background: #ffffff;
            border: 1.5px solid {cls.PRI};
            color: {cls.PRI};
            font-weight: 500;
        }}
        QPushButton[class="outline"]:hover {{ background: #eff6ff; border-color: {cls.PRI_H}; }}

        QPushButton[class="danger"] {{
            background: #ffffff;
            border: 1.5px solid #ef4444;
            color: #dc2626;
            font-weight: 500;
        }}
        QPushButton[class="danger"]:hover {{ background: #fef2f2; border-color: #b91c1c; }}

        QPushButton[size="sm"] {{
            padding: 4px 12px;
            font-size: 12px;
            border-radius: 6px;
            min-width: 76px;
        }}

        /* Inputs & listes */
        QComboBox, QLineEdit {{
            background: {cls.BG_TABLE};
            border: 1.5px solid {cls.BDR};
            border-radius: 8px;
            padding: 6px 10px;
            color: {cls.TXT};
        }}
        QComboBox:hover, QLineEdit:hover {{
            border-color: {cls.BDR_STRONG};
        }}
        QComboBox:focus, QLineEdit:focus {{
            border: 1.5px solid {cls.PRI};
            background: #ffffff;
        }}
        QDateEdit {{
            background: {cls.BG_TABLE};
            border: 1.5px solid {cls.BDR};
            border-radius: 8px;
            padding: 6px 10px;
            color: {cls.TXT};
        }}
        QDateEdit:hover {{ border-color: {cls.BDR_STRONG}; }}
        QDateEdit:focus {{ border: 1.5px solid {cls.PRI}; background: #ffffff; }}
        QSpinBox, QDoubleSpinBox, QTextEdit {{
            background: {cls.BG_TABLE};
            border: 1.5px solid {cls.BDR};
            border-radius: 8px;
            padding: 4px 8px;
            color: {cls.TXT};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
            border: 1.5px solid {cls.PRI};
        }}
        QListWidget {{
            background: {cls.BG_TABLE};
            border: 1px solid {cls.BDR};
            border-radius: 10px;
            padding: 4px;
        }}
        QListWidget::item {{ padding: 8px 10px; height: 28px; border-radius: 6px; }}
        QListWidget::item:hover {{ background: #f1f5f9; }}
        QListWidget::item:selected {{ background: #dbeafe; color: {cls.TXT}; }}
        QListView::item {{ border-bottom: 1px solid #f1f5f9; }}

        /* Tables / QAbstractItemView */
        QAbstractItemView {{
            background: {cls.BG_TABLE};
            color: {cls.TXT};
            gridline-color: {cls.BDR};
            selection-background-color: #dbeafe;
            selection-color: {cls.TXT};
            alternate-background-color: #f8fafc;
        }}
        QTableWidget {{ border: 1px solid {cls.BDR}; border-radius: 10px; }}
        QHeaderView::section {{
            background: #f1f5f9;
            color: {cls.TXT_DIM};
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            border: none;
            border-bottom: 2px solid {cls.BDR_STRONG};
            border-right: 1px solid {cls.BDR};
            padding: 8px 10px;
        }}
        QHeaderView::section:first {{ border-top-left-radius: 8px; }}
        QHeaderView::section:last {{ border-right: none; border-top-right-radius: 8px; }}
        
        /* Calendrier FIX */
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: {cls.BG_CARD}; 
            border-bottom: 1px solid {cls.BDR_STRONG};
        }}
        QCalendarWidget QToolButton {{
            color: {cls.TXT};
        }}
        
        /* FIX GRILLE: Assure que le jour sélectionné est bien visible (thème clair) */
        QCalendarWidget QAbstractItemView:enabled {{
            selection-background-color: #3b82f6; 
            selection-color: #ffffff; /* CORRECTION: Texte du jour sélectionné en blanc */
            color: {cls.TXT}; 
        }}
        /* FIX GRILLE: Assure que les jours estompés (disabled) sont lisibles */
        QCalendarWidget QAbstractItemView:disabled {{
            color: {cls.TXT_DIM}; /* Jours d'un autre mois en gris estompé */
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
        pal = app.palette()
        pal.setColor(QPalette.Window, QColor(cls.BG))
        pal.setColor(QPalette.WindowText, QColor(cls.TXT))
        pal.setColor(QPalette.Base, QColor(cls.BG_TABLE))
        pal.setColor(QPalette.AlternateBase, QColor("#f8fafc"))
        pal.setColor(QPalette.Text, QColor(cls.TXT))
        pal.setColor(QPalette.Button, QColor(cls.BG_CARD))
        pal.setColor(QPalette.ButtonText, QColor(cls.TXT))
        pal.setColor(QPalette.Highlight, QColor(cls.PRI))
        pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        # Couleurs spécifiques au calendrier
        pal.setColor(QPalette.Light, QColor(cls.BG_TABLE))
        pal.setColor(QPalette.Midlight, QColor(cls.BG_TABLE))
        app.setPalette(pal)
        # QSS global
        app.setStyleSheet(cls.qss())
        # Alternance de lignes sur tous les QTableWidget/QTableView créés après apply()
        from PyQt5.QtWidgets import QTableWidget, QTableView
        _orig_tw_init = QTableWidget.__init__
        _orig_tv_init = QTableView.__init__

        def _tw_init(self, *args, **kwargs):
            _orig_tw_init(self, *args, **kwargs)
            self.setAlternatingRowColors(True)

        def _tv_init(self, *args, **kwargs):
            _orig_tv_init(self, *args, **kwargs)
            self.setAlternatingRowColors(True)

        QTableWidget.__init__ = _tw_init
        QTableView.__init__ = _tv_init

# -------------------------------------------------------------------
# === Fonction utilitaire de Thème ===
# -------------------------------------------------------------------

def get_current_theme():
    return EmacTheme

# -------------------------------------------------------------------
# === Classes de Composants ===
# -------------------------------------------------------------------


class EmacCard(QFrame):
    """Conteneur carte avec entête optionnelle."""
    def __init__(self, title: str = None, subtitle: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
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
    """Carte avec indicateur coloré type alerte/succès."""
    COLORS_MAP = {
        'danger':  {'acc_key': 'ERR',  'dot': '#ef4444', 'bg': '#fef2f2'},
        'success': {'acc_key': 'ACC',  'dot': '#22c55e', 'bg': '#f0fdf4'},
        'warning': {'acc_key': 'WARN', 'dot': '#f59e0b', 'bg': '#fffbeb'},
        'info':    {'acc_key': 'PRI',  'dot': '#2563eb', 'bg': '#eff6ff'},
    }

    def __init__(self, title: str, variant: str = 'info', subtitle: str = None, parent=None):
        super().__init__(None, None, parent)

        c = self.COLORS_MAP.get(variant, self.COLORS_MAP['info'])
        dot_color = c['dot']

        header = QHBoxLayout()
        header.setSpacing(10)
        header.setContentsMargins(0, 0, 0, 0)

        # Indicateur coloré (point)
        dot = QFrame()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(
            f"background: {dot_color}; border-radius: 5px; border: none;"
        )
        header.addWidget(dot, 0, Qt.AlignVCenter)

        # Titre
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-weight: 600; font-size: 14px; color: {EmacTheme.TXT}; background: transparent;")
        header.addWidget(lbl, 0, Qt.AlignVCenter)
        header.addStretch(1)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet(f"color: {EmacTheme.TXT_DIM}; font-size: 12px; background: transparent;")
            header.addWidget(sub, 0, Qt.AlignRight | Qt.AlignVCenter)

        w = QWidget()
        w.setLayout(header)
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
    """Bouton avec tailles uniformes et variantes (primary/secondary/ghost/outline/danger)."""
    VARIANTS = ('primary', 'secondary', 'ghost', 'outline', 'danger')

    def __init__(self, text: str, variant: str = None, size: str = 'md', parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        if size == 'sm':
            self.setFixedHeight(32)
            self.setMinimumWidth(80)
            font = self.font()
            font.setPointSize(9)
            self.setFont(font)
            self.setProperty('size', 'sm')
        else:
            self.setFixedHeight(44)
        if variant in self.VARIANTS:
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

        # ----- STYLE selon variante -----
        if variant == "primary":
            self.setStyleSheet(f"""
                QToolButton {{
                    background: {EmacTheme.PRI};
                    border: 1px solid {EmacTheme.PRI};
                    border-radius: 12px;
                }}
                QToolButton:hover {{
                    background: {EmacTheme.PRI_H};
                    border-color: {EmacTheme.PRI_H};
                }}
                QToolButton:pressed {{
                    background: {EmacTheme.PRI_H};
                }}
            """)
            self._color_normal = QtGui.QColor(255, 255, 255)
            self._color_hover  = QtGui.QColor(255, 255, 255)
        else:
            self.setStyleSheet(f"""
                QToolButton {{
                    background: rgba(255,255,255,0.95);
                    border: 1px solid {EmacTheme.BDR};
                    border-radius: 12px;
                }}
                QToolButton:hover {{
                    background: #f0f2f7;
                    border-color: {EmacTheme.BDR_STRONG};
                }}
                QToolButton:pressed {{ background: #f0f2f7; }}
            """)
            self._color_normal = QtGui.QColor(EmacTheme.TXT)
            self._color_hover  = QtGui.QColor(EmacTheme.TXT)

        # Pictogramme
        self._bar_w = bar_width
        self._bar_h = bar_height
        self._gap   = gap
        self._hover = False
        self.setAttribute(QtCore.Qt.WA_Hover, True)
        

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
            rect = QRectF(cx - w / 2, cy - h / 2 + dy, w, h)
            path = QPainterPath()
            path.addRoundedRect(rect, h / 2, h / 2) # h/2 pour un bord complètement arrondi
            p.drawPath(path)
        p.end()


def make_primary(text: str) -> EmacButton:
    return EmacButton(text, variant='primary')