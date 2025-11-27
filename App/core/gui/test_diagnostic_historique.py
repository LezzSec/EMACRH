# SCRIPT DE DIAGNOSTIC CORRIGÉ - test_diagnostic_historique.py
# À exécuter depuis la racine de votre projet EMAC

import sys
import os

# Ajouter le chemin du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import corrigé - adaptez selon votre structure
try:
    from App.core.db.configbd import get_connection as get_db_connection
except ImportError:
    try:
        from core.db.configbd import get_connection as get_db_connection
    except ImportError:
        print("❌ ERREUR : Impossible d'importer get_db_connection")
        print("Vérifiez le chemin d'import dans votre projet")
        sys.exit(1)

from datetime import datetime
import json

def test_1_verifier_table_historique():
    """Test 1: Vérifier que la table historique existe et sa structure"""
    print("=" * 60)
    print("TEST 1 : STRUCTURE DE LA TABLE HISTORIQUE")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier que la table existe
        cursor.execute("SHOW TABLES LIKE 'historique'")
        if not cursor.fetchone():
            print("❌ ERREUR : La table 'historique' n'existe pas !")
            return False
        
        print("✅ La table 'historique' existe")
        
        # Vérifier la structure
        cursor.execute("DESCRIBE historique")
        columns = cursor.fetchall()
        
        print("\nColonnes de la table historique :")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        return False

