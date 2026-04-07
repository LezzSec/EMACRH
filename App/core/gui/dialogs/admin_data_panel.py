# -*- coding: utf-8 -*-
"""
Panel d'administration des données de référence.

Accessible uniquement aux administrateurs, permet de gérer toutes les tables
de paramétrage depuis l'interface :

  Ateliers · Services · Types d'absence · Jours fériés · Compétences ·
  Catégories documents · Motifs de sortie · Tranches d'âge · Rôles

Usage (depuis main_qt.py) :
    from core.gui.dialogs.admin_data_panel import AdminDataPanelDialog
    dlg = AdminDataPanelDialog(parent=self)
    dlg.exec_()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QTableWidget, QTableWidgetItem, QAbstractItemView,
    QMessageBox, QLineEdit, QTextEdit, QCheckBox, QSpinBox, QDoubleSpinBox,
    QFormLayout, QDialogButtonBox, QComboBox, QFrame, QDateEdit,
    QColorDialog, QPushButton, QListWidget, QListWidgetItem, QStackedWidget
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QColor, QFont

from core.gui.components.ui_theme import EmacButton
from core.gui.workers.db_worker import DbWorker, DbThreadPool
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
#  1. ATELIERS
# ════════════════════════════════════════════════════════════════

class _AtelierForm(_SimpleFormDialog):
    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier l'atelier" if data else "Nouvel atelier"
        super().__init__(title, parent)
        self._data = data

        self.inp_nom = QLineEdit()
        self.inp_nom.setPlaceholderText("Nom de l'atelier")
        self.form.addRow("Nom *", self.inp_nom)

        if data:
            self.inp_nom.setText(data.get('nom', ''))

    def validate(self):
        return self._require_text(self.inp_nom, "Nom")

    def get_values(self) -> dict:
        return {'nom': self.inp_nom.text().strip()}


class AteliersTab(_ConfigTab):
    COLUMNS = [("ID", "id"), ("Nom", "nom")]
    DESCRIPTION = "Ateliers de production — unités organisationnelles regroupant des postes de travail."
    USAGE = "Création/suppression de postes, grille de polyvalence, filtres de planning"

    def fetch_data(self):
        from domain.services.admin.config_service import AtelierService
        return AtelierService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import AtelierService
        dlg = _AtelierForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    AtelierService.update(data['id'], **vals)
                else:
                    AtelierService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur atelier: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import AtelierService
        return AtelierService.delete(record_id)


# ════════════════════════════════════════════════════════════════
#  2. SERVICES RH
# ════════════════════════════════════════════════════════════════

class _ServiceRHForm(_SimpleFormDialog):
    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier le service" if data else "Nouveau service"
        super().__init__(title, parent)
        self._data = data

        self.inp_nom = QLineEdit()
        self.inp_nom.setPlaceholderText("Nom du service")
        self.form.addRow("Nom *", self.inp_nom)

        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(80)
        self.inp_desc.setPlaceholderText("Description (optionnelle)")
        self.form.addRow("Description", self.inp_desc)

        if data:
            self.inp_nom.setText(data.get('nom_service', ''))
            self.inp_desc.setPlainText(data.get('description') or '')

    def validate(self):
        return self._require_text(self.inp_nom, "Nom")

    def get_values(self) -> dict:
        return {
            'nom_service': self.inp_nom.text().strip(),
            'description': self.inp_desc.toPlainText().strip() or None
        }


class ServicesTab(_ConfigTab):
    COLUMNS = [("ID", "id"), ("Nom", "nom_service"), ("Description", "description")]
    DESCRIPTION = "Services RH — divisions fonctionnelles du personnel (ex : Maintenance, Logistique…)."
    USAGE = "Fiche personnel, filtres RH, statistiques par service"

    def fetch_data(self):
        from domain.services.admin.config_service import ServicesRHService
        return ServicesRHService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import ServicesRHService
        dlg = _ServiceRHForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    ServicesRHService.update(data['id'], **vals)
                else:
                    ServicesRHService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur service: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import ServicesRHService
        return ServicesRHService.delete(record_id)


# ════════════════════════════════════════════════════════════════
#  3. TYPES D'ABSENCE
# ════════════════════════════════════════════════════════════════

class _TypeAbsenceForm(_SimpleFormDialog):
    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier le type d'absence" if data else "Nouveau type d'absence"
        super().__init__(title, parent)

        self.inp_code = QLineEdit()
        self.inp_code.setMaxLength(20)
        self.inp_code.setPlaceholderText("Ex: CP, RTT, MAL…")
        self.form.addRow("Code *", self.inp_code)

        self.inp_libelle = QLineEdit()
        self.inp_libelle.setPlaceholderText("Libellé complet")
        self.form.addRow("Libellé *", self.inp_libelle)

        self.chk_decompte = QCheckBox("Décompter du solde de congés")
        self.chk_decompte.setChecked(True)
        self.form.addRow("", self.chk_decompte)

        self.chk_actif = QCheckBox("Actif")
        self.chk_actif.setChecked(True)
        self.form.addRow("", self.chk_actif)

        # Couleur
        couleur_row = QHBoxLayout()
        self.inp_couleur = QLineEdit()
        self.inp_couleur.setMaxLength(7)
        self.inp_couleur.setText('#3498db')
        self.inp_couleur.setMaximumWidth(90)
        self._color_preview = QPushButton()
        self._color_preview.setFixedSize(30, 24)
        self._color_preview.clicked.connect(self._pick_color)
        couleur_row.addWidget(self.inp_couleur)
        couleur_row.addWidget(self._color_preview)
        couleur_row.addStretch()
        self.form.addRow("Couleur", couleur_row)
        self.inp_couleur.textChanged.connect(self._update_color_preview)

        if data:
            self.inp_code.setText(data.get('code', ''))
            self.inp_libelle.setText(data.get('libelle', ''))
            self.chk_decompte.setChecked(bool(data.get('decompte_solde', True)))
            self.chk_actif.setChecked(bool(data.get('actif', True)))
            self.inp_couleur.setText(data.get('couleur') or '#3498db')

        self._update_color_preview()

    def _pick_color(self):
        current = self.inp_couleur.text()
        color = QColorDialog.getColor(QColor(current), self, "Choisir une couleur")
        if color.isValid():
            self.inp_couleur.setText(color.name())

    def _update_color_preview(self):
        c = self.inp_couleur.text()
        try:
            QColor(c)
            self._color_preview.setStyleSheet(f"background-color: {c}; border: 1px solid #ccc; border-radius: 3px;")
        except Exception:
            pass

    def validate(self):
        ok, msg = self._require_text(self.inp_code, "Code")
        if not ok:
            return ok, msg
        return self._require_text(self.inp_libelle, "Libellé")

    def get_values(self) -> dict:
        return {
            'code': self.inp_code.text().strip().upper(),
            'libelle': self.inp_libelle.text().strip(),
            'decompte_solde': self.chk_decompte.isChecked(),
            'couleur': self.inp_couleur.text().strip() or '#3498db',
            'actif': self.chk_actif.isChecked()
        }


class TypesAbsenceTab(_ConfigTab):
    COLUMNS = [
        ("ID", "id"), ("Code", "code"), ("Libellé", "libelle"),
        ("Décompte solde", "decompte_solde"), ("Couleur", "couleur"), ("Actif", "actif")
    ]
    BOOL_KEYS = {'decompte_solde', 'actif'}
    DESCRIPTION = "Types d'absence — catégories disponibles lors de la déclaration d'une absence (CP, RTT, maladie…)."
    USAGE = "Module Planning, déclarations d'absence, calcul des soldes de congés"

    def fetch_data(self):
        from domain.services.admin.config_service import TypeAbsenceService
        return TypeAbsenceService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import TypeAbsenceService
        dlg = _TypeAbsenceForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    TypeAbsenceService.update(data['id'], **vals)
                else:
                    TypeAbsenceService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur type absence: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import TypeAbsenceService
        return TypeAbsenceService.delete(record_id)


# ════════════════════════════════════════════════════════════════
#  4. JOURS FÉRIÉS
# ════════════════════════════════════════════════════════════════

class _JourFerieForm(_SimpleFormDialog):
    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier le jour férié" if data else "Nouveau jour férié"
        super().__init__(title, parent)

        self.inp_date = QDateEdit()
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDisplayFormat("dd/MM/yyyy")
        self.inp_date.setDate(QDate.currentDate())
        self.form.addRow("Date *", self.inp_date)

        self.inp_libelle = QLineEdit()
        self.inp_libelle.setPlaceholderText("Ex: 1er Janvier")
        self.form.addRow("Libellé *", self.inp_libelle)

        self.chk_fixe = QCheckBox("Date fixe chaque année")
        self.chk_fixe.setChecked(True)
        self.form.addRow("", self.chk_fixe)

        if data:
            date_val = data.get('date_ferie')
            if date_val:
                if hasattr(date_val, 'year'):
                    self.inp_date.setDate(QDate(date_val.year, date_val.month, date_val.day))
                else:
                    parts = str(date_val).split('-')
                    if len(parts) == 3:
                        self.inp_date.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
            self.inp_libelle.setText(data.get('libelle', ''))
            self.chk_fixe.setChecked(bool(data.get('fixe', True)))

    def validate(self):
        return self._require_text(self.inp_libelle, "Libellé")

    def get_values(self) -> dict:
        qd = self.inp_date.date()
        return {
            'date_ferie': f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}",
            'libelle': self.inp_libelle.text().strip(),
            'fixe': self.chk_fixe.isChecked()
        }


class JoursFeriesTab(_ConfigTab):
    COLUMNS = [
        ("ID", "id"), ("Date", "date_ferie"), ("Libellé", "libelle"), ("Fixe", "fixe")
    ]
    BOOL_KEYS = {'fixe'}
    DATE_KEYS = {'date_ferie'}
    DESCRIPTION = "Jours fériés — dates exclues automatiquement du calcul des jours ouvrés."
    USAGE = "Calcul des évaluations, planning, décompte des absences"

    def fetch_data(self):
        from domain.services.admin.config_service import JoursFeriesService
        return JoursFeriesService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import JoursFeriesService
        dlg = _JourFerieForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    JoursFeriesService.update(data['id'], **vals)
                else:
                    JoursFeriesService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur jour férié: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import JoursFeriesService
        return JoursFeriesService.delete(record_id)


# ════════════════════════════════════════════════════════════════
#  5. COMPÉTENCES CATALOGUE
# ════════════════════════════════════════════════════════════════

class _CompetenceForm(_SimpleFormDialog):
    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier la compétence" if data else "Nouvelle compétence"
        super().__init__(title, parent)
        self.setMinimumWidth(520)

        self.inp_code = QLineEdit()
        self.inp_code.setMaxLength(50)
        self.form.addRow("Code *", self.inp_code)

        self.inp_libelle = QLineEdit()
        self.form.addRow("Libellé *", self.inp_libelle)

        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(70)
        self.form.addRow("Description", self.inp_desc)

        self.inp_categorie = QLineEdit()
        self.form.addRow("Catégorie", self.inp_categorie)

        self.inp_duree = QSpinBox()
        self.inp_duree.setRange(0, 600)
        self.inp_duree.setSuffix(" mois")
        self.inp_duree.setSpecialValueText("Non définie")
        self.form.addRow("Durée validité", self.inp_duree)

        self.chk_actif = QCheckBox("Actif")
        self.chk_actif.setChecked(True)
        self.form.addRow("", self.chk_actif)

        if data:
            self.inp_code.setText(data.get('code', ''))
            self.inp_libelle.setText(data.get('libelle', ''))
            self.inp_desc.setPlainText(data.get('description') or '')
            self.inp_categorie.setText(data.get('categorie') or '')
            duree = data.get('duree_validite_mois')
            self.inp_duree.setValue(int(duree) if duree else 0)
            self.chk_actif.setChecked(bool(data.get('actif', True)))

    def validate(self):
        ok, msg = self._require_text(self.inp_code, "Code")
        if not ok:
            return ok, msg
        return self._require_text(self.inp_libelle, "Libellé")

    def get_values(self) -> dict:
        duree = self.inp_duree.value() if self.inp_duree.value() > 0 else None
        return {
            'code': self.inp_code.text().strip().upper(),
            'libelle': self.inp_libelle.text().strip(),
            'description': self.inp_desc.toPlainText().strip() or None,
            'categorie': self.inp_categorie.text().strip() or None,
            'duree_validite_mois': duree,
            'actif': self.chk_actif.isChecked()
        }


class CompetencesTab(_ConfigTab):
    COLUMNS = [
        ("ID", "id"), ("Code", "code"), ("Libellé", "libelle"),
        ("Catégorie", "categorie"), ("Validité (mois)", "duree_validite_mois"), ("Actif", "actif")
    ]
    BOOL_KEYS = {'actif'}
    DESCRIPTION = "Catalogue de compétences — référentiel des savoir-faire pouvant être attribués au personnel."
    USAGE = "Fiches de formation, suivi des qualifications, exports RH"

    def fetch_data(self):
        from domain.services.admin.config_service import CompetencesCatalogueService
        return CompetencesCatalogueService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import CompetencesCatalogueService
        dlg = _CompetenceForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    CompetencesCatalogueService.update(data['id'], **vals)
                else:
                    CompetencesCatalogueService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur compétence: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import CompetencesCatalogueService
        return CompetencesCatalogueService.delete(record_id)


# ════════════════════════════════════════════════════════════════
#  6. CATÉGORIES DE DOCUMENTS
# ════════════════════════════════════════════════════════════════

class _CategorieDocForm(_SimpleFormDialog):
    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier la catégorie" if data else "Nouvelle catégorie de document"
        super().__init__(title, parent)
        self.setMinimumWidth(520)

        self.inp_nom = QLineEdit()
        self.form.addRow("Nom *", self.inp_nom)

        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(70)
        self.form.addRow("Description", self.inp_desc)

        # Couleur
        couleur_row = QHBoxLayout()
        self.inp_couleur = QLineEdit()
        self.inp_couleur.setMaxLength(7)
        self.inp_couleur.setText('#3b82f6')
        self.inp_couleur.setMaximumWidth(90)
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(30, 24)
        self._color_btn.clicked.connect(self._pick_color)
        couleur_row.addWidget(self.inp_couleur)
        couleur_row.addWidget(self._color_btn)
        couleur_row.addStretch()
        self.form.addRow("Couleur", couleur_row)
        self.inp_couleur.textChanged.connect(self._update_preview)

        self.chk_expiration = QCheckBox("Exige une date d'expiration")
        self.form.addRow("", self.chk_expiration)

        self.inp_ordre = QSpinBox()
        self.inp_ordre.setRange(0, 999)
        self.form.addRow("Ordre d'affichage", self.inp_ordre)

        if data:
            self.inp_nom.setText(data.get('nom', ''))
            self.inp_desc.setPlainText(data.get('description') or '')
            self.inp_couleur.setText(data.get('couleur') or '#3b82f6')
            self.chk_expiration.setChecked(bool(data.get('exige_date_expiration', False)))
            self.inp_ordre.setValue(int(data.get('ordre_affichage') or 0))

        self._update_preview()

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.inp_couleur.text()), self)
        if color.isValid():
            self.inp_couleur.setText(color.name())

    def _update_preview(self):
        c = self.inp_couleur.text()
        try:
            self._color_btn.setStyleSheet(f"background-color: {c}; border: 1px solid #ccc; border-radius: 3px;")
        except Exception:
            pass

    def validate(self):
        return self._require_text(self.inp_nom, "Nom")

    def get_values(self) -> dict:
        return {
            'nom': self.inp_nom.text().strip(),
            'description': self.inp_desc.toPlainText().strip() or None,
            'couleur': self.inp_couleur.text().strip() or '#3b82f6',
            'exige_date_expiration': self.chk_expiration.isChecked(),
            'ordre_affichage': self.inp_ordre.value()
        }


class CategoriesDocsTab(_ConfigTab):
    COLUMNS = [
        ("ID", "id"), ("Nom", "nom"), ("Couleur", "couleur"),
        ("Expiration requise", "exige_date_expiration"), ("Ordre", "ordre_affichage")
    ]
    BOOL_KEYS = {'exige_date_expiration'}
    DESCRIPTION = "Catégories de documents — classement des fichiers attachés au personnel (contrats, diplômes, visites médicales…)."
    USAGE = "Module Documents RH, alertes d'expiration, filtres documentaires"

    def fetch_data(self):
        from domain.services.admin.config_service import CategoriesDocsService
        return CategoriesDocsService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import CategoriesDocsService
        dlg = _CategorieDocForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    CategoriesDocsService.update(data['id'], **vals)
                else:
                    CategoriesDocsService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur catégorie doc: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import CategoriesDocsService
        return CategoriesDocsService.delete(record_id)


# ════════════════════════════════════════════════════════════════
#  7. MOTIFS DE SORTIE
# ════════════════════════════════════════════════════════════════

class _MotifSortieForm(_SimpleFormDialog):
    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier le motif" if data else "Nouveau motif de sortie"
        super().__init__(title, parent)

        self.inp_libelle = QLineEdit()
        self.form.addRow("Libellé *", self.inp_libelle)

        self.chk_actif = QCheckBox("Actif")
        self.chk_actif.setChecked(True)
        self.form.addRow("", self.chk_actif)

        if data:
            self.inp_libelle.setText(data.get('libelle', ''))
            self.chk_actif.setChecked(bool(data.get('actif', True)))

    def validate(self):
        return self._require_text(self.inp_libelle, "Libellé")

    def get_values(self) -> dict:
        return {
            'libelle': self.inp_libelle.text().strip(),
            'actif': self.chk_actif.isChecked()
        }


class MotifsortieTab(_ConfigTab):
    COLUMNS = [("ID", "id"), ("Libellé", "libelle"), ("Actif", "actif")]
    BOOL_KEYS = {'actif'}
    DESCRIPTION = "Motifs de sortie — raisons sélectionnables lors du passage d'une personne en statut INACTIF (démission, fin de contrat, retraite…)."
    USAGE = "Désactivation dans la fiche personnel"

    def fetch_data(self):
        from domain.services.admin.config_service import RefMotifSortieService
        return RefMotifSortieService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import RefMotifSortieService
        dlg = _MotifSortieForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    RefMotifSortieService.update(data['id'], **vals)
                else:
                    RefMotifSortieService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur motif sortie: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import RefMotifSortieService
        return RefMotifSortieService.delete(record_id)


# ════════════════════════════════════════════════════════════════
#  8. TRANCHES D'ÂGE
# ════════════════════════════════════════════════════════════════

class _TrancheAgeForm(_SimpleFormDialog):
    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier la tranche" if data else "Nouvelle tranche d'âge"
        super().__init__(title, parent)

        self.inp_libelle = QLineEdit()
        self.inp_libelle.setPlaceholderText("Ex: 25-34 ans")
        self.form.addRow("Libellé *", self.inp_libelle)

        self.inp_age_min = QSpinBox()
        self.inp_age_min.setRange(0, 120)
        self.form.addRow("Âge minimum *", self.inp_age_min)

        self.inp_age_max = QSpinBox()
        self.inp_age_max.setRange(0, 120)
        self.inp_age_max.setSpecialValueText("Illimité")
        self.form.addRow("Âge maximum", self.inp_age_max)

        if data:
            self.inp_libelle.setText(data.get('libelle', ''))
            self.inp_age_min.setValue(int(data.get('age_min') or 0))
            age_max = data.get('age_max')
            self.inp_age_max.setValue(int(age_max) if age_max else 0)

    def validate(self):
        ok, msg = self._require_text(self.inp_libelle, "Libellé")
        if not ok:
            return ok, msg
        if self.inp_age_max.value() > 0 and self.inp_age_max.value() < self.inp_age_min.value():
            return False, "L'âge maximum doit être supérieur ou égal à l'âge minimum."
        return True, ""

    def get_values(self) -> dict:
        age_max = self.inp_age_max.value() if self.inp_age_max.value() > 0 else None
        return {
            'libelle': self.inp_libelle.text().strip(),
            'age_min': self.inp_age_min.value(),
            'age_max': age_max
        }


class TranchesAgeTab(_ConfigTab):
    COLUMNS = [("ID", "id"), ("Libellé", "libelle"), ("Âge min", "age_min"), ("Âge max", "age_max")]
    DESCRIPTION = "Tranches d'âge — intervalles utilisés pour segmenter les statistiques RH par âge."
    USAGE = "Rapports et statistiques RH, tableaux de bord"

    def _format_cell(self, key, val, record):
        if key == 'age_max' and (val is None or val == 0):
            return '∞'
        return _txt(val)

    def fetch_data(self):
        from domain.services.admin.config_service import TranchesAgeService
        return TranchesAgeService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import TranchesAgeService
        dlg = _TrancheAgeForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    TranchesAgeService.update(data['id'], **vals)
                else:
                    TranchesAgeService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur tranche âge: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import TranchesAgeService
        return TranchesAgeService.delete(record_id)


# ════════════════════════════════════════════════════════════════
#  9. RÔLES
# ════════════════════════════════════════════════════════════════

class _RoleForm(_SimpleFormDialog):
    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier le rôle" if data else "Nouveau rôle"
        super().__init__(title, parent)

        self.inp_nom = QLineEdit()
        self.inp_nom.setMaxLength(50)
        self.inp_nom.setPlaceholderText("Ex: Responsable RH")
        self.form.addRow("Nom *", self.inp_nom)

        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(80)
        self.form.addRow("Description", self.inp_desc)

        if data:
            self.inp_nom.setText(data.get('nom', ''))
            self.inp_desc.setPlainText(data.get('description') or '')

    def validate(self):
        return self._require_text(self.inp_nom, "Nom")

    def get_values(self) -> dict:
        return {
            'nom': self.inp_nom.text().strip(),
            'description': self.inp_desc.toPlainText().strip() or None
        }


class RolesTab(_ConfigTab):
    COLUMNS = [("ID", "id"), ("Nom", "nom"), ("Description", "description")]
    DESCRIPTION = "Rôles utilisateurs — définissent les droits d'accès dans l'application. Chaque utilisateur est assigné à un rôle."
    USAGE = "Gestion des utilisateurs, système de permissions (features), contrôle d'accès"

    def fetch_data(self):
        from domain.services.admin.config_service import RolesConfigService
        return RolesConfigService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import RolesConfigService
        dlg = _RoleForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    RolesConfigService.update(data['id'], **vals)
                else:
                    RolesConfigService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur rôle: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import RolesConfigService
        return RolesConfigService.delete(record_id)


# ════════════════════════════════════════════════════════════════
#  Base : onglet lecture seule
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
        self.btn_refresh = EmacButton("🔄 Actualiser", variant='ghost')
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


# ════════════════════════════════════════════════════════════════
#  10. SOLDE DE CONGÉS
# ════════════════════════════════════════════════════════════════

class _SoldeCongesForm(_SimpleFormDialog):

    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier le solde" if data else "Nouveau solde de congés"
        super().__init__(title, parent)
        self.setMinimumWidth(520)
        self._personnel_map: dict = {}  # label → id

        # Personnel
        self.cmb_personnel = QComboBox()
        self.form.addRow("Personnel *", self.cmb_personnel)

        # Année
        self.inp_annee = QSpinBox()
        self.inp_annee.setRange(2020, 2035)
        self.inp_annee.setValue(QDate.currentDate().year())
        self.form.addRow("Année *", self.inp_annee)

        # CP acquis
        self.inp_cp_acquis = QDoubleSpinBox()
        self.inp_cp_acquis.setRange(0, 60)
        self.inp_cp_acquis.setSingleStep(0.5)
        self.form.addRow("CP acquis", self.inp_cp_acquis)

        # CP N-1
        self.inp_cp_n1 = QDoubleSpinBox()
        self.inp_cp_n1.setRange(0, 60)
        self.inp_cp_n1.setSingleStep(0.5)
        self.form.addRow("CP N-1", self.inp_cp_n1)

        # CP pris
        self.inp_cp_pris = QDoubleSpinBox()
        self.inp_cp_pris.setRange(0, 60)
        self.inp_cp_pris.setSingleStep(0.5)
        self.form.addRow("CP pris", self.inp_cp_pris)

        # RTT acquis
        self.inp_rtt_acquis = QDoubleSpinBox()
        self.inp_rtt_acquis.setRange(0, 60)
        self.inp_rtt_acquis.setSingleStep(0.5)
        self.form.addRow("RTT acquis", self.inp_rtt_acquis)

        # RTT pris
        self.inp_rtt_pris = QDoubleSpinBox()
        self.inp_rtt_pris.setRange(0, 60)
        self.inp_rtt_pris.setSingleStep(0.5)
        self.form.addRow("RTT pris", self.inp_rtt_pris)

        self._load_personnel()

        if data:
            self.inp_annee.setValue(int(data.get('annee') or QDate.currentDate().year()))
            self.inp_cp_acquis.setValue(float(data.get('cp_acquis') or 0))
            self.inp_cp_n1.setValue(float(data.get('cp_n_1') or 0))
            self.inp_cp_pris.setValue(float(data.get('cp_pris') or 0))
            self.inp_rtt_acquis.setValue(float(data.get('rtt_acquis') or 0))
            self.inp_rtt_pris.setValue(float(data.get('rtt_pris') or 0))
            self._data = data
        else:
            self._data = None

    def _load_personnel(self):
        from domain.services.admin.config_service import SoldeCongesService
        try:
            personnel = SoldeCongesService.get_all_personnel()
            self.cmb_personnel.clear()
            self._personnel_map = {}
            for p in personnel:
                label = f"{p['nom']} {p['prenom']}"
                self.cmb_personnel.addItem(label, p['id'])
                self._personnel_map[label] = p['id']
            # Pré-sélectionner si édition
            if self._data:
                pid = self._data.get('personnel_id')
                for i in range(self.cmb_personnel.count()):
                    if self.cmb_personnel.itemData(i) == pid:
                        self.cmb_personnel.setCurrentIndex(i)
                        break
        except Exception as e:
            logger.exception(f"Erreur chargement personnel: {e}")

    def validate(self):
        if self.cmb_personnel.currentIndex() < 0:
            return False, "Veuillez sélectionner un personnel."
        return True, ""

    def get_values(self) -> dict:
        return {
            'personnel_id': self.cmb_personnel.currentData(),
            'annee': self.inp_annee.value(),
            'cp_acquis': self.inp_cp_acquis.value(),
            'cp_n_1': self.inp_cp_n1.value(),
            'cp_pris': self.inp_cp_pris.value(),
            'rtt_acquis': self.inp_rtt_acquis.value(),
            'rtt_pris': self.inp_rtt_pris.value(),
        }


class SoldeCongesTab(_ConfigTab):
    COLUMNS = [
        ("ID", "id"), ("Personnel", "personnel_label"), ("Année", "annee"),
        ("CP acquis", "cp_acquis"), ("CP N-1", "cp_n_1"), ("CP pris", "cp_pris"),
        ("RTT acquis", "rtt_acquis"), ("RTT pris", "rtt_pris"),
    ]
    DESCRIPTION = "Soldes de congés — compteurs annuels de congés payés et RTT par personne."
    USAGE = "Module Absences, validation des demandes de congés, alertes dépassement"

    def _format_cell(self, key, val, record):
        if key == 'personnel_label':
            return f"{record.get('nom', '')} {record.get('prenom', '')}"
        return super()._format_cell(key, val, record)

    def fetch_data(self):
        from domain.services.admin.config_service import SoldeCongesService
        return SoldeCongesService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import SoldeCongesService
        dlg = _SoldeCongesForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    SoldeCongesService.update(data['id'], **vals)
                else:
                    SoldeCongesService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur solde congés: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import SoldeCongesService
        return SoldeCongesService.delete(record_id)

    def _get_display_name(self, record):
        return f"{record.get('nom', '')} {record.get('prenom', '')} — {record.get('annee', '')}"


# ════════════════════════════════════════════════════════════════
#  11. RÈGLES ÉVÉNEMENTS DOCUMENTS
# ════════════════════════════════════════════════════════════════

class _DocumentEventRuleForm(_SimpleFormDialog):

    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier la règle" if data else "Nouvelle règle événement"
        super().__init__(title, parent)
        self.setMinimumWidth(520)

        self.inp_event_name = QLineEdit()
        self.inp_event_name.setPlaceholderText("Ex: CREATION_PERSONNEL")
        self.form.addRow("Événement *", self.inp_event_name)

        self.cmb_template = QComboBox()
        self.form.addRow("Template", self.cmb_template)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(['AUTO', 'PROPOSED', 'SILENT'])
        self.form.addRow("Mode exécution", self.cmb_mode)

        self.inp_priority = QSpinBox()
        self.inp_priority.setRange(0, 100)
        self.form.addRow("Priorité", self.inp_priority)

        self.chk_actif = QCheckBox("Actif")
        self.chk_actif.setChecked(True)
        self.form.addRow("", self.chk_actif)

        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(70)
        self.form.addRow("Description", self.inp_desc)

        self._load_templates()

        if data:
            self.inp_event_name.setText(data.get('event_name', ''))
            mode = data.get('execution_mode', 'AUTO')
            idx = self.cmb_mode.findText(mode)
            if idx >= 0:
                self.cmb_mode.setCurrentIndex(idx)
            self.inp_priority.setValue(int(data.get('priority') or 0))
            self.chk_actif.setChecked(bool(data.get('actif', True)))
            self.inp_desc.setPlainText(data.get('description') or '')
            # template sélectionné après chargement
            self._pending_template_id = data.get('template_id')
        else:
            self._pending_template_id = None

    def _load_templates(self):
        from domain.services.admin.config_service import DocumentEventRulesService
        try:
            templates = DocumentEventRulesService.get_all_templates()
            self.cmb_template.clear()
            self.cmb_template.addItem("— Aucun —", None)
            for t in templates:
                self.cmb_template.addItem(t['nom'], t['id'])
            if self._pending_template_id is not None:
                for i in range(self.cmb_template.count()):
                    if self.cmb_template.itemData(i) == self._pending_template_id:
                        self.cmb_template.setCurrentIndex(i)
                        break
        except Exception as e:
            logger.exception(f"Erreur chargement templates: {e}")

    def validate(self):
        return self._require_text(self.inp_event_name, "Événement")

    def get_values(self) -> dict:
        return {
            'event_name': self.inp_event_name.text().strip(),
            'template_id': self.cmb_template.currentData(),
            'execution_mode': self.cmb_mode.currentText(),
            'priority': self.inp_priority.value(),
            'actif': self.chk_actif.isChecked(),
            'description': self.inp_desc.toPlainText().strip() or None,
        }


class DocumentEventRulesTab(_ConfigTab):
    COLUMNS = [
        ("ID", "id"), ("Événement", "event_name"), ("Template", "template_nom"),
        ("Mode", "execution_mode"), ("Priorité", "priority"), ("Actif", "actif"),
    ]
    BOOL_KEYS = {'actif'}
    DESCRIPTION = "Règles événements/documents — définissent quel template est proposé automatiquement lors d'un événement (création personnel, changement de niveau…)."
    USAGE = "Génération automatique de documents, module Templates"

    def fetch_data(self):
        from domain.services.admin.config_service import DocumentEventRulesService
        return DocumentEventRulesService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import DocumentEventRulesService
        dlg = _DocumentEventRuleForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    DocumentEventRulesService.update(data['id'], **vals)
                else:
                    DocumentEventRulesService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur règle événement: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import DocumentEventRulesService
        return DocumentEventRulesService.delete(record_id)

    def _get_display_name(self, record):
        return record.get('event_name', f"#{record.get('id', '?')}")


# ════════════════════════════════════════════════════════════════
#  12. DEMANDES D'ABSENCE (admin)
# ════════════════════════════════════════════════════════════════

class _UpdateStatutForm(_SimpleFormDialog):
    """Formulaire de mise à jour du statut d'une demande d'absence."""

    def __init__(self, data: dict, parent=None):
        super().__init__("Modifier le statut de la demande", parent)
        self._data = data

        self.cmb_statut = QComboBox()
        self.cmb_statut.addItems(['EN_ATTENTE', 'VALIDEE', 'REFUSEE', 'ANNULEE'])
        current = data.get('statut', 'EN_ATTENTE')
        idx = self.cmb_statut.findText(current)
        if idx >= 0:
            self.cmb_statut.setCurrentIndex(idx)
        self.form.addRow("Statut *", self.cmb_statut)

        self.inp_commentaire = QTextEdit()
        self.inp_commentaire.setMaximumHeight(80)
        self.inp_commentaire.setPlaceholderText("Commentaire de validation (optionnel)")
        self.inp_commentaire.setPlainText(data.get('commentaire_validation') or '')
        self.form.addRow("Commentaire", self.inp_commentaire)

    def get_values(self) -> dict:
        return {
            'statut': self.cmb_statut.currentText(),
            'commentaire': self.inp_commentaire.toPlainText().strip() or None,
        }


class DemandeAbsenceTab(_ConfigTab):
    COLUMNS = [
        ("ID", "id"), ("Personnel", "personnel_label"), ("Type", "type_libelle"),
        ("Début", "date_debut"), ("Fin", "date_fin"), ("Jours", "nb_jours"),
        ("Statut", "statut"), ("Date création", "date_creation"),
    ]
    DATE_KEYS = {'date_debut', 'date_fin', 'date_creation'}
    DESCRIPTION = "Demandes d'absence — toutes les demandes soumises par le personnel, en attente de validation ou traitées."
    USAGE = "Validation RH, planning, soldes de congés"

    def _build_ui(self):
        super()._build_ui()
        # Masquer "Ajouter" — l'admin ne crée pas de demandes
        self.btn_add.setVisible(False)
        # Renommer "Modifier" en "Modifier statut"
        self.btn_edit.setText("✏️ Modifier statut")

    def _format_cell(self, key, val, record):
        if key == 'personnel_label':
            return f"{record.get('nom', '')} {record.get('prenom', '')}"
        return super()._format_cell(key, val, record)

    def fetch_data(self):
        from domain.services.admin.config_service import DemandeAbsenceAdminService
        return DemandeAbsenceAdminService.get_all()

    def show_form(self, data):
        """Appelé pour la modification de statut uniquement."""
        if not data:
            return
        from domain.services.admin.config_service import DemandeAbsenceAdminService
        dlg = _UpdateStatutForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                DemandeAbsenceAdminService.update_statut(
                    data['id'], vals['statut'], vals['commentaire']
                )
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur mise à jour statut: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import DemandeAbsenceAdminService
        return DemandeAbsenceAdminService.delete(record_id)

    def _get_display_name(self, record):
        return (
            f"{record.get('nom', '')} {record.get('prenom', '')} "
            f"— {record.get('type_libelle', '')} "
            f"({record.get('date_debut', '')})"
        )


# ════════════════════════════════════════════════════════════════
#  13. POLYVALENCE (corrections admin)
# ════════════════════════════════════════════════════════════════

class _PolyvalenceAdminForm(_SimpleFormDialog):

    def __init__(self, data: dict, parent=None):
        super().__init__("Corriger l'entrée de polyvalence", parent)
        self._data = data

        # Info contextuelle (lecture seule)
        lbl_ctx = QLabel(
            f"{data.get('nom', '')} {data.get('prenom', '')}  ·  Poste : {data.get('poste_code', '')}"
        )
        lbl_ctx.setStyleSheet("font-weight: bold; color: #444;")
        self._main_layout.insertWidget(2, lbl_ctx)

        self.inp_niveau = QSpinBox()
        self.inp_niveau.setRange(1, 4)
        self.inp_niveau.setValue(int(data.get('niveau') or 1))
        self.form.addRow("Niveau (1-4) *", self.inp_niveau)

        self.inp_date_eval = QDateEdit()
        self.inp_date_eval.setCalendarPopup(True)
        self.inp_date_eval.setDisplayFormat("dd/MM/yyyy")
        self.inp_date_eval.setDate(QDate.currentDate())
        self.form.addRow("Date évaluation *", self.inp_date_eval)

        self.inp_prochaine = QDateEdit()
        self.inp_prochaine.setCalendarPopup(True)
        self.inp_prochaine.setDisplayFormat("dd/MM/yyyy")
        self.inp_prochaine.setDate(QDate.currentDate())
        self.form.addRow("Prochaine évaluation", self.inp_prochaine)

        # Pré-remplissage des dates
        for attr, widget in (
            ('date_evaluation', self.inp_date_eval),
            ('prochaine_evaluation', self.inp_prochaine),
        ):
            val = data.get(attr)
            if val:
                if hasattr(val, 'year'):
                    widget.setDate(QDate(val.year, val.month, val.day))
                else:
                    parts = str(val).split('-')
                    if len(parts) == 3:
                        widget.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))

    def get_values(self) -> dict:
        qd_eval = self.inp_date_eval.date()
        qd_proch = self.inp_prochaine.date()
        return {
            'niveau': self.inp_niveau.value(),
            'date_evaluation': f"{qd_eval.year():04d}-{qd_eval.month():02d}-{qd_eval.day():02d}",
            'prochaine_evaluation': f"{qd_proch.year():04d}-{qd_proch.month():02d}-{qd_proch.day():02d}",
        }


class PolyvalenceAdminTab(_ConfigTab):
    COLUMNS = [
        ("ID", "id"), ("Nom", "nom"), ("Prénom", "prenom"), ("Poste", "poste_code"),
        ("Niveau", "niveau"), ("Date éval", "date_evaluation"),
        ("Prochaine éval", "prochaine_evaluation"),
    ]
    DATE_KEYS = {'date_evaluation', 'prochaine_evaluation'}
    DESCRIPTION = "Polyvalence — correction administrative des entrées de niveaux (200 plus récentes). Utiliser l'interface Évaluations en priorité."
    USAGE = "Grille de polyvalence, tableau de bord évaluations, planning"

    def _build_ui(self):
        super()._build_ui()
        # Désactiver "Ajouter" — passer par l'interface Évaluations
        self.btn_add.setEnabled(False)
        self.btn_add.setToolTip("Utiliser l'interface Évaluations pour ajouter des entrées")

        # Avertissement
        lbl_warn = QLabel("⚠️ Modifications directes — préférer l'interface Évaluations")
        lbl_warn.setStyleSheet(
            "color: #b45309; background: #fef3c7; border: 1px solid #f59e0b; "
            "border-radius: 4px; padding: 6px 10px; font-size: 12px;"
        )
        self.layout().insertWidget(0, lbl_warn)

    def fetch_data(self):
        from domain.services.admin.config_service import PolyvalenceAdminService
        return PolyvalenceAdminService.get_all_recent(200)

    def show_form(self, data):
        if not data:
            return
        from domain.services.admin.config_service import PolyvalenceAdminService
        dlg = _PolyvalenceAdminForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                PolyvalenceAdminService.update(data['id'], **vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur polyvalence admin: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import PolyvalenceAdminService
        return PolyvalenceAdminService.delete(record_id)

    def _get_display_name(self, record):
        return (
            f"{record.get('nom', '')} {record.get('prenom', '')} "
            f"— {record.get('poste_code', '')}"
        )


# ════════════════════════════════════════════════════════════════
#  14. HISTORIQUE (lecture seule)
# ════════════════════════════════════════════════════════════════

class HistoriqueAdminTab(_ReadOnlyTab):
    INFO_LABEL = "Affichage des 100 dernières entrées (lecture seule)"
    COLUMNS = [
        ("ID", "id"), ("Date/Heure", "date_time"), ("Action", "action"),
        ("Table", "table_name"), ("Utilisateur", "utilisateur"), ("Description", "description"),
    ]
    DATETIME_KEYS = {'date_time'}

    def fetch_data(self):
        from domain.services.admin.config_service import HistoriqueAdminService
        return HistoriqueAdminService.get_recent(100)


# ════════════════════════════════════════════════════════════════
#  15. LOGS DE CONNEXION (lecture seule)
# ════════════════════════════════════════════════════════════════

class LogsConnexionTab(_ReadOnlyTab):
    INFO_LABEL = "Affichage des 50 dernières connexions (lecture seule)"
    COLUMNS = [
        ("ID", "id"), ("Utilisateur", "username"), ("Connexion", "date_connexion"),
        ("Déconnexion", "date_deconnexion"), ("IP", "ip_address"),
    ]
    DATETIME_KEYS = {'date_connexion', 'date_deconnexion'}

    def fetch_data(self):
        from domain.services.admin.config_service import LogsConnexionService
        return LogsConnexionService.get_recent(50)


# ════════════════════════════════════════════════════════════════
#  Dialog principal
# ════════════════════════════════════════════════════════════════

class AdminDataPanelDialog(QDialog):
    """
    Panel d'administration des données de référence.
    Accessible aux administrateurs uniquement.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Vérification des droits admin (fresh check en DB)
        from domain.services.admin.auth_service import is_admin
        if not is_admin():
            QMessageBox.critical(
                self, "Accès refusé",
                "Seuls les administrateurs peuvent accéder à cette fonctionnalité."
            )
            # On ferme immédiatement après l'affichage du message
            QTimer.singleShot(0, self.reject)
            return

        self.setWindowTitle("Administration — Paramètres de l'application")
        self.setMinimumSize(1100, 680)
        self.setModal(True)

        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── En-tête coloré ────────────────────────────────────────
        hdr = QWidget()
        hdr.setStyleSheet("background: #1b2f4e;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(24, 14, 20, 14)
        hdr_lay.setSpacing(10)

        ttl = QLabel("Administration — Paramètres de l'application")
        ttl.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        hdr_lay.addWidget(ttl)

        hdr_lay.addSpacing(16)
        sub = QLabel("· Modifications tracées dans l'historique")
        sub.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px;")
        hdr_lay.addWidget(sub)

        hdr_lay.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close.setStyleSheet(
            "color: white; background: rgba(255,255,255,0.15); "
            "border: 1px solid rgba(255,255,255,0.3); border-radius: 6px; "
            "padding: 6px 18px; font-size: 12px;"
        )
        btn_close.clicked.connect(self.accept)
        hdr_lay.addWidget(btn_close)
        outer.addWidget(hdr)

        # ── Corps : sidebar + contenu ──────────────────────────────
        body = QHBoxLayout()
        body.setSpacing(0)
        body.setContentsMargins(0, 0, 0, 0)

        # -- Sidebar --
        self._nav = QListWidget()
        self._nav.setFixedWidth(200)
        self._nav.setStyleSheet("""
            QListWidget {
                background: #f5f6f8;
                border: none;
                border-right: 1px solid #dde0e6;
                outline: none;
                padding: 8px 0;
            }
            QListWidget::item {
                padding: 8px 0 8px 22px;
                color: #374151;
                font-size: 12px;
                border: none;
            }
            QListWidget::item:selected {
                background: #dbeafe;
                color: #1e40af;
                font-weight: 600;
                border-left: 3px solid #2563eb;
                padding-left: 19px;
            }
            QListWidget::item:hover:!selected {
                background: #eceef2;
            }
        """)

        # -- Stack --
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: white;")

        # -- Construction nav + stack avec groupes thématiques --
        self._factories = {}     # nav_row → factory fn
        self._nav_widgets = {}   # nav_row → widget dans le stack (placeholder ou réel)
        self._created = set()    # nav_rows dont le widget est déjà instancié

        _GROUPS = [
            ("RH", [
                ("Ateliers",           lambda: AteliersTab()),
                ("Services",           lambda: ServicesTab()),
                ("Tranches d'âge",     lambda: TranchesAgeTab()),
                ("Motifs de sortie",   lambda: MotifsortieTab()),
            ]),
            ("Absences", [
                ("Types d'absence",    lambda: TypesAbsenceTab()),
                ("Jours fériés",       lambda: JoursFeriesTab()),
                ("Soldes de congés",   lambda: SoldeCongesTab()),
                ("Demandes",           lambda: DemandeAbsenceTab()),
            ]),
            ("Production", [
                ("Compétences",        lambda: CompetencesTab()),
                ("Polyvalence",        lambda: PolyvalenceAdminTab()),
            ]),
            ("Documents", [
                ("Catégories",         lambda: CategoriesDocsTab()),
                ("Règles événements",  lambda: DocumentEventRulesTab()),
            ]),
            ("Système", [
                ("Rôles",              lambda: RolesTab()),
                ("Historique",         lambda: HistoriqueAdminTab()),
                ("Logs connexion",     lambda: LogsConnexionTab()),
            ]),
        ]

        # widget_key → nav_row (pour les badges)
        self._widget_to_nav_row: dict = {}

        first_nav_row = None
        for group_label, items in _GROUPS:
            # En-tête de groupe (non sélectionnable)
            h_item = QListWidgetItem(group_label.upper())
            h_item.setFlags(Qt.NoItemFlags)
            h_item.setForeground(QColor("#9ca3af"))
            fnt = QFont()
            fnt.setPointSize(8)
            fnt.setBold(True)
            h_item.setFont(fnt)
            self._nav.addItem(h_item)

            for label, factory in items:
                nav_row = self._nav.count()
                self._nav.addItem(QListWidgetItem("  " + label))
                self._factories[nav_row] = factory
                # Placeholder dans le stack
                ph = QWidget()
                ph.setStyleSheet("background: white;")
                self._stack.addWidget(ph)
                self._nav_widgets[nav_row] = ph
                if first_nav_row is None:
                    first_nav_row = nav_row

            # Petit espacement visuel entre groupes
            spacer_item = QListWidgetItem()
            spacer_item.setFlags(Qt.NoItemFlags)
            spacer_item.setSizeHint(spacer_item.sizeHint().__class__(0, 6))
            self._nav.addItem(spacer_item)

        self._nav.currentRowChanged.connect(self._on_nav_changed)

        body.addWidget(self._nav)
        body.addWidget(self._stack, 1)
        outer.addLayout(body)

        # Sélection du premier élément
        if first_nav_row is not None:
            self._nav.setCurrentRow(first_nav_row)

    def _update_nav_badge(self, widget, count: int):
        """Met à jour le badge de comptage dans la sidebar pour un onglet donné."""
        for nav_row, w in self._nav_widgets.items():
            if w is widget:
                item = self._nav.item(nav_row)
                if item is None:
                    return
                text = item.text().strip()
                # Retirer un éventuel badge précédent (format "Label  [N]")
                if '  [' in text:
                    text = text[:text.index('  [')]
                item.setText(f"  {text.strip()}  [{count}]")
                break

    def _on_nav_changed(self, nav_row: int):
        if nav_row not in self._factories:
            return
        if nav_row not in self._created:
            new_widget = self._factories[nav_row]()
            old = self._nav_widgets[nav_row]
            idx = self._stack.indexOf(old)
            self._stack.insertWidget(idx, new_widget)
            self._stack.removeWidget(old)
            old.deleteLater()
            self._nav_widgets[nav_row] = new_widget
            self._created.add(nav_row)
        self._stack.setCurrentWidget(self._nav_widgets[nav_row])
