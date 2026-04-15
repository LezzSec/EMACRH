# -*- coding: utf-8 -*-
"""
Classes de base pour les onglets de configuration du panel admin.

Fournit :
  - Helpers : _txt, _bool_label, _confirm_delete
  - _ConfigTab    : widget de base avec table + boutons CRUD + chargement async
  - _SimpleFormDialog : dialogue de formulaire générique
  - _ReadOnlyTab  : variante lecture seule de _ConfigTab
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QTableWidget, QTableWidgetItem, QAbstractItemView,
    QMessageBox, QLineEdit, QTextEdit,
    QFormLayout, QDialogButtonBox, QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from gui.components.ui_theme import EmacButton
from gui.workers.db_worker import DbWorker, DbThreadPool
from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date, format_datetime

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════════
#  Helpers
# ════════════════════════════════════════════════════════════════

def _txt(val) -> str:
    """Convertit une valeur en texte d'affichage (None → '')."""
    if val is None:
        return ''
    return str(val)


def _bool_label(val) -> str:
    return 'Oui' if val else 'Non'


def _confirm_delete(parent, name: str) -> bool:
    reply = QMessageBox.question(
        parent,
        "Confirmer la suppression",
        f"Supprimer « {name} » ?\n\nCette action est irréversible.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    return reply == QMessageBox.Yes


# ════════════════════════════════════════════════════════════════
#  Widget de base pour chaque onglet
# ════════════════════════════════════════════════════════════════

class _ConfigTab(QWidget):
    """
    Widget de base pour un onglet de configuration.

    Fournit :
      - Bandeau de description (DESCRIPTION + USAGE)
      - QTableWidget avec en-têtes configurables
      - Barre de boutons : Ajouter / Modifier / Supprimer / Actualiser
      - Chargement asynchrone via DbWorker

    À surcharger :
      - COLUMNS      : liste de (header_label, row_key) dans l'ordre d'affichage
      - DESCRIPTION  : courte description de ce que contient cet onglet
      - USAGE        : où ces données sont utilisées dans l'application
      - fetch_data()    → list[dict]
      - show_form(data) → ouvre add (data=None) ou edit form
    """

    # Sous-classes : liste de (header, key_dans_dict)
    COLUMNS: list = []

    # Description affichée en bandeau dans l'onglet
    DESCRIPTION: str = ""
    USAGE: str = ""

    # Clés dont la valeur est un booléen → affiché "Oui"/"Non"
    BOOL_KEYS: set = set()
    # Clés dont la valeur est une date → affiché en DD/MM/YYYY
    DATE_KEYS: set = set()
    # Clés dont la valeur est une datetime → affiché en DD/MM/YYYY HH:MM:SS
    DATETIME_KEYS: set = set()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records: list = []
        self._build_ui()
        QTimer.singleShot(50, self._load_async)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 12)
        layout.setSpacing(12)

        # ── Bandeau description ───────────────────────────────────
        if self.DESCRIPTION or self.USAGE:
            info_widget = QWidget()
            info_widget.setStyleSheet(
                "background: #f0f4ff; border: 1px solid #c7d2fe; border-radius: 6px;"
            )
            info_lay = QVBoxLayout(info_widget)
            info_lay.setContentsMargins(12, 10, 12, 10)
            info_lay.setSpacing(3)
            if self.DESCRIPTION:
                lbl_desc = QLabel(self.DESCRIPTION)
                lbl_desc.setStyleSheet("color: #1e3a8a; font-size: 12px; font-weight: 600; background: transparent; border: none;")
                lbl_desc.setWordWrap(True)
                info_lay.addWidget(lbl_desc)
            if self.USAGE:
                lbl_usage = QLabel(f"Utilisé dans : {self.USAGE}")
                lbl_usage.setStyleSheet("color: #4b5563; font-size: 11px; background: transparent; border: none;")
                lbl_usage.setWordWrap(True)
                info_lay.addWidget(lbl_usage)
            layout.addWidget(info_widget)

        # ── Barre de boutons ──────────────────────────────────────
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)

        self.btn_add = EmacButton("Ajouter", variant='primary')
        self.btn_add.setStyleSheet(
            "QPushButton { background: #0f172a; color: #ffffff; border: 1px solid #0f172a; "
            "border-radius: 6px; font-weight: 600; padding: 0 16px; }"
            "QPushButton:hover { background: #1e293b; border-color: #1e293b; }"
        )
        self.btn_add.clicked.connect(self._on_add)
        btn_bar.addWidget(self.btn_add)

        self.btn_edit = EmacButton("Modifier", variant='ghost')
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_edit.setEnabled(False)
        self.btn_edit.setToolTip("Sélectionnez une ligne pour modifier")
        btn_bar.addWidget(self.btn_edit)

        self.btn_del = EmacButton("Supprimer", variant='ghost')
        self.btn_del.clicked.connect(self._on_delete)
        self.btn_del.setEnabled(False)
        self.btn_del.setToolTip("Sélectionnez une ligne pour supprimer")
        btn_bar.addWidget(self.btn_del)

        btn_bar.addStretch()

        self.btn_refresh = EmacButton("Actualiser", variant='ghost')
        self.btn_refresh.clicked.connect(self._load_async)
        btn_bar.addWidget(self.btn_refresh)

        layout.addLayout(btn_bar)

        # ── Table ─────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in self.COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(self._on_edit)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e6ea;
                border-radius: 6px;
                background: white;
                selection-background-color: #dbeafe;
                selection-color: #1e40af;
                font-size: 12px;
            }
            QHeaderView::section {
                background: #f8f9fb;
                border: none;
                border-bottom: 1px solid #e2e6ea;
                padding: 8px 12px;
                font-weight: 600;
                color: #6b7280;
                font-size: 11px;
                text-transform: uppercase;
            }
            QTableWidget::item {
                padding: 7px 12px;
                border-bottom: 1px solid #f3f4f6;
                color: #374151;
            }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #1e40af;
            }
        """)
        self.table.verticalHeader().setDefaultSectionSize(36)

        layout.addWidget(self.table)

        # ── Statut ────────────────────────────────────────────────
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #9ca3af; font-size: 11px;")
        layout.addWidget(self.lbl_status)

    # ── Chargement ────────────────────────────────────────────────

    def _load_async(self):
        self.lbl_status.setText("Chargement…")
        self.btn_refresh.setEnabled(False)
        # DbWorker injecte toujours progress_callback ; on l'absorbe ici
        # pour ne pas avoir à le déclarer dans chaque fetch_data() de sous-classe.
        def _fetch(**_):
            return self.fetch_data()
        worker = DbWorker(_fetch)
        worker.signals.result.connect(self._on_data_loaded)
        worker.signals.error.connect(self._on_load_error)
        DbThreadPool.start(worker)

    def _on_data_loaded(self, records: list):
        self._records = records or []
        self._populate_table(self._records)
        n = len(self._records)
        self.lbl_status.setText(
            f"{n} enregistrement{'s' if n > 1 else ''}  —  Cliquez sur une ligne pour activer Modifier / Supprimer"
        )
        self.btn_refresh.setEnabled(True)
        # Notifier le dialog parent pour mettre à jour le badge sidebar
        self._emit_count(n)

    def _emit_count(self, n: int):
        """Remonte le comptage au dialog parent pour mise à jour du badge sidebar."""
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, '_update_nav_badge'):
                parent._update_nav_badge(self, n)
                break
            parent = parent.parent() if hasattr(parent, 'parent') else None

    def _on_load_error(self, error_msg: str):
        logger.error(f"Erreur chargement {self.__class__.__name__}: {error_msg}")
        self.lbl_status.setText("Erreur de chargement")
        self.btn_refresh.setEnabled(True)

    def _populate_table(self, records: list):
        self.table.setRowCount(0)
        for row_idx, rec in enumerate(records):
            self.table.insertRow(row_idx)
            for col_idx, (_, key) in enumerate(self.COLUMNS):
                val = rec.get(key)
                item = QTableWidgetItem(self._format_cell(key, val, rec))
                item.setData(Qt.UserRole, rec.get('id'))
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _format_cell(self, key: str, val, record: dict) -> str:
        """Peut être surchargée pour formater certaines colonnes."""
        if key in self.BOOL_KEYS:
            return _bool_label(val)
        if key in self.DATE_KEYS and val is not None:
            return format_date(val) or str(val)
        if key in self.DATETIME_KEYS and val is not None:
            return format_datetime(val) or str(val)
        if isinstance(val, bool):
            return _bool_label(val)
        if val is None:
            return ''
        return str(val)

    # ── Sélection ─────────────────────────────────────────────────

    def _on_selection_changed(self):
        has_sel = bool(self.table.selectedItems())
        self.btn_edit.setEnabled(has_sel)
        self.btn_del.setEnabled(has_sel)
        if has_sel:
            self.lbl_status.setText(f"{len(self._records)} enregistrement(s)")
        elif self._records:
            self.lbl_status.setText(
                f"{len(self._records)} enregistrement(s)  —  Cliquez sur une ligne pour activer Modifier / Supprimer"
            )

    def _get_selected_record(self) -> dict | None:
        rows = self.table.selectedItems()
        if not rows:
            return None
        row = self.table.currentRow()
        record_id = self.table.item(row, 0).data(Qt.UserRole)
        for rec in self._records:
            if rec.get('id') == record_id:
                return rec
        return None

    # ── Actions ───────────────────────────────────────────────────

    def _on_add(self):
        self.show_form(None)

    def _on_edit(self):
        rec = self._get_selected_record()
        if rec:
            self.show_form(rec)

    def _on_delete(self):
        rec = self._get_selected_record()
        if not rec:
            return
        name = self._get_display_name(rec)
        if not _confirm_delete(self, name):
            return
        try:
            ok, msg = self.delete_record(rec['id'])
            if ok:
                self._load_async()
            else:
                QMessageBox.warning(self, "Suppression impossible", msg)
        except Exception as e:
            logger.exception(f"Erreur suppression: {e}")
            QMessageBox.critical(self, "Erreur", "Impossible de supprimer cet enregistrement. Consultez les logs pour plus de détails.")

    # ── À surcharger ──────────────────────────────────────────────

    def fetch_data(self) -> list:
        raise NotImplementedError

    def show_form(self, data: dict | None):
        raise NotImplementedError

    def delete_record(self, record_id: int) -> tuple:
        raise NotImplementedError

    def _get_display_name(self, record: dict) -> str:
        """Retourne le nom affiché dans la confirmation de suppression."""
        for key in ('nom', 'libelle', 'code', 'nom_service'):
            if key in record and record[key]:
                return str(record[key])
        return f"#{record.get('id', '?')}"


# ════════════════════════════════════════════════════════════════
#  Formulaire générique simple
# ════════════════════════════════════════════════════════════════

class _SimpleFormDialog(QDialog):
    """
    Dialogue de formulaire réutilisable basé sur QFormLayout.
    """

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(460)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(20, 20, 20, 20)
        self._main_layout.setSpacing(14)

        lbl = QLabel(title)
        lbl.setProperty('class', 'h2')
        self._main_layout.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #ddd;")
        self._main_layout.addWidget(sep)

        self.form = QFormLayout()
        self.form.setSpacing(10)
        self.form.setLabelAlignment(Qt.AlignRight)
        self._main_layout.addLayout(self.form)

        self._main_layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        self._main_layout.addWidget(buttons)

    def _on_accept(self):
        ok, msg = self.validate()
        if not ok:
            QMessageBox.warning(self, "Validation", msg)
            return
        self.accept()

    def validate(self) -> tuple:
        return True, ""

    def _require_text(self, widget: QLineEdit, label: str) -> tuple:
        if not widget.text().strip():
            return False, f"Le champ « {label} » est obligatoire."
        return True, ""


# ════════════════════════════════════════════════════════════════
#  Onglet lecture seule
# ════════════════════════════════════════════════════════════════

class _ReadOnlyTab(_ConfigTab):
    """
    Variante de _ConfigTab sans boutons Ajouter / Modifier / Supprimer.
    Affiche uniquement le bouton Actualiser et un label informatif en haut.
    """

    INFO_LABEL: str = "Affichage en lecture seule."

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Info label ────────────────────────────────────────────
        lbl_info = QLabel(self.INFO_LABEL)
        lbl_info.setStyleSheet("color: #666; font-size: 12px; font-style: italic;")
        layout.addWidget(lbl_info)

        # ── Barre de boutons (Actualiser uniquement) ──────────────
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        self.btn_refresh = EmacButton("Actualiser", variant='ghost')
        self.btn_refresh.clicked.connect(self._load_async)
        btn_bar.addWidget(self.btn_refresh)
        layout.addLayout(btn_bar)

        # Attributs vides requis par la classe de base
        self.btn_add = None
        self.btn_edit = None
        self.btn_del = None

        # ── Table ─────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in self.COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.table)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.lbl_status)

    def _on_selection_changed(self):
        pass  # Pas de boutons à activer

    # Les méthodes abstraites n'ont pas besoin d'être implémentées pour les onglets RO
    def show_form(self, data):
        pass

    def delete_record(self, record_id):
        return True, ""
