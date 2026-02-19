# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EMAC is a PyQt5-based desktop application for managing personnel evaluations, polyvalence (skill versatility), and contracts in an industrial/workshop environment. The application tracks employee skills across multiple work positions (postes), schedules evaluations, and manages contract renewals.

## Running the Application

```bash
# Run from the App directory
cd App
py -m core.gui.main_qt

# Alternative: Use the provided launcher (Windows)
# Double-click: App/run_emac.vbs
```

## Database Configuration

The application uses MySQL 8.0 with the following connection details:
- Host: `localhost` (configurable via `EMAC_DB_HOST`)
- User: `root` (configurable via `EMAC_DB_USER`)
- Database: `emac_db` (configurable via `EMAC_DB_NAME`)
- Charset: `utf8mb4`
- Configuration file: [App/core/db/configbd.py](App/core/db/configbd.py)

### 🔐 Security: Password Configuration

The database password is **NO LONGER hardcoded** in the source code. It is loaded from:

1. **Environment variables** (recommended for production):
   ```bash
   set EMAC_DB_PASSWORD=your_password_here
   ```

2. **`.env` file** (recommended for development):
   ```bash
   # Run the configuration script (Windows)
   cd App/config
   configure_db.bat

   # Or manually create .env file
   copy config/.env.example .env
   # Edit App/.env with your password
   ```

3. **No default fallback**: Configuration is now **mandatory** for security reasons.

**Important**: The `.env` file is in `.gitignore` and will never be committed to Git.

For detailed configuration instructions, see [docs/security/database-credentials.md](docs/security/database-credentials.md).
For security changelog, see [docs/security/security-changelog.md](docs/security/security-changelog.md).

Database schema is located in [App/database/schema/bddemac.sql](App/database/schema/bddemac.sql).

### ⚡ Database Performance Optimizations (2026-01-07)

**IMPORTANT**: Major database optimizations have been implemented for 10-100x performance gains:

1. **MySQL Connection Pool** ([configbd.py](App/core/db/configbd.py))
   - All connections go through `get_connection()` from the centralized pool
   - 5 reusable connections with 5-second timeout
   - Automatic ping/reconnect after PC sleep
   - ❌ **NEVER use** `mysql.connector.connect()` directly

2. **Context Managers** (standardized DB access)
   ```python
   # ✅ RECOMMENDED: Use DatabaseConnection or DatabaseCursor
   from core.db.configbd import DatabaseConnection, DatabaseCursor

   # Simple queries
   with DatabaseCursor(dictionary=True) as cur:
       cur.execute("SELECT * FROM personnel WHERE statut = 'ACTIF'")
       results = cur.fetchall()

   # Complex operations
   with DatabaseConnection() as conn:
       cur = conn.cursor()
       cur.execute("INSERT ...")
       # Auto commit/rollback/close
   ```

3. **Performance Indexes** (29 indexes on 9 tables)
   - Apply with: `python App/scripts/apply_performance_indexes.py`
   - Migration file: [App/database/migrations/001_add_performance_indexes.sql](App/database/migrations/001_add_performance_indexes.sql)
   - Critical indexes on: `personnel.statut`, `polyvalence.prochaine_evaluation`, `polyvalence.operateur_id`, etc.

4. **Optimized Queries**
   - Authentication fetches user + role + permissions in 1 query instead of 2
   - Avoid N+1 queries (use JOINs instead of loops with queries)

**Full documentation**: [docs/dev/optimisation-database.md](docs/dev/optimisation-database.md)

### 🔧 Refactoring Patterns - Code Duplication Elimination (2026-02-09)

**IMPORTANT**: Nouveaux patterns pour éliminer le code dupliqué (-650 lignes) et améliorer la maintenabilité.

#### 1. **QueryExecutor** - Accès base de données centralisé ([App/core/db/query_executor.py](App/core/db/query_executor.py))

✅ **UTILISER** `QueryExecutor` pour tous les accès DB au lieu de `with DatabaseCursor`:

