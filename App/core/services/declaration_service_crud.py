# -*- coding: utf-8 -*-
"""
DeclarationServiceCRUD - Service CRUD pour les déclarations (absences).

Usage:
    from core.services.declaration_service_crud import DeclarationServiceCRUD

    # Créer une déclaration
    success, msg, new_id = DeclarationServiceCRUD.create(
        operateur_id=1,
        type_declaration='Maladie',
        date_debut=date.today(),
        date_fin=date.today()
    )

    # Récupérer les déclarations d'un opérateur
    declarations = DeclarationServiceCRUD.get_by_operateur(operateur_id=1)
"""

from typing import Dict, List, Optional, Tuple
from core.services.crud_service import CRUDService
from core.db.query_executor import QueryExecutor
from core.utils.logging_config import get_logger

logger = get_logger(__name__)


# Types de déclaration disponibles
TYPES_DECLARATION = [
    'CongePaye',
    'RTT',
    'SansSolde',
    'Maladie',
    'AccidentTravail',
    'AccidentTrajet',
    'ArretTravail',
    'CongeNaissance',
    'Formation',
    'Autorisation',
    'Autre'
]


class DeclarationServiceCRUD(CRUDService):
    """Service CRUD pour la table declaration."""

    TABLE_NAME = "declaration"
    ACTION_PREFIX = "DECLARATION_"

    ALLOWED_FIELDS = [
        'personnel_id',
        'type_declaration',
        'date_debut',
        'date_fin',
        'motif'
    ]

    @classmethod
    def get_by_operateur(
        cls,
        operateur_id: int,
        order_by: str = 'date_debut DESC'
    ) -> List[Dict]:
        """
        Récupère toutes les déclarations d'un opérateur.

        Args:
            operateur_id: ID de l'opérateur
            order_by: Clause ORDER BY

        Returns:
            Liste des déclarations
        """
        return cls.get_all(
            conditions={'personnel_id': operateur_id},
            order_by=order_by
        )

    @classmethod
    def get_en_cours(cls, operateur_id: int) -> List[Dict]:
        """Récupère les déclarations en cours (date_debut <= aujourd'hui <= date_fin)."""
        try:
            return QueryExecutor.fetch_all(
                """
                SELECT * FROM declaration
                WHERE personnel_id = %s
                  AND date_debut <= CURDATE()
                  AND date_fin >= CURDATE()
                ORDER BY date_debut DESC
                """,
                (operateur_id,),
                dictionary=True
            )
        except Exception as e:
            logger.exception(f"Erreur get_en_cours: {e}")
            return []

    @classmethod
    def count_en_cours(cls, operateur_id: int) -> int:
        """Compte les déclarations en cours pour un opérateur."""
        try:
            return QueryExecutor.fetch_scalar(
                """
                SELECT COUNT(*) FROM declaration
                WHERE personnel_id = %s
                  AND date_debut <= CURDATE()
                  AND date_fin >= CURDATE()
                """,
                (operateur_id,),
                default=0
            )
        except Exception as e:
            logger.exception(f"Erreur count_en_cours: {e}")
            return 0

    @classmethod
    def get_types_declaration(cls) -> List[str]:
        """Retourne la liste des types de déclaration disponibles."""
        return TYPES_DECLARATION
