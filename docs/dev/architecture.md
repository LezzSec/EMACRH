# Architecture EMAC

---

## Couches applicatives

```
┌──────────────────────────────────────────────────────────────┐
│  GUI  (core/gui/)                                            │
│  PyQt5 · Dialogs · Widgets · Thème                          │
│  Règle : JAMAIS d'accès DB direct                           │
└───────────────────────┬──────────────────────────────────────┘
                        │ appels
┌───────────────────────▼──────────────────────────────────────┐
│  Services  (core/services/)                                  │
│  Logique métier · Validation · Logging automatique           │
│  CRUDService, PersonnelService, rh_service_refactored…       │
└───────────────────────┬──────────────────────────────────────┘
                        │ appels
┌───────────────────────▼──────────────────────────────────────┐
│  Repositories  (core/repositories/)                          │
│  Accès données · Pagination · Filtres                        │
│  PersonnelRepository, PolyvalenceRepository…                 │
└───────────────────────┬──────────────────────────────────────┘
                        │ appels
┌───────────────────────▼──────────────────────────────────────┐
│  QueryExecutor  (core/db/query_executor.py)                  │
│  fetch_all · fetch_one · execute_write · exists · count      │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  Pool de connexions  (core/db/configbd.py)                   │
│  5 connexions · timeout 5s · reconnexion auto                │
└───────────────────────┬──────────────────────────────────────┘
                        │
               MySQL 8.0  (emac_db)
```

---

## GUI (`core/gui/`)

### Fenêtre principale

- **`main_qt.py`** — Fenêtre principale, menu tiroir (drawer) lazy-loaded, crash handler → `logs/crash.log`

### Dialogs métier

| Fichier | Rôle |
|---------|------|
| `gestion_rh.py` | `GestionRHDialog` + `GestionRHWidget` (mixin `_GestionRHMixin`) |
| `gestion_rh_dialogs.py` | Dialogs RH : contrat, médical, déclaration, formation… |
| `gestion_personnel.py` | Fiche complète employé |
| `gestion_evaluation.py` | Évaluations, niveaux, alertes |
| `gestion_absences.py` | Demandes d'absence, validation |
| `planning_absences.py` | Vue planning + demandes CP/RTT |
| `gestion_formations.py` | Suivi des formations |
| `gestion_alertes_rh.py` | Tableau de bord alertes |
| `gestion_documentaire.py` | GED principale |
| `gestion_templates.py` | Templates de documents |
| `admin_data_panel.py` | Données de référence (ateliers, types, jours fériés…) |
| `liste_et_grilles.py` | Grilles polyvalence par atelier |
| `historique.py` | Audit trail |
| `contract_management_refactored.py` | Gestion contrats |
| `feature_puzzle.py` | Permissions granulaires |
| `user_management.py` | Comptes utilisateurs |

### Infrastructure UI

| Fichier | Rôle |
|---------|------|
| `ui_theme.py` | `EmacTheme`, `EmacDarkTheme` — appliquer avant `MainWindow` |
| `emac_ui_kit.py` | `EmacButton`, `EmacCard`, `show_error_message()` |
| `emac_dialog.py` | `EmacDialog`, `EmacFormDialog`, `EmacTableDialog` |
| `db_worker.py` | `DbWorker`, `DbThreadPool` — toutes les requêtes DB hors UI thread |
| `lazy_loading.py` | `LazyTabWidget`, `PaginatedTableWidget` |
| `loading_components.py` | `LoadingLabel`, `LoadingPlaceholder`, `ErrorPlaceholder` |
| `session_timeout.py` | Déconnexion auto après 30 min d'inactivité |

---

## Services (`core/services/`)

### Patterns de base

| Fichier | Rôle |
|---------|------|
| `crud_service.py` | Classe de base `CRUDService` — create/update/delete + logging auto |
| `optimized_db_logger.py` | `log_hist()`, `log_hist_async()` — audit trail |
| `logger.py` | Shim de compatibilité → redirige vers `optimized_db_logger` |
| `permission_manager.py` | `perm.can()`, `require()`, cache 5 min |

### Services CRUD

| Fichier | Tables |
|---------|--------|
| `personnel_service.py` | `personnel` |
| `contrat_service_crud.py` | `contrats` |
| `absence_service_crud.py` | `absences` |
| `formation_service_crud.py` | `formations` |
| `declaration_service_crud.py` | `declarations` |

### Services métier

