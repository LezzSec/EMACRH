# -*- coding: utf-8 -*-
"""
Service de gestion des dossiers de formation pour les niveaux de polyvalence.

Ces documents sont associes a un poste (et optionnellement un niveau 1-4).
Ils sont lisibles par tous les utilisateurs et administres par les responsables.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)

from core.db.query_executor import QueryExecutor
from core.db.configbd import DatabaseConnection
from core.services.optimized_db_logger import log_hist


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def get_docs_pour_poste(poste_id: int, niveau: Optional[int] = None) -> List[Dict]:
    """
    Retourne les documents de formation associes a un poste.

    Si niveau est fourni, retourne les docs du niveau exact + les docs sans niveau
    (applicables a tous niveaux). Sinon retourne tous les docs du poste.
    """
    try:
        if niveau is not None:
            sql = """
                SELECT
                    d.id, d.poste_id, d.niveau, d.nom_affichage, d.nom_fichier,
                    d.type_mime, d.taille_octets, d.description, d.date_ajout, d.ajoute_par,
                    p.poste_code
                FROM documents_formation_polyvalence d
                JOIN postes p ON p.id = d.poste_id
                WHERE d.poste_id = %s AND (d.niveau = %s OR d.niveau IS NULL)
                ORDER BY d.niveau ASC, d.nom_affichage ASC
            """
            return QueryExecutor.fetch_all(sql, (poste_id, niveau), dictionary=True)
        else:
            sql = """
                SELECT
                    d.id, d.poste_id, d.niveau, d.nom_affichage, d.nom_fichier,
                    d.type_mime, d.taille_octets, d.description, d.date_ajout, d.ajoute_par,
                    p.poste_code
                FROM documents_formation_polyvalence d
                JOIN postes p ON p.id = d.poste_id
                WHERE d.poste_id = %s
                ORDER BY d.niveau ASC, d.nom_affichage ASC
            """
            return QueryExecutor.fetch_all(sql, (poste_id,), dictionary=True)
    except Exception as e:
        logger.exception(f"Erreur get_docs_pour_poste(poste_id={poste_id}): {e}")
        return []


def get_docs_pour_operateur(operateur_id: int) -> List[Dict]:
    """
    Retourne les polyvalences d'un operateur avec les documents de formation associes.

    Retourne une liste de dicts avec les champs polyvalence + liste 'documents'.
    """
    try:
        polyvalences = QueryExecutor.fetch_all(
            """
            SELECT
                pv.id AS polyvalence_id,
                pv.poste_id,
                pv.niveau,
                pv.date_evaluation,
                pv.prochaine_evaluation,
                po.poste_code,
                a.nom AS atelier_nom
            FROM polyvalence pv
            JOIN postes po ON po.id = pv.poste_id
            LEFT JOIN atelier a ON a.id = po.atelier_id
            WHERE pv.personnel_id = %s
            ORDER BY a.nom ASC, po.poste_code ASC
            """,
            (operateur_id,),
            dictionary=True
        )

        for poly in polyvalences:
            poly['documents'] = get_docs_pour_poste(poly['poste_id'], poly['niveau'])

        return polyvalences

    except Exception as e:
        logger.exception(f"Erreur get_docs_pour_operateur(op={operateur_id}): {e}")
        return []


def get_tous_les_postes_avec_docs() -> List[Dict]:
    """
    Retourne tous les postes qui ont au moins un document de formation,
    avec le nombre de documents par niveau.
    Utile pour l'ecran d'administration.
    """
    try:
        return QueryExecutor.fetch_all(
            """
            SELECT
                p.id AS poste_id,
                p.poste_code,
                a.nom AS atelier_nom,
                COUNT(d.id) AS nb_documents
            FROM postes p
            LEFT JOIN atelier a ON a.id = p.atelier_id
            LEFT JOIN documents_formation_polyvalence d ON d.poste_id = p.id
            WHERE p.visible = 1
            GROUP BY p.id, p.poste_code, a.nom
            ORDER BY a.nom ASC, p.poste_code ASC
            """,
            dictionary=True
        )
    except Exception as e:
        logger.exception(f"Erreur get_tous_les_postes_avec_docs: {e}")
        return []


# ---------------------------------------------------------------------------
# Contenu / ouverture
# ---------------------------------------------------------------------------

def get_contenu_document(doc_id: int) -> Optional[Tuple[bytes, str, str]]:
    """
    Retourne (contenu_bytes, nom_fichier, type_mime) ou None si introuvable.
    """
    try:
        row = QueryExecutor.fetch_one(
            "SELECT contenu_fichier, nom_fichier, type_mime "
            "FROM documents_formation_polyvalence WHERE id = %s",
            (doc_id,),
            dictionary=True
        )
        if row and row.get('contenu_fichier'):
            return (row['contenu_fichier'], row['nom_fichier'], row['type_mime'] or '')
        return None
    except Exception as e:
        logger.exception(f"Erreur get_contenu_document(id={doc_id}): {e}")
        return None


def extraire_vers_fichier_temp(doc_id: int) -> Optional[Path]:
    """
    Extrait le BLOB vers un fichier temporaire pour ouverture par l'OS.
    Retourne le Path temporaire ou None.
    """
    result = get_contenu_document(doc_id)
    if not result:
        return None
    contenu, nom_fichier, _ = result

    temp_dir = Path(tempfile.gettempdir()) / "emac_formation_poly" / str(doc_id)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Nettoyer le nom de fichier
    safe_name = ''.join(c if (c.isalnum() or c in '._ -') else '_' for c in nom_fichier)
    temp_path = temp_dir / safe_name
    temp_path.write_bytes(contenu)
    return temp_path


# ---------------------------------------------------------------------------
# Ecriture (admin)
# ---------------------------------------------------------------------------

def ajouter_document(
    poste_id: int,
    nom_affichage: str,
    fichier_source: str,
    niveau: Optional[int] = None,
    description: str = None,
    ajoute_par: str = "Systeme"
) -> Tuple[bool, str, Optional[int]]:
    """
    Ajoute un document de formation pour un poste (et optionnellement un niveau).

    Returns:
        (succes, message, doc_id)
    """
    try:
        source = Path(fichier_source)
        if not source.exists():
            return False, f"Fichier introuvable : {fichier_source}", None

        taille = source.stat().st_size
        if taille > 32 * 1024 * 1024:  # 32 Mo max
            return False, "Fichier trop volumineux (max 32 Mo)", None

        import mimetypes
        type_mime = mimetypes.guess_type(str(source))[0] or 'application/octet-stream'
        contenu = source.read_bytes()

        new_id = QueryExecutor.execute_write(
            """
            INSERT INTO documents_formation_polyvalence
                (poste_id, niveau, nom_affichage, nom_fichier, contenu_fichier,
                 type_mime, taille_octets, description, ajoute_par)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (poste_id, niveau, nom_affichage, source.name, contenu,
             type_mime, taille, description, ajoute_par)
        )

        log_hist(
            "AJOUT_DOC_FORMATION_POLYVALENCE",
            f"Document '{nom_affichage}' ajouté pour poste_id={poste_id} niveau={niveau}",
            poste_id=poste_id
        )
        return True, "Document ajouté avec succès", new_id

    except Exception as e:
        logger.exception(f"Erreur ajouter_document: {e}")
        return False, f"Erreur lors de l'ajout : {e}", None


def supprimer_document(doc_id: int) -> Tuple[bool, str]:
    """Supprime un document de formation."""
    try:
        # Récupérer les infos pour le log
        row = QueryExecutor.fetch_one(
            "SELECT nom_affichage, poste_id, niveau FROM documents_formation_polyvalence WHERE id = %s",
            (doc_id,),
            dictionary=True
        )
        if not row:
            return False, "Document introuvable"

        QueryExecutor.execute_write(
            "DELETE FROM documents_formation_polyvalence WHERE id = %s",
            (doc_id,)
        )

        log_hist(
            "SUPPRESSION_DOC_FORMATION_POLYVALENCE",
            f"Document '{row['nom_affichage']}' supprimé (poste_id={row['poste_id']}, niveau={row['niveau']})",
            poste_id=row['poste_id']
        )
        return True, "Document supprimé"

    except Exception as e:
        logger.exception(f"Erreur supprimer_document(id={doc_id}): {e}")
        return False, f"Erreur : {e}"
