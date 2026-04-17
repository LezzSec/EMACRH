# -*- coding: utf-8 -*-
"""
HistoriqueService - Couche service pour les requêtes sur la table historique.

Centralise toutes les opérations DB liées à l'historique afin que
la couche GUI n'accède jamais directement à la base de données.

Usage:
    from domain.services.admin.historique_service import (
        get_entity_name, fetch_historique, delete_historique_range
    )
"""

import datetime as dt
from typing import List, Dict, Optional, Any

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# Mapping action SQL → libellé FR (utilisé par les vues)
ACTION_MAP_FR_TO_SQL = {
    "Ajout": "INSERT",
    "Modification": "UPDATE",
    "Suppression": "DELETE",
    "Erreur": "ERROR",
}

# Tables regroupées par module (utilisé par HistoriqueDialog pour filtrer par onglet)
MODULE_TABLES: Dict[str, List[str]] = {
    "RH": [
        "contrat", "formation", "declaration", "personnel", "personnel_infos",
        "demande_absence", "competences_catalogue", "competences_personnel",
        "visite_medicale", "accident_travail", "sanction", "entretien",
        "controle_alcool", "test_salivaire", "validite_medical",
    ],
    "Production": ["polyvalence", "postes", "atelier"],
    "Planning":   ["planning", "demande_absence"],
    "Admin":      ["utilisateurs", "roles", "features", "role_features", "user_features"],
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
            from domain.repositories.personnel_repo import PersonnelRepository
            p = PersonnelRepository.get_by_id(int(entity_id))
            if p:
                return f"{p.prenom} {p.nom}"
        elif entity_type == "poste":
            from domain.repositories.poste_repo import PosteRepository
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
            "CAST(personnel_id AS CHAR) LIKE %s OR "
            "CAST(poste_id AS CHAR) LIKE %s"
            ")"
        )
        params += [like, like, like, like]

    where_clause = " AND ".join(where)
    sql = (
        "SELECT h.id, h.date_time, h.action, h.personnel_id, h.poste_id, h.description, "
        "h.utilisateur, h.table_name, h.record_id, "
        "CONCAT(p.prenom, ' ', p.nom) AS op_name, "
        "pos.poste_code AS po_name "
        "FROM historique h "
        "LEFT JOIN personnel p ON h.personnel_id = p.id "
        "LEFT JOIN postes pos ON h.poste_id = pos.id "
        f"WHERE {where_clause} "
        "ORDER BY h.date_time DESC, h.id DESC"
    )

    return QueryExecutor.fetch_all(sql, tuple(params), dictionary=True)


def get_utilisateurs() -> List[str]:
    """
    Retourne la liste distincte des utilisateurs présents dans la table historique.

    Returns:
        Liste de chaînes (logins/noms d'utilisateurs)
    """
    try:
        rows = QueryExecutor.fetch_all(
            "SELECT DISTINCT utilisateur FROM historique "
            "WHERE utilisateur IS NOT NULL AND utilisateur != '' "
            "ORDER BY utilisateur",
            dictionary=False,
        )
        return [r[0] for r in rows if r and r[0]]
    except Exception as e:
        logger.exception(f"Erreur get_utilisateurs: {e}")
        return []


def _build_historique_where(
    date_from: dt.datetime,
    date_to: dt.datetime,
    search_text: str = "",
    action_filter: str = "",
    utilisateur_filter: str = "",
    table_names: Optional[List[str]] = None,
) -> tuple:
    """
    Construit la clause WHERE et les paramètres partagés entre
    count_historique() et fetch_historique_paginated().

    Returns:
        (where_clause: str, params: list)
    """
    where: List[str] = ["date_time >= %s", "date_time <= %s"]
    params: List[Any] = [date_from, date_to]

    if action_filter and action_filter not in ("", "(Toutes les actions)"):
        sql_action = ACTION_MAP_FR_TO_SQL.get(action_filter, action_filter)
        where.append("action = %s")
        params.append(sql_action)

    if utilisateur_filter:
        where.append("utilisateur = %s")
        params.append(utilisateur_filter)

    if table_names:
        placeholders = ", ".join(["%s"] * len(table_names))
        where.append(f"table_name IN ({placeholders})")
        params.extend(table_names)

    if search_text:
        like = f"%{search_text}%"
        where.append(
            "(action LIKE %s OR description LIKE %s OR "
            "CAST(personnel_id AS CHAR) LIKE %s OR "
            "CAST(poste_id AS CHAR) LIKE %s)"
        )
        params += [like, like, like, like]

    return " AND ".join(where), params


