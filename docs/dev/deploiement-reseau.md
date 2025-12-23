# Déploiement EMAC sur Partage Réseau

## Problème : Lenteur au lancement

Lorsque l'exécutable EMAC est placé sur un partage réseau Windows, le démarrage peut prendre **plusieurs minutes** au lieu de quelques secondes.

### Causes principales

1. **Extraction temporaire lente** : PyInstaller extrait les bibliothèques dans `%TEMP%` via le réseau
2. **Latence réseau** : Chaque DLL/fichier génère des requêtes réseau
3. **Antivirus réseau** : Scan en temps réel des fichiers extraits
4. **Compression UPX** : Ralentit la décompression sur partages réseau

---

## ✅ Solution 1 : Lanceur avec cache local (RECOMMANDÉ)

### Principe
Le script `launcher_reseau.bat` copie automatiquement l'application dans `%LOCALAPPDATA%` au premier lancement, puis lance depuis cette copie locale.

### Avantages
- ✅ Démarrage rapide (2-3 secondes) après la première copie
- ✅ Mise à jour automatique détectée (compare les dates)
- ✅ Aucune modification du .exe nécessaire
- ✅ Fonctionne même avec antivirus réseau actif

### Installation

1. **Placez le dossier `dist\EMAC` sur le partage réseau** :
   ```
   \\serveur\partage\EMAC\
   ├── EMAC.exe
   ├── _internal\
   ├── .env
   └── (autres fichiers)
   ```

2. **Modifiez `launcher_reseau.bat`** (ligne 10) :
   ```batch
   set "SOURCE_RESEAU=\\serveur\partage\EMAC"
   ```

3. **Distribuez le lanceur aux utilisateurs** :
   - Option A : Copiez `launcher_reseau.bat` sur le bureau de chaque utilisateur
   - Option B : Créez un raccourci réseau vers le .bat

### Utilisation

L'utilisateur double-clique sur `launcher_reseau.bat` :
```
================================================
  LANCEMENT EMAC (depuis réseau)
================================================

[1/3] Création du cache local...
[2/3] Première installation locale...
Copie depuis le réseau... (peut prendre 30-60 secondes)
[3/3] Lancement de l'application...

✅ Application lancée
```

**Première exécution** : 30-60 secondes (copie complète)
**Lancements suivants** : 2-3 secondes (cache local)

---

## ✅ Solution 2 : Optimisation du fichier .spec

Si vous ne pouvez pas utiliser un lanceur, optimisez la compilation :

### Modifications appliquées dans `EMAC_optimized.spec`

```python
# Ligne 162-164 : Désactiver UPX
upx=False,  # UPX ralentit la décompression sur réseau
runtime_tmpdir=None,  # Force extraction dans %TEMP% local

# Ligne 179 : Désactiver UPX dans COLLECT
upx=False,
```

### Recompiler avec optimisations réseau

```batch
cd App
pyinstaller EMAC_optimized.spec --clean --noconfirm
```

### Gains attendus
- **Sans optimisation** : 2-5 minutes de démarrage
- **Avec optimisation** : 30-60 secondes de démarrage

⚠️ **Limitation** : Reste lent comparé au cache local (Solution 1)

---

## ✅ Solution 3 : One-File au lieu de One-Folder

### Créer un exécutable unique

Modifiez `EMAC_optimized.spec` :

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # ✅ Inclure les binaires dans l'EXE
    a.datas,         # ✅ Inclure les données dans l'EXE
    [],
    name='EMAC',
    debug=False,
    strip=False,
    upx=False,       # Désactivé pour réseau
    console=True,
    runtime_tmpdir=None,
)

# ❌ Supprimer la section COLLECT
# coll = COLLECT(...)  # Ne pas créer de dossier
```

### Avantages
- Un seul fichier à transférer (300-500 Mo)
- Extraction plus rapide qu'un dossier de 1000+ fichiers

### Inconvénients
- ❌ Fichier volumineux (300-500 Mo)
- ❌ Toujours lent sur réseau (extraction dans %TEMP%)
- ❌ Compliqué pour inclure `.env`

---

## 🎯 Recommandation finale

| Méthode | Temps démarrage | Complexité | Recommandé |
|---------|-----------------|------------|------------|
| **Solution 1 : Cache local** | 2-3 sec | Facile | ✅ OUI |
| Solution 2 : Optimisation spec | 30-60 sec | Facile | Si Solution 1 impossible |
| Solution 3 : One-file | 30-60 sec | Moyen | Non recommandé |
| Rien (partage réseau direct) | 2-5 min | - | ❌ NON |

---

## Configuration réseau Windows

### Désactiver l'antivirus sur le cache EMAC

Si le démarrage reste lent même avec le cache local :

1. Ouvrir Windows Defender
2. **Paramètres > Virus et menaces > Exclusions**
3. Ajouter : `%LOCALAPPDATA%\EMAC_Cache`

### Activer SMB3 pour meilleures performances

```powershell
# Vérifier la version SMB
Get-SmbConnection

# Si SMB 2.x, activer SMB3
Set-SmbClientConfiguration -EnableSMB3Protocol $true
```

---

## Dépannage

### Le lanceur échoue avec "Échec de la copie"

**Cause** : Partage réseau inaccessible

**Solutions** :
1. Vérifiez le chemin UNC : `\\serveur\partage\EMAC`
2. Testez l'accès manuel : `explorer \\serveur\partage\EMAC`
3. Vérifiez les droits de lecture sur le partage

### L'application plante au démarrage

**Cause** : `.env` manquant dans le cache

**Solution** : Le lanceur copie automatiquement le `.env`. Si le problème persiste :
```batch
copy "\\serveur\partage\EMAC\.env" "%LOCALAPPDATA%\EMAC_Cache\.env"
```

### Mise à jour non détectée

**Cause** : Comparaison de dates échoue

**Solution** : Supprimez le cache pour forcer la recopie :
```batch
rmdir /s /q "%LOCALAPPDATA%\EMAC_Cache"
```

---

## Script de déploiement pour administrateur

```batch
@echo off
REM Déployer EMAC sur le réseau avec le lanceur

set "DEST_RESEAU=\\serveur\partage\EMAC"

echo Copie de l'application sur le réseau...
robocopy "dist\EMAC" "%DEST_RESEAU%" /MIR

echo.
echo ✅ Déploiement terminé
echo.
echo Instructions pour les utilisateurs :
echo 1. Copiez launcher_reseau.bat sur votre bureau
echo 2. Modifiez la ligne 10 avec : %DEST_RESEAU%
echo 3. Double-cliquez sur launcher_reseau.bat
pause
```

---

## Performance attendue

| Scénario | Temps | Commentaire |
|----------|-------|-------------|
| Premier lancement (cache vide) | 30-60 sec | Copie complète depuis réseau |
| Lancement normal (cache valide) | 2-3 sec | Depuis disque local |
| Mise à jour détectée | 30-60 sec | Recopie uniquement les fichiers modifiés |
| Lancement direct depuis réseau (sans cache) | 2-5 min | ❌ Non recommandé |
