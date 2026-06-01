# -*- coding: utf-8 -*-
"""
Service de gestion des dossiers de formation pour les niveaux de polyvalence.

Ces documents sont associes a un poste (et optionnellement un niveau 1-4).
Ils sont lisibles par tous les utilisateurs et administres par les responsables.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.optimized_db_logger import log_hist_async


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

    Chaque dict inclut 'eval_doc_id' et 'eval_doc_nom' (document d'evaluation joint
    a l'instance de polyvalence, distinct des dossiers de formation par poste/niveau).
    """
    try:
        polyvalences = QueryExecutor.fetch_all(
            """
            SELECT
                pv.id AS polyvalence_id,
                pv.document_id AS eval_doc_id,
                pv.poste_id,
                pv.niveau,
                pv.date_evaluation,
                pv.prochaine_evaluation,
                po.poste_code,
                a.nom AS atelier_nom,
                d.nom_affichage AS eval_doc_nom
            FROM polyvalence pv
            JOIN postes po ON po.id = pv.poste_id
            LEFT JOIN atelier a ON a.id = po.atelier_id
            LEFT JOIN documents d ON d.id = pv.document_id
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


def attacher_document_evaluation(poly_id: int, document_id: int) -> Tuple[bool, str]:
    """Lie un document d'evaluation a une instance de polyvalence."""
    from application.permission_manager import require
    require("rh.documents.edit")
    try:
        QueryExecutor.execute_write(
            "UPDATE polyvalence SET document_id = %s WHERE id = %s",
            (document_id, poly_id),
            return_lastrowid=False,
        )
        return True, "Document d'evaluation attache avec succes"
    except Exception as e:
        logger.exception(f"Erreur attacher_document_evaluation(poly={poly_id}): {e}")
        return False, f"Erreur lors de l'attachement : {e}"


def retirer_document_evaluation(poly_id: int) -> Tuple[bool, str]:
    """Delie et archive le document d'evaluation d'une polyvalence."""
    from application.permission_manager import require
    require("rh.documents.edit")
    try:
        row = QueryExecutor.fetch_one(
            "SELECT document_id FROM polyvalence WHERE id = %s",
            (poly_id,), dictionary=True
        )
        doc_id = row.get('document_id') if row else None

        QueryExecutor.execute_write(
            "UPDATE polyvalence SET document_id = NULL WHERE id = %s",
            (poly_id,),
            return_lastrowid=False,
        )

        if doc_id:
            from domain.services.documents.document_service import DocumentService
            DocumentService().archive_document(doc_id)

        return True, "Document archive"
    except Exception as e:
        logger.exception(f"Erreur retirer_document_evaluation(poly={poly_id}): {e}")
        return False, f"Erreur lors du retrait : {e}"


def get_polyvalences_synthese() -> List[Dict]:
    """
    Retourne toutes les polyvalences du personnel actif avec leur document d'evaluation.

    Utilise dans l'onglet Formation > Synthese polyvalences.
    """
    try:
        return QueryExecutor.fetch_all(
            """
            SELECT
                pv.id AS polyvalence_id,
                pv.document_id AS eval_doc_id,
                pv.niveau,
                pv.date_evaluation,
                po.poste_code,
                a.nom AS atelier_nom,
                p.nom, p.prenom, p.matricule,
                d.nom_affichage AS eval_doc_nom
            FROM polyvalence pv
            JOIN personnel p ON p.id = pv.personnel_id
            JOIN postes po ON po.id = pv.poste_id
            LEFT JOIN atelier a ON a.id = po.atelier_id
            LEFT JOIN documents d ON d.id = pv.document_id
            WHERE p.statut = 'ACTIF'
            ORDER BY p.nom ASC, p.prenom ASC, a.nom ASC, po.poste_code ASC
            """,
            dictionary=True,
        )
    except Exception as e:
        logger.exception(f"Erreur get_polyvalences_synthese: {e}")
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

    from domain.services.documents.template_service import get_temp_dir
    temp_dir = get_temp_dir() / "formation_poly" / str(doc_id)
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

        log_hist_async(
            action="AJOUT_DOC_FORMATION_POLYVALENCE",
            table_name="documents_formation_polyvalence",
            record_id=new_id,
            description=f"Document '{nom_affichage}' ajouté pour poste_id={poste_id} niveau={niveau}",
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

        log_hist_async(
            action="SUPPRESSION_DOC_FORMATION_POLYVALENCE",
            table_name="documents_formation_polyvalence",
            record_id=doc_id,
            description=f"Document '{row['nom_affichage']}' supprimé (poste_id={row['poste_id']}, niveau={row['niveau']})",
            poste_id=row['poste_id']
        )
        return True, "Document supprimé"

    except Exception as e:
        logger.exception(f"Erreur supprimer_document(id={doc_id}): {e}")
        return False, f"Erreur : {e}"
