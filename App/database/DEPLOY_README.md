# Déploiement base de données EMAC

Ce document décrit les options de déploiement DB. Pour les nouvelles évolutions, privilégier le CLI de migrations plutôt que l'ancien script incrémental.

## Méthode recommandée : migrations CLI

Depuis `App/` :

```bash
python -m cli migrate --status
python -m cli migrate --apply-all
```

Le CLI :

- crée la table `schema_migrations` si nécessaire ;
- détecte les fichiers `NNN_*.sql` dans `database/migrations/` ;
- applique uniquement les migrations absentes ;
- trace les migrations par nom de fichier complet.

Avant production :

```bash
mysqldump -u gestionrh -p emac_db > App/database/backups/emac_db_avant_migration.sql
```

## Initialiser une base déjà préparée

Si la base contient déjà le schéma mais que `schema_migrations` n'est pas renseignée :

```bash
python -m cli migrate --mark-applied-all
python -m cli migrate --status
```

À utiliser avec prudence : cette commande marque les migrations comme appliquées sans exécuter leur SQL.

## Ancienne méthode : script incrémental

Les fichiers suivants sont conservés pour compatibilité historique :

```
App/database/
├── deploy_incremental.sql
├── deploy_to_server.bat
└── DEPLOY_README.md
```

Ils concernent surtout l'ancien déploiement initial des tables utilisateurs/permissions. Pour l'application actuelle, vérifier d'abord si une migration numérotée couvre déjà le besoin.

Lancement manuel legacy depuis `App/database/` :

```bash
deploy_to_server.bat
```

Ou :

```bash
mysql -h localhost -u root -p emac_db < deploy_incremental.sql
```

## Configuration application

La connexion applicative est lue depuis `App/.env` par `infrastructure/db/configbd.py` :

```env
EMAC_DB_HOST=127.0.0.1
EMAC_DB_PORT=3306
EMAC_DB_USER=gestionrh
EMAC_DB_PASSWORD=votre_mot_de_passe
EMAC_DB_NAME=emac_db
```

Ne jamais stocker de mot de passe réel dans ce fichier README.

## Vérifications post-déploiement

```sql
USE emac_db;
SHOW TABLES LIKE 'schema_migrations';
SELECT filename, applied_at FROM schema_migrations ORDER BY filename;
SHOW TABLES LIKE 'utilisateurs';
SHOW TABLES LIKE 'role_features';
SHOW TABLES LIKE 'features';
```

Vérifier aussi le lancement applicatif :

```bash
cd App
py -m gui.main_qt
```

## Build applicatif

Depuis la racine du dépôt :

```bash
cd build-scripts
build_optimized.bat
```

La sortie attendue est `dist/EMAC/EMAC.exe`.

## Dépannage

### `mysql: command not found`

Ajouter le dossier `bin` MySQL au `PATH` ou utiliser le chemin complet de `mysql.exe`.

### `Access denied for user`

Vérifier l'utilisateur, le mot de passe, le host, le port et les droits SQL (`CREATE`, `ALTER`, `INSERT`, `UPDATE`, `SELECT`).

### `Unknown database`

Créer la base :

```sql
CREATE DATABASE IF NOT EXISTS emac_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_general_ci;
```

### Migration en erreur

1. Ne pas relancer à l'aveugle en production.
2. Lire l'erreur SQL exacte.
3. Vérifier l'état de `schema_migrations`.
4. Restaurer la sauvegarde si nécessaire.
5. Corriger la migration ou appliquer un rollback ciblé.
