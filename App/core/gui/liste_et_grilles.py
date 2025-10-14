from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QMessageBox, QInputDialog, QDialogButtonBox, QListWidget, QListWidgetItem,
    QLineEdit, QFileDialog, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import sys
import pandas as pd
from datetime import datetime, timedelta

from core.db.configbd import get_connection as get_db_connection
from .besoin_poste_dialog import BesoinPosteDialog
from core.services.logger import log_hist

# 💥 IMPORT DU THÈME pour adaptation dynamique
try:
    from core.gui.ui_theme import get_current_theme
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False


def _cursor(conn):
    """Retourne (cursor, dict_mode). dict_mode=True si le curseur supporte dictionary=True."""
    try:
        cur = conn.cursor(dictionary=True)  
        return cur, True
    except TypeError:
        cur = conn.cursor()                
        return cur, False

def _rows(cur, dict_mode):
    """Retourne une liste de dicts quelle que soit la lib DB."""
    if dict_mode:
        return cur.fetchall()
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


class GrillesDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grilles Polyvalence")
        self.setGeometry(200, 200, 1000, 600)

        self.layout = QVBoxLayout()
        self.is_editable = False
        self.modified_cells = set()

        self._setup_theme_colors()

        # Boutons de modification au-dessus
        self.add_edit_buttons()

        # Table principale
        self.main_table = QTableWidget()
        self.main_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.main_table.cellChanged.connect(self.on_cell_changed)
        self.layout.addWidget(self.main_table)

        # Tri
        self.main_table.setSortingEnabled(True)
        self.sort_column = None
        self.sort_order = Qt.AscendingOrder
        header = self.main_table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.sortIndicatorChanged.connect(self._remember_sort_state)

        # Boutons principaux
        self.add_buttons()

        # Infos niveaux
        self.add_level_info()

        self.setLayout(self.layout)

        # Données
        self.operateurs = []
        self.postes = []
        self.load_data()

    def _setup_theme_colors(self):
        """Définit les couleurs adaptées au thème actuel (clair ou sombre)."""
        if THEME_AVAILABLE:
            ThemeCls = get_current_theme()
            # Couleurs pour lignes de synthèse (non éditables)
            self.color_synthesis_bg = QColor(ThemeCls.BG_CARD)
            self.color_synthesis_text = QColor(ThemeCls.TXT)
            # Couleurs pour ligne "Besoins par poste" (éditable)
            self.color_besoins_bg = QColor(ThemeCls.BG_ELEV)
            self.color_besoins_text = QColor(ThemeCls.TXT)
        else:
            # Fallback si thème non disponible (mode clair par défaut)
            self.color_synthesis_bg = QColor(211, 211, 211)  # lightGray
            self.color_synthesis_text = QColor(17, 24, 39)   # texte sombre
            self.color_besoins_bg = QColor(255, 255, 255)    # white
            self.color_besoins_text = QColor(17, 24, 39)

    # ----------------- UI haut -----------------
    def add_edit_buttons(self):
        edit_button_layout = QHBoxLayout()

        add_button = QPushButton("+")
        add_button.setToolTip("Ajouter une colonne ou une ligne")
        add_button.clicked.connect(self.add_data)
        edit_button_layout.addWidget(add_button)

        remove_button = QPushButton("-")
        remove_button.setToolTip("Supprimer une colonne ou une ligne")
        remove_button.clicked.connect(self.remove_data)
        edit_button_layout.addWidget(remove_button)

        edit_button = QPushButton("✏️")
        edit_button.setToolTip("Activer/Désactiver le mode édition")
        edit_button.clicked.connect(self.toggle_edit_mode)
        edit_button_layout.addWidget(edit_button)

        duplicate_button = QPushButton("📄")
        duplicate_button.setToolTip("Dupliquer une colonne ou une ligne")
        duplicate_button.clicked.connect(self.duplicate_data)
        edit_button_layout.addWidget(duplicate_button)

        self.layout.addLayout(edit_button_layout)

    def add_buttons(self):
        button_layout = QHBoxLayout()

        export_button = QPushButton("Exporter")
        export_button.clicked.connect(self.export_data)
        button_layout.addWidget(export_button)

        refresh_button = QPushButton("Recharger les Données")
        refresh_button.clicked.connect(self.reload_data)
        button_layout.addWidget(refresh_button)

        filter_button = QPushButton("Filtrer les Données")
        filter_button.clicked.connect(self.filter_data)
        button_layout.addWidget(filter_button)

        self.layout.addLayout(button_layout)

    def add_level_info(self):
        level_info = QLabel(
            """
            <b>Niveaux :</b><br>
            - <b>Niveau 1</b>: Opérateur nouveau à encadrer par titulaire N3/4 ou absent du poste depuis plus de 12 mois. (<b>&lt; 80%</b>)<br>
            - <b>Niveau 2</b>: Opérateur formé et apte à conduire le poste seul. Certaines notions sont en cours d'acquisition. (<b>&gt; 80%</b>)<br>
            - <b>Niveau 3</b>: Opérateur titulaire, formé, apte à conduire le poste et apte à former. (<b>&gt; 90%</b>)<br>
            - <b>Niveau 4</b>: N3 + Leader ou Polyvalent (maîtrise 3 postes d'une ligne : mél. interne, cylindres, conditionnement) (<b>&gt; 90%</b>)<br>
            """
        )
        level_info.setStyleSheet("font-size: 12px; margin-top: 10px;")
        self.layout.addWidget(level_info)

    # ----------------- Filtres -----------------
    def show_multiselect_dialog(self, title, items):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout()
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        for item in items:
            list_item = QListWidgetItem(item)
            list_widget.addItem(list_item)

        layout.addWidget(list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            return [item.text() for item in list_widget.selectedItems()]
        return []

    def filter_data(self):
        try:
            mode, ok = QInputDialog.getItem(
                self, "Mode de Filtrage",
                "Choisissez le mode de filtrage :",
                ["Par Opérateur", "Par Poste"], 0, False
            )
            if not ok or not mode:
                return

            # Sauvegarder toutes les données visibles avant le filtrage
            saved_data = {}
            for row in range(self.main_table.rowCount()):
                for col in range(self.main_table.columnCount()):
                    item = self.main_table.item(row, col)
                    if item:
                        saved_data[(row, col)] = item.text()

            if mode == "Par Opérateur":
                noms = [self.main_table.verticalHeaderItem(row).text()
                        for row in range(self.main_table.rowCount())]
                selected_noms = self.show_multiselect_dialog("Filtrer les Opérateurs", noms)

                # Masquer toutes les lignes puis réafficher les sélectionnées
                for row in range(self.main_table.rowCount()):
                    nom = self.main_table.verticalHeaderItem(row).text()
                    is_visible = nom in selected_noms
                    self.main_table.setRowHidden(row, not is_visible)
                    if is_visible:
                        for col in range(self.main_table.columnCount()):
                            if (row, col) in saved_data:
                                item = QTableWidgetItem(saved_data[(row, col)])
                                item.setTextAlignment(Qt.AlignCenter)
                                self.main_table.setItem(row, col, item)

                # Masquer les colonnes vides
                for col in range(self.main_table.columnCount() - 1, -1, -1):
                    has_values = False
                    for row in range(self.main_table.rowCount()):
                        if not self.main_table.isRowHidden(row):
                            item = self.main_table.item(row, col)
                            if item and item.text().strip():
                                has_values = True
                                break
                    self.main_table.setColumnHidden(col, not has_values)

            elif mode == "Par Poste":
                postes = [self.main_table.horizontalHeaderItem(col).text()
                          for col in range(self.main_table.columnCount())]
                selected_postes = self.show_multiselect_dialog("Filtrer les Postes", postes)

                # Masquer toutes les colonnes puis réafficher les sélectionnées
                for col in range(self.main_table.columnCount()):
                    poste = self.main_table.horizontalHeaderItem(col).text()
                    is_visible = poste in selected_postes
                    self.main_table.setColumnHidden(col, not is_visible)
                    if is_visible:
                        for row in range(self.main_table.rowCount()):
                            if (row, col) in saved_data:
                                item = QTableWidgetItem(saved_data[(row, col)])
                                item.setTextAlignment(Qt.AlignCenter)
                                self.main_table.setItem(row, col, item)

                # Masquer les lignes sans données
                for row in range(self.main_table.rowCount()):
                    has_values = False
                    for col in range(self.main_table.columnCount()):
                        if not self.main_table.isColumnHidden(col):
                            item = self.main_table.item(row, col)
                            if item and item.text().strip():
                                has_values = True
                                break
                    self.main_table.setRowHidden(row, not has_values)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du filtrage : {e}")

    # ----------------- Édition -----------------
    def on_cell_changed(self, row, column):
        """
        Gère les modifications de cellules :
        - ligne opérateurs -> table polyvalence
        - ligne "Besoins par poste" -> colonne postes.besoins_postes
        """
        if not self.is_editable:
            return

        item = self.main_table.item(row, column)
        if not item:
            return

        try:
            n_ops = len(self.operateurs)
            besoins_row = n_ops + 6  # index de la ligne "Besoins par poste" (7 lignes de synthèse)

            # ---------- CAS : modification sur la ligne "Besoins par poste" ----------
            if row == besoins_row:
                new_val_txt = item.text().strip()
                if new_val_txt == "":
                    new_db_val = None
                elif not new_val_txt.isdigit():
                    QMessageBox.warning(self, "Erreur", "Veuillez entrer un nombre valide.")
                    self.reload_data()  # remet proprement la valeur affichée depuis DB
                    return
                else:
                    new_db_val = int(new_val_txt)

                poste_id = self.postes[column][0]
                connection = get_db_connection()
                cur, _ = _cursor(connection)
                cur.execute("UPDATE postes SET besoins_postes = %s WHERE id = %s", (new_db_val, poste_id))
                connection.commit()
                cur.close()
                connection.close()

                # Si tu veux recalculer des stats conditionnées au besoin, garde :
                self.update_statistics()
                return

            # ---------- CAS : lignes opérateurs (polyvalence) ----------
            if row < n_ops:
                operateur_id = self.operateurs[row][0]
                poste_id = self.postes[column][0]
                value = item.text().strip()

                if value and not value.isdigit():
                    QMessageBox.warning(self, "Erreur", "Veuillez entrer un nombre valide")
                    self.reload_cell(row, column)
                    return

                conn = get_db_connection()
                cur, _ = _cursor(conn)

                if value == "":
                    cur.execute(
                        "DELETE FROM polyvalence WHERE operateur_id = %s AND poste_id = %s",
                        (operateur_id, poste_id)
                    )
                else:
                    cur.execute("""
                        REPLACE INTO polyvalence (operateur_id, poste_id, niveau)
                        VALUES (%s, %s, %s)
                    """, (operateur_id, poste_id, value))

                    # Prochaine évaluation +30 jours
                    nouvelle_date = (datetime.today() + timedelta(days=30)).strftime('%Y-%m-%d')
                    cur.execute(
                        """UPDATE polyvalence 
                           SET prochaine_evaluation = %s 
                           WHERE operateur_id = %s AND poste_id = %s""",
                        (nouvelle_date, operateur_id, poste_id)
                    )

                conn.commit()
                cur.close()
                conn.close()

                self.update_statistics()
                return

            # autres lignes de synthèse : on ignore
            return

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {e}")
            self.reload_data()

    def reload_cell(self, row, column):
        """Recharge une cellule opérateur spécifique avec sa valeur depuis la base de données."""
        try:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)

            operateur_id = self.operateurs[row][0]
            poste_id = self.postes[column][0]

            cursor.execute(
                "SELECT niveau FROM polyvalence WHERE operateur_id = %s AND poste_id = %s",
                (operateur_id, poste_id)
            )
            result = cursor.fetchone()

            self.main_table.blockSignals(True)
            if result:
                value = result["niveau"] if isinstance(result, dict) else result[0]
                self.main_table.setItem(row, column, QTableWidgetItem(str(value)))
            else:
                self.main_table.setItem(row, column, QTableWidgetItem(""))
            self.main_table.blockSignals(False)

            cursor.close()
            connection.close()

        except Exception as e:
            print(f"Erreur lors du rechargement de la cellule : {e}")

    # ----------------- Statistiques -----------------
    def update_statistics(self):
        """Remplit les 7 lignes de synthèse en bas, alignées aux colonnes des postes (sans toucher aux besoins)."""
        try:
            self.main_table.blockSignals(True)

            n_ops = len(self.operateurs)
            row_lvl1 = n_ops + 0
            row_lvl2 = n_ops + 1
            row_lvl3 = n_ops + 2
            row_lvl4 = n_ops + 3
            row_total_ops = n_ops + 4
            row_total_34  = n_ops + 5
            row_besoins   = n_ops + 6  # éditable, on NE l'écrase PAS

            for col in range(self.main_table.columnCount()):
                niveaux = []
                any_value = 0

                for row in range(n_ops):
                    item = self.main_table.item(row, col)
                    txt = item.text().strip() if item else ""
                    if txt.isdigit():
                        niveaux.append(int(txt))
                        any_value += 1

                c1 = niveaux.count(1)
                c2 = niveaux.count(2)
                c3 = niveaux.count(3)
                c4 = niveaux.count(4)
                total_34 = c3 + c4

                def _set(r, val):
                    it = self.main_table.item(r, col)
                    if not it:
                        it = QTableWidgetItem("")
                        self.main_table.setItem(r, col, it)
                    it.setText("" if (val is None or val == 0) else str(val))
                    it.setTextAlignment(Qt.AlignCenter)
                    # 💥 Application des couleurs selon le thème
                    it.setForeground(self.color_synthesis_text)

                # Option styling initial (col 0 pour coupure visuelle – conservé)
                if col == 0:
                    _set(row_lvl1, None)
                else:
                    _set(row_lvl1, c1)

                _set(row_lvl2, c2)
                _set(row_lvl3, c3)
                _set(row_lvl4, c4)
                _set(row_total_ops, any_value)
                _set(row_total_34, total_34)
                # row_besoins: ne pas modifier

            self.main_table.blockSignals(False)

        except Exception as e:
            print(f"Erreur lors de la mise à jour des statistiques : {e}")
            self.main_table.blockSignals(False)

    # ----------------- Chargement -----------------
    def load_data(self):
        """Charge opérateurs/postes + prépare 7 lignes de synthèse en bas + remplit la ligne Besoins."""
        connection = get_db_connection()
        cursor, dict_mode = _cursor(connection)

        query = """
        SELECT 
            o.id as operateur_id,
            o.nom,
            o.prenom,
            p.id as poste_id,
            p.poste_code,
            COALESCE(pv.niveau, '') AS niveau
        FROM operateurs o
        CROSS JOIN postes p
        LEFT JOIN polyvalence pv ON o.id = pv.operateur_id 
            AND p.id = pv.poste_id
        WHERE o.statut = 'ACTIF'
          AND p.visible = 1
        ORDER BY o.nom, o.prenom, p.poste_code;
        """

        try:
            cursor.execute(query)
            rows = _rows(cursor, dict_mode)

            # --- indexation opérateurs/postes ---
            self.operateurs = []
            operateurs_dict = {}
            postes_set = set()

            for row in rows:
                nom_complet = f"{row['nom']} {row['prenom']}".strip()
                if nom_complet not in operateurs_dict:
                    operateurs_dict[nom_complet] = {'id': row['operateur_id'], 'postes': {}}
                    self.operateurs.append((row['operateur_id'], nom_complet))

                if row['poste_code']:
                    postes_set.add((row['poste_id'], row['poste_code']))
                    operateurs_dict[nom_complet]['postes'][row['poste_code']] = row['niveau']

            self.postes = sorted(list(postes_set), key=lambda x: x[1])

            # --- dimensions : #ops + 7 lignes de synthèse ---
            n_ops = len(operateurs_dict)
            SUMMARY_ROWS = [
                "Niveau 1",
                "Niveau 2",
                "Niveau 3",
                "Niveau 4",
                "Nb total d'opérateurs au poste",
                "Total des niveaux 3 et 4",
                "Besoins par poste",
            ]

            self.main_table.blockSignals(True)
            self.main_table.setRowCount(n_ops + len(SUMMARY_ROWS))
            self.main_table.setColumnCount(len(self.postes))

            # En-têtes colonnes / lignes
            self.main_table.setHorizontalHeaderLabels([poste[1] for poste in self.postes])
            self.main_table.setVerticalHeaderLabels(
                sorted(operateurs_dict.keys()) + SUMMARY_ROWS
            )

            # Remplissage des cellules opérateurs
            for row_idx, (nom_complet, data) in enumerate(sorted(operateurs_dict.items())):
                for col_idx, (_, poste_code) in enumerate(self.postes):
                    niveau = data['postes'].get(poste_code, '')
                    item = QTableWidgetItem(str(niveau))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.main_table.setItem(row_idx, col_idx, item)

            # 💥 Style : 6 premières lignes de synthèse non éditables (avec couleurs thème)
            start_row = n_ops  # première ligne de synthèse
            for r in range(start_row, start_row + len(SUMMARY_ROWS) - 1):
                for c in range(self.main_table.columnCount()):
                    it = self.main_table.item(r, c)
                    if not it:
                        it = QTableWidgetItem("")
                        self.main_table.setItem(r, c, it)
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                    # 💥 Couleurs adaptées au thème
                    it.setBackground(self.color_synthesis_bg)
                    it.setForeground(self.color_synthesis_text)

            # 💥 Ligne "Besoins par poste" éditable (avec couleurs thème)
            besoins_row = start_row + len(SUMMARY_ROWS) - 1
            for c in range(self.main_table.columnCount()):
                it = self.main_table.item(besoins_row, c)
                if not it:
                    it = QTableWidgetItem("")
                    self.main_table.setItem(besoins_row, c, it)
                it.setFlags((it.flags() | Qt.ItemIsEditable))
                # 💥 Couleurs adaptées au thème pour la ligne éditable
                it.setBackground(self.color_besoins_bg)
                it.setForeground(self.color_besoins_text)
                it.setTextAlignment(Qt.AlignCenter)

            # --- Récupération et affichage des besoins_postes alignés aux colonnes ---
            try:
                cursor.execute("SELECT id, besoins_postes FROM postes WHERE visible = 1")
                besoins_rows = _rows(cursor, dict_mode)
                besoins_by_id = {r["id"]: r.get("besoins_postes", "") for r in besoins_rows}

                for col_idx, (poste_id, _code) in enumerate(self.postes):
                    val = besoins_by_id.get(poste_id, "")
                    it = self.main_table.item(besoins_row, col_idx)
                    it.setText("" if val in (None, "") else str(val))
                    # 💥 Réapplication des couleurs après setText
                    it.setForeground(self.color_besoins_text)
            except Exception as _e:
                # On n'empêche pas l'écran de se charger si les besoins ne sont pas dispos
                pass

            self.main_table.blockSignals(False)

            # Calculs
            self.update_statistics()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des données : {e}")
        finally:
            cursor.close()
            connection.close()

    # ----------------- Mode édition -----------------
    def toggle_edit_mode(self):
        self.is_editable = not self.is_editable
        if self.is_editable:
            self.main_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
            QMessageBox.information(self, "Mode Édition", "Le mode édition est activé. Cliquez à nouveau pour le désactiver.")
        else:
            self.main_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            QMessageBox.information(self, "Mode Édition", "Le mode édition est désactivé.")

    def track_changes(self, item):
        if item:
            self.modified_cells.add((item.row(), item.column()))

    def save_changes(self):
        """Enregistre les modifications (utilisé pour les niveaux opérateurs)."""
        try:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)

            for row, col in self.modified_cells:
                if row >= len(self.operateurs) or col >= len(self.postes):
                    continue

                operateur_id = self.operateurs[row][0]
                poste_id = self.postes[col][0]
                item = self.main_table.item(row, col)
                niveau = item.text() if item else None

                if niveau is None or niveau.strip() == "":
                    niveau = None
                elif not niveau.isdigit():
                    QMessageBox.critical(self, "Erreur", f"Valeur incorrecte : '{niveau}' dans la cellule ({row + 1}, {col + 1}).")
                    continue

                cursor.execute(
                    "REPLACE INTO polyvalence (operateur_id, poste_id, niveau) VALUES (%s, %s, %s)",
                    (operateur_id, poste_id, niveau if niveau is not None else None),
                )

            connection.commit()
            cursor.close()
            connection.close()
            self.modified_cells.clear()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement des modifications : {e}")

    # ----------------- Ajout / Suppression / Duplication -----------------
    def add_data(self):
        choice, ok = QInputDialog.getItem(self, "Ajouter", "Que voulez-vous ajouter ?", ["Colonne", "Ligne"], 0, False)
        if ok and choice:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            if choice == "Colonne":
                col_name, name_ok = QInputDialog.getText(self, "Nom de Colonne", "Entrez un nom pour la nouvelle colonne :")
                if name_ok and col_name:
                    # Vérifier doublon
                    cursor.execute("SELECT id FROM postes WHERE poste_code = %s", (col_name,))
                    if cursor.fetchone():
                        QMessageBox.warning(self, "Attention", f"Le poste '{col_name}' existe déjà.")
                    else:
                        # INSERT poste
                        cursor.execute("INSERT INTO postes (poste_code, visible) VALUES (%s, 1)", (col_name,))

                        # Pop-up besoin (obligatoire en création)
                        dlg = BesoinPosteDialog(parent=self, titre_poste=col_name)
                        if dlg.exec_() != dlg.Accepted:
                            connection.rollback()
                            QMessageBox.information(self, "Création annulée", "Le poste n'a pas été créé.")
                        else:
                            besoin_val = dlg.get_besoin_int_or_none()
                            cursor.execute(
                                "UPDATE postes SET besoins_postes = %s WHERE poste_code = %s",
                                (besoin_val, col_name)
                            )
                            connection.commit()
                            self.load_data()
            elif choice == "Ligne":
                row_name, name_ok = QInputDialog.getText(self, "Nom de Ligne", "Entrez le nom pour la nouvelle ligne (Nom) :")
                if name_ok and row_name:
                    prenom, ok = QInputDialog.getText(self, "Prénom", "Entrez le prénom de l'opérateur :")
                    if ok:
                        cursor.execute("INSERT INTO operateurs (nom, prenom, statut) VALUES (%s, %s, 'ACTIF')", (row_name, prenom))
                        connection.commit()
                        self.load_data()
            cursor.close()
            connection.close()

    def remove_data(self):
        choice, ok = QInputDialog.getItem(self, "Supprimer", "Que voulez-vous supprimer ?", ["Colonne", "Ligne"], 0, False)
        if ok and choice:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            if choice == "Colonne":
                col_name, name_ok = QInputDialog.getText(self, "Nom de la Colonne", "Entrez le nom du poste à masquer :")
                if name_ok and col_name:
                    cursor.execute("SELECT id FROM postes WHERE poste_code = %s AND visible = 1", (col_name,))
                    poste = cursor.fetchone()
                    if poste:
                        poste_id = poste["id"] if dict_mode else poste[0]
                        cursor.execute("UPDATE postes SET visible = 0 WHERE id = %s", (poste_id,))
                        connection.commit()
                        self.load_data()
                    else:
                        QMessageBox.critical(self, "Erreur", f"Le poste '{col_name}' n'existe pas ou est déjà masqué.")
            elif choice == "Ligne":
                row_name, name_ok = QInputDialog.getText(self, "Nom de la Ligne", "Entrez le nom complet de l'opérateur à masquer :")
                if name_ok and row_name:
                    cursor.execute("SELECT id FROM operateurs WHERE CONCAT(nom, ' ', prenom) = %s AND statut = 'ACTIF'", (row_name,))
                    operateur = cursor.fetchone()
                    if operateur:
                        operateur_id = operateur["id"] if dict_mode else operateur[0]
                        cursor.execute("UPDATE operateurs SET statut = 'INACTIF' WHERE id = %s", (operateur_id,))
                        connection.commit()
                        self.load_data()
                    else:
                        QMessageBox.critical(self, "Erreur", f"L'opérateur '{row_name}' n'existe pas ou est déjà inactif.")
            cursor.close()
            connection.close()

    def duplicate_data(self):
        choice, ok = QInputDialog.getItem(self, "Dupliquer", "Que voulez-vous dupliquer ?", ["Colonne", "Ligne"], 0, False)
        if ok and choice:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            if choice == "Colonne":
                col_name, name_ok = QInputDialog.getText(self, "Nom de la Colonne", "Entrez le nom du poste à dupliquer :")
                if name_ok and col_name:
                    cursor.execute("SELECT id, poste_code FROM postes WHERE poste_code = %s AND visible = 1", (col_name,))
                    poste = cursor.fetchone()
                    if poste:
                        poste_id = poste["id"] if dict_mode else poste[0]
                        poste_code = poste["poste_code"] if dict_mode else poste[1]

                        # Création du nouveau poste
                        try:
                            cursor.execute(
                                "INSERT INTO postes (poste_code, visible) VALUES (%s, 1) RETURNING id",
                                (f"{poste_code}_copy",)
                            )
                            new_poste_id = cursor.fetchone()[0]
                        except Exception:
                            # Fallback MySQL
                            cursor.execute(
                                "INSERT INTO postes (poste_code, visible) VALUES (%s, 1)",
                                (f"{poste_code}_copy",)
                            )
                            new_poste_id = getattr(cursor, "lastrowid", None)

                        # Copier la polyvalence
                        cursor.execute(
                            """
                            INSERT INTO polyvalence (operateur_id, poste_id, niveau)
                            SELECT operateur_id, %s, niveau FROM polyvalence WHERE poste_id = %s
                            """,
                            (new_poste_id, poste_id)
                        )
                        connection.commit()
                        self.load_data()
                    else:
                        QMessageBox.critical(self, "Erreur", f"Le poste '{col_name}' n'existe pas ou est masqué.")

            elif choice == "Ligne":
                row_name, name_ok = QInputDialog.getText(self, "Nom de la Ligne", "Entrez le nom complet de l'opérateur à dupliquer :")
                if name_ok and row_name:
                    cursor.execute("SELECT id, nom, prenom FROM operateurs WHERE CONCAT(nom, ' ', prenom) = %s AND statut = 'ACTIF'", (row_name,))
                    operateur = cursor.fetchone()
                    if operateur:
                        operateur_id = operateur["id"] if dict_mode else operateur[0]
                        nom = operateur["nom"] if dict_mode else operateur[1]
                        prenom = operateur["prenom"] if dict_mode else operateur[2]

                        # Créer le nouvel opérateur
                        try:
                            cursor.execute(
                                "INSERT INTO operateurs (nom, prenom, statut) VALUES (%s, %s, 'ACTIF') RETURNING id",
                                (f"{nom}_copy", prenom)
                            )
                            new_operateur_id = cursor.fetchone()[0]
                        except Exception:
                            # Fallback MySQL
                            cursor.execute(
                                "INSERT INTO operateurs (nom, prenom, statut) VALUES (%s, %s, 'ACTIF')",
                                (f"{nom}_copy", prenom)
                            )
                            new_operateur_id = getattr(cursor, "lastrowid", None)

                        # Copier la polyvalence
                        cursor.execute(
                            """
                            INSERT INTO polyvalence (operateur_id, poste_id, niveau)
                            SELECT %s, poste_id, niveau FROM polyvalence WHERE operateur_id = %s
                            """,
                            (new_operateur_id, operateur_id)
                        )
                        connection.commit()
                        self.load_data()
                    else:
                        QMessageBox.critical(self, "Erreur", f"L'opérateur '{row_name}' n'existe pas ou est inactif.")
            cursor.close()
            connection.close()

    # ----------------- Reload & Tri -----------------
    def reload_data(self):
        """ Remet la table dans son état initial, recharge et retrie. """
        self.reset_filters()
        self.load_data()
        self._sort_columns_az()
        self._apply_sort_state()

    def _remember_sort_state(self, column, order):
        self.sort_column = column
        self.sort_order = order

    def _apply_sort_state(self):
        if self.sort_column is not None:
            self.main_table.blockSignals(True)
            self.main_table.sortItems(self.sort_column, self.sort_order)
            self.main_table.blockSignals(False)

    def _sort_columns_az(self):
        header = self.main_table.horizontalHeader()
        col_count = self.main_table.columnCount()
        if col_count <= 1:
            return

        target = sorted(
            range(col_count),
            key=lambda i: self.main_table.horizontalHeaderItem(i).text()
                          if self.main_table.horizontalHeaderItem(i) else ""
        )
        for new_pos, logical_index in enumerate(target):
            current_visual = header.visualIndex(logical_index)
            if current_visual != new_pos:
                header.moveSection(current_visual, new_pos)

    def reset_filters(self):
        if hasattr(self, 'search_operator_input'):
            self.search_operator_input.clear()
        if hasattr(self, 'search_poste_input'):
            self.search_poste_input.clear()

        for row in range(self.main_table.rowCount()):
            self.main_table.setRowHidden(row, False)
        for col in range(self.main_table.columnCount()):
            self.main_table.setColumnHidden(col, False)

    # ----------------- Export -----------------
    def export_data(self):
        """Demande l’état (actuel / complet) puis exporte en Excel ou PDF."""
        print("Exportation démarrée - Choix de l'état")

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Exporter les données")
        msg_box.setText("Voulez-vous exporter :")
        msg_box.addButton("État Actuel (avec filtres et modifications)", QMessageBox.AcceptRole)
        msg_box.addButton("Grille Générale (toutes les données)", QMessageBox.RejectRole)
        msg_box.addButton("Annuler", QMessageBox.NoRole)

        choice = msg_box.exec_()
        if choice == 2:
            return

        export_current_state = (choice == 0)

        format_choice, ok = QInputDialog.getItem(
            self, "Choix du format", "Sélectionnez le format d'exportation :",
            ["Excel", "PDF"], 0, False
        )
        if not ok:
            return

        file_extension = {"Excel": "xlsx", "PDF": "pdf"}[format_choice]
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le fichier", "", f"{format_choice} Files (*.{file_extension})"
        )
        if not file_name:
            return

        print(f"Exportation en {format_choice} : {file_name}")

        if format_choice == "Excel":
            self.export_to_excel(file_name, export_current_state)
        elif format_choice == "PDF":
            self.export_to_pdf(file_name, export_current_state)

    def export_to_excel(self, file_name, export_current_state):
        """Exporte les données du tableau en fichier Excel + ajoute la légende 'Niveaux' pour impression."""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, Border, Side
            from openpyxl.utils import get_column_letter
            from openpyxl.utils.dataframe import dataframe_to_rows

            # Récupère l'état visible (ou complet) de la grille -> DataFrame
            data = []
            headers = []
            for col in range(self.main_table.columnCount()):
                if export_current_state and self.main_table.isColumnHidden(col):
                    continue
                headers.append(self.main_table.horizontalHeaderItem(col).text())

            for row in range(self.main_table.rowCount()):
                if export_current_state and self.main_table.isRowHidden(row):
                    continue
                row_data = [self.main_table.verticalHeaderItem(row).text()]
                for col in range(self.main_table.columnCount()):
                    if export_current_state and self.main_table.isColumnHidden(col):
                        continue
                    item = self.main_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            if not data:
                QMessageBox.warning(self, "Exportation annulée", "Aucune donnée visible à exporter.")
                return

            # ====== Création du classeur ======
            wb = Workbook()
            ws = wb.active
            ws.title = "Grille Polyvalence"

            # Écrit l’en-tête
            ws.cell(row=1, column=1, value="Nom").font = Font(bold=True)
            for c, h in enumerate(headers, start=2):
                cell = ws.cell(row=1, column=c, value=h)
                cell.font = Font(bold=True)

            # Écrit les données
            for r, row_vals in enumerate(data, start=2):
                for c, val in enumerate(row_vals, start=1):
                    ws.cell(row=r, column=c, value=val)

            # Mise en forme tableau
            thin = Border(left=Side(style="thin"), right=Side(style="thin"),
                          top=Side(style="thin"), bottom=Side(style="thin"))
            for r in range(1, len(data) + 1 + 1):
                for c in range(1, len(headers) + 1 + 1):
                    cell = ws.cell(row=r, column=c)
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                    cell.border = thin

            # Largeurs de colonnes (Nom plus large)
            ws.column_dimensions[get_column_letter(1)].width = 28
            for c in range(2, len(headers) + 2):
                ws.column_dimensions[get_column_letter(c)].width = 6

            # ====== Légende "Niveaux" sous le tableau ======
            start_legend_row = len(data) + 3  # 1 ligne vide + 1 marge
            bullet = "\u2022"  # •

            # Titre
            ws.cell(row=start_legend_row, column=1, value="Niveaux :").font = Font(bold=True)
            ws.merge_cells(start_row=start_legend_row, start_column=1,
                           end_row=start_legend_row, end_column=len(headers) + 1)

            # Lignes de légende
            legend_lines = [
                f"{bullet} Niveau 1 : Opérateur nouveau à encadrer par titulaire N3/4 ou absent du poste depuis plus de 12 mois. (< 80%)",
                f"{bullet} Niveau 2 : Opérateur formé et apte à conduire le poste seul. Certaines notions sont en cours d'acquisition. (> 80%)",
                f"{bullet} Niveau 3 : Opérateur titulaire, formé, apte à conduire le poste et apte à former. (> 90%)",
                f"{bullet} Niveau 4 : N3 + Leader ou Polyvalent (maîtrise 3 postes d'une ligne : mél. interne, cylindres, conditionnement) (> 90%)",
            ]

            for i, line in enumerate(legend_lines, start=1):
                r = start_legend_row + i
                ws.cell(row=r, column=1, value=line)
                ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=len(headers) + 1)
                c = ws.cell(row=r, column=1)
                c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

            # Ajuste automatiquement la hauteur des lignes de légende (un peu plus hautes pour l’impression)
            for r in range(start_legend_row, start_legend_row + len(legend_lines) + 1):
                ws.row_dimensions[r].height = 18

            # Zone d’impression incluant la légende
            last_row = start_legend_row + len(legend_lines)
            last_col_letter = get_column_letter(len(headers) + 1)
            ws.print_area = f"A1:{last_col_letter}{last_row}"

            # Orientation paysage conseillée pour impression (facultatif)
            ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE

            # Sauvegarde
            wb.save(file_name)
            QMessageBox.information(self, "Exportation réussie", f"Les données ont été exportées dans {file_name}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'exportation : {e}")


    def export_to_pdf(self, file_name, export_current_state):
        """Export PDF format A4 portrait avec colonnes de postes optimisées"""
        try:
            from datetime import datetime
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
    
            headers = []
            for c in range(self.main_table.columnCount()):
                if export_current_state and self.main_table.isColumnHidden(c):
                    continue
                hi = self.main_table.horizontalHeaderItem(c)
                headers.append(hi.text() if hi else "")
    
            data_rows = []
            row_headers = []
            n_ops = len(self.operateurs)
            
            for r in range(self.main_table.rowCount()):
                if export_current_state and self.main_table.isRowHidden(r):
                    continue
                vh = self.main_table.verticalHeaderItem(r)
                row_name = vh.text() if vh else ""
                row_headers.append(row_name)
                
                row = []
                for c in range(self.main_table.columnCount()):
                    if export_current_state and self.main_table.isColumnHidden(c):
                        continue
                    it = self.main_table.item(r, c)
                    row.append("" if it is None else it.text())
                data_rows.append(row)
    
            if not data_rows:
                QMessageBox.warning(self, "Exportation annulée", "Aucune donnée à exporter.")
                return
    
            synthesis_start = len(data_rows) - 7
            operator_rows = data_rows[:synthesis_start]
            operator_headers = row_headers[:synthesis_start]
            synthesis_rows = data_rows[synthesis_start:]
            synthesis_headers = row_headers[synthesis_start:]
    
            operator_rows_with_levels = operator_rows
            synthesis_rows_with_levels = synthesis_rows
    
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle("T", parent=styles["Title"],
                                         fontName="Helvetica-Bold", fontSize=14,
                                         alignment=1, spaceAfter=3*mm)
            
            th_size = 8
            td_size = 7.5
            leading = 9
            th = ParagraphStyle("TH", parent=styles["BodyText"], fontName="Helvetica-Bold",
                                fontSize=th_size, leading=leading, alignment=1)
            td_c = ParagraphStyle("TDc", parent=styles["BodyText"], fontName="Helvetica",
                                  fontSize=td_size, leading=leading, alignment=1)
            td_l = ParagraphStyle("TDl", parent=styles["BodyText"], fontName="Helvetica",
                                  fontSize=td_size, leading=leading, alignment=0)
    
            page = A4
            LM, RM, TM, BM = 8*mm, 8*mm, 15*mm, 12*mm
            usable_w = page[0] - LM - RM
    
            first_col_w = 32*mm
            n_poste_cols = len(headers)
            poste_col_w = 5*mm
            
            total_poste_w = poste_col_w * n_poste_cols
            if first_col_w + total_poste_w > usable_w:
                remaining_w = usable_w - first_col_w
                poste_col_w = max(4*mm, remaining_w / n_poste_cols)
    
            col_widths = [first_col_w] + [poste_col_w] * n_poste_cols
    
            from reportlab.platypus import Flowable
            
            class RotatedText(Flowable):
                def __init__(self, text, fontSize=8):
                    Flowable.__init__(self)
                    self.text = text
                    self.fontSize = fontSize
                    self.width = fontSize * 1.2
                    self.height = len(text) * fontSize * 0.7
                    
                def draw(self):
                    canvas = self.canv
                    canvas.saveState()
                    canvas.translate(self.width / 2, 0)
                    canvas.rotate(90)
                    canvas.setFont("Helvetica-Bold", self.fontSize)
                    canvas.drawString(2, -self.fontSize/3, self.text)
                    canvas.restoreState()
            
            header_row = [""] + [RotatedText(h, th_size) for h in headers]
            
            data = [header_row]
            for i, row in enumerate(operator_rows_with_levels):
                data.append([Paragraph(operator_headers[i], td_l)] + 
                           [Paragraph(str(v), td_c) for v in row])
    
            for i, row in enumerate(synthesis_rows_with_levels):
                data.append([Paragraph(f"<b>{synthesis_headers[i]}</b>", td_l)] + 
                           [Paragraph(str(v) if v else "", td_c) for v in row])
    
            table = Table(data, colWidths=col_widths, repeatRows=1)
            
            n_total_cols = len(headers) + 1
            n_rows = len(data)
            n_op_rows = len(operator_rows_with_levels) + 1
            
            table_style = [
                ("GRID", (0, 0), (-1, -1), 0.3, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#BFBFBF")),
                ("FONTSIZE", (0, 0), (-1, 0), th_size),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 1), (-1, n_op_rows - 1), td_size),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, n_op_rows), (-1, -1), colors.HexColor("#D0D0D0")),
                ("FONTSIZE", (0, n_op_rows), (-1, -1), th_size),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, 0), 2),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 1.5),
            ]
            
            table.setStyle(TableStyle(table_style))
    
            legend_title = Paragraph("<b>Définition</b>", styles["Heading4"])
            
            legend_header_style = ParagraphStyle("LegHeader", parent=styles["BodyText"], 
                                                fontName="Helvetica-Bold", fontSize=9, 
                                                alignment=1, leading=10)
            legend_cell_style = ParagraphStyle("LegCell", parent=styles["BodyText"], 
                                              fontName="Helvetica", fontSize=8, 
                                              alignment=0, leading=10)
            
            leg = [
                [Paragraph("Niveau", legend_header_style), 
                 Paragraph("Définition", legend_header_style), 
                 Paragraph("Valeur de la<br/>dernière<br/>évaluation", legend_header_style)],
                [Paragraph("1", legend_cell_style), 
                 Paragraph("Opérateur nouveau à encadrer par titulaire N3/4 ou absent du poste depuis plus de 12 mois", legend_cell_style), 
                 Paragraph("&lt; 80%", legend_cell_style)],
                [Paragraph("2", legend_cell_style), 
                 Paragraph("Opérateur formé et apte à conduire le poste seul. Certaines notions sont en cours d'acquisition", legend_cell_style), 
                 Paragraph("≥ 80%", legend_cell_style)],
                [Paragraph("3", legend_cell_style), 
                 Paragraph("Opérateur titulaire, formé, apte à conduire le poste et apte à former", legend_cell_style), 
                 Paragraph("&gt; 90%", legend_cell_style)],
                [Paragraph("4", legend_cell_style), 
                 Paragraph("N3 + Leader ou Polyvalent (maîtrise ≥ 3 postes d'une ligne: mél. interne, cylindres, conditionnement)", legend_cell_style), 
                 Paragraph("&gt; 90%", legend_cell_style)],
            ]
            
            legend_w = usable_w
            leg_tbl = Table(leg, colWidths=[15*mm, legend_w - 45*mm, 30*mm])
            leg_tbl.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9D9D9")),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
    
            def on_page(canvas, doc):
                canvas.saveState()
                canvas.setFont("Helvetica", 7)
                canvas.drawString(LM, page[1] - TM + 6*mm, "LQ 07 02 02 rév.1")
                canvas.drawRightString(page[0] - RM, BM - 3*mm, f"Page {doc.page}")
                canvas.restoreState()
    
            doc = SimpleDocTemplate(
                file_name, pagesize=page,
                leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                title="Grille de Polyvalence"
            )
    
            story = [
                Paragraph(f"Grille de Polyvalence au {datetime.now().strftime('%d/%m/%Y')}", title_style),
                Spacer(1, 2*mm),
                table,
                Spacer(1, 4*mm),
                legend_title,
                Spacer(1, 1*mm),
                leg_tbl
            ]
            
            doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
            QMessageBox.information(self, "Exportation réussie", f"PDF généré : {file_name}")
    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export PDF : {e}")
            import traceback
            traceback.print_exc()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = GrillesDialog()
    dialog.show()
    sys.exit(app.exec_())
