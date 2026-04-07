# -*- coding: utf-8 -*-
"""
Service de gestion du planning et des absences.
Centralise tous les accès DB du module planning.py.
"""
from datetime import date, timedelta
from typing import List, Dict, Optional

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


def get_absents_du_jour(today: date = None) -> List[Dict]:
    """Retourne la liste des absents (déclarations) pour un jour donné."""
    if today is None:
        today = date.today()
    return QueryExecutor.fetch_all("""
        SELECT
            d.id,
            d.personnel_id,
            p.nom,
            p.prenom,
            d.type_declaration,
            d.date_debut,
            d.date_fin,
            d.motif
        FROM declaration d
        LEFT JOIN personnel p ON p.id = d.personnel_id
        WHERE %s BETWEEN d.date_debut AND d.date_fin
        ORDER BY p.nom, p.prenom
    """, (today,), dictionary=True)


def get_personnel_actif_liste() -> List[Dict]:
    """Retourne la liste du personnel actif (id, nom, prenom, matricule)."""
    return QueryExecutor.fetch_all("""
        SELECT id, nom, prenom, matricule
        FROM personnel
        WHERE statut = 'ACTIF'
        ORDER BY nom, prenom
    """, dictionary=True)


def creer_declaration(operateur_id: int, type_decl: str,
                      date_debut: date, date_fin: date,
                      motif: str = None) -> Optional[int]:
    """
    Crée une déclaration d'absence.
    Retourne l'ID de la déclaration créée, ou None si échec.
    """
    from core.services.permission_manager import require
    require("planning.absences.edit")
    try:
        new_id = QueryExecutor.execute_write("""
            INSERT INTO declaration (personnel_id, type_declaration, date_debut, date_fin, motif)
            VALUES (%s, %s, %s, %s, %s)
        """, (operateur_id, type_decl, date_debut, date_fin, motif or None),
        return_lastrowid=True)

        from infrastructure.logging.optimized_db_logger import log_hist
        log_hist(
            "INSERT",
            f"Déclaration d'absence : {type_decl}",
            operateur_id,
            None
        )
        return new_id

    except Exception as e:
        logger.exception(f"Erreur création déclaration pour opérateur {operateur_id}: {e}")
        return None


def get_absences_du_mois(first_day: date, last_day: date) -> List[Dict]:
    """Retourne les périodes d'absence qui se chevauchent avec le mois donné."""
    return QueryExecutor.fetch_all("""
        SELECT DISTINCT date_debut, date_fin
        FROM declaration
        WHERE (date_debut BETWEEN %s AND %s)
           OR (date_fin BETWEEN %s AND %s)
           OR (date_debut <= %s AND date_fin >= %s)
    """, (first_day, last_day, first_day, last_day, first_day, last_day), dictionary=True)


def get_absences_du_jour(selected: date) -> List[Dict]:
    """Retourne la liste des absents pour un jour spécifique."""
    return QueryExecutor.fetch_all("""
        SELECT
            p.nom,
            p.prenom,
            d.type_declaration,
            d.motif
        FROM declaration d
        LEFT JOIN personnel p ON p.id = d.personnel_id
        WHERE %s BETWEEN d.date_debut AND d.date_fin
        ORDER BY p.nom, p.prenom
    """, (selected,), dictionary=True)


def get_postes_avec_polyvalences() -> List[Dict]:
    """Retourne les postes visibles qui ont des polyvalences (pour les filtres)."""
    return QueryExecutor.fetch_all("""
        SELECT DISTINCT p.id, p.poste_code
        FROM postes p
        INNER JOIN polyvalence poly ON poly.poste_id = p.id
        WHERE p.visible = 1
        ORDER BY p.poste_code
    """, dictionary=True)


def get_evaluations_dates_du_mois(first_day: date, last_day: date) -> List[Dict]:
    """Retourne les dates distinctes d'évaluations planifiées dans un mois."""
    return QueryExecutor.fetch_all("""
        SELECT DISTINCT DATE(poly.prochaine_evaluation) as eval_date
        FROM polyvalence poly
        JOIN personnel pers ON poly.personnel_id = pers.id
        JOIN postes p ON poly.poste_id = p.id
        WHERE poly.prochaine_evaluation BETWEEN %s AND %s
          AND pers.statut = 'ACTIF'
          AND p.visible = 1
    """, (first_day, last_day), dictionary=True)


