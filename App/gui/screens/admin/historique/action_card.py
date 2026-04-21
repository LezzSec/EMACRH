# -*- coding: utf-8 -*-
import json
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QCursor

from gui.screens.admin.historique.utils import get_action_config, get_detailed_action_type, make_resume
from gui.screens.admin.historique.detail_dialog import DetailDialog


class ActionCard(QFrame):
    """Widget représentant une action sous forme de card moderne."""
    def __init__(self, row: dict, parent=None):
        super().__init__(parent)
        self.row = row

        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(0)

        action = (row.get("action") or "").upper()
        icon, _, icon_color, bg_color = get_action_config(action)
        border_color = icon_color

        self.setStyleSheet(f"""
            ActionCard {{
                background-color: {bg_color};
                border-left: 4px solid {border_color};
                border-radius: 6px;
                padding: 12px;
                margin: 4px 0px;
            }}
            ActionCard:hover {{
                background-color: {self._lighten_color(bg_color)};
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                cursor: pointer;
            }}
        """)

        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip("Cliquez pour voir les détails")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        icon_label.setStyleSheet(f"color: {icon_color}; background: transparent;")
        icon_label.setFixedWidth(40)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(6)

        resume = make_resume(row)
        title_label = QLabel(resume)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet("color: #212121; background: transparent;")
        title_label.setWordWrap(True)
        content_layout.addWidget(title_label)

        details_layout = QHBoxLayout()
        details_layout.setSpacing(20)

        dt_txt = str(row.get("date_time", ""))
        try:
            from datetime import datetime
            if not isinstance(dt_txt, str) and hasattr(dt_txt, "strftime"):
                dt_txt = row["date_time"].strftime("%d/%m/%Y à %H:%M")
            else:
                try:
                    dt_txt = datetime.fromisoformat(dt_txt).strftime("%d/%m/%Y à %H:%M")
                except Exception:
                    pass
        except Exception:
            pass

        time_label = QLabel(f"{dt_txt}")
        time_label.setStyleSheet("color: #757575; font-size: 10px; background: transparent;")
        details_layout.addWidget(time_label)

        action_type = get_detailed_action_type(row)
        type_label = QLabel(f"• {action_type}")
        type_label.setStyleSheet("color: #757575; font-size: 10px; background: transparent;")
        details_layout.addWidget(type_label)

        utilisateur = row.get("utilisateur")
        if utilisateur:
            user_label = QLabel(f"• Par: {utilisateur}")
            user_label.setStyleSheet("color: #1976d2; font-size: 10px; font-weight: bold; background: transparent;")
            details_layout.addWidget(user_label)

        details_layout.addStretch()
        content_layout.addLayout(details_layout)

        extra_parts = []
        table_name = row.get("table_name")
        if table_name:
            extra_parts.append(f"{table_name}")
        record_id = row.get("record_id")
        if record_id is not None:
            extra_parts.append(f"#ID {record_id}")

        if not row.get("operateur_id") and not row.get("poste_id"):
            raw_desc = row.get("description") or ""
            try:
                data = json.loads(raw_desc)
                excerpt = data.get("details") or data.get("description") or ""
            except (json.JSONDecodeError, ValueError):
                excerpt = raw_desc
            if excerpt and len(excerpt) > 2:
                max_len = 80
                excerpt_str = excerpt[:max_len] + ("…" if len(excerpt) > max_len else "")
                extra_parts.append(f"{excerpt_str}")

        if extra_parts:
            extra_layout = QHBoxLayout()
            extra_layout.setSpacing(12)
            extra_label = QLabel("  ".join(extra_parts))
            extra_label.setStyleSheet("color: #9e9e9e; font-size: 9px; background: transparent;")
            extra_label.setWordWrap(True)
            extra_layout.addWidget(extra_label)
            extra_layout.addStretch()
            content_layout.addLayout(extra_layout)

        layout.addLayout(content_layout, stretch=1)
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            dialog = DetailDialog(self.row, self)
            dialog.exec_()
        super().mousePressEvent(event)

    def _lighten_color(self, hex_color):
        color = QColor(hex_color)
        h, s, l, a = color.getHsl()
        return QColor.fromHsl(h, max(0, s - 10), min(255, l + 10), a).name()
