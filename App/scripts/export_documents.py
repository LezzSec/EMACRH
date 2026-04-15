# -*- coding: utf-8 -*-
"""
Export des documents BLOB vers le systeme de fichiers.

Cree la structure :
  <racine_projet>/export/documents/
    {matricule} - {NOM} {Prenom}/
      {Categorie}/
        {nom_fichier}

Usage (depuis le dossier App/) :
    py -m scripts.export_documents              # tous les employes
    py -m scripts.export_documents --id 448    # un seul employe
    py -m scripts.export_documents --mat M000115
"""

import sys
import os
import re
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.db.query_executor import QueryExecutor

# Dossier racine de l'export (EMAC/export/documents/)
EXPORT_ROOT = Path(__file__).resolve().parents[2] / "export" / "documents"


# ──────────────────────────────────────────────────────────────────────────────
# Utilitaires
# ──────────────────────────────────────────────────────────────────────────────

def _safe_name(name: str) -> str:
    """Supprime les caracteres interdits dans les noms de fichiers/dossiers Windows."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def _dossier_employe(matricule: str, nom: str, prenom: str) -> Path:
    """Retourne le chemin du dossier employe, en le creant si necessaire."""
    nom_dossier = _safe_name(f"{matricule} - {nom.upper()} {prenom}")
    path = EXPORT_ROOT / nom_dossier
    path.mkdir(parents=True, exist_ok=True)
    return path


def _dossier_categorie(dossier_employe: Path, categorie: str) -> Path:
    """Retourne le chemin du sous-dossier categorie, en le creant si necessaire."""
    path = dossier_employe / _safe_name(categorie)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _nom_fichier_unique(dossier: Path, nom: str) -> Path:
    """
    Retourne un chemin sans collision : si le fichier existe deja,
    ajoute un suffixe numerique (_2, _3...).
    """
    target = dossier / _safe_name(nom)
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    i = 2
    while True:
        candidate = dossier / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def _extraire_blob(doc_id: int) -> bytes | None:
    """Recupere le contenu BLOB d'un document depuis la BDD."""
    row = QueryExecutor.fetch_one(
        "SELECT contenu_fichier, stockage_type, chemin_fichier "
        "FROM documents WHERE id = %s",
        (doc_id,), dictionary=True
    )
    if not row:
        return None
    if row['stockage_type'] == 'BLOB' and row['contenu_fichier']:
        return bytes(row['contenu_fichier'])
    # Legacy filesystem
    if row['chemin_fichier']:
        p = Path(row['chemin_fichier'])
        if p.exists():
            return p.read_bytes()
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Export
# ──────────────────────────────────────────────────────────────────────────────

def exporter_employe(personnel_id: int) -> dict:
    """
    Exporte tous les documents d'un employe.
    Retourne un dict de stats : {ok, skip, erreur, dossier}.
    """
    # Infos employe
    employe = QueryExecutor.fetch_one(
        "SELECT id, matricule, nom, prenom FROM personnel WHERE id = %s",
        (personnel_id,), dictionary=True
    )
    if not employe:
        return {'ok': 0, 'skip': 0, 'erreur': 1, 'dossier': None,
                'message': f"Personnel id={personnel_id} introuvable"}

    # Documents actifs (hors archives)
    docs = QueryExecutor.fetch_all(
        """
        SELECT d.id, d.nom_affichage, d.nom_fichier, d.stockage_type, d.statut,
               c.nom AS categorie
        FROM documents d
        JOIN categories_documents c ON c.id = d.categorie_id
        WHERE d.personnel_id = %s AND d.statut != 'archive'
        ORDER BY c.nom, d.date_upload
        """,
        (personnel_id,), dictionary=True
    )

    dossier_emp = _dossier_employe(
        employe['matricule'], employe['nom'], employe['prenom']
    )

    stats = {'ok': 0, 'skip': 0, 'erreur': 0, 'dossier': dossier_emp}

    for doc in docs:
        contenu = _extraire_blob(doc['id'])
        if contenu is None:
            print(f"    [SKIP]  id={doc['id']} '{doc['nom_affichage']}' — contenu introuvable")
            stats['skip'] += 1
            continue

        dossier_cat = _dossier_categorie(dossier_emp, doc['categorie'])
        nom = doc['nom_affichage'] or doc['nom_fichier'] or f"document_{doc['id']}"
        dest = _nom_fichier_unique(dossier_cat, nom)

        try:
            dest.write_bytes(contenu)
            print(f"    [OK]    {doc['categorie']} / {dest.name}")
            stats['ok'] += 1
        except Exception as e:
            print(f"    [ERR]   id={doc['id']} '{nom}' — {e}")
            stats['erreur'] += 1

    return stats


def exporter_tous() -> None:
    """Exporte les documents de tous les employes qui en ont."""
    employes = QueryExecutor.fetch_all(
        """
        SELECT DISTINCT p.id, p.matricule, p.nom, p.prenom
        FROM personnel p
        JOIN documents d ON d.personnel_id = p.id
        WHERE d.statut != 'archive'
        ORDER BY p.nom, p.prenom
        """,
        dictionary=True
    )

    if not employes:
        print("Aucun document a exporter.")
        return

    total_ok = total_skip = total_err = 0

    for emp in employes:
        print(f"\n  {emp['matricule']} — {emp['nom'].upper()} {emp['prenom']}")
        stats = exporter_employe(emp['id'])
        total_ok   += stats['ok']
        total_skip += stats['skip']
        total_err  += stats['erreur']

    print(f"\n{'='*60}")
    print(f"  Export termine : {total_ok} fichier(s) exporte(s)"
          + (f", {total_skip} ignore(s)" if total_skip else "")
          + (f", {total_err} erreur(s)" if total_err else ""))
    print(f"  Dossier : {EXPORT_ROOT}")
    print(f"{'='*60}")


# ──────────────────────────────────────────────────────────────────────────────
# Point d'entree
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Exporte les documents BLOB vers le systeme de fichiers."
    )
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--id",  type=int,  help="ID personnel a exporter")
    grp.add_argument("--mat", type=str,  help="Matricule a exporter (ex: M000115)")
    args = parser.parse_args()

    print(f"\nExport documents BLOB -> systeme de fichiers")
    print(f"Destination : {EXPORT_ROOT}\n")

    if args.id:
        stats = exporter_employe(args.id)
        if stats['dossier']:
            print(f"\n  {stats['ok']} fichier(s) exporte(s) dans :\n  {stats['dossier']}")
    elif args.mat:
        row = QueryExecutor.fetch_one(
            "SELECT id FROM personnel WHERE matricule = %s", (args.mat,), dictionary=True
        )
        if not row:
            print(f"Matricule '{args.mat}' introuvable.")
            sys.exit(1)
        stats = exporter_employe(row['id'])
        if stats['dossier']:
            print(f"\n  {stats['ok']} fichier(s) exporte(s) dans :\n  {stats['dossier']}")
    else:
        exporter_tous()
