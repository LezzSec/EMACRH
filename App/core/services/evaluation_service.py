"""
Service de gestion des evaluations de polyvalence
Fournit les fonctions pour recuperer les evaluations en retard et a venir

✅ OPTIMISATIONS APPLIQUÉES:
- Monitoring des requêtes clés (détection régressions)
- Logs DB optimisés (async, non-bloquant)
- DTOs typés pour robustesse (EvaluationResume, Polyvalence)
"""

from datetime import date, timedelta
from typing import List, Dict, Optional

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

from infrastructure.config.performance_monitor import monitor_query
from core.services.permission_manager import require
from core.models import EvaluationResume, StatistiquesEvaluations


@monitor_query('Get Evaluations En Retard')
def get_evaluations_en_retard() -> List[Dict]:
    """
    Recupere toutes les evaluations en retard (date passee)
    Triees par urgence (plus de retard en premier)

    Returns:
        List[Dict]: Liste des evaluations en retard avec informations employe et poste
    """
    return QueryExecutor.fetch_all("""
        SELECT
            p.id as polyvalence_id,
            p.personnel_id,
            pers.nom,
            pers.prenom,
            pers.matricule,
            p.poste_id,
            pos.poste_code,
            a.nom as nom_atelier,
            p.niveau,
            p.date_evaluation,
            p.prochaine_evaluation,
            DATEDIFF(CURDATE(), p.prochaine_evaluation) as jours_retard
        FROM polyvalence p
        JOIN personnel pers ON p.personnel_id = pers.id
        JOIN postes pos ON p.poste_id = pos.id
        LEFT JOIN atelier a ON pos.atelier_id = a.id
        WHERE pers.statut = 'ACTIF'
          AND p.prochaine_evaluation < CURDATE()
        ORDER BY jours_retard DESC, p.prochaine_evaluation ASC
    """, dictionary=True)


@monitor_query('Get Prochaines Evaluations')
def get_prochaines_evaluations(jours: int = 30) -> List[Dict]:
    """
    Recupere les evaluations a venir dans les N prochains jours

    Args:
        jours (int): Nombre de jours a regarder en avant (defaut: 30)

    Returns:
        List[Dict]: Liste des evaluations a venir
    """
    date_limite = date.today() + timedelta(days=jours)

    return QueryExecutor.fetch_all("""
        SELECT
            p.id as polyvalence_id,
            p.personnel_id,
            pers.nom,
            pers.prenom,
            pers.matricule,
            p.poste_id,
            pos.poste_code,
            a.nom as nom_atelier,
            p.niveau,
            p.date_evaluation,
            p.prochaine_evaluation,
            DATEDIFF(p.prochaine_evaluation, CURDATE()) as jours_restants
        FROM polyvalence p
        JOIN personnel pers ON p.personnel_id = pers.id
        JOIN postes pos ON p.poste_id = pos.id
        LEFT JOIN atelier a ON pos.atelier_id = a.id
        WHERE pers.statut = 'ACTIF'
          AND p.prochaine_evaluation BETWEEN CURDATE() AND %s
        ORDER BY p.prochaine_evaluation ASC
    """, (date_limite,), dictionary=True)


@monitor_query('Get Evaluations Par Operateur')
def get_evaluations_par_operateur(operateur_id: int) -> List[Dict]:
    """
    Recupere toutes les evaluations d'un operateur

    Args:
        operateur_id (int): ID de l'operateur

    Returns:
        List[Dict]: Liste des evaluations de l'operateur
    """
    return QueryExecutor.fetch_all("""
        SELECT
            p.id as polyvalence_id,
            p.poste_id,
            pos.poste_code,
            a.nom as nom_atelier,
            p.niveau,
            p.date_evaluation,
            p.prochaine_evaluation,
            CASE
                WHEN p.prochaine_evaluation < CURDATE() THEN 'RETARD'
                WHEN p.prochaine_evaluation <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 'URGENT'
                ELSE 'OK'
            END as statut
        FROM polyvalence p
        JOIN postes pos ON p.poste_id = pos.id
        LEFT JOIN atelier a ON pos.atelier_id = a.id
        WHERE p.personnel_id = %s
        ORDER BY p.prochaine_evaluation ASC
    """, (operateur_id,), dictionary=True)


