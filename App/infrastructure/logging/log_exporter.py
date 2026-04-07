# core/services/log_exporter.py
# Export des logs 'historique' sur une journée en CSV (+ ZIP optionnel)

import os, csv, datetime as dt, zipfile
from typing import Dict
from infrastructure.db.configbd import get_connection as get_db_connection
from infrastructure.config.app_paths import get_logs_dir

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _query_for_day(cursor, target_day: dt.date):
    """Essaie MySQL (DATE()) puis fallback Postgres (CAST ... AS DATE)."""
    params = (target_day.isoformat(),)
    try:
        cursor.execute(
            """
            SELECT id, date_time, action, personnel_id, poste_id,
                   description, utilisateur, table_name, record_id
            FROM historique
            WHERE DATE(date_time) = %s
            ORDER BY date_time
            """,
            params,
        )
        return
    except Exception:
        cursor.execute(
            """
            SELECT id, date_time, action, personnel_id, poste_id,
                   description, utilisateur, table_name, record_id
            FROM historique
            WHERE CAST(date_time AS DATE) = %s
            ORDER BY date_time
            """,
            params,
        )

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

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        try:
            cur = conn.cursor(dictionary=True)
            dict_mode = True
        except TypeError:
            cur = conn.cursor()
            dict_mode = False

        _query_for_day(cur, day)
        rows = cur.fetchall()

        # normaliser en dicts
        if not dict_mode:
            names = [d[0] for d in cur.description]
            rows = [dict(zip(names, r)) for r in rows]

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

    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
