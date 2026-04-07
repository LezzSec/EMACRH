# -*- coding: utf-8 -*-
"""
FormationViewModel — logique UI pour la gestion des formations.

Ce module n'importe aucun widget Qt.
Le Dialog n'importe aucun service.

Architecture :
    GestionFormationsDialog / AddEditFormationDialog (View)
        ↓ appelle
    FormationViewModel (ViewModel)
        ↓ appelle
    FormationServiceCRUD, DocumentService, FormationExportService (Services)
"""

from __future__ import annotations

import os
import sys
import subprocess
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

from core.services.formation_service_crud import FormationServiceCRUD
from core.services.document_service import DocumentService
from core.gui.workers.db_worker import DbWorker, DbThreadPool
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

_doc_service = DocumentService()


class FormationViewModel(QObject):
    """
    ViewModel pour l'écran de gestion des formations.

    Signaux vers la View :
        personnel_loaded(list)          → remplir les combos opérateurs
        formations_loaded(list)         → rafraîchir la table principale
        stats_loaded(dict)              → mettre à jour les compteurs
        formation_loaded(dict)          → ouvrir la fiche édition
        action_succeeded(str)           → message de succès
        error_occurred(str)             → message d'erreur
        document_path_ready(str)        → chemin fichier à ouvrir
        document_nom_ready(str)         → nom du document (affichage)
        dossier_generated(bool, str, str) → (succès, message, chemin)
        data_changed()                  → signal de propagation vers le parent
    """

    personnel_loaded = pyqtSignal(list)
    formations_loaded = pyqtSignal(list)
    stats_loaded = pyqtSignal(dict)
    formation_loaded = pyqtSignal(dict)
    action_succeeded = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    document_path_ready = pyqtSignal(str)
    document_nom_ready = pyqtSignal(str)
    dossier_generated = pyqtSignal(bool, str, str)
    data_changed = pyqtSignal()

    # ------------------------------------------------------------------
    # Chargements
    # ------------------------------------------------------------------

    def load_personnel(self) -> None:
        """Charge la liste des employés (combo filtres + combo formulaire)."""
        def fetch(progress_callback=None):
            return FormationServiceCRUD.get_personnel_list()

        def on_success(data):
            self.personnel_loaded.emit(data)

        def on_error(msg):
            logger.error(f"Erreur chargement personnel formations: {msg}")
            self.error_occurred.emit(msg)

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def load_formations(
        self,
        operateur_id: Optional[int] = None,
        statut: Optional[str] = None,
        search: Optional[str] = None,
    ) -> None:
        """Charge et filtre la liste des formations."""
        def fetch(progress_callback=None):
            formations = FormationServiceCRUD.get_all_formations(
                statut=statut,
                operateur_id=operateur_id,
            )
            if search:
                q = search.lower()
                formations = [
                    f for f in formations
                    if q in (f.get('intitule') or '').lower()
                    or q in (f.get('organisme') or '').lower()
                    or q in (f.get('nom_complet') or '').lower()
                ]
            return formations

        def on_success(data):
            self.formations_loaded.emit(data)

        def on_error(msg):
            logger.error(f"Erreur chargement formations: {msg}")
            self.error_occurred.emit(msg)

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def load_stats(self) -> None:
        """Charge les statistiques globales des formations."""
        try:
            stats = FormationServiceCRUD.get_formations_stats()
            self.stats_loaded.emit(stats)
        except Exception as e:
            logger.exception(f"Erreur chargement stats formations: {e}")
            self.error_occurred.emit(str(e))

    def load_formation(self, formation_id: int) -> None:
        """Charge le détail d'une formation par ID."""
        try:
            formation = FormationServiceCRUD.get_formation_by_id(formation_id)
            if formation:
                self.formation_loaded.emit(formation)
            else:
                self.error_occurred.emit("Formation introuvable.")
        except Exception as e:
            logger.exception(f"Erreur chargement formation {formation_id}: {e}")
            self.error_occurred.emit(str(e))

    # ------------------------------------------------------------------
    # Actions CRUD
    # ------------------------------------------------------------------

    def save_formation(self, data: dict, formation_id: Optional[int] = None) -> None:
        """
        Crée ou met à jour une formation.

        data : dict des champs du formulaire (opérateur_id, intitule, ...)
        formation_id : None → création, int → modification
        """
        try:
            if formation_id:
                success, message = FormationServiceCRUD.update_formation(
                    formation_id, **data
                )
                saved_id = formation_id if success else None
            else:
                success, message, saved_id = FormationServiceCRUD.add_formation(**data)
                if success and saved_id and data.get('document_id'):
                    FormationServiceCRUD.update_formation(saved_id, document_id=data['document_id'])

            if success:
                self.action_succeeded.emit(message)
                if saved_id:
                    self.formation_loaded.emit({'_saved_id': saved_id})
                self.data_changed.emit()
            else:
                self.error_occurred.emit(message)
        except Exception as e:
            logger.exception(f"Erreur sauvegarde formation: {e}")
            self.error_occurred.emit(str(e))

    def delete_formation(self, formation_id: int) -> None:
        """Supprime une formation."""
        try:
            success, message = FormationServiceCRUD.delete_formation(formation_id)
            if success:
                self.action_succeeded.emit(message)
                self.data_changed.emit()
            else:
                self.error_occurred.emit(message)
        except Exception as e:
            logger.exception(f"Erreur suppression formation {formation_id}: {e}")
            self.error_occurred.emit(str(e))

    # ------------------------------------------------------------------
    # Export / Documents
    # ------------------------------------------------------------------

    def generate_dossier(self, formation_id: int) -> None:
        """Génère les documents officiels de formation (async)."""
        def fetch(progress_callback=None):
            from core.services.formation_export_service import FormationExportService
            data = FormationServiceCRUD.get_formation_by_id(formation_id)
            if not data:
                return False, "Formation introuvable.", ""
            return FormationExportService.generate_dossier_formation(data)

        def on_success(result):
            success, msg, path = result
            self.dossier_generated.emit(success, msg, path or "")

        def on_error(msg):
            logger.error(f"Erreur génération dossier formation: {msg}")
            self.dossier_generated.emit(False, msg, "")

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def open_file(self, path: str) -> None:
        """Ouvre un fichier avec le programme par défaut."""
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
        except Exception as e:
            logger.exception(f"Erreur ouverture fichier: {e}")
            self.error_occurred.emit(str(e))

    def get_document_path(self, doc_id: int) -> None:
        """Résout le chemin d'un document et émet document_path_ready."""
        try:
            path = _doc_service.get_document_path(doc_id)
            if path and path.exists():
                self.document_path_ready.emit(str(path))
            else:
                self.error_occurred.emit("Fichier introuvable.")
        except Exception as e:
            logger.exception(f"Erreur résolution chemin document {doc_id}: {e}")
            self.error_occurred.emit(str(e))

    def get_document_nom(self, doc_id: int) -> None:
        """Résout le nom d'un document et émet document_nom_ready."""
        try:
            nom = _doc_service.get_document_nom(doc_id)
            if nom:
                self.document_nom_ready.emit(nom)
        except Exception as e:
            logger.exception(f"Erreur résolution nom document {doc_id}: {e}")
