# -*- coding: utf-8 -*-
"""
Grille de polyvalence — dialogue principal.
Orchestre GrillesViewModel, GrillesFilterDialog et les services d'export.
"""

import sys
from typing import List, Set, Tuple

from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QInputDialog,
    QFileDialog, QAbstractItemView, QWidget, QToolButton, QMenu, QAction,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from domain.services.formation.grilles_service import GrillesService
from infrastructure.logging.logging_config import get_logger
from gui.components.ui_theme import EmacButton, get_current_theme
from gui.components.emac_ui_kit import add_custom_title_bar, show_error_message
from gui.view_models.grilles_view_model import GrillesViewModel
from .grilles_filter_dialog import GrillesFilterDialog
from .besoin_poste_dialog import BesoinPosteDialog

logger = get_logger(__name__)

THEME_AVAILABLE = True


class GrillesDialog(QDialog):

    SUMMARY_ROWS = [
        "Niveau 1",
        "Niveau 2",
        "Niveau 3",
        "Niveau 4",
        "Nb total d'opérateurs au poste",
        "Total des niveaux 3 et 4",
        "Besoins par poste",
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grilles de Polyvalence")
        self.setGeometry(100, 80, 1400, 800)

        self.is_editable = False
        self.modified_cells: Set[Tuple[int, int]] = set()

        self._setup_theme_colors()

        self._vm = GrillesViewModel(self)
        self._vm.grille_loaded.connect(self._on_grille_loaded)
        self._vm.cell_saved.connect(self._on_cell_saved)
        self._vm.error.connect(self._on_vm_error)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = add_custom_title_bar(self, "Grilles de Polyvalence")
        main_layout.addWidget(title_bar)

        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(8)

        header_label = QLabel("Grilles de Polyvalence")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(header_label)

        self._add_toolbar()

        self.main_table = QTableWidget()
        self.main_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.main_table.cellChanged.connect(self._on_cell_changed)
        self._style_table()
        self.layout.addWidget(self.main_table, 1)

        self.main_table.setSortingEnabled(False)
        self.sort_column = None
        self.sort_order = Qt.AscendingOrder

        self._add_level_info()

        main_layout.addWidget(content_widget)

        self.operateurs: List[Tuple[int, str]] = []
        self.postes: List[Tuple[int, str]] = []

        self.load_data()

    # ------------------------------------------------------------------ #
    # Couleurs thème                                                       #
    # ------------------------------------------------------------------ #

    def _setup_theme_colors(self):
        ThemeCls = get_current_theme()
        self.color_synthesis_bg = QColor(ThemeCls.BG_CARD)
        self.color_synthesis_text = QColor(ThemeCls.TXT)
        self.color_besoins_bg = QColor(ThemeCls.BG_ELEV)
        self.color_besoins_text = QColor(ThemeCls.TXT)

    # ------------------------------------------------------------------ #
    # Chargement                                                           #
    # ------------------------------------------------------------------ #

    def load_data(self):
        """Lance le chargement via le ViewModel."""
        self._vm.load_grille()

    def _on_grille_loaded(self, postes, operateurs, niveaux, besoins):
        """Remplit le tableau depuis les données du ViewModel."""
        self.postes = postes
        self.operateurs = operateurs

        n_ops = len(operateurs)
        n_rows = n_ops + len(self.SUMMARY_ROWS)

        self.main_table.blockSignals(True)
        self.main_table.setRowCount(n_rows)
        self.main_table.setColumnCount(len(postes))

        self.main_table.setHorizontalHeaderLabels([p[1] for p in postes])
        self.main_table.setVerticalHeaderLabels(
            [op[1] for op in operateurs] + list(self.SUMMARY_ROWS)
        )

        # Remplissage cellules opérateurs
        for row_idx, (op_id, _) in enumerate(operateurs):
            for col_idx, (poste_id, _) in enumerate(postes):
                niveau = niveaux.get((op_id, poste_id), '')
                item = QTableWidgetItem(str(niveau) if niveau != '' else '')
                item.setTextAlignment(Qt.AlignCenter)
                self.main_table.setItem(row_idx, col_idx, item)

        # Lignes de synthèse non éditables (sauf "Besoins")
        start_row = n_ops
        for r in range(start_row, start_row + len(self.SUMMARY_ROWS) - 1):
            for c in range(len(postes)):
                it = self.main_table.item(r, c) or QTableWidgetItem("")
                self.main_table.setItem(r, c, it)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                it.setBackground(self.color_synthesis_bg)
                it.setForeground(self.color_synthesis_text)

        # Ligne "Besoins" éditable
        besoins_row = start_row + len(self.SUMMARY_ROWS) - 1
        for c, (poste_id, _) in enumerate(postes):
            it = self.main_table.item(besoins_row, c) or QTableWidgetItem("")
            self.main_table.setItem(besoins_row, c, it)
            it.setFlags(it.flags() | Qt.ItemIsEditable)
            it.setBackground(self.color_besoins_bg)
            it.setForeground(self.color_besoins_text)
            it.setTextAlignment(Qt.AlignCenter)
            val = besoins.get(poste_id, "")
            it.setText("" if val in (None, "") else str(val))

        self.main_table.blockSignals(False)
        self._update_statistics()

    # ------------------------------------------------------------------ #
    # Édition cellule                                                      #
    # ------------------------------------------------------------------ #

    def _on_cell_changed(self, row: int, column: int):
        if not self.is_editable:
            return
        item = self.main_table.item(row, column)
        if not item:
            return

        try:
            self.main_table.cellChanged.disconnect(self._on_cell_changed)
        except Exception:
            pass

        try:
            n_ops = len(self.operateurs)
            if row >= n_ops:
                return

            value = item.text().strip()
            if value and not value.isdigit():
                QMessageBox.warning(self, "Erreur", "Veuillez entrer un nombre valide")
                return

            op_id, op_nom = self.operateurs[row]
            poste_id, poste_code = self.postes[column]

            self._vm.save_cell(row, column, op_id, poste_id, value, op_nom, poste_code)

        finally:
            try:
                self.main_table.cellChanged.connect(self._on_cell_changed)
            except Exception:
                pass

    def _on_cell_saved(self, row, col, action, old_niveau, new_niveau):
        msgs = {
            'DELETE': lambda: f"Compétence supprimée\n\n{self.operateurs[row][1]} - {self.postes[col][1]}",
            'INSERT': lambda: f"Nouvelle compétence ajoutée\n\n{self.operateurs[row][1]} - {self.postes[col][1]}\nNiveau : {new_niveau}",
            'UPDATE': lambda: f"Compétence modifiée\n\n{self.operateurs[row][1]} - {self.postes[col][1]}\n{old_niveau} → {new_niveau}",
        }
        if action in msgs:
            QMessageBox.information(self, action.capitalize(), msgs[action]())

    def _on_vm_error(self, message: str):
        show_error_message(self, "Erreur", "Une erreur est survenue", Exception(message))

    def _reload_cell(self, row: int, column: int):
        op_id = self.operateurs[row][0]
        poste_id = self.postes[column][0]
        niveau = self._vm.get_cell_niveau(op_id, poste_id)
        self.main_table.blockSignals(True)
        self.main_table.setItem(
            row, column,
            QTableWidgetItem(str(niveau) if niveau is not None else "")
        )
        self.main_table.blockSignals(False)

    # ------------------------------------------------------------------ #
    # Statistiques                                                         #
    # ------------------------------------------------------------------ #

    def _update_statistics(self):
        n_ops = len(self.operateurs)
        n_cols = self.main_table.columnCount()
        cell_values = {}
        for r in range(n_ops):
            for c in range(n_cols):
                it = self.main_table.item(r, c)
                cell_values[(r, c)] = it.text() if it else ""

        stats = self._vm.compute_statistics(cell_values, n_ops, n_cols)

        self.main_table.blockSignals(True)
        for col, s in stats.items():
            row_base = n_ops
            for offset, key in enumerate(['n1', 'n2', 'n3', 'n4', 'total', 'total_34']):
                r = row_base + offset
                it = self.main_table.item(r, col) or QTableWidgetItem("")
                self.main_table.setItem(r, col, it)
                val = s[key]
                it.setText("" if (val is None or val == 0) else str(val))
                it.setTextAlignment(Qt.AlignCenter)
        self.main_table.blockSignals(False)

    # ------------------------------------------------------------------ #
    # Mode édition                                                         #
    # ------------------------------------------------------------------ #

    def toggle_edit_mode(self):
        self.is_editable = not self.is_editable

        if self.is_editable:
            self.main_table.setEditTriggers(
                QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
            )
            if hasattr(self, 'edit_mode_button'):
                self.edit_mode_button.setText("Mode Édition (Actif)")
            QMessageBox.information(
                self, "Mode Édition",
                "Mode édition activé\n\nLes modifications seront sauvegardées "
                "automatiquement\nlorsque vous désactiverez le mode édition."
            )
        else:
            if hasattr(self, 'edit_mode_button'):
                self.edit_mode_button.setText("Mode Édition")
            if self.modified_cells:
                self._save_changes()
            else:
                self.main_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                QMessageBox.information(
                    self, "Mode Édition",
                    "Mode édition désactivé.\n\nAucune modification à sauvegarder."
                )

    def _save_changes(self):
        modifications = []
        for row, col in self.modified_cells:
            if row >= len(self.operateurs) or col >= len(self.postes):
                continue
            op_id, op_nom = self.operateurs[row]
            poste_id, poste_code = self.postes[col]
            item = self.main_table.item(row, col)
            new_niveau = item.text().strip() if item else ""
            if new_niveau and not new_niveau.isdigit():
                QMessageBox.critical(
                    self, "Erreur",
                    f"Valeur incorrecte : '{new_niveau}' dans la cellule ({row + 1}, {col + 1})."
                )
                continue
            modifications.append((op_id, poste_id, new_niveau, op_nom, poste_code))

        count = self._vm.save_batch(modifications)
        self.modified_cells.clear()
        QMessageBox.information(self, "Succès", f"{count} modification(s) enregistrée(s) !")
        self.main_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    # ------------------------------------------------------------------ #
    # Filtrage                                                             #
    # ------------------------------------------------------------------ #

    def show_filter_dialog(self):
        hidden_rows = {r for r in range(len(self.operateurs)) if self.main_table.isRowHidden(r)}
        hidden_cols = {c for c in range(len(self.postes)) if self.main_table.isColumnHidden(c)}

        dlg = GrillesFilterDialog(
            self.operateurs, self.postes, hidden_rows, hidden_cols, parent=self
        )
        if dlg.exec_() != QDialog.Accepted:
            return

        selected_op_rows = dlg.get_selected_op_rows()
        selected_poste_cols = dlg.get_selected_poste_cols()
        n_ops = len(self.operateurs)

        # Opérateurs
        if not selected_op_rows and selected_poste_cols:
            # Montrer seulement les opérateurs ayant une compétence dans les postes sélectionnés
            ops_with_skills = set()
            for col_idx in selected_poste_cols:
                for row_idx in range(n_ops):
                    it = self.main_table.item(row_idx, col_idx)
                    if it and it.text().strip().isdigit():
                        ops_with_skills.add(row_idx)
            for r in range(n_ops):
                self.main_table.setRowHidden(r, r not in ops_with_skills)
        else:
            for r in range(n_ops):
                self.main_table.setRowHidden(r, r not in selected_op_rows)

        # Postes
        if selected_poste_cols:
            for c in range(len(self.postes)):
                self.main_table.setColumnHidden(c, c not in selected_poste_cols)
        elif selected_op_rows:
            postes_with_skills = set()
            for row_idx in selected_op_rows:
                for c in range(len(self.postes)):
                    it = self.main_table.item(row_idx, c)
                    if it and it.text().strip().isdigit():
                        postes_with_skills.add(c)
            for c in range(len(self.postes)):
                self.main_table.setColumnHidden(c, c not in postes_with_skills)
        else:
            for c in range(len(self.postes)):
                self.main_table.setColumnHidden(c, False)

        self._update_statistics()

    def reset_filters(self):
        for r in range(self.main_table.rowCount()):
            self.main_table.setRowHidden(r, False)
        for c in range(self.main_table.columnCount()):
            self.main_table.setColumnHidden(c, False)
        self._update_statistics()

    # ------------------------------------------------------------------ #
    # Ajout / Suppression / Duplication                                   #
    # ------------------------------------------------------------------ #

    def add_data(self):
        choice, ok = QInputDialog.getItem(
            self, "Ajouter", "Que voulez-vous ajouter ?", ["Colonne", "Ligne"], 0, False
        )
        if not ok:
            return
        if choice == "Colonne":
            col_name, ok2 = QInputDialog.getText(self, "Nom de Colonne", "Nom pour la nouvelle colonne :")
            if ok2 and col_name:
                dlg = BesoinPosteDialog(parent=self, titre_poste=col_name)
                if dlg.exec_() != dlg.Accepted:
                    QMessageBox.information(self, "Création annulée", "Le poste n'a pas été créé.")
                    return
                success, msg = GrillesService.ajouter_poste(col_name, dlg.get_besoin_int_or_none())
                if success:
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Attention", msg)
        elif choice == "Ligne":
            row_name, ok2 = QInputDialog.getText(self, "Nom de Ligne", "Nom de l'opérateur :")
            if ok2 and row_name:
                prenom, ok3 = QInputDialog.getText(self, "Prénom", "Prénom de l'opérateur :")
                if ok3:
                    success, msg, _ = GrillesService.ajouter_operateur(row_name, prenom)
                    if success:
                        self.load_data()

    def remove_data(self):
        choice, ok = QInputDialog.getItem(
            self, "Supprimer", "Que voulez-vous supprimer ?", ["Colonne", "Ligne"], 0, False
        )
        if not ok:
            return
        if choice == "Colonne":
            col_name, ok2 = QInputDialog.getText(self, "Nom de la Colonne", "Nom du poste à masquer :")
            if ok2 and col_name:
                success, msg = GrillesService.masquer_poste(col_name)
                if success:
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Erreur", msg)
        elif choice == "Ligne":
            operateurs = GrillesService.get_operateurs_actifs()
            if not operateurs:
                QMessageBox.information(self, "Information", "Aucun opérateur actif à masquer.")
                return
            op_map = {f"{op['nom']} {op['prenom']}": op['id'] for op in operateurs}
            selected, ok2 = QInputDialog.getItem(
                self, "Masquer un opérateur", "Sélectionnez l'opérateur :",
                list(op_map.keys()), 0, False
            )
            if ok2 and selected:
                success, msg = GrillesService.masquer_operateur(op_map[selected])
                if success:
                    QMessageBox.information(self, "Succès", f"L'opérateur {selected} a été masqué.")
                    self.load_data()

    def duplicate_data(self):
        choice, ok = QInputDialog.getItem(
            self, "Dupliquer", "Que voulez-vous dupliquer ?", ["Colonne", "Ligne"], 0, False
        )
        if not ok:
            return
        if choice == "Colonne":
            col_name, ok2 = QInputDialog.getText(self, "Nom de la Colonne", "Nom du poste à dupliquer :")
            if ok2 and col_name:
                success, msg = GrillesService.dupliquer_poste(col_name)
                if success:
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Erreur", msg)
        elif choice == "Ligne":
            row_name, ok2 = QInputDialog.getText(self, "Nom de la Ligne", "Nom complet de l'opérateur :")
            if ok2 and row_name:
                success, msg = GrillesService.dupliquer_operateur(row_name)
                if success:
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Erreur", msg)

    # ------------------------------------------------------------------ #
    # Reload & Tri                                                         #
    # ------------------------------------------------------------------ #

    def reload_data(self):
        self.reset_filters()
        self.load_data()
        self._sort_columns_az()
        self._apply_sort_state()

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
            key=lambda i: (self.main_table.horizontalHeaderItem(i).text()
                           if self.main_table.horizontalHeaderItem(i) else "")
        )
        for new_pos, logical_index in enumerate(target):
            current_visual = header.visualIndex(logical_index)
            if current_visual != new_pos:
                header.moveSection(current_visual, new_pos)

    # ------------------------------------------------------------------ #
    # Export                                                               #
    # ------------------------------------------------------------------ #

    def _export_direct(self, format_type: str, current: bool):
        """Export direct sans dialog intermédiaire."""
        import datetime as _dt
        suffix = "vue_actuelle" if current else "complet"
        default_name = f"grille_polyvalence_{suffix}_{_dt.date.today():%Y%m%d}.{format_type}"
        file_filter = "Excel Files (*.xlsx)" if format_type == "xlsx" else "PDF Files (*.pdf)"
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer l'export", default_name, file_filter
        )
        if not file_name:
            return

        headers, row_labels, data = self._collect_export_data(export_current=current)
        if not data:
            QMessageBox.warning(self, "Exportation annulée", "Aucune donnée visible à exporter.")
            return

        fmt_label = "Excel" if format_type == "xlsx" else "PDF"
        try:
            if format_type == "xlsx":
                from domain.services.formation.grilles_export_excel import export_grille_excel
                export_grille_excel(file_name, headers, row_labels, data)
            else:
                from domain.services.formation.grilles_export_pdf import export_grille_pdf
                synthesis_start = sum(
                    1 for r in range(self.main_table.rowCount())
                    if not (current and self.main_table.isRowHidden(r))
                    and r < len(self.operateurs)
                )
                export_grille_pdf(file_name, headers, row_labels, data, synthesis_start)
            QMessageBox.information(self, "Exportation réussie", f"Fichier généré : {file_name}")
        except Exception as e:
            logger.exception(f"Erreur export {fmt_label}: {e}")
            show_error_message(self, "Erreur", f"Erreur lors de l'export {fmt_label}", e)

    def _collect_export_data(self, export_current: bool):
        """Collecte headers, row_labels et data depuis le tableau, en respectant la visibilité."""
        headers = []
        for col in range(self.main_table.columnCount()):
            if export_current and self.main_table.isColumnHidden(col):
                continue
            hi = self.main_table.horizontalHeaderItem(col)
            headers.append(hi.text() if hi else "")

        row_labels = []
        data = []
        for row in range(self.main_table.rowCount()):
            if export_current and self.main_table.isRowHidden(row):
                continue
            vh = self.main_table.verticalHeaderItem(row)
            row_labels.append(vh.text() if vh else "")
            row_data = []
            for col in range(self.main_table.columnCount()):
                if export_current and self.main_table.isColumnHidden(col):
                    continue
                it = self.main_table.item(row, col)
                row_data.append(it.text() if it else "")
            data.append(row_data)

        return headers, row_labels, data

    # ------------------------------------------------------------------ #
    # Construction UI                                                      #
    # ------------------------------------------------------------------ #

    def _add_toolbar(self):
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        btn_add = EmacButton("+ Ajouter", variant='primary')
        btn_add.setToolTip("Ajouter une colonne (poste) ou une ligne (opérateur)")
        btn_add.clicked.connect(self.add_data)
        toolbar.addWidget(btn_add)

        btn_remove = EmacButton("− Masquer", variant='ghost')
        btn_remove.setToolTip("Masquer une colonne ou une ligne")
        btn_remove.clicked.connect(self.remove_data)
        toolbar.addWidget(btn_remove)

        self.edit_mode_button = EmacButton("Mode Édition", variant='ghost')
        self.edit_mode_button.setToolTip("Activer/Désactiver le mode édition")
        self.edit_mode_button.clicked.connect(self.toggle_edit_mode)
        toolbar.addWidget(self.edit_mode_button)

        btn_dup = EmacButton("Dupliquer", variant='ghost')
        btn_dup.setToolTip("Dupliquer une colonne ou une ligne")
        btn_dup.clicked.connect(self.duplicate_data)
        toolbar.addWidget(btn_dup)

        sep = QLabel("|")
        sep.setStyleSheet("color: #d1d5db; font-size: 18px; padding: 0 8px;")
        toolbar.addWidget(sep)

        btn_filter = EmacButton("Filtrer", variant='ghost')
        btn_filter.setToolTip("Sélectionner les opérateurs et/ou postes à afficher")
        btn_filter.clicked.connect(self.show_filter_dialog)
        toolbar.addWidget(btn_filter)

        btn_reset = EmacButton("↻ Réinitialiser", variant='ghost')
        btn_reset.setToolTip("Réinitialiser les filtres")
        btn_reset.clicked.connect(self.reset_filters)
        toolbar.addWidget(btn_reset)

        toolbar.addStretch()

        self.export_btn = QToolButton()
        self.export_btn.setText("Exporter \u25bc")
        self.export_btn.setPopupMode(QToolButton.InstantPopup)
        export_menu = QMenu(self)
        act_xlsx_current = QAction("Excel \u2014 vue actuelle (filtres appliqu\u00e9s)", self)
        act_xlsx_current.triggered.connect(lambda: self._export_direct("xlsx", current=True))
        export_menu.addAction(act_xlsx_current)
        act_xlsx_full = QAction("Excel \u2014 grille compl\u00e8te", self)
        act_xlsx_full.triggered.connect(lambda: self._export_direct("xlsx", current=False))
        export_menu.addAction(act_xlsx_full)
        export_menu.addSeparator()
        act_pdf_current = QAction("PDF \u2014 vue actuelle (filtres appliqu\u00e9s)", self)
        act_pdf_current.triggered.connect(lambda: self._export_direct("pdf", current=True))
        export_menu.addAction(act_pdf_current)
        act_pdf_full = QAction("PDF \u2014 grille compl\u00e8te", self)
        act_pdf_full.triggered.connect(lambda: self._export_direct("pdf", current=False))
        export_menu.addAction(act_pdf_full)
        self.export_btn.setMenu(export_menu)
        toolbar.addWidget(self.export_btn)

        self.layout.addLayout(toolbar)

    def _add_level_info(self):
        info = QHBoxLayout()
        info.setSpacing(12)
        info.addWidget(QLabel("<b>Niveaux :</b>"))
        for desc, color in [
            ("<b>N1</b> : &lt;80% (nouveau/absent 12 mois)", "#dc2626"),
            ("<b>N2</b> : ≥80% (formé, autonome)", "#d97706"),
            ("<b>N3</b> : &gt;90% (formateur)", "#059669"),
            ("<b>N4</b> : &gt;90% (leader/polyvalent ≥3 postes)", "#0369a1"),
        ]:
            lbl = QLabel(desc)
            lbl.setStyleSheet(f"color: {color}; font-size: 11px;")
            info.addWidget(lbl)
        info.addStretch()
        self.layout.addLayout(info)

    def _style_table(self):
        ThemeCls = get_current_theme()
        self.main_table.setStyleSheet(f"""
            QTableWidget {{
                background: {ThemeCls.BG_TABLE};
                border: 1px solid {ThemeCls.BDR};
                border-radius: 10px;
                gridline-color: {ThemeCls.BDR};
            }}
            QTableWidget::item {{
                padding: 6px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background: {ThemeCls.PRI};
                color: white;
            }}
            QHeaderView::section {{
                background: {ThemeCls.BG_ELEV};
                color: {ThemeCls.TXT};
                padding: 8px;
                border: 1px solid {ThemeCls.BDR};
                font-weight: 600;
                font-size: 13px;
            }}
            QHeaderView::section:hover {{
                background: {ThemeCls.BDR};
            }}
        """)
        self.main_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.main_table.verticalHeader().setDefaultSectionSize(32)
        self.main_table.horizontalHeader().setDefaultSectionSize(70)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = GrillesDialog()
    dialog.show()
    sys.exit(app.exec_())
