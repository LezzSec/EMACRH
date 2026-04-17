# -*- coding: utf-8 -*-
"""
Script de calcul en masse des distances domicile-entreprise pour tout le personnel.

Pour chaque membre du personnel ayant une adresse complète :
  - Géocode l'adresse (api-adresse.data.gouv.fr)
  - Calcule la distance routière (OSRM public ou ORS si EMAC_ORS_API_KEY défini)
  - Met à jour les colonnes latitude, longitude, distance_domicile_km, duree_trajet_min

Options :
  --force    : Recalcule même si une distance existe déjà
  --tous     : Inclut aussi le personnel INACTIF (défaut : ACTIF uniquement)
  --dry-run  : Affiche ce qui serait fait sans écrire en base

Usage (depuis le dossier App/) :
    py -m scripts.affecter_distances
    py -m scripts.affecter_distances --force
    py -m scripts.affecter_distances --tous --force
    py -m scripts.affecter_distances --dry-run
"""

import sys
import os
import time
import argparse

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Charger le .env avant d'importer les services
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(_env_path)

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.optimized_db_logger import log_hist
from domain.services.geo.distance_service import compute_distance_from_address
from domain.repositories.personnel_repo import PersonnelRepository

# Délai entre requêtes pour ne pas surcharger le serveur OSRM public
_DELAY_BETWEEN_REQUESTS = 1.2  # secondes


def _build_address(row: dict) -> str | None:
    """Assemble l'adresse complète depuis les champs personnels."""
    parts = []
    if row.get('adresse1'):
        parts.append(row['adresse1'].strip())
    if row.get('adresse2'):
        parts.append(row['adresse2'].strip())
    if row.get('cp_adresse'):
        parts.append(row['cp_adresse'].strip())
    if row.get('ville_adresse'):
        parts.append(row['ville_adresse'].strip())
    return ' '.join(parts) if len(parts) >= 2 else None


def main():
    parser = argparse.ArgumentParser(description="Calcul en masse des distances domicile-entreprise")
    parser.add_argument('--force', action='store_true',
                        help="Recalcule même si une distance existe déjà")
    parser.add_argument('--tous', action='store_true',
                        help="Inclut aussi le personnel INACTIF")
    parser.add_argument('--dry-run', action='store_true',
                        help="Affiche ce qui serait fait sans écrire en base")
    args = parser.parse_args()

    statut_clause = "" if args.tous else "AND p.statut = 'ACTIF'"

    rows = QueryExecutor.fetch_all(
        f"""
        SELECT p.id, p.nom, p.prenom, p.matricule, p.statut,
               pi.adresse1, pi.adresse2, pi.cp_adresse, pi.ville_adresse,
               pi.distance_domicile_km, pi.duree_trajet_min
        FROM personnel p
        LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
        WHERE 1=1 {statut_clause}
        ORDER BY p.nom, p.prenom
        """,
        dictionary=True,
    )

    if not rows:
        print("Aucun membre du personnel trouvé.")
        return

    # Filtrage
    avec_adresse = [r for r in rows if _build_address(r)]
    sans_adresse = len(rows) - len(avec_adresse)

    if not args.force:
        a_calculer = [r for r in avec_adresse if r.get('distance_domicile_km') is None]
        deja_calcule = len(avec_adresse) - len(a_calculer)
    else:
        a_calculer = avec_adresse
        deja_calcule = 0

    total = len(a_calculer)

    print(f"\n{'='*65}")
    print(f"  Calcul distances domicile-entreprise")
    if args.dry_run:
        print(f"  MODE DRY-RUN — aucune écriture en base")
    print(f"{'='*65}")
    print(f"  Personnel total          : {len(rows)}")
    print(f"  Sans adresse (ignorés)   : {sans_adresse}")
    if not args.force:
        print(f"  Distance déjà calculée   : {deja_calcule}")
    print(f"  A calculer               : {total}")
    print(f"{'='*65}\n")

    if total == 0:
        print("Rien à calculer. Utilisez --force pour recalculer.")
        return

    ok = ko = 0

    for i, row in enumerate(a_calculer, 1):
        pid = row['id']
        nom_complet = f"{row['nom'].upper()} {row['prenom']}"
        matricule = row.get('matricule') or '-'
        adresse = _build_address(row)

        dist_actuelle = row.get('distance_domicile_km')
        suffix = f"(était {dist_actuelle} km)" if dist_actuelle is not None else ""
        print(f"[{i:>3}/{total}]  {matricule:<10}  {nom_complet:<30}  {adresse}  {suffix}")

        if args.dry_run:
            print(f"         -> dry-run, skip\n")
            continue

        result = compute_distance_from_address(adresse)

        if result and result.get('distance_km') is not None:
            PersonnelRepository.update_distance_domicile(
                personnel_id=pid,
                latitude=result.get('latitude'),
                longitude=result.get('longitude'),
                distance_km=result['distance_km'],
                duree_min=result.get('duree_min'),
            )
            log_hist(
                "CALCUL_DISTANCE_DOMICILE",
                table_name="personnel_infos",
                record_id=pid,
                description=(
                    f"Distance calculée via script batch : {result['distance_km']} km, "
                    f"{result.get('duree_min')} min ({adresse})"
                ),
                operateur_id=pid,
            )
            print(f"         -> {result['distance_km']} km  ({result.get('duree_min')} min)\n")
            ok += 1
        elif result and result.get('latitude') is not None:
            # Géocodage OK mais routing KO : on sauve les coords sans distance
            PersonnelRepository.update_distance_domicile(
                personnel_id=pid,
                latitude=result['latitude'],
                longitude=result['longitude'],
                distance_km=None,
                duree_min=None,
            )
            print(f"         -> coords GPS sauvegardées, distance non calculée\n")
            ko += 1
        else:
            print(f"         -> adresse introuvable ou API en erreur\n")
            ko += 1

        # Pause pour ne pas surcharger le serveur OSRM public
        if i < total:
            time.sleep(_DELAY_BETWEEN_REQUESTS)

    print(f"\n{'='*65}")
    print(f"  Terminé : {ok} distance(s) calculée(s), {ko} échec(s) sur {total}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
