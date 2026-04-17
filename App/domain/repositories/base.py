# -*- coding: utf-8 -*-
"""
Base Repository - Fondation pour tous les repositories.

Fournit:
- SafeQueryBuilder : Construction sécurisée de requêtes dynamiques
- BaseRepository : Classe de base avec opérations CRUD communes

⚠️ RÈGLES DE SÉCURITÉ SQL:
1. JAMAIS de f-string avec des données utilisateur
2. Toujours utiliser %s pour les valeurs
3. Pour les noms de colonnes dynamiques, utiliser WHITELIST uniquement
4. Utiliser SafeQueryBuilder pour les requêtes complexes

✅ BON:
    cur.execute("SELECT * FROM personnel WHERE id = %s", (user_id,))
    builder.where("statut", "=", "ACTIF")

❌ MAUVAIS:
    cur.execute(f"SELECT * FROM personnel WHERE id = {user_id}")
    cur.execute(f"SELECT * FROM {table_name}")
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, TypeVar, Generic, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from infrastructure.db.query_executor import QueryExecutor
from domain.models import ModelMixin

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=ModelMixin)


# ===========================
# Safe Query Builder
# ===========================

class SqlOperator(Enum):
    """Opérateurs SQL autorisés (whitelist)"""
    EQ = "="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    LIKE = "LIKE"
    IN = "IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


@dataclass
class WhereClause:
    """Représente une clause WHERE"""
    column: str
    operator: SqlOperator
    value: Any = None

    def to_sql(self) -> Tuple[str, Optional[Any]]:
        """Génère le SQL et la valeur pour le placeholder"""
        if self.operator == SqlOperator.IS_NULL:
            return f"{self.column} IS NULL", None
        elif self.operator == SqlOperator.IS_NOT_NULL:
            return f"{self.column} IS NOT NULL", None
        elif self.operator == SqlOperator.IN:
            placeholders = ", ".join(["%s"] * len(self.value))
            return f"{self.column} IN ({placeholders})", self.value
        else:
            return f"{self.column} {self.operator.value} %s", self.value


class SafeQueryBuilder:
    """
    Constructeur de requêtes SQL sécurisé.

    Utilise des whitelists pour les noms de colonnes et tables,
    et des placeholders pour toutes les valeurs.

    Usage:
        builder = SafeQueryBuilder("personnel", allowed_columns=["id", "nom", "statut"])
        query, params = (builder
            .select(["id", "nom", "prenom"])
            .where("statut", "=", "ACTIF")
            .where("nom", "LIKE", "DUP%")
            .order_by("nom")
            .limit(10)
            .build())

        cur.execute(query, params)
    """

    # Tables autorisées (whitelist globale - alignée avec emac_structure.sql)
    ALLOWED_TABLES = {
        "personnel", "personnel_infos", "postes", "atelier", "polyvalence",
        "contrat", "demande_absence", "declaration", "formation", "historique",
        "historique_polyvalence", "documents", "categories_documents",
        "documents_templates", "document_event_rules",
        "utilisateurs", "roles", "permissions", "permissions_utilisateur",
        "features", "role_features", "user_features",
        "medical", "medical_visite", "medical_accident_travail",
        "medical_prolongation_arret", "medical_maladie_pro", "validite",
        "vie_salarie_sanction", "vie_salarie_entretien",
        "vie_salarie_alcoolemie", "vie_salarie_test_salivaire",
        "competences_catalogue", "personnel_competences",
        "type_absence", "solde_conges", "jours_feries",
        "batch_operations", "batch_operation_details",
        "logs_connexion", "services", "ref_motif_sortie",
    }

    def __init__(self, table: str, allowed_columns: Optional[List[str]] = None):
        """
        Args:
            table: Nom de la table (doit être dans ALLOWED_TABLES)
            allowed_columns: Liste des colonnes autorisées pour cette requête
        """
        if table not in self.ALLOWED_TABLES:
            raise ValueError(f"Table '{table}' non autorisée. Tables valides: {self.ALLOWED_TABLES}")

        self._table = table
        self._allowed_columns = set(allowed_columns) if allowed_columns else None
        self._select_columns: List[str] = ["*"]
        self._where_clauses: List[WhereClause] = []
        self._order_by: Optional[str] = None
        self._order_dir: str = "ASC"
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._joins: List[str] = []

    def _validate_column(self, column: str) -> str:
        """Valide qu'une colonne est autorisée"""
        # Permettre les alias (table.column)
        base_column = column.split(".")[-1] if "." in column else column

        if self._allowed_columns and base_column not in self._allowed_columns:
            raise ValueError(f"Colonne '{column}' non autorisée. Colonnes valides: {self._allowed_columns}")
        return column

    def select(self, columns: List[str]) -> "SafeQueryBuilder":
        """Définit les colonnes à sélectionner"""
        self._select_columns = [self._validate_column(c) for c in columns]
        return self

    def where(self, column: str, operator: str, value: Any = None) -> "SafeQueryBuilder":
        """
        Ajoute une clause WHERE.

        Args:
            column: Nom de la colonne
            operator: Opérateur (=, !=, <, >, LIKE, IN, IS NULL, etc.)
            value: Valeur (ignorée pour IS NULL/IS NOT NULL)
        """
        column = self._validate_column(column)

        # Convertir l'opérateur string en enum
        op_map = {
            "=": SqlOperator.EQ, "==": SqlOperator.EQ,
            "!=": SqlOperator.NE, "<>": SqlOperator.NE,
            "<": SqlOperator.LT, "<=": SqlOperator.LE,
            ">": SqlOperator.GT, ">=": SqlOperator.GE,
            "LIKE": SqlOperator.LIKE, "like": SqlOperator.LIKE,
            "IN": SqlOperator.IN, "in": SqlOperator.IN,
            "IS NULL": SqlOperator.IS_NULL, "is null": SqlOperator.IS_NULL,
            "IS NOT NULL": SqlOperator.IS_NOT_NULL, "is not null": SqlOperator.IS_NOT_NULL,
        }

        sql_op = op_map.get(operator)
        if sql_op is None:
            raise ValueError(f"Opérateur '{operator}' non autorisé")

        self._where_clauses.append(WhereClause(column, sql_op, value))
        return self

    def where_in(self, column: str, values: List[Any]) -> "SafeQueryBuilder":
        """Raccourci pour WHERE column IN (...)"""
        return self.where(column, "IN", values)

    def where_null(self, column: str) -> "SafeQueryBuilder":
        """Raccourci pour WHERE column IS NULL"""
        return self.where(column, "IS NULL")

    def where_not_null(self, column: str) -> "SafeQueryBuilder":
        """Raccourci pour WHERE column IS NOT NULL"""
        return self.where(column, "IS NOT NULL")

    def order_by(self, column: str, direction: str = "ASC") -> "SafeQueryBuilder":
        """Définit le tri"""
        self._order_by = self._validate_column(column)
        self._order_dir = "DESC" if direction.upper() == "DESC" else "ASC"
        return self

    def limit(self, count: int) -> "SafeQueryBuilder":
        """Limite le nombre de résultats"""
        self._limit = int(count)
        return self

    def offset(self, count: int) -> "SafeQueryBuilder":
        """Définit l'offset"""
        self._offset = int(count)
        return self

    def join(self, table: str, on_clause: str) -> "SafeQueryBuilder":
        """
        Ajoute un JOIN.

        ⚠️ on_clause doit être une expression sûre (pas de données utilisateur)

        Args:
            table: Table à joindre (doit être dans ALLOWED_TABLES)
            on_clause: Clause ON (ex: "p.operateur_id = pers.id")
        """
        if table not in self.ALLOWED_TABLES:
            raise ValueError(f"Table '{table}' non autorisée pour JOIN")
        self._joins.append(f"JOIN {table} ON {on_clause}")
        return self

    def left_join(self, table: str, on_clause: str) -> "SafeQueryBuilder":
        """Ajoute un LEFT JOIN"""
        if table not in self.ALLOWED_TABLES:
            raise ValueError(f"Table '{table}' non autorisée pour LEFT JOIN")
        self._joins.append(f"LEFT JOIN {table} ON {on_clause}")
        return self

    def build(self) -> Tuple[str, Tuple]:
        """
        Construit la requête SQL finale.

        Returns:
            (query_string, parameters_tuple)
        """
        params = []

        # SELECT
        columns_str = ", ".join(self._select_columns)
        query = f"SELECT {columns_str} FROM {self._table}"

        # JOINs
        for join in self._joins:
            query += f" {join}"

        # WHERE
        if self._where_clauses:
            where_parts = []
            for clause in self._where_clauses:
                sql, value = clause.to_sql()
                where_parts.append(sql)
                if value is not None:
                    if isinstance(value, (list, tuple)):
                        params.extend(value)
                    else:
                        params.append(value)
            query += " WHERE " + " AND ".join(where_parts)

        # ORDER BY
        if self._order_by:
            query += f" ORDER BY {self._order_by} {self._order_dir}"

        # LIMIT / OFFSET
        if self._limit is not None:
            query += f" LIMIT {self._limit}"
        if self._offset is not None:
            query += f" OFFSET {self._offset}"

        return query, tuple(params)

    def build_count(self) -> Tuple[str, Tuple]:
        """Construit une requête COUNT(*)"""
        original_select = self._select_columns
        self._select_columns = ["COUNT(*) as total"]

        # Ignorer ORDER BY et LIMIT pour COUNT
        original_order = self._order_by
        original_limit = self._limit
        self._order_by = None
        self._limit = None

        query, params = self.build()

        # Restaurer
        self._select_columns = original_select
        self._order_by = original_order
        self._limit = original_limit

        return query, params


