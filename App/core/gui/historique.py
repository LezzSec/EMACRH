from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QFrame, QDateEdit, QMessageBox, QComboBox, QSizePolicy,
    QTextEdit, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QPalette, QCursor

from core.services.historique_service import fetch_historique_paginated, delete_historique_range, MODULE_TABLES
from core.services.log_exporter import export_day
from core.gui.emac_ui_kit import add_custom_title_bar, show_error_message
from core.gui.db_worker import DbWorker, DbThreadPool
from core.gui.loading_components import LoadingLabel
from core.utils.logging_config import get_logger

import json
import datetime as dt
import os
from itertools import groupby

logger = get_logger(__name__)

_PAGE_SIZE = 100  # Nombre de cards chargées par page

# --- Fonctions utilitaires (garder vos fonctions existantes) ---
ACTION_LABEL = {
    "INSERT": "Ajout",
    "UPDATE": "Modification",
    "DELETE": "Suppression",
    "ERROR":  "Erreur",
}

# Mapping action → (icône, libellé, couleur texte, couleur fond clair)
ACTION_CONFIG = {
    "INSERT":         ("✚",  "Ajout de compétence",     "#4caf50", "#e8f5e9"),
    "UPDATE":         ("✏️", "Modification de compétence","#f57f17", "#fff8e1"),
    "DELETE":         ("✕",  "Suppression de compétence","#f44336", "#ffebee"),
    "ERROR":          ("⚠",  "Erreur",                  "#d32f2f", "#ffebee"),
    "CONNEXION":      ("🔐", "Connexion utilisateur",    "#1976d2", "#e3f2fd"),
    "DECONNEXION":    ("🚪", "Déconnexion utilisateur",  "#455a64", "#eceff1"),
    "LOGOUT_TIMEOUT": ("⏱",  "Déconnexion automatique", "#7b1fa2", "#f3e5f5"),
}
_ACTION_CONFIG_DEFAULT = ("ℹ️", "Action",              "#616161", "#f5f5f5")

def get_action_config(action: str) -> tuple:
    """Retourne (icône, libellé, couleur, couleur_fond) pour un type d'action."""
    return ACTION_CONFIG.get((action or "").upper(), _ACTION_CONFIG_DEFAULT)

def fr_action(a: str) -> str:
    return ACTION_LABEL.get((a or "").upper(), a or "")

# get_entity_name est importé depuis core.services.historique_service

def get_detailed_action_type(row: dict) -> str:
    action = row.get("action", "")
    desc = row.get("description") or ""

    try:
        data = json.loads(desc)

        if action.upper() == "INSERT":
            niveau = data.get("niveau", "?")
            return f"Ajout (N{niveau})"

        elif action.upper() == "UPDATE":
            changes = data.get("changes", {})
            if "niveau" in changes:
                old = changes["niveau"].get("old", "?")
                new = changes["niveau"].get("new", "?")
                return f"Modification (N{old}→N{new})"
            else:
                return "Modification"

        elif action.upper() == "DELETE":
            niveau = data.get("niveau", "?")
            return f"Suppression (N{niveau})"

    except (json.JSONDecodeError, ValueError):
        pass

    return fr_action(action)

def make_resume(row: dict) -> str:
    action = row.get("action", "")
    op_id = row.get("operateur_id")
    po_id = row.get("poste_id")
    desc = row.get("description") or ""

    # Noms déjà résolus par le JOIN dans fetch_historique_paginated — pas de requête N+1
    op_name = row.get('op_name') or (f"#{op_id}" if op_id else None)
    po_name = row.get('po_name') or (f"Poste #{po_id}" if po_id else None)

    try:
        data = json.loads(desc)
    except (json.JSONDecodeError, ValueError):
        # Si la description n'est pas du JSON, retourner un résumé simple
        if desc:
            return desc[:100] + ("..." if len(desc) > 100 else "")
        return fr_action(action)

    try:
        
        if "operateur" in data:
            op_name = data["operateur"]
        if "poste" in data:
            po_name = data["poste"]
        
        if action.upper() == "INSERT":
            niveau = data.get("niveau", "?")
            return f"{op_name} ➜ {po_name} : ✚ Niveau {niveau} (nouveau)"
        
        elif action.upper() == "UPDATE":
            changes = data.get("changes", {})
            if "niveau" in changes:
                old = changes["niveau"].get("old", "?")
                new = changes["niveau"].get("new", "?")
                return f"{op_name} ➜ {po_name} : Niveau {old} → {new}"
            else:
                return f"{op_name} ➜ {po_name} : Modifié"
        
        elif action.upper() == "DELETE":
            niveau = data.get("niveau", "?")
            return f"{op_name} ➜ {po_name} : ✕ Niveau {niveau} (supprimé)"
        
    except Exception as e:
        pass
    
    parts = []
    if op_name:
        parts.append(op_name)
    elif op_id:
        parts.append(f"#{op_id}")
    
    if po_name:
        parts.append(po_name)
    elif po_id:
        parts.append(f"Poste #{po_id}")
    
    if parts:
        return " ➜ ".join(parts)
    
    return f"Action : {action}"


