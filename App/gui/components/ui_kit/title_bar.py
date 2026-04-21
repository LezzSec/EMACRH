# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtGui, QtCore


class CustomTitleBar(QtWidgets.QWidget):
    """Barre de titre personnalisée avec boutons de contrôle Windows."""
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

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet("color: #000000; font-size: 12px; border: none;")
        layout.addWidget(self.title_label)
        layout.addStretch()

        btn_size = 46
        btn_height = 32

        self.btn_minimize = QtWidgets.QPushButton("―")
        self.btn_minimize.setFixedSize(btn_size, btn_height)
        self.btn_minimize.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #000000; font-size: 12px; }
            QPushButton:hover { background: #f3f4f6; }
        """)
        self.btn_minimize.clicked.connect(lambda: parent_dialog.showMinimized())
        layout.addWidget(self.btn_minimize)

        self.btn_maximize = QtWidgets.QPushButton("⛶")
        self.btn_maximize.setFixedSize(btn_size, btn_height)
        self.btn_maximize.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #000000; font-size: 14px; }
            QPushButton:hover { background: #f3f4f6; }
        """)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_maximize.setToolTip("Plein écran (F11)")
        layout.addWidget(self.btn_maximize)

        self.btn_close = QtWidgets.QPushButton("✕")
        self.btn_close.setFixedSize(btn_size, btn_height)
        self.btn_close.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #000000; font-size: 16px; }
            QPushButton:hover { background: #e81123; color: white; }
        """)
        self.btn_close.clicked.connect(lambda: parent_dialog.close())
        layout.addWidget(self.btn_close)

        self.dragging = False
        self.offset = None

    def toggle_maximize(self):
        if self.parent_dialog.isMaximized() or self.parent_dialog.isFullScreen():
            self.parent_dialog.showNormal()
            self.btn_maximize.setText("⛶")
        else:
            self.parent_dialog.showMaximized()
            self.btn_maximize.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPos() - self.parent_dialog.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.dragging and self.offset:
            self.parent_dialog.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.toggle_maximize()


def add_custom_title_bar(dialog, title=None):
    """
    Utilise la barre de titre système (FramelessWindowHint retiré).
    Retourne un widget vide pour ne pas casser les layouts existants.
    """
    flags = (QtCore.Qt.Window | QtCore.Qt.WindowSystemMenuHint
             | QtCore.Qt.WindowMinimizeButtonHint
             | QtCore.Qt.WindowMaximizeButtonHint
             | QtCore.Qt.WindowCloseButtonHint)
    dialog.setWindowFlags(flags)

    if title is not None:
        dialog.setWindowTitle(title)

    dialog.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)
    dialog.setAttribute(QtCore.Qt.WA_OpaquePaintEvent, False)

    placeholder = QtWidgets.QWidget(dialog)
    placeholder.setFixedHeight(0)
    placeholder.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    return placeholder


def add_fullscreen_button(dialog, button_parent=None, style="compact"):
    """
    Ajoute un bouton plein écran à un QDialog et retourne le bouton créé.

    Args:
        dialog: Le QDialog auquel ajouter la fonctionnalité plein écran
        button_parent: Layout ou widget parent où ajouter le bouton (optionnel)
        style: "compact" (Windows) ou "rounded"
    """
    if style == "compact":
        fullscreen_btn = QtWidgets.QPushButton("⛶")
        fullscreen_btn.setToolTip("Plein écran (F11)")
        fullscreen_btn.setFixedSize(46, 32)
        fullscreen_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none; color: #000000;
                font-size: 14px; font-weight: normal;
            }
            QPushButton:hover { background: #f3f4f6; }
            QPushButton:pressed { background: #e5e7eb; color: #6b7280; }
        """)
    else:
        fullscreen_btn = QtWidgets.QPushButton("⛶")
        fullscreen_btn.setToolTip("Basculer en plein écran (F11)")
        fullscreen_btn.setFixedSize(32, 32)
        fullscreen_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: 1px solid #e5e7eb;
                border-radius: 6px; font-size: 16px; color: #6b7280;
            }
            QPushButton:hover { background: #f3f4f6; border-color: #d1d5db; color: #111827; }
            QPushButton:pressed { background: #e5e7eb; }
        """)

    dialog._is_fullscreen = False
    dialog._previous_geometry = None

    def toggle_fullscreen():
        if not dialog._is_fullscreen:
            dialog._previous_geometry = dialog.geometry()
            dialog.showFullScreen()
            dialog._is_fullscreen = True
            fullscreen_btn.setText("⛶")
            fullscreen_btn.setToolTip("Quitter le plein écran (F11 ou Echap)")
        else:
            dialog.showNormal()
            if dialog._previous_geometry:
                dialog.setGeometry(dialog._previous_geometry)
            dialog._is_fullscreen = False
            fullscreen_btn.setText("⛶")
            fullscreen_btn.setToolTip("Basculer en plein écran (F11)")

    fullscreen_btn.clicked.connect(toggle_fullscreen)

    shortcut_f11 = QtWidgets.QShortcut(QtGui.QKeySequence("F11"), dialog)
    shortcut_f11.activated.connect(toggle_fullscreen)

    shortcut_esc = QtWidgets.QShortcut(QtGui.QKeySequence("Esc"), dialog)
    shortcut_esc.activated.connect(lambda: toggle_fullscreen() if dialog._is_fullscreen else None)

    if button_parent:
        if isinstance(button_parent, QtWidgets.QLayout):
            button_parent.addWidget(fullscreen_btn)
        elif hasattr(button_parent, 'layout') and button_parent.layout():
            button_parent.layout().addWidget(fullscreen_btn)

    return fullscreen_btn
