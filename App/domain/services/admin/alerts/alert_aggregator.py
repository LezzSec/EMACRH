# -*- coding: utf-8 -*-
from typing import List, Dict, Optional

from infrastructure.db.query_executor import QueryExecutor
from domain.models import Alert, StatistiquesAlertes
from infrastructure.config.performance_monitor import monitor_query
from infrastructure.logging.logging_config import get_logger
from domain.services.admin.alerts.alert_types import TypeAlerte
from domain.services.admin.alerts.contrat_alerts import ContratAlerts
from domain.services.admin.alerts.personnel_alerts import PersonnelAlerts
from domain.services.admin.alerts.rh_alerts import RHAlerts
from domain.services.admin.alerts.document_alerts import DocumentAlerts

logger = get_logger(__name__)


class AlertService:
    """
    Façade qui délègue aux sous-modules spécialisés.
    Toutes les méthodes sont statiques pour faciliter l'utilisation.
    """

    # --- Délégation Contrats ---
    get_contrats_expires = staticmethod(ContratAlerts.get_contrats_expires)
    get_contrats_expirant = staticmethod(ContratAlerts.get_contrats_expirant)
    get_personnel_sans_contrat = staticmethod(ContratAlerts.get_personnel_sans_contrat)
    get_all_contract_alerts = staticmethod(ContratAlerts.get_all_contract_alerts)

    # --- Délégation Personnel ---
    get_personnel_sans_competences = staticmethod(PersonnelAlerts.get_personnel_sans_competences)
    get_nouveaux_sans_affectation = staticmethod(PersonnelAlerts.get_nouveaux_sans_affectation)
    get_all_personnel_alerts = staticmethod(PersonnelAlerts.get_all_personnel_alerts)

    # --- Délégation RH ---
    get_personnel_sans_mutuelle = staticmethod(RHAlerts.get_personnel_sans_mutuelle)
    get_personnel_sans_visite_medicale = staticmethod(RHAlerts.get_personnel_sans_visite_medicale)
    get_personnel_sans_entretien = staticmethod(RHAlerts.get_personnel_sans_entretien)
    _get_mutuelles_expirant = staticmethod(RHAlerts._get_mutuelles_expirant)

    # --- Délégation Documents ---
    get_all_document_alerts = staticmethod(DocumentAlerts.get_all_document_alerts)

    # --- Agrégation (méthodes propres à la façade) ---

    @staticmethod
    @monitor_query('AlertService.get_statistics')
    def get_statistics() -> Dict[str, StatistiquesAlertes]:
        """Calcule les statistiques d'alertes par catégorie."""
        logger.debug("get_statistics: calcul des statistiques d'alertes")
        stats = {
            'contrats': StatistiquesAlertes(),
            'personnel': StatistiquesAlertes(),
            'total': StatistiquesAlertes()
        }

        contract_alerts = ContratAlerts.get_all_contract_alerts()
        stats['contrats'].total = len(contract_alerts)
        stats['contrats'].critiques = len([a for a in contract_alerts if a.urgence == "CRITIQUE"])
        stats['contrats'].avertissements = len([a for a in contract_alerts if a.urgence == "AVERTISSEMENT"])
        stats['contrats'].infos = len([a for a in contract_alerts if a.urgence == "INFO"])

        personnel_alerts = PersonnelAlerts.get_all_personnel_alerts()
        stats['personnel'].total = len(personnel_alerts)
        stats['personnel'].critiques = len([a for a in personnel_alerts if a.urgence == "CRITIQUE"])
        stats['personnel'].avertissements = len([a for a in personnel_alerts if a.urgence == "AVERTISSEMENT"])
        stats['personnel'].infos = len([a for a in personnel_alerts if a.urgence == "INFO"])

        all_alerts = contract_alerts + [
            a for a in personnel_alerts
            if a.type_alerte != TypeAlerte.PERSONNEL_SANS_CONTRAT
        ]
        stats['total'].total = len(all_alerts)
        stats['total'].critiques = stats['contrats'].critiques + stats['personnel'].critiques
        stats['total'].avertissements = stats['contrats'].avertissements + stats['personnel'].avertissements
        stats['total'].infos = stats['contrats'].infos + stats['personnel'].infos

        logger.info(
            f"get_statistics: total={stats['total'].total} — "
            f"critiques={stats['total'].critiques}, "
            f"avertissements={stats['total'].avertissements}, "
            f"infos={stats['total'].infos} | "
            f"contrats={stats['contrats'].total}, personnel={stats['personnel'].total}"
        )
        return stats

    @staticmethod
    def get_quick_counts() -> Dict[str, int]:
        """Récupère rapidement les comptages pour le dashboard (optimisé)."""
        logger.debug("get_quick_counts: calcul rapide des comptages")
        counts = {'critiques': 0, 'avertissements': 0, 'infos': 0}

        try:
            counts['critiques'] += QueryExecutor.fetch_scalar(
                "SELECT COUNT(*) FROM v_contrats_fin_proche WHERE jours_restants < 0", default=0)
            counts['critiques'] += QueryExecutor.fetch_scalar(
                "SELECT COUNT(*) FROM v_contrats_fin_proche WHERE jours_restants BETWEEN 0 AND 7", default=0)
            counts['avertissements'] += QueryExecutor.fetch_scalar(
                "SELECT COUNT(*) FROM v_contrats_fin_proche WHERE jours_restants BETWEEN 8 AND 30", default=0)
            counts['avertissements'] += QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM personnel p
                LEFT JOIN contrat c ON c.personnel_id = p.id AND c.actif = 1
                WHERE p.statut = 'ACTIF' AND c.id IS NULL
            """, default=0)
        except Exception as e:
            logger.exception(f"get_quick_counts: erreur DB — {e}")

        logger.info(
            f"get_quick_counts: critiques={counts['critiques']}, "
            f"avertissements={counts['avertissements']}, infos={counts['infos']}"
        )
        return counts

    @staticmethod
    def get_startup_summary() -> Dict[str, int]:
        """Résumé détaillé par catégorie pour le popup de démarrage."""
        logger.debug("get_startup_summary: calcul du résumé de démarrage")
        result = {}

        _queries = {
            'evaluations_retard': """
                SELECT COUNT(*) FROM polyvalence poly
                JOIN personnel p ON p.id = poly.personnel_id
                WHERE poly.prochaine_evaluation < CURDATE() AND p.statut = 'ACTIF'
            """,
            'contrats_expires': "SELECT COUNT(*) FROM v_contrats_fin_proche WHERE jours_restants < 0",
            'contrats_expirant': "SELECT COUNT(*) FROM v_contrats_fin_proche WHERE jours_restants BETWEEN 0 AND 30",
            'personnel_sans_contrat': """
                SELECT COUNT(*) FROM personnel p
                LEFT JOIN contrat c ON c.personnel_id = p.id AND c.actif = 1
                WHERE p.statut = 'ACTIF' AND c.id IS NULL
            """,
            'mutuelles_expirees': """
                SELECT COUNT(*) FROM mutuelle m JOIN personnel p ON p.id = m.personnel_id
                WHERE p.statut = 'ACTIF' AND m.date_fin IS NOT NULL AND m.date_fin < CURDATE()
            """,
            'mutuelles_expirant': """
                SELECT COUNT(*) FROM mutuelle m JOIN personnel p ON p.id = m.personnel_id
                WHERE p.statut = 'ACTIF'
                  AND m.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            """,
            'visites_retard': """
                SELECT COUNT(DISTINCT mv.personnel_id) FROM medical_visite mv
                JOIN personnel p ON p.id = mv.personnel_id
                WHERE p.statut = 'ACTIF' AND mv.prochaine_visite < CURDATE()
                  AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE personnel_id = mv.personnel_id)
            """,
            'visites_a_planifier': """
                SELECT COUNT(DISTINCT mv.personnel_id) FROM medical_visite mv
                JOIN personnel p ON p.id = mv.personnel_id
                WHERE p.statut = 'ACTIF'
                  AND mv.prochaine_visite BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                  AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE personnel_id = mv.personnel_id)
            """,
            'rqth_expirant': """
                SELECT COUNT(*) FROM validite v JOIN personnel p ON p.id = v.personnel_id
                WHERE p.statut = 'ACTIF' AND v.type_validite = 'RQTH'
                  AND v.date_fin IS NOT NULL
                  AND v.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)
            """,
            'oeth_expirant': """
                SELECT COUNT(*) FROM validite v JOIN personnel p ON p.id = v.personnel_id
                WHERE p.statut = 'ACTIF' AND v.type_validite = 'OETH'
                  AND v.date_fin IS NOT NULL
                  AND v.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)
            """,
            'competences_expirees': """
                SELECT COUNT(*) FROM personnel_competences pc JOIN personnel p ON p.id = pc.personnel_id
                WHERE p.statut = 'ACTIF'
                  AND pc.date_expiration IS NOT NULL AND pc.date_expiration < CURDATE()
            """,
            'competences_expirant': """
                SELECT COUNT(*) FROM personnel_competences pc JOIN personnel p ON p.id = pc.personnel_id
                WHERE p.statut = 'ACTIF'
                  AND pc.date_expiration BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            """,
            'documents_expires': """
                SELECT COUNT(*) FROM documents d JOIN personnel p ON p.id = d.personnel_id
                WHERE p.statut = 'ACTIF' AND d.statut = 'expire'
            """,
            'documents_expirant': """
                SELECT COUNT(*) FROM documents d JOIN personnel p ON p.id = d.personnel_id
                WHERE p.statut = 'ACTIF' AND d.statut = 'actif'
                  AND d.date_expiration IS NOT NULL
                  AND d.date_expiration BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            """,
        }

        try:
            for key, query in _queries.items():
                result[key] = QueryExecutor.fetch_scalar(query, default=0)
        except Exception as e:
            logger.exception(f"get_startup_summary: erreur DB — {e}")
            for key in _queries:
                result.setdefault(key, 0)

        result['total_critique'] = (
            result['evaluations_retard'] + result['contrats_expires'] +
            result['mutuelles_expirees'] + result['visites_retard'] +
            result['competences_expirees'] + result['documents_expires']
        )
        result['total_avertissement'] = (
            result['contrats_expirant'] + result['personnel_sans_contrat'] +
            result['mutuelles_expirant'] + result['visites_a_planifier'] +
            result['rqth_expirant'] + result['oeth_expirant'] +
            result['competences_expirant'] + result['documents_expirant']
        )

        logger.info(
            f"get_startup_summary: éval_retard={result['evaluations_retard']}, "
            f"contrats={result['contrats_expires']}/{result['contrats_expirant']}, "
            f"total_critique={result['total_critique']}, "
            f"total_avertissement={result['total_avertissement']}"
        )
        return result
