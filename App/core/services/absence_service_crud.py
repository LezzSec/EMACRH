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

from typing import Dict, List, Optional, Tuple
from datetime import date
from core.services.crud_service import CRUDService


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