```python
from core.db.query_executor import QueryExecutor

# ✅ BON: Récupérer des données
personnels = QueryExecutor.fetch_all(
    "SELECT * FROM personnel WHERE statut = %s",
    ('ACTIF',),
    dictionary=True
)

# ✅ BON: Insérer/Modifier
new_id = QueryExecutor.execute_write(
    "INSERT INTO personnel (nom, prenom) VALUES (%s, %s)",
    ('Dupont', 'Jean')
)

# ✅ BON: Compter / Vérifier existence
count = QueryExecutor.count('personnel', {'statut': 'ACTIF'})
exists = QueryExecutor.exists('personnel', {'id': 1})

# ❌ ÉVITER: Code boilerplate avec try/finally
# with DatabaseCursor() as cur:
#     cur.execute(...)
#     result = cur.fetchall()
```

**Méthodes disponibles**: `fetch_all()`, `fetch_one()`, `fetch_scalar()`, `execute_write()`, `execute_many()`, `exists()`, `count()`

#### 2. **Services CRUD** - Services métier standardisés

✅ **UTILISER** les services CRUD au lieu de requêtes SQL manuelles:

```python
from core.services.personnel_service import PersonnelService
from core.services.formation_service_crud import FormationServiceCRUD
from core.services.contrat_service_crud import ContratServiceCRUD
from core.services.polyvalence_service_crud import PolyvalenceServiceCRUD
from core.services.absence_service_crud import AbsenceServiceCRUD

# ✅ BON: Créer avec logging automatique
success, msg, new_id = PersonnelService.create(
    nom="Dupont",
    prenom="Jean",
    statut="ACTIF"
)

# ✅ BON: Mettre à jour
PersonnelService.update(record_id=1, statut="INACTIF")

# ✅ BON: Récupérer avec filtres
actifs = PersonnelService.get_actifs()
formations = FormationServiceCRUD.get_by_operateur(operateur_id=1)

# ❌ ÉVITER: SQL manuel avec logging manuel
# with DatabaseConnection() as conn:
#     cur = conn.cursor()
#     cur.execute("INSERT INTO personnel ...")
#     log_hist("CREATION_PERSONNEL", ...)
```

**Services disponibles**:
- `PersonnelService` - Gestion personnel
- `FormationServiceCRUD` - Gestion formations
- `ContratServiceCRUD` - Gestion contrats
- `PolyvalenceServiceCRUD` - Gestion compétences
- `AbsenceServiceCRUD` - Gestion absences

**Avantages**: Logging automatique, validation des champs, méthodes utilitaires

#### 3. **EmacDialog** - Dialogs standardisés ([App/core/gui/emac_dialog.py](App/core/gui/emac_dialog.py))

✅ **UTILISER** `EmacDialog` ou `EmacFormDialog` pour tous les nouveaux dialogs:

```python
from core.gui.emac_dialog import EmacFormDialog

class MyFormDialog(EmacFormDialog):
    def __init__(self, parent=None):
        super().__init__(title="Mon Formulaire", parent=parent)

    def init_ui(self):
        # Ajouter vos widgets au self.content_layout
        self.name_input = QLineEdit()
        self.content_layout.addWidget(self.name_input)

    def validate(self):
        if not self.name_input.text():
            return False, "Le nom est obligatoire"
        return True, ""

    def save_to_db(self):
        PersonnelService.create(nom=self.name_input.text(), ...)

# ❌ ÉVITER: Dupliquer le code boilerplate de QDialog
# class MyDialog(QDialog):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle(...)
#         layout = QVBoxLayout(self)
#         scroll = QScrollArea()  # ... 50+ lignes de setup
```

**Classes disponibles**:
- `EmacDialog` - Base générique
- `EmacFormDialog` - Formulaire avec scroll + boutons + validation
- `EmacTableDialog` - Dialog avec table

**Avantages**: Structure standardisée, validation automatique, -80 lignes de code par dialog

#### 4. **CRUDService Base Class** - Pour créer de nouveaux services

✅ **CRÉER** de nouveaux services en héritant de `CRUDService`:

```python
from core.services.crud_service import CRUDService

class MonNouveauService(CRUDService):
    TABLE_NAME = "ma_table"
    ACTION_PREFIX = "MA_TABLE_"
    ALLOWED_FIELDS = ['champ1', 'champ2', 'champ3']

# Méthodes disponibles automatiquement:
# - create(), update(), delete()
# - get_by_id(), get_all(), exists(), count()
# - Logging automatique dans historique
```

#### 📚 Documentation complète

- **Guide de refactoring**: [docs/dev/refactoring-guide-2026-02-09.md](docs/dev/refactoring-guide-2026-02-09.md)
- **Script de test**: `py -m scripts.test_new_patterns`

