# core/services/log_exporter.py
# Export des logs 'historique' sur une journée en CSV (+ ZIP optionnel)

import os, csv, datetime as dt, zipfile
from typing import Dict
from infrastructure.db.query_executor import QueryExecutor
from infrastructure.config.app_paths import get_logs_dir

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _fetch_rows_for_day(target_day: dt.date):
    """Essaie MySQL (DATE()) puis fallback Postgres (CAST ... AS DATE)."""
    _SELECT = """
        SELECT id, date_time, action, personnel_id, poste_id,
               description, utilisateur, table_name, record_id
        FROM historique
        WHERE {cond}
        ORDER BY date_time
    """
    params = (target_day.isoformat(),)

    def _query(cur):
        try:
            cur.execute(_SELECT.format(cond="DATE(date_time) = %s"), params)
        except Exception:
            cur.execute(_SELECT.format(cond="CAST(date_time AS DATE) = %s"), params)
        rows = cur.fetchall()
        if rows and not isinstance(rows[0], dict):
            names = [d[0] for d in cur.description]
            rows = [dict(zip(names, r)) for r in rows]
        return rows

    return QueryExecutor.with_transaction(_query)

def export_day(day: dt.date, base_dir: str = None, make_zip: bool = True) -> Dict[str, str]:
    """
    Exporte les entrées de la table 'historique' pour la date 'day'.
    Retourne les chemins créés: {'csv': ..., 'zip': ...?}

    Args:
        day: Date à exporter
        base_dir: Dossier de base (None = utilise get_logs_dir(), compatible .exe)
        make_zip: Créer un fichier ZIP
    """
    if base_dir is None:
        # Utiliser le dossier logs compatible dev/exe
        base_dir = str(get_logs_dir())

    out_dir = os.path.join(base_dir, day.isoformat())
    _ensure_dir(out_dir)
    csv_path = os.path.join(out_dir, f"historique_{day.isoformat()}.csv")
    zip_path = os.path.join(out_dir, f"historique_{day.isoformat()}.zip")

    rows = _fetch_rows_for_day(day)

    # écrire CSV - colonnes correspondant à la table historique
    fieldnames = ["id", "date_time", "action", "personnel_id", "poste_id",
                  "description", "utilisateur", "table_name", "record_id"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            r = dict(r)
            # convertir datetime en ISO lisible
            dtv = r.get("date_time")
            if hasattr(dtv, "isoformat"):
                r["date_time"] = dtv.isoformat(sep=" ")
            w.writerow(r)

    result = {"csv": csv_path}
    if make_zip:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(csv_path, arcname=os.path.basename(csv_path))
        result["zip"] = zip_path
    return result
