# -*- coding: utf-8 -*-
"""
Script interactif de nettoyage du personnel.

Affiche tout le personnel avec leur statut et service/poste (numposte),
et permet pour chacun de :
  - Changer le statut (ACTIF / INACTIF)
  - Changer le numposte (service)
  - Passer au suivant sans modifier

Usage :
    cd App
    py -m scripts.nettoyage_personnel
"""

import sys
import os

# Assure que le dossier App est dans le path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.logging_config import setup_logging

setup_logging()

SERVICES = [
    "Production",
    "Administratif",
    "Labo",
    "R&D",
    "Methode",
    "Maintenance",
    "Logistique",
]

# ─────────────────────────────────────────────────────────────
# Helpers affichage
# ─────────────────────────────────────────────────────────────

def _col(text, code):
    """Entoure text d'un code couleur ANSI."""
    return f"\033[{code}m{text}\033[0m"

def green(t):  return _col(t, "92")
def red(t):    return _col(t, "91")
def yellow(t): return _col(t, "93")
def cyan(t):   return _col(t, "96")
def bold(t):   return _col(t, "1")
def dim(t):    return _col(t, "2")


def clear():
    os.system("cls" if os.name == "nt" else "clear")


# ─────────────────────────────────────────────────────────────
# Requêtes
# ─────────────────────────────────────────────────────────────

def charger_personnel():
    return QueryExecutor.fetch_all(
        """
        SELECT
            p.id,
            p.nom,
            p.prenom,
            p.statut,
            pi.numposte,
            pi.sexe,
            pi.categorie
        FROM personnel p
        LEFT JOIN personnel_infos pi ON pi.operateur_id = p.id
        ORDER BY p.nom, p.prenom
        """,
        dictionary=True,
    )


def maj_statut(personnel_id: int, statut: str):
    QueryExecutor.execute_write(
        "UPDATE personnel SET statut = %s WHERE id = %s",
        (statut, personnel_id),
    )


CATEGORIES = [
    ("O", "Ouvrier"),
    ("E", "Employe"),
    ("L", "Leader"),
    ("C", "Cadre"),
]
CAT_MAP = {code: label for code, label in CATEGORIES}


def maj_categorie(personnel_id: int, categorie: str):
    exists = QueryExecutor.exists("personnel_infos", {"operateur_id": personnel_id})
    if exists:
        QueryExecutor.execute_write(
            "UPDATE personnel_infos SET categorie = %s WHERE operateur_id = %s",
            (categorie or None, personnel_id),
        )
    else:
        QueryExecutor.execute_write(
            "INSERT INTO personnel_infos (operateur_id, categorie) VALUES (%s, %s)",
            (personnel_id, categorie or None),
        )


def maj_sexe(personnel_id: int, sexe: str):
    exists = QueryExecutor.exists("personnel_infos", {"operateur_id": personnel_id})
    if exists:
        QueryExecutor.execute_write(
            "UPDATE personnel_infos SET sexe = %s WHERE operateur_id = %s",
            (sexe or None, personnel_id),
        )
    else:
        QueryExecutor.execute_write(
            "INSERT INTO personnel_infos (operateur_id, sexe) VALUES (%s, %s)",
            (personnel_id, sexe or None),
        )


def maj_numposte(personnel_id: int, numposte: str):
    exists = QueryExecutor.exists("personnel_infos", {"operateur_id": personnel_id})
    if exists:
        QueryExecutor.execute_write(
            "UPDATE personnel_infos SET numposte = %s WHERE operateur_id = %s",
            (numposte or None, personnel_id),
        )
    else:
        QueryExecutor.execute_write(
            "INSERT INTO personnel_infos (operateur_id, numposte) VALUES (%s, %s)",
            (personnel_id, numposte or None),
        )


# ─────────────────────────────────────────────────────────────
# Interaction
# ─────────────────────────────────────────────────────────────

