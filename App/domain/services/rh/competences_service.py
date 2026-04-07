# -*- coding: utf-8 -*-
"""
Service de gestion des compétences transversales.

Ce service gère :
- Le catalogue des compétences (CRUD)
- L'assignation des compétences au personnel
- Les statistiques et alertes d'expiration

Les compétences transversales sont des compétences génériques (managériales,
sécurité, habilitations) qui peuvent être assignées à plusieurs personnes,
contrairement à la polyvalence qui est liée aux postes de travail.

Refactorisé: Utilise QueryExecutor au lieu de DatabaseCursor/DatabaseConnection.
"""

from datetime import date
from typing import List, Dict, Optional, Tuple, Any

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.optimized_db_logger import log_hist
from application.permission_manager import require
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# Champs autorisés pour les mises à jour (protection injection SQL)
ALLOWED_CATALOGUE_FIELDS = frozenset([
    'code', 'libelle', 'description', 'categorie', 'duree_validite_mois', 'actif'
])

ALLOWED_ASSIGNMENT_FIELDS = frozenset([
    'date_acquisition', 'date_expiration', 'commentaire', 'document_id'
])


# ============================================================
# CATALOGUE DES COMPÉTENCES
# ============================================================

def get_all_competences(actif_only: bool = True) -> List[Dict]:
    """
    Récupère toutes les compétences du catalogue.

    Args:
        actif_only: Si True, retourne uniquement les compétences actives

    Returns:
        Liste des compétences avec leurs attributs
    """
    try:
        if actif_only:
            return QueryExecutor.fetch_all(
                """SELECT id, code, libelle, description, categorie,
                          duree_validite_mois, actif, created_at, updated_at
                   FROM competences_catalogue
                   WHERE actif = 1
                   ORDER BY categorie, libelle""",
                dictionary=True
            )
        else:
            return QueryExecutor.fetch_all(
                """SELECT id, code, libelle, description, categorie,
                          duree_validite_mois, actif, created_at, updated_at
                   FROM competences_catalogue
                   ORDER BY categorie, libelle""",
                dictionary=True
            )
    except Exception as e:
        logger.exception(f"Erreur get_all_competences: {e}")
        return []


def get_competence_by_id(competence_id: int) -> Optional[Dict]:
    """
    Récupère une compétence par son ID.

    Args:
        competence_id: ID de la compétence

    Returns:
        Dictionnaire de la compétence ou None
    """
    try:
        return QueryExecutor.fetch_one(
            """SELECT id, code, libelle, description, categorie,
                      duree_validite_mois, actif, created_at, updated_at
               FROM competences_catalogue
               WHERE id = %s""",
            (competence_id,), dictionary=True
        )
    except Exception as e:
        logger.exception(f"Erreur get_competence_by_id: {e}")
        return None


def get_categories() -> List[str]:
    """
    Récupère la liste des catégories distinctes.

    Returns:
        Liste des catégories
    """
    try:
        rows = QueryExecutor.fetch_all(
            """SELECT DISTINCT categorie
               FROM competences_catalogue
               WHERE categorie IS NOT NULL AND actif = 1
               ORDER BY categorie""",
            dictionary=True
        )
        return [row['categorie'] for row in rows]
    except Exception as e:
        logger.exception(f"Erreur get_categories: {e}")
        return []


def create_competence(
    code: str,
    libelle: str,
    categorie: Optional[str] = None,
    description: Optional[str] = None,
    duree_validite_mois: Optional[int] = None
) -> Tuple[bool, str, Optional[int]]:
    """
    Crée une nouvelle compétence dans le catalogue.

    Args:
        code: Code unique de la compétence
        libelle: Libellé affiché
        categorie: Catégorie (Managérial, Sécurité, etc.)
        description: Description détaillée
        duree_validite_mois: Durée de validité en mois (None = permanent)

    Returns:
        Tuple (succès, message, id_créé)
    """
    require('rh.competences.edit')
    if not code or not code.strip():
        return False, "Le code est obligatoire", None
    if not libelle or not libelle.strip():
        return False, "Le libellé est obligatoire", None

    try:
        competence_id = QueryExecutor.execute_write(
            """INSERT INTO competences_catalogue
               (code, libelle, categorie, description, duree_validite_mois)
               VALUES (%s, %s, %s, %s, %s)""",
            (code.strip().upper(), libelle.strip(), categorie, description, duree_validite_mois)
        )

        log_hist(
            action="CREATION_COMPETENCE_CATALOGUE",
            table_name="competences_catalogue",
            record_id=competence_id,
            description=f"Compétence '{libelle}' ({code}) créée"
        )

        return True, "Compétence créée avec succès", competence_id

    except Exception as e:
        logger.exception(f"Erreur create_competence: {e}")
        if "Duplicate entry" in str(e):
            return False, f"Le code '{code}' existe déjà", None
        return False, "Erreur lors de la création", None


