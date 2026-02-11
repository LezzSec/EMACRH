# -*- coding: utf-8 -*-
"""
Service de gestion des formations
CRUD pour la table `formation` existante
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Tuple, Any

from core.db.query_executor import QueryExecutor
from core.services.logger import log_hist
from core.utils.logging_config import get_logger

logger = get_logger(__name__)


def get_all_formations(
    statut: str = None,
    operateur_id: int = None
) -> List[Dict]:
    """
    Récupère toutes les formations avec filtres optionnels

    Args:
        statut: Filtrer par statut (Planifiée, En cours, Terminée, Annulée)
        operateur_id: Filtrer par opérateur

    Returns:
        Liste des formations avec infos opérateur
    """
    try:
        sql = """
            SELECT
                f.id, f.operateur_id, f.intitule, f.organisme,
                f.date_debut, f.date_fin, f.duree_heures, f.statut,
                f.certificat_obtenu, f.cout, f.commentaire,
                f.document_id,
                f.date_creation, f.date_modification,
                CONCAT(p.prenom, ' ', p.nom) as nom_complet,
                p.matricule,
                d.nom_fichier as attestation_nom
            FROM formation f
            JOIN personnel p ON f.operateur_id = p.id
            LEFT JOIN documents d ON f.document_id = d.id
            WHERE 1=1
        """
        params = []

        if statut:
            sql += " AND f.statut = %s"
            params.append(statut)

        if operateur_id:
            sql += " AND f.operateur_id = %s"
            params.append(operateur_id)

        sql += " ORDER BY f.date_debut DESC"

        formations = QueryExecutor.fetch_all(sql, tuple(params), dictionary=True)

        # Convertir Decimal en float pour éviter les problèmes de sérialisation
        for f in formations:
            if f.get('duree_heures') is not None:
                f['duree_heures'] = float(f['duree_heures'])
            if f.get('cout') is not None:
                f['cout'] = float(f['cout'])

        return formations
    except Exception as e:
        logger.error(f"Erreur get_all_formations: {e}")
        return []


def get_formations_personnel(operateur_id: int) -> List[Dict]:
    """
    Récupère les formations d'un opérateur spécifique

    Args:
        operateur_id: ID de l'opérateur

    Returns:
        Liste des formations
    """
    return get_all_formations(operateur_id=operateur_id)


def get_formation_by_id(formation_id: int) -> Optional[Dict]:
    """
    Récupère une formation par son ID

    Args:
        formation_id: ID de la formation

    Returns:
        Dictionnaire de la formation ou None
    """
    try:
        formation = QueryExecutor.fetch_one("""
            SELECT
                f.id, f.operateur_id, f.intitule, f.organisme,
                f.date_debut, f.date_fin, f.duree_heures, f.statut,
                f.certificat_obtenu, f.cout, f.commentaire,
                f.document_id,
                f.date_creation, f.date_modification,
                CONCAT(p.prenom, ' ', p.nom) as nom_complet,
                p.matricule,
                d.nom_fichier as attestation_nom
            FROM formation f
            JOIN personnel p ON f.operateur_id = p.id
            LEFT JOIN documents d ON f.document_id = d.id
            WHERE f.id = %s
        """, (formation_id,), dictionary=True)

        if formation:
            if formation.get('duree_heures') is not None:
                formation['duree_heures'] = float(formation['duree_heures'])
            if formation.get('cout') is not None:
                formation['cout'] = float(formation['cout'])

        return formation
    except Exception as e:
        logger.error(f"Erreur get_formation_by_id: {e}")
        return None


def add_formation(
    operateur_id: int,
    intitule: str,
    date_debut: date,
    date_fin: date,
    organisme: str = None,
    duree_heures: float = None,
    statut: str = "Planifiée",
    certificat_obtenu: bool = False,
    cout: float = None,
    commentaire: str = None
) -> Tuple[bool, str, Optional[int]]:
    """
    Ajoute une nouvelle formation

    Args:
        operateur_id: ID de l'opérateur
        intitule: Titre de la formation
        date_debut: Date de début
        date_fin: Date de fin
        organisme: Organisme formateur
        duree_heures: Durée en heures
        statut: Statut (Planifiée, En cours, Terminée, Annulée)
        certificat_obtenu: Si un certificat a été obtenu
        cout: Coût de la formation
        commentaire: Notes

    Returns:
        (succès, message, formation_id)
    """
    try:
        formation_id = QueryExecutor.execute_write("""
            INSERT INTO formation (
                operateur_id, intitule, organisme, date_debut, date_fin,
                duree_heures, statut, certificat_obtenu, cout, commentaire
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            operateur_id, intitule, organisme, date_debut, date_fin,
            duree_heures, statut, certificat_obtenu, cout, commentaire
        ), return_lastrowid=True)

        log_hist(
            action="CREATION_FORMATION",
            table_name="formation",
            record_id=formation_id,
            description=f"Formation '{intitule}' ajoutée pour opérateur {operateur_id}"
        )

        return True, "Formation ajoutée avec succès", formation_id

    except Exception as e:
        return False, f"Erreur lors de l'ajout: {str(e)}", None


