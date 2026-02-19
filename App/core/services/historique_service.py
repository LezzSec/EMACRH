# -*- coding: utf-8 -*-
"""
HistoriqueService - Couche service pour les requêtes sur la table historique.

Centralise toutes les opérations DB liées à l'historique afin que
la couche GUI n'accède jamais directement à la base de données.

Usage:
    from core.services.historique_service import (
        get_entity_name, fetch_historique, delete_historique_range
    )
"""

import datetime as dt
from typing import List, Dict, Optional, Any

from core.db.query_executor import QueryExecutor
from core.db.configbd import DatabaseConnection
from core.utils.logging_config import get_logger

logger = get_logger(__name__)

# Mapping action SQL → libellé FR (utilisé par les vues)
ACTION_MAP_FR_TO_SQL = {
    "Ajout": "INSERT",
    "Modification": "UPDATE",
    "Suppression": "DELETE",
    "Erreur": "ERROR",
}


def get_entity_name(entity_type: str, entity_id) -> str:
    """
    Résout un id d'entité (opérateur ou poste) en nom lisible.

    Args:
        entity_type: "operateur" ou "poste"
        entity_id: ID de l'entité

    Returns:
        Chaîne lisible, ou "#<id>" si non trouvé
    """
    if entity_id is None or entity_id == "":
        return ""

    try:
        if entity_type == "operateur":
            from core.repositories.personnel_repo import PersonnelRepository
            p = PersonnelRepository.get_by_id(int(entity_id))
            if p:
                return f"{p.prenom} {p.nom}"
        elif entity_type == "poste":
            from core.repositories.poste_repo import PosteRepository
            pos = PosteRepository.get_by_id(int(entity_id))
            if pos:
                return pos.poste_code
    except Exception:
        pass

    return f"#{entity_id}"


def fetch_historique(
    date_from: dt.datetime,
    date_to: dt.datetime,
    search_text: str = "",
    action_filter: str = "",
) -> List[Dict]:
    """
    Récupère les entrées d'historique selon les filtres.

    Args:
        date_from: Début de la plage (datetime)
        date_to: Fin de la plage (datetime)
        search_text: Texte libre (action, description, ids)
        action_filter: Libellé FR ex "Ajout", "Modification"…
                       ou "(Toutes les actions)" pour ne pas filtrer

    Returns:
        Liste de dicts avec id, date_time, action, operateur_id,
        poste_id, description, utilisateur
    """
    # Conditions fixes — pas de valeurs utilisateur ici
    where: List[str] = ["date_time >= %s", "date_time <= %s"]
    params: List[Any] = [date_from, date_to]

    if action_filter and action_filter != "(Toutes les actions)":
        sql_action = ACTION_MAP_FR_TO_SQL.get(action_filter, action_filter)
        where.append("action = %s")
        params.append(sql_action)

    if search_text:
        like = f"%{search_text}%"
        where.append(
            "("
            "action LIKE %s OR "
            "description LIKE %s OR "
            "CAST(operateur_id AS CHAR) LIKE %s OR "
            "CAST(poste_id AS CHAR) LIKE %s"
            ")"
        )
        params += [like, like, like, like]

    where_clause = " AND ".join(where)
    sql = (
        "SELECT id, date_time, action, operateur_id, poste_id, description, utilisateur "
        "FROM historique "
        f"WHERE {where_clause} "
        "ORDER BY date_time DESC, id DESC"
    )

    return QueryExecutor.fetch_all(sql, tuple(params), dictionary=True)


def delete_historique_range(date_from: dt.datetime, date_to: dt.datetime) -> int:
    """
    Supprime les entrées d'historique dans une plage de dates.

    Args:
        date_from: Début de la plage (datetime)
        date_to: Fin de la plage (datetime)

    Returns:
        Nombre de lignes supprimées
    """
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM historique WHERE date_time >= %s AND date_time <= %s",
            (date_from, date_to),
        )
        deleted = cur.rowcount or 0
        cur.close()
    return deleted
