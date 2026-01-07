# -*- coding: utf-8 -*-
"""
Script de vérification des index de performance.
Vérifie que tous les 29 index recommandés sont bien présents dans la base.
"""

import sys
import os

# Ajouter le chemin parent pour importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.configbd import get_connection


# Liste des index attendus (nom de l'index, table, colonnes)
EXPECTED_INDEXES = [
    # Polyvalence
    ('idx_polyvalence_operateur_id', 'polyvalence', ['operateur_id']),
    ('idx_polyvalence_poste_id', 'polyvalence', ['poste_id']),
    ('idx_polyvalence_prochaine_eval', 'polyvalence', ['prochaine_evaluation']),
    ('idx_polyvalence_date_eval', 'polyvalence', ['date_evaluation']),
    ('idx_polyvalence_niveau', 'polyvalence', ['niveau']),
    ('idx_polyvalence_op_poste', 'polyvalence', ['operateur_id', 'poste_id']),
    ('idx_polyvalence_eval_retard', 'polyvalence', ['prochaine_evaluation', 'niveau']),

    # Personnel
    ('idx_personnel_statut', 'personnel', ['statut']),
    ('idx_personnel_matricule', 'personnel', ['matricule']),
    ('idx_personnel_nom_prenom', 'personnel', ['nom', 'prenom']),

    # Operateurs (table legacy)
    ('idx_operateurs_statut', 'operateurs', ['statut']),
    ('idx_operateurs_nom_prenom', 'operateurs', ['nom', 'prenom']),

    # Postes
    ('idx_postes_code', 'postes', ['poste_code']),
    ('idx_postes_atelier_id', 'postes', ['atelier_id']),
    ('idx_postes_statut', 'postes', ['statut']),
    ('idx_postes_code_atelier', 'postes', ['poste_code', 'atelier_id']),

    # Contrats
    ('idx_contrats_personnel_id', 'contrats', ['personnel_id']),
    ('idx_contrats_date_fin', 'contrats', ['date_fin']),
    ('idx_contrats_type', 'contrats', ['type_contrat']),
    ('idx_contrats_personnel_type', 'contrats', ['personnel_id', 'type_contrat']),

    # Absences
    ('idx_absences_personnel_id', 'absences', ['personnel_id']),
    ('idx_absences_date_debut', 'absences', ['date_debut']),
    ('idx_absences_date_fin', 'absences', ['date_fin']),
    ('idx_absences_type', 'absences', ['type_absence']),
    ('idx_absences_personnel_dates', 'absences', ['personnel_id', 'date_debut', 'date_fin']),

    # Historique
    ('idx_historique_date', 'historique', ['date_action']),
    ('idx_historique_operateur_id', 'historique', ['operateur_id']),
    ('idx_historique_action', 'historique', ['action']),

    # Utilisateurs
    ('idx_utilisateurs_username', 'utilisateurs', ['username']),
]


