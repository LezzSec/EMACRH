# -*- coding: utf-8 -*-
"""
StatistiquesService - Requêtes agrégées pour le tableau de bord statistiques.
Toutes les fonctions retournent des dicts/listes prêts à l'affichage.
"""

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Vue d'ensemble (KPIs)
# ---------------------------------------------------------------------------

def get_resume() -> dict:
    """Retourne les KPIs globaux : effectif actif, évaluations en retard,
    contrats expirant dans 30j, absences en attente ce mois."""
    try:
        effectif_actif = QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM personnel WHERE statut = 'ACTIF'"
        ) or 0

        evals_retard = QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM polyvalence WHERE prochaine_evaluation < CURDATE()"
        ) or 0

        contrats_30j = QueryExecutor.fetch_scalar(
            """SELECT COUNT(*) FROM contrat
               WHERE actif = 1 AND date_fin IS NOT NULL
               AND date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)"""
        ) or 0

        absences_mois = QueryExecutor.fetch_scalar(
            """SELECT COUNT(*) FROM demande_absence
               WHERE MONTH(date_debut) = MONTH(CURDATE())
               AND YEAR(date_debut) = YEAR(CURDATE())
               AND statut = 'VALIDEE'"""
        ) or 0

        mobilite_actifs = QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM personnel_mobilite WHERE actif = 1 AND date_fin IS NULL"
        ) or 0

        return {
            "effectif_actif": effectif_actif,
            "evals_retard": evals_retard,
            "contrats_30j": contrats_30j,
            "absences_mois": absences_mois,
            "mobilite_actifs": mobilite_actifs,
        }
    except Exception as e:
        logger.exception(f"get_resume: {e}")
        return {}


# ---------------------------------------------------------------------------
# Personnel
# ---------------------------------------------------------------------------

def get_stats_personnel() -> dict:
    """Effectifs par statut, catégorie, ancienneté."""
    try:
        par_statut = QueryExecutor.fetch_all(
            "SELECT statut, COUNT(*) AS nb FROM personnel GROUP BY statut ORDER BY statut",
            dictionary=True,
        ) or []

        par_categorie = QueryExecutor.fetch_all(
            """SELECT COALESCE(pi.categorie, '?') AS categorie, COUNT(*) AS nb
               FROM personnel p
               LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
               WHERE p.statut = 'ACTIF'
               GROUP BY pi.categorie ORDER BY categorie""",
            dictionary=True,
        ) or []

        par_anciennete = QueryExecutor.fetch_all(
            """SELECT
                SUM(CASE WHEN pi.date_entree IS NULL THEN 1 ELSE 0 END) AS inconnue,
                SUM(CASE WHEN TIMESTAMPDIFF(YEAR, pi.date_entree, CURDATE()) < 1 THEN 1 ELSE 0 END) AS moins_1_an,
                SUM(CASE WHEN TIMESTAMPDIFF(YEAR, pi.date_entree, CURDATE()) BETWEEN 1 AND 4 THEN 1 ELSE 0 END) AS de_1_a_5_ans,
                SUM(CASE WHEN TIMESTAMPDIFF(YEAR, pi.date_entree, CURDATE()) BETWEEN 5 AND 9 THEN 1 ELSE 0 END) AS de_5_a_10_ans,
                SUM(CASE WHEN TIMESTAMPDIFF(YEAR, pi.date_entree, CURDATE()) >= 10 THEN 1 ELSE 0 END) AS plus_10_ans
               FROM personnel p
               LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
               WHERE p.statut = 'ACTIF'""",
            dictionary=True,
        ) or []

        return {
            "par_statut": par_statut,
            "par_categorie": par_categorie,
            "par_anciennete": par_anciennete[0] if par_anciennete else {},
        }
    except Exception as e:
        logger.exception(f"get_stats_personnel: {e}")
        return {}


# ---------------------------------------------------------------------------
# Évaluations / Polyvalence
# ---------------------------------------------------------------------------

def get_stats_evaluations() -> dict:
    """Répartition par niveau, retards, top postes en retard."""
    try:
        par_niveau = QueryExecutor.fetch_all(
            """SELECT niveau, COUNT(*) AS nb FROM polyvalence
               GROUP BY niveau ORDER BY niveau""",
            dictionary=True,
        ) or []

        total_evals = QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM polyvalence"
        ) or 0

        en_retard = QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM polyvalence WHERE prochaine_evaluation < CURDATE()"
        ) or 0

        top_postes_retard = QueryExecutor.fetch_all(
            """SELECT p.poste_code AS poste, COUNT(*) AS nb_retard
               FROM polyvalence pv
               JOIN postes p ON pv.poste_id = p.id
               WHERE pv.prochaine_evaluation < CURDATE()
               GROUP BY pv.poste_id, p.poste_code
               ORDER BY nb_retard DESC LIMIT 8""",
            dictionary=True,
        ) or []

        return {
            "par_niveau": par_niveau,
            "total": total_evals,
            "en_retard": en_retard,
            "top_postes_retard": top_postes_retard,
        }
    except Exception as e:
        logger.exception(f"get_stats_evaluations: {e}")
        return {}


