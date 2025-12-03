# -*- coding: utf-8 -*-
"""
historique_personnel.py - Widget d'historique pour la fiche d'un personnel
Affiche l'historique complet des actions concernant un opérateur spécifique
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLabel, QPushButton, QFrame, QTextEdit,
    QSplitter, QDateEdit, QLineEdit, QMessageBox, QDialog, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QBrush

from core.db.configbd import get_connection as get_db_connection
import json
import datetime as dt


# ============================================================
# UTILITAIRES DE FORMATAGE
# ============================================================

def format_datetime(dt_value):
    """Formate une date/heure pour l'affichage."""
    if isinstance(dt_value, str):
        try:
            dt_value = dt.datetime.fromisoformat(dt_value)
        except:
            return str(dt_value)

    if hasattr(dt_value, 'strftime'):
        return dt_value.strftime("%d/%m/%Y %H:%M:%S")

    return str(dt_value)


def get_action_icon_and_color(action):
    """Retourne l'icône et la couleur pour un type d'action."""
    action_upper = action.upper()

    if action_upper == "INSERT":
        return "✚", "#10b981", "#d1fae5"  # Vert
    elif action_upper == "UPDATE":
        return "✎", "#3b82f6", "#dbeafe"  # Bleu
    elif action_upper == "DELETE":
        return "✕", "#ef4444", "#fee2e2"  # Rouge
    elif action_upper == "ERROR":
        return "⚠", "#f59e0b", "#fed7aa"  # Orange
    else:
        return "•", "#6b7280", "#f3f4f6"  # Gris


def parse_description_json(description_str):
    """Parse la description JSON et retourne un dict."""
    if not description_str:
        return {}

    try:
        return json.loads(description_str)
    except:
        return {"raw": description_str}


def format_action_resume(action, data, poste_code=None):
    """Génère un résumé lisible de l'action."""
    action_upper = action.upper()

    # Récupérer le poste depuis les données si disponible
    if not poste_code:
        poste_code = data.get("poste", "Poste inconnu")

    if action_upper == "INSERT":
        niveau = data.get("niveau", "?")
        return f"Ajout de compétence : Niveau {niveau} sur {poste_code}"

    elif action_upper == "UPDATE":
        changes = data.get("changes", {})

        if "niveau" in changes:
            old = changes["niveau"].get("old", "?")
            new = changes["niveau"].get("new", "?")
            return f"Modification niveau : {old} → {new} sur {poste_code}"

        # Autres types de modifications
        field_names = []
        if "date_evaluation" in changes:
            field_names.append("date d'évaluation")
        if "prochaine_evaluation" in changes:
            field_names.append("prochaine évaluation")

        if field_names:
            return f"Modification {', '.join(field_names)} sur {poste_code}"

        return f"Modification sur {poste_code}"

    elif action_upper == "DELETE":
        niveau = data.get("niveau", "?")
        return f"Suppression : Niveau {niveau} sur {poste_code}"

    elif action_upper == "ERROR":
        return f"Erreur signalée sur {poste_code}"

    return f"Action {action} sur {poste_code}"


