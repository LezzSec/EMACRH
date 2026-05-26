# -*- coding: utf-8 -*-
"""
Onglets de configuration production : Compétences catalogue, Polyvalence (admin).
"""

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QSpinBox,
    QDateEdit, QMessageBox, QHBoxLayout,
)
from PyQt5.QtCore import QDate

from gui.components.ui_theme import EmacButton
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
#  6. NIVEAUX DE POLYVALENCE
# ════════════════════════════════════════════════════════════════

class _NiveauPolyvalenceForm(_SimpleFormDialog):

    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier le niveau" if data else "Nouveau niveau de polyvalence"
        super().__init__(title, parent)
        self.setMinimumWidth(520)

        self.inp_nom = QLineEdit()
        self.inp_nom.setMaxLength(100)
        self.form.addRow("Nom *", self.inp_nom)

        self.inp_code = QSpinBox()
        self.inp_code.setRange(1, 999)
        self.form.addRow("Code numérique *", self.inp_code)

        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(60)
        self.form.addRow("Description", self.inp_desc)

        self.inp_frequence = QSpinBox()
        self.inp_frequence.setRange(1, 36500)
        self.inp_frequence.setSuffix(" jours")
        self.form.addRow("Fréquence évaluation *", self.inp_frequence)

        self.inp_ordre = QSpinBox()
        self.inp_ordre.setRange(1, 999)
        self.form.addRow("Ordre d'affichage *", self.inp_ordre)

        self.inp_couleur = QLineEdit()
        self.inp_couleur.setMaxLength(7)
        self.inp_couleur.setPlaceholderText("#rrggbb")
        self.form.addRow("Couleur (hex)", self.inp_couleur)

        self.inp_evenement = QLineEdit()
        self.inp_evenement.setMaxLength(100)
        self.inp_evenement.setPlaceholderText("polyvalence.niveau_X_reached")
        self.form.addRow("Nom événement", self.inp_evenement)

        if data:
            self.inp_nom.setText(data.get('nom', ''))
            self.inp_code.setValue(int(data.get('code') or 1))
            self.inp_desc.setPlainText(data.get('description') or '')
            self.inp_frequence.setValue(int(data.get('frequence_evaluation_jours') or 30))
            self.inp_ordre.setValue(int(data.get('ordre') or 1))
            self.inp_couleur.setText(data.get('couleur') or '')
            self.inp_evenement.setText(data.get('nom_evenement') or '')

    def validate(self):
        return self._require_text(self.inp_nom, "Nom")

    def get_values(self) -> dict:
        return {
            'nom': self.inp_nom.text().strip(),
            'code': self.inp_code.value(),
            'description': self.inp_desc.toPlainText().strip() or None,
            'frequence_evaluation_jours': self.inp_frequence.value(),
            'ordre': self.inp_ordre.value(),
            'couleur': self.inp_couleur.text().strip() or None,
            'nom_evenement': self.inp_evenement.text().strip() or None,
        }


