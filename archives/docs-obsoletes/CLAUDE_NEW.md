# CLAUDE.md

Ce fichier fournit des instructions à Claude Code lors du travail sur ce projet.

## Vue d'ensemble du Projet

EMAC est une application PyQt5 de bureau pour la gestion des évaluations de personnel, de la polyvalence (compétences multi-postes) et des contrats dans un environnement industriel/atelier.

**Version:** 2.0.0 (Réorganisée le 2026-01-05)

## Lancement de l'Application

```bash
# Depuis la racine du projet
python -m emac

# Ou avec le lanceur (Windows)
deploy/local/launcher.vbs
```

## Configuration de la Base de Données

L'application utilise MySQL 8.0 avec les paramètres suivants:
- Host: `localhost` (configurable via `EMAC_DB_HOST`)
- User: `root` (configurable via `EMAC_DB_USER`)
- Database: `emac_db` (configurable via `EMAC_DB_NAME`)
- Charset: `utf8mb4`
- Configuration: [src/emac/db/connection.py](src/emac/db/connection.py)

### 🔐 Sécurité: Configuration du Mot de Passe

Le mot de passe de BDD est chargé depuis:

1. **Variables d'environnement** (recommandé production):
   ```bash
   set EMAC_DB_PASSWORD=your_password_here
   ```

2. **Fichier `.env`** (recommandé développement):
   ```bash
   cd tools/setup
   configure_db.bat
   # Ou manuellement: copier config/.env.example vers .env
   ```

3. **Pas de fallback par défaut** - Configuration obligatoire pour la sécurité.

⚠️ **Important:** Le fichier `.env` est dans `.gitignore` et ne sera jamais commité.

Pour plus d'informations: [docs/security/credentials-management.md](docs/security/credentials-management.md)

Le schéma SQL est dans [database/schema/current/](database/schema/current/).

## Tables Principales de la Base de Données

- `personnel` / `operateurs`: Enregistrements des employés avec statut (ACTIF/INACTIF)
- `postes`: Postes de travail avec codes (ex: "0506", "0830") liés aux ateliers
- `atelier`: Ateliers contenant plusieurs postes
- `polyvalence`: Table de jonction traçant les compétences des employés par poste avec dates d'évaluation et niveaux (1-4)
- `historique`: Journal d'audit de toutes les actions système
- `contrats`: Contrats de travail avec dates de début/fin et types

**Important:** Le code est en transition - certains fichiers référencent la table `operateurs` tandis que le code récent utilise `personnel`. Les deux tables contiennent des données d'employés avec: `id`, `nom`, `prenom`, `statut`.

## Architecture

### Structure des Modules

```
EMAC/
├── src/emac/              # Package Python principal
│   ├── db/                # Couche base de données
│   │   ├── connection.py  # Configuration MySQL (ex-configbd.py)
│   │   └── import_infos.py # Utilitaires d'import
│   │
│   ├── services/          # Couche logique métier
│   │   ├── auth.py        # Authentification
│   │   ├── evaluation.py  # Logique d'évaluation
│   │   ├── calendar.py    # Calculs calendaires
│   │   ├── contract.py    # Gestion des contrats
│   │   ├── absence.py     # Gestion des absences
│   │   ├── document.py    # Gestion documentaire
│   │   ├── matricule.py   # Gestion des matricules
│   │   ├── grid.py        # Génération de grilles
│   │   ├── logger.py      # Logging historique
│   │   └── polyvalence.py # Historique polyvalence
│   │
│   ├── gui/               # Couche interface utilisateur (PyQt5)
│   │   ├── app.py         # Fenêtre principale (ex-main_qt.py)
│   │   │
│   │   ├── components/    # Composants réutilisables
│   │   │   ├── theme.py   # Système de thème (EmacTheme)
│   │   │   └── ui_kit.py  # Kit UI EMAC
│   │   │
│   │   ├── dialogs/       # Fenêtres de dialogue
│   │   │   ├── login.py
│   │   │   ├── personnel.py
│   │   │   ├── evaluation.py
│   │   │   ├── rh.py
│   │   │   ├── absences.py
│   │   │   ├── documents.py
│   │   │   ├── contracts.py
│   │   │   ├── positions.py
│   │   │   └── users.py
│   │   │
│   │   ├── views/         # Vues principales
│   │   │   ├── grids.py   # Grilles de polyvalence
│   │   │   ├── planning.py
│   │   │   ├── history.py
│   │   │   └── dashboard.py
│   │   │
│   │   └── widgets/       # Widgets personnalisés
│   │
│   ├── exporters/         # Couche export de fichiers
│   │   ├── excel.py
│   │   ├── pdf.py
│   │   └── csv.py
│   │
│   └── utils/             # Fonctions utilitaires
│       ├── paths.py
│       ├── permissions.py
│       └── validators.py
│
├── tests/                 # Suite de tests
│   ├── unit/              # Tests unitaires
│   ├── integration/       # Tests d'intégration
│   └── ui/                # Tests UI
│
├── database/              # Base de données
│   ├── schema/            # Schémas SQL
│   ├── migrations/        # Migrations
│   ├── backups/           # Sauvegardes
│   └── seeds/             # Données de test
│
├── tools/                 # Outils de développement
│   ├── setup/
│   ├── maintenance/
│   ├── migration/
│   ├── diagnostics/
│   └── security/
│
├── build/                 # Système de build
│   ├── configs/           # Configurations PyInstaller
│   └── scripts/           # Scripts de build
│
├── deploy/                # Déploiement
│   ├── local/
│   ├── network/
│   └── diagnostics/
│
├── docs/                  # Documentation
│   ├── getting-started/
│   ├── user-guides/
│   ├── developer/
│   ├── deployment/
│   ├── security/
│   └── features/
│
└── config/                # Configuration
    └── .env.example
```

