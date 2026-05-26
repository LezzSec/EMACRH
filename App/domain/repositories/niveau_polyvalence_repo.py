# -*- coding: utf-8 -*-
from __future__ import annotations

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

_FALLBACK_FREQUENCES: dict[int, int] = {1: 30, 2: 30, 3: 3650, 4: 3650}
_FALLBACK_CODES: list[int] = [1, 2, 3, 4]


class NiveauPolyvalenceRepository:
    """Accès à la table niveau_polyvalence.

    Toutes les méthodes de lecture utilisent un cache en mémoire chargé en une
    seule requête au premier appel. Appeler invalidate_cache() après toute
    mutation pour forcer le rechargement.
    """

    # {code: row_dict} — None signifie "pas encore chargé"
    _cache: dict[int, dict] | None = None

    @classmethod
    def _ensure_cache(cls) -> None:
        if cls._cache is not None:
            return
        try:
            rows = QueryExecutor.fetch_all(
                "SELECT id, code, nom, description, frequence_evaluation_jours, "
                "ordre, couleur, nom_evenement, actif "
                "FROM niveau_polyvalence ORDER BY ordre",
                dictionary=True,
            ) or []
            cls._cache = {int(r['code']): r for r in rows}
        except Exception as exc:
            logger.warning("Cache niveaux polyvalence indisponible: %s", exc)
            cls._cache = {}

    @classmethod
    def invalidate_cache(cls) -> None:
        cls._cache = None

    @classmethod
    def get_frequence_jours(cls, code: int) -> int:
        cls._ensure_cache()
        row = cls._cache.get(code)
        if row is not None:
            return int(row['frequence_evaluation_jours'] or 30)
        return _FALLBACK_FREQUENCES.get(code, 30)

    @classmethod
    def get_codes_actifs(cls) -> list[int]:
        cls._ensure_cache()
        return [
            c for c, r in sorted(cls._cache.items(), key=lambda x: (x[1].get('ordre') or 999, x[0]))
            if r.get('actif')
        ]

    @classmethod
    def get_nom_evenement(cls, code: int) -> str:
        cls._ensure_cache()
        row = cls._cache.get(code)
        if row and row.get('nom_evenement'):
            return row['nom_evenement']
        return f"polyvalence.niveau_{code}_reached"

    @classmethod
    def get_all_actifs(cls) -> list[dict]:
        cls._ensure_cache()
        return sorted(
            (r for r in cls._cache.values() if r.get('actif')),
            key=lambda r: (r.get('ordre') or 999, r.get('code') or 999),
        )
