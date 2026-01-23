# -*- coding: utf-8 -*-
"""
Service de logging pour les polyvalences
Enregistre automatiquement toutes les actions sur les polyvalences dans historique_polyvalence
"""

import json
import logging
from datetime import datetime

from core.db.configbd import get_connection

logger = logging.getLogger(__name__)


def log_polyvalence_action(
    action_type,
    operateur_id,
    poste_id,
    polyvalence_id=None,
    ancien_niveau=None,
    ancienne_date_evaluation=None,
    ancienne_prochaine_evaluation=None,
    ancien_statut=None,
    nouveau_niveau=None,
    nouvelle_date_evaluation=None,
    nouvelle_prochaine_evaluation=None,
    nouveau_statut=None,
    utilisateur=None,
    commentaire=None,
    source="SYSTEM",
    import_batch_id=None,
    metadata=None,
    date_action=None
):
    """
    Enregistre une action sur une polyvalence.

    Args:
        action_type (str): Type d'action ('AJOUT', 'MODIFICATION', 'SUPPRESSION', 'IMPORT_MANUEL')
        operateur_id (int): ID de l'opérateur
        poste_id (int): ID du poste
        polyvalence_id (int, optional): ID de la polyvalence (NULL si suppression ou import)
        ancien_niveau (int, optional): Niveau avant modification
        ancienne_date_evaluation (date, optional): Date évaluation avant modification
        ancienne_prochaine_evaluation (date, optional): Date prochaine éval avant modification
        ancien_statut (str, optional): Statut avant modification
        nouveau_niveau (int, optional): Niveau après modification
        nouvelle_date_evaluation (date, optional): Date évaluation après modification
        nouvelle_prochaine_evaluation (date, optional): Date prochaine éval après modification
        nouveau_statut (str, optional): Statut après modification
        utilisateur (str, optional): Utilisateur ayant effectué l'action
        commentaire (str, optional): Commentaire libre
        source (str): Source de l'action (SYSTEM, GUI, IMPORT_MANUEL, etc.)
        import_batch_id (str, optional): ID du lot d'import
        metadata (dict, optional): Métadonnées supplémentaires (stockées en JSON)
        date_action (datetime, optional): Date de l'action (par défaut: maintenant)

    Returns:
        int: ID de l'enregistrement créé dans historique_polyvalence
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Convertir metadata en JSON si fourni
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None

        # Utiliser la date actuelle si non fournie
        if date_action is None:
            date_action = datetime.now()

        query = """
            INSERT INTO historique_polyvalence (
                date_action,
                action_type,
                operateur_id,
                poste_id,
                polyvalence_id,
                ancien_niveau,
                ancienne_date_evaluation,
                ancienne_prochaine_evaluation,
                ancien_statut,
                nouveau_niveau,
                nouvelle_date_evaluation,
                nouvelle_prochaine_evaluation,
                nouveau_statut,
                utilisateur,
                commentaire,
                source,
                import_batch_id,
                metadata_json
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        cur.execute(query, (
            date_action,
            action_type,
            operateur_id,
            poste_id,
            polyvalence_id,
            ancien_niveau,
            ancienne_date_evaluation,
            ancienne_prochaine_evaluation,
            ancien_statut,
            nouveau_niveau,
            nouvelle_date_evaluation,
            nouvelle_prochaine_evaluation,
            nouveau_statut,
            utilisateur,
            commentaire,
            source,
            import_batch_id,
            metadata_json
        ))

        hist_id = cur.lastrowid
        conn.commit()

        return hist_id

    except Exception as e:
        conn.rollback()
        logger.error(f"Impossible d'enregistrer l'action polyvalence : {e}")
        raise
    finally:
        cur.close()
        conn.close()


def log_polyvalence_ajout(operateur_id, poste_id, polyvalence_id, niveau, date_evaluation, prochaine_evaluation, utilisateur=None, source="GUI"):
    """
    Enregistre l'ajout d'une polyvalence.

    Args:
        operateur_id (int): ID de l'opérateur
        poste_id (int): ID du poste
        polyvalence_id (int): ID de la polyvalence créée
        niveau (int): Niveau de compétence
        date_evaluation (date): Date de l'évaluation
        prochaine_evaluation (date): Date de la prochaine évaluation
        utilisateur (str, optional): Utilisateur ayant effectué l'action
        source (str): Source de l'action

    Returns:
        int: ID de l'enregistrement créé
    """
    return log_polyvalence_action(
        action_type='AJOUT',
        operateur_id=operateur_id,
        poste_id=poste_id,
        polyvalence_id=polyvalence_id,
        nouveau_niveau=niveau,
        nouvelle_date_evaluation=date_evaluation,
        nouvelle_prochaine_evaluation=prochaine_evaluation,
        utilisateur=utilisateur,
        source=source
    )


def log_polyvalence_modification(
    operateur_id, poste_id, polyvalence_id,
    ancien_niveau, ancienne_date_eval, ancienne_prochaine_eval,
    nouveau_niveau, nouvelle_date_eval, nouvelle_prochaine_eval,
    utilisateur=None, source="GUI"
):
    """
    Enregistre la modification d'une polyvalence.

    Args:
        operateur_id (int): ID de l'opérateur
        poste_id (int): ID du poste
        polyvalence_id (int): ID de la polyvalence
        ancien_niveau (int): Ancien niveau
        ancienne_date_eval (date): Ancienne date d'évaluation
        ancienne_prochaine_eval (date): Ancienne date prochaine évaluation
        nouveau_niveau (int): Nouveau niveau
        nouvelle_date_eval (date): Nouvelle date d'évaluation
        nouvelle_prochaine_eval (date): Nouvelle date prochaine évaluation
        utilisateur (str, optional): Utilisateur ayant effectué l'action
        source (str): Source de l'action

    Returns:
        int: ID de l'enregistrement créé
    """
    return log_polyvalence_action(
        action_type='MODIFICATION',
        operateur_id=operateur_id,
        poste_id=poste_id,
        polyvalence_id=polyvalence_id,
        ancien_niveau=ancien_niveau,
        ancienne_date_evaluation=ancienne_date_eval,
        ancienne_prochaine_evaluation=ancienne_prochaine_eval,
        nouveau_niveau=nouveau_niveau,
        nouvelle_date_evaluation=nouvelle_date_eval,
        nouvelle_prochaine_evaluation=nouvelle_prochaine_eval,
        utilisateur=utilisateur,
        source=source
    )


def log_polyvalence_suppression(operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation, utilisateur=None, source="GUI"):
    """
    Enregistre la suppression d'une polyvalence.

    Args:
        operateur_id (int): ID de l'opérateur
        poste_id (int): ID du poste
        niveau (int): Niveau de la polyvalence supprimée
        date_evaluation (date): Date de l'évaluation
        prochaine_evaluation (date): Date de la prochaine évaluation
        utilisateur (str, optional): Utilisateur ayant effectué l'action
        source (str): Source de l'action

    Returns:
        int: ID de l'enregistrement créé
    """
    return log_polyvalence_action(
        action_type='SUPPRESSION',
        operateur_id=operateur_id,
        poste_id=poste_id,
        polyvalence_id=None,  # Plus d'ID car supprimé
        ancien_niveau=niveau,
        ancienne_date_evaluation=date_evaluation,
        ancienne_prochaine_evaluation=prochaine_evaluation,
        utilisateur=utilisateur,
        source=source
    )


def get_historique_operateur(operateur_id, limit=None):
    """
    Récupère l'historique des polyvalences pour un opérateur.

    Args:
        operateur_id (int): ID de l'opérateur
        limit (int, optional): Nombre maximum d'enregistrements à retourner

    Returns:
        list: Liste des actions (dictionnaires)
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM v_historique_polyvalence_complet
            WHERE operateur_id = %s
            ORDER BY date_action DESC
        """

        # ✅ SÉCURITÉ: Validation stricte de LIMIT (MySQL ne supporte pas les paramètres pour LIMIT)
        if limit:
            try:
                limit_val = int(limit)
                if limit_val <= 0 or limit_val > 10000:  # Protection contre valeurs extrêmes
                    raise ValueError("LIMIT doit être entre 1 et 10000")
                query += f" LIMIT {limit_val}"
            except (ValueError, TypeError) as e:
                raise ValueError(f"Valeur LIMIT invalide: {e}")

        cur.execute(query, (operateur_id,))
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def get_historique_poste(operateur_id, poste_id, limit=None):
    """
    Récupère l'historique d'un opérateur sur un poste spécifique.

    Args:
        operateur_id (int): ID de l'opérateur
        poste_id (int): ID du poste
        limit (int, optional): Nombre maximum d'enregistrements

    Returns:
        list: Liste des actions
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM v_historique_polyvalence_complet
            WHERE operateur_id = %s AND poste_id = %s
            ORDER BY date_action DESC
        """

        # ✅ SÉCURITÉ: Validation stricte de LIMIT
        if limit:
            try:
                limit_val = int(limit)
                if limit_val <= 0 or limit_val > 10000:
                    raise ValueError("LIMIT doit être entre 1 et 10000")
                query += f" LIMIT {limit_val}"
            except (ValueError, TypeError) as e:
                raise ValueError(f"Valeur LIMIT invalide: {e}")

        cur.execute(query, (operateur_id, poste_id))
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def get_derniere_action_poste(operateur_id, poste_id):
    """
    Récupère la dernière action sur un poste pour un opérateur.

    Args:
        operateur_id (int): ID de l'opérateur
        poste_id (int): ID du poste

    Returns:
        dict or None: Dernière action ou None si aucune
    """
    results = get_historique_poste(operateur_id, poste_id, limit=1)
    return results[0] if results else None


def get_statistiques_operateur(operateur_id):
    """
    Récupère des statistiques sur l'historique d'un opérateur.

    Args:
        operateur_id (int): ID de l'opérateur

    Returns:
        dict: Statistiques (nb total, nb par type, postes touchés, etc.)
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT
                COUNT(*) as total_actions,
                SUM(CASE WHEN action_type = 'AJOUT' THEN 1 ELSE 0 END) as nb_ajouts,
                SUM(CASE WHEN action_type = 'MODIFICATION' THEN 1 ELSE 0 END) as nb_modifications,
                SUM(CASE WHEN action_type = 'SUPPRESSION' THEN 1 ELSE 0 END) as nb_suppressions,
                SUM(CASE WHEN action_type = 'IMPORT_MANUEL' THEN 1 ELSE 0 END) as nb_imports,
                COUNT(DISTINCT poste_id) as nb_postes_touches,
                MIN(date_action) as premiere_action,
                MAX(date_action) as derniere_action
            FROM historique_polyvalence
            WHERE operateur_id = %s
        """

        cur.execute(query, (operateur_id,))
        return cur.fetchone()

    finally:
        cur.close()
        conn.close()
