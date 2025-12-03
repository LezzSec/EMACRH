# -*- coding: utf-8 -*-
"""
Test du service de génération de matricule
"""

from core.services.matricule_service import generer_prochain_matricule, matricule_existe
from core.db.configbd import get_connection

def test_generer_matricule():
    """Test de génération de matricule"""
    print("\n=== TEST: Génération de matricule ===")

    try:
        # Générer un matricule
        matricule = generer_prochain_matricule()
        print(f"[OK] Matricule généré: {matricule}")

        # Vérifier le format
        if matricule.startswith('M') and len(matricule) == 7:
            print(f"[OK] Format correct: {matricule}")
        else:
            print(f"[ERREUR] Format incorrect: {matricule}")
            return False

        # Vérifier s'il existe dans la base
        existe = matricule_existe(matricule)
        if not existe:
            print(f"[OK] Le matricule {matricule} n'existe pas encore dans la base")
        else:
            print(f"[INFO] Le matricule {matricule} existe déjà")

        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

def test_insertion_avec_matricule():
    """Test d'insertion d'un personnel avec matricule"""
    print("\n=== TEST: Insertion personnel avec matricule ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Générer un matricule
        matricule = generer_prochain_matricule()
        print(f"[INFO] Matricule à insérer: {matricule}")

        # Insérer un personnel de test
        nom = "TestMatricule"
        prenom = "Personnel"

        # Vérifier si existe déjà
        cur.execute("SELECT id FROM personnel WHERE nom = %s AND prenom = %s", (nom, prenom))
        existing = cur.fetchone()

        if existing:
            print(f"[INFO] Personnel de test existe déjà (id={existing[0]})")
            # Mettre à jour le matricule
            cur.execute("UPDATE personnel SET matricule = %s WHERE id = %s", (matricule, existing[0]))
            conn.commit()
            print(f"[OK] Matricule mis à jour: {matricule}")
        else:
            # Insérer nouveau personnel
            cur.execute(
                "INSERT INTO personnel (nom, prenom, statut, matricule) VALUES (%s, %s, 'ACTIF', %s)",
                (nom, prenom, matricule)
            )
            conn.commit()
            personnel_id = cur.lastrowid
            print(f"[OK] Personnel créé avec id={personnel_id}, matricule={matricule}")

        # Vérifier l'insertion
        cur.execute("SELECT id, nom, prenom, matricule FROM personnel WHERE matricule = %s", (matricule,))
        result = cur.fetchone()

        if result:
            print(f"[OK] Vérification réussie: {result}")
            return True
        else:
            print(f"[ERREUR] Personnel non trouvé après insertion")
            return False

    except Exception as e:
        print(f"[ERREUR] {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def test_liste_et_grilles_query():
    """Test de la requête utilisée dans liste_et_grilles"""
    print("\n=== TEST: Requête Liste et Grilles ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Simuler la requête de liste_et_grilles
        cur.execute("""
            SELECT id, nom, prenom, matricule
            FROM personnel
            WHERE statut = 'ACTIF'
            AND matricule IS NOT NULL
            AND matricule != ''
            ORDER BY nom, prenom
        """)

        results = cur.fetchall()
        print(f"[OK] Nombre d'opérateurs avec matricule: {len(results)}")

        if results:
            print("[INFO] Premiers opérateurs:")
            for i, row in enumerate(results[:5]):
                print(f"  {i+1}. ID={row[0]}, {row[1]} {row[2]}, Matricule={row[3]}")

        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("TESTS DU SERVICE MATRICULE")
    print("=" * 60)

    test1 = test_generer_matricule()
    test2 = test_insertion_avec_matricule()
    test3 = test_liste_et_grilles_query()

    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"Génération matricule: {'PASS' if test1 else 'FAIL'}")
    print(f"Insertion avec matricule: {'PASS' if test2 else 'FAIL'}")
    print(f"Requête liste et grilles: {'PASS' if test3 else 'FAIL'}")

    if test1 and test2 and test3:
        print("\n[OK] Tous les tests sont passés!")
    else:
        print("\n[ERREUR] Certains tests ont échoué")
