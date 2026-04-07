# -*- coding: utf-8 -*-
"""
CRUDService — service générique CRUD avec logging automatique.

Délègue toutes les opérations de base de données à GenericRepository (via IRepository).
Ce service ne contient aucun SQL : il orchestre uniquement la logique métier
(validation, logging, gestion des erreurs).

Architecture :
    CRUDService → IRepository → GenericRepository → QueryExecutor → MySQL

Usage :
    from core.services.crud_service import CRUDService

    class PersonnelService(CRUDService):
        TABLE_NAME = "personnel"
        ACTION_PREFIX = "PERSONNEL_"
        ALLOWED_FIELDS = ['nom', 'prenom', 'matricule', 'statut']

    success, msg, new_id = PersonnelService.create(nom="Dupont", prenom="Jean")
    success, msg = PersonnelService.update(record_id=1, statut="INACTIF")
    success, msg = PersonnelService.delete(record_id=1)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from infrastructure.logging.optimized_db_logger import log_hist
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# Colonne "propriétaire" par table — pour alimenter l'historique
_OWNER_COLUMNS: Dict[str, str] = {
    "contrat": "personnel_id",
    "formation": "personnel_id",
    "polyvalence": "personnel_id",
    "demande_absence": "personnel_id",
    "declaration": "personnel_id",
}


class CRUDService:
    """
    Classe de base pour services CRUD avec logging automatique.

    Règle : aucun SQL ici. Toute interaction avec la DB passe par IRepository.

    À surcharger dans les sous-classes :
        TABLE_NAME:     nom de la table SQL
        ACTION_PREFIX:  préfixe des codes action dans l'historique
        ALLOWED_FIELDS: champs autorisés en INSERT / UPDATE (sécurité)
    """

    TABLE_NAME: str = None
    ACTION_PREFIX: str = None
    ALLOWED_FIELDS: List[str] = []

    # Feature requise pour create/update (None = pas de vérification)
    WRITE_FEATURE: Optional[str] = None
    # Feature requise pour delete (None = utilise WRITE_FEATURE)
    DELETE_FEATURE: Optional[str] = None

    # Cache de repositories — une instance par sous-classe
    _repo_cache: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Repository (couche données)
    # ------------------------------------------------------------------

    @classmethod
    def _get_repository(cls):
        """
        Retourne le GenericRepository configuré pour cette sous-classe.

        Le repository est instancié une seule fois (singleton par classe).
        """
        cache_key = cls.__name__
        if cache_key not in cls._repo_cache:
            from core.repositories.generic_repo import GenericRepository
            cls._repo_cache[cache_key] = GenericRepository(
                table_name=cls.TABLE_NAME,
                allowed_fields=cls.ALLOWED_FIELDS or None,
                owner_column=_OWNER_COLUMNS.get(cls.TABLE_NAME),
            )
        return cls._repo_cache[cache_key]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @classmethod
    def _validate_config(cls) -> None:
        """Vérifie que TABLE_NAME et ACTION_PREFIX sont définis."""
        if not cls.TABLE_NAME:
            raise ValueError(f"{cls.__name__}: TABLE_NAME doit être défini")
        if not cls.ACTION_PREFIX:
            raise ValueError(f"{cls.__name__}: ACTION_PREFIX doit être défini")

    # ------------------------------------------------------------------
    # Écriture
    # ------------------------------------------------------------------

    @classmethod
    def create(cls, **kwargs) -> Tuple[bool, str, Optional[int]]:
        """
        Crée un enregistrement avec logging automatique.

        Args:
            **kwargs: colonnes et valeurs à insérer

        Returns:
            (success, message, record_id)

        Example:
            >>> success, msg, new_id = PersonnelService.create(
            ...     nom="Dupont", prenom="Jean", statut="ACTIF"
            ... )
        """
        cls._validate_config()
        if cls.WRITE_FEATURE:
            from core.services.permission_manager import require
            require(cls.WRITE_FEATURE)
        try:
            repo = cls._get_repository()
            record_id = repo.create(dict(kwargs))

            operateur_id = kwargs.get("operateur_id") or kwargs.get("personnel_id")
            log_hist(
                action=f"{cls.ACTION_PREFIX}CREATION",
                table_name=cls.TABLE_NAME,
                record_id=record_id,
                description=f"Enregistrement créé dans {cls.TABLE_NAME}",
                details=kwargs,
                operateur_id=operateur_id,
            )

            logger.info(f"{cls.TABLE_NAME}: création réussie, ID={record_id}")
            return True, "Création réussie", record_id

        except Exception as e:
            logger.exception(f"Erreur création {cls.TABLE_NAME}: {e}")
            return False, "Une erreur est survenue lors de la création", None

    @classmethod
    def update(
        cls,
        record_id: int,
        validate_fields: bool = True,
        **kwargs,
    ) -> Tuple[bool, str]:
        """
        Met à jour un enregistrement avec logging automatique.

        Args:
            record_id: ID de l'enregistrement à modifier
            validate_fields: si True, vérifie que les champs sont dans ALLOWED_FIELDS
            **kwargs: colonnes et nouvelles valeurs

        Returns:
            (success, message)

        Example:
            >>> success, msg = PersonnelService.update(record_id=1, statut="INACTIF")
        """
        cls._validate_config()
        if cls.WRITE_FEATURE:
            from core.services.permission_manager import require
            require(cls.WRITE_FEATURE)

        if not kwargs:
            return False, "Aucun champ à mettre à jour"

        if validate_fields and cls.ALLOWED_FIELDS:
            invalid = set(kwargs.keys()) - set(cls.ALLOWED_FIELDS)
            if invalid:
                return False, f"Champs non autorisés : {', '.join(sorted(invalid))}"

        try:
            repo = cls._get_repository()
            repo.update(record_id, dict(kwargs))

            operateur_id = kwargs.get("operateur_id") or kwargs.get("personnel_id")
            if not operateur_id:
                operateur_id = repo.get_owner_id(record_id)

            log_hist(
                action=f"{cls.ACTION_PREFIX}UPDATE",
                table_name=cls.TABLE_NAME,
                record_id=record_id,
                description=f"Enregistrement {record_id} modifié",
                details=kwargs,
                operateur_id=operateur_id,
            )

            logger.info(f"{cls.TABLE_NAME}: mise à jour réussie, ID={record_id}")
            return True, "Mise à jour réussie"

        except Exception as e:
            logger.exception(f"Erreur mise à jour {cls.TABLE_NAME}: {e}")
            return False, "Une erreur est survenue lors de la mise à jour"

    @classmethod
    def delete(
        cls,
        record_id: int,
        soft_delete: bool = False,
        soft_delete_field: str = "actif",
    ) -> Tuple[bool, str]:
        """
        Supprime (hard ou soft) un enregistrement avec logging automatique.

        Args:
            record_id: ID de l'enregistrement à supprimer
            soft_delete: si True, marque comme inactif au lieu de supprimer
            soft_delete_field: colonne à mettre à 0 pour le soft delete

        Returns:
            (success, message)

        Example:
            >>> success, msg = PersonnelService.delete(record_id=1)
            >>> success, msg = PersonnelService.delete(record_id=1, soft_delete=True)
        """
        cls._validate_config()
        _delete_feature = cls.DELETE_FEATURE or cls.WRITE_FEATURE
        if _delete_feature:
            from core.services.permission_manager import require
            require(_delete_feature)

        try:
            repo = cls._get_repository()
            operateur_id = repo.get_owner_id(record_id)

            if soft_delete:
                repo.soft_delete(record_id, soft_delete_field)
                action = f"{cls.ACTION_PREFIX}SOFT_DELETE"
                description = f"Enregistrement {record_id} désactivé"
            else:
                repo.delete(record_id)
                action = f"{cls.ACTION_PREFIX}DELETE"
                description = f"Enregistrement {record_id} supprimé"

            log_hist(
                action=action,
                table_name=cls.TABLE_NAME,
                record_id=record_id,
                description=description,
                operateur_id=operateur_id,
            )

            logger.info(f"{cls.TABLE_NAME}: suppression réussie, ID={record_id}")
            return True, "Suppression réussie"

        except Exception as e:
            logger.exception(f"Erreur suppression {cls.TABLE_NAME}: {e}")
            return False, "Une erreur est survenue lors de la suppression"

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    @classmethod
    def get_by_id(cls, record_id: int) -> Optional[Dict]:
        """
        Récupère un enregistrement par son ID.

        Returns:
            Dictionnaire ou None si non trouvé

        Example:
            >>> personnel = PersonnelService.get_by_id(1)
        """
        cls._validate_config()
        try:
            return cls._get_repository().get_by_id(record_id)
        except Exception as e:
            logger.exception(f"Erreur get_by_id {cls.TABLE_NAME}: {e}")
            return None

    @classmethod
    def get_all(
        cls,
        conditions: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        Récupère des enregistrements avec filtres optionnels.

        Args:
            conditions: {colonne: valeur} — filtre égalité strict
            order_by: expression ORDER BY (ex: "nom ASC")
            limit: nombre maximum de résultats

        Returns:
            Liste de dictionnaires

        Example:
            >>> actifs = PersonnelService.get_all(
            ...     conditions={"statut": "ACTIF"},
            ...     order_by="nom ASC"
            ... )
        """
        cls._validate_config()
        try:
            return cls._get_repository().get_all(conditions, order_by, limit)
        except Exception as e:
            logger.exception(f"Erreur get_all {cls.TABLE_NAME}: {e}")
            return []

    @classmethod
    def exists(cls, **conditions) -> bool:
        """
        Vérifie si un enregistrement existe.

        Example:
            >>> exists = PersonnelService.exists(matricule="JD001")
        """
        cls._validate_config()
        try:
            if "id" in conditions and len(conditions) == 1:
                return cls._get_repository().exists(conditions["id"])
            return cls._get_repository().count(conditions) > 0
        except Exception as e:
            logger.exception(f"Erreur exists {cls.TABLE_NAME}: {e}")
            return False

    @classmethod
    def count(cls, **conditions) -> int:
        """
        Compte les enregistrements.

        Example:
            >>> total = PersonnelService.count()
            >>> actifs = PersonnelService.count(statut="ACTIF")
        """
        cls._validate_config()
        try:
            return cls._get_repository().count(conditions if conditions else None)
        except Exception as e:
            logger.exception(f"Erreur count {cls.TABLE_NAME}: {e}")
            return 0