# ---------------------------------------------------------------------------
# Contrats
# ---------------------------------------------------------------------------

def get_stats_contrats() -> dict:
    """Types de contrats actifs, expirations par tranche."""
    try:
        par_type = QueryExecutor.fetch_all(
            """SELECT type_contrat, COUNT(*) AS nb FROM contrat
               WHERE actif = 1 GROUP BY type_contrat ORDER BY nb DESC""",
            dictionary=True,
        ) or []

        expirations = QueryExecutor.fetch_all(
            """SELECT
                SUM(CASE WHEN date_fin < CURDATE() THEN 1 ELSE 0 END) AS expires,
                SUM(CASE WHEN date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) AS dans_30j,
                SUM(CASE WHEN date_fin BETWEEN DATE_ADD(CURDATE(), INTERVAL 31 DAY) AND DATE_ADD(CURDATE(), INTERVAL 60 DAY) THEN 1 ELSE 0 END) AS dans_60j,
                SUM(CASE WHEN date_fin BETWEEN DATE_ADD(CURDATE(), INTERVAL 61 DAY) AND DATE_ADD(CURDATE(), INTERVAL 90 DAY) THEN 1 ELSE 0 END) AS dans_90j,
                SUM(CASE WHEN date_fin IS NULL THEN 1 ELSE 0 END) AS sans_date_fin
               FROM contrat WHERE actif = 1""",
            dictionary=True,
        ) or []

        return {
            "par_type": par_type,
            "expirations": expirations[0] if expirations else {},
        }
    except Exception as e:
        logger.exception(f"get_stats_contrats: {e}")
        return {}


# ---------------------------------------------------------------------------
# Absences
# ---------------------------------------------------------------------------

def get_stats_absences() -> dict:
    """Par type (6 derniers mois) et répartition des jours par mois."""
    try:
        par_type = QueryExecutor.fetch_all(
            """SELECT ta.libelle AS type_absence, COUNT(*) AS nb,
                      ROUND(SUM(da.nb_jours), 1) AS total_jours
               FROM demande_absence da
               JOIN type_absence ta ON da.type_absence_id = ta.id
               WHERE da.statut = 'VALIDEE'
               AND da.date_debut >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
               GROUP BY ta.id, ta.libelle ORDER BY total_jours DESC""",
            dictionary=True,
        ) or []

        par_mois = QueryExecutor.fetch_all(
            """SELECT DATE_FORMAT(date_debut, '%Y-%m') AS mois,
                      COUNT(*) AS nb_absences,
                      ROUND(SUM(nb_jours), 1) AS total_jours
               FROM demande_absence
               WHERE statut = 'VALIDEE'
               AND date_debut >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
               GROUP BY mois ORDER BY mois ASC""",
            dictionary=True,
        ) or []

        return {
            "par_type": par_type,
            "par_mois": par_mois,
        }
    except Exception as e:
        logger.exception(f"get_stats_absences: {e}")
        return {}


# ---------------------------------------------------------------------------
# Mobilité
# ---------------------------------------------------------------------------

def get_stats_mobilite() -> dict:
    """Modes de transport, distance moyenne, primes estimées."""
    try:
        par_mode = QueryExecutor.fetch_all(
            """SELECT mode_transport, COUNT(*) AS nb,
                      ROUND(AVG(distance_km), 1) AS dist_moy
               FROM personnel_mobilite
               WHERE actif = 1 AND date_fin IS NULL
               GROUP BY mode_transport ORDER BY nb DESC""",
            dictionary=True,
        ) or []

        distances = QueryExecutor.fetch_all(
            """SELECT
                SUM(CASE WHEN distance_km < 7 THEN 1 ELSE 0 END) AS moins_7km,
                SUM(CASE WHEN distance_km BETWEEN 7 AND 13 THEN 1 ELSE 0 END) AS de_7_a_13,
                SUM(CASE WHEN distance_km BETWEEN 14 AND 20 THEN 1 ELSE 0 END) AS de_14_a_20,
                SUM(CASE WHEN distance_km BETWEEN 21 AND 40 THEN 1 ELSE 0 END) AS de_21_a_40,
                SUM(CASE WHEN distance_km > 40 THEN 1 ELSE 0 END) AS plus_40km,
                ROUND(AVG(distance_km), 1) AS distance_moyenne
               FROM personnel_mobilite WHERE actif = 1 AND date_fin IS NULL""",
            dictionary=True,
        ) or []

        return {
            "par_mode": par_mode,
            "distances": distances[0] if distances else {},
        }
    except Exception as e:
        logger.exception(f"get_stats_mobilite: {e}")
        return {}
