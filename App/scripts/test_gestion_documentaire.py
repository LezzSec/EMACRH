# -*- coding: utf-8 -*-
"""
Script de test pour identifier les problèmes de la gestion documentaire
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier parent au PATH
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*70)
print("  Test du Module de Gestion Documentaire")
print("="*70)
print()

# Test 1: Import des modules
print("Test 1: Import des modules...")
try:
    from core.db.configbd import get_connection
    print("  OK - configbd importe")
except Exception as e:
    print(f"  ERREUR - configbd: {e}")
    sys.exit(1)

try:
    from core.services.document_service import DocumentService
    print("  OK - DocumentService importe")
except Exception as e:
    print(f"  ERREUR - DocumentService: {e}")
    sys.exit(1)

try:
    from core.services.logger import log_hist
    print("  OK - logger importe")
except Exception as e:
    print(f"  ERREUR - logger: {e}")
    sys.exit(1)

print()

# Test 2: Connexion à la base de données
print("Test 2: Connexion a la base de donnees...")
try:
    conn = get_connection()
    cur = conn.cursor(buffered=True)
    cur.execute("SELECT 1")
    result = cur.fetchone()
    cur.close()
    conn.close()
    print("  OK - Connexion reussie")
except Exception as e:
    print(f"  ERREUR - Connexion: {e}")
    sys.exit(1)

print()

# Test 3: Vérifier les tables
print("Test 3: Verification des tables...")
try:
    conn = get_connection()
    cur = conn.cursor(buffered=True)

    cur.execute("SHOW TABLES LIKE 'personnel'")
    if cur.fetchone():
        print("  OK - Table 'personnel' existe")
    else:
        print("  ATTENTION - Table 'personnel' n'existe pas")

    cur.execute("SHOW TABLES LIKE 'categories_documents'")
    if cur.fetchone():
        print("  OK - Table 'categories_documents' existe")
    else:
        print("  ATTENTION - Table 'categories_documents' n'existe pas")

    cur.execute("SHOW TABLES LIKE 'documents'")
    if cur.fetchone():
        print("  OK - Table 'documents' existe")
    else:
        print("  ATTENTION - Table 'documents' n'existe pas")

    cur.close()
    conn.close()
except Exception as e:
    print(f"  ERREUR: {e}")

print()

# Test 4: Créer le service DocumentService
print("Test 4: Creation du service DocumentService...")
try:
    doc_service = DocumentService()
    print("  OK - DocumentService cree")
except Exception as e:
    print(f"  ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 5: Charger les catégories
print("Test 5: Chargement des categories...")
try:
    categories = doc_service.get_categories()
    if categories:
        print(f"  OK - {len(categories)} categories trouvees:")
        for cat in categories:
            print(f"    - {cat['nom']}")
    else:
        print("  ATTENTION - Aucune categorie trouvee")
except Exception as e:
    print(f"  ERREUR: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 6: Import PyQt5
print("Test 6: Import PyQt5...")
try:
    from PyQt5.QtWidgets import QApplication
    print("  OK - PyQt5 importe")
except Exception as e:
    print(f"  ERREUR: {e}")
    sys.exit(1)

print()

# Test 7: Créer l'interface
print("Test 7: Creation de l'interface GestionDocumentaireDialog...")
try:
    from PyQt5.QtWidgets import QApplication
    from core.gui.gestion_documentaire import GestionDocumentaireDialog

    app = QApplication([])
    dialog = GestionDocumentaireDialog()
    print("  OK - Interface creee avec succes")
except Exception as e:
    print(f"  ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 8: Tester l'ajout de document (sans afficher)
print("Test 8: Test de la fenetre AddDocumentDialog...")
try:
    from core.gui.gestion_documentaire import AddDocumentDialog

    # Essayer de créer la fenêtre avec un ID bidon
    add_dialog = AddDocumentDialog(operateur_id=1, parent=None)
    print("  OK - Fenetre AddDocumentDialog creee")
except Exception as e:
    print(f"  ERREUR: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
print("  Tests termines")
print("="*70)
print()
print("Appuyez sur Entree pour quitter...")
input()
