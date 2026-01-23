import json
import datetime
import logging

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QHBoxLayout, QFormLayout, QDateEdit, QComboBox, QApplication, QInputDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate, pyqtSignal

from core.gui.historique import HistoriqueDialog
from core.db.configbd import get_connection as get_db_connection
from core.services.matricule_service import generer_prochain_matricule

logger = logging.getLogger(__name__)

# -------- Logger compatible avec votre historique --------
def log_to_historique(connection, cursor, action: str, operateur_id=None, poste_id=None, description_data: dict = None):
    """
    Enregistre une action dans la table historique avec le bon format
    """
    try:
        # Récupérer l'utilisateur connecté
        utilisateur = None
        try:
            from core.services.auth_service import get_current_user
            current_user = get_current_user()
            if current_user:
                utilisateur = current_user.get('username') or f"{current_user.get('prenom', '')} {current_user.get('nom', '')}".strip()
        except Exception:
            pass

        # Ajouter la source dans les données
        if description_data is None:
            description_data = {}
        description_data['source'] = description_data.get('source', 'Gestion opérateur')

        desc_json = json.dumps(description_data, ensure_ascii=False)

        sql = """
            INSERT INTO historique (date_time, action, operateur_id, poste_id, description, utilisateur)
            VALUES (NOW(), %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (action, operateur_id, poste_id, desc_json, utilisateur))
    except Exception as e:
        logger.error(f"Erreur log historique: {e}")
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

        # Poste (seulement visibles)
        self.poste_combo = QComboBox(self)
        form.addRow("Poste :", self.poste_combo)
        self._charger_postes()

        # Niveau de compétence
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

        self.setWindowTitle("Ajouter du personnel")
        self.setGeometry(200, 200, 440, 300)

        layout = QVBoxLayout(self)

        # Titre
        title = QLabel("Gestion du personnel")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Section saisie
        section = QLabel("Ajouter du personnel")
        section.setFont(QFont("Arial", 11))
        layout.addWidget(section)

        self.add_nom_input = QLineEdit(self)
        self.add_nom_input.setPlaceholderText("Nom")
        layout.addWidget(self.add_nom_input)

        self.add_prenom_input = QLineEdit(self)
        self.add_prenom_input.setPlaceholderText("Prénom")
        layout.addWidget(self.add_prenom_input)

        # Date d'entrée
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

    # --------------------------- Helpers DB ---------------------------

    def _resolve_operateurs_columns(self, cursor):
        """
        Détecte automatiquement les colonnes 'nom'/'prenom' (ou 'firstname'/'lastname'...).
        Retourne: (col_nom, col_prenom, col_statut_ou_None)
        """
        cursor.execute("SHOW COLUMNS FROM personnel;")
        rows = cursor.fetchall()
        cols = {r["Field"] for r in rows} if rows and isinstance(rows[0], dict) else {r[0] for r in rows}

        # ✅ SÉCURITÉ: Whitelist des colonnes autorisées pour éviter les injections SQL
        ALLOWED_COLUMNS = {
            "nom", "lastname", "last_name", "name", "surname",
            "prenom", "firstname", "first_name", "given_name",
            "statut", "status"
        }

        # Filtrer uniquement les colonnes autorisées
        cols = cols & ALLOWED_COLUMNS

        cand_nom = ["nom", "lastname", "last_name", "name", "surname"]
        cand_prenom = ["prenom", "firstname", "first_name", "given_name"]
        cand_statut = ["statut", "status"]

        def pick(candidates, required=True):
            for c in candidates:
                if c in cols:
                    return c
            if required:
                raise RuntimeError(
                    "La table 'personnel' doit contenir l'une de ces colonnes : "
                    + ", ".join(candidates)
                )
            return None

        return pick(cand_nom), pick(cand_prenom), pick(cand_statut, required=False)

    def _get_or_create_operateur_id(self, cursor, nom: str, prenom: str):
        """Récupère l'id de l'opérateur tout juste inséré (fallback via SELECT)."""
        op_id = getattr(cursor, "lastrowid", None)
        if not op_id:
            # ✅ SÉCURITÉ: Utiliser des colonnes standard validées
            # La table personnel utilise toujours 'nom' et 'prenom'
            cursor.execute(
                "SELECT id FROM personnel "
                "WHERE `nom`=%s AND `prenom`=%s "
                "ORDER BY id DESC LIMIT 1",
                (nom, prenom),
            )
            row = cursor.fetchone()
            if row:
                op_id = row["id"] if isinstance(row, dict) else row[0]
        return op_id

    def _enregistrer_date_polyvalence(self, connection, cursor, operateur_id: int, poste_id: int, qdate: QDate, niveau: int = 1):
        """
        Insère ou met à jour la prochaine évaluation dans `polyvalence` (poste_id obligatoire).
        NE FAIT NI commit() NI start_transaction().
        Évite les doublons en vérifiant d'abord si l'entrée existe déjà.
        """
        date_iso = qdate.toString("yyyy-MM-dd")

        # Vérifier si l'entrée existe déjà
        cursor.execute(
            """
            SELECT id FROM polyvalence
            WHERE operateur_id = %s AND poste_id = %s
            """,
            (operateur_id, poste_id),
        )
        existing = cursor.fetchone()

        if existing:
            # Mettre à jour l'entrée existante
            cursor.execute(
                """
                UPDATE polyvalence
                SET prochaine_evaluation = %s, niveau = %s
                WHERE operateur_id = %s AND poste_id = %s
                """,
                (date_iso, niveau, operateur_id, poste_id),
            )
        else:
            # Insérer une nouvelle entrée avec le niveau choisi
            cursor.execute(
                """
                INSERT INTO polyvalence (operateur_id, poste_id, niveau, prochaine_evaluation)
                VALUES (%s, %s, %s, %s)
                """,
                (operateur_id, poste_id, niveau, date_iso),
            )

    # --------------------------- Action UI ---------------------------

    def add_operator(self):
        # Demander le type de personnel EN PREMIER
        type_personnel, ok = QInputDialog.getItem(
            self,
            "Type de personnel",
            "Quel type de personnel souhaitez-vous ajouter ?",
            ["Opérateur de Production (avec matricule)", "Autre Personnel (sans matricule)"],
            0,
            False
        )

        if not ok:
            return  # Annulation

        is_production = "Production" in type_personnel

        # Ensuite vérifier nom et prénom
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

            # ✅ SÉCURITÉ: Utiliser les colonnes standard (nom, prenom, statut)
            # La table personnel a été standardisée avec ces colonnes

            # Vérifier doublon exact nom+prenom
            cursor.execute(
                "SELECT id FROM personnel WHERE `nom`=%s AND `prenom`=%s",
                (nom, prenom)
            )
            existing = cursor.fetchone()

            if existing is None:
                existing_id = None
            else:
                existing_id = existing["id"] if dict_mode else existing[0]

            # Si production, demander le poste pour la polyvalence
            add_polyvalence = False
            if is_production:
                dlg = EvaluationDateDialog(connection, cursor, self)
                result = dlg.exec_()
                add_polyvalence = (result == QDialog.Accepted)

            poste_id = None
            qdate = None
            date_iso = None
            poste_name = None
            niveau = 1  # Niveau par défaut

            if add_polyvalence:
                poste_id = dlg.poste_combo.currentData()
                qdate = dlg.date_edit.date()
                date_iso = qdate.toString("yyyy-MM-dd")
                niveau = dlg.niveau_combo.currentData()  # Récupérer le niveau choisi

                # Récupérer le nom du poste pour le log
                if poste_id:
                    cursor.execute("SELECT poste_code FROM postes WHERE id = %s", (poste_id,))
                    poste_row = cursor.fetchone()
                    poste_name = poste_row["poste_code"] if (poste_row and dict_mode) else (poste_row[0] if poste_row else f"Poste #{poste_id}")

            # Insertion(s)
            if existing_id:
                operateur_id = int(existing_id)
            else:
                # Générer le matricule si c'est du personnel de production
                matricule = None
                if is_production:  # Si production, générer un matricule
                    matricule = generer_prochain_matricule()

                # ✅ SÉCURITÉ: Requêtes SQL avec colonnes hardcodées
                # Insérer avec ou sans matricule et statut
                if matricule:
                    cursor.execute(
                        "INSERT INTO personnel (`nom`, `prenom`, `statut`, `matricule`, `numposte`) "
                        "VALUES (%s, %s, 'ACTIF', %s, 'Production')",
                        (nom, prenom, matricule)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO personnel (`nom`, `prenom`, `statut`) "
                        "VALUES (%s, %s, 'ACTIF')",
                        (nom, prenom)
                    )

                operateur_id = self._get_or_create_operateur_id(cursor, nom, prenom)
                if not operateur_id:
                    raise RuntimeError("Impossible de récupérer l'id du nouvel opérateur.")

                # Insérer la date d'entrée dans personnel_infos
                date_entree = self.add_date_entree.date().toString("yyyy-MM-dd")

                # Vérifier si personnel_infos existe déjà
                cursor.execute("SELECT operateur_id FROM personnel_infos WHERE operateur_id = %s", (operateur_id,))
                exists_infos = cursor.fetchone()

                if exists_infos:
                    # Mettre à jour
                    cursor.execute(
                        "UPDATE personnel_infos SET date_entree = %s WHERE operateur_id = %s",
                        (date_entree, operateur_id)
                    )
                else:
                    # Créer
                    cursor.execute(
                        "INSERT INTO personnel_infos (operateur_id, date_entree) VALUES (%s, %s)",
                        (operateur_id, date_entree)
                    )

                # ✅ LOG création opérateur dans l'historique
                log_data = {
                    "operateur": f"{prenom} {nom}",
                    "type": "creation_operateur",
                    "details": f"Création de l'opérateur {prenom} {nom} (Date d'entrée: {self.add_date_entree.date().toString('dd/MM/yyyy')})"
                }
                if matricule:
                    log_data["matricule"] = matricule
                    log_data["numposte"] = "Production"
                    log_data["details"] += f" (matricule: {matricule}, poste: Production)"

                log_to_historique(
                    connection, cursor,
                    action="INSERT",
                    operateur_id=operateur_id,
                    poste_id=None,  # Pas de poste associé à la création d'opérateur
                    description_data=log_data
                )

            # Évaluation liée (seulement si polyvalence ajoutée)
            if add_polyvalence and poste_id:
                self._enregistrer_date_polyvalence(connection, cursor, operateur_id, poste_id, qdate, niveau)

                # Déterminer le texte du niveau pour le log
                niveau_texte = {
                    1: "Niveau 1 - Débutant",
                    2: "Niveau 2 - Intermédiaire",
                    3: "Niveau 3 - Confirmé",
                    4: "Niveau 4 - Expert/Formateur"
                }.get(niveau, f"Niveau {niveau}")

                # ✅ LOG planification évaluation dans l'historique
                log_to_historique(
                    connection, cursor,
                    action="INSERT",
                    operateur_id=operateur_id,
                    poste_id=poste_id,
                    description_data={
                        "operateur": f"{prenom} {nom}",
                        "poste": poste_name,
                        "niveau": niveau_texte,
                        "type": "planification_evaluation",
                        "prochaine_evaluation": date_iso,
                        "details": f"Planification évaluation pour le {date_iso} ({niveau_texte})"
                    }
                )

            # Commit unique
            connection.commit()

            # UI - Messages informatifs
            if existing_id:
                if add_polyvalence:
                    QMessageBox.information(
                        self, "Succès",
                        f"Évaluation ajoutée à l'opérateur existant (id={operateur_id})."
                    )
                else:
                    QMessageBox.information(
                        self, "Info",
                        f"Opérateur existant, aucune polyvalence ajoutée."
                    )
            else:
                if is_production:
                    msg = f"Opérateur '{prenom} {nom}' créé avec succès !\n\n"
                    if matricule:
                        msg += f"Matricule : {matricule}\n"
                        msg += f"Poste : Production\n"
                        msg += f"Cet opérateur apparaîtra dans les Listes et Grilles."
                        if add_polyvalence and poste_id:
                            msg += f"\nPolyvalence ajoutée au poste {poste_name}"
                    else:
                        msg += "Erreur : Pas de matricule généré."
                    QMessageBox.information(self, "Succès", msg)
                else:
                    QMessageBox.information(
                        self, "Succès",
                        f"Opérateur '{prenom} {nom}' créé (personnel non-production).\n\n"
                        f"Cet opérateur n'apparaîtra PAS dans les Listes et Grilles\n"
                        f"car il n'a pas de matricule."
                    )

            # Reset + notifier pour rafraîchir la liste ailleurs
            self.add_nom_input.clear()
            self.add_prenom_input.clear()
            self.data_changed.emit(int(operateur_id))

            # Proposer les documents templates pour le nouvel opérateur
            if not existing_id:
                self._proposer_documents_nouvel_operateur(nom, prenom)

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


    def _proposer_documents_nouvel_operateur(self, nom: str, prenom: str):
        """
        Propose les documents templates à générer pour un nouvel opérateur.
        """
        try:
            from core.services.template_service import check_templates_table_exists

            if not check_templates_table_exists():
                return

            # Demander à l'utilisateur s'il veut générer les documents
            reply = QMessageBox.question(
                self,
                "Documents d'accueil",
                f"Voulez-vous générer les documents d'accueil pour {prenom} {nom} ?\n\n"
                "(Consignes générales, Formation initiale, etc.)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                from core.gui.gestion_templates import TemplateSelectionDialog

                dialog = TemplateSelectionDialog(
                    contexte='NOUVEL_OPERATEUR',
                    operateur_nom=nom,
                    operateur_prenom=prenom,
                    parent=self
                )
                dialog.exec_()

        except Exception as e:
            # Ne pas bloquer si le module templates n'est pas disponible
            logger.error(f"Erreur lors de la proposition des documents: {e}")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = ManageOperatorsDialog()
    w.show()
    sys.exit(app.exec_())