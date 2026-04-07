# -*- coding: utf-8 -*-
"""
Repository pour la table documents et categories_documents.

Centralise toutes les requêtes SQL liées aux documents RH :
récupération par domaine, archives, catégories, alertes et entités.

Usage:
    from domain.repositories.document_repo import DocumentRepository

    docs = DocumentRepository.get_by_operateur_domaine(1, [3, 7])
    cats = DocumentRepository.get_categories()
    alertes = DocumentRepository.get_alertes(jours=30)
"""

import logging
from typing import List, Dict, Optional, Any

from infrastructure.db.query_executor import QueryExecutor

logger = logging.getLogger(__name__)

# Whitelist des types d'entités autorisés pour get_by_entite()
# Protection contre l'injection SQL via les noms de colonnes.
_ENTITE_QUERIES: Dict[str, str] = {
    'contrat': (
        "SELECT id, nom_affichage, nom_fichier, date_expiration "
        "FROM documents WHERE contrat_id = %s"
    ),
    'formation': (
        "SELECT id, nom_affichage, nom_fichier, date_expiration "
        "FROM documents WHERE formation_id = %s"
    ),
    'declaration': (
        "SELECT id, nom_affichage, nom_fichier, date_expiration "
        "FROM documents WHERE declaration_id = %s"
    ),
}

_DOC_SELECT = """
    SELECT
        d.id, d.personnel_id, d.categorie_id,
        d.nom_fichier, d.nom_affichage, d.chemin_fichier,
        d.type_mime, d.taille_octets, d.date_upload,
        d.date_expiration, d.statut, d.notes, d.uploaded_by,
        c.nom  AS categorie_nom,
        c.couleur AS categorie_couleur,
        CASE
            WHEN d.date_expiration IS NULL                                     THEN NULL
            WHEN d.date_expiration < CURDATE()                                 THEN 'EXPIRE'
            WHEN d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)     THEN 'EXPIRE_BIENTOT'
            ELSE 'VALIDE'
        END AS statut_expiration,
        DATEDIFF(d.date_expiration, CURDATE()) AS jours_avant_expiration
    FROM documents d
    JOIN categories_documents c ON d.categorie_id = c.id
"""


