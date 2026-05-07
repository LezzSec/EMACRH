# -*- coding: utf-8 -*-
"""
Script d'affectation en chaine des numeros de securite sociale.

Affiche chaque employe et demande un numero de securite sociale.
Entree vide = passer au suivant.
'q' ou Ctrl+C = arreter.

Le numero est stocke au format compact sur 15 caracteres dans personnel_infos.numero_ss.
La cle NIR est verifiee avant enregistrement.

Usage (depuis le dossier App/) :
    py -m scripts.affecter_numeros_ss
    py -m scripts.affecter_numeros_ss --tous
    py -m scripts.affecter_numeros_ss --force   # inclut aussi ceux deja renseignes
"""

import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.repositories.personnel_repo import PersonnelRepository
from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.optimized_db_logger import log_hist


_SEPARATORS_RE = re.compile(r"[\s.\-]+")
_NIR_RE = re.compile(r"^[1-478][0-9]{2}(0[1-9]|1[0-2])([0-9]{2}|2A|2B)[0-9]{6}[0-9]{2}$")


def _format_numero_ss(value: str) -> str:
    clean = (value or "").replace(" ", "").upper()
    if len(clean) != 15:
        return value or ""
    return f"{clean[0]} {clean[1:3]} {clean[3:5]} {clean[5:7]} {clean[7:10]} {clean[10:13]} {clean[13:15]}"


def _mask_numero_ss(value: str) -> str:
    clean = (value or "").replace(" ", "").upper()
    if len(clean) != 15:
        return "***"
    return f"{clean[0]} {clean[1:3]} ** ** *** *** {clean[13:15]}"


def _nir_base_for_key(numero_ss: str) -> int:
    base = numero_ss[:13]
    base = base.replace("2A", "19").replace("2B", "18")
    return int(base)


def _expected_key(numero_ss: str) -> int:
    return 97 - (_nir_base_for_key(numero_ss) % 97)


def _normaliser_numero_ss(saisie: str) -> str | None:
    compact = _SEPARATORS_RE.sub("", saisie.strip()).upper()
    if not compact:
        return None

    if not _NIR_RE.match(compact):
        return None

    key = int(compact[13:15])
    if key != _expected_key(compact):
        return None

    return compact


def _context_warnings(numero_ss: str, emp: dict) -> list[str]:
    warnings = []

    sexe = (emp.get("sexe") or "").strip().upper()
    first_digit = numero_ss[0]
    if sexe == "M" and first_digit not in {"1", "3", "7"}:
        warnings.append("sexe fiche=M mais le NIR ne commence pas par 1/3/7")
    elif sexe == "F" and first_digit not in {"2", "4", "8"}:
        warnings.append("sexe fiche=F mais le NIR ne commence pas par 2/4/8")

    date_naissance = emp.get("date_naissance")
    if date_naissance:
        yy = f"{date_naissance.year % 100:02d}"
        mm = f"{date_naissance.month:02d}"
        if numero_ss[1:3] != yy:
            warnings.append(f"annee naissance fiche={yy}, NIR={numero_ss[1:3]}")
        if numero_ss[3:5] != mm:
            warnings.append(f"mois naissance fiche={mm}, NIR={numero_ss[3:5]}")

    return warnings


def _afficher_resume(traites: int, ignores: int, total: int) -> None:
    print(f"\n{'=' * 60}")
    print(f"  Termine : {traites} numero(s) enregistre(s), {ignores} passe(s) sur {total}")
    print(f"{'=' * 60}\n")


def _fetch_personnel(inclure_inactifs: bool, force: bool) -> list[dict]:
    filtre_statut = "" if inclure_inactifs else "AND p.statut = 'ACTIF'"
    filtre_numero = "" if force else "AND (pi.numero_ss IS NULL OR pi.numero_ss = '' OR pi.personnel_id IS NULL)"
    return QueryExecutor.fetch_all(
        f"""
        SELECT
            p.id, p.nom, p.prenom, p.matricule, p.statut,
            pi.numero_ss, pi.sexe, pi.date_naissance
        FROM personnel p
        LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
        WHERE 1=1
        {filtre_statut}
        {filtre_numero}
        ORDER BY p.nom, p.prenom
        """,
        dictionary=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Affectation des numeros de securite sociale")
    parser.add_argument(
        "--tous",
        action="store_true",
        help="Inclure les personnels INACTIF (par defaut : ACTIF seulement)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Inclure aussi les personnels qui ont deja un numero renseigne",
    )
    args = parser.parse_args()

    personnel = _fetch_personnel(inclure_inactifs=args.tous, force=args.force)

    if not personnel:
        scope = "tous statuts" if args.tous else "ACTIF"
        print(f"Tous les employes ({scope}) ont deja un numero de securite sociale renseigne. Rien a faire.")
        return

    total = len(personnel)
    scope = "tous statuts" if args.tous else "ACTIF uniquement"
    print(f"\n{total} employe(s) a traiter ({scope}).")
    print("Formats acceptes : 193027510813615, 1 93 02 75 108 136 15, 2A/2B acceptes.")
    print("La cle NIR est verifiee. Entree vide = passer | q = quitter\n")
    print(f"{'#':<5} {'Matricule':<12} {'Statut':<10} {'Nom':<22} {'Prenom'}")
    print("-" * 65)

    traites = ignores = 0

    for i, emp in enumerate(personnel, 1):
        pid = emp["id"]
        matricule = emp["matricule"] or "-"
        nom = emp["nom"]
        prenom = emp["prenom"]
        statut = emp["statut"]
        actuel = emp.get("numero_ss") or ""

        print(f"\n[{i}/{total}]  {matricule:<12} {statut:<10} {nom.upper():<22} {prenom}")
        if actuel:
            print(f"  Actuel : {_mask_numero_ss(actuel)}")

        while True:
            try:
                saisie = input("  Numero SS : ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nArret demande.")
                _afficher_resume(traites, ignores, total)
                return

            if saisie.lower() == "q":
                _afficher_resume(traites, ignores, total)
                return

            if saisie == "":
                print("  -> Passe.")
                ignores += 1
                break

            valeur = _normaliser_numero_ss(saisie)
            if valeur is None:
                print("  Numero invalide : format attendu sur 15 caracteres et cle NIR correcte.")
                continue

            warnings = _context_warnings(valeur, emp)
            if warnings:
                print("  Attention :")
                for warning in warnings:
                    print(f"    - {warning}")

            confirm = input(
                f"  Confirmer '{_format_numero_ss(valeur)}' pour {nom} {prenom} ? (o/n) : "
            ).strip().lower()
            if confirm != "o":
                print("  Annule, ressaisissez.")
                continue

            PersonnelRepository.upsert_infos(pid, {"numero_ss": valeur})
            log_hist(
                "AFFECTATION_NUMERO_SS",
                f"Numero de securite sociale affecte via script batch : {_mask_numero_ss(valeur)}",
                pid,
                None,
            )
            print(f"  -> Enregistre : {_mask_numero_ss(valeur)}")
            traites += 1
            break

    _afficher_resume(traites, ignores, total)


if __name__ == "__main__":
    main()
