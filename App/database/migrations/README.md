# Migrations Base de Données EMAC

Ce dossier contient les migrations SQL pour faire évoluer le schéma de la base de données.

## Liste des migrations

| # | Fichier | Description | Date | Status |
|---|---------|-------------|------|--------|
| 001 | `001_add_performance_indexes.sql` | Ajout de 29 index de performance | 2026-01-07 |  À appliquer |

## Comment appliquer une migration

### Méthode 1 : Via script Python (RECOMMANDÉ)

```bash
cd App/scripts
python apply_performance_indexes.py
```

### Méthode 2 : Via MySQL

```bash
mysql -u root -p emac_db < App/database/migrations/001_add_performance_indexes.sql
```

### Méthode 3 : Via un script d'application générique

```bash
cd App/scripts
python apply_migration.py 001_add_performance_indexes.sql
```

## Vérifier qu'une migration est appliquée

### Vérifier les index

```sql
-- Se connecter à MySQL
mysql -u root -p emac_db

-- Lister tous les index de performance
SELECT TABLE_NAME, INDEX_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'emac_db'
  AND INDEX_NAME LIKE 'idx_%'
ORDER BY TABLE_NAME, INDEX_NAME;
```

### Vérifier un index spécifique

```sql
SHOW INDEX FROM polyvalence;
```

## Bonnes pratiques

1. ✅ **Toujours tester** sur une base de développement avant la production
2. ✅ **Faire un backup** avant d'appliquer une migration
3. ✅ **Vérifier le résultat** après application
4. ✅ **Documenter** les changements dans ce README

## Structure d'une migration

```sql
-- =====================================================================
-- Migration XXX : Titre de la migration
-- Date : YYYY-MM-DD
-- Description : Ce que fait cette migration
-- =====================================================================

USE emac_db;

-- Commandes SQL ici
CREATE INDEX ...;
ALTER TABLE ...;

-- Vérification
SELECT ... FROM information_schema ...;
```

## Rollback (annuler une migration)

Pour annuler la migration 001 (supprimer les index) :

```sql
-- ATTENTION : Ceci va supprimer les gains de performance !
DROP INDEX idx_personnel_statut ON personnel;
DROP INDEX idx_personnel_matricule ON personnel;
-- ... etc pour tous les index
```

**Note** : Il est généralement déconseillé de supprimer les index une fois créés.

## Impact des migrations

### Migration 001 - Index de performance

**Gains attendus** :
-  10-100x plus rapide sur les requêtes de lecture
-  Amélioration notable au démarrage de l'app
-  Meilleure scalabilité

**Impact négatif** :
-  +5-10% d'espace disque
-  INSERT/UPDATE légèrement plus lents (négligeable)

**Durée d'application** : 10-30 secondes

## Support

Pour toute question sur les migrations, consulter :
- [`docs/dev/optimisation-database.md`](../../../docs/dev/optimisation-database.md)
- [`OPTIMISATIONS_DB_APPLIQUEES.md`](../../../OPTIMISATIONS_DB_APPLIQUEES.md)
