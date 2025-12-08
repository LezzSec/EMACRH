# -*- coding: utf-8 -*-
"""
Script pour corriger les postes orphelins (sans atelier)
Crée un atelier "Non affecté" et y assigne tous les postes orphelins
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.configbd import get_connection
from core.services.logger import log_hist


def fix_postes_orphelins():
    """Corrige les postes sans atelier assigné"""

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Vérifier combien de postes orphelins existent
        cur.execute("""
            SELECT COUNT(*) as count
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            WHERE a.id IS NULL
        """)
        nb_orphelins = cur.fetchone()['count']

        if nb_orphelins == 0:
            print("Aucun poste orphelin trouvé.")
            return

        print(f"Trouvé {nb_orphelins} postes orphelins.")

        # Vérifier si l'atelier "Non affecté" existe
        cur.execute("SELECT id FROM atelier WHERE nom LIKE '%affec%' LIMIT 1")
        atelier_row = cur.fetchone()

        if atelier_row:
            atelier_id = atelier_row['id']
            print(f"Atelier 'Non affecté' existant trouvé (ID: {atelier_id})")
        else:
            # Créer l'atelier
            cur.execute("INSERT INTO atelier (nom) VALUES ('Non affecte - Postes sans atelier')")
            atelier_id = cur.lastrowid
            conn.commit()
            print(f"Atelier 'Non affecté' créé (ID: {atelier_id})")

        # Récupérer les postes orphelins
        cur.execute("""
            SELECT p.id, p.poste_code
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            WHERE a.id IS NULL
        """)
        postes_orphelins = cur.fetchall()

        # Affecter chaque poste à l'atelier
        for poste in postes_orphelins:
            cur.execute("""
                UPDATE postes
                SET atelier_id = %s
                WHERE id = %s
            """, (atelier_id, poste['id']))
            print(f"  - Poste {poste['poste_code']} (ID: {poste['id']}) assigné à l'atelier")

        conn.commit()

        # Logger l'action
        log_hist(
            "FIX_POSTES_ORPHELINS",
            f"Correction de {nb_orphelins} postes orphelins - assignés à l'atelier ID {atelier_id}",
            None,
            None
        )

        print(f"\n✓ Correction terminée : {nb_orphelins} postes ont été assignés à l'atelier ID {atelier_id}")

        # Vérification finale
        cur.execute("""
            SELECT COUNT(*) as count
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            WHERE a.id IS NULL
        """)
        nb_restants = cur.fetchone()['count']

        if nb_restants > 0:
            print(f"\n⚠ Attention : {nb_restants} postes orphelins restants")
        else:
            print("\n✓ Tous les postes ont maintenant un atelier assigné")

    except Exception as e:
        print(f"Erreur lors de la correction : {e}")
        conn.rollback()

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("="*70)
    print("CORRECTION DES POSTES ORPHELINS")
    print("="*70 + "\n")

    fix_postes_orphelins()

    print("\n" + "="*70)
