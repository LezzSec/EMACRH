# -*- coding: utf-8 -*-
"""
FormationService - Service métier CRUD pour la gestion des formations.

Ce service encapsule toutes les opérations CRUD sur la table formation
avec logging automatique dans l'historique.

Note: Ce service coexiste avec l'ancien formation_service.py.
Pour nouveaux développements, utiliser FormationServiceCRUD.

Usage:
    from core.services.formation_service_crud import FormationServiceCRUD

    # Créer une nouvelle formation
    success, msg, new_id = FormationServiceCRUD.create(
        operateur_id=1,
        intitule="Formation Python",
        organisme="AFPA",
        date_debut=date.today(),
        date_fin=date.today() + timedelta(days=5),
        statut='Planifiée'
    )

    # Mettre à jour le statut
    FormationServiceCRUD.update(record_id=10, statut='Terminée', certificat_obtenu=True)

    # Récupérer toutes les formations d'un opérateur
    formations = FormationServiceCRUD.get_by_operateur(operateur_id=1)
"""

from typing import Dict, List, Optional, Tuple
from datetime import date
from core.services.crud_service import CRUDService


class FormationServiceCRUD(CRUDService):
    """Service métier CRUD pour la table formation."""

    TABLE_NAME = "formation"
    ACTION_PREFIX = "FORMATION_"

    # Champs autorisés pour les mises à jour (sécurité)
    ALLOWED_FIELDS = [
        'operateur_id',
        'intitule',
        'organisme',
        'date_debut',
        'date_fin',
        'duree_heures',
        'statut',
        'certificat_obtenu',
        'cout',
        'commentaire'
    ]

    @classmethod
    def get_by_operateur(
        cls,
        operateur_id: int,
        order_by: str = 'date_debut DESC'
    ) -> List[Dict]:
        """
        Récupère toutes les formations d'un opérateur.

        Args:
            operateur_id: ID de l'opérateur
            order_by: Clause ORDER BY (défaut: 'date_debut DESC')

        Returns:
            Liste de dictionnaires représentant les formations

        Example:
            >>> formations = FormationServiceCRUD.get_by_operateur(1)
            >>> for f in formations:
            ...     print(f"{f['intitule']} - {f['statut']}")
        """
        return cls.get_all(
            conditions={'operateur_id': operateur_id},
            order_by=order_by
        )

    @classmethod
    def get_by_statut(
        cls,
        statut: str,
        order_by: str = 'date_debut ASC'
    ) -> List[Dict]:
        """
        Récupère toutes les formations d'un statut donné.

        Args:
            statut: Statut des formations ('Planifiée', 'En cours', 'Terminée', 'Annulée')
            order_by: Clause ORDER BY

        Returns:
            Liste de formations

        Example:
            >>> planifiees = FormationServiceCRUD.get_by_statut('Planifiée')
        """
        return cls.get_all(
            conditions={'statut': statut},
            order_by=order_by
        )

    @classmethod
    def get_planifiees(cls) -> List[Dict]:
        """Récupère toutes les formations planifiées."""
        return cls.get_by_statut('Planifiée')

    @classmethod
    def get_en_cours(cls) -> List[Dict]:
        """Récupère toutes les formations en cours."""
        return cls.get_by_statut('En cours')

    @classmethod
    def get_terminees(cls) -> List[Dict]:
        """Récupère toutes les formations terminées."""
        return cls.get_by_statut('Terminée')

    @classmethod
    def marquer_terminee(
        cls,
        record_id: int,
        certificat_obtenu: bool = False
    ) -> Tuple[bool, str]:
        """
        Marque une formation comme terminée.

        Args:
            record_id: ID de la formation
            certificat_obtenu: Si le certificat a été obtenu

        Returns:
            (success: bool, message: str)

        Example:
            >>> FormationServiceCRUD.marquer_terminee(10, certificat_obtenu=True)
        """
        return cls.update(
            record_id=record_id,
            statut='Terminée',
            certificat_obtenu=certificat_obtenu
        )

    @classmethod
    def annuler(cls, record_id: int, commentaire: str = None) -> Tuple[bool, str]:
        """
        Annule une formation.

        Args:
            record_id: ID de la formation
            commentaire: Raison de l'annulation (optionnel)

        Returns:
            (success: bool, message: str)
        """
        update_data = {'statut': 'Annulée'}
        if commentaire:
            update_data['commentaire'] = commentaire

        return cls.update(record_id=record_id, **update_data)

    @classmethod
    def count_by_operateur(cls, operateur_id: int) -> int:
        """
        Compte le nombre de formations d'un opérateur.

        Args:
            operateur_id: ID de l'opérateur

        Returns:
            Nombre de formations

        Example:
            >>> total = FormationServiceCRUD.count_by_operateur(1)
        """
        return cls.count(operateur_id=operateur_id)

    @classmethod
    def count_by_statut(cls, statut: str) -> int:
        """
        Compte le nombre de formations par statut.

        Args:
            statut: Statut des formations

        Returns:
            Nombre de formations

        Example:
            >>> nb_planifiees = FormationServiceCRUD.count_by_statut('Planifiée')
        """
        return cls.count(statut=statut)

    @classmethod
    def get_catalogue_competences(cls) -> list:
        """Retourne le catalogue des compétences actives (id, code, libelle, categorie, duree_validite_mois)."""
        from core.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            """
            SELECT id, code, libelle, categorie, duree_validite_mois
            FROM competences_catalogue
            WHERE actif = 1
            ORDER BY categorie, libelle
            """,
            dictionary=True,
        )
