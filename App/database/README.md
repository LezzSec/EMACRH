# Base de données EMAC

Ce dossier regroupe les schémas, migrations, diagnostics et scripts de déploiement liés à la base EMAC.

## Structure

```
database/
├── schema/                 # Schémas de référence
├── migrations/             # Migrations SQL suivies par le CLI
│   ├── archive/            # Anciennes migrations conservées pour historique
│   └── rollback/           # Scripts de rollback ciblés
├── diagnostics/            # Requêtes de diagnostic/performance
├── backups/                # Sauvegardes locales, ignorées par Git
├── deploy_incremental.sql  # Ancien script de déploiement incrémental
├── deploy_to_server.bat    # Assistant Windows legacy
└── DEPLOY_README.md
```

## Schémas de référence

- `schema/emac_structure_mariadb.sql` : structure actuelle de référence.
- `schema/historique_polyvalence.sql` : schéma historique lié à la polyvalence.

Les anciens dumps SQL présents à la racine du dossier servent d'historique ou de support de reprise. Pour l'évolution courante, privilégier les migrations.

## Migrations

Les migrations actives sont dans `migrations/` et suivent le format `NNN_description.sql`. Elles sont suivies en base dans la table `schema_migrations` par nom de fichier complet.

Commandes depuis `App/` :

```bash
python -m cli migrate --status
python -m cli migrate --apply-all
python -m cli migrate --apply 056_mutuelle_ui_support.sql
python -m cli migrate --mark-applied-all
```

Les dernières migrations présentes sont :

- `052_unique_personnel_competences.sql`
- `053_fulltext_historique.sql`
- `054_password_upgrade_flag.sql`
- `055_add_priority_performance_indexes.sql`
- `056_mutuelle_ui_support.sql`

Voir [migrations/README.md](migrations/README.md) et [migrations/MIGRATION_LOG.md](migrations/MIGRATION_LOG.md).

## Configuration de connexion

Le code de connexion est dans `App/infrastructure/db/configbd.py`.

La configuration se fait via `App/.env` :

```env
EMAC_DB_HOST=127.0.0.1
EMAC_DB_PORT=3306
EMAC_DB_USER=gestionrh
EMAC_DB_PASSWORD=votre_mot_de_passe
EMAC_DB_NAME=emac_db
```

Ne documenter aucun mot de passe réel dans ce dossier.

## Sauvegarde et restauration

Créer une sauvegarde :

```bash
mysqldump -u gestionrh -p emac_db > App/database/backups/emac_db_YYYYMMDD.sql
```

Restaurer dans une base dédiée :

```bash
mysql -u root -p -e "CREATE DATABASE emac_db_restore CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
mysql -u root -p emac_db_restore < App/database/backups/emac_db_YYYYMMDD.sql
```

## Bonnes pratiques

- Créer une migration SQL pour toute évolution de schéma.
- Rendre les migrations idempotentes quand c'est possible.
- Ne pas renommer une migration déjà appliquée en production.
- Tester `python -m cli migrate --status` avant un déploiement.
- Sauvegarder la base avant toute migration structurelle.
