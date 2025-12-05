# -*- coding: utf-8 -*-
"""
Script de correction de l'encodage des catégories
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.configbd import get_connection

print("="*70)
print("  Correction de l'encodage des categories")
print("="*70)
print()

conn = None
cur = None

try:
    print("Connexion a la base de donnees...")
    conn = get_connection()
    cur = conn.cursor(buffered=True)
    print("OK\n")

    # Supprimer toutes les catégories
    print("Suppression des categories existantes...")
    cur.execute("DELETE FROM categories_documents")
    conn.commit()
    print("OK\n")

    # Réinsérer les catégories avec le bon encodage
    print("Insertion des categories avec encodage UTF-8...")

    categories = [
        ('Contrats de travail', 'Contrats CDI, CDD, avenants', '#10b981', True, 1),
        ('Certificats medicaux', 'Visites medicales, aptitudes, RQTH', '#ef4444', True, 2),
        ('Diplomes et formations', 'Diplomes, certificats de formation, habilitations', '#8b5cf6', False, 3),
        ('Autorisations de travail', 'Titres de sejour, autorisations de travail pour etrangers', '#f59e0b', True, 4),
        ('Pieces d\'identite', 'CNI, passeport, permis de conduire', '#06b6d4', True, 5),
        ('Attestations diverses', 'Attestations employeur, certificats de travail', '#6366f1', False, 6),
        ('Documents administratifs', 'Fiches de paie, releves, justificatifs', '#64748b', False, 7),
        ('Autres', 'Documents non classes', '#9ca3af', False, 99)
    ]

    for cat in categories:
        cur.execute("""
            INSERT INTO categories_documents
            (nom, description, couleur, exige_date_expiration, ordre_affichage)
            VALUES (%s, %s, %s, %s, %s)
        """, cat)
        print(f"  - {cat[0]}")

    conn.commit()
    print("\nOK - Categories inserees\n")

    # Vérifier
    print("Verification...")
    cur.execute("SELECT nom FROM categories_documents ORDER BY ordre_affichage")
    categories = cur.fetchall()
    print(f"OK - {len(categories)} categories trouvees\n")

    print("="*70)
    print("OK - Correction terminee avec succes!")
    print("="*70)

except Exception as e:
    print(f"\nERREUR: {e}")
    if conn:
        conn.rollback()
    import traceback
    traceback.print_exc()

finally:
    if cur:
        cur.close()
    if conn:
        conn.close()

print("\nAppuyez sur Entree pour quitter...")
input()
