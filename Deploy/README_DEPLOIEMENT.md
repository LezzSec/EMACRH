# Déploiement EMAC sur Réseau d'Entreprise

## 📋 Contenu de ce dossier

- `Lancer_EMAC.bat` : Lanceur optimisé pour déploiement réseau
- `README_DEPLOIEMENT.md` : Ce fichier (instructions pour admin système)

## 🎯 Objectif

Déployer EMAC sur un partage réseau Windows tout en garantissant un démarrage rapide (2-3 secondes) pour les utilisateurs finaux.

## ⚙️ Principe de fonctionnement

Le lanceur `Lancer_EMAC.bat` utilise un **système de cache local** :

1. **Premier lancement** : Copie l'application depuis le réseau vers `%LOCALAPPDATA%\EMAC_Cache` (~30-60 sec)
2. **Lancements suivants** : Lance depuis le cache local (2-3 sec)
3. **Mise à jour automatique** : Détecte les nouvelles versions et recopie si nécessaire

### Avantages
✅ Démarrage rapide après la première utilisation
✅ Mise à jour transparente pour l'utilisateur
✅ Fonctionne même avec antivirus réseau actif
✅ Pas de configuration utilisateur requise

---

## 📦 Étape 1 : Préparer l'application

### 1.1 Compiler EMAC (sur poste développeur)

```batch
cd App
pyinstaller EMAC_optimized.spec --clean --noconfirm
```

Résultat : Dossier `App\dist\EMAC\` contenant :
```
EMAC\
├── EMAC.exe
├── _internal\      (bibliothèques Python, Qt, etc.)
├── .env            (IMPORTANT : configuration base de données)
└── (autres fichiers)
```

### 1.2 Vérifier le fichier .env

⚠️ **CRITIQUE** : Le fichier `.env` contient le mot de passe de la base de données.

```ini
# Exemple de .env
EMAC_DB_HOST=serveur-mysql.entreprise.local
EMAC_DB_USER=emac_user
EMAC_DB_PASSWORD=VotreMotDePasseSecurise123
EMAC_DB_NAME=emac_db
```

**Sécurité** :
- ✅ Le `.env` sera copié automatiquement dans le cache local de chaque utilisateur
- ✅ Le `.env` n'est jamais commité dans Git
- ⚠️ Assurez-vous que le partage réseau a les bonnes permissions (lecture seule pour utilisateurs)

---

## 🌐 Étape 2 : Déployer sur le réseau

### 2.1 Créer le partage réseau

1. **Choisir l'emplacement** :
   ```
   Exemple : \\SERVEUR-APP\Applications\EMAC
   ```

2. **Copier le dossier EMAC** :
   ```batch
   robocopy "App\dist\EMAC" "\\SERVEUR-APP\Applications\EMAC" /MIR
   ```

3. **Configurer les permissions** :
   - **Lecture** : Tous les utilisateurs EMAC
   - **Écriture** : Aucune (sauf administrateurs pour mises à jour)

### 2.2 Vérifier l'accès réseau

Testez depuis un poste utilisateur :
```batch
dir \\SERVEUR-APP\Applications\EMAC
```

Vous devriez voir :
```
EMAC.exe
_internal
.env
```

---

## 👥 Étape 3 : Distribuer le lanceur aux utilisateurs

### 3.1 Configurer le lanceur

1. **Copier le lanceur** depuis `Deploy\Lancer_EMAC.bat`

2. **Modifier la ligne 10** avec le chemin réseau correct :
   ```batch
   set "SOURCE_RESEAU=\\SERVEUR-APP\Applications\EMAC"
   ```

### 3.2 Distribution

**Option A : Script de déploiement GPO (recommandé)**

Créez `deploy_launcher.bat` :
```batch
@echo off
REM Déployer le lanceur EMAC sur le bureau de chaque utilisateur

set "LAUNCHER_SOURCE=\\SERVEUR-APP\Applications\EMAC_Launcher\Lancer_EMAC.bat"
set "DESKTOP=%USERPROFILE%\Desktop"

