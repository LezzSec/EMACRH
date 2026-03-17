# Guide d'optimisation du démarrage de l'exécutable EMAC

## Problème identifié

**Temps de démarrage actuel : ~15 secondes** 

### Causes principales :
1. **Mode "one-file"** : L'exécutable décompresse 50-100 Mo dans un dossier temporaire à chaque lancement
2. **Windows Defender** : Scanne tous les fichiers extraits
3. **Imports lourds** : Tous les modules PyQt5 sont chargés au démarrage

---

## ✅ Solutions implémentées

### 1. **Mode "one-folder" (gain : ~10-12 secondes)**

**Avant (one-file)** :
```
EMAC.exe (80 Mo)
└─ Extrait tout dans %TEMP% à chaque lancement → 15 secondes
```

**Après (one-folder)** :
```
EMAC/
├── EMAC.exe (petit lanceur, ~5 Mo)
├── Python DLLs
└── Librairies (déjà extraites) → ~2-3 secondes
```

### 2. **Imports paresseux (gain : ~500ms)**
Les dialogues ne sont plus importés au démarrage, mais uniquement à l'ouverture.

### 3. **Pool de connexions MySQL (gain : ~200ms)**
Réutilisation des connexions base de données.

### 4. **Requêtes SQL optimisées (gain : ~100ms)**
Une seule requête au lieu de deux.

### 5. **Exclusion de modules inutiles (gain : ~1-2 secondes)**
Tkinter, matplotlib, tests exclus du build.

---

## Comment recompiler l'exécutable optimisé

### Option A : Script automatique (recommandé)

```batch
cd App
build_optimized.bat
```

### Option B : Commande manuelle

```batch
cd App
pyinstaller EMAC_optimized.spec --clean --noconfirm
```

---

## Résultat attendu

| Version | Taille | Temps de démarrage | Notes |
|---------|--------|-------------------|-------|
| Ancienne (one-file) | ~80 Mo | **15 secondes** | Tout extrait à chaque fois |
| **Nouvelle (one-folder)** | ~120 Mo (dossier) | **2-3 secondes** | Pas d'extraction |

**Gain total : ~12 secondes (80% plus rapide)** 

---

## Bonus : Exclure du Windows Defender

Pour gagner encore 1-2 secondes, ajoutez le dossier aux exclusions :

1. **Paramètres Windows** → **Mise à jour et sécurité**
2. **Sécurité Windows** → **Protection contre les virus et menaces**
3. **Gérer les paramètres** → **Exclusions**
4. **Ajouter une exclusion** → **Dossier** → `C:\...\EMAC\App\dist\EMAC`

---

## Dépannage

### L'exécutable ne se lance pas

**Erreur "Module not found"** :
- Vérifiez que tous les imports paresseux sont dans `hiddenimports` (ligne 11-21 de `EMAC_optimized.spec`)

**Fenêtre console apparaît** :
- Changez `console=False` dans le .spec (déjà fait)

**Erreur MySQL** :
- Vérifiez que le service MySQL est démarré
- Le pool de connexions gère automatiquement les reconnexions

### L'exécutable est trop gros

Supprimez les modules inutiles dans `excludes` :
- `pandas` si non utilisé pour l'export
- `reportlab` si pas de génération PDF
- `openpyxl` si pas d'export Excel

---

## Fichiers modifiés

### Code source (optimisations runtime)
- ✅ [`App/core/gui/main_qt.py`](App/core/gui/main_qt.py) - Imports paresseux
- ✅ [`App/core/db/configbd.py`](App/core/db/configbd.py) - Pool de connexions

### Build (optimisations compilation)
- ✅ [`App/EMAC_optimized.spec`](App/EMAC_optimized.spec) - Config PyInstaller optimisée
- ✅ [`App/build_optimized.bat`](App/build_optimized.bat) - Script de build automatique

---

## Distribution

### Pour partager l'application :

1. **Zippez le dossier complet** :
   ```
   dist/EMAC/  →  EMAC_v1.0.zip
   ```

2. **Instructions utilisateur** :
   - Extraire le ZIP
   - Double-cliquer sur `EMAC.exe`
   - (Optionnel) Créer un raccourci sur le bureau

### Avantages du mode one-folder :
- ✅ Démarrage ultra-rapide
- ✅ Mise à jour facile (remplacer juste les fichiers modifiés)
- ✅ Moins de faux positifs antivirus
- ❌ Plus gros à distribuer (~120 Mo vs 80 Mo)

**Compromis acceptable** : +40 Mo pour gagner 12 secondes de démarrage

---

## Prochaines étapes

Si vous voulez optimiser encore plus :

1. **Compilation Cython** : Compiler les modules Python critiques en C
2. **Lazy loading avancé** : Charger PyQt5 en arrière-plan
3. **Pré-connexion MySQL** : Garder une connexion ouverte en permanence

Mais avec les optimisations actuelles, vous devriez déjà être à **~2-3 secondes** ! 
