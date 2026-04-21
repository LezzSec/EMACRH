# -*- coding: utf-8 -*-
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from gui.screens.admin.historique.utils import get_action_config


class DetailDialog(QDialog):
    """Dialogue affichant les détails complets d'une action."""
    def __init__(self, row: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Détails de l'action")
        self.resize(600, 500)
        self.setStyleSheet("QDialog { background-color: #ffffff; color: #212121; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        action = (row.get("action") or "").upper()
        icon, action_text, color, bg_color = get_action_config(action)

        header = QLabel(f"{icon}  {action_text}")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setStyleSheet(f"color: {color}; padding: 12px; background-color: {bg_color}; border-radius: 6px;")
        layout.addWidget(header)

        dt_txt = str(row.get("date_time", ""))
        try:
            from datetime import datetime
            if not isinstance(dt_txt, str) and hasattr(dt_txt, "strftime"):
                dt_txt = row["date_time"].strftime("%d/%m/%Y à %H:%M:%S")
            else:
                try:
                    dt_txt = datetime.fromisoformat(dt_txt).strftime("%d/%m/%Y à %H:%M:%S")
                except Exception:
                    pass
        except Exception:
            pass

        date_label = QLabel(f"Date : {dt_txt}")
        date_label.setStyleSheet("font-size: 12px; color: #616161; padding: 4px;")
        layout.addWidget(date_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(sep)

        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: #ffffff;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(12)

        op_id = row.get("operateur_id")
        op_name = row.get('op_name') or ""
        if not op_name and op_id:
            try:
                data = json.loads(row.get("description", "{}"))
                op_name = data.get("operateur", f"#{op_id}")
            except (json.JSONDecodeError, ValueError):
                op_name = f"#{op_id}"
        if op_name:
            info_layout.addWidget(self._create_info_row("Personnel :", op_name))

        po_id = row.get("poste_id")
        po_name = row.get('po_name') or ""
        if not po_name and po_id:
            try:
                data = json.loads(row.get("description", "{}"))
                po_name = data.get("poste", f"#{po_id}")
            except (json.JSONDecodeError, ValueError):
                po_name = f"#{po_id}"
        if po_name:
            info_layout.addWidget(self._create_info_row("Poste :", po_name))

        utilisateur = row.get("utilisateur")
        if utilisateur:
            info_layout.addWidget(self._create_info_row("Effectué par :", utilisateur))

        table_name = row.get("table_name")
        if table_name:
            info_layout.addWidget(self._create_info_row("Table :", table_name))

        record_id = row.get("record_id")
        if record_id is not None:
            info_layout.addWidget(self._create_info_row("ID enregistrement :", str(record_id)))

        try:
            desc_str = row.get("description", "{}")
            try:
                data = json.loads(desc_str)
            except (json.JSONDecodeError, ValueError):
                if desc_str and desc_str.strip():
                    info_layout.addWidget(self._create_info_row("Description :", desc_str))
                data = {}

            if data:
                matricule = data.get("matricule")
                if matricule:
                    info_layout.addWidget(self._create_info_row("Matricule :", matricule))
                atelier = data.get("atelier")
                if atelier:
                    info_layout.addWidget(self._create_info_row("Atelier :", atelier))
                source = data.get("source")
                if source:
                    info_layout.addWidget(self._create_info_row("Source :", source))

            if action in ("CONNEXION", "DECONNEXION", "LOGOUT_TIMEOUT"):
                import re
                role_match = re.search(r'r[oô]le\s*:\s*([^\)]+)', desc_str, re.IGNORECASE)
                if role_match:
                    info_layout.addWidget(self._create_info_row("Rôle :", role_match.group(1).strip()))

                if action == "CONNEXION":
                    badge_text = "Session ouverte avec succès"
                    badge_style = "color: #1565c0; background-color: #e3f2fd; padding: 8px; border-radius: 4px; font-style: italic;"
                elif action == "DECONNEXION":
                    badge_text = "Session fermée normalement"
                    badge_style = "color: #37474f; background-color: #eceff1; padding: 8px; border-radius: 4px; font-style: italic;"
                else:
                    badge_text = "Session expirée après inactivité"
                    badge_style = "color: #6a1b9a; background-color: #f3e5f5; padding: 8px; border-radius: 4px; font-style: italic;"
                badge = QLabel(badge_text)
                badge.setWordWrap(True)
                badge.setStyleSheet(badge_style)
                info_layout.addWidget(badge)

            elif action == "INSERT" and data:
                niveau = data.get("niveau", "?")
                info_layout.addWidget(self._create_info_row("Niveau attribué :", f"Niveau {niveau}"))
                date_eval = data.get("date_evaluation")
                prochaine_eval = data.get("prochaine_evaluation")
                if date_eval:
                    info_layout.addWidget(self._create_info_row("Date d'évaluation :", date_eval))
                if prochaine_eval:
                    info_layout.addWidget(self._create_info_row("Prochaine évaluation :", prochaine_eval))
                info_text = QLabel("Un nouveau niveau de compétence a été attribué à cette personne pour ce poste.")
                info_text.setWordWrap(True)
                info_text.setStyleSheet("color: #757575; font-style: italic; padding: 8px; background-color: #f5f5f5; border-radius: 4px;")
                info_layout.addWidget(info_text)

            elif action == "UPDATE":
                changes = data.get("changes", {})
                if "niveau" in changes:
                    old = changes["niveau"].get("old", "?")
                    new = changes["niveau"].get("new", "?")

                    change_widget = QWidget()
                    change_layout = QHBoxLayout(change_widget)
                    change_layout.setContentsMargins(0, 0, 0, 0)
                    old_label = QLabel(f"Niveau {old}")
                    old_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336; padding: 8px; background-color: #ffebee; border-radius: 4px;")
                    change_layout.addWidget(old_label)
                    arrow = QLabel("→")
                    arrow.setStyleSheet("font-size: 24px; color: #757575;")
                    change_layout.addWidget(arrow)
                    new_label = QLabel(f"Niveau {new}")
                    new_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4caf50; padding: 8px; background-color: #e8f5e9; border-radius: 4px;")
                    change_layout.addWidget(new_label)
                    change_layout.addStretch()
                    info_layout.addWidget(change_widget)

                    try:
                        direction = "augmenté" if int(new) > int(old) else "diminué"
                    except (ValueError, TypeError):
                        direction = "modifié"
                    info_text = QLabel(f"Le niveau de compétence a été {direction}.")
                    info_text.setWordWrap(True)
                    info_text.setStyleSheet("color: #757575; font-style: italic; padding: 8px; background-color: #f5f5f5; border-radius: 4px;")
                    info_layout.addWidget(info_text)

                ancienne_date = data.get("ancienne_date_eval")
                nouvelle_date = data.get("nouvelle_date_eval")
                prochaine_eval = data.get("prochaine_evaluation")
                if ancienne_date or nouvelle_date:
                    if ancienne_date and nouvelle_date:
                        dates_text = f"Date d'évaluation : {ancienne_date} → {nouvelle_date}"
                    elif nouvelle_date:
                        dates_text = f"Nouvelle date d'évaluation : {nouvelle_date}"
                    else:
                        dates_text = ""
                    if dates_text:
                        dates_label = QLabel(dates_text)
                        dates_label.setStyleSheet("color: #616161; font-size: 11px; padding: 4px;")
                        info_layout.addWidget(dates_label)
                if prochaine_eval:
                    info_layout.addWidget(self._create_info_row("Prochaine évaluation :", prochaine_eval))

            elif action == "DELETE":
                niveau = data.get("niveau") or data.get("niveau_supprime", "?")
                info_layout.addWidget(self._create_info_row("Niveau supprimé :", f"Niveau {niveau}"))
                date_supprimee = data.get("date_eval_supprimee")
                if date_supprimee:
                    info_layout.addWidget(self._create_info_row("Date d'évaluation (supprimée) :", date_supprimee))
                info_text = QLabel("Cette compétence a été retirée de la personne pour ce poste.")
                info_text.setWordWrap(True)
                info_text.setStyleSheet("color: #757575; font-style: italic; padding: 8px; background-color: #f5f5f5; border-radius: 4px;")
                info_layout.addWidget(info_text)

        except Exception as e:
            error_label = QLabel(f"Impossible de charger les détails : {str(e)}")
            error_label.setStyleSheet("color: #d32f2f; padding: 8px;")
            info_layout.addWidget(error_label)

        info_layout.addStretch()
        layout.addWidget(info_widget, stretch=1)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2; color: white; border: none;
                padding: 10px 24px; border-radius: 4px;
                font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

    def _create_info_row(self, label: str, value: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-weight: bold; color: #424242; min-width: 140px;")
        layout.addWidget(label_widget)
        value_widget = QLabel(value)
        value_widget.setStyleSheet("color: #212121; font-size: 12px;")
        layout.addWidget(value_widget, stretch=1)
        return widget