def mettre_a_jour_evaluation(polyvalence_id: int, nouveau_niveau: int,
                             date_evaluation: date, prochaine_evaluation: date) -> bool:
    """
    Met a jour une evaluation de polyvalence

    Args:
        polyvalence_id (int): ID de l'enregistrement polyvalence
        nouveau_niveau (int): Nouveau niveau de competence (1-4)
        date_evaluation (date): Date de l'evaluation
        prochaine_evaluation (date): Date de la prochaine evaluation

    Returns:
        bool: True si succes, False sinon

    Raises:
        PermissionError: Si l'utilisateur n'a pas la permission production.evaluations.edit
    """
    require('production.evaluations.edit')

    if nouveau_niveau not in [1, 2, 3, 4]:
        return False

    try:
        # Récupérer les anciennes valeurs pour le log
        ancien = QueryExecutor.fetch_one(
            "SELECT personnel_id, poste_id, niveau, date_evaluation FROM polyvalence WHERE id = %s",
            (polyvalence_id,),
            dictionary=True
        )
        operateur_id = ancien['personnel_id'] if ancien else None
        poste_id = ancien['poste_id'] if ancien else None
        ancien_niveau = ancien['niveau'] if ancien else None
        ancienne_date = ancien['date_evaluation'] if ancien else None

        QueryExecutor.execute_write("""
            UPDATE polyvalence
            SET niveau = %s,
                date_evaluation = %s,
                prochaine_evaluation = %s
            WHERE id = %s
        """, (nouveau_niveau, date_evaluation, prochaine_evaluation, polyvalence_id))

        # Archiver dans historique_polyvalence
        try:
            from core.services.polyvalence_logger import log_polyvalence_action
            log_polyvalence_action(
                action_type='MODIFICATION',
                operateur_id=operateur_id,
                poste_id=poste_id,
                polyvalence_id=polyvalence_id,
                ancien_niveau=ancien_niveau,
                nouveau_niveau=nouveau_niveau,
                ancienne_date_evaluation=ancienne_date,
                nouvelle_date_evaluation=date_evaluation,
            )
        except Exception as _e:
            logger.warning(f"Erreur archivage historique_polyvalence: {_e}")

        return True

    except Exception as e:
        logger.error(f"Erreur lors de la mise a jour de l'evaluation : {e}")
        return False


@monitor_query('Get Statistiques Evaluations')
def get_statistiques_evaluations() -> Dict:
    """
    Recupere des statistiques sur les evaluations

    Returns:
        Dict: Dictionnaire contenant les statistiques
    """
    stats = {}

    # Total d'evaluations actives
    stats['total'] = QueryExecutor.fetch_scalar("""
        SELECT COUNT(*) FROM polyvalence p
        JOIN personnel pers ON p.personnel_id = pers.id
        WHERE pers.statut = 'ACTIF'
    """, default=0)

    # Evaluations en retard
    stats['en_retard'] = QueryExecutor.fetch_scalar("""
        SELECT COUNT(*) FROM polyvalence p
        JOIN personnel pers ON p.personnel_id = pers.id
        WHERE pers.statut = 'ACTIF'
          AND p.prochaine_evaluation < CURDATE()
    """, default=0)

    # Evaluations a venir (30 jours)
    stats['a_venir_30j'] = QueryExecutor.fetch_scalar("""
        SELECT COUNT(*) FROM polyvalence p
        JOIN personnel pers ON p.personnel_id = pers.id
        WHERE pers.statut = 'ACTIF'
          AND p.prochaine_evaluation BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
    """, default=0)

    # Repartition par niveau
    stats['par_niveau'] = QueryExecutor.fetch_all("""
        SELECT niveau, COUNT(*) as count
        FROM polyvalence p
        JOIN personnel pers ON p.personnel_id = pers.id
        WHERE pers.statut = 'ACTIF'
        GROUP BY niveau
        ORDER BY niveau
    """, dictionary=True)

    return stats


# ===========================
# MÉTHODES TYPÉES (DTOs)
# ===========================
# Ces méthodes retournent des dataclasses au lieu de dicts bruts
# Avantages : typage fort, autocomplétion IDE, validation

