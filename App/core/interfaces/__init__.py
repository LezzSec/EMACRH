# -*- coding: utf-8 -*-
"""
Couche interfaces / ports — contrats abstraits entre services et repositories.

Architecture cible :
    GUI → Services → Interfaces → Repositories → DB

Les services ne connaissent que ces interfaces.
Les repositories les implémentent (structurellement, via Protocol).

Usage:
    from core.interfaces import IPersonnelRepository, IContratRepository
    from core.interfaces.base import IRepository
"""

from core.interfaces.base import IRepository
from core.interfaces.i_personnel import IPersonnelRepository
from core.interfaces.i_contrat import IContratRepository
from core.interfaces.i_polyvalence import IPolyvalenceRepository
from core.interfaces.i_poste import IPosteRepository
from core.interfaces.i_formation import IFormationRepository
from core.interfaces.i_absence import IAbsenceRepository
from core.interfaces.i_historique import IHistoriqueRepository

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
