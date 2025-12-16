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
   cd App
   configure_db.bat

   # Or manually create .env file
   copy .env.example .env
   # Edit .env with your password
   ```

3. **Default value** (fallback for local dev only): `emacViodos$13`

**Important**: The `.env` file is in `.gitignore` and will never be committed to Git.

For detailed configuration instructions, see [App/SECURITE_DB.md](App/SECURITE_DB.md).

Database schema is located in [App/database/schema/bddemac.sql](App/database/schema/bddemac.sql).

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
├── docs/                          # Documentation
│   ├── GUIDE_UTILISATION_ABSENCES.md
│   ├── MODULE_ABSENCES_README.md
│   └── ANALYSE_FONCTIONNALITES_RH_MANQUANTES.md
├── App/
│   ├── core/                      # Core application code
│   │   ├── db/                    # Database layer
│   │   │   ├── configbd.py       # MySQL connection setup
│   │   │   ├── insert_*.py       # Database population scripts
│   │   │   └── import_infos.py   # Data import utilities
│   │   ├── services/             # Business logic layer
│   │   │   ├── evaluation_service.py      # Evaluation scheduling logic
│   │   │   ├── calendrier_service.py      # Calendar computations
│   │   │   ├── contrat_service.py         # Contract expiration tracking
│   │   │   ├── absence_service.py         # Absence management
│   │   │   ├── matricule_service.py       # Employee ID management
│   │   │   ├── liste_et_grilles_service.py # Grid generation
│   │   │   ├── audit_logger.py            # Basic logging (deprecated)
│   │   │   ├── logger.py                  # Historique table logging
│   │   │   └── log_exporter.py            # Export logs to files
│   │   ├── gui/                  # PyQt5 UI layer
│   │   │   ├── main_qt.py                 # Main application window
│   │   │   ├── ui_theme.py                # Theme system (EmacTheme, EmacDarkTheme)
│   │   │   ├── emac_ui_kit.py            # Reusable UI components
│   │   │   ├── gestion_evaluation.py      # Evaluation management dialog
│   │   │   ├── gestion_personnel.py       # Personnel details & management
│   │   │   ├── gestion_absences.py        # Absence management dialog
│   │   │   ├── manage_operateur.py        # Add/edit employees
│   │   │   ├── liste_et_grilles.py        # Skill matrix grids
│   │   │   ├── creation_modification_poste.py  # Position CRUD
│   │   │   ├── historique.py              # Audit log viewer
│   │   │   ├── planning.py                # Planning/schedule view
│   │   │   └── contract_management.py     # Contract renewal interface
│   │   └── exporters/            # File export layer
│   │       ├── excel_export.py   # Export grids to Excel
│   │       ├── pdf_export.py     # PDF generation with ReportLab
│   │       └── log_export.py     # CSV export of logs
│   ├── database/                 # Database files
│   │   ├── schema/               # Schema definitions
│   │   │   └── bddemac.sql       # Main database schema
│   │   ├── migrations/           # Schema migrations
│   │   │   └── schema_absences_conges.sql
│   │   └── backups/              # SQL backup files
│   ├── tests/                    # Test files
│   │   ├── test_add_operateur.py
│   │   ├── test_advanced.py
│   │   ├── test_database_integrity.py
│   │   ├── test_masquage_operateur.py
│   │   ├── test_matricule_service.py
│   │   └── test_personnel_non_production.py
│   ├── scripts/                  # Utility scripts
│   │   ├── cleanup_test_data.py
│   │   ├── fix_matricule_lowercase.py
│   │   ├── install_absences_module.py
│   │   ├── delete_operators.py
│   │   └── quick_db_query.py
│   ├── logs/                     # Application logs
│   ├── run/                      # Runtime files
│   └── run_emac.vbs             # Windows launcher
├── Deploy/                       # Deployment files
└── CLAUDE.md                     # Claude Code instructions
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

## Critical Implementation Notes

1. **Dual Table Names**: When querying employees, check if code uses `personnel` or `operateurs` table. The schema contains both and they may reference different foreign key relationships.

2. **Historique Logging**: Use `log_hist()` from [logger.py](App/core/services/logger.py) rather than the older `log_action()` from [audit_logger.py](App/core/services/audit_logger.py). The new logger writes to the `historique` database table.

3. **Theme Application**: Always call `EmacTheme.apply(app)` before creating the main window, not after. The QSS stylesheet must be applied to QApplication before widgets are instantiated.

4. **Drawer Menu**: The main window has a lazy-loaded sliding drawer menu. The drawer is created on first access in [main_qt.py](App/core/gui/main_qt.py):206-243, not during `__init__`. Always check `if self.drawer is not None` before accessing it.

5. **Date Calculations**: Evaluation dates often extend 10 years into the future. This is intentional - the system tracks long-term skill maintenance rather than frequent re-certification.

6. **Contract Management**: The contract expiration system in [contrat_service.py](App/core/services/contrat_service.py) calculates days remaining and highlights urgent renewals (< 7 days) with warning indicators.
