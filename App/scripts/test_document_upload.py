# -*- coding: utf-8 -*-
"""
Script de test pour vérifier l'upload de documents existants
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta

# Fix encoding pour Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Ajouter App au PYTHONPATH
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from core.services.document_service import DocumentService
from core.db.configbd import get_connection


def test_module_installed():
    """Vérifie que le module documentaire est installé"""
    print("\n=== TEST 1: Vérification de l'installation ===")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Vérifier la table categories_documents
        cursor.execute("SHOW TABLES LIKE 'categories_documents'")
        cat_exists = cursor.fetchone()

        cursor.close()
        cursor = conn.cursor()

        # Vérifier la table documents
        cursor.execute("SHOW TABLES LIKE 'documents'")
        doc_exists = cursor.fetchone()

        cursor.close()
        conn.close()

        if cat_exists and doc_exists:
            print("✅ Tables du module documentaire présentes")
            return True
        else:
            print("❌ Tables manquantes. Exécutez: python scripts/install_gestion_documentaire.py")
            return False

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_get_categories():
    """Teste la récupération des catégories"""
    print("\n=== TEST 2: Récupération des catégories ===")

    try:
        doc_service = DocumentService()
        categories = doc_service.get_categories()

        print(f"✅ {len(categories)} catégorie(s) trouvée(s):")
        for cat in categories:
            print(f"   - {cat['nom']} (ID: {cat['id']})")

        return categories

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []


def test_create_test_file():
    """Crée un fichier de test temporaire"""
    print("\n=== TEST 3: Création d'un fichier de test ===")

    try:
        test_file = Path(__file__).parent / "test_document_temp.txt"

        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Ceci est un fichier de test pour l'upload de documents.\n")
            f.write("Date de création: {}\n".format(date.today().strftime("%d/%m/%Y")))
            f.write("\n")
            f.write("Ce fichier sera copié dans le système de gestion documentaire.\n")

        print(f"✅ Fichier de test créé: {test_file}")
        print(f"   Taille: {test_file.stat().st_size} octets")

        return test_file

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


def test_get_first_operateur():
    """Récupère le premier opérateur actif"""
    print("\n=== TEST 4: Recherche d'un opérateur actif ===")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nom, prenom, matricule
            FROM personnel
            WHERE statut = 'ACTIF'
            LIMIT 1
        """)

        operateur = cursor.fetchone()

        cursor.close()
        conn.close()

        if operateur:
            print(f"✅ Opérateur trouvé: {operateur['nom']} {operateur['prenom']} (ID: {operateur['id']})")
            return operateur
        else:
            print("❌ Aucun opérateur actif trouvé")
            return None

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


def test_upload_document(operateur_id, categorie_id, test_file):
    """Teste l'upload d'un document"""
    print("\n=== TEST 5: Upload du document ===")

    try:
        doc_service = DocumentService()

        success, message, doc_id = doc_service.add_document(
            operateur_id=operateur_id,
            categorie_id=categorie_id,
            fichier_source=str(test_file),
            nom_affichage="Document de test automatique",
            date_expiration=date.today() + timedelta(days=365),
            notes="Ce document a été ajouté automatiquement par le script de test",
            uploaded_by="Script de test"
        )

        if success:
            print(f"✅ {message}")
            print(f"   Document ID: {doc_id}")
            return doc_id
        else:
            print(f"❌ Échec: {message}")
            return None

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


def test_verify_document(doc_id):
    """Vérifie que le document a bien été enregistré"""
    print("\n=== TEST 6: Vérification du document ===")

    try:
        doc_service = DocumentService()
        file_path = doc_service.get_document_path(doc_id)

        if file_path and file_path.exists():
            print(f"✅ Fichier physique trouvé: {file_path}")
            print(f"   Taille: {file_path.stat().st_size} octets")

            # Vérifier en base de données
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM documents WHERE id = %s", (doc_id,))
            doc = cursor.fetchone()

            cursor.close()
            conn.close()

            if doc:
                print(f"✅ Entrée en base de données trouvée")
                print(f"   Nom: {doc['nom_affichage']}")
                print(f"   Catégorie ID: {doc['categorie_id']}")
                print(f"   Statut: {doc['statut']}")
                print(f"   Date ajout: {doc['date_upload']}")
                return True
            else:
                print("❌ Entrée en base de données introuvable")
                return False
        else:
            print("❌ Fichier physique introuvable")
            return False

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_cleanup(doc_id, test_file):
    """Nettoie les fichiers de test"""
    print("\n=== TEST 7: Nettoyage ===")

    try:
        # Supprimer le document
        doc_service = DocumentService()
        success, message = doc_service.delete_document(doc_id)

        if success:
            print(f"✅ Document supprimé: {message}")
        else:
            print(f"⚠️  Échec de la suppression: {message}")

        # Supprimer le fichier de test temporaire
        if test_file and test_file.exists():
            test_file.unlink()
            print(f"✅ Fichier de test temporaire supprimé")

        return True

    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False


def main():
    """Exécute tous les tests"""
    print("=" * 70)
    print("TEST DU MODULE DE GESTION DOCUMENTAIRE - UPLOAD DE FICHIERS")
    print("=" * 70)

    # Test 1: Installation
    if not test_module_installed():
        print("\n❌ Le module n'est pas installé. Arrêt des tests.")
        return

    # Test 2: Catégories
    categories = test_get_categories()
    if not categories:
        print("\n❌ Impossible de charger les catégories. Arrêt des tests.")
        return

    # Test 3: Fichier de test
    test_file = test_create_test_file()
    if not test_file:
        print("\n❌ Impossible de créer le fichier de test. Arrêt des tests.")
        return

    # Test 4: Opérateur
    operateur = test_get_first_operateur()
    if not operateur:
        print("\n❌ Aucun opérateur trouvé. Arrêt des tests.")
        if test_file.exists():
            test_file.unlink()
        return

    # Test 5: Upload
    doc_id = test_upload_document(
        operateur_id=operateur['id'],
        categorie_id=categories[0]['id'],
        test_file=test_file
    )

    if not doc_id:
        print("\n❌ Échec de l'upload. Arrêt des tests.")
        if test_file.exists():
            test_file.unlink()
        return

    # Test 6: Vérification
    verified = test_verify_document(doc_id)

    # Test 7: Nettoyage
    test_cleanup(doc_id, test_file)

    # Résumé
    print("\n" + "=" * 70)
    if verified:
        print("✅ TOUS LES TESTS ONT RÉUSSI!")
        print("Le module de gestion documentaire fonctionne correctement.")
        print("Vous pouvez maintenant uploader des documents existants depuis l'interface.")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("Vérifiez les messages d'erreur ci-dessus.")
    print("=" * 70)


if __name__ == "__main__":
    main()