def test_2_insertion_manuelle():
    """Test 2: Essayer d'insérer manuellement dans l'historique"""
    print("\n" + "=" * 60)
    print("TEST 2 : INSERTION MANUELLE DANS L'HISTORIQUE")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        description = json.dumps({
            "operateur": "TEST DIAGNOSTIC",
            "poste": "TEST",
            "niveau": 3,
            "type": "test"
        }, ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO historique (date_time, action, operateur_id, poste_id, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (datetime.now(), 'INSERT', 1, 1, description))
        
        conn.commit()
        print("✅ Insertion réussie !")
        
        # Vérifier que l'entrée existe
        cursor.execute("SELECT COUNT(*) FROM historique")
        count = cursor.fetchone()[0]
        print(f"✅ Nombre d'entrées dans l'historique : {count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ERREUR lors de l'insertion : {e}")
        import traceback
        traceback.print_exc()
        try:
            conn.rollback()
        except:
            pass
        return False

def test_3_verifier_cles_etrangeres():
    """Test 3: Vérifier les clés étrangères"""
    print("\n" + "=" * 60)
    print("TEST 3 : CLÉS ÉTRANGÈRES")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                CONSTRAINT_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = 'historique'
            AND TABLE_SCHEMA = DATABASE()
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        
        fks = cursor.fetchall()
        
        if not fks:
            print("⚠️  Aucune clé étrangère définie")
        else:
            print("Clés étrangères trouvées :")
            for fk in fks:
                print(f"  - {fk[0]}: {fk[1]} -> {fk[2]}.{fk[3]}")
                
                # Vérifier si c'est personnel ou operateurs
                if fk[2] == 'operateurs':
                    print(f"    ⚠️  ATTENTION : Référence 'operateurs' au lieu de 'personnel'")
                    print(f"    → Cela peut causer des erreurs si la table s'appelle maintenant 'personnel'")
                elif fk[2] == 'personnel':
                    print(f"    ✅ Référence correcte à 'personnel'")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        return False

def test_4_verifier_donnees_existantes():
    """Test 4: Vérifier les données dans l'historique"""
    print("\n" + "=" * 60)
    print("TEST 4 : DONNÉES EXISTANTES")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM historique")
        count = cursor.fetchone()[0]
        
        print(f"Nombre total d'entrées : {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT id, date_time, action, operateur_id, poste_id, 
                       LEFT(description, 100) as desc_short
                FROM historique
                ORDER BY date_time DESC
                LIMIT 5
            """)
            
            rows = cursor.fetchall()
            print("\nDernières entrées :")
            for row in rows:
                print(f"  ID: {row[0]}")
                print(f"  Date: {row[1]}")
                print(f"  Action: {row[2]}")
                print(f"  Opérateur ID: {row[3]}")
                print(f"  Poste ID: {row[4]}")
                print(f"  Description: {row[5] if len(row) > 5 else 'N/A'}")
                print("  " + "-" * 40)
        else:
            print("⚠️  L'historique est vide")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        return False

def test_5_verifier_personnel_et_postes():
    """Test 5: Vérifier que les tables personnel et postes existent"""
    print("\n" + "=" * 60)
    print("TEST 5 : TABLES PERSONNEL ET POSTES")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier personnel
        cursor.execute("SHOW TABLES LIKE 'personnel'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM personnel WHERE statut = 'ACTIF'")
            count = cursor.fetchone()[0]
            print(f"✅ Table 'personnel' existe - {count} opérateurs actifs")
            table_operateurs = 'personnel'
        else:
            cursor.execute("SHOW TABLES LIKE 'operateurs'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM operateurs WHERE statut = 'ACTIF'")
                count = cursor.fetchone()[0]
                print(f"⚠️  Table 'operateurs' existe (ancienne version) - {count} opérateurs actifs")
                table_operateurs = 'operateurs'
            else:
                print("❌ Aucune table pour les opérateurs !")
                return False
        
        # Vérifier postes
        cursor.execute("SHOW TABLES LIKE 'postes'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM postes WHERE visible = 1")
            count = cursor.fetchone()[0]
            print(f"✅ Table 'postes' existe - {count} postes visibles")
        else:
            print("❌ Table 'postes' n'existe pas !")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_6_simuler_save_changes():
    """Test 6: Simuler ce que fait save_changes()"""
    print("\n" + "=" * 60)
    print("TEST 6 : SIMULATION DE SAVE_CHANGES()")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Déterminer quelle table utiliser
        cursor.execute("SHOW TABLES LIKE 'personnel'")
        if cursor.fetchone():
            table_name = 'personnel'
        else:
            table_name = 'operateurs'
        
        print(f"Utilisation de la table : {table_name}")
        
        # Récupérer un opérateur et un poste
        cursor.execute(f"SELECT id, nom, prenom FROM {table_name} WHERE statut = 'ACTIF' LIMIT 1")
        operateur = cursor.fetchone()
        
        if not operateur:
            print("❌ Aucun opérateur trouvé")
            return False
        
        cursor.execute("SELECT id, poste_code FROM postes WHERE visible = 1 LIMIT 1")
        poste = cursor.fetchone()
        
        if not poste:
            print("❌ Aucun poste trouvé")
            return False
        
        operateur_id = operateur[0]
        operateur_nom = f"{operateur[2]} {operateur[1]}"
        poste_id = poste[0]
        poste_code = poste[1]
        
        print(f"Test avec : {operateur_nom} (ID: {operateur_id}) sur poste {poste_code} (ID: {poste_id})")
        
        # Vérifier niveau actuel
        cursor.execute("""
            SELECT niveau FROM polyvalence 
            WHERE operateur_id = %s AND poste_id = %s
        """, (operateur_id, poste_id))
        
        existing = cursor.fetchone()
        if existing:
            old_niveau = existing[0]
            new_niveau = (old_niveau % 4) + 1  # Changer le niveau
            action = 'UPDATE'
            print(f"Niveau actuel : {old_niveau}, nouveau : {new_niveau}")
        else:
            old_niveau = None
            new_niveau = 2
            action = 'INSERT'
            print(f"Aucun niveau existant, création avec niveau {new_niveau}")
        
        # Construire la description
        if action == 'INSERT':
            description = json.dumps({
                "operateur": operateur_nom,
                "poste": poste_code,
                "niveau": new_niveau,
                "type": "ajout"
            }, ensure_ascii=False)
        else:
            description = json.dumps({
                "operateur": operateur_nom,
                "poste": poste_code,
                "changes": {"niveau": {"old": old_niveau, "new": new_niveau}},
                "type": "modification"
            }, ensure_ascii=False)
        
        print(f"Description JSON : {description[:80]}...")
        
        # Tester l'insertion dans historique
        print("\nTentative d'insertion dans l'historique...")
        cursor.execute("""
            INSERT INTO historique (date_time, action, operateur_id, poste_id, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (datetime.now(), action, operateur_id, poste_id, description))
        
        conn.commit()
        print("✅ Insertion dans l'historique réussie !")
        
        # Vérifier
        cursor.execute("SELECT COUNT(*) FROM historique")
        count = cursor.fetchone()[0]
        print(f"✅ Total d'entrées maintenant : {count}")
        
        # Afficher la dernière entrée
        cursor.execute("""
            SELECT id, date_time, action, description
            FROM historique
            ORDER BY date_time DESC
            LIMIT 1
        """)
        last_entry = cursor.fetchone()
        print(f"\nDernière entrée créée :")
        print(f"  ID: {last_entry[0]}")
        print(f"  Date: {last_entry[1]}")
        print(f"  Action: {last_entry[2]}")
        print(f"  Description: {last_entry[3][:100]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        try:
            conn.rollback()
        except:
            pass
        return False

# ============================================================================
# EXÉCUTION DE TOUS LES TESTS
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "DIAGNOSTIC HISTORIQUE" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    results = []
    
    results.append(("Structure table", test_1_verifier_table_historique()))
    results.append(("Insertion manuelle", test_2_insertion_manuelle()))
    results.append(("Clés étrangères", test_3_verifier_cles_etrangeres()))
    results.append(("Données existantes", test_4_verifier_donnees_existantes()))
    results.append(("Tables personnel/postes", test_5_verifier_personnel_et_postes()))
    results.append(("Simulation save_changes", test_6_simuler_save_changes()))
    
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ OK" if result else "❌ ÉCHEC"
        print(f"{test_name:.<40} {status}")
    
    print("\n" + "=" * 60)
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("✅ TOUS LES TESTS SONT PASSÉS !")
        print("\n📋 PROCHAINES ÉTAPES :")
        print("1. L'historique fonctionne au niveau de la base de données")
        print("2. Vérifiez que save_changes() dans liste_et_grilles.py utilise bien le code modifié")
        print("3. Redémarrez complètement votre application")
        print("4. Faites une modification et sauvegardez")
        print("5. Ouvrez l'historique pour voir le résultat")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("\nRegardez les erreurs ci-dessus pour identifier le problème.")
    
    print("=" * 60 + "\n")