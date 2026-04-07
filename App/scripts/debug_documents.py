# -*- coding: utf-8 -*-
"""
Script de diagnostic pour déboguer les problèmes d'affichage des documents.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.db.configbd import get_connection
from infrastructure.config.app_paths import get_documents_dir

def check_table_structure():
    """Vérifie la structure de la table documents."""
    print("=" * 70)
    print("1️⃣  STRUCTURE DE LA TABLE DOCUMENTS")
    print("=" * 70)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("DESCRIBE documents")
        columns = cur.fetchall()

        print(f"\n📋 Colonnes présentes ({len(columns)}):")
        important_cols = ['personnel_id', 'formation_id', 'contrat_id', 'declaration_id']

        for col in columns:
            col_name = col[0]
            col_type = col[1]
            is_important = '✅' if col_name in important_cols else '  '
            print(f"{is_important} {col_name:20} {col_type}")

        # Vérifier les colonnes critiques
        col_names = [c[0] for c in columns]
        missing = [c for c in important_cols if c not in col_names]

        if missing:
            print(f"\n⚠️  Colonnes manquantes: {', '.join(missing)}")
            print("   → Exécutez: python scripts\\setup_documents_complete.py")
            return False
        else:
            print("\n✅ Toutes les colonnes critiques sont présentes")
            return True

    finally:
        cur.close()
        conn.close()

def check_view_exists():
    """Vérifie si la vue v_documents_complet existe."""
    print("\n" + "=" * 70)
    print("2️⃣  VUE v_documents_complet")
    print("=" * 70)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SHOW FULL TABLES WHERE Table_type = 'VIEW'
            AND Tables_in_emac_db = 'v_documents_complet'
        """)
        exists = cur.fetchone() is not None

        if exists:
            print("\n✅ La vue v_documents_complet existe")
            return True
        else:
            print("\n❌ La vue v_documents_complet N'EXISTE PAS")
            print("   → Exécutez: python scripts\\setup_documents_complete.py")
            return False

    finally:
        cur.close()
        conn.close()

def check_documents_in_db():
    """Vérifie les documents dans la base de données."""
    print("\n" + "=" * 70)
    print("3️⃣  DOCUMENTS DANS LA BASE DE DONNÉES")
    print("=" * 70)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Compter tous les documents
        cur.execute("SELECT COUNT(*) as total FROM documents")
        total = cur.fetchone()['total']
        print(f"\n📊 Nombre total de documents: {total}")

        if total == 0:
            print("   ⚠️  Aucun document dans la base")
            return

        # Compter par statut
        cur.execute("""
            SELECT statut, COUNT(*) as nb
            FROM documents
            GROUP BY statut
        """)
        print("\n   Par statut:")
        for row in cur.fetchall():
            print(f"     - {row['statut']}: {row['nb']}")

        # Compter les documents avec formation_id
        cur.execute("""
            SELECT COUNT(*) as total
            FROM documents
            WHERE formation_id IS NOT NULL
        """)
        with_formation = cur.fetchone()['total']
        print(f"\n   Documents liés à une formation: {with_formation}")

        # Afficher les 5 derniers documents ajoutés
        print("\n📄 5 derniers documents ajoutés:")
        cur.execute("""
            SELECT
                id,
                personnel_id,
                formation_id,
                contrat_id,
                nom_affichage,
                chemin_fichier,
                date_upload
            FROM documents
            ORDER BY date_upload DESC
            LIMIT 5
        """)

        documents = cur.fetchall()
        if not documents:
            print("   Aucun document trouvé")
        else:
            for doc in documents:
                print(f"\n   ID: {doc['id']}")
                print(f"   Nom: {doc['nom_affichage']}")
                print(f"   Personnel ID: {doc['personnel_id']}")
                print(f"   Formation ID: {doc['formation_id']}")
                print(f"   Contrat ID: {doc['contrat_id']}")
                print(f"   Chemin: {doc['chemin_fichier']}")
                print(f"   Date: {doc['date_upload']}")
                print("   " + "-" * 60)

    finally:
        cur.close()
        conn.close()

