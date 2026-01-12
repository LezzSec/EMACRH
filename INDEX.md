# 📑 Index de Navigation - EMAC

Guide de navigation rapide vers tous les documents et ressources du projet.

---

## 🎯 Démarrage

| Document | Description | Temps |
|----------|-------------|-------|
| [docs/DEMARRAGE_RAPIDE.md](docs/DEMARRAGE_RAPIDE.md) | Installation et lancement en 5 minutes | ⚡ 5 min |
| [README.md](README.md) | Documentation principale complète | 📖 15 min |
| [docs/STRUCTURE.md](docs/STRUCTURE.md) | Arborescence détaillée du projet | 🗺️ 10 min |
| [docs/BIENVENUE.md](docs/BIENVENUE.md) | Guide de bienvenue pour les nouveaux développeurs | 👋 5 min |

---

## 📚 Documentation Principale

### Pour les Utilisateurs

| Document | Contenu |
|----------|---------|
| [docs/user/guide-absences.md](docs/user/guide-absences.md) | Guide de gestion des absences |
| [docs/user/guide-interface-historique.md](docs/user/guide-interface-historique.md) | Guide de l'interface historique |

### Pour les Développeurs

| Document | Contenu |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | Instructions pour Claude Code / Conventions |
| [docs/dev/architecture.md](docs/dev/architecture.md) | Architecture du système |
| [docs/dev/build-optimization.md](docs/dev/build-optimization.md) | Guide d'optimisation |
| [docs/dev/guide-optimisation-build.md](docs/dev/guide-optimisation-build.md) | Guide de compilation |
| [docs/dev/exemples-logging.md](docs/dev/exemples-logging.md) | Exemples de logging |
| [docs/dev/tests-report.md](docs/dev/tests-report.md) | Rapports de tests |

#### 🚀 Optimisations de Performance (2026-01-06 à 2026-01-08)

| Document | Contenu |
|----------|---------|
| [docs/dev/optimisation-reports/README.md](docs/dev/optimisation-reports/README.md) | **📊 Vue d'ensemble des optimisations** |
| [docs/dev/optimisation-database.md](docs/dev/optimisation-database.md) | Guide optimisation DB (pooling, indexes) |
| [docs/dev/optimisation-ui-threads.md](docs/dev/optimisation-ui-threads.md) | Guide optimisation UI/threading (DbWorker) |
| [docs/dev/optimisation-cache.md](docs/dev/optimisation-cache.md) | Guide système de cache LRU |
| [docs/dev/optimisation-packaging.md](docs/dev/optimisation-packaging.md) | Guide optimisation PyInstaller |
| [docs/dev/optimisation-logs-io.md](docs/dev/optimisation-logs-io.md) | Guide optimisation logs I/O |
| [docs/dev/monitoring-performance.md](docs/dev/monitoring-performance.md) | Guide monitoring de performance |

**Gains de performance:** Démarrage 75% plus rapide, requêtes DB 10x plus rapides, taille exe -47%

### Fonctionnalités

| Document | Contenu |
|----------|---------|
| [docs/features/module-absences.md](docs/features/module-absences.md) | Module de gestion des absences |
| [docs/features/module-documents.md](docs/features/module-documents.md) | Module de gestion des documents |
| [docs/features/historique-polyvalence.md](docs/features/historique-polyvalence.md) | Historique des polyvalences |

### Sécurité

| Document | Contenu |
|----------|---------|
| [docs/security/database-credentials.md](docs/security/database-credentials.md) | Gestion des credentials |
| [docs/security/security-changelog.md](docs/security/security-changelog.md) | Changelog sécurité |

### Installation

| Document | Contenu |
|----------|---------|
| [App/config/README.md](App/config/README.md) | Configuration de la base de données |
| [docs/INSTALLATION_CLIENT.md](docs/INSTALLATION_CLIENT.md) | Installation réseau pour clients |

---

## 🔧 Scripts et Outils

### Build et Compilation

| Fichier | Utilisation |
|---------|-------------|
| [build-scripts/README.md](build-scripts/README.md) | Documentation du build |
| [build-scripts/build_optimized.bat](build-scripts/build_optimized.bat) | Compiler l'application |
| [build-scripts/EMAC_optimized.spec](build-scripts/EMAC_optimized.spec) | Config PyInstaller |
| [build-scripts/analyze_imports.py](build-scripts/analyze_imports.py) | Analyser les imports |

### Tests

| Fichier | Utilisation |
|---------|-------------|
| [tests/README.md](tests/README.md) | Documentation des tests |
| [tests/test_gestion_evaluation.py](tests/test_gestion_evaluation.py) | Test basique module évaluation |
| [tests/test_gestion_eval_full.py](tests/test_gestion_eval_full.py) | Test complet avec DB |
| [tests/test_gestion_eval_crash.py](tests/test_gestion_eval_crash.py) | Test diagnostic erreurs |
| [tests/test_menu_gestion_eval.py](tests/test_menu_gestion_eval.py) | Test menu application |
| [App/tests/run_all_tests.py](App/tests/run_all_tests.py) | Lancer tous les tests unitaires |

---

## 📋 Rapports et Historique

### Rapports de Session (Temporaires)

| Fichier | Contenu |
|---------|---------|
| [session-reports/README.md](session-reports/README.md) | Documentation des rapports |
| [session-reports/BUG_FIX_GESTION_EVAL.md](session-reports/BUG_FIX_GESTION_EVAL.md) | Correction bug gestion évaluation |
| [session-reports/DIAGNOSTIC_GESTION_EVAL.md](session-reports/DIAGNOSTIC_GESTION_EVAL.md) | Diagnostic module évaluation |
| [session-reports/OPTIMISATION_RECAP.md](session-reports/OPTIMISATION_RECAP.md) | Récapitulatif optimisations |
| [session-reports/CORRECTIONS_DOCUMENTATION.md](session-reports/CORRECTIONS_DOCUMENTATION.md) | Corrections documentation |
| [session-reports/RECAP_SESSION_2026-01-07.md](session-reports/RECAP_SESSION_2026-01-07.md) | Résumé session 2026-01-07 |

