# Tests EMAC - Documentation

## Vue d'ensemble

Cette suite de tests complète valide tous les aspects critiques de l'application EMAC, incluant:
- Système d'évaluation et polyvalence
- Gestion des contrats
- Audit logging (historique)
- Intégrité de la base de données
- Gestion du personnel

## Exécution des tests

### Exécuter tous les tests

```bash
cd App
py tests/run_all_tests.py
```

### Options disponibles

```bash
# Mode verbeux (affiche tous les détails)
py tests/run_all_tests.py --verbose

# Exécuter une suite spécifique
py tests/run_all_tests.py --suite=evaluation
py tests/run_all_tests.py --suite=contrat
py tests/run_all_tests.py --suite=audit

# Exporter le rapport dans un fichier
py tests/run_all_tests.py --export
```

### Exécuter un test individuel

```bash
cd App
py tests/test_evaluation_system_advanced.py
py tests/test_contrat_management_advanced.py
py tests/test_audit_logging_advanced.py
```

## Suites de tests

### 1. Tests d'intégration (`integration`)

**Fichier:** `test_integration_complete.py`

Tests de base pour vérifier le bon fonctionnement global:
- Connexion à la base de données
- Pool de connexions
- Opérations CRUD sur les opérateurs
- Gestion de la polyvalence
- Évaluations en retard
- Changement de statut

**Couverture:** ~13 tests
**Durée:** ~5-10 secondes

---

### 2. Système d'évaluation (`evaluation`)

**Fichier:** `test_evaluation_system_advanced.py`

Tests complets du système d'évaluation et de polyvalence:

#### Tests des niveaux (1-4)
- Niveau 1: évaluation initiale (1 an)
- Niveau 2: progression (2 ans)
- Niveau 3: maîtrise (5 ans)
- Niveau 4: expert/formateur (10 ans)

#### Tests des retards
- Détection des évaluations expirées
- Calcul des jours de retard
- Tri par urgence

#### Tests des prochaines évaluations
- Évaluations dans les 30 jours
- Évaluations dans les 90 jours

#### Tests de cohérence
- Dates chronologiques
- Niveaux valides (1-4)
- Filtrage opérateurs ACTIF

#### Tests de performance
- Récupération évaluations en retard (< 2s)
- Récupération prochaines évaluations (< 2s)
- Requêtes multi-opérateurs (< 3s)

#### Edge cases
- Évaluation le jour même
- Évaluation future lointaine (10 ans)
- Multiple polyvalences par opérateur

**Couverture:** ~30 tests
**Durée:** ~15-20 secondes

---

### 3. Gestion des contrats (`contrat`)

**Fichier:** `test_contrat_management_advanced.py`

Tests complets de la gestion des contrats:

#### Tests CRUD
- Création CDI (sans date_fin)
- Création CDD (avec date_fin)
- Création INTERIM (durée courte)
- Lecture et modification

#### Tests de validation
- Dates cohérentes (date_fin >= date_debut)
- ETP valide (0-1)
- Type de contrat valide
- Date_debut obligatoire

#### Tests expiration et alertes
- Détection contrats expirés
- Calcul jours restants
- Alerte urgente (< 7 jours)
- Alerte (< 30 jours)
- Info (30-90 jours)

#### Tests métier
- Renouvellement CDD
- Passage CDD vers CDI
- Historique des contrats
- Contrats multiples (séquentiels)

#### Tests de performance
- Liste tous les contrats (< 2s)
- Contrats expirant bientôt (< 2s)
- Statistiques par type (< 1s)

#### Edge cases
- Contrat sans ETP
- Contrat avec date_debut future
- Contrat très long (> 10 ans)
- Contrat expirant aujourd'hui

**Couverture:** ~35 tests
**Durée:** ~20-25 secondes

---

### 4. Audit et logging (`audit`)

**Fichier:** `test_audit_logging_advanced.py`

Tests du système d'audit et traçabilité:

#### Tests basiques
- Logging simple
- Logging avec operateur_id
- Logging avec poste_id
- Logging complet
- Description longue (> 255 caractères)

#### Tests de structure
- Timestamp automatique
- Champ action obligatoire
- Contraintes de clés étrangères

#### Tests de requêtes
- Filtrage par action
- Filtrage par opérateur
- Filtrage par poste
- Filtrage par période
- Tri chronologique

#### Tests de traçabilité métier
- Ajout opérateur
- Modification polyvalence
- Soft delete
- Changement de statut

#### Tests de performance
- Insertion rapide (100 logs < 5s)
- Requête historique complet (< 2s)
- Requête avec filtres (< 1s)
- Agrégations statistiques (< 2s)

#### Tests de sécurité
- Logs immuables
- Cascade delete operateur
- Cascade delete poste

#### Tests statistiques
- Actions par type
- Activité par opérateur
- Activité par jour

**Couverture:** ~40 tests
**Durée:** ~20-30 secondes

---

### 5. Intégrité base de données (`database`)

**Fichier:** `test_database_integrity.py`

Tests d'intégrité et contraintes:
- Contraintes de clés étrangères
- Contraintes UNIQUE
- Valeurs NULL
- Types de données
- Indexes et performances

**Couverture:** Variable selon le fichier existant
**Durée:** ~10-15 secondes

---

### 6. Gestion du personnel (`personnel`)

**Fichiers:**
- `test_add_operateur.py`
- `test_masquage_operateur.py`
- `test_personnel_non_production.py`
- `test_matricule_service.py`