def afficher_entete(idx, total, pers):
    clear()
    print(bold(f"\n  === Nettoyage du personnel  [{idx}/{total}] ===\n"))

    statut_fmt = green("ACTIF") if pers["statut"] == "ACTIF" else red("INACTIF")
    numposte_fmt = cyan(pers["numposte"]) if pers["numposte"] else dim("(non renseigné)")
    sexe_map = {"M": "Homme", "F": "Femme"}
    sexe_fmt = cyan(sexe_map.get(pers.get("sexe"), "")) if pers.get("sexe") else dim("(non renseigné)")
    cat_fmt = cyan(CAT_MAP.get(pers.get("categorie"), pers.get("categorie") or "")) if pers.get("categorie") else dim("(non renseigné)")

    print(f"  {bold(pers['nom'])} {bold(pers['prenom'])}  (ID {pers['id']})")
    print(f"  Statut    : {statut_fmt}")
    print(f"  Sexe      : {sexe_fmt}")
    print(f"  Categorie : {cat_fmt}")
    print(f"  Service   : {numposte_fmt}")
    print()


def choisir_statut(pers):
    actuel = pers["statut"]
    inverse = "INACTIF" if actuel == "ACTIF" else "ACTIF"
    print(f"  Nouveau statut — actuellement {green('ACTIF') if actuel == 'ACTIF' else red('INACTIF')}")
    print(f"  [1] Passer à {green(inverse) if inverse == 'ACTIF' else red(inverse)}")
    print(f"  [0] Annuler")
    choix = input("\n  > ").strip()
    if choix == "1":
        maj_statut(pers["id"], inverse)
        pers["statut"] = inverse
        print(green(f"\n  Statut mis à jour : {inverse}"))
        input("  Appuyez sur Entrée pour continuer…")


def choisir_categorie(pers):
    actuel = pers.get("categorie")
    print(f"  Categorie — actuellement : {cyan(CAT_MAP.get(actuel, actuel or '(vide)'))}\n")
    for i, (code, label) in enumerate(CATEGORIES, 1):
        print(f"  [{i}] {label} ({code})")
    print(f"  [v] Vider")
    print(f"  [0] Annuler")

    choix = input("\n  > ").strip().lower()

    if choix == "0":
        return
    elif choix == "v":
        maj_categorie(pers["id"], None)
        pers["categorie"] = None
        print(green("\n  Categorie videe."))
    elif choix.isdigit() and 1 <= int(choix) <= len(CATEGORIES):
        code, label = CATEGORIES[int(choix) - 1]
        maj_categorie(pers["id"], code)
        pers["categorie"] = code
        print(green(f"\n  Categorie mise a jour : {label}"))
    else:
        print(yellow("  Choix invalide, aucune modification."))

    input("  Appuyez sur Entree pour continuer…")


def choisir_sexe(pers):
    actuel = pers.get("sexe")
    sexe_map = {"M": "Homme", "F": "Femme"}
    print(f"  Sexe — actuellement : {cyan(sexe_map.get(actuel, '(vide)'))}\n")
    print(f"  [1] Homme (M)")
    print(f"  [2] Femme (F)")
    print(f"  [v] Vider")
    print(f"  [0] Annuler")

    choix = input("\n  > ").strip().lower()

    if choix == "0":
        return
    elif choix == "1":
        maj_sexe(pers["id"], "M")
        pers["sexe"] = "M"
        print(green("\n  Sexe mis à jour : Homme"))
    elif choix == "2":
        maj_sexe(pers["id"], "F")
        pers["sexe"] = "F"
        print(green("\n  Sexe mis à jour : Femme"))
    elif choix == "v":
        maj_sexe(pers["id"], None)
        pers["sexe"] = None
        print(green("\n  Sexe vidé."))
    else:
        print(yellow("  Choix invalide, aucune modification."))

    input("  Appuyez sur Entrée pour continuer…")


