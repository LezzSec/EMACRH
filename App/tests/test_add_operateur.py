# -*- coding: utf-8 -*-
"""
Script de test pour ajouter un opérateur avec matricule
"""

from core.db.configbd import get_connection
from core.services.matricule_service import generer_prochain_matricule

def test_add_operateur_with_matricule():
    """Test d'ajout d'un opérateur avec matricule"""

    nom = "Test"
    prenom = "Utilisateur"

    # Générer un matricule
    matricule = generer_prochain_matricule()
    print(f"Matricule généré : {matricule}")

    # Se connecter à la base
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Vérifier si existe déjà
        cur.execute("SELECT id FROM personnel WHERE nom = %s AND prenom = %s", (nom, prenom))
        existing = cur.fetchone()

        if existing:
            print(f"L'opérateur {prenom} {nom} existe déjà (id={existing[0]})")
            return existing[0]

        # Insérer avec matricule
        print(f"Insertion de {prenom} {nom} avec matricule {matricule}")
        cur.execute(
            "INSERT INTO personnel (nom, prenom, statut, matricule) VALUES (%s, %s, 'ACTIF', %s)",
            (nom, prenom, matricule)
        )

        operateur_id = cur.lastrowid
        conn.commit()

        print(f"✅ Opérateur créé avec succès ! ID = {operateur_id}")

        # Vérifier
        cur.execute("SELECT id, nom, prenom, matricule FROM personnel WHERE id = %s", (operateur_id,))
        result = cur.fetchone()
        print(f"Vérification : {result}")

        return operateur_id

    except Exception as e:
        print(f"❌ Erreur : {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_add_operateur_with_matricule()
