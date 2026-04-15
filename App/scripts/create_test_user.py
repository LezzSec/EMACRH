# -*- coding: utf-8 -*-
"""
Script de création d'un utilisateur de test dans la BDD.
Utilise le service auth pour générer le hash bcrypt correctement.

Usage (depuis le dossier App/) :
    py -m scripts.create_test_user
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.query_executor import QueryExecutor
from domain.services.admin.auth_service import create_user, hash_password

USERNAME  = "test"
PASSWORD  = "Test1234!"
NOM       = "Utilisateur"
PRENOM    = "Test"
ROLE_NOM  = "admin"  # admin | gestion_production | gestion_rh


def main():
    # Récupérer le role_id
    role = QueryExecutor.fetch_one(
        "SELECT id, nom FROM roles WHERE nom = %s",
        (ROLE_NOM,), dictionary=True
    )
    if not role:
        roles = QueryExecutor.fetch_all("SELECT id, nom FROM roles", dictionary=True)
        print(f"Role '{ROLE_NOM}' introuvable. Roles disponibles :")
        for r in roles:
            print(f"  - {r['nom']} (id={r['id']})")
        sys.exit(1)

    role_id = role['id']

    # Vérifier si l'utilisateur existe déjà
    existing = QueryExecutor.fetch_one(
        "SELECT id FROM utilisateurs WHERE username = %s",
        (USERNAME,), dictionary=True
    )
    pw_hash = hash_password(PASSWORD)

    if existing:
        print(f"L'utilisateur '{USERNAME}' existe deja (id={existing['id']}).")
        print("Mise a jour du mot de passe...")
        QueryExecutor.execute_write(
            "UPDATE utilisateurs SET password_hash = %s, role_id = %s, actif = 1 WHERE username = %s",
            (pw_hash, role_id, USERNAME),
            return_lastrowid=False
        )
        print("Mot de passe reinitialise.")
    else:
        QueryExecutor.execute_write(
            "INSERT INTO utilisateurs (username, password_hash, nom, prenom, role_id, actif) VALUES (%s, %s, %s, %s, %s, 1)",
            (USERNAME, pw_hash, NOM, PRENOM, role_id)
        )
        print("Utilisateur cree avec succes.")

    print()
    print("=== Identifiants de connexion ===")
    print(f"  Utilisateur : {USERNAME}")
    print(f"  Mot de passe : {PASSWORD}")
    print(f"  Role         : {ROLE_NOM}")
    print("=================================")


if __name__ == "__main__":
    main()