### Système de Thème UI

L'application utilise un système de thème personnalisé défini dans [src/emac/gui/components/theme.py](src/emac/gui/components/theme.py):
- `EmacTheme`: Thème clair (défaut)
- `EmacDarkTheme`: Variante thème sombre
- Composants réutilisables: `EmacButton`, `EmacCard`, `EmacStatusCard`, `EmacHeader`, `HamburgerButton`
- Appliquer le thème avec: `EmacTheme.apply(app)` avant d'afficher la fenêtre principale

### Pattern de la Couche Service

Les services encapsulent la logique métier et les requêtes de base de données:
- Les services sont des modules utilitaires sans état (fonctions, pas classes)
- Tous les services utilisent `get_connection()` depuis [connection.py](src/emac/db/connection.py)
- Les services doivent gérer le nettoyage des curseurs avec des blocs try/finally
- Utiliser `log_hist(action, description, operateur_id, poste_id)` depuis [logger.py](src/emac/services/logger.py) pour l'audit trail

Exemple de pattern service:
```python
from emac.db.connection import get_connection
from emac.services.logger import log_hist

def my_service_function(param):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT ...")
        result = cur.fetchall()
        log_hist("ACTION_NAME", "description", operateur_id=None, poste_id=None)
        conn.commit()
        return result
    finally:
        cur.close()
        conn.close()
```

## Logique du Système d'Évaluation

La table polyvalence trace les évaluations de compétences avec un système basé sur les dates:
- `niveau`: Niveau de compétence de 1 (apprentissage) à 4 (expert/formateur)
- `date_evaluation`: Date de la dernière évaluation
- `prochaine_evaluation`: Date d'évaluation planifiée suivante (typiquement 10 ans après la date d'évaluation)
- Le tableau de bord principal affiche les évaluations en retard et à venir

La planification des évaluations utilise une formule complexe dans [calendar.py](src/emac/services/calendar.py) qui prend en compte:
- Niveau de compétence actuel
- Temps depuis la dernière évaluation
- Fréquence requise par niveau
- Calcul des jours ouvrables excluant les weekends

## Tâches de Développement Courantes

### Ajouter une Nouvelle Fenêtre de Dialogue

1. Créer un fichier dans `src/emac/gui/dialogs/` héritant de `QDialog`
2. Importer les composants du thème: `from emac.gui.components.theme import EmacTheme, EmacButton, EmacCard`
3. Utiliser les composants du thème pour un style cohérent
4. Ajouter l'accès à la base de données via `from emac.db.connection import get_connection`
5. Enregistrer dans [app.py](src/emac/gui/app.py) comme élément de menu ou bouton d'action

### Modifier le Schéma de la Base de Données

1. Mettre à jour [database/schema/current/00_main_schema.sql](database/schema/current/00_main_schema.sql) avec les changements
2. Créer un script de migration dans [database/migrations/applied/](database/migrations/applied/) si nécessaire
3. Appliquer les changements à la base de données locale `emac_db`
4. Mettre à jour les scripts `seeds/` affectés dans [database/seeds/](database/seeds/)
5. Mettre à jour les fonctions de service qui interrogent les tables modifiées
6. Tester les composants UI qui affichent les données affectées

### Ajouter un Nouveau Format d'Export

1. Créer un exporteur dans `src/emac/exporters/` en suivant les patterns existants
2. Les fonctions d'export doivent accepter des structures de données et retourner des chemins de fichiers
3. Utiliser des context managers pour les opérations sur fichiers
4. Enregistrer l'exporteur dans les dialogues UI pertinents (ex: [dialogs/evaluation.py](src/emac/gui/dialogs/evaluation.py))

## Dépendances

