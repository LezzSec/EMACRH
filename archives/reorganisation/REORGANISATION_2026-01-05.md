# 📋 Réorganisation du Projet EMAC - 2026-01-05

## 🎯 Objectif

Réorganisation complète de la structure du projet EMAC pour améliorer la maintenabilité, la clarté et suivre les meilleures pratiques Python.

---

## 📊 Résumé des Changements

### Avant (v1.x)
```
EMAC/
├── App/
│   ├── core/
│   │   ├── db/
│   │   ├── services/
│   │   ├── gui/
│   │   ├── exporters/
│   │   └── utils/
│   ├── database/
│   ├── tests/
│   ├── scripts/
│   └── [nombreux fichiers .bat, .spec, .md]
├── docs/
├── Deploy/
└── temp_archives/
```

### Après (v2.0)
```
EMAC/
├── src/emac/           # Package Python principal
├── tests/              # Tests organisés
├── database/           # Schémas et migrations
├── tools/              # Outils de dev catégorisés
├── build/              # Système de build centralisé
├── deploy/             # Déploiement
├── docs/               # Documentation structurée
├── config/             # Configuration
└── archives/           # Fichiers historiques
```

---

## 🔄 Changements Principaux

### 1. Code Source: `App/core/` → `src/emac/`

**Nouveau Package Python Standard**

| Ancien | Nouveau |
|--------|---------|
| `App/core/db/configbd.py` | `src/emac/db/connection.py` |
| `App/core/services/*_service.py` | `src/emac/services/*.py` |
| `App/core/gui/main_qt.py` | `src/emac/gui/app.py` |
| `App/core/gui/ui_theme.py` | `src/emac/gui/components/theme.py` |

**Structure GUI Réorganisée:**
- `gui/components/` - Composants réutilisables (theme, ui_kit)
- `gui/dialogs/` - Fenêtres de dialogue
- `gui/views/` - Vues principales
- `gui/widgets/` - Widgets personnalisés

### 2. Tests: Organisés par Type

```
tests/
├── unit/               # Tests unitaires
│   └── test_services/
├── integration/        # Tests d'intégration
└── ui/                 # Tests UI
```

**Changements:**
- `App/tests/test_*.py` → `tests/unit/` ou `tests/integration/`
- `run_all_tests.py` → `run_tests.py`
- Ajout de `conftest.py` pour configuration pytest

### 3. Outils: Catégorisés par Fonction

```
tools/
├── setup/              # Installation et configuration
├── maintenance/        # Scripts de maintenance
├── migration/          # Outils de migration
├── diagnostics/        # Diagnostic
└── security/           # Sécurité
```

**24 scripts** réorganisés depuis `App/scripts/` en catégories logiques.

### 4. Build: Système Centralisé

```
build/
├── configs/            # emac.spec (PyInstaller)
├── scripts/            # build.bat, clean.bat
└── output/             # Builds générés
```

**Consolidation:**
- 5 fichiers `.spec` → 1 seul: `build/configs/emac.spec`
- 7 scripts `.bat` → 2 principaux: `build.bat`, `clean.bat`

### 5. Base de Données: Structure Claire

```
database/
├── schema/
│   ├── current/        # Schémas actuels
│   └── archive/        # Anciennes versions
├── migrations/
│   ├── applied/        # Migrations appliquées
│   └── rollback/       # Scripts rollback
├── backups/
│   ├── latest/         # Dernière sauvegarde
│   └── archive/        # Anciennes sauvegardes
└── seeds/
    ├── dev/            # Données de dev
    └── prod/           # Données de prod
```

**Fichiers réorganisés:**
- Schéma principal: `00_main_schema.sql`
- Historique: `01_historique.sql`
- 7 backups archivés

### 6. Documentation: Par Audience

```
docs/
├── getting-started/    # Démarrage rapide
├── user-guides/        # Guides utilisateur
├── developer/          # Documentation développeur
├── deployment/         # Guides de déploiement
├── security/           # Documentation sécurité
└── features/           # Fonctionnalités
```

**13 fichiers MD** de la racine déplacés et organisés par thème.

### 7. Déploiement: Organisation par Type

```
deploy/
├── local/              # Déploiement local
├── network/            # Déploiement réseau
└── diagnostics/        # Outils diagnostic
```

### 8. Archives: Historique Préservé

```
archives/
├── code/               # Code legacy
│   ├── old_specs/
│   └── old_build_scripts/
├── database/           # Anciennes sauvegardes
├── docs/               # Notes de réorganisation
└── builds/             # Anciennes versions
```

---

## 🔧 Migration des Imports

### Changements d'Imports

**Base de Données:**
```python
# Avant
from core.db.configbd import get_connection

# Après
from emac.db.connection import get_connection
```

**Services:**
```python
# Avant
from core.services.evaluation_service import calculate_next_evaluation
from core.services.calendrier_service import compute_dates

# Après
from emac.services.evaluation import calculate_next_evaluation
from emac.services.calendar import compute_dates
```

**GUI:**
```python
# Avant
from core.gui.ui_theme import EmacTheme
from core.gui.main_qt import MainWindow

# Après
from emac.gui.components.theme import EmacTheme
from emac.gui.app import MainWindow
```

### Script de Migration Automatique

Un script de migration automatique est disponible:

```bash
cd tools/migration
python migrate_imports.py
```

