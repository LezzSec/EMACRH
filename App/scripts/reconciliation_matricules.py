# -*- coding: utf-8 -*-
"""
Reconciliation des matricules pour les INACTIFS EMAC <- hopempl.

Objectif : aligner les matricules des fiches EMAC inactives sur ceux de la base
hopempl (SIRH externe), en combinant correspondance exacte (nom/prenom normalise)
et rapprochement par similarite pour les cas ambigus.

Deux phases :

  1) detect  : interroge les deux bases, ecrit un CSV de propositions a valider
  2) apply   : applique les mises a jour validees directement dans EMAC (avec --dry-run)

Variables d'environnement (fichier .env) :
  EMAC_DB_HOST, EMAC_DB_USER, EMAC_DB_PASSWORD, EMAC_DB_NAME   (MySQL EMAC)
  EMAC_EXT_SS_SERVER, EMAC_EXT_SS_DATABASE                      (SQL Server hopempl)

Exemples :
  cd App
  python scripts/reconciliation_matricules.py detect  propositions.csv
  python scripts/reconciliation_matricules.py apply   propositions.csv --dry-run
  python scripts/reconciliation_matricules.py apply   propositions.csv
"""

import argparse
import csv
import os
import sys
import unicodedata
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.configbd import _load_env_once, DatabaseCursor
from infrastructure.db.sqlserver_config import SqlServerCursor
from infrastructure.db.query_executor import QueryExecutor

# ─── config ───────────────────────────────────────────────────────────────────

# Seuils de similarite (0-100)
SEUIL_AUTO  = 92    # >= : match fort, pre-rempli "OUI" (a confirmer quand meme)
SEUIL_REVUE = 75    # >= : match faible a verifier ; en dessous => AUCUN_MATCH

DELIM = ";"

_PARTICULES = {"DIT", "DE", "DU", "DES", "LA", "LE", "DI", "DA"}

# ─── normalisation / scoring ──────────────────────────────────────────────────

def _sans_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def normaliser(s: str) -> str:
    s = _sans_accents(s or "").upper()
    s = "".join(c if c.isalnum() else " " for c in s)
    return " ".join(s.split())