def format_details_html(action, data, poste_code=None):
    """Génère un HTML formaté pour les détails de l'action."""
    action_upper = action.upper()

    if not poste_code:
        poste_code = data.get("poste", "Poste inconnu")

    html = f"<div style='font-family: Segoe UI, Arial; font-size: 11pt;'>"

    # En-tête
    icon, color, bg_color = get_action_icon_and_color(action)
    html += f"<div style='background: {bg_color}; padding: 12px; border-left: 4px solid {color}; margin-bottom: 12px;'>"
    html += f"<h3 style='margin: 0; color: {color};'>{icon} {action.upper()}</h3>"
    html += f"</div>"

    # Informations générales
    html += "<table style='width: 100%; border-collapse: collapse; margin-bottom: 16px;'>"

    operateur = data.get("operateur", "Non spécifié")
    html += f"<tr><td style='padding: 8px; font-weight: bold; width: 180px;'>👤 Opérateur :</td>"
    html += f"<td style='padding: 8px;'>{operateur}</td></tr>"

    html += f"<tr style='background: #f9fafb;'><td style='padding: 8px; font-weight: bold;'>📍 Poste :</td>"
    html += f"<td style='padding: 8px;'>{poste_code}</td></tr>"

    # Détails spécifiques selon le type d'action
    if action_upper == "INSERT":
        niveau = data.get("niveau", "?")
        html += f"<tr><td style='padding: 8px; font-weight: bold;'>⭐ Niveau attribué :</td>"
        html += f"<td style='padding: 8px;'><strong style='color: {color}; font-size: 13pt;'>Niveau {niveau}</strong></td></tr>"

        if "date_evaluation" in data:
            html += f"<tr style='background: #f9fafb;'><td style='padding: 8px; font-weight: bold;'>📅 Date évaluation :</td>"
            html += f"<td style='padding: 8px;'>{data['date_evaluation']}</td></tr>"

        if "prochaine_evaluation" in data:
            html += f"<tr><td style='padding: 8px; font-weight: bold;'>📅 Prochaine évaluation :</td>"
            html += f"<td style='padding: 8px;'>{data['prochaine_evaluation']}</td></tr>"

    elif action_upper == "UPDATE":
        changes = data.get("changes", {})

        if "niveau" in changes:
            old = changes["niveau"].get("old", "?")
            new = changes["niveau"].get("new", "?")

            html += f"<tr><td style='padding: 8px; font-weight: bold;'>⭐ Changement niveau :</td>"
            html += f"<td style='padding: 8px;'>"
            html += f"<span style='background: #fee2e2; padding: 4px 12px; border-radius: 4px; color: #dc2626; font-weight: bold;'>N{old}</span>"
            html += f" <span style='font-size: 16pt; color: #6b7280;'>→</span> "
            html += f"<span style='background: #d1fae5; padding: 4px 12px; border-radius: 4px; color: #059669; font-weight: bold;'>N{new}</span>"
            html += f"</td></tr>"

        if "date_evaluation" in changes:
            old = changes["date_evaluation"].get("old", "Non définie")
            new = changes["date_evaluation"].get("new", "Non définie")
            html += f"<tr style='background: #f9fafb;'><td style='padding: 8px; font-weight: bold;'>📅 Date évaluation :</td>"
            html += f"<td style='padding: 8px;'>{old} → {new}</td></tr>"

        if "prochaine_evaluation" in changes:
            old = changes["prochaine_evaluation"].get("old", "Non définie")
            new = changes["prochaine_evaluation"].get("new", "Non définie")
            html += f"<tr><td style='padding: 8px; font-weight: bold;'>📅 Prochaine évaluation :</td>"
            html += f"<td style='padding: 8px;'>{old} → {new}</td></tr>"

        # Afficher toutes les autres modifications
        for key, value in changes.items():
            if key not in ["niveau", "date_evaluation", "prochaine_evaluation"]:
                old = value.get("old", "?")
                new = value.get("new", "?")
                html += f"<tr style='background: #f9fafb;'><td style='padding: 8px; font-weight: bold;'>🔄 {key} :</td>"
                html += f"<td style='padding: 8px;'>{old} → {new}</td></tr>"

    elif action_upper == "DELETE":
        niveau = data.get("niveau", "?")
        html += f"<tr><td style='padding: 8px; font-weight: bold;'>⭐ Niveau supprimé :</td>"
        html += f"<td style='padding: 8px;'><strong style='color: {color}; font-size: 13pt;'>Niveau {niveau}</strong></td></tr>"

    html += "</table>"

    # Métadonnées supplémentaires
    if "type" in data:
        html += f"<div style='background: #f3f4f6; padding: 8px; border-radius: 4px; font-size: 9pt; color: #6b7280;'>"
        html += f"<strong>Type d'opération :</strong> {data['type']}"
        html += "</div>"

    html += "</div>"

    return html


