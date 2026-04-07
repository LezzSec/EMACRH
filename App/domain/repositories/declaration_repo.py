# -*- coding: utf-8 -*-
"""
Repository pour la table declaration.

Centralise toutes les requêtes SQL liées aux déclarations RH
(arrêts maladie, accidents, congés...).

Usage:
    from domain.repositories.declaration_repo import DeclarationRepository

    declarations = DeclarationRepository.get_by_operateur(operateur_id)
    resume = DeclarationRepository.get_resume(operateur_id)
"""

import logging
from datetime import date as _date
from typing import List, Dict, Optional, Any

from infrastructure.db.query_executor import QueryExecutor

logger = logging.getLogger(__name__)


class DeclarationRepository:
    """Repository pour la table declaration."""

    TABLE = "declaration"

    @classmethod
    def get_by_operateur(cls, operateur_id: int) -> List[Dict[str, Any]]:
        """
        Retourne toutes les déclarations d'un opérateur, ordre chronologique inverse.

        Args:
            operateur_id: ID du personnel

        Returns:
            Liste de dicts (toutes colonnes de declaration)
        """
        return QueryExecutor.fetch_all(
            "SELECT * FROM declaration WHERE personnel_id = %s ORDER BY date_debut DESC",
            (operateur_id,),
            dictionary=True,
        )

    @classmethod
    def get_resume(cls, operateur_id: int) -> Dict[str, Any]:
        """
        Retourne un résumé agrégé : total et nombre en cours.

        Utilisé par get_resume_operateur() dans rh_service.

        Returns:
            {"total": int, "en_cours": int}
        """
        row = QueryExecutor.fetch_one(
            """
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE WHEN date_debut <= CURDATE() AND date_fin >= CURDATE()
                         THEN 1 ELSE 0 END
                ) AS en_cours
            FROM declaration
            WHERE personnel_id = %s
            """,
            (operateur_id,),
            dictionary=True,
        ) or {}
        return {
            "total": row.get("total") or 0,
            "en_cours": row.get("en_cours") or 0,
        }

    @classmethod
    def get_by_id(cls, declaration_id: int) -> Optional[Dict[str, Any]]:
        """Retourne une déclaration par son ID."""
        return QueryExecutor.fetch_one(
            "SELECT * FROM declaration WHERE id = %s",
            (declaration_id,),
            dictionary=True,
        )
