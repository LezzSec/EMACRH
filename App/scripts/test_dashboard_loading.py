# -*- coding: utf-8 -*-
"""Test du chargement des données du dashboard"""

import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(app_dir))

print("="*60)
print("TEST CHARGEMENT DASHBOARD")
print("="*60)

# Simuler la fonction _fetch_evaluations de main_qt.py
def test_fetch_evaluations():
    from core.db.configbd import DatabaseCursor

    print("\n[TEST] Simulation _fetch_evaluations...")

    with DatabaseCursor() as cur:
        # Requête en retard
        query_retard = """
            SELECT p.nom, p.prenom, pos.poste_code, poly.prochaine_evaluation
            FROM polyvalence poly
            INNER JOIN personnel p ON p.id = poly.operateur_id
            LEFT JOIN postes pos ON pos.id = poly.poste_id
            WHERE poly.prochaine_evaluation < CURDATE()
              AND p.statut = 'ACTIF'
            ORDER BY poly.prochaine_evaluation ASC
            LIMIT 10
        """
        cur.execute(query_retard)
        retard = cur.fetchall()

        # Requête prochaines
        query_next = """
            SELECT p.nom, p.prenom, pos.poste_code, poly.prochaine_evaluation
            FROM polyvalence poly
            INNER JOIN personnel p ON p.id = poly.operateur_id
            LEFT JOIN postes pos ON pos.id = poly.poste_id
            WHERE poly.prochaine_evaluation >= CURDATE()
              AND p.statut = 'ACTIF'
            ORDER BY poly.prochaine_evaluation ASC
            LIMIT 10
        """
        cur.execute(query_next)
        prochaines = cur.fetchall()

        return {"retard": retard, "prochaines": prochaines}

# Test de chargement
try:
    result = test_fetch_evaluations()

    retard = result["retard"]
    prochaines = result["prochaines"]

    print(f"\n[OK] Evaluations en retard : {len(retard)}")
    if retard:
        print(f"     Type premier element: {type(retard[0])}")
        print(f"     Exemple: {retard[0]}")

    print(f"\n[OK] Prochaines evaluations : {len(prochaines)}")
    if prochaines:
        print(f"     Type premier element: {type(prochaines[0])}")
        print(f"     Exemple: {prochaines[0]}")

    # Simuler l'affichage
    print("\n[SIMULATION] Affichage dans l'UI:")
    print("-" * 60)

    for nom, prenom, poste, date_ev in retard[:3]:
        if hasattr(date_ev, 'strftime'):
            date_txt = date_ev.strftime('%d/%m/%Y')
        else:
            date_txt = str(date_ev)
        print(f"  [RETARD] {nom} {prenom} · {poste or ''}  —  Retard: {date_txt}")

    for nom, prenom, poste, date_ev in prochaines[:3]:
        if hasattr(date_ev, 'strftime'):
            date_txt = date_ev.strftime('%d/%m/%Y')
        else:
            date_txt = str(date_ev)
        print(f"  [PREVU]  {nom} {prenom} · {poste or ''}  —  Prevu: {date_txt}")

    print("\n[SUCCESS] Le chargement du dashboard fonctionne correctement!")

except Exception as e:
    print(f"\n[ERREUR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
