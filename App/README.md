# EMAC - Application

Application PyQt5 de bureau pour la gestion RH, la polyvalence et les processus administratifs en environnement industriel.

## Technologies

| Couche | Technologie |
|---|---|
| Interface | PyQt5 5.15 |
| Base de données | MySQL / MariaDB |
| Connecteur DB | `mysql-connector-python` |
| Sécurité | `bcrypt`, `cryptography`, permissions granulaires |
| Exports | `openpyxl`, `reportlab` |
| Géolocalisation | `geo.api.gouv.fr`, Overpass, OSRM/OpenRouteService |
| Packaging | PyInstaller |
| Python | 3.12 |

## Lancement

Depuis ce dossier :

```bash
pip install -r requirements.txt
py -m gui.main_qt
```

Ou via le lanceur Windows :

```text
run_emac.vbs
```

En production, l'utilisateur lance `EMAC.exe` depuis le dossier ou partage réseau préparé.

## Structure

```
App/
├── main.py                         # Point d'entrée avec login puis fenêtre principale
├── __main__.py
├── application/                    # Permissions, event bus, triggers documents
├── cli/                            # Commandes CLI, dont migrations
├── config/                         # .env.example et configure_db.bat
├── database/                       # Schémas, migrations, déploiement
├── domain/
│   ├── models.py
│   ├── repositories/               # Accès données orienté domaine
│   └── services/                   # Services métier RH, formation, planning...
├── gui/
│   ├── main_qt.py                  # Bootstrap GUI
│   ├── main_qt/                    # MainWindow découpée
│   ├── components/                 # UI kit, dialogs, thème
│   ├── screens/                    # Écrans par domaine
│   ├── view_models/                # État et logique de présentation
│   └── workers/                    # Threads / chargement asynchrone
├── infrastructure/
│   ├── db/                         # Pool DB, QueryExecutor
│   ├── cache/                      # Cache applicatif
│   ├── config/                     # Chemins, dates, monitoring
│   ├── logging/                    # Logs applicatifs et audit
│   └── security/                   # Sécurité config, hors secret réel
├── scripts/                        # Scripts de maintenance
├── templates/                      # Modèles bureautiques
└── tests/                          # Unitaires, intégration, smoke
```

## Configuration

Le mot de passe DB n'est pas dans le code source. Créer `App/.env` :

```env
EMAC_DB_HOST=127.0.0.1
EMAC_DB_PORT=3306
EMAC_DB_USER=gestionrh
EMAC_DB_PASSWORD=votre_mot_de_passe
EMAC_DB_NAME=emac_db
EMAC_DB_POOL_SIZE=10
```

Variables optionnelles pour la distance domicile :

```env
EMAC_COMPANY_INSEE=00000
EMAC_COMPANY_COMMUNE=Votre commune
EMAC_COMPANY_LAT=00.0000
EMAC_COMPANY_LON=0.0000
EMAC_COMPANY_MAIRIE_LAT=00.0000
EMAC_COMPANY_MAIRIE_LON=0.0000
OPENROUTESERVICE_API_KEY=
```

## Conventions de développement

- Imports actuels : `infrastructure.*`, `domain.*`, `application.*`, `gui.*`.
- Accès DB : utiliser `QueryExecutor` ou les repositories/services.
- GUI : éviter le SQL direct dans les écrans ; passer par les services ou view models.
- Dates : utiliser les helpers de formatage du projet.
- Audit : utiliser les services de logging existants.
- Permissions : passer par `application.permission_manager`.
- Secrets : ne jamais commiter `.env`, `.env.encrypted` ni clé de chiffrement réelle.

## Fonctionnalités

- Personnel, fiches salariés et données complémentaires.
- Polyvalence, grilles, niveaux, évaluations et historique.
- Formation, catalogue, besoins par poste, attestations.
- Contrats, absences, congés, planning et régularisation.
- RH intégré : médical, mutuelle, mobilité, déclarations, compétences, vie salarié.
- Documents RH, templates, expiration et règles automatiques.
- Distance domicile par commune/mairie, approche RGPD-friendly.
- Administration : utilisateurs, rôles, permissions, modules.
- Audit : historique applicatif, connexions et tentatives échouées.

## Base de données

```bash
python -m cli migrate --status
python -m cli migrate --apply-all
```

Les migrations actives vont jusqu'à `054_password_upgrade_flag.sql`. Le suivi se fait dans `schema_migrations` par nom de fichier.

## Tests

```bash
python -m pytest tests/ -v
python -m pytest tests/ -v -m "not integration"
```

Voir [tests/README_TESTS.md](tests/README_TESTS.md).

## Compilation

Depuis la racine du dépôt :

```bash
cd build-scripts
build_optimized.bat
```