def _ratio(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def _score_champ(a: str, b: str) -> float:
    na, nb = normaliser(a), normaliser(b)
    seq = _ratio(na, nb)
    ta = set(na.split()) - _PARTICULES
    tb = set(nb.split()) - _PARTICULES
    if ta and tb:
        contenance = len(ta & tb) / min(len(ta), len(tb))
    else:
        contenance = 0.0
    return max(seq, contenance)


def score_similarite(nom_a, prenom_a, nom_b, prenom_b) -> float:
    s_nom    = _score_champ(nom_a, nom_b)
    s_prenom = _score_champ(prenom_a, prenom_b)
    return round((0.55 * s_nom + 0.45 * s_prenom) * 100, 1)

# ─── chargement DB ────────────────────────────────────────────────────────────

def charger_inactifs_emac() -> list[dict]:
    """Charge tous les INACTIFS de la table personnel (MySQL EMAC)."""
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute(
            "SELECT id, matricule, nom, prenom FROM personnel "
            "WHERE statut = 'INACTIF' ORDER BY nom, prenom"
        )
        rows = cur.fetchall()
    print(f"  {len(rows)} inactifs EMAC charges.")
    return rows


def charger_hopempl() -> list[dict]:
    """Charge MATRI, NOM, PRENOM depuis hopempl (tous les enregistrements)."""
    with SqlServerCursor() as cur:
        cur.execute("SELECT MATRI, NOM, PRENOM FROM hopempl")
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
    data = [dict(zip(cols, r)) for r in rows]
    print(f"  {len(data)} entrees hopempl chargees.")
    return data

# ─── phase 1 : detect ────────────────────────────────────────────────────────

def detecter(chemin_sortie: str) -> None:
    print("Chargement EMAC (inactifs)...")
    inactifs = charger_inactifs_emac()

    print("Chargement hopempl (SQL Server)...")
    hopempl = charger_hopempl()

    # index exact : cle = (nom_normalise, prenom_normalise) -> liste d'entrees hopempl
    index_exact: dict[tuple, list[dict]] = {}
    for h in hopempl:
        cle = (normaliser(h.get("NOM", "")), normaliser(h.get("PRENOM", "")))
        index_exact.setdefault(cle, []).append(h)

    propositions = []
    matricules_b_utilises: dict[str, int] = {}  # b_matricule -> emac_id deja propose

    for e in inactifs:
        e_id  = e["id"]
        e_mat = (e.get("matricule") or "").strip()
        e_nom = (e.get("nom") or "").strip()
        e_pre = (e.get("prenom") or "").strip()

        cle = (normaliser(e_nom), normaliser(e_pre))
        matches_exacts = index_exact.get(cle, [])

        b_mat = b_nom = b_pre = ""
        match_type = ""
        score = 0.0

        if matches_exacts:
            # Match exact sur nom + prenom
            candidats = [m for m in matches_exacts if (m.get("MATRI") or "").strip()]
            if len(candidats) == 1:
                b = candidats[0]
                b_mat = b["MATRI"].strip()
                b_nom = (b.get("NOM") or "").strip()
                b_pre = (b.get("PRENOM") or "").strip()
                match_type = "EXACT"
                score = 100.0
            elif len(candidats) > 1:
                # Plusieurs entrees : prendre celle commencant par '0' (employe)
                prod = [m for m in candidats if (m["MATRI"] or "").strip().startswith("0")]
                if len(prod) == 1:
                    b = prod[0]
                    b_mat = b["MATRI"].strip()
                    b_nom = (b.get("NOM") or "").strip()
                    b_pre = (b.get("PRENOM") or "").strip()
                    match_type = "EXACT"
                    score = 100.0
                else:
                    # Ambigu meme apres filtrage
                    b_mat = ", ".join(m["MATRI"].strip() for m in candidats)
                    b_nom = (candidats[0].get("NOM") or "").strip()
                    b_pre = (candidats[0].get("PRENOM") or "").strip()
                    match_type = "AMBIGU"
                    score = 100.0
        else:
            # Pas de match exact : recherche par similarite
            meilleur, meilleur_score = None, -1.0
            for h in hopempl:
                if not (h.get("MATRI") or "").strip():
                    continue
                s = score_similarite(e_nom, e_pre, h.get("NOM", ""), h.get("PRENOM", ""))
                if s > meilleur_score:
                    meilleur, meilleur_score = h, s

            if meilleur and meilleur_score >= SEUIL_REVUE:
                b_mat = (meilleur.get("MATRI") or "").strip()
                b_nom = (meilleur.get("NOM") or "").strip()
                b_pre = (meilleur.get("PRENOM") or "").strip()
                match_type = "FUZZY"
                score = meilleur_score

        # Determination du statut
        if not b_mat or match_type == "":
            statut, valider = "AUCUN_MATCH", ""
        elif match_type == "AMBIGU":
            statut, valider = "AMBIGU", ""
        elif e_mat == b_mat:
            statut, valider = "DEJA_ALIGNE", ""
        elif match_type == "EXACT" or score >= SEUIL_AUTO:
            statut = "AUTO"
            valider = "OUI"
        else:
            statut, valider = "A_VERIFIER", ""

        # Detection de collision (meme matricule B propose pour deux EMAC differents)
        if b_mat and statut in ("AUTO", "A_VERIFIER") and "," not in b_mat:
            if b_mat in matricules_b_utilises:
                statut = f"COLLISION(emac {matricules_b_utilises[b_mat]})"
                valider = ""
            else:
                matricules_b_utilises[b_mat] = e_id

        propositions.append({
            "emac_id":       e_id,
            "emac_matricule": e_mat,
            "emac_nom":      e_nom,
            "emac_prenom":   e_pre,
            "b_matricule":   b_mat,
            "b_nom":         b_nom,
            "b_prenom":      b_pre,
            "match_type":    match_type,
            "score":         score if score > 0 else "",
            "statut":        statut,
            "valider":       valider,
        })

    # Tri : A_VERIFIER + AMBIGU en premier, puis AUTO, puis le reste
    ordre = {"A_VERIFIER": 0, "AMBIGU": 1, "AUTO": 2, "DEJA_ALIGNE": 3, "AUCUN_MATCH": 4}
    propositions.sort(key=lambda p: (ordre.get(p["statut"], 1), -(p["score"] or 0)))

    cols = ["emac_id", "emac_matricule", "emac_nom", "emac_prenom",
            "b_matricule", "b_nom", "b_prenom", "match_type", "score",
            "statut", "valider"]
    with open(chemin_sortie, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=DELIM)
        w.writeheader()
        w.writerows(propositions)

    _afficher_resume(propositions, chemin_sortie)


def _afficher_resume(propositions: list[dict], chemin_sortie: str) -> None:
    from collections import Counter
    c = Counter(p["statut"].split("(")[0] for p in propositions)
    print(f"\n{len(propositions)} inactifs analyses -> {chemin_sortie}")
    for statut in ("A_VERIFIER", "AMBIGU", "AUTO", "COLLISION", "DEJA_ALIGNE", "AUCUN_MATCH"):
        if c.get(statut):
            print(f"  {statut:<14} : {c[statut]}")
    auto = c.get("AUTO", 0)
    print(f"\n>>> Ouvre le CSV, controle chaque ligne (surtout les AUTO et A_VERIFIER),")
    print(f"    mets 'OUI' dans 'valider' pour celles a aligner,")
    print(f"    puis lance : python scripts/reconciliation_matricules.py apply {chemin_sortie}")
    if auto:
        print(f"    ({auto} lignes pre-remplies OUI - a verifier quand meme)")

# ─── phase 2 : apply ─────────────────────────────────────────────────────────

def appliquer(chemin_propositions: str, dry_run: bool = False) -> None:
    with open(chemin_propositions, encoding="utf-8-sig", newline="") as f:
        try:
            delim = csv.Sniffer().sniff(f.read(4096), delimiters=";,\t").delimiter
            f.seek(0)
        except csv.Error:
            f.seek(0)
            delim = DELIM
        propositions = list(csv.DictReader(f, delimiter=delim))

    a_appliquer = [
        p for p in propositions
        if (p.get("valider") or "").strip().upper() == "OUI"
    ]

    if not a_appliquer:
        print("Aucune ligne avec valider=OUI trouvee. Rien a faire.")
        return

    mode = "[DRY-RUN] " if dry_run else ""
    print(f"\n{mode}{len(a_appliquer)} mise(s) a jour prevue(s)...\n")

    vus: dict[str, int] = {}
    updated = errors = skipped = 0

    for p in a_appliquer:
        e_id  = (p.get("emac_id") or "").strip()
        e_mat = (p.get("emac_matricule") or "").strip()
        b_mat = (p.get("b_matricule") or "").strip()
        e_nom = p.get("emac_nom", "")
        e_pre = p.get("emac_prenom", "")

        if not e_id or not b_mat or "," in b_mat:
            print(f"  IGNORE  {e_nom} {e_pre} : id ou matricule invalide ({b_mat!r})")
            skipped += 1
            continue

        if e_mat == b_mat:
            print(f"  SKIP    {e_nom:<25} {e_pre:<20} deja aligne ({b_mat})")
            skipped += 1
            continue

        if b_mat in vus:
            print(f"  SKIP    {e_nom:<25} {e_pre:<20} collision CSV : {b_mat} deja attribue a emac {vus[b_mat]}")
            skipped += 1
            continue
        vus[b_mat] = int(e_id)

        label = f"{e_nom:<25} {e_pre:<20}  {e_mat or '(vide)':<15} -> {b_mat}"

        # Verifier que le matricule cible n'est pas deja pris par un autre employe
        proprietaire = QueryExecutor.fetch_one(
            "SELECT id, nom, prenom, statut FROM personnel WHERE matricule = %s AND id != %s",
            (b_mat, int(e_id))
        )
        if proprietaire:
            pid, pnom, ppre, pstat = proprietaire
            print(f"  SKIP    {label}  (deja pris par id={pid} {pnom} {ppre} [{pstat}])")
            skipped += 1
            continue

        if dry_run:
            print(f"  {mode}{label}")
            updated += 1
            continue

        try:
            QueryExecutor.execute_write(
                "UPDATE personnel SET matricule = %s WHERE id = %s AND statut = 'INACTIF'",
                (b_mat, int(e_id)),
                return_lastrowid=False
            )
            print(f"  OK      {label}")
            updated += 1
        except Exception as e:
            print(f"  ERR     {label}  -> {e}")
            errors += 1

    print(f"\n{mode}{updated} mis a jour{' (simulation)' if dry_run else ''}."
          + (f"  {skipped} ignores." if skipped else "")
          + (f"  {errors} erreurs." if errors else ""))

    if dry_run:
        print("\nRelancer sans --dry-run pour appliquer les modifications.")

# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconciliation matricules INACTIFS EMAC <- hopempl"
    )
    sub = ap.add_subparsers(dest="mode", required=True)

    d = sub.add_parser("detect", help="Analyse les deux bases et produit un CSV a valider")
    d.add_argument("sortie_csv", help="Fichier CSV de sortie (ex: propositions.csv)")

    a = sub.add_parser("apply", help="Applique les mises a jour validees dans EMAC")
    a.add_argument("propositions_csv", help="CSV valide produit par 'detect'")
    a.add_argument("--dry-run", action="store_true",
                   help="Simule sans modifier la base")

    args = ap.parse_args()
    _load_env_once()

    try:
        if args.mode == "detect":
            detecter(args.sortie_csv)
        elif args.mode == "apply":
            appliquer(args.propositions_csv, dry_run=args.dry_run)
    except Exception as e:
        print(f"\nERREUR : {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
