# -*- coding: utf-8 -*-
"""
PolyvalenceService - Service métier CRUD pour la gestion des compétences/polyvalences.

Ce service encapsule toutes les opérations CRUD sur la table polyvalence
avec logging automatique dans l'historique.

Usage:
    from core.services.polyvalence_service_crud import PolyvalenceServiceCRUD

    # Créer une nouvelle compétence
    success, msg, new_id = PolyvalenceServiceCRUD.create(
        operateur_id=1,
        poste_id=10,
        niveau=2,
        date_evaluation=date.today()
    )

    # Mettre à jour le niveau
    PolyvalenceServiceCRUD.update(record_id=5, niveau=3)

    # Récupérer toutes les compétences d'un opérateur
    competences = PolyvalenceServiceCRUD.get_by_operateur(operateur_id=1)
"""

from typing import Dict, List, Optional, Tuple
from datetime import date
from core.services.crud_service import CRUDService


class PolyvalenceServiceCRUD(CRUDService):
    """Service métier CRUD pour la table polyvalence."""

    TABLE_NAME = "polyvalence"
    ACTION_PREFIX = "POLYVALENCE_"

    # Champs autorisés pour les mises à jour (sécurité)
    ALLOWED_FIELDS = [
        'operateur_id',
        'poste_id',
        'niveau',
        'date_evaluation',
        'prochaine_evaluation'
    ]

    @classmethod
    def get_by_operateur(
        cls,
        operateur_id: int,
        order_by: str = 'niveau DESC'
    ) -> List[Dict]:
        """
        Récupère toutes les compétences d'un opérateur.

        Args:
            operateur_id: ID de l'opérateur
            order_by: Clause ORDER BY

        Returns:
            Liste de dictionnaires représentant les compétences

        Example:
            >>> competences = PolyvalenceServiceCRUD.get_by_operateur(1)
        """
        return cls.get_all(
            conditions={'operateur_id': operateur_id},
            order_by=order_by
        )

    @classmethod
    def get_by_poste(
        cls,
        poste_id: int,
        order_by: str = 'niveau DESC'
    ) -> List[Dict]:
        """
        Récupère toutes les compétences pour un poste.

        Args:
            poste_id: ID du poste
            order_by: Clause ORDER BY

        Returns:
            Liste de compétences

        Example:
            >>> competences = PolyvalenceServiceCRUD.get_by_poste(10)
        """
        return cls.get_all(
            conditions={'poste_id': poste_id},
            order_by=order_by
        )

    @classmethod
    def get_by_niveau(
        cls,
        niveau: int,
        order_by: str = 'operateur_id'
    ) -> List[Dict]:
        """
        Récupère toutes les compétences d'un niveau donné.

        Args:
            niveau: Niveau (1-4)
            order_by: Clause ORDER BY

        Returns:
            Liste de compétences

        Example:
            >>> experts = PolyvalenceServiceCRUD.get_by_niveau(4)
        """
        return cls.get_all(
            conditions={'niveau': niveau},
            order_by=order_by
        )

    @classmethod
    def augmenter_niveau(cls, record_id: int) -> Tuple[bool, str]:
        """
        Augmente le niveau d'une compétence (max 4).

        Args:
            record_id: ID de la polyvalence

        Returns:
            (success: bool, message: str)

        Example:
            >>> PolyvalenceServiceCRUD.augmenter_niveau(5)
        """
        from core.db.query_executor import QueryExecutor

        # Récupérer le niveau actuel
        poly = cls.get_by_id(record_id)
        if not poly:
            return False, "Compétence introuvable"

        niveau_actuel = poly['niveau']
        if niveau_actuel >= 4:
            return False, "Niveau maximum atteint (4)"

        return cls.update(record_id=record_id, niveau=niveau_actuel + 1)

    @classmethod
    def diminuer_niveau(cls, record_id: int) -> Tuple[bool, str]:
        """
        Diminue le niveau d'une compétence (min 1).

        Args:
            record_id: ID de la polyvalence

        Returns:
            (success: bool, message: str)
        """
        poly = cls.get_by_id(record_id)
        if not poly:
            return False, "Compétence introuvable"

        niveau_actuel = poly['niveau']
        if niveau_actuel <= 1:
            return False, "Niveau minimum atteint (1)"

        return cls.update(record_id=record_id, niveau=niveau_actuel - 1)

    @classmethod
    def count_by_operateur(cls, operateur_id: int) -> int:
        """
        Compte le nombre de compétences d'un opérateur.

        Args:
            operateur_id: ID de l'opérateur

        Returns:
            Nombre de compétences

        Example:
            >>> total = PolyvalenceServiceCRUD.count_by_operateur(1)
        """
        return cls.count(operateur_id=operateur_id)

    @classmethod
    def count_by_niveau(cls, niveau: int) -> int:
        """
        Compte le nombre de compétences par niveau.

        Args:
            niveau: Niveau (1-4)

        Returns:
            Nombre de compétences

        Example:
            >>> nb_experts = PolyvalenceServiceCRUD.count_by_niveau(4)
        """
        return cls.count(niveau=niveau)
