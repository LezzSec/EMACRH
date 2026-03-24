# -*- coding: utf-8 -*-
"""
IPosteRepository — contrat pour la gestion des postes et ateliers.
"""

from __future__ import annotations
from typing import List, Optional, Protocol, Tuple

from core.interfaces.base import IRepository
from core.models import Poste


class IPosteRepository(IRepository[Poste], Protocol):
    """
    Contrat du repository postes.

    Gère les postes de travail et leur rattachement aux ateliers.
    """

    def get_by_atelier(self, atelier_id: int) -> List[Poste]:
        """Retourne tous les postes d'un atelier."""
        ...

    def get_visible(self) -> List[Poste]:
        """Retourne les postes visibles (actifs, non masqués)."""
        ...

    def search(self, terme: str, limit: int = 50) -> List[Poste]:
        """Recherche des postes par code ou libellé."""
        ...

    def get_paginated(
        self,
        offset: int,
        limit: int,
        filters: Optional[dict] = None,
    ) -> Tuple[List, int]:
        """Retourne une page de postes et le total."""
        ...