@monitor_query('Get Evaluations En Retard (Typed)')
def get_evaluations_en_retard_typed() -> List[EvaluationResume]:
    """
    Version typée de get_evaluations_en_retard().
    Retourne des objets EvaluationResume au lieu de dicts.

    Returns:
        List[EvaluationResume]: Liste typée des évaluations en retard

    Example:
        evaluations = get_evaluations_en_retard_typed()
        for eval in evaluations:
            print(f"{eval.operateur_nom_complet} - {eval.label_poste}")
            if eval.est_en_retard:
                print(f"  ⚠️ {eval.jours_retard} jours de retard")
    """
    rows = get_evaluations_en_retard()
    return [
        EvaluationResume(
            polyvalence_id=row['polyvalence_id'],
            operateur_id=row['personnel_id'],
            operateur_nom=row['nom'],
            operateur_prenom=row['prenom'],
            poste_code=row['poste_code'],
            poste_nom=row.get('nom_atelier'),
            niveau=row['niveau'],
            prochaine_evaluation=row['prochaine_evaluation'],
            jours_retard=row.get('jours_retard', 0)
        )
        for row in rows
    ]


@monitor_query('Get Prochaines Evaluations (Typed)')
def get_prochaines_evaluations_typed(jours: int = 30) -> List[EvaluationResume]:
    """
    Version typée de get_prochaines_evaluations().

    Args:
        jours: Nombre de jours à regarder en avant

    Returns:
        List[EvaluationResume]: Liste typée des évaluations à venir
    """
    rows = get_prochaines_evaluations(jours)
    return [
        EvaluationResume(
            polyvalence_id=row['polyvalence_id'],
            operateur_id=row['personnel_id'],
            operateur_nom=row['nom'],
            operateur_prenom=row['prenom'],
            poste_code=row['poste_code'],
            poste_nom=row.get('nom_atelier'),
            niveau=row['niveau'],
            prochaine_evaluation=row['prochaine_evaluation'],
            jours_retard=-row.get('jours_restants', 0)  # Négatif = à venir
        )
        for row in rows
    ]


def get_statistiques_evaluations_typed() -> StatistiquesEvaluations:
    """
    Version typée de get_statistiques_evaluations().

    Returns:
        StatistiquesEvaluations: Objet typé avec les statistiques
    """
    stats = get_statistiques_evaluations()
    return StatistiquesEvaluations(
        total=stats.get('total', 0),
        en_retard=stats.get('en_retard', 0),
        a_venir_30j=stats.get('a_venir_30j', 0)
    )


# ===========================
# MÉTHODES POUR DetailOperateurDialog
# ===========================

def get_operateurs_avec_stats_polyvalences() -> List[tuple]:
    """
    Liste des opérateurs actifs avec leurs statistiques de polyvalences.
    Retourne uniquement les opérateurs ayant au moins une polyvalence.
    """
    return QueryExecutor.fetch_all("""
        SELECT
            p.id,
            p.nom,
            p.prenom,
            p.matricule,
            COUNT(poly.id) as total_poly,
            SUM(CASE WHEN poly.niveau = 4 THEN 1 ELSE 0 END) as n4,
            SUM(CASE WHEN poly.niveau = 3 THEN 1 ELSE 0 END) as n3,
            SUM(CASE WHEN poly.niveau = 2 THEN 1 ELSE 0 END) as n2,
            SUM(CASE WHEN poly.niveau = 1 THEN 1 ELSE 0 END) as n1,
            SUM(
                CASE
                    WHEN poly.prochaine_evaluation IS NULL THEN 1
                    WHEN poly.prochaine_evaluation BETWEEN CURDATE()
                         AND DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 1
                    ELSE 0
                END
            ) as a_planifier,
            SUM(
                CASE WHEN poly.prochaine_evaluation < CURDATE() THEN 1 ELSE 0 END
            ) as retard
        FROM personnel p
        INNER JOIN polyvalence poly ON poly.personnel_id = p.id
        WHERE p.statut = 'ACTIF'
        GROUP BY p.id, p.nom, p.prenom, p.matricule
        HAVING COUNT(poly.id) > 0
        ORDER BY p.nom, p.prenom
    """)


def get_postes_liste() -> List[Dict]:
    """Retourne la liste de tous les postes (id, poste_code) triés par code."""
    return QueryExecutor.fetch_all(
        "SELECT id, poste_code FROM postes ORDER BY poste_code",
        dictionary=True
    )


