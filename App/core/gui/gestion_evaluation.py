# gestion_evaluation.py — gestion & export des évaluations
# Version adaptée pour la nouvelle arbo (imports absolus)
# - conserve : filtres opérateur/poste, DateDelegate pour l'édition des dates,
#              export PDF, colonne technique _poly_id masquée
# - change   : imports -> core.db.configbd ; suppression de mysql.connector
# - bonus    : export PDF ignore la colonne cachée (index 0) pour éviter le décalage

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QComboBox, QLabel, QFileDialog, QStyledItemDelegate, QDateEdit, QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import QDate, Qt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from core.gui.historique import HistoriqueDialog
from reportlab.lib.styles import getSampleStyleSheet

# 🔧 alias pour ne rien casser dans le code existant
from core.db.configbd import get_connection as get_db_connection


# --- Délégué pour éditer les dates dans le tableau ---
class DateDelegate(QStyledItemDelegate):
    """
    Affiche un QDateEdit pour les cellules de dates.
    Appelle un callback on_commit(row, col, qdate) pour mettre à jour la BDD.
    """
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
        self.setGeometry(100, 100, 800, 500)

        # Variables de filtre
        self.selected_operator = None
        self.selected_operator_name = "Tous les opérateurs"
        self.selected_poste = None
        self.selected_poste_code = "Tous les postes"

        # Layout principal
        layout = QVBoxLayout()

        # Bouton pour filtrer
        self.filter_button = QPushButton("Filtrer les évaluations")
        self.filter_button.clicked.connect(self.open_filter_dialog)
        layout.addWidget(self.filter_button)

        # Bouton pour exporter en PDF
        self.export_pdf_button = QPushButton("Exporter en PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        layout.addWidget(self.export_pdf_button)

        # Bouton pour rafraîchir
        self.refresh_button = QPushButton("Rafraîchir")
        self.refresh_button.clicked.connect(lambda: self.load_data())
        layout.addWidget(self.refresh_button)

        # Bouton pour activer l'édition des dates
        self.edit_dates_btn = QPushButton("Modifier les dates")
        self.edit_dates_btn.setCheckable(True)
        self.edit_dates_btn.toggled.connect(self._toggle_edit_dates)
        layout.addWidget(self.edit_dates_btn)

        # Tableau
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # lecture seule par défaut
        layout.addWidget(self.table)

        self.setLayout(layout)

        # Chargement initial
        self.load_data()

        # Ajustement automatique
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def open_filter_dialog(self):
        """Boîte de dialogue de filtre opérateur/poste."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Filtrer les évaluations")
        dialog.setGeometry(300, 300, 350, 150)

        layout = QVBoxLayout()

        # Connexion à la BDD
        conn = get_db_connection()
        cursor = conn.cursor()

        # ✅ CORRECTION 1: 'operateurs' → 'personnel'
        self.operator_combo = QComboBox()
        self.operator_combo.addItem("Tous les opérateurs", "")
        cursor.execute("SELECT nom, prenom, id FROM personnel WHERE statut = 'ACTIF' ORDER BY nom;")
        for nom, prenom, op_id in cursor.fetchall():
            self.operator_combo.addItem(f"{nom} {prenom}", op_id)
        layout.addWidget(QLabel("Sélectionner un opérateur :"))
        layout.addWidget(self.operator_combo)

        # Poste (✅ déjà correct)
        self.poste_combo = QComboBox()
        self.poste_combo.addItem("Tous les postes", "")
        cursor.execute("SELECT poste_code, id FROM postes ORDER BY poste_code;")
        for poste_code, poste_id in cursor.fetchall():
            self.poste_combo.addItem(poste_code, poste_id)
        layout.addWidget(QLabel("Sélectionner un poste :"))
        layout.addWidget(self.poste_combo)

        # Fermeture
        cursor.close()
        conn.close()

        # Valider
        validate_button = QPushButton("Appliquer le filtre")
        validate_button.clicked.connect(lambda: self.apply_filter(dialog))
        layout.addWidget(validate_button)

        dialog.setLayout(layout)
        dialog.exec()

    def apply_filter(self, dialog):
        """Applique le filtre sélectionné et stocke les critères pour l'export."""
        self.selected_operator = self.operator_combo.currentData()    # ID opérateur
        self.selected_operator_name = self.operator_combo.currentText()
        self.selected_poste = self.poste_combo.currentData()          # ID poste
        self.selected_poste_code = self.poste_combo.currentText()

        self.load_data(self.selected_operator, self.selected_poste)
        dialog.accept()

    def load_data(self, operator_id=None, poste_id=None):
        """Charge les évaluations (et garde l'ID technique pour UPDATE)."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # ✅ CORRECTION 2: 'operateurs' → 'personnel' (alias 'pers')
        query = """
        SELECT 
            poly.id,                                -- 0: ID technique (caché)
            pers.nom, pers.prenom, p.poste_code, 
            COALESCE(poly.niveau, 'N/A') AS niveau, 
            COALESCE(poly.date_evaluation, 'Non défini') AS date_evaluation, 
            COALESCE(poly.prochaine_evaluation, 'Non défini') AS prochaine_evaluation
        FROM polyvalence poly
        JOIN personnel pers ON poly.operateur_id = pers.id
        JOIN postes p ON poly.poste_id = p.id
        """

        params = []
        where_added = False
        
        # ✅ AMÉLIORATION: Utilisation des alias pour plus de cohérence
        if operator_id:
            query += " WHERE pers.id = %s"
            params.append(operator_id)
            where_added = True

        if poste_id:
            query += " AND p.id = %s" if where_added else " WHERE p.id = %s"
            params.append(poste_id)

        query += " ORDER BY pers.nom, pers.prenom, p.poste_code;"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Maj tableau
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(7)  # +1 colonne cachée pour poly.id
        self.table.setHorizontalHeaderLabels(
            ["_poly_id", "Nom", "Prénom", "Poste", "Niveau", "Date Évaluation", "Prochaine Évaluation"]
        )

        for row_idx, row_data in enumerate(rows):
            for col_idx, col_data in enumerate(row_data):
                text = col_data.strftime("%d/%m/%Y") if hasattr(col_data, "strftime") else str(col_data)
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # lecture seule par défaut
                self.table.setItem(row_idx, col_idx, item)

        self.table.setColumnHidden(0, True)  # col technique
        self.table.setSortingEnabled(True)

    # --- Édition des dates (toggle) ---
    def _toggle_edit_dates(self, checked: bool):
        if checked:
            self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
            self._date_delegate = DateDelegate(self.table, self._update_date_in_db)
            self.table.setItemDelegateForColumn(5, self._date_delegate)  # Date Évaluation
            self.table.setItemDelegateForColumn(6, self._date_delegate)  # Prochaine Évaluation
            self.edit_dates_btn.setText("Terminer la modification")
            QMessageBox.information(self, "Édition activée",
                                    "Double-clique une cellule de date pour la modifier.")
        else:
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setItemDelegateForColumn(5, None)
            self.table.setItemDelegateForColumn(6, None)
            self._date_delegate = None
            self.edit_dates_btn.setText("Modifier les dates")

    def _update_date_in_db(self, row: int, col: int, qdate: QDate):
        """Enregistre la date dans la table `polyvalence` pour la ligne sélectionnée."""
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
            cur = conn.cursor()
            # ✅ SÉCURITÉ: Utilisation de paramètres préparés (déjà correct)
            cur.execute(f"UPDATE polyvalence SET {field} = %s WHERE id = %s", (date_iso, poly_id))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            # Rétablit visuellement l'ancienne valeur et informe
            old_text = self.table.item(row, col).text()
            self.table.item(row, col).setText(old_text)
            QMessageBox.warning(self, "Erreur de mise à jour", f"Impossible d'enregistrer la date : {e}")

    # --- Export PDF ---
    def export_to_pdf(self):
        """Exporte les données affichées (hors colonne technique) en PDF."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter en PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options
        )
        if not file_path:
            return  # annulé

        pdf = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        normal_style = styles["Normal"]

        # Entête dynamique selon filtre
        header_text = "Liste complète des évaluations"
        if self.selected_operator and self.selected_poste:
            header_text = f"Évaluations de {self.selected_operator_name} - Poste {self.selected_poste_code}"
        elif self.selected_operator:
            header_text = f"Évaluations de {self.selected_operator_name}"
        elif self.selected_poste:
            header_text = f"Évaluations du Poste {self.selected_poste_code}"

        elements.append(Paragraph(header_text, title_style))
        elements.append(Paragraph(" ", normal_style))  # espace

        # Données
        table_data = []
        headers = ["Nom", "Prénom", "Poste", "Niveau", "Date Évaluation", "Prochaine Évaluation"]
        table_data.append(headers)

        # 🔍 on ignore la colonne 0 (_poly_id) pour coller aux en-têtes
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(1, self.table.columnCount()):
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