copy /y "%LAUNCHER_SOURCE%" "%DESKTOP%\Lancer EMAC.bat"

echo ✅ Lanceur EMAC installé sur le bureau
exit /b 0
```

Déployez via GPO : `Stratégies de groupe > Scripts de démarrage/ouverture de session`

**Option B : Distribution manuelle**

1. Envoyez `Lancer_EMAC.bat` par email
2. Demandez aux utilisateurs de le copier sur leur bureau
3. Renommez en `Lancer EMAC.bat` (sans underscore pour meilleure lisibilité)

**Option C : Raccourci réseau**

Créez un raccourci `.lnk` pointant vers :
```
Cible : \\SERVEUR-APP\Applications\EMAC_Launcher\Lancer_EMAC.bat
Démarrer dans : %LOCALAPPDATA%
```

---

## 🔄 Étape 4 : Mettre à jour l'application

### 4.1 Procédure de mise à jour

1. **Compiler la nouvelle version** :
   ```batch
   cd App
   pyinstaller EMAC_optimized.spec --clean --noconfirm
   ```

2. **Déployer sur le réseau** :
   ```batch
   robocopy "App\dist\EMAC" "\\SERVEUR-APP\Applications\EMAC" /MIR
   ```

3. **Informer les utilisateurs** :
   > "Au prochain lancement d'EMAC, une mise à jour automatique sera téléchargée (30-60 sec)"

### 4.2 Détection automatique

Le lanceur détecte automatiquement les mises à jour en comparant :
- ✅ Taille du fichier `EMAC.exe`
- ✅ Date de modification

Pas d'action utilisateur requise !

### 4.3 Forcer la mise à jour

Si un utilisateur a des problèmes, demandez-lui de supprimer le cache :
```batch
rmdir /s /q "%LOCALAPPDATA%\EMAC_Cache"
```

Au prochain lancement, l'application sera recopiée.

---

## 🛠️ Dépannage

### Problème 1 : "Application non trouvée sur le réseau"

**Symptôme** :
```
❌ ERREUR : Application non trouvée sur le réseau
   Chemin configuré : \\SERVEUR\...
```

**Solutions** :
1. Vérifiez que le chemin réseau est accessible depuis le poste utilisateur
2. Testez manuellement : `explorer \\SERVEUR-APP\Applications\EMAC`
3. Vérifiez les permissions de lecture du partage
4. Vérifiez que le pare-feu autorise SMB (port 445)

### Problème 2 : "Échec de la copie depuis le réseau"

**Symptôme** :
```
❌ ERREUR : Échec de la copie depuis le réseau
   Code d'erreur : 8
