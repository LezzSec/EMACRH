# -*- coding: utf-8 -*-
"""
Script d'affectation en chaîne des catégories pour le personnel ACTIF.

Affiche chaque employé et demande la catégorie.
Entrée vide = passer au suivant.
'q' ou Ctrl+C = arrêter.

Usage (depuis le dossier App/) :
    py -m scripts.affecter_categories
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.optimized_db_logger import log_hist

CATEGORIES = {
    'O': 'Ouvrier',
    'E': 'Employé',
    'T': 'Technicien',
    'C': 'Cadre',
}


def main():
    personnel = QueryExecutor.fetch_all(
        """
        SELECT p.id, p.nom, p.prenom, p.matricule, pi.categorie
        FROM personnel p
        LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
        WHERE p.statut = 'ACTIF'
        ORDER BY p.nom, p.prenom
        """,
        dictionary=True,
    )

    if not personnel:
        print("Aucun employé ACTIF trouvé.")
        return

    total = len(personnel)
    cats = "  ".join(f"{k}={v}" for k, v in CATEGORIES.items())
    print(f"\n{total} employé(s) ACTIF.")
    print(f"Catégories : {cats}")
    print("Entrée vide = passer | q = quitter\n")

    traites = ignores = 0

    for i, emp in enumerate(personnel, 1):
        pid       = emp['id']
        matricule = emp['matricule'] or '-'
        nom       = emp['nom']
        prenom    = emp['prenom']
        cat_actuelle = emp.get('categorie') or '-'
        cat_label = CATEGORIES.get(cat_actuelle, '-')

        print(f"\n[{i}/{total}]  {matricule}  {nom.upper()} {prenom}  (actuelle : {cat_actuelle} - {cat_label})")

        while True:
            try:
                saisie = input(f"  Catégorie (O/E/T/C) : ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\nArrêt demandé.")
                _afficher_resume(traites, ignores, total)
                return

            if saisie.lower() == 'q':
                _afficher_resume(traites, ignores, total)
                return

            if saisie == '':
                print("  -> Passé.")
                ignores += 1
                break

            if saisie not in CATEGORIES:
                print(f"  Valeur invalide. Saisissez : {'/'.join(CATEGORIES)}")
                continue

            QueryExecutor.execute_write(
                """
                INSERT INTO personnel_infos (personnel_id, categorie)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE categorie = VALUES(categorie)
                """,
                (pid, saisie)
            )
            log_hist(
                "AFFECTATION_CATEGORIE",
                f"Catégorie affectée via script : {saisie} - {CATEGORIES[saisie]}",
                pid,
                None,
            )
            print(f"  -> Enregistré : {saisie} - {CATEGORIES[saisie]}")
            traites += 1
            break

    _afficher_resume(traites, ignores, total)


def _afficher_resume(traites, ignores, total):
    print(f"\n{'='*60}")
    print(f"  Terminé : {traites} catégorie(s) enregistrée(s), {ignores} passé(s) sur {total}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
