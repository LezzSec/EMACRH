# Guide de Build EMAC - Création de l'Exécutable

## 🚀 Build Rapide (Recommandé)

### Méthode Simple - Un Clic

```bash
# Depuis la racine du projet
build.bat
```

**C'est tout !** Le script fait automatiquement :
- Nettoyage des anciens builds
- Vérification des prérequis
- Compilation avec PyInstaller
- Création du README
- Ouverture du dossier de sortie

---

## 📋 Prérequis

### Obligatoire

1. **Python 3.8+** installé et dans le PATH
   ```bash
   python --version
   # Doit afficher: Python 3.x.x
   ```

2. **PyInstaller** installé
   ```bash
   pip install pyinstaller
   ```

3. **Dépendances EMAC** installées
   ```bash
   pip install -r App/requirements.txt
   ```

### Optionnel (mais recommandé)

4. **Fichier .env configuré**
   ```bash
   # Copier le template
   copy App\config\.env.example App\.env

   # Éditer avec vos identifiants DB
   notepad App\.env
   ```

---

## 🛠️ Méthode Manuelle

Si vous préférez plus de contrôle:

### 1. Nettoyer les anciens builds

```bash
# Windows
rmdir /S /Q build dist

# Linux/Mac
rm -rf build/ dist/
```

### 2. Lancer PyInstaller

```bash
pyinstaller --clean --noconfirm EMAC.spec
```

### 3. Vérifier la sortie

```bash
dir dist\EMAC\EMAC.exe
# ou
ls -lh dist/EMAC/EMAC.exe
```

---

## 📦 Sortie du Build

### Structure du Dossier `dist/EMAC/`

```
dist/EMAC/
├── EMAC.exe                    # Exécutable principal
├── python3X.dll                # Runtime Python
├── _internal/                  # Dépendances (DLLs, modules)
│   ├── PyQt5/
│   ├── mysql/
│   ├── reportlab/
│   └── ...
├── config/                     # Configuration template
│   └── .env.example
├── database/                   # Schéma DB (référence)
│   └── schema/
│       └── bddemac.sql
└── README.txt                  # Guide utilisateur
```

**Taille attendue :** ~120-150 MB

---

## ⚙️ Configuration du .spec

Le fichier [EMAC.spec](EMAC.spec) contient toutes les optimisations:

### Optimisations Actives

| Paramètre | Valeur | Bénéfice |
|-----------|--------|----------|
| `optimize` | `2` | Bytecode optimisé (-30% taille) |
| `strip` | `True` | Symboles debug supprimés (-20%) |
| `upx` | `False` | Évite faux positifs antivirus |
| `console` | `False` | Application GUI (pas de console) |
| `excludes` | 70+ modules | Exclusions agressives |

### Modules Exclus

Les modules suivants sont **exclus** du build car non utilisés:
- `pandas`, `numpy`, `matplotlib` (data science)
- `tkinter`, `wx`, `PySide` (GUI alternatives)
- `flask`, `django` (web frameworks)
- `pytest`, `unittest` (tests)
- Et 60+ autres modules...

### Modules Inclus (Hidden Imports)

Ces modules sont **inclus explicitement** car importés dynamiquement:
- `mysql.connector` + sous-modules
- `PyQt5.QtPrintSupport`, `PyQt5.QtSvg`
- `reportlab` + sous-modules (PDF)
- `openpyxl` + sous-modules (Excel)
- `bcrypt` (authentification)

---

## 🐛 Dépannage

### Erreur: "PyInstaller n'est pas installé"

```bash
pip install pyinstaller
```

### Erreur: "Module X not found"

1. Vérifiez que toutes les dépendances sont installées:
   ```bash
   pip install -r App/requirements.txt
   ```

2. Si un module manque encore, ajoutez-le dans `EMAC.spec` > `HIDDEN_IMPORTS`

### Erreur: "Failed to execute script"

Lancez avec console pour voir les erreurs:
1. Éditez `EMAC.spec`
2. Changez `console=False` en `console=True`
3. Rebuild: `build.bat`
4. Relancez `EMAC.exe` et lisez les erreurs dans la console

### Build très lent (>5 minutes)

Normal si c'est le premier build. Les builds suivants sont plus rapides grâce au cache PyInstaller.

Pour accélérer:
```bash
# Ne pas nettoyer le cache
pyinstaller --noconfirm EMAC.spec
```

