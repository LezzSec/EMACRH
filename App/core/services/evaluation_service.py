"""
Service de gestion des evaluations de polyvalence
Fournit les fonctions pour recuperer les evaluations en retard et a venir

✅ OPTIMISATIONS APPLIQUÉES:
- Monitoring des requêtes clés (détection régressions)
- Logs DB optimisés (async, non-bloquant)
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from core.db.configbd import DatabaseCursor, DatabaseConnection

# ✅ OPTIMISATIONS : Monitoring + Logs optimisés
from core.utils.performance_monitor import monitor_query
from core.services.optimized_db_logger import log_hist_async


@monitor_query('Get Evaluations En Retard')
def get_evaluations_en_retard() -> List[Dict]:
    """
    Recupere toutes les evaluations en retard (date passee)
    Triees par urgence (plus de retard en premier)

    Returns:
        List[Dict]: Liste des evaluations en retard avec informations employe et poste
    """
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT
                p.id as polyvalence_id,
                p.operateur_id,
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
            JOIN personnel pers ON p.operateur_id = pers.id
            JOIN postes pos ON p.poste_id = pos.id
            LEFT JOIN atelier a ON pos.atelier_id = a.id
            WHERE pers.statut = 'ACTIF'
              AND p.prochaine_evaluation < CURDATE()
            ORDER BY jours_retard DESC, p.prochaine_evaluation ASC
        """)

        return cur.fetchall()


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

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT
                p.id as polyvalence_id,
                p.operateur_id,
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
            JOIN personnel pers ON p.operateur_id = pers.id
            JOIN postes pos ON p.poste_id = pos.id
            LEFT JOIN atelier a ON pos.atelier_id = a.id
            WHERE pers.statut = 'ACTIF'
              AND p.prochaine_evaluation BETWEEN CURDATE() AND %s
            ORDER BY p.prochaine_evaluation ASC
        """, (date_limite,))

        return cur.fetchall()


@monitor_query('Get Evaluations Par Operateur')
def get_evaluations_par_operateur(operateur_id: int) -> List[Dict]:
    """
    Recupere toutes les evaluations d'un operateur

    Args:
        operateur_id (int): ID de l'operateur

    Returns:
        List[Dict]: Liste des evaluations de l'operateur
    """
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
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
            WHERE p.operateur_id = %s
            ORDER BY p.prochaine_evaluation ASC
        """, (operateur_id,))

        return cur.fetchall()


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
    """
    if nouveau_niveau not in [1, 2, 3, 4]:
        return False

    try:
        with DatabaseCursor() as cur:
            # Récupérer les anciennes valeurs pour le log
            cur.execute("SELECT operateur_id, poste_id, niveau, date_evaluation FROM polyvalence WHERE id = %s", (polyvalence_id,))
            ancien = cur.fetchone()
            operateur_id = ancien[0] if ancien else None
            poste_id = ancien[1] if ancien else None
            ancien_niveau = ancien[2] if ancien else None
            ancienne_date = ancien[3] if ancien else None

            cur.execute("""
                UPDATE polyvalence
                SET niveau = %s,
                    date_evaluation = %s,
                    prochaine_evaluation = %s
                WHERE id = %s
            """, (nouveau_niveau, date_evaluation, prochaine_evaluation, polyvalence_id))

            # Logger la modification
            from core.services.logger import log_hist
            log_hist(
                action="UPDATE",
                table_name="polyvalence",
                record_id=polyvalence_id,
                description=f"Évaluation mise à jour: N{ancien_niveau}→N{nouveau_niveau}, date: {ancienne_date}→{date_evaluation}, prochaine: {prochaine_evaluation}",
                operateur_id=operateur_id,
                poste_id=poste_id
            )

            return True

    except Exception as e:
        print(f"Erreur lors de la mise a jour de l'evaluation : {e}")
        return False


@monitor_query('Get Statistiques Evaluations')
def get_statistiques_evaluations() -> Dict:
    """
    Recupere des statistiques sur les evaluations

    Returns:
        Dict: Dictionnaire contenant les statistiques
    """
    stats = {}

    with DatabaseCursor(dictionary=True) as cur:
        # Total d'evaluations actives
        cur.execute("""
            SELECT COUNT(*) as total
            FROM polyvalence p
            JOIN personnel pers ON p.operateur_id = pers.id
            WHERE pers.statut = 'ACTIF'
        """)
        stats['total'] = cur.fetchone()['total']

        # Evaluations en retard
        cur.execute("""
            SELECT COUNT(*) as total
            FROM polyvalence p
            JOIN personnel pers ON p.operateur_id = pers.id
            WHERE pers.statut = 'ACTIF'
              AND p.prochaine_evaluation < CURDATE()
        """)
        stats['en_retard'] = cur.fetchone()['total']

        # Evaluations a venir (30 jours)
        cur.execute("""
            SELECT COUNT(*) as total
            FROM polyvalence p
            JOIN personnel pers ON p.operateur_id = pers.id
            WHERE pers.statut = 'ACTIF'
              AND p.prochaine_evaluation BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """)
        stats['a_venir_30j'] = cur.fetchone()['total']

        # Repartition par niveau
        cur.execute("""
            SELECT niveau, COUNT(*) as count
            FROM polyvalence p
            JOIN personnel pers ON p.operateur_id = pers.id
            WHERE pers.statut = 'ACTIF'
            GROUP BY niveau
            ORDER BY niveau
        """)
        stats['par_niveau'] = cur.fetchall()

    return stats