def choisir_numposte(pers):
    print(f"  Nouveau service / poste — actuellement : {cyan(pers['numposte'] or '(vide)')}\n")
    for i, svc in enumerate(SERVICES, 1):
        print(f"  [{i}] {svc}")
    print(f"  [c] Saisie libre")
    print(f"  [v] Vider (supprimer)")
    print(f"  [0] Annuler")

    choix = input("\n  > ").strip().lower()

    if choix == "0":
        return
    elif choix == "v":
        maj_numposte(pers["id"], None)
        pers["numposte"] = None
        print(green("\n  Service vidé."))
    elif choix == "c":
        valeur = input("  Saisir la valeur : ").strip()
        if valeur:
            maj_numposte(pers["id"], valeur)
            pers["numposte"] = valeur
            print(green(f"\n  Service mis à jour : {valeur}"))
    elif choix.isdigit() and 1 <= int(choix) <= len(SERVICES):
        valeur = SERVICES[int(choix) - 1]
        maj_numposte(pers["id"], valeur)
        pers["numposte"] = valeur
        print(green(f"\n  Service mis à jour : {valeur}"))
    else:
        print(yellow("  Choix invalide, aucune modification."))

    input("  Appuyez sur Entrée pour continuer…")


def traiter_personne(idx, total, pers):
    while True:
        afficher_entete(idx, total, pers)
        print("  Que voulez-vous faire ?")
        print("  [1] Changer le statut (ACTIF / INACTIF)")
        print("  [2] Changer le service (numposte)")
        print("  [3] Changer le sexe (H / F)")
        print("  [4] Changer la categorie (Ouvrier / Leader / Employe / Cadre)")
        print("  [n] Personne suivante")
        print("  [p] Personne précédente")
        print("  [q] Quitter")
        print()

        choix = input("  > ").strip().lower()

        if choix == "1":
            choisir_statut(pers)
        elif choix == "2":
            choisir_numposte(pers)
        elif choix == "3":
            choisir_sexe(pers)
        elif choix == "4":
            choisir_categorie(pers)
        elif choix == "n":
            return "next"
        elif choix == "p":
            return "prev"
        elif choix == "q":
            return "quit"
        else:
            print(yellow("  Choix invalide."))
            input("  Appuyez sur Entrée…")


def afficher_resume(personnel, modifies):
    clear()
    print(bold("\n  === Résumé des modifications ===\n"))
    if not modifies:
        print(dim("  Aucune modification effectuée."))
    else:
        for pid, avant, apres in modifies:
            pers = next((p for p in personnel if p["id"] == pid), None)
            nom = f"{pers['nom']} {pers['prenom']}" if pers else f"ID {pid}"
            print(f"  {bold(nom)}")
            for champ, v_avant, v_apres in zip(avant[0], avant[1], apres):
                if v_avant != v_apres:
                    print(f"    {champ}: {red(str(v_avant))} → {green(str(v_apres))}")
    print()


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    clear()
    print(bold("\n  Chargement du personnel…"))
    personnel = charger_personnel()

    if not personnel:
        print(red("  Aucun personnel trouvé en base."))
        return

    total = len(personnel)
    modifies = []  # liste de (id, snapshot_avant, snapshot_apres)

    # Snapshot initial
    snapshots = {
        p["id"]: {"statut": p["statut"], "numposte": p["numposte"], "sexe": p.get("sexe"), "categorie": p.get("categorie")}
        for p in personnel
    }

    idx = 0
    while 0 <= idx < total:
        pers = personnel[idx]
        resultat = traiter_personne(idx + 1, total, pers)

        if resultat == "next":
            idx += 1
        elif resultat == "prev":
            idx = max(0, idx - 1)
        elif resultat == "quit":
            break

    # Calcul des changements
    for p in personnel:
        av = snapshots[p["id"]]
        if any([
            av["statut"] != p["statut"],
            av["numposte"] != p["numposte"],
            av["sexe"] != p.get("sexe"),
            av["categorie"] != p.get("categorie"),
        ]):
            modifies.append((
                p["id"],
                (["statut", "service", "sexe", "categorie"],
                 [av["statut"], av["numposte"], av["sexe"], av["categorie"]]),
                [p["statut"], p["numposte"], p.get("sexe"), p.get("categorie")],
            ))

    afficher_resume(personnel, modifies)
    print(bold(f"  {len(modifies)} personne(s) modifiée(s) sur {total}.\n"))


if __name__ == "__main__":
    main()
