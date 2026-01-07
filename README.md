# 🏭 EMAC - Gestion de Personnel et Polyvalence

Application de bureau PyQt5 pour la gestion des compétences, évaluations, et ressources humaines dans un environnement industriel.

---

## 📋 Vue d'ensemble

EMAC est une application complète de gestion RH conçue pour les ateliers de production. Elle permet de :

- ✅ **Suivre les compétences** (polyvalence) des employés sur différents postes
- ✅ **Planifier les évaluations** périodiques avec calendrier automatisé
- ✅ **Gérer les contrats** et renouvellements
- ✅ **Suivre les absences** et congés
- ✅ **Gérer les documents RH** (certificats, permis, formations)
- ✅ **Auditer toutes les modifications** dans un historique complet

---

## 🚀 Démarrage rapide

### Installation

```bash
# 1. Cloner le projet
git clone <repo-url>
cd EMAC

# 2. Installer les dépendances
pip install -r App/requirements.txt

# 3. Configurer la base de données
cd App/config
configure_db.bat  # Windows
# Ou copier .env.example vers App/.env et remplir les valeurs

# 4. Initialiser la base de données MySQL
mysql -u root -p emac_db < App/database/schema/bddemac.sql

# 5. ⚡ NOUVEAU : Appliquer les optimisations de performance (RECOMMANDÉ)
cd App/scripts
python apply_performance_indexes.py  # Ajoute 29 index → app 10-100x plus rapide

# 6. Lancer l'application
cd App
py -m core.gui.main_qt
```

**Guides** :
- ⚡ [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md) - Installation en 5 minutes
- 📖 [App/config/README.md](App/config/README.md) - Configuration détaillée
- 🌐 [docs/INSTALLATION_CLIENT.md](docs/INSTALLATION_CLIENT.md) - Installation réseau
- 🗺️ [INDEX.md](INDEX.md) - Navigation complète du projet

---

## 📚 Documentation