#### ✅ Règles pour nouveaux développements (OBLIGATOIRE)

1. ❌ **NE PLUS** créer de code avec `with DatabaseCursor` en try/finally → ✅ Utiliser `QueryExecutor`
2. ❌ **NE PLUS** dupliquer le code de création de dialogs → ✅ Hériter de `EmacFormDialog`
3. ❌ **NE PLUS** écrire CRUD + logging manuellement → ✅ Hériter de `CRUDService`
4. ✅ **TOUJOURS** utiliser les services existants (PersonnelService, FormationServiceCRUD, etc.)
5. ❌ **INTERDIT dans `core/gui/`** : importer ou utiliser directement `DatabaseCursor`, `DatabaseConnection`, `QueryExecutor`, `get_connection()` ou tout autre accès DB direct. La couche GUI ne communique **QU'AVEC** `core/services/` ou `core/repositories/`.

#### 🚫 Séparation stricte GUI / Service (Architecture)

```
❌ INTERDIT dans core/gui/*.py :
   from core.db.configbd import DatabaseCursor, DatabaseConnection
   from core.db.query_executor import QueryExecutor
   conn = get_connection()
   cur.execute("SELECT ...")

✅ OBLIGATOIRE dans core/gui/*.py :
   from core.services.personnel_service import PersonnelService
   from core.services.rh_service_refactored import get_contrats_operateur
   from core.repositories.personnel_repo import PersonnelRepository
   # → La GUI appelle les services, les services accèdent à la DB
```

**Fichier de référence officiel RH** : `rh_service_refactored.py` (1 109 lignes, QueryExecutor)
❌ `rh_service.py` a été **supprimé** le 2026-02-18 — ne pas recréer.

### ⚡ UI / Threads Optimizations (2026-01-07)

**IMPORTANT**: UI responsiveness optimizations to prevent freezes:

1. **DbWorker System** ([App/core/gui/db_worker.py](App/core/gui/db_worker.py))
   - Generic worker for all DB operations
   - QThreadPool configured automatically (4 threads max, aligned with MySQL pool)
   - Signals: `result`, `error`, `progress`, `started`, `finished`
   - ❌ **NEVER run** DB queries in the main (UI) thread

2. **Loading Components** ([App/core/gui/loading_components.py](App/core/gui/loading_components.py))
   - `LoadingLabel` - Simple loading label with animated dots
   - `LoadingPlaceholder` - Complete widget with icon
   - `ProgressWidget` - Progress bar with percentage
   - `EmptyStatePlaceholder` - Empty state display
   - `ErrorPlaceholder` - Error display
   - Helper functions: `replace_widget_with_loading()`, etc.

3. **2-Stage Loading Pattern**
   ```python
   def __init__(self):
       # Stage 1: Build minimal UI (0-50ms)
       self.setup_ui_skeleton()

       # Stage 2: Show immediately with placeholders
       self.show()

       # Stage 3: Load data in background (after display)
       QTimer.singleShot(100, self.load_data_async)
   ```

4. **Usage Example**
   ```python
   from core.gui.db_worker import DbWorker, DbThreadPool
   from core.gui.loading_components import LoadingLabel

   # Show placeholder
   loading = LoadingLabel("Loading data")
   layout.addWidget(loading)

   # Load in background
   worker = DbWorker(fetch_function)
   worker.signals.result.connect(on_success)
   worker.signals.error.connect(on_error)
   DbThreadPool.start(worker)
   ```

**Full documentation**: [docs/dev/optimisation-ui-threads.md](docs/dev/optimisation-ui-threads.md)

### ⚡ Lazy Loading & Pagination (2026-01-26)

**IMPORTANT**: Startup and list performance optimizations:

1. **Lazy Tab Loading** ([App/core/gui/lazy_loading.py](App/core/gui/lazy_loading.py))
   - `LazyTabWidget` - Tabs are only created when first clicked
   - Reduces startup time significantly for dialogs with many tabs
   - Usage:
   ```python
   from core.gui.lazy_loading import LazyTabWidget

   tabs = LazyTabWidget()
   tabs.add_lazy_tab("Personnel", lambda: PersonnelTab())
   tabs.add_lazy_tab("Contrats", lambda: ContratsTab())
   # Tabs are created on-demand, not at startup
   ```

