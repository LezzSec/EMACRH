# Base de données EMAC

Ce répertoire contient tous les fichiers liés à la base de données MySQL de l'application EMAC.

## Structure

```
database/
├── schema/        # Schémas de base de données
├── migrations/    # Scripts de migration
└── backups/       # Sauvegardes SQL
```

## Schémas

### schema/bddemac.sql
Schéma principal de la base de données contenant :
- Tables de personnel (personnel, operateurs)
- Tables de postes et ateliers
- Tables de polyvalence et évaluations
- Tables de contrats
- Tables d'historique et logs
- Tables d'absences et congés

## Migrations

### migrations/schema_absences_conges.sql
Migration pour ajouter la gestion des absences et congés.

Pour appliquer une migration :
```bash
mysql -u root emac_db < App/database/migrations/schema_absences_conges.sql
```

## Sauvegardes

Le dossier `backups/` contient les sauvegardes SQL horodatées :
- bddserver.sql
- bddserver2.sql
- bddserver3.sql
- bddserver4.sql
- bddserver9.sql
- bddserver11.sql
- bddserver12.sql
- dumpemacbdd.sql

### Restaurer une sauvegarde

```bash
# Créer une nouvelle base de données
mysql -u root -e "CREATE DATABASE emac_db_restore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Restaurer depuis une sauvegarde
mysql -u root emac_db_restore < App/database/backups/bddserver12.sql
```

### Créer une nouvelle sauvegarde

```bash
mysqldump -u root emac_db > App/database/backups/bddserver_$(date +%Y%m%d).sql
```

## Configuration de connexion

La configuration de connexion se trouve dans [App/core/db/configbd.py](../core/db/configbd.py).

**Configuration actuelle :**
- Host: 192.168.1.128
- User: gestionrh
- Database: emac_db
- Port: 3306
- Charset: utf8mb4
