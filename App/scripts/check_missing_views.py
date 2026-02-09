# -*- coding: utf-8 -*-
"""Script pour vérifier toutes les vues manquantes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.configbd import get_connection

# Liste de toutes les vues qui devraient exister selon les migrations
EXPECTED_VIEWS = [
    'v_absences_details',
    'v_alertes_entretiens',
    'v_alertes_medicales',
    'v_batch_operations_stats',
    'v_contrat_anciennete',
    'v_contrats_fin_proche',
    'v_document_rules_with_templates',
    'v_documents_complet',
    'v_documents_employes',
    'v_documents_expiration_alerte',
    'v_documents_expiration_proche',
    'v_documents_stats',
    'v_documents_stats_operateur',
    'v_historique_polyvalence_complet',
    'v_personnel_age',
    'v_personnel_anciennete',
    'v_soldes_disponibles',
    'v_stats_absences',
    'v_suivi_medical',
    'v_vie_salarie_recap',
]

def main():
    conn = get_connection()
    cur = conn.cursor()

    print("=== VERIFICATION DES VUES ===\n")

    # Récupérer les vues existantes
    cur.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
    existing_views = set(t[0] for t in cur.fetchall())

    print(f"Vues existantes: {len(existing_views)}")
    print(f"Vues attendues: {len(EXPECTED_VIEWS)}\n")

    missing_views = []
    present_views = []

    for view in sorted(EXPECTED_VIEWS):
        if view in existing_views:
            print(f"  OK {view}")
            present_views.append(view)
        else:
            print(f"  MANQUANT {view}")
            missing_views.append(view)

    print(f"\n=== RESUME ===")
    print(f"Vues presentes: {len(present_views)}/{len(EXPECTED_VIEWS)}")
    print(f"Vues manquantes: {len(missing_views)}/{len(EXPECTED_VIEWS)}")

    if missing_views:
        print(f"\nVues a creer:")
        for view in missing_views:
            print(f"  - {view}")
    else:
        print("\nToutes les vues sont presentes!")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
