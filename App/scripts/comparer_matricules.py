# -*- coding: utf-8 -*-
"""
Comparaison des matricules entre la base EMAC (MySQL) et la base RH externe (SQL Server).

Base 1 (MySQL/emac_db) : table `personnel`  -> colonnes matricule, nom, prenom
Base 2 (SQL Server)    : table `hopempl`    -> colonnes MATRI, NOM, PRENOM

Principe :
  - Rapprochement par NOM + PRENOM (insensible à la casse, accents normalisés)
  - Affiche les cas où les matricules diffèrent -> à corriger dans la base 1
  - Exporte les résultats dans un fichier CSV

Lancement :
    cd App
    python scripts/comparer_matricules.py
    python scripts/comparer_matricules.py --output comparaison.csv
"""

import sys
import os
import csv
import argparse
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.configbd import _load_env_once, DatabaseCursor
from infrastructure.db.sqlserver_config import SqlServerCursor


def normalize(s: str) -> str:
    """Minuscule + suppression des accents + strip."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s.strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def load_personnel_mysql() -> list[dict]:
    """Charge id, matricule, nom, prenom depuis MySQL."""
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute(
            "SELECT id, matricule, nom, prenom FROM personnel WHERE statut = 'ACTIF' ORDER BY nom, prenom"
        )
        return cur.fetchall()


def load_hopempl_sqlserver() -> list[dict]:
    """Charge MATRI, NOM, PRENOM depuis SQL Server."""
    with SqlServerCursor() as cur:
        cur.execute("SELECT MATRI, NOM, PRENOM FROM hopempl WHERE DATCLO = '1900-01-01'")
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
    return [dict(zip(cols, r)) for r in rows]


def build_hopempl_index(hopempl: list[dict]) -> dict[str, list[dict]]:
    """Index par (nom_normalisé, prenom_normalisé) -> liste d'entrées."""
    index: dict[str, list[dict]] = {}
    for row in hopempl:
        key = (normalize(row.get("NOM", "")), normalize(row.get("PRENOM", "")))
        index.setdefault(key, []).append(row)
    return index


def run_comparison(include_all: bool = False) -> list[dict]:
    """
    Retourne une liste de résultats.
    Chaque entrée contient :
        id_mysql, nom, prenom,
        matricule_mysql (base 1),
        matri_sqlserver (base 2),
        statut : 'DIFF' | 'OK' | 'NON_TROUVE'
    """
    print("Chargement base 1 (MySQL)...")
    personnel = load_personnel_mysql()
    print(f"  {len(personnel)} employés actifs trouvés.")

    print("Chargement base 2 (SQL Server hopempl)...")
    hopempl = load_hopempl_sqlserver()
    print(f"  {len(hopempl)} entrées hopempl trouvées.")

    index = build_hopempl_index(hopempl)
    results = []

    for p in personnel:
        key = (normalize(p["nom"] or ""), normalize(p["prenom"] or ""))
        matches = index.get(key, [])

        if not matches:
            results.append({
                "id_mysql":          p["id"],
                "nom":               p["nom"],
                "prenom":            p["prenom"],
                "matricule_base1":   p["matricule"] or "",
                "matri_base2":       "",
                "statut":            "NON_TROUVE",
                "nb_correspondances": 0,
            })
        elif len(matches) == 1:
            m = matches[0]
            matri2 = (m["MATRI"] or "").strip()
            matri1 = (p["matricule"] or "").strip()
            statut = "OK" if matri1 == matri2 else "DIFF"
            if statut == "DIFF" or include_all:
                results.append({
                    "id_mysql":           p["id"],
                    "nom":                p["nom"],
                    "prenom":             p["prenom"],
                    "matricule_base1":    matri1,
                    "matri_base2":        matri2,
                    "statut":             statut,
                    "nb_correspondances": 1,
                })
        else:
            # Plusieurs entrées : prendre celle dont le MATRI commence par '0'
            candidates = [m for m in matches if (m["MATRI"] or "").strip().startswith("0")]
            if len(candidates) == 1:
                matri2 = candidates[0]["MATRI"].strip()
                matri1 = (p["matricule"] or "").strip()
                statut = "OK" if matri1 == matri2 else "DIFF"
                if statut == "DIFF" or include_all:
                    results.append({
                        "id_mysql":           p["id"],
                        "nom":                p["nom"],
                        "prenom":             p["prenom"],
                        "matricule_base1":    matri1,
                        "matri_base2":        matri2,
                        "statut":             statut,
                        "nb_correspondances": len(matches),
                    })
            else:
                # Toujours ambigu après filtrage (0 ou 2+ commençant par '0')
                matri2_values = ", ".join((m["MATRI"] or "").strip() for m in matches)
                results.append({
                    "id_mysql":           p["id"],
                    "nom":                p["nom"],
                    "prenom":             p["prenom"],
                    "matricule_base1":    (p["matricule"] or "").strip(),
                    "matri_base2":        matri2_values,
                    "statut":             "AMBIGU",
                    "nb_correspondances": len(matches),
                })

    return results


