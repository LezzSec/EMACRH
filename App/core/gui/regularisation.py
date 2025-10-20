# regularisation.py – Ajout rapide d'opérateur avec polyvalences existantes
# Permet d'insérer un opérateur oublié avec toutes ses évaluations déjà définies

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QDateEdit, QComboBox,
    QHeaderView, QAbstractItemView, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from core.gui.historique import HistoriqueDialog
from core.db.configbd import get_connection as get_db_connection
from core.services.logger import log_hist

try:
    from core.services.audit_logger import log_insert, log_action
except ImportError:
    def log_action(action, table_name="", description="", details=None, connection=None, cursor=None):
        try:
            if cursor is None and connection is not None:
                cursor = connection.cursor()
            if cursor is None:
                return
            cursor.execute(
                "INSERT INTO historique (action, table_name, description, details, source) "
                "VALUES (%s, %s, %s, %s, %s)",
                (action, table_name or "", description or "", str(details or {}), "regularisation"),
            )
        except Exception:
            pass

    def log_insert(table_name, description="", record_id=None, details=None, connection=None, cursor=None):
        log_action("INSERT", table_name, description, {**(details or {}), "record_id": record_id},
                   connection=connection, cursor=cursor)


# -------- Helpers DB --------
def _cursor(conn):
    """Retourne (cursor, dict_mode)."""
    try:
        cur = conn.cursor(dictionary=True)
        return cur, True
    except TypeError:
        cur = conn.cursor()
        return cur, False


