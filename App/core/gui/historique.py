from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QFrame, QDateEdit, QMessageBox, QComboBox, QSizePolicy,
    QTextEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QPalette, QCursor

from core.db.configbd import get_connection as get_db_connection
from core.services.log_exporter import export_day
from core.gui.emac_ui_kit import add_custom_title_bar

import json
import datetime as dt
import os

# --- Fonctions utilitaires (garder vos fonctions existantes) ---
ACTION_LABEL = {
    "INSERT": "Ajout",
    "UPDATE": "Modification",
    "DELETE": "Suppression",
    "ERROR":  "Erreur",
}

def fr_action(a: str) -> str:
    return ACTION_LABEL.get((a or "").upper(), a or "")

def get_entity_name(conn, entity_type: str, entity_id) -> str:
    if entity_id is None or entity_id == "":
        return ""
    
    try:
        cur = conn.cursor(dictionary=True)
        if entity_type == "operateur":
            cur.execute("SELECT nom, prenom FROM personnel WHERE id = %s", (entity_id,))
            row = cur.fetchone()
            if row:
                return f"{row['prenom']} {row['nom']}"
        elif entity_type == "poste":
            cur.execute("SELECT poste_code FROM postes WHERE id = %s", (entity_id,))
            row = cur.fetchone()
            if row:
                return row['poste_code']
        cur.close()
    except Exception:
        pass
    
    return f"#{entity_id}"

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
        
    except:
        pass
    
    return fr_action(action)

