# -*- coding: utf-8 -*-
"""
Import des types d'absence depuis la base SQL Server externe (table HOPMOTI)
vers la table type_absence d'EMAC (MySQL).

Règles :
- Seuls les codes absents de type_absence sont insérés (pas d'écrasement).
- MOTIF  → code  (tronqué à 20 caractères)
- LIBELLE → libelle
- INACTIF → actif (inversé)
- decompte_solde et couleur : valeurs par défaut EMAC.
"""

from infrastructure.db.sqlserver_config import SqlServerCursor
from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.optimized_db_logger import log_hist_async
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


def import_types_absence_from_sqlserver() -> tuple[int, int]:
    """
    Lit HOPMOTI depuis SQL Server et insère dans type_absence les codes manquants.

    Returns:
        (nb_inseres, nb_ignores)
    """
    with SqlServerCursor() as cur:
        cur.execute(
            "SELECT MOTIF, LIBELLE, INACTIF FROM HOPMOTI "
            "WHERE MOTIF IS NOT NULL AND LIBELLE IS NOT NULL "
            "AND LTRIM(RTRIM(MOTIF)) <> '' AND LTRIM(RTRIM(LIBELLE)) <> '' "
            "ORDER BY MOTIF"
        )
        rows = cur.fetchall()

    inserted = 0
    skipped = 0

    for row in rows:
        motif = str(row[0]).strip() if row[0] else None
        libelle = str(row[1]).strip() if row[1] else None
        inactif = row[2]

        if not motif or not libelle:
            skipped += 1
            continue

        code = motif[:20].upper()
        actif = not bool(inactif)

        if QueryExecutor.exists('type_absence', {'code': code}):
            skipped += 1
            continue

        QueryExecutor.execute_write(
            "INSERT INTO type_absence (code, libelle, decompte_solde, couleur, actif) "
            "VALUES (%s, %s, %s, %s, %s)",
            (code, libelle, 1, '#3498db', int(actif))
        )
        inserted += 1
        logger.debug(f"Type absence importé : {code} — {libelle}")

    if inserted > 0:
        log_hist_async(
            action="IMPORT_TYPES_ABSENCE",
            description=f"Import SQL Server (HOPMOTI) : {inserted} importé(s), {skipped} ignoré(s)"
        )

    logger.info(f"Import HOPMOTI terminé : {inserted} insérés, {skipped} ignorés")
    return inserted, skipped
