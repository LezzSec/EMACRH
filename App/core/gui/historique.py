# historique.py — viewer des logs (1 seule connexion réutilisée)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QDateEdit, QMessageBox, QComboBox
)
from PyQt5.QtCore import QDate

# ⬇️ Nouveaux imports ABSOLUS alignés sur ta structure
#    - on garde le nom get_db_connection via un alias pour ne rien casser dans le fichier
from core.db.configbd import get_connection as get_db_connection
from core.services.log_exporter import export_day

import json
import datetime as dt
import os


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

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.clicked.connect(self.reload)
        filters.addWidget(self.btn_refresh)

        self.btn_clear = QPushButton("Vider la période…")
        self.btn_clear.clicked.connect(self._clear_range_with_optional_export)
        filters.addWidget(self.btn_clear)

        root.addLayout(filters)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Date/Heure", "Utilisateur", "Action", "Table",
            "Record ID", "Description", "Détails", "Source"
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
            raise

    def _cursor(self):
        """Retourne (cursor, dict_mode) sur self.conn."""
        self._ensure_conn()
        try:
            cur = self.conn.cursor(dictionary=True)  # mysql-connector
            return cur, True
        except TypeError:
            cur = self.conn.cursor()                  # PyMySQL / MySQLdb
            return cur, False

    def closeEvent(self, event):
        """Ferme la connexion quand on ferme le viewer."""
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.conn = None
        super().closeEvent(event)

    # ----------------- Data helpers -----------------

    def _populate_table_filter(self, cur, date_col: str, df: str, dt_to: str, has):
        """Peuple le combo 'Table' avec les valeurs distinctes de la période (même curseur)."""
        if not has("table_name"):
            self.table_filter.blockSignals(True)
            self.table_filter.clear()
            self.table_filter.addItem("(Toutes)")
            self.table_filter.setEnabled(False)
            self.table_filter.blockSignals(False)
            return

        cur.execute(
            f"SELECT DISTINCT `table_name` FROM historique "
            f"WHERE `{date_col}` BETWEEN %s AND %s ORDER BY `table_name`",
            (df, dt_to),
        )
        rows = cur.fetchall()
        vals = []
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            vals = [r.get("table_name") for r in rows]
        else:
            vals = [r[0] for r in rows]

        current = self.table_filter.currentText()
        self.table_filter.blockSignals(True)
        self.table_filter.clear()
        self.table_filter.addItem("(Toutes)")
        for v in vals:
            if v is not None:
                self.table_filter.addItem(str(v))
        self.table_filter.setEnabled(True)
        if current:
            idx = self.table_filter.findText(current)
            if idx >= 0:
                self.table_filter.setCurrentIndex(idx)
        self.table_filter.blockSignals(False)

    # ----------------- Fetch -----------------

    def _fetch_logs(self, date_from: QDate, date_to: QDate, query_text: str, action_sel: str, table_sel: str):
        """Récupère les logs via la connexion persistante."""
        df = date_from.toString("yyyy-MM-dd") + " 00:00:00"
        dt_to = date_to.toString("yyyy-MM-dd") + " 23:59:59"
        like_txt = query_text.strip()

        cur, dict_mode = self._cursor()
        try:
            # Schéma (MySQL-like) — on adaptera pour Postgres plus tard
            cur.execute("SHOW TABLES LIKE %s", ("historique",))
            if not cur.fetchone():
                raise RuntimeError("La table 'historique' n'existe pas.")

            cur.execute("SHOW COLUMNS FROM historique;")
            cols_raw = cur.fetchall()
            colnames = {row["Field"] for row in cols_raw} if dict_mode else {row[0] for row in cols_raw}
            has = colnames.__contains__

            date_candidates = ["date_time", "created_at", "date", "timestamp", "ts"]
            date_col = next((c for c in date_candidates if has(c)), None)
            if not date_col:
                raise RuntimeError("La table 'historique' doit contenir une colonne date/heure.")

            # Peuple le filtre Table
            self._populate_table_filter(cur, date_col, df, dt_to, has)

            # Colonne utilisateur facultative
            user_candidates = ["utilisateur", "user", "user_id", "utilisateur_id", "login", "username"]
            user_col = next((c for c in user_candidates if has(c)), None)

            def sel_or_null(c):
                return f"`{c}`" if has(c) else f"NULL AS `{c}`"

            select_list = [
                f"`{date_col}` AS date_time",
                (f"`{user_col}` AS utilisateur") if user_col else "NULL AS utilisateur",
                sel_or_null("action"),
                sel_or_null("table_name"),
                sel_or_null("record_id"),
                sel_or_null("description"),
                sel_or_null("details"),
                sel_or_null("source"),
            ]

            sql = f"SELECT {', '.join(select_list)} FROM historique WHERE `{date_col}` BETWEEN %s AND %s"
            params = [df, dt_to]

            # Masque la ligne "planification"
            if has("description"):
                sql += " AND IFNULL(`description`, '') <> 'Planification prochaine évaluation'"

            # Filtre Action
            if action_sel and action_sel != "(Toutes)" and has("action"):
                sql += " AND `action` = %s"
                params.append(action_sel)

            # Filtre Table
            if table_sel and table_sel != "(Toutes)" and has("table_name"):
                sql += " AND `table_name` = %s"
                params.append(table_sel)

            # Filtre texte
            if like_txt:
                like = f"%{like_txt}%"
                search_cols = [c for c in ["action", "table_name", "record_id", "description", "source"] if has(c)]
                if user_col:
                    search_cols.append(user_col)
                preds = [f"IFNULL(`{c}`,'') LIKE %s" for c in search_cols]
                if has("details"):
                    preds.append("IFNULL(CAST(`details` AS CHAR),'') LIKE %s")
                if preds:
                    sql += " AND (" + " OR ".join(preds) + ")"
                    params += [like] * len(preds)

            # Tri
            order_by = f" ORDER BY `{date_col}` ASC"
            if has("id"):
                order_by += ", `id` ASC"
            sql += order_by

            cur.execute(sql, params)

            if dict_mode:
                return cur.fetchall()

            columns = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]

        finally:
            try:
                cur.close()
            except Exception:
                pass

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
            self.table.setItem(r, 0, QTableWidgetItem(str(row.get("date_time", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(str(row.get("utilisateur", ""))))
            self.table.setItem(r, 2, QTableWidgetItem(str(row.get("action", ""))))
            self.table.setItem(r, 3, QTableWidgetItem(str(row.get("table_name", ""))))
            self.table.setItem(r, 4, QTableWidgetItem(str(row.get("record_id", ""))))
            self.table.setItem(r, 5, QTableWidgetItem(str(row.get("description", ""))))

            details_val = row.get("details", "")
            try:
                if isinstance(details_val, (bytes, bytearray)):
                    details_val = details_val.decode("utf-8", errors="ignore")
                parsed = json.loads(details_val) if isinstance(details_val, str) else details_val
                details_str = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                details_str = str(details_val) if details_val is not None else ""
            self.table.setItem(r, 6, QTableWidgetItem(details_str))
            self.table.setItem(r, 7, QTableWidgetItem(str(row.get("source", ""))))

    # ----------------- Clear + export optionnel -----------------

    def _export_range(self, d_from: QDate, d_to: QDate):
        """
        Exporte la période :
        - ≤ 31 jours  : un dossier par jour (comportement actuel)
        - > 31 jours  : un dossier par mois (YYYY-MM) avec tous les jours dedans
        """
        start = dt.date.fromisoformat(d_from.toString("yyyy-MM-dd"))
        end = dt.date.fromisoformat(d_to.toString("yyyy-MM-dd"))
        nb_jours = (end - start).days + 1

        day = start
        if nb_jours <= 31:
            # export "classique" : logs/YYYY-MM-DD
            while day <= end:
                export_day(day, base_dir="logs", make_zip=False)
                day += dt.timedelta(days=1)
            return

        # export groupé par mois : logs/YYYY-MM/ (contient les CSV de chaque jour)
        while day <= end:
            month_dir = os.path.join("logs", day.strftime("%Y-%m"))
            export_day(day, base_dir=month_dir, make_zip=False)
            day += dt.timedelta(days=1)

    def _clear_range_with_optional_export(self):
        """Demande export puis supprime tous les logs de la période affichée."""
        dfrom = self.from_date.date()
        dto = self.to_date.date()
        txt_from = dfrom.toString("dd/MM/yyyy")
        txt_to = dto.toString("dd/MM/yyyy")

        resp = QMessageBox.question(
            self,
            "Vider l'historique",
            f"Voulez-vous exporter les logs de la période\n"
            f"du {txt_from} au {txt_to} avant suppression ?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        if resp == QMessageBox.Cancel:
            return

        try:
            if resp == QMessageBox.Yes:
                self._export_range(dfrom, dto)

            df = dfrom.toString("yyyy-MM-dd") + " 00:00:00"
            dt_to = dto.toString("yyyy-MM-dd") + " 23:59:59"

            cur, dict_mode = self._cursor()

            # Détection colonne date
            cur.execute("SHOW COLUMNS FROM historique;")
            cols_raw = cur.fetchall()
            colnames = {row["Field"] for row in cols_raw} if dict_mode else {row[0] for row in cols_raw}
            has = colnames.__contains__
            date_candidates = ["date_time", "created_at", "date", "timestamp", "ts"]
            date_col = next((c for c in date_candidates if has(c)), None)
            if not date_col:
                raise RuntimeError("La table 'historique' doit contenir une colonne date/heure.")

            cur.execute(f"DELETE FROM historique WHERE `{date_col}` BETWEEN %s AND %s", (df, dt_to))
            deleted = cur.rowcount
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
