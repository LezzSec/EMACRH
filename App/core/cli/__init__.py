# -*- coding: utf-8 -*-
"""
EMAC CLI — point d'entrée des commandes d'administration.

Usage (depuis App/) :
    python -m core.cli migrate --status
    python -m core.cli migrate --apply-all
    python -m core.cli diagnose
    python -m core.cli diagnose --performance
    python -m core.cli diagnose --views

Usage (depuis EMAC/) :
    python -m App migrate --status
    python -m App diagnose
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m core.cli",
        description="EMAC — outils d'administration",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMANDE")
    sub.required = True

    # ---- migrate ----
    p_mig = sub.add_parser("migrate", help="Gestion des migrations de base de données")
    p_mig.add_argument(
        "--status",
        action="store_true",
        help="Afficher le statut des migrations (défaut)",
    )
    p_mig.add_argument(
        "--apply",
        metavar="FICHIER",
        help="Appliquer une migration par nom de fichier",
    )
    p_mig.add_argument(
        "--apply-all",
        action="store_true",
        dest="apply_all",
        help="Appliquer toutes les migrations en attente",
    )
    p_mig.add_argument(
        "--mark-applied-all",
        action="store_true",
        dest="mark_applied_all",
        help="Marquer toutes les migrations comme appliquées SANS les exécuter "
             "(à utiliser sur une base déjà configurée manuellement)",
    )

    # ---- diagnose ----
    p_diag = sub.add_parser("diagnose", help="Diagnostics de l'application")
    p_diag.add_argument(
        "--performance",
        action="store_true",
        help="Vérifier les index de performance",
    )
    p_diag.add_argument(
        "--views",
        action="store_true",
        help="Vérifier les vues attendues",
    )
    p_diag.add_argument(
        "--db",
        action="store_true",
        help="Vérifier la connectivité et le volume des tables",
    )

    args = parser.parse_args()

    if args.command == "migrate":
        from core.cli.commands.migrate import run_migrate
        run_migrate(args)
    elif args.command == "diagnose":
        from core.cli.commands.diagnose import run_diagnose
        run_diagnose(args)
