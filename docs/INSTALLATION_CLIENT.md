# 📦 Installation EMAC - Poste Client

## ⚠️ Information importante

**MySQL n'a PAS besoin d'être installé sur les postes clients.**

L'application EMAC se connecte à une base de données MySQL **hébergée sur un serveur**. Seul le serveur doit avoir MySQL installé.

---

## ✅ Prérequis

### Sur le poste client (où vous installez EMAC) :
- ✅ **Windows 10/11** (64-bit)
- ✅ **Accès réseau** au serveur MySQL (port 3306)
- ❌ **AUCUN logiciel supplémentaire requis** (Python, MySQL, etc.)

### Sur le serveur (hébergement de la base de données) :
- ✅ **MySQL 8.0** installé et configuré
- ✅ Base de données **`emac_db`** créée
- ✅ Utilisateur MySQL avec droits d'accès
- ✅ Port **3306** accessible depuis le réseau

---

## 📥 Installation rapide

### Étape 1 : Récupérer les fichiers

Copiez le dossier `EMAC` complet sur le poste client :

```
EMAC/
├── EMAC.exe
├── _internal/
├── .env.example
├── LISEZMOI.txt
└── ... (autres dossiers)
```

### Étape 2 : Configurer la connexion au serveur

1. **Copiez** `.env.example` → `.env`
2. **Éditez** le fichier `.env` avec un éditeur de texte
3. **Configurez** les paramètres de connexion :

```env
# Adresse du serveur MySQL (remplacez par l'IP réelle de votre serveur)
EMAC_DB_HOST=192.168.1.100

# Utilisateur MySQL
EMAC_DB_USER=emac_user

# Mot de passe
EMAC_DB_PASSWORD=MotDePasseSecurise

# Nom de la base de données
EMAC_DB_NAME=emac_db
```

**Exemples de configuration** :

| Scénario | EMAC_DB_HOST |
|----------|--------------|
| Serveur sur le même PC | `localhost` |
| Serveur sur le réseau local | `192.168.1.100` |
| Serveur avec nom de domaine | `db.monentreprise.local` |
| Serveur distant | `203.0.113.50` |

### Étape 3 : Tester la connexion

1. **Double-cliquez** sur `EMAC.exe`
2. **Connectez-vous** avec vos identifiants
3. Si erreur de connexion, vérifiez :
   - L'IP du serveur est correcte
   - Le port 3306 est accessible
   - Les identifiants MySQL sont valides
   - Le serveur MySQL est démarré

---

## 🔧 Configuration réseau

### Vérifier l'accès au serveur MySQL

Depuis le poste client, testez la connexion :

```bash
# Sous Windows (PowerShell)
Test-NetConnection -ComputerName 192.168.1.100 -Port 3306

# Alternative : Avec telnet
telnet 192.168.1.100 3306
```

Si la connexion échoue, vérifiez :
1. **Pare-feu du serveur** : Autorisez le port 3306
2. **Pare-feu du client** : Autorisez les connexions sortantes
3. **Configuration MySQL** : Le serveur doit écouter sur `0.0.0.0` (pas seulement `127.0.0.1`)

### Configuration MySQL côté serveur

Sur le serveur MySQL, vérifiez dans `my.ini` ou `my.cnf` :

```ini
[mysqld]
bind-address = 0.0.0.0  # Écoute sur toutes les interfaces
port = 3306
```

Créez un utilisateur avec accès distant :

```sql
-- Sur le serveur MySQL
CREATE USER 'emac_user'@'%' IDENTIFIED BY 'MotDePasseSecurise';
GRANT ALL PRIVILEGES ON emac_db.* TO 'emac_user'@'%';
FLUSH PRIVILEGES;
```

---

## 🚀 Déploiement sur plusieurs postes

### Installation silencieuse (administrateur réseau)

Pour installer EMAC sur 10+ postes :

1. **Préparez** un dossier partagé réseau :
   ```
   \\serveur\partage\EMAC\
   ```

