# -*- coding: utf-8 -*-
"""
IAbsenceRepository — contrat pour la gestion des absences.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, Tuple
from datetime import date

from core.interfaces.base import IRepository


class IAbsenceRepository(IRepository[Dict[str, Any]], Protocol):
    """
    Contrat du repository absences.

    Gère les demandes d'absence et leur statut.
    """

    def get_by_personnel(self, personnel_id: int) -> List[Dict[str, Any]]:
        """Retourne toutes les absences d'un employé."""
        ...

    def get_by_statut(self, statut: str) -> List[Dict[str, Any]]:
        """Retourne les absences selon leur statut (EN_ATTENTE, VALIDEE, etc.)."""
        ...

    def get_by_periode(
        self,
        date_debut: date,
        date_fin: date,
    ) -> List[Dict[str, Any]]:
        """Retourne les absences chevauchant une période donnée."""
        ...

    def get_paginated(
        self,
        offset: int,
        limit: int,
        filters: Optional[Dict] = None,
    ) -> Tuple[List, int]:
        """Retourne une page d'absences et le total."""
        ...
