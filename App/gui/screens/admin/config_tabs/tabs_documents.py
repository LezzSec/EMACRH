# -*- coding: utf-8 -*-
"""
Onglets de configuration documents : Catégories de documents, Règles événements/documents.
"""

from PyQt5.QtWidgets import (
    QDialog, QLineEdit, QTextEdit, QCheckBox, QSpinBox, QComboBox,
    QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog

from infrastructure.logging.logging_config import get_logger
from .base import _ConfigTab, _SimpleFormDialog

logger = get_logger(__name__)


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
