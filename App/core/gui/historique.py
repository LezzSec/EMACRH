# historique.py – viewer des logs (version améliorée pour non-techniciens)
# Colonnes DB utilisées: id, date_time, action, operateur_id, poste_id, description

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QDateEdit, QMessageBox, QComboBox
)
from PyQt5.QtCore import QDate
from PyQt5 import QtGui

from core.db.configbd import get_connection as get_db_connection
from core.services.log_exporter import export_day

import json
import datetime as dt
import os

# --- Traductions & rendu lisible ---
ACTION_LABEL = {
    "INSERT": "Ajout",
    "UPDATE": "Modification",
    "DELETE": "Suppression",
    "ERROR":  "Erreur",
}

def fr_action(a: str) -> str:
    """Traduit l'action technique en français courant"""
    return ACTION_LABEL.get((a or "").upper(), a or "")

def get_entity_name(conn, entity_type: str, entity_id) -> str:
    """
    Récupère le nom lisible d'une entité (opérateur ou poste)
    """
    if entity_id is None or entity_id == "":
        return ""
    
    try:
        cur = conn.cursor(dictionary=True)
        if entity_type == "operateur":
            cur.execute("SELECT nom, prenom FROM operateurs WHERE id = %s", (entity_id,))
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

def parse_description(desc: str, action: str) -> str:
    """
    Analyse la description JSON et génère un texte compréhensible
    """
    if not desc:
        return ""
    
    try:
        data = json.loads(desc)
        
        # Pour les modifications (UPDATE)
        if action.upper() == "UPDATE" and "changes" in data:
            changes = data["changes"]
            parts = []
            
            field_translations = {
                "niveau": "Niveau de compétence",
                "date_evaluation": "Date d'évaluation",
                "prochaine_evaluation": "Prochaine évaluation",
                "nom": "Nom",
                "prenom": "Prénom",
                "statut": "Statut",
                "poste_code": "Code poste",
                "visible": "Visibilité",
                "atelier_id": "Atelier"
            }
            
            niveau_labels = {
                1: "Débutant",
                2: "Autonome",
                3: "Confirmé",
                4: "Expert"
            }
            
            for field, change in changes.items():
                field_name = field_translations.get(field, field)
                old_val = change.get("old", "")
                new_val = change.get("new", "")
                
                # Traduction spéciale pour le niveau
                if field == "niveau":
                    old_val = niveau_labels.get(old_val, old_val) if old_val else ""
                    new_val = niveau_labels.get(new_val, new_val) if new_val else ""
                
                # Format des dates
                if "date" in field.lower() and new_val:
                    try:
                        new_val = dt.datetime.fromisoformat(str(new_val)).strftime("%d/%m/%Y")
                    except:
                        pass
                if "date" in field.lower() and old_val:
                    try:
                        old_val = dt.datetime.fromisoformat(str(old_val)).strftime("%d/%m/%Y")
                    except:
                        pass
                
                parts.append(f"{field_name}: {old_val} → {new_val}")
            
            return " | ".join(parts)
        
        # Pour les ajouts (INSERT)
        elif action.upper() == "INSERT":
            if "niveau" in data:
                niveau = data["niveau"]
                niveau_labels = {1: "Débutant", 2: "Autonome", 3: "Confirmé", 4: "Expert"}
                return f"Niveau initial: {niveau_labels.get(niveau, niveau)}"
            return "Nouvelle entrée créée"
        
        # Pour les suppressions (DELETE)
        elif action.upper() == "DELETE":
            return "Entrée supprimée"
        
    except json.JSONDecodeError:
        # Si ce n'est pas du JSON, retourner tel quel
        return desc
    except Exception:
        return desc
    
    return desc

def make_resume(row: dict, conn=None) -> str:
    """
    Génère un résumé lisible de l'action
    Exemple: 'Modification de compétence – Jean DUPONT sur poste 0515 – Niveau: Confirmé → Expert'
    """
    act = fr_action(row.get("action"))
    op_id = row.get("operateur_id")
    po_id = row.get("poste_id")
    desc = row.get("description") or ""
    action = row.get("action", "")
    
    # Récupération des noms lisibles
    op_name = get_entity_name(conn, "operateur", op_id) if conn and op_id else None
    po_name = get_entity_name(conn, "poste", po_id) if conn and po_id else None
    
    # Construction du résumé
    parts = []
    
    # Type d'action avec contexte
    if action.upper() == "INSERT":
        parts.append("Ajout de compétence")
    elif action.upper() == "UPDATE":
        parts.append("Modification de compétence")
    elif action.upper() == "DELETE":
        parts.append("Suppression de compétence")
    else:
        parts.append(act)
    
    # Informations sur qui et où
    sub_parts = []
    if op_name:
        sub_parts.append(f"Opérateur: {op_name}")
    elif op_id:
        sub_parts.append(f"Opérateur #{op_id}")
    
    if po_name:
        sub_parts.append(f"Poste: {po_name}")
    elif po_id:
        sub_parts.append(f"Poste #{po_id}")
    
    if sub_parts:
        parts.append(" – " + " | ".join(sub_parts))
    
    # Détails de la modification
    parsed_desc = parse_description(desc, action)
    if parsed_desc:
        parts.append(" – " + parsed_desc)
    
    return "".join(parts)


