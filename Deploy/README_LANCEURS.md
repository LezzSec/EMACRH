# Lanceurs EMAC

## 📦 Deux versions disponibles

### 1. `Lancer_EMAC_Local.bat` ⭐ Pour développement

**Utilisez celui-ci si** :
- ✅ Vous développez sur votre PC local
- ✅ L'exe est dans `App\dist\EMAC` sur votre disque
- ✅ Vous n'avez PAS de partage réseau configuré

**Ce qu'il fait** :
- Copie `App\dist\EMAC` vers `%LOCALAPPDATA%\EMAC_Cache`
- Lance depuis le cache local (rapide)
- Premier lancement : 10-30 sec
- Lancements suivants : 2-3 sec

---

### 2. `Lancer_EMAC.bat` - Pour production réseau

**Utilisez celui-ci si** :
- ✅ L'exe est déployé sur un partage réseau (ex: `\\serveur\Apps\EMAC`)
- ✅ Vous distribuez l'application aux utilisateurs
- ✅ Le partage réseau est accessible

**Configuration requise** :
Modifier la ligne 12 avec le bon chemin réseau :
```batch
set "SOURCE_RESEAU=\\votre-serveur\partage\EMAC"
```

---

## 🚀 Pour vous (développeur)

**Utilisez** : `Lancer_EMAC_Local.bat`

```batch
cd c:\Users\tlahirigoyen\Desktop\PROJET\EMAC\Deploy
Lancer_EMAC_Local.bat
```

**Résultat attendu** :
```
================================================
  EMAC - Lanceur Local (Developpement)
================================================

[1/3] Verification de la source...
   ✅ Source trouvee : C:\...\App\dist\EMAC

[2/3] Premiere installation...
   📂 Copie vers le cache local...
   (Peut prendre 10-30 secondes)

   ✅ Copie terminee

[3/3] Lancement d'EMAC...

✅ Application lancee
```

---

## 📁 Logs de diagnostic

| Lanceur | Fichier log | Emplacement |
|---------|-------------|-------------|
| `Lancer_EMAC_Local.bat` | `launcher_local.log` | `%LOCALAPPDATA%\EMAC_Cache\` |
| `Lancer_EMAC.bat` | `launcher.log` | `%LOCALAPPDATA%\EMAC_Cache\` |

**Consulter les logs** :
```batch
type %LOCALAPPDATA%\EMAC_Cache\launcher_local.log
```

---

## 🔧 En cas d'erreur

### Erreur : "EMAC.exe introuvable"

**Cause** : Le chemin source est incorrect

**Solution** :
1. Vérifiez que `App\dist\EMAC\EMAC.exe` existe
2. Recompilez si nécessaire :
   ```batch
   cd App
   build_optimized.bat
   ```

---

### Erreur : "Echec de la copie"

**Cause** : Problème de droits ou disque plein

**Solution** :
1. Vérifiez l'espace disque libre
2. Consultez le log : `%LOCALAPPDATA%\EMAC_Cache\launcher_local.log`
3. Essayez de supprimer le cache et recommencer :
   ```batch
   rmdir /s /q %LOCALAPPDATA%\EMAC_Cache
   ```

---

### Erreur : ".env manquant"

**Cause** : Le fichier `.env` n'est pas dans `App\dist\EMAC\`

**Solution** :
```batch
copy App\.env App\dist\EMAC\.env
```

Ou recompilez avec `build_optimized.bat` qui copie le `.env` automatiquement.

---

## ✅ Checklist avant de lancer

- [ ] EMAC.exe compilé dans `App\dist\EMAC\`
- [ ] Fichier `.env` présent dans `App\dist\EMAC\`
- [ ] Espace disque suffisant (~ 200 Mo pour le cache)
- [ ] Pour production : Chemin réseau configuré dans `Lancer_EMAC.bat`

---

**Version** : 1.0
**Date** : Décembre 2025
