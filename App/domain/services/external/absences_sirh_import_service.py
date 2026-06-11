# -*- coding: utf-8 -*-
"""
Import des absences depuis HOPHABS (SQL Server) vers absences_sirh (MySQL).

- Exclut FERI (jours fériés) et FINPER (marqueur administratif).
- Résout le personnel_id via personnel.matricule.
- Import incrémental : ne recharge que les lignes modifiées depuis le dernier import
  (basé sur DATMOD).  Sans argument, recharge tout.

Usage :
    from domain.services.external.absences_sirh_import_service import sync_absences_sirh
    inserted, updated, skipped = sync_absences_sirh()
    inserted, updated, skipped = sync_absences_sirh(incremental=True)
"""

from datetime import datetime

from infrastructure.db.sqlserver_config import SqlServerCursor
from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.optimized_db_logger import log_hist_async
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# Codes à ne jamais importer (pas des absences métier)
_MOTIFS_EXCLUS = frozenset({"FERI", "FINPER"})


def _last_import_datmod() -> datetime | None:
    """Retourne le DATMOD max déjà importé, pour l'import incrémental."""
    row = QueryExecutor.fetch_one(
        "SELECT MAX(datmod) FROM absences_sirh WHERE datmod IS NOT NULL"
    )
    return row[0] if row and row[0] else None


def _build_matricule_index() -> dict[str, int]:
    """Construit un index matri -> personnel_id depuis la table personnel."""
    rows = QueryExecutor.fetch_all(
        "SELECT id, matricule FROM personnel WHERE matricule IS NOT NULL AND matricule != ''",
        dictionary=False
    )
    return {str(r[1]).strip(): r[0] for r in rows if r[1]}


def sync_absences_sirh(incremental: bool = False) -> tuple[int, int, int]:
    """
    Synchronise HOPHABS vers absences_sirh.

    Args:
        incremental: si True, ne charge que les lignes HOPHABS avec
                     DATMOD > max(datmod) déjà importé.

    Returns:
        (inserted, updated, skipped)
    """
    since: datetime | None = None
    if incremental:
        since = _last_import_datmod()
        logger.info(f"Import incrémental depuis DATMOD > {since}")
    else:
        logger.info("Import complet HOPHABS")

    # --- Lecture SQL Server ---
    query = (
        "SELECT MATRI, DAT, MOTIF, MOTYPE, MOTIDUR, TYPJOU, MOTIFINI, DATMOD "
        "FROM HOPHABS "
        "WHERE MATRI IS NOT NULL AND DAT IS NOT NULL "
        "  AND LTRIM(RTRIM(MOTIF)) NOT IN ('FERI', 'FINPER') "
    )
    params = []
    if since:
        query += "  AND DATMOD > ? "
        params.append(since)
    query += "ORDER BY MATRI, DAT"

    with SqlServerCursor() as cur:
        cur.execute(query, params) if params else cur.execute(query)
        cols = [c[0] for c in cur.description]
        raw_rows = cur.fetchall()

    logger.info(f"HOPHABS : {len(raw_rows)} lignes lues")

    # --- Résolution personnel_id ---
    matri_index = _build_matricule_index()

    inserted = updated = skipped = 0

    for row in raw_rows:
        r = dict(zip(cols, row))

        matri = (r.get("MATRI") or "").strip()
        dat = r.get("DAT")
        motif = (r.get("MOTIF") or "").strip() or None
        motype = (r.get("MOTYPE") or "").strip()[:1] or None
        motidur = r.get("MOTIDUR")
        typjou = (r.get("TYPJOU") or "").strip() or None
        motifini = (r.get("MOTIFINI") or "").strip() or None
        datmod = r.get("DATMOD")

        if not matri or not dat:
            skipped += 1
            continue
        if motif in _MOTIFS_EXCLUS:
            skipped += 1
            continue

        dat_date = dat.date() if hasattr(dat, "date") else dat
        personnel_id = matri_index.get(matri)

        exists = QueryExecutor.exists("absences_sirh", {"matri": matri, "dat": dat_date})

        if exists:
            QueryExecutor.execute_write(
                "UPDATE absences_sirh "
                "SET personnel_id=%s, motif=%s, motype=%s, motidur=%s, "
                "    typjou=%s, motifini=%s, datmod=%s "
                "WHERE matri=%s AND dat=%s",
                (personnel_id, motif, motype, motidur,
                 typjou, motifini, datmod, matri, dat_date),
                return_lastrowid=False
            )
            updated += 1
        else:
            QueryExecutor.execute_write(
                "INSERT INTO absences_sirh "
                "(matri, personnel_id, dat, motif, motype, motidur, typjou, motifini, datmod) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (matri, personnel_id, dat_date, motif, motype,
                 motidur, typjou, motifini, datmod)
            )
            inserted += 1

    log_hist_async(
        action="SYNC_ABSENCES_SIRH",
        description=(
            f"{'Incrémental' if incremental else 'Complet'} : "
            f"{inserted} insérés, {updated} mis à jour, {skipped} ignorés"
        )
    )
    logger.info(f"Sync terminée : {inserted} insérés, {updated} mis à jour, {skipped} ignorés")
    return inserted, updated, skipped