def update_competence(competence_id: int, **kwargs) -> Tuple[bool, str]:
    """
    Met à jour une compétence du catalogue.

    Args:
        competence_id: ID de la compétence
        **kwargs: Champs à mettre à jour

    Returns:
        Tuple (succès, message)
    """
    require('rh.competences.edit')
    updates = {k: v for k, v in kwargs.items() if k in ALLOWED_CATALOGUE_FIELDS}

    if not updates:
        return False, "Aucun champ valide à mettre à jour"

    try:
        # Construction sécurisée de la requête
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [competence_id]

        QueryExecutor.execute_write(
            f"""UPDATE competences_catalogue
                SET {set_clause}
                WHERE id = %s""",
            values, return_lastrowid=False
        )

        log_hist(
            action="MODIFICATION_COMPETENCE_CATALOGUE",
            table_name="competences_catalogue",
            record_id=competence_id,
            description=f"Compétence ID {competence_id} modifiée: {list(updates.keys())}"
        )

        return True, "Compétence mise à jour"

    except Exception as e:
        logger.exception(f"Erreur update_competence: {e}")
        return False, "Erreur lors de la mise à jour"


def delete_competence(competence_id: int) -> Tuple[bool, str]:
    """
    Désactive une compétence (soft delete).

    Args:
        competence_id: ID de la compétence

    Returns:
        Tuple (succès, message)
    """
    require('rh.competences.delete')
    try:
        # Vérifier si des assignations existent
        count = QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM personnel_competences WHERE competence_id = %s",
            (competence_id,), default=0
        )

        if count > 0:
            # Soft delete si des assignations existent
            QueryExecutor.execute_write(
                "UPDATE competences_catalogue SET actif = 0 WHERE id = %s",
                (competence_id,), return_lastrowid=False
            )
            msg = "Compétence désactivée (assignations existantes)"
        else:
            # Hard delete si aucune assignation
            QueryExecutor.execute_write(
                "DELETE FROM competences_catalogue WHERE id = %s",
                (competence_id,), return_lastrowid=False
            )
            msg = "Compétence supprimée"

        log_hist(
            action="SUPPRESSION_COMPETENCE_CATALOGUE",
            table_name="competences_catalogue",
            record_id=competence_id,
            description=msg
        )

        return True, msg

    except Exception as e:
        logger.exception(f"Erreur delete_competence: {e}")
        return False, "Erreur lors de la suppression"


# ============================================================
# ASSIGNATION DES COMPÉTENCES AU PERSONNEL
# ============================================================

def get_competences_personnel(personnel_id: int) -> List[Dict]:
    """
    Récupère les compétences assignées à un membre du personnel.

    Args:
        personnel_id: ID du personnel

    Returns:
        Liste des compétences avec statut (active, expirée, expirant bientôt)
    """
    try:
        competences = QueryExecutor.fetch_all(
            """SELECT
                   pc.id as assignment_id,
                   pc.personnel_id,
                   pc.competence_id,
                   pc.date_acquisition,
                   pc.date_expiration,
                   pc.commentaire,
                   pc.document_id,
                   c.code,
                   c.libelle,
                   c.categorie,
                   c.duree_validite_mois,
                   DATEDIFF(pc.date_expiration, CURDATE()) as jours_restants
               FROM personnel_competences pc
               JOIN competences_catalogue c ON pc.competence_id = c.id
               WHERE pc.personnel_id = %s
               ORDER BY c.categorie, c.libelle""",
            (personnel_id,), dictionary=True
        )

        # Calculer le statut de chaque compétence
        for comp in competences:
            jours = comp.get('jours_restants')
            if comp.get('date_expiration') is None:
                comp['statut'] = 'permanent'
                comp['statut_label'] = 'Permanent'
            elif jours is not None and jours < 0:
                comp['statut'] = 'expiree'
                comp['statut_label'] = 'Expirée'
            elif jours is not None and jours <= 30:
                comp['statut'] = 'expire_bientot'
                comp['statut_label'] = f'Expire dans {jours} jour(s)'
            elif jours is not None and jours <= 90:
                comp['statut'] = 'attention'
                comp['statut_label'] = f'Expire dans {jours} jours'
            else:
                comp['statut'] = 'valide'
                comp['statut_label'] = 'Valide'

        return competences

    except Exception as e:
        logger.exception(f"Erreur get_competences_personnel: {e}")
        return []


