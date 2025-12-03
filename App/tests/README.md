# Tests EMAC

Ce répertoire contient tous les tests pour l'application EMAC.

## Tests disponibles

- **test_add_operateur.py** - Tests d'ajout d'opérateurs
- **test_advanced.py** - Tests avancés de fonctionnalités
- **test_database_integrity.py** - Tests d'intégrité de la base de données
- **test_masquage_operateur.py** - Tests de masquage/désactivation d'opérateurs
- **test_matricule_service.py** - Tests du service de gestion des matricules
- **test_personnel_non_production.py** - Tests du personnel hors production

## Exécution des tests

```bash
# Depuis la racine du projet
cd App

# Exécuter un test spécifique
py tests/test_database_integrity.py

# Ou avec pytest (si installé)
pytest tests/
```

## Conventions

- Tous les fichiers de test commencent par `test_`
- Les tests utilisent la connexion MySQL définie dans `core/db/configbd.py`
- Nettoyer les données de test après chaque exécution avec `scripts/cleanup_test_data.py`
