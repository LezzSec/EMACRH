# -*- coding: utf-8 -*-
"""
Import des dates d'entrée depuis un fichier Excel vers personnel_infos.

Le script détecte automatiquement les colonnes, affiche un aperçu des
correspondances, puis demande confirmation avant d'écrire en base.

Usage (depuis le dossier App/) :
    py -m scripts.import_dates_entree_excel chemin/vers/fichier.xlsx

Options :
    --sheet NOM       Nom de l'onglet Excel (défaut : premier onglet)
    --simulation      Affiche les correspondances sans écrire en base
    --tous            Importe aussi les dates déjà renseignées (écrase)

Colonnes reconnues automatiquement (insensible à la casse) :
    Identification  : matricule, nom, prenom / prénom
    Date            : date_entree, date entrée, date d'entrée, entrée, entry date, ...
"""

import sys
import os
import argparse
from datetime import datetime, date

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pandas as pd
except ImportError:
    print("ERREUR : pandas est requis. Installez-le avec : pip install pandas openpyxl")
    sys.exit(1)

from infrastructure.db.query_executor import QueryExecutor
from domain.repositories.personnel_repo import PersonnelRepository
from infrastructure.logging.optimized_db_logger import log_hist


# ---------------------------------------------------------------------------
# Aliases de colonnes reconnus (minuscules)
# ---------------------------------------------------------------------------
_ALIAS_MATRICULE = {'matricule', 'mat', 'matr', 'num', 'numero', 'numéro'}
_ALIAS_NOM       = {'nom', 'name', 'last_name', 'lastname'}
_ALIAS_PRENOM    = {'prenom', 'prénom', 'first_name', 'firstname'}
_ALIAS_DATE      = {
    'date_entree', 'date entrée', "date d'entrée", 'date_entree_entreprise',
    'entree', 'entrée', 'entry_date', 'entry date', 'date embauche',
    'date_embauche', 'embauche',
}


def _find_col(columns: list[str], aliases: set) -> str | None:
    """Retourne le nom de colonne correspondant à un alias, ou None."""
    for col in columns:
        if col.strip().lower() in aliases:
            return col
    return None


