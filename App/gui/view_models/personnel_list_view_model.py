# -*- coding: utf-8 -*-
"""
PersonnelListViewModel — état de pagination et filtres pour GestionPersonnelDialog.

N'importe aucun widget Qt (QMessageBox, QTableWidget, etc.).
Seuls QObject et pyqtSignal sont autorisés depuis PyQt5.
"""

from __future__ import annotations

from PyQt5.QtCore import QObject

from domain.repositories.personnel_repo import PersonnelRepository
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class PersonnelListViewModel(QObject):
    """
    ViewModel pour GestionPersonnelDialog.

    Encapsule :
    - L'état de pagination (page_offset, page_size, total_count)
    - Les filtres (statut, recherche texte, production_only)
    - La méthode fetch_page() qui appelle PersonnelRepository.get_paginated()
    """

    def __init__(self, page_size: int = 50, parent=None):
        super().__init__(parent)
        self.page_size:   int = page_size
        self.page_offset: int = 0
        self.total_count: int = 0

        # Filtres courants
        self._statut_filter:   str | None = "ACTIF"
        self._search_text:     str        = ""
        self._production_only: bool       = False

    # ------------------------------------------------------------------
    # Gestion des filtres
    # ------------------------------------------------------------------

    def set_filters(
        self,
        statut:          str | None = "ACTIF",
        search:          str        = "",
        production_only: bool       = False,
    ) -> None:
        """
        Applique de nouveaux filtres et remet l'offset à 0.
        Appelé quand l'utilisateur change un filtre dans l'UI.
        """
        self._statut_filter   = statut
        self._search_text     = search.strip()
        self._production_only = production_only
        self.page_offset      = 0

    def get_current_filters(self) -> dict:
        """Retourne les filtres actifs sous forme de dict pour get_paginated()."""
        filters: dict = {}
        if self._statut_filter:
            filters["statut"] = self._statut_filter
        if self._search_text:
            filters["search"] = self._search_text
        if self._production_only:
            filters["production_only"] = True
        return filters

    # ------------------------------------------------------------------
    # Navigation de page
    # ------------------------------------------------------------------

    def go_to_prev_page(self) -> bool:
        """Décrémente l'offset d'une page. Retourne True si l'action a été effectuée."""
        if self.page_offset >= self.page_size:
            self.page_offset -= self.page_size
            return True
        return False

    def go_to_next_page(self) -> bool:
        """Incrémente l'offset d'une page. Retourne True si l'action a été effectuée."""
        if self.page_offset + self.page_size < self.total_count:
            self.page_offset += self.page_size
            return True
        return False

    def reset_page(self) -> None:
        """Remet l'offset à 0 (utile après changement de filtre)."""
        self.page_offset = 0

    # ------------------------------------------------------------------
    # Chargement des données (appelé dans un DbWorker)
    # ------------------------------------------------------------------

    def fetch_page(self, progress_callback=None) -> tuple[list, int]:
        """
        Interroge PersonnelRepository.get_paginated() avec les filtres courants.

        Retourne (rows, total) — met à jour self.total_count en interne.
        Destiné à être passé directement à DbWorker(self.vm.fetch_page).
        """
        rows, total = PersonnelRepository.get_paginated(
            offset=self.page_offset,
            limit=self.page_size,
            filters=self.get_current_filters(),
        )
        self.total_count = total
        return rows, total

    # ------------------------------------------------------------------
    # Propriétés calculées (utilitaires pour la View)
    # ------------------------------------------------------------------

    @property
    def current_page(self) -> int:
        return self.page_offset // self.page_size + 1

    @property
    def total_pages(self) -> int:
        return max(1, (self.total_count + self.page_size - 1) // self.page_size)

    @property
    def has_prev(self) -> bool:
        return self.page_offset > 0

    @property
    def has_next(self) -> bool:
        return self.page_offset + self.page_size < self.total_count
