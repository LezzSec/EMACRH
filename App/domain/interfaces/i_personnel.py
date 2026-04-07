# -*- coding: utf-8 -*-
"""
IPersonnelRepository — contrat pour la gestion du personnel.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Protocol, Tuple

from domain.interfaces.base import IRepository
from domain.models import Personnel, PersonnelResume


class IPersonnelRepository(IRepository[Personnel], Protocol):
    """
    Contrat du repository personnel.

    Étend IRepository avec les opérations propres au domaine RH :
    recherche, filtrage par atelier, comptage par statut, etc.
    """

    def get_all_actifs(self, limit: int = 500) -> List[Personnel]:
        """Retourne tous les employés actifs, triés par nom."""
        ...

    def get_all_inactifs(self, limit: int = 500) -> List[Personnel]:
        """Retourne tous les employés inactifs, triés par nom."""
        ...

    def get_by_matricule(self, matricule: str) -> Optional[Personnel]:
        """Récupère un employé par son matricule."""
        ...

    def search(
        self,
        terme: str,
        statut: Optional[str] = None,
        limit: int = 50,
    ) -> List[Personnel]:
        """
        Recherche plein texte sur nom, prénom, matricule.

        Args:
            terme: texte à rechercher
            statut: filtre optionnel ACTIF / INACTIF
            limit: nombre maximum de résultats
        """
        ...

    def get_by_atelier(self, atelier_id: int) -> List[Personnel]:
        """Retourne les employés actifs rattachés à un atelier (via polyvalence)."""
        ...

    def get_resume_list(self, statut: str = "ACTIF") -> List[PersonnelResume]:
        """Retourne une liste légère (id, nom, prénom, matricule) pour les combos."""
        ...

    def count_by_statut(self) -> Dict[str, int]:
        """Retourne le nombre d'employés par statut : {"ACTIF": X, "INACTIF": Y}."""
        ...

    def count_actifs(self) -> int:
        """Retourne le nombre d'employés actifs."""
        ...

    def get_paginated(
        self,
        offset: int,
        limit: int,
        filters: Optional[Dict] = None,
    ) -> Tuple[List, int]:
        """
        Retourne une page de résultats et le total.

        Returns:
            (liste, total_count)
        """
        ...

    def set_statut(self, personnel_id: int, statut: str) -> bool:
        """Change le statut d'un employé (ACTIF / INACTIF)."""
        ...

    def desactiver(self, personnel_id: int) -> bool:
        """Passe le statut à INACTIF."""
        ...

    def reactiver(self, personnel_id: int) -> bool:
        """Passe le statut à ACTIF."""
        ...
