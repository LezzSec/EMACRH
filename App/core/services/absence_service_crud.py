# -*- coding: utf-8 -*-
"""
AbsenceService - Service métier CRUD pour la gestion des absences.

Ce service encapsule toutes les opérations CRUD sur la table absences
avec logging automatique dans l'historique.

Note: Ce service coexiste avec l'ancien absence_service.py.
Pour nouveaux développements, utiliser AbsenceServiceCRUD.

Usage:
    from core.services.absence_service_crud import AbsenceServiceCRUD

    # Créer une nouvelle absence
    success, msg, new_id = AbsenceServiceCRUD.create(
        personnel_id=1,
        type_absence_code="CP",
        date_debut=date.today(),
        date_fin=date.today() + timedelta(days=5),
        nb_jours=5.0,
        statut="VALIDEE"
    )

    # Valider une absence
    AbsenceServiceCRUD.valider(record_id=10)

    # Récupérer toutes les absences d'un personnel
    absences = AbsenceServiceCRUD.get_by_personnel(personnel_id=1)
"""

from typing import Dict, FrozenSet, List, Optional, Set, Tuple
from datetime import date, timedelta
from functools import lru_cache
from core.services.crud_service import CRUDService
from core.services.permission_manager import require


# =============================================================================
# UTILITAIRES : CALCUL DES JOURS OUVRÉS
# =============================================================================

@lru_cache(maxsize=16)
def _get_jours_feries_cached(annee_debut: int, annee_fin: int) -> FrozenSet[date]:
    """
    Requête DB mise en cache : retourne les jours fériés sous forme de frozenset.
    Le cache est conservé pendant toute la durée de la session (les jours fériés
    ne changent pas au cours d'une session utilisateur).
    """
    from core.db.query_executor import QueryExecutor
    try:
        rows = QueryExecutor.fetch_all(
            "SELECT date_ferie FROM jours_feries WHERE YEAR(date_ferie) BETWEEN %s AND %s",
            (annee_debut, annee_fin),
        )
        return frozenset(
            row[0] if isinstance(row, (tuple, list)) else row.get('date_ferie')
            for row in rows
        )
    except Exception:
        return frozenset()


def get_jours_feries(annee_debut: int, annee_fin: int) -> Set[date]:
    """
    Retourne l'ensemble des jours fériés entre deux années (incluses).
    Utilise un cache en mémoire — la DB n'est interrogée qu'une seule fois
    par paire (annee_debut, annee_fin) pendant la session.

    Args:
        annee_debut: Année de début
        annee_fin: Année de fin

    Returns:
        Ensemble de dates correspondant aux jours fériés
    """
    return set(_get_jours_feries_cached(annee_debut, annee_fin))


def calculer_jours_ouvres(
    date_debut: date,
    date_fin: date,
    demi_journee_debut: str = 'JOURNEE',
    demi_journee_fin: str = 'JOURNEE'
) -> float:
    """
    Calcule le nombre de jours ouvrés entre deux dates (incluses).

    Les samedis, dimanches et jours fériés sont exclus.
    Gère les demi-journées (MATIN / APRES_MIDI / JOURNEE).

    Args:
        date_debut: Date de début (incluse)
        date_fin: Date de fin (incluse)
        demi_journee_debut: 'JOURNEE', 'MATIN' ou 'APRES_MIDI'
        demi_journee_fin: 'JOURNEE', 'MATIN' ou 'APRES_MIDI'

    Returns:
        Nombre de jours ouvrés (float, peut être .5 pour demi-journées)
    """
    if not date_debut or not date_fin or date_fin < date_debut:
        return 0.0

    feries = get_jours_feries(date_debut.year, date_fin.year)

    # Cas particulier : même jour
    if date_debut == date_fin:
        if date_debut.weekday() >= 5 or date_debut in feries:
            return 0.0
        if demi_journee_debut in ('MATIN', 'APRES_MIDI') and demi_journee_fin in ('MATIN', 'APRES_MIDI'):
            return 0.5
        return 1.0

    nb_jours = 0.0
    current = date_debut
    while current <= date_fin:
        if current.weekday() < 5 and current not in feries:
            valeur = 1.0
            if current == date_debut and demi_journee_debut in ('MATIN', 'APRES_MIDI'):
                valeur = 0.5
            elif current == date_fin and demi_journee_fin in ('MATIN', 'APRES_MIDI'):
                valeur = 0.5
            nb_jours += valeur
        current += timedelta(days=1)

    return nb_jours