def get_polyvalence_par_id(poly_id: int) -> Optional[Dict]:
    """Retourne les données complètes d'une polyvalence par son ID."""
    return QueryExecutor.fetch_one(
        """SELECT id, personnel_id, poste_id, niveau, date_evaluation, prochaine_evaluation
           FROM polyvalence WHERE id = %s""",
        (poly_id,),
        dictionary=True
    )


def get_stats_polyvalence_operateur(operateur_id: int) -> Optional[Dict]:
    """Stats niveaux/retard/à planifier pour un opérateur."""
    return QueryExecutor.fetch_one("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN niveau = 4 THEN 1 ELSE 0 END) as n4,
               SUM(CASE WHEN niveau = 3 THEN 1 ELSE 0 END) as n3,
               SUM(CASE WHEN niveau = 2 THEN 1 ELSE 0 END) as n2,
               SUM(CASE WHEN niveau = 1 THEN 1 ELSE 0 END) as n1,
               SUM(CASE WHEN prochaine_evaluation < CURDATE() THEN 1 ELSE 0 END) as retard,
               SUM(CASE WHEN prochaine_evaluation BETWEEN CURDATE()
                        AND DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) as a_planifier
        FROM polyvalence
        WHERE personnel_id = %s
    """, (operateur_id,), dictionary=True)


def has_operateur_deja_eu_niveau_1(
    operateur_id: int,
    old_niveau: int = None,
    exclude_polyvalence_id: int = None,
    exclude_poste_id: int = None,
) -> bool:
    """
    Vérifie si l'opérateur a déjà eu une expérience niveau 1 par le passé.

    Retourne True si ce n'est PAS la première fois que cet opérateur passe au
    niveau 1, ce qui signifie que les documents NOUVEL_OPERATEUR (consignes
    générales, formation initiale) n'ont pas besoin d'être réimprimés.

    Logique :
    1. Si ``old_niveau`` est fourni et non None → l'opérateur avait déjà un
       niveau sur ce poste → documents déjà reçus.
    2. Sinon, cherche d'autres polyvalences actives (autres postes).
    3. Enfin, consulte historique_polyvalence pour tout antécédent.

    Args:
        operateur_id: ID de l'opérateur.
        old_niveau: Niveau AVANT la modification en cours (None = nouvel enregistrement).
        exclude_polyvalence_id: ID de la polyvalence venant d'être mise à jour (à exclure).
        exclude_poste_id: ID du poste venant d'être inséré (à exclure, pour INSERT).

    Returns:
        True si l'opérateur a déjà été niveau 1 ailleurs / auparavant.
    """
    # 1. Le poste avait déjà un niveau enregistré → formation déjà effectuée
    if old_niveau is not None:
        return True

    # 2. Autres polyvalences actives (hors enregistrement courant)
    params: list = [operateur_id]
    exclude_clause = ""
    if exclude_polyvalence_id is not None:
        exclude_clause = " AND id != %s"
        params.append(exclude_polyvalence_id)
    elif exclude_poste_id is not None:
        exclude_clause = " AND poste_id != %s"
        params.append(exclude_poste_id)

    count_other = QueryExecutor.fetch_scalar(
        f"SELECT COUNT(*) FROM polyvalence WHERE personnel_id = %s{exclude_clause}",
        tuple(params),
        default=0,
    )
    if count_other > 0:
        return True

    # 3. Antécédents dans historique_polyvalence (modifications passées)
    count_hist = QueryExecutor.fetch_scalar(
        "SELECT COUNT(*) FROM historique_polyvalence WHERE personnel_id = %s",
        (operateur_id,),
        default=0,
    )
    return count_hist > 0


def get_polyvalences_actuelles_operateur(operateur_id: int) -> List[Dict]:
    """Polyvalences actuelles (dernière par poste) pour un opérateur."""
    return QueryExecutor.fetch_all("""
        SELECT poly.id,
               poly.poste_id,
               ps.poste_code,
               poly.niveau,
               poly.date_evaluation,
               poly.prochaine_evaluation
        FROM polyvalence poly
        JOIN postes ps ON poly.poste_id = ps.id
        WHERE poly.personnel_id = %s
          AND poly.id = (
              SELECT MAX(p2.id)
              FROM polyvalence p2
              WHERE p2.personnel_id = poly.personnel_id
                AND p2.poste_id = poly.poste_id
          )
        ORDER BY ps.poste_code
    """, (operateur_id,), dictionary=True)



def get_historique_polyvalence_operateur(operateur_id: int) -> List[Dict]:
    """Historique complet des modifications de polyvalence pour un opérateur."""
    return QueryExecutor.fetch_all("""
        SELECT
            hp.id,
            hp.date_action,
            hp.action_type,
            p.poste_code,
            hp.ancien_niveau,
            hp.nouveau_niveau,
            hp.nouvelle_date_evaluation AS date_eval_affiche,
            hp.commentaire
        FROM historique_polyvalence hp
        LEFT JOIN postes p ON hp.poste_id = p.id
        WHERE hp.personnel_id = %s
        ORDER BY hp.date_action DESC
    """, (operateur_id,), dictionary=True)


def importer_ancienne_polyvalence(operateur_id: int, poste_id: int, niveau: int,
                                   date_eval, date_prochaine,
                                   commentaire: str = None) -> bool:
    """
    Importe une ancienne polyvalence (IMPORT_MANUEL) de façon atomique :
    - INSERT dans historique_polyvalence
    - INSERT/UPDATE dans polyvalence
    """
    try:
        from infrastructure.db.configbd import DatabaseConnection
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO historique_polyvalence
                (personnel_id, poste_id, action_type, nouveau_niveau,
                 nouvelle_date_evaluation, commentaire, date_action)
                VALUES (%s, %s, 'IMPORT_MANUEL', %s, %s, %s, NOW())
            """, (operateur_id, poste_id, niveau, date_eval, commentaire or None))

            cur.execute("""
                INSERT INTO polyvalence
                (personnel_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    niveau = VALUES(niveau),
                    date_evaluation = VALUES(date_evaluation),
                    prochaine_evaluation = VALUES(prochaine_evaluation)
            """, (operateur_id, poste_id, niveau, date_eval, date_prochaine))

        from infrastructure.logging.optimized_db_logger import log_hist
        log_hist(
            action="IMPORT_MANUEL",
            table_name="polyvalence",
            record_id=None,
            description=f"Import manuel polyvalence N{niveau}, date éval: {date_eval}",
            operateur_id=operateur_id,
            poste_id=poste_id
        )
        return True

    except Exception as e:
        logger.exception(f"Erreur import ancienne polyvalence opérateur {operateur_id}: {e}")
        return False