Packages Python requis (depuis [requirements.txt](requirements.txt)):
- PyQt5==5.15.10
- mysql-connector-python==8.4.0
- pandas==2.2.2
- openpyxl==3.1.5
- reportlab==4.2.2
- python-docx==1.1.2
- python-pptx==0.6.23
- odfpy==1.4.1
- pypandoc==1.13

Installer avec: `pip install -r requirements.txt`

## Conventions de Code

- Utiliser l'encodage UTF-8 avec l'en-tête `# -*- coding: utf-8 -*-` pour les fichiers avec du texte français
- Les curseurs de base de données doivent être fermés dans des blocs `finally`
- Les classes de dialogue UI suivent le pattern de nommage: `*Dialog` (ex: `GestionEvaluationDialog`)
- Les modules de service utilisent des noms de fonction en snake_case
- Les modules GUI importent le thème en haut: `from emac.gui.components.theme import EmacTheme, ...`
- Format de date: Utiliser `strftime('%d/%m/%Y')` pour l'affichage (format français DD/MM/YYYY)
- Tout le texte destiné à l'utilisateur est en français

## Notes Critiques d'Implémentation

1. **Noms de Tables Doubles**: Lors de l'interrogation des employés, vérifier si le code utilise la table `personnel` ou `operateurs`. Le schéma contient les deux et elles peuvent référencer différentes relations de clés étrangères.

2. **Logging Historique**: Utiliser `log_hist()` depuis [logger.py](src/emac/services/logger.py) plutôt que l'ancien `log_action()` depuis [audit_logger.py](src/emac/services/audit_logger.py). Le nouveau logger écrit dans la table `historique` de la base de données.

3. **Application du Thème**: Toujours appeler `EmacTheme.apply(app)` avant de créer la fenêtre principale, pas après. La feuille de style QSS doit être appliquée à QApplication avant l'instanciation des widgets.

4. **Menu Drawer**: La fenêtre principale a un menu drawer à chargement paresseux. Le drawer est créé au premier accès dans [app.py](src/emac/gui/app.py):206-243, pas pendant `__init__`. Toujours vérifier `if self.drawer is not None` avant d'y accéder.

5. **Calculs de Dates**: Les dates d'évaluation s'étendent souvent 10 ans dans le futur. C'est intentionnel - le système trace la maintenance des compétences à long terme plutôt que des re-certifications fréquentes.

6. **Gestion des Contrats**: Le système d'expiration des contrats dans [contract.py](src/emac/services/contract.py) calcule les jours restants et met en évidence les renouvellements urgents (< 7 jours) avec des indicateurs d'avertissement.

7. **Migration des Imports**: Si vous travaillez avec l'ancien code de `App/core/`, les imports doivent être mis à jour:
   - `from core.db.configbd import ...` → `from emac.db.connection import ...`
   - `from core.services.evaluation_service import ...` → `from emac.services.evaluation import ...`
   - `from core.gui.ui_theme import ...` → `from emac.gui.components.theme import ...`

## Build et Déploiement

### Compiler l'Application

```bash
cd build/scripts
build.bat
```

La sortie sera dans `build/output/release/`

Configuration PyInstaller: [build/configs/emac.spec](build/configs/emac.spec)

### Déploiement

- **Local:** Utiliser `deploy/local/launcher.vbs`
- **Réseau:** Utiliser `deploy/network/deploy.bat`

Voir [build/README.md](build/README.md) et [deploy/README.md](deploy/README.md) pour plus de détails.

## Tests

Exécuter tous les tests:
```bash
cd tests
python run_tests.py
```

Les tests sont organisés en:
- `tests/unit/` - Tests unitaires
- `tests/integration/` - Tests d'intégration
- `tests/ui/` - Tests UI

## Documentation

- **Getting Started:** [docs/getting-started/](docs/getting-started/)
- **User Guides:** [docs/user-guides/](docs/user-guides/)
- **Developer Docs:** [docs/developer/](docs/developer/)
- **Deployment:** [docs/deployment/](docs/deployment/)
- **Security:** [docs/security/](docs/security/)
- **Features:** [docs/features/](docs/features/)

**Index:** [docs/README.md](docs/README.md)

## Outils de Développement

- **Setup:** [tools/setup/](tools/setup/)
- **Maintenance:** [tools/maintenance/](tools/maintenance/)
- **Migration:** [tools/migration/](tools/migration/)
- **Diagnostics:** [tools/diagnostics/](tools/diagnostics/)
- **Security:** [tools/security/](tools/security/)

## Contexte Important

Ce projet a été réorganisé le 2026-01-05 de l'ancienne structure `App/core/` vers la nouvelle structure `src/emac/`. Si vous rencontrez du code référençant les anciens chemins, il doit être migré vers la nouvelle structure.

Utilisez le script de migration: `tools/migration/migrate_imports.py` (à créer)
