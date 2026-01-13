# Fix Crash .exe EMAC - 2026-01-13

## 🔴 Problème identifié

L'application crash après la connexion dans la version .exe compilée avec PyInstaller, alors qu'elle fonctionne correctement en local.

## 🔧 Causes probables

1. **Exclusions trop agressives dans EMAC.spec** :
   - `asyncio` était exclu → requis par Python 3.x
   - `concurrent.futures` était exclu → utilisé par QThreadPool
   - `unittest` était exclu → dépendances peuvent en avoir besoin
   - `email` était exclu → module système requis

2. **Modules manquants** :
   - Modules critiques pour threading (`queue`, `concurrent`, etc.)
   - Modules système de base (`traceback`, `os`, `sys`)

## ✅ Corrections appliquées dans [EMAC.spec](EMAC.spec)

### 1. Modules retirés de la liste EXCLUDES

```python
# AVANT (ligne 95-96) - CASSAIT L'APPLICATION
'asyncio',
'concurrent.futures',
'unittest',
'email',

# APRÈS - Ces modules NE SONT PLUS exclus
```

### 2. Modules ajoutés dans HIDDEN_IMPORTS

```python
# Modules critiques ajoutés (lignes 178-188)
'traceback',
'os',
'sys',
'queue',              # Threading
'concurrent',         # Module parent
'concurrent.futures', # QThreadPool
'email',              # Modules système
'unittest',           # Dépendances
```

### 3. Mode debug temporaire activé

```python
# EXE configuration (lignes 252-254)
strip=False,    # ⚠️ Désactivé pour debug
console=True,   # ⚠️ Console activée pour voir les erreurs
```

## 📋 Procédure de test

### Étape 1 : Nettoyer les anciens builds

```bash
cd c:\Users\tlahirigoyen\Desktop\PROJET\EMAC

# Supprimer les dossiers de build
rmdir /S /Q build dist

# Supprimer les fichiers de cache PyInstaller
del /Q *.spec.pyc
```

### Étape 2 : Compiler avec le nouveau .spec

```bash
# Activer l'environnement virtuel si nécessaire
# venv\Scripts\activate

# Compiler
pyinstaller EMAC.spec

# Temps estimé : 2-3 minutes
```

### Étape 3 : Copier le fichier .env (CRITIQUE)

```bash
# IMPORTANT : L'exe a besoin du fichier .env pour la connexion DB
copy App\.env dist\EMAC\.env
```

### Étape 4 : Tester l'application

```bash
cd dist\EMAC
EMAC.exe
```

**Attendu** :
- Une fenêtre console s'ouvre (mode debug)
- L'application démarre
- Vous entrez les identifiants
- **Si crash** : la console affichera l'erreur exacte
- **Si OK** : l'application se connecte et charge le dashboard

### Étape 5 : Analyser les résultats

#### ✅ Si l'application fonctionne :

1. Désactiver le mode debug dans [EMAC.spec](EMAC.spec) :
   ```python
   strip=True,     # Réactiver l'optimisation
   console=False,  # Désactiver la console
   ```

2. Recompiler une version finale :
   ```bash
   pyinstaller EMAC.spec
   copy App\.env dist\EMAC\.env
   ```

#### 🔴 Si l'application crash toujours :

**Relevez l'erreur exacte** dans la console et envoyez-la moi. Par exemple :
```
Traceback (most recent call last):
  File "core/gui/main_qt.py", line XXX
  ModuleNotFoundError: No module named 'XXX'
```

## 🎯 Diagnostics supplémentaires

### Test 1 : Vérifier les modules inclus

Après compilation, vérifiez que les modules critiques sont présents :

```bash
cd dist\EMAC
python -c "import sys; print('\n'.join(sys.path))"
```

### Test 2 : Tester l'import des modules

```bash
cd dist\EMAC
python -c "import concurrent.futures; import queue; import unittest; print('OK')"
```

### Test 3 : Lancer avec les logs maximum

Dans [main_qt.py](App/core/gui/main_qt.py), vous pouvez ajouter en haut du fichier :

```python
import sys
import traceback

# Configurer logging détaillé
import logging
logging.basicConfig(level=logging.DEBUG)

# Capturer toutes les exceptions
def exception_hook(exctype, value, tb):
    print("=" * 80)
    print("EXCEPTION NON GÉRÉE:")
    print("=" * 80)
    traceback.print_exception(exctype, value, tb)
    print("=" * 80)

sys.excepthook = exception_hook
```

## 📊 Comparaison des exclusions

| Module | Avant | Après | Justification |
|--------|-------|-------|---------------|
| `asyncio` | ❌ Exclu | ✅ Inclus | Requis par Python 3.x |
| `concurrent.futures` | ❌ Exclu | ✅ Inclus | Utilisé par QThreadPool |
| `unittest` | ❌ Exclu | ✅ Inclus | Dépendances système |
| `email` | ❌ Exclu | ✅ Inclus | Module système requis |
| `pandas` | ❌ Exclu | ❌ Exclu | Non utilisé (OK) |
| `numpy` | ❌ Exclu | ❌ Exclu | Non utilisé (OK) |

## 🚀 Après la correction

Une fois que l'application fonctionne avec `console=True`, vous devez :

1. **Désactiver la console** pour la version finale
2. **Réactiver strip** pour optimiser la taille
3. **Tester à nouveau** pour confirmer

```python
# Version finale dans EMAC.spec
strip=True,
console=False,
```

## 📁 Fichiers modifiés

- ✅ [EMAC.spec](EMAC.spec) - Configuration PyInstaller corrigée
- 📝 [PATCH_ANTI_CRASH.md](PATCH_ANTI_CRASH.md) - Patch précédent (référence)
- 📝 Ce fichier - Procédure de correction

## 💡 Notes importantes

1. **Toujours copier le .env** dans le dossier dist/EMAC/ après compilation
2. **Ne jamais exclure** `concurrent.futures`, `asyncio`, `unittest` ou `email`
3. **Tester avec console=True** d'abord avant de faire une version finale
4. **Le mode console** n'affecte que l'affichage d'une fenêtre cmd, pas les performances

## 🔗 Ressources

- [PyInstaller - When Things Go Wrong](https://pyinstaller.org/en/stable/when-things-go-wrong.html)
- [docs/dev/build-optimization.md](docs/dev/build-optimization.md) - Guide de build
- [CLAUDE.md](CLAUDE.md) - Instructions du projet