def check_file_paths():
    """Vérifie les chemins des fichiers."""
    print("\n" + "=" * 70)
    print("4️⃣  VÉRIFICATION DES FICHIERS PHYSIQUES")
    print("=" * 70)

    # Afficher le répertoire de base
    base_path = get_documents_dir()
    print(f"\n📁 Répertoire de base: {base_path}")
    print(f"   Existe: {'✅ OUI' if base_path.exists() else '❌ NON'}")

    if not base_path.exists():
        print("   → Le répertoire de base n'existe pas!")
        return

    # Lister les fichiers récents
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT
                id,
                nom_affichage,
                chemin_fichier,
                taille_octets
            FROM documents
            ORDER BY date_upload DESC
            LIMIT 5
        """)

        documents = cur.fetchall()

        if not documents:
            print("\n   Aucun document dans la base")
            return

        print(f"\n📄 Vérification des 5 derniers fichiers:")

        for doc in documents:
            file_path = base_path / doc['chemin_fichier']
            exists = file_path.exists()

            print(f"\n   Document ID {doc['id']}: {doc['nom_affichage']}")
            print(f"   Chemin BDD: {doc['chemin_fichier']}")
            print(f"   Chemin complet: {file_path}")
            print(f"   Existe: {'✅ OUI' if exists else '❌ NON'}")

            if exists:
                actual_size = file_path.stat().st_size
                expected_size = doc['taille_octets']
                print(f"   Taille: {actual_size} octets (BDD: {expected_size})")

    finally:
        cur.close()
        conn.close()

def check_recent_formations():
    """Vérifie les formations récentes et leurs documents."""
    print("\n" + "=" * 70)
    print("5️⃣  FORMATIONS RÉCENTES ET DOCUMENTS ASSOCIÉS")
    print("=" * 70)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Récupérer les 5 dernières formations
        cur.execute("""
            SELECT
                f.id,
                f.operateur_id,
                f.intitule,
                f.date_debut,
                p.nom,
                p.prenom,
                (SELECT COUNT(*)
                 FROM documents d
                 WHERE d.formation_id = f.id) as nb_documents
            FROM formation f
            JOIN personnel p ON f.operateur_id = p.id
            ORDER BY f.date_creation DESC
            LIMIT 5
        """)

        formations = cur.fetchall()

        if not formations:
            print("\n   Aucune formation trouvée")
            return

        print(f"\n📚 5 dernières formations:")

        for formation in formations:
            print(f"\n   Formation ID {formation['id']}")
            print(f"   Personnel: {formation['nom']} {formation['prenom']} (ID: {formation['operateur_id']})")
            print(f"   Intitulé: {formation['intitule']}")
            print(f"   Date début: {formation['date_debut']}")
            print(f"   Documents associés: {formation['nb_documents']}")

            # Récupérer les documents pour cette formation
            if formation['nb_documents'] > 0:
                cur.execute("""
                    SELECT id, nom_affichage, chemin_fichier
                    FROM documents
                    WHERE formation_id = %s
                """, (formation['id'],))

                docs = cur.fetchall()
                for doc in docs:
                    print(f"     → Document: {doc['nom_affichage']} (ID: {doc['id']})")
                    print(f"        Chemin: {doc['chemin_fichier']}")

    finally:
        cur.close()
        conn.close()

def main():
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "DIAGNOSTIC DES DOCUMENTS" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝\n")

    # 1. Vérifier la structure de la table
    table_ok = check_table_structure()

    # 2. Vérifier la vue
    view_ok = check_view_exists()

    # 3. Vérifier les documents en base
    check_documents_in_db()

    # 4. Vérifier les fichiers physiques
    check_file_paths()

    # 5. Vérifier les formations récentes
    check_recent_formations()

    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ DU DIAGNOSTIC")
    print("=" * 70)

    if not table_ok or not view_ok:
        print("\n❌ PROBLÈME DÉTECTÉ")
        print("   La table ou la vue n'est pas configurée correctement")
        print("\n🔧 SOLUTION:")
        print("   Exécutez: python scripts\\setup_documents_complete.py")
    else:
        print("\n✅ Configuration de base OK")
        print("\n💡 Si les documents ne s'affichent toujours pas:")
        print("   1. Vérifiez que formation_id est bien rempli (section 3 ci-dessus)")
        print("   2. Vérifiez que les fichiers existent physiquement (section 4)")
        print("   3. Rechargez l'interface de l'application (F5)")

    print("=" * 70)

if __name__ == "__main__":
    main()
