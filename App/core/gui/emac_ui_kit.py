# -*- coding: utf-8 -*-
"""
EMAC UI KIT – PyQt5
Composants et thèmes réutilisables pour garder la même identité visuelle partout.

Contenu :
- get_stylesheet(theme="light"|"dark") → QSS prêt à appliquer sur QApplication ou un widget racine
- Card(QFrame) → carte avec ombre, coins arrondis, header (title/subtitle) et body
- TopBar(QFrame) → barre supérieure avec titre, champ de recherche, actions
- SideNav(QFrame) → barre latérale avec boutons de navigation checkables
- apply_shadow(widget, radius=24, y_offset=8, alpha=40) → ombre douce

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
QWidget { color: {TXT}; }

/* SideNav */
#SideNav { background: {SIDE_BG}; border-right: 1px solid {BORDER}; }
#SideNav QPushButton {
    color: {TXT_MUTED}; text-align: left; padding: 10px 14px; border: none; border-radius: 10px;
}
#SideNav QPushButton:hover { background: {HOVER}; color: {TXT}; }
#SideNav QPushButton:checked { background: {ACCENT_SOFT}; color: {ACCENT_TXT}; }

/* TopBar */
#TopBar { background: {TOP_BG}; border-bottom: 1px solid {BORDER}; }
#TitleLabel { color: {TXT}; font-size: 18px; font-weight: 600; }

/* Inputs */
QLineEdit, QComboBox, QDateEdit, QTextEdit {
    background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 10px; padding: 8px 10px; color: {TXT};
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus { border: 1px solid {ACCENT}; }

/* Buttons */
QPushButton#Primary { background: {ACCENT}; color: white; border: none; border-radius: 12px; padding: 10px 14px; font-weight: 600; }
QPushButton#Primary:disabled { background: {DISABLED_BG}; color: {DISABLED_TXT}; }
QPushButton#Soft { background: {ACCENT_SOFT}; color: {ACCENT_TXT}; border: none; border-radius: 12px; padding: 10px 14px; font-weight: 600; }

/* Tables */
QTableWidget, QTableView { background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 12px; gridline-color: {BORDER}; }
QHeaderView::section { background: {SIDE_BG}; color: {TXT}; border: none; padding: 8px; }

/* Cards */
#Card { background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 16px; }
#CardTitle { color: {TXT}; font-weight: 600; }
#CardSub { color: {TXT_MUTED}; }

/* Scrollbar */
QScrollBar:vertical { background: transparent; width: 10px; margin: 10px 0; }
QScrollBar::handle:vertical { background: {SCROLL}; border-radius: 5px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

_THEME_LIGHT = {
    "BG": "#F6F7FB",
    "TOP_BG": "#FFFFFF",
    "SIDE_BG": "#FFFFFF",
    "CARD_BG": "#FFFFFF",
    "BORDER": "#E5E7EB",
    "TXT": "#111827",
    "TXT_MUTED": "#6B7280",
    "ACCENT": "#2563EB",
    "ACCENT_SOFT": "#DBEAFE",
    "ACCENT_TXT": "#1E3A8A",
    "HOVER": "#F3F4F6",
    "DISABLED_BG": "#E5E7EB",
    "DISABLED_TXT": "#9CA3AF",
    "SCROLL": "#D1D5DB",
}

_THEME_DARK = {
    "BG": "#0B0F14",
    "TOP_BG": "#0F172A",
    "SIDE_BG": "#0F172A",
    "CARD_BG": "#111827",
    "BORDER": "#1F2937",
    "TXT": "#E5E7EB",
    "TXT_MUTED": "#9CA3AF",
    "ACCENT": "#3B82F6",
    "ACCENT_SOFT": "#1E3A8A",
    "ACCENT_TXT": "#BFDBFE",
    "HOVER": "#111827",
    "DISABLED_BG": "#374151",
    "DISABLED_TXT": "#9CA3AF",
    "SCROLL": "#374151",
}


def get_stylesheet(theme: str = "light") -> str:
    """Retourne un QSS prêt à appliquer. theme in {"light", "dark"}."""
    tokens = _THEME_LIGHT if theme.lower() == "light" else _THEME_DARK
    return _THEME_BASE.format(**tokens)


# =============================
# Helpers
# =============================

def apply_shadow(widget: QtWidgets.QWidget, radius: int = 24, y_offset: int = 8, alpha: int = 40):
    shadow = QtWidgets.QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(radius)
    shadow.setXOffset(0)
    shadow.setYOffset(y_offset)
    shadow.setColor(QtGui.QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


# =============================
# Composants
# =============================

class Card(QtWidgets.QFrame):
    """Carte réutilisable. Contient body_layout pour y placer votre contenu."""
    def __init__(self, title: str = "", subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        if title:
            ttl = QtWidgets.QLabel(title, objectName="CardTitle")
            ttl.setWordWrap(True)
            lay.addWidget(ttl)
        if subtitle:
            sub = QtWidgets.QLabel(subtitle, objectName="CardSub")
            sub.setWordWrap(True)
            lay.addWidget(sub)

        apply_shadow(self)

        self.body = QtWidgets.QWidget(self)
        lay.addWidget(self.body)
        self.body_layout = QtWidgets.QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(8)


class TopBar(QtWidgets.QFrame):
    """Barre supérieure standard avec titre + recherche + 2 actions.
    Tu peux masquer des éléments si tu n'en veux pas.
    """
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(10)

        self.title = QtWidgets.QLabel(title, objectName="TitleLabel")
        lay.addWidget(self.title, 0, QtCore.Qt.AlignVCenter)
        lay.addStretch(1)

        self.search = QtWidgets.QLineEdit(); self.search.setPlaceholderText("Rechercher…"); self.search.setFixedWidth(280)
        self.btnTheme = QtWidgets.QPushButton("🌓 Thème", objectName="Soft")
        self.btnPrimary = QtWidgets.QPushButton("✔ Action", objectName="Primary")

        lay.addWidget(self.search)
        lay.addWidget(self.btnTheme)
        lay.addWidget(self.btnPrimary)


class SideNav(QtWidgets.QFrame):
    """Barre de navigation latérale. Emet le signal navigate(index)."""
    navigate = QtCore.pyqtSignal(int)

    def __init__(self, labels=None, title="EMAC • Console", parent=None):
        super().__init__(parent)
        self.setObjectName("SideNav")
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 16, 12, 16)
        lay.setSpacing(8)

        # Brand
        brand = QtWidgets.QLabel(title)
        font = brand.font(); font.setPointSize(14); font.setBold(True)
        brand.setFont(font)
        lay.addWidget(brand)
        lay.addSpacing(8)

        # Nav buttons
        self.btns = []
        labels = labels or ["📊 Dashboard", "🧰 Gestion", "🗂 Historique"]
        for i, text in enumerate(labels):
            b = QtWidgets.QPushButton(text)
            b.setCheckable(True)
            b.clicked.connect(lambda _, idx=i: self._on_click(idx))
            lay.addWidget(b)
            self.btns.append(b)
        if self.btns:
            self.btns[0].setChecked(True)

        lay.addStretch(1)

    def _on_click(self, idx: int):
        for i, b in enumerate(self.btns):
            b.setChecked(i == idx)
        self.navigate.emit(idx)


# =============================
# Démo locale (facultatif)
# =============================
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet("light"))

    win = QtWidgets.QMainWindow()
    win.resize(1100, 720)

    wrapper = QtWidgets.QWidget(); root = QtWidgets.QHBoxLayout(wrapper); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

    sidenav = SideNav()
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
    blay.addWidget(c3, 0, 2)

    big = Card("Vue générale"); big.body_layout.addWidget(QtWidgets.QLabel("(Graphique ou calendrier ici)"))
    blay.addWidget(big, 1, 0, 1, 3)

    rlay.addWidget(body)

    root.addWidget(right, 1)
    win.setCentralWidget(wrapper)

    win.show()
    sys.exit(app.exec_())