2. **Paginated Tables** ([App/core/gui/lazy_loading.py](App/core/gui/lazy_loading.py))
   - `PaginatedTableWidget` - Load data by pages instead of all at once
   - Built-in pagination controls (first, prev, next, last)
   - Server-side filtering support
   - Usage:
   ```python
   from core.gui.lazy_loading import PaginatedTableWidget

   def fetch_data(offset, limit, filters):
       return PersonnelRepository.get_paginated(offset, limit, filters)

   table = PaginatedTableWidget(
       fetch_fn=fetch_data,
       columns=["Nom", "Prénom", "Statut"],
       page_size=50
   )
   table.set_filters({"statut": "ACTIF"})
   ```

3. **Repository Pagination** ([App/core/repositories/](App/core/repositories/))
   - All repositories support `get_paginated()` method
   - Returns (rows, total_count) for proper pagination
   - Example:
   ```python
   from core.repositories import PersonnelRepository

   rows, total = PersonnelRepository.get_paginated(
       offset=0, limit=50,
       filters={"statut": "ACTIF", "search": "Dupont"}
   )
   ```

4. **SELECT Optimization**
   - ❌ Avoid `SELECT *` on large tables
   - ✅ Use specific columns: `SELECT id, nom, prenom FROM personnel`
   - Repositories now use `cls.COLUMNS` for explicit column lists

### 📝 Logging System (2026-01-27)

**IMPORTANT**: Centralized logging configuration for production-ready logs:

1. **Configuration** ([App/core/utils/logging_config.py](App/core/utils/logging_config.py))
   - Centralized setup with `RotatingFileHandler` → `logs/emac.log`
   - 10 MB max file size, 5 backup files
   - Context includes: user_id, screen/action, timestamp
   - ❌ **NEVER use** `print()` for debugging in services/GUI
   - ❌ **NEVER use** `traceback.print_exc()` - use `logger.exception()` instead

2. **Modes**
   - **Development** (default): DEBUG level, logs to console + file
   - **Production** (`EMAC_ENV=production`): WARNING level, logs to file only

3. **Usage**
   ```python
   from core.utils.logging_config import get_logger, set_log_context

   logger = get_logger(__name__)

   # Basic logging
   logger.debug("Debug message (dev only)")
   logger.info("Info message")
   logger.warning("Warning message")
   logger.error("Error message")

   # With exception traceback (in except block)
   try:
       something()
   except Exception as e:
       logger.exception(f"Error in something: {e}")  # Includes full traceback

   # Set context (user_id, screen) after login
   set_log_context(user_id="jdupont", screen="GestionEvaluation")
   ```

4. **Log Format**
   ```
   2026-01-27 14:30:00 | INFO     | core.gui.main_qt | [jdupont] [MainWindow] | Application started
   ```

5. **Initialization** (already done in `main_qt.py`)
   ```python
   from core.utils.logging_config import setup_logging
   setup_logging(production_mode=os.getenv('EMAC_ENV') == 'production')
   ```

### 🔐 Permission System "Features" (2026-01-27)

**IMPORTANT**: New granular permission system based on "features":

1. **Architecture**
   - **Tables**: `features` (catalogue), `role_features`, `user_features` (overrides)
   - **PermissionManager**: Singleton with `perm.can("rh.personnel.edit")`
   - **Compatibility**: `has_permission()` maps to new features automatically
   - Migration: [010_add_features_system.sql](App/database/migrations/010_add_features_system.sql)

2. **Feature Naming Convention**
   - Format: `module.submodule.action`
   - Examples: `rh.personnel.edit`, `production.evaluations.view`, `admin.permissions`
   - Modules: RH, Production, Planning, Admin

3. **Usage in Code**
   ```python
   from core.services.permission_manager import perm, can, require, require_fresh

   # UI checks (uses cache for performance)
   if perm.can("rh.personnel.edit"):
       btn_edit.setVisible(True)

   # Shortcut function (cached)
   if can("production.grilles.export"):
       do_export()

   # Critical operation - ALWAYS verify fresh in DB (default)
   require("admin.permissions")  # Raises PermissionError, checks DB

   # Explicit fresh check (same as require())
   require_fresh("rh.personnel.delete")

   # Use cache for non-critical checks
   require("rh.view", fresh=False)  # Uses cache

   # Multiple features
   if perm.can_any("rh.view", "production.view"):
       show_dashboard()

   if perm.can_all("rh.contrats.edit", "rh.documents.edit"):
       allow_full_rh_access()
   ```

