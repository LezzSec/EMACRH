# -*- coding: utf-8 -*-
"""
Onglets de configuration production : Compétences catalogue, Polyvalence (admin).
"""

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QTextEdit, QCheckBox, QSpinBox,
    QDateEdit, QMessageBox
)
from PyQt5.QtCore import QDate

from infrastructure.logging.logging_config import get_logger
from .base import _ConfigTab, _SimpleFormDialog

logger = get_logger(__name__)


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
        lbl_warn = QLabel("Modifications directes — préférer l'interface Évaluations")
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
