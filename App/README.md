# 📦 EMAC - Application de Gestion de Polyvalence

Application PyQt5 de bureau pour la gestion des compétences, évaluations, absences et contrats du personnel dans un environnement industriel.

---

## 🎯 Vue d'Ensemble

EMAC est une application complète qui permet de:

- 👥 **Gérer le personnel** (opérateurs, matricules, informations)
- 📊 **Suivre les compétences** (polyvalence sur différents postes)
- 📅 **Planifier les évaluations** (calendrier automatique)
- 🏖️ **Gérer les absences** (congés, arrêts maladie, formation)
- 📄 **Suivre les contrats** (échéances, renouvellements)
- 📁 **Gérer les documents** (GED intégrée)
- 📜 **Tracer les actions** (historique complet)
- 🔐 **Contrôler les accès** (authentification, permissions)

---

## 📚 Documentation

### 🚀 Démarrage Rapide

| Document | Description | Pour Qui |
|----------|-------------|----------|
| **[QUICK_START.md](QUICK_START.md)** | Guide de démarrage rapide | 🎯 **Tous** |
| [BUILD_README.md](BUILD_README.md) | Guide de compilation détaillé | 👨‍💻 Développeurs |
| [DEPLOIEMENT.md](DEPLOIEMENT.md) | Procédures de déploiement | 🛠️ Admins |

### 📖 Référence Technique

| Document | Description | Pour Qui |
|----------|-------------|----------|
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Structure complète du projet | 👨‍💻 Développeurs |
| [BUILD_MANIFEST.txt](BUILD_MANIFEST.txt) | Liste des fichiers essentiels | 🏗️ Build |
| [CLAUDE.md](../CLAUDE.md) | Instructions Claude Code | 🤖 Claude |

### 🔧 Configuration

| Document | Description | Pour Qui |
|----------|-------------|----------|
| [config/README.md](config/README.md) | Configuration de la BDD | ⚙️ Admins |
| [config/.env.example](config/.env.example) | Template de configuration | ⚙️ Admins |

---

## ⚡ Quick Start

### Pour les Utilisateurs

```bash
# Lancer EMAC (depuis le réseau)
Z:\Applications\EMAC\EMAC.exe

# Ou double-cliquer sur le raccourci "EMAC" sur le bureau
```

### Pour les Développeurs

```bash
# 1. Cloner le projet
git clone <url_projet>
cd EMAC/App

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer la BDD
cd config
configure_db.bat

# 4. Lancer l'application
cd ..
py -m core.gui.main_qt
```

### Pour les Administrateurs

```bash
# 1. Compiler l'application
cd App
build_clean.bat

# 2. Déployer sur le réseau
xcopy /E /I dist\EMAC Z:\Applications\EMAC

# 3. Configurer le .env de production
notepad Z:\Applications\EMAC\.env
```

📖 **Voir [QUICK_START.md](QUICK_START.md) pour plus de détails**

---

## 🏗️ Architecture

```
EMAC/
├── App/                              # 🚀 Application principale
│   ├── core/                         # Code source
│   │   ├── gui/                      # 🎨 Interface PyQt5
│   │   ├── services/                 # 🧠 Logique métier
│   │   ├── db/                       # 💾 Base de données
│   │   ├── exporters/                # 📤 Exports PDF/Excel
│   │   └── utils/                    # 🛠️ Utilitaires
│   │
│   ├── database/                     # 💾 Schémas SQL
│   ├── config/                       # ⚙️ Configuration
│   ├── scripts/                      # 🔧 Scripts maintenance
│   ├── tests/                        # 🧪 Tests
│   │
│   ├── build_clean.bat               # 🏗️ Build propre
│   └── EMAC_optimized.spec           # ⚙️ Config PyInstaller
│
└── docs/                             # 📖 Documentation projet
```

📖 **Voir [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) pour la structure complète**

---

## 🔧 Technologies

