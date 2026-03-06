# -*- coding: utf-8 -*-
"""
CRUDService - Service générique pour opérations CRUD avec logging automatique.

Ce module fournit une classe de base pour créer des services CRUD standardisés
avec audit trail automatique via la table historique.

Usage:
    from core.services.crud_service import CRUDService

    class PersonnelService(CRUDService):
        TABLE_NAME = "personnel"
        ACTION_PREFIX = "PERSONNEL_"
        ALLOWED_FIELDS = ['nom', 'prenom', 'matricule', 'statut']

    # Création
    success, message, new_id = PersonnelService.create(
        nom="Dupont",
        prenom="Jean",
        matricule="JD001",
        statut="ACTIF"
    )

    # Mise à jour
    success, message = PersonnelService.update(
        record_id=1,
        statut="INACTIF"
    )

    # Suppression
    success, message = PersonnelService.delete(record_id=1)
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from core.db.query_executor import QueryExecutor
from core.services.logger import log_hist
from core.utils.logging_config import get_logger

logger = get_logger(__name__)


class CRUDService:
    """
    Classe de base pour services CRUD avec logging automatique.

    À surcharger dans les sous-classes en définissant :
    - TABLE_NAME : nom de la table SQL
    - ACTION_PREFIX : préfixe pour les actions (ex: "PERSONNEL_")
    - ALLOWED_FIELDS : liste des champs autorisés en UPDATE (sécurité)
    """

    TABLE_NAME: str = None
    ACTION_PREFIX: str = None
    ALLOWED_FIELDS: List[str] = []

    @classmethod
    def _validate_config(cls):
        """Vérifie que la configuration est complète."""
        if not cls.TABLE_NAME:
            raise ValueError(f"{cls.__name__}: TABLE_NAME doit être défini")
        if not cls.ACTION_PREFIX:
            raise ValueError(f"{cls.__name__}: ACTION_PREFIX doit être défini")

    @classmethod
    def create(cls, **kwargs) -> Tuple[bool, str, Optional[int]]:
        """
        Crée un nouvel enregistrement avec logging automatique.

        Args:
            **kwargs: Colonnes et valeurs à insérer

        Returns:
            (success: bool, message: str, record_id: int or None)

        Example:
            >>> success, msg, new_id = PersonnelService.create(
            ...     nom="Dupont",
            ...     prenom="Jean",
            ...     matricule="JD001"
            ... )
        """
        cls._validate_config()

        try:
            # Construction de la requête INSERT
            columns = list(kwargs.keys())
            placeholders = ['%s'] * len(columns)
            values = tuple(kwargs.values())

            query = f"""
                INSERT INTO {cls.TABLE_NAME} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """

            # Exécution
            record_id = QueryExecutor.execute_write(query, values, return_lastrowid=True)

            # Logging dans historique
            # ✅ Extraire operateur_id ou personnel_id si présent
            operateur_id = kwargs.get('operateur_id') or kwargs.get('personnel_id')

            log_hist(
                action=f"{cls.ACTION_PREFIX}CREATION",
                table_name=cls.TABLE_NAME,
                record_id=record_id,
                description=f"Enregistrement créé dans {cls.TABLE_NAME}",
                details=kwargs,
                operateur_id=operateur_id  # ✅ Ajouté
            )

            logger.info(f"{cls.TABLE_NAME}: création réussie, ID={record_id}")
            return True, "Création réussie", record_id

        except Exception as e:
            logger.exception(f"Erreur création {cls.TABLE_NAME}: {e}")
            return False, f"Erreur lors de la création : {str(e)}", None

    @classmethod
    def update(
        cls,
        record_id: int,
        validate_fields: bool = True,
        **kwargs
    ) -> Tuple[bool, str]:
        """
        Met à jour un enregistrement avec logging automatique.

        Args:
            record_id: ID de l'enregistrement à modifier
            validate_fields: Si True, vérifie que les champs sont dans ALLOWED_FIELDS
            **kwargs: Colonnes et nouvelles valeurs

        Returns:
            (success: bool, message: str)

        Example:
            >>> success, msg = PersonnelService.update(
            ...     record_id=1,
            ...     statut="INACTIF"
            ... )
        """
        cls._validate_config()

        if not kwargs:
            return False, "Aucun champ à mettre à jour"

        # Validation des champs (sécurité)
        if validate_fields and cls.ALLOWED_FIELDS:
            invalid_fields = set(kwargs.keys()) - set(cls.ALLOWED_FIELDS)
            if invalid_fields:
                return False, f"Champs non autorisés : {', '.join(invalid_fields)}"

        try:
            # Construction de la requête UPDATE
            set_clauses = [f"{k} = %s" for k in kwargs.keys()]
            values = list(kwargs.values()) + [record_id]

            query = f"""
                UPDATE {cls.TABLE_NAME}
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """

            # Exécution
            QueryExecutor.execute_write(query, tuple(values), return_lastrowid=False)

            # Logging dans historique
            # ✅ Extraire operateur_id ou personnel_id si présent dans les données modifiées
            operateur_id = kwargs.get('operateur_id') or kwargs.get('personnel_id')

            # ✅ Si pas dans kwargs, essayer de le récupérer de la table
            if not operateur_id and cls.TABLE_NAME in ('contrat', 'formation', 'polyvalence'):
                try:
                    id_col = 'personnel_id' if cls.TABLE_NAME == 'contrat' else 'operateur_id'
                    result = QueryExecutor.fetch_one(
                        f"SELECT {id_col} FROM {cls.TABLE_NAME} WHERE id = %s",
                        (record_id,),
                        dictionary=True
                    )
                    if result:
                        operateur_id = result.get(id_col)
                except:
                    pass  # Pas grave si ça échoue

            log_hist(
                action=f"{cls.ACTION_PREFIX}UPDATE",
                table_name=cls.TABLE_NAME,
                record_id=record_id,
                description=f"Enregistrement {record_id} modifié",
                details=kwargs,
                operateur_id=operateur_id  # ✅ Ajouté
            )

            logger.info(f"{cls.TABLE_NAME}: mise à jour réussie, ID={record_id}")
            return True, "Mise à jour réussie"

        except Exception as e:
            logger.exception(f"Erreur mise à jour {cls.TABLE_NAME}: {e}")
            return False, f"Erreur lors de la mise à jour : {str(e)}"

    @classmethod
    def delete(
        cls,
        record_id: int,
        soft_delete: bool = False,
        soft_delete_field: str = 'actif'
    ) -> Tuple[bool, str]:
        """
        Supprime (hard ou soft) un enregistrement avec logging automatique.

        Args:
            record_id: ID de l'enregistrement à supprimer
            soft_delete: Si True, marque comme inactif au lieu de supprimer
            soft_delete_field: Nom du champ pour soft delete (défaut: 'actif')

        Returns:
            (success: bool, message: str)

        Example:
            >>> # Hard delete
            >>> success, msg = PersonnelService.delete(record_id=1)
            >>>
            >>> # Soft delete
            >>> success, msg = PersonnelService.delete(
            ...     record_id=1,
            ...     soft_delete=True,
            ...     soft_delete_field='actif'
            ... )
        """
        cls._validate_config()

        try:
            # ✅ Récupérer operateur_id AVANT suppression si la table en a un
            operateur_id = None
            if cls.TABLE_NAME in ('contrat', 'formation', 'polyvalence'):
                try:
                    id_col = 'personnel_id' if cls.TABLE_NAME == 'contrat' else 'operateur_id'
                    result = QueryExecutor.fetch_one(
                        f"SELECT {id_col} FROM {cls.TABLE_NAME} WHERE id = %s",
                        (record_id,),
                        dictionary=True
                    )
                    if result:
                        operateur_id = result.get(id_col)
                except:
                    pass  # Pas grave si ça échoue

            if soft_delete:
                # Soft delete : marquer comme inactif
                query = f"UPDATE {cls.TABLE_NAME} SET {soft_delete_field} = 0 WHERE id = %s"
                action = f"{cls.ACTION_PREFIX}SOFT_DELETE"
                description = f"Enregistrement {record_id} désactivé"
            else:
                # Hard delete : suppression réelle
                query = f"DELETE FROM {cls.TABLE_NAME} WHERE id = %s"
                action = f"{cls.ACTION_PREFIX}DELETE"
                description = f"Enregistrement {record_id} supprimé"

            # Exécution
            QueryExecutor.execute_write(query, (record_id,), return_lastrowid=False)

            # Logging dans historique
            log_hist(
                action=action,
                table_name=cls.TABLE_NAME,
                record_id=record_id,
                description=description,
                operateur_id=operateur_id  # ✅ Ajouté
            )

            logger.info(f"{cls.TABLE_NAME}: suppression réussie, ID={record_id}")
            return True, "Suppression réussie"

        except Exception as e:
            logger.exception(f"Erreur suppression {cls.TABLE_NAME}: {e}")
            return False, f"Erreur lors de la suppression : {str(e)}"

    @classmethod
    def get_by_id(
        cls,
        record_id: int,
        dictionary: bool = True
    ) -> Optional[Dict]:
        """
        Récupère un enregistrement par son ID.

        Args:
            record_id: ID de l'enregistrement
            dictionary: Si True, retourne un dictionnaire

        Returns:
            Dictionnaire ou None si non trouvé

        Example:
            >>> personnel = PersonnelService.get_by_id(1)
            >>> print(personnel['nom'])
        """
        cls._validate_config()

        try:
            query = f"SELECT * FROM {cls.TABLE_NAME} WHERE id = %s"
            return QueryExecutor.fetch_one(query, (record_id,), dictionary=dictionary)
        except Exception as e:
            logger.exception(f"Erreur get_by_id {cls.TABLE_NAME}: {e}")
            return None

    @classmethod
    def get_all(
        cls,
        conditions: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        dictionary: bool = True
    ) -> List[Dict]:
        """
        Récupère tous les enregistrements avec filtres optionnels.

        Args:
            conditions: Dictionnaire {colonne: valeur} pour filtrage
            order_by: Clause ORDER BY (ex: "nom ASC")
            limit: Nombre maximum de résultats
            dictionary: Si True, retourne des dictionnaires

        Returns:
            Liste de dictionnaires

        Example:
            >>> # Tous les actifs
            >>> actifs = PersonnelService.get_all(
            ...     conditions={'statut': 'ACTIF'},
            ...     order_by='nom ASC'
            ... )
        """
        cls._validate_config()

        try:
            query = f"SELECT * FROM {cls.TABLE_NAME}"
            params = []

            # Conditions WHERE
            if conditions:
                where_clauses = [f"{k} = %s" for k in conditions.keys()]
                query += " WHERE " + " AND ".join(where_clauses)
                params.extend(conditions.values())

            # ORDER BY
            if order_by:
                query += f" ORDER BY {order_by}"

            # LIMIT
            if limit:
                query += f" LIMIT {limit}"

            return QueryExecutor.fetch_all(query, tuple(params), dictionary=dictionary)

        except Exception as e:
            logger.exception(f"Erreur get_all {cls.TABLE_NAME}: {e}")
            return []

    @classmethod
    def exists(cls, **conditions) -> bool:
        """
        Vérifie si un enregistrement existe selon les conditions.

        Args:
            **conditions: Colonnes et valeurs à vérifier

        Returns:
            True si au moins un enregistrement existe

        Example:
            >>> exists = PersonnelService.exists(matricule="JD001")
        """
        cls._validate_config()

        try:
            return QueryExecutor.exists(cls.TABLE_NAME, conditions)
        except Exception as e:
            logger.exception(f"Erreur exists {cls.TABLE_NAME}: {e}")
            return False

    @classmethod
    def count(cls, **conditions) -> int:
        """
        Compte le nombre d'enregistrements selon les conditions.

        Args:
            **conditions: Colonnes et valeurs à vérifier

        Returns:
            Nombre d'enregistrements

        Example:
            >>> total = PersonnelService.count()
            >>> actifs = PersonnelService.count(statut='ACTIF')
        """
        cls._validate_config()

        try:
            return QueryExecutor.count(cls.TABLE_NAME, conditions if conditions else None)
        except Exception as e:
            logger.exception(f"Erreur count {cls.TABLE_NAME}: {e}")
            return 0