def update_formation(formation_id: int, **kwargs) -> Tuple[bool, str]:
    """
    Met à jour une formation

    Args:
        formation_id: ID de la formation
        **kwargs: Champs à mettre à jour

    Returns:
        (succès, message)
    """
    # SÉCURITÉ: Whitelist stricte des colonnes autorisées (frozenset = immutable)
    ALLOWED_FIELDS = frozenset([
        'operateur_id', 'intitule', 'organisme', 'date_debut', 'date_fin',
        'duree_heures', 'statut', 'certificat_obtenu', 'cout', 'commentaire',
        'document_id'
    ])

    # Filtrer les champs autorisés
    updates = {k: v for k, v in kwargs.items() if k in ALLOWED_FIELDS}

    if not updates:
        return False, "Aucun champ à mettre à jour"

    try:
        # SÉCURITÉ: Vérification que chaque clé est bien dans la whitelist
        set_clauses = []
        values = []
        for key in updates.keys():
            assert key in ALLOWED_FIELDS, f"Colonne non autorisée: {key}"
            set_clauses.append(f"{key} = %s")
            values.append(updates[key])
        values.append(formation_id)

        # SÉCURITÉ: Les colonnes proviennent uniquement de ALLOWED_FIELDS (constante)
        sql = "UPDATE formation SET " + ", ".join(set_clauses) + " WHERE id = %s"

        QueryExecutor.execute_write(sql, tuple(values))

        log_hist(
            action="UPDATE_FORMATION",
            table_name="formation",
            record_id=formation_id,
            description=f"Formation {formation_id} mise à jour",
            details=updates
        )

        return True, "Formation mise à jour avec succès"

    except Exception as e:
        return False, f"Erreur lors de la mise à jour: {str(e)}"


def delete_formation(formation_id: int) -> Tuple[bool, str]:
    """
    Supprime une formation

    Args:
        formation_id: ID de la formation

    Returns:
        (succès, message)
    """
    try:
        # Récupérer les infos avant suppression pour le log
        formation = get_formation_by_id(formation_id)

        QueryExecutor.execute_write(
            "DELETE FROM formation WHERE id = %s",
            (formation_id,)
        )

        log_hist(
            action="SUPPRESSION_FORMATION",
            table_name="formation",
            record_id=formation_id,
            description=f"Formation '{formation.get('intitule', '?')}' supprimée" if formation else f"Formation {formation_id} supprimée"
        )

        return True, "Formation supprimée avec succès"

    except Exception as e:
        return False, f"Erreur lors de la suppression: {str(e)}"


def get_formations_stats() -> Dict[str, Any]:
    """
    Récupère les statistiques des formations

    Returns:
        Dictionnaire avec les stats
    """
    try:
        stats = {}

        # Total formations
        stats['total'] = QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM formation", default=0
        )

        # Par statut
        rows = QueryExecutor.fetch_all("""
            SELECT statut, COUNT(*) as count
            FROM formation
            GROUP BY statut
        """, dictionary=True)
        stats['par_statut'] = {row['statut']: row['count'] for row in rows}

        # Formations cette année
        annee = datetime.now().year
        stats['cette_annee'] = QueryExecutor.fetch_scalar("""
            SELECT COUNT(*) FROM formation
            WHERE YEAR(date_debut) = %s
        """, (annee,), default=0)

        # Formations terminées cette année
        stats['terminees_cette_annee'] = QueryExecutor.fetch_scalar("""
            SELECT COUNT(*) FROM formation
            WHERE statut = 'Terminée' AND YEAR(date_fin) = %s
        """, (annee,), default=0)

        # En cours
        stats['en_cours'] = stats['par_statut'].get('En cours', 0)

        # Planifiées
        stats['planifiees'] = stats['par_statut'].get('Planifiée', 0)

        return stats

    except Exception as e:
        logger.error(f"Erreur get_formations_stats: {e}")
        return {
            'total': 0,
            'par_statut': {},
            'cette_annee': 0,
            'terminees_cette_annee': 0,
            'en_cours': 0,
            'planifiees': 0
        }


def get_personnel_list() -> List[Dict]:
    """
    Récupère la liste du personnel actif pour les combos

    Returns:
        Liste des opérateurs (id, nom_complet, matricule)
    """
    try:
        return QueryExecutor.fetch_all("""
            SELECT id, CONCAT(prenom, ' ', nom) as nom_complet, matricule
            FROM personnel
            WHERE statut = 'ACTIF'
            ORDER BY nom, prenom
        """, dictionary=True)
    except Exception as e:
        logger.error(f"Erreur get_personnel_list: {e}")
        return []
