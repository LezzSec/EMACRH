# -*- coding: utf-8 -*-
"""
Commande migrate — gestion des migrations SQL.

Les migrations sont les fichiers .sql de App/database/migrations/.
Le suivi des migrations appliquées est stocké dans la table `schema_migrations`.

Numéros dupliqués (001_, 002_, 003_) : le tracking se fait par nom de fichier
complet, pas par numéro, pour éviter les conflits.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

from core.utils.logging_config import get_logger

logger = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).parents[3] / "database" / "migrations"

_NUMBERED_RE = re.compile(r"^\d{3}_.*\.sql$")

_CREATE_TRACKING_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    filename    VARCHAR(255) NOT NULL UNIQUE,
    applied_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def _ensure_tracking_table() -> None:
    from core.db.configbd import DatabaseConnection
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute(_CREATE_TRACKING_TABLE)


def _applied_migrations() -> set[str]:
    from core.db.query_executor import QueryExecutor
    rows = QueryExecutor.fetch_all(
        "SELECT filename FROM schema_migrations",
        dictionary=True,
    )
    return {r["filename"] for r in rows}


def _numbered_sql_files() -> list[Path]:
    """Retourne les fichiers .sql numérotés (NNN_*.sql) triés par nom."""
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted(
        f for f in MIGRATIONS_DIR.glob("*.sql")
        if _NUMBERED_RE.match(f.name)
    )


def _execute_sql_file(path: Path) -> None:
    """Exécute un fichier SQL (DDL multi-statements) et enregistre la migration."""
    from core.db.configbd import get_connection

    sql = path.read_text(encoding="utf-8")

    # Supprimer les commentaires de ligne avant le split
    lines = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped.startswith("--"):
            lines.append(line)
    sql_clean = "\n".join(lines)

    # Découper sur les ; en fin d'instruction (heuristique fiable pour DDL)
    statements = [s.strip() for s in sql_clean.split(";") if s.strip()]

    conn = get_connection()
    try:
        cur = conn.cursor()
        for stmt in statements:
            try:
                cur.execute(stmt)
            except Exception as exc:
                msg = str(exc).lower()
                # Ignorer les erreurs "déjà existant" pour l'idempotence
                if any(k in msg for k in ("already exists", "duplicate entry", "can't drop")):
                    continue
                raise

        cur.execute(
            "INSERT INTO schema_migrations (filename) VALUES (%s)",
            (path.name,),
        )
        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Sous-commandes
# ---------------------------------------------------------------------------

def _cmd_status() -> None:
    _ensure_tracking_table()
    files = _numbered_sql_files()
    applied = _applied_migrations()

    if not files:
        print(f"Aucun fichier de migration trouvé dans :\n  {MIGRATIONS_DIR}")
        return

    pending_count = sum(1 for f in files if f.name not in applied)

    print(f"\nMigrations — {len(files)} fichiers, {len(applied)} appliquées, {pending_count} en attente\n")
    for f in files:
        marker = "[OK]" if f.name in applied else "[ ] "
        print(f"  {marker}  {f.name}")

    if pending_count:
        print(f"\n  {pending_count} migration(s) en attente. Lancez --apply-all pour les appliquer.")
    else:
        print("\n  Base de données à jour.")


def _cmd_apply_all() -> None:
    _ensure_tracking_table()
    files = _numbered_sql_files()
    applied = _applied_migrations()
    pending = [f for f in files if f.name not in applied]

    if not pending:
        print("Aucune migration en attente.")
        return

    print(f"\n{len(pending)} migration(s) à appliquer...\n")
    errors = 0
    for f in pending:
        print(f"  {f.name}... ", end="", flush=True)
        try:
            _execute_sql_file(f)
            print("OK")
        except Exception as exc:
            print(f"ERREUR")
            print(f"    {exc}")
            logger.exception(f"Erreur migration {f.name}: {exc}")
            errors += 1

    print()
    if errors:
        print(f"  {errors} erreur(s). Vérifiez les logs pour le détail.")
        sys.exit(1)
    else:
        print(f"  Toutes les migrations appliquées avec succès.")


def _cmd_mark_applied_all() -> None:
    """
    Marque toutes les migrations comme appliquées SANS les exécuter.

    À utiliser une seule fois sur une base déjà configurée manuellement,
    pour initialiser le suivi sans risquer de ré-exécuter des migrations
    qui ont déjà été appliquées.
    """
    _ensure_tracking_table()
    files = _numbered_sql_files()
    already = _applied_migrations()
    to_mark = [f for f in files if f.name not in already]

    if not to_mark:
        print("Toutes les migrations sont déjà enregistrées.")
        return

    from core.db.configbd import get_connection
    conn = get_connection()
    try:
        cur = conn.cursor()
        for f in to_mark:
            cur.execute(
                "INSERT IGNORE INTO schema_migrations (filename) VALUES (%s)",
                (f.name,),
            )
            print(f"  marquée  {f.name}")
        conn.commit()
        cur.close()
        print(f"\n  {len(to_mark)} migration(s) enregistrée(s). "
              "Les prochaines migrations seront appliquées normalement.")
    except Exception as exc:
        conn.rollback()
        print(f"Erreur : {exc}")
        logger.exception(f"_cmd_mark_applied_all: {exc}")
        sys.exit(1)
    finally:
        conn.close()


def _cmd_apply_one(filename: str) -> None:
    _ensure_tracking_table()

    # Tolérer le nom avec ou sans chemin
    target = MIGRATIONS_DIR / Path(filename).name
    if not target.exists():
        print(f"Erreur : '{filename}' introuvable dans {MIGRATIONS_DIR}")
        sys.exit(1)

    applied = _applied_migrations()
    if target.name in applied:
        print(f"Migration '{target.name}' déjà appliquée.")
        return

    print(f"Application de {target.name}... ", end="", flush=True)
    try:
        _execute_sql_file(target)
        print("OK")
    except Exception as exc:
        print(f"ERREUR\n  {exc}")
        logger.exception(f"Erreur migration {target.name}: {exc}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def run_migrate(args) -> None:
    if args.apply_all:
        _cmd_apply_all()
    elif getattr(args, "mark_applied_all", False):
        _cmd_mark_applied_all()
    elif args.apply:
        _cmd_apply_one(args.apply)
    else:
        # --status ou pas d'argument → afficher le statut
        _cmd_status()
