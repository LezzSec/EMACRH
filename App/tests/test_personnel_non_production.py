# -*- coding: utf-8 -*-
"""
Test d'ajout de personnel non-production (sans matricule)
"""

from core.db.configbd import get_connection

def test_add_personnel_non_production():
    """Test d'ajout d'un personnel non-production sans matricule"""
    print("\n=== TEST: Ajout personnel non-production ===")

    nom = "TestNonProd"
    prenom = "Personnel"

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Vérifier si existe déjà
        cur.execute("SELECT id, matricule FROM personnel WHERE nom = %s AND prenom = %s", (nom, prenom))
        existing = cur.fetchone()

        if existing:
            print(f"[INFO] Personnel existe déjà: id={existing[0]}, matricule={existing[1]}")
            # Supprimer pour le test
            cur.execute("DELETE FROM personnel WHERE id = %s", (existing[0],))
            conn.commit()
            print(f"[INFO] Personnel supprimé pour le test")

        # Insérer personnel SANS matricule
        cur.execute(
            "INSERT INTO personnel (nom, prenom, statut) VALUES (%s, %s, 'ACTIF')",
            (nom, prenom)
        )
        conn.commit()
        personnel_id = cur.lastrowid
        print(f"[OK] Personnel non-production créé: id={personnel_id}")

        # Vérifier l'insertion
        cur.execute("SELECT id, nom, prenom, matricule, statut FROM personnel WHERE id = %s", (personnel_id,))
        result = cur.fetchone()

        if result:
            print(f"[OK] Vérification: id={result[0]}, {result[1]} {result[2]}, matricule={result[3]}, statut={result[4]}")

            if result[3] is None or result[3] == '':
                print(f"[OK] Le personnel n'a PAS de matricule (correct pour non-production)")
            else:
                print(f"[ERREUR] Le personnel a un matricule alors qu'il ne devrait pas: {result[3]}")
                return False

            # Vérifier qu'il N'apparaît PAS dans la requête liste_et_grilles
            cur.execute("""
                SELECT id FROM personnel
                WHERE statut = 'ACTIF'
                AND matricule IS NOT NULL
                AND matricule != ''
                AND id = %s
            """, (personnel_id,))

            in_list = cur.fetchone()

            if in_list is None:
                print(f"[OK] Le personnel N'apparaît PAS dans les listes et grilles (correct)")
            else:
                print(f"[ERREUR] Le personnel apparaît dans les listes et grilles alors qu'il ne devrait pas")
                return False

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

if __name__ == "__main__":
    print("=" * 60)
    print("TEST PERSONNEL NON-PRODUCTION")
    print("=" * 60)

    result = test_add_personnel_non_production()

    print("\n" + "=" * 60)
    if result:
        print("[OK] Test réussi!")
    else:
        print("[ERREUR] Test échoué")
