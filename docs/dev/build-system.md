# 📦 EMAC - Guide de Build et Déploiement

## 🎯 Objectif

Ce guide explique comment compiler EMAC en **incluant uniquement les fichiers essentiels**, sans tous les fichiers de développement, tests, et scripts inutiles en production.

---

## 🏗️ Structure du Projet Réorganisée

### ✅ Fichiers ESSENTIELS (inclus dans le build)

```
App/
├── core/                           # Code source principal
│   ├── db/
│   │   ├── configbd.py             ⭐ Configuration BDD (CRITIQUE)
│   │   └── import_infos.py         📥 Import de données
│   │
│   ├── services/                   # Logique métier
│   │   ├── auth_service.py         🔐 Authentification
│   │   ├── logger.py               📝 Logging
│   │   ├── evaluation_service.py   📊 Évaluations
│   │   ├── contrat_service.py      📄 Contrats
│   │   ├── absence_service.py      📅 Absences
│   │   └── ...                     (tous les services)
│   │
│   ├── gui/                        # Interface graphique
│   │   ├── main_qt.py              🪟 Fenêtre principale (CRITIQUE)
│   │   ├── ui_theme.py             🎨 Thème
│   │   ├── emac_ui_kit.py          🧩 Composants UI
│   │   └── ...                     (tous les dialogues)
│   │
│   ├── exporters/                  # Exports PDF/Excel
│   │   ├── excel_export.py         📊 Export Excel
│   │   ├── pdf_export.py           📄 Export PDF
│   │   └── log_export.py           📋 Export logs
│   │
│   └── utils/                      # Utilitaires
│       ├── app_paths.py            📂 Gestion chemins (CRITIQUE)
│       └── permission_helper.py    🔒 Permissions
│
├── database/                       # Base de données
│   ├── schema/
│   │   └── bddemac.sql             💾 Schéma BDD
│   └── migrations/
│       └── *.sql                   🔄 Migrations
│
├── config/                         # Configuration
│   ├── .env.example                📝 Template config
│   └── configure_db.bat            🔧 Script config
│
├── .env                            🔐 Config BDD (OBLIGATOIRE)
├── requirements.txt                📦 Dépendances Python
└── EMAC_optimized.spec             ⚙️ Configuration PyInstaller
```

### ❌ Fichiers EXCLUS (non inclus dans le build)

```
App/
├── core/db/
│   └── insert_*.py                 🚫 Scripts de peuplement BDD
│
├── scripts/                        🚫 Scripts de développement/migration
│   ├── cleanup_*.py
│   ├── fix_*.py
│   ├── install_*.py
│   ├── test_*.py
│   └── ...
│
├── tests/                          🚫 Tests unitaires/intégration
│   ├── test_*.py
│   └── run_all_tests.py
│
├── build/                          🚫 Fichiers temporaires de build
├── dist/                           🚫 Builds précédents
├── dist_nuitka/                    🚫 Builds Nuitka
├── logs/                           🚫 Logs générés (créés par l'app)
├── documents/                      🚫 Documents générés (créés par l'app)
│
├── demo_ui_kit.py                  🚫 Démonstration UI
├── test_startup_time.py            🚫 Test de performance
├── BUILD_INFO.txt                  🚫 Info de build
├── nuitka-crash-report.xml         🚫 Rapport de crash
│
└── build_*.bat                     🚫 Autres scripts de build
    (sauf build_clean.bat et build_optimized.bat)
```

---

## 🚀 Compilation

### Option 1: Build Propre (RECOMMANDÉ)

Utilise le nouveau script qui nettoie et compile proprement:

```bash
cd App
build_clean.bat
```

**Ce que fait ce script:**
1. ✅ Vérifie les prérequis (main_qt.py, .env, .spec)
2. 🧹 Nettoie les anciens builds et __pycache__
3. 🏗️ Compile avec PyInstaller (mode one-folder)
4. 📋 Copie .env et fichiers SQL
5. 🗑️ Supprime les fichiers non-essentiels de dist/
6. 📊 Génère un rapport détaillé

### Option 2: Build Optimisé (ancien script)

```bash
cd App
build_optimized.bat
```

---

## 📋 Fichiers Importants

### 1. BUILD_MANIFEST.txt

Liste **exhaustive** de tous les fichiers inclus/exclus du build.
📖 Consultez ce fichier pour comprendre ce qui est embarqué dans l'exe.

### 2. EMAC_optimized.spec

Configuration PyInstaller avec:
- ✅ `hiddenimports`: Modules Python à inclure explicitement
- ❌ `excludes`: Modules à exclure (tests, dev tools, etc.)
- ⚙️ `optimize=2`: Optimisation bytecode (supprime docstrings)

**Modifications importantes:**
```python
excludes=[
    # Scripts de dev exclus
    'scripts',
    'tests',
    'demo_ui_kit',
    'test_startup_time',

    # Scripts d'insertion BDD exclus
    'core.db.insert_atelier',
    'core.db.insert_date',
    'core.db.insert_polyvalence',
    # ...
]
```

### 3. .gitignore

Mis à jour pour ignorer:
- Tous les builds (`build/`, `dist/`, `dist_nuitka/`)
- Fichiers temporaires (`.pyc`, `__pycache__`)
- Configuration sensible (`.env`)
- Documents générés (`documents/`, `logs/`)