4. **Resolution Rules**
   - User override (TRUE/FALSE) → **wins**
   - Role feature → if no override, inherits from role
   - Default → denied

5. **UI Components**
   - **FeaturePuzzleWidget**: Grid by modules with OUI/NON/AUTO toggles
   - Access via: Gestion Utilisateurs → "🔐 Gérer les Features"
   - File: [feature_puzzle.py](App/core/gui/feature_puzzle.py)

6. **Security: Service-level checks** (Race Condition TOCTOU Protection)
   ```python
   # ✅ In services, ALWAYS use require() - checks DB by default
   def delete_personnel(personnel_id):
       require("rh.personnel.delete")  # Checks DB, not cache!
       # ... proceed with deletion

   # ❌ NEVER use can() for critical operations
   def bad_delete(personnel_id):
       if can("rh.personnel.delete"):  # Uses cache - INSECURE!
           # Permission could have been revoked since cache was loaded
   ```

7. **Cache TTL & Auto-Reload** (2026-02-04)
   - Cache expires after 5 minutes (`PERMISSION_CACHE_TTL_SECONDS`)
   - `can()` auto-reloads if cache is stale
   - `require()` always checks DB by default (fresh=True)
   - After permission modification, cache is invalidated AND reloaded

**Full list of features**: See [010_add_features_system.sql](App/database/migrations/010_add_features_system.sql)

### 🔐 Session Timeout (2026-02-04)

**IMPORTANT**: Automatic logout after inactivity period:

1. **Configuration** ([session_timeout.py](App/core/gui/session_timeout.py))
   - `SESSION_TIMEOUT_MINUTES = 30` - Logout after 30 minutes inactivity
   - `WARNING_BEFORE_MINUTES = 5` - Warning 5 minutes before
   - `CHECK_INTERVAL_SECONDS = 30` - Check every 30 seconds

2. **SessionTimeoutManager Features**
   - Tracks user activity (mouse, keyboard events)
   - Shows warning dialog before logout
   - Allows session extension
   - Logs automatic logouts to audit trail

3. **Integration in MainWindow**
   ```python
   # Automatically initialized in MainWindow.__init__
   self._timeout_manager = SessionTimeoutManager(self)
   self._timeout_manager.timeout_logout.connect(self._force_logout_timeout)
   ```

4. **Activity Detection**
   - Mouse movements, clicks
   - Keyboard input
   - Scroll events
   - Automatically resets timeout timer

5. **Security Benefits**
   - Protects unattended workstations
   - Reduces unauthorized access risk
   - Audit trail of timeout logouts (action: LOGOUT_TIMEOUT)

## Key Database Tables

- `personnel` / `operateurs`: Employee records with status (ACTIF/INACTIF)
- `postes`: Work positions with codes (e.g., "0506", "0830") linked to ateliers
- `atelier`: Workshops that contain multiple postes
- `polyvalence`: Junction table tracking employee skills at positions with evaluation dates and skill levels (1-4)
- `historique`: Audit log of all system actions
- `contrats`: Employment contracts with start/end dates and types

**Important**: The codebase is in transition - some files reference `operateurs` table while newer code uses `personnel`. Both tables contain employee data with fields: `id`, `nom`, `prenom`, `statut`.

## Architecture

### Core Module Structure