### Pour les utilisateurs
- 📖 [Guide des absences](docs/user/guide-absences.md)
- 📖 [Guide de l'interface historique](docs/user/guide-interface-historique.md)

### Pour les développeurs
- 🏗️ [Architecture du projet](docs/dev/architecture.md)
- 🧪 [Guide des tests](docs/dev/tests-report.md)
- 🔧 [Optimisation de l'exécutable](docs/dev/build-optimization.md)
- 🌐 [Déploiement réseau](docs/dev/deploiement-reseau.md) ⚡ **Résout la lenteur au lancement**

#### 🔥 Optimisations Performance (NOUVEAU 2026-01-07)
- ⚡ **[Optimisations Base de Données](docs/dev/optimisation-database.md)** - Gains 10-100x avec indexes
- 🧵 **[Optimisations UI/Threads](docs/dev/optimisation-ui-threads.md)** - UI fluide, zero freeze
- 💾 **[Optimisations Cache](docs/dev/optimisation-cache.md)** - Cache mémoire avec TTL
- 📦 **[Optimisations Packaging](docs/dev/optimisation-packaging.md)** - PyInstaller démarrage 5x plus rapide
- 📝 **[Optimisations Logs/IO](docs/dev/optimisation-logs-io.md)** - Logs async, évite micro-lenteurs

#### Guides rapides des optimisations
- 📄 [DB - Guide rapide](OPTIMISATIONS_DB_APPLIQUEES.md)
- 📄 [UI - Guide rapide](OPTIMISATIONS_UI_APPLIQUEES.md)
- 📄 [Cache - Guide rapide](OPTIMISATIONS_CACHE_APPLIQUEES.md)
- 📄 [Packaging - Guide rapide](OPTIMISATIONS_PACKAGING_APPLIQUEES.md)
- 📄 [Logs - Guide rapide](OPTIMISATIONS_LOGS_APPLIQUEES.md)

- 📝 [Exemples de logging](docs/dev/exemples-logging.md)
- 💡 [Exemples de cache](docs/dev/exemples-cache.md)

### Fonctionnalités
- 📋 [Module Absences](docs/features/module-absences.md)
- 📄 [Module Documents RH](docs/features/module-documents.md)
- 📊 [Historique Polyvalence](docs/features/historique-polyvalence.md)

### Sécurité
- 🔐 [Gestion des credentials](docs/security/database-credentials.md)
- 📝 [Changelog sécurité](docs/security/security-changelog.md)

---

## 🛠️ Technologies

- **Interface** : PyQt5 (thème personnalisé)
- **Base de données** : MySQL 8.0 (serveur distant ou local)
- **Exports** : Excel (openpyxl), PDF (ReportLab)
- **Logging** : Système d'audit complet en base de données

**Note importante** : Les postes clients n'ont **PAS besoin** d'installer MySQL. Seul le serveur hébergeant la base de données nécessite MySQL. L'application se connecte au serveur via le réseau.

---

## 📂 Structure du projet

```
EMAC/
├── App/                    # Application principale
│   ├── core/              # Code source
│   │   ├── db/           # Couche base de données
│   │   ├── gui/          # Interface PyQt5
│   │   ├── services/     # Logique métier
│   │   └── exporters/    # Export Excel/PDF
│   ├── config/           # Configuration (templates)
│   ├── database/         # Schémas et migrations SQL
│   ├── scripts/          # Scripts utilitaires
│   └── tests/            # Tests unitaires et intégration
│
├── docs/                  # Documentation
│   ├── dev/              # Docs développeur
│   ├── user/             # Guides utilisateur
│   ├── features/         # Documentation fonctionnelle
│   └── security/         # Documentation sécurité
│
└── Deploy/               # Déploiement réseau
    ├── Lancer_EMAC.bat         # Lanceur optimisé (cache local)
    ├── README_DEPLOIEMENT.md   # Guide admin système
    ├── GUIDE_UTILISATEUR.md    # Guide utilisateur final
    └── test_deploiement.bat    # Script de validation
```

**Documentation complète** : [CLAUDE.md](CLAUDE.md)

---

## 🔐 Sécurité

- ✅ Protection contre les injections SQL (requêtes paramétrées)
- ✅ Credentials en variables d'environnement (`.env`)
- ✅ Mot de passe jamais commité dans Git
- ✅ Audit trail complet de toutes les modifications

**Guide sécurité** : [docs/security/database-credentials.md](docs/security/database-credentials.md)

---

## 🧪 Tests

```bash
cd App/tests
python run_all_tests.py
```

Les tests couvrent :
- ✅ Intégrité de la base de données
- ✅ Logique métier (évaluations, contrats, absences)
- ✅ Système d'audit et logging
- ✅ Gestion des matricules

**Rapport de tests** : [docs/dev/tests-report.md](docs/dev/tests-report.md)

---

## 📦 Déploiement

### Build de l'exécutable

Pour créer un exécutable autonome optimisé :

```bash
# Build optimisé (recommandé)
build_optimized.bat

# Résultat : dist/EMAC/ (~40-60 MB)
```

**Guide complet** : [docs/dev/guide-optimisation-build.md](docs/dev/guide-optimisation-build.md)

### Installation sur les postes clients

⚠️ **Aucune installation de MySQL nécessaire sur les postes clients !**

1. Copiez le dossier `dist/EMAC/` sur le poste client
2. Configurez `.env` avec l'adresse du serveur MySQL :
   ```env
   EMAC_DB_HOST=192.168.1.100  # IP du serveur
   EMAC_DB_USER=emac_user
   EMAC_DB_PASSWORD=***
   EMAC_DB_NAME=emac_db
   ```
3. Lancez `EMAC.exe`

**Guide d'installation client** : [INSTALLATION_CLIENT.md](INSTALLATION_CLIENT.md)

---

## 📊 Fonctionnalités principales

### 🎯 Gestion de la Polyvalence
- Matrice de compétences par poste et atelier
- 4 niveaux de qualification (1=Apprenti → 4=Formateur)
- Calcul automatique des prochaines évaluations
- Grilles d'affichage et exports Excel

### 📅 Système d'évaluation
- Planification automatique sur 10 ans
- Prise en compte des jours fériés
- Alertes pour les évaluations en retard
- Historique complet des évaluations

### 📄 Gestion documentaire
- Stockage centralisé des documents RH
- Suivi des dates d'expiration (permis, certificats)
- Catégorisation flexible
- Alertes d'expiration

### 👥 Ressources Humaines
- Gestion des contrats (CDD, CDI, intérim)
- Suivi des renouvellements
- Gestion des absences et congés
- Calcul automatique des soldes

### 📝 Audit et Historique
- Tous les changements tracés (qui, quoi, quand)
- Consultation de l'historique par table, action, ou opérateur
- Export des logs en CSV
- Interface de recherche avancée

---

## 🌐 Déploiement en production

### Compilation de l'exécutable

```bash
cd App
pyinstaller EMAC_optimized.spec --clean --noconfirm
```

Résultat : `App\dist\EMAC\EMAC.exe` (mode one-folder)

### Déploiement sur réseau d'entreprise

⚡ **Problème résolu** : Lancement lent (2-5 min) depuis un partage réseau

**Solution** : Système de cache local avec le lanceur `Lancer_EMAC.bat`

| Scénario | Temps | Documentation |
|----------|-------|---------------|
| Premier lancement | 30-60 sec | [Deploy/README.md](Deploy/README.md) |
| Lancements suivants | 2-3 sec | [docs/dev/deploiement-reseau.md](docs/dev/deploiement-reseau.md) |

**Pour déployer** :
1. Consultez [Deploy/README_DEPLOIEMENT.md](Deploy/README_DEPLOIEMENT.md) (administrateurs)
2. Testez avec `Deploy\test_deploiement.bat`
3. Distribuez `Deploy\Lancer_EMAC.bat` aux utilisateurs

---

## 🤝 Contribution

Pour contribuer au projet :

1. Lire [CLAUDE.md](CLAUDE.md) pour comprendre l'architecture
2. Consulter [docs/dev/architecture.md](docs/dev/architecture.md)
3. Créer une branche pour vos modifications
4. Tester avec `python App/tests/run_all_tests.py`
5. Soumettre une Pull Request

---

## 📞 Support

- 📧 Documentation technique : [CLAUDE.md](CLAUDE.md)
- 🔧 Configuration : [App/config/README.md](App/config/README.md)
- 🐛 Problèmes : Consulter [docs/dev/tests-report.md](docs/dev/tests-report.md)

---

## 📄 Licence

Projet interne - Tous droits réservés

---

## 🎯 Roadmap

- [ ] Migration vers python-dotenv pour parsing .env
- [ ] API REST pour intégration externe
- [ ] Dashboard temps réel avec WebSockets
- [ ] Application mobile (consultation)
- [ ] Export PDF avancé avec templates

---

**Version** : 2.0
**Dernière mise à jour** : 2025-12-16
**Statut** : ✅ Production
