# -*- coding: utf-8 -*-
"""
Module repositories - Couche d'accès aux données standardisée.

Ce module fournit des repositories typés pour chaque domaine métier,
centralisant les requêtes SQL et évitant la dispersion dans le code.

Architecture:
    GUI → Services → Repositories → DB

Usage:
    from core.repositories import PersonnelRepository, ContratRepository

    # Lecture
    personnel = PersonnelRepository.get_by_id(123)
    actifs = PersonnelRepository.get_all_actifs()

    # Écriture
    PersonnelRepository.create(data)
    PersonnelRepository.update(123, data)
"""

from core.repositories.base import BaseRepository, SafeQueryBuilder
from core.repositories.personnel_repo import PersonnelRepository
from core.repositories.contrat_repo import ContratRepository
from core.repositories.polyvalence_repo import PolyvalenceRepository
from core.repositories.poste_repo import PosteRepository, AtelierRepository
from core.repositories.absence_repo import AbsenceRepository

__all__ = [
    # Base
    'BaseRepository',
    'SafeQueryBuilder',
    # Repositories
    'PersonnelRepository',
    'ContratRepository',
    'PolyvalenceRepository',
    'PosteRepository',
    'AtelierRepository',
    'AbsenceRepository',
]
