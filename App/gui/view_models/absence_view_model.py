# -*- coding: utf-8 -*-
"""
AbsenceViewModel — logique UI pour la gestion des absences.

Sépare la logique de présentation du Dialog PyQt5.

Responsabilités :
    - Charger les données (via services)
    - Calculer les soldes et le nombre de jours ouvrés
    - Orchestrer les actions (soumettre, annuler, valider)
    - Exposer des signaux Qt pour informer la View

Ce module n'importe aucun widget Qt.
Le Dialog n'importe aucun service.

Architecture :
    GestionAbsencesDialog (View)
        ↓ appelle
    AbsenceViewModel (ViewModel)
        ↓ appelle
    AbsenceServiceCRUD (Service)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

from domain.services.planning.absence_service_crud import AbsenceServiceCRUD, calculer_jours_ouvres
from gui.workers.db_worker import DbWorker, DbThreadPool
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class AbsenceViewModel(QObject):
    """
    ViewModel pour l'écran de gestion des absences.

    Signaux émis vers la View :
        types_loaded(list)              → remplir le combo de types
        demandes_loaded(list)           → rafraîchir la table "Mes demandes"
        soldes_loaded(dict)             → mettre à jour les cards CP/RTT
        validation_demandes_loaded(list) → rafraîchir la table "Validation"
        nb_jours_changed(float)         → afficher le nombre de jours calculés
        demande_submitted(int)          → demande_id créée avec succès
        demande_cancelled()             → demande annulée avec succès
        demande_validated(bool)         → True=validée / False=refusée
        error_occurred(str)             → message d'erreur à afficher
        data_changed()                  → données modifiées (pour les parents)
    """

    types_loaded = pyqtSignal(list)
    demandes_loaded = pyqtSignal(list)
    soldes_loaded = pyqtSignal(dict)
    validation_demandes_loaded = pyqtSignal(list)
    nb_jours_changed = pyqtSignal(float)
    demande_submitted = pyqtSignal(int)
    demande_cancelled = pyqtSignal()
    demande_validated = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    data_changed = pyqtSignal()

    def __init__(self, personnel_id: Optional[int], parent: QObject = None) -> None:
        super().__init__(parent)
        self._personnel_id = personnel_id

    @property
    def personnel_id(self) -> Optional[int]:
        return self._personnel_id

    # ------------------------------------------------------------------
    # Chargement initial
    # ------------------------------------------------------------------

    def load_all(self) -> None:
        """Charge toutes les données au démarrage."""
        self.load_types()
        self.load_demandes()
        self.load_soldes()
        self.load_validation_demandes()

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------

    def load_types(self) -> None:
        """Charge la liste des types d'absence."""
        try:
            types = AbsenceServiceCRUD.get_types_absence()
            self.types_loaded.emit(types)
        except Exception as e:
            logger.exception(f"Erreur chargement types absence: {e}")
            self.error_occurred.emit(str(e))

    def load_demandes(
        self,
        annee: Optional[int] = None,
        statut: Optional[str] = None,
    ) -> None:
        """
        Charge les demandes du personnel connecté.

        Args:
            annee:  année à afficher (défaut: année courante)
            statut: filtre optionnel (EN_ATTENTE / VALIDEE / REFUSEE)
        """
        if not self._personnel_id:
            self.demandes_loaded.emit([])
            return

        if annee is None:
            annee = datetime.now().year

        try:
            demandes = AbsenceServiceCRUD.get_demandes_personnel_details(
                self._personnel_id, annee, statut
            )
            self.demandes_loaded.emit(demandes)
        except Exception as e:
            logger.exception(f"Erreur chargement demandes: {e}")
            self.error_occurred.emit(str(e))

    def load_soldes(self, annee: Optional[int] = None) -> None:
        """
        Calcule et émet les soldes CP/RTT pour l'année donnée.

        Émet soldes_loaded avec : {'cp': float, 'rtt': float}
        """
        if not self._personnel_id:
            self.soldes_loaded.emit({"cp": 0.0, "rtt": 0.0})
            return

        if annee is None:
            annee = datetime.now().year

        try:
            absences = AbsenceServiceCRUD.get_demandes_personnel_details(
                self._personnel_id, annee, "VALIDEE"
            )
            cp = sum(
                a["nb_jours"]
                for a in absences
                if "CP" in (a.get("type_libelle") or "")
            )
            rtt = sum(
                a["nb_jours"]
                for a in absences
                if "RTT" in (a.get("type_libelle") or "")
            )
            self.soldes_loaded.emit({"cp": round(cp, 1), "rtt": round(rtt, 1)})
        except Exception as e:
            logger.exception(f"Erreur calcul soldes: {e}")
            self.error_occurred.emit(str(e))

    def load_validation_demandes(self) -> None:
        """Charge les demandes en attente de validation (en background)."""

        def fetch(progress_callback=None):
            return AbsenceServiceCRUD.get_en_attente_with_details()

        def on_success(demandes):
            self.validation_demandes_loaded.emit(demandes)

        def on_error(msg):
            logger.error(f"Erreur chargement demandes validation: {msg}")
            self.error_occurred.emit(msg)

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    # ------------------------------------------------------------------
    # Calculs
    # ------------------------------------------------------------------

    def compute_nb_jours(
        self,
        date_debut,
        date_fin,
        demi_debut: str,
        demi_fin: str,
    ) -> float:
        """
        Calcule le nombre de jours ouvrés et émet nb_jours_changed.

        Args:
            date_debut: datetime.date
            date_fin:   datetime.date
            demi_debut: 'JOURNEE' | 'MATIN' | 'APRES_MIDI'
            demi_fin:   'JOURNEE' | 'MATIN' | 'APRES_MIDI'

        Returns:
            Nombre de jours ouvrés calculé
        """
        nb = calculer_jours_ouvres(date_debut, date_fin, demi_debut, demi_fin)
        self.nb_jours_changed.emit(float(nb))
        return nb

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def submit_demande(
        self,
        date_debut,
        date_fin,
        demi_debut: str,
        demi_fin: str,
        type_code: str,
        motif: str,
    ) -> None:
        """
        Soumet une nouvelle demande d'absence.

        Émet demande_submitted(demande_id) en cas de succès,
        error_occurred(msg) en cas d'échec.
        """
        if not self._personnel_id:
            self.error_occurred.emit("Personnel non identifié")
            return

        try:
            nb_jours = calculer_jours_ouvres(date_debut, date_fin, demi_debut, demi_fin)
            success, msg, demande_id = AbsenceServiceCRUD.create(
                personnel_id=self._personnel_id,
                type_absence_code=type_code,
                date_debut=date_debut,
                date_fin=date_fin,
                demi_debut=demi_debut,
                demi_fin=demi_fin,
                nb_jours=nb_jours,
                motif=motif,
                statut="EN_ATTENTE",
            )
            if not success:
                self.error_occurred.emit(msg)
                return

            self.demande_submitted.emit(demande_id)
            self.data_changed.emit()

        except Exception as e:
            logger.exception(f"Erreur soumission demande: {e}")
            self.error_occurred.emit(str(e))

    def cancel_demande(self, demande_id: int) -> None:
        """
        Annule une demande (statut EN_ATTENTE uniquement).

        Émet demande_cancelled() en cas de succès.
        """
        try:
            AbsenceServiceCRUD.annuler(demande_id)
            self.demande_cancelled.emit()
            self.data_changed.emit()
        except Exception as e:
            logger.exception(f"Erreur annulation demande {demande_id}: {e}")
            self.error_occurred.emit(str(e))

    def validate_demande(
        self,
        demande_id: int,
        valide: bool,
        validateur_id: int,
    ) -> None:
        """
        Valide ou refuse une demande.

        Args:
            demande_id:    ID de la demande
            valide:        True pour valider, False pour refuser
            validateur_id: ID du manager connecté

        Émet demande_validated(valide) en cas de succès.
        """
        try:
            if valide:
                AbsenceServiceCRUD.valider(demande_id, valideur_id=validateur_id)
            else:
                AbsenceServiceCRUD.refuser(demande_id, valideur_id=validateur_id)

            self.demande_validated.emit(valide)
            self.data_changed.emit()

        except Exception as e:
            logger.exception(f"Erreur validation demande {demande_id}: {e}")
            self.error_occurred.emit(str(e))
