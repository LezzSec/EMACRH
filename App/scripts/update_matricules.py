# -*- coding: utf-8 -*-
"""
Met à jour les matricules dans la table `personnel` (MySQL/emac_db)
à partir des MATRI trouvés dans `hopempl` (SQL Server).

Lancement :
    cd App
    python scripts/update_matricules.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.configbd import _load_env_once
from infrastructure.db.query_executor import QueryExecutor
from scripts.comparer_matricules import run_comparison

_load_env_once()


def apply_updates() -> None:
    results = run_comparison(include_all=True)
    to_update = [r for r in results if r["statut"] == "DIFF"]

    print(f"\n{len(to_update)} matricules à mettre à jour...\n")

    updated = 0
    errors = []

    for r in to_update:
        try:
            QueryExecutor.execute_write(
                "UPDATE personnel SET matricule = %s WHERE id = %s",
                (r["matri_base2"], r["id_mysql"])
            )
            print(f"  OK  {r['nom']:<25} {r['prenom']:<20} {r['matricule_base1'] or '(vide)':<15} -> {r['matri_base2']}")
            updated += 1
        except Exception as e:
            errors.append((r, str(e)))
            print(f"  ERR {r['nom']:<25} {r['prenom']:<20} {e}")

    print(f"\n{updated} matricules mis à jour.")
    if errors:
        print(f"{len(errors)} erreurs.")


if __name__ == "__main__":
    apply_updates()