```
EMAC/
├── 📄 README.md                    # Main project documentation
├── 📄 CLAUDE.md                    # Instructions for Claude Code
│
├── 📁 docs/                        # Documentation
│   ├── dev/                        # Developer documentation
│   │   ├── architecture.md         # System architecture
│   │   ├── tests-report.md         # Test reports
│   │   ├── build-optimization.md   # Build & optimization guide
│   │   └── exemples-logging.md     # Logging examples
│   ├── user/                       # User guides
│   │   ├── guide-absences.md       # Absence management guide
│   │   └── guide-interface-historique.md
│   ├── features/                   # Feature documentation
│   │   ├── module-absences.md
│   │   ├── module-documents.md
│   │   └── historique-polyvalence.md
│   └── security/                   # Security documentation
│       ├── database-credentials.md # Credential management
│       └── security-changelog.md   # Security audit log
│
├── 📁 App/
│   ├── core/                               # Core application code
│   │   ├── db/                             # Database layer
│   │   │   ├── configbd.py                 # MySQL connection setup
│   │   │   ├── insert_*.py                 # Database population scripts
│   │   │   └── import_infos.py             # Data import utilities
│   │   ├── services/                       # Business logic layer
│   │   │   ├── evaluation_service.py       # Evaluation scheduling logic
│   │   │   ├── calendrier_service.py       # Calendar computations
│   │   │   ├── contrat_service.py          # Contract expiration tracking
│   │   │   ├── absence_service.py          # Absence management
│   │   │   ├── matricule_service.py        # Employee ID management
│   │   │   ├── liste_et_grilles_service.py # Grid generation
│   │   │   ├── logger.py                   # Historique table logging
│   │   │   └── log_exporter.py             # Export logs to files
│   │   ├── repositories/                   # Data access layer (Repository pattern)
│   │   │   ├── base.py                     # BaseRepository, SafeQueryBuilder
│   │   │   ├── personnel_repo.py           # Personnel CRUD + pagination
│   │   │   ├── contrat_repo.py             # Contract operations
│   │   │   ├── polyvalence_repo.py         # Skills/evaluations
│   │   │   ├── poste_repo.py               # Workstations + Ateliers
│   │   │   └── absence_repo.py             # Absence management
│   │   ├── models.py                       # DTOs/Dataclasses (Personnel, Contrat, etc.)
│   │   ├── gui/                            # PyQt5 UI layer
│   │   │   ├── main_qt.py                  # Main application window
│   │   │   ├── ui_theme.py                 # Theme system (EmacTheme, EmacDarkTheme)
│   │   │   ├── emac_ui_kit.py              # Reusable UI components
│   │   │   ├── db_worker.py                # Background DB workers (DbWorker, DbThreadPool)
│   │   │   ├── lazy_loading.py             # LazyTabWidget, PaginatedTableWidget
│   │   │   ├── loading_components.py       # Loading placeholders & progress widgets
│   │   │   ├── gestion_evaluation.py       # Evaluation management dialog
│   │   │   ├── gestion_personnel.py        # Personnel details & management
│   │   │   ├── gestion_absences.py         # Absence management dialog
│   │   │   ├── manage_operateur.py         # Add/edit employees
│   │   │   ├── liste_et_grilles.py         # Skill matrix grids
│   │   │   ├── creation_modification_poste.py   # Position CRUD
│   │   │   ├── historique.py               # Audit log viewer
│   │   │   ├── planning.py                 # Planning/schedule view
│   │   │   └── contract_management.py      # Contract renewal interface
│   │   ├── exporters/                      # File export layer
│   │   │   ├── excel_export.py             # Export grids to Excel
│   │   │   ├── pdf_export.py               # PDF generation with ReportLab
│   │   │   └── log_export.py               # CSV export of logs
│   │   └── utils/                          # Utility functions
│   │
│   ├── config/                    # Configuration templates
│   │   ├── .env.example           # Environment variables template
│   │   ├── configure_db.bat       # DB configuration script (Windows)
│   │   └── README.md              # Configuration guide
│   │
│   ├── database/                  # Database files
│   │   ├── schema/                # Schema definitions
│   │   │   └── bddemac.sql        # Main database schema
│   │   ├── migrations/            # Schema migrations
│   │   └── backups/               # SQL backup files
│   │
│   ├── tests/                     # Test files
│   │   ├── unit/                  # Unit tests
│   │   ├── integration/           # Integration tests
│   │   └── run_all_tests.py       # Test runner
│   │
│   ├── scripts/                   # Utility scripts
│   │   ├── cleanup_test_data.py
│   │   ├── fix_matricule_lowercase.py
│   │   ├── install_absences_module.py
│   │   └── quick_db_query.py
│   │
│   ├── .env                       # Local configuration (Git ignored)
│   ├── .gitignore
│   ├── logs/                      # Application logs (Git ignored)
│   ├── run/                       # Runtime files
│   └── run_emac.vbs               # Windows launcher
│
└── 📁 Deploy/                     # Deployment files
```

### UI Theme System

