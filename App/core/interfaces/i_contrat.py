# -*- coding: utf-8 -*-
"""
IContratRepository — contrat pour la gestion des contrats de travail.
"""

from __future__ import annotations
from typing import List, Optional, Protocol, Tuple
from datetime import date

from core.interfaces.base import IRepository
from core.models import Contrat


class IContratRepository(IRepository[Contrat], Protocol):
    """
    Contrat du repository contrats.

    Étend IRepository avec les opérations propres aux contrats :
    filtrage par personnel, par type, contrats actifs, expirant bientôt.
    """

    def get_by_personnel(self, personnel_id: int) -> List[Contrat]:
        """Retourne tous les contrats d'un employé."""
        ...

    def get_actifs(self) -> List[Contrat]:
        """Retourne tous les contrats actifs (non expirés)."""
        ...

    def get_by_type(self, type_contrat: str) -> List[Contrat]:
        """Retourne les contrats d'un type donné (CDD, CDI, etc.)."""
        ...

    def get_expiring(self, before_date: date, limit: int = 100) -> List[Contrat]:
        """
        Retourne les contrats expirant avant une date donnée.

        Args:
            before_date: date limite
            limit: nombre maximum de résultats
        """
        ...

    def get_paginated(
        self,
        offset: int,
        limit: int,
        filters: Optional[dict] = None,
    ) -> Tuple[List, int]:
        """Retourne une page de contrats et le total."""
        ...
