# -*- coding: utf-8 -*-
"""
Nettoyage de toutes les données de test
"""

from core.db.configbd import get_connection

conn = get_connection()
cur = conn.cursor()

try:
    test_patterns = [
        'TestMatricule%',
        'TestNonProd%',
        'IntegrationTest%',
        'TestConcurrence%',
        'TestRollback%'
    ]

    total_deleted = 0

    # D'abord supprimer les polyvalences liées
    for pattern in test_patterns:
        cur.execute("""
            DELETE FROM polyvalence
            WHERE operateur_id IN (
                SELECT id FROM personnel WHERE nom LIKE %s
            )
        """, (pattern,))
        poly_deleted = cur.rowcount
        if poly_deleted > 0:
            print(f"Polyvalences supprimées pour '{pattern}': {poly_deleted}")

    # Ensuite supprimer le personnel
    for pattern in test_patterns:
        cur.execute("DELETE FROM personnel WHERE nom LIKE %s", (pattern,))
        deleted = cur.rowcount
        if deleted > 0:
            print(f"Personnel supprimé pour '{pattern}': {deleted}")
            total_deleted += deleted

    conn.commit()
    print(f"\n[OK] Total nettoyé: {total_deleted} enregistrement(s) de test")

except Exception as e:
    print(f"[ERREUR] {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