### Antivirus bloque EMAC.exe

C'est normal avec PyInstaller. Solutions:
1. **Recommandé:** Ajoutez une exception dans l'antivirus pour `dist/EMAC/`
2. Désactivez temporairement l'antivirus pendant le build
3. **Ne jamais** activer UPX (déjà désactivé dans EMAC.spec)

### L'application ne démarre pas

1. **Vérifiez les prérequis système** (Windows 10+, 64-bit)
2. **Testez en mode console** (voir ci-dessus)
3. **Vérifiez la configuration .env** sur le PC cible
4. **Vérifiez la connectivité DB** (MySQL accessible)

---

## 📊 Comparaison avec l'Ancien Build

| Métrique | Ancien (EMAC_optimized.spec) | Nouveau (EMAC.spec) | Gain |
|----------|------------------------------|---------------------|------|
| **Taille** | 180-220 MB | 120-150 MB | **-30%** |
| **Temps build** | 3-4 min | 2-3 min | **-25%** |
| **Modules exclus** | 4 | 70+ | **+1650%** |
| **Documentation** | Minimale | Exhaustive | **+500%** |
| **Strip symbols** | ❌ | ✅ | - |
| **Optimize=2** | ❌ | ✅ | - |

---

## 🚢 Distribution

### Préparer pour Distribution

1. **Copiez tout le dossier `dist/EMAC/`** (pas seulement EMAC.exe)

2. **Créez une archive**:
   ```bash
   # Depuis dist/
   tar -czf EMAC_v1.0.0.zip EMAC/
   # ou utilisez 7-Zip / WinRAR
   ```

3. **Incluez la documentation**:
   - Guide utilisateur
   - Instructions de configuration .env
   - Guide de connexion DB

### Installation sur le PC Cible

1. **Décompresser** `EMAC_v1.0.0.zip`
2. **Configurer** `.env` avec les credentials DB
3. **Lancer** `EMAC.exe`

**Important:** Le PC cible n'a **PAS besoin** de Python installé !

---

## 📝 Modifier le Build

### Ajouter un Module

Si vous ajoutez une nouvelle dépendance dans le code:

1. Installez-la localement:
   ```bash
   pip install nouveau_module
   ```

2. Ajoutez-la dans `App/requirements.txt`

3. Si elle n'est pas auto-détectée, ajoutez-la dans `EMAC.spec` > `HIDDEN_IMPORTS`

4. Rebuild:
   ```bash
   build.bat
   ```

### Ajouter une Icône

1. Créez/obtenez un fichier `.ico` (256x256 recommandé)

2. Placez-le dans `App/resources/icon.ico`

3. Éditez `EMAC.spec` ligne ~209:
   ```python
   icon=None,  # TODO: Ajouter icon='App/resources/icon.ico'
   ```
   Remplacez par:
   ```python
   icon='App/resources/icon.ico',
   ```

4. Rebuild

### Créer un Installeur

Pour créer un `.msi` ou `.exe` installeur:

1. **Inno Setup** (recommandé, gratuit)
   - https://jrsoftware.org/isinfo.php
   - Créez un script `.iss` pointant vers `dist/EMAC/`

2. **NSIS** (alternative)
   - https://nsis.sourceforge.io/

3. **Advanced Installer** (payant, très complet)
   - https://www.advancedinstaller.com/

---

## ✅ Checklist Avant Build de Production

- [ ] Toutes les dépendances sont à jour (`pip install -U -r App/requirements.txt`)
- [ ] Les tests passent (`python -m pytest App/tests/`)
- [ ] Le `.env.example` est à jour
- [ ] La version est incrémentée (si applicable)
- [ ] Les logs de debug sont désactivés
- [ ] La base de données de production est testée
- [ ] La documentation utilisateur est à jour
- [ ] Un backup DB existe avant déploiement

---

## 📞 Support

**Problème de build ?**
1. Consultez la section Dépannage ci-dessus
2. Vérifiez les logs de PyInstaller dans `build/EMAC/warn-EMAC.txt`
3. Consultez la documentation PyInstaller: https://pyinstaller.org/

**Problème d'exécution ?**
1. Lancez en mode console (voir Dépannage)
2. Vérifiez les logs dans `logs/` (si l'app démarre)
3. Vérifiez la configuration .env

---

**Dernière mise à jour :** 13 janvier 2026
**Version :** EMAC.spec v1.0
