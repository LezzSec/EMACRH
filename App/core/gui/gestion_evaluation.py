# gestion_evaluation.py — Gestion moderne des évaluations
# Interface améliorée avec recherche, filtres intégrés et code couleur

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QComboBox, QLabel, QFileDialog,
    QStyledItemDelegate, QDateEdit, QAbstractItemView, QMessageBox,
    QLineEdit, QGroupBox, QWidget
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import date, timedelta
from core.db.configbd import get_connection as get_db_connection


# --- Délégué pour éditer les dates dans le tableau ---
class DateDelegate(QStyledItemDelegate):
    """Affiche un QDateEdit pour les cellules de dates."""

    def __init__(self, parent, on_commit):
        super().__init__(parent)
        self.on_commit = on_commit

    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd/MM/yyyy")
        return editor

    def setEditorData(self, editor, index):
        txt = index.model().data(index, Qt.EditRole) or index.model().data(index, Qt.DisplayRole)
        qd = QDate.fromString(str(txt), "dd/MM/yyyy")
        if not qd.isValid():
            qd = QDate.fromString(str(txt), "yyyy-MM-dd")
        if not qd.isValid():
            qd = QDate.currentDate()
        editor.setDate(qd)

    def setModelData(self, editor, model, index):
        qd = editor.date()
        model.setData(index, qd.toString("dd/MM/yyyy"), Qt.EditRole)
        if self.on_commit:
            self.on_commit(index.row(), index.column(), qd)


class GestionEvaluationDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestion des Évaluations")
        self.setGeometry(100, 100, 1200, 700)

        # Données
        self.all_evaluations = []
        self.is_edit_mode = False

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # === En-tête ===
        header = QLabel("Gestion des Évaluations")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Consultez et gérez les évaluations de polyvalence du personnel")
        subtitle.setStyleSheet("color: #6b7280; font-size: 12px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # === Section Recherche et Filtres ===
        filter_group = QGroupBox("Recherche et Filtres")
        filter_layout = QVBoxLayout()

        # Ligne 1: Recherche
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Rechercher :"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom, prénom ou poste...")
        self.search_input.textChanged.connect(self.apply_filters)
        search_row.addWidget(self.search_input)
        filter_layout.addLayout(search_row)

        # Ligne 2: Filtres
        combo_row = QHBoxLayout()

        combo_row.addWidget(QLabel("Personnel :"))
        self.personnel_filter = QComboBox()
        self.personnel_filter.currentIndexChanged.connect(self.apply_filters)
        combo_row.addWidget(self.personnel_filter)

        combo_row.addWidget(QLabel("Poste :"))
        self.poste_filter = QComboBox()
        self.poste_filter.currentIndexChanged.connect(self.apply_filters)
        combo_row.addWidget(self.poste_filter)

        combo_row.addWidget(QLabel("Statut :"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tous", "En retard", "À planifier (30j)", "À jour"])
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        combo_row.addWidget(self.status_filter)

        combo_row.addWidget(QLabel("Niveau :"))
        self.niveau_filter = QComboBox()
        self.niveau_filter.addItems(["Tous", "N/A", "D1", "D2", "D3", "D4"])
        self.niveau_filter.currentIndexChanged.connect(self.apply_filters)
        combo_row.addWidget(self.niveau_filter)

        filter_layout.addLayout(combo_row)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # === Statistiques ===
        stats_group = QGroupBox("Statistiques")
        stats_layout = QHBoxLayout()

        self.total_label = QLabel("Total : 0")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        stats_layout.addWidget(self.total_label)

        self.retard_label = QLabel("En retard : 0")
        self.retard_label.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 14px;")
        stats_layout.addWidget(self.retard_label)

        self.a_planifier_label = QLabel("À planifier : 0")
        self.a_planifier_label.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 14px;")
        stats_layout.addWidget(self.a_planifier_label)

        self.a_jour_label = QLabel("À jour : 0")
        self.a_jour_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
        stats_layout.addWidget(self.a_jour_label)

        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # === Tableau ===
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "_poly_id", "Nom", "Prénom", "Poste", "Niveau",
            "Date Évaluation", "Prochaine Évaluation", "Statut"
        ])
        self.table.setColumnHidden(0, True)  # ID technique caché
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table, 1)

        # === Boutons d'action ===
        btn_layout = QHBoxLayout()

        self.edit_btn = QPushButton("✏️ Modifier les dates")
        self.edit_btn.setCheckable(True)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:checked {
                background: #059669;
            }
        """)
        self.edit_btn.toggled.connect(self.toggle_edit_mode)
        btn_layout.addWidget(self.edit_btn)

        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)

        self.export_btn = QPushButton("📄 Exporter PDF")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4b5563;
            }
        """)
        self.export_btn.clicked.connect(self.export_to_pdf)
        btn_layout.addWidget(self.export_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton("Fermer")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        # Charger les données
        self.load_filter_options()
        self.load_data()

    def load_filter_options(self):
        """Charge les options des filtres Personnel et Poste."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Personnel
            self.personnel_filter.clear()
            self.personnel_filter.addItem("Tous", None)
            cursor.execute("""
                SELECT DISTINCT p.id, p.nom, p.prenom
                FROM personnel p
                INNER JOIN polyvalence poly ON poly.operateur_id = p.id
                WHERE p.statut = 'ACTIF'
                ORDER BY p.nom, p.prenom
            """)
            for row in cursor.fetchall():
                pid, nom, prenom = row
                self.personnel_filter.addItem(f"{nom} {prenom}", pid)

            # Poste
            self.poste_filter.clear()
            self.poste_filter.addItem("Tous", None)
            cursor.execute("""
                SELECT DISTINCT pos.id, pos.poste_code
                FROM postes pos
                INNER JOIN polyvalence poly ON poly.poste_id = pos.id
                ORDER BY pos.poste_code
            """)
            for row in cursor.fetchall():
                poste_id, poste_code = row
                self.poste_filter.addItem(poste_code, poste_id)

            cursor.close()
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les filtres :\n{e}")

    def load_data(self):
        """Charge toutes les évaluations depuis la base de données."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    poly.id,
                    pers.nom,
                    pers.prenom,
                    p.poste_code,
                    COALESCE(poly.niveau, 'N/A') AS niveau,
                    poly.date_evaluation,
                    poly.prochaine_evaluation
                FROM polyvalence poly
                JOIN personnel pers ON poly.operateur_id = pers.id
                JOIN postes p ON poly.poste_id = p.id
                ORDER BY pers.nom, pers.prenom, p.poste_code
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            # Stocker toutes les données
            self.all_evaluations = []
            today = date.today()

            for row in rows:
                poly_id, nom, prenom, poste_code, niveau, date_eval, prochaine_eval = row

                # Déterminer le statut
                statut = "Non défini"
                if prochaine_eval:
                    if isinstance(prochaine_eval, str):
                        from datetime import datetime
                        prochaine_eval = datetime.strptime(prochaine_eval, '%Y-%m-%d').date()

                    if prochaine_eval < today:
                        statut = "En retard"
                    elif prochaine_eval <= today + timedelta(days=30):
                        statut = "À planifier"
                    else:
                        statut = "À jour"

                # Formater les dates
                date_eval_str = date_eval.strftime('%d/%m/%Y') if date_eval else "Non défini"
                prochaine_eval_str = prochaine_eval.strftime('%d/%m/%Y') if prochaine_eval else "Non défini"

                self.all_evaluations.append({
                    'poly_id': poly_id,
                    'nom': nom,
                    'prenom': prenom,
                    'poste': poste_code,
                    'niveau': niveau,
                    'date_eval': date_eval_str,
                    'prochaine_eval': prochaine_eval_str,
                    'prochaine_eval_date': prochaine_eval,
                    'statut': statut
                })

            # Appliquer les filtres
            self.apply_filters()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les évaluations :\n{e}")

    def apply_filters(self):
        """Applique les filtres de recherche et affiche les résultats."""
        search_text = self.search_input.text().lower()
        personnel_id = self.personnel_filter.currentData()
        poste_id = self.poste_filter.currentData()
        status_filter = self.status_filter.currentText()
        niveau_filter = self.niveau_filter.currentText()

        # Filtrer les données
        filtered = []
        for eval_data in self.all_evaluations:
            # Filtre recherche
            if search_text:
                searchable = f"{eval_data['nom']} {eval_data['prenom']} {eval_data['poste']}".lower()
                if search_text not in searchable:
                    continue

            # Filtre statut
            if status_filter != "Tous":
                if status_filter == "À planifier (30j)" and eval_data['statut'] != "À planifier":
                    continue
                elif status_filter != "À planifier (30j)" and eval_data['statut'] != status_filter:
                    continue

            # Filtre niveau
            if niveau_filter != "Tous" and eval_data['niveau'] != niveau_filter:
                continue

            # Note: filtres personnel et poste nécessiteraient de stocker les IDs
            # Pour simplifier, on les ignore ici (peuvent être ajoutés si besoin)

            filtered.append(eval_data)

        # Afficher dans le tableau
        self.display_evaluations(filtered)

        # Mettre à jour les statistiques
        self.update_statistics(filtered)

    def display_evaluations(self, evaluations):
        """Affiche les évaluations dans le tableau avec code couleur."""
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)

        for eval_data in evaluations:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            # Colonne 0: ID (caché)
            self.table.setItem(row_pos, 0, QTableWidgetItem(str(eval_data['poly_id'])))

            # Colonnes 1-6: Données
            self.table.setItem(row_pos, 1, QTableWidgetItem(eval_data['nom']))
            self.table.setItem(row_pos, 2, QTableWidgetItem(eval_data['prenom']))
            self.table.setItem(row_pos, 3, QTableWidgetItem(eval_data['poste']))
            self.table.setItem(row_pos, 4, QTableWidgetItem(eval_data['niveau']))
            self.table.setItem(row_pos, 5, QTableWidgetItem(eval_data['date_eval']))
            self.table.setItem(row_pos, 6, QTableWidgetItem(eval_data['prochaine_eval']))

            # Colonne 7: Statut avec code couleur
            statut_item = QTableWidgetItem(eval_data['statut'])
            statut_item.setTextAlignment(Qt.AlignCenter)

            if eval_data['statut'] == "En retard":
                statut_item.setBackground(QColor("#fecaca"))
                statut_item.setForeground(QColor("#dc2626"))
                statut_item.setText("⚠️ En retard")
            elif eval_data['statut'] == "À planifier":
                statut_item.setBackground(QColor("#fed7aa"))
                statut_item.setForeground(QColor("#ea580c"))
                statut_item.setText("📅 À planifier")
            elif eval_data['statut'] == "À jour":
                statut_item.setBackground(QColor("#d1fae5"))
                statut_item.setForeground(QColor("#059669"))
                statut_item.setText("✅ À jour")
            else:
                statut_item.setBackground(QColor("#e5e7eb"))
                statut_item.setForeground(QColor("#6b7280"))

            self.table.setItem(row_pos, 7, statut_item)

        self.table.setSortingEnabled(True)

    def update_statistics(self, evaluations):
        """Met à jour les statistiques affichées."""
        total = len(evaluations)
        en_retard = sum(1 for e in evaluations if e['statut'] == "En retard")
        a_planifier = sum(1 for e in evaluations if e['statut'] == "À planifier")
        a_jour = sum(1 for e in evaluations if e['statut'] == "À jour")

        self.total_label.setText(f"Total : {total}")
        self.retard_label.setText(f"En retard : {en_retard}")
        self.a_planifier_label.setText(f"À planifier : {a_planifier}")
        self.a_jour_label.setText(f"À jour : {a_jour}")

    def toggle_edit_mode(self, checked):
        """Active/désactive le mode édition des dates."""
        if checked:
            self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
            self._date_delegate = DateDelegate(self.table, self.update_date_in_db)
            self.table.setItemDelegateForColumn(5, self._date_delegate)
            self.table.setItemDelegateForColumn(6, self._date_delegate)
            self.edit_btn.setText("✅ Terminer la modification")
            self.is_edit_mode = True
            QMessageBox.information(self, "Mode édition activé",
                                    "Double-cliquez sur une date pour la modifier.")
        else:
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setItemDelegateForColumn(5, None)
            self.table.setItemDelegateForColumn(6, None)
            self._date_delegate = None
            self.edit_btn.setText("✏️ Modifier les dates")
            self.is_edit_mode = False

    def update_date_in_db(self, row, col, qdate):
        """Met à jour une date dans la base de données."""
        poly_id_item = self.table.item(row, 0)
        if not poly_id_item:
            return

        try:
            poly_id = int(poly_id_item.text())
        except ValueError:
            return

        if col == 5:
            field = "date_evaluation"
        elif col == 6:
            field = "prochaine_evaluation"
        else:
            return

        date_iso = qdate.toString("yyyy-MM-dd")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f"UPDATE polyvalence SET {field} = %s WHERE id = %s", (date_iso, poly_id))
            conn.commit()
            cursor.close()
            conn.close()

            QMessageBox.information(self, "Succès", "Date mise à jour avec succès.")

            # Recharger les données
            self.load_data()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de mettre à jour la date :\n{e}")

    def export_to_pdf(self):
        """Exporte les données affichées en PDF."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter en PDF", "evaluations.pdf", "PDF Files (*.pdf)", options=options
        )
        if not file_path:
            return

        try:
            pdf = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []

            styles = getSampleStyleSheet()
            title_style = styles["Title"]
            normal_style = styles["Normal"]

            # Titre
            elements.append(Paragraph("Rapport des Évaluations", title_style))
            elements.append(Paragraph(" ", normal_style))

            # Données du tableau (colonnes 1-7, sans la colonne cachée 0)
            table_data = []
            headers = ["Nom", "Prénom", "Poste", "Niveau", "Date Éval.", "Prochaine Éval.", "Statut"]
            table_data.append(headers)

            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(1, 8):  # Colonnes 1 à 7
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                table_data.append(row_data)

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            elements.append(table)
            pdf.build(elements)

            QMessageBox.information(self, "Export réussi", f"Le fichier PDF a été créé :\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'exporter en PDF :\n{e}")