def get_existing_indexes(conn):
    """
    Récupère tous les index existants dans la base emac_db.

    Returns:
        dict: {table_name: {index_name: [columns]}}
    """
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT
                TABLE_NAME,
                INDEX_NAME,
                COLUMN_NAME,
                SEQ_IN_INDEX
            FROM
                information_schema.STATISTICS
            WHERE
                TABLE_SCHEMA = DATABASE()
                AND INDEX_NAME != 'PRIMARY'
            ORDER BY
                TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
        """)

        rows = cur.fetchall()

        # Organiser par table et index
        indexes = {}
        for row in rows:
            table = row['TABLE_NAME']
            index_name = row['INDEX_NAME']
            column = row['COLUMN_NAME']

            if table not in indexes:
                indexes[table] = {}

            if index_name not in indexes[table]:
                indexes[table][index_name] = []

            indexes[table][index_name].append(column)

        return indexes

    finally:
        cur.close()


def verify_indexes():
    """Vérifie que tous les index attendus sont présents"""
    print("=" * 70)
    print("🔍 VÉRIFICATION DES INDEX DE PERFORMANCE")
    print("=" * 70)
    print()

    try:
        conn = get_connection()
        print("✅ Connexion à la base de données établie")
        print()

        # Récupérer les index existants
        existing_indexes = get_existing_indexes(conn)

        # Vérifier chaque index attendu
        missing_indexes = []
        present_indexes = []

        for index_name, table_name, expected_columns in EXPECTED_INDEXES:
            if table_name in existing_indexes and index_name in existing_indexes[table_name]:
                actual_columns = existing_indexes[table_name][index_name]

                # Vérifier que les colonnes correspondent
                if actual_columns == expected_columns:
                    present_indexes.append((index_name, table_name, expected_columns))
                else:
                    print(f"⚠️  Index '{index_name}' sur '{table_name}' : colonnes incorrectes")
                    print(f"   Attendu  : {expected_columns}")
                    print(f"   Trouvé   : {actual_columns}")
                    print()
            else:
                missing_indexes.append((index_name, table_name, expected_columns))

        # Afficher les résultats
        print("=" * 70)
        print("📊 RÉSULTATS")
        print("=" * 70)
        print()

        print(f"✅ Index présents : {len(present_indexes)} / {len(EXPECTED_INDEXES)}")
        print(f"❌ Index manquants : {len(missing_indexes)} / {len(EXPECTED_INDEXES)}")
        print()

        if present_indexes:
            print("=" * 70)
            print("✅ INDEX PRÉSENTS")
            print("=" * 70)
            for index_name, table_name, columns in present_indexes:
                cols_str = ', '.join(columns)
                print(f"  • {index_name:40} {table_name:20} ({cols_str})")
            print()

        if missing_indexes:
            print("=" * 70)
            print("❌ INDEX MANQUANTS")
            print("=" * 70)
            for index_name, table_name, columns in missing_indexes:
                cols_str = ', '.join(columns)
                print(f"  • {index_name:40} {table_name:20} ({cols_str})")
            print()
            print("⚠️  Pour créer les index manquants, exécutez :")
            print("    cd App\\scripts")
            print("    python apply_performance_indexes.py")
            print()

        # Statistiques supplémentaires
        print("=" * 70)
        print("📈 STATISTIQUES PAR TABLE")
        print("=" * 70)

        table_stats = {}
        for index_name, table_name, columns in EXPECTED_INDEXES:
            if table_name not in table_stats:
                table_stats[table_name] = {'expected': 0, 'present': 0}
            table_stats[table_name]['expected'] += 1

        for index_name, table_name, columns in present_indexes:
            if table_name in table_stats:
                table_stats[table_name]['present'] += 1

        for table_name in sorted(table_stats.keys()):
            stats = table_stats[table_name]
            present = stats['present']
            expected = stats['expected']
            percentage = (present / expected * 100) if expected > 0 else 0

            status = "✅" if present == expected else "⚠️ "
            print(f"  {status} {table_name:20} {present:2}/{expected:2} index ({percentage:5.1f}%)")

        print()
        print("=" * 70)

        conn.close()

        # Code de sortie
        if missing_indexes:
            return 1  # Erreur : index manquants
        else:
            print("✅ TOUS LES INDEX SONT PRÉSENTS !")
            print()
            return 0  # Succès

    except Exception as e:
        print(f"❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return 2


def show_all_indexes():
    """Affiche TOUS les index de la base (debug)"""
    print("=" * 70)
    print("📋 TOUS LES INDEX DE LA BASE emac_db")
    print("=" * 70)
    print()

    try:
        conn = get_connection()
        existing_indexes = get_existing_indexes(conn)

        for table_name in sorted(existing_indexes.keys()):
            print(f"\n📁 Table: {table_name}")
            print("-" * 70)

            for index_name, columns in existing_indexes[table_name].items():
                cols_str = ', '.join(columns)
                print(f"  • {index_name:40} ({cols_str})")

        print()
        print("=" * 70)

        conn.close()

    except Exception as e:
        print(f"❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Vérifie les index de performance')
    parser.add_argument('--all', action='store_true',
                       help='Affiche tous les index (pas seulement les attendus)')

    args = parser.parse_args()

    if args.all:
        show_all_indexes()
    else:
        exit_code = verify_indexes()
        sys.exit(exit_code)
