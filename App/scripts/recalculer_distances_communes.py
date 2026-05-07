# -*- coding: utf-8 -*-
"""
Recalcule en masse les distances RGPD-friendly CP + commune.

Le script :
  - lit le CP et la ville depuis personnel_infos ;
  - calcule une seule fois chaque couple CP + ville ;
  - met a jour les distances commune/mairie dans personnel_infos ;
  - met a jour la mobilite active existante avec la distance mairie si disponible ;
  - attend entre deux communes pour eviter de taper trop vite les API publiques.

Usage depuis le dossier App/ :
    py -m scripts.recalculer_distances_communes --dry-run
    py -m scripts.recalculer_distances_communes --delay 3
    py -m scripts.recalculer_distances_communes --tous --delay 3
"""

import argparse
import os
import sys
import time
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_APP_DIR, ".env"))

from domain.repositories.personnel_repo import PersonnelRepository
from domain.services.geo.distance_service import compute_distances_for_commune
from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.optimized_db_logger import log_hist


def _commune_key(cp: str, ville: str) -> str:
    return f"{(cp or '').strip()}|{(ville or '').strip().lower()}"


def _fetch_personnel(include_inactive: bool) -> list[dict]:
    statut_clause = "" if include_inactive else "AND UPPER(COALESCE(p.statut, '')) = 'ACTIF'"
    return QueryExecutor.fetch_all(
        f"""
        SELECT
            p.id, p.nom, p.prenom, p.matricule, p.statut,
            pi.cp_adresse, pi.ville_adresse,
            pi.distance_commune_km, pi.distance_mairie_km,
            pm.id AS mobilite_id,
            pm.distance_km AS mobilite_distance_km
        FROM personnel p
        LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
        LEFT JOIN personnel_mobilite pm
          ON pm.personnel_id = p.id
         AND pm.actif = 1
         AND pm.date_fin IS NULL
        WHERE 1=1 {statut_clause}
        ORDER BY p.nom, p.prenom, p.id
        """,
        dictionary=True,
    )


def _update_personnel_infos(personnel_id: int, result: dict) -> None:
    PersonnelRepository.update_distances(
        personnel_id=personnel_id,
        code_insee_commune=result["code_insee_commune"],
        commune_lat=result["commune_lat"],
        commune_lon=result["commune_lon"],
        distance_commune_km=result["distance_commune_km"],
        duree_trajet_commune_min=result["duree_trajet_commune_min"],
        mairie_lat=result["mairie_lat"],
        mairie_lon=result["mairie_lon"],
        distance_mairie_km=result["distance_mairie_km"],
        duree_trajet_mairie_min=result["duree_trajet_mairie_min"],
    )


def _update_mobilite_active(row: dict, cp: str, ville: str, result: dict) -> float | None:
    mobilite_id = row.get("mobilite_id")
    if not mobilite_id:
        return None

    dist = result.get("distance_mairie_km")
    if dist is None:
        dist = result.get("distance_commune_km")
    if dist is None:
        return None

    QueryExecutor.execute_write(
        """
        UPDATE personnel_mobilite
        SET distance_km = %s,
            cp_depart = %s,
            ville_depart = %s
        WHERE id = %s
        """,
        (dist, cp, ville, mobilite_id),
        return_lastrowid=False,
    )
    return float(dist)


def main() -> None:
    parser = argparse.ArgumentParser(description="Recalcul lent des distances CP + commune")
    parser.add_argument("--tous", action="store_true", help="Inclut aussi le personnel inactif")
    parser.add_argument("--dry-run", action="store_true", help="Affiche sans ecrire en base")
    parser.add_argument("--delay", type=float, default=3.0, help="Pause en secondes entre deux communes")
    parser.add_argument("--limit", type=int, default=0, help="Limite le nombre de communes uniques a calculer")
    parser.add_argument("--cp", default="", help="Ne traite que ce code postal")
    parser.add_argument("--ville", default="", help="Ne traite que cette ville (insensible a la casse)")
    parser.add_argument(
        "--skip-mobilite",
        action="store_true",
        help="Ne met pas a jour les lignes personnel_mobilite actives",
    )
    args = parser.parse_args()

    rows = _fetch_personnel(include_inactive=args.tous)
    rows = [
        row for row in rows
        if (row.get("cp_adresse") or "").strip() and (row.get("ville_adresse") or "").strip()
    ]
    if args.cp:
        rows = [row for row in rows if (row.get("cp_adresse") or "").strip() == args.cp.strip()]
    if args.ville:
        ville_filter = args.ville.strip().lower()
        rows = [
            row for row in rows
            if (row.get("ville_adresse") or "").strip().lower() == ville_filter
        ]

    by_commune: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_commune[_commune_key(row["cp_adresse"], row["ville_adresse"])].append(row)

    items = list(by_commune.items())
    if args.limit > 0:
        items = items[:args.limit]

    print("\n" + "=" * 72)
    print("  Recalcul distances CP + commune")
    print(f"  Personnel avec CP/ville : {len(rows)}")
    print(f"  Communes uniques        : {len(by_commune)}")
    print(f"  Communes a traiter      : {len(items)}")
    print(f"  Delai entre communes    : {args.delay:.1f}s")
    if args.dry_run:
        print("  MODE DRY-RUN            : aucune ecriture en base")
    if args.skip_mobilite:
        print("  Mobilite active         : non modifiee")
    print("=" * 72 + "\n")

    ok_communes = ko_communes = ok_personnel = ok_mobilites = 0

    for idx, (key, persons) in enumerate(items, 1):
        first = persons[0]
        cp = (first.get("cp_adresse") or "").strip()
        ville = (first.get("ville_adresse") or "").strip()
        print(f"[{idx:>3}/{len(items)}] {cp} {ville}  ({len(persons)} personne(s))")

        if args.dry_run:
            print("      -> dry-run\n")
            continue

        result = compute_distances_for_commune(cp, ville)
        if result is None:
            print("      -> echec resolution/calcul")
            ko_communes += 1
        elif result.get("distance_mairie_km") is None and result.get("distance_commune_km") is None:
            print("      -> echec routing, aucune distance exploitable")
            ko_communes += 1
        else:
            d_mairie = result.get("distance_mairie_km")
            d_commune = result.get("distance_commune_km")
            for row in persons:
                pid = row["id"]
                _update_personnel_infos(pid, result)
                ok_personnel += 1

                if not args.skip_mobilite:
                    dist_mobilite = _update_mobilite_active(row, cp, ville, result)
                    if dist_mobilite is not None:
                        ok_mobilites += 1

                log_hist(
                    "RECALCUL_DISTANCE_COMMUNE",
                    table_name="personnel_infos",
                    record_id=pid,
                    description=(
                        f"Distance commune recalculee : mairie={d_mairie} km, "
                        f"commune={d_commune} km ({cp} {ville})"
                    ),
                    operateur_id=pid,
                )

            ok_communes += 1
            print(
                f"      -> mairie={d_mairie} km, commune={d_commune} km, "
                f"{len(persons)} fiche(s) maj"
            )

        if idx < len(items) and args.delay > 0:
            time.sleep(args.delay)
        print()

    print("=" * 72)
    print(f"  Communes OK / KO       : {ok_communes} / {ko_communes}")
    print(f"  Personnel mis a jour   : {ok_personnel}")
    print(f"  Mobilites actives maj  : {ok_mobilites}")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