def get_stats_personnel(personnel_id: int) -> Dict[str, Any]:
    """
    Calcule les statistiques des compétences d'un personnel.

    Args:
        personnel_id: ID du personnel

    Returns:
        Dictionnaire avec les statistiques
    """
    competences = get_competences_personnel(personnel_id)

    stats = {
        'total': len(competences),
        'permanentes': sum(1 for c in competences if c['statut'] == 'permanent'),
        'valides': sum(1 for c in competences if c['statut'] in ('permanent', 'valide', 'attention')),
        'expirees': sum(1 for c in competences if c['statut'] == 'expiree'),
        'expire_bientot_30j': sum(1 for c in competences if c['statut'] == 'expire_bientot'),
        'expire_bientot_90j': sum(1 for c in competences if c['statut'] in ('expire_bientot', 'attention')),
    }

    # Compter par catégorie
    categories = {}
    for c in competences:
        cat = c.get('categorie') or 'Autre'
        categories[cat] = categories.get(cat, 0) + 1
    stats['par_categorie'] = categories

    return stats


def assign_competence(
    personnel_id: int,
    competence_id: int,
    date_acquisition: date,
    date_expiration: Optional[date] = None,
    commentaire: Optional[str] = None,
    document_id: Optional[int] = None
) -> Tuple[bool, str, Optional[int]]:
    """
    Assigne une compétence à un membre du personnel.

    Args:
        personnel_id: ID du personnel
        competence_id: ID de la compétence
        date_acquisition: Date d'acquisition
        date_expiration: Date d'expiration (optionnel)
        commentaire: Commentaire (optionnel)
        document_id: ID du document lié (optionnel)

    Returns:
        Tuple (succès, message, id_assignation)
    """
    require('rh.competences.edit')
    try:
        # Vérifier que la compétence existe
        comp = QueryExecutor.fetch_one(
            "SELECT libelle FROM competences_catalogue WHERE id = %s",
            (competence_id,), dictionary=True
        )
        if not comp:
            return False, "Compétence introuvable", None

        # Vérifier si déjà assignée
        existing = QueryExecutor.fetch_one(
            """SELECT id FROM personnel_competences
               WHERE personnel_id = %s AND competence_id = %s""",
            (personnel_id, competence_id), dictionary=True
        )
        if existing:
            return False, "Cette compétence est déjà assignée à cette personne", None

        # Créer l'assignation
        assignment_id = QueryExecutor.execute_write(
            """INSERT INTO personnel_competences
               (personnel_id, competence_id, date_acquisition, date_expiration, commentaire, document_id)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (personnel_id, competence_id, date_acquisition, date_expiration, commentaire, document_id)
        )

        log_hist(
            action="ASSIGNATION_COMPETENCE",
            table_name="personnel_competences",
            record_id=assignment_id,
            description=f"Compétence '{comp['libelle']}' assignée au personnel {personnel_id}",
            operateur_id=personnel_id
        )

        return True, "Compétence assignée avec succès", assignment_id

    except Exception as e:
        logger.exception(f"Erreur assign_competence: {e}")
        return False, "Erreur lors de l'assignation", None


def update_assignment(assignment_id: int, **kwargs) -> Tuple[bool, str]:
    """
    Met à jour une assignation de compétence.

    Args:
        assignment_id: ID de l'assignation
        **kwargs: Champs à mettre à jour

    Returns:
        Tuple (succès, message)
    """
    require('rh.competences.edit')
    updates = {k: v for k, v in kwargs.items() if k in ALLOWED_ASSIGNMENT_FIELDS}

    if not updates:
        return False, "Aucun champ valide à mettre à jour"

    try:
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [assignment_id]

        QueryExecutor.execute_write(
            f"""UPDATE personnel_competences
                SET {set_clause}
                WHERE id = %s""",
            values, return_lastrowid=False
        )

        log_hist(
            action="MODIFICATION_COMPETENCE_PERSONNEL",
            table_name="personnel_competences",
            record_id=assignment_id,
            description=f"Assignation ID {assignment_id} modifiée: {list(updates.keys())}"
        )

        return True, "Compétence mise à jour"

    except Exception as e:
        logger.exception(f"Erreur update_assignment: {e}")
        return False, "Erreur lors de la mise à jour"


def remove_assignment(assignment_id: int) -> Tuple[bool, str]:
    """
    Retire une compétence d'un membre du personnel.

    Args:
        assignment_id: ID de l'assignation

    Returns:
        Tuple (succès, message)
    """
    require('rh.competences.delete')
    try:
        # Récupérer les infos pour le log
        info = QueryExecutor.fetch_one(
            """SELECT pc.personnel_id, c.libelle
               FROM personnel_competences pc
               JOIN competences_catalogue c ON pc.competence_id = c.id
               WHERE pc.id = %s""",
            (assignment_id,), dictionary=True
        )

        if not info:
            return False, "Assignation introuvable"

        QueryExecutor.execute_write(
            "DELETE FROM personnel_competences WHERE id = %s",
            (assignment_id,), return_lastrowid=False
        )

        log_hist(
            action="RETRAIT_COMPETENCE",
            table_name="personnel_competences",
            record_id=assignment_id,
            description=f"Compétence '{info['libelle']}' retirée du personnel {info['personnel_id']}",
            operateur_id=info['personnel_id']
        )

        return True, "Compétence retirée"

    except Exception as e:
        logger.exception(f"Erreur remove_assignment: {e}")
        return False, "Erreur lors du retrait"


# ============================================================
# UTILITAIRES
# ============================================================

def get_competences_expirant_bientot(jours: int = 30) -> List[Dict]:
    """
    Récupère toutes les compétences qui expirent dans les N prochains jours.

    Args:
        jours: Nombre de jours à vérifier

    Returns:
        Liste des assignations qui expirent bientôt
    """
    try:
        return QueryExecutor.fetch_all(
            """SELECT
                   pc.id as assignment_id,
                   pc.personnel_id,
                   pc.date_expiration,
                   p.nom, p.prenom,
                   c.libelle as competence,
                   c.categorie,
                   DATEDIFF(pc.date_expiration, CURDATE()) as jours_restants
               FROM personnel_competences pc
               JOIN personnel p ON pc.personnel_id = p.id
               JOIN competences_catalogue c ON pc.competence_id = c.id
               WHERE pc.date_expiration IS NOT NULL
                 AND pc.date_expiration BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
                 AND p.statut = 'ACTIF'
               ORDER BY pc.date_expiration""",
            (jours,), dictionary=True
        )

    except Exception as e:
        logger.exception(f"Erreur get_competences_expirant_bientot: {e}")
        return []


def get_competences_expirees() -> List[Dict]:
    """
    Récupère toutes les compétences expirées pour le personnel actif.

    Returns:
        Liste des assignations expirées
    """
    try:
        return QueryExecutor.fetch_all(
            """SELECT
                   pc.id as assignment_id,
                   pc.personnel_id,
                   pc.date_expiration,
                   p.nom, p.prenom,
                   c.libelle as competence,
                   c.categorie,
                   DATEDIFF(CURDATE(), pc.date_expiration) as jours_expires
               FROM personnel_competences pc
               JOIN personnel p ON pc.personnel_id = p.id
               JOIN competences_catalogue c ON pc.competence_id = c.id
               WHERE pc.date_expiration IS NOT NULL
                 AND pc.date_expiration < CURDATE()
                 AND p.statut = 'ACTIF'
               ORDER BY pc.date_expiration DESC""",
            dictionary=True
        )

    except Exception as e:
        logger.exception(f"Erreur get_competences_expirees: {e}")
        return []


def calculer_date_expiration(date_acquisition: date, duree_validite_mois: int) -> date:
    """
    Calcule la date d'expiration à partir de la date d'acquisition et la durée de validité.

    Args:
        date_acquisition: Date d'acquisition
        duree_validite_mois: Durée de validité en mois

    Returns:
        Date d'expiration calculée
    """
    from dateutil.relativedelta import relativedelta
    return date_acquisition + relativedelta(months=duree_validite_mois)
