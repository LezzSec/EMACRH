# EMAC — Application

Application PyQt5 de bureau pour la gestion RH et polyvalence en milieu industriel.

---

## Démarrage rapide

### Développeurs

```bash
# 1. Dépendances
pip install -r requirements.txt

# 2. Configuration base de données
cd config && configure_db.bat

# 3. Lancement
cd .. && py -m gui.main_qt
```

### Utilisateurs (réseau)

```
Double-clic sur EMAC.exe (depuis le partage réseau)
```

---

## Technologies

| Couche | Technologie |
|--------|-------------|
| Interface | PyQt5 5.15 |
| Base de données | MySQL 8.0 |
| Connecteur DB | mysql-connector-python |
| Sécurité | bcrypt, Fernet |
| Exports | openpyxl, reportlab, pandas |
| Géolocalisation | geo.api.gouv.fr, OSM Overpass, OSRM |
| Compilation | PyInstaller |
| Python | 3.12 |

---

## Structure

```
App/
├── domain/                   # Logique métier
│   ├── repositories/         # Accès données (Repository pattern)
│   └── services/             # Services par domaine (rh, geo, planning…)
│
├── infrastructure/           # Couche technique
│   ├── db/                   # Pool MySQL, QueryExecutor
│   ├── logging/              # log_hist / log_hist_async
│   ├── cache/                # emac_cache
│   ├── config/
│   └── security/
│
├── application/              # Cas d'utilisation transverses
│   └── permission_manager.py # Permissions / features (singleton)
│
├── gui/                      # Interface PyQt5
│   ├── main_qt.py            # Fenêtre principale
│   ├── components/           # Widgets réutilisables
│   ├── screens/              # Écrans par domaine
│   ├── view_models/
│   └── workers/              # DbWorker, threads
│
├── config/                   # .env.example, configure_db.bat
├── database/                 # Schéma SQL, migrations (~45), backups
├── scripts/                  # Scripts maintenance et migration
├── tests/                    # Tests unitaires et d'intégration
├── logs/                     # emac.log + crash.log  (Git ignore)
├── .env                      # Configuration locale  (Git ignore)
├── requirements.txt
└── run_emac.vbs              # Lanceur Windows
```

[Structure détaillée](../docs/STRUCTURE.md)

---

## Configuration

Le mot de passe DB **ne doit pas** être dans le code source.
Créer `App/.env` :

```env
EMAC_DB_HOST=localhost
EMAC_DB_USER=root
EMAC_DB_PASSWORD=votre_mot_de_passe
EMAC_DB_NAME=emac_db
```

> `.env` est dans `.gitignore` — ne jamais commiter.

[Guide complet](config/README.md)

---

## Base de données

| Table | Description |
|-------|-------------|
| `personnel` | Employés (nom, matricule, statut) |
| `personnel_infos` | Infos complémentaires (adresse, commune, distance) |
| `postes` | Postes de travail |
| `atelier` | Ateliers (contiennent des postes) |
| `polyvalence` | Compétences employé×poste (niveaux 1–4) |
| `historique` | Audit trail global |
| `historique_polyvalence` | Historique polyvalence |
| `contrats` | CDI, CDD, intérim |
| `absences` | Congés, RTT, maladie |
| `documents` | GED (upload, catégorie, expiration) |
| `users` | Comptes applicatifs (bcrypt) |
| `features` | Permissions granulaires |

Schéma : [database/schema/bddemac.sql](database/schema/bddemac.sql)
Migrations : [database/migrations/](database/migrations/)

---

## Fonctionnalités

- Personnel — fiches, matricules, statuts
- Polyvalence — matrice compétences, 4 niveaux, historique
- Évaluations — planification auto, alertes échéances
- Absences — congés, RTT, maladie, planning visuel
- Contrats — CDI/CDD/intérim, alertes renouvellement
- Documents — GED intégrée, templates, expiration
- RH intégré — vue unifiée par domaine (contrat, médical, vie salarié…)
- Distance domicile — calcul distance commune/mairie entreprise via OSM (RGPD-friendly)
- Permissions — rôles + features granulaires par utilisateur
- Audit — historique complet de toutes les actions

---

## Développement

### Conventions

- **Encodage** : UTF-8 + `# -*- coding: utf-8 -*-`
- **Langue UI** : Français
- **Dates affichage** : `format_date()` / `format_datetime()` depuis `domain/services/`
- **Logging** : `log_hist()` / `log_hist_async()` depuis `infrastructure/logging/optimized_db_logger.py`
- **Accès DB** : `QueryExecutor` depuis `infrastructure/db/query_executor.py` (jamais `mysql.connector.connect()` direct)
- **GUI → DB** : toujours via `domain/services/` ou `domain/repositories/` — jamais d'accès DB direct dans `gui/`

### Ajouter une fonctionnalité

1. Service dans `domain/services/` (hériter de `CRUDService` si CRUD)
2. Dialog dans `gui/screens/` (hériter de `EmacFormDialog`)
3. Intégrer dans `gui/main_qt.py`
4. Tests dans `tests/`

[Guide complet](../CLAUDE.md)

---

## Tests

```bash
py -m pytest tests/
```

---

## Compilation

```bash
cd build-scripts
build_optimized.bat
# → dist/EMAC/EMAC.exe
```

---

## Dépannage

| Problème | Solution |
|----------|----------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `Can't connect to MySQL` | Vérifier `App/.env` et que MySQL est démarré |
| `.exe ne démarre pas` | Vérifier que `_internal/` est présent et `App/.env` existe |
| `Access Denied` MySQL | Vérifier les permissions de l'utilisateur dans MySQL |
| Logs introuvables | `App/logs/emac.log` et `App/logs/crash.log` |

---

## Logs

- Développement : `App/logs/emac.log`
- Crash : `App/logs/crash.log`
- Production : `dist/EMAC/logs/`

---

**v3.1** · 2026-04-20 · Production