def update_date_evaluation_polyvalence(poly_id: int, new_date_eval, prochaine_eval) -> bool:
    """
    Met à jour date_evaluation + prochaine_evaluation d'une polyvalence
    (sans changer le niveau). Utilisé quand l'utilisateur modifie la date dans le tableau.
    """
    try:
        ancien = QueryExecutor.fetch_one(
            "SELECT personnel_id, poste_id, date_evaluation FROM polyvalence WHERE id = %s",
            (poly_id,), dictionary=True
        )
        operateur_id = ancien['personnel_id'] if ancien else None
        poste_id = ancien['poste_id'] if ancien else None
        ancienne_date = ancien['date_evaluation'] if ancien else None

        QueryExecutor.execute_write("""
            UPDATE polyvalence
            SET date_evaluation = %s, prochaine_evaluation = %s
            WHERE id = %s
        """, (new_date_eval, prochaine_eval, poly_id))

        from infrastructure.logging.optimized_db_logger import log_hist
        log_hist(
            action="UPDATE",
            table_name="polyvalence",
            record_id=poly_id,
            description=(f"Date évaluation modifiée: {ancienne_date} → {new_date_eval}, "
                         f"prochaine éval: {prochaine_eval}"),
            operateur_id=operateur_id,
            poste_id=poste_id
        )
        return True

    except Exception as e:
        logger.exception(f"Erreur update date évaluation polyvalence {poly_id}: {e}")
        return False


