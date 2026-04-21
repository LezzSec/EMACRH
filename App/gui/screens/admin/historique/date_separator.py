# -*- coding: utf-8 -*-
import datetime as dt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt5.QtGui import QFont


class DateSeparator(QWidget):
    """En-tête de date pour la timeline de l'historique."""
    _MONTHS_FR = [
        "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
    ]
    _DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    def __init__(self, date_val, count: int = 0, parent=None):
        super().__init__(parent)

        if hasattr(date_val, 'weekday'):
            today     = dt.date.today()
            yesterday = today - dt.timedelta(days=1)
            day_name  = self._DAYS_FR[date_val.weekday()]
            month     = self._MONTHS_FR[date_val.month]
            base_str  = f"{day_name} {date_val.day} {month} {date_val.year}"
            if date_val == today:
                date_str = f"Aujourd'hui  —  {base_str}"
            elif date_val == yesterday:
                date_str = f"Hier  —  {base_str}"
            else:
                date_str = base_str
        else:
            date_str = str(date_val)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 18, 4, 6)
        layout.setSpacing(10)

        dot = QLabel("◆")
        dot.setFont(QFont("Segoe UI", 9))
        dot.setStyleSheet("color: #1976d2; background: transparent;")
        dot.setFixedWidth(14)
        layout.addWidget(dot)

        lbl = QLabel(date_str)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl.setStyleSheet("color: #1565c0; background: transparent;")
        layout.addWidget(lbl)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("QFrame { background-color: #bbdefb; border: none; }")
        layout.addWidget(line, stretch=1)

        if count > 0:
            badge = QLabel(f"  {count} action{'s' if count > 1 else ''}  ")
            badge.setStyleSheet(
                "background-color: #e3f2fd; color: #1565c0;"
                "border: 1px solid #90caf9; border-radius: 10px;"
                "font-size: 10px; padding: 2px 8px;"
            )
            layout.addWidget(badge)

        self.setStyleSheet("background: transparent;")
