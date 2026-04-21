# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QScrollArea, QListWidget, QMessageBox

from infrastructure.logging.logging_config import get_logger
from gui.components.emac_ui_kit import show_error_message

logger = get_logger(__name__)


class NavigationMixin:
    """Méthodes d'ouverture des dialogs de l'application."""

    def create_scrollable_list(self):
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        lw = QListWidget()
        sc.setWidget(lw)
        return sc, lw

    def show_liste_personnel(self):
        from gui.screens.personnel.gestion_personnel import GestionPersonnelDialog
        dialog = GestionPersonnelDialog(self)
        dialog.data_changed.connect(self.load_evaluations_async)
        dialog.exec_()

    def show_manage_operator(self):
        from gui.screens.personnel.manage_operateur import ManageOperatorsDialog
        dialog = ManageOperatorsDialog()
        dialog.data_changed.connect(lambda _: self.load_evaluations_async())
        dialog.exec_()

    def show_gestion_evaluations(self):
        try:
            from gui.screens.formation.gestion_evaluation import GestionEvaluationDialog
            GestionEvaluationDialog().exec_()
        except Exception as e:
            logger.exception(f"show_gestion_evaluations: {e}")
            show_error_message(self, "Erreur", "Impossible d'ouvrir la gestion des évaluations.", e)

    def ouvrir_gestion_evaluations(self, filtre_statut):
        try:
            from gui.screens.formation.gestion_evaluation import GestionEvaluationDialog
            dialog = GestionEvaluationDialog()
            if hasattr(dialog, 'status_filter'):
                index = dialog.status_filter.findText(filtre_statut)
                if index >= 0:
                    dialog.status_filter.setCurrentIndex(index)
            dialog.exec_()
            self.load_evaluations_async()
        except Exception as e:
            logger.exception(f"Erreur ouverture gestion evaluations: {e}")
            show_error_message(self, "Erreur", "Impossible d'ouvrir la gestion des évaluations", e)

    def show_listes_grilles_dialog(self):
        from gui.screens.formation.liste_et_grilles import GrillesDialog
        GrillesDialog().exec_()

    def show_poste_form(self):
        from gui.screens.admin.creation_modification_poste import CreationModificationPosteDialog
        CreationModificationPosteDialog().exec_()
        self._postes_cache = None
        self._postes_cache_time = None
        self.populate_filters_async()

    def show_historique(self):
        from gui.screens.admin.historique import HistoriqueDialog
        HistoriqueDialog().exec_()

    def show_statistiques(self):
        from gui.screens.statistiques.statistiques_dialog import StatistiquesDialog
        StatistiquesDialog(self).exec_()

    def show_regularisation(self):
        from gui.workers.db_worker import DbWorker, DbThreadPool
        w = DbWorker(self._fetch_one_actif_personnel_id)
        w.signals.result.connect(self._open_regularisation)
        w.signals.error.connect(self._on_bg_error)
        DbThreadPool.start(w)

    def _fetch_one_actif_personnel_id(self, progress_callback=None):
        from domain.repositories.personnel_repo import PersonnelRepository
        return PersonnelRepository.get_first_actif_id()

    def _open_regularisation(self, personnel_id):
        if not personnel_id:
            QMessageBox.warning(self, "Erreur", "Aucun personnel actif trouvé")
            return
        from gui.screens.planning.planning_absences import PlanningAbsencesDialog
        dialog = PlanningAbsencesDialog(personnel_id=personnel_id, parent=self)
        dialog.data_changed.connect(self.load_evaluations_async)
        dialog.exec_()

    def show_contract_management(self):
        from gui.screens.rh.gestion_rh_dialog import GestionRHDialog
        dialog = GestionRHDialog(self)
        dialog.data_changed.connect(self.load_evaluations_async)
        dialog.data_changed.connect(self.load_alertes_rh_async)
        dialog.exec_()

    def show_alertes_rh(self):
        from gui.screens.rh.gestion_alertes_rh import GestionAlertesRHDialog
        dialog = GestionAlertesRHDialog(self)
        dialog.data_changed.connect(self.load_alertes_rh_async)
        dialog.exec_()

    def show_gestion_documentaire(self):
        from gui.screens.documents.gestion_documentaire import GestionDocumentaireDialog
        dialog = GestionDocumentaireDialog(self)
        dialog.document_added.connect(self.load_evaluations_async)
        dialog.document_added.connect(self.load_alertes_rh_async)
        dialog.exec_()

    def show_gestion_templates(self):
        from gui.screens.documents.gestion_templates import GestionTemplatesDialog
        GestionTemplatesDialog(parent=self).exec_()
