# 🏭 EMAC - Gestion des Évaluations et de la Polyvalence

Application PyQt5 de bureau pour la gestion des évaluations de personnel, de la polyvalence (compétences multi-postes) et des contrats dans un environnement industriel/atelier.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15-orange)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue)

---

## 🚀 Démarrage Rapide

### Installation

```bash
# 1. Cloner le projet
git clone [URL_DU_REPO]
cd EMAC

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer la base de données
cd tools/setup
configure_db.bat

# 4. Initialiser la base de données
mysql -u root -p emac_db < ../../database/schema/current/00_main_schema.sql

# 5. Lancer l'application
cd ../..
python -m emac
```

📖 **Guide complet:** [docs/getting-started/quick-start.md](docs/getting-started/quick-start.md)

---

## 📋 Fonctionnalités Principales

- ✅ **Gestion du Personnel** - Suivi des employés, matricules, statuts
- 📊 **Évaluations** - Planification et suivi des évaluations de compétences
- 🎯 **Polyvalence** - Matrice de compétences multi-postes avec historique
- 📅 **Absences** - Gestion des congés et absences
- 📄 **Contrats** - Suivi des contrats et échéances
- 📑 **Documents** - Gestion documentaire intégrée
- 👥 **Utilisateurs** - Système d'authentification et permissions
- 📈 **Exports** - Excel, PDF, CSV
- 🔍 **Historique** - Audit trail complet de toutes les actions

---

## 🏗️ Architecture du Projet

```
EMAC/
├── 📁 src/emac/          # ⭐ CODE SOURCE PRINCIPAL
│   ├── db/               # Couche base de données
│   ├── services/         # Logique métier
│   ├── gui/              # Interface PyQt5
│   │   ├── components/   # Composants réutilisables
│   │   ├── dialogs/      # Fenêtres de dialogue
│   │   ├── views/        # Vues principales
│   │   └── widgets/      # Widgets personnalisés
│   ├── exporters/        # Exports fichiers
│   └── utils/            # Utilitaires
│
├── 📁 tests/             # Tests
│   ├── unit/             # Tests unitaires
│   ├── integration/      # Tests d'intégration
│   └── ui/               # Tests UI
│
├── 📁 database/          # Base de données
│   ├── schema/           # Schémas SQL
│   ├── migrations/       # Migrations
│   ├── backups/          # Sauvegardes
│   └── seeds/            # Données de test
│
├── 📁 tools/             # Outils de développement
│   ├── setup/            # Installation & config
│   ├── maintenance/      # Maintenance
│   ├── migration/        # Migration de données
│   ├── diagnostics/      # Diagnostic
│   └── security/         # Sécurité
│
├── 📁 build/             # Système de build
│   ├── configs/          # Configurations
│   ├── scripts/          # Scripts de build
│   └── output/           # Builds générés
│
├── 📁 deploy/            # Déploiement
│   ├── local/            # Déploiement local
│   ├── network/          # Déploiement réseau
│   └── diagnostics/      # Outils diagnostic
│
├── 📁 docs/              # Documentation
│   ├── getting-started/  # Démarrage
│   ├── user-guides/      # Guides utilisateur
│   ├── developer/        # Documentation développeur
│   ├── deployment/       # Guides déploiement
│   ├── security/         # Sécurité
│   └── features/         # Fonctionnalités
│
├── 📁 config/            # Configuration
│   ├── .env.example      # Template environnement
│   └── configure_db.bat  # Script de config
│
└── 📁 archives/          # Archives historiques
```

📖 **Architecture détaillée:** [docs/developer/architecture.md](docs/developer/architecture.md)

---

## 💾 Base de Données

- **SGBD:** MySQL 8.0
- **Database:** `emac_db`
- **Configuration:** Fichier `.env` (voir [config/README.md](config/README.md))

### Tables Principales

- `personnel` - Données des employés
- `postes` - Postes de travail
- `atelier` - Ateliers
- `polyvalence` - Compétences par poste
- `historique` - Audit trail
- `contrats` - Contrats de travail
- `absences` - Gestion des absences

