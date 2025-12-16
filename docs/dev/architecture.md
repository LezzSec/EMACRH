# Structure du Projet EMAC

## 📊 Vue d'ensemble

```
EMAC/
├── 📄 docs/                    # Documentation (4 fichiers)
├── 💻 App/                     # Application principale
│   ├── 🔧 core/               # Code source
│   │   ├── db/               # Base de données (5 fichiers)
│   │   ├── services/         # Services métier (11 fichiers)
│   │   ├── gui/              # Interface PyQt5 (15 fichiers)
│   │   └── exporters/        # Exports (3 fichiers)
│   ├── 🧪 tests/              # Tests (6 fichiers + README)
│   ├── 🔧 scripts/            # Scripts utilitaires (5 fichiers + README)
│   ├── 💾 database/           # Fichiers BDD
│   │   ├── schema/           # 1 schéma principal
│   │   ├── migrations/       # 1 migration
│   │   └── backups/          # 8 sauvegardes
│   ├── 📝 logs/               # Logs applicatifs
│   ├── ⚙️ run/                # Fichiers runtime
│   └── 🚀 run_emac.vbs       # Lanceur Windows
├── 📦 Deploy/                 # Déploiement
├── 🗑️ Fichiers inutilisés/    # Archives
├── 📘 CLAUDE.md               # Instructions Claude
├── 📋 REORGANISATION.md       # Historique réorganisation
└── 📊 STRUCTURE.md            # Ce fichier

```

## 🎯 Points d'entrée

### Lancement de l'application
```bash
# Méthode 1 : Double-clic sur le lanceur
App/run_emac.vbs

# Méthode 2 : Ligne de commande
cd App
py -m core.gui.main_qt
```

### Exécution des tests
```bash
cd App
py tests/test_database_integrity.py
```

### Scripts utilitaires
```bash
cd App
py scripts/cleanup_test_data.py
py scripts/quick_db_query.py
```

## 📚 Documentation

| Fichier | Description |
|---------|-------------|
| [CLAUDE.md](CLAUDE.md) | Instructions complètes pour Claude Code |
| [docs/README.md](docs/README.md) | Index de toute la documentation |
| [docs/GUIDE_UTILISATION_ABSENCES.md](docs/GUIDE_UTILISATION_ABSENCES.md) | Guide utilisateur absences |
| [docs/MODULE_ABSENCES_README.md](docs/MODULE_ABSENCES_README.md) | Doc technique absences |
| [docs/ANALYSE_FONCTIONNALITES_RH_MANQUANTES.md](docs/ANALYSE_FONCTIONNALITES_RH_MANQUANTES.md) | Analyse fonctionnalités RH |

## 🗄️ Base de données

### Configuration
- **Serveur**: 192.168.1.128:3306
- **Base**: emac_db
- **User**: gestionrh
- **Config**: [App/core/db/configbd.py](App/core/db/configbd.py)

### Fichiers importants
- **Schéma principal**: [App/database/schema/bddemac.sql](App/database/schema/bddemac.sql)
- **Migration absences**: [App/database/migrations/schema_absences_conges.sql](App/database/migrations/schema_absences_conges.sql)
- **Sauvegardes**: [App/database/backups/](App/database/backups/)

## 🧩 Modules principaux

### Core (`App/core/`)

#### Database Layer (`db/`)
- `configbd.py` - Connexion MySQL
- `insert_*.py` - Scripts de population
- `import_infos.py` - Import de données

#### Service Layer (`services/`)
- `evaluation_service.py` - Gestion des évaluations
- `absence_service.py` - Gestion des absences
- `contrat_service.py` - Gestion des contrats
- `matricule_service.py` - Gestion des matricules
- `logger.py` - Système de logs

#### GUI Layer (`gui/`)
- `main_qt.py` - Fenêtre principale
- `ui_theme.py` - Système de thèmes
- `gestion_*.py` - Dialogs de gestion
- `emac_ui_kit.py` - Composants réutilisables

#### Exporters (`exporters/`)
- `excel_export.py` - Export Excel
- `pdf_export.py` - Export PDF
- `log_export.py` - Export CSV

## 📈 Statistiques

- **Tests**: 6 fichiers
- **Scripts**: 5 fichiers
- **Sauvegardes SQL**: 8 fichiers
- **Documentation**: 4 fichiers Markdown
- **Services**: 11 fichiers
- **Interfaces GUI**: 15 fichiers

## 🔄 Workflow de développement

### 1. Modification du schéma BDD
1. Modifier `App/database/schema/bddemac.sql`
2. Créer migration dans `App/database/migrations/`
3. Appliquer à la BDD
4. Mettre à jour les services concernés
5. Tester les interfaces GUI

### 2. Ajout d'une fonctionnalité
1. Créer/modifier service dans `App/core/services/`
2. Créer/modifier dialog dans `App/core/gui/`
3. Intégrer dans `main_qt.py`
4. Créer tests dans `App/tests/`
5. Documenter dans `docs/`

### 3. Maintenance
1. Utiliser scripts dans `App/scripts/`
2. Créer sauvegardes dans `App/database/backups/`
3. Vérifier logs dans `App/logs/`

## 🛠️ Outils de développement

### Git
```bash
# Ignorer les fichiers temporaires
# Voir App/.gitignore pour la liste complète
```

### Dépendances
```bash
pip install -r Fichiers\ inutilisés/requirements.txt
```

### Base de données
```bash
# Sauvegarde
mysqldump -u gestionrh -p emac_db > App/database/backups/backup_$(date +%Y%m%d).sql

# Restauration
mysql -u gestionrh -p emac_db < App/database/backups/bddserver12.sql
```

## 🎨 Conventions de code

- **Encodage**: UTF-8 avec header `# -*- coding: utf-8 -*-`
- **Langue**: Tout le texte UI en français
- **Dates**: Format DD/MM/YYYY (`strftime('%d/%m/%Y')`)
- **Nommage**: snake_case pour fonctions, PascalCase pour classes
- **Dialogs**: Suffixe `*Dialog` (ex: `GestionEvaluationDialog`)

## ⚠️ Notes importantes

1. **Tables duales**: `personnel` ET `operateurs` existent dans la BDD
2. **Logging**: Utiliser `logger.py`, pas `audit_logger.py` (deprecated)
3. **Theme**: Appliquer avant création fenêtre principale
4. **Drawer menu**: Chargement lazy, vérifier `is not None`
5. **Évaluations**: Dates à 10 ans = normal (maintenance long terme)

## 🚀 Déploiement

Les fichiers de déploiement se trouvent dans le dossier `Deploy/`.

## 📞 Support

Pour toute question sur la structure ou l'organisation du projet, consultez :
- [CLAUDE.md](CLAUDE.md) pour les instructions détaillées
- [REORGANISATION.md](REORGANISATION.md) pour l'historique des changements
