# -*- coding: utf-8 -*-
import time

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QHBoxLayout, QListWidgetItem

from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date
from gui.workers.db_worker import DbWorker, DbThreadPool
from gui.main_qt._shared import get_theme_components

logger = get_logger(__name__)


class DashboardMixin:
    """Chargement async des données du dashboard principal."""

    # --- User + Permissions ---

    def load_user_and_permissions_async(self):
        w = DbWorker(self._fetch_user_and_perms)
        w.signals.result.connect(self._apply_user_and_perms)
        w.signals.error.connect(self._on_bg_error)
        DbThreadPool.start(w)

    def _fetch_user_and_perms(self, progress_callback=None):
        from gui.main_qt._shared import _lazy_auth
        auth = _lazy_auth()
        current_user = auth.get_current_user()

        from application.permission_manager import can
        perms = {
            "grilles_lecture": can('production.grilles.view'),
            "evaluations_lecture": can('production.evaluations.view'),
            "personnel_ecriture": can('rh.personnel.edit'),
            "personnel_lecture": can('rh.personnel.view'),
            "postes_ecriture": can('production.postes.edit'),
            "contrats_lecture": can('rh.contrats.view'),
            "contrats_ecriture": can('rh.contrats.edit'),
            "documentsrh_lecture": can('rh.documents.view'),
            "documentsrh_ecriture": can('rh.documents.edit'),
            "planning_lecture": can('planning.view'),
            "historique_lecture": can('admin.historique.view'),
            "is_admin": auth.is_admin(),
        }

        try:
            from domain.services.admin.module_service import get_enabled_codes
            enabled_modules = get_enabled_codes()
        except Exception:
            enabled_modules = {"rh", "production", "planning", "documents", "historique"}

        return {"user": current_user, "perms": perms, "enabled_modules": enabled_modules}

    def _apply_user_and_perms(self, payload):
        user = payload.get("user")
        perms = payload.get("perms", {})

        if user:
            user_text = f"{user.get('prenom','')} {user.get('nom','')} - {user.get('role_nom','')}"
            self.user_info.setText(user_text)
        else:
            self.user_info.setText("Non connecté")

        EmacButton = get_theme_components()['EmacButton']

        insert_idx = 1  # 0 = Liste du Personnel, dernier = Quitter

        if perms.get("contrats_lecture"):
            r_rh = QHBoxLayout()
            b_rh = EmacButton("Gestion RH", 'ghost')
            b_rh.clicked.connect(self.show_contract_management)
            r_rh.addWidget(b_rh)
            self.rows.insertLayout(insert_idx, r_rh)
            insert_idx += 1

        if perms.get("grilles_lecture"):
            r2 = QHBoxLayout()
            b2 = EmacButton("Liste et Grilles", 'ghost')
            b2.clicked.connect(self.show_listes_grilles_dialog)
            r2.addWidget(b2)
            self.rows.insertLayout(insert_idx, r2)
            insert_idx += 1

        if perms.get("evaluations_lecture"):
            r3 = QHBoxLayout()
            b3 = EmacButton("Gestion des Évaluations", 'ghost')
            b3.clicked.connect(self.show_gestion_evaluations)
            r3.addWidget(b3)
            self.rows.insertLayout(insert_idx, r3)
            insert_idx += 1

        has_production_access = perms.get("evaluations_lecture")
        self.retard_card.setVisible(has_production_access)
        self.next_card.setVisible(has_production_access)
        if has_production_access:
            self.load_evaluations_async()

        has_rh_access = perms.get("contrats_ecriture") or perms.get("documentsrh_ecriture")
        self.alertes_rh_card.setVisible(has_rh_access)
        if has_rh_access:
            self.load_alertes_rh_async()

        self._perms_cache = perms
        self._modules_cache = payload.get("enabled_modules", {"rh", "production", "planning", "documents", "historique"})

        if self.drawer is not None:
            self.drawer.deleteLater()
            self.drawer = None

        if has_rh_access:
            QTimer.singleShot(1500, self._load_notification_counts)

    # --- Postes filter ---

    def populate_filters_async(self):
        w = DbWorker(self._fetch_postes_cached)
        w.signals.result.connect(self._apply_postes_to_filters)
        w.signals.error.connect(self._on_bg_error)
        DbThreadPool.start(w)

    def _fetch_postes_cached(self, progress_callback=None):
        if self._postes_cache is not None and self._postes_cache_time is not None:
            if (time.time() - self._postes_cache_time) < 300:
                return self._postes_cache

        from domain.repositories.poste_repo import PosteRepository
        codes = PosteRepository.get_codes_list()
        postes = [(code,) for code in codes]
        self._postes_cache = postes
        self._postes_cache_time = time.time()
        return postes

    def _apply_postes_to_filters(self, postes):
        try:
            for (poste,) in postes:
                if self.retard_filter.findData(poste) == -1:
                    self.retard_filter.addItem(poste, poste)
                if self.next_eval_filter.findData(poste) == -1:
                    self.next_eval_filter.addItem(poste, poste)
        except Exception as e:
            logger.warning(f"Erreur apply filtres: {e}")

    # --- Evaluations ---

    def load_evaluations_async(self):
        poste_retard = self.retard_filter.currentData()
        poste_next = self.next_eval_filter.currentData()
        w = DbWorker(self._fetch_evaluations, poste_retard, poste_next)
        w.signals.result.connect(self._apply_evaluations_to_ui)
        w.signals.error.connect(self._on_bg_error)
        DbThreadPool.start(w)

    def _fetch_evaluations(self, poste_retard, poste_next, progress_callback=None):
        from domain.repositories.polyvalence_repo import PolyvalenceRepository
        try:
            retard = PolyvalenceRepository.get_en_retard_filtre(
                poste_code=poste_retard or None, limit=10
            )
            prochaines = PolyvalenceRepository.get_a_venir_filtre(
                jours=30, poste_code=poste_next or None, limit=10
            )
            return {"retard": retard, "prochaines": prochaines}
        except Exception as e:
            logger.error(f"Erreur dans _fetch_evaluations: {e}", exc_info=True)
            raise

    def _apply_evaluations_to_ui(self, payload):
        try:
            retard = payload.get("retard", [])
            prochaines = payload.get("prochaines", [])

            self.retard_list.clear()
            for r in retard:
                date_ev = r.get('prochaine_evaluation')
                date_txt = format_date(date_ev) if hasattr(date_ev, 'strftime') else str(date_ev)
                self.retard_list.addItem(
                    f"{r.get('nom','')} {r.get('prenom','')} · {r.get('poste_code','')}  —  Retard: {date_txt}"
                )

            self.next_eval_list.clear()
            for r in prochaines:
                date_ev = r.get('prochaine_evaluation')
                date_txt = format_date(date_ev) if hasattr(date_ev, 'strftime') else str(date_ev)
                self.next_eval_list.addItem(
                    f"{r.get('nom','')} {r.get('prenom','')} · {r.get('poste_code','')}  —  Prévu: {date_txt}"
                )
        except Exception as e:
            logger.error(f"Erreur dans _apply_evaluations_to_ui: {e}", exc_info=True)

    # --- Alertes RH ---

    def load_alertes_rh_async(self):
        type_contrat = self.alertes_rh_filter.currentData() if hasattr(self, 'alertes_rh_filter') else ""
        w = DbWorker(self._fetch_alertes_rh, type_contrat)
        w.signals.result.connect(self._apply_alertes_rh_to_ui)
        w.signals.error.connect(self._on_bg_error)
        DbThreadPool.start(w)

    def _fetch_alertes_rh(self, type_doc_filter, progress_callback=None):
        from domain.services.admin.alert_service import AlertService
        try:
            alertes = AlertService.get_all_document_alerts(type_doc=type_doc_filter or None, jours=30)
            return {"alertes": alertes}
        except Exception as e:
            logger.error(f"Erreur dans _fetch_alertes_rh: {e}", exc_info=True)
            raise

    def _apply_alertes_rh_to_ui(self, payload):
        _CAT_LABELS = {
            "CONTRAT": "Contrat",
            "PERSONNEL": "Sans contrat",
            "VISITE_MEDICALE": "Visite médicale",
            "RQTH": "RQTH",
            "ENTRETIEN": "Entretien",
            "MUTUELLE": "Mutuelle",
            "SANS_MUTUELLE": "Sans mutuelle",
            "SANS_VISITE": "Sans visite médicale",
            "SANS_ENTRETIEN": "Sans entretien",
        }
        try:
            alertes = payload.get("alertes", [])
            self.alertes_rh_list.clear()
            for a in alertes:
                date_txt = ""
                if a.date_echeance:
                    date_txt = format_date(a.date_echeance) if hasattr(a.date_echeance, 'strftime') else str(a.date_echeance)
                    date_txt = f"  —  {date_txt}"
                cat = _CAT_LABELS.get(a.categorie, a.categorie)
                label = f"{a.personnel_prenom} {a.personnel_nom}  [{cat}]  {a.description}{date_txt}"
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, a.personnel_id)
                self.alertes_rh_list.addItem(item)
            if not alertes:
                self.alertes_rh_list.addItem("Aucun document à renouveler")
        except Exception as e:
            logger.error(f"Erreur dans _apply_alertes_rh_to_ui: {e}", exc_info=True)

    def _on_alerte_rh_double_click(self, item):
        personnel_id = item.data(Qt.UserRole)
        if not personnel_id:
            return
        from gui.screens.rh.gestion_rh_dialog import GestionRHDialog
        dialog = GestionRHDialog(self, preselect_personnel_id=personnel_id)
        dialog.data_changed.connect(self.load_evaluations_async)
        dialog.data_changed.connect(self.load_alertes_rh_async)
        dialog.exec_()