### Backend
- **Python 3.10+**
- **MySQL 8.0+** (Base de données)
- **mysql-connector-python** (Connexion BDD)
- **bcrypt** (Sécurité des mots de passe)
- **python-dotenv** (Configuration)

### Frontend
- **PyQt5** (Interface graphique)
- **Custom UI Kit** (Thème EMAC)

### Exports
- **openpyxl** (Excel)
- **reportlab** (PDF)
- **pandas** (Traitement de données)

### Build
- **PyInstaller** (Compilation en .exe)

---

## 📋 Fonctionnalités Principales

### 👥 Gestion du Personnel
- Fiche complète des opérateurs
- Gestion des matricules
- Statut (ACTIF/INACTIF)
- Historique personnel
- Personnel non-production

### 📊 Gestion de la Polyvalence
- Niveaux de compétence (1-4)
- Grilles de polyvalence par atelier
- Besoins par poste
- Historique des modifications

### 📅 Évaluations
- Planification automatique
- Alertes échéances
- Calendrier intelligent
- Suivi des retards

### 🏖️ Gestion des Absences
- Congés, maladie, formation
- Planning visuel
- Calcul des jours
- Statistiques

### 📄 Gestion des Contrats
- Types de contrats (CDI, CDD, Interim, etc.)
- Alertes d'expiration
- Renouvellements
- Historique

### 📁 Gestion Documentaire
- Upload de documents
- Catégorisation
- Recherche
- Archivage

### 📜 Historique et Traçabilité
- Audit trail complet
- Logs par utilisateur
- Historique de polyvalence
- Export des logs

### 🔐 Sécurité
- Authentification utilisateurs
- Gestion des rôles (Admin, Gestionnaire, Opérateur, Lecteur)
- Permissions granulaires
- Mots de passe hashés (bcrypt)

---

## 📦 Installation et Déploiement

### Prérequis

**Pour le développement:**
- Python 3.10+
- MySQL 8.0+
- Git

