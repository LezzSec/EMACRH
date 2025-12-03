# -*- coding: utf-8 -*-
"""
Script de nettoyage des doublons dans la table polyvalence.

Ce script :
1. Identifie les entrées en double (même operateur_id + poste_id)
2. Garde la meilleure entrée (avec date_evaluation la plus récente ou niveau le plus élevé)
3. Supprime les doublons
4. Log les actions effectuées
"""

import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.configbd import get_connection
from datetime import datetime


def find_duplicates(cursor):
    """
    Trouve tous les doublons dans la table polyvalence.
    Retourne une liste de (operateur_id, poste_id, count)
    """
    cursor.execute("""
        SELECT operateur_id, poste_id, COUNT(*) as nb_doublons
        FROM polyvalence
        GROUP BY operateur_id, poste_id
        HAVING COUNT(*) > 1
        ORDER BY nb_doublons DESC
    """)
    return cursor.fetchall()


def get_duplicate_rows(cursor, operateur_id, poste_id):
    """
    Récupère toutes les lignes pour une combinaison operateur_id + poste_id.
    Retourne (id, operateur_id, poste_id, date_evaluation, prochaine_evaluation, niveau)
    """
    cursor.execute("""
        SELECT id, operateur_id, poste_id, date_evaluation, prochaine_evaluation, niveau
        FROM polyvalence
        WHERE operateur_id = %s AND poste_id = %s
        ORDER BY
            CASE WHEN date_evaluation IS NULL THEN 1 ELSE 0 END,
            date_evaluation DESC,
            niveau DESC,
            id DESC
    """, (operateur_id, poste_id))
    return cursor.fetchall()


def choose_best_row(rows):
    """
    Choisit la meilleure ligne parmi les doublons.
    Critères :
    1. Ligne avec date_evaluation la plus récente (non NULL)
    2. Si toutes NULL, prendre le niveau le plus élevé
    3. En dernier recours, prendre l'ID le plus récent

    Retourne : (best_row, rows_to_delete)
    """
    if not rows:
        return None, []

    # rows est déjà trié par date_evaluation DESC, niveau DESC, id DESC
    # La première ligne est donc la meilleure selon nos critères
    best_row = rows[0]
    rows_to_delete = rows[1:]

    return best_row, rows_to_delete


def clean_duplicates(dry_run=True):
    """
    Nettoie les doublons dans la table polyvalence.

    Args:
        dry_run: Si True, affiche ce qui serait fait sans modifier la base
    """
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        print("=" * 80)
        print("NETTOYAGE DES DOUBLONS DE POLYVALENCE")
        print("=" * 80)
        print(f"Mode: {'DRY RUN (simulation)' if dry_run else 'EXECUTION RÉELLE'}")
        print()

        # Trouver tous les doublons
        duplicates = find_duplicates(cursor)

        if not duplicates:
            print("OK - Aucun doublon trouve dans la table polyvalence.")
            return

        print(f"Trouve {len(duplicates)} combinaisons operateur+poste avec des doublons\n")

        total_to_delete = 0
        details = []

        for dup in duplicates:
            operateur_id = dup['operateur_id']
            poste_id = dup['poste_id']
            count = dup['nb_doublons']

            # Récupérer le nom de l'opérateur
            cursor.execute(
                "SELECT nom, prenom FROM personnel WHERE id = %s",
                (operateur_id,)
            )
            person = cursor.fetchone()
            person_name = f"{person['prenom']} {person['nom']}" if person else f"ID {operateur_id}"

            # Récupérer le code du poste
            cursor.execute(
                "SELECT poste_code FROM postes WHERE id = %s",
                (poste_id,)
            )
            poste = cursor.fetchone()
            poste_code = poste['poste_code'] if poste else f"ID {poste_id}"

            # Récupérer toutes les lignes
            rows = get_duplicate_rows(cursor, operateur_id, poste_id)
            best_row, rows_to_delete = choose_best_row(rows)

            if not best_row:
                continue

            print(f"[*] {person_name} - Poste {poste_code}")
            print(f"   Doublons: {count} entrees")
            print(f"   [OK] Ligne a GARDER:")
            print(f"      ID: {best_row['id']}, Niveau: {best_row['niveau']}, "
                  f"Date eval: {best_row['date_evaluation']}, "
                  f"Prochaine: {best_row['prochaine_evaluation']}")

            if rows_to_delete:
                print(f"   [X] Lignes a SUPPRIMER ({len(rows_to_delete)}):")
                for row in rows_to_delete:
                    print(f"      ID: {row['id']}, Niveau: {row['niveau']}, "
                          f"Date eval: {row['date_evaluation']}, "
                          f"Prochaine: {row['prochaine_evaluation']}")

                total_to_delete += len(rows_to_delete)

                # Supprimer les doublons si pas en mode dry run
                if not dry_run:
                    ids_to_delete = [row['id'] for row in rows_to_delete]
                    placeholders = ','.join(['%s'] * len(ids_to_delete))
                    cursor.execute(
                        f"DELETE FROM polyvalence WHERE id IN ({placeholders})",
                        ids_to_delete
                    )

                details.append({
                    'person': person_name,
                    'poste': poste_code,
                    'kept_id': best_row['id'],
                    'deleted_count': len(rows_to_delete)
                })

            print()

        print("=" * 80)
        print(f"RÉSUMÉ")
        print("=" * 80)
        print(f"Combinaisons avec doublons: {len(duplicates)}")
        print(f"Total lignes à supprimer: {total_to_delete}")

        if not dry_run:
            connection.commit()
            print("\n[OK] NETTOYAGE EFFECTUE AVEC SUCCES")

            # Log dans l'historique
            cursor.execute("""
                INSERT INTO historique (date_time, action, description)
                VALUES (NOW(), 'CLEANUP', %s)
            """, (f"Nettoyage de {total_to_delete} doublons dans la table polyvalence",))
            connection.commit()
        else:
            print("\n[!] MODE DRY RUN - Aucune modification effectuee")
            print("   Pour effectuer le nettoyage reel, executez:")
            print("   py scripts/fix_duplicate_polyvalence.py --execute")

        return details

    except Exception as e:
        print(f"\n[ERREUR] {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nettoie les doublons dans la table polyvalence")
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Exécute réellement le nettoyage (par défaut: dry-run)'
    )

    args = parser.parse_args()

    try:
        clean_duplicates(dry_run=not args.execute)
    except KeyboardInterrupt:
        print("\n\n[!] Operation annulee par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERREUR] Erreur fatale: {e}")
        sys.exit(1)
