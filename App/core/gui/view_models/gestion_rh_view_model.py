# -*- coding: utf-8 -*-
"""
GestionRHViewModel — logique UI pour l'écran RH opérateur.

Extrait du mixin _GestionRHMixin tous les appels services,
la gestion asynchrone et les vérifications de permissions.

La View (gestion_rh.py) ne connaît que ce ViewModel.
Ce module n'importe aucun widget Qt.

Architecture :
    GestionRHDialog / _GestionRHMixin (View)
        ↓ appelle
    GestionRHViewModel (ViewModel)
        ↓ appelle
    rh_service, medical_service, document_service… (Services)

Exports utilisables dans la View :
    DomaineRH, get_domaines_rh  (enum + config statique)
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

from domain.services.rh.rh_service import (
    rechercher_operateurs,
    get_operateur_by_id,
    get_donnees_domaine,
    get_documents_domaine,
    get_documents_archives_operateur,
    delete_formation,
    delete_declaration,
    DomaineRH,
    get_domaines_rh,
)
from core.services import competences_service as _competences_service
from domain.services.rh.medical_service import delete_visite, delete_accident
from domain.services.rh.vie_salarie_service import delete_sanction, delete_entretien
from domain.services.rh.mutuelle_service import delete_mutuelle
from core.services.permission_manager import require
from core.gui.workers.db_worker import DbWorker, DbThreadPool
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# Re-export pour la View (évite que la View importe directement les services)
__all__ = ["GestionRHViewModel", "DomaineRH", "get_domaines_rh"]


class GestionRHViewModel(QObject):
    """
    ViewModel pour l'écran de gestion RH opérateur.

    État maintenu :
        _operateur_id   ID de l'opérateur sélectionné
        _domaine_actif  DomaineRH actif (pour annulation de chargement concurrent)
        _loading_worker Worker en cours (annulable)

    Signaux émis vers la View :
        resultats_loaded(list)              → résultats de recherche
        operateur_loaded(dict)              → opérateur sélectionné
        domaine_loaded(object, list, object) → donnees, documents, domaine
        archives_loaded(list)               → documents archivés
        document_path_ready(str)            → chemin à ouvrir (fichier local)
        dossier_formation_ready(bool,str,str) → success, msg, path
        action_succeeded(str)               → message succès (restauration, etc.)
        error_occurred(str)                 → message d'erreur
        permission_denied(str)              → accès refusé
    """

    resultats_loaded = pyqtSignal(list)
    operateur_loaded = pyqtSignal(dict)
    domaine_loaded = pyqtSignal(object, list, object)
    archives_loaded = pyqtSignal(list)
    document_path_ready = pyqtSignal(str)
    dossier_formation_ready = pyqtSignal(bool, str, str)
    action_succeeded = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    permission_denied = pyqtSignal(str)

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self._operateur_id: Optional[int] = None
        self._domaine_actif: Optional[DomaineRH] = None
        self._loading_worker: Optional[DbWorker] = None

    # ------------------------------------------------------------------
    # Recherche d'opérateur
    # ------------------------------------------------------------------

    def rechercher(self, terme: Optional[str] = None) -> None:
        """
        Lance une recherche asynchrone d'opérateurs.

        Args:
            terme: texte de recherche (None = tous les actifs)
        """
        def fetch(progress_callback=None):
            limit = 50 if terme else 2000
            return rechercher_operateurs(recherche=terme if terme else None, limit=limit)

        def on_success(resultats):
            self.resultats_loaded.emit(resultats)

        def on_error(err):
            logger.error(f"Erreur recherche opérateurs: {err}")
            self.error_occurred.emit(str(err))

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    # ------------------------------------------------------------------
    # Sélection d'opérateur
    # ------------------------------------------------------------------

    def selectionner_operateur(self, operateur_id: int) -> None:
        """
        Charge et sélectionne un opérateur.

        Émet operateur_loaded(dict) en cas de succès.
        """
        try:
            operateur = get_operateur_by_id(operateur_id)
            if operateur:
                self._operateur_id = operateur_id
                self.operateur_loaded.emit(operateur)
            else:
                self.error_occurred.emit(f"Opérateur {operateur_id} introuvable")
        except Exception as e:
            logger.exception(f"Erreur sélection opérateur {operateur_id}: {e}")
            self.error_occurred.emit(str(e))

    # ------------------------------------------------------------------
    # Chargement du domaine RH
    # ------------------------------------------------------------------

    def charger_domaine(self, domaine: DomaineRH) -> None:
        """
        Charge les données du domaine RH en arrière-plan.

        Annule automatiquement le chargement précédent si encore en cours.
        Émet domaine_loaded(donnees, documents, domaine) en cas de succès.

        Args:
            domaine: DomaineRH à charger
        """
        if not self._operateur_id:
            return

        if self._loading_worker:
            self._loading_worker.cancel()
            self._loading_worker = None

        self._domaine_actif = domaine
        operateur_id = self._operateur_id

        def fetch(progress_callback=None):
            donnees = get_donnees_domaine(operateur_id, domaine)
            documents = get_documents_domaine(operateur_id, domaine, include_archives=True)
            return donnees, documents, domaine

        def on_success(result):
            donnees, documents, fetched_domaine = result
            if fetched_domaine == self._domaine_actif:
                self.domaine_loaded.emit(donnees, documents, fetched_domaine)

        def on_error(err):
            logger.error(f"Erreur chargement domaine RH: {err}")
            self.error_occurred.emit(str(err))

        self._loading_worker = DbWorker(fetch)
        self._loading_worker.signals.result.connect(on_success)
        self._loading_worker.signals.error.connect(on_error)
        DbThreadPool.start(self._loading_worker)

    def rafraichir(self) -> None:
        """Recharge le domaine actif (après une modification)."""
        if self._domaine_actif is not None:
            self.charger_domaine(self._domaine_actif)

    # ------------------------------------------------------------------
    # Archives
    # ------------------------------------------------------------------

    def charger_archives(self) -> None:
        """
        Charge les documents archivés de l'opérateur.

        Émet archives_loaded(list). La View utilise ce signal pour :
          - mettre à jour le bouton Archives (toujours)
          - afficher le contenu si l'onglet Archives est actif
        """
        if not self._operateur_id:
            self.archives_loaded.emit([])
            return

        operateur_id = self._operateur_id

        def fetch(progress_callback=None):
            return get_documents_archives_operateur(operateur_id)

        def on_success(archives):
            self.archives_loaded.emit(archives or [])

        def on_error(err):
            logger.error(f"Erreur chargement archives: {err}")
            self.archives_loaded.emit([])

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    # ------------------------------------------------------------------
    # Suppressions — pattern uniforme : require() + delete + rafraichir
    # ------------------------------------------------------------------

    def _supprimer(
        self,
        feature: str,
        fn_delete,
        record_id: int,
    ) -> None:
        """
        Vérifie la permission, supprime, puis émet rafraichissement.

        Émet permission_denied(str) ou error_occurred(str) en cas d'échec.
        """
        try:
            require(feature)
        except PermissionError as e:
            self.permission_denied.emit(str(e))
            return

        try:
            success, msg = fn_delete(record_id)
            if success:
                self.rafraichir()
            else:
                self.error_occurred.emit(msg)
        except Exception as e:
            logger.exception(f"Erreur suppression (feature={feature}): {e}")
            self.error_occurred.emit(str(e))

    def supprimer_formation(self, formation_id: int) -> None:
        self._supprimer("rh.formations.delete", delete_formation, formation_id)

    def supprimer_declaration(self, declaration_id: int) -> None:
        self._supprimer("rh.declarations.edit", delete_declaration, declaration_id)

    def supprimer_visite(self, visite_id: int) -> None:
        self._supprimer("rh.medical.delete", delete_visite, visite_id)

    def supprimer_accident(self, accident_id: int) -> None:
        self._supprimer("rh.medical.delete", delete_accident, accident_id)

    def supprimer_sanction(self, sanction_id: int) -> None:
        self._supprimer("rh.vie_salarie.edit", delete_sanction, sanction_id)

    def supprimer_entretien(self, entretien_id: int) -> None:
        self._supprimer("rh.vie_salarie.edit", delete_entretien, entretien_id)

    def supprimer_mutuelle(self, mutuelle_id: int) -> None:
        self._supprimer("rh.mutuelle.edit", delete_mutuelle, mutuelle_id)

    def supprimer_competence(self, assignment_id: int) -> None:
        """Retire une compétence d'un opérateur."""
        try:
            require("rh.competences.delete")
        except PermissionError as e:
            self.permission_denied.emit(str(e))
            return

        try:
            success, message = _competences_service.remove_assignment(assignment_id)
            if success:
                self.action_succeeded.emit(message)
                self.rafraichir()
            else:
                self.error_occurred.emit(message)
        except Exception as e:
            logger.exception(f"Erreur suppression compétence: {e}")
            self.error_occurred.emit(str(e))

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    def restaurer_document(self, doc_id: int) -> None:
        """
        Restaure un document archivé.

        Émet action_succeeded(msg) puis rafraichit domaine + archives.
        """
        try:
            from domain.services.documents.document_service import DocumentService
            doc_service = DocumentService()
            success, message = doc_service.restore_document(doc_id)
            if success:
                self.action_succeeded.emit("Document restauré avec succès")
                self.rafraichir()
                self.charger_archives()
            else:
                self.error_occurred.emit(message)
        except Exception as e:
            logger.exception(f"Erreur restauration document {doc_id}: {e}")
            self.error_occurred.emit(str(e))

    def archiver_document(self, doc_id: int) -> None:
        """
        Archive un document.

        Vérifie la permission, archive, puis rafraichit domaine + archives.
        """
        try:
            require("rh.documents.edit")
        except PermissionError as e:
            self.permission_denied.emit(str(e))
            return

        try:
            from domain.services.documents.document_service import DocumentService
            doc_service = DocumentService()
            success, message = doc_service.archive_document(doc_id)
            if success:
                self.action_succeeded.emit("Document archivé avec succès")
                self.rafraichir()
                self.charger_archives()
            else:
                self.error_occurred.emit(message)
        except Exception as e:
            logger.exception(f"Erreur archivage document {doc_id}: {e}")
            self.error_occurred.emit(str(e))

    def ouvrir_document(self, doc_id: int) -> None:
        """
        Résout le chemin d'un document et émet document_path_ready(path).

        La View se charge d'ouvrir le fichier (os.startfile / xdg-open).
        """
        try:
            from domain.services.documents.document_service import DocumentService
            doc_service = DocumentService()
            doc_path = doc_service.get_document_path(doc_id)
            if doc_path and doc_path.exists():
                self.document_path_ready.emit(str(doc_path))
            else:
                self.error_occurred.emit("Le fichier n'a pas été trouvé sur le disque")
        except Exception as e:
            logger.exception(f"Erreur ouverture document {doc_id}: {e}")
            self.error_occurred.emit(str(e))

    def extraire_doc_formation(self, doc_id: int) -> None:
        """
        Extrait un dossier de formation vers un fichier temp et émet son chemin.
        """
        try:
            from domain.services.documents.polyvalence_docs_service import extraire_vers_fichier_temp
            temp_path = extraire_vers_fichier_temp(doc_id)
            if temp_path and temp_path.exists():
                self.document_path_ready.emit(str(temp_path))
            else:
                self.error_occurred.emit("Le dossier de formation n'a pas pu être ouvert.")
        except Exception as e:
            logger.exception(f"Erreur extraction doc formation {doc_id}: {e}")
            self.error_occurred.emit(str(e))

    def generer_dossier_formation(self, formation_id: int) -> None:
        """
        Génère les documents de formation pré-remplis.

        Émet dossier_formation_ready(success, msg, path).
        La View affiche le résultat et appelle document_path_ready si l'utilisateur
        veut ouvrir le fichier.
        """
        try:
            from domain.services.formation.formation_export_service import FormationExportService
            from domain.services.formation.formation_service_crud import FormationServiceCRUD

            data = FormationServiceCRUD.get_formation_by_id(formation_id)
            if not data:
                self.dossier_formation_ready.emit(False, "Formation introuvable.", "")
                return

            success, msg, path = FormationExportService.generate_dossier_formation(data)
            self.dossier_formation_ready.emit(success, msg, str(path) if path else "")

        except Exception as e:
            logger.exception(f"Erreur génération dossier formation {formation_id}: {e}")
            self.dossier_formation_ready.emit(False, str(e), "")