# ============================================================
# DIALOGUE DE DÉTAILS
# ============================================================

class DetailHistoriqueDialog(QDialog):
    """Dialogue affichant les détails complets d'une action."""

    def __init__(self, row_data, poste_code=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Détails de l'action")
        self.setGeometry(200, 150, 700, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # En-tête
        action = row_data.get("action", "").upper()
        icon, color, bg_color = get_action_icon_and_color(action)

        header = QLabel(f"{icon} Détails de l'action : {action}")
        header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.setStyleSheet(f"""
            QLabel {{
                background: {bg_color};
                color: {color};
                padding: 16px;
                border-left: 6px solid {color};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(header)

        # Date et heure
        dt_str = format_datetime(row_data.get("date_time"))
        date_label = QLabel(f"🕐 {dt_str}")
        date_label.setStyleSheet("font-size: 11pt; color: #6b7280; padding: 4px;")
        layout.addWidget(date_label)

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #e5e7eb; max-height: 2px;")
        layout.addWidget(sep)

        # Zone de détails
        self.details_view = QTextEdit()
        self.details_view.setReadOnly(True)
        self.details_view.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 12px;
                background: white;
            }
        """)

        # Générer le HTML des détails
        data = parse_description_json(row_data.get("description", "{}"))
        html = format_details_html(action, data, poste_code)
        self.details_view.setHtml(html)

        layout.addWidget(self.details_view, 1)

        # Bouton fermer
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)


# ============================================================
# WIDGET PRINCIPAL - ONGLET HISTORIQUE
# ============================================================

class HistoriquePersonnelTab(QWidget):
    """Widget d'historique pour un opérateur spécifique."""

    def __init__(self, operateur_id, operateur_nom="", operateur_prenom="", parent=None):
        super().__init__(parent)

        self.operateur_id = operateur_id
        self.operateur_nom = operateur_nom
        self.operateur_prenom = operateur_prenom
        self.current_data = []  # Données actuellement affichées

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        """Initialise l'interface utilisateur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # === EN-TÊTE ===
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 8px;
                padding: 16px;
            }
        """)
        header_layout = QVBoxLayout(header_widget)

        title = QLabel(f"📜 Historique complet")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title)

        subtitle = QLabel(f"Toutes les actions concernant {self.operateur_prenom} {self.operateur_nom}")
        subtitle.setStyleSheet("color: #e0e7ff; font-size: 10pt; background: transparent;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header_widget)

        # === FILTRES ===
        filters_frame = QFrame()
        filters_frame.setStyleSheet("""
            QFrame {
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(10)

        # Type d'action
        filters_layout.addWidget(QLabel("Type :"))
        self.action_filter = QComboBox()
        self.action_filter.addItems([
            "Toutes les actions",
            "Ajouts",
            "Modifications",
            "Suppressions",
            "Erreurs"
        ])
        self.action_filter.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.action_filter)

        # Poste
        filters_layout.addWidget(QLabel("Poste :"))
        self.poste_filter = QComboBox()
        self.poste_filter.addItem("Tous les postes", None)
        self.poste_filter.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.poste_filter)

        # Période
        filters_layout.addWidget(QLabel("Du :"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        self.date_from.setDate(QDate.currentDate().addMonths(-6))
        self.date_from.dateChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.date_from)

        filters_layout.addWidget(QLabel("au :"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.date_to)

        # Recherche textuelle
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher...")
        self.search_input.textChanged.connect(self._apply_filters)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 2px solid #6366f1;
            }
        """)
        filters_layout.addWidget(self.search_input, 1)

        # Bouton réinitialiser
        reset_btn = QPushButton("🔄 Réinitialiser")
        reset_btn.clicked.connect(self._reset_filters)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4b5563;
            }
        """)
        filters_layout.addWidget(reset_btn)

        # Bouton import manuel
        import_btn = QPushButton("📥 Import manuel")
        import_btn.clicked.connect(self._open_import_dialog)
        import_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        import_btn.setToolTip("Ajouter des anciennes données historiques manuellement")
        filters_layout.addWidget(import_btn)

        layout.addWidget(filters_frame)

        # === TABLEAU PRINCIPAL (sans splitter, pleine hauteur) ===
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Date/Heure", "Type", "Table", "Résumé", "_id"
        ])
        self.table.setColumnHidden(4, True)  # Colonne ID cachée

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        self.table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #1e40af;
            }
            QHeaderView::section {
                background: #f3f4f6;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                font-weight: bold;
                font-size: 10pt;
            }
        """)

        self.table.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table, 1)

        # Hint pour l'utilisateur
        hint_label = QLabel("💡 Double-cliquez sur une ligne pour voir tous les détails de l'action")
        hint_label.setStyleSheet("color: #6b7280; font-style: italic; padding: 4px;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)

        # === STATISTIQUES ===
        stats_layout = QHBoxLayout()

        self.stats_label = QLabel("📊 0 action(s)")
        self.stats_label.setStyleSheet("color: #6b7280; font-size: 10pt; font-weight: bold;")
        stats_layout.addWidget(self.stats_label)

        stats_layout.addStretch()

        # Légende des couleurs
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)

        for text, color in [
            ("Ajout", "#10b981"),
            ("Modification", "#3b82f6"),
            ("Suppression", "#ef4444"),
            ("Erreur", "#f59e0b")
        ]:
            box = QLabel("  ")
            box.setStyleSheet(f"background: {color}; border-radius: 2px;")
            box.setFixedSize(12, 12)
            legend_layout.addWidget(box)

            label = QLabel(text)
            label.setStyleSheet("color: #6b7280; font-size: 9pt;")
            legend_layout.addWidget(label)

        stats_layout.addLayout(legend_layout)

        layout.addLayout(stats_layout)

    def _load_data(self):
        """Charge les données depuis la base de données."""
        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)

            # Charger TOUTES les actions pour cet opérateur depuis les deux tables
            # 1. Table historique générale
            query_historique = """
                SELECT h.id, h.date_time, h.action, h.poste_id, h.description,
                       h.table_name,
                       p.poste_code,
                       'historique' as source_table
                FROM historique h
                LEFT JOIN postes p ON h.poste_id = p.id
                WHERE h.operateur_id = %s
            """
            cur.execute(query_historique, (self.operateur_id,))
            rows_historique = cur.fetchall()

            # 2. Table historique_polyvalence (données détaillées)
            query_poly = """
                SELECT hp.id, hp.date_action as date_time, hp.action_type as action,
                       hp.poste_id, hp.commentaire as description,
                       'polyvalence' as table_name,
                       p.poste_code,
                       'historique_polyvalence' as source_table,
                       hp.ancien_niveau, hp.nouveau_niveau,
                       hp.ancienne_date_evaluation, hp.nouvelle_date_evaluation,
                       hp.utilisateur, hp.source as poly_source
                FROM historique_polyvalence hp
                LEFT JOIN postes p ON hp.poste_id = p.id
                WHERE hp.operateur_id = %s
            """
            cur.execute(query_poly, (self.operateur_id,))
            rows_poly = cur.fetchall()

            # Fusionner et trier toutes les données
            all_rows = list(rows_historique) + list(rows_poly)
            all_rows.sort(key=lambda x: x['date_time'], reverse=True)

            # Enrichir les données avec info table
            self.current_data = []
            for row in all_rows:
                row_data = dict(row)

                # Déterminer le nom de table lisible
                table_name = row.get("table_name", "")
                source_table = row.get("source_table", "historique")

                if table_name:
                    table_display = {
                        "polyvalence": "Polyvalence",
                        "personnel": "Personnel",
                        "contrat": "Contrat",
                        "formation": "Formation",
                        "validite": "Validité",
                        "absence": "Absence",
                        "system": "Système"
                    }.get(table_name.lower(), table_name)

                    # Ajouter un badge si c'est une donnée détaillée
                    if source_table == "historique_polyvalence":
                        table_display += " [Détaillé]"

                    row_data["table_display"] = table_display
                else:
                    row_data["table_display"] = "Général"

                self.current_data.append(row_data)

            # Charger la liste des postes pour le filtre (seulement ceux dans l'historique)
            query_postes = """
                SELECT DISTINCT p.id, p.poste_code
                FROM historique h
                JOIN postes p ON h.poste_id = p.id
                WHERE h.operateur_id = %s
                ORDER BY p.poste_code
            """
            cur.execute(query_postes, (self.operateur_id,))
            postes = cur.fetchall()

            self.poste_filter.clear()
            self.poste_filter.addItem("Tous les postes", None)
            for poste in postes:
                self.poste_filter.addItem(poste["poste_code"], poste["id"])

            cur.close()
            conn.close()

            self._apply_filters()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger l'historique :\n{e}")

    def _apply_filters(self):
        """Applique les filtres et met à jour le tableau."""
        action_filter = self.action_filter.currentText()
        poste_id = self.poste_filter.currentData()
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        search_text = self.search_input.text().lower()

        # Filtrer les données
        filtered_data = []
        for row in self.current_data:
            # Filtre par type d'action
            action = row["action"].upper()
            if action_filter == "Ajouts" and action != "INSERT":
                continue
            elif action_filter == "Modifications" and action != "UPDATE":
                continue
            elif action_filter == "Suppressions" and action != "DELETE":
                continue
            elif action_filter == "Erreurs" and action != "ERROR":
                continue

            # Filtre par poste
            if poste_id is not None and row.get("poste_id") != poste_id:
                continue

            # Filtre par période
            row_date = row["date_time"]
            if isinstance(row_date, str):
                row_date = dt.datetime.fromisoformat(row_date).date()
            elif hasattr(row_date, 'date'):
                row_date = row_date.date()

            if row_date < date_from or row_date > date_to:
                continue

            # Filtre par recherche textuelle
            if search_text:
                searchable = f"{row.get('action', '')} {row.get('poste_code', '')} {row.get('description', '')}".lower()
                if search_text not in searchable:
                    continue

            filtered_data.append(row)

        # Afficher les données filtrées
        self._display_data(filtered_data)
        self.stats_label.setText(f"📊 {len(filtered_data)} action(s) affichée(s) sur {len(self.current_data)} au total")

    def _display_data(self, data):
        """Affiche les données dans le tableau."""
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)

        for row in data:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            # Date/Heure
            dt_str = format_datetime(row["date_time"])
            self.table.setItem(row_pos, 0, QTableWidgetItem(dt_str))

            # Type avec icône et couleur
            action = row["action"]
            icon, color, bg_color = get_action_icon_and_color(action)
            type_item = QTableWidgetItem(f"{icon} {action.upper()}")
            type_item.setForeground(QBrush(QColor(color)))
            type_item.setBackground(QBrush(QColor(bg_color)))
            font = QFont()
            font.setBold(True)
            type_item.setFont(font)
            type_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_pos, 1, type_item)

            # Table concernée
            table_display = row.get("table_display", "Général")
            table_item = QTableWidgetItem(table_display)
            table_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_pos, 2, table_item)

            # Résumé
            source_table = row.get("source_table", "historique")
            poste_code = row.get("poste_code", None)
            table_name = row.get("table_name", "")

            # Si c'est une donnée de historique_polyvalence, générer un résumé détaillé
            if source_table == "historique_polyvalence":
                ancien_niveau = row.get("ancien_niveau")
                nouveau_niveau = row.get("nouveau_niveau")
                action_type = row.get("action", "").upper()

                if action_type == "AJOUT":
                    resume = f"Ajout N{nouveau_niveau} - {poste_code or '?'}"
                elif action_type == "MODIFICATION":
                    resume = f"Modification N{ancien_niveau} → N{nouveau_niveau} - {poste_code or '?'}"
                elif action_type == "SUPPRESSION":
                    resume = f"Suppression N{ancien_niveau} - {poste_code or '?'}"
                elif action_type == "IMPORT_MANUEL":
                    if nouveau_niveau:
                        resume = f"Import manuel N{nouveau_niveau} - {poste_code or '?'}"
                    else:
                        resume = f"Import manuel - {poste_code or '?'}"
                else:
                    resume = f"{action_type} - {poste_code or '?'}"

                # Ajouter le commentaire s'il existe
                commentaire = row.get("commentaire", "")
                if commentaire and commentaire != "None":
                    resume += f" ({commentaire[:50]}{'...' if len(commentaire) > 50 else ''})"

            # Sinon, utiliser l'ancien système de génération de résumé
            else:
                data_json = parse_description_json(row.get("description", "{}"))

                # Générer résumé adapté selon la table
                if table_name == "personnel":
                    # Changement de statut, infos perso, etc.
                    if "changes" in data_json and "statut" in data_json.get("changes", {}):
                        old = data_json["changes"]["statut"].get("old", "?")
                        new = data_json["changes"]["statut"].get("new", "?")
                        resume = f"Changement statut : {old} → {new}"
                    else:
                        resume = f"Modification des informations personnelles"
                elif table_name == "contrat":
                    # Contrat
                    if action.upper() == "INSERT":
                        type_contrat = data_json.get("type_contrat", "")
                        resume = f"Nouveau contrat : {type_contrat}"
                    elif action.upper() == "UPDATE":
                        resume = f"Modification de contrat"
                    else:
                        resume = f"Suppression de contrat"
                elif table_name in ["formation", "validite", "absence"]:
                    # Autres tables
                    resume = f"{action.upper()} - {table_display}"
                else:
                    # Polyvalence ou autre
                    resume = format_action_resume(action, data_json, poste_code)

            self.table.setItem(row_pos, 3, QTableWidgetItem(resume))

            # ID (caché)
            self.table.setItem(row_pos, 4, QTableWidgetItem(str(row["id"])))

        self.table.setSortingEnabled(True)

    def _on_double_click(self):
        """Ouvre le dialogue de détails complets."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row_idx = selected_rows[0].row()
        hist_id = int(self.table.item(row_idx, 4).text())
        row_data = next((r for r in self.current_data if r["id"] == hist_id), None)

        if row_data:
            poste_code = row_data.get("poste_code", "Inconnu")
            dialog = DetailHistoriqueDialog(row_data, poste_code, self)
            dialog.exec_()

    def _reset_filters(self):
        """Réinitialise tous les filtres."""
        self.action_filter.setCurrentIndex(0)
        self.poste_filter.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-6))
        self.date_to.setDate(QDate.currentDate())
        self.search_input.clear()
        self._apply_filters()

    def _open_import_dialog(self):
        """Ouvre le dialogue d'import de données historiques."""
        try:
            print("[DEBUG] Début _open_import_dialog")
            from core.gui.import_historique_polyvalence import ImportHistoriquePolyvalenceDialog
            print("[DEBUG] Import réussi")

            dialog = ImportHistoriquePolyvalenceDialog(
                operateur_id=self.operateur_id,
                parent=self
            )
            print("[DEBUG] Dialogue créé")

            result = dialog.exec_()
            print(f"[DEBUG] Dialogue fermé avec résultat: {result}")

            if result == QDialog.Accepted:
                # Recharger les données après l'import
                self._load_data()
                QMessageBox.information(
                    self,
                    "Import réussi",
                    "Les données historiques ont été importées avec succès !\n\n"
                    "L'historique a été rechargé pour afficher les nouvelles données."
                )
        except Exception as e:
            print(f"[ERREUR] _open_import_dialog: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de l'ouverture du dialogue d'import :\n{e}"
            )
