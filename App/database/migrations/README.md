# Migrations EMAC

## Convention de nommage

Les fichiers de migration suivent le format `NNN_description.sql` où NNN est un numéro séquentiel à 3 chiffres.
Le prochain numéro disponible est **051**.

## Tracking

Les migrations appliquées sont tracées dans la table `schema_migrations` par nom de fichier.
Voir [MIGRATION_LOG.md](MIGRATION_LOG.md) pour l'historique complet, les doublons de préfixes et les fichiers archivés.

## Commandes

```bash
python -m cli migrate --status        # Statut de toutes les migrations
python -m cli migrate --apply-all     # Appliquer tout ce qui est en attente
python -m cli migrate --apply <file>  # Appliquer un fichier spécifique
python -m cli migrate --mark-applied-all  # Marquer appliquées sans exécuter
```

## Créer une nouvelle migration

1. Créer `051_description.sql` (incrémenter le numéro à chaque migration)
2. Utiliser `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` pour l'idempotence
3. Ajouter un commentaire en-tête :
   ```sql
   -- Migration 051 : Titre
   -- Date : YYYY-MM-DD
   -- Description : Ce que fait cette migration
   ```
4. Documenter dans `MIGRATION_LOG.md`

## Structure

```
migrations/
├── 001_*.sql ... 050_*.sql   # Migrations actives (tracées par le CLI)
├── archive/                   # Scripts obsolètes ou redondants
├── rollback/                  # Scripts de rollback
├── migrate.bat                # Script batch legacy (operateurs → personnel)
├── MIGRATION_LOG.md           # Historique complet
└── README.md                  # Ce fichier
```
