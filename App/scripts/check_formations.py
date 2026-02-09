# -*- coding: utf-8 -*-
"""
Script pour vérifier les formations assignées dans la base de données.
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.configbd import DatabaseCursor
from datetime import datetime


def show_recent_formations(limit=20):
    """Affiche les formations les plus récentes."""

    # Vérifier si la colonne created_at existe
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("SHOW COLUMNS FROM formation LIKE 'created_at'")
        has_created_at = cur.fetchone() is not None

    if has_created_at:
        query = """
            SELECT
                f.id,
                f.operateur_id,
                CONCAT(p.nom, ' ', p.prenom) AS employe,
                f.intitule,
                f.organisme,
                f.date_debut,
                f.date_fin,
                f.statut,
                f.certificat_obtenu,
                f.created_at
            FROM formation f
            INNER JOIN personnel p ON f.operateur_id = p.id
            ORDER BY f.created_at DESC
            LIMIT %s
        """
    else:
        query = """
            SELECT
                f.id,
                f.operateur_id,
                CONCAT(p.nom, ' ', p.prenom) AS employe,
                f.intitule,
                f.organisme,
                f.date_debut,
                f.date_fin,
                f.statut,
                f.certificat_obtenu
            FROM formation f
            INNER JOIN personnel p ON f.operateur_id = p.id
            ORDER BY f.id DESC
            LIMIT %s
        """

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute(query, (limit,))
        formations = cur.fetchall()

    if not formations:
        print("[X] Aucune formation trouvee dans la base de donnees.")
        return

    print(f"\n[+] {len(formations)} FORMATIONS RECENTES\n")
    print("=" * 120)

    for f in formations:
        print(f"\n[ID] Formation ID: {f['id']}")
        print(f"     Employe: {f['employe']} (ID: {f['operateur_id']})")
        print(f"     Intitule: {f['intitule']}")
        print(f"     Organisme: {f['organisme'] or 'Non specifie'}")
        print(f"     Dates: {f['date_debut'] or 'N/A'} -> {f['date_fin'] or 'N/A'}")
        print(f"     Statut: {f['statut']}")
        print(f"     Certificat: {'Oui' if f['certificat_obtenu'] else 'Non'}")
        if has_created_at and 'created_at' in f:
            print(f"     Cree le: {f['created_at']}")
        print("-" * 120)


def show_formations_by_person(nom=None, prenom=None):
    """Affiche les formations pour une personne spécifique."""

    # Vérifier si la colonne created_at existe
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("SHOW COLUMNS FROM formation LIKE 'created_at'")
        has_created_at = cur.fetchone() is not None

    base_select = """
        SELECT
            f.id,
            CONCAT(p.nom, ' ', p.prenom) AS employe,
            f.intitule,
            f.organisme,
            f.date_debut,
            f.date_fin,
            f.statut,
            f.certificat_obtenu
    """

    if has_created_at:
        base_select += ", f.created_at"

    query = base_select + """
        FROM formation f
        INNER JOIN personnel p ON f.operateur_id = p.id
        WHERE 1=1
    """

    params = []

    if nom:
        query += " AND p.nom LIKE %s"
        params.append(f"%{nom}%")

    if prenom:
        query += " AND p.prenom LIKE %s"
        params.append(f"%{prenom}%")

    query += " ORDER BY f.id DESC" if not has_created_at else " ORDER BY f.created_at DESC"

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute(query, params)
        formations = cur.fetchall()

    if not formations:
        print(f"[X] Aucune formation trouvee pour {nom or ''} {prenom or ''}")
        return

    print(f"\n[+] {len(formations)} FORMATION(S) POUR {formations[0]['employe']}\n")
    print("=" * 120)

    for f in formations:
        print(f"\n[ID] Formation ID: {f['id']}")
        print(f"     Intitule: {f['intitule']}")
        print(f"     Organisme: {f['organisme'] or 'Non specifie'}")
        print(f"     Dates: {f['date_debut'] or 'N/A'} -> {f['date_fin'] or 'N/A'}")
        print(f"     Statut: {f['statut']}")
        print(f"     Certificat: {'Oui' if f['certificat_obtenu'] else 'Non'}")
        if has_created_at and 'created_at' in f:
            print(f"     Cree le: {f['created_at']}")
        print("-" * 120)


def show_stats():
    """Affiche des statistiques sur les formations."""

    queries = {
        "Total formations": "SELECT COUNT(*) as count FROM formation",
        "Formations planifiees": "SELECT COUNT(*) as count FROM formation WHERE statut = 'Planifiée'",
        "Formations en cours": "SELECT COUNT(*) as count FROM formation WHERE statut = 'En cours'",
        "Formations terminees": "SELECT COUNT(*) as count FROM formation WHERE statut = 'Terminée'",
        "Formations annulees": "SELECT COUNT(*) as count FROM formation WHERE statut = 'Annulée'",
        "Employes ayant des formations": """
            SELECT COUNT(DISTINCT operateur_id) as count FROM formation
        """,
    }

    print("\n[STATS] STATISTIQUES DES FORMATIONS\n")
    print("=" * 60)

    with DatabaseCursor(dictionary=True) as cur:
        for label, query in queries.items():
            cur.execute(query)
            result = cur.fetchone()
            print(f"{label:.<40} {result['count']:>5}")

    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vérifier les formations assignées")
    parser.add_argument("--recent", type=int, default=20, help="Nombre de formations récentes à afficher")
    parser.add_argument("--nom", help="Rechercher par nom")
    parser.add_argument("--prenom", help="Rechercher par prénom")
    parser.add_argument("--stats", action="store_true", help="Afficher les statistiques")

    args = parser.parse_args()

    try:
        if args.stats:
            show_stats()
        elif args.nom or args.prenom:
            show_formations_by_person(args.nom, args.prenom)
        else:
            show_recent_formations(args.recent)

    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
