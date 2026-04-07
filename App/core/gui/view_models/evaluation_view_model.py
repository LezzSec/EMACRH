# -*- coding: utf-8 -*-
"""
EvaluationViewModel — logique UI pour la gestion des évaluations/polyvalences.

Ce module n'importe aucun widget Qt.
Les Dialogs (GestionEvaluationDialog, DetailOperateurDialog) n'importent aucun service.

Architecture :
    GestionEvaluationDialog / DetailOperateurDialog (View)
        ↓ appelle
    EvaluationViewModel (ViewModel)
        ↓ appelle
    evaluation_service, PosteRepository, EventBus… (Services)
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

from domain.services.formation.evaluation_service import (
    get_operateurs_avec_stats_polyvalences,
    get_stats_polyvalence_operateur,
    get_polyvalences_actuelles_operateur,
    get_historique_polyvalence_operateur,
    get_polyvalence_par_id,
    mettre_a_jour_evaluation,
    update_date_evaluation_polyvalence,
    supprimer_polyvalence_par_id,
    compter_polyvalences_operateur,
)
from core.gui.workers.db_worker import DbWorker, DbThreadPool
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

_JOURS_PAR_NIVEAU = {1: 30, 2: 30, 3: 3650, 4: 3650}


class EvaluationViewModel(QObject):
    """
    ViewModel partagé par GestionEvaluationDialog et DetailOperateurDialog.

    Signaux vers la View :
        operateurs_loaded(list)     → remplir le tableau principal
        detail_loaded(dict)         → remplir le tableau de détail d'un opérateur
        action_succeeded(str)       → message de succès
        error_occurred(str)         → message d'erreur
        evaluation_count(int)       → nombre de polyvalences (pour validation suppression)
        polyvalence_loaded(dict)    → info d'une polyvalence (avant modification)
    """

    operateurs_loaded = pyqtSignal(list)
    detail_loaded = pyqtSignal(dict)
    action_succeeded = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    evaluation_count = pyqtSignal(int)
    polyvalence_loaded = pyqtSignal(dict)

    # ------------------------------------------------------------------
    # Chargements
    # ------------------------------------------------------------------

    def load_operateurs(self) -> None:
        """Charge tous les opérateurs avec leur résumé de polyvalences (async)."""
        def fetch(progress_callback=None):
            rows = get_operateurs_avec_stats_polyvalences()
            result = []
            for row in rows:
                pers_id, nom, prenom, matricule, total, n4, n3, n2, n1, a_planifier, retard = row
                if retard and retard > 0:
                    statut = f"⚠️ {retard} en retard"
                    statut_code = "En retard"
                elif a_planifier and a_planifier > 0:
                    statut = f"📅 {a_planifier} à planifier"
                    statut_code = "À planifier"
                else:
                    statut = "✅ À jour"
                    statut_code = "À jour"
                result.append({
                    'personnel_id': pers_id, 'nom': nom, 'prenom': prenom,
                    'matricule': matricule or "N/A",
                    'total': total or 0,
                    'n4': n4 or 0, 'n3': n3 or 0, 'n2': n2 or 0, 'n1': n1 or 0,
                    'retard': retard or 0, 'a_planifier': a_planifier or 0,
                    'statut': statut, 'statut_code': statut_code,
                })
            return result

        def on_success(data):
            self.operateurs_loaded.emit(data)

        def on_error(msg):
            logger.error(f"Erreur chargement opérateurs évaluations: {msg}")
            self.error_occurred.emit(msg)

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def load_detail(self, operateur_id: int) -> None:
        """Charge stats + polyvalences + historique d'un opérateur (async)."""
        def fetch(progress_callback=None):
            stats = get_stats_polyvalence_operateur(operateur_id)
            polyvalences = get_polyvalences_actuelles_operateur(operateur_id)
            historique = get_historique_polyvalence_operateur(operateur_id)
            return {'stats': stats, 'polyvalences': polyvalences, 'historique': historique}

        def on_success(data):
            self.detail_loaded.emit(data)

        def on_error(msg):
            logger.error(f"Erreur chargement détail opérateur {operateur_id}: {msg}")
            self.error_occurred.emit(msg)

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def get_polyvalence(self, poly_id: int) -> None:
        """Charge une polyvalence par ID et émet polyvalence_loaded."""
        try:
            info = get_polyvalence_par_id(poly_id)
            if info:
                self.polyvalence_loaded.emit(info)
            else:
                self.error_occurred.emit("Polyvalence introuvable.")
        except Exception as e:
            logger.exception(f"Erreur lecture polyvalence {poly_id}: {e}")
            self.error_occurred.emit(str(e))

    def compter_polyvalences(self, operateur_id: int) -> None:
        """Émet evaluation_count avec le nombre de polyvalences de l'opérateur."""
        try:
            n = compter_polyvalences_operateur(operateur_id)
            self.evaluation_count.emit(n)
        except Exception as e:
            logger.exception(f"Erreur comptage polyvalences: {e}")
            self.error_occurred.emit(str(e))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def mettre_a_jour_niveau(
        self,
        poly_id: int,
        nouveau_niveau: int,
        date_eval: Optional[date] = None,
        operateur_nom: str = "",
    ) -> None:
        """
        Met à jour le niveau d'une polyvalence et calcule la prochaine évaluation.
        Émet l'événement EventBus si le niveau a changé.
        """
        if nouveau_niveau not in [1, 2, 3, 4]:
            self.error_occurred.emit("Niveau invalide — doit être 1, 2, 3 ou 4.")
            return

        if date_eval is None:
            date_eval = date.today()

        jours = _JOURS_PAR_NIVEAU.get(nouveau_niveau, 30)
        prochaine_eval = date_eval + timedelta(days=jours)

        try:
            poly_info = get_polyvalence_par_id(poly_id)
            ancien_niveau = poly_info['niveau'] if poly_info else None
            operateur_id = poly_info['personnel_id'] if poly_info else None
            poste_id = poly_info['poste_id'] if poly_info else None

            if not mettre_a_jour_evaluation(poly_id, nouveau_niveau, date_eval, prochaine_eval):
                self.error_occurred.emit("Échec de la mise à jour du niveau.")
                return

            self.action_succeeded.emit(
                f"Niveau mis à jour.\nProchaine évaluation : {prochaine_eval.strftime('%d/%m/%Y')}"
            )

            if ancien_niveau != nouveau_niveau and operateur_id and poste_id:
                self._emettre_event_niveau_change(
                    poly_id, operateur_id, poste_id, operateur_nom,
                    ancien_niveau, nouveau_niveau, prochaine_eval,
                )
        except Exception as e:
            logger.exception(f"Erreur mise à jour niveau polyvalence {poly_id}: {e}")
            self.error_occurred.emit(str(e))

    def mettre_a_jour_date(
        self,
        poly_id: int,
        date_eval: date,
        nouveau_niveau: Optional[int] = None,
        operateur_nom: str = "",
    ) -> None:
        """Met à jour la date d'évaluation et recalcule la prochaine."""
        try:
            poly_info = get_polyvalence_par_id(poly_id)
            niveau = nouveau_niveau or (poly_info['niveau'] if poly_info else 1)
            operateur_id = poly_info['personnel_id'] if poly_info else None
            poste_id = poly_info['poste_id'] if poly_info else None

            jours = _JOURS_PAR_NIVEAU.get(niveau, 30)
            prochaine_eval = date_eval + timedelta(days=jours)

            if not update_date_evaluation_polyvalence(poly_id, date_eval, prochaine_eval):
                self.error_occurred.emit("Échec de la mise à jour de la date.")
                return

            self.action_succeeded.emit(
                f"Date mise à jour.\nProchaine évaluation : {prochaine_eval.strftime('%d/%m/%Y')}"
            )
        except Exception as e:
            logger.exception(f"Erreur mise à jour date polyvalence {poly_id}: {e}")
            self.error_occurred.emit(str(e))

    def supprimer_polyvalence(self, poly_id: int, poste_code: str = "") -> None:
        """Supprime une polyvalence après vérification."""
        try:
            if supprimer_polyvalence_par_id(poly_id):
                self.action_succeeded.emit(
                    f"Polyvalence{f' pour le poste {poste_code}' if poste_code else ''} supprimée."
                )
            else:
                self.error_occurred.emit("Impossible de supprimer la polyvalence.")
        except Exception as e:
            logger.exception(f"Erreur suppression polyvalence {poly_id}: {e}")
            self.error_occurred.emit(str(e))

    # ------------------------------------------------------------------
    # Privé
    # ------------------------------------------------------------------

    def _emettre_event_niveau_change(
        self, poly_id, operateur_id, poste_id, operateur_nom,
        ancien_niveau, nouveau_niveau, prochaine_eval,
    ):
        try:
            from core.services.event_bus import EventBus
            from domain.repositories.poste_repo import PosteRepository
            from domain.services.formation.evaluation_service import has_operateur_deja_eu_niveau_1

            poste = PosteRepository.get_by_id(poste_id)
            poste_code = poste.get('code') if poste else None
            poste_nom = poste.get('nom') if poste else None

            EventBus.emit('polyvalence_niveau_changed', {
                'polyvalence_id': poly_id,
                'operateur_id': operateur_id,
                'nom': operateur_nom,
                'poste_id': poste_id,
                'poste_code': poste_code,
                'poste_nom': poste_nom,
                'ancien_niveau': ancien_niveau,
                'nouveau_niveau': nouveau_niveau,
                'prochaine_evaluation': prochaine_eval,
                'premier_niveau_1': (
                    nouveau_niveau == 1 and not has_operateur_deja_eu_niveau_1(operateur_id, poste_id)
                ),
            })
        except Exception as e:
            logger.warning(f"EventBus non disponible: {e}")
