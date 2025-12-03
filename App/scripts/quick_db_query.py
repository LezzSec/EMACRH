# -*- coding: utf-8 -*-
"""
Script de requête rapide pour analyser la base de données EMAC
Utilisé par Claude pour inspecter rapidement les données
"""

import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db.configbd import get_connection as get_db_connection
import json

def execute_query(query, params=None):
    """
    Exécute une requête SQL et retourne les résultats en format JSON

    Args:
        query (str): Requête SQL à exécuter
        params (tuple): Paramètres pour la requête préparée

    Returns:
        dict: Résultats avec colonnes et lignes
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)

        # Récupérer les noms de colonnes
        columns = [desc[0] for desc in cur.description] if cur.description else []

        # Récupérer les données
        rows = cur.fetchall()

        # Convertir en format lisible
        result = {
            'columns': columns,
            'rows': rows,
            'count': len(rows)
        }

        return result

    except Exception as e:
        return {
            'error': str(e),
            'query': query
        }
    finally:
        cur.close()
        conn.close()

def show_table_info(table_name):
    """Affiche la structure d'une table"""
    query = f"DESCRIBE {table_name}"
    result = execute_query(query)

    print(f"\n{'='*60}")
    print(f"STRUCTURE DE LA TABLE: {table_name}")
    print(f"{'='*60}")

    if 'error' in result:
        print(f"ERREUR: {result['error']}")
        return

    for row in result['rows']:
        print(f"  {row[0]:25} {row[1]:20} {row[2]:5} {row[3]:5}")
    print()

def show_table_count(table_name):
    """Affiche le nombre de lignes dans une table"""
    query = f"SELECT COUNT(*) FROM {table_name}"
    result = execute_query(query)

    if 'error' in result:
        print(f"Erreur pour {table_name}: {result['error']}")
    else:
        count = result['rows'][0][0]
        print(f"  {table_name:30} : {count:5} lignes")

def show_sample_data(table_name, limit=5):
    """Affiche un échantillon de données d'une table"""
    query = f"SELECT * FROM {table_name} LIMIT {limit}"
    result = execute_query(query)

    print(f"\n{'='*60}")
    print(f"ÉCHANTILLON DE DONNÉES: {table_name} (max {limit} lignes)")
    print(f"{'='*60}")

    if 'error' in result:
        print(f"ERREUR: {result['error']}")
        return

    # Afficher les colonnes
    print("Colonnes:", ", ".join(result['columns']))
    print("-" * 60)

    # Afficher les données
    for i, row in enumerate(result['rows'], 1):
        print(f"Ligne {i}:")
        for col, val in zip(result['columns'], row):
            print(f"  {col:20} : {val}")
        print()

def database_overview():
    """Affiche un aperçu complet de la base de données"""
    print("\n" + "="*60)
    print("APERÇU DE LA BASE DE DONNÉES EMAC")
    print("="*60)

    # Liste des tables principales
    tables = [
        'personnel',
        'postes',
        'atelier',
        'polyvalence',
        'contrat',
        'historique',
        'formation',
        'documents'
    ]

    print("\nNOMBRE DE LIGNES PAR TABLE:")
    print("-" * 60)
    for table in tables:
        show_table_count(table)

    # Afficher quelques statistiques utiles
    print("\n\nSTATISTIQUES UTILES:")
    print("-" * 60)

    # Personnel actif/inactif
    query = "SELECT statut, COUNT(*) FROM personnel GROUP BY statut"
    result = execute_query(query)
    if 'error' not in result:
        print("\nPersonnel par statut:")
        for row in result['rows']:
            print(f"  {row[0]:15} : {row[1]} personnes")

    # Polyvalence par niveau
    query = "SELECT niveau, COUNT(*) FROM polyvalence GROUP BY niveau ORDER BY niveau"
    result = execute_query(query)
    if 'error' not in result:
        print("\nPolyvalence par niveau:")
        for row in result['rows']:
            print(f"  Niveau {row[0]} : {row[1]} évaluations")

    # Évaluations en retard
    query = """
        SELECT COUNT(*)
        FROM polyvalence
        WHERE prochaine_evaluation < CURDATE()
        AND prochaine_evaluation IS NOT NULL
    """
    result = execute_query(query)
    if 'error' not in result:
        retard = result['rows'][0][0]
        print(f"\nÉvaluations en retard : {retard}")

    # Contrats actifs
    query = """
        SELECT COUNT(*)
        FROM contrat
        WHERE date_fin >= CURDATE() OR date_fin IS NULL
    """
    result = execute_query(query)
    if 'error' not in result:
        actifs = result['rows'][0][0]
        print(f"Contrats actifs : {actifs}")

def custom_query(sql):
    """Exécute une requête SQL personnalisée"""
    print("\n" + "="*60)
    print("REQUÊTE PERSONNALISÉE")
    print("="*60)
    print(f"SQL: {sql}")
    print("-" * 60)

    result = execute_query(sql)

    if 'error' in result:
        print(f"\nERREUR: {result['error']}")
        return

    print(f"\nNombre de résultats: {result['count']}")
    print(f"Colonnes: {', '.join(result['columns'])}")
    print("\nRésultats:")
    print("-" * 60)

    for i, row in enumerate(result['rows'], 1):
        print(f"\nLigne {i}:")
        for col, val in zip(result['columns'], row):
            print(f"  {col:20} : {val}")

if __name__ == "__main__":
    import sys

    # Si un argument est passé, l'exécuter comme requête SQL
    if len(sys.argv) > 1:
        sql = " ".join(sys.argv[1:])
        custom_query(sql)
    else:
        # Sinon, afficher l'aperçu complet
        database_overview()
