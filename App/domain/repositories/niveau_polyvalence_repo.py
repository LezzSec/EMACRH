# -*- coding: utf-8 -*-
from __future__ import annotations

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# Valeurs de secours si la table n'est pas encore disponible (avant migration).
_FALLBACK_FREQUENCES: dict[int, int] = {1: 30, 2: 30, 3: 3650, 4: 3650}
_FALLBACK_CODES: list[int] = [1, 2, 3, 4]


class NiveauPolyvalenceRepository:
    """Accès à la table niveau_polyvalence."""

    @classmethod
    def get_frequence_jours(cls, code: int) -> int:
        """Retourne la fréquence d'évaluation en jours pour un code de niveau.
        Utilise le fallback hardcodé si la table n'est pas disponible."""
        try:
            row = QueryExecutor.fetch_one(
                "SELECT frequence_evaluation_jours "
                "FROM niveau_polyvalence WHERE code = %s AND actif = 1",
                (code,),
            )
            if row is not None:
                return int(row[0])
        except Exception as exc:
            logger.warning("Fallback fréquence niveau %s (table indisponible): %s", code, exc)
        return _FALLBACK_FREQUENCES.get(code, 30)

    @classmethod
    def get_codes_actifs(cls) -> list[int]:
        """Retourne la liste des codes de niveaux actifs.
        Utilise le fallback si la table n'est pas disponible."""
        try:
            rows = QueryExecutor.fetch_all(
                "SELECT code FROM niveau_polyvalence WHERE actif = 1 ORDER BY ordre",
            )
            if rows:
                return [int(r[0]) for r in rows]
        except Exception as exc:
            logger.warning("Fallback codes niveaux polyvalence (table indisponible): %s", exc)
        return _FALLBACK_CODES[:]

    @classmethod
    def get_nom_evenement(cls, code: int) -> str:
        """Retourne le nom d'événement EventBus pour un code de niveau.
        Fallback sur le pattern conventionnel si la colonne n'est pas renseignée."""
        try:
            row = QueryExecutor.fetch_one(
                "SELECT nom_evenement FROM niveau_polyvalence WHERE code = %s AND actif = 1",
                (code,),
            )
            if row and row[0]:
                return row[0]
        except Exception as exc:
            logger.warning("Fallback nom_evenement niveau %s: %s", code, exc)
        return f"polyvalence.niveau_{code}_reached"

    @classmethod
    def get_all_actifs(cls) -> list[dict]:
        """Retourne tous les niveaux actifs avec leurs attributs."""
        try:
            return QueryExecutor.fetch_all(
                "SELECT id, code, nom, description, frequence_evaluation_jours, ordre, couleur "
                "FROM niveau_polyvalence WHERE actif = 1 ORDER BY ordre",
                dictionary=True,
            ) or []
        except Exception as exc:
            logger.warning("Impossible de charger les niveaux de polyvalence: %s", exc)
            return []
