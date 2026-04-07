# -*- coding: utf-8 -*-
"""
QueryExecutor - Wrapper centralisé pour simplifier les accès base de données.

Ce module fournit des méthodes utilitaires pour exécuter des requêtes SQL
de manière standardisée, réduisant le code boilerplate dans les services.

Usage:
    from infrastructure.db.query_executor import QueryExecutor

    # Récupérer plusieurs lignes
    users = QueryExecutor.fetch_all("SELECT * FROM personnel WHERE statut = %s", ('ACTIF',))

    # Récupérer une ligne
    user = QueryExecutor.fetch_one("SELECT * FROM personnel WHERE id = %s", (user_id,))

    # Insertion/Update/Delete
    new_id = QueryExecutor.execute_write("INSERT INTO personnel (...) VALUES (...)", (...))
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from infrastructure.db.configbd import DatabaseConnection, DatabaseCursor
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# Regex stricte : lettres, chiffres, underscores uniquement (pas d'espaces, tirets, points)
_IDENTIFIER_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def _validate_identifier(name: str, kind: str = "identifiant") -> None:
    """
    Valide qu'un nom de table ou de colonne ne contient que des caractères autorisés.
    Lève ValueError si le nom est suspect (injection SQL potentielle).
    """
    if not name or not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Nom {kind} invalide (injection SQL potentielle): {name!r}")


class QueryExecutor:
    """Exécuteur centralisé de requêtes SQL avec gestion standardisée."""

    @staticmethod
    def fetch_all(
        query: str,
        params: Optional[Tuple] = None,
        dictionary: bool = False
    ) -> List[Union[Tuple, Dict]]:
        """
        Exécute une requête SELECT et retourne toutes les lignes.

        Args:
            query: Requête SQL SELECT
            params: Paramètres de la requête (tuple)
            dictionary: Si True, retourne des dictionnaires au lieu de tuples

        Returns:
            Liste de tuples ou dictionnaires selon le paramètre dictionary

        Raises:
            Exception: En cas d'erreur SQL

        Example:
            >>> personnel = QueryExecutor.fetch_all(
            ...     "SELECT id, nom, prenom FROM personnel WHERE statut = %s",
            ...     ('ACTIF',),
            ...     dictionary=True
            ... )
            >>> print(personnel[0]['nom'])
        """
        try:
            with DatabaseCursor(dictionary=dictionary) as cur:
                cur.execute(query, params or ())
                result = cur.fetchall()
                logger.debug(f"fetch_all: {len(result)} lignes récupérées")
                return result
        except Exception as e:
            logger.error(f"Erreur fetch_all: {e}", exc_info=True)
            raise

    @staticmethod
    def fetch_one(
        query: str,
        params: Optional[Tuple] = None,
        dictionary: bool = False
    ) -> Optional[Union[Tuple, Dict]]:
        """
        Exécute une requête SELECT et retourne une seule ligne.

        Args:
            query: Requête SQL SELECT
            params: Paramètres de la requête (tuple)
            dictionary: Si True, retourne un dictionnaire au lieu d'un tuple

        Returns:
            Tuple ou dictionnaire, ou None si aucun résultat

        Example:
            >>> user = QueryExecutor.fetch_one(
            ...     "SELECT * FROM personnel WHERE id = %s",
            ...     (user_id,),
            ...     dictionary=True
            ... )
        """
        try:
            with DatabaseCursor(dictionary=dictionary) as cur:
                cur.execute(query, params or ())
                result = cur.fetchone()
                logger.debug(f"fetch_one: {'trouvé' if result else 'non trouvé'}")
                return result
        except Exception as e:
            logger.error(f"Erreur fetch_one: {e}", exc_info=True)
            raise

    @staticmethod
    def fetch_scalar(
        query: str,
        params: Optional[Tuple] = None,
        default: Any = None
    ) -> Any:
        """
        Exécute une requête et retourne la première colonne de la première ligne.
        Utile pour COUNT, MAX, etc.

        Args:
            query: Requête SQL (doit retourner une seule colonne)
            params: Paramètres de la requête
            default: Valeur par défaut si aucun résultat

        Returns:
            La valeur scalaire ou default

        Example:
            >>> count = QueryExecutor.fetch_scalar("SELECT COUNT(*) FROM personnel")
            >>> max_id = QueryExecutor.fetch_scalar("SELECT MAX(id) FROM personnel", default=0)
        """
        try:
            with DatabaseCursor() as cur:
                cur.execute(query, params or ())
                result = cur.fetchone()
                return result[0] if result else default
        except Exception as e:
            logger.error(f"Erreur fetch_scalar: {e}", exc_info=True)
            raise

    @staticmethod
    def execute_write(
        query: str,
        params: Optional[Tuple] = None,
        return_lastrowid: bool = True
    ) -> Union[int, bool]:
        """
        Exécute une requête d'écriture (INSERT, UPDATE, DELETE) avec commit automatique.

        Args:
            query: Requête SQL d'écriture
            params: Paramètres de la requête
            return_lastrowid: Si True, retourne l'ID inséré (pour INSERT), sinon True

        Returns:
            ID de la dernière insertion (INSERT) ou True (UPDATE/DELETE)

        Raises:
            Exception: En cas d'erreur SQL (rollback automatique)

        Example:
            >>> # INSERT
            >>> new_id = QueryExecutor.execute_write(
            ...     "INSERT INTO personnel (nom, prenom) VALUES (%s, %s)",
            ...     ('Dupont', 'Jean')
            ... )
            >>>
            >>> # UPDATE
            >>> QueryExecutor.execute_write(
            ...     "UPDATE personnel SET statut = %s WHERE id = %s",
            ...     ('INACTIF', user_id),
            ...     return_lastrowid=False
            ... )
        """
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                try:
                    cur.execute(query, params or ())

                    # Auto-commit géré par le context manager DatabaseConnection
                    if return_lastrowid and 'INSERT' in query.upper():
                        result = cur.lastrowid
                        logger.debug(f"execute_write: INSERT réussi, ID={result}")
                        return result
                    else:
                        affected = cur.rowcount
                        logger.debug(f"execute_write: {affected} lignes affectées")
                        return True
                finally:
                    cur.close()
        except Exception as e:
            logger.error(f"Erreur execute_write: {e}", exc_info=True)
            raise

    @staticmethod
    def execute_many(
        query: str,
        params_list: List[Tuple]
    ) -> int:
        """
        Exécute une requête d'écriture multiple (batch INSERT/UPDATE/DELETE).

        Args:
            query: Requête SQL avec placeholders
            params_list: Liste de tuples de paramètres

        Returns:
            Nombre total de lignes affectées

        Example:
            >>> QueryExecutor.execute_many(
            ...     "INSERT INTO polyvalence (operateur_id, poste_id, niveau) VALUES (%s, %s, %s)",
            ...     [(1, 10, 2), (1, 11, 3), (2, 10, 1)]
            ... )
        """
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                try:
                    cur.executemany(query, params_list)
                    affected = cur.rowcount
                    logger.debug(f"execute_many: {affected} lignes affectées")
                    return affected
                finally:
                    cur.close()
        except Exception as e:
            logger.error(f"Erreur execute_many: {e}", exc_info=True)
            raise

    @staticmethod
    def exists(
        table: str,
        conditions: Dict[str, Any]
    ) -> bool:
        """
        Vérifie si un enregistrement existe selon les conditions données.

        Args:
            table: Nom de la table
            conditions: Dictionnaire {colonne: valeur}

        Returns:
            True si au moins un enregistrement existe

        Example:
            >>> exists = QueryExecutor.exists(
            ...     'polyvalence',
            ...     {'operateur_id': 1, 'poste_id': 10}
            ... )
        """
        _validate_identifier(table, "table")
        for col in conditions.keys():
            _validate_identifier(col, "colonne")

        where_clauses = [f"{k} = %s" for k in conditions.keys()]
        where_str = " AND ".join(where_clauses)
        params = tuple(conditions.values())

        query = f"SELECT 1 FROM {table} WHERE {where_str} LIMIT 1"

        try:
            result = QueryExecutor.fetch_one(query, params)
            return result is not None
        except Exception as e:
            logger.error(f"Erreur exists: {e}", exc_info=True)
            raise

    @staticmethod
    def count(
        table: str,
        conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Compte le nombre d'enregistrements selon les conditions.

        Args:
            table: Nom de la table
            conditions: Dictionnaire {colonne: valeur} (optionnel)

        Returns:
            Nombre d'enregistrements

        Example:
            >>> total = QueryExecutor.count('personnel')
            >>> actifs = QueryExecutor.count('personnel', {'statut': 'ACTIF'})
        """
        _validate_identifier(table, "table")
        if conditions:
            for col in conditions.keys():
                _validate_identifier(col, "colonne")
            where_clauses = [f"{k} = %s" for k in conditions.keys()]
            where_str = " WHERE " + " AND ".join(where_clauses)
            params = tuple(conditions.values())
        else:
            where_str = ""
            params = ()

        query = f"SELECT COUNT(*) FROM {table}{where_str}"

        try:
            return QueryExecutor.fetch_scalar(query, params, default=0)
        except Exception as e:
            logger.error(f"Erreur count: {e}", exc_info=True)
            raise
