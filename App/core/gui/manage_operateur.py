from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QHBoxLayout, QFormLayout, QDateEdit, QComboBox, QApplication
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate, pyqtSignal

from core.gui.historique import HistoriqueDialog
from core.db.configbd import get_connection as get_db_connection
import json
import datetime

# -------- Logger compatible avec votre historique --------
def log_to_historique(connection, cursor, action: str, operateur_id=None, poste_id=None, description_data: dict = None):
    """
    Enregistre une action dans la table historique avec le bon format
    """
    try:
        desc_json = json.dumps(description_data or {}, ensure_ascii=False)
        
        sql = """
            INSERT INTO historique (date_time, action, operateur_id, poste_id, description)
            VALUES (NOW(), %s, %s, %s, %s)
        """
        cursor.execute(sql, (action, operateur_id, poste_id, desc_json))
    except Exception as e:
        print(f"Erreur log historique: {e}")
        pass

# -------- Helpers DB (compat mysql-connector / psycopg) --------
def _cursor(conn):
    """Retourne (cursor, dict_mode). dict_mode=True si le driver supporte dictionary=True."""
    try:
        cur = conn.cursor(dictionary=True)
        return cur, True
    except TypeError:
        cur = conn.cursor()      
        return cur, False


# --------------------------- Dialog: Date + Poste ---------------------------

class EvaluationDateDialog(QDialog):
    """
    Fenêtre pour saisir la date d'évaluation (prochaine) et le poste.
    """
    def __init__(self, connection, cursor, parent=None):
        super().__init__(parent)
        self.connection = connection
        self.cursor = cursor

        self.setWindowTitle("Prochaine évaluation")
        self.setModal(True)
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)

        title = QLabel("Renseigner la prochaine évaluation")
        title.setWordWrap(True)
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        form = QFormLayout()

        # Date d'évaluation (à venir)
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addDays(30))
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date :", self.date_edit)

        # Poste (seulement visibles)
        self.poste_combo = QComboBox(self)
        form.addRow("Poste :", self.poste_combo)
        self._charger_postes()

        layout.addLayout(form)

        # Boutons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler", self)
        btn_ok = QPushButton("Enregistrer", self)
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._validate)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _charger_postes(self):
        """Remplit le combo avec les postes visibles (id + poste_code)."""
        try:
            self.cursor.execute(
                "SELECT id, poste_code FROM postes "
                "WHERE COALESCE(visible, 1) = 1 "
                "ORDER BY poste_code;"
            )
            rows = self.cursor.fetchall()
            self.poste_combo.clear()
            if not rows:
                self.poste_combo.addItem("Aucun poste disponible", None)
                return
            for r in rows:
                # r peut être un tuple (id, code) ou un dict {"id":..,"poste_code":..}
                if isinstance(r, dict):
                    poste_id, label = r.get("id"), r.get("poste_code")
                else:
                    poste_id, label = r[0], r[1]
                try:
                    poste_id = int(poste_id) if poste_id is not None else None
                except Exception:
                    pass
                self.poste_combo.addItem(str(label), poste_id)
        except Exception as e:
            self.poste_combo.clear()
            self.poste_combo.addItem("Erreur de chargement", None)
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les postes :\n{e}")

    def _validate(self):
        if self.poste_combo.currentData() is None:
            QMessageBox.warning(self, "Champ requis", "Veuillez sélectionner un poste.")
            return
        self.accept()


# --------------------------- Dialog principal ---------------------------