def get_evaluations_du_jour(selected: date, poste_id: int = None) -> List[Dict]:
    """
    Retourne les évaluations prévues pour un jour donné.
    Filtre optionnel par poste (ID entier validé).
    """
    query = """
        SELECT
            pers.nom,
            pers.prenom,
            p.poste_code,
            poly.niveau,
            poly.prochaine_evaluation
        FROM polyvalence poly
        JOIN personnel pers ON poly.personnel_id = pers.id
        JOIN postes p ON poly.poste_id = p.id
        WHERE DATE(poly.prochaine_evaluation) = %s
          AND pers.statut = 'ACTIF'
          AND p.visible = 1
    """
    params = [selected]

    if poste_id is not None:
        query += " AND p.id = %s"
        params.append(int(poste_id))  # Sécurité: forcer entier

    query += " ORDER BY pers.nom, pers.prenom, p.poste_code"
    return QueryExecutor.fetch_all(query, params, dictionary=True)


def get_historique_declarations(type_filter: str = None, period: str = None) -> List[Dict]:
    """
    Retourne l'historique des déclarations avec filtres optionnels.
    Utilise une whitelist pour les types et périodes (sécurité SQL).

    Args:
        type_filter: Type de déclaration ("Tous" ou type spécifique)
        period: Période ("30 derniers jours", "3 derniers mois", etc.)
    """
    _ALLOWED_TYPES = {
        'CongePaye', 'RTT', 'Maladie', 'ArretTravail',
        'AccidentTravail', 'AccidentTrajet', 'Formation',
        'CongeMaternite', 'CongeParentalite', 'Autre',
    }
    _PERIOD_MAP = {
        "30 derniers jours": 30,
        "3 derniers mois": 90,
        "6 derniers mois": 180,
    }

    query = """
        SELECT
            d.id,
            p.nom,
            p.prenom,
            d.type_declaration,
            d.date_debut,
            d.date_fin,
            d.motif
        FROM declaration d
        LEFT JOIN personnel p ON p.id = d.personnel_id
        WHERE 1=1
    """
    params = []

    if type_filter and type_filter != "Tous" and type_filter in _ALLOWED_TYPES:
        query += " AND d.type_declaration = %s"
        params.append(type_filter)

    if period and period != "Tout":
        if period in _PERIOD_MAP:
            start_date = date.today() - timedelta(days=_PERIOD_MAP[period])
            query += " AND d.date_debut >= %s"
            params.append(start_date)
        elif period == "Cette année":
            start_date = date(date.today().year, 1, 1)
            query += " AND d.date_debut >= %s"
            params.append(start_date)

    query += " ORDER BY d.date_debut DESC, p.nom, p.prenom"
    return QueryExecutor.fetch_all(query, params, dictionary=True)


def get_evaluations_mois(first_day, last_day) -> list:
    """
    Retourne les évaluations planifiées dans la plage de dates avec nom, poste, niveau.
    Utilisé par le calendrier de planning pour colorier les jours d'évaluation.
    """
    return QueryExecutor.fetch_all(
        """
        SELECT poly.prochaine_evaluation,
               CONCAT(p.prenom, ' ', p.nom) AS nom_complet,
               pos.poste_code,
               poly.niveau
        FROM polyvalence poly
        JOIN personnel p ON poly.personnel_id = p.id
        JOIN postes pos ON poly.poste_id = pos.id
        WHERE p.statut = 'ACTIF'
          AND poly.prochaine_evaluation >= %s
          AND poly.prochaine_evaluation <= %s
        ORDER BY poly.prochaine_evaluation
        """,
        (first_day, last_day),
        dictionary=True,
    )


def get_documents_expirant(jours: int = 30) -> List[Dict]:
    """
    Retourne les documents RH du personnel actif qui expirent dans les prochains jours.
    Jours validé en int pour éviter toute injection.
    """
    jours = int(jours)
    return QueryExecutor.fetch_all(
        """
        SELECT
            d.id,
            d.personnel_id,
            p.nom,
            p.prenom,
            p.matricule,
            COALESCE(d.nom_affichage, d.nom_fichier) AS nom_document,
            c.nom AS categorie,
            d.date_expiration,
            DATEDIFF(d.date_expiration, CURDATE()) AS jours_restants
        FROM documents d
        INNER JOIN personnel p ON p.id = d.personnel_id
        LEFT JOIN categories_documents c ON c.id = d.categorie_id
        WHERE d.statut = 'actif'
          AND d.date_expiration IS NOT NULL
          AND d.date_expiration BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
          AND p.statut = 'ACTIF'
        ORDER BY d.date_expiration ASC
        """,
        (jours,),
        dictionary=True,
    )


def supprimer_declaration(decl_id: int) -> bool:
    """Supprime une déclaration d'absence par ID."""
    from core.services.permission_manager import require
    require("planning.absences.edit")
    try:
        QueryExecutor.execute_write(
            "DELETE FROM declaration WHERE id = %s", (decl_id,)
        )
        return True
    except Exception as e:
        logger.exception(f"Erreur suppression déclaration {decl_id}: {e}")
        return False
