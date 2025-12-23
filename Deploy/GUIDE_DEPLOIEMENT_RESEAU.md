# Guide de Déploiement Réseau EMAC

## 📋 Résumé

Ce guide explique comment déployer EMAC sur le partage réseau `\\s_data\Bureautique\Services\THOMAS\EMAC` et distribuer l'application aux utilisateurs.

---

## ✅ Étape 1 : Déployer sur le Réseau

### Option A : Script Automatisé (Recommandé)

```batch
cd c:\Users\tlahirigoyen\Desktop\PROJET\EMAC\Deploy
deployer_sur_reseau.bat
```

**Ce que fait le script** :
- ✅ Vérifie que `App\dist\EMAC\EMAC.exe` existe
- ✅ Teste l'accès au partage `\\s_data`
- ✅ Crée le dossier de destination si nécessaire
- ✅ Copie tout le contenu avec robocopy (182 Mo)
- ✅ Vérifie que EMAC.exe, .env et _internal sont présents
- ✅ Génère un log détaillé : `Deploy\deploiement.log`

**Durée estimée** : 2-5 minutes selon la vitesse réseau

---

### Option B : Copie Manuelle

Si le script échoue, vous pouvez copier manuellement :

```batch
robocopy "c:\Users\tlahirigoyen\Desktop\PROJET\EMAC\App\dist\EMAC" "\\s_data\Bureautique\Services\THOMAS\EMAC" /MIR /R:2 /W:5
```

Ou via l'Explorateur Windows :
1. Ouvrez `c:\Users\tlahirigoyen\Desktop\PROJET\EMAC\App\dist\EMAC`
2. Sélectionnez TOUT (EMAC.exe, .env, _internal)
3. Copiez vers `\\s_data\Bureautique\Services\THOMAS\EMAC`

---

## ✅ Étape 2 : Vérifier le Déploiement

### Vérification Manuelle

Ouvrez `\\s_data\Bureautique\Services\THOMAS\EMAC` et vérifiez :

```
\\s_data\Bureautique\Services\THOMAS\EMAC\
├── EMAC.exe (11 Mo)
├── .env (164 octets)
└── _internal\ (171 Mo)
    ├── python312.dll
    ├── PyQt5\
    ├── mysql\
    └── ... (autres dépendances)
```

**Total attendu** : 182 Mo

---

### Test de Lancement depuis le Réseau

⚠️ **Important** : Ne lancez PAS `EMAC.exe` directement depuis le réseau (lent).

Testez le lanceur :

```batch
cd c:\Users\tlahirigoyen\Desktop\PROJET\EMAC\Deploy
Lancer_EMAC.bat
```

**Résultat attendu** :
```
[1/4] Vérification du réseau...
   ✅ Exécutable trouvé sur le réseau

[2/4] Vérification du cache local...
   📂 Première installation détectée
   Copie vers le cache local...

[3/4] Copie des fichiers (182 Mo)...
   (peut prendre 30-60 secondes)

[4/4] Lancement d'EMAC...
   ✅ Application lancée
```

**Lancements suivants** : 2-3 secondes (depuis le cache)

---

## ✅ Étape 3 : Configurer le Lanceur pour Production

Actuellement, `Lancer_EMAC.bat` pointe vers votre dossier de développement. Pour la production réseau :

### 1. Ouvrir le fichier

```batch
notepad Deploy\Lancer_EMAC.bat
```

### 2. Modifier la ligne 12

**Avant (développement)** :
```batch
set "SOURCE_RESEAU=%~dp0..\App\dist\EMAC"
```

**Après (production)** :
```batch
set "SOURCE_RESEAU=\\s_data\Bureautique\Services\THOMAS\EMAC"
```

### 3. Sauvegarder et Tester

```batch
cd Deploy
Lancer_EMAC.bat
```

Si le lanceur fonctionne correctement, passez à l'étape suivante.

---

## ✅ Étape 4 : Distribuer aux Utilisateurs

### Option 1 : Partager le Lanceur via Réseau

