# -*- coding: utf-8 -*-
"""
ContratService - Service métier CRUD pour la gestion des contrats.

Ce service encapsule toutes les opérations CRUD sur la table contrat
avec logging automatique dans l'historique.

Note: Ce service coexiste avec l'ancien contrat_service.py.
Pour nouveaux développements, utiliser ContratServiceCRUD.

Usage:
    from core.services.contrat_service_crud import ContratServiceCRUD

    # Créer un nouveau contrat
    success, msg, new_id = ContratServiceCRUD.create(
        operateur_id=1,
        type_contrat="CDI",
        date_debut=date.today(),
        etp=1.00,
        emploi="Technicien",
        actif=1
    )

    # Désactiver un contrat
    ContratServiceCRUD.desactiver(record_id=5)

    # Récupérer tous les contrats d'un opérateur
    contrats = ContratServiceCRUD.get_by_operateur(operateur_id=1)
"""

from typing import Dict, List, Optional, Tuple
from datetime import date
from core.services.crud_service import CRUDService


class ContratServiceCRUD(CRUDService):
    """Service métier CRUD pour la table contrat."""

    TABLE_NAME = "contrat"
    ACTION_PREFIX = "CONTRAT_"

    # Champs autorisés pour les mises à jour (sécurité)
    ALLOWED_FIELDS = [
        'operateur_id',
        'type_contrat',
        'date_debut',
        'date_fin',
        'etp',
        'categorie',
        'echelon',
        'emploi',
        'salaire',
        'actif'
    ]

    @classmethod
    def get_by_operateur(
        cls,
        operateur_id: int,
        actif_only: bool = False,
        order_by: str = 'date_debut DESC'
    ) -> List[Dict]:
        """
        Récupère tous les contrats d'un opérateur.

        Args:
            operateur_id: ID de l'opérateur
            actif_only: Si True, ne retourne que les contrats actifs
            order_by: Clause ORDER BY

        Returns:
            Liste de dictionnaires représentant les contrats

        Example:
            >>> contrats = ContratServiceCRUD.get_by_operateur(1)
            >>> contrats_actifs = ContratServiceCRUD.get_by_operateur(1, actif_only=True)
        """
        conditions = {'operateur_id': operateur_id}
        if actif_only:
            conditions['actif'] = 1

        return cls.get_all(conditions=conditions, order_by=order_by)

    @classmethod
    def get_actifs(cls, order_by: str = 'date_debut DESC') -> List[Dict]:
        """
        Récupère tous les contrats actifs.

        Args:
            order_by: Clause ORDER BY

        Returns:
            Liste de contrats actifs

        Example:
            >>> actifs = ContratServiceCRUD.get_actifs()
        """
        return cls.get_all(conditions={'actif': 1}, order_by=order_by)

    @classmethod
    def get_by_type(
        cls,
        type_contrat: str,
        actif_only: bool = False
    ) -> List[Dict]:
        """
        Récupère tous les contrats d'un type donné.

        Args:
            type_contrat: Type de contrat (CDI, CDD, Intérim, etc.)
            actif_only: Si True, ne retourne que les contrats actifs

        Returns:
            Liste de contrats

        Example:
            >>> cdis = ContratServiceCRUD.get_by_type('CDI', actif_only=True)
        """
        conditions = {'type_contrat': type_contrat}
        if actif_only:
            conditions['actif'] = 1

        return cls.get_all(conditions=conditions, order_by='date_debut DESC')

    @classmethod
    def get_expirant_soon(cls, jours: int = 30) -> List[Dict]:
        """
        Récupère les contrats qui expirent dans les N prochains jours.

        Args:
            jours: Nombre de jours (défaut: 30)

        Returns:
            Liste de contrats arrivant à expiration

        Example:
            >>> expirant_bientot = ContratServiceCRUD.get_expirant_soon(30)
        """
        from core.db.query_executor import QueryExecutor

        query = """
            SELECT *
            FROM contrat
            WHERE actif = 1
              AND date_fin IS NOT NULL
              AND date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
            ORDER BY date_fin ASC
        """

        return QueryExecutor.fetch_all(query, (jours,), dictionary=True)

    @classmethod
    def activer(cls, record_id: int) -> Tuple[bool, str]:
        """
        Active un contrat.

        Args:
            record_id: ID du contrat

        Returns:
            (success: bool, message: str)

        Example:
            >>> ContratServiceCRUD.activer(5)
        """
        return cls.update(record_id=record_id, actif=1)

    @classmethod
    def desactiver(cls, record_id: int) -> Tuple[bool, str]:
        """
        Désactive un contrat.

        Args:
            record_id: ID du contrat

        Returns:
            (success: bool, message: str)

        Example:
            >>> ContratServiceCRUD.desactiver(5)
        """
        return cls.update(record_id=record_id, actif=0)

    @classmethod
    def count_by_operateur(cls, operateur_id: int, actif_only: bool = False) -> int:
        """
        Compte le nombre de contrats d'un opérateur.

        Args:
            operateur_id: ID de l'opérateur
            actif_only: Si True, ne compte que les contrats actifs

        Returns:
            Nombre de contrats

        Example:
            >>> total = ContratServiceCRUD.count_by_operateur(1, actif_only=True)
        """
        conditions = {'operateur_id': operateur_id}
        if actif_only:
            conditions['actif'] = 1

        return cls.count(**conditions)

    @classmethod
    def count_by_type(cls, type_contrat: str, actif_only: bool = False) -> int:
        """
        Compte le nombre de contrats par type.

        Args:
            type_contrat: Type de contrat
            actif_only: Si True, ne compte que les contrats actifs

        Returns:
            Nombre de contrats

        Example:
            >>> nb_cdi = ContratServiceCRUD.count_by_type('CDI', actif_only=True)
        """
        conditions = {'type_contrat': type_contrat}
        if actif_only:
            conditions['actif'] = 1

        return cls.count(**conditions)
