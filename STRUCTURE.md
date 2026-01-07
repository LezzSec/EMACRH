# 📁 Structure du Projet EMAC

Documentation de l'organisation du projet après réorganisation (2026-01-07).

---

## 🌳 Arborescence Complète

```
EMAC/
│
├── 📁 App/                                  # APPLICATION PRINCIPALE
│   ├── core/                                # Code source principal
│   │   ├── db/                              # Couche base de données
│   │   │   ├── configbd.py                  # Configuration MySQL
│   │   │   ├── insert_*.py                  # Scripts de population
│   │   │   └── import_infos.py              # Import de données
│   │   │
│   │   ├── services/                        # Logique métier
│   │   │   ├── evaluation_service.py        # Gestion évaluations
│   │   │   ├── calendrier_service.py        # Calculs de dates
│   │   │   ├── contrat_service.py           # Gestion contrats
│   │   │   ├── absence_service.py           # Gestion absences
│   │   │   ├── matricule_service.py         # Gestion matricules
│   │   │   ├── liste_et_grilles_service.py  # Génération grilles
│   │   │   ├── logger.py                    # Logs historique
│   │   │   └── auth_service.py              # Authentification
│   │   │
│   │   ├── gui/                             # Interface PyQt5
│   │   │   ├── main_qt.py                   # Fenêtre principale
│   │   │   ├── ui_theme.py                  # Système de thème
│   │   │   ├── emac_ui_kit.py               # Composants UI
│   │   │   ├── gestion_evaluation.py        # Module évaluations
│   │   │   ├── gestion_personnel.py         # Module personnel
│   │   │   ├── gestion_absences.py          # Module absences
│   │   │   ├── manage_operateur.py          # CRUD employés
│   │   │   ├── liste_et_grilles.py          # Grilles polyvalence
│   │   │   ├── creation_modification_poste.py  # CRUD postes
│   │   │   ├── historique.py                # Visualisation logs
│   │   │   ├── planning.py                  # Planning
│   │   │   └── contract_management.py       # Gestion contrats
│   │   │
│   │   ├── exporters/                       # Export de données
│   │   │   ├── excel_export.py              # Export Excel
│   │   │   ├── pdf_export.py                # Export PDF
│   │   │   └── log_export.py                # Export logs CSV
│   │   │
│   │   └── utils/                           # Utilitaires
│   │
│   ├── config/                              # Configuration
│   │   ├── .env.example                     # Template configuration
│   │   ├── configure_db.bat                 # Script config DB
│   │   └── README.md                        # Guide configuration
│   │
│   ├── database/                            # Base de données
│   │   ├── schema/                          # Schémas SQL
│   │   │   └── bddemac.sql                  # Schéma principal
│   │   ├── migrations/                      # Migrations
│   │   └── backups/                         # Sauvegardes
│   │
│   ├── documents/                           # Documents RH
│   │   └── uploads/                         # Fichiers téléversés
│   │
│   ├── logs/                                # Logs application
│   │
│   ├── scripts/                             # Scripts utilitaires
│   │   ├── cleanup_test_data.py
│   │   ├── fix_matricule_lowercase.py
│   │   ├── install_absences_module.py
│   │   └── quick_db_query.py
│   │
│   ├── tests/                               # Tests unitaires
│   │   ├── unit/
│   │   ├── integration/
│   │   └── run_all_tests.py
│   │
│   ├── .env                                 # Config locale (Git ignore)
│   ├── .gitignore
│   ├── requirements.txt                     # Dépendances Python
│   └── run_emac.vbs                         # Lanceur Windows
│
├── 📁 docs/                                 # DOCUMENTATION
│   ├── dev/                                 # Documentation développeur
│   │   ├── architecture.md                  # Architecture système
│   │   ├── tests-report.md                  # Rapports de tests
│   │   ├── build-optimization.md            # Guide optimisation
│   │   ├── guide-optimisation-build.md      # Guide build
│   │   └── exemples-logging.md              # Exemples de logs
│   │
│   ├── user/                                # Guides utilisateur
│   │   ├── guide-absences.md
│   │   └── guide-interface-historique.md
│   │
│   ├── features/                            # Documentation fonctionnalités
│   │   ├── module-absences.md
│   │   ├── module-documents.md
│   │   └── historique-polyvalence.md
│   │
│   ├── security/                            # Documentation sécurité
│   │   ├── database-credentials.md          # Gestion credentials
│   │   └── security-changelog.md            # Historique sécurité
│   │
│   ├── project-history/                     # Historique du projet
│   │
│   └── INSTALLATION_CLIENT.md               # Guide installation réseau
│
├── 📁 build-scripts/                        # COMPILATION & ANALYSE
│   ├── build_optimized.bat                  # Script de build PyInstaller
│   ├── EMAC_optimized.spec                  # Config PyInstaller
│   ├── analyze_imports.py                   # Analyse des imports
│   ├── build_dependencies.txt               # Liste dépendances build
│   ├── dependency_analysis_report.txt       # Rapport d'analyse
│   └── README.md                            # Documentation build
│
├── 📁 tests/                                # TESTS SYSTÈME
│   ├── test_gestion_evaluation.py           # Test basique
│   ├── test_gestion_eval_full.py            # Test complet avec DB
│   ├── test_gestion_eval_crash.py           # Test diagnostic
│   ├── test_menu_gestion_eval.py            # Test menu
│   └── README.md                            # Documentation tests
│
├── 📁 session-reports/                      # RAPPORTS (Git ignore)
│   ├── BUG_FIX_GESTION_EVAL.md             # Corrections bugs
│   ├── CORRECTIONS_DOCUMENTATION.md         # Corrections doc
│   ├── DIAGNOSTIC_GESTION_EVAL.md          # Diagnostics
│   ├── OPTIMISATION_RECAP.md               # Récap optimisations
│   ├── RECAP_SESSION_2026-01-07.md         # Résumés sessions
│   └── README.md                            # Documentation
│
├── 📁 archives/                             # ARCHIVES HISTORIQUES
│   ├── build-tests/
│   ├── builds/
│   ├── code/
│   ├── database/
│   ├── docs/
│   ├── docs-obsoletes/
│   ├── fichiers_inutilises/
│   ├── reorganisation/
│   └── securite_sql/
│
├── 📁 temp/                                 # TEMPORAIRES (Git ignore)
│   └── build/                               # Builds temporaires
│
├── 📁 dist/                                 # DISTRIBUTION
│   └── EMAC/                                # Application compilée
│       └── EMAC.exe                         # Exécutable Windows
│
├── 📄 README.md                             # Documentation principale
├── 📄 CLAUDE.md                             # Instructions Claude Code
├── 📄 STRUCTURE.md                          # Ce fichier
├── 📄 REORGANISATION.md                     # Log de réorganisation
├── 📄 .gitignore                            # Configuration Git
└── 📄 .env                                  # Config locale (Git ignore)
```

