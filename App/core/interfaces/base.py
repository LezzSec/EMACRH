# -*- coding: utf-8 -*-
"""
IRepository — contrat de base pour tous les repositories.

Définit les opérations CRUD génériques que tout repository doit exposer.
Les repositories l'implémentent structurellement (Protocol = duck typing).

Règle : les services importent uniquement ces interfaces, jamais les classes concrètes.
"""

from __future__ import annotations
from typing import Any, Dict, Generic, List, Optional, Protocol, Tuple, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class IRepository(Protocol[T]):
    """
    Contrat générique CRUD.

    T est le type retourné (modèle dataclass ou Dict selon le repository).

    Méthodes de lecture :
        get_by_id, get_all, exists, count, get_owner_id

    Méthodes d'écriture :
        create, update, delete, soft_delete
    """

    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """
        Insère un enregistrement.

        Args:
            data: colonnes → valeurs à insérer

        Returns:
            ID du nouvel enregistrement, ou None en cas d'erreur
        """
        ...

    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Met à jour un enregistrement existant.

        Args:
            record_id: ID de l'enregistrement
            data: colonnes → nouvelles valeurs

        Returns:
            True si la mise à jour a réussi
        """
        ...

    def delete(self, record_id: int) -> bool:
        """
        Supprime définitivement un enregistrement.

        Args:
            record_id: ID de l'enregistrement

        Returns:
            True si supprimé
        """
        ...

    def soft_delete(self, record_id: int, field: str = "actif") -> bool:
        """
        Désactive un enregistrement sans le supprimer (soft delete).

        Args:
            record_id: ID de l'enregistrement
            field: colonne booléenne à mettre à 0 (défaut: 'actif')

        Returns:
            True si désactivé
        """
        ...

    def get_by_id(self, record_id: int) -> Optional[T]:
        """
        Récupère un enregistrement par son ID.

        Returns:
            Modèle ou dict, None si absent
        """
        ...

    def get_all(
        self,
        conditions: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[T]:
        """
        Récupère des enregistrements avec filtres optionnels.

        Args:
            conditions: {colonne: valeur} — filtre égalité strict
            order_by: expression ORDER BY (ex: "nom ASC")
            limit: nombre maximum de résultats

        Returns:
            Liste de modèles ou dicts
        """
        ...

    def exists(self, record_id: int) -> bool:
        """Vérifie si un enregistrement existe par son ID."""
        ...

    def count(self, conditions: Optional[Dict[str, Any]] = None) -> int:
        """
        Compte les enregistrements.

        Args:
            conditions: filtres optionnels {colonne: valeur}

        Returns:
            Nombre d'enregistrements correspondants
        """
        ...

    def get_owner_id(self, record_id: int) -> Optional[int]:
        """
        Retourne l'ID du propriétaire (personnel / opérateur) pour le logging.

        Utile pour alimenter l'historique lors d'opérations sur des tables
        liées à un personnel (contrats, formations, polyvalence…).

        Returns:
            ID du personnel associé, ou None si non applicable
        """
        ...