class AbsenceServiceCRUD(CRUDService):
    """Service métier CRUD pour la table demande_absence."""

    TABLE_NAME = "demande_absence"
    ACTION_PREFIX = "ABSENCE_"

    # Champs autorisés pour les mises à jour (sécurité)
    ALLOWED_FIELDS = [
        'personnel_id',
        'type_absence_code',
        'date_debut',
        'date_fin',
        'demi_debut',
        'demi_fin',
        'nb_jours',
        'motif',
        'statut',
        'commentaire',
        'valideur_id',
        'date_validation'
    ]

    @classmethod
    def create(cls, **kwargs) -> Tuple[bool, str, Optional[int]]:
        """Crée une absence (vérifie la permission planning.absences.edit)."""
        require('planning.absences.edit')
        return super().create(**kwargs)

    @classmethod
    def get_by_personnel(
        cls,
        personnel_id: int,
        order_by: str = 'date_debut DESC'
    ) -> List[Dict]:
        """
        Récupère toutes les absences d'un personnel.

        Args:
            personnel_id: ID du personnel
            order_by: Clause ORDER BY

        Returns:
            Liste de dictionnaires représentant les absences

        Example:
            >>> absences = AbsenceServiceCRUD.get_by_personnel(1)
        """
        return cls.get_all(
            conditions={'personnel_id': personnel_id},
            order_by=order_by
        )

    @classmethod
    def get_by_statut(
        cls,
        statut: str,
        order_by: str = 'date_debut DESC'
    ) -> List[Dict]:
        """
        Récupère toutes les absences d'un statut donné.

        Args:
            statut: Statut des absences (EN_ATTENTE, VALIDEE, REFUSEE, ANNULEE)
            order_by: Clause ORDER BY

        Returns:
            Liste d'absences

        Example:
            >>> en_attente = AbsenceServiceCRUD.get_by_statut('EN_ATTENTE')
        """
        return cls.get_all(
            conditions={'statut': statut},
            order_by=order_by
        )

    @classmethod
    def get_en_attente(cls) -> List[Dict]:
        """Récupère toutes les absences en attente de validation."""
        return cls.get_by_statut('EN_ATTENTE', order_by='date_debut ASC')

    @classmethod
    def get_validees(cls) -> List[Dict]:
        """Récupère toutes les absences validées."""
        return cls.get_by_statut('VALIDEE')

    @classmethod
    def get_refusees(cls) -> List[Dict]:
        """Récupère toutes les absences refusées."""
        return cls.get_by_statut('REFUSEE')

    @classmethod
    def valider(
        cls,
        record_id: int,
        valideur_id: int = None
    ) -> Tuple[bool, str]:
        """
        Valide une absence.

        Args:
            record_id: ID de l'absence
            valideur_id: ID du valideur (optionnel)

        Returns:
            (success: bool, message: str)

        Example:
            >>> AbsenceServiceCRUD.valider(10, valideur_id=5)
        """
        require('planning.absences.edit')
        from datetime import datetime

        update_data = {
            'statut': 'VALIDEE',
            'date_validation': datetime.now()
        }

        if valideur_id:
            update_data['valideur_id'] = valideur_id

        return cls.update(record_id=record_id, **update_data)

    @classmethod
    def refuser(
        cls,
        record_id: int,
        commentaire: str = None,
        valideur_id: int = None
    ) -> Tuple[bool, str]:
        """
        Refuse une absence.

        Args:
            record_id: ID de l'absence
            commentaire: Raison du refus (optionnel)
            valideur_id: ID du valideur (optionnel)

        Returns:
            (success: bool, message: str)

        Example:
            >>> AbsenceServiceCRUD.refuser(10, commentaire="Période déjà occupée")
        """
        require('planning.absences.edit')
        from datetime import datetime

        update_data = {
            'statut': 'REFUSEE',
            'date_validation': datetime.now()
        }

        if commentaire:
            update_data['commentaire'] = commentaire

        if valideur_id:
            update_data['valideur_id'] = valideur_id

        return cls.update(record_id=record_id, **update_data)

    @classmethod
    def annuler(cls, record_id: int, commentaire: str = None) -> Tuple[bool, str]:
        """
        Annule une absence.

        Args:
            record_id: ID de l'absence
            commentaire: Raison de l'annulation (optionnel)

        Returns:
            (success: bool, message: str)
        """
        require('planning.absences.edit')
        update_data = {'statut': 'ANNULEE'}

        if commentaire:
            update_data['commentaire'] = commentaire

        return cls.update(record_id=record_id, **update_data)

    @classmethod
    def count_by_personnel(cls, personnel_id: int, statut: str = None) -> int:
        """
        Compte le nombre d'absences d'un personnel.

        Args:
            personnel_id: ID du personnel
            statut: Filtrer par statut (optionnel)

        Returns:
            Nombre d'absences

        Example:
            >>> total = AbsenceServiceCRUD.count_by_personnel(1)
            >>> validees = AbsenceServiceCRUD.count_by_personnel(1, statut='VALIDEE')
        """
        conditions = {'personnel_id': personnel_id}
        if statut:
            conditions['statut'] = statut

        return cls.count(**conditions)

    @classmethod
    def count_by_statut(cls, statut: str) -> int:
        """
        Compte le nombre d'absences par statut.

        Args:
            statut: Statut des absences

        Returns:
            Nombre d'absences

        Example:
            >>> nb_en_attente = AbsenceServiceCRUD.count_by_statut('EN_ATTENTE')
        """
        return cls.count(statut=statut)

    @classmethod
    def get_types_absence(cls) -> list:
        """Retourne les types d'absence actifs (id, code, libelle)."""
        from core.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            "SELECT id, code, libelle FROM type_absence WHERE actif = TRUE ORDER BY code",
            dictionary=True,
        )

    @classmethod
    def get_en_attente_with_details(cls) -> list:
        """
        Retourne les demandes EN_ATTENTE avec nom complet et libellé du type.
        Utilisé par la vue de validation manager.
        """
        from core.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            """
            SELECT da.id,
                   CONCAT(p.prenom, ' ', p.nom) AS nom_complet,
                   ta.libelle AS type_libelle,
                   da.date_debut,
                   da.date_fin,
                   da.nb_jours,
                   da.motif
            FROM demande_absence da
            JOIN personnel p ON da.personnel_id = p.id
            JOIN type_absence ta ON da.type_absence_id = ta.id
            WHERE da.statut = 'EN_ATTENTE'
              AND p.statut = 'ACTIF'
            ORDER BY da.date_creation ASC
            """,
            dictionary=True,
        )

    @classmethod
    def get_demandes_personnel_details(
        cls,
        personnel_id: int,
        annee: int = None,
        statut: str = None
    ) -> list:
        """
        Retourne les demandes d'un personnel avec détails (type, validateur).

        Args:
            personnel_id: ID du personnel
            annee: Filtrer par année (optionnel)
            statut: Filtrer par statut (optionnel)

        Returns:
            Liste de dicts avec: id, type_libelle, date_debut, date_fin, nb_jours,
                                 motif, statut, validateur, date_validation
        """
        from core.db.query_executor import QueryExecutor

        conditions = ["da.personnel_id = %s"]
        params = [personnel_id]

        if annee:
            conditions.append("YEAR(da.date_debut) = %s")
            params.append(annee)

        if statut:
            conditions.append("da.statut = %s")
            params.append(statut)

        where_clause = " AND ".join(conditions)

        return QueryExecutor.fetch_all(
            f"""
            SELECT da.id,
                   ta.libelle AS type_libelle,
                   da.date_debut,
                   da.date_fin,
                   da.nb_jours,
                   da.motif,
                   da.statut,
                   CONCAT(v.prenom, ' ', v.nom) AS validateur,
                   da.date_validation
            FROM demande_absence da
            JOIN type_absence ta ON da.type_absence_id = ta.id
            LEFT JOIN personnel v ON da.valideur_id = v.id
            WHERE {where_clause}
            ORDER BY da.date_debut DESC
            """,
            tuple(params),
            dictionary=True,
        )

    @classmethod
    def get_validees_pour_mois(cls, first_day, last_day) -> list:
        """
        Retourne les demandes VALIDEE qui se chevauchent avec la plage donnée.
        Utilisé par le calendrier de planning pour colorier les jours.
        """
        from core.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            """
            SELECT da.date_debut, da.date_fin,
                   CONCAT(p.prenom, ' ', p.nom) AS nom_complet,
                   ta.libelle AS type_libelle,
                   da.statut
            FROM demande_absence da
            JOIN personnel p ON da.personnel_id = p.id
            JOIN type_absence ta ON da.type_absence_id = ta.id
            WHERE da.statut = 'VALIDEE'
              AND p.statut = 'ACTIF'
              AND da.date_debut <= %s
              AND da.date_fin >= %s
            ORDER BY da.date_debut
            """,
            (last_day, first_day),
            dictionary=True,
        )
