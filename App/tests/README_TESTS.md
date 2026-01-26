# Tests EMAC

Suite de tests complète pour l'application EMAC.

## Structure des tests

```
tests/
├── conftest.py              # Configuration pytest et fixtures partagées
├── run_all_tests.py         # Runner de tests principal
├── README_TESTS.md          # Cette documentation
├── unit/                    # Tests unitaires
│   ├── test_auth_service.py        # Tests authentification
│   ├── test_evaluation_service.py  # Tests évaluations
│   ├── test_contrat_service.py     # Tests contrats
│   ├── test_absence_service.py     # Tests absences
│   ├── test_logger.py              # Tests système de logging
│   └── test_rh_service.py          # Tests service RH
└── integration/             # Tests d'intégration
    └── test_database.py     # Tests connexion DB
```

## Installation des dépendances

```bash
pip install pytest pytest-cov
```

## Exécution des tests

### Tous les tests unitaires
```bash
cd App
python -m pytest tests/ -v
# ou
python tests/run_all_tests.py
```

### Tests d'un service spécifique
```bash
python -m pytest tests/unit/test_auth_service.py -v
python -m pytest tests/unit/test_evaluation_service.py -v
python -m pytest tests/unit/test_contrat_service.py -v
```

### Tests avec couverture de code
```bash
python -m pytest tests/ --cov=core --cov-report=html -v
# Le rapport HTML sera dans htmlcov/
```

### Tests d'intégration (nécessite DB configurée)
```bash
python -m pytest tests/integration/ -v -m integration
```

### Tests rapides (exclut l'intégration)
```bash
python -m pytest tests/ -v -m "not integration"
```

### Filtre par nom de test
```bash
python -m pytest tests/ -v -k "test_password"
python -m pytest tests/ -v -k "test_auth"
```

## Couverture des tests

### Services testés

| Service | Fichier de test | Couverture |
|---------|-----------------|------------|
| auth_service.py | test_auth_service.py | Validation mdp, hash, session, permissions, CRUD utilisateurs |
| evaluation_service.py | test_evaluation_service.py | Évaluations en retard, à venir, mise à jour, statistiques |
| contrat_service.py | test_contrat_service.py | CRUD contrats, validation dates/ETP, expiration, statistiques |
| absence_service.py | test_absence_service.py | Jours ouvrés, soldes congés, demandes, validation |
| logger.py | test_logger.py | Audit trail, formatage JSON, gestion erreurs |
| rh_service.py | test_rh_service.py | Recherche opérateurs, données par domaine |
| configbd.py | test_database.py | Connexions, pool, context managers |

### Nombre de tests par catégorie

- **Authentification** : ~40 tests
- **Évaluations** : ~25 tests
- **Contrats** : ~35 tests
- **Absences** : ~30 tests
- **Logging/Audit** : ~25 tests
- **Service RH** : ~20 tests
- **Base de données** : ~15 tests

**Total** : ~190 tests

## Fixtures disponibles (conftest.py)

### Mocks base de données
- `mock_db_connection` : Mock de connexion + curseur
- `mock_get_connection` : Patch de get_connection()
- `mock_database_cursor` : Mock du context manager DatabaseCursor
- `mock_database_connection` : Mock du context manager DatabaseConnection

### Données de test
- `sample_user` : Utilisateur de test
- `sample_operator` : Opérateur de test
- `sample_poste` : Poste de test
- `sample_polyvalence` : Enregistrement polyvalence
- `sample_contract` : Contrat CDI
- `sample_contract_cdd` : Contrat CDD avec date de fin
- `sample_absence_request` : Demande d'absence
- `sample_evaluation_overdue` : Évaluation en retard
- `sample_evaluation_upcoming` : Évaluation à venir

### Sessions
- `mock_user_session` : Session admin connecté
- `mock_non_admin_session` : Session utilisateur standard

### Logging
- `mock_log_hist` : Mock de log_hist()
- `mock_log_hist_async` : Mock de log_hist_async()

## Conventions de tests

### Nommage
- Classes : `TestNomFonctionnalite`
- Méthodes : `test_description_du_cas`

### Structure d'un test
```python
def test_example(self, mock_cursor_class):
    """Description claire du test"""
    # Arrange - préparation des mocks
    mock_cursor = MagicMock()
    mock_cursor_class.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor_class.return_value.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = [{'id': 1}]

    # Act - appel de la fonction testée
    result = ma_fonction()

    # Assert - vérification des résultats
    assert len(result) == 1
```

### Tests paramétrés
```python
@pytest.mark.parametrize("niveau", [1, 2, 3, 4])
def test_niveaux_valides(self, niveau):
    """Test tous les niveaux valides"""
    result = valider_niveau(niveau)
    assert result is True
```

## Bonnes pratiques

1. **Isolation** : Chaque test doit être indépendant
2. **Mocking** : Mocker la DB pour les tests unitaires
3. **Clarté** : Un test = une assertion principale
4. **Nommage** : Noms de tests descriptifs
5. **Couverture** : Viser 80%+ de couverture
6. **Performance** : Les tests unitaires doivent être rapides (< 1s chacun)

## CI/CD

Pour intégrer dans un pipeline CI/CD :

```yaml
test:
  script:
    - pip install -r requirements.txt
    - pip install pytest pytest-cov
    - cd App
    - python -m pytest tests/ -v --junitxml=test-results.xml --cov=core --cov-report=xml
  artifacts:
    reports:
      junit: App/test-results.xml
      coverage: App/coverage.xml
```

## Dépannage

### ImportError: No module named 'core'
Assurez-vous d'être dans le répertoire `App/` avant d'exécuter les tests.

### Tests d'intégration échouent
Vérifiez que :
1. Le fichier `.env` est configuré avec le mot de passe DB
2. MySQL est démarré
3. La base de données `emac_db` existe

### Tests trop lents
- Utilisez `-x` pour arrêter au premier échec
- Filtrez avec `-k "pattern"`
- Exécutez uniquement les tests unitaires : `-m "not integration"`
