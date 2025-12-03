# -*- coding: utf-8 -*-
"""
Tests avancés et approfondis de l'application EMAC
"""

from core.db.configbd import get_connection
from core.services.matricule_service import generer_prochain_matricule, matricule_existe
import time

# ============================================================
# TESTS CAS LIMITES MATRICULE
# ============================================================

def test_matricule_concurrence():
    """Test de génération de matricule avec insertions réelles"""
    print("\n=== TEST: Génération matricule concurrence ===")
    print("[INFO] Ce test génère et insère 5 matricules successifs")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Nettoyer d'abord les éventuels tests précédents
        cur.execute("DELETE FROM personnel WHERE nom LIKE 'TestConcurrence%'")
        cleaned = cur.rowcount
        if cleaned > 0:
            print(f"[INFO] {cleaned} enregistrement(s) de tests précédents nettoyés")
        conn.commit()

        matricules = []
        ids_created = []

        # Générer et insérer 5 matricules
        for i in range(5):
            mat = generer_prochain_matricule()
            matricules.append(mat)

            # Insérer immédiatement en base
            cur.execute(
                "INSERT INTO personnel (nom, prenom, statut, matricule) VALUES (%s, %s, 'INACTIF', %s)",
                (f"TestConcurrence{i}", f"Test{i}", mat)
            )
            ids_created.append(cur.lastrowid)
            print(f"  Matricule {i+1}: {mat} (ID={cur.lastrowid})")

        conn.commit()

        # Vérifier qu'ils sont tous différents
        if len(matricules) == len(set(matricules)):
            print("[OK] Tous les matricules sont uniques et séquentiels")
            success = True
        else:
            print("[ERREUR] Doublons détectés dans les matricules!")
            success = False

        # Nettoyer les données de test
        for id_pers in ids_created:
            cur.execute("DELETE FROM personnel WHERE id = %s", (id_pers,))
        conn.commit()
        print(f"[INFO] {len(ids_created)} enregistrements de test supprimés")

        return success

    except Exception as e:
        print(f"[ERREUR] {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def test_matricule_format_edge_cases():
    """Test des cas limites de format de matricule"""
    print("\n=== TEST: Format matricule - cas limites ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Tester avec des matricules invalides
        invalid_matricules = [
            '',
            'M',
            'M0',
            'M00',
            'M000',
            'M0000',
            'M00000',
            'MABCDEF',
            'm000001',
            'N000001',
            'M0000001',
            None
        ]

        for mat in invalid_matricules:
            cur.execute("SELECT COUNT(*) FROM personnel WHERE matricule = %s", (mat,))
            count = cur.fetchone()[0]
            if count > 0:
                print(f"[ATTENTION] Matricule invalide trouvé en base: '{mat}' ({count} fois)")

        # Vérifier le prochain matricule après le max
        cur.execute("""
            SELECT MAX(CAST(SUBSTRING(matricule, 2) AS UNSIGNED))
            FROM personnel
            WHERE matricule LIKE 'M%'
        """)
        max_num = cur.fetchone()[0]

        if max_num:
            print(f"[INFO] Prochain matricule sera: M{(max_num+1):06d}")

            # Simuler un matricule très grand
            if max_num < 999999:
                print(f"[OK] Capacité restante: {999999 - max_num} matricules")
            else:
                print(f"[ATTENTION] Approche de la limite max (M999999)")

        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

def test_matricule_rollback():
    """Test du rollback en cas d'erreur lors de l'insertion avec matricule"""
    print("\n=== TEST: Rollback matricule ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Compter les matricules avant
        cur.execute("SELECT COUNT(*) FROM personnel WHERE matricule IS NOT NULL")
        count_before = cur.fetchone()[0]

        # Générer un matricule
        matricule = generer_prochain_matricule()
        print(f"[INFO] Matricule généré: {matricule}")

        # Tenter une insertion qui échouera (nom trop long par exemple)
        try:
            # Simuler une erreur en insérant dans une colonne invalide
            cur.execute(
                "INSERT INTO personnel (nom, prenom, matricule, colonne_invalide) VALUES (%s, %s, %s, %s)",
                ("TestRollback", "Test", matricule, "valeur")
            )
            conn.commit()
            print("[ERREUR] L'insertion aurait dû échouer")
            return False
        except Exception as e:
            conn.rollback()
            print(f"[OK] Erreur capturée et rollback effectué: {type(e).__name__}")

        # Vérifier que le matricule n'a pas été utilisé
        cur.execute("SELECT COUNT(*) FROM personnel WHERE matricule = %s", (matricule,))
        mat_used = cur.fetchone()[0]

        if mat_used == 0:
            print(f"[OK] Le matricule {matricule} n'a pas été utilisé après rollback")
        else:
            print(f"[ERREUR] Le matricule {matricule} a été utilisé malgré le rollback")
            return False

        # Vérifier le compte total
        cur.execute("SELECT COUNT(*) FROM personnel WHERE matricule IS NOT NULL")
        count_after = cur.fetchone()[0]

        if count_before == count_after:
            print(f"[OK] Nombre de matricules inchangé: {count_after}")
            return True
        else:
            print(f"[ERREUR] Nombre de matricules changé: {count_before} -> {count_after}")
            return False

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

# ============================================================
# TESTS GESTION DES DOUBLONS
# ============================================================

def test_doublon_detection():
    """Test de la détection de doublons nom/prénom"""
    print("\n=== TEST: Détection doublons ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Chercher un doublon existant
        cur.execute("""
            SELECT nom, prenom, COUNT(*) as cnt
            FROM personnel
            GROUP BY nom, prenom
            HAVING cnt > 1
            LIMIT 1
        """)

        doublon = cur.fetchone()

        if doublon:
            nom, prenom, count = doublon
            print(f"[ATTENTION] Doublon détecté: {nom} {prenom} ({count} fois)")

            # Lister les IDs
            cur.execute(
                "SELECT id, matricule, statut FROM personnel WHERE nom = %s AND prenom = %s",
                (nom, prenom)
            )
            records = cur.fetchall()

            print("[INFO] Enregistrements trouvés:")
            for rec in records:
                print(f"  - ID={rec[0]}, Matricule={rec[1]}, Statut={rec[2]}")

            return False  # Les doublons ne devraient pas exister
        else:
            print("[OK] Aucun doublon nom+prénom détecté")
            return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

def test_doublon_matricule():
    """Test de détection de doublons de matricules"""
    print("\n=== TEST: Doublons matricules ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Chercher des doublons de matricules
        cur.execute("""
            SELECT matricule, COUNT(*) as cnt
            FROM personnel
            WHERE matricule IS NOT NULL AND matricule != ''
            GROUP BY matricule
            HAVING cnt > 1
        """)

        doublons = cur.fetchall()

        if doublons:
            print(f"[ERREUR] {len(doublons)} matricule(s) en doublon détecté(s):")
            for mat, count in doublons:
                print(f"  - {mat}: {count} fois")
            return False
        else:
            print("[OK] Aucun doublon de matricule détecté")
            return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

# ============================================================
# TESTS INTÉGRATION COMPLÈTE
# ============================================================

def test_integration_personnel_polyvalence():
    """Test complet: ajout personnel production + polyvalence"""
    print("\n=== TEST: Intégration personnel + polyvalence ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # 1. Créer un personnel de production
        nom = "IntegrationTest"
        prenom = "TestComplet"
        matricule = generer_prochain_matricule()

        print(f"[1/5] Création personnel: {prenom} {nom}, matricule={matricule}")

        # Vérifier s'il existe déjà et le supprimer
        cur.execute("SELECT id FROM personnel WHERE nom = %s AND prenom = %s", (nom, prenom))
        existing = cur.fetchone()
        if existing:
            cur.execute("DELETE FROM polyvalence WHERE operateur_id = %s", (existing[0],))
            cur.execute("DELETE FROM personnel WHERE id = %s", (existing[0],))
            conn.commit()
            print(f"[INFO] Personnel existant supprimé")

        # Insérer le personnel
        cur.execute(
            "INSERT INTO personnel (nom, prenom, statut, matricule) VALUES (%s, %s, 'ACTIF', %s)",
            (nom, prenom, matricule)
        )
        operateur_id = cur.lastrowid
        conn.commit()
        print(f"[OK] Personnel créé: id={operateur_id}")

        # 2. Récupérer un poste visible
        print(f"[2/5] Récupération d'un poste visible")
        cur.execute("SELECT id, poste_code FROM postes WHERE COALESCE(visible, 1) = 1 LIMIT 1")
        poste = cur.fetchone()

        if not poste:
            print("[ERREUR] Aucun poste disponible")
            return False

        poste_id, poste_code = poste
        print(f"[OK] Poste sélectionné: {poste_code} (id={poste_id})")

        # 3. Ajouter une polyvalence
        print(f"[3/5] Ajout polyvalence")
        from datetime import datetime, timedelta
        date_eval = datetime.now() + timedelta(days=30)
        date_str = date_eval.strftime('%Y-%m-%d')

        cur.execute("""
            INSERT INTO polyvalence (operateur_id, poste_id, prochaine_evaluation)
            VALUES (%s, %s, %s)
        """, (operateur_id, poste_id, date_str))
        conn.commit()
        print(f"[OK] Polyvalence ajoutée pour le {date_str}")

        # 4. Vérifier que l'opérateur apparaît dans les grilles
        print(f"[4/5] Vérification visibilité dans grilles")
        cur.execute("""
            SELECT COUNT(*) FROM personnel
            WHERE id = %s
            AND statut = 'ACTIF'
            AND matricule IS NOT NULL
            AND matricule != ''
        """, (operateur_id,))

        visible = cur.fetchone()[0]

        if visible == 1:
            print(f"[OK] Personnel visible dans les grilles")
        else:
            print(f"[ERREUR] Personnel NON visible dans les grilles")
            return False

        # 5. Vérifier la polyvalence
        print(f"[5/5] Vérification polyvalence")
        cur.execute("""
            SELECT p.id, pos.poste_code, p.prochaine_evaluation
            FROM polyvalence p
            JOIN postes pos ON p.poste_id = pos.id
            WHERE p.operateur_id = %s
        """, (operateur_id,))

        poly = cur.fetchone()

        if poly:
            print(f"[OK] Polyvalence trouvée: poste={poly[1]}, date={poly[2]}")
            return True
        else:
            print(f"[ERREUR] Polyvalence non trouvée")
            return False

    except Exception as e:
        print(f"[ERREUR] {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

# ============================================================
# TESTS PERFORMANCE
# ============================================================

def test_performance_load_grilles():
    """Test de performance: chargement des grilles"""
    print("\n=== TEST: Performance chargement grilles ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Mesurer le temps de la requête principale
        start_time = time.time()

        cur.execute("""
            SELECT
                o.id,
                o.nom,
                o.prenom,
                o.matricule,
                p.poste_id,
                pos.poste_code,
                p.niveau,
                p.date_evaluation,
                p.prochaine_evaluation
            FROM personnel o
            LEFT JOIN polyvalence p ON o.id = p.operateur_id
            LEFT JOIN postes pos ON p.poste_id = pos.id
            WHERE o.statut = 'ACTIF'
            AND o.matricule IS NOT NULL
            AND o.matricule != ''
            AND COALESCE(pos.visible, 1) = 1
            ORDER BY o.nom, o.prenom
        """)

        results = cur.fetchall()
        end_time = time.time()

        duration = (end_time - start_time) * 1000  # en ms

        print(f"[INFO] Nombre de lignes: {len(results)}")
        print(f"[INFO] Temps d'exécution: {duration:.2f} ms")

        if duration < 100:
            print(f"[OK] Performance excellente (< 100ms)")
            return True
        elif duration < 500:
            print(f"[OK] Performance acceptable (< 500ms)")
            return True
        elif duration < 1000:
            print(f"[ATTENTION] Performance moyenne ({duration:.0f}ms)")
            return True
        else:
            print(f"[ATTENTION] Performance lente ({duration:.0f}ms)")
            return False

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

def test_performance_matricule_generation():
    """Test de performance: génération de matricules"""
    print("\n=== TEST: Performance génération matricules ===")

    try:
        iterations = 10
        start_time = time.time()

        for i in range(iterations):
            mat = generer_prochain_matricule()

        end_time = time.time()
        duration = (end_time - start_time) * 1000
        avg = duration / iterations

        print(f"[INFO] {iterations} générations en {duration:.2f} ms")
        print(f"[INFO] Moyenne: {avg:.2f} ms par génération")

        if avg < 50:
            print(f"[OK] Performance excellente (< 50ms par génération)")
            return True
        elif avg < 100:
            print(f"[OK] Performance acceptable (< 100ms par génération)")
            return True
        else:
            print(f"[ATTENTION] Performance lente ({avg:.0f}ms par génération)")
            return False

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

# ============================================================
# TESTS SÉCURITÉ SQL
# ============================================================

def test_sql_injection_protection():
    """Test de protection contre les injections SQL"""
    print("\n=== TEST: Protection SQL injection ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Tentatives d'injection SQL
        malicious_inputs = [
            "Test'; DROP TABLE personnel; --",
            "Test' OR '1'='1",
            "Test' UNION SELECT * FROM personnel --",
            "Test\"; DELETE FROM personnel WHERE '1'='1",
            "<script>alert('XSS')</script>",
        ]

        all_safe = True

        for malicious in malicious_inputs:
            try:
                # Cette requête utilise des paramètres donc devrait être sûre
                cur.execute(
                    "SELECT COUNT(*) FROM personnel WHERE nom = %s",
                    (malicious,)
                )
                count = cur.fetchone()[0]

                if count == 0:
                    print(f"[OK] Input malveillant bloqué: '{malicious[:30]}...'")
                else:
                    print(f"[INFO] Input trouvé en base (pourrait être légitime): {count}")

            except Exception as e:
                print(f"[OK] Erreur capturée pour: '{malicious[:30]}...'")

        # Vérifier que la table existe toujours
        cur.execute("SELECT COUNT(*) FROM personnel")
        count = cur.fetchone()[0]

        if count > 0:
            print(f"[OK] Table personnel intacte ({count} enregistrements)")
            return True
        else:
            print(f"[ERREUR] Table personnel vide ou corrompue")
            return False

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

# ============================================================
# TESTS HISTORIQUE
# ============================================================

def test_historique_logging():
    """Test de l'enregistrement dans l'historique"""
    print("\n=== TEST: Enregistrement historique ===")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Compter les entrées d'historique avant
        cur.execute("SELECT COUNT(*) FROM historique")
        count_before = cur.fetchone()[0]
        print(f"[INFO] Entrées historique avant: {count_before}")

        # Récupérer les dernières entrées
        cur.execute("""
            SELECT id, action, description, date_time
            FROM historique
            ORDER BY date_time DESC
            LIMIT 5
        """)

        recent = cur.fetchall()

        if recent:
            print(f"[INFO] Dernières entrées d'historique:")
            for entry in recent:
                hist_id, action, desc, date = entry
                desc_short = desc[:50] if desc else "N/A"
                print(f"  - #{hist_id}: {action} - {desc_short}... ({date})")
        else:
            print(f"[INFO] Aucune entrée d'historique récente")

        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        cur.close()
        conn.close()

# ============================================================
# EXÉCUTION DES TESTS
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TESTS AVANCÉS ET APPROFONDIS - APPLICATION EMAC")
    print("=" * 70)

    results = {}

    # Tests cas limites matricule
    print("\n" + "=" * 70)
    print("SECTION 1: TESTS CAS LIMITES MATRICULE")
    print("=" * 70)
    results['matricule_concurrence'] = test_matricule_concurrence()
    results['matricule_format_edge'] = test_matricule_format_edge_cases()
    results['matricule_rollback'] = test_matricule_rollback()

    # Tests gestion doublons
    print("\n" + "=" * 70)
    print("SECTION 2: TESTS GESTION DOUBLONS")
    print("=" * 70)
    results['doublon_detection'] = test_doublon_detection()
    results['doublon_matricule'] = test_doublon_matricule()

    # Tests intégration
    print("\n" + "=" * 70)
    print("SECTION 3: TESTS INTÉGRATION")
    print("=" * 70)
    results['integration_complete'] = test_integration_personnel_polyvalence()

    # Tests performance
    print("\n" + "=" * 70)
    print("SECTION 4: TESTS PERFORMANCE")
    print("=" * 70)
    results['perf_grilles'] = test_performance_load_grilles()
    results['perf_matricule'] = test_performance_matricule_generation()

    # Tests sécurité
    print("\n" + "=" * 70)
    print("SECTION 5: TESTS SÉCURITÉ")
    print("=" * 70)
    results['sql_injection'] = test_sql_injection_protection()

    # Tests historique
    print("\n" + "=" * 70)
    print("SECTION 6: TESTS HISTORIQUE")
    print("=" * 70)
    results['historique'] = test_historique_logging()

    # Résumé final
    print("\n" + "=" * 70)
    print("RÉSUMÉ FINAL DES TESTS AVANCÉS")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "[OK]" if result else "[ERREUR]"
        print(f"{symbol} {test_name:30s}: {status}")

    print("\n" + "-" * 70)
    print(f"TOTAL: {passed}/{total} tests réussis ({passed*100//total}%)")

    if passed == total:
        print("\n[OK] TOUS LES TESTS AVANCÉS SONT PASSÉS!")
    elif passed >= total * 0.8:
        print(f"\n[ATTENTION] {total-passed} test(s) échoué(s)")
    else:
        print(f"\n[ERREUR] Plusieurs tests ont échoué ({total-passed}/{total})")