📖 **Documentation BDD:** [database/README.md](database/README.md)

---

## 🛠️ Développement

### Prérequis

- Python 3.8+
- MySQL 8.0
- PyQt5
- Git

### Structure des Imports

⚠️ **IMPORTANT:** La structure des imports a changé!

**Ancienne structure (App/):**
```python
from core.db.configbd import get_connection
from core.services.evaluation_service import calculate_next_evaluation
from core.gui.ui_theme import EmacTheme
```

**Nouvelle structure (src/emac/):**
```python
from emac.db.connection import get_connection
from emac.services.evaluation import calculate_next_evaluation
from emac.gui.components.theme import EmacTheme
```

### Lancer les Tests

```bash
cd tests
python run_tests.py
```

### Build de l'Application

```bash
cd build/scripts
build.bat
```

📖 **Guide développeur:** [docs/developer/](docs/developer/)

---

## 📚 Documentation

- 🚀 [Démarrage Rapide](docs/getting-started/quick-start.md)
- 👤 [Guides Utilisateur](docs/user-guides/)
- 💻 [Documentation Développeur](docs/developer/)
- 🚢 [Guides de Déploiement](docs/deployment/)
- 🔒 [Sécurité](docs/security/)
- ✨ [Fonctionnalités](docs/features/)

**Index complet:** [docs/README.md](docs/README.md)

---

## 🔐 Sécurité

Les credentials de base de données ne sont **pas hardcodés**. Configuration via:
- Variables d'environnement
- Fichier `.env` (gitignored)

⚠️ **Ne JAMAIS commiter le fichier `.env`**

📖 **Guide sécurité:** [docs/security/credentials-management.md](docs/security/credentials-management.md)

---

## 🚀 Déploiement

### Local
```bash
# Utiliser le lanceur VBScript (silencieux)
deploy/local/launcher.vbs
```

### Réseau
```bash
cd deploy/network
deploy.bat
```

📖 **Guides déploiement:** [docs/deployment/](docs/deployment/)

---

## 🧪 Tests

Les tests couvrent:
- ✅ Intégrité de la base de données
- ✅ Logique métier (évaluations, contrats, absences)
- ✅ Système d'audit et logging
- ✅ Gestion des matricules

```bash
cd tests
python run_tests.py
```

---

## 📊 Technologies

- **Interface:** PyQt5 5.15+ (thème personnalisé)
- **Base de données:** MySQL 8.0
- **Exports:** Excel (openpyxl), PDF (ReportLab)
- **Logging:** Système d'audit complet en BDD

---

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit les changements (`git commit -m 'Ajout fonctionnalité'`)
4. Lancer les tests (`cd tests && python run_tests.py`)
5. Push vers la branche (`git push origin feature/amelioration`)
6. Ouvrir une Pull Request

---

## 📝 Historique

- **v2.0.0** (2026-01-05) - Réorganisation complète du projet
  - Nouvelle structure `src/emac/`
  - Tests organisés en `unit/`, `integration/`, `ui/`
  - Système de build consolidé
  - Documentation restructurée

- **v1.x** - Versions précédentes (voir archives/)

📖 **Changelog complet:** [CHANGELOG.md](CHANGELOG.md)

---

## 📞 Support

- 📧 Documentation technique: [CLAUDE.md](CLAUDE.md)
- 🔧 Configuration: [config/README.md](config/README.md)
- 🏗️ Build: [build/README.md](build/README.md)
- 💾 Database: [database/README.md](database/README.md)

---

## 📄 Licence

[À définir]

---

## 🎯 Migration depuis v1.x

Si vous migrez depuis l'ancienne structure `App/core/`:

1. Mettre à jour les imports (voir section Développement)
2. Utiliser le script de migration: `tools/migration/migrate_imports.py`
3. Consulter: [docs/developer/migration-guide.md](docs/developer/migration-guide.md)

---

**Version:** 2.0.0
**Dernière mise à jour:** 2026-01-05
**Python:** 3.8+
**PyQt5:** 5.15+
**MySQL:** 8.0
**Statut:** ✅ En production