def print_report(results: list[dict]) -> None:
    diff = [r for r in results if r["statut"] == "DIFF"]
    ambigu = [r for r in results if r["statut"] == "AMBIGU"]
    non_trouve = [r for r in results if r["statut"] == "NON_TROUVE"]
    ok = [r for r in results if r["statut"] == "OK"]

    print(f"\n{'='*70}")
    print(f"  RESULTATS DE COMPARAISON DES MATRICULES")
    print(f"{'='*70}")
    print(f"  OK (matricules identiques)    : {len(ok)}")
    print(f"  DIFF (matricule a corriger)   : {len(diff)}")
    print(f"  AMBIGU (doublon nom/prenom)   : {len(ambigu)}")
    print(f"  NON TROUVE (absent base 2)    : {len(non_trouve)}")
    print(f"{'='*70}")

    if diff:
        print(f"\n--- MATRICULES DIFFERENTS ({len(diff)}) ---")
        print(f"{'NOM':<20} {'PRENOM':<20} {'BASE1 (MySQL)':<15} {'BASE2 (SS)':<15}")
        print("-" * 70)
        for r in diff:
            print(f"{r['nom']:<20} {r['prenom']:<20} {r['matricule_base1']:<15} {r['matri_base2']:<15}")

    if ambigu:
        print(f"\n--- AMBIGUS - plusieurs entrees hopempl ({len(ambigu)}) ---")
        print(f"{'NOM':<20} {'PRENOM':<20} {'BASE1':<15} {'BASE2 (tous)':<30}")
        print("-" * 85)
        for r in ambigu:
            print(f"{r['nom']:<20} {r['prenom']:<20} {r['matricule_base1']:<15} {r['matri_base2']:<30}")

    if non_trouve:
        print(f"\n--- NON TROUVES dans hopempl ({len(non_trouve)}) ---")
        print(f"{'NOM':<20} {'PRENOM':<20} {'BASE1':<15}")
        print("-" * 55)
        for r in non_trouve:
            print(f"{r['nom']:<20} {r['prenom']:<20} {r['matricule_base1']:<15}")


def export_csv(results: list[dict], path: str) -> None:
    fieldnames = ["id_mysql", "nom", "prenom", "matricule_base1", "matri_base2", "statut", "nb_correspondances"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(results)
    print(f"\nExporte dans : {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comparaison matricules MySQL vs SQL Server")
    parser.add_argument("--output", "-o", help="Fichier CSV de sortie (optionnel)")
    parser.add_argument("--all", action="store_true", help="Inclure aussi les lignes OK dans le CSV")
    args = parser.parse_args()

    _load_env_once()

    try:
        results = run_comparison(include_all=args.all)
        print_report(results)
        if args.output:
            export_csv(results, args.output)
        else:
            diff_count = sum(1 for r in results if r["statut"] == "DIFF")
            if diff_count > 0:
                print(f"\nAstuce : relancer avec --output comparaison_matricules.csv pour exporter.")
    except Exception as e:
        print(f"ERREUR : {e}", file=sys.stderr)
        sys.exit(1)
