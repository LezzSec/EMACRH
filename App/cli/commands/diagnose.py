# -*- coding: utf-8 -*-
"""
Commande diagnose — diagnostics de l'application EMAC.

Sous-vérifications disponibles :
  --db            Connectivité + volume des tables principales
  --performance   Index de performance manquants
  --views         Vues attendues absentes de la DB
  (sans argument) Tout
"""

from __future__ import annotations

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Index critiques attendus : (table, colonne(s), nom_index)
# ---------------------------------------------------------------------------

_CRITICAL_INDEXES = [
    ("personnel",   "statut",               "idx_personnel_statut"),
    ("personnel",   "nom",                  "idx_personnel_nom"),
    ("polyvalence", "prochaine_evaluation",  "idx_poly_prochaine_eval"),
    ("polyvalence", "operateur_id",          "idx_poly_operateur"),
    ("polyvalence", "poste_id",              "idx_poly_poste"),
    ("contrat",     "personnel_id",          "idx_contrat_personnel"),
    ("contrat",     "date_fin",              "idx_contrat_date_fin"),
    ("demande_absence", "operateur_id",      "idx_absence_operateur"),
    ("historique",  "date_action",           "idx_hist_date"),
]

# ---------------------------------------------------------------------------
# Vues attendues
# ---------------------------------------------------------------------------

_EXPECTED_VIEWS = [
    "v_alertes_medicales",
    "v_alertes_entretiens",
    "v_documents_complet",
    "v_contrats_actifs",
    "v_evaluations_retard",
    "v_personnel_actif",
]

# ---------------------------------------------------------------------------
# Tables principales à surveiller
# ---------------------------------------------------------------------------

_MAIN_TABLES = [
    "personnel", "polyvalence", "postes", "atelier",
    "contrat", "formation", "demande_absence",
    "historique", "utilisateurs",
]


# ---------------------------------------------------------------------------
# Vérifications
# ---------------------------------------------------------------------------

def _section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def check_db() -> int:
    """Connectivité + volume des tables. Retourne le nombre d'anomalies."""
    _section("Connectivité et volume")
    errors = 0

    try:
        from infrastructure.db.query_executor import QueryExecutor

        row = QueryExecutor.fetch_one("SELECT VERSION() AS v", dictionary=True)
        print(f"  MySQL : {row['v']}")

        for table in _MAIN_TABLES:
            try:
                count = QueryExecutor.count(table)
                print(f"  {table:<30} {count:>6} lignes")
            except Exception as exc:
                print(f"  {table:<30} ERREUR : {exc}")
                errors += 1

    except Exception as exc:
        print(f"  Connexion impossible : {exc}")
        errors += 1

    return errors


def check_performance() -> int:
    """Vérifie les index critiques. Retourne le nombre d'index manquants."""
    _section("Index de performance")
    errors = 0

    try:
        from infrastructure.db.query_executor import QueryExecutor

        # Récupérer tous les index existants en une seule requête
        rows = QueryExecutor.fetch_all(
            """
            SELECT TABLE_NAME, INDEX_NAME
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
            """,
            dictionary=True,
        )
        existing = {(r["TABLE_NAME"], r["INDEX_NAME"]) for r in rows}

        for table, column, idx_name in _CRITICAL_INDEXES:
            if (table, idx_name) in existing:
                print(f"  [OK]  {table}.{column} ({idx_name})")
            else:
                print(f"  [--]  {table}.{column} ({idx_name})  — MANQUANT")
                errors += 1

        if errors == 0:
            print("\n  Tous les index critiques sont présents.")
        else:
            print(
                f"\n  {errors} index manquant(s). "
                "Appliquez : python scripts/apply_performance_indexes.py"
            )

    except Exception as exc:
        print(f"  Erreur lors de la vérification des index : {exc}")
        logger.exception(f"check_performance: {exc}")
        errors += 1

    return errors


def check_views() -> int:
    """Vérifie les vues attendues. Retourne le nombre de vues manquantes."""
    _section("Vues de base de données")
    errors = 0

    try:
        from infrastructure.db.query_executor import QueryExecutor

        rows = QueryExecutor.fetch_all(
            """
            SELECT TABLE_NAME
            FROM information_schema.VIEWS
            WHERE TABLE_SCHEMA = DATABASE()
            """,
            dictionary=True,
        )
        existing_views = {r["TABLE_NAME"] for r in rows}

        for view in _EXPECTED_VIEWS:
            if view in existing_views:
                print(f"  [OK]  {view}")
            else:
                print(f"  [--]  {view}  — MANQUANTE")
                errors += 1

        if errors == 0:
            print("\n  Toutes les vues attendues sont présentes.")
        else:
            print(
                f"\n  {errors} vue(s) manquante(s). "
                "Lancez : python -m cli migrate --apply create_all_missing_views.sql"
            )

    except Exception as exc:
        print(f"  Erreur lors de la vérification des vues : {exc}")
        logger.exception(f"check_views: {exc}")
        errors += 1

    return errors


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def run_diagnose(args) -> None:
    run_all = not any([args.db, args.performance, args.views])

    total_errors = 0

    print("\nDiagnostic EMAC")

    if run_all or args.db:
        total_errors += check_db()

    if run_all or args.performance:
        total_errors += check_performance()

    if run_all or args.views:
        total_errors += check_views()

    print(f"\n{'─' * 50}")
    if total_errors == 0:
        print("  Résultat : OK — aucune anomalie détectée.")
    else:
        print(f"  Résultat : {total_errors} anomalie(s) détectée(s).")
    print()
