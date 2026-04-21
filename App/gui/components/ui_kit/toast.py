# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore


class ToastNotification(QtWidgets.QFrame):
    """
    Notification temporaire flottante (auto-dismiss).
    Créé via ToastManager, ne pas instancier directement.
    """
    _VARIANTS = {
        "success": ("#10b981", "#d1fae5", "#065f46", "✓"),
        "error":   ("#ef4444", "#fee2e2", "#991b1b", "✕"),
        "warning": ("#f59e0b", "#fef3c7", "#92400e", "⚠"),
        "info":    ("#3b82f6", "#dbeafe", "#1e3a8a", "ℹ"),
    }

    def __init__(self, message: str, variant: str = "info", duration_ms: int = 3500):
        super().__init__(None, QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

        border, bg, text_color, icon = self._VARIANTS.get(variant, self._VARIANTS["info"])
        self.setStyleSheet(f"""
            QFrame {{ background: {bg}; border-left: 4px solid {border}; border-radius: 10px; }}
        """)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        icon_lbl = QtWidgets.QLabel(icon)
        icon_lbl.setStyleSheet(f"color: {border}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        layout.addWidget(icon_lbl)

        msg_lbl = QtWidgets.QLabel(message)
        msg_lbl.setStyleSheet(f"color: {text_color}; font-size: 13px; background: transparent; border: none;")
        msg_lbl.setWordWrap(True)
        msg_lbl.setMaximumWidth(320)
        layout.addWidget(msg_lbl, 1)

        close_btn = QtWidgets.QPushButton("✕")
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; color: {text_color}; font-size: 12px; padding: 0; }}
            QPushButton:hover {{ background: rgba(0,0,0,0.1); border-radius: 4px; }}
        """)
        close_btn.clicked.connect(self._dismiss)
        layout.addWidget(close_btn)

        self.adjustSize()
        self.setWindowOpacity(0.0)

        self._fade_in = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self._fade_in.setDuration(200)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)

        QtCore.QTimer.singleShot(duration_ms, self._dismiss)

    def show(self):
        super().show()
        self._fade_in.start()

    def _dismiss(self):
        self._fade_out = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self._fade_out.setDuration(250)
        self._fade_out.setStartValue(self.windowOpacity())
        self._fade_out.setEndValue(0.0)
        self._fade_out.finished.connect(self.close)
        self._fade_out.start()


class ToastManager:
    """
    Affiche des notifications temporaires en bas à droite de l'écran.

    Usage:
        ToastManager.success("Enregistrement réussi")
        ToastManager.error("Erreur lors de la sauvegarde")
    """
    _active: list = []

    @classmethod
    def _show(cls, message: str, variant: str, duration_ms: int):
        cls._active = [t for t in cls._active if t.isVisible()]

        toast = ToastNotification(message, variant, duration_ms)

        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        margin = 16
        y_offset = sum(t.height() + 8 for t in cls._active)
        x = screen.right() - toast.sizeHint().width() - margin
        y = screen.bottom() - toast.sizeHint().height() - margin - y_offset

        toast.move(x, y)
        cls._active.append(toast)
        toast.show()

    @classmethod
    def success(cls, message: str, duration_ms: int = 3500):
        cls._show(message, "success", duration_ms)

    @classmethod
    def error(cls, message: str, duration_ms: int = 4500):
        cls._show(message, "error", duration_ms)

    @classmethod
    def warning(cls, message: str, duration_ms: int = 4000):
        cls._show(message, "warning", duration_ms)

    @classmethod
    def info(cls, message: str, duration_ms: int = 3000):
        cls._show(message, "info", duration_ms)
