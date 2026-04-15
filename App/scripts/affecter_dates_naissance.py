# -*- coding: utf-8 -*-
"""
Script d'affectation en chaine des dates de naissance pour le personnel ACTIF
sans date de naissance dans personnel_infos.

Affiche chaque employe et demande une date. Entree vide = passer au suivant.
'q' ou Ctrl+C = arreter.

Usage (depuis le dossier App/) :
    py -m scripts.affecter_dates_naissance
    py -m scripts.affecter_dates_naissance --tous        # inclut les INACTIF
"""

import sys
import os
import argparse
from datetime import datetime, date

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.query_executor import QueryExecutor
from domain.repositories.personnel_repo import PersonnelRepository
from infrastructure.logging.optimized_db_logger import log_hist


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def parse_date(saisie: str):
    """Accepte dd/mm/yyyy, dd-mm-yyyy ou yyyy-mm-dd. Retourne str yyyy-mm-dd ou None."""
    saisie = saisie.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(saisie, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _age(date_sql: str) -> str:
    """Calcule l'age a partir d'une date ISO et retourne une chaine lisible."""
    try:
        naissance = datetime.strptime(date_sql, "%Y-%m-%d").date()
        aujourd_hui = date.today()
        ans = (
            aujourd_hui.year - naissance.year
            - ((aujourd_hui.month, aujourd_hui.day) < (naissance.month, naissance.day))
        )
        return f"{ans} ans"
    except Exception:
        return ""


def _afficher_resume(traites: int, ignores: int, total: int) -> None:
    print(f"\n{'='*60}")
    print(f"  Termine : {traites} date(s) enregistree(s), {ignores} passe(s) sur {total}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Requete
# ---------------------------------------------------------------------------

def _fetch_sans_date_naissance(inclure_inactifs: bool):
    """Personnel sans date de naissance dans personnel_infos."""
    filtre_statut = "" if inclure_inactifs else "AND p.statut = 'ACTIF'"
    return QueryExecutor.fetch_all(
        f"""
        SELECT p.id, p.nom, p.prenom, p.matricule, p.statut
        FROM personnel p
        LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
        WHERE (pi.date_naissance IS NULL OR pi.personnel_id IS NULL)
        {filtre_statut}
        ORDER BY p.nom, p.prenom
        """,
        dictionary=True,
    )


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Affectation des dates de naissance")
    parser.add_argument(
        "--tous",
        action="store_true",
        help="Inclure les personnels INACTIF (par defaut : ACTIF seulement)",
    )
    args = parser.parse_args()

    personnel = _fetch_sans_date_naissance(inclure_inactifs=args.tous)

    if not personnel:
        scope = "tous statuts" if args.tous else "ACTIF"
        print(f"Tous les employes ({scope}) ont deja une date de naissance. Rien a faire.")
        return

    total = len(personnel)
    scope = "tous statuts" if args.tous else "ACTIF uniquement"
    print(f"\n{total} employe(s) sans date de naissance ({scope}).")
    print("Format date attendu : JJ/MM/AAAA  (ex: 14/07/1985)")
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
                saisie = input("  Date de naissance : ").strip()
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

            date_sql = parse_date(saisie)
            if not date_sql:
                print("  Format invalide. Utilisez JJ/MM/AAAA.")
                continue

            # Coherence : date dans le passe, age raisonnable (16-80 ans)
            naissance = datetime.strptime(date_sql, "%Y-%m-%d").date()
            today = date.today()
            if naissance >= today:
                print("  La date de naissance doit etre dans le passe.")
                continue
            age_ans = (
                today.year - naissance.year
                - ((today.month, today.day) < (naissance.month, naissance.day))
            )
            if not (16 <= age_ans <= 80):
                confirm_age = input(
                    f"  Age calcule : {age_ans} ans — confirmer quand meme ? (o/n) : "
                ).strip().lower()
                if confirm_age != 'o':
                    print("  Annule, ressaisissez.")
                    continue

            # Confirmation
            date_display = naissance.strftime("%d/%m/%Y")
            confirm = input(
                f"  Confirmer {date_display} ({_age(date_sql)}) pour {nom} {prenom} ? (o/n) : "
            ).strip().lower()
            if confirm != 'o':
                print("  Annule, ressaisissez.")
                continue

            PersonnelRepository.upsert_infos(pid, {"date_naissance": date_sql})
            log_hist(
                "AFFECTATION_DATE_NAISSANCE",
                f"Date de naissance affectee via script batch : {date_display}",
                pid,
                None,
            )
            print(f"  -> Enregistre : {date_display}  ({_age(date_sql)})")
            traites += 1
            break

    _afficher_resume(traites, ignores, total)


if __name__ == "__main__":
    main()
