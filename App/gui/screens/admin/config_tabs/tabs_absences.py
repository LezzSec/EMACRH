# -*- coding: utf-8 -*-
"""
Onglets de configuration absences : Types d'absence, Jours fériés, Soldes de congés,
Demandes d'absence (admin).
"""

from PyQt5.QtWidgets import (
    QDialog, QLineEdit, QTextEdit, QCheckBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QDateEdit, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog

from infrastructure.logging.logging_config import get_logger
from .base import _ConfigTab, _SimpleFormDialog

logger = get_logger(__name__)


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
        self.btn_edit.setText("Modifier statut")

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
