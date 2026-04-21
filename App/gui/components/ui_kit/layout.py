# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore


class Card(QtWidgets.QFrame):
    """Conteneur carte avec coins arrondis."""
    def __init__(self, title: str = None, subtitle: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setFrameShadow(QtWidgets.QFrame.Plain)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        self.body_layout = QtWidgets.QVBoxLayout()
        self.body_layout.setSpacing(8)
        bodyw = QtWidgets.QWidget()
        bodyw.setLayout(self.body_layout)

        if title:
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
        self.title_label.setObjectName("TopBarTitle")

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
        self.nav_area.addWidget(btn)

    def add_action_button(self, btn: SideNavButton):
        self.actions_area.addWidget(btn)