class DetailDialog(QDialog):
    """
    Dialogue affichant les détails complets d'une action
    """
    def __init__(self, row: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Détails de l'action")
        self.resize(600, 500)

        self.setStyleSheet("QDialog { background-color: #ffffff; color: #212121; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # En-tête avec type d'action
        action = row.get("action", "").upper()
        icon, action_text, color, bg_color = get_action_config(action)

        header = QLabel(f"{icon}  {action_text}")
        header_font = QFont("Segoe UI", 16, QFont.Bold)
        header.setFont(header_font)
        header.setStyleSheet(
            f"color: {color}; padding: 12px; background-color: {bg_color}; border-radius: 6px;"
        )
        layout.addWidget(header)
        
        # Date et heure
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
        
        date_label = QLabel(f"📅 Date : {dt_txt}")
        date_label.setStyleSheet("font-size: 12px; color: #616161; padding: 4px;")
        layout.addWidget(date_label)
        
        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(sep)
        
        # Informations détaillées
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: #ffffff;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(12)
        
        # Opérateur (n'afficher que s'il y en a un)
        op_id = row.get("operateur_id")
        # Nom résolu par le JOIN — pas de requête N+1
        op_name = row.get('op_name') or ""
        if not op_name and op_id:
            try:
                data = json.loads(row.get("description", "{}"))
                op_name = data.get("operateur", f"#{op_id}")
            except (json.JSONDecodeError, ValueError):
                op_name = f"#{op_id}"

        # N'afficher la ligne Opérateur que si on a un nom valide
        if op_name:
            op_label = self._create_info_row("👤 Opérateur :", op_name)
            info_layout.addWidget(op_label)

        # Poste (n'afficher que s'il y en a un)
        po_id = row.get("poste_id")
        po_name = row.get('po_name') or ""
        if not po_name and po_id:
            try:
                data = json.loads(row.get("description", "{}"))
                po_name = data.get("poste", f"#{po_id}")
            except (json.JSONDecodeError, ValueError):
                po_name = f"#{po_id}"

        # N'afficher la ligne Poste que si on a un nom valide
        if po_name:
            po_label = self._create_info_row("📍 Poste :", po_name)
            info_layout.addWidget(po_label)

        # Utilisateur (qui a effectué l'action)
        utilisateur = row.get("utilisateur")
        if utilisateur:
            user_label = self._create_info_row("👨‍💼 Effectué par :", utilisateur)
            info_layout.addWidget(user_label)

        # Table et record modifiés
        table_name = row.get("table_name")
        if table_name:
            info_layout.addWidget(self._create_info_row("🗃 Table :", table_name))

        record_id = row.get("record_id")
        if record_id is not None:
            info_layout.addWidget(self._create_info_row("🔑 ID enregistrement :", str(record_id)))

        # Détails selon le type d'action
        try:
            desc_str = row.get("description", "{}")
            # Tenter de parser en JSON, sinon traiter comme texte simple
            try:
                data = json.loads(desc_str)
            except (json.JSONDecodeError, ValueError):
                # Si ce n'est pas du JSON, afficher le texte brut
                if desc_str and desc_str.strip():
                    desc_label = self._create_info_row("📝 Description :", desc_str)
                    info_layout.addWidget(desc_label)
                data = {}

            # === Informations complémentaires (matricule, atelier, source) ===
            if data:
                # Matricule
                matricule = data.get("matricule")
                if matricule:
                    info_layout.addWidget(self._create_info_row("🔢 Matricule :", matricule))

                # Atelier
                atelier = data.get("atelier")
                if atelier:
                    info_layout.addWidget(self._create_info_row("🏭 Atelier :", atelier))

                # Source de la modification
                source = data.get("source")
                if source:
                    info_layout.addWidget(self._create_info_row("📍 Source :", source))

            # === Détails spécifiques : sessions (CONNEXION / DECONNEXION / LOGOUT_TIMEOUT) ===
            if action in ("CONNEXION", "DECONNEXION", "LOGOUT_TIMEOUT"):
                import re
                # La description est du texte libre, ex:
                # "Connexion de l'utilisateur admin (rôle: admin)"
                # Extraire rôle si présent
                role_match = re.search(r'r[oô]le\s*:\s*([^\)]+)', desc_str, re.IGNORECASE)
                if role_match:
                    role_val = role_match.group(1).strip()
                    info_layout.addWidget(self._create_info_row("🎭 Rôle :", role_val))

                # Badge visuel selon le type de session
                if action == "CONNEXION":
                    badge_text = "Session ouverte avec succès"
                    badge_style = "color: #1565c0; background-color: #e3f2fd; padding: 8px; border-radius: 4px; font-style: italic;"
                elif action == "DECONNEXION":
                    badge_text = "Session fermée normalement"
                    badge_style = "color: #37474f; background-color: #eceff1; padding: 8px; border-radius: 4px; font-style: italic;"
                else:  # LOGOUT_TIMEOUT
                    badge_text = "Session expirée après inactivité"
                    badge_style = "color: #6a1b9a; background-color: #f3e5f5; padding: 8px; border-radius: 4px; font-style: italic;"

                badge = QLabel(badge_text)
                badge.setWordWrap(True)
                badge.setStyleSheet(badge_style)
                info_layout.addWidget(badge)

            # === Détails spécifiques selon le type d'action ===
            elif action == "INSERT" and data:
                niveau = data.get("niveau", "?")
                niveau_label = self._create_info_row("⭐ Niveau attribué :", f"Niveau {niveau}")
                info_layout.addWidget(niveau_label)

                # Dates d'évaluation
                date_eval = data.get("date_evaluation")
                prochaine_eval = data.get("prochaine_evaluation")
                if date_eval:
                    info_layout.addWidget(self._create_info_row("📅 Date d'évaluation :", date_eval))
                if prochaine_eval:
                    info_layout.addWidget(self._create_info_row("📆 Prochaine évaluation :", prochaine_eval))

                info_text = QLabel("Un nouveau niveau de compétence a été attribué à cet opérateur pour ce poste.")
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

                # Dates d'évaluation pour UPDATE
                ancienne_date = data.get("ancienne_date_eval")
                nouvelle_date = data.get("nouvelle_date_eval")
                prochaine_eval = data.get("prochaine_evaluation")

                if ancienne_date or nouvelle_date:
                    dates_text = ""
                    if ancienne_date and nouvelle_date:
                        dates_text = f"Date d'évaluation : {ancienne_date} → {nouvelle_date}"
                    elif nouvelle_date:
                        dates_text = f"Nouvelle date d'évaluation : {nouvelle_date}"
                    if dates_text:
                        dates_label = QLabel(dates_text)
                        dates_label.setStyleSheet("color: #616161; font-size: 11px; padding: 4px;")
                        info_layout.addWidget(dates_label)

                if prochaine_eval:
                    info_layout.addWidget(self._create_info_row("📆 Prochaine évaluation :", prochaine_eval))

            elif action == "DELETE":
                niveau = data.get("niveau") or data.get("niveau_supprime", "?")
                niveau_label = self._create_info_row("⭐ Niveau supprimé :", f"Niveau {niveau}")
                info_layout.addWidget(niveau_label)

                # Date d'évaluation supprimée
                date_supprimee = data.get("date_eval_supprimee")
                if date_supprimee:
                    info_layout.addWidget(self._create_info_row("📅 Date d'évaluation (supprimée) :", date_supprimee))

                info_text = QLabel("Cette compétence a été retirée de l'opérateur pour ce poste.")
                info_text.setWordWrap(True)
                info_text.setStyleSheet("color: #757575; font-style: italic; padding: 8px; background-color: #f5f5f5; border-radius: 4px;")
                info_layout.addWidget(info_text)
        
        except Exception as e:
            error_label = QLabel(f"Impossible de charger les détails : {str(e)}")
            error_label.setStyleSheet("color: #d32f2f; padding: 8px;")
            info_layout.addWidget(error_label)
        
        info_layout.addStretch()
        layout.addWidget(info_widget, stretch=1)
        
        # Bouton fermer
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
    
    def _create_info_row(self, label: str, value: str) -> QWidget:
        """Crée une ligne d'information formatée"""
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


class ActionCard(QFrame):
    """
    Widget représentant une action sous forme de card moderne
    """
    def __init__(self, row: dict, parent=None):
        super().__init__(parent)
        self.row = row
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(0)
        
        # Styles selon le type d'action
        action = row.get("action", "").upper()
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
        
        # Rendre la card cliquable
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip("Cliquez pour voir les détails")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # --- Icône ---
        icon_label = QLabel(icon)
        icon_font = QFont("Segoe UI", 24, QFont.Bold)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet(f"color: {icon_color}; background: transparent;")
        icon_label.setFixedWidth(40)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # --- Contenu principal ---
        content_layout = QVBoxLayout()
        content_layout.setSpacing(6)
        
        # Titre : résumé de l'action
        resume = make_resume(row)
        title_label = QLabel(resume)
        title_font = QFont("Segoe UI", 11, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #212121; background: transparent;")
        title_label.setWordWrap(True)
        content_layout.addWidget(title_label)
        
        # Détails secondaires
        details_layout = QHBoxLayout()
        details_layout.setSpacing(20)
        
        # Date/Heure
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
        
        time_label = QLabel(f"🕐 {dt_txt}")
        time_label.setStyleSheet("color: #757575; font-size: 10px; background: transparent;")
        details_layout.addWidget(time_label)
        
        # Type d'action détaillé
        action_type = get_detailed_action_type(row)
        type_label = QLabel(f"• {action_type}")
        type_label.setStyleSheet("color: #757575; font-size: 10px; background: transparent;")
        details_layout.addWidget(type_label)

        # Utilisateur (qui a effectué l'action)
        utilisateur = row.get("utilisateur")
        if utilisateur:
            user_label = QLabel(f"• Par: {utilisateur}")
            user_label.setStyleSheet("color: #1976d2; font-size: 10px; font-weight: bold; background: transparent;")
            details_layout.addWidget(user_label)

        details_layout.addStretch()
        content_layout.addLayout(details_layout)

        # --- Ligne secondaire : table, record_id, extrait description ---
        extra_parts = []

        table_name = row.get("table_name")
        if table_name:
            extra_parts.append(f"🗃 {table_name}")

        record_id = row.get("record_id")
        if record_id is not None:
            extra_parts.append(f"#ID {record_id}")

        # Extrait de description pour les entrées sans opérateur/poste (ex: CONNEXION, admin)
        if not row.get("operateur_id") and not row.get("poste_id"):
            raw_desc = row.get("description") or ""
            # Tenter de lire le champ "details" dans le JSON, sinon tronquer le texte brut
            try:
                data = json.loads(raw_desc)
                excerpt = data.get("details") or data.get("description") or ""
            except (json.JSONDecodeError, ValueError):
                excerpt = raw_desc
            if excerpt and len(excerpt) > 2:
                max_len = 80
                excerpt_str = excerpt[:max_len] + ("…" if len(excerpt) > max_len else "")
                extra_parts.append(f"📝 {excerpt_str}")

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

        # Ajuster la hauteur
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
    def mousePressEvent(self, event):
        """Ouvre le dialogue détaillé au clic"""
        if event.button() == Qt.LeftButton:
            dialog = DetailDialog(self.row, self)
            dialog.exec_()
        super().mousePressEvent(event)
    
    def _lighten_color(self, hex_color):
        """Éclaircit légèrement une couleur pour l'effet hover"""
        color = QColor(hex_color)
        h, s, l, a = color.getHsl()
        return QColor.fromHsl(h, max(0, s - 10), min(255, l + 10), a).name()


class DateSeparator(QWidget):
    """
    En-tête de date pour la timeline de l'historique.
    Affiche le jour en français avec un marqueur ◆ et une ligne horizontale.
    """
    _MONTHS_FR = [
        "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
    ]
    _DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    def __init__(self, date_val, count: int = 0, parent=None):
        super().__init__(parent)

        # Formater la date en français
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

        # Marqueur ◆
        dot = QLabel("◆")
        dot.setFont(QFont("Segoe UI", 9))
        dot.setStyleSheet("color: #1976d2; background: transparent;")
        dot.setFixedWidth(14)
        layout.addWidget(dot)

        # Label date
        lbl = QLabel(date_str)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl.setStyleSheet("color: #1565c0; background: transparent;")
        layout.addWidget(lbl)

        # Ligne extensible
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("QFrame { background-color: #bbdefb; border: none; }")
        layout.addWidget(line, stretch=1)

        # Badge nombre d'actions
        if count > 0:
            badge = QLabel(f"  {count} action{'s' if count > 1 else ''}  ")
            badge.setStyleSheet(
                "background-color: #e3f2fd; color: #1565c0;"
                "border: 1px solid #90caf9; border-radius: 10px;"
                "font-size: 10px; padding: 2px 8px;"
            )
            layout.addWidget(badge)

        self.setStyleSheet("background: transparent;")


class HistoriqueDialog(QDialog):
    """
    Visionneuse moderne de l'historique avec vue en cards/timeline
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique des modifications")
        self.resize(1000, 700)

        # Layout principal avec marges nulles
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Historique des modifications")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content_widget = QWidget()
        content_widget.setStyleSheet("background: #eef1f5;")
        root = QVBoxLayout(content_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- Zone header avec fond gris clair ---
        header_bg = QWidget()
        header_bg.setStyleSheet("background: #eef1f5;")
        header_bg_layout = QVBoxLayout(header_bg)
        header_bg_layout.setContentsMargins(18, 16, 18, 14)
        header_bg_layout.setSpacing(0)

        # Card blanche élevée
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: none;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 40))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.setSpacing(12)

        # --- Ligne 1 : Titre ---
        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        icon_badge = QLabel("🕐")
        icon_badge.setFont(QFont("Segoe UI", 16))
        icon_badge.setStyleSheet("""
            background-color: #e3f2fd;
            border-radius: 8px;
            padding: 4px 8px;
        """)
        title_row.addWidget(icon_badge)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel("Historique des modifications")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #1a237e; background: transparent;")
        title_col.addWidget(title)
        sub = QLabel("Chronologie complète des actions enregistrées")
        sub.setStyleSheet("color: #90a4ae; font-size: 10px; background: transparent;")
        title_col.addWidget(sub)
        title_row.addLayout(title_col, stretch=1)

        card_layout.addLayout(title_row)

        # Séparateur interne
        inner_sep = QFrame()
        inner_sep.setFrameShape(QFrame.HLine)
        inner_sep.setFixedHeight(1)
        inner_sep.setStyleSheet("QFrame { background-color: #f0f4f8; border: none; }")
        card_layout.addWidget(inner_sep)

        # --- Ligne 2 : Filtres ---
        filters_row = QHBoxLayout()
        filters_row.setSpacing(8)

        field_style = """
            QDateEdit, QComboBox, QLineEdit {
                padding: 5px 10px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: #f8fafc;
                font-size: 11px;
                color: #37474f;
            }
            QDateEdit:focus, QComboBox:focus, QLineEdit:focus {
                border: 1.5px solid #1976d2;
                background: white;
            }
        """

        self.from_date = QDateEdit(calendarPopup=True)
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setDisplayFormat("dd/MM/yyyy")
        self.from_date.setFixedHeight(32)
        self.from_date.setStyleSheet(field_style)
        filters_row.addWidget(self.from_date)

        arr = QLabel("→")
        arr.setStyleSheet("color: #b0bec5; font-size: 13px; background: transparent;")
        filters_row.addWidget(arr)

        self.to_date = QDateEdit(calendarPopup=True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setDisplayFormat("dd/MM/yyyy")
        self.to_date.setFixedHeight(32)
        self.to_date.setStyleSheet(field_style)
        filters_row.addWidget(self.to_date)

        vsep1 = QFrame()
        vsep1.setFrameShape(QFrame.VLine)
        vsep1.setFixedHeight(22)
        vsep1.setStyleSheet("QFrame { color: #e0e0e0; }")
        filters_row.addWidget(vsep1, alignment=Qt.AlignVCenter)

        self.action_filter = QComboBox()
        self.action_filter.addItems([
            "(Toutes les actions)", "Ajout", "Modification", "Suppression", "Erreur"
        ])
        self.action_filter.setFixedHeight(32)
        self.action_filter.setStyleSheet(field_style)
        self.action_filter.currentIndexChanged.connect(self.reload)
        filters_row.addWidget(self.action_filter)

        vsep2 = QFrame()
        vsep2.setFrameShape(QFrame.VLine)
        vsep2.setFixedHeight(22)
        vsep2.setStyleSheet("QFrame { color: #e0e0e0; }")
        filters_row.addWidget(vsep2, alignment=Qt.AlignVCenter)

        self.search = QLineEdit(placeholderText="🔍  Rechercher...")
        self.search.setFixedHeight(32)
        self.search.returnPressed.connect(self.reload)
        self.search.setStyleSheet(field_style)
        filters_row.addWidget(self.search, stretch=1)

        filters_row.addSpacing(4)

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.setFixedHeight(32)
        self.btn_refresh.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_refresh.clicked.connect(self.reload)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 0px 18px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:pressed { background-color: #0d47a1; }
        """)
        filters_row.addWidget(self.btn_refresh)

        self.btn_clear = QPushButton("Archiver...")
        self.btn_clear.setFixedHeight(32)
        self.btn_clear.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_clear.clicked.connect(self._clear_range_with_optional_export)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #fff3e0;
                color: #e65100;
                border: 1px solid #ffcc80;
                padding: 0px 18px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #ffe0b2; border-color: #ffa726; }
            QPushButton:pressed { background-color: #ffcc80; }
        """)
        filters_row.addWidget(self.btn_clear)

        card_layout.addLayout(filters_row)
        header_bg_layout.addWidget(card)
        root.addWidget(header_bg)

        # Contenu scrollable
        content_inner = QWidget()
        content_inner.setStyleSheet("background: #eef1f5;")
        inner_layout = QVBoxLayout(content_inner)
        inner_layout.setContentsMargins(18, 0, 18, 14)
        inner_layout.setSpacing(0)

        # --- Zone de scroll pour les cards ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #eef1f5; border: none; }")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setContentsMargins(0, 8, 0, 4)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        inner_layout.addWidget(scroll, stretch=1)

        # --- Bouton "Charger plus" (pagination) ---
        self._btn_load_more = QPushButton("Charger plus…")
        self._btn_load_more.clicked.connect(self._load_more)
        self._btn_load_more.setVisible(False)
        self._btn_load_more.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #616161;
                border: 1px solid #e0e0e0;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #eeeeee; }
        """)
        inner_layout.addWidget(self._btn_load_more)

        # --- Compteur ---
        self.count_label = QLabel()
        self.count_label.setStyleSheet("""
            QLabel {
                padding: 6px 10px;
                color: #78909c;
                font-size: 10px;
                background-color: transparent;
            }
        """)
        inner_layout.addWidget(self.count_label)

        root.addWidget(content_inner, stretch=1)

        # Ajouter le widget de contenu au layout principal
        main_layout.addWidget(content_widget)

        # État de pagination + timeline
        self._page_offset = 0
        self._current_worker = None
        self._loading_label = None
        self._last_shown_date = None  # Dernier jour affiché (évite les doublons de séparateur)

        # Filtrage par rôle : chaque utilisateur ne voit que son périmètre métier
        self._allowed_tables = self._resolve_allowed_tables()
        if self._allowed_tables is not None:
            modules = ', '.join(sorted(
                m for m, tables in MODULE_TABLES.items()
                if any(t in self._allowed_tables for t in tables)
            ))
            sub.setText(f"Actions liées à votre périmètre ({modules})")
            self.btn_clear.setVisible(False)  # Archivage réservé à l'admin

        self.reload()

    # ---------- Filtrage par rôle ----------

    def _resolve_allowed_tables(self):
        """
        Retourne la liste de tables autorisées selon le rôle de l'utilisateur.
        None = admin → toutes les tables.
        """
        try:
            from core.services.auth_service import get_current_user
            user = get_current_user()
            if not user:
                return None
            role = user.get('role_nom', '')
            if role == 'gestion_production':
                return MODULE_TABLES["Production"] + MODULE_TABLES["Planning"] + ["personnel", "personnel_infos"]
            elif role == 'gestion_rh':
                return MODULE_TABLES["RH"] + MODULE_TABLES["Planning"]
            # admin et autres rôles : pas de restriction
            return None
        except Exception:
            return None

    # ---------- Gestion du worker courant ----------

    def _cancel_current_worker(self):
        """Déconnecte les signaux et annule le worker en cours.

        Déconnecter avant cancel() est essentiel : cela libère immédiatement
        les closures (qui capturent self) et évite qu'un worker terminé
        après cancel() rappelle nos callbacks ou retarde le GC du dialog.
        """
        if self._current_worker is None:
            return
        try:
            self._current_worker.signals.result.disconnect()
        except TypeError:
            pass  # Déjà déconnecté
        try:
            self._current_worker.signals.error.disconnect()
        except TypeError:
            pass
        self._current_worker.cancel()
        self._current_worker = None

    # ---------- Reload (déclenché par changements de filtres) ----------

    def reload(self):
        """Recharge depuis le début — appelé quand les filtres changent."""
        self._page_offset = 0
        self._last_shown_date = None  # Réinitialiser la timeline

        self._cancel_current_worker()

        # Vider toutes les cards existantes
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Afficher le label de chargement
        self._loading_label = LoadingLabel("Chargement de l'historique")
        self._loading_label.setAlignment(Qt.AlignCenter)
        self.cards_layout.insertWidget(0, self._loading_label)

        self.count_label.setText("⏳ Chargement…")
        self._btn_load_more.setVisible(False)

        self._launch_fetch()

    def _launch_fetch(self):
        """Lance la récupération asynchrone d'une page via DbWorker."""
        d_from = self.from_date.date()
        d_to   = self.to_date.date()
        search_text   = self.search.text()
        action_filter = self.action_filter.currentText()
        offset        = self._page_offset

        def fetch(progress_callback=None):
            return fetch_historique_paginated(
                date_from=dt.datetime(d_from.year(), d_from.month(), d_from.day(), 0, 0, 0),
                date_to=dt.datetime(d_to.year(), d_to.month(), d_to.day(), 23, 59, 59),
                search_text=search_text,
                action_filter=action_filter,
                table_names=self._allowed_tables,
                offset=offset,
                limit=_PAGE_SIZE + 1,  # +1 pour détecter s'il y a une suite
            )

        def on_result(rows):
            self._on_data_fetched(rows, offset)

        def on_error(err):
            if self._loading_label:
                self._loading_label.stop()
                self._loading_label.setText("❌ Erreur de chargement")
                self._loading_label = None
            self.count_label.setText("❌ Erreur")
            logger.error(f"Erreur fetch historique: {err}")
            QMessageBox.critical(self, "Erreur", "Impossible de charger l'historique.")

        self._current_worker = DbWorker(fetch)
        self._current_worker.signals.result.connect(on_result)
        self._current_worker.signals.error.connect(on_error)
        DbThreadPool.start(self._current_worker)

    def _on_data_fetched(self, rows, offset):
        """Appelé dans le thread UI après chargement d'une page."""
        has_more = len(rows) > _PAGE_SIZE
        if has_more:
            rows = rows[:_PAGE_SIZE]

        # Retirer le label de chargement
        if self._loading_label:
            self._loading_label.stop()
            self._loading_label.deleteLater()
            self._loading_label = None

        # Grouper les lignes par jour et insérer les séparateurs de date (timeline)
        insert_pos = self.cards_layout.count() - 1
        for row_date, group in groupby(rows, key=self._row_date):
            group_rows = list(group)
            # Séparateur de date uniquement si le jour change
            if row_date is not None and row_date != self._last_shown_date:
                sep = DateSeparator(row_date, count=len(group_rows))
                self.cards_layout.insertWidget(insert_pos, sep)
                insert_pos += 1
                self._last_shown_date = row_date
            for row in group_rows:
                card = ActionCard(row)
                self.cards_layout.insertWidget(insert_pos, card)
                insert_pos += 1

        # Message "aucun résultat" sur la première page vide
        if offset == 0 and len(rows) == 0:
            no_result = QLabel("Aucune action trouvée pour cette période")
            no_result.setAlignment(Qt.AlignCenter)
            no_result.setStyleSheet("color: #9e9e9e; font-size: 12px; padding: 40px;")
            self.cards_layout.insertWidget(0, no_result)

        total = offset + len(rows)
        self._page_offset = total
        suffix = " — ⬇ suite disponible" if has_more else ""
        self.count_label.setText(f"📊 {total} action(s) affichée(s){suffix}")
        self._btn_load_more.setVisible(has_more)

    @staticmethod
    def _row_date(row: dict):
        """Extrait la date (sans heure) d'une ligne — clé de groupement pour la timeline."""
        dt_val = row.get('date_time')
        if dt_val is None:
            return None
        if hasattr(dt_val, 'date'):
            return dt_val.date()
        if isinstance(dt_val, str):
            try:
                return dt.datetime.fromisoformat(dt_val).date()
            except Exception:
                return None
        return None

    def _load_more(self):
        """Charge la page suivante sans effacer les cards existantes."""
        self._cancel_current_worker()
        self._btn_load_more.setVisible(False)
        self.count_label.setText("⏳ Chargement de la suite…")
        self._launch_fetch()

    # ---------- Clear + export ----------
    def _export_range(self, d_from: QDate, d_to: QDate):
        # Exporter dans App/logs/exports/ au lieu du Bureau
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "exports")
        os.makedirs(base_dir, exist_ok=True)

        if d_from == d_to:
            export_day(
                dt.date(d_from.year(), d_from.month(), d_from.day()),
                base_dir=base_dir
            )
            QMessageBox.information(self, "Export réussi",
                                    f"Export du {d_from.toString('dd/MM/yyyy')} effectué dans:\n{base_dir}")
        else:
            d = dt.date(d_from.year(), d_from.month(), d_from.day())
            end = dt.date(d_to.year(), d_to.month(), d_to.day())
            count = 0
            while d <= end:
                export_day(d, base_dir=base_dir)
                d += dt.timedelta(days=1)
                count += 1
            QMessageBox.information(self, "Export réussi",
                                   f"{count} fichier(s) d'export créé(s) dans:\n{base_dir}")

    def _clear_range_with_optional_export(self):
        d_from = self.from_date.date()
        d_to   = self.to_date.date()

        resp = QMessageBox.question(
            self, "Archivage de l'historique",
            f"Vous êtes sur le point d'archiver les logs du {d_from.toString('dd/MM/yyyy')} au {d_to.toString('dd/MM/yyyy')}.\n\n"
            "Voulez-vous créer une sauvegarde (export) avant la suppression ?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        if resp == QMessageBox.Cancel:
            return
        if resp == QMessageBox.Yes:
            try:
                self._export_range(d_from, d_to)
            except Exception as e:
                logger.exception(f"Erreur export: {e}")
                show_error_message(self, "Erreur d'export", "Échec de l'export", e)
                return

        confirm = QMessageBox.warning(
            self, "Confirmation de suppression",
            "Cette action va supprimer définitivement les logs de la période sélectionnée.\n\n"
            "Êtes-vous certain de vouloir continuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return

        try:
            deleted = delete_historique_range(
                date_from=dt.datetime(d_from.year(), d_from.month(), d_from.day(), 0, 0, 0),
                date_to=dt.datetime(d_to.year(), d_to.month(), d_to.day(), 23, 59, 59),
            )
            QMessageBox.information(self, "Archivage terminé",
                                   f"Archivage effectué avec succès.\n"
                                   f"{deleted} ligne(s) supprimée(s) de l'historique.")
            self.reload()

        except Exception as e:
            code = getattr(e, "errno", None) or (e.args[0] if getattr(e, "args", None) else "")
            msg  = getattr(e, "msg", None) or (e.args[1] if getattr(e, "args", None) and len(e.args) > 1 else str(e))
            QMessageBox.critical(self, "Erreur", f"Échec de la suppression :\n{msg or code}")