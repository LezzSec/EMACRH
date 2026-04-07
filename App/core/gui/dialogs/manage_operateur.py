import json

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QHBoxLayout, QFormLayout, QDateEdit, QComboBox, QApplication, QInputDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate, pyqtSignal

from core.repositories.personnel_repo import PersonnelRepository
from core.repositories.poste_repo import PosteRepository
from core.repositories.polyvalence_repo import PolyvalenceRepository
from core.services.matricule_service import generer_prochain_matricule
from infrastructure.logging.optimized_db_logger import log_hist
from core.gui.components.emac_ui_kit import show_error_message
from core.services.permission_manager import require
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# --------------------------- Dialog: Date + Poste ---------------------------

class EvaluationDateDialog(QDialog):
    """
    Fenêtre pour saisir la date d'évaluation (prochaine) et le poste.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Ajouter une polyvalence (optionnel)")
        self.setModal(True)
        self.setFixedWidth(480)

        layout = QVBoxLayout(self)

        title = QLabel("Ajouter une polyvalence de production ?")
        title.setWordWrap(True)
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        subtitle = QLabel("Si cet opérateur n'est PAS dans la production, cliquez sur 'Passer'.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #6b7280; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        form = QFormLayout()

        self.poste_combo = QComboBox(self)
        form.addRow("Poste :", self.poste_combo)
        self._charger_postes()

        self.niveau_combo = QComboBox(self)
        self.niveau_combo.addItem("Niveau 1 - Débutant (réévaluation dans 1 mois)", 1)
        self.niveau_combo.addItem("Niveau 2 - Intermédiaire (réévaluation dans 1 mois)", 2)
        self.niveau_combo.addItem("Niveau 3 - Confirmé (réévaluation dans 10 ans)", 3)
        self.niveau_combo.addItem("Niveau 4 - Expert/Formateur (réévaluation dans 10 ans)", 4)
        self.niveau_combo.currentIndexChanged.connect(self._calculer_date_evaluation)
        form.addRow("Niveau de compétence :", self.niveau_combo)

        # Date d'évaluation (à venir) - calculée automatiquement
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Prochaine évaluation :", self.date_edit)

        # Calcul initial de la date
        self._calculer_date_evaluation()

        layout.addLayout(form)

        # Boutons
        btn_row = QHBoxLayout()
        btn_skip = QPushButton("Passer", self)
        btn_skip.setStyleSheet("background: #6b7280; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_skip.clicked.connect(self.reject)

        btn_cancel = QPushButton("Annuler", self)
        btn_ok = QPushButton("Ajouter Polyvalence", self)
        btn_ok.setStyleSheet("background: #10b981; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._validate)

        btn_row.addWidget(btn_skip)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _calculer_date_evaluation(self):
        """Calcule automatiquement la date de prochaine évaluation selon le niveau choisi."""
        niveau = self.niveau_combo.currentData()
        if niveau is None:
            return

        # Calcul selon le niveau
        if niveau == 1:
            jours = 30  # 1 mois
        elif niveau == 2:
            jours = 30  # 1 mois
        elif niveau in [3, 4]:
            jours = 3650  # 10 ans
        else:
            jours = 30  # Par défaut 1 mois

        date_future = QDate.currentDate().addDays(jours)
        self.date_edit.setDate(date_future)

    def _charger_postes(self):
        """Remplit le combo avec les postes visibles (id + poste_code)."""
        try:
            postes = PosteRepository.get_all_visibles()
            self.poste_combo.clear()
            if not postes:
                self.poste_combo.addItem("Aucun poste disponible", None)
                return
            for poste in postes:
                self.poste_combo.addItem(str(poste.poste_code), poste.id)
        except Exception as e:
            self.poste_combo.clear()
            self.poste_combo.addItem("Erreur de chargement", None)
            logger.exception(f"Erreur chargement postes: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les postes", e)

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

        self.setWindowTitle("Ajouter du personnel")
        self.setGeometry(200, 200, 440, 300)

        layout = QVBoxLayout(self)

        title = QLabel("Gestion du personnel")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        section = QLabel("Ajouter du personnel")
        section.setFont(QFont("Arial", 11))
        layout.addWidget(section)

        self.add_nom_input = QLineEdit(self)
        self.add_nom_input.setPlaceholderText("Nom")
        layout.addWidget(self.add_nom_input)

        self.add_prenom_input = QLineEdit(self)
        self.add_prenom_input.setPlaceholderText("Prénom")
        layout.addWidget(self.add_prenom_input)

        date_layout = QHBoxLayout()
        date_label = QLabel("Date d'entrée :")
        date_label.setFont(QFont("Arial", 10))
        self.add_date_entree = QDateEdit(self)
        self.add_date_entree.setCalendarPopup(True)  # Active le calendrier déroulant
        self.add_date_entree.setDate(QDate.currentDate())  # Date par défaut = aujourd'hui
        self.add_date_entree.setDisplayFormat("dd/MM/yyyy")
        self.add_date_entree.setMinimumDate(QDate(1950, 1, 1))  # Date min = 1950
        self.add_date_entree.setMaximumDate(QDate.currentDate())  # Date max = aujourd'hui
        self.add_date_entree.setMinimumWidth(150)
        self.add_date_entree.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 11px;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #ccc;
            }
        """)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.add_date_entree)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        # Bouton Ajouter
        self.add_button = QPushButton("Ajouter", self)
        self.add_button.setFont(QFont("Arial", 10))
        self.add_button.setStyleSheet(
            "font-size: 14px; padding: 10px 20px; border: 1px solid #ccc; border-radius: 6px;"
            "background-color: white; color: black;"
        )
        self.add_button.clicked.connect(self.add_operator)
        layout.addWidget(self.add_button, alignment=Qt.AlignCenter)

    # (Méthodes DB supprimées — toutes les opérations passent par les repositories)

    # --------------------------- Action UI ---------------------------

    def add_operator(self):
        try:
            require('rh.personnel.create')
        except PermissionError:
            QMessageBox.warning(self, "Accès refusé", "Vous n'avez pas les droits pour créer du personnel.")
            return

        # Demander le type de personnel EN PREMIER
        type_personnel, ok = QInputDialog.getItem(
            self,
            "Type de personnel",
            "Quel type de personnel souhaitez-vous ajouter ?",
            ["Opérateur de Production", "Autre Personnel"],
            0,
            False
        )

        if not ok:
            return  # Annulation

        is_production = "Production" in type_personnel

        # Si non-production, demander le service
        service_numposte = None
        if not is_production:
            service_value, ok_svc = QInputDialog.getItem(
                self,
                "Service",
                "Sélectionner le service :",
                ["Administratif", "Labo", "R&D", "Méthode", "Maintenance", "Logistique", "Autre"],
                0,
                False
            )
            if not ok_svc:
                return
            service_numposte = service_value

        # Ensuite vérifier nom et prénom
        nom = self.add_nom_input.text().strip()
        prenom = self.add_prenom_input.text().strip()

        if not nom or not prenom:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un nom et un prénom valides.")
            return

        # Si production, demander le poste pour la polyvalence AVANT la transaction
        add_polyvalence = False
        dlg = None
        if is_production:
            dlg = EvaluationDateDialog(self)
            result = dlg.exec_()
            add_polyvalence = (result == QDialog.Accepted)

        poste_id = None
        qdate = None
        date_iso = None
        poste_name = None
        niveau = 1  # Niveau par défaut

        if add_polyvalence and dlg:
            poste_id = dlg.poste_combo.currentData()
            qdate = dlg.date_edit.date()
            date_iso = qdate.toString("yyyy-MM-dd")
            niveau = dlg.niveau_combo.currentData()

        try:
            # Vérifier doublon nom+prenom
            existing_id = PersonnelRepository.get_by_nom_prenom(nom, prenom)

            # Récupérer le nom du poste pour les messages
            poste_name = None
            if poste_id:
                poste = PosteRepository.get_by_id(poste_id)
                poste_name = poste.poste_code if poste else f"Poste #{poste_id}"

            if existing_id:
                operateur_id = int(existing_id)
            else:
                # Générer le matricule
                matricule = generer_prochain_matricule()

                # Créer le personnel via repository (logging + EventBus inclus)
                data = {
                    "nom": nom,
                    "prenom": prenom,
                    "statut": "ACTIF",
                    "matricule": matricule,
                }
                if is_production:
                    data["numposte"] = "Production"
                elif service_numposte:
                    data["numposte"] = service_numposte

                ok, msg_create, new_id = PersonnelRepository.create(data)
                if not ok or not new_id:
                    raise RuntimeError(f"Impossible de créer l'opérateur : {msg_create}")
                operateur_id = new_id

                # Sauvegarder la date d'entrée
                date_entree = self.add_date_entree.date().toString("yyyy-MM-dd")
                PersonnelRepository.save_date_entree(operateur_id, date_entree)

                # Log création (le repository a déjà loggé, on ajoute le détail RH)
                log_hist(
                    action="INSERT",
                    table_name="personnel",
                    record_id=operateur_id,
                    operateur_id=operateur_id,
                    description=json.dumps({
                        "operateur": f"{prenom} {nom}",
                        "matricule": matricule,
                        "type": "creation_operateur",
                        "details": f"Création {prenom} {nom} (entrée: {self.add_date_entree.date().toString('dd/MM/yyyy')})",
                        **({"numposte": "Production"} if is_production else ({"numposte": service_numposte} if service_numposte else {})),
                    }, ensure_ascii=False),
                    source="GUI/manage_operateur",
                )

            # Ajouter la polyvalence si demandée
            if add_polyvalence and poste_id:
                niveau_texte = {
                    1: "Niveau 1 - Débutant",
                    2: "Niveau 2 - Intermédiaire",
                    3: "Niveau 3 - Confirmé",
                    4: "Niveau 4 - Expert/Formateur",
                }.get(niveau, f"Niveau {niveau}")

                PolyvalenceRepository.upsert_prochaine_evaluation(
                    operateur_id, poste_id, niveau, date_iso
                )

                log_hist(
                    action="INSERT",
                    table_name="polyvalence",
                    record_id=None,
                    operateur_id=operateur_id,
                    poste_id=poste_id,
                    description=json.dumps({
                        "operateur": f"{prenom} {nom}",
                        "poste": poste_name,
                        "niveau": niveau_texte,
                        "type": "planification_evaluation",
                        "prochaine_evaluation": date_iso,
                    }, ensure_ascii=False),
                    source="GUI/manage_operateur",
                )

            # Messages UI
            if existing_id:
                if add_polyvalence:
                    QMessageBox.information(
                        self, "Succès",
                        f"Évaluation ajoutée à l'opérateur existant (id={operateur_id})."
                    )
                else:
                    QMessageBox.information(self, "Info", "Opérateur existant, aucune polyvalence ajoutée.")
            else:
                if is_production:
                    msg = f"Opérateur '{prenom} {nom}' créé avec succès !\n\nMatricule : {matricule}\nPoste : Production\nCet opérateur apparaîtra dans les Listes et Grilles."
                    if add_polyvalence and poste_id:
                        msg += f"\nPolyvalence ajoutée au poste {poste_name}"
                else:
                    msg = (
                        f"Personnel '{prenom} {nom}' créé avec succès.\n\n"
                        f"Matricule : {matricule}\n"
                        f"Ce membre du personnel n'apparaîtra PAS dans les Listes et Grilles."
                    )
                QMessageBox.information(self, "Succès", msg)

            # Reset + signal
            self.add_nom_input.clear()
            self.add_prenom_input.clear()
            self.data_changed.emit(int(operateur_id))

        except Exception as e:
            logger.exception(f"Erreur enregistrement: {e}")
            show_error_message(self, "Erreur", "Échec de l'enregistrement", e)



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = ManageOperatorsDialog()
    w.show()
    sys.exit(app.exec_())