```

**Solutions** :
1. Vérifiez les droits d'écriture dans `%LOCALAPPDATA%`
2. Désactivez l'antivirus temporairement pour tester
3. Ajoutez `%LOCALAPPDATA%\EMAC_Cache` aux exclusions antivirus
4. Consultez le fichier log : `%LOCALAPPDATA%\EMAC_Cache\launcher.log`

### Problème 3 : Application plante au démarrage

**Symptôme** :
L'application se lance mais crash immédiatement

**Solutions** :
1. **Vérifiez le .env** :
   ```batch
   type "%LOCALAPPDATA%\EMAC_Cache\.env"
   ```
   Doit contenir : `EMAC_DB_PASSWORD=...`

2. **Testez la connexion MySQL** :
   - Vérifiez que le serveur MySQL est accessible depuis le poste utilisateur
   - Testez : `mysql -h serveur-mysql -u emac_user -p`

3. **Consultez les logs** :
   ```batch
   type "%LOCALAPPDATA%\EMAC_Cache\logs\emac.log"
   ```

### Problème 4 : Démarrage lent malgré le cache

**Symptôme** :
Même avec cache local, l'application met > 30 secondes à démarrer

**Solutions** :
1. **Exclure du scan antivirus** :
   - Ajoutez `%LOCALAPPDATA%\EMAC_Cache` aux exclusions Windows Defender
   - Paramètres > Virus et menaces > Exclusions > Ajouter un dossier

2. **Désactiver SMB Signing** (si autorisé par la sécurité réseau) :
   ```powershell
   Set-SmbClientConfiguration -RequireSecuritySignature $false
   ```

3. **Vérifier la version SMB** :
   ```powershell
   Get-SmbConnection
   # Devrait afficher SMB 3.x pour meilleures performances
   ```

---

## 📊 Monitoring et statistiques

### Consulter les logs utilisateur

Chaque lancement génère un log dans :
```
%LOCALAPPDATA%\EMAC_Cache\launcher.log
```

Exemple de log normal :
```
================================================
EMAC Launcher - 23/12/2025 10:30:15
================================================
Version locale à jour, pas de copie nécessaire
Lancement de l'application : 10:30:16
Commande : C:\Users\jdupont\AppData\Local\EMAC_Cache\EMAC.exe
Application started successfully
```

### Script de diagnostic

Créez `diagnostic_emac.bat` pour les utilisateurs :
```batch
@echo off
echo ========== Diagnostic EMAC ==========
echo.
echo Version cache local :
for %%A in ("%LOCALAPPDATA%\EMAC_Cache\EMAC.exe") do echo   Taille: %%~zA  Date: %%~tA
echo.
echo Version réseau :
for %%A in ("\\SERVEUR-APP\Applications\EMAC\EMAC.exe") do echo   Taille: %%~zA  Date: %%~tA
echo.
echo Contenu du .env :
type "%LOCALAPPDATA%\EMAC_Cache\.env" | findstr /V "PASSWORD"
echo   (Mot de passe masqué)
echo.
echo Dernières lignes du log :
powershell -Command "Get-Content '%LOCALAPPDATA%\EMAC_Cache\launcher.log' -Tail 10"
echo.
pause
```

---

## 🔒 Sécurité

### Protection du .env

⚠️ **Le fichier .env contient des informations sensibles**

**Bonnes pratiques** :
1. ✅ Permissions réseau : Lecture seule pour utilisateurs
2. ✅ Chiffrer le partage réseau (SMB Encryption)
3. ✅ Utiliser un compte MySQL dédié avec droits limités
4. ✅ Changer régulièrement le mot de passe MySQL

**Éviter** :
- ❌ Ne JAMAIS commiter .env dans Git
- ❌ Ne JAMAIS envoyer .env par email non chiffré
- ❌ Ne JAMAIS donner droits d'écriture sur le partage réseau

### Audit

Pour voir quels utilisateurs accèdent à EMAC :
```powershell
# Sur le serveur de fichiers
Get-SmbOpenFile | Where-Object Path -like "*\EMAC\*"
```

---

## 📈 Performance attendue

| Scénario | Temps | Action utilisateur |
|----------|-------|-------------------|
| **Premier lancement** | 30-60 sec | Attendre la copie |
| **Lancement normal** | 2-3 sec | Aucune |
| **Mise à jour détectée** | 30-60 sec | Attendre la recopie |
| **Sans cache (problème)** | 2-5 min | ⚠️ Contacter support |

---

## ✅ Checklist de déploiement

Avant de déployer en production :

- [ ] Application compilée avec `EMAC_optimized.spec`
- [ ] Fichier `.env` configuré avec le bon mot de passe MySQL
- [ ] Partage réseau créé avec permissions lecture seule
- [ ] Lanceur `Lancer_EMAC.bat` configuré avec le bon chemin réseau
- [ ] Test du lanceur depuis un poste utilisateur
- [ ] Exclusion antivirus configurée sur `%LOCALAPPDATA%\EMAC_Cache`
- [ ] Documentation utilisateur fournie
- [ ] Plan de mise à jour communiqué

---

## 📞 Support

En cas de problème persistant :

1. **Consultez les logs** : `%LOCALAPPDATA%\EMAC_Cache\launcher.log`
2. **Testez le diagnostic** : `diagnostic_emac.bat`
3. **Vérifiez la connectivité** : `ping serveur-mysql`
4. **Contactez l'équipe IT** avec les informations du log

---

**Version du document** : 1.0
**Date** : Décembre 2025
**Auteur** : Équipe EMAC