class NiveauxPolyvalenceTab(_ConfigTab):
    COLUMNS = [
        ("Code", "code"), ("Nom", "nom"), ("Fréq. (j)", "frequence_evaluation_jours"),
        ("Ordre", "ordre"), ("Couleur", "couleur"), ("Événement", "nom_evenement"), ("Actif", "actif"),
    ]
    BOOL_KEYS = {'actif'}
    DESCRIPTION = "Niveaux de polyvalence — référentiel des degrés de maîtrise (Apprentissage, Autonome, etc.)."
    USAGE = "Évaluations, grille de polyvalence, documents événementiels"

    def _build_ui(self):
        self._all_records = []
        super()._build_ui()

        # Remplacer "Supprimer" par "Désactiver" + ajouter "Réactiver"
        self.btn_del.setText("Désactiver")
        self.btn_del.setToolTip("Désactive le niveau sélectionné (conserve l'historique)")

        btn_bar = self.layout().itemAt(1).layout()
        self.btn_reactivate = EmacButton("Réactiver", variant='ghost')
        self.btn_reactivate.clicked.connect(self._on_reactivate)
        self.btn_reactivate.setEnabled(False)
        self.btn_reactivate.setToolTip("Sélectionnez un niveau inactif pour le réactiver")
        btn_bar.insertWidget(3, self.btn_reactivate)

        # Toggle affichage inactifs — inséré avant le stretch (index 4)
        self._chk_inactifs = QCheckBox("Afficher les inactifs")
        self._chk_inactifs.setStyleSheet("color: #6b7280; font-size: 12px;")
        self._chk_inactifs.toggled.connect(self._apply_filter_ui)
        btn_bar.insertWidget(4, self._chk_inactifs)

    def _on_data_loaded(self, records: list):
        self._all_records = records or []
        self._apply_filter_ui()
        self.btn_refresh.setEnabled(True)
        self._emit_count(len(self._records))

    def _apply_filter_ui(self):
        show_inactive = self._chk_inactifs.isChecked()
        self._records = self._all_records if show_inactive else [
            r for r in self._all_records if r.get('actif')
        ]
        self._populate_table(self._records)
        n = len(self._records)
        hidden = len(self._all_records) - n
        suffix = f"  ({hidden} inactif(s) masqué(s) — cochez 'Afficher les inactifs')" if hidden else ""
        self.lbl_status.setText(
            f"{n} niveau(x){suffix}  —  Cliquez sur une ligne pour activer Modifier / Désactiver"
        )

    def _on_selection_changed(self):
        rec = self._get_selected_record()
        has_sel = rec is not None
        is_inactive = has_sel and not rec.get('actif')
        self.btn_edit.setEnabled(has_sel)
        self.btn_del.setEnabled(has_sel and not is_inactive)
        self.btn_reactivate.setEnabled(is_inactive)

    def _on_delete(self):
        rec = self._get_selected_record()
        if not rec:
            return
        from domain.services.admin.config_service import NiveauPolyvalenceService
        count = NiveauPolyvalenceService.count_polyvalences_using(rec['id'])
        msg = f"Désactiver le niveau « {rec.get('nom', '')} » ?\n\n"
        if count > 0:
            msg += f"{count} polyvalence(s) en cours utilisent ce niveau.\n"
            msg += "Elles seront conservées mais ce niveau ne pourra plus être attribué.\n\n"
        msg += "Cette action est réversible via le bouton « Réactiver »."
        reply = QMessageBox.question(
            self, "Confirmer la désactivation", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        ok, err_msg = self.delete_record(rec['id'])
        if ok:
            self._load_async()
        else:
            QMessageBox.warning(self, "Désactivation impossible", err_msg)

    def fetch_data(self):
        from domain.services.admin.config_service import NiveauPolyvalenceService
        return NiveauPolyvalenceService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import NiveauPolyvalenceService
        dlg = _NiveauPolyvalenceForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    NiveauPolyvalenceService.update(data['id'], **vals)
                else:
                    NiveauPolyvalenceService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur niveau polyvalence: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import NiveauPolyvalenceService
        return NiveauPolyvalenceService.deactivate(record_id)

    def _on_reactivate(self):
        rec = self._get_selected_record()
        if not rec:
            return
        from domain.services.admin.config_service import NiveauPolyvalenceService
        try:
            NiveauPolyvalenceService.reactivate(rec['id'])
            self._load_async()
        except Exception as e:
            logger.exception(f"Erreur réactivation niveau: {e}")
            QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def _get_display_name(self, record):
        return record.get('nom') or f"#{record.get('id', '?')}"


# ════════════════════════════════════════════════════════════════
#  7. POSTES
# ════════════════════════════════════════════════════════════════

class _PosteForm(_SimpleFormDialog):

    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier le poste" if data else "Nouveau poste"
        super().__init__(title, parent)
        self.setMinimumWidth(420)

        self.inp_code = QLineEdit()
        self.inp_code.setMaxLength(20)
        self.inp_code.setPlaceholderText("Ex: 0506")
        self.form.addRow("Code *", self.inp_code)

        self.cmb_atelier = QComboBox()
        self.cmb_atelier.addItem("— Aucun atelier —", None)
        try:
            from domain.services.admin.config_service import AtelierService
            for a in AtelierService.get_all():
                self.cmb_atelier.addItem(a['nom'], a['id'])
        except Exception:
            pass
        self.form.addRow("Atelier", self.cmb_atelier)

        self.inp_besoin = QSpinBox()
        self.inp_besoin.setRange(0, 99)
        self.inp_besoin.setSuffix(" opérateur(s)")
        self.form.addRow("Besoin effectif", self.inp_besoin)

        if data:
            self.inp_code.setText(data.get('poste_code', ''))
            atelier_id = data.get('atelier_id')
            if atelier_id is not None:
                idx = self.cmb_atelier.findData(atelier_id)
                if idx >= 0:
                    self.cmb_atelier.setCurrentIndex(idx)
            self.inp_besoin.setValue(int(data.get('besoins_postes') or 0))

    def validate(self):
        return self._require_text(self.inp_code, "Code")

    def get_values(self) -> dict:
        return {
            'poste_code': self.inp_code.text().strip().upper(),
            'atelier_id': self.cmb_atelier.currentData(),
            'besoins_postes': self.inp_besoin.value(),
        }


class PostesTab(_ConfigTab):
    COLUMNS = [
        ("Code", "poste_code"), ("Atelier", "atelier_nom"),
        ("Besoin", "besoins_postes"), ("Visible", "visible"),
    ]
    BOOL_KEYS = {'visible'}
    DESCRIPTION = "Postes de travail — référentiel des postes de production utilisés dans les grilles de polyvalence."
    USAGE = "Grilles de polyvalence, évaluations, planning, documents"

    def _build_ui(self):
        self._all_records = []
        super()._build_ui()

        self.btn_del.setText("Désactiver")
        self.btn_del.setToolTip("Masque le poste sans supprimer l'historique de polyvalence")

        btn_bar = self.layout().itemAt(1).layout()
        self.btn_reactivate = EmacButton("Réactiver", variant='ghost')
        self.btn_reactivate.clicked.connect(self._on_reactivate)
        self.btn_reactivate.setEnabled(False)
        self.btn_reactivate.setToolTip("Sélectionnez un poste masqué pour le réactiver")
        btn_bar.insertWidget(3, self.btn_reactivate)

        self._chk_invisibles = QCheckBox("Afficher les masqués")
        self._chk_invisibles.setStyleSheet("color: #6b7280; font-size: 12px;")
        self._chk_invisibles.toggled.connect(self._apply_filter_ui)
        btn_bar.insertWidget(4, self._chk_invisibles)

    def _on_data_loaded(self, records: list):
        self._all_records = records or []
        self._apply_filter_ui()
        self.btn_refresh.setEnabled(True)
        self._emit_count(len(self._records))

    def _apply_filter_ui(self):
        show_invisible = self._chk_invisibles.isChecked()
        self._records = self._all_records if show_invisible else [
            r for r in self._all_records if r.get('visible')
        ]
        self._populate_table(self._records)
        n = len(self._records)
        hidden = len(self._all_records) - n
        suffix = f"  ({hidden} masqué(s) — cochez 'Afficher les masqués')" if hidden else ""
        self.lbl_status.setText(
            f"{n} poste(s){suffix}  —  Cliquez sur une ligne pour activer Modifier / Désactiver"
        )

    def _on_selection_changed(self):
        rec = self._get_selected_record()
        has_sel = rec is not None
        is_invisible = has_sel and not rec.get('visible')
        self.btn_edit.setEnabled(has_sel)
        self.btn_del.setEnabled(has_sel and not is_invisible)
        self.btn_reactivate.setEnabled(is_invisible)

    def _on_delete(self):
        rec = self._get_selected_record()
        if not rec:
            return
        from domain.services.admin.config_service import PostesService
        count = PostesService.count_polyvalences_using(rec['id'])
        msg = f"Désactiver (masquer) le poste « {rec.get('poste_code', '')} » ?\n\n"
        if count > 0:
            msg += f"{count} entrée(s) de polyvalence sont liées à ce poste.\n"
            msg += "Elles seront conservées mais le poste disparaîtra des listes et grilles.\n\n"
        msg += "Cette action est réversible via le bouton « Réactiver »."
        reply = QMessageBox.question(
            self, "Confirmer la désactivation", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        ok, err_msg = self.delete_record(rec['id'])
        if ok:
            self._load_async()
        else:
            QMessageBox.warning(self, "Désactivation impossible", err_msg)

    def fetch_data(self):
        from domain.services.admin.config_service import PostesService
        return PostesService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import PostesService
        dlg = _PosteForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    PostesService.update(data['id'], **vals)
                else:
                    ok, msg, _ = PostesService.create(**vals)
                    if not ok:
                        QMessageBox.warning(self, "Impossible de créer", msg)
                        return
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur poste: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import PostesService
        return PostesService.deactivate(record_id)

    def _on_reactivate(self):
        rec = self._get_selected_record()
        if not rec:
            return
        from domain.services.admin.config_service import PostesService
        try:
            PostesService.reactivate(rec['id'])
            self._load_async()
        except Exception as e:
            logger.exception(f"Erreur réactivation poste: {e}")
            QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def _get_display_name(self, record):
        return record.get('poste_code') or f"#{record.get('id', '?')}"


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
