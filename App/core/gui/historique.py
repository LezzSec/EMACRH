# historique.py — viewer des logs (1 seule connexion réutilisée)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QDateEdit, QMessageBox, QComboBox
)
from PyQt5.QtCore import QDate
from PyQt5 import QtGui

# ⬇️ Nouveaux imports ABSOLUS alignés sur ta structure
#    - on garde le nom get_db_connection via un alias pour ne rien casser dans le fichier
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

TABLE_LABEL = {
    "postes": "Postes",
    "operateurs": "Opérateurs",
    "polyvalence": "Polyvalence",
    "historique": "Historique",
}

def fr_action(a: str) -> str:
    return ACTION_LABEL.get((a or "").upper(), a or "")

def fr_table(t: str) -> str:
    return TABLE_LABEL.get((t or ""), t or "")

def make_resume(row: dict) -> str:
    """
    Construit une phrase lisible : ex.
    'Modification de Polyvalence — opérateur 12 sur poste 34 : niveau 3'
    """
    act = fr_action(row.get("action"))
    tab = fr_table(row.get("table_name"))
    rec = row.get("record_id") or ""
    desc = row.get("description") or ""

    # Extra depuis details si JSON
    details = row.get("details")
    if isinstance(details, (bytes, bytearray)):
        try:
            details = details.decode("utf-8", "ignore")
        except Exception:
            pass
    extra = ""
    try:
        parsed = json.loads(details) if isinstance(details, str) else details
        if isinstance(parsed, dict):
            op = parsed.get("operateur_id")
            po = parsed.get("poste_id") or parsed.get("poste_code")
            niv = parsed.get("niveau") or parsed.get("nouveau")
            bits = []
            if op is not None: bits.append(f"opérateur {op}")
            if po is not None: bits.append(f"poste {po}")
            if niv not in (None, ""): bits.append(f"niveau {niv}")
            if bits:
                extra = " — " + ", ".join(bits)
    except Exception:
        pass

    base = f"{act} de {tab}"
    if rec:
        base += f" (réf. {rec})"
    if desc:
        base += f" — {desc}"
    base += extra
    return base