def get_derniere_sync() -> datetime | None:
    """Retourne la date du dernier enregistrement importé (max imported_at)."""
    row = QueryExecutor.fetch_one(
        "SELECT MAX(imported_at) FROM absences_sirh"
    )
    return row[0] if row and row[0] else None


def get_absences_periode(
    date_debut,
    date_fin,
    personnel_id: int | None = None,
    motif: str | None = None,
) -> list[dict]:
    """
    Retourne les absences groupées en périodes pour une plage de dates.

    Détecte les ruptures de période via un gap > 4 jours consécutifs
    (gère les week-ends dans les données HOPHABS).

    Returns:
        Liste de dicts : matri, nom, prenom, motif, libelle_motif,
                         date_debut, date_fin, nb_jours
    """
    where_extra = ""
    params: list = [date_debut, date_fin]

    if personnel_id:
        where_extra += " AND a.personnel_id = %s"
        params.append(personnel_id)
    if motif:
        where_extra += " AND a.motif = %s"
        params.append(motif)

    sql = f"""
        SELECT
            grp.matri,
            p.nom,
            p.prenom,
            grp.motif,
            t.libelle COLLATE utf8mb4_general_ci AS libelle_motif,
            MIN(grp.dat) AS date_debut,
            MAX(grp.dat) AS date_fin,
            COUNT(grp.dat) AS nb_jours
        FROM (
            SELECT matri, personnel_id, motif, dat,
                SUM(new_period) OVER (PARTITION BY matri, motif ORDER BY dat) AS period_id
            FROM (
                SELECT matri, personnel_id, motif, dat,
                    CASE
                        WHEN DATEDIFF(dat,
                            COALESCE(LAG(dat) OVER (PARTITION BY matri, motif ORDER BY dat), '1900-01-01')
                        ) > 4
                        THEN 1 ELSE 0
                    END AS new_period
                FROM absences_sirh a
                WHERE dat BETWEEN %s AND %s
                  {where_extra}
            ) base
        ) grp
        LEFT JOIN personnel p ON grp.personnel_id = p.id
        LEFT JOIN type_absence t ON grp.motif COLLATE utf8mb4_general_ci = t.code COLLATE utf8mb4_general_ci
        GROUP BY grp.matri, grp.personnel_id, grp.motif, grp.period_id,
                 p.nom, p.prenom, t.libelle
        ORDER BY date_debut, p.nom, p.prenom, grp.motif
    """
    return QueryExecutor.fetch_all(sql, params, dictionary=True)


