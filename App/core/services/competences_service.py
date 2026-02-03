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
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

from core.db.configbd import DatabaseCursor, DatabaseConnection
from core.services.logger import log_hist

logger = logging.getLogger(__name__)

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
        with DatabaseCursor(dictionary=True) as cur:
            if actif_only:
                cur.execute("""
                    SELECT id, code, libelle, description, categorie,
                           duree_validite_mois, actif, created_at, updated_at
                    FROM competences_catalogue
                    WHERE actif = 1
                    ORDER BY categorie, libelle
                """)
            else:
                cur.execute("""
                    SELECT id, code, libelle, description, categorie,
                           duree_validite_mois, actif, created_at, updated_at
                    FROM competences_catalogue
                    ORDER BY categorie, libelle
                """)
            return cur.fetchall()
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
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT id, code, libelle, description, categorie,
                       duree_validite_mois, actif, created_at, updated_at
                FROM competences_catalogue
                WHERE id = %s
            """, (competence_id,))
            return cur.fetchone()
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
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT DISTINCT categorie
                FROM competences_catalogue
                WHERE categorie IS NOT NULL AND actif = 1
                ORDER BY categorie
            """)
            return [row['categorie'] for row in cur.fetchall()]
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
    if not code or not code.strip():
        return False, "Le code est obligatoire", None
    if not libelle or not libelle.strip():
        return False, "Le libellé est obligatoire", None

    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO competences_catalogue
                (code, libelle, categorie, description, duree_validite_mois)
                VALUES (%s, %s, %s, %s, %s)
            """, (code.strip().upper(), libelle.strip(), categorie, description, duree_validite_mois))

            competence_id = cur.lastrowid
            conn.commit()

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
    updates = {k: v for k, v in kwargs.items() if k in ALLOWED_CATALOGUE_FIELDS}

    if not updates:
        return False, "Aucun champ valide à mettre à jour"

    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            # Construction sécurisée de la requête
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [competence_id]

            cur.execute(f"""
                UPDATE competences_catalogue
                SET {set_clause}
                WHERE id = %s
            """, values)

            conn.commit()

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
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            # Vérifier si des assignations existent
            cur.execute("""
                SELECT COUNT(*) as count FROM personnel_competences
                WHERE competence_id = %s
            """, (competence_id,))
            result = cur.fetchone()

            if result and result[0] > 0:
                # Soft delete si des assignations existent
                cur.execute("""
                    UPDATE competences_catalogue SET actif = 0 WHERE id = %s
                """, (competence_id,))
                msg = "Compétence désactivée (assignations existantes)"
            else:
                # Hard delete si aucune assignation
                cur.execute("""
                    DELETE FROM competences_catalogue WHERE id = %s
                """, (competence_id,))
                msg = "Compétence supprimée"

            conn.commit()

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
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
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
                ORDER BY c.categorie, c.libelle
            """, (personnel_id,))

            competences = cur.fetchall()

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
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor(dictionary=True)

            # Vérifier que la compétence existe
            cur.execute("SELECT libelle FROM competences_catalogue WHERE id = %s", (competence_id,))
            comp = cur.fetchone()
            if not comp:
                return False, "Compétence introuvable", None

            # Vérifier si déjà assignée
            cur.execute("""
                SELECT id FROM personnel_competences
                WHERE personnel_id = %s AND competence_id = %s
            """, (personnel_id, competence_id))

            if cur.fetchone():
                return False, "Cette compétence est déjà assignée à cette personne", None

            # Créer l'assignation
            cur.execute("""
                INSERT INTO personnel_competences
                (personnel_id, competence_id, date_acquisition, date_expiration, commentaire, document_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (personnel_id, competence_id, date_acquisition, date_expiration, commentaire, document_id))

            assignment_id = cur.lastrowid
            conn.commit()

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
    updates = {k: v for k, v in kwargs.items() if k in ALLOWED_ASSIGNMENT_FIELDS}

    if not updates:
        return False, "Aucun champ valide à mettre à jour"

    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [assignment_id]

            cur.execute(f"""
                UPDATE personnel_competences
                SET {set_clause}
                WHERE id = %s
            """, values)

            conn.commit()

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
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor(dictionary=True)

            # Récupérer les infos pour le log
            cur.execute("""
                SELECT pc.personnel_id, c.libelle
                FROM personnel_competences pc
                JOIN competences_catalogue c ON pc.competence_id = c.id
                WHERE pc.id = %s
            """, (assignment_id,))
            info = cur.fetchone()

            if not info:
                return False, "Assignation introuvable"

            cur.execute("DELETE FROM personnel_competences WHERE id = %s", (assignment_id,))
            conn.commit()

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
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    pc.id as assignment_id,
                    pc.personnel_id,
                    pc.date_expiration,
                    p.nom,
                    p.prenom,
                    c.libelle as competence,
                    c.categorie,
                    DATEDIFF(pc.date_expiration, CURDATE()) as jours_restants
                FROM personnel_competences pc
                JOIN personnel p ON pc.personnel_id = p.id
                JOIN competences_catalogue c ON pc.competence_id = c.id
                WHERE pc.date_expiration IS NOT NULL
                  AND pc.date_expiration BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
                  AND p.statut = 'ACTIF'
                ORDER BY pc.date_expiration
            """, (jours,))

            return cur.fetchall()

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
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    pc.id as assignment_id,
                    pc.personnel_id,
                    pc.date_expiration,
                    p.nom,
                    p.prenom,
                    c.libelle as competence,
                    c.categorie,
                    DATEDIFF(CURDATE(), pc.date_expiration) as jours_expires
                FROM personnel_competences pc
                JOIN personnel p ON pc.personnel_id = p.id
                JOIN competences_catalogue c ON pc.competence_id = c.id
                WHERE pc.date_expiration IS NOT NULL
                  AND pc.date_expiration < CURDATE()
                  AND p.statut = 'ACTIF'
                ORDER BY pc.date_expiration DESC
            """)

            return cur.fetchall()

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