The application uses a custom theme system defined in [App/core/gui/ui_theme.py](App/core/gui/ui_theme.py):
- `EmacTheme`: Light theme (default)
- `EmacDarkTheme`: Dark theme variant
- Reusable components: `EmacButton`, `EmacCard`, `EmacStatusCard`, `EmacHeader`, `HamburgerButton`
- Apply theme with: `EmacTheme.apply(app)` before showing main window

### Service Layer Pattern

Services encapsulate business logic and database queries:
- Services are stateless utility modules (functions, not classes)
- All services use `get_db_connection()` from [configbd.py](App/core/db/configbd.py)
- Services must handle cursor cleanup with try/finally blocks
- Use `log_hist(action, description, operateur_id, poste_id)` from [logger.py](App/core/services/logger.py) for audit trail

Example service pattern:
```python
from core.db.configbd import get_connection
from core.services.logger import log_hist

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

## Evaluation System Logic

The polyvalence table tracks skill evaluations with a date-based system:
- `niveau`: Skill level from 1 (learning) to 4 (expert/trainer)
- `date_evaluation`: Date of last evaluation
- `prochaine_evaluation`: Scheduled next evaluation date (typically 10 years from evaluation date)
- Main dashboard shows overdue evaluations (retard) and upcoming evaluations

Evaluation scheduling uses a complex formula in [calendrier_service.py](App/core/services/calendrier_service.py) that accounts for:
- Current skill level
- Time since last evaluation
- Required frequency per level
- Business day calculations excluding weekends

## Common Development Tasks

### Adding a New Dialog Window

1. Create file in `App/core/gui/` inheriting from `QDialog`
2. Import theme components: `from core.gui.ui_theme import EmacTheme, EmacButton, EmacCard`
3. Use theme components for consistent styling
4. Add database access via `from core.db.configbd import get_connection`
5. Register in [main_qt.py](App/core/gui/main_qt.py) as menu item or action button

### Modifying Database Schema

1. Update [App/database/schema/bddemac.sql](App/database/schema/bddemac.sql) with schema changes
2. Create migration script in [App/database/migrations/](App/database/migrations/) if needed
3. Apply changes to local `emac_db` database
4. Update any affected `insert_*.py` scripts in [App/core/db/](App/core/db/)
5. Update service functions that query modified tables
6. Test UI components that display the affected data

### Adding New Export Format

1. Create exporter in `App/core/exporters/` following existing patterns
2. Export functions should accept data structures and return file paths
3. Use context managers for file operations
4. Register exporter in relevant UI dialogs (e.g., [gestion_evaluation.py](App/core/gui/gestion_evaluation.py))

## Dependencies

Required Python packages (from [requirements.txt](Fichiers inutilisés/requirements.txt)):
- PyQt5==5.15.10
- mysql-connector-python==8.4.0
- pandas==2.2.2
- openpyxl==3.1.5
- reportlab==4.2.2
- python-docx==1.1.2
- python-pptx==0.6.23
- odfpy==1.4.1
- pypandoc==1.13

Install with: `pip install -r requirements.txt`

## Code Conventions

- Use UTF-8 encoding with `# -*- coding: utf-8 -*-` header for files with French text
- Database cursors must be closed in `finally` blocks
- UI dialog classes follow naming pattern: `*Dialog` (e.g., `GestionEvaluationDialog`)
- Service modules use snake_case function names
- GUI modules import theme at top: `from core.gui.ui_theme import EmacTheme, ...`
- Date formatting: Use `strftime('%d/%m/%Y')` for display (DD/MM/YYYY French format)
- All user-facing text is in French

## 🔒 Security Patterns (2026-02-02)

**IMPORTANT**: Follow these security patterns to prevent vulnerabilities.

### 1. SQL Injection Prevention

```python
# ❌ NEVER: Dynamic column/table names with f-strings
cur.execute(f"SELECT * FROM {table} WHERE {column} = %s", (value,))

# ✅ ALWAYS: Use parameterized queries with whitelist validation
ALLOWED_COLUMNS = {'nom': 'nom', 'prenom': 'prenom', 'statut': 'statut'}

def get_by_column(column, value):
    if column not in ALLOWED_COLUMNS:
        raise ValueError(f"Colonne non autorisee: {column}")

    # Use predefined static queries
    queries = {
        'nom': "SELECT * FROM personnel WHERE nom = %s",
        'prenom': "SELECT * FROM personnel WHERE prenom = %s",
    }
    cur.execute(queries[column], (value,))
```

