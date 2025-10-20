# liste_personnel.py — Liste du personnel + changement de statut

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QListWidget
)
from PyQt5.QtCore import Qt
from core.db.configbd import get_connection as get_db_connection


# -------- Helpers DB (compat multi-drivers) --------
def _cursor(conn):
    """Retourne (cursor, dict_mode). dict_mode=True si le driver supporte dictionary=True."""
    try:
        cur = conn.cursor(dictionary=True)  
        return cur, True
    except TypeError:
        cur = conn.cursor()                
        return cur, False

def _rows(cur, dict_mode):
    """Renvoie une liste de dicts quelle que soit la lib DB."""
    if dict_mode:
        return cur.fetchall()
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


class ListePersonnelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Liste du Personnel")
        self.setGeometry(200, 200, 600, 400)

        self.layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        # Bouton pour changer le statut
        self.change_status_button = QPushButton("Changer le statut")
        self.change_status_button.clicked.connect(self.open_status_change_dialog)
        self.layout.addWidget(self.change_status_button)

        self.setLayout(self.layout)
        self.load_personnel_list()

    # ---------------- Data UI ----------------
    def load_personnel_list(self):
        """Charge et affiche la liste des opérateurs, triés par ordre alphabétique."""
        connection = get_db_connection()
        cursor, dict_mode = _cursor(connection)

        cursor.execute("""
            SELECT id, nom, prenom, UPPER(statut) AS statut
            FROM operateurs
            ORDER BY nom ASC, prenom ASC
        """)
        rows = _rows(cursor, dict_mode)

        self.table.setRowCount(len(rows))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nom", "Prénom", "Statut"])

        for i, row in enumerate(rows):
            nom = row["nom"]
            prenom = row["prenom"]
            statut = row["statut"]

            item_nom = QTableWidgetItem(nom)
            item_nom.setFlags(item_nom.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, item_nom)

            item_prenom = QTableWidgetItem(prenom)
            item_prenom.setFlags(item_prenom.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 1, item_prenom)

            item_statut = QTableWidgetItem(statut)
            item_statut.setFlags(item_statut.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 2, item_statut)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

        cursor.close()
        connection.close()

    def open_status_change_dialog(self):
        """Ouvre une boîte de dialogue pour changer le statut d'un opérateur."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Changer le statut")
        dialog.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout(dialog)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Rechercher un opérateur...")
        layout.addWidget(search_input)

        operator_list = QListWidget()
        layout.addWidget(operator_list)

        # Charger les opérateurs
        connection = get_db_connection()
        cursor, dict_mode = _cursor(connection)
        cursor.execute("""
            SELECT id, nom, prenom, UPPER(statut) AS statut
            FROM operateurs
            ORDER BY nom ASC, prenom ASC
        """)
        self.operators = _rows(cursor, dict_mode)
        cursor.close()
        connection.close()

        def update_operator_list():
            query = search_input.text().lower()
            operator_list.clear()
            for op in self.operators:
                full_name = f"{op['nom']} {op['prenom']} ({op['statut']})"
                if query in full_name.lower():
                    item = full_name
                    operator_list.addItem(item)
                    operator_list.item(operator_list.count() - 1).setData(Qt.UserRole, op["id"])

        search_input.textChanged.connect(update_operator_list)
        update_operator_list()

        change_button = QPushButton("Changer le statut")
        change_button.clicked.connect(lambda: self.change_operator_status(operator_list, dialog))
        layout.addWidget(change_button)

        dialog.setLayout(layout)
        dialog.exec()

    def change_operator_status(self, operator_list, dialog):
        """Change le statut de l'opérateur sélectionné dans la boîte de dialogue."""
        current_item = operator_list.currentItem()
        if not current_item:
            return

        operator_id = current_item.data(Qt.UserRole)

        connection = get_db_connection()
        cursor, dict_mode = _cursor(connection)

        cursor.execute("SELECT statut FROM operateurs WHERE id = %s", (operator_id,))
        res = cursor.fetchone()
        current_statut = (res["statut"] if dict_mode else res[0]).upper()
        new_statut = "INACTIF" if current_statut == "ACTIF" else "ACTIF"

        cursor.execute("UPDATE operateurs SET statut = %s WHERE id = %s", (new_statut, operator_id))
        connection.commit()

        cursor.close()
        connection.close()

        self.load_personnel_list()
        dialog.accept()