# ===========================
# Base Repository
# ===========================

class BaseRepository(ABC, Generic[T]):
    """
    Classe de base pour tous les repositories.

    Fournit les opérations CRUD communes et encourage
    la centralisation des requêtes.

    Usage:
        class PersonnelRepository(BaseRepository[Personnel]):
            TABLE = "personnel"
            MODEL = Personnel
            COLUMNS = ["id", "nom", "prenom", "statut", ...]
    """

    # À surcharger dans les sous-classes
    TABLE: str = ""
    MODEL: Type[T] = None
    COLUMNS: List[str] = []

    @classmethod
    def _get_builder(cls) -> SafeQueryBuilder:
        """Crée un builder pré-configuré pour ce repository"""
        return SafeQueryBuilder(cls.TABLE, allowed_columns=cls.COLUMNS)

    @classmethod
    def _row_to_model(cls, row: Dict) -> Optional[T]:
        """Convertit une ligne SQL en modèle"""
        if row is None:
            return None
        return cls.MODEL.from_dict(row)

    @classmethod
    def _rows_to_models(cls, rows: List[Dict]) -> List[T]:
        """Convertit des lignes SQL en modèles"""
        return [cls._row_to_model(row) for row in rows if row]

    @classmethod
    def get_by_id(cls, id: int) -> Optional[T]:
        """
        Récupère un enregistrement par son ID.

        Args:
            id: ID de l'enregistrement

        Returns:
            Modèle ou None si non trouvé
        """
        query, params = (cls._get_builder()
            .where("id", "=", id)
            .limit(1)
            .build())

        return cls._row_to_model(QueryExecutor.fetch_one(query, params, dictionary=True))

    @classmethod
    def get_all(cls, limit: int = 1000) -> List[T]:
        """
        Récupère tous les enregistrements.

        Args:
            limit: Nombre maximum de résultats (défaut: 1000)

        Returns:
            Liste de modèles
        """
        query, params = (cls._get_builder()
            .limit(limit)
            .build())

        return cls._rows_to_models(QueryExecutor.fetch_all(query, params, dictionary=True))

    @classmethod
    def count(cls) -> int:
        """Compte le nombre total d'enregistrements"""
        query, params = cls._get_builder().build_count()
        result = QueryExecutor.fetch_one(query, params, dictionary=True)
        return result['total'] if result else 0

    @classmethod
    def exists(cls, id: int) -> bool:
        """Vérifie si un enregistrement existe"""
        return QueryExecutor.fetch_one(
            f"SELECT 1 FROM {cls.TABLE} WHERE id = %s LIMIT 1", (id,)
        ) is not None

    @classmethod
    def delete(cls, id: int) -> bool:
        """
        Supprime un enregistrement.

        Args:
            id: ID de l'enregistrement

        Returns:
            True si supprimé, False sinon
        """
        query = f"DELETE FROM {cls.TABLE} WHERE id = %s"

        try:
            def _do_delete(cur):
                cur.execute(query, (id,))
                return cur.rowcount > 0
            return QueryExecutor.with_transaction(_do_delete)
        except Exception as e:
            logger.error(f"Erreur suppression {cls.TABLE} id={id}: {e}")
            return False

    # ===========================
    # Pagination générique
    # ===========================

    @classmethod
    def get_page(
        cls,
        offset: int = 0,
        limit: int = 50,
        order_by: str = "id",
        order_dir: str = "ASC",
        **filters
    ) -> Tuple[List[T], int]:
        """
        Récupère une page d'enregistrements avec compte total.

        Args:
            offset: Nombre d'enregistrements à sauter
            limit: Nombre d'enregistrements à retourner
            order_by: Colonne de tri (doit être dans COLUMNS)
            order_dir: Direction (ASC/DESC)
            **filters: Filtres dynamiques (ex: statut="ACTIF")

        Returns:
            (liste_modèles, total_count)

        Usage:
            rows, total = PersonnelRepository.get_page(
                offset=0, limit=50,
                order_by="nom",
                statut="ACTIF"
            )
        """
        builder = cls._get_builder()

        # Appliquer les filtres
        for column, value in filters.items():
            if value is not None and column in cls.COLUMNS:
                builder.where(column, "=", value)

        # Ordre et pagination
        if order_by in cls.COLUMNS:
            builder.order_by(order_by, safe_order_direction(order_dir))

        builder.limit(limit).offset(offset)

        # Construire les requêtes
        query, params = builder.build()

        # Réinitialiser pour le comptage
        count_builder = cls._get_builder()
        for column, value in filters.items():
            if value is not None and column in cls.COLUMNS:
                count_builder.where(column, "=", value)
        count_query, count_params = count_builder.build_count()

        rows = cls._rows_to_models(QueryExecutor.fetch_all(query, params, dictionary=True))
        total_row = QueryExecutor.fetch_one(count_query, count_params, dictionary=True)
        total = total_row['total'] if total_row else 0
        return rows, total


# ===========================
# Helpers pour colonnes dynamiques
# ===========================

def safe_column_name(column: str, allowed: List[str]) -> str:
    """
    Valide et retourne un nom de colonne depuis une whitelist.

    Usage:
        column = safe_column_name(user_input, ["nom", "prenom", "statut"])
        cur.execute(f"SELECT {column} FROM personnel")  # Sûr car whitelist

    Raises:
        ValueError si la colonne n'est pas dans la whitelist
    """
    if column not in allowed:
        raise ValueError(f"Colonne '{column}' non autorisée. Valides: {allowed}")
    return column


def safe_order_direction(direction: str) -> str:
    """Valide et retourne une direction de tri (ASC/DESC)"""
    return "DESC" if direction.upper() == "DESC" else "ASC"


def safe_table_name(table: str) -> str:
    """Valide et retourne un nom de table depuis la whitelist globale"""
    if table not in SafeQueryBuilder.ALLOWED_TABLES:
        raise ValueError(f"Table '{table}' non autorisée")
    return table
