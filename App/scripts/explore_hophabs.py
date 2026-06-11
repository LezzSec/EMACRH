# -*- coding: utf-8 -*-
"""
Exploration de la table HOPHABS dans SQL Server.

Affiche :
  1. Colonnes et types
  2. Nombre de lignes
  3. Plage de dates (min/max)
  4. Echantillon de 10 lignes
  5. Valeurs distinctes des colonnes clés (MATRI, MOTIF, statut...)

Lancement :
    cd App
    python scripts/explore_hophabs.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.configbd import _load_env_once
from infrastructure.db.sqlserver_config import SqlServerCursor

_load_env_once()

TABLE = "HOPHABS"


def _cols(cur) -> list[tuple]:
    """Retourne les colonnes de la table : (nom, type, nullable)."""
    cur.execute(
        "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE "
        "FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME = ? "
        "ORDER BY ORDINAL_POSITION",
        (TABLE,)
    )
    return cur.fetchall()


def _count(cur) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
    return cur.fetchone()[0]


def _date_range(cur, col: str):
    try:
        cur.execute(f"SELECT MIN({col}), MAX({col}) FROM {TABLE}")
        return cur.fetchone()
    except Exception:
        return None, None


def _sample(cur, n: int = 10):
    cur.execute(f"SELECT TOP {n} * FROM {TABLE}")
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    return cols, rows


def _distinct(cur, col: str, limit: int = 30):
    try:
        cur.execute(
            f"SELECT TOP {limit} {col}, COUNT(*) as n "
            f"FROM {TABLE} WHERE {col} IS NOT NULL "
            f"GROUP BY {col} ORDER BY n DESC"
        )
        return cur.fetchall()
    except Exception as e:
        return [(f"<erreur: {e}>", 0)]


def run():
    print(f"\n{'=' * 60}")
    print(f"  Exploration de {TABLE}")
    print(f"{'=' * 60}\n")

    with SqlServerCursor() as cur:
        # 1. Colonnes
        cols_info = _cols(cur)
        if not cols_info:
            print(f"Table {TABLE} introuvable ou inaccessible.")
            return

        print(f"COLONNES ({len(cols_info)}) :")
        for name, dtype, nullable in cols_info:
            print(f"  {name:<25} {dtype:<15} {'NULL' if nullable == 'YES' else 'NOT NULL'}")

        col_names = [c[0] for c in cols_info]

        # 2. Nombre de lignes
        n = _count(cur)
        print(f"\nNOMBRE DE LIGNES : {n:,}")

        # 3. Plages de dates pour colonnes date probables
        date_cols = [c for c in col_names if any(k in c.upper() for k in ("DAT", "DATE", "DEB", "FIN"))]
        if date_cols:
            print(f"\nPLAGES DE DATES :")
            for dc in date_cols[:6]:
                mn, mx = _date_range(cur, dc)
                print(f"  {dc:<25} {str(mn):<20} → {str(mx)}")

        # 4. Valeurs distinctes des colonnes clés
        key_cols = [c for c in col_names if any(k in c.upper()
                    for k in ("MATRI", "MOTIF", "STAT", "TYPE", "NATURE", "CODE"))]
        if key_cols:
            print(f"\nVALEURS DISTINCTES (colonnes clés) :")
            for kc in key_cols[:6]:
                vals = _distinct(cur, kc)
                print(f"\n  {kc} :")
                for v, cnt in vals:
                    print(f"    {str(v):<30} {cnt:>6} lignes")

        # 5. Echantillon
        sample_cols, sample_rows = _sample(cur, 10)
        print(f"\nECHANTILLON (10 premières lignes) :")
        header = "  " + " | ".join(f"{c[:18]:<18}" for c in sample_cols)
        print(header)
        print("  " + "-" * (len(header) - 2))
        for row in sample_rows:
            line = "  " + " | ".join(f"{str(v)[:18]:<18}" for v in row)
            print(line)

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"\nERREUR : {e}", file=sys.stderr)
        sys.exit(1)
