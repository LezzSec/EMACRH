# -*- coding: utf-8 -*-
"""
Couche interfaces / ports — contrats abstraits entre services et repositories.

Architecture cible :
    GUI → Services → Interfaces → Repositories → DB

Les services ne connaissent que ces interfaces.
Les repositories les implémentent (structurellement, via Protocol).

Usage:
    from domain.interfaces import IPersonnelRepository, IContratRepository
    from domain.interfaces.base import IRepository
"""

from domain.interfaces.base import IRepository
from domain.interfaces.i_personnel import IPersonnelRepository
from domain.interfaces.i_contrat import IContratRepository
from domain.interfaces.i_polyvalence import IPolyvalenceRepository
from domain.interfaces.i_poste import IPosteRepository
from domain.interfaces.i_formation import IFormationRepository
from domain.interfaces.i_absence import IAbsenceRepository
from domain.interfaces.i_historique import IHistoriqueRepository

__all__ = [
    "IRepository",
    "IPersonnelRepository",
    "IContratRepository",
    "IPolyvalenceRepository",
    "IPosteRepository",
    "IFormationRepository",
    "IAbsenceRepository",
    "IHistoriqueRepository",
]
