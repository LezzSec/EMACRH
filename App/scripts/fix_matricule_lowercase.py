# -*- coding: utf-8 -*-
"""
Script pour corriger les matricules en minuscule
"""

from core.db.configbd import get_connection

conn = get_connection()
cur = conn.cursor()

try:
    # Trouver les matricules en minuscule ou avec format invalide
    cur.execute("""
        SELECT id, nom, prenom, matricule
        FROM personnel
        WHERE matricule IS NOT NULL
        AND (
            matricule != UPPER(matricule)
            OR matricule NOT REGEXP '^M[0-9]{6}$'
        )
    """)

    results = cur.fetchall()

    if results:
        print(f"Trouve {len(results)} matricule(s) a corriger:")
        for row in results:
            id_pers, nom, prenom, matricule = row
            print(f"  - ID={id_pers}, {nom} {prenom}, matricule='{matricule}'")

            # Tenter de corriger en majuscules si c'est juste une question de casse
            matricule_upper = matricule.upper()
            if matricule_upper[0] == 'M' and len(matricule_upper) == 7:
                cur.execute(
                    "UPDATE personnel SET matricule = %s WHERE id = %s",
                    (matricule_upper, id_pers)
                )
                print(f"    -> Corrige en: {matricule_upper}")
            else:
                print(f"    -> Format invalide, suppression recommandee")

        conn.commit()
        print("\n[OK] Corrections appliquees!")
    else:
        print("[OK] Aucun matricule a corriger")

except Exception as e:
    print(f"[ERREUR] {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
