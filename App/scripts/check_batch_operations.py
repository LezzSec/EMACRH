# -*- coding: utf-8 -*-
"""Script rapide pour vérifier les opérations batch."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.configbd import DatabaseCursor

print("\n[BATCH OPERATIONS RECENTES]\n")
print("=" * 120)

with DatabaseCursor(dictionary=True) as cur:
    cur.execute("SELECT * FROM batch_operations ORDER BY created_at DESC LIMIT 10")
    rows = cur.fetchall()

    if not rows:
        print("Aucune operation batch trouvee.")
    else:
        for r in rows:
            print(f"\nID: {r['id']}")
            print(f"  Type: {r['operation_type']}")
            print(f"  Description: {r['description']}")
            print(f"  Statut: {r['status']}")
            print(f"  Personnel concernes: {r['nb_personnel']}")
            print(f"  Succes: {r['nb_success']}")
            print(f"  Erreurs: {r['nb_errors']}")
            print(f"  Cree par: {r['created_by'] or 'N/A'}")
            print(f"  Date: {r['created_at']}")
            print("-" * 120)
