# -*- coding: utf-8 -*-
"""
Script d'affectation en chaine des dates d'entree pour le personnel ACTIF
sans date d'entree dans personnel_infos.

Affiche chaque employe et demande une date. Entree vide = passer au suivant.
'q' ou Ctrl+C = arreter.

Usage (depuis le dossier App/) :
    py -m scripts.affecter_dates_entree
"""

import sys
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.query_executor import QueryExecutor
from domain.repositories.personnel_repo import PersonnelRepository
from infrastructure.logging.optimized_db_logger import log_hist


def parse_date(saisie: str):
    """Accepte dd/mm/yyyy ou dd-mm-yyyy ou yyyy-mm-dd. Retourne une str yyyy-mm-dd ou None."""
    saisie = saisie.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(saisie, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def main():
    personnel = QueryExecutor.fetch_all(
        """
        SELECT p.id, p.nom, p.prenom, p.matricule, pi.date_entree
        FROM personnel p
        LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
        WHERE p.statut = 'ACTIF'
        ORDER BY p.nom, p.prenom
        """,
        dictionary=True,
    )

    if not personnel:
        print("Aucun employe ACTIF trouve.")
        return

    total = len(personnel)
    print(f"\n{total} employe(s) ACTIF.")
    print("Format date attendu : JJ/MM/AAAA  (ex: 15/03/2019)")
    print("Entree vide = passer | q = quitter\n")
    print(f"{'#':<5} {'Matricule':<12} {'Nom':<20} {'Prenom':<20}")
    print("-" * 60)

    traites = ignores = 0

    for i, emp in enumerate(personnel, 1):
        pid       = emp['id']
        matricule = emp['matricule'] or '-'
        nom       = emp['nom']
        prenom    = emp['prenom']

        date_actuelle = emp.get('date_entree')
        date_actuelle_str = date_actuelle.strftime("%d/%m/%Y") if date_actuelle else "aucune"
        print(f"\n[{i}/{total}]  {matricule}  {nom.upper()} {prenom}  (actuelle : {date_actuelle_str})")

        while True:
            try:
                saisie = input("  Date d'entree : ").strip()
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

            # Confirmation rapide
            date_display = datetime.strptime(date_sql, "%Y-%m-%d").strftime("%d/%m/%Y")
            confirm = input(f"  Confirmer {date_display} pour {nom} {prenom} ? (o/n) : ").strip().lower()
            if confirm != 'o':
                print("  Annule, ressaisissez.")
                continue

            PersonnelRepository.save_date_entree(pid, date_sql)
            log_hist(
                "AFFECTATION_DATE_ENTREE",
                f"Date d'entree affectee via script batch : {date_display}",
                pid,
                None,
            )
            print(f"  -> Enregistre : {date_display}")
            traites += 1
            break

    _afficher_resume(traites, ignores, total)


def _afficher_resume(traites, ignores, total):
    print(f"\n{'='*60}")
    print(f"  Termine : {traites} date(s) enregistree(s), {ignores} passe(s) sur {total}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