Tests de gestion des opérateurs:
- Ajout d'opérateurs
- Masquage (soft delete)
- Personnel non-production
- Génération et validation des matricules

**Couverture:** Variable
**Durée:** ~10-20 secondes

---

## Statistiques globales

### Couverture totale estimée
- **Nombre total de tests:** ~150+
- **Durée totale:** 1-2 minutes
- **Lignes de code de test:** ~5000+

### Domaines couverts
✅ Système d'évaluation et polyvalence
✅ Gestion des contrats
✅ Audit logging (historique)
✅ Intégrité base de données
✅ Gestion du personnel
✅ Performance des requêtes
✅ Edge cases et cas limites
✅ Validation métier

## Interprétation des résultats

### Code de sortie
- `0`: Tous les tests sont passés
- `1`: Au moins un test a échoué

### Statuts possibles
- `OK` ✓: Test réussi
- `FAIL` ✗: Test échoué
- `SKIP` ⊘: Test ignoré (fichier manquant, condition non remplie)
- `TIMEOUT` ⏱: Test trop long (> 5 minutes)
- `ERROR` ⚠: Erreur d'exécution

### Taux de réussite attendu
- **Production:** 100% (tous les tests doivent passer)
- **Développement:** >= 95% (quelques tests peuvent être en cours)

## Structure d'un test

Chaque test suit cette structure:

```python
class TestXXXAdvanced:
    def __init__(self):
        self.test_data = []
        self.successes = []
        self.failures = []

    def run_all_tests(self):
        """Exécute tous les tests."""
        tests = [
            ("Description test 1", self.test_1),
            ("Description test 2", self.test_2),
            # ...
        ]

        for test_name, test_func in tests:
            self._run_test(test_name, test_func)

        self._print_summary()

    def _run_test(self, name, func):
        """Exécute un test individuel."""
        try:
            func()
            self.successes.append(name)
            print(f"   ✓ SUCCÈS")
        except Exception as e:
            self.failures.append((name, str(e)))
            print(f"   ✗ ÉCHEC: {e}")

    def test_cleanup(self):
        """Nettoyage des données de test."""
        # Suppression des données créées
        pass
```

## Bonnes pratiques

### 1. Isolation des tests
- Chaque test crée ses propres données
- Nettoyage obligatoire en fin de test
- Pas de dépendances entre tests

### 2. Données de test
- Préfixer les données: `TEST_*`
- Utiliser timestamps pour unicité
- Nettoyer systématiquement

### 3. Assertions claires
```python
# ✓ Bon
assert count == 5, f"Attendu 5, obtenu {count}"

# ✗ Mauvais
assert count == 5
```

### 4. Performance
- Tests unitaires: < 1s
- Tests d'intégration: < 5s
- Tests complets: < 30s

### 5. Messages informatifs
```python
print(f"   > {count} enregistrements trouvés")
print(f"   > Durée: {elapsed:.3f}s")
```

## Maintenance

### Ajout d'un nouveau test

1. Créer le fichier: `test_nouveau_module.py`
2. Suivre la structure standard
3. Ajouter dans `run_all_tests.py`:

```python
self.test_suites = {
    # ...
    'nouveau': {
        'name': 'Nouveau module',
        'files': ['test_nouveau_module.py'],
        'description': 'Tests du nouveau module'
    }
}
```

### Mise à jour d'un test existant

1. Modifier le fichier de test
2. Vérifier que le nettoyage fonctionne
3. Exécuter la suite complète
4. Mettre à jour la documentation si nécessaire

## Dépannage

### Échec de connexion à la base

**Erreur:** `Can't connect to MySQL server`

**Solution:**
1. Vérifier que MySQL est démarré
2. Vérifier les identifiants dans `configbd.py`
3. Vérifier que la base `emac_db` existe

### Timeout lors des tests

**Erreur:** `Test timeout après 5 minutes`

**Solution:**
1. Vérifier les performances de la base
2. Optimiser les requêtes lentes
3. Augmenter le timeout dans `run_all_tests.py` si nécessaire

### Données de test non nettoyées

**Problème:** Les tests créent des données qui restent en base

**Solution:**
1. Vérifier que `test_cleanup()` est bien appelé
2. Exécuter manuellement le nettoyage:

```sql
DELETE FROM personnel WHERE nom LIKE 'TEST_%';
DELETE FROM historique WHERE action LIKE 'TEST_%';
```

### Tests qui échouent sporadiquement

**Problème:** Un test passe parfois, échoue parfois

**Causes possibles:**
1. Problèmes de timing (race conditions)
2. Données résiduelles d'un test précédent
3. État de la base non déterministe

**Solution:**
1. Améliorer l'isolation des tests
2. Ajouter des `time.sleep()` si nécessaire
3. Nettoyer plus agressivement

## Intégration continue

Pour intégrer ces tests dans un pipeline CI/CD:

```bash
# Dans votre script CI
cd App
python tests/run_all_tests.py --export

# Le code de sortie indique le succès (0) ou l'échec (1)
```

### GitHub Actions exemple

```yaml
name: Tests EMAC

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v2

    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Run tests
      run: |
        cd App
        python tests/run_all_tests.py --verbose --export

    - name: Upload test report
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: test-report
        path: App/tests/test_report.txt
```

## Contact et support

Pour toute question sur les tests:
1. Consulter ce README
2. Examiner le code source des tests
3. Vérifier les logs de sortie des tests

## Licence

Ces tests font partie du projet EMAC et suivent la même licence.
