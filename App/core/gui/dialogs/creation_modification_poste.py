from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QComboBox
)

from .besoin_poste_dialog import BesoinPosteDialog
from core.repositories.poste_repo import PosteRepository



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
            codes = PosteRepository.get_all_codes()
            self.delete_combobox.clear()
            for code in codes:
                self.delete_combobox.addItem(str(code))
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
            # Vérifier l'existence avant de créer
            if PosteRepository.get_by_code(post_name):
                QMessageBox.warning(self, "Attention", f"Le poste '{post_name}' existe déjà.")
                return

            # Créer le poste (visible=1, besoins_postes=0 par défaut)
            ok, msg, new_id = PosteRepository.create(
                {"poste_code": post_name, "visible": 1, "besoins_postes": 0}
            )
            if not ok:
                QMessageBox.critical(self, "Erreur", f"Impossible de créer le poste :\n{msg}")
                return

            # Demander le besoin en effectif
            dlg = BesoinPosteDialog(parent=self, titre_poste=post_name)
            if dlg.exec_() != dlg.Accepted:
                # Annulation → supprimer le poste créé
                PosteRepository.delete_by_code(post_name)
                QMessageBox.information(self, "Création annulée", "Le poste n'a pas été créé.")
                return

            besoin_val = dlg.get_besoin_int_or_none()

            # Mettre à jour le besoin (le poste a déjà été créé)
            if new_id and besoin_val is not None:
                PosteRepository.set_besoin(new_id, besoin_val)

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
            # Suppression via repository (logging inclus, contrainte d'intégrité laissée à MySQL)
            ok, msg = PosteRepository.delete_by_code(post_name)
            if not ok:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le poste :\n{msg}")
                return

            QMessageBox.information(self, "Succès",
                                    f"Le poste '{post_name}' a été supprimé avec succès.")
            self.load_posts()

        except Exception as e:
            QMessageBox.critical(self, "Erreur",
                                 f"Une erreur s'est produite lors de la suppression du poste :\n{e}")