Ce script:
- ✅ Scanne tous les fichiers `.py`
- ✅ Convertit automatiquement les imports
- ✅ Génère un rapport de migration
- ✅ Préserve les fichiers originaux

---

## 🚀 Lancement de l'Application

### Avant
```bash
cd App
py -m core.gui.main_qt
```

### Après
```bash
# Depuis la racine
python -m emac

# Ou avec le lanceur
deploy/local/launcher.vbs
```

---

## 📦 Nouveaux Fichiers Créés

| Fichier | Description |
|---------|-------------|
| `src/emac/__init__.py` | Package principal |
| `src/emac/__main__.py` | Point d'entrée (`python -m emac`) |
| `README_NEW.md` | Nouveau README |
| `CLAUDE_NEW.md` | Guide Claude mis à jour |
| `build/README.md` | Documentation build |
| `database/README.md` | Documentation BDD |
| `deploy/README.md` | Documentation déploiement |
| `config/README.md` | Documentation configuration |
| `archives/README.md` | Index des archives |
| `tools/migration/migrate_imports.py` | Script de migration |
| `build/scripts/clean.bat` | Script de nettoyage |

---

## ✅ Checklist de Migration

### Phase 1: Structure (✓ Complétée)
- [x] Créer nouvelle structure de répertoires
- [x] Déplacer code source vers `src/emac/`
- [x] Réorganiser tests dans `tests/`
- [x] Consolider scripts dans `tools/`
- [x] Organiser build dans `build/`
- [x] Restructurer database dans `database/`
- [x] Réorganiser docs dans `docs/`
- [x] Organiser déploiement dans `deploy/`
- [x] Archiver anciens fichiers dans `archives/`

### Phase 2: Documentation (✓ Complétée)
- [x] Créer README.md principal
- [x] Mettre à jour CLAUDE.md
- [x] Créer README par module
- [x] Documenter la migration

### Phase 3: Migration du Code (À Faire)
- [ ] Exécuter script de migration des imports
- [ ] Mettre à jour les configurations (build, tests)
- [ ] Adapter les chemins dans les scripts
- [ ] Tester l'application
- [ ] Tester les builds
- [ ] Valider les tests

### Phase 4: Finalisation (À Faire)
- [ ] Remplacer ancien README par README_NEW
- [ ] Remplacer ancien CLAUDE.md par CLAUDE_NEW
- [ ] Supprimer fichiers redondants de App/
- [ ] Créer release v2.0
- [ ] Documenter changements dans CHANGELOG

---

## ⚠️ Points d'Attention

### 1. Compatibilité Ascendante
- L'ancien code dans `App/` reste disponible
- Migration progressive possible
- Ancien et nouveau peuvent coexister temporairement

### 2. Base de Données
- **Aucun changement** au schéma
- Connexion identique
- Fichier `.env` à la racine du projet

### 3. Imports
- Tous les imports `core.*` doivent devenir `emac.*`
- Noms de services simplifiés (sans `_service`)
- Structure GUI plus détaillée

### 4. Build
- Mettre à jour `emac.spec` avec nouveaux chemins
- Tester compilation avant déploiement

### 5. Tests
- Mettre à jour imports dans tests
- Adapter fixtures si nécessaire

---

## 📈 Avantages de la Réorganisation

### Organisation
- ✅ Structure Python standard (`src/`)
- ✅ Séparation claire des responsabilités
- ✅ Documentation bien organisée
- ✅ Outils catégorisés

### Maintenabilité
- ✅ Un seul fichier de build
- ✅ Tests organisés par type
- ✅ Imports plus clairs
- ✅ Moins de redondance

### Professionnalisme
- ✅ Suit les meilleures pratiques Python
- ✅ Structure scalable
- ✅ Documentation complète
- ✅ Facilite onboarding nouveaux développeurs

### Performance
- ✅ Build optimisé
- ✅ Tests mieux organisés
- ✅ Moins de fichiers à la racine

---

## 🔗 Ressources

### Documentation
- [README.md](README_NEW.md) - Vue d'ensemble
- [CLAUDE.md](CLAUDE_NEW.md) - Guide développeur
- [docs/](docs/) - Documentation complète

### Migration
- [tools/migration/migrate_imports.py](tools/migration/migrate_imports.py) - Script de migration
- [Migration Guide](docs/developer/migration-guide.md) - Guide détaillé (à créer)

### Modules
- [build/README.md](build/README.md) - Système de build
- [database/README.md](database/README.md) - Base de données
- [deploy/README.md](deploy/README.md) - Déploiement
- [config/README.md](config/README.md) - Configuration

---

## 📞 Support

En cas de problème lors de la migration:

1. Consulter ce document
2. Vérifier [docs/developer/migration-guide.md](docs/developer/migration-guide.md)
3. Utiliser le script de migration automatique
4. Consulter les archives pour retrouver anciens fichiers

---

## 📅 Timeline

- **2026-01-05 14:00** - Début de la réorganisation
- **2026-01-05 16:00** - Structure complète créée
- **2026-01-05 17:00** - Documentation mise à jour
- **À planifier** - Migration du code et tests
- **À planifier** - Release v2.0

---

**Réorganisé par:** Claude Code
**Date:** 2026-01-05
**Version:** 2.0.0
**Statut:** ✅ Structure créée - Migration du code en attente