class DocumentRepository:
    """Repository pour les documents et leurs catégories."""

    # ------------------------------------------------------------------
    # Catégories
    # ------------------------------------------------------------------

    @classmethod
    def get_categories(cls) -> List[Dict[str, Any]]:
        """
        Retourne toutes les catégories de documents, triées par ordre d'affichage.

        Returns:
            Liste de dicts (id, nom, couleur, ordre_affichage, ...)
        """
        return QueryExecutor.fetch_all(
            "SELECT * FROM categories_documents ORDER BY ordre_affichage",
            dictionary=True,
        )

    # ------------------------------------------------------------------
    # Documents par domaine
    # ------------------------------------------------------------------

    @classmethod
    def get_by_operateur_domaine(
        cls,
        operateur_id: int,
        categories_ids: List[int],
        include_archives: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Retourne les documents d'un opérateur pour une liste de catégories.

        Args:
            operateur_id: ID du personnel
            categories_ids: IDs des catégories correspondant au domaine
            include_archives: Inclure les documents archivés

        Returns:
            Liste de dicts enrichis (categorie_nom, statut_expiration, ...)
        """
        if not categories_ids:
            return []

        placeholders = ", ".join(["%s"] * len(categories_ids))
        sql = (
            f"{_DOC_SELECT}"
            f"WHERE d.personnel_id = %s AND d.categorie_id IN ({placeholders})"
        )
        params: list = [operateur_id] + categories_ids

        if not include_archives:
            sql += " AND (d.statut IS NULL OR d.statut != 'archive')"

        sql += " ORDER BY d.date_upload DESC"

        return QueryExecutor.fetch_all(sql, tuple(params), dictionary=True)

    @classmethod
    def get_archives_by_operateur(cls, operateur_id: int) -> List[Dict[str, Any]]:
        """
        Retourne tous les documents archivés d'un opérateur.

        Returns:
            Liste de dicts (sans statut_expiration — archives n'ont plus de date utile)
        """
        return QueryExecutor.fetch_all(
            """
            SELECT
                d.id, d.personnel_id, d.categorie_id,
                d.nom_fichier, d.nom_affichage, d.chemin_fichier,
                d.type_mime, d.taille_octets, d.date_upload,
                d.date_expiration, d.statut, d.notes, d.uploaded_by,
                c.nom  AS categorie_nom,
                c.couleur AS categorie_couleur
            FROM documents d
            JOIN categories_documents c ON d.categorie_id = c.id
            WHERE d.personnel_id = %s AND d.statut = 'archive'
            ORDER BY d.date_upload DESC
            """,
            (operateur_id,),
            dictionary=True,
        )

    # ------------------------------------------------------------------
    # Documents par entité (contrat / formation / declaration)
    # ------------------------------------------------------------------

    @classmethod
    def get_by_entite(cls, entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
        """
        Retourne les documents liés à une entité (contrat, formation, declaration).

        Utilise une whitelist statique pour prévenir l'injection SQL via entity_type.
        Les types inconnus retournent [] sans lever d'exception.

        Args:
            entity_type: 'contrat' | 'formation' | 'declaration'
            entity_id: ID de l'entité

        Returns:
            Liste de dicts ou [] si type invalide
        """
        if not isinstance(entity_type, str) or entity_type not in _ENTITE_QUERIES:
            logger.warning("Type d'entité invalide ou non autorisé: %r", entity_type)
            return []

        return QueryExecutor.fetch_all(
            _ENTITE_QUERIES[entity_type],
            (entity_id,),
            dictionary=True,
        )

    # ------------------------------------------------------------------
    # Alertes (documents expirant bientôt)
    # ------------------------------------------------------------------

    @classmethod
    def get_alertes(cls, jours: int = 30, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Retourne les documents actifs expirant dans les N prochains jours,
        pour tous les opérateurs actifs.

        Utilisé par get_alertes_rh_dashboard() dans rh_service.

        Returns:
            Liste de dicts (id, personnel_id, nom_affichage, date_expiration,
                            nom, prenom, matricule, categorie, jours_restants)
        """
        return QueryExecutor.fetch_all(
            """
            SELECT
                d.id, d.personnel_id, d.nom_affichage, d.nom_fichier,
                d.date_expiration,
                p.nom, p.prenom, p.matricule,
                c.nom AS categorie,
                DATEDIFF(d.date_expiration, CURDATE()) AS jours_restants
            FROM documents d
            INNER JOIN personnel p ON p.id = d.personnel_id
            LEFT JOIN categories_documents c ON c.id = d.categorie_id
            WHERE d.statut = 'actif'
              AND d.date_expiration IS NOT NULL
              AND d.date_expiration BETWEEN CURDATE()
                  AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
              AND p.statut = 'ACTIF'
            ORDER BY d.date_expiration ASC
            LIMIT %s
            """,
            (jours, limit),
            dictionary=True,
        )

    @classmethod
    def count_alertes(cls, jours: int = 30) -> int:
        """
        Compte les documents actifs expirant dans les N prochains jours.

        Utilisé par get_alertes_rh_count() dans rh_service.
        """
        return QueryExecutor.fetch_scalar(
            """
            SELECT COUNT(*) FROM documents d
            INNER JOIN personnel p ON p.id = d.personnel_id
            WHERE d.statut = 'actif'
              AND d.date_expiration IS NOT NULL
              AND d.date_expiration BETWEEN CURDATE()
                  AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
              AND p.statut = 'ACTIF'
            """,
            (jours,),
            default=0,
        )

    # ------------------------------------------------------------------
    # Résumé documents d'un opérateur
    # ------------------------------------------------------------------

    @classmethod
    def get_resume(cls, operateur_id: int) -> Dict[str, Any]:
        """
        Retourne un résumé agrégé des documents d'un opérateur.

        Utilisé par get_resume_operateur() dans rh_service.

        Returns:
            {"total": int, "expires": int, "expire_bientot": int}
        """
        row = QueryExecutor.fetch_one(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN statut = 'expire'  THEN 1 ELSE 0 END) AS expires,
                SUM(
                    CASE WHEN date_expiration IS NOT NULL
                              AND date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                              AND date_expiration > CURDATE()
                         THEN 1 ELSE 0 END
                ) AS expire_bientot
            FROM documents
            WHERE personnel_id = %s AND statut != 'archive'
            """,
            (operateur_id,),
            dictionary=True,
        ) or {}
        return {
            "total": row.get("total") or 0,
            "expires": row.get("expires") or 0,
            "expire_bientot": row.get("expire_bientot") or 0,
        }
