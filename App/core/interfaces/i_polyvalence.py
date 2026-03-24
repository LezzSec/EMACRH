# -*- coding: utf-8 -*-
"""
IPolyvalenceRepository — contrat pour la gestion des compétences / évaluations.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, Tuple
from datetime import date

from core.interfaces.base import IRepository
from core.models import Polyvalence


class IPolyvalenceRepository(IRepository[Polyvalence], Protocol):
    """
    Contrat du repository polyvalence.

    Gère les compétences des employés sur les postes de travail
    et le planning des évaluations.
    """

    def get_by_operateur(self, operateur_id: int) -> List[Polyvalence]:
        """Retourne toutes les compétences d'un employé."""
        ...

    def get_by_poste(self, poste_id: int) -> List[Polyvalence]:
        """Retourne toutes les compétences rattachées à un poste."""
        ...

    def get_by_operateur_poste(
        self,
        operateur_id: int,
        poste_id: int,
    ) -> Optional[Polyvalence]:
        """Retourne la compétence d'un employé sur un poste spécifique."""
        ...

    def get_evaluations_a_venir(
        self,
        before_date: date,
        limit: int = 200,
    ) -> List[Polyvalence]:
        """Retourne les évaluations planifiées avant une date donnée."""
        ...

    def get_evaluations_en_retard(self) -> List[Polyvalence]:
        """Retourne les évaluations dont la prochaine date est dépassée."""
        ...

    def get_paginated(
        self,
        offset: int,
        limit: int,
        filters: Optional[Dict] = None,
    ) -> Tuple[List, int]:
        """Retourne une page de compétences et le total."""
        ...
