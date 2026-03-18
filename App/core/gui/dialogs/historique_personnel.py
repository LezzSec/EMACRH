# -*- coding: utf-8 -*-
"""
historique_personnel.py - Widget d'historique pour la fiche d'un personnel
Affiche l'historique complet des actions concernant un opérateur spécifique
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLabel, QPushButton, QFrame, QTextEdit,
    QDialog, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from core.repositories.polyvalence_repo import PolyvalenceRepository
from core.gui.components.emac_ui_kit import show_error_message
import json
import datetime as dt
from core.utils.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# UTILITAIRES DE FORMATAGE
# ============================================================

def format_datetime(dt_value):
    """Formate une date/heure pour l'affichage."""
    if isinstance(dt_value, str):
        try:
            dt_value = dt.datetime.fromisoformat(dt_value)
        except Exception:
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
    except Exception:
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
        header_layout = QHBoxLayout()

        header = QLabel(f"📜 Historique des polyvalences - {self.operateur_prenom} {self.operateur_nom}")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header.setStyleSheet("color: #374151; padding: 8px;")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # === FILTRE SIMPLE ===
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("Afficher :"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["Toutes les polyvalences", "Actuelles uniquement", "Anciennes uniquement"])
        self.type_filter.currentIndexChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.type_filter)

        filter_layout.addStretch()

        self.stats_label = QLabel("0 polyvalence(s)")
        self.stats_label.setStyleSheet("color: #6b7280; font-size: 10pt;")
        filter_layout.addWidget(self.stats_label)

        layout.addLayout(filter_layout)

        # === TABLEAU DES POLYVALENCES ===
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Type", "Poste", "Niveau", "Date Évaluation", "Prochaine Éval.", "Commentaire", "_id"
        ])
        self.table.setColumnHidden(6, True)  # ID caché

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
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
                padding: 8px;
            }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #1e40af;
            }
            QHeaderView::section {
                background: #f3f4f6;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.table, 1)


    def _format_date(self, date_val):
        """Formate une date."""
        if date_val is None:
            return "N/A"
        if isinstance(date_val, str):
            try:
                return dt.datetime.strptime(date_val, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                return date_val
        if hasattr(date_val, "strftime"):
            return date_val.strftime("%d/%m/%Y")
        return str(date_val)

    def _calculate_anciennete(self, date_eval):
        """Calcule l'ancienneté."""
        if date_eval is None:
            return "N/A"
        try:
            if isinstance(date_eval, str):
                date_obj = dt.datetime.strptime(date_eval, "%Y-%m-%d").date()
            elif hasattr(date_eval, "date"):
                date_obj = date_eval.date()
            else:
                date_obj = date_eval

            delta = dt.date.today() - date_obj
            years = delta.days // 365
            months = (delta.days % 365) // 30

            if years > 0:
                return f"{years} an(s) {months} mois"
            elif months > 0:
                return f"{months} mois"
            else:
                return f"{delta.days} jour(s)"
        except Exception:
            return "N/A"

    def _load_data(self):
        """Charge les polyvalences actuelles et anciennes."""
        try:
            # Charger les polyvalences ACTUELLES (table polyvalence)
            polyvalences_actuelles = PolyvalenceRepository.get_actuelles_with_type(self.operateur_id)

            # Charger les ANCIENNES polyvalences (table historique_polyvalence avec action_type='IMPORT_MANUEL')
            polyvalences_anciennes = PolyvalenceRepository.get_anciennes_historique(self.operateur_id)

            # Stocker toutes les données
            self.all_polyvalences = list(polyvalences_actuelles) + list(polyvalences_anciennes)

            self._apply_filter()

        except Exception as e:
            logger.exception(f"Erreur chargement donnees: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les données", e)

    def _apply_filter(self):
        """Applique le filtre de type et affiche les polyvalences."""
        filter_type = self.type_filter.currentText()

        # Filtrer les données selon le type
        filtered_data = []
        for poly in self.all_polyvalences:
            poly_type = poly.get("type", "")

            if filter_type == "Actuelles uniquement" and poly_type != "ACTUELLE":
                continue
            elif filter_type == "Anciennes uniquement" and poly_type != "ANCIENNE":
                continue

            filtered_data.append(poly)

        # Afficher dans le tableau
        self.table.setRowCount(0)

        for poly in filtered_data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Colonne 0 : Type (badge coloré)
            type_poly = poly.get("type", "")
            type_item = QTableWidgetItem(type_poly)
            type_item.setTextAlignment(Qt.AlignCenter)
            if type_poly == "ACTUELLE":
                type_item.setBackground(QColor("#d1fae5"))
                type_item.setForeground(QColor("#065f46"))
            else:
                type_item.setBackground(QColor("#fef3c7"))
                type_item.setForeground(QColor("#92400e"))
            font = QFont()
            font.setBold(True)
            type_item.setFont(font)
            self.table.setItem(row, 0, type_item)

            # Colonne 1 : Poste
            self.table.setItem(row, 1, QTableWidgetItem(poly.get("poste_code", "N/A")))

            # Colonne 2 : Niveau (coloré)
            niveau = poly.get("niveau")
            niveau_item = QTableWidgetItem(f"N{niveau}" if niveau else "N/A")
            niveau_item.setTextAlignment(Qt.AlignCenter)
            if niveau:
                if niveau == 1:
                    niveau_item.setBackground(QColor("#fef2f2"))
                    niveau_item.setForeground(QColor("#dc2626"))
                elif niveau == 2:
                    niveau_item.setBackground(QColor("#fffbeb"))
                    niveau_item.setForeground(QColor("#d97706"))
                elif niveau == 3:
                    niveau_item.setBackground(QColor("#f0fdf4"))
                    niveau_item.setForeground(QColor("#059669"))
                elif niveau == 4:
                    niveau_item.setBackground(QColor("#eff6ff"))
                    niveau_item.setForeground(QColor("#2563eb"))
            self.table.setItem(row, 2, niveau_item)

            # Colonne 3 : Date évaluation
            date_eval = poly.get("date_evaluation")
            date_str = self._format_date(date_eval) if date_eval else "N/A"
            self.table.setItem(row, 3, QTableWidgetItem(date_str))

            # Colonne 4 : Prochaine évaluation
            date_next = poly.get("prochaine_evaluation")
            date_next_str = self._format_date(date_next) if date_next else "—"
            self.table.setItem(row, 4, QTableWidgetItem(date_next_str))

            # Colonne 5 : Commentaire
            commentaire = poly.get("commentaire", "")
            self.table.setItem(row, 5, QTableWidgetItem(commentaire or "—"))

            # Colonne 6 : ID (caché)
            self.table.setItem(row, 6, QTableWidgetItem(str(poly.get("id", ""))))

        # Mise à jour des stats
        self.stats_label.setText(f"{len(filtered_data)} polyvalence(s)")
