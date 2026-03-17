# Guide de Déploiement Incrémental - EMAC

## Objectif

Ce guide explique comment déployer les **nouvelles tables** du système de gestion des utilisateurs sur le serveur de production **SANS ÉCRASER** les données existantes.

## ✅ Ce qui sera ajouté

Le script de déploiement ajoute uniquement :

### Nouvelles Tables
- `roles` - Rôles utilisateurs (admin, gestion_production, gestion_rh)
- `utilisateurs` - Comptes utilisateurs avec authentification
- `permissions` - Permissions par rôle et module
- `logs_connexion` - Historique des connexions/déconnexions

### Modifications de Tables Existantes
- Ajout de colonnes dans `historique` :
  - `utilisateur` (varchar 100)
  - `table_name` (varchar 100)
  - `record_id` (int)

## ⚠️ Garanties de Sécurité

Le script utilise :
- ✅ `CREATE TABLE IF NOT EXISTS` - Ne crée que si la table n'existe pas
- ✅ `INSERT IGNORE` - N'insère que si les données n'existent pas déjà
- ✅ Vérification des colonnes avant ajout - Pas de doublon possible
- ❌ **AUCUN `DROP TABLE`** - Jamais de suppression
- ❌ **AUCUN `DELETE`** - Jamais d'effacement de données
- ❌ **AUCUN `TRUNCATE`** - Jamais de vidage de tables

## Méthode 1 : Déploiement Automatique (Recommandé)

### Étapes

1. **Ouvrir un terminal** dans le dossier `App/database/`
   ```bash
   cd c:\Users\tlahirigoyen\Desktop\PROJET\EMAC\App\database
   ```

2. **Exécuter le script de déploiement**
   ```bash
   deploy_to_server.bat
   ```

3. **Suivre les instructions** :
   - Entrer l'hôte MySQL (ex: `localhost` ou IP du serveur)
   - Entrer l'utilisateur (ex: `root`)
   - Entrer le nom de la base de données (ex: `emac_db`)
   - Entrer le mot de passe (sera masqué)
   - Confirmer le déploiement

4. **Vérifier le résultat** :
   - Le script affiche un message de succès
   - Les nouvelles tables sont listées

### Exemple de Session

```
============================================================================
EMAC - Déploiement incrémental de la base de données
============================================================================

Hôte MySQL (ex: localhost ou IP serveur): localhost
Utilisateur MySQL (ex: root): root
Nom de la base de données (ex: emac_db): emac_db

Entrez le mot de passe MySQL (il sera masqué):
************

Confirmer le déploiement? (O/N): O

Déploiement en cours...

============================================================================
SUCCES: Déploiement terminé avec succès!
============================================================================

Les nouvelles tables ont été créées:
 [OK] roles
 [OK] utilisateurs
 [OK] permissions
 [OK] logs_connexion

Utilisateur admin créé:
 - Username: admin
 - Mot de passe: admin123
 - IMPORTANT: Changez ce mot de passe dès la première connexion!
```

## Méthode 2 : Déploiement Manuel

Si le script automatique ne fonctionne pas :

### Via MySQL Command Line

```bash
mysql -h localhost -u root -p emac_db < deploy_incremental.sql
```

### Via phpMyAdmin

1. Se connecter à phpMyAdmin
2. Sélectionner la base de données `emac_db`
3. Aller dans l'onglet **Importer**
4. Choisir le fichier `deploy_incremental.sql`
5. Cliquer sur **Exécuter**

### Via MySQL Workbench

1. Ouvrir MySQL Workbench
2. Se connecter au serveur
3. Menu **File** → **Open SQL Script**
4. Sélectionner `deploy_incremental.sql`
5. Cliquer sur **Execute** (éclair )

## Compte Admin par Défaut

Après le déploiement, un compte admin est créé :

- **Username** : `admin`
- **Mot de passe** : `admin123`

⚠️ **IMPORTANT** : Changez ce mot de passe dès la première connexion !

## Créer un Nouvel EXE

Une fois la base de données déployée, créer l'exécutable :

```bash
cd App
pyinstaller --onefile --windowed --name EMAC --icon=icon.ico core/gui/main_qt.py
```

L'EXE sera dans le dossier `dist/`

## Vérification Post-Déploiement

### Vérifier que les tables existent

```sql
USE emac_db;
SHOW TABLES LIKE '%utilisateurs%';
SHOW TABLES LIKE '%roles%';
SHOW TABLES LIKE '%permissions%';
SHOW TABLES LIKE '%logs_connexion%';
```

### Vérifier les données initiales

```sql
SELECT * FROM roles;
SELECT username, nom, prenom, actif FROM utilisateurs;
SELECT COUNT(*) as nb_permissions FROM permissions;
```

### Vérifier les colonnes de historique

```sql
DESCRIBE historique;
```

Vous devriez voir les colonnes `utilisateur`, `table_name`, et `record_id`.

## 🆘 Dépannage

### Erreur : "mysql: command not found"

**Solution** : Ajouter MySQL au PATH ou modifier le script `deploy_to_server.bat` avec le chemin complet de mysql.exe :

```batch
set "MYSQL_CMD=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
```

### Erreur : "Access denied for user"

**Solution** : Vérifier :
- Le nom d'utilisateur et mot de passe
- Que l'utilisateur a les droits CREATE TABLE et INSERT
- La connexion au serveur (firewall, port 3306)

### Erreur : "Unknown database 'emac_db'"

**Solution** : Créer d'abord la base de données :

```sql
CREATE DATABASE IF NOT EXISTS emac_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;
```

### Les tables existent déjà

✅ **C'est normal !** Le script utilise `IF NOT EXISTS`, donc :
- Si les tables existent déjà, elles ne seront pas modifiées
- Si les données existent déjà, elles ne seront pas dupliquées
- Aucun impact sur les données existantes

## Fichiers Fournis

```
App/database/
├── deploy_incremental.sql      # Script SQL sécurisé
├── deploy_to_server.bat        # Script de déploiement Windows
└── DEPLOY_README.md            # Ce fichier (guide)
```

## Support

En cas de problème :
1. Vérifier les messages d'erreur dans le terminal
2. Consulter la section Dépannage ci-dessus
3. Vérifier les logs MySQL : `/var/log/mysql/error.log` (Linux) ou Event Viewer (Windows)

---

** Bon déploiement !**
