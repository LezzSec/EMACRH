# -*- coding: utf-8 -*-
"""
GenericRepository — implémentation concrète de IRepository pour tables sans repo dédié.

Centralise le SQL générique (INSERT / UPDATE / DELETE / SELECT) qui résidait
dans CRUDService. Les services passent par cette classe via IRepository —
ils ne voient jamais le SQL.

Usage (interne, via CRUDService uniquement) :
    repo = GenericRepository(
        table_name="formation",
        allowed_fields=["operateur_id", "intitule", "date_formation"],
        owner_column="operateur_id",
    )
    new_id = repo.create({"operateur_id": 1, "intitule": "Sécurité"})
    repo.update(new_id, {"intitule": "Sécurité incendie"})
    repo.delete(new_id)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from infrastructure.db.query_executor import QueryExecutor
from core.repositories.base import safe_table_name
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# Regex de validation des noms de colonnes (protection SQL injection)
_SAFE_COLUMN_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

# Regex de validation d'une expression ORDER BY : "colonne" ou "colonne ASC/DESC"
_SAFE_ORDER_BY_RE = re.compile(
    r'^[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?$',
    re.IGNORECASE,
)


def _assert_safe_column(name: str) -> str:
    """Valide qu'un nom de colonne ne contient pas de caractères dangereux."""
    if not _SAFE_COLUMN_RE.match(name):
        raise ValueError(f"Nom de colonne invalide : '{name}'")
    return name


def _assert_safe_order_by(order_by: str) -> str:
    """Valide qu'une expression ORDER BY est de la forme 'colonne [ASC|DESC]'."""
    if not _SAFE_ORDER_BY_RE.match(order_by.strip()):
        raise ValueError(f"Expression ORDER BY invalide : '{order_by}'")
    return order_by.strip()


class GenericRepository:
    """
    Repository générique CRUD sur une table MySQL.

    Implémente structurellement IRepository[Dict] (Protocol).

    Paramètres de construction :
        table_name:     nom de la table (doit être dans la whitelist)
        allowed_fields: colonnes autorisées en INSERT / UPDATE (sécurité)
        owner_column:   colonne contenant l'ID du personnel propriétaire
                        (ex: 'operateur_id', 'personnel_id') — pour le logging
    """

    def __init__(
        self,
        table_name: str,
        allowed_fields: Optional[List[str]] = None,
        owner_column: Optional[str] = None,
    ) -> None:
        self._table = safe_table_name(table_name)
        self._allowed_fields: Optional[frozenset] = (
            frozenset(allowed_fields) if allowed_fields else None
        )
        self._owner_column: Optional[str] = (
            _assert_safe_column(owner_column) if owner_column else None
        )

    # ------------------------------------------------------------------
    # Écriture
    # ------------------------------------------------------------------

    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """
        Insère un enregistrement.

        Les colonnes sont validées contre allowed_fields si défini.

        Returns:
            ID du nouvel enregistrement
        """
        safe_data = self._filter_and_validate(data)
        if not safe_data:
            raise ValueError("Aucun champ valide à insérer")

        columns = [_assert_safe_column(k) for k in safe_data.keys()]
        placeholders = ["%s"] * len(columns)
        values = tuple(safe_data.values())

        query = (
            f"INSERT INTO {self._table} ({', '.join(columns)})"
            f" VALUES ({', '.join(placeholders)})"
        )
        return QueryExecutor.execute_write(query, values, return_lastrowid=True)

    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Met à jour un enregistrement existant.

        Returns:
            True (lève une exception en cas d'erreur)
        """
        safe_data = self._filter_and_validate(data)
        if not safe_data:
            raise ValueError("Aucun champ valide à mettre à jour")

        set_clauses = [f"{_assert_safe_column(k)} = %s" for k in safe_data.keys()]
        values = list(safe_data.values()) + [record_id]

        query = (
            f"UPDATE {self._table}"
            f" SET {', '.join(set_clauses)}"
            f" WHERE id = %s"
        )
        QueryExecutor.execute_write(query, tuple(values), return_lastrowid=False)
        return True

    def delete(self, record_id: int) -> bool:
        """Supprime définitivement un enregistrement."""
        QueryExecutor.execute_write(
            f"DELETE FROM {self._table} WHERE id = %s",
            (record_id,),
            return_lastrowid=False,
        )
        return True

    def soft_delete(self, record_id: int, field: str = "actif") -> bool:
        """Marque un enregistrement comme inactif (soft delete)."""
        _assert_safe_column(field)
        QueryExecutor.execute_write(
            f"UPDATE {self._table} SET {field} = 0 WHERE id = %s",
            (record_id,),
            return_lastrowid=False,
        )
        return True

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un enregistrement par son ID."""
        return QueryExecutor.fetch_one(
            f"SELECT * FROM {self._table} WHERE id = %s",
            (record_id,),
            dictionary=True,
        )

    def get_all(
        self,
        conditions: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Récupère des enregistrements avec filtres optionnels.

        Note : order_by est une expression de confiance interne
               (jamais exposée directement à l'utilisateur).
        """
        query = f"SELECT * FROM {self._table}"
        params: List[Any] = []

        if conditions:
            clauses = [
                f"{_assert_safe_column(k)} = %s" for k in conditions.keys()
            ]
            query += " WHERE " + " AND ".join(clauses)
            params.extend(conditions.values())

        if order_by:
            query += f" ORDER BY {_assert_safe_order_by(order_by)}"

        if limit is not None:
            query += f" LIMIT {int(limit)}"

        return QueryExecutor.fetch_all(query, tuple(params), dictionary=True)

    def exists(self, record_id: int) -> bool:
        """Vérifie si un enregistrement existe par son ID."""
        return QueryExecutor.exists(self._table, {"id": record_id})

    def count(self, conditions: Optional[Dict[str, Any]] = None) -> int:
        """Compte les enregistrements selon des conditions optionnelles."""
        return QueryExecutor.count(self._table, conditions or None)

    def get_owner_id(self, record_id: int) -> Optional[int]:
        """
        Retourne l'ID du personnel propriétaire de cet enregistrement.

        Utilisé par CRUDService pour alimenter l'historique.
        """
        if not self._owner_column:
            return None
        result = QueryExecutor.fetch_one(
            f"SELECT {self._owner_column} FROM {self._table} WHERE id = %s",
            (record_id,),
            dictionary=True,
        )
        return result.get(self._owner_column) if result else None

    # ------------------------------------------------------------------
    # Helpers privés
    # ------------------------------------------------------------------

    def _filter_and_validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filtre les champs selon allowed_fields et valide les noms de colonnes.

        - Si allowed_fields est défini : retire les champs non autorisés.
        - Toujours : valide les noms de colonnes contre la regex sûre.
        """
        if self._allowed_fields is not None:
            invalid = set(data.keys()) - self._allowed_fields
            if invalid:
                raise ValueError(f"Champs non autorisés : {sorted(invalid)}")
            return {k: v for k, v in data.items() if k in self._allowed_fields}
        return dict(data)
