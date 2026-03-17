# Guide de sécurité - Configuration Base de Données

## Configuration du mot de passe MySQL

Le mot de passe MySQL n'est plus hardcodé dans le code source. Vous avez **3 méthodes** pour le configurer :

---

## Méthode 1 : Fichier .env (Recommandée)

### Étape 1 : Créer le fichier `.env`

1. Copier le fichier `.env.example` en `.env` :
   ```bash
   copy .env.example .env
   ```

2. Éditer le fichier `.env` avec vos vraies valeurs :
   ```
   EMAC_DB_PASSWORD=emacViodos$13
   EMAC_DB_HOST=localhost
   EMAC_DB_USER=root
   EMAC_DB_NAME=emac_db
   EMAC_DB_PORT=3306
   ```

### ✅ Avantages
- Simple à utiliser
- Fichier ignoré par Git (ne sera pas commité)
- Facile à partager entre machines (chacun a son `.env` local)

---

## Méthode 2 : Variables d'environnement Windows

### Définir pour la session actuelle (temporaire)
```cmd
set EMAC_DB_PASSWORD=emacViodos$13
set EMAC_DB_HOST=localhost
set EMAC_DB_USER=root
set EMAC_DB_NAME=emac_db
```

### Définir de manière permanente (système)

1. **Via l'interface Windows** :
   - Ouvrir : `Panneau de configuration` → `Système` → `Paramètres système avancés`
   - Cliquer sur `Variables d'environnement`
   - Dans "Variables utilisateur", cliquer `Nouvelle`
   - Nom : `EMAC_DB_PASSWORD`
   - Valeur : `emacViodos$13`

2. **Via PowerShell (admin)** :
   ```powershell
   [Environment]::SetEnvironmentVariable("EMAC_DB_PASSWORD", "emacViodos$13", "User")
   ```

### ✅ Avantages
- Sécurisé : pas de fichier à gérer
- Global : disponible pour tous les projets
- Survit aux redémarrages

---

## Méthode 3 : Valeur par défaut (Développement local uniquement)

Si aucune configuration n'est trouvée, l'application utilisera la valeur par défaut `emacViodos$13` avec un avertissement dans la console.

### ⚠️ Important
Cette méthode est **uniquement pour le développement local**. Pour la production ou le partage de code :
- Utiliser la méthode 1 (`.env`) ou 2 (variables d'environnement)
- Ne JAMAIS commiter le fichier `.env` sur Git

---

## Sécurité Git

Le fichier `.env` est déjà dans `.gitignore` et ne sera **jamais** commité.

Pour vérifier :
```bash
git status
# Le fichier .env ne doit PAS apparaître dans les fichiers modifiés
```

Si le mot de passe a déjà été commité dans l'historique Git :
```bash
# ⚠️ ATTENTION : Ceci réécrit l'historique Git
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch App/core/db/configbd.py" \
  --prune-empty --tag-name-filter cat -- --all
```

---

## Vérification de la configuration

Pour vérifier que la configuration fonctionne :

```bash
cd App
py -m core.gui.main_qt
```

Si le mot de passe n'est pas configuré, vous verrez :
```
⚠️ AVERTISSEMENT: Mot de passe DB non configuré, utilisation de la valeur par défaut
   Pour configurer: définir la variable d'environnement EMAC_DB_PASSWORD
   ou créer un fichier .env avec: EMAC_DB_PASSWORD=votre_mot_de_passe
```

---

## Déploiement sur une autre machine

1. Cloner le dépôt
2. Créer le fichier `.env` avec les valeurs locales :
   ```bash
   copy .env.example .env
   # Éditer .env avec les bonnes valeurs
   ```
3. Lancer l'application

---

## Bonnes pratiques

### ✅ À FAIRE
- Utiliser un fichier `.env` local pour chaque machine
- Utiliser des variables d'environnement pour la production
- Changer le mot de passe par défaut en production
- Garder le fichier `.env.example` à jour (avec des valeurs factices)

### ❌ À NE PAS FAIRE
- Commiter le fichier `.env` sur Git
- Partager le mot de passe par email/Slack
- Utiliser le même mot de passe en dev et en production
- Hardcoder des mots de passe dans le code source

---

## 🆘 Dépannage

### Problème : "Access denied for user 'root'@'localhost'"
- Vérifier que le mot de passe dans `.env` est correct
- Vérifier que MySQL est démarré
- Tester la connexion avec MySQL Workbench

### Problème : "Unknown database 'emac_db'"
- Créer la base de données : `CREATE DATABASE emac_db;`
- Importer le schéma : `mysql -u root -p emac_db < database/schema/bddemac.sql`

### Problème : L'application ne lit pas le fichier .env
- Vérifier que le fichier est bien nommé `.env` (pas `.env.txt`)
- Vérifier qu'il est dans le répertoire `App/`
- Vérifier l'encodage UTF-8