def get_motifs_distincts() -> list[str]:
    """Retourne la liste des codes motif présents dans absences_sirh, triée."""
    rows = QueryExecutor.fetch_all(
        "SELECT DISTINCT motif FROM absences_sirh "
        "WHERE motif IS NOT NULL ORDER BY motif",
        dictionary=False
    )
    return [r[0] for r in rows if r[0]]


def get_sirh_absences_pour_mois(date_debut_str: str, date_fin_str: str) -> list[dict]:
    """
    Retourne les absences SIRH du mois groupées en périodes consécutives.
    Un gap > 4 jours entre deux lignes du même (matri, motif) crée une nouvelle période
    (gère les week-ends absents des données HOPHABS).

    Returns:
        Liste de dicts : matri, nom_complet, motif, type_libelle, date_debut, date_fin
    """
    return QueryExecutor.fetch_all(
        """
        SELECT
            grp.matri,
            COALESCE(CONCAT(p.nom, ' ', p.prenom), grp.matri COLLATE utf8mb4_general_ci) AS nom_complet,
            grp.motif,
            COALESCE(t.libelle COLLATE utf8mb4_general_ci, grp.motif COLLATE utf8mb4_general_ci) AS type_libelle,
            MIN(grp.dat) AS date_debut,
            MAX(grp.dat) AS date_fin
        FROM (
            SELECT matri, personnel_id, motif, dat,
                SUM(new_period) OVER (PARTITION BY matri, motif ORDER BY dat) AS period_id
            FROM (
                SELECT matri, personnel_id, motif, dat,
                    CASE
                        WHEN DATEDIFF(dat,
                            COALESCE(LAG(dat) OVER (PARTITION BY matri, motif ORDER BY dat), '1900-01-01')
                        ) > 4 THEN 1 ELSE 0
                    END AS new_period
                FROM absences_sirh
                WHERE dat BETWEEN %s AND %s
            ) base
        ) grp
        LEFT JOIN personnel p ON grp.personnel_id = p.id
        LEFT JOIN type_absence t
            ON grp.motif COLLATE utf8mb4_general_ci = t.code COLLATE utf8mb4_general_ci
        GROUP BY grp.matri, grp.personnel_id, grp.motif, grp.period_id, p.nom, p.prenom, t.libelle
        ORDER BY MIN(grp.dat), p.nom, p.prenom
        """,
        (date_debut_str, date_fin_str),
        dictionary=True
    )


def get_sirh_absences_pour_personnel(personnel_id: int) -> list[dict]:
    """
    Retourne l'historique complet des absences SIRH d'un personnel, groupées en périodes.
    Un gap > 4 jours entre deux lignes du même motif crée une nouvelle période
    (gère les week-ends absents des données HOPHABS).

    Returns:
        Liste de dicts : motif, type_libelle, date_debut, date_fin, nb_jours
    """
    return QueryExecutor.fetch_all(
        """
        SELECT
            grp.motif,
            COALESCE(t.libelle COLLATE utf8mb4_general_ci, grp.motif COLLATE utf8mb4_general_ci) AS type_libelle,
            MIN(grp.dat) AS date_debut,
            MAX(grp.dat) AS date_fin,
            COUNT(grp.dat) AS nb_jours
        FROM (
            SELECT motif, dat,
                SUM(new_period) OVER (PARTITION BY motif ORDER BY dat) AS period_id
            FROM (
                SELECT motif, dat,
                    CASE
                        WHEN DATEDIFF(dat,
                            COALESCE(LAG(dat) OVER (PARTITION BY motif ORDER BY dat), '1900-01-01')
                        ) > 4 THEN 1 ELSE 0
                    END AS new_period
                FROM absences_sirh
                WHERE personnel_id = %s
            ) base
        ) grp
        LEFT JOIN type_absence t
            ON grp.motif COLLATE utf8mb4_general_ci = t.code COLLATE utf8mb4_general_ci
        GROUP BY grp.motif, grp.period_id, t.libelle
        ORDER BY MIN(grp.dat) DESC
        """,
        (personnel_id,),
        dictionary=True
    )
