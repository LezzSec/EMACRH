# -*- coding: utf-8 -*-
"""
Script d'affectation en chaine des numeros de telephone pour le personnel ACTIF
sans valeur renseignee dans personnel_infos.

Affiche chaque employe et demande un numero de telephone.
Entree vide = passer au suivant.
'q' ou Ctrl+C = arreter.

Usage (depuis le dossier App/) :
    py -m scripts.affecter_telephones
    py -m scripts.affecter_telephones --tous        # inclut les INACTIF
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


_MAX_LEN = 20  # longueur max definie dans le schema : varchar(20)
_SEPARATORS_RE = re.compile(r"[\s.\-()]+")
_PHONE_RE = re.compile(r"^\+?\d{6,15}$")


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def _format_fr(numero: str) -> str:
    """Formate un numero francais sur 10 chiffres : 0612345678 -> 06 12 34 56 78."""
    return " ".join(numero[i:i + 2] for i in range(0, 10, 2))


def _format_fr_international(chiffres: str) -> str:
    """Formate la partie nationale d'un numero +33 : +33612345678 -> +33 6 12 34 56 78."""
    return "+33 " + " ".join([chiffres[0], *[chiffres[i:i + 2] for i in range(1, 9, 2)]])


def _normaliser_telephone(saisie: str):
    """
    Retourne un numero normalise ou None si invalide.

    Formats acceptes :
      - 0612345678, 06 12 34 56 78, 06.12.34.56.78
      - +33612345678, +33 6 12 34 56 78, 0033612345678
      - autres numeros internationaux au format +XXXXXXXX
    """
    valeur = saisie.strip()
    if not valeur:
        return None

    compacte = _SEPARATORS_RE.sub("", valeur)
    if compacte.startswith("00"):
        compacte = "+" + compacte[2:]

    if compacte.startswith("+330") and len(compacte) == 13:
        compacte = "+33" + compacte[4:]
    elif compacte.startswith("330") and len(compacte) == 12:
        compacte = "+33" + compacte[3:]

    if compacte.startswith("33") and len(compacte) == 11:
        compacte = "+" + compacte

    if not _PHONE_RE.match(compacte):
        return None

    if compacte.startswith("+33") and len(compacte) == 12:
        national = compacte[3:]
        if national[0] in "123456789":
            normalise = _format_fr_international(national)
        else:
            return None
    elif compacte.startswith("0") and len(compacte) == 10:
        normalise = _format_fr(compacte)
    elif compacte.startswith("+"):
        normalise = compacte
    else:
        return None

    if len(normalise) > _MAX_LEN:
        return None
    return normalise


def _afficher_resume(traites: int, ignores: int, total: int) -> None:
    print(f"\n{'='*60}")
    print(f"  Termine : {traites} numero(s) enregistre(s), {ignores} passe(s) sur {total}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Requete
# ---------------------------------------------------------------------------

def _fetch_sans_telephone(inclure_inactifs: bool):
    """Personnel sans telephone renseigne dans personnel_infos."""
    filtre_statut = "" if inclure_inactifs else "AND p.statut = 'ACTIF'"
    return QueryExecutor.fetch_all(
        f"""
        SELECT p.id, p.nom, p.prenom, p.matricule, p.statut
        FROM personnel p
        LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
        WHERE (pi.telephone IS NULL OR pi.telephone = '' OR pi.personnel_id IS NULL)
        {filtre_statut}
        ORDER BY p.nom, p.prenom
        """,
        dictionary=True,
    )


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Affectation des numeros de telephone")
    parser.add_argument(
        "--tous",
        action="store_true",
        help="Inclure les personnels INACTIF (par defaut : ACTIF seulement)",
    )
    args = parser.parse_args()

    personnel = _fetch_sans_telephone(inclure_inactifs=args.tous)

    if not personnel:
        scope = "tous statuts" if args.tous else "ACTIF"
        print(f"Tous les employes ({scope}) ont deja un telephone renseigne. Rien a faire.")
        return

    total = len(personnel)
    scope = "tous statuts" if args.tous else "ACTIF uniquement"
    print(f"\n{total} employe(s) sans telephone renseigne ({scope}).")
    print("Formats acceptes : 0612345678, 06 12 34 56 78, +33612345678.")
    print("Entree vide = passer | q = quitter\n")
    print(f"{'#':<5} {'Matricule':<12} {'Statut':<10} {'Nom':<22} {'Prenom'}")
    print("-" * 65)

    traites = ignores = 0

    for i, emp in enumerate(personnel, 1):
        pid = emp["id"]
        matricule = emp["matricule"] or "-"
        nom = emp["nom"]
        prenom = emp["prenom"]
        statut = emp["statut"]

        print(f"\n[{i}/{total}]  {matricule:<12} {statut:<10} {nom.upper():<22} {prenom}")

        while True:
            try:
                saisie = input("  Telephone : ").strip()
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

            valeur = _normaliser_telephone(saisie)
            if valeur is None:
                print(
                    "  Numero invalide. Saisir un numero francais ou international "
                    f"({_MAX_LEN} caracteres max une fois formate)."
                )
                continue

            confirm = input(
                f"  Confirmer '{valeur}' pour {nom} {prenom} ? (o/n) : "
            ).strip().lower()
            if confirm != "o":
                print("  Annule, ressaisissez.")
                continue

            PersonnelRepository.upsert_infos(pid, {"telephone": valeur})
            log_hist(
                "AFFECTATION_TELEPHONE",
                f"Telephone affecte via script batch : {valeur}",
                pid,
                None,
            )
            print(f"  -> Enregistre : {valeur}")
            traites += 1
            break

    _afficher_resume(traites, ignores, total)


if __name__ == "__main__":
    main()