**Créer un dossier accessible** :
```
\\s_data\Bureautique\Services\THOMAS\Lanceurs\
└── Lancer_EMAC.bat
```

**Distribuer aux utilisateurs** :
- Email avec lien : `\\s_data\Bureautique\Services\THOMAS\Lanceurs\Lancer_EMAC.bat`
- Créer un raccourci sur les bureaux
- Ajouter au menu Démarrer

---

### Option 2 : Copier le Lanceur Localement

**Avantages** :
- Fonctionne même si le partage réseau est temporairement inaccessible
- Plus rapide à ouvrir

**Instructions pour chaque utilisateur** :

1. Copier `Lancer_EMAC.bat` vers `C:\Utilisateurs\[nom]\Bureau\`
2. Double-cliquer sur le fichier pour lancer EMAC
3. Premier lancement : 30-60 secondes (création du cache local)
4. Lancements suivants : 2-3 secondes

**⚠️ Important** : Le lanceur doit pointer vers le partage réseau (pas vers votre dossier de développement).

---

## 📊 Performances Attendues

| Scénario | Temps de Lancement |
|----------|-------------------|
| Premier lancement (sans cache) | 30-60 secondes |
| Lancement normal (avec cache) | 2-3 secondes |
| Mise à jour disponible sur réseau | 30-60 secondes (re-copie) |

---

## 🔧 Dépannage

### Problème : "Source réseau inaccessible"

**Cause** : L'utilisateur n'a pas accès à `\\s_data`

**Solutions** :
1. Vérifier les droits d'accès au partage
2. Connecter le lecteur réseau `\\s_data` manuellement
3. Vérifier la connexion VPN si nécessaire

---

### Problème : ".env manquant"

**Cause** : Le fichier `.env` n'a pas été copié sur le réseau

**Solution** :
```batch
copy "c:\Users\tlahirigoyen\Desktop\PROJET\EMAC\App\dist\EMAC\.env" "\\s_data\Bureautique\Services\THOMAS\EMAC\.env"
```

---

### Problème : "Application super lente"

**Cause** : L'utilisateur lance `EMAC.exe` directement au lieu du lanceur

**Solution** :
- ❌ Ne PAS lancer `\\s_data\...\EMAC.exe` directement
- ✅ Toujours utiliser `Lancer_EMAC.bat`

---

## 🔐 Connexion à l'Application

**Identifiants par défaut** :
- Utilisateur : `admin`
- Mot de passe : `admin123`

**⚠️ Recommandation** : Changez le mot de passe admin après la première connexion.

---

## 📝 Logs et Diagnostic

### Logs de Déploiement

```
Deploy\deploiement.log        # Log de deployer_sur_reseau.bat
```

### Logs de Lancement Utilisateur

```
%LOCALAPPDATA%\EMAC_Cache\launcher.log   # Log de Lancer_EMAC.bat
```

**Consulter les logs** :
```batch
type %LOCALAPPDATA%\EMAC_Cache\launcher.log
```

---

## 📞 Support

### Script de Diagnostic

Si un utilisateur rencontre des problèmes :

```batch
cd c:\Users\tlahirigoyen\Desktop\PROJET\EMAC\Deploy
generer_diagnostic.bat
```

Envoyer le fichier `diagnostic_rapport.txt` généré.

---

## ✅ Checklist de Déploiement

- [ ] EMAC.exe compilé avec `build_optimized.bat`
- [ ] `.env` présent dans `App\dist\EMAC\`
- [ ] Dossier `_internal\` complet (171 Mo)
- [ ] Déployé sur `\\s_data\Bureautique\Services\THOMAS\EMAC` (182 Mo total)
- [ ] `Lancer_EMAC.bat` configuré avec le bon chemin réseau
- [ ] Lanceur testé depuis un poste utilisateur
- [ ] Lanceur distribué aux utilisateurs
- [ ] Identifiants de connexion communiqués (admin/admin123)
- [ ] Documentation disponible (ce guide)

---

**Version** : 1.0
**Date** : 23 décembre 2025
**Auteur** : Système EMAC