class ManageOperatorsDialog(QDialog):
    data_changed = pyqtSignal(int)  # émis après succès (opérateur_id)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ajouter un opérateur")
        self.setGeometry(200, 200, 440, 300)

        layout = QVBoxLayout(self)

        # Titre
        title = QLabel("Gestion des opérateurs")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Section saisie
        section = QLabel("Ajouter un opérateur")
        section.setFont(QFont("Arial", 11))
        layout.addWidget(section)

        self.add_nom_input = QLineEdit(self)
        self.add_nom_input.setPlaceholderText("Nom de l'opérateur")
        layout.addWidget(self.add_nom_input)

        self.add_prenom_input = QLineEdit(self)
        self.add_prenom_input.setPlaceholderText("Prénom de l'opérateur")
        layout.addWidget(self.add_prenom_input)

        # Bouton Ajouter
        self.add_button = QPushButton("Ajouter", self)
        self.add_button.setFont(QFont("Arial", 10))
        self.add_button.setStyleSheet(
            "font-size: 14px; padding: 10px 20px; border: 1px solid #ccc; border-radius: 6px;"
            "background-color: white; color: black;"
        )
        self.add_button.clicked.connect(self.add_operator)
        layout.addWidget(self.add_button, alignment=Qt.AlignCenter)

    # --------------------------- Helpers DB ---------------------------

    def _resolve_operateurs_columns(self, cursor):
        """
        Détecte automatiquement les colonnes 'nom'/'prenom' (ou 'firstname'/'lastname'...).
        Retourne: (col_nom, col_prenom, col_statut_ou_None)
        """
        cursor.execute("SHOW COLUMNS FROM personnel;")
        rows = cursor.fetchall()
        cols = {r["Field"] for r in rows} if rows and isinstance(rows[0], dict) else {r[0] for r in rows}

        cand_nom = ["nom", "lastname", "last_name", "name", "surname"]
        cand_prenom = ["prenom", "firstname", "first_name", "given_name"]
        cand_statut = ["statut", "status"]

        def pick(candidates, required=True):
            for c in candidates:
                if c in cols:
                    return c
            if required:
                raise RuntimeError(
                    "La table 'operateurs' doit contenir l'une de ces colonnes : "
                    + ", ".join(candidates)
                )
            return None

        return pick(cand_nom), pick(cand_prenom), pick(cand_statut, required=False)

    def _get_or_create_operateur_id(self, cursor, nom: str, prenom: str):
        """Récupère l'id de l'opérateur tout juste inséré (fallback via SELECT)."""
        op_id = getattr(cursor, "lastrowid", None)
        if not op_id:
            col_nom, col_prenom, _ = self._resolve_operateurs_columns(cursor)
            cursor.execute(
                f"SELECT id FROM personnel "
                f"WHERE `{col_nom}`=%s AND `{col_prenom}`=%s "
                f"ORDER BY id DESC LIMIT 1",
                (nom, prenom),
            )
            row = cursor.fetchone()
            if row:
                op_id = row["id"] if isinstance(row, dict) else row[0]
        return op_id

    def _enregistrer_date_polyvalence(self, connection, cursor, operateur_id: int, poste_id: int, qdate: QDate):
        """
        Insère la prochaine évaluation dans `polyvalence` (poste_id obligatoire).
        NE FAIT NI commit() NI start_transaction().
        """
        date_iso = qdate.toString("yyyy-MM-dd")
        cursor.execute(
            """
            INSERT INTO polyvalence (operateur_id, poste_id, prochaine_evaluation)
            VALUES (%s, %s, %s)
            """,
            (operateur_id, poste_id, date_iso),
        )

    # --------------------------- Action UI ---------------------------

    def add_operator(self):
        nom = self.add_nom_input.text().strip()
        prenom = self.add_prenom_input.text().strip()

        if not nom or not prenom:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un nom et un prénom valides.")
            return

        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)

            # --- transaction via autocommit ---
            old_autocommit = getattr(connection, "autocommit", True)
            try:
                connection.autocommit = False
            except Exception:
                try:
                    connection.autocommit(False)
                except Exception:
                    pass

            col_nom, col_prenom, col_statut = self._resolve_operateurs_columns(cursor)

            # Vérifier doublon exact nom+prenom
            cursor.execute(
                f"SELECT id FROM personnel WHERE `{col_nom}`=%s AND `{col_prenom}`=%s",
                (nom, prenom)
            )
            existing = cursor.fetchone()
            
            if existing is None:
                existing_id = None
            else:
                existing_id = existing["id"] if dict_mode else existing[0]

            # Demande date + poste (si annulé -> rien)
            dlg = EvaluationDateDialog(connection, cursor, self)
            if dlg.exec_() != QDialog.Accepted:
                try:
                    if hasattr(connection, "autocommit"):
                        connection.autocommit = old_autocommit
                except Exception:
                    pass
                QMessageBox.information(self, "Info", "Ajout annulé.")
                return

            poste_id = dlg.poste_combo.currentData()
            qdate = dlg.date_edit.date()
            date_iso = qdate.toString("yyyy-MM-dd")
            
            # Récupérer le nom du poste pour le log
            cursor.execute("SELECT poste_code FROM postes WHERE id = %s", (poste_id,))
            poste_row = cursor.fetchone()
            poste_name = poste_row["poste_code"] if (poste_row and dict_mode) else (poste_row[0] if poste_row else f"Poste #{poste_id}")

            # Insertion(s)
            if existing_id:
                operateur_id = int(existing_id)
            else:
                if col_statut:
                    cursor.execute(
                        f"INSERT INTO personnel (`{col_nom}`, `{col_prenom}`, `{col_statut}`) "
                        f"VALUES (%s, %s, 'ACTIF')",
                        (nom, prenom)
                    )
                else:
                    cursor.execute(
                        f"INSERT INTO personnel (`{col_nom}`, `{col_prenom}`) "
                        f"VALUES (%s, %s)",
                        (nom, prenom)
                    )
                operateur_id = self._get_or_create_operateur_id(cursor, nom, prenom)
                if not operateur_id:
                    raise RuntimeError("Impossible de récupérer l'id du nouvel opérateur.")

                # ✅ LOG création opérateur dans l'historique
                log_to_historique(
                    connection, cursor,
                    action="INSERT",
                    operateur_id=operateur_id,
                    poste_id=None,  # Pas de poste associé à la création d'opérateur
                    description_data={
                        "operateur": f"{prenom} {nom}",
                        "type": "creation_operateur",
                        "details": f"Création de l'opérateur {prenom} {nom}"
                    }
                )

            # Évaluation liée
            self._enregistrer_date_polyvalence(connection, cursor, operateur_id, poste_id, qdate)

            # ✅ LOG planification évaluation dans l'historique
            log_to_historique(
                connection, cursor,
                action="INSERT",
                operateur_id=operateur_id,
                poste_id=poste_id,
                description_data={
                    "operateur": f"{prenom} {nom}",
                    "poste": poste_name,
                    "type": "planification_evaluation",
                    "prochaine_evaluation": date_iso,
                    "details": f"Planification évaluation pour le {date_iso}"
                }
            )

            # Commit unique
            connection.commit()

            # UI
            if existing_id:
                QMessageBox.information(
                    self, "Succès",
                    f"Évaluation ajoutée à l'opérateur existant (id={operateur_id})."
                )
            else:
                QMessageBox.information(
                    self, "Succès",
                    f"Opérateur '{nom} {prenom}' et évaluation enregistrés."
                )

            # Reset + notifier pour rafraîchir la liste ailleurs
            self.add_nom_input.clear()
            self.add_prenom_input.clear()
            self.data_changed.emit(int(operateur_id))

        except Exception as e:
            try:
                if connection:
                    connection.rollback()
            except Exception:
                pass
            # ✅ LOG d'erreur dans l'historique
            try:
                log_to_historique(
                    connection, cursor,
                    action="ERROR",
                    operateur_id=None,
                    poste_id=None,
                    description_data={
                        "error": str(e),
                        "details": "Échec d'enregistrement opérateur/évaluation"
                    }
                )
                connection.commit()
            except Exception:
                pass
            QMessageBox.critical(self, "Échec de l'enregistrement", f"{e}")
        finally:
            try:
                if hasattr(connection, "autocommit"):
                    connection.autocommit = True
            except Exception:
                pass
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                if connection:
                    connection.close()
            except Exception:
                pass


# Test rapide en autonome
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = ManageOperatorsDialog()
    w.show()
    sys.exit(app.exec_())