def update_date_champ_polyvalence(poly_id: int, field: str, new_date) -> bool:
    """
    Met à jour un champ date d'une polyvalence (date_evaluation ou prochaine_evaluation).
    Whitelist de champs pour prévenir les injections SQL.
    """
    import json
    _ALLOWED = {
        'date_evaluation': (
            "SELECT pv.date_evaluation, p.nom, p.prenom, po.poste_code, pv.personnel_id, po.id "
            "FROM polyvalence pv JOIN personnel p ON p.id = pv.personnel_id "
            "JOIN postes po ON po.id = pv.poste_id WHERE pv.id = %s",
            "UPDATE polyvalence SET date_evaluation = %s WHERE id = %s",
            "Date d'évaluation"
        ),
        'prochaine_evaluation': (
            "SELECT pv.prochaine_evaluation, p.nom, p.prenom, po.poste_code, pv.personnel_id, po.id "
            "FROM polyvalence pv JOIN personnel p ON p.id = pv.personnel_id "
            "JOIN postes po ON po.id = pv.poste_id WHERE pv.id = %s",
            "UPDATE polyvalence SET prochaine_evaluation = %s WHERE id = %s",
            "Prochaine évaluation"
        ),
    }
    if field not in _ALLOWED:
        raise ValueError(f"Champ non autorisé: {field}")

    query_select, query_update, field_display = _ALLOWED[field]

    try:
        result = QueryExecutor.fetch_one(query_select, (poly_id,))
        old_date = result[0] if result else None
        nom = result[1] if result else None
        prenom = result[2] if result else None
        poste_code = result[3] if result else None
        operateur_id = result[4] if result else None
        poste_id = result[5] if result else None

        QueryExecutor.execute_write(query_update, (new_date, poly_id))

        from infrastructure.logging.optimized_db_logger import log_hist
        log_hist(
            action="UPDATE",
            table_name="polyvalence",
            record_id=poly_id,
            operateur_id=operateur_id,
            poste_id=poste_id,
            description=json.dumps({
                "operateur": f"{prenom} {nom}",
                "poste": poste_code,
                "field": field_display,
                "old_value": str(old_date) if old_date else "Non défini",
                "new_value": str(new_date),
                "type": "modification_date_evaluation"
            }, ensure_ascii=False),
            source="service/evaluation_service"
        )
        return True

    except Exception as e:
        logger.exception(f"Erreur update champ {field} polyvalence {poly_id}: {e}")
        return False


def compter_polyvalences_operateur(operateur_id: int) -> int:
    """Retourne le nombre de polyvalences actives d'un opérateur."""
    return QueryExecutor.fetch_scalar(
        "SELECT COUNT(*) FROM polyvalence WHERE personnel_id = %s",
        (operateur_id,)
    ) or 0


def supprimer_polyvalence_par_id(poly_id: int) -> bool:
    """
    Supprime une polyvalence par son ID et enregistre l'action dans les historiques.
    Équivalent à ce que fait la grille de polyvalence quand la cellule est vidée.
    """
    import json

    # Récupérer les infos avant suppression pour les logs
    poly_info = QueryExecutor.fetch_one(
        """SELECT pv.id, pv.personnel_id, pv.poste_id, pv.niveau,
                  pv.date_evaluation, pv.prochaine_evaluation,
                  p.nom, p.prenom, po.poste_code
           FROM polyvalence pv
           JOIN personnel p ON p.id = pv.personnel_id
           JOIN postes po ON po.id = pv.poste_id
           WHERE pv.id = %s""",
        (poly_id,),
        dictionary=True
    )
    if not poly_info:
        logger.warning(f"supprimer_polyvalence_par_id: polyvalence {poly_id} introuvable")
        return False

    try:
        QueryExecutor.execute_write("DELETE FROM polyvalence WHERE id = %s", (poly_id,))

        from infrastructure.logging.optimized_db_logger import log_hist
        log_hist(
            action="DELETE",
            table_name="polyvalence",
            record_id=poly_id,
            operateur_id=poly_info['personnel_id'],
            poste_id=poly_info['poste_id'],
            description=json.dumps({
                "operateur": f"{poly_info['prenom']} {poly_info['nom']}",
                "poste": poly_info['poste_code'],
                "niveau": poly_info['niveau'],
                "type": "suppression_polyvalence"
            }, ensure_ascii=False),
            source="service/evaluation_service"
        )

        try:
            from core.services.polyvalence_logger import log_polyvalence_action
            log_polyvalence_action(
                action_type='SUPPRESSION',
                operateur_id=poly_info['personnel_id'],
                poste_id=poly_info['poste_id'],
                ancien_niveau=poly_info['niveau'],
                ancienne_date_evaluation=poly_info['date_evaluation'],
                source='GUI',
            )
        except Exception as _e:
            logger.warning(f"Erreur archivage historique_polyvalence: {_e}")

        return True

    except Exception as e:
        logger.exception(f"Erreur suppression polyvalence {poly_id}: {e}")
        return False
