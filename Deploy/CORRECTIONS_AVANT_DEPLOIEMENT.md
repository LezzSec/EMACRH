# Corrections nécessaires avant déploiement

## ❌ Problèmes détectés par le test

### 1. Fichier `.env` manquant dans `dist\EMAC\`

**Symptôme** :
```
[TEST 2/7] Verification du fichier .env...
   [ERREUR] .env introuvable
            L'application ne pourra pas se connecter a la base de donnees
```

**Cause** :
Le script `build_optimized.bat` devrait copier le `.env` automatiquement, mais cela n'a pas été fait lors de la dernière compilation.

**Solution TEMPORAIRE (déjà appliquée)** :
```batch
copy App\.env App\dist\EMAC\.env
```

**Solution PERMANENTE** :
Recompiler l'application avec le script qui copie automatiquement le `.env` :

```batch
cd App
build_optimized.bat
```

Le script `build_optimized.bat` contient déjà le code pour copier le `.env` (lignes 29-44).

---

### 2. SOURCE_RESEAU non configuré dans `Lancer_EMAC.bat`

**Symptôme** :
```
[TEST 4/7] Verification du lanceur reseau...
   [OK] Lancer_EMAC.bat trouve
   [ATTENTION] SOURCE_RESEAU non configure (valeur par defaut)
               Modifiez la ligne 10 de Lancer_EMAC.bat avant deploiement
```

**Cause** :
Le fichier `Lancer_EMAC.bat` contient encore la valeur d'exemple `\\SERVEUR\Partage\EMAC`.

**Solution** :
Avant de distribuer le lanceur, modifiez la ligne 10 de `Deploy\Lancer_EMAC.bat` :

```batch
REM Remplacer cette ligne :
set "SOURCE_RESEAU=\\SERVEUR\Partage\EMAC"

REM Par votre vrai chemin réseau, par exemple :
set "SOURCE_RESEAU=\\serveur-fichiers\Applications\EMAC"
```

---

## ✅ Checklist avant déploiement

Avant de déployer en production, assurez-vous que :

- [ ] **Recompiler l'application** pour que le `.env` soit copié automatiquement :
  ```batch
  cd App
  build_optimized.bat
  ```

- [ ] **Vérifier que `.env` est présent** dans `App\dist\EMAC\` :
  ```batch
  dir App\dist\EMAC\.env
  ```

- [ ] **Configurer le chemin réseau** dans `Deploy\Lancer_EMAC.bat` (ligne 10)

- [ ] **Relancer le test de déploiement** :
  ```batch
  cd Deploy
  test_deploiement.bat
  ```

- [ ] **Vérifier que tous les tests passent** (7/7)

---

## 🚀 Procédure de déploiement complète

### Étape 1 : Recompilation

```batch
cd c:\Users\tlahirigoyen\Desktop\PROJET\EMAC\App
build_optimized.bat
```

**Vérifications** :
- Le script doit afficher : `✅ EXECUTABLE CREE : dist\EMAC\EMAC.exe`
- Le fichier `dist\EMAC\.env` doit exister

---

### Étape 2 : Configuration du lanceur

1. Ouvrir `Deploy\Lancer_EMAC.bat` dans un éditeur
2. Modifier la ligne 10 :
   ```batch
   set "SOURCE_RESEAU=\\VotreChemin\Reseau\EMAC"
   ```
3. Sauvegarder

---

### Étape 3 : Tests de validation

```batch
cd Deploy
test_deploiement.bat
```

**Résultat attendu** :
```
================================================
  RESUME DES TESTS
================================================

  Tests reussis : 7/7
  Tests echoues : 0/7

  [SUCCES] TOUS LES TESTS SONT PASSES
```

---

### Étape 4 : Déploiement sur le réseau

```batch
REM Copier sur le partage réseau
robocopy "App\dist\EMAC" "\\VotreChemin\Reseau\EMAC" /MIR
```

---

### Étape 5 : Distribution du lanceur

**Option A : GPO (recommandé)**
- Déployez `Deploy\Lancer_EMAC.bat` via une stratégie de groupe

**Option B : Manuel**
- Envoyez `Deploy\Lancer_EMAC.bat` aux utilisateurs
- Demandez-leur de le copier sur leur bureau

---

## 📞 En cas de problème

Si le test `test_deploiement.bat` échoue après recompilation :

1. **Vérifiez manuellement** :
   ```batch
   dir App\dist\EMAC\.env
   dir App\dist\EMAC\EMAC.exe
   dir App\dist\EMAC\_internal
   ```

2. **Consultez les logs** de compilation dans la console

3. **Vérifiez les variables d'environnement** :
   ```batch
   type App\.env
   ```
   Le fichier doit contenir `EMAC_DB_PASSWORD=...`

4. **Consultez la documentation** :
   - [Deploy/README_DEPLOIEMENT.md](README_DEPLOIEMENT.md)
   - [docs/dev/deploiement-reseau.md](../docs/dev/deploiement-reseau.md)

---

**Dernière mise à jour** : 23 décembre 2025