class HistoriqueDialog(QDialog):
    """
    Visionneuse de l'historique des modifications
    - Filtres: période, type d'action, recherche
    - Tri chronologique décroissant (plus récent en premier)
    - Export et suppression des logs avec confirmation
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique des modifications")
        self.resize(1200, 700)

        # Connexion DB persistante pour la durée de la fenêtre
        self.conn = None
        self._ensure_conn()

        root = QVBoxLayout(self)

        # --- En-tête informatif ---
        info_label = QLabel("Consultez l'historique complet des modifications effectuées sur les compétences")
        info_label.setStyleSheet("padding: 8px; background-color: #e3f2fd; border-radius: 4px; color: #1976d2;")
        root.addWidget(info_label)

        # --- Filtres ---
        filters = QHBoxLayout()
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

        self.search = QLineEdit(placeholderText="Rechercher un opérateur, un poste...")
        self.search.returnPressed.connect(self.reload)
        filters.addWidget(self.search, stretch=1)

        self.simple_mode = QComboBox()
        self.simple_mode.addItems(["Affichage détaillé", "Mode simplifié"])
        self.simple_mode.currentIndexChanged.connect(self.reload)
        filters.addWidget(self.simple_mode)

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.clicked.connect(self.reload)
        filters.addWidget(self.btn_refresh)

        self.btn_clear = QPushButton("Archiver la période...")
        self.btn_clear.clicked.connect(self._clear_range_with_optional_export)
        self.btn_clear.setStyleSheet("background-color: #fff3e0; color: #e65100;")
        filters.addWidget(self.btn_clear)

        root.addLayout(filters)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Résumé de l'action", "Date et Heure", "Type", 
            "Opérateur", "Poste", "Détails"
        ])
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        # --- Compteur ---
        self.count_label = QLabel()
        self.count_label.setStyleSheet("padding: 5px; color: #666;")
        root.addWidget(self.count_label)

        self.reload()

    # ---------- Connexion ----------
    def _ensure_conn(self):
        try:
            if self.conn is None:
                self.conn = get_db_connection()
            else:
                # ping simple
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

            # Conversion du filtre français vers SQL
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

            sql = (
                "SELECT id, date_time, action, operateur_id, poste_id, description "
                "FROM historique "
                f"WHERE {' AND '.join(where)} "
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

        self.table.setRowCount(len(rows))
        
        for r, row in enumerate(rows):
            resume = make_resume(row, self.conn)

            # Date formatée FR
            dt_txt = str(row.get("date_time", ""))
            try:
                from datetime import datetime
                if not isinstance(dt_txt, str) and hasattr(dt_txt, "strftime"):
                    dt_txt = row["date_time"].strftime("%d/%m/%Y %H:%M:%S")
                else:
                    try:
                        dt_txt = datetime.fromisoformat(dt_txt).strftime("%d/%m/%Y %H:%M:%S")
                    except Exception:
                        pass
            except Exception:
                pass

            action_txt = fr_action(row.get("action", ""))
            
            # Noms lisibles pour opérateur et poste
            op_display = get_entity_name(self.conn, "operateur", row.get("operateur_id")) or ""
            po_display = get_entity_name(self.conn, "poste", row.get("poste_id")) or ""
            
            # Description parsée
            desc_display = parse_description(row.get("description", ""), row.get("action", ""))

            vals = [
                resume,
                dt_txt,
                action_txt,
                op_display,
                po_display,
                desc_display,
            ]
            
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c in (0, 5):  # tooltips utiles
                    item.setToolTip(v)
                self.table.setItem(r, c, item)

            # Couleurs selon action avec icônes
            if action_txt == "Erreur":
                bg = QtGui.QColor(255, 235, 238)  # Rouge pâle
            elif action_txt == "Suppression":
                bg = QtGui.QColor(255, 243, 224)  # Orange pâle
            elif action_txt == "Ajout":
                bg = QtGui.QColor(232, 245, 233)  # Vert pâle
            elif action_txt == "Modification":
                bg = QtGui.QColor(227, 242, 253)  # Bleu pâle
            else:
                bg = None
            
            if bg:
                for c in range(self.table.columnCount()):
                    it = self.table.item(r, c)
                    if it: it.setBackground(bg)

        # Mode simple : masque colonnes ID pour focus sur le contenu
        simple = (self.simple_mode.currentIndex() == 1)
        cols_to_hide = [3, 4] if simple else []
        for c in range(self.table.columnCount()):
            self.table.setColumnHidden(c, c in cols_to_hide)
        
        # Mise à jour du compteur
        self.count_label.setText(f"{len(rows)} modification(s) trouvée(s)")
        
        # Ajustement automatique des colonnes
        self.table.resizeColumnsToContents()

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

        # Confirmation finale
        confirm = QMessageBox.warning(
            self, "Confirmation de suppression",
            "Cette action va supprimer définitivement les logs de la période sélectionnée.\n\n"
            "Êtes-vous certain de vouloir continuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return

        # Suppression
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