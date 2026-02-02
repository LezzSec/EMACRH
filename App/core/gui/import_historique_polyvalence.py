# -*- coding: utf-8 -*-
"""
Interface d'import manuel de données historiques de polyvalence
Permet d'ajouter des anciennes actions pour lesquelles il n'y avait pas de traçabilité
"""

import csv
import uuid
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QComboBox, QSpinBox, QTextEdit,
    QMessageBox, QGroupBox, QFormLayout, QFileDialog, QAbstractItemView, QWidget
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from core.db.configbd import get_connection
from core.services.polyvalence_logger import log_polyvalence_action
from core.gui.emac_ui_kit import show_error_message

logger = logging.getLogger(__name__)


class ImportHistoriquePolyvalenceDialog(QDialog):
    """
    Dialogue pour importer des données historiques de polyvalence manuellement.
    """

    def __init__(self, operateur_id=None, parent=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.import_batch_id = None  # Sera généré à la première insertion

        self.setWindowTitle("Import de données historiques de polyvalence")
        self.setGeometry(150, 100, 1000, 700)

        self._init_ui()
        self._load_operateurs()
        self._load_postes()

        if operateur_id:
            self._select_operateur(operateur_id)

    def _init_ui(self):
        """Initialise l'interface utilisateur."""
        layout = QVBoxLayout(self)

        # === Header ===
        header = QLabel("📥 Import de données historiques")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                color: white;
                padding: 15px;
                border-radius: 8px;
            }
        """)
        layout.addWidget(header)

        subtitle = QLabel("Ajoutez des actions passées pour lesquelles vous n'aviez pas de traçabilité automatique")
        subtitle.setStyleSheet("color: #6b7280; font-style: italic; padding: 8px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # === Info discrète ===
        info_label = QLabel(
            "ℹ️  <b>Note :</b> Cet import ajoute uniquement des entrées dans l'historique "
            "pour documenter des évaluations passées. Les polyvalences actuelles ne sont pas modifiées."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #e0f2fe;
                color: #075985;
                padding: 8px 12px;
                border-left: 4px solid #0284c7;
                border-radius: 4px;
                font-size: 9pt;
            }
        """)
        layout.addWidget(info_label)

        # === Formulaire d'ajout ===
        form_group = QGroupBox("Ajouter une action historique")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Date de l'action
        self.date_action_input = QDateEdit()
        self.date_action_input.setDate(QDate.currentDate())
        self.date_action_input.setCalendarPopup(True)
        self.date_action_input.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Date de l'action :", self.date_action_input)

        # Type d'action
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems(["AJOUT", "MODIFICATION", "SUPPRESSION"])
        self.action_type_combo.currentTextChanged.connect(self._on_action_type_changed)
        form_layout.addRow("Type d'action :", self.action_type_combo)

        # Opérateur
        self.operateur_combo = QComboBox()
        form_layout.addRow("Opérateur :", self.operateur_combo)

        # Poste
        self.poste_combo = QComboBox()
        form_layout.addRow("Poste :", self.poste_combo)

        # Ancien niveau (pour MODIFICATION et SUPPRESSION)
        self.ancien_niveau_spin = QSpinBox()
        self.ancien_niveau_spin.setRange(1, 4)
        self.ancien_niveau_spin.setValue(2)
        self.ancien_niveau_label = QLabel("Ancien niveau :")
        form_layout.addRow(self.ancien_niveau_label, self.ancien_niveau_spin)

        # Ancienne date évaluation
        self.ancienne_date_eval_input = QDateEdit()
        self.ancienne_date_eval_input.setDate(QDate.currentDate().addYears(-1))
        self.ancienne_date_eval_input.setCalendarPopup(True)
        self.ancienne_date_eval_input.setDisplayFormat("dd/MM/yyyy")
        self.ancienne_date_eval_label = QLabel("Ancienne date éval. :")
        form_layout.addRow(self.ancienne_date_eval_label, self.ancienne_date_eval_input)

        # Nouveau niveau (pour AJOUT et MODIFICATION)
        self.nouveau_niveau_spin = QSpinBox()
        self.nouveau_niveau_spin.setRange(1, 4)
        self.nouveau_niveau_spin.setValue(3)
        self.nouveau_niveau_label = QLabel("Nouveau niveau :")
        form_layout.addRow(self.nouveau_niveau_label, self.nouveau_niveau_spin)

        # Nouvelle date évaluation
        self.nouvelle_date_eval_input = QDateEdit()
        self.nouvelle_date_eval_input.setDate(QDate.currentDate())
        self.nouvelle_date_eval_input.setCalendarPopup(True)
        self.nouvelle_date_eval_input.setDisplayFormat("dd/MM/yyyy")
        self.nouvelle_date_eval_label = QLabel("Nouvelle date éval. :")
        form_layout.addRow(self.nouvelle_date_eval_label, self.nouvelle_date_eval_input)

        # Nouvelle date prochaine évaluation
        self.nouvelle_prochaine_eval_input = QDateEdit()
        self.nouvelle_prochaine_eval_input.setDate(QDate.currentDate().addYears(10))
        self.nouvelle_prochaine_eval_input.setCalendarPopup(True)
        self.nouvelle_prochaine_eval_input.setDisplayFormat("dd/MM/yyyy")
        self.nouvelle_prochaine_eval_label = QLabel("Prochaine éval. :")
        form_layout.addRow(self.nouvelle_prochaine_eval_label, self.nouvelle_prochaine_eval_input)

        # Commentaire
        self.commentaire_input = QTextEdit()
        self.commentaire_input.setMaximumHeight(60)
        self.commentaire_input.setPlaceholderText("Optionnel : précisez le contexte de cette action...")
        form_layout.addRow("Commentaire :", self.commentaire_input)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Boutons d'action formulaire
        form_buttons = QHBoxLayout()

        self.add_btn = QPushButton("➕ Ajouter à la liste")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        self.add_btn.clicked.connect(self._add_to_list)
        form_buttons.addWidget(self.add_btn)

        self.clear_btn = QPushButton("🗑️ Effacer")
        self.clear_btn.clicked.connect(self._clear_form)
        form_buttons.addWidget(self.clear_btn)

        form_buttons.addStretch()
        layout.addLayout(form_buttons)

        # === Tableau des actions à importer ===
        table_label = QLabel("Actions en attente d'import")
        table_label.setFont(QFont("Arial", 12, QFont.Bold))
        table_label.setStyleSheet("color: #374151; padding: 8px 0;")
        layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Date", "Type", "Opérateur", "Poste", "Ancien N.", "Nouveau N.",
            "Date Éval.", "Commentaire", "_ids"
        ])
        self.table.setColumnHidden(8, True)  # Cacher colonne IDs
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        # Boutons action tableau
        table_buttons = QHBoxLayout()

        self.remove_btn = QPushButton("❌ Retirer la ligne sélectionnée")
        self.remove_btn.clicked.connect(self._remove_from_list)
        table_buttons.addWidget(self.remove_btn)

        self.import_csv_btn = QPushButton("📄 Importer depuis CSV")
        self.import_csv_btn.clicked.connect(self._import_from_csv)
        table_buttons.addWidget(self.import_csv_btn)

        table_buttons.addStretch()

        self.count_label = QLabel("0 action(s) en attente")
        self.count_label.setStyleSheet("font-weight: bold; color: #6b7280;")
        table_buttons.addWidget(self.count_label)

        layout.addLayout(table_buttons)

        # === Boutons finaux ===
        final_buttons = QHBoxLayout()

        self.save_all_btn = QPushButton("💾 Enregistrer toutes les actions")
        self.save_all_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                padding: 12px 24px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        self.save_all_btn.clicked.connect(self._save_all_actions)
        final_buttons.addWidget(self.save_all_btn)

        final_buttons.addStretch()

        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        final_buttons.addWidget(self.cancel_btn)

        layout.addLayout(final_buttons)

        # Initialiser l'affichage des champs
        self._on_action_type_changed("AJOUT")

    def _load_operateurs(self):
        """Charge la liste des opérateurs."""
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)

            cur.execute("""
                SELECT id, nom, prenom, matricule
                FROM personnel
                ORDER BY nom, prenom
            """)

            operateurs = cur.fetchall()

            self.operateurs_map = {}
            for op in operateurs:
                display = f"{op['nom']} {op['prenom']}"
                if op.get('matricule'):
                    display += f" ({op['matricule']})"
                self.operateur_combo.addItem(display, op['id'])
                self.operateurs_map[op['id']] = display

            cur.close()
            conn.close()

        except Exception as e:
            logger.exception(f"Erreur chargement operateurs: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les opérateurs", e)

    def _load_postes(self):
        """Charge la liste des postes."""
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)

            cur.execute("""
                SELECT id, poste_code
                FROM postes
                WHERE visible = 1
                ORDER BY poste_code
            """)

            postes = cur.fetchall()

            self.postes_map = {}
            for poste in postes:
                self.poste_combo.addItem(poste['poste_code'], poste['id'])
                self.postes_map[poste['id']] = poste['poste_code']

            cur.close()
            conn.close()

        except Exception as e:
            logger.exception(f"Erreur chargement postes: {e}")
            show_error_message(self, "Erreur", "Impossible de charger les postes", e)

    def _select_operateur(self, operateur_id):
        """Pré-sélectionne un opérateur dans le combo."""
        for i in range(self.operateur_combo.count()):
            if self.operateur_combo.itemData(i) == operateur_id:
                self.operateur_combo.setCurrentIndex(i)
                break

    def _on_action_type_changed(self, action_type):
        """Ajuste l'affichage des champs selon le type d'action."""
        is_ajout = action_type == "AJOUT"
        is_modif = action_type == "MODIFICATION"
        is_suppr = action_type == "SUPPRESSION"

        # Ancien niveau : visible pour MODIFICATION et SUPPRESSION
        self.ancien_niveau_label.setVisible(not is_ajout)
        self.ancien_niveau_spin.setVisible(not is_ajout)
        self.ancienne_date_eval_label.setVisible(not is_ajout)
        self.ancienne_date_eval_input.setVisible(not is_ajout)

        # Nouveau niveau : visible pour AJOUT et MODIFICATION
        self.nouveau_niveau_label.setVisible(not is_suppr)
        self.nouveau_niveau_spin.setVisible(not is_suppr)
        self.nouvelle_date_eval_label.setVisible(not is_suppr)
        self.nouvelle_date_eval_input.setVisible(not is_suppr)
        self.nouvelle_prochaine_eval_label.setVisible(not is_suppr)
        self.nouvelle_prochaine_eval_input.setVisible(not is_suppr)

    def _add_to_list(self):
        """Ajoute l'action à la liste d'attente."""
        # Récupérer les valeurs
        date_action = self.date_action_input.date().toPyDate()
        action_type = self.action_type_combo.currentText()
        operateur_id = self.operateur_combo.currentData()
        poste_id = self.poste_combo.currentData()
        commentaire = self.commentaire_input.toPlainText().strip()

        if not operateur_id or not poste_id:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un opérateur et un poste.")
            return

        ancien_niveau = self.ancien_niveau_spin.value() if action_type != "AJOUT" else None
        ancienne_date_eval = self.ancienne_date_eval_input.date().toPyDate() if action_type != "AJOUT" else None

        nouveau_niveau = self.nouveau_niveau_spin.value() if action_type != "SUPPRESSION" else None
        nouvelle_date_eval = self.nouvelle_date_eval_input.date().toPyDate() if action_type != "SUPPRESSION" else None
        nouvelle_prochaine_eval = self.nouvelle_prochaine_eval_input.date().toPyDate() if action_type != "SUPPRESSION" else None

        # Ajouter à la table
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(date_action.strftime("%d/%m/%Y")))
        self.table.setItem(row, 1, QTableWidgetItem(action_type))
        self.table.setItem(row, 2, QTableWidgetItem(self.operateurs_map[operateur_id]))
        self.table.setItem(row, 3, QTableWidgetItem(self.postes_map[poste_id]))
        self.table.setItem(row, 4, QTableWidgetItem(str(ancien_niveau) if ancien_niveau else "-"))
        self.table.setItem(row, 5, QTableWidgetItem(str(nouveau_niveau) if nouveau_niveau else "-"))
        self.table.setItem(row, 6, QTableWidgetItem(nouvelle_date_eval.strftime("%d/%m/%Y") if nouvelle_date_eval else "-"))
        self.table.setItem(row, 7, QTableWidgetItem(commentaire if commentaire else "-"))

        # Stocker les données en JSON dans la colonne cachée
        import json
        data = {
            "date_action": date_action.isoformat(),
            "action_type": action_type,
            "operateur_id": operateur_id,
            "poste_id": poste_id,
            "ancien_niveau": ancien_niveau,
            "ancienne_date_evaluation": ancienne_date_eval.isoformat() if ancienne_date_eval else None,
            "nouveau_niveau": nouveau_niveau,
            "nouvelle_date_evaluation": nouvelle_date_eval.isoformat() if nouvelle_date_eval else None,
            "nouvelle_prochaine_evaluation": nouvelle_prochaine_eval.isoformat() if nouvelle_prochaine_eval else None,
            "commentaire": commentaire
        }
        self.table.setItem(row, 8, QTableWidgetItem(json.dumps(data)))

        self._update_count()
        self._clear_form()

    def _remove_from_list(self):
        """Retire la ligne sélectionnée de la liste."""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
            self._update_count()

    def _clear_form(self):
        """Réinitialise le formulaire."""
        self.commentaire_input.clear()
        self.date_action_input.setDate(QDate.currentDate())
        self.action_type_combo.setCurrentIndex(0)

    def _update_count(self):
        """Met à jour le compteur d'actions."""
        count = self.table.rowCount()
        self.count_label.setText(f"{count} action(s) en attente")

    def _import_from_csv(self):
        """Importe des actions depuis un fichier CSV."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importer depuis CSV", "", "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')

                imported = 0
                for row_data in reader:
                    # TODO: Parser et ajouter chaque ligne
                    # Format attendu: date;type;operateur_id;poste_id;ancien_niveau;nouveau_niveau;date_eval;commentaire
                    pass

            QMessageBox.information(self, "Import CSV", f"{imported} action(s) importée(s) depuis le fichier CSV.")
            self._update_count()

        except Exception as e:
            logger.exception(f"Erreur import CSV: {e}")
            show_error_message(self, "Erreur d'import", "Impossible d'importer le fichier CSV", e)

    def _save_all_actions(self):
        """Enregistre toutes les actions de la liste dans la base de données."""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Attention", "Aucune action à enregistrer.")
            return

        reply = QMessageBox.question(
            self, "Confirmation",
            f"Êtes-vous sûr de vouloir enregistrer {self.table.rowCount()} action(s) historique(s) ?\n\n"
            "Ces données seront ajoutées à l'historique des polyvalences.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Générer un batch ID unique pour ce lot d'import
        if not self.import_batch_id:
            self.import_batch_id = f"IMPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        import json
        success_count = 0
        error_count = 0

        for row in range(self.table.rowCount()):
            try:
                # Récupérer les données de la ligne
                data_json = self.table.item(row, 8).text()
                data = json.loads(data_json)

                # Convertir les dates ISO en objets date
                from datetime import date
                data['date_action'] = datetime.fromisoformat(data['date_action'])
                if data.get('ancienne_date_evaluation'):
                    data['ancienne_date_evaluation'] = date.fromisoformat(data['ancienne_date_evaluation'])
                if data.get('nouvelle_date_evaluation'):
                    data['nouvelle_date_evaluation'] = date.fromisoformat(data['nouvelle_date_evaluation'])
                if data.get('nouvelle_prochaine_evaluation'):
                    data['nouvelle_prochaine_evaluation'] = date.fromisoformat(data['nouvelle_prochaine_evaluation'])

                # Enregistrer dans la base
                log_polyvalence_action(
                    action_type='IMPORT_MANUEL',
                    operateur_id=data['operateur_id'],
                    poste_id=data['poste_id'],
                    polyvalence_id=None,
                    ancien_niveau=data.get('ancien_niveau'),
                    ancienne_date_evaluation=data.get('ancienne_date_evaluation'),
                    nouveau_niveau=data.get('nouveau_niveau'),
                    nouvelle_date_evaluation=data.get('nouvelle_date_evaluation'),
                    nouvelle_prochaine_evaluation=data.get('nouvelle_prochaine_evaluation'),
                    utilisateur="Import manuel",
                    commentaire=data.get('commentaire'),
                    source="IMPORT_MANUEL",
                    import_batch_id=self.import_batch_id,
                    date_action=data['date_action']
                )

                success_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f"Ligne {row + 1} : {e}")

        # Message de confirmation
        if error_count == 0:
            QMessageBox.information(
                self, "Import réussi",
                f"✅ {success_count} action(s) historique(s) ont été enregistrée(s) avec succès !\n\n"
                f"Batch ID : {self.import_batch_id}"
            )
            self.accept()
        else:
            QMessageBox.warning(
                self, "Import partiel",
                f"⚠️ {success_count} action(s) enregistrée(s)\n"
                f"❌ {error_count} erreur(s)\n\n"
                f"Batch ID : {self.import_batch_id}"
            )


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = ImportHistoriquePolyvalenceDialog()
    dialog.show()
    sys.exit(app.exec_())
