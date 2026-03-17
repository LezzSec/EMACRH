# Réorganisation du Projet - 5 janvier 2026

## Objectif
Nettoyer et organiser les fichiers du projet EMAC en regroupant les fichiers similaires dans des dossiers appropriés et en éliminant les doublons et fichiers temporaires.

## Actions Effectuées

### 1. Création de la Structure d'Archivage
Nouveaux dossiers créés :
- `archives/docs-obsoletes/` - Documentation obsolète ou remplacée
- `archives/reorganisation/` - Fichiers de réorganisation historiques
- `archives/build-tests/` - Tests de build anciens
- `docs/project-history/` - Historique du projet

### 2. Fichiers Déplacés vers Archives

#### Archives de Documentation Obsolète (`archives/docs-obsoletes/`)
- `CLAUDE_NEW.md` - Brouillon de mise à jour de CLAUDE.md
- `README_NEW.md` - Brouillon de mise à jour du README
- `IMPLEMENTATION_COMPLETE.md` - Rapport d'implémentation historique
- `INSTRUCTIONS_COMMIT.md` - Instructions git obsolètes
- `STRUCTURE_BUILD_OPTIMISE.md` - Documentation de build ancienne

#### Archives de Réorganisation (`archives/reorganisation/`)
- `REORGANISATION_2026-01-05.md` - Ce fichier de réorganisation
- `REORGANISATION_GIT.md` - Plan de réorganisation git
- `REORGANISATION_2025-12-24.md` - Réorganisation précédente (depuis App/)
- `RESUME_REORGANISATION.txt` - Résumé de réorganisation
- `GUIDE_RAPIDE_REORGANISATION.md` - Guide rapide
- `structure_finale.txt` - Structure finale planifiée
- `STRUCTURE_V2.0.txt` - Documentation de structure v2

### 3. Organisation des Fichiers de Build dans App/

#### Scripts de Build (`App/build/scripts/`)
- `build_and_deploy.bat`
- `build_clean.bat`
- `build_nuitka.bat`
- `build_nuitka_simple.bat`
- `build_emac.bat`
- `build_optimized.bat`
- `launcher_reseau.bat`

#### Spécifications PyInstaller (`App/build/specs/`)
- `EMAC.spec`
- `EMAC_debug.spec`
- `EMAC_onefile.spec`
- `EMAC_optimized.spec`

#### Documentation de Build (`App/docs/build/`)
- `BUILD_INFO.txt`
- `BUILD_MANIFEST.txt`
- `BUILD_README.md`

### 4. Organisation de la Documentation

#### Documentation Projet (racine `docs/`)
- `docs/security/` - Documentation de sécurité
  - `SECURITE_SYSTEME_UTILISATEURS.md` (déplacé)
  - `SYSTEME_UTILISATEURS_README.md` (déplacé)
- `docs/deployment/` - Documentation de déploiement
  - `SOLUTION_RESEAU.md` (déplacé)
- `docs/project-history/` - Historique du projet
  - `CHANGELOG.md` (déplacé)

#### Documentation App (`App/docs/`)
- `App/docs/getting-started/` - Guide de démarrage
  - `QUICK_START.md` (déplacé)
- `App/docs/` - Documentation générale
  - `DEPLOIEMENT.md`
  - `INDEX_DOCUMENTATION.md`
  - `PROJECT_STRUCTURE.md`

### 5. Nettoyage des Fichiers Temporaires
Fichiers supprimés :
- `nul` (fichier vide Windows)
- `App/test_startup_time.py` (script de test temporaire)
- `App/nuitka-crash-report.xml` (rapport de crash obsolète)

Dossiers fusionnés :
- `temp_archives/` → `archives/` (puis supprimé)

Fichiers déplacés :
- `demo_ui_kit.py` → `App/tests/` (fichier de démonstration/test)

### 6. Outils et Scripts
- `install_user_system.bat` → `tools/` (script d'installation)

### 7. Mise à Jour du .gitignore
Ajouts :
```gitignore
# Archives temporaires
archives/docs-obsoletes/
archives/reorganisation/
archives/build-tests/

# Dossiers de build
App/dist_nuitka/

# Fichiers temporaires
App/*.xml
```

Suppressions :
- `*.spec` (les specs de build sont maintenant trackés dans `App/build/specs/`)

## Structure Finale Simplifiée

```
EMAC/
├──  CLAUDE.md                 # Instructions pour Claude Code
├──  README.md                 # Documentation principale
├──  requirements.txt          # Dépendances Python
│
├──  App/                      # Application principale
│   ├── core/                    # Code source
│   ├── build/                   # Scripts et specs de build
│   │   ├── scripts/             # Scripts .bat de build
│   │   └── specs/               # Fichiers .spec PyInstaller
│   ├── docs/                    # Documentation App
│   │   ├── build/               # Docs de build
│   │   └── getting-started/     # Guide démarrage
│   ├── config/                  # Configuration
│   ├── database/                # Base de données
│   ├── tests/                   # Tests
│   ├── scripts/                 # Scripts utilitaires
│   └── run_emac.vbs             # Lanceur
│
├──  docs/                     # Documentation projet
│   ├── deployment/              # Déploiement
│   ├── developer/               # Documentation développeur
│   ├── security/                # Sécurité
│   ├── features/                # Fonctionnalités
│   ├── user-guides/             # Guides utilisateur
│   └── project-history/         # Historique
│
├──  archives/                 # Archives (ignoré par git)
│   ├── docs-obsoletes/          # Docs obsolètes
│   ├── reorganisation/          # Fichiers de réorganisation
│   └── build-tests/             # Tests de build
│
├──  tools/                    # Outils de maintenance
├──  tests/                    # Tests projet
├──  config/                   # Configuration globale
├──  database/                 # Schémas et migrations
└──  Deploy/                   # Déploiement
    ├── diagnostics/
    ├── local/
    └── network/
```

## Bénéfices

1. **Clarté** : Les fichiers sont maintenant organisés logiquement par catégorie
2. **Maintenabilité** : Plus facile de trouver et maintenir les fichiers
3. **Propreté** : Suppression des doublons et fichiers temporaires
4. **Traçabilité** : Les anciens fichiers sont archivés, pas perdus
5. **Git** : .gitignore mis à jour pour ignorer les archives et fichiers temporaires

## Fichiers Essentiels Conservés à la Racine

- `CLAUDE.md` - Instructions pour l'IA
- `README.md` - Documentation principale
- `requirements.txt` - Dépendances
- `.gitignore` - Configuration Git

Tous les autres fichiers ont été déplacés dans des dossiers appropriés.

## Notes

- Les dossiers dans `archives/` sont ignorés par Git (ajoutés au .gitignore)
- Les fichiers .spec de PyInstaller sont maintenant trackés car ils sont essentiels pour le build
- La structure est maintenant plus conforme aux standards de projets Python
- Tous les scripts de build sont centralisés dans `App/build/`