---

## 📊 Répartition par Type

### 🔵 Code Source (App/)
- **Total** : ~50 fichiers Python
- **Lignes** : ~15,000 lignes de code
- **Modules** : db, services, gui, exporters, utils

### 📘 Documentation (docs/)
- **Total** : ~20 fichiers Markdown
- **Catégories** : dev, user, features, security
- **Pages** : ~200 pages de documentation

### 🔧 Scripts (build-scripts/ + tests/)
- **Build** : 6 fichiers
- **Tests** : 4 fichiers de test + tests unitaires

### 📋 Rapports (session-reports/)
- **Bugs** : Corrections et diagnostics
- **Sessions** : Résumés de travail
- **Temporaire** : Ignoré par Git

---

## 🎯 Points d'Entrée Principaux

### Développement

```bash
# Lancer l'application en développement
cd App
py -m core.gui.main_qt

# Lancer les tests
py tests/run_all_tests.py

# Lancer un test spécifique
py ../tests/test_gestion_evaluation.py
```

### Build

```bash
# Compiler l'application
cd build-scripts
build_optimized.bat

# Analyser les dépendances
py analyze_imports.py
```

### Configuration

```bash
# Configurer la base de données
cd App/config
configure_db.bat

# Ou manuellement
copy .env.example ../. env
# Éditer App/.env
```

---

## 📝 Conventions

### Nommage des Fichiers

- **Modules Python** : `snake_case.py`
- **Documentation** : `kebab-case.md`
- **Scripts batch** : `snake_case.bat`
- **Configuration** : `.lowercase`

### Organisation des Dossiers

```
type/
├── sous-type/
│   ├── fichier.ext
│   └── README.md       # Chaque dossier a son README
└── README.md
```

### Fichiers Ignorés (.gitignore)

- `__pycache__/` - Cache Python
- `*.pyc` - Bytecode Python
- `.env` - Configuration locale
- `logs/` - Logs applicatifs
- `temp/` - Fichiers temporaires
- `session-reports/` - Rapports temporaires
- `build/`, `dist/` - Builds

---

## 🔍 Navigation Rapide

| Je cherche... | Je vais dans... |
|---------------|-----------------|
| Code source de l'interface | `App/core/gui/` |
| Configuration DB | `App/core/db/configbd.py` |
| Logique métier | `App/core/services/` |
| Schéma de la base | `App/database/schema/bddemac.sql` |
| Guide utilisateur | `docs/user/` |
| Guide développeur | `docs/dev/` |
| Comment compiler | `build-scripts/README.md` |
| Tests | `tests/` ou `App/tests/` |
| Rapports de bugs | `session-reports/` |
| Documentation sécurité | `docs/security/` |

---

## ✅ Validation

Structure validée le **2026-01-07**

- ✅ Organisation claire par type
- ✅ README dans chaque dossier important
- ✅ .gitignore à jour
- ✅ Pas de fichiers en doublon
- ✅ Chemins d'accès documentés
- ✅ Navigation intuitive

---

**Dernière mise à jour** : 2026-01-07
**Responsable** : Équipe EMAC
**Version** : 1.0 (après réorganisation)