def _parse_date(val) -> date | None:
    """Convertit une valeur Excel (date, str, int) en date Python."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return None


def charger_excel(path: str, sheet: str | None) -> pd.DataFrame:
    try:
        df = pd.read_excel(path, sheet_name=sheet or 0, dtype=str)
    except FileNotFoundError:
        print(f"ERREUR : Fichier introuvable : {path}")
        sys.exit(1)
    except Exception as e:
        print(f"ERREUR lecture Excel : {e}")
        sys.exit(1)
    df.columns = [str(c) for c in df.columns]
    return df


def charger_personnel_db() -> dict:
    """Retourne un dict indexé par matricule ET par (nom_upper, prenom_upper)."""
    rows = QueryExecutor.fetch_all(
        """
        SELECT p.id, p.nom, p.prenom, p.matricule, pi.date_entree
        FROM personnel p
        LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
        WHERE p.statut = 'ACTIF'
        """,
        dictionary=True,
    )
    par_matricule = {}
    par_nom_prenom = {}
    for r in rows:
        if r['matricule']:
            par_matricule[r['matricule'].strip().upper()] = r
        cle = (r['nom'].strip().upper(), r['prenom'].strip().upper())
        par_nom_prenom[cle] = r
    return par_matricule, par_nom_prenom


def apparier(df: pd.DataFrame, par_matricule: dict, par_nom_prenom: dict) -> list[dict]:
    """
    Associe chaque ligne Excel à un enregistrement DB.
    Retourne une liste de résultats avec statut pour affichage.
    """
    cols = df.columns.tolist()
    col_mat    = _find_col(cols, _ALIAS_MATRICULE)
    col_nom    = _find_col(cols, _ALIAS_NOM)
    col_prenom = _find_col(cols, _ALIAS_PRENOM)
    col_date   = _find_col(cols, _ALIAS_DATE)

    if col_date is None:
        print("\nERREUR : Colonne de date introuvable.")
        print(f"Colonnes détectées : {cols}")
        print(f"Noms reconnus : {sorted(_ALIAS_DATE)}")
        sys.exit(1)

    if col_mat is None and (col_nom is None or col_prenom is None):
        print("\nERREUR : Impossible d'identifier le personnel.")
        print("Il faut au moins : 'matricule'  OU  'nom' + 'prenom'")
        print(f"Colonnes détectées : {cols}")
        sys.exit(1)

    print(f"\nColonnes utilisées :")
    print(f"  Identification : matricule={col_mat!r}  nom={col_nom!r}  prenom={col_prenom!r}")
    print(f"  Date           : {col_date!r}")

    resultats = []
    for _, row in df.iterrows():
        personnel = None
        methode   = None

        # 1. Recherche par matricule
        if col_mat and pd.notna(row.get(col_mat, None)):
            mat = str(row[col_mat]).strip().upper()
            if mat in par_matricule:
                personnel = par_matricule[mat]
                methode   = f"matricule={mat}"

        # 2. Recherche par nom + prénom si pas trouvé
        if personnel is None and col_nom and col_prenom:
            nom    = str(row.get(col_nom, '')).strip().upper()
            prenom = str(row.get(col_prenom, '')).strip().upper()
            if nom and prenom:
                cle = (nom, prenom)
                if cle in par_nom_prenom:
                    personnel = par_nom_prenom[cle]
                    methode   = f"{nom} {prenom}"

        date_val = _parse_date(row.get(col_date))

        resultats.append({
            'ligne':      _ + 2,  # numéro ligne Excel (1-indexé + en-tête)
            'personnel':  personnel,
            'methode':    methode,
            'date':       date_val,
            'raw_date':   str(row.get(col_date, '')),
        })

    return resultats


def afficher_apercu(resultats: list[dict]) -> tuple[int, int, int]:
    """Affiche le tableau de correspondances. Retourne (ok, sans_date, non_trouves)."""
    ok = sans_date = non_trouves = date_invalide = 0

    print(f"\n{'Ligne':<6} {'Identifiant':<25} {'Date Excel':<14} {'DB actuelle':<14} {'Statut'}")
    print("-" * 85)

    for r in resultats:
        ligne     = r['ligne']
        methode   = r['methode'] or '?'
        date_val  = r['date']
        raw       = r['raw_date']
        p         = r['personnel']

        if p is None:
            statut = "INTROUVABLE en base"
            non_trouves += 1
        elif date_val is None:
            statut = "date manquante/invalide"
            date_invalide += 1
        else:
            date_actuelle = p['date_entree']
            if date_actuelle and date_actuelle != date(2000, 1, 1):
                statut = f"ecrase {date_actuelle.strftime('%d/%m/%Y')}"
            else:
                statut = "OK"
            ok += 1

        date_str = date_val.strftime("%d/%m/%Y") if date_val else f"[{raw}]"
        db_str   = p['date_entree'].strftime("%d/%m/%Y") if (p and p['date_entree']) else "-"
        print(f"{ligne:<6} {methode:<25} {date_str:<14} {db_str:<14} {statut}")

    print(f"\nRésumé : {ok} à importer | {date_invalide} date(s) invalide(s) | {non_trouves} introuvable(s)")
    return ok, date_invalide, non_trouves


def main():
    parser = argparse.ArgumentParser(description="Import dates d'entrée depuis Excel")
    parser.add_argument('fichier', help="Chemin vers le fichier Excel (.xlsx/.xls)")
    parser.add_argument('--sheet', default=None, help="Nom de l'onglet (défaut : premier)")
    parser.add_argument('--simulation', action='store_true',
                        help="Affiche les correspondances sans écrire en base")
    parser.add_argument('--tous', action='store_true',
                        help="Importe aussi les dates déjà renseignées (écrase)")
    args = parser.parse_args()

    print(f"\nLecture du fichier : {args.fichier}")
    df = charger_excel(args.fichier, args.sheet)
    print(f"{len(df)} ligne(s) trouvée(s) dans l'onglet.")

    par_matricule, par_nom_prenom = charger_personnel_db()
    resultats = apparier(df, par_matricule, par_nom_prenom)
    ok, date_invalide, non_trouves = afficher_apercu(resultats)

    if args.simulation:
        print("\n[SIMULATION] Aucune modification effectuée.")
        return

    if ok == 0:
        print("\nAucune ligne à importer. Fin du script.")
        return

    print()
    try:
        confirm = input(f"Confirmer l'import de {ok} date(s) en base ? (o/n) : ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nAnnulé.")
        return

    if confirm != 'o':
        print("Import annulé.")
        return

    # --- Écriture en base ---
    traites = erreurs = ignores = 0
    for r in resultats:
        p        = r['personnel']
        date_val = r['date']

        if p is None or date_val is None:
            continue

        date_actuelle = p['date_entree']
        if not args.tous and date_actuelle and date_actuelle != date(2000, 1, 1):
            ignores += 1
            continue

        try:
            date_sql = date_val.strftime("%Y-%m-%d")
            PersonnelRepository.save_date_entree(p['id'], date_sql)
            log_hist(
                "IMPORT_DATE_ENTREE_EXCEL",
                f"Date d'entrée importée depuis Excel : {date_val.strftime('%d/%m/%Y')}",
                p['id'],
                None,
            )
            traites += 1
        except Exception as e:
            print(f"  ERREUR {p['nom']} {p['prenom']} : {e}")
            erreurs += 1

    print(f"\n{'='*60}")
    print(f"  Importé : {traites}  |  Ignoré (déjà renseigné) : {ignores}  |  Erreur : {erreurs}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
