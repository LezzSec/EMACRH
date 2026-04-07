# -*- coding: utf-8 -*-
"""
PersonnelService - Service métier pour la gestion du personnel.

Ce service encapsule toutes les opérations CRUD sur la table personnel
avec logging automatique dans l'historique.

Usage:
    from domain.services.personnel.personnel_service import PersonnelService

    # Créer un nouveau personnel
    success, msg, new_id = PersonnelService.create(
        nom="Dupont",
        prenom="Jean",
        statut="ACTIF"
    )

    # Mettre à jour le statut
    PersonnelService.update(record_id=1, statut="INACTIF")

    # Récupérer tous les actifs
    actifs = PersonnelService.get_all(
        conditions={'statut': 'ACTIF'},
        order_by='nom, prenom'
    )
"""

from typing import Dict, List, Optional, Tuple
from application.crud_service import CRUDService


class PersonnelService(CRUDService):
    """Service métier pour la table personnel."""

    TABLE_NAME = "personnel"
    ACTION_PREFIX = "PERSONNEL_"
    WRITE_FEATURE = "rh.personnel.edit"
    DELETE_FEATURE = "rh.personnel.delete"

    # Champs autorisés pour les mises à jour (sécurité)
    ALLOWED_FIELDS = [
        'nom',
        'prenom',
        'statut'
    ]

    @classmethod
    def get_actifs(cls, order_by: str = 'nom, prenom') -> List[Dict]:
        """
        Récupère tous les personnels actifs.

        Args:
            order_by: Clause ORDER BY (défaut: 'nom, prenom')

        Returns:
            Liste de dictionnaires représentant les personnels actifs

        Example:
            >>> actifs = PersonnelService.get_actifs()
            >>> for p in actifs:
            ...     print(f"{p['nom']} {p['prenom']}")
        """
        return cls.get_all(
            conditions={'statut': 'ACTIF'},
            order_by=order_by
        )

    @classmethod
    def get_inactifs(cls, order_by: str = 'nom, prenom') -> List[Dict]:
        """
        Récupère tous les personnels inactifs.

        Args:
            order_by: Clause ORDER BY (défaut: 'nom, prenom')

        Returns:
            Liste de dictionnaires représentant les personnels inactifs
        """
        return cls.get_all(
            conditions={'statut': 'INACTIF'},
            order_by=order_by
        )

    @classmethod
    def activer(cls, record_id: int) -> Tuple[bool, str]:
        """
        Active un personnel (statut = ACTIF).

        Args:
            record_id: ID du personnel

        Returns:
            (success: bool, message: str)

        Example:
            >>> success, msg = PersonnelService.activer(1)
        """
        return cls.update(record_id=record_id, statut='ACTIF')

    @classmethod
    def desactiver(cls, record_id: int) -> Tuple[bool, str]:
        """
        Désactive un personnel (statut = INACTIF).

        Args:
            record_id: ID du personnel

        Returns:
            (success: bool, message: str)

        Example:
            >>> success, msg = PersonnelService.desactiver(1)
        """
        return cls.update(record_id=record_id, statut='INACTIF')

    @classmethod
    def count_actifs(cls) -> int:
        """
        Compte le nombre de personnels actifs.

        Returns:
            Nombre de personnels actifs

        Example:
            >>> total = PersonnelService.count_actifs()
            >>> print(f"Total actifs: {total}")
        """
        return cls.count(statut='ACTIF')

    @classmethod
    def count_inactifs(cls) -> int:
        """
        Compte le nombre de personnels inactifs.

        Returns:
            Nombre de personnels inactifs
        """
        return cls.count(statut='INACTIF')