**Pour la production (utilisateurs):**
- Windows 10/11
- Accès au serveur MySQL
- Aucune installation Python requise (tout inclus dans l'exe)

### Installation Développement

```bash
# 1. Cloner le projet
git clone <url_projet>
cd EMAC/App

# 2. Créer un environnement virtuel (optionnel)
python -m venv venv
venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer la base de données
cd config
configure_db.bat
# Suivre les instructions pour créer .env

# 5. Importer le schéma BDD
mysql -u root -p < database/schema/bddemac.sql

# 6. Créer l'utilisateur admin
cd ..
py scripts/reset_admin_password.py

# 7. Lancer l'application
py -m core.gui.main_qt
```

### Compilation

```bash
cd App
build_clean.bat
```

**Résultat:** `dist\EMAC\EMAC.exe` (+ dossier `_internal/`)

### Déploiement Production

```bash
# 1. Copier sur le serveur
xcopy /E /I dist\EMAC Z:\Applications\EMAC

# 2. Configurer le .env
notepad Z:\Applications\EMAC\.env

# 3. Tester
Z:\Applications\EMAC\EMAC.exe
```

📖 **Voir [DEPLOIEMENT.md](DEPLOIEMENT.md) pour le guide complet**

---

## 🔒 Configuration Sécurisée

### Fichier .env (OBLIGATOIRE)

Créer `App/.env` avec:

```env
EMAC_DB_HOST=localhost
EMAC_DB_USER=root
EMAC_DB_PASSWORD=votre_mot_de_passe
EMAC_DB_NAME=emac_db
```

**⚠️ IMPORTANT:**
- Le fichier `.env` contient des mots de passe
- **NE JAMAIS** commiter `.env` dans Git
- Utiliser `.env.example` comme template
- Créer un `.env` différent pour dev et production

📖 **Voir [config/README.md](config/README.md) pour plus de détails**

---

## 🧪 Tests

```bash
# Lancer tous les tests
py tests/run_all_tests.py

# Lancer un test spécifique
py tests/test_auth_system.py
```

---

## 📊 Base de Données

### Tables Principales

- **personnel** / **operateurs**: Employés
- **postes**: Postes de travail
- **atelier**: Ateliers (contiennent des postes)
- **polyvalence**: Compétences employé×poste
- **evaluations**: Évaluations planifiées
- **contrats**: Contrats de travail
- **absences**: Absences
- **documents**: Documents GED
- **historique**: Audit trail
- **historique_polyvalence**: Historique modifications polyvalence
- **users**: Utilisateurs de l'application

### Schéma

Le schéma complet est dans [database/schema/bddemac.sql](database/schema/bddemac.sql)

---

## 🛠️ Développement

### Conventions de Code

- **Encodage:** UTF-8 avec `# -*- coding: utf-8 -*-`
- **Format dates:** `DD/MM/YYYY` (français)
- **Langue:** Français pour l'interface
- **Cursors BDD:** Toujours fermer dans `finally` blocks
- **Logging:** Utiliser `log_hist()` de [logger.py](core/services/logger.py)
- **UI:** Utiliser les composants de [emac_ui_kit.py](core/gui/emac_ui_kit.py)

### Ajouter une Nouvelle Fonctionnalité

1. Créer le fichier dans `core/gui/` ou `core/services/`
2. Ajouter dans `EMAC_optimized.spec` → `hiddenimports`
3. Importer dans `main_qt.py` si c'est une interface
4. Documenter dans les fichiers appropriés
5. Ajouter des tests si nécessaire

📖 **Voir [CLAUDE.md](../CLAUDE.md) pour les instructions complètes**

---

## 📈 Roadmap

### ✅ Version 1.0 (Actuelle)
- Gestion personnel, polyvalence, évaluations
- Absences et contrats
- Gestion documentaire
- Authentification et permissions
- Exports Excel/PDF

### 🔮 Version 1.1 (À venir)
- Dashboard statistiques avancé
- Notifications par email
- API REST
- Application mobile (lecture seule)
- Synchronisation multi-sites

### 💡 Idées Futures
- Intelligence artificielle (suggestions d'affectation)
- Intégration avec systèmes RH existants
- Module de formation en ligne
- Gamification des compétences

---

## 🐛 Dépannage

### Problèmes Fréquents

| Problème | Solution |
|----------|----------|
| `ModuleNotFoundError` | Installer les dépendances: `pip install -r requirements.txt` |
| `Can't connect to MySQL` | Vérifier le `.env` et que MySQL est démarré |
| `.exe ne démarre pas` | Vérifier que `_internal/` est présent et `.env` existe |
| `Access Denied` (BDD) | Vérifier les permissions MySQL de l'utilisateur |
| Build trop gros | Ajouter des exclusions dans `EMAC_optimized.spec` |

📖 **Voir [BUILD_README.md](BUILD_README.md) section Dépannage**

---

## 📞 Support

### Documentation
- [QUICK_START.md](QUICK_START.md) - Démarrage rapide
- [BUILD_README.md](BUILD_README.md) - Compilation
- [DEPLOIEMENT.md](DEPLOIEMENT.md) - Déploiement
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Architecture

### Logs
- **Développement:** `App/logs/`
- **Production:** `dist\EMAC\logs/` ou `Z:\Applications\EMAC\logs/`

### Contact
- **Support Technique:** support@emac.local
- **Issues GitHub:** <url_issues>
- **Email:** emac@company.com

---

## 📄 Licence

Propriétaire - Tous droits réservés

---

## 👥 Crédits

**Développé par:** Équipe EMAC
**Dernière mise à jour:** 2025-12-24
**Version:** 1.0

---

## 🌟 Contribuer

Pour contribuer au projet:

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

**Bon développement avec EMAC! 🚀**
