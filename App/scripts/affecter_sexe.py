# -*- coding: utf-8 -*-
"""
Script d'affectation en chaine du sexe pour le personnel ACTIF
sans valeur renseignee (NULL ou NSP) dans personnel_infos.

Affiche chaque employe et demande H / F (ou M / F / X).
Entree vide = passer au suivant.
'q' ou Ctrl+C = arreter.

Usage (depuis le dossier App/) :
    py -m scripts.affecter_sexe
    py -m scripts.affecter_sexe --tous        # inclut les INACTIF
"""

import sys
import os
import argparse

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.query_executor import QueryExecutor
from domain.repositories.personnel_repo import PersonnelRepository
from infrastructure.logging.optimized_db_logger import log_hist


# Valeurs acceptees en saisie -> valeur stockee en DB
_SAISIES_VALIDES = {
    'h': 'M', 'm': 'M',
    'f': 'F',
    'x': 'X',
}

_LIBELLES = {'M': 'Homme', 'F': 'Femme', 'X': 'Autre'}


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def _afficher_resume(traites: int, ignores: int, total: int) -> None:
    print(f"\n{'='*60}")
    print(f"  Termine : {traites} valeur(s) enregistree(s), {ignores} passe(s) sur {total}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Requete
# ---------------------------------------------------------------------------

def _fetch_sans_sexe(inclure_inactifs: bool):
    """Personnel sans sexe renseigne (NULL ou NSP) dans personnel_infos."""
    filtre_statut = "" if inclure_inactifs else "AND p.statut = 'ACTIF'"
    return QueryExecutor.fetch_all(
        f"""
        SELECT p.id, p.nom, p.prenom, p.matricule, p.statut
        FROM personnel p
        LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
        WHERE (pi.sexe IS NULL OR pi.sexe = 'NSP' OR pi.personnel_id IS NULL)
        {filtre_statut}
        ORDER BY p.nom, p.prenom
        """,
        dictionary=True,
    )


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Affectation du sexe H/F")
    parser.add_argument(
        "--tous",
        action="store_true",
        help="Inclure les personnels INACTIF (par defaut : ACTIF seulement)",
    )
    args = parser.parse_args()

    personnel = _fetch_sans_sexe(inclure_inactifs=args.tous)

    if not personnel:
        scope = "tous statuts" if args.tous else "ACTIF"
        print(f"Tous les employes ({scope}) ont deja un sexe renseigne. Rien a faire.")
        return

    total = len(personnel)
    scope = "tous statuts" if args.tous else "ACTIF uniquement"
    print(f"\n{total} employe(s) sans sexe renseigne ({scope}).")
    print("Saisir : H ou M = Homme  |  F = Femme  |  X = Autre")
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
                saisie = input("  Sexe (H/F/X) : ").strip()
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

            valeur_db = _SAISIES_VALIDES.get(saisie.lower())
            if valeur_db is None:
                print("  Valeur invalide. Saisir H, M, F ou X.")
                continue

            libelle = _LIBELLES[valeur_db]
            confirm = input(
                f"  Confirmer '{libelle}' pour {nom} {prenom} ? (o/n) : "
            ).strip().lower()
            if confirm != 'o':
                print("  Annule, ressaisissez.")
                continue

            PersonnelRepository.upsert_infos(pid, {"sexe": valeur_db})
            log_hist(
                "AFFECTATION_SEXE",
                f"Sexe affecte via script batch : {valeur_db} ({libelle})",
                pid,
                None,
            )
            print(f"  -> Enregistre : {valeur_db} ({libelle})")
            traites += 1
            break

    _afficher_resume(traites, ignores, total)


if __name__ == "__main__":
    main()
