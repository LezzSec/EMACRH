# gestion_evaluation.py — Gestion moderne des évaluations
# Interface améliorée avec recherche, filtres intégrés et code couleur

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QComboBox, QLabel, QFileDialog,
    QStyledItemDelegate, QDateEdit, QAbstractItemView, QMessageBox,
    QLineEdit, QGroupBox, QWidget, QTabWidget
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from gui.view_models.evaluation_view_model import EvaluationViewModel
from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date, format_datetime

logger = get_logger(__name__)

from gui.components.ui_theme import EmacButton, EmacCard, EmacHeader, get_current_theme
from gui.components.emac_ui_kit import add_custom_title_bar, show_error_message


# --- Dialogue popup avec 2 onglets pour un opérateur ---
class DetailOperateurDialog(QDialog):
    """Dialogue détaillé pour un opérateur avec résumé et ajout d'anciennes polyvalences."""

    def __init__(self, operateur_id, operateur_nom, operateur_prenom, parent=None, vm=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.operateur_nom = operateur_nom
        self.operateur_prenom = operateur_prenom
        self._vm = vm or EvaluationViewModel(parent=self)
        self._pending_count: int = 0
        self._vm_signals_connected = False

        self.setWindowTitle(f"Détails - {operateur_prenom} {operateur_nom}")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        header_frame = QWidget()
        header_frame.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #a78bfa);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)

        title = QLabel(f"{operateur_prenom} {operateur_nom}")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title)

        layout.addWidget(header_frame)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                background: white;
            }
            QTabBar::tab {
                background: #f3f4f6;
                color: #374151;
                padding: 10px 20px;
                border: 1px solid #e5e7eb;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #8b5cf6;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #e5e7eb;
            }
        """)

        self.tab_resume = QWidget()
        self._init_tab_resume()
        self.tabs.addTab(self.tab_resume, "Résumé")

        self.tab_anciennes = QWidget()
        self._init_tab_anciennes()
        self.tabs.addTab(self.tab_anciennes, "Historique")

        layout.addWidget(self.tabs, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        self._connect_viewmodel()
        self.finished.connect(lambda _result: self._disconnect_viewmodel())
        self._load_data()

    def _connect_viewmodel(self):
        if self._vm_signals_connected:
            return
        self._vm.detail_loaded.connect(self._on_detail_loaded)
        self._vm.evaluation_count.connect(self._on_count_received)
        self._vm.action_succeeded.connect(self._on_action_succeeded)
        self._vm.error_occurred.connect(self._on_error_occurred)
        self._vm_signals_connected = True

    def _disconnect_viewmodel(self):
        if not self._vm_signals_connected:
            return
        for signal, slot in (
            (self._vm.detail_loaded, self._on_detail_loaded),
            (self._vm.evaluation_count, self._on_count_received),
            (self._vm.action_succeeded, self._on_action_succeeded),
            (self._vm.error_occurred, self._on_error_occurred),
        ):
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass
        self._vm_signals_connected = False

    def _on_count_received(self, n: int):
        self._pending_count = n

    def _on_action_succeeded(self, msg: str):
        QMessageBox.information(self, "Succès", msg)
        self._load_data()

    def _on_error_occurred(self, msg: str):
        QMessageBox.critical(self, "Erreur", msg)
        self._load_data()

    def _init_tab_resume(self):
        """Initialise l'onglet Résumé."""
        layout = QVBoxLayout(self.tab_resume)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        stats_group = QGroupBox("Statistiques")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("Chargement...")
        self.stats_label.setStyleSheet("font-size: 11pt; padding: 10px;")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        layout.addWidget(stats_group)

        poly_group = QGroupBox("Polyvalences actuelles")
        poly_layout = QVBoxLayout(poly_group)

        self.poly_table = QTableWidget()
        self.poly_table.setColumnCount(6)
        self.poly_table.setHorizontalHeaderLabels([
            "Poste", "Niveau", "Date Éval.", "Prochaine Éval.", "Statut", "_poly_id"
        ])
        self.poly_table.setColumnHidden(5, True)  # Cacher l'ID
        self.poly_table.horizontalHeader().setStretchLastSection(True)
        self.poly_table.setEditTriggers(QAbstractItemView.DoubleClicked)  # Édition au double-clic
        self.poly_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.poly_table.setAlternatingRowColors(True)
        self.poly_table.itemChanged.connect(self._on_poly_cell_changed)
        self.poly_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                gridline-color: #e5e7eb;
            }
            QHeaderView::section {
                background: #f3f4f6;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        poly_layout.addWidget(self.poly_table)
        layout.addWidget(poly_group, 1)

    def _init_tab_anciennes(self):
        """Initialise l'onglet Historique des polyvalences."""
        layout = QVBoxLayout(self.tab_anciennes)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        anciennes_group = QGroupBox("Historique des polyvalences")
        anciennes_layout = QVBoxLayout(anciennes_group)

        self.anciennes_table = QTableWidget()
        self.anciennes_table.setColumnCount(6)
        self.anciennes_table.setHorizontalHeaderLabels([
            "Date", "Poste", "Changement", "Nouveau niveau", "Commentaire", "_id"
        ])
        self.anciennes_table.setColumnHidden(5, True)
        self.anciennes_table.horizontalHeader().setStretchLastSection(True)
        self.anciennes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.anciennes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.anciennes_table.setAlternatingRowColors(True)
        self.anciennes_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                gridline-color: #e5e7eb;
            }
            QHeaderView::section {
                background: #f3f4f6;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        anciennes_layout.addWidget(self.anciennes_table)
        layout.addWidget(anciennes_group, 1)

    def _load_data(self):
        """Charge toutes les données de l'opérateur via le ViewModel (async)."""
        self._vm.load_detail(self.operateur_id)

    def _on_detail_loaded(self, data: dict):
        """Reçoit stats + polyvalences + historique et peuple les tables."""
        stats = data.get('stats') or {}
        polyvalences = data.get('polyvalences') or []
        historique = data.get('historique') or []

        # --- Onglet Résumé : statistiques ---
        if stats:
            total = stats.get('total') or 0
            parts = []
            if stats.get('n4'): parts.append(f"N4×{stats['n4']}")
            if stats.get('n3'): parts.append(f"N3×{stats['n3']}")
            if stats.get('n2'): parts.append(f"N2×{stats['n2']}")
            if stats.get('n1'): parts.append(f"N1×{stats['n1']}")
            poly_text = " | ".join(parts) if parts else "Aucune"

            eval_parts = []
            if stats.get('retard'): eval_parts.append(f"{stats['retard']} en retard")
            if stats.get('a_planifier'): eval_parts.append(f"{stats['a_planifier']} à planifier")
            if not eval_parts: eval_parts.append("Toutes à jour")

            self.stats_label.setText(
                f"<b>{total} polyvalence(s) actuelle(s)</b><br/>"
                f"Niveaux : {poly_text}<br/>"
                f"Évaluations : {' | '.join(eval_parts)}"
            )

        # --- Onglet Résumé : tableau polyvalences ---
        self.poly_table.blockSignals(True)
        self.poly_table.setRowCount(len(polyvalences))

        from datetime import date as dt_date
        today = dt_date.today()

        for row_idx, poly in enumerate(polyvalences):
            poste_item = QTableWidgetItem(poly['poste_code'])
            poste_item.setFlags(poste_item.flags() & ~Qt.ItemIsEditable)
            self.poly_table.setItem(row_idx, 0, poste_item)

            niveau_item = QTableWidgetItem(str(poly['niveau']))
            niveau_item.setTextAlignment(Qt.AlignCenter)
            self.poly_table.setItem(row_idx, 1, niveau_item)

            date_eval_str = format_date(poly['date_evaluation']) if poly['date_evaluation'] else "N/A"
            self.poly_table.setItem(row_idx, 2, QTableWidgetItem(date_eval_str))

            date_next_str = format_date(poly['prochaine_evaluation']) if poly['prochaine_evaluation'] else "N/A"
            date_next_item = QTableWidgetItem(date_next_str)
            date_next_item.setFlags(date_next_item.flags() & ~Qt.ItemIsEditable)
            self.poly_table.setItem(row_idx, 3, date_next_item)

            if poly['prochaine_evaluation']:
                if poly['prochaine_evaluation'] < today:
                    statut = "En retard"
                elif (poly['prochaine_evaluation'] - today).days <= 30:
                    statut = "À planifier"
                else:
                    statut = "À jour"
            else:
                statut = "N/A"
            statut_item = QTableWidgetItem(statut)
            statut_item.setFlags(statut_item.flags() & ~Qt.ItemIsEditable)
            self.poly_table.setItem(row_idx, 4, statut_item)
            self.poly_table.setItem(row_idx, 5, QTableWidgetItem(str(poly['id'])))

        self.poly_table.blockSignals(False)

        # --- Onglet Historique ---
        action_labels = {
            'MODIFICATION': 'Modification',
            'AJOUT': 'Ajout',
            'SUPPRESSION': 'Suppression',
            'IMPORT_MANUEL': 'Import manuel',
        }
        self.anciennes_table.setRowCount(len(historique))

        for row_idx, anc in enumerate(historique):
            date_action = anc['date_action']
            date_str = format_datetime(date_action, default=str(date_action)) if date_action else "N/A"
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.anciennes_table.setItem(row_idx, 0, date_item)

            self.anciennes_table.setItem(row_idx, 1, QTableWidgetItem(anc['poste_code'] or "N/A"))

            action_type = anc.get('action_type', '')
            label = action_labels.get(action_type, action_type)
            ancien = anc.get('ancien_niveau')
            nouveau = anc.get('nouveau_niveau')
            if ancien is not None and nouveau is not None and ancien != nouveau:
                label = f"N{ancien} → N{nouveau}"
            changement_item = QTableWidgetItem(label)
            changement_item.setTextAlignment(Qt.AlignCenter)
            self.anciennes_table.setItem(row_idx, 2, changement_item)

            niveau_txt = f"N{nouveau}" if nouveau is not None else "N/A"
            niveau_item = QTableWidgetItem(niveau_txt)
            niveau_item.setTextAlignment(Qt.AlignCenter)
            self.anciennes_table.setItem(row_idx, 3, niveau_item)

            self.anciennes_table.setItem(row_idx, 4, QTableWidgetItem(anc.get('commentaire') or "—"))
            self.anciennes_table.setItem(row_idx, 5, QTableWidgetItem(str(anc['id'])))

    def _on_poly_cell_changed(self, item):
        """Gère les modifications de cellules dans le tableau des polyvalences."""
        if item is None:
            return

        row = item.row()
        col = item.column()

        if col not in [1, 2]:
            return

        poly_id_item = self.poly_table.item(row, 5)
        if not poly_id_item:
            return

        poly_id = int(poly_id_item.text())
        new_value = item.text().strip()

        # === NIVEAU (colonne 1) ===
        if col == 1:
            if new_value == "":
                poste_item = self.poly_table.item(row, 0)
                poste_code = poste_item.text() if poste_item else "?"

                self._vm.compter_polyvalences(self.operateur_id)  # emits evaluation_count synchronously
                if self._pending_count <= 1:
                    QMessageBox.warning(
                        self, "Suppression impossible",
                        "Impossible de supprimer la dernière polyvalence de cet opérateur.\n"
                        "Il disparaîtrait de la grille de compétences et ne pourrait plus être modifié.\n\n"
                        "Utilisez 'Masquer' depuis la grille pour retirer l'opérateur."
                    )
                    self._load_data()
                    return

                reply = QMessageBox.question(
                    self, "Supprimer la polyvalence",
                    f"Voulez-vous supprimer la polyvalence pour le poste {poste_code} ?\n"
                    "Cette action est irréversible.",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    self._load_data()
                    return
                self._vm.supprimer_polyvalence(poly_id, poste_code)
                return

            try:
                new_niveau = int(new_value)
                if new_niveau not in [1, 2, 3, 4]:
                    raise ValueError()
            except ValueError:
                QMessageBox.warning(self, "Valeur invalide", "Le niveau doit être 1, 2, 3 ou 4")
                self._load_data()
                return

            date_eval_item = self.poly_table.item(row, 2)
            if not date_eval_item or date_eval_item.text() == "N/A":
                from datetime import date
                date_eval = date.today()
            else:
                from datetime import datetime, date
                try:
                    date_eval = datetime.strptime(date_eval_item.text(), "%d/%m/%Y").date()
                except ValueError:
                    date_eval = date.today()

            niveau_changed = self._vm.mettre_a_jour_niveau(
                poly_id,
                new_niveau,
                date_eval,
                self.operateur_nom,
                self.operateur_prenom,
            )
            if niveau_changed:
                self._ajouter_documents_formation_en_attente(poly_id, new_niveau)
            return

        # === DATE D'ÉVALUATION (colonne 2) ===
        from datetime import datetime
        try:
            new_date = datetime.strptime(new_value, "%d/%m/%Y").date()
        except ValueError:
            QMessageBox.warning(self, "Format invalide", "Le format de date doit être JJ/MM/AAAA")
            self._load_data()
            return

        niveau_item = self.poly_table.item(row, 1)
        nouveau_niveau = None
        if niveau_item:
            try:
                nouveau_niveau = int(niveau_item.text())
            except (ValueError, AttributeError):
                pass

        self._vm.mettre_a_jour_date(poly_id, new_date, nouveau_niveau)

    def _ajouter_documents_formation_en_attente(self, poly_id: int, niveau: int) -> None:
        """
        Ajoute les dossiers de formation poste/niveau a la file d'impression.

        Le dialogue de proposition est ensuite affiche par le debounce global
        de MainWindow, comme pour les documents issus des regles.
        """
        if niveau not in (1, 2, 3):
            return

        try:
            from domain.services.formation.evaluation_service import get_polyvalence_par_id
            from application.document_trigger_service import DocumentTriggerService

            poly = get_polyvalence_par_id(poly_id)
            poste_id = poly.get('poste_id') if poly else None
            if not poste_id:
                return

            added = DocumentTriggerService.add_formation_docs_for_level(
                operateur_id=self.operateur_id,
                nom=self.operateur_nom,
                prenom=self.operateur_prenom,
                poste_id=poste_id,
                niveau=niveau,
                event_name=f'polyvalence.niveau_{niveau}_reached',
            )
            if added:
                logger.info(
                    f"{added} document(s) formation ajoute(s) a la file "
                    f"pour operateur {self.operateur_id}, poste {poste_id}, N{niveau}"
                )
        except Exception as e:
            logger.warning(f"Impossible d'ajouter les documents formation a la file: {e}")


# --- Délégué pour empêcher l'édition ---
class NoEditDelegate(QStyledItemDelegate):
    """Empêche l'édition des cellules."""

    def createEditor(self, _parent, _option, _index):
        # Retourner None empêche la création d'un éditeur
        return None


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
        self.setGeometry(100, 80, 1400, 800)

        self._vm = EvaluationViewModel(parent=self)

        # Données
        self.all_evaluations = []
        self._filtered_evaluations = []

        # Layout principal avec marges nulles
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Gestion des Évaluations")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # === En-tête ===
        layout.addWidget(EmacHeader(
            "Gestion des Évaluations",
            "Consultez et gérez les évaluations de polyvalence du personnel",
        ))

        # === Recherche et Filtres ===
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        filter_layout.addWidget(QLabel("Rechercher :"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom, prénom ou matricule...")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)

        sep = QLabel("·")
        sep.setStyleSheet("color: #d1d5db; font-size: 16px; padding: 0 8px;")
        filter_layout.addWidget(sep)

        filter_layout.addWidget(QLabel("Statut :"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tous", "En retard", "À planifier (30j)", "À jour"])
        self.status_filter.setMinimumWidth(120)
        self.status_filter.setMaximumWidth(160)
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # === Statistiques ===
        stats_card = EmacCard()
        stats_lbl = QLabel("Statistiques")
        stats_lbl.setProperty('class', 'h2')
        stats_card.body.addWidget(stats_lbl)

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
        stats_card.body.addLayout(stats_layout)
        layout.addWidget(stats_card)

        # === Tableau ===
        table_card = EmacCard()
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "_pers_id", "Nom", "Prénom", "Matricule", "Polyvalences", "Évaluations", "Statut"
        ])
        self.table.setColumnHidden(0, True)
        for col in range(1, 7):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self._style_table()
        self.table.cellDoubleClicked.connect(self._on_row_double_click)

        table_layout.addWidget(self.table)
        table_card.body.addLayout(table_layout)
        layout.addWidget(table_card, 1)

        # === Boutons ===
        btn_layout = QHBoxLayout()

        self.refresh_btn = EmacButton("Actualiser", variant='primary')
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)

        self.export_btn = EmacButton("Exporter PDF", variant='ghost')
        self.export_btn.clicked.connect(self.export_to_pdf)
        btn_layout.addWidget(self.export_btn)

        self.print_btn = EmacButton("Imprimer les documents", variant='ghost')
        self.print_btn.setToolTip("Ouvrir la fenêtre de sélection des documents à imprimer")
        self.print_btn.clicked.connect(self._imprimer_documents_operateur)
        btn_layout.addWidget(self.print_btn)

        btn_layout.addStretch()

        self.close_btn = EmacButton("Fermer", variant='ghost')
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        # Ajouter le widget de contenu au layout principal
        main_layout.addWidget(content_widget)

        self._connect_viewmodel()

        # Charger les données
        self.load_data()

    def _connect_viewmodel(self):
        self._vm.operateurs_loaded.connect(self._on_operateurs_loaded)
        self._vm.error_occurred.connect(
            lambda msg: QMessageBox.critical(self, "Erreur", msg)
        )

    def _style_table(self):
        """Applique un style moderne à la table."""
        ThemeCls = get_current_theme()

        self.table.setStyleSheet(f"""
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

        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.verticalHeader().setDefaultSectionSize(32)


    def load_data(self):
        """Charge la liste des opérateurs (async via ViewModel)."""
        self._vm.load_operateurs()

    def _on_operateurs_loaded(self, data: list):
        self.all_evaluations = data
        self.apply_filters()

    def apply_filters(self):
        """Applique les filtres de recherche et affiche les résultats."""
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()

        # Filtrer les données
        filtered = []
        for oper_data in self.all_evaluations:
            # Filtre recherche (nom, prénom ou matricule)
            if search_text:
                searchable = f"{oper_data['nom']} {oper_data['prenom']} {oper_data['matricule']}".lower()
                if search_text not in searchable:
                    continue

            # Filtre statut
            if status_filter != "Tous":
                if status_filter == "À planifier (30j)" and oper_data['statut_code'] != "À planifier":
                    continue
                elif status_filter != "À planifier (30j)" and oper_data['statut_code'] != status_filter:
                    continue

            filtered.append(oper_data)

        # Mémoriser pour le bouton impression
        self._filtered_evaluations = filtered

        # Afficher dans le tableau
        self.display_operateurs(filtered)

        # Mettre à jour les statistiques
        self.update_statistics(filtered)

    def display_operateurs(self, operateurs):
        """Affiche la liste des opérateurs dans le tableau."""
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)

        for oper_data in operateurs:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            # Colonne 0: ID (caché)
            self.table.setItem(row_pos, 0, QTableWidgetItem(str(oper_data['personnel_id'])))

            # Colonne 1-3: Nom, Prénom, Matricule
            self.table.setItem(row_pos, 1, QTableWidgetItem(oper_data['nom']))
            self.table.setItem(row_pos, 2, QTableWidgetItem(oper_data['prenom']))
            self.table.setItem(row_pos, 3, QTableWidgetItem(oper_data['matricule']))

            # Colonne 4: Polyvalences (résumé compact)
            poly_parts = []
            if oper_data['n4']: poly_parts.append(f"N4×{oper_data['n4']}")
            if oper_data['n3']: poly_parts.append(f"N3×{oper_data['n3']}")
            if oper_data['n2']: poly_parts.append(f"N2×{oper_data['n2']}")
            if oper_data['n1']: poly_parts.append(f"N1×{oper_data['n1']}")

            poly_text = " | ".join(poly_parts) if poly_parts else "Aucune"
            poly_item = QTableWidgetItem(f"{oper_data['total']} : {poly_text}")
            self.table.setItem(row_pos, 4, poly_item)

            # Colonne 5: Évaluations en retard/à planifier
            eval_parts = []
            if oper_data['retard']: eval_parts.append(f"{oper_data['retard']} en retard")
            if oper_data['a_planifier']: eval_parts.append(f"{oper_data['a_planifier']} à planifier")

            eval_text = " | ".join(eval_parts) if eval_parts else "—"
            self.table.setItem(row_pos, 5, QTableWidgetItem(eval_text))

            # Colonne 6: Statut global
            statut_item = QTableWidgetItem(oper_data['statut'])
            statut_item.setTextAlignment(Qt.AlignCenter)

            if oper_data['statut_code'] == "En retard":
                statut_item.setBackground(QColor("#fecaca"))
                statut_item.setForeground(QColor("#dc2626"))
            elif oper_data['statut_code'] == "À planifier":
                statut_item.setBackground(QColor("#fed7aa"))
                statut_item.setForeground(QColor("#ea580c"))
            else:
                statut_item.setBackground(QColor("#d1fae5"))
                statut_item.setForeground(QColor("#059669"))

            font = QFont()
            font.setBold(True)
            statut_item.setFont(font)
            self.table.setItem(row_pos, 6, statut_item)

        self.table.setSortingEnabled(True)

    def update_statistics(self, operateurs):
        """Met à jour les statistiques affichées."""
        total = len(operateurs)
        en_retard = sum(1 for o in operateurs if o['statut_code'] == "En retard")
        a_planifier = sum(1 for o in operateurs if o['statut_code'] == "À planifier")
        a_jour = sum(1 for o in operateurs if o['statut_code'] == "À jour")

        self.total_label.setText(f"Total : {total}")
        self.retard_label.setText(f"En retard : {en_retard}")
        self.a_planifier_label.setText(f"À planifier : {a_planifier}")
        self.a_jour_label.setText(f"À jour : {a_jour}")

    def _imprimer_documents_operateur(self):
        """
        Ouvre la fenêtre de sélection multi-opérateurs pour l'impression
        des documents d'évaluation à la demande.

        Passe la liste des opérateurs actuellement filtrés dans le tableau.
        """
        operateurs = self._filtered_evaluations or self.all_evaluations

        if not operateurs:
            QMessageBox.information(
                self,
                "Liste vide",
                "Aucun opérateur dans la liste courante.\n"
                "Actualisez ou modifiez les filtres."
            )
            return

        try:
            from gui.screens.documents.imprimer_documents_dialog import ImprimerDocumentsDialog
            dialog = ImprimerDocumentsDialog(operateurs=operateurs, parent=self)
            dialog.exec_()
        except Exception as e:
            logger.exception(f"Erreur ouverture dialog impression: {e}")
            if show_error_message:
                show_error_message(self, "Erreur", "Impossible d'ouvrir la fenêtre d'impression", e)
            else:
                QMessageBox.critical(self, "Erreur",
                                     "Impossible d'ouvrir la fenêtre d'impression. Contactez l'administrateur.")

    def update_date_in_db(self, row, col, qdate):
        """Met à jour une date de polyvalence via le ViewModel."""
        poly_id_item = self.table.item(row, 0)
        if not poly_id_item:
            return
        try:
            poly_id = int(poly_id_item.text())
        except ValueError:
            return

        if col not in (5, 6):
            return

        new_date = qdate.toPyDate()
        self._vm.mettre_a_jour_date(poly_id, new_date)

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
            logger.exception(f"Erreur export PDF: {e}")
            if show_error_message:
                show_error_message(self, "Erreur", "Impossible d'exporter en PDF", e)
            else:
                QMessageBox.critical(self, "Erreur", "Impossible d'exporter en PDF. Contactez l'administrateur.")

    def _on_row_double_click(self, row, col):
        """Gère le double-clic sur une ligne du tableau."""
        # Ne pas ouvrir le dialogue si on double-clique sur les colonnes de dates (5-6)
        if col in [5, 6]:
            return

        # Récupérer l'ID depuis la colonne cachée (colonne 0)
        id_item = self.table.item(row, 0)
        if not id_item:
            return

        operateur_id = int(id_item.text())

        # Récupérer nom et prénom depuis les colonnes visibles
        nom_item = self.table.item(row, 1)
        prenom_item = self.table.item(row, 2)

        nom = nom_item.text() if nom_item else ""
        prenom = prenom_item.text() if prenom_item else ""

        # Ouvrir le dialogue détaillé avec 2 onglets
        dialog = DetailOperateurDialog(operateur_id, nom, prenom, self, vm=self._vm)
        dialog.exec_()

        # Les documents en attente sont gérés par le mécanisme debounce
        # de MainWindow (_on_event_for_documents) via l'EventBus.
        # Ne pas appeler show_pending_documents_if_any ici pour éviter
        # une double apparition du dialog.

        # Recharger les données après fermeture du dialogue
        self.load_data()

