# -*- coding: utf-8 -*-
"""
Commande export-paie — export CSV du personnel pour intégration logiciel de paie / ERP.

Usage (depuis App/) :
    python -m cli export-paie
    python -m cli export-paie --output exports/paie_avril.csv
    python -m cli export-paie --statut ACTIF --format paie
    python -m cli export-paie --format polyvalence --output grille.csv

Formats disponibles :
    paie        : matricule, nom, prénom, contrat actif, dates → intégration paie / RH
    polyvalence : matricule, nom, prénom, postes certifiés, niveau moyen → ERP / pointeuse
    complet     : fusion des deux

La commande peut être appelée par un planificateur (cron, Tâches Windows) ou
depuis un script d'intégration ERP sans lancer l'interface graphique.
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from infrastructure.logging.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Colonnes par format
# ---------------------------------------------------------------------------

_COLS_PAIE = [
    "matricule", "nom", "prenom", "statut",
    "type_contrat", "date_debut_contrat", "date_fin_contrat",
    "email", "telephone",
]

_COLS_POLYVALENCE = [
    "matricule", "nom", "prenom", "statut",
    "nb_postes_certifies", "niveau_moyen", "derniere_evaluation",
]

_COLS_COMPLET = list(dict.fromkeys(_COLS_PAIE + _COLS_POLYVALENCE))  # sans doublon, ordre conservé


# ---------------------------------------------------------------------------
# Requêtes
# ---------------------------------------------------------------------------

def _fetch_personnel(statut: Optional[str]) -> List[Dict]:
    """Récupère le personnel avec son contrat actif le plus récent."""
    from infrastructure.db.query_executor import QueryExecutor

    where = "WHERE p.statut = %s" if statut else ""
    params = (statut,) if statut else ()

    return QueryExecutor.fetch_all(
        f"""
        SELECT
            p.matricule,
            p.nom,
            p.prenom,
            p.statut,
            p.email,
            p.telephone,
            c.type_contrat,
            c.date_debut  AS date_debut_contrat,
            c.date_fin    AS date_fin_contrat
        FROM personnel p
        LEFT JOIN contrats c ON c.id = (
            SELECT id FROM contrats
            WHERE operateur_id = p.id
            ORDER BY date_debut DESC
            LIMIT 1
        )
        {where}
        ORDER BY p.nom, p.prenom
        """,
        params,
        dictionary=True,
    )


def _fetch_polyvalence_summary(statut: Optional[str]) -> Dict[str, Dict]:
    """Retourne un dict matricule → résumé polyvalence."""
    from infrastructure.db.query_executor import QueryExecutor

    where = "AND p.statut = %s" if statut else ""
    params = (statut,) if statut else ()

    rows = QueryExecutor.fetch_all(
        f"""
        SELECT
            p.matricule,
            COUNT(po.id)                   AS nb_postes_certifies,
            ROUND(AVG(po.niveau), 1)       AS niveau_moyen,
            MAX(po.date_evaluation)        AS derniere_evaluation
        FROM personnel p
        LEFT JOIN polyvalence po ON po.operateur_id = p.id
        {where}
        GROUP BY p.id, p.matricule
        """,
        params,
        dictionary=True,
    )

    return {r["matricule"]: r for r in rows if r["matricule"]}


# ---------------------------------------------------------------------------
# Formatage
# ---------------------------------------------------------------------------

def _fmt_date(val) -> str:
    if val is None:
        return ""
    if hasattr(val, "strftime"):
        return val.strftime("%d/%m/%Y")
    return str(val)


def _build_row(pers: Dict, poly_summary: Dict, fmt: str) -> Dict:
    """Construit une ligne CSV selon le format demandé."""
    matricule = pers.get("matricule") or ""
    poly = poly_summary.get(matricule, {})

    base = {
        "matricule": matricule,
        "nom": pers.get("nom") or "",
        "prenom": pers.get("prenom") or "",
        "statut": pers.get("statut") or "",
        "type_contrat": pers.get("type_contrat") or "",
        "date_debut_contrat": _fmt_date(pers.get("date_debut_contrat")),
        "date_fin_contrat": _fmt_date(pers.get("date_fin_contrat")),
        "email": pers.get("email") or "",
        "telephone": pers.get("telephone") or "",
        "nb_postes_certifies": poly.get("nb_postes_certifies") or 0,
        "niveau_moyen": poly.get("niveau_moyen") or "",
        "derniere_evaluation": _fmt_date(poly.get("derniere_evaluation")),
    }

    cols = {"paie": _COLS_PAIE, "polyvalence": _COLS_POLYVALENCE}.get(fmt, _COLS_COMPLET)
    return {k: base[k] for k in cols}


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def run_export_paie(args) -> None:
    """Lance l'export paie/polyvalence en CSV."""
    setup_logging(production_mode=False)

    fmt = getattr(args, "format", "paie") or "paie"
    statut = getattr(args, "statut", None)
    output_arg = getattr(args, "output", None)

    # Chemin de sortie
    if output_arg:
        output_path = Path(output_arg)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        exports_dir = Path(__file__).parents[3] / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        output_path = exports_dir / f"paie_{fmt}_{ts}.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cols = {"paie": _COLS_PAIE, "polyvalence": _COLS_POLYVALENCE}.get(fmt, _COLS_COMPLET)

    try:
        print(f"Chargement personnel (statut={statut or 'tous'})…")
        personnels = _fetch_personnel(statut)

        poly_summary: Dict = {}
        if fmt in ("polyvalence", "complet"):
            print("Chargement résumé polyvalence…")
            poly_summary = _fetch_polyvalence_summary(statut)

        print(f"Export vers {output_path} ({fmt}, {len(personnels)} ligne(s))…")

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=cols, delimiter=";")
            writer.writeheader()
            for pers in personnels:
                writer.writerow(_build_row(pers, poly_summary, fmt))

        print(f"Export terminé : {output_path.resolve()}")
        logger.info(f"Export paie '{fmt}' : {len(personnels)} lignes → {output_path}")

    except Exception as e:
        logger.exception(f"Erreur export paie : {e}")
        print(f"ERREUR : {e}", file=sys.stderr)
        sys.exit(1)
