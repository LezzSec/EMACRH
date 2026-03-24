# -*- coding: utf-8 -*-
"""
IHistoriqueRepository — contrat pour l'audit trail (table historique).

Les services utilisent cette interface pour écrire dans l'historique
sans connaître les détails de la table.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, Tuple


class IHistoriqueRepository(Protocol):
    """
    Contrat du repository historique.

    Abstrait l'écriture et la lecture de l'audit trail.
    """

    def log(
        self,
        action: str,
        table_name: str,
        record_id: Optional[int],
        description: str,
        details: Optional[Dict[str, Any]] = None,
        operateur_id: Optional[int] = None,
    ) -> None:
        """
        Enregistre une entrée dans l'historique.

        Args:
            action: code action (ex: "PERSONNEL_CREATION")
            table_name: table concernée
            record_id: ID de l'enregistrement concerné
            description: texte lisible
            details: données complémentaires (sérialisées en JSON)
            operateur_id: ID de l'employé concerné (pour filtrage)
        """
        ...

    def get_by_record(
        self,
        table_name: str,
        record_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retourne l'historique d'un enregistrement spécifique."""
        ...

    def get_by_operateur(
        self,
        operateur_id: int,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retourne l'historique des actions concernant un employé."""
        ...

    def get_paginated(
        self,
        offset: int,
        limit: int,
        filters: Optional[Dict] = None,
    ) -> Tuple[List, int]:
        """Retourne une page de l'historique et le total."""
        ...
