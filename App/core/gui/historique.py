# historique.py — viewer des logs (schéma minimal)
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
    "INSERT": "Création",
    "UPDATE": "Modification",
    "DELETE": "Suppression",
    "ERROR":  "Erreur",
}

def fr_action(a: str) -> str:
    return ACTION_LABEL.get((a or "").upper(), a or "")

def make_resume(row: dict) -> str:
    """
    Exemple: 'Modification — opérateur 12, poste 34 — Changement niveau'
    """
    act = fr_action(row.get("action"))
    op  = row.get("operateur_id")
    po  = row.get("poste_id")
    desc = row.get("description") or ""

    bits = [act]
    sub = []
    if op not in (None, ""): sub.append(f"opérateur {op}")
    if po not in (None, ""): sub.append(f"poste {po}")
    if sub: bits.append(" — " + ", ".join(sub))
    if desc: bits.append(" — " + str(desc))
    return "".join(bits)


class HistoriqueDialog(QDialog):
    """
    Visionneuse des logs (table `historique`).
    - Filtres: période, Action, recherche (action/description/opérateur/poste)
    - Tri chrono décroissant
    - Bouton "Vider la période…" (propose d'exporter avant suppression)
    - Réutilise UNE SEULE connexion DB
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique des modifications")
        self.resize(1100, 640)

        # Connexion DB persistante pour la durée de la fenêtre
        self.conn = None
        self._ensure_conn()

        root = QVBoxLayout(self)

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

        filters.addWidget(QLabel("Action"))
        self.action_filter = QComboBox()
        self.action_filter.addItems(["(Toutes)", "INSERT", "UPDATE", "DELETE", "ERROR"])
        self.action_filter.currentIndexChanged.connect(self.reload)
        filters.addWidget(self.action_filter)

        self.search = QLineEdit(placeholderText="Recherche (action, description, opérateur, poste)")
        self.search.returnPressed.connect(self.reload)
        filters.addWidget(self.search, stretch=1)

        self.simple_mode = QComboBox()
        self.simple_mode.addItems(["Affichage détaillé", "Mode simple"])
        self.simple_mode.currentIndexChanged.connect(self.reload)
        filters.addWidget(self.simple_mode)

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.clicked.connect(self.reload)
        filters.addWidget(self.btn_refresh)

        self.btn_clear = QPushButton("Vider la période…")
        self.btn_clear.clicked.connect(self._clear_range_with_optional_export)
        filters.addWidget(self.btn_clear)

        root.addLayout(filters)

        # --- Table ---
        self.table = QTableWidget()
        # Colonnes: Résumé | Date/Heure | Action | Opérateur | Poste | Description
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Résumé", "Date/Heure", "Action", "Opérateur", "Poste", "Description"
        ])
        self.table.setSortingEnabled(True)
        root.addWidget(self.table)

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

            if action_filter and action_filter != "(Toutes)":
                where.append("action = %s")
                params.append(action_filter)

            if search_text:
                like = f"%{search_text}%"
                # Recherche plein-texte simple + cast des entiers
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
            resume = make_resume(row)

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

            vals = [
                resume,
                dt_txt,
                action_txt,
                str(row.get("operateur_id", "") or ""),
                str(row.get("poste_id", "") or ""),
                str(row.get("description", "") or ""),
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c in (0, 5):  # tooltips utiles
                    item.setToolTip(v)
                self.table.setItem(r, c, item)

            # Couleurs selon action
            if action_txt == "Erreur":
                bg = QtGui.QColor(255, 235, 238)
            elif action_txt == "Suppression":
                bg = QtGui.QColor(255, 243, 224)
            elif action_txt == "Création":
                bg = QtGui.QColor(232, 245, 233)
            else:
                bg = None
            if bg:
                for c in range(self.table.columnCount()):
                    it = self.table.item(r, c)
                    if it: it.setBackground(bg)

        # Mode simple : masque colonnes Opérateur & Poste pour focus sur le texte
        simple = (self.simple_mode.currentIndex() == 1)
        cols_to_hide = [3, 4] if simple else []
        for c in range(self.table.columnCount()):
            self.table.setColumnHidden(c, c in cols_to_hide)

    # ---------- Clear + export ----------
    def _export_range(self, d_from: QDate, d_to: QDate):
        base_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if d_from == d_to:
            export_day(self.conn,
                       dt.date(d_from.year(), d_from.month(), d_from.day()),
                       output_dir=base_dir)
            QMessageBox.information(self, "Export",
                                    f"Export du {d_from.toString('dd/MM/yyyy')} effectué sur le Bureau.")
        else:
            d = dt.date(d_from.year(), d_from.month(), d_from.day())
            end = dt.date(d_to.year(), d_to.month(), d_to.day())
            while d <= end:
                export_day(self.conn, d, output_dir=base_dir)
                d += dt.timedelta(days=1)
            QMessageBox.information(self, "Export", "Exports journaliers effectués sur le Bureau.")

    def _clear_range_with_optional_export(self):
        d_from = self.from_date.date()
        d_to   = self.to_date.date()

        resp = QMessageBox.question(
            self, "Historique",
            "Voulez-vous exporter les logs de la période avant suppression ?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        if resp == QMessageBox.Cancel:
            return
        if resp == QMessageBox.Yes:
            try:
                self._export_range(d_from, d_to)
            except Exception as e:
                QMessageBox.warning(self, "Export", f"Échec de l'export :\n{e}")
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

            QMessageBox.information(self, "Historique", f"Suppression effectuée.\n{deleted} ligne(s) supprimée(s).")
            self.reload()

        except Exception as e:
            code = getattr(e, "errno", None) or (e.args[0] if getattr(e, "args", None) else "")
            msg  = getattr(e, "msg", None) or (e.args[1] if getattr(e, "args", None) and len(e.args) > 1 else str(e))
            QMessageBox.critical(self, "Historique", f"Échec de la suppression :\n{msg or code}")
        finally:
            try:
                cur.close()
            except Exception:
                pass
