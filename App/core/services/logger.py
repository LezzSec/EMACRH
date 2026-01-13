# core/services/logger.py
# Utilitaire simple pour écrire dans la table SQL `historique`
# Compatible avec ton viewer (historique.py) et log_exporter.py

from __future__ import annotations
import json
from typing import Any

from core.db.configbd import get_connection as get_db_connection

__all__ = ["log_hist"]


def _get_current_username() -> str | None:
    """Récupère le nom d'utilisateur connecté"""
    try:
        from core.services.auth_service import get_current_user
        user = get_current_user()
        if user:
            return user.get('username') or user.get('nom') or None
    except Exception:
        pass
    return None


def _to_json_str(details: Any) -> str | None:
    if details is None:
        return None
    if isinstance(details, (str, bytes, bytearray)):
        # bytes -> str
        if isinstance(details, (bytes, bytearray)):
            try:
                return details.decode("utf-8", errors="ignore")
            except Exception:
                return str(details)
        return details  # str
    try:
        return json.dumps(details, ensure_ascii=False)
    except Exception:
        return str(details)


def log_hist(
    action: str,
    table_name: str | None = None,
    record_id: Any | None = None,
    description: str | None = None,
    details: Any | None = None,
    source: str | None = None,
    utilisateur: str | None = None,
) -> None:
    """Insère une ligne dans la table `historique`.

    Champs utilisés par `historique.py` et `log_exporter.py` :
      - date_time      (NOW())
      - action         (INSERT/UPDATE/DELETE/ERROR ou texte libre)
      - table_name     ("postes", "polyvalence", ...)
      - record_id      (id concerné, string ou int)
      - utilisateur    (optionnel, récupéré automatiquement si non fourni)
      - description    (phrase courte)
      - details        (JSON texte ou dict)
      - source         (ex: "GUI/liste_et_grilles")
    """
    # Si utilisateur non fourni, récupérer l'utilisateur connecté
    if utilisateur is None:
        utilisateur = _get_current_username()

    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Préparer la description finale (inclure details si fourni)
        final_description = description
        if details:
            details_str = _to_json_str(details)
            if final_description:
                final_description = f"{final_description} | Details: {details_str}"
            else:
                final_description = details_str

        cur.execute(
            """
            INSERT INTO historique
                (date_time, action, table_name, record_id, utilisateur, description)
            VALUES (NOW(), %s, %s, %s, %s, %s)
            """,
            (
                action,
                table_name,
                str(record_id) if record_id is not None else None,
                utilisateur,
                final_description,
            ),
        )
        conn.commit()
    except Exception:
        # On ne casse jamais le flux métier si le log échoue
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass
