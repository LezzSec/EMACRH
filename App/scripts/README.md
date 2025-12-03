# Scripts Utilitaires EMAC

Ce répertoire contient les scripts utilitaires pour la maintenance et l'administration de l'application EMAC.

## Scripts disponibles

### Maintenance de la base de données

- **cleanup_test_data.py** - Nettoie les données de test de la base de données
- **delete_operators.py** - Supprime des opérateurs spécifiques
- **quick_db_query.py** - Exécute des requêtes SQL rapides pour le diagnostic

### Installation et migration

- **install_absences_module.py** - Installe le module de gestion des absences
- **fix_matricule_lowercase.py** - Corrige les matricules en minuscules

## Utilisation

```bash
# Depuis la racine du projet
cd App

# Exécuter un script
py scripts/cleanup_test_data.py
py scripts/quick_db_query.py
```

## Notes importantes

⚠️ **Attention** : Ces scripts modifient directement la base de données. Toujours faire une sauvegarde avant de les exécuter en production.

Les scripts utilisent la configuration de base de données définie dans `core/db/configbd.py`.
