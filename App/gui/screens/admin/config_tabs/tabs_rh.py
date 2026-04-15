# -*- coding: utf-8 -*-
"""
Onglets de configuration RH : Ateliers, Services, Tranches d'âge, Motifs de sortie.
"""

from PyQt5.QtWidgets import (
    QDialog, QLineEdit, QTextEdit, QCheckBox, QSpinBox, QMessageBox
)

from infrastructure.logging.logging_config import get_logger
from .base import _ConfigTab, _SimpleFormDialog, _txt

logger = get_logger(__name__)


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