class HistoriqueDialog(QDialog):
    """
    Visionneuse des logs (table `historique`).
    - Filtres: période, Action, Table (si colonne présente), recherche texte
    - Tri chrono croissant (tie-break sur id si dispo)
    - Bouton "Vider la période…" (propose d'exporter avant suppression)
    - Masque la ligne "Planification prochaine évaluation" (courte, sans date)
    - ⚠️ Réutilise UNE SEULE connexion DB pour éviter "Too many connections"
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique des modifications")
        self.resize(1100, 640)

        # --- Connexion DB persistante pour la durée de la fenêtre
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

        filters.addWidget(QLabel("Table"))
        self.table_filter = QComboBox()
        self.table_filter.addItem("(Toutes)")
        self.table_filter.setEnabled(False)  # activé si `table_name` existe
        self.table_filter.currentIndexChanged.connect(self.reload)
        filters.addWidget(self.table_filter)

        self.search = QLineEdit(placeholderText="Recherche (action, table, description, etc.)")
        self.search.returnPressed.connect(self.reload)
        filters.addWidget(self.search, stretch=1)
        # Affichage : Mode simple/ détaillé
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
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Résumé", "Date/Heure", "Utilisateur", "Action", "Table",
            "Référence", "Description", "Détails", "Source"
        ])
        self.table.setSortingEnabled(True)
        root.addWidget(self.table)

        self.reload()

    # ----------------- Connexion & curseurs -----------------

    def _ensure_conn(self):
        """(Re)crée self.conn si besoin."""
        try:
            if self.conn is None:
                self.conn = get_db_connection()
            else:
                try:
                    _ = self.conn.cursor()
                    _.close()
                except Exception:
                    self.conn = get_db_connection()
        except Exception:
            QMessageBox.critical(self, "Historique", "Impossible de se connecter à la base de données.")
            self.conn = None

    def _cursor(self):
        if self.conn is None:
            self._ensure_conn()
        if self.conn is None:
            raise RuntimeError("Connexion DB indisponible")
        cur = self.conn.cursor(dictionary=True)
        return cur

    # ----------------- Fetch -----------------

    def _fetch_logs(self, d_from: QDate, d_to: QDate, search_text: str, action_filter: str, table_filter: str):
        cur = None
        try:
            cur = self._cursor()

            where = [
                "date_time >= %s",
                "date_time < %s"
            ]
            params = [
                dt.datetime(d_from.year(), d_from.month(), d_from.day(), 0, 0, 0),
                dt.datetime(d_to.year(),   d_to.month(),   d_to.day(),   23, 59, 59)
            ]

            if action_filter and action_filter != "(Toutes)":
                where.append("action = %s")
                params.append(action_filter)

            # Table filter activé seulement si la colonne existe
            has_table_col = False
            try:
                cur.execute("SHOW COLUMNS FROM historique LIKE 'table_name'")
                has_table_col = cur.fetchone() is not None
            except Exception:
                has_table_col = False

            if has_table_col:
                self.table_filter.setEnabled(True)
                if self.table_filter.count() == 1:
                    # Remplir la liste des tables distinctes
                    cur.execute("SELECT DISTINCT table_name FROM historique WHERE table_name IS NOT NULL ORDER BY 1")
                    self.table_filter.blockSignals(True)
                    for row in cur.fetchall():
                        name = row.get("table_name")
                        if name:
                            self.table_filter.addItem(name)
                    self.table_filter.blockSignals(False)

                if table_filter and table_filter != "(Toutes)":
                    where.append("table_name = %s")
                    params.append(table_filter)
            else:
                self.table_filter.setEnabled(False)

            if search_text:
                like = f"%{search_text}%"
                where.append("(action LIKE %s OR table_name LIKE %s OR description LIKE %s OR details LIKE %s OR source LIKE %s)")
                params += [like, like, like, like, like]

            sql = (
                "SELECT id, date_time, utilisateur, action, table_name, record_id, description, details, source "
                "FROM historique "
                f"WHERE {' AND '.join(where)} "
                "ORDER BY date_time DESC, id DESC"
            )

            cur.execute(sql, params)
            rows = cur.fetchall() or []
            return rows
        finally:
            try:
                if cur:
                    cur.close()
            except Exception:
                pass

    # ----------------- UI Reload -----------------

    def reload(self):
        try:
            rows = self._fetch_logs(
                self.from_date.date(),
                self.to_date.date(),
                self.search.text(),
                self.action_filter.currentText(),
                self.table_filter.currentText(),
            )
        except Exception as e:
            code = getattr(e, "errno", None) or (e.args[0] if getattr(e, "args", None) else "")
            msg  = getattr(e, "msg", None) or (e.args[1] if getattr(e, "args", None) and len(e.args) > 1 else str(e))
            QMessageBox.critical(self, "Erreur", f"Impossible de charger l'historique :\n{msg or code}")
            return

        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            # Résumé lisible
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
            table_txt  = fr_table(row.get("table_name", ""))

            # Détails jolis + tooltip
            details_val = row.get("details", "")
            try:
                if isinstance(details_val, (bytes, bytearray)):
                    details_val = details_val.decode("utf-8", errors="ignore")
                parsed = json.loads(details_val) if isinstance(details_val, str) else details_val
                details_str = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                details_str = str(details_val) if details_val is not None else ""

            vals = [
                resume,
                dt_txt,
                str(row.get("utilisateur", "") or ""),
                action_txt,
                table_txt,
                str(row.get("record_id", "") or ""),
                str(row.get("description", "") or ""),
                details_str,
                str(row.get("source", "") or ""),
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c in (0, 7):  # tooltips utiles
                    item.setToolTip(v)
                self.table.setItem(r, c, item)

            # Couleurs selon action
            if action_txt == "Erreur":
                for c in range(self.table.columnCount()):
                    it = self.table.item(r, c)
                    if it: it.setBackground(QtGui.QColor(255, 235, 238))
            elif action_txt == "Suppression":
                for c in range(self.table.columnCount()):
                    it = self.table.item(r, c)
                    if it: it.setBackground(QtGui.QColor(255, 243, 224))
            elif action_txt == "Création":
                for c in range(self.table.columnCount()):
                    it = self.table.item(r, c)
                    if it: it.setBackground(QtGui.QColor(232, 245, 233))

        # Mode simple : masque colonnes techniques
        simple = (self.simple_mode.currentIndex() == 1)
        cols_to_hide = [2,4,5,7,8] if simple else []
        for c in range(self.table.columnCount()):
            self.table.setColumnHidden(c, c in cols_to_hide)

    # ----------------- Clear + export optionnel -----------------

    def _export_range(self, d_from: QDate, d_to: QDate):
        """
        Exporte la journée si d_from == d_to, sinon export multi-jours.
        Utilise export_day() pour la granularité jour.
        """
        base_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if d_from == d_to:
            export_day(self.conn,
                       dt.date(d_from.year(), d_from.month(), d_from.day()),
                       output_dir=base_dir)
            QMessageBox.information(self, "Export",
                                    f"Export du {d_from.toString('dd/MM/yyyy')} effectué sur le Bureau.")
        else:
            # multi-jours : dossier par jour
            d = dt.date(d_from.year(), d_from.month(), d_from.day())
            end = dt.date(d_to.year(), d_to.month(), d_to.day())
            while d <= end:
                export_day(self.conn, d, output_dir=base_dir)
                d += dt.timedelta(days=1)
            QMessageBox.information(self, "Export", "Exports journaliers effectués sur le Bureau.")

    def _clear_range_with_optional_export(self):
        """Propose d'exporter avant la suppression, puis supprime la période."""
        d_from = self.from_date.date()
        d_to   = self.to_date.date()

        # Demande export
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
