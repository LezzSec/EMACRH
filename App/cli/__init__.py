# -*- coding: utf-8 -*-
"""
EMAC CLI — point d'entrée des commandes d'administration.

Usage (depuis App/) :
    python -m cli migrate --status
    python -m cli migrate --apply-all
    python -m cli diagnose
    python -m cli diagnose --performance
    python -m cli diagnose --views

Usage (depuis EMAC/) :
    python -m App migrate --status
    python -m App diagnose
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m cli",
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

    # ---- export-paie ----
    p_exp = sub.add_parser("export-paie", help="Export CSV personnel / polyvalence (intégration paie, ERP)")
    p_exp.add_argument(
        "--output", "-o",
        metavar="FICHIER",
        help="Chemin du fichier CSV de sortie (défaut : exports/paie_<format>_<horodatage>.csv)",
    )
    p_exp.add_argument(
        "--format", "-f",
        choices=["paie", "polyvalence", "complet"],
        default="paie",
        help="Format de sortie : paie (défaut), polyvalence, complet",
    )
    p_exp.add_argument(
        "--statut",
        choices=["ACTIF", "INACTIF"],
        default="ACTIF",
        help="Filtrer par statut personnel (défaut : ACTIF)",
    )

    args = parser.parse_args()

    if args.command == "migrate":
        from cli.commands.migrate import run_migrate
        run_migrate(args)
    elif args.command == "diagnose":
        from cli.commands.diagnose import run_diagnose
        run_diagnose(args)
    elif args.command == "export-paie":
        from cli.commands.export_paie import run_export_paie
        run_export_paie(args)
