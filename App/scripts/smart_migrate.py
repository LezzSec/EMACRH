# -*- coding: utf-8 -*-
"""
smart_migrate.py — Applique les migrations en comparant d'abord l'état réel de la base.

Pour chaque migration non encore enregistrée dans schema_migrations :
  1. Parse le SQL pour détecter les objets créés/modifiés (tables, colonnes, index)
  2. Vérifie leur présence dans information_schema
  3. Tout présent  → marque comme appliquée SANS exécuter
  4. Quelque chose manque → applique normalement
  5. Rien de vérifiable (INSERT/UPDATE/etc.) → applique (idempotent par construction)

Usage :
    cd App
    python scripts/smart_migrate.py
    python scripts/smart_migrate.py --dry-run
"""

from __future__ import annotations

import re
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

MIGRATIONS_DIR = Path(__file__).parents[1] / "database" / "migrations"
_NUMBERED_RE = re.compile(r"^\d{3}_.*\.sql$")

_CREATE_TRACKING_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    filename   VARCHAR(255) NOT NULL UNIQUE,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

# ---------------------------------------------------------------------------
# Patterns de détection dans le SQL
# ---------------------------------------------------------------------------

_RE_CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?",
    re.IGNORECASE,
)
_RE_ADD_COLUMN = re.compile(
    r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+ADD\s+COLUMN\s+[`\"]?(\w+)[`\"]?",
    re.IGNORECASE,
)
_RE_CREATE_INDEX = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?\s+ON\s+[`\"]?(\w+)[`\"]?",
    re.IGNORECASE,
)
_RE_ADD_KEY = re.compile(
    r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+ADD\s+(?:UNIQUE\s+)?(?:KEY|INDEX)\s+[`\"]?(\w+)[`\"]?",
    re.IGNORECASE,
)
_RE_DROP_TABLE = re.compile(
    r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?",
    re.IGNORECASE,
)
_RE_DROP_COLUMN = re.compile(
    r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+DROP\s+(?:COLUMN\s+)?[`\"]?(\w+)[`\"]?",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Helpers SQL
# ---------------------------------------------------------------------------

def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", "", sql)
    return sql


def _check_migration(cursor, sql: str) -> tuple[str, list[tuple[str, bool]]]:
    """
    Analyse le SQL et vérifie chaque objet dans information_schema.

    Retourne (status, checks) :
      - status : 'all_present' | 'absent' | 'unverifiable'
      - checks : liste de (description, existe_en_base)
    """
    clean = _strip_comments(sql)
    checks: list[tuple[str, bool]] = []

    # CREATE TABLE
    for m in _RE_CREATE_TABLE.finditer(clean):
        table = m.group(1)
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
            (table,),
        )
        exists = cursor.fetchone()[0] > 0
        checks.append((f"TABLE `{table}`", exists))

    # ALTER TABLE … ADD COLUMN col
    for m in _RE_ADD_COLUMN.finditer(clean):
        table, col = m.group(1), m.group(2)
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (table, col),
        )
        exists = cursor.fetchone()[0] > 0
        checks.append((f"COLUMN `{table}`.`{col}`", exists))

    # CREATE [UNIQUE] INDEX idx ON table
    for m in _RE_CREATE_INDEX.finditer(clean):
        idx, table = m.group(1), m.group(2)
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND INDEX_NAME = %s",
            (table, idx),
        )
        exists = cursor.fetchone()[0] > 0
        checks.append((f"INDEX `{idx}` ON `{table}`", exists))

    # ALTER TABLE … ADD KEY/INDEX idx
    for m in _RE_ADD_KEY.finditer(clean):
        table, idx = m.group(1), m.group(2)
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND INDEX_NAME = %s",
            (table, idx),
        )
        exists = cursor.fetchone()[0] > 0
        checks.append((f"KEY `{idx}` ON `{table}`", exists))

    # DROP TABLE → déjà appliqué si la table n'existe plus
    for m in _RE_DROP_TABLE.finditer(clean):
        table = m.group(1)
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
            (table,),
        )
        still_exists = cursor.fetchone()[0] > 0
        checks.append((f"DROP TABLE `{table}`", not still_exists))

    # DROP COLUMN → déjà appliqué si la colonne n'existe plus
    for m in _RE_DROP_COLUMN.finditer(clean):
        table, col = m.group(1), m.group(2)
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (table, col),
        )
        still_exists = cursor.fetchone()[0] > 0
        checks.append((f"DROP COLUMN `{table}`.`{col}`", not still_exists))

    if not checks:
        return "unverifiable", []

    all_present = all(exists for _, exists in checks)
    return ("all_present" if all_present else "absent"), checks


