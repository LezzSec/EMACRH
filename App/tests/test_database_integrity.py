# -*- coding: utf-8 -*-
"""
Vérification de l'intégrité de la base de données après les modifications
"""

from core.db.configbd import get_connection

def check_matricule_distribution():
    """Vérifier la répartition des matricules"""
    print("\n=== RÉPARTITION DES MATRICULES ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Compter personnel avec matricule
        cur.execute("SELECT COUNT(*) FROM personnel WHERE matricule IS NOT NULL AND matricule != ''")
        with_mat = cur.fetchone()[0]

        # Compter personnel sans matricule
        cur.execute("SELECT COUNT(*) FROM personnel WHERE matricule IS NULL OR matricule = ''")
        without_mat = cur.fetchone()[0]

        # Total
        total = with_mat + without_mat

        print(f"Personnel AVEC matricule: {with_mat}")
        print(f"Personnel SANS matricule: {without_mat}")
        print(f"Total: {total}")

        # Vérifier les matricules actifs visibles dans les grilles
        cur.execute("""
            SELECT COUNT(*) FROM personnel
            WHERE statut = 'ACTIF'
            AND matricule IS NOT NULL
            AND matricule != ''
        """)
        visible = cur.fetchone()[0]

        print(f"\nPersonnel VISIBLE dans les grilles (ACTIF + matricule): {visible}")

        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

def check_matricule_format():
    """Vérifier le format des matricules"""
    print("\n=== FORMAT DES MATRICULES ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Vérifier tous les matricules
        cur.execute("SELECT matricule FROM personnel WHERE matricule IS NOT NULL AND matricule != ''")
        matricules = cur.fetchall()

        invalid = []
        for (mat,) in matricules:
            if not mat.startswith('M') or len(mat) != 7:
                invalid.append(mat)

        if invalid:
            print(f"[ATTENTION] {len(invalid)} matricules avec format invalide:")
            for mat in invalid[:10]:
                print(f"  - {mat}")
        else:
            print(f"[OK] Tous les {len(matricules)} matricules ont le bon format (M000XXX)")

        # Afficher le dernier matricule
        cur.execute("""
            SELECT MAX(CAST(SUBSTRING(matricule, 2) AS UNSIGNED)) as dernier
            FROM personnel
            WHERE matricule LIKE 'M%'
        """)
        dernier = cur.fetchone()[0]
        print(f"[INFO] Dernier numéro de matricule: M{dernier:06d}")

        return len(invalid) == 0

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

def check_polyvalence_integrity():
    """Vérifier l'intégrité des polyvalences"""
    print("\n=== INTÉGRITÉ DES POLYVALENCES ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Vérifier les polyvalences orphelines (opérateur n'existe pas)
        cur.execute("""
            SELECT COUNT(*) FROM polyvalence p
            LEFT JOIN personnel o ON p.operateur_id = o.id
            WHERE o.id IS NULL
        """)
        orphan_operateurs = cur.fetchone()[0]

        # Vérifier les polyvalences orphelines (poste n'existe pas)
        cur.execute("""
            SELECT COUNT(*) FROM polyvalence p
            LEFT JOIN postes pos ON p.poste_id = pos.id
            WHERE pos.id IS NULL
        """)
        orphan_postes = cur.fetchone()[0]

        if orphan_operateurs > 0:
            print(f"[ATTENTION] {orphan_operateurs} polyvalences avec opérateurs inexistants")
        else:
            print(f"[OK] Aucune polyvalence avec opérateur inexistant")

        if orphan_postes > 0:
            print(f"[ATTENTION] {orphan_postes} polyvalences avec postes inexistants")
        else:
            print(f"[OK] Aucune polyvalence avec poste inexistant")

        # Statistiques des polyvalences
        cur.execute("SELECT COUNT(*) FROM polyvalence")
        total_poly = cur.fetchone()[0]
        print(f"[INFO] Total polyvalences: {total_poly}")

        return orphan_operateurs == 0 and orphan_postes == 0

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

def check_test_data():
    """Vérifier les données de test créées"""
    print("\n=== DONNÉES DE TEST ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Personnel de test
        test_names = [
            ('TestMatricule', 'Personnel'),
            ('TestNonProd', 'Personnel'),
            ('Lahirigoyen', 'Thomas')
        ]

        for nom, prenom in test_names:
            cur.execute(
                "SELECT id, matricule, statut FROM personnel WHERE nom = %s AND prenom = %s",
                (nom, prenom)
            )
            result = cur.fetchone()

            if result:
                print(f"[INFO] {prenom} {nom}: id={result[0]}, matricule={result[1]}, statut={result[2]}")
            else:
                print(f"[INFO] {prenom} {nom}: non trouvé")

        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("VÉRIFICATION INTÉGRITÉ BASE DE DONNÉES")
    print("=" * 60)

    test1 = check_matricule_distribution()
    test2 = check_matricule_format()
    test3 = check_polyvalence_integrity()
    test4 = check_test_data()

    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"Répartition matricules: {'OK' if test1 else 'ERREUR'}")
    print(f"Format matricules: {'OK' if test2 else 'ERREUR'}")
    print(f"Intégrité polyvalences: {'OK' if test3 else 'ERREUR'}")
    print(f"Données de test: {'OK' if test4 else 'ERREUR'}")

    if test1 and test2 and test3 and test4:
        print("\n[OK] Base de données intègre!")
    else:
        print("\n[ATTENTION] Problèmes détectés")
