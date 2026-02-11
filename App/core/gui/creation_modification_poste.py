from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QComboBox
)

from core.db.configbd import DatabaseConnection
from core.db.query_executor import QueryExecutor
from .besoin_poste_dialog import BesoinPosteDialog
from core.services.logger import log_hist
from core.gui.historique import HistoriqueDialog


class CreationModificationPosteDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Création / Suppression de Poste")
        self.setGeometry(200, 200, 400, 400)

        layout = QVBoxLayout()

        # --- Création ---
        self.add_label = QLabel("Créer un nouveau poste (20 caractères max) :", self)
        layout.addWidget(self.add_label)

        self.add_input = QLineEdit(self)
        self.add_input.setMaxLength(20)  
        self.add_input.setPlaceholderText("Nom du poste (ex: 0123, A001, ...) ")
        layout.addWidget(self.add_input)

        self.add_button = QPushButton("Créer", self)
        self.add_button.clicked.connect(self.add_post)
        layout.addWidget(self.add_button)

        # --- Suppression ---
        self.delete_label = QLabel("Supprimer un poste existant :", self)
        layout.addWidget(self.delete_label)

        self.delete_combobox = QComboBox(self)
        layout.addWidget(self.delete_combobox)

        self.delete_button = QPushButton("Supprimer", self)
        self.delete_button.clicked.connect(self.delete_post)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)
        self.load_posts()

    # ------------------ Data ------------------

    def load_posts(self):
        """Charge les postes existants dans le combobox de suppression."""
        try:
            rows = QueryExecutor.fetch_all(
                "SELECT poste_code FROM postes ORDER BY poste_code ASC",
                dictionary=True
            )

            self.delete_combobox.clear()
            for r in rows:
                self.delete_combobox.addItem(str(r["poste_code"]))

        except Exception as e:
            QMessageBox.critical(self, "Erreur",
                                 f"Une erreur s'est produite lors du chargement des postes :\n{e}")

    def add_post(self):
        post_name = (self.add_input.text() or "").strip()

        if not post_name:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un code de poste valide.")
            return

        # Auto-normalisation simple : si code 3 chiffres -> pad à 4
        if len(post_name) == 3 and post_name.isdigit():
            post_name = f"0{post_name}"

        try:
            with DatabaseConnection() as connection:
                cursor = connection.cursor(dictionary=True)

                exists = QueryExecutor.exists('postes', {'poste_code': post_name})
                if exists:
                    QMessageBox.warning(self, "Attention", f"Le poste '{post_name}' existe déjà.")
                    return

                QueryExecutor.execute_write(
                    "INSERT INTO postes (poste_code, visible, besoins_postes) VALUES (%s, 1, 0)",
                    (post_name,)
                )

                dlg = BesoinPosteDialog(parent=self, titre_poste=post_name)
                if dlg.exec_() != dlg.Accepted:
                    connection.rollback()
                    QMessageBox.information(self, "Création annulée", "Le poste n'a pas été créé.")
                    return

                besoin_val = dlg.get_besoin_int_or_none()

                cursor.execute(
                    "UPDATE postes SET besoins_postes = %s WHERE poste_code = %s",
                    (besoin_val, post_name)
                )
                connection.commit()
                cursor.close()

            # Logger la création du poste
            import json
            log_hist(
                action="INSERT",
                table_name="postes",
                record_id=None,
                description=json.dumps({
                    "poste_code": post_name,
                    "besoins_postes": besoin_val if besoin_val is not None else 0,
                    "type": "creation_poste"
                }, ensure_ascii=False),
                source="GUI/creation_modification_poste"
            )

            QMessageBox.information(self, "Succès", f"Le poste '{post_name}' a été créé avec succès.")
            self.add_input.clear()
            self.load_posts()

        except Exception as e:
            QMessageBox.critical(self, "Erreur",
                                 f"Une erreur s'est produite lors de la création du poste :\n{e}")


    def delete_post(self):
        post_name = self.delete_combobox.currentText().strip()
        if not post_name:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un poste à supprimer.")
            return

        confirm = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer définitivement le poste '{post_name}' ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            # Suppression (⚠️ laisse la contrainte d'intégrité référentielle décider si relié à polyvalence)
            QueryExecutor.execute_write(
                "DELETE FROM postes WHERE poste_code = %s",
                (post_name,)
            )

            # Logger la suppression du poste
            import json
            log_hist(
                action="DELETE",
                table_name="postes",
                record_id=None,
                description=json.dumps({
                    "poste_code": post_name,
                    "type": "suppression_poste"
                }, ensure_ascii=False),
                source="GUI/creation_modification_poste"
            )

            QMessageBox.information(self, "Succès",
                                    f"Le poste '{post_name}' a été supprimé avec succès.")
            self.load_posts()

        except Exception as e:
            QMessageBox.critical(self, "Erreur",
                                 f"Une erreur s'est produite lors de la suppression du poste :\n{e}")
