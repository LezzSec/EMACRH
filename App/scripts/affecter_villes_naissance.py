# -*- coding: utf-8 -*-
"""
Script d'affectation en chaine de la ville de naissance pour le personnel ACTIF
sans valeur renseignee dans personnel_infos.

Affiche chaque employe et demande une saisie libre.
Entree vide = passer au suivant.
'q' ou Ctrl+C = arreter.

Usage (depuis le dossier App/) :
    py -m scripts.affecter_villes_naissance
    py -m scripts.affecter_villes_naissance --tous        # inclut les INACTIF
"""

import sys
import os
import argparse
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.query_executor import QueryExecutor
from domain.repositories.personnel_repo import PersonnelRepository
from infrastructure.logging.optimized_db_logger import log_hist


_MAX_LEN = 100  # longueur max definie dans le schema (varchar(100))

# Caracteres autorises : lettres (y compris accentuees), espaces, tirets, apostrophes
_PATTERN = re.compile(r"^[\w\s'\-àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]+$", re.UNICODE)


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def _normaliser(saisie: str) -> str:
    """Supprime les espaces superflus et met en titre."""
    return " ".join(saisie.split()).upper()


def _valider(saisie: str):
    """Retourne la valeur normalisee ou None si invalide."""
    valeur = _normaliser(saisie)
    if not valeur:
        return None
    if len(valeur) > _MAX_LEN:
        return None
    if not _PATTERN.match(valeur):
        return None
    return valeur


def _afficher_resume(traites: int, ignores: int, total: int) -> None:
    print(f"\n{'='*60}")
    print(f"  Termine : {traites} valeur(s) enregistree(s), {ignores} passe(s) sur {total}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Requete
# ---------------------------------------------------------------------------

def _fetch_sans_ville(inclure_inactifs: bool):
    """Personnel sans ville de naissance dans personnel_infos."""
    filtre_statut = "" if inclure_inactifs else "AND p.statut = 'ACTIF'"
    return QueryExecutor.fetch_all(
        f"""
        SELECT p.id, p.nom, p.prenom, p.matricule, p.statut
        FROM personnel p
        LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
        WHERE (pi.ville_naissance IS NULL OR pi.ville_naissance = '' OR pi.personnel_id IS NULL)
        {filtre_statut}
        ORDER BY p.nom, p.prenom
        """,
        dictionary=True,
    )


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Affectation de la ville de naissance")
    parser.add_argument(
        "--tous",
        action="store_true",
        help="Inclure les personnels INACTIF (par defaut : ACTIF seulement)",
    )
    args = parser.parse_args()

    personnel = _fetch_sans_ville(inclure_inactifs=args.tous)

    if not personnel:
        scope = "tous statuts" if args.tous else "ACTIF"
        print(f"Tous les employes ({scope}) ont deja une ville de naissance renseignee. Rien a faire.")
        return

    total = len(personnel)
    scope = "tous statuts" if args.tous else "ACTIF uniquement"
    print(f"\n{total} employe(s) sans ville de naissance ({scope}).")
    print("Saisie libre (max 100 caracteres). Sera enregistree en majuscules.")
    print("Entree vide = passer | q = quitter\n")
    print(f"{'#':<5} {'Matricule':<12} {'Statut':<10} {'Nom':<22} {'Prenom'}")
    print("-" * 65)

    traites = ignores = 0

    for i, emp in enumerate(personnel, 1):
        pid       = emp['id']
        matricule = emp['matricule'] or '-'
        nom       = emp['nom']
        prenom    = emp['prenom']
        statut    = emp['statut']

        print(f"\n[{i}/{total}]  {matricule:<12} {statut:<10} {nom.upper():<22} {prenom}")

        while True:
            try:
                saisie = input("  Ville de naissance : ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nArret demande.")
                _afficher_resume(traites, ignores, total)
                return

            if saisie.lower() == 'q':
                _afficher_resume(traites, ignores, total)
                return

            if saisie == '':
                print("  -> Passe.")
                ignores += 1
                break

            valeur = _valider(saisie)
            if valeur is None:
                print(f"  Valeur invalide (max {_MAX_LEN} caracteres, lettres/tirets/apostrophes uniquement).")
                continue

            confirm = input(
                f"  Confirmer '{valeur}' pour {nom} {prenom} ? (o/n) : "
            ).strip().lower()
            if confirm != 'o':
                print("  Annule, ressaisissez.")
                continue

            PersonnelRepository.upsert_infos(pid, {"ville_naissance": valeur})
            log_hist(
                "AFFECTATION_VILLE_NAISSANCE",
                f"Ville de naissance affectee via script batch : {valeur}",
                pid,
                None,
            )
            print(f"  -> Enregistre : {valeur}")
            traites += 1
            break

    _afficher_resume(traites, ignores, total)


if __name__ == "__main__":
    main()