### 2. Path Traversal Prevention

```python
from pathlib import Path

# ❌ NEVER: Use user input directly in file paths
file_path = base_dir / user_input  # Dangerous!

# ✅ ALWAYS: Validate and resolve paths
def safe_file_access(user_input: str, allowed_dir: Path) -> Path:
    # Remove traversal attempts
    clean_input = user_input.replace('..', '').replace('\\', '/').strip('/')

    # Resolve to absolute path
    target_path = (allowed_dir / clean_input).resolve()

    # Verify containment
    try:
        target_path.relative_to(allowed_dir.resolve())
    except ValueError:
        raise PermissionError("Acces au fichier refuse")

    return target_path
```

### 3. Error Message Security (Information Disclosure)

```python
from core.gui.emac_ui_kit import show_error_message
import logging
logger = logging.getLogger(__name__)

# ❌ NEVER: Expose exception details to users
except Exception as e:
    QMessageBox.critical(self, "Erreur", f"Erreur: {e}")  # Exposes system info!

# ✅ ALWAYS: Log details, show generic message
except Exception as e:
    logger.exception(f"Erreur operation XYZ: {e}")  # Full traceback in logs
    show_error_message(self, "Erreur", "Operation impossible", e)  # Generic to user
```

### 4. Permission Checks in Services

```python
from core.services.permission_manager import require, can

# ✅ ALWAYS: Check permissions at service layer (not just UI)
def delete_personnel(personnel_id: int):
    require("rh.personnel.delete")  # Raises PermissionError if denied
    # ... proceed with deletion

# ✅ For conditional logic
if can("rh.personnel.edit"):
    # Show edit button
```

### 5. Subprocess/Command Execution

```python
import subprocess
from pathlib import Path

# ❌ NEVER: Execute commands with user-controlled paths
subprocess.run(['open', user_file])  # Command injection risk!

# ✅ ALWAYS: Validate file exists and is in allowed directory
def safe_open_file(file_path: Path, allowed_dirs: list[Path]):
    resolved = file_path.resolve()

    # Verify file exists
    if not resolved.is_file():
        raise FileNotFoundError("Fichier introuvable")

    # Verify in allowed directory
    if not any(resolved.is_relative_to(d) for d in allowed_dirs):
        raise PermissionError("Acces refuse")

    # Safe to execute
    if sys.platform == 'win32':
        os.startfile(str(resolved))
    else:
        subprocess.run(['xdg-open', str(resolved)])
```

### 6. Input Validation Pattern

```python
# ✅ Validate at system boundaries (user input, API responses)
def validate_matricule(matricule: str) -> str:
    if not matricule or not matricule.strip():
        raise ValueError("Matricule requis")

    # Whitelist allowed characters
    import re
    if not re.match(r'^[A-Z0-9]{4,10}$', matricule.upper()):
        raise ValueError("Format matricule invalide")

    return matricule.upper().strip()
```

### Security Audit Reports

- Latest audit: [docs/security/audit-report-2026-02-02.md](docs/security/audit-report-2026-02-02.md)
- Remediation: [docs/security/audit-remediation-2026-02-02.md](docs/security/audit-remediation-2026-02-02.md)

## Critical Implementation Notes

1. **Dual Table Names**: When querying employees, check if code uses `personnel` or `operateurs` table. The schema contains both and they may reference different foreign key relationships.

2. **Historique Logging**: Use `log_hist()` from [logger.py](App/core/services/logger.py) rather than the older `log_action()` from [audit_logger.py](App/core/services/audit_logger.py). The new logger writes to the `historique` database table.

3. **Theme Application**: Always call `EmacTheme.apply(app)` before creating the main window, not after. The QSS stylesheet must be applied to QApplication before widgets are instantiated.

4. **Drawer Menu**: The main window has a lazy-loaded sliding drawer menu. The drawer is created on first access in [main_qt.py](App/core/gui/main_qt.py):206-243, not during `__init__`. Always check `if self.drawer is not None` before accessing it.

5. **Date Calculations**: Evaluation dates often extend 10 years into the future. This is intentional - the system tracks long-term skill maintenance rather than frequent re-certification.

6. **Contract Management**: The contract expiration system in [contrat_service.py](App/core/services/contrat_service.py) calculates days remaining and highlights urgent renewals (< 7 days) with warning indicators.
