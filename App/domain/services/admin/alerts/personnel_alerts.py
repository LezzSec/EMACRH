# -*- coding: utf-8 -*-
from datetime import date, timedelta
from typing import List

from infrastructure.db.query_executor import QueryExecutor
from domain.models import Alert
from infrastructure.config.performance_monitor import monitor_query
from infrastructure.logging.logging_config import get_logger
from domain.services.admin.alerts.alert_types import TypeAlerte
from domain.services.admin.alerts.contrat_alerts import ContratAlerts

logger = get_logger(__name__)


class PersonnelAlerts:
    """Alertes relatives au personnel (compétences, affectation)."""

    @staticmethod
    @monitor_query('AlertService.get_personnel_sans_competences')
    def get_personnel_sans_competences() -> List[Alert]:
        query = """
            SELECT p.id, p.nom, p.prenom, p.matricule, pi.date_entree
            FROM personnel p
            LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
            LEFT JOIN polyvalence poly ON poly.personnel_id = p.id
            WHERE p.statut = 'ACTIF' AND poly.id IS NULL
            ORDER BY pi.date_entree DESC, p.nom
        """
        try:
            rows = QueryExecutor.fetch_all(query, dictionary=True)
        except Exception as e:
            logger.exception(f"get_personnel_sans_competences: erreur DB — {e}")
            return []

        alerts = [
            Alert(
                id=row['id'],
                categorie="PERSONNEL",
                type_alerte=TypeAlerte.PERSONNEL_SANS_COMPETENCES,
                urgence="INFO",
                titre="Personnel sans compétences",
                description="Aucune polyvalence assignée",
                personnel_id=row['id'],
                personnel_nom=row['nom'],
                personnel_prenom=row['prenom'],
                date_alerte=date.today(),
                date_echeance=None,
                jours_restants=None,
                data={
                    'matricule': row['matricule'],
                    'date_entree': row['date_entree'].isoformat() if row['date_entree'] else None
                }
            )
            for row in rows
        ]

        if alerts:
            logger.info(f"get_personnel_sans_competences: {len(alerts)} personnel(s) sans polyvalence")
        else:
            logger.info("get_personnel_sans_competences: tout le personnel actif a des compétences")
        return alerts

    @staticmethod
    @monitor_query('AlertService.get_nouveaux_sans_affectation')
    def get_nouveaux_sans_affectation(jours: int = 30) -> List[Alert]:
        date_limite = date.today() - timedelta(days=jours)
        query = """
            SELECT p.id, p.nom, p.prenom, p.matricule, pi.date_entree,
                   DATEDIFF(CURDATE(), pi.date_entree) as jours_depuis_entree
            FROM personnel p
            JOIN personnel_infos pi ON pi.personnel_id = p.id
            LEFT JOIN polyvalence poly ON poly.personnel_id = p.id
            WHERE p.statut = 'ACTIF'
              AND pi.date_entree IS NOT NULL
              AND pi.date_entree >= %s
              AND poly.id IS NULL
            ORDER BY pi.date_entree DESC
        """
        try:
            rows = QueryExecutor.fetch_all(query, (date_limite,), dictionary=True)
        except Exception as e:
            logger.exception(f"get_nouveaux_sans_affectation: erreur DB (jours={jours}) — {e}")
            return []

        alerts = [
            Alert(
                id=row['id'],
                categorie="PERSONNEL",
                type_alerte=TypeAlerte.PERSONNEL_NOUVEAU_SANS_AFFECTATION,
                urgence="INFO",
                titre="Nouveau sans affectation",
                description=f"Arrivé il y a {row['jours_depuis_entree']} jour(s), aucune compétence",
                personnel_id=row['id'],
                personnel_nom=row['nom'],
                personnel_prenom=row['prenom'],
                date_alerte=date.today(),
                date_echeance=None,
                jours_restants=None,
                data={
                    'matricule': row['matricule'],
                    'date_entree': row['date_entree'].isoformat() if row['date_entree'] else None,
                    'jours_depuis_entree': row['jours_depuis_entree']
                }
            )
            for row in rows
        ]

        if alerts:
            logger.info(f"get_nouveaux_sans_affectation({jours}j): {len(alerts)} nouveau(x) sans compétences")
        else:
            logger.info(f"get_nouveaux_sans_affectation({jours}j): aucun nouveau sans affectation")
        return alerts

    @staticmethod
    def get_all_personnel_alerts() -> List[Alert]:
        alerts = []
        alerts.extend(ContratAlerts.get_personnel_sans_contrat())
        alerts.extend(PersonnelAlerts.get_nouveaux_sans_affectation(30))

        seen_ids = {}
        unique_alerts = []
        doublons = 0
        for alert in alerts:
            key = (alert.personnel_id, alert.type_alerte)
            if key not in seen_ids:
                seen_ids[key] = True
                unique_alerts.append(alert)
            else:
                doublons += 1

        if doublons:
            logger.info(f"get_all_personnel_alerts: {doublons} doublon(s) supprimé(s)")

        result = sorted(unique_alerts, key=lambda a: a.urgence_ordre)
        logger.info(f"get_all_personnel_alerts: {len(result)} alerte(s) personnel au total")
        return result