def _execute_sql(cursor, sql: str, path: Path) -> None:
    clean = _strip_comments(sql)
    for stmt in (s.strip() for s in clean.split(";") if s.strip()):
        if stmt.lower().startswith("use "):
            continue
        try:
            cursor.execute(stmt)
        except Exception as exc:
            msg = str(exc).lower()
            ignorable = (
                "already exists",
                "duplicate column",
                "duplicate entry",
                "duplicate key",
                "can't drop",
            )
            if any(k in msg for k in ignorable):
                continue
            raise RuntimeError(
                f"Erreur dans {path.name}\n  SQL : {stmt[:120]}\n  Cause : {exc}"
            ) from exc

# ---------------------------------------------------------------------------
# Gestion schema_migrations
# ---------------------------------------------------------------------------

def _ensure_tracking(cursor, conn) -> None:
    cursor.execute(_CREATE_TRACKING_SQL)
    conn.commit()


def _get_applied(cursor) -> set[str]:
    cursor.execute("SELECT filename FROM schema_migrations")
    return {r[0] for r in cursor.fetchall()}


def _mark_applied(cursor, filename: str) -> None:
    cursor.execute(
        "INSERT IGNORE INTO schema_migrations (filename) VALUES (%s)", (filename,)
    )


def _pending_files(applied: set[str]) -> list[Path]:
    return [
        f for f in sorted(MIGRATIONS_DIR.glob("*.sql"))
        if _NUMBERED_RE.match(f.name) and f.name not in applied
    ]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(dry_run: bool = False) -> None:
    try:
        from infrastructure.db.configbd import get_connection
        conn = get_connection()
    except Exception as exc:
        print(f"\n  ERREUR connexion : {exc}")
        print("  Verifiez .env et que MariaDB est demarre.")
        sys.exit(1)

    try:
        cur = conn.cursor()
        _ensure_tracking(cur, conn)

        applied = _get_applied(cur)
        pending = _pending_files(applied)

        if not pending:
            print("  Base de donnees a jour. Aucune migration en attente.")
            return

        print(f"  {len(pending)} migration(s) a analyser...\n")

        to_apply: list[Path] = []
        to_skip: list[Path] = []

        for path in pending:
            sql = path.read_text(encoding="utf-8")
            status, checks = _check_migration(cur, sql)

            print(f"  {path.name}")

            if status == "all_present":
                for desc, _ in checks:
                    print(f"    [OK] {desc}  (deja present en base)")
                print(f"    --> Sera marquee appliquee sans execution\n")
                to_skip.append(path)

            elif status == "absent":
                for desc, exists in checks:
                    marker = "[OK]" if exists else "[ ]"
                    print(f"    {marker} {desc}")
                print(f"    --> A appliquer\n")
                to_apply.append(path)

            else:  # unverifiable
                print(f"    [??] Aucun objet verifiable detecte (INSERT/UPDATE/etc.)")
                print(f"    --> A appliquer (idempotent par construction)\n")
                to_apply.append(path)

        # Résumé
        print("-" * 60)
        if to_skip:
            print(f"  {len(to_skip)} migration(s) deja presente(s) en base → sans execution")
        if to_apply:
            print(f"  {len(to_apply)} migration(s) a appliquer")
        else:
            print(f"  Aucune migration a executer.")
        print()

        if dry_run:
            print("  [dry-run] Aucune modification effectuee.")
            return

        # Marquer les migrations déjà présentes
        if to_skip:
            for path in to_skip:
                _mark_applied(cur, path.name)
            conn.commit()
            print(f"  {len(to_skip)} migration(s) marquee(s) dans schema_migrations.")

        if not to_apply:
            return

        # Confirmation avant d'appliquer
        confirm = input("  Appliquer les migrations manquantes ? (O/N) : ").strip().upper()
        if confirm != "O":
            print("  Annule.")
            return

        print()
        errors = 0
        for path in to_apply:
            print(f"  {path.name}... ", end="", flush=True)
            sql = path.read_text(encoding="utf-8")
            try:
                _execute_sql(cur, sql, path)
                _mark_applied(cur, path.name)
                conn.commit()
                print("OK")
            except Exception as exc:
                conn.rollback()
                print("ERREUR")
                print(f"    {exc}")
                errors += 1

        print()
        if errors:
            print(f"  {errors} erreur(s). Consultez logs/emac.log.")
            sys.exit(1)
        else:
            print(f"  Toutes les migrations appliquees avec succes.")

    finally:
        conn.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
