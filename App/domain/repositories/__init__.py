# -*- coding: utf-8 -*-
"""
Module repositories - Couche d'accès aux données standardisée.

Ce module fournit des repositories typés pour chaque domaine métier,
centralisant les requêtes SQL et évitant la dispersion dans le code.

Architecture:
    GUI → Services → Repositories → DB

Usage:
    from domain.repositories import PersonnelRepository, ContratRepository

    # Lecture
    personnel = PersonnelRepository.get_by_id(123)
    actifs = PersonnelRepository.get_all_actifs()

    # Écriture
    PersonnelRepository.create(data)
    PersonnelRepository.update(123, data)
"""

from domain.repositories.base import BaseRepository, SafeQueryBuilder
from domain.repositories.personnel_repo import PersonnelRepository
from domain.repositories.contrat_repo import ContratRepository
from domain.repositories.polyvalence_repo import PolyvalenceRepository
from domain.repositories.poste_repo import PosteRepository, AtelierRepository
from domain.repositories.declaration_repo import DeclarationRepository
from domain.repositories.document_repo import DocumentRepository

# Note: AbsenceRepository supprimé - utilisait la table inexistante 'absences'.
# Utiliser absence_service.py ou absence_service_crud.py (table 'demande_absence').

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
    'DeclarationRepository',
    'DocumentRepository',
]
