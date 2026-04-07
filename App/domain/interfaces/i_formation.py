# -*- coding: utf-8 -*-
"""
IFormationRepository — contrat pour la gestion des formations.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, Tuple

from domain.interfaces.base import IRepository


class IFormationRepository(IRepository[Dict[str, Any]], Protocol):
    """
    Contrat du repository formations.

    Gère les formations suivies par les employés.
    """

    def get_by_operateur(self, operateur_id: int) -> List[Dict[str, Any]]:
        """Retourne toutes les formations d'un employé."""
        ...

    def get_paginated(
        self,
        offset: int,
        limit: int,
        filters: Optional[Dict] = None,
    ) -> Tuple[List, int]:
        """Retourne une page de formations et le total."""
        ...