def make_resume(row: dict, conn=None) -> str:
    action = row.get("action", "")
    op_id = row.get("operateur_id")
    po_id = row.get("poste_id")
    desc = row.get("description") or ""
    
    op_name = get_entity_name(conn, "operateur", op_id) if conn and op_id else None
    po_name = get_entity_name(conn, "poste", po_id) if conn and po_id else None
    
    try:
        data = json.loads(desc)
        
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
    def __init__(self, row: dict, conn=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Détails de l'action")
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # En-tête avec type d'action
        action = row.get("action", "").upper()
        if action == "INSERT":
            icon = "✚"
            action_text = "Ajout de compétence"
            color = "#4caf50"
        elif action == "UPDATE":
            icon = "✏️"
            action_text = "Modification de compétence"
            color = "#ffc107"
        elif action == "DELETE":
            icon = "✕"
            action_text = "Suppression de compétence"
            color = "#f44336"
        else:
            icon = "⚠"
            action_text = "Action"
            color = "#9e9e9e"
        
        header = QLabel(f"{icon} {action_text}")
        header_font = QFont("Segoe UI", 16, QFont.Bold)
        header.setFont(header_font)
        header.setStyleSheet(f"color: {color}; padding: 12px; background-color: {color}22; border-radius: 6px;")
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
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(12)
        
        # Opérateur
        op_name = get_entity_name(conn, "operateur", row.get("operateur_id"))
        if not op_name:
            try:
                data = json.loads(row.get("description", "{}"))
                op_name = data.get("operateur", f"#{row.get('operateur_id')}")
            except:
                op_name = f"#{row.get('operateur_id')}"
        
        op_label = self._create_info_row("👤 Opérateur :", op_name)
        info_layout.addWidget(op_label)
        
        # Poste
        po_name = get_entity_name(conn, "poste", row.get("poste_id"))
        if not po_name:
            try:
                data = json.loads(row.get("description", "{}"))
                po_name = data.get("poste", f"#{row.get('poste_id')}")
            except:
                po_name = f"#{row.get('poste_id')}"
        
        po_label = self._create_info_row("📍 Poste :", po_name)
        info_layout.addWidget(po_label)
        
        # Détails selon le type d'action
        try:
            data = json.loads(row.get("description", "{}"))
            
            if action == "INSERT":
                niveau = data.get("niveau", "?")
                niveau_label = self._create_info_row("⭐ Niveau attribué :", f"Niveau {niveau}")
                info_layout.addWidget(niveau_label)
                
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
                    
                    direction = "augmenté" if new > old else "diminué"
                    info_text = QLabel(f"Le niveau de compétence a été {direction}.")
                    info_text.setWordWrap(True)
                    info_text.setStyleSheet("color: #757575; font-style: italic; padding: 8px; background-color: #f5f5f5; border-radius: 4px;")
                    info_layout.addWidget(info_text)
            
            elif action == "DELETE":
                niveau = data.get("niveau", "?")
                niveau_label = self._create_info_row("⭐ Niveau supprimé :", f"Niveau {niveau}")
                info_layout.addWidget(niveau_label)
                
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
    def __init__(self, row: dict, conn=None, parent=None):
        super().__init__(parent)
        self.row = row
        self.conn = conn
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(0)
        
        # Styles selon le type d'action
        action = row.get("action", "").upper()
        if action == "INSERT":
            bg_color = "#e8f5e9"  # Vert très clair
            border_color = "#4caf50"  # Vert
            icon = "✚"
            icon_color = "#2e7d32"
        elif action == "UPDATE":
            bg_color = "#fff8e1"  # Jaune très clair
            border_color = "#ffc107"  # Jaune/orange
            icon = "✏️"
            icon_color = "#f57f17"
        elif action == "DELETE":
            bg_color = "#ffebee"  # Rouge très clair
            border_color = "#f44336"  # Rouge
            icon = "✕"
            icon_color = "#c62828"
        else:
            bg_color = "#f5f5f5"
            border_color = "#9e9e9e"
            icon = "⚠"
            icon_color = "#424242"
        
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
        resume = make_resume(row, conn)
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
        
        details_layout.addStretch()
        content_layout.addLayout(details_layout)
        
        layout.addLayout(content_layout, stretch=1)
        
        # Ajuster la hauteur
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
    def mousePressEvent(self, event):
        """Ouvre le dialogue détaillé au clic"""
        if event.button() == Qt.LeftButton:
            dialog = DetailDialog(self.row, self.conn, self)
            dialog.exec_()
        super().mousePressEvent(event)
    
    def _lighten_color(self, hex_color):
        """Éclaircit légèrement une couleur pour l'effet hover"""
        color = QColor(hex_color)
        h, s, l, a = color.getHsl()
        return QColor.fromHsl(h, max(0, s - 10), min(255, l + 10), a).name()


class HistoriqueDialog(QDialog):
    """
    Visionneuse moderne de l'historique avec vue en cards/timeline
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique des modifications")
        self.resize(1000, 700)

        self.conn = None
        self._ensure_conn()

        # Layout principal avec marges nulles
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Historique des modifications")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content_widget = QWidget()
        root = QVBoxLayout(content_widget)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # --- En-tête simplifié ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Historique des modifications")
        title_font = QFont("Segoe UI", 13, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #212121; padding: 4px;")
        header_layout.addWidget(title)

        subtitle = QLabel("• Chronologie complète des actions")
        subtitle.setStyleSheet("color: #757575; font-size: 10px; padding: 4px;")
        header_layout.addWidget(subtitle)

        header_layout.addStretch()

        root.addLayout(header_layout)

        # --- Barre de filtres ---
        filters_frame = QFrame()
        filters_frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        filters = QHBoxLayout(filters_frame)
        filters.setSpacing(8)
        
        filters.addWidget(QLabel("Du"))
        self.from_date = QDateEdit(calendarPopup=True)
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setDisplayFormat("dd/MM/yyyy")
        filters.addWidget(self.from_date)

        filters.addWidget(QLabel("au"))
        self.to_date = QDateEdit(calendarPopup=True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setDisplayFormat("dd/MM/yyyy")
        filters.addWidget(self.to_date)

        filters.addWidget(QLabel("Type"))
        self.action_filter = QComboBox()
        self.action_filter.addItems([
            "(Toutes les actions)",
            "Ajout",
            "Modification", 
            "Suppression",
            "Erreur"
        ])
        self.action_filter.currentIndexChanged.connect(self.reload)
        filters.addWidget(self.action_filter)

        self.search = QLineEdit(placeholderText="🔍 Rechercher...")
        self.search.returnPressed.connect(self.reload)
        self.search.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #1976d2;
            }
        """)
        filters.addWidget(self.search, stretch=1)

        self.btn_refresh = QPushButton("🔄 Actualiser")
        self.btn_refresh.clicked.connect(self.reload)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        filters.addWidget(self.btn_refresh)

        self.btn_clear = QPushButton("📦 Archiver...")
        self.btn_clear.clicked.connect(self._clear_range_with_optional_export)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        filters.addWidget(self.btn_clear)

        root.addWidget(filters_frame)

        # --- Zone de scroll pour les cards ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #ffffff; border: none; }")
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setContentsMargins(4, 4, 4, 4)
        self.cards_layout.addStretch()
        
        scroll.setWidget(self.cards_container)
        root.addWidget(scroll, stretch=1)

        # --- Compteur ---
        self.count_label = QLabel()
        self.count_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                color: #616161;
                font-size: 11px;
                background-color: #fafafa;
                border-radius: 4px;
            }
        """)
        root.addWidget(self.count_label)

        # Ajouter le widget de contenu au layout principal
        main_layout.addWidget(content_widget)

        self.reload()

    # ---------- Connexion ----------
    def _ensure_conn(self):
        try:
            if self.conn is None:
                self.conn = get_db_connection()
            else:
                _ = self.conn.cursor(); _.close()
        except Exception:
            QMessageBox.critical(self, "Historique", "Impossible de se connecter à la base de données.")
            self.conn = None

    def _cursor(self):
        if self.conn is None:
            self._ensure_conn()
        if self.conn is None:
            raise RuntimeError("Connexion DB indisponible")
        return self.conn.cursor(dictionary=True)

    # ---------- Fetch ----------
    def _fetch_logs(self, d_from: QDate, d_to: QDate, search_text: str, action_filter: str):
        cur = None
        try:
            cur = self._cursor()

            where = ["date_time >= %s", "date_time <= %s"]
            params = [
                dt.datetime(d_from.year(), d_from.month(), d_from.day(), 0, 0, 0),
                dt.datetime(d_to.year(),   d_to.month(),   d_to.day(),   23, 59, 59)
            ]

            action_map = {
                "Ajout": "INSERT",
                "Modification": "UPDATE",
                "Suppression": "DELETE",
                "Erreur": "ERROR"
            }
            
            if action_filter and action_filter != "(Toutes les actions)":
                sql_action = action_map.get(action_filter, action_filter)
                where.append("action = %s")
                params.append(sql_action)

            if search_text:
                like = f"%{search_text}%"
                where.append("("
                             "action LIKE %s OR "
                             "description LIKE %s OR "
                             "CAST(operateur_id AS CHAR) LIKE %s OR "
                             "CAST(poste_id AS CHAR) LIKE %s"
                             ")")
                params += [like, like, like, like]

            # ✅ SÉCURITÉ: Construction sécurisée de la clause WHERE
            where_clause = " AND ".join(where) if where else "1=1"
            sql = (
                "SELECT id, date_time, action, operateur_id, poste_id, description "
                "FROM historique "
                f"WHERE {where_clause} "
                "ORDER BY date_time DESC, id DESC"
            )
            cur.execute(sql, params)
            return cur.fetchall() or []
        finally:
            try:
                if cur: cur.close()
            except Exception:
                pass

    # ---------- UI Reload ----------
    def reload(self):
        # Supprimer toutes les cards existantes
        while self.cards_layout.count() > 1:  # Garder le stretch
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            rows = self._fetch_logs(
                self.from_date.date(),
                self.to_date.date(),
                self.search.text(),
                self.action_filter.currentText(),
            )
        except Exception as e:
            code = getattr(e, "errno", None) or (e.args[0] if getattr(e, "args", None) else "")
            msg  = getattr(e, "msg", None) or (e.args[1] if getattr(e, "args", None) and len(e.args) > 1 else str(e))
            QMessageBox.critical(self, "Erreur", f"Impossible de charger l'historique :\n{msg or code}")
            return

        # Créer une card pour chaque action
        for row in rows:
            card = ActionCard(row, self.conn)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        
        # Message si aucun résultat
        if len(rows) == 0:
            no_result = QLabel("Aucune action trouvée pour cette période")
            no_result.setAlignment(Qt.AlignCenter)
            no_result.setStyleSheet("color: #9e9e9e; font-size: 12px; padding: 40px;")
            self.cards_layout.insertWidget(0, no_result)
        
        self.count_label.setText(f"📊 {len(rows)} action(s) trouvée(s)")

    # ---------- Clear + export ----------
    def _export_range(self, d_from: QDate, d_to: QDate):
        base_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if d_from == d_to:
            export_day(self.conn,
                       dt.date(d_from.year(), d_from.month(), d_from.day()),
                       output_dir=base_dir)
            QMessageBox.information(self, "Export réussi",
                                    f"Export du {d_from.toString('dd/MM/yyyy')} effectué sur le Bureau.")
        else:
            d = dt.date(d_from.year(), d_from.month(), d_from.day())
            end = dt.date(d_to.year(), d_to.month(), d_to.day())
            count = 0
            while d <= end:
                export_day(self.conn, d, output_dir=base_dir)
                d += dt.timedelta(days=1)
                count += 1
            QMessageBox.information(self, "Export réussi", 
                                   f"{count} fichier(s) d'export créé(s) sur le Bureau.")

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
                QMessageBox.warning(self, "Erreur d'export", f"Échec de l'export :\n{e}")
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

        cur = None
        try:
            cur = self._cursor()
            sql = (
                "DELETE FROM historique "
                "WHERE date_time >= %s AND date_time <= %s"
            )
            params = [
                dt.datetime(d_from.year(), d_from.month(), d_from.day(), 0, 0, 0),
                dt.datetime(d_to.year(),   d_to.month(),   d_to.day(),   23, 59, 59)
            ]
            cur.execute(sql, params)
            deleted = cur.rowcount or 0
            self.conn.commit()

            QMessageBox.information(self, "Archivage terminé", 
                                   f"Archivage effectué avec succès.\n"
                                   f"{deleted} ligne(s) supprimée(s) de l'historique.")
            self.reload()

        except Exception as e:
            code = getattr(e, "errno", None) or (e.args[0] if getattr(e, "args", None) else "")
            msg  = getattr(e, "msg", None) or (e.args[1] if getattr(e, "args", None) and len(e.args) > 1 else str(e))
            QMessageBox.critical(self, "Erreur", f"Échec de la suppression :\n{msg or code}")
        finally:
            try:
                cur.close()
            except Exception:
                pass