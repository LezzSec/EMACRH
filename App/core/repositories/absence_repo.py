# -*- coding: utf-8 -*-
"""
DEPRECATED - Ce repository utilisait une table 'absences' qui n'existe pas dans la DB.

La table réelle pour les absences est 'demande_absence'.
Utiliser à la place :
    - core.services.absence_service (fonctions directes avec QueryExecutor)
    - core.services.absence_service_crud (AbsenceServiceCRUD, basé sur CRUDService)

Ce fichier est conservé vide pour éviter les erreurs d'import résiduelles.
"""

import logging
logger = logging.getLogger(__name__)

logger.warning(
    "absence_repo.py est deprecated. "
    "Utiliser absence_service.py ou absence_service_crud.py (table 'demande_absence')."
)
