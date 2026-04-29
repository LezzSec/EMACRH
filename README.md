# EMAC - Gestion RH, polyvalence et planning

Application de bureau Windows en Python/PyQt5 pour la gestion du personnel, de la polyvalence, des formations, des contrats, des absences, des documents RH et des alertes associées.

| | |
|---|---|
| Type | Application lourde PyQt5 |
| Version documentée | 3.1, état projet au 27/04/2026 |
| Python | 3.12 |
| Base de données | MySQL / MariaDB, charset `utf8mb4` |
| Lancement dev | `cd App && py -m gui.main_qt` |
| Configuration | `App/.env`, non versionné |

## Architecture

```
App/
├── gui/              # Interface PyQt5, écrans, composants, workers
├── domain/           # Services métier, repositories, modèles, interfaces
├── application/      # Cas d'utilisation transverses, permissions, événements
├── infrastructure/   # DB, cache, logs, config, sécurité
├── database/         # Schémas, migrations, scripts de déploiement
├── scripts/          # Maintenance, diagnostic, migrations ponctuelles
├── tests/            # Tests unitaires et intégration
├── templates/        # Modèles Excel/Word utilisés par l'application
└── config/           # Exemple de .env et aide de configuration
```

L'accès base de données passe par `infrastructure.db.configbd` et `infrastructure.db.query_executor.QueryExecutor`. Les écrans GUI doivent rester au maximum consommateurs de services métier, pas de SQL direct.

## Modules principaux

- Personnel : fiches salariés, matricules, statuts, données complémentaires.
- Polyvalence : niveaux par poste, grilles, historique, documents associés.
- Formation : catalogue, besoins par poste, évaluations, attestations.
- Planning / absences : demandes, congés, RTT, maladie, calendrier.
- RH intégré : contrat, médical, déclaration, compétences, mobilité, mutuelle, vie salarié.
- Documents : stockage, templates, catégories, expiration, règles de déclenchement.
- Distance domicile : calcul par commune/mairie, sans géocoder l'adresse exacte.
- Administration : utilisateurs, rôles, permissions granulaires, modules applicatifs.
- Audit : historique et logs de connexion/tentatives.

## Démarrage développeur

```bash
cd App
pip install -r requirements.txt
cd config
configure_db.bat
cd ..
py -m gui.main_qt
```

Configuration minimale dans `App/.env` :

```env
EMAC_DB_HOST=127.0.0.1
EMAC_DB_PORT=3306
EMAC_DB_USER=gestionrh
EMAC_DB_PASSWORD=votre_mot_de_passe
EMAC_DB_NAME=emac_db
```

Le fichier `.env` ne doit jamais être commité.

## Base de données

Les migrations sont dans `App/database/migrations/` et sont suivies par la table `schema_migrations`, par nom de fichier complet. Les dernières migrations présentes vont jusqu'à `056_mutuelle_ui_support.sql`.

Commandes utiles :

```bash
cd App
python -m cli migrate --status
python -m cli migrate --apply-all
python -m cli migrate --apply 056_mutuelle_ui_support.sql
```

## Tests

```bash
cd App
python -m pytest tests/ -v
python -m pytest tests/ -v -m "not integration"
```

La suite contient des tests unitaires sur les services, la sécurité, les permissions, la DB, les view models et des tests d'intégration/smoke.

## Build

```bash
cd build-scripts
build_release.bat
```

La sortie attendue est `dist/EMAC/EMAC.exe`.

## Documentation utile

- [Application](App/README.md)
- [Configuration](App/config/README.md)
- [Base de données](App/database/README.md)
- [Migrations](App/database/migrations/README.md)
- [Tests](App/tests/README_TESTS.md)