| Fichier | Rôle |
|---------|------|
| `rh_service_refactored.py` | Agrégation données RH par domaine (1 109 lignes, référence officielle) |
| `evaluation_service.py` | Planification évaluations, calcul prochaine date |
| `calendrier_service.py` | Calculs jours ouvrés, fériés |
| `grilles_service.py` | Génération PDF/Excel grilles polyvalence |
| `alert_service.py` | Détection et envoi des alertes |
| `template_service.py` | Génération documents depuis templates Word/ODF |
| `polyvalence_logger.py` | `log_polyvalence_action()` → `historique_polyvalence` |
| `config_service.py` | Données de référence (ateliers, types absence, jours fériés…) |
| `auth_service.py` | Login, bcrypt, session |

---

## Repositories (`core/repositories/`)

| Fichier | Méthodes clés |
|---------|---------------|
| `base.py` | `BaseRepository`, `SafeQueryBuilder` |
| `personnel_repo.py` | `get_actifs()`, `get_paginated()`, `search()` |
| `polyvalence_repo.py` | `get_by_operateur()`, `update_niveau()` |
| `contrat_repo.py` | `get_actif()`, `get_expirant_bientot()` |
| `poste_repo.py` | `get_all_with_atelier()` |
| `absence_repo.py` | `get_by_personnel()`, `get_paginated()` |

---

## DB (`core/db/`)

### QueryExecutor

```python
from core.db.query_executor import QueryExecutor

# Lire
rows = QueryExecutor.fetch_all("SELECT * FROM personnel WHERE statut = %s", ('ACTIF',), dictionary=True)
row  = QueryExecutor.fetch_one("SELECT * FROM personnel WHERE id = %s", (1,), dictionary=True)

# Écrire (retourne last insert id)
new_id = QueryExecutor.execute_write("INSERT INTO ...", params)

# Vérifier
exists = QueryExecutor.exists('personnel', {'id': 1})
count  = QueryExecutor.count('personnel', {'statut': 'ACTIF'})
```

### Connection Pool

```python
# ✅ Utiliser DatabaseCursor pour les cas complexes
from core.db.configbd import DatabaseCursor
with DatabaseCursor(dictionary=True) as cur:
    cur.execute("SELECT ...")
    rows = cur.fetchall()

# ❌ NE JAMAIS utiliser mysql.connector.connect() directement
```

---

## Utils (`core/utils/`)

| Fichier | Exports principaux |
|---------|-------------------|
| `date_format.py` | `format_date()`, `format_datetime()`, `format_timestamp()` |
| `logging_config.py` | `get_logger()`, `set_log_context()`, `setup_logging()`, `get_logs_dir()` |
| `config_crypter.py` | Chiffrement `.env.encrypted` — clé dérivée de la machine |
| `cache.py` | Cache générique TTL |
| `performance_monitor.py` | `@monitor_query` décorateur |

---

## Base de données

### Tables principales

| Table | Rôle |
|-------|------|
| `personnel` | Employés (id, nom, prenom, matricule, statut) |
| `postes` | Postes de travail (code, atelier_id) |
| `atelier` | Ateliers (contiennent des postes) |
| `polyvalence` | Compétences employé×poste (niveau 1–4, dates éval) |
| `historique` | Audit trail global |
| `historique_polyvalence` | Historique modifications polyvalence |
| `contrats` | Contrats (type, dates, actif) |
| `absences` | Absences / congés |
| `documents` | GED (chemin, catégorie, expiration) |
| `users` | Comptes applicatifs (bcrypt) |
| `features` | Catalogue de permissions granulaires |
| `role_features` | Permissions par rôle |
| `user_features` | Overrides par utilisateur |

### Migrations

Fichiers SQL dans `App/database/migrations/` — numérotés `001_` → `~040_`.
Appliquer dans l'ordre sur une nouvelle base.

---

## Patterns obligatoires

### Logging (audit trail)

```python
from core.services.optimized_db_logger import log_hist

log_hist("CREATION_CONTRAT", "operateurs", operateur_id, "CDI signé", utilisateur="jdupont")
```

### Permissions

```python
from core.services.permission_manager import perm, can, require

# UI (cache, non critique)
if can("rh.personnel.edit"):
    btn_edit.setEnabled(True)

# Service (vérifie en DB, critique)
require("rh.personnel.delete")  # lève PermissionError si refusé
```

### Dates

```python
from core.utils.date_format import format_date, format_datetime, format_timestamp

label.setText(format_date(some_date))          # "17/03/2026"
label.setText(format_datetime(some_datetime))  # "17/03/2026 14:30:00"
batch_id = f"IMPORT_{format_timestamp()}"      # "IMPORT_20260317_143000"
```

### Erreurs (ne pas exposer les détails à l'utilisateur)

```python
from core.utils.logging_config import get_logger
logger = get_logger(__name__)

try:
    do_something()
except Exception as e:
    logger.exception(f"Erreur XYZ: {e}")  # traceback complet dans les logs
    QMessageBox.critical(self, "Erreur", "Operation impossible. Consultez les logs.")
```

---

**Dernière mise à jour** : 2026-03-17