class RegularisationDialog(QDialog):
    """
    Fenêtre de régularisation pour ajouter rapidement un opérateur
    avec toutes ses polyvalences (niveaux + dates d'évaluation).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Régularisation Opérateur")
        self.setGeometry(150, 150, 900, 650)
        
        self.postes_data = []  # Liste des postes disponibles
        
        layout = QVBoxLayout(self)
        
        # === Section Informations Opérateur ===
        info_group = QGroupBox("Informations Opérateur")
        info_layout = QFormLayout()
        
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom de l'opérateur")
        info_layout.addRow("Nom :", self.nom_input)
        
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Prénom de l'opérateur")
        info_layout.addRow("Prénom :", self.prenom_input)
        
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(["ACTIF", "INACTIF"])
        info_layout.addRow("Statut :", self.statut_combo)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # === Section Polyvalences ===
        poly_group = QGroupBox("Polyvalences à définir")
        poly_layout = QVBoxLayout()
        
        # Boutons d'action rapide
        btn_row = QHBoxLayout()
        
        self.add_row_btn = QPushButton("+ Ajouter une ligne")
        self.add_row_btn.clicked.connect(self.add_polyvalence_row)
        btn_row.addWidget(self.add_row_btn)
        
        self.remove_row_btn = QPushButton("- Supprimer la ligne")
        self.remove_row_btn.clicked.connect(self.remove_polyvalence_row)
        btn_row.addWidget(self.remove_row_btn)
        
        btn_row.addStretch()
        poly_layout.addLayout(btn_row)
        
        # Table des polyvalences
        self.poly_table = QTableWidget()
        self.poly_table.setColumnCount(4)
        self.poly_table.setHorizontalHeaderLabels([
            "Poste", "Niveau (1-4)", "Date Évaluation", "Prochaine Évaluation"
        ])
        self.poly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.poly_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        poly_layout.addWidget(self.poly_table)
        
        poly_group.setLayout(poly_layout)
        layout.addWidget(poly_group, 1)
        
        # === Boutons de validation ===
        action_row = QHBoxLayout()
        action_row.addStretch()
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        action_row.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Enregistrer")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #0f172a;
                color: white;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #0b1220;
            }
        """)
        self.save_btn.clicked.connect(self.save_regularisation)
        action_row.addWidget(self.save_btn)
        
        layout.addLayout(action_row)
        
        # Charger les données
        self.load_postes()
        
        # Ajouter une ligne par défaut
        self.add_polyvalence_row()
    
    def load_postes(self):
        """Charge la liste des postes visibles."""
        try:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            
            cursor.execute(
                "SELECT id, poste_code FROM postes "
                "WHERE COALESCE(visible, 1) = 1 "
                "ORDER BY poste_code"
            )
            
            rows = cursor.fetchall()
            self.postes_data = []
            
            for r in rows:
                if dict_mode:
                    self.postes_data.append((r["id"], r["poste_code"]))
                else:
                    self.postes_data.append((r[0], r[1]))
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les postes :\n{e}")
    
    def add_polyvalence_row(self):
        """Ajoute une nouvelle ligne dans la table des polyvalences."""
        row = self.poly_table.rowCount()
        self.poly_table.insertRow(row)
        
        # Colonne 0 : ComboBox des postes
        poste_combo = QComboBox()
        for poste_id, poste_code in self.postes_data:
            poste_combo.addItem(poste_code, poste_id)
        self.poly_table.setCellWidget(row, 0, poste_combo)
        
        # Colonne 1 : ComboBox niveau (1-4)
        niveau_combo = QComboBox()
        niveau_combo.addItems(["", "1", "2", "3", "4"])
        self.poly_table.setCellWidget(row, 1, niveau_combo)
        
        # Colonne 2 : DateEdit pour date d'évaluation
        date_eval = QDateEdit()
        date_eval.setCalendarPopup(True)
        date_eval.setDisplayFormat("dd/MM/yyyy")
        date_eval.setDate(QDate.currentDate())
        self.poly_table.setCellWidget(row, 2, date_eval)
        
        # Colonne 3 : DateEdit pour prochaine évaluation
        date_next = QDateEdit()
        date_next.setCalendarPopup(True)
        date_next.setDisplayFormat("dd/MM/yyyy")
        date_next.setDate(QDate.currentDate().addDays(30))
        self.poly_table.setCellWidget(row, 3, date_next)
    
    def remove_polyvalence_row(self):
        """Supprime la ligne sélectionnée."""
        current_row = self.poly_table.currentRow()
        if current_row >= 0:
            self.poly_table.removeRow(current_row)
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une ligne à supprimer.")
    
    def validate_data(self):
        """Valide les données saisies."""
        # Vérifier nom et prénom
        nom = self.nom_input.text().strip()
        prenom = self.prenom_input.text().strip()
        
        if not nom or not prenom:
            QMessageBox.warning(self, "Attention", "Le nom et le prénom sont obligatoires.")
            return False
        
        # Vérifier qu'il y a au moins une polyvalence
        if self.poly_table.rowCount() == 0:
            QMessageBox.warning(self, "Attention", "Veuillez définir au moins une polyvalence.")
            return False
        
        # Vérifier chaque ligne de polyvalence
        for row in range(self.poly_table.rowCount()):
            niveau_combo = self.poly_table.cellWidget(row, 1)
            niveau = niveau_combo.currentText().strip()
            
            if not niveau:
                QMessageBox.warning(
                    self, "Attention",
                    f"Le niveau est obligatoire pour la ligne {row + 1}."
                )
                return False
        
        return True
    
    def save_regularisation(self):
        """Enregistre l'opérateur et toutes ses polyvalences."""
        if not self.validate_data():
            return
        
        nom = self.nom_input.text().strip()
        prenom = self.prenom_input.text().strip()
        statut = self.statut_combo.currentText()
        
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            
            # Désactiver autocommit pour transaction
            old_autocommit = getattr(connection, "autocommit", True)
            try:
                connection.autocommit = False
            except Exception:
                try:
                    connection.autocommit(False)
                except Exception:
                    pass
            
            # Vérifier si l'opérateur existe déjà
            cursor.execute(
                "SELECT id FROM operateurs WHERE nom = %s AND prenom = %s",
                (nom, prenom)
            )
            existing = cursor.fetchone()
            
            if existing:
                reply = QMessageBox.question(
                    self, "Opérateur existant",
                    f"L'opérateur {nom} {prenom} existe déjà.\n"
                    "Voulez-vous ajouter les polyvalences à cet opérateur existant ?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    connection.rollback()
                    return
                
                operateur_id = existing["id"] if dict_mode else existing[0]
            else:
                # Créer le nouvel opérateur
                cursor.execute(
                    "INSERT INTO operateurs (nom, prenom, statut) VALUES (%s, %s, %s)",
                    (nom, prenom, statut)
                )
                
                # Récupérer l'ID
                operateur_id = getattr(cursor, "lastrowid", None)
                if not operateur_id:
                    cursor.execute(
                        "SELECT id FROM operateurs WHERE nom = %s AND prenom = %s "
                        "ORDER BY id DESC LIMIT 1",
                        (nom, prenom)
                    )
                    row = cursor.fetchone()
                    operateur_id = row["id"] if dict_mode else row[0]
                
                # Logger la création
                log_insert(
                    "operateurs",
                    description=f"Régularisation opérateur {nom} {prenom}",
                    record_id=operateur_id,
                    details={"nom": nom, "prenom": prenom, "statut": statut},
                    connection=connection, cursor=cursor
                )
            
            # Insérer toutes les polyvalences
            poly_count = 0
            for row in range(self.poly_table.rowCount()):
                poste_combo = self.poly_table.cellWidget(row, 0)
                niveau_combo = self.poly_table.cellWidget(row, 1)
                date_eval_widget = self.poly_table.cellWidget(row, 2)
                date_next_widget = self.poly_table.cellWidget(row, 3)
                
                poste_id = poste_combo.currentData()
                niveau = niveau_combo.currentText().strip()
                date_eval = date_eval_widget.date().toString("yyyy-MM-dd")
                date_next = date_next_widget.date().toString("yyyy-MM-dd")
                
                if not niveau:
                    continue
                
                # Vérifier si la polyvalence existe déjà
                cursor.execute(
                    "SELECT id FROM polyvalence WHERE operateur_id = %s AND poste_id = %s",
                    (operateur_id, poste_id)
                )
                existing_poly = cursor.fetchone()
                
                if existing_poly:
                    # Mise à jour
                    cursor.execute(
                        """UPDATE polyvalence 
                           SET niveau = %s, date_evaluation = %s, prochaine_evaluation = %s
                           WHERE operateur_id = %s AND poste_id = %s""",
                        (niveau, date_eval, date_next, operateur_id, poste_id)
                    )
                else:
                    # Insertion
                    cursor.execute(
                        """INSERT INTO polyvalence 
                           (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (operateur_id, poste_id, niveau, date_eval, date_next)
                    )
                
                poly_count += 1
                
                # Logger chaque polyvalence
                log_insert(
                    "polyvalence",
                    description=f"Régularisation polyvalence niveau {niveau}",
                    record_id=operateur_id,
                    details={
                        "operateur_id": operateur_id,
                        "poste_id": poste_id,
                        "niveau": niveau,
                        "date_evaluation": date_eval,
                        "prochaine_evaluation": date_next
                    },
                    connection=connection, cursor=cursor
                )
            
            # Commit
            connection.commit()
            
            QMessageBox.information(
                self, "Succès",
                f"✅ Régularisation réussie !\n\n"
                f"Opérateur : {nom} {prenom}\n"
                f"Polyvalences enregistrées : {poly_count}"
            )
            
            self.accept()
            
        except Exception as e:
            try:
                if connection:
                    connection.rollback()
            except Exception:
                pass
            
            QMessageBox.critical(self, "Erreur", f"Échec de la régularisation :\n{e}")
            
        finally:
            try:
                if hasattr(connection, "autocommit"):
                    connection.autocommit = old_autocommit
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


# Test autonome
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = RegularisationDialog()
    dialog.show()
    sys.exit(app.exec_())