---

## 🎯 Résultat Final

Après compilation avec `build_clean.bat`:

```
dist/EMAC/
├── EMAC.exe                    🚀 Exécutable principal
├── .env                        🔐 Configuration BDD (copié automatiquement)
│
├── _internal/                  📦 Bibliothèques Python + DLLs
│   ├── python*.dll
│   ├── PyQt5/
│   ├── mysql/
│   └── ...
│
├── database/                   💾 Schémas SQL (optionnel)
│   ├── schema/
│   └── migrations/
│
├── logs/                       📝 Dossier de logs (vide au départ)
└── documents/                  📄 Documents générés (vide au départ)
```

**Taille typique:** ~150-250 MB (selon les dépendances)

---

## ✅ Vérifications Avant Déploiement

### 1. Tester localement

```bash
cd dist\EMAC
EMAC.exe
```

### 2. Vérifier le .env

```bash
# Le fichier doit contenir:
EMAC_DB_PASSWORD=votre_mot_de_passe
EMAC_DB_HOST=localhost
EMAC_DB_USER=root
EMAC_DB_NAME=emac_db
```

### 3. Vérifier les connexions BDD

- L'application doit se connecter à MySQL
- Vérifier que le schéma `emac_db` existe
- Tester l'authentification (login admin)

---

## 📦 Déploiement sur Réseau

### Étape 1: Préparer le package

```bash
# Copier TOUT le dossier dist\EMAC\ sur le serveur réseau
xcopy /E /I dist\EMAC Z:\Applications\EMAC
```

### Étape 2: Configurer le .env sur le serveur

```bash
# Éditer Z:\Applications\EMAC\.env avec les paramètres du serveur
EMAC_DB_HOST=serveur-mysql.local
EMAC_DB_USER=emac_user
EMAC_DB_PASSWORD=mot_de_passe_production
```

### Étape 3: Créer un lanceur réseau

Créez un raccourci `EMAC.lnk` ou utilisez `launcher_reseau.bat`:

```batch
@echo off
REM Lancer EMAC depuis le réseau
Z:\Applications\EMAC\EMAC.exe
```

---

## 🐛 Dépannage

### ❌ Erreur: "Module not found"

**Cause:** Un module Python n'est pas inclus dans le build.

**Solution:** Ajoutez-le dans `EMAC_optimized.spec` → `hiddenimports`:

```python
hiddenimports=[
    # ...
    'nom_du_module_manquant',
]
```

### ❌ Erreur: "Can't connect to MySQL server"

**Cause:** Le fichier `.env` est manquant ou mal configuré.

**Solution:**
1. Vérifiez que `dist\EMAC\.env` existe
2. Vérifiez les paramètres de connexion
3. Testez la connexion MySQL manuellement

### ❌ L'exe est trop volumineux (>500 MB)

**Cause:** Des bibliothèques inutiles sont incluses.

**Solution:** Ajoutez-les dans `excludes` du fichier `.spec`:

```python
excludes=[
    'matplotlib',  # Si non utilisé
    'scipy',       # Si non utilisé
    # ...
]
```

---

## 📊 Comparaison des Scripts de Build

| Script                | Taille | Vitesse | Propreté | Recommandé |
|-----------------------|--------|---------|----------|------------|
| `build_clean.bat`     | ⭐⭐⭐  | ⭐⭐    | ⭐⭐⭐   | ✅ OUI     |
| `build_optimized.bat` | ⭐⭐   | ⭐⭐⭐  | ⭐⭐     | ⚠️ Ancien  |
| `build_nuitka.bat`    | ⭐     | ⭐      | ⭐       | ❌ Instable|

---

## 🔒 Sécurité

### ⚠️ IMPORTANT: Ne JAMAIS commiter .env

Le fichier `.env` contient des mots de passe et **NE DOIT JAMAIS** être versionné dans Git.

**Déjà configuré:**
- ✅ `.env` est dans `.gitignore`
- ✅ Seul `.env.example` est versionné (template)

### 🔐 Bonnes pratiques

1. **Développement:** Utilisez `.env` local avec mot de passe dev
2. **Production:** Créez un `.env` séparé sur le serveur avec mot de passe production
3. **Backup:** Sauvegardez `.env` de production dans un gestionnaire de mots de passe (KeePass, etc.)

---

## 📚 Fichiers de Documentation

| Fichier                | Description                          |
|------------------------|--------------------------------------|
| `BUILD_MANIFEST.txt`   | Liste complète des fichiers inclus   |
| `BUILD_README.md`      | Ce guide (compilation/déploiement)   |
| `CLAUDE.md`            | Instructions pour Claude Code        |
| `README.md`            | Documentation générale du projet     |

---

## 🆘 Support

En cas de problème:

1. 📖 Consultez [BUILD_MANIFEST.txt](BUILD_MANIFEST.txt) pour voir ce qui est inclus
2. 🔍 Vérifiez les logs dans `dist\EMAC\logs\`
3. 🐛 Activez `console=True` dans `EMAC_optimized.spec` pour voir les erreurs
4. 📧 Contactez le support technique

---

**Dernière mise à jour:** 2025-12-24
**Version EMAC:** 1.0
**Auteur:** Équipe EMAC
