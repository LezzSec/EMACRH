# evaluation_calendar.py
# Calendrier des évaluations : marque les jours et liste opérateurs & postes du jour
# Double-clic sur une ligne -> ouvre l'Historique filtré pour l'opérateur.

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QCalendarWidget, QComboBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QTextCharFormat, QBrush, QFont

from core.db.configbd import get_connection as get_db_connection
from core.gui.historique import HistoriqueDialog

import json


class EvaluationCalendarDialog(QDialog):
    """
    Affiche un calendrier mensuel avec :
      - marquage des jours qui ont des 'prochaine_evaluation'
      - liste des opérateurs/postes pour le jour sélectionné
    Double-clic sur une ligne -> Historique filtré pour l'opérateur.
    La fenêtre réutilise UNE connexion DB jusqu'à sa fermeture.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calendrier des évaluations")
        self.resize(1000, 620)

        self.conn = None
        self._ensure_conn()

        self._rows = []  # mémorise les données de la table (op_id, poste_id, date, etc.)

        root = QVBoxLayout(self)

        # -- Filtres haut
        filters = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher opérateur (nom/prénom)...")
        self.search.returnPressed.connect(self.refresh_all)
        filters.addWidget(self.search, stretch=1)

        filters.addWidget(QLabel("Poste"))
        self.poste_filter = QComboBox()
        self.poste_filter.addItem("(Tous)")
        self.poste_filter.currentIndexChanged.connect(self.refresh_all)
        filters.addWidget(self.poste_filter)

        self.only_visible = QCheckBox("Postes visibles uniquement")
        self.only_visible.setChecked(True)
        self.only_visible.toggled.connect(self.refresh_all)
        filters.addWidget(self.only_visible)

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.clicked.connect(self.refresh_all)
        filters.addWidget(self.btn_refresh)

        root.addLayout(filters)

        # -- Corps : calendrier + table
        body = QHBoxLayout()

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.currentPageChanged.connect(self._month_changed)
        self.calendar.selectionChanged.connect(self._selection_changed)
        body.addWidget(self.calendar, stretch=1)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Opérateur", "Poste", "Date"])
        self.table.setSortingEnabled(True)
        self.table.cellDoubleClicked.connect(self._open_history_for_row)  # <-- double-clic
        body.addWidget(self.table, stretch=1)

        root.addLayout(body)

        # Préparation colonnes dynamiques
        self.op_nom_col, self.op_prenom_col = self._resolve_operateurs_name_columns()
        self.poste_label_col = self._resolve_poste_label_column()

        # charger les postes dans le filtre
        self._load_postes_filter()
        # affichage initial
        self.refresh_all()

    # --------------- Connexion / curseur ---------------

    def _ensure_conn(self):
        if self.conn is None:
            self.conn = get_db_connection()
        else:
            try:
                cur = self.conn.cursor()
                cur.close()
            except Exception:
                self.conn = get_db_connection()

    def _cursor(self):
        self._ensure_conn()
        try:
            cur = self.conn.cursor(dictionary=True)  # mysql-connector
            return cur, True
        except TypeError:
            cur = self.conn.cursor()                  # PyMySQL / MySQLdb / psycopg
            return cur, False

    def closeEvent(self, event):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.conn = None
        super().closeEvent(event)

    # --------------- Résolutions de colonnes dynamiques ---------------

    def _resolve_operateurs_name_columns(self):
        cur, dict_mode = self._cursor()
        try:
            cur.execute("SHOW COLUMNS FROM operateurs;")
            rows = cur.fetchall()
            cols = {r["Field"] for r in rows} if dict_mode else {r[0] for r in rows}
        finally:
            try: cur.close()
            except: pass

        cand_nom = ["nom", "lastname", "last_name", "name", "surname"]
        cand_pre = ["prenom", "firstname", "first_name", "given_name"]
        def pick(cands, fallback):
            for c in cands:
                if c in cols: return c
            return fallback
        return pick(cand_nom, "nom"), pick(cand_pre, "prenom")

    def _resolve_poste_label_column(self):
        cur, dict_mode = self._cursor()
        try:
            cur.execute("SHOW COLUMNS FROM postes;")
            rows = cur.fetchall()
            cols = {r["Field"] for r in rows} if dict_mode else {r[0] for r in rows}
        finally:
            try: cur.close()
            except: pass

        for c in ["poste_code", "nom", "libelle", "label", "name"]:
            if c in cols:
                return c
        return "poste_code"

    # --------------- Chargement filtres ---------------

    def _load_postes_filter(self):
        cur, dict_mode = self._cursor()
        try:
            where = ""
            if self.only_visible.isChecked():
                # seulement si la colonne existe
                try:
                    cur.execute("SHOW COLUMNS FROM postes LIKE 'visible';")
                    if cur.fetchone():
                        where = "WHERE COALESCE(visible,1)=1"
                except Exception:
                    pass

            cur.execute(f"SELECT id, {self.poste_label_col} FROM postes {where} ORDER BY {self.poste_label_col}")
            rows = cur.fetchall()
            self.poste_filter.blockSignals(True)
            self.poste_filter.clear()
            self.poste_filter.addItem("(Tous)", None)
            if dict_mode:
                for r in rows:
                    self.poste_filter.addItem(str(r[self.poste_label_col]), r["id"])
            else:
                for r in rows:
                    self.poste_filter.addItem(str(r[1]), r[0])
            self.poste_filter.blockSignals(False)
        finally:
            try: cur.close()
            except: pass

    # --------------- Data helpers ---------------

    def _build_filters_sql(self):
        """Construit (where_sql, params) communs aux requêtes, selon filtres UI."""
        where = []
        params = []

        # filtre poste
        poste_id = self.poste_filter.currentData()
        if poste_id is not None:
            where.append("p.poste_id = %s")
            params.append(int(poste_id))

        # filtre visible sur postes (si demandé et colonne présente)
        if self.only_visible.isChecked():
            cur, _ = self._cursor()
            try:
                cur.execute("SHOW COLUMNS FROM postes LIKE 'visible';")
                if cur.fetchone():
                    where.append("COALESCE(ps.visible,1)=1")
            finally:
                try: cur.close()
                except: pass

        # filtre texte sur opérateur
        txt = self.search.text().strip()
        if txt:
            like = f"%{txt}%"
            where.append(f"(LOWER(o.`{self.op_nom_col}`) LIKE LOWER(%s) OR LOWER(o.`{self.op_prenom_col}`) LIKE LOWER(%s))")
            params.extend([like, like])

        where_sql = " AND ".join(where)
        if where_sql:
            where_sql = " AND " + where_sql
        return where_sql, params

    # --------------- UI refresh ---------------

    def refresh_all(self):
        """Rafraîchit les marquages du mois et la liste du jour sélectionné."""
        self._load_month_marks()
        self._selection_changed()

    def _month_changed(self, year, month):
        self._load_month_marks()

    def _clear_calendar_formats(self):
        default_fmt = QTextCharFormat()
        first = QDate(self.calendar.yearShown(), self.calendar.monthShown(), 1)
        d = QDate(first)
        while d.month() == first.month():
            self.calendar.setDateTextFormat(d, default_fmt)
            d = d.addDays(1)

    def _load_month_marks(self):
        """Calcule le nombre d'évals par jour du mois affiché et marque le calendrier."""
        self._clear_calendar_formats()

        year = self.calendar.yearShown()
        month = self.calendar.monthShown()
        first = QDate(year, month, 1)
        last = QDate(year, month, first.daysInMonth())

        df = first.toString("yyyy-MM-dd")
        dt = last.toString("yyyy-MM-dd")

        cur, dict_mode = self._cursor()
        try:
            where_sql, params = self._build_filters_sql()
            sql = (
                "SELECT p.prochaine_evaluation AS d, COUNT(*) AS n "
                "FROM polyvalence p "
                "JOIN operateurs o ON o.id = p.operateur_id "
                "JOIN postes ps ON ps.id = p.poste_id "
                "WHERE p.prochaine_evaluation BETWEEN %s AND %s"
                f"{where_sql} "
                "GROUP BY p.prochaine_evaluation"
            )
            cur.execute(sql, [df, dt, *params])
            rows = cur.fetchall()
        finally:
            try: cur.close()
            except: pass

        # Appliquer un marquage sur chaque jour avec au moins 1 éval
        for r in rows:
            d_str = r["d"] if dict_mode else r[0]
            n = r["n"] if dict_mode else r[1]
            try:
                y, m, dd = map(int, str(d_str).split("-"))
                qd = QDate(y, m, dd)
            except Exception:
                continue

            fmt = QTextCharFormat()
            fmt.setBackground(QBrush(Qt.yellow))
            if int(n) > 1:
                fmt.setFontWeight(QFont.Bold)
            self.calendar.setDateTextFormat(qd, fmt)

    def _selection_changed(self):
        """Charge la liste des évaluations pour la date sélectionnée."""
        day = self.calendar.selectedDate()
        d = day.toString("yyyy-MM-dd")

        where_sql, params = self._build_filters_sql()

        cur, dict_mode = self._cursor()
        try:
            # on récupère aussi les IDs pour le double-clic
            sql = (
                f"SELECT o.id AS operateur_id, ps.id AS poste_id, "
                f"o.`{self.op_nom_col}` AS nom, o.`{self.op_prenom_col}` AS prenom, "
                f"ps.`{self.poste_label_col}` AS poste, p.prochaine_evaluation AS d "
                "FROM polyvalence p "
                "JOIN operateurs o ON o.id = p.operateur_id "
                "JOIN postes ps ON ps.id = p.poste_id "
                "WHERE p.prochaine_evaluation = %s"
                f"{where_sql} "
                "ORDER BY nom, prenom"
            )
            cur.execute(sql, [d, *params])
            rows = cur.fetchall()
        finally:
            try: cur.close()
            except: pass

        self.table.setRowCount(0)
        self._rows = []  # reset

        for r in rows:
            if dict_mode:
                op_id, poste_id = r["operateur_id"], r["poste_id"]
                nom, prenom, poste, d_str = r["nom"], r["prenom"], r["poste"], r["d"]
            else:
                op_id, poste_id = r[0], r[1]
                nom, prenom, poste, d_str = r[2], r[3], r[4], r[5]

            self._rows.append({
                "operateur_id": op_id,
                "poste_id": poste_id,
                "nom": nom, "prenom": prenom,
                "poste": poste, "date": d_str
            })

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(f"{nom} {prenom}".strip()))
            self.table.setItem(row, 1, QTableWidgetItem(str(poste)))
            self.table.setItem(row, 2, QTableWidgetItem(str(d_str)))

    # --------------- Double-clic : ouvrir l'historique ---------------

    def _open_history_for_row(self, row: int, col: int):
        """Ouvre l'Historique préfiltré pour l'opérateur de la ligne."""
        if row < 0 or row >= len(self._rows):
            return
        data = self._rows[row]
        op_id = data["operateur_id"]

        try:
            dlg = HistoriqueDialog(self)
            # période large par défaut (12 mois passés -> +1 semaine)
            dlg.from_date.setDate(QDate.currentDate().addYears(-1))
            dlg.to_date.setDate(QDate.currentDate().addDays(7))
            # rechercher par operateur_id (ça matche la colonne record_id si elle est remplie)
            dlg.search.setText(str(op_id))
            dlg.reload()
            # si la colonne table_name existe, on force "polyvalence" si présent
            idx = dlg.table_filter.findText("polyvalence")
            if idx >= 0:
                dlg.table_filter.setCurrentIndex(idx)
                dlg.reload()
            dlg.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Ouverture de l'historique",
                                f"Impossible d'ouvrir l'historique pour l'opérateur {op_id}.\n{e}")
