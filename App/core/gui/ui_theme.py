# -*- coding: utf-8 -*-
"""
Thème visuel EMAC — Variante CLAIRE (Light)
• Fond clair, cartes blanches, contrastes forts pour les listes/tableaux
• Widgets : EmacButton, EmacCard, EmacHeader (inchangés)

Usage (inchangé) :
from core.gui.ui_theme import EmacTheme, EmacButton, EmacCard, EmacHeader
EmacTheme.apply(app)
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame


class EmacTheme:
    """Palette + QSS centralisés (version claire)."""
    # Palette claire (neutres + accent très discret)
    BG = "#f6f7fb"          # fond application
    BG_CARD = "#ffffff"     # cartes
    BG_ELEV = "#fafbff"     # surfaces élevées
    BG_TABLE = "#ffffff"     # listes/tableaux

    TXT = "#111827"         # texte principal (très foncé)
    TXT_DIM = "#6b7280"     # texte secondaire

    BDR = "#e5e7eb"         # bordures
    BDR_STRONG = "#d1d5db"  # bordures en-tête table

    PRI = "#111827"         # couleur primaire (anthracite discret)
    PRI_H = "#0b1220"       # hover primaire (un poil plus foncé)

    ACC = "#059669"         # accent (succès) — peu utilisé
    WARN = "#d97706"
    ERR = "#dc2626"

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
            padding: 9px 14px;
            color: {cls.TXT};
        }}
        QPushButton:hover {{
            border-color: {cls.BDR_STRONG};
            background: {cls.BG_ELEV};
        }}
        QPushButton:pressed {{
            background: #f0f2f7;
        }}
        QPushButton[class="primary"] {{
            background: {cls.PRI};
            color: #ffffff;
            border: 1px solid {cls.PRI};
            font-weight: 600;
        }}
        QPushButton[class="primary"]:hover {{
            background: {cls.PRI_H};
            border-color: {cls.PRI_H};
        }}

        /* Inputs & listes */
        QComboBox, QListWidget {{
            background: {cls.BG_TABLE};
            border: 1px solid {cls.BDR};
            border-radius: 8px;
            padding: 6px 8px;
        }}
        QListWidget::item {{
            padding: 6px 10px;
            height: 28px;
        }}
        QListWidget::item:selected {{
            background: #e8eefc;    /* sélection lisible sur fond clair */
            color: {cls.TXT};
        }}

        /* Tables/génériques pour QAbstractItemView (QTableView, etc.) */
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
        '''

    @classmethod
    def apply(cls, app):
        # Police par défaut
        app.setFont(QFont('Segoe UI', 10))
        # Palette Qt (pour widgets natifs)
        pal = app.palette()
        pal.setColor(QPalette.Window, QColor(cls.BG))
        pal.setColor(QPalette.WindowText, QColor(cls.TXT))
        pal.setColor(QPalette.Base, QColor(cls.BG_TABLE))
        pal.setColor(QPalette.Text, QColor(cls.TXT))
        pal.setColor(QPalette.Button, QColor(cls.BG_CARD))
        pal.setColor(QPalette.ButtonText, QColor(cls.TXT))
        app.setPalette(pal)
        # QSS global
        app.setStyleSheet(cls.qss())


class EmacCard(QFrame):
    """Conteneur carte avec entête optionnelle."""
    def __init__(self, title: str = None, subtitle: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        if title:
            header = QHBoxLayout()
            lbl = QLabel(title)
            lbl.setProperty('class', 'h2')
            header.addWidget(lbl)
            header.addStretch(1)
            if subtitle:
                sub = QLabel(subtitle)
                sub.setProperty('class', 'muted')
                header.addWidget(sub, 0, Qt.AlignRight)
            wrap = QWidget(); wrap.setLayout(header)
            lay.addWidget(wrap)
        self.body = QVBoxLayout(); self.body.setSpacing(8)
        bodyw = QWidget(); bodyw.setLayout(self.body)
        lay.addWidget(bodyw)


class EmacStatusCard(EmacCard):
    """Carte avec bandeau coloré type alerte/succès, style pastel."""
    COLORS = {
        'danger': { 'bg': '#fee2e2', 'txt': '#991b1b', 'chip': '#fecaca', 'icon': '⚠️' },
        'success': { 'bg': '#dcfce7', 'txt': '#065f46', 'chip': '#bbf7d0', 'icon': '📅' },
        'info': { 'bg': '#e0f2fe', 'txt': '#075985', 'chip': '#bae6fd', 'icon': 'ℹ️' },
    }

    def __init__(self, title: str, variant: str = 'info', subtitle: str = None, parent=None):
        super().__init__(None, None, parent)
        c = self.COLORS.get(variant, self.COLORS['info'])
        # En-tête colorée
        header = QHBoxLayout(); header.setSpacing(8)
        pill = QLabel(f" {c['icon']}  {title}"); pill.setStyleSheet(
            f"background:{c['bg']}; color:{c['txt']}; font-weight:600; padding:6px 10px; border-radius:8px;")
        header.addWidget(pill, 0, Qt.AlignLeft)
        header.addStretch(1)
        if subtitle:
            sub = QLabel(subtitle); sub.setStyleSheet("color:#6b7280;")
            header.addWidget(sub, 0, Qt.AlignRight)
        w = QWidget(); w.setLayout(header)
        self.layout().insertWidget(0, w)

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
        root.setContentsMargins(0, 0, 16, 16)

        left = QVBoxLayout()
        left.setSpacing(2)

        h1 = QLabel(title)
        h1.setProperty('class', 'h1')
        left.addWidget(h1)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setProperty('class', 'muted')
            left.addWidget(sub)

        root.addLayout(left, 1)

        self.actions = QHBoxLayout()
        self.actions.setSpacing(8)
        root.addLayout(self.actions)

    def add_action(self, btn: QPushButton):
        self.actions.addWidget(btn)


class EmacButton(QPushButton):
    """Bouton avec tailles uniformes et variantes (primary)."""
    def __init__(self, text: str, variant: str = None, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(40)
        if variant == 'primary':
            self.setProperty('class', 'primary')


def make_primary(text: str) -> EmacButton:
    return EmacButton(text, variant='primary')
