# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore


class EmacBadge(QtWidgets.QLabel):
    """
    Badge de notification/compteur stylisé.

    Usage:
        badge = EmacBadge("12", variant="error")
    """
    def __init__(self, text: str = "0", variant: str = "default", parent=None):
        super().__init__(text, parent)
        self.setObjectName("EmacBadge")
        self.setAlignment(QtCore.Qt.AlignCenter)

        styles = {
            "default": ("background: #6b7280; color: #ffffff;", 4),
            "primary": ("background: #0f172a; color: #ffffff;", 6),
            "success": ("background: #10b981; color: #ffffff;", 6),
            "warning": ("background: #f59e0b; color: #111827;", 6),
            "error": ("background: #ef4444; color: #ffffff;", 6),
            "info": ("background: #3b82f6; color: #ffffff;", 6),
        }

        bg_color, padding = styles.get(variant, styles["default"])
        self.setStyleSheet(f"""
            QLabel#EmacBadge {{
                {bg_color}
                border-radius: 10px;
                padding: 2px {padding}px;
                font-size: 11px;
                font-weight: 600;
                min-width: 20px;
            }}
        """)
        self.setMinimumHeight(20)


class EmacAlert(QtWidgets.QFrame):
    """
    Bandeau d'alerte/information stylisé.

    Usage:
        alert = EmacAlert("Contrat expire dans 5 jours !", variant="warning")
    """
    def __init__(self, message: str, variant: str = "info", dismissible: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("EmacAlert")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        styles = {
            "success": ("#10b981", "#d1fae5", "#065f46"),
            "warning": ("#f59e0b", "#fef3c7", "#92400e"),
            "error": ("#ef4444", "#fee2e2", "#991b1b"),
            "info": ("#3b82f6", "#dbeafe", "#1e3a8a"),
        }
        border_color, bg_color, text_color = styles.get(variant, styles["info"])

        self.setStyleSheet(f"""
            QFrame#EmacAlert {{
                background: {bg_color};
                border-left: 4px solid {border_color};
                border-radius: 8px;
                padding: 12px 16px;
            }}
        """)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        icons = {"success": "✓", "warning": "⚠", "error": "✕", "info": "ℹ"}
        icon_label = QtWidgets.QLabel(icons.get(variant, "ℹ"))
        icon_label.setStyleSheet(f"color: {text_color}; font-size: 16px; font-weight: bold;")
        layout.addWidget(icon_label)

        message_label = QtWidgets.QLabel(message)
        message_label.setStyleSheet(f"color: {text_color}; font-size: 13px;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label, 1)

        if dismissible:
            close_btn = QtWidgets.QPushButton("✕")
            close_btn.setFixedSize(20, 20)
            close_btn.setCursor(QtCore.Qt.PointingHandCursor)
            close_btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; color: {text_color}; font-size: 16px; }}
                QPushButton:hover {{ background: rgba(0, 0, 0, 0.1); border-radius: 4px; }}
            """)
            close_btn.clicked.connect(lambda: self.setVisible(False))
            layout.addWidget(close_btn)


class EmacChip(QtWidgets.QLabel):
    """
    Tag/Chip stylisé pour catégories, niveaux, etc.

    Usage:
        chip = EmacChip("Niveau 3", variant="success")
    """
    closed = QtCore.pyqtSignal()

    def __init__(self, text: str, variant: str = "default", closable: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("EmacChip")

        self._container = QtWidgets.QWidget(self)
        self._layout = QtWidgets.QHBoxLayout(self._container)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(4)

        styles = {
            "default": ("#6b7280", "#f3f4f6", "#111827"),
            "primary": ("#0f172a", "#e8eefc", "#0f172a"),
            "success": ("#10b981", "#d1fae5", "#065f46"),
            "warning": ("#f59e0b", "#fef3c7", "#92400e"),
            "error": ("#ef4444", "#fee2e2", "#991b1b"),
            "info": ("#3b82f6", "#dbeafe", "#1e3a8a"),
            "niveau1": ("#ef4444", "#fee2e2", "#991b1b"),
            "niveau2": ("#f59e0b", "#fef3c7", "#92400e"),
            "niveau3": ("#3b82f6", "#dbeafe", "#1e3a8a"),
            "niveau4": ("#10b981", "#d1fae5", "#065f46"),
        }
        border_color, bg_color, text_color = styles.get(variant, styles["default"])

        self.setStyleSheet(f"""
            QLabel#EmacChip {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }}
        """)

        text_label = QtWidgets.QLabel(text)
        text_label.setStyleSheet(f"color: {text_color}; border: none; background: transparent;")
        self._layout.addWidget(text_label)

        if closable:
            close_btn = QtWidgets.QPushButton("✕")
            close_btn.setFixedSize(14, 14)
            close_btn.setCursor(QtCore.Qt.PointingHandCursor)
            close_btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; color: {text_color}; font-size: 12px; padding: 0; }}
                QPushButton:hover {{ background: rgba(0, 0, 0, 0.1); border-radius: 7px; }}
            """)
            close_btn.clicked.connect(lambda: (self.setVisible(False), self.closed.emit()))
            self._layout.addWidget(close_btn)

        self._container.adjustSize()
        self.setFixedSize(self._container.sizeHint())
