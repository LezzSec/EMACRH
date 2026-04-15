# -*- coding: utf-8 -*-
"""
Script de création d'un personnel de test dans la BDD.
Insère un employé "TEST / Utilisateur" avec un matricule auto-généré
et des données minimales pour pouvoir tester toutes les fonctionnalités.

Usage (depuis le dossier App/) :
    py -m scripts.create_test_personnel
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.query_executor import QueryExecutor
from domain.services.personnel.matricule_service import generer_prochain_matricule


NOM    = "TEST"
PRENOM = "Utilisateur"
STATUT = "ACTIF"


def main():
    # Vérifier si déjà existant
    existing = QueryExecutor.fetch_one(
        "SELECT id, matricule FROM personnel WHERE nom = %s AND prenom = %s",
        (NOM, PRENOM), dictionary=True
    )

    if existing:
        pid = existing['id']
        mat = existing['matricule']
        print(f"Le personnel '{PRENOM} {NOM}' existe deja (id={pid}, matricule={mat}).")
        print("Rien a faire.")
        _afficher_recap(pid, mat)
        return

    # Générer un matricule
    matricule = generer_prochain_matricule()

    # Insérer dans personnel
    pid = QueryExecutor.execute_write(
        "INSERT INTO personnel (nom, prenom, statut, matricule) VALUES (%s, %s, %s, %s)",
        (NOM, PRENOM, STATUT, matricule)
    )
    print(f"Personnel insere : id={pid}, matricule={matricule}")

    # Insérer dans personnel_infos (données minimales)
    # Déterminer le nom de la colonne FK (operateur_id ou personnel_id selon migration appliquée)
    cols = QueryExecutor.fetch_all("SHOW COLUMNS FROM personnel_infos", dictionary=True)
    col_names = [c['Field'] for c in cols]
    fk_col = 'personnel_id' if 'personnel_id' in col_names else 'operateur_id'
    QueryExecutor.execute_write(
        f"INSERT INTO personnel_infos ({fk_col}, date_entree) VALUES (%s, %s)",
        (pid, date.today())
    )
    print("Fiche personnel_infos creee.")

    _afficher_recap(pid, matricule)


def _afficher_recap(pid, matricule):
    print()
    print("=== Personnel de test cree ===")
    print(f"  Nom      : {NOM}")
    print(f"  Prenom   : {PRENOM}")
    print(f"  Statut   : {STATUT}")
    print(f"  Matricule: {matricule}")
    print(f"  ID BDD   : {pid}")
    print()
    print("Pour le supprimer apres les tests :")
    print(f"  DELETE FROM personnel WHERE id = {pid};")
    print("==============================")


if __name__ == "__main__":
    main()