### Projet

| Fichier | Contenu |
|---------|---------|
| [REORGANISATION.md](REORGANISATION.md) | Log de la réorganisation du projet |

---

## 💻 Code Source

### Structure Principale

| Dossier | Contenu |
|---------|---------|
| [App/core/db/](App/core/db/) | Couche base de données |
| [App/core/services/](App/core/services/) | Logique métier |
| [App/core/gui/](App/core/gui/) | Interface PyQt5 |
| [App/core/exporters/](App/core/exporters/) | Export de données |
| [App/core/utils/](App/core/utils/) | Utilitaires |

### Fichiers Importants

| Fichier | Description |
|---------|-------------|
| [App/core/db/configbd.py](App/core/db/configbd.py) | Configuration MySQL |
| [App/core/gui/main_qt.py](App/core/gui/main_qt.py) | Fenêtre principale |
| [App/core/gui/ui_theme.py](App/core/gui/ui_theme.py) | Système de thème |
| [App/core/gui/gestion_evaluation.py](App/core/gui/gestion_evaluation.py) | Module évaluations |
| [App/core/services/logger.py](App/core/services/logger.py) | Service de logging |
| [App/requirements.txt](App/requirements.txt) | Dépendances Python |

### Base de Données

| Fichier | Description |
|---------|-------------|
| [App/database/schema/bddemac.sql](App/database/schema/bddemac.sql) | Schéma principal MySQL |
| [App/database/migrations/](App/database/migrations/) | Migrations de base |

---

## 🔍 Recherche Rapide

### Je cherche...

| Quoi | Où |
|------|-----|
| Comment installer | [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md) |
| Comment ça marche | [README.md](README.md) |
| Structure du projet | [STRUCTURE.md](STRUCTURE.md) |
| Conventions de code | [CLAUDE.md](CLAUDE.md) |
| Architecture | [docs/dev/architecture.md](docs/dev/architecture.md) |
| Comment compiler | [build-scripts/README.md](build-scripts/README.md) |
| Comment tester | [tests/README.md](tests/README.md) |
| Configuration DB | [App/config/README.md](App/config/README.md) |
| Sécurité | [docs/security/](docs/security/) |
| Guides utilisateur | [docs/user/](docs/user/) |
| Bug connu | [session-reports/BUG_*.md](session-reports/) |
| Schéma SQL | [App/database/schema/bddemac.sql](App/database/schema/bddemac.sql) |

---

## 📖 Parcours de Lecture Recommandés

### 👤 Je suis Utilisateur

1. [README.md](README.md) - Vue d'ensemble
2. [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md) - Installation
3. [docs/user/](docs/user/) - Guides utilisateur
4. [docs/INSTALLATION_CLIENT.md](docs/INSTALLATION_CLIENT.md) - Installation réseau

### 💻 Je suis Développeur (débutant sur le projet)

1. [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md) - Installation
2. [README.md](README.md) - Vue d'ensemble
3. [CLAUDE.md](CLAUDE.md) - Conventions
4. [STRUCTURE.md](STRUCTURE.md) - Organisation
5. [docs/dev/architecture.md](docs/dev/architecture.md) - Architecture
6. Explorer [App/core/](App/core/) - Code source

### 🔧 Je veux Compiler l'Application

1. [build-scripts/README.md](build-scripts/README.md) - Guide build
2. [docs/dev/guide-optimisation-build.md](docs/dev/guide-optimisation-build.md) - Optimisations
3. [build-scripts/build_optimized.bat](build-scripts/build_optimized.bat) - Compiler

### 🐛 Je cherche un Bug Connu

1. [session-reports/](session-reports/) - Rapports de bugs
2. [docs/dev/tests-report.md](docs/dev/tests-report.md) - Rapports de tests
3. [tests/](tests/) - Scripts de diagnostic

---

## 📊 Statistiques du Projet

| Type | Quantité |
|------|----------|
| Fichiers Python | ~50 |
| Lignes de code | ~15,000 |
| Fichiers Markdown | ~30 |
| Pages de doc | ~300 |
| Modules principaux | 5 (db, services, gui, exporters, utils) |
| Scripts de test | 8 |
| Scripts de build | 6 |

---

## 🗂️ Organisation des Dossiers

```
EMAC/
├── App/              # Code source
├── docs/             # Documentation
├── build-scripts/    # Compilation
├── tests/            # Tests système
├── session-reports/  # Rapports (ignoré Git)
├── archives/         # Historique
├── temp/             # Temporaire (ignoré Git)
└── dist/             # Distribution
```

---

## ✅ Checklist Nouveaux Arrivants

- [ ] Lire [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md)
- [ ] Installer l'application (5-10 min)
- [ ] Lancer l'application avec succès
- [ ] Lire [CLAUDE.md](CLAUDE.md) (conventions)
- [ ] Explorer [STRUCTURE.md](STRUCTURE.md)
- [ ] Lire [docs/dev/architecture.md](docs/dev/architecture.md)
- [ ] Explorer le code dans [App/core/](App/core/)
- [ ] Lancer un test dans [tests/](tests/)

---

**Dernière mise à jour** : 2026-01-07
**Version de l'index** : 1.0

**Navigation rapide** : Ce fichier est votre point de départ pour trouver n'importe quelle information dans le projet EMAC.
