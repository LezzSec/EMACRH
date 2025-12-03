# -*- coding: utf-8 -*-
"""
Test de la fonctionnalité de masquage d'opérateurs
"""

from core.db.configbd import get_connection

def test_masquage_operateur():
    """Test du masquage d'un opérateur (passage à INACTIF)"""
    print("\n=== TEST: Masquage opérateur ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Trouver un opérateur de test avec matricule
        cur.execute("""
            SELECT id, nom, prenom, matricule, statut
            FROM personnel
            WHERE matricule LIKE 'M%'
            AND statut = 'ACTIF'
            ORDER BY id DESC
            LIMIT 1
        """)

        operateur = cur.fetchone()

        if not operateur:
            print("[INFO] Aucun opérateur actif avec matricule trouvé")
            return False

        op_id, nom, prenom, matricule, statut = operateur
        print(f"[INFO] Opérateur sélectionné: id={op_id}, {nom} {prenom}, matricule={matricule}, statut={statut}")

        # Simuler le masquage (changer statut à INACTIF)
        cur.execute("UPDATE personnel SET statut = 'INACTIF' WHERE id = %s", (op_id,))
        conn.commit()
        print(f"[OK] Opérateur masqué (statut changé à INACTIF)")

        # Vérifier le changement
        cur.execute("SELECT statut FROM personnel WHERE id = %s", (op_id,))
        new_statut = cur.fetchone()[0]

        if new_statut == 'INACTIF':
            print(f"[OK] Statut vérifié: {new_statut}")
        else:
            print(f"[ERREUR] Statut incorrect: {new_statut}")
            return False

        # Vérifier qu'il N'apparaît PLUS dans liste_et_grilles
        cur.execute("""
            SELECT id FROM personnel
            WHERE statut = 'ACTIF'
            AND matricule IS NOT NULL
            AND matricule != ''
            AND id = %s
        """, (op_id,))

        in_list = cur.fetchone()

        if in_list is None:
            print(f"[OK] L'opérateur N'apparaît PLUS dans les listes et grilles")
        else:
            print(f"[ERREUR] L'opérateur apparaît encore dans les listes et grilles")
            return False

        # Remettre l'opérateur actif pour ne pas modifier la base
        cur.execute("UPDATE personnel SET statut = 'ACTIF' WHERE id = %s", (op_id,))
        conn.commit()
        print(f"[INFO] Opérateur remis à ACTIF (restauration)")

        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def test_liste_operateurs_masquables():
    """Test de la récupération de la liste des opérateurs masquables"""
    print("\n=== TEST: Liste opérateurs masquables ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Requête identique à celle de liste_et_grilles.py remove_data()
        cur.execute("""
            SELECT id, nom, prenom, matricule
            FROM personnel
            WHERE statut = 'ACTIF'
            AND matricule IS NOT NULL
            AND matricule != ''
            ORDER BY nom, prenom
        """)

        operateurs = cur.fetchall()
        print(f"[OK] Nombre d'opérateurs masquables: {len(operateurs)}")

        if operateurs:
            print("[INFO] Premiers opérateurs masquables:")
            for i, op in enumerate(operateurs[:5]):
                print(f"  {i+1}. ID={op[0]}, {op[1]} {op[2]} ({op[3]})")

        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("TEST MASQUAGE OPÉRATEURS")
    print("=" * 60)

    test1 = test_liste_operateurs_masquables()
    test2 = test_masquage_operateur()

    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"Liste opérateurs masquables: {'PASS' if test1 else 'FAIL'}")
    print(f"Masquage opérateur: {'PASS' if test2 else 'FAIL'}")

    if test1 and test2:
        print("\n[OK] Tous les tests sont passés!")
    else:
        print("\n[ERREUR] Certains tests ont échoué")