def count_historique(
    date_from: dt.datetime,
    date_to: dt.datetime,
    search_text: str = "",
    action_filter: str = "",
    utilisateur_filter: str = "",
    table_names: Optional[List[str]] = None,
) -> int:
    """
    Compte le nombre d'entrées d'historique selon les filtres.

    Args:
        date_from: Début de la plage (datetime)
        date_to: Fin de la plage (datetime)
        search_text: Texte libre (action, description, ids)
        action_filter: Libellé FR ex "Ajout", "Modification"…
        utilisateur_filter: Login exact de l'utilisateur (ou "" pour tous)
        table_names: Liste de noms de tables à inclure (None = toutes)

    Returns:
        Nombre total d'entrées correspondantes
    """
    where_clause, params = _build_historique_where(
        date_from, date_to, search_text, action_filter,
        utilisateur_filter, table_names,
    )
    sql = f"SELECT COUNT(*) FROM historique WHERE {where_clause}"
    try:
        result = QueryExecutor.fetch_one(sql, tuple(params), dictionary=False)
        return result[0] if result else 0
    except Exception as e:
        logger.exception(f"Erreur count_historique: {e}")
        return 0


def fetch_historique_paginated(
    date_from: dt.datetime,
    date_to: dt.datetime,
    search_text: str = "",
    action_filter: str = "",
    utilisateur_filter: str = "",
    table_names: Optional[List[str]] = None,
    offset: int = 0,
    limit: int = 100,
    sort_order: str = "DESC",
) -> List[Dict]:
    """
    Récupère les entrées d'historique avec pagination et filtres étendus.

    Args:
        date_from: Début de la plage (datetime)
        date_to: Fin de la plage (datetime)
        search_text: Texte libre (action, description, ids)
        action_filter: Libellé FR ex "Ajout", "Modification"…
        utilisateur_filter: Login exact de l'utilisateur (ou "" pour tous)
        table_names: Liste de noms de tables à inclure (None = toutes)
        offset: Nombre d'entrées à sauter (pagination)
        limit: Nombre max d'entrées à retourner
        sort_order: "DESC" (plus récent en premier) ou "ASC" (plus ancien en premier)

    Returns:
        Liste de dicts avec id, date_time, action, table_name, record_id,
        operateur_id, poste_id, description, utilisateur
    """
    order = "ASC" if sort_order == "ASC" else "DESC"
    where_clause, params = _build_historique_where(
        date_from, date_to, search_text, action_filter,
        utilisateur_filter, table_names,
    )
    sql = (
        "SELECT h.id, h.date_time, h.action, h.table_name, h.record_id, "
        "h.personnel_id, h.poste_id, h.description, h.utilisateur, "
        "CONCAT(p.prenom, ' ', p.nom) AS op_name, "
        "pos.poste_code AS po_name "
        "FROM historique h "
        "LEFT JOIN personnel p ON h.personnel_id = p.id "
        "LEFT JOIN postes pos ON h.poste_id = pos.id "
        f"WHERE {where_clause} "
        f"ORDER BY h.date_time {order}, h.id {order} "
        "LIMIT %s OFFSET %s"
    )
    params_tuple = tuple(params) + (limit, offset)
    return QueryExecutor.fetch_all(sql, params_tuple, dictionary=True)


def delete_historique_range(date_from: dt.datetime, date_to: dt.datetime) -> int:
    """
    Supprime les entrées d'historique dans une plage de dates.

    Args:
        date_from: Début de la plage (datetime)
        date_to: Fin de la plage (datetime)

    Returns:
        Nombre de lignes supprimées
    """
    def _do_delete(cur):
        cur.execute(
            "DELETE FROM historique WHERE date_time >= %s AND date_time <= %s",
            (date_from, date_to),
        )
        return cur.rowcount or 0

    return QueryExecutor.with_transaction(_do_delete)