2. **Créez** un script batch `deploy.bat` :
   ```batch
   @echo off
   REM Copie EMAC vers les postes
   xcopy /E /I /Y "\\serveur\partage\EMAC" "C:\Program Files\EMAC"

   REM Crée le raccourci Bureau
   powershell "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\EMAC.lnk'); $s.TargetPath = 'C:\Program Files\EMAC\EMAC.exe'; $s.Save()"

   echo Installation terminee!
   pause
   ```

3. **Distribuez** le fichier `.env` pré-configuré (attention : contient le mot de passe)

### Alternative : Installateur MSI (avancé)

Utilisez **Inno Setup** ou **WiX Toolset** pour créer un installateur :
- Installe EMAC dans `C:\Program Files\EMAC\`
- Crée raccourcis Bureau et Menu Démarrer
- Demande l'IP du serveur pendant l'installation
- Crée le fichier `.env` automatiquement

---

## 🔒 Sécurité

### Bonnes pratiques

1. **Ne partagez jamais** le fichier `.env` par email/chat
2. **Utilisez des mots de passe forts** pour MySQL
3. **Créez un utilisateur MySQL dédié** (pas `root`)
4. **Limitez les droits** aux tables nécessaires :
   ```sql
   GRANT SELECT, INSERT, UPDATE ON emac_db.* TO 'emac_user'@'%';
   ```
5. **Utilisez un VPN** si accès depuis Internet

### Chiffrement de la connexion (optionnel)

Pour chiffrer les communications MySQL :

1. Configurez MySQL avec SSL
2. Dans `.env`, ajoutez :
   ```env
   EMAC_DB_SSL=true
   ```

---

## 📊 Architecture réseau typique

```
┌─────────────────────────────────────────────────────┐
│                  Réseau Local                        │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Poste 1      │  │ Poste 2      │  │ Poste N   │ │
│  │ EMAC.exe     │  │ EMAC.exe     │  │ EMAC.exe  │ │
│  │ .env         │  │ .env         │  │ .env      │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │
│         │                 │                 │       │
│         └─────────────────┴─────────────────┘       │
│                           │                         │
│                           ▼                         │
│                  ┌────────────────┐                 │
│                  │ Serveur MySQL  │                 │
│                  │ Port 3306      │                 │
│                  │ emac_db        │                 │
│                  └────────────────┘                 │
└─────────────────────────────────────────────────────┘
```

**Avantages** :
- ✅ Base de données centralisée
- ✅ Sauvegardes simplifiées (un seul serveur)
- ✅ Pas d'installation MySQL sur chaque poste
- ✅ Données synchronisées en temps réel
- ✅ Mises à jour facilitées (remplacer EMAC.exe)

---

## 🆘 Dépannage

### Erreur : "Can't connect to MySQL server"

**Causes possibles** :
1. ❌ Serveur MySQL arrêté → Démarrez le service MySQL
2. ❌ Mauvaise IP dans `.env` → Vérifiez l'adresse
3. ❌ Pare-feu bloque port 3306 → Autorisez le port
4. ❌ MySQL n'écoute que sur localhost → Changez `bind-address`

### Erreur : "Access denied for user"

**Causes possibles** :
1. ❌ Mauvais mot de passe → Vérifiez `.env`
2. ❌ Utilisateur n'a pas les droits → Accordez les privilèges
3. ❌ Utilisateur n'a pas accès distant → Créez avec `'user'@'%'`

### Erreur : "Unknown database 'emac_db'"

**Solution** : Créez la base de données sur le serveur :
```sql
CREATE DATABASE emac_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 📞 Support

Pour toute question :
1. Consultez le fichier `LISEZMOI.txt` dans le dossier EMAC
2. Vérifiez les logs dans `logs/emac.log`
3. Contactez votre administrateur réseau/base de données

---

## ✅ Checklist de validation

Après installation, vérifiez :

- [ ] Le fichier `.env` existe et est configuré
- [ ] EMAC.exe se lance sans erreur
- [ ] La connexion à la base de données fonctionne
- [ ] Vous pouvez voir la liste du personnel
- [ ] Les exports Excel/PDF fonctionnent
- [ ] Le raccourci Bureau est créé (optionnel)

---

**Version** : 1.0
**Date** : 2026-01-07
**Application** : EMAC - Gestion du Personnel
