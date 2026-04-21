# -*- coding: utf-8 -*-
from datetime import date, timedelta
from typing import List, Optional

from infrastructure.db.query_executor import QueryExecutor
from domain.models import Alert
from infrastructure.config.performance_monitor import monitor_query
from infrastructure.logging.logging_config import get_logger
from domain.services.admin.alerts.alert_types import TypeAlerte

logger = get_logger(__name__)


class ContratAlerts:
    """Alertes relatives aux contrats."""

    @staticmethod
    @monitor_query('AlertService.get_contrats_expires')
    def get_contrats_expires() -> List[Alert]:
        query = """
            SELECT id, personnel_id, type_contrat, date_debut, date_fin,
                   nom, prenom, matricule,
                   -jours_restants as jours_expires
            FROM v_contrats_fin_proche
            WHERE jours_restants < 0
            ORDER BY date_fin ASC
        """
        try:
            rows = QueryExecutor.fetch_all(query, dictionary=True)
        except Exception as e:
            logger.exception(f"get_contrats_expires: erreur DB — {e}")
            return []

        alerts = []
        for row in rows:
            alerts.append(Alert(
                id=row['id'],
                categorie="CONTRAT",
                type_alerte=TypeAlerte.CONTRAT_EXPIRE,
                urgence="CRITIQUE",
                titre=f"Contrat expiré ({row['type_contrat']})",
                description=f"Contrat expiré depuis {row['jours_expires']} jour(s)",
                personnel_id=row['personnel_id'],
                personnel_nom=row['nom'],
                personnel_prenom=row['prenom'],
                date_alerte=date.today(),
                date_echeance=row['date_fin'],
                jours_restants=-row['jours_expires'],
                data={
                    'type_contrat': row['type_contrat'],
                    'date_debut': row['date_debut'].isoformat() if row['date_debut'] else None,
                    'matricule': row['matricule']
                }
            ))

        if alerts:
            logger.warning(f"get_contrats_expires: {len(alerts)} contrat(s) expiré(s) détecté(s)")
        else:
            logger.info("get_contrats_expires: aucun contrat expiré")
        return alerts

    @staticmethod
    @monitor_query('AlertService.get_contrats_expirant')
    def get_contrats_expirant(jours: int = 30) -> List[Alert]:
        date_limite = date.today() + timedelta(days=jours)
        query = """
            SELECT id, personnel_id, type_contrat, date_debut, date_fin,
                   nom, prenom, matricule, jours_restants
            FROM v_contrats_fin_proche
            WHERE jours_restants >= 0
              AND date_fin <= %s
            ORDER BY date_fin ASC
        """
        try:
            rows = QueryExecutor.fetch_all(query, (date_limite,), dictionary=True)
        except Exception as e:
            logger.exception(f"get_contrats_expirant: erreur DB (jours={jours}) — {e}")
            return []

        alerts = []
        nb_critiques = nb_avertissements = 0
        for row in rows:
            jours_restants = row['jours_restants']
            if jours_restants <= 7:
                urgence = "CRITIQUE"
                type_alerte = TypeAlerte.CONTRAT_EXPIRE_7J
                nb_critiques += 1
            else:
                urgence = "AVERTISSEMENT"
                type_alerte = TypeAlerte.CONTRAT_EXPIRE_30J
                nb_avertissements += 1

            alerts.append(Alert(
                id=row['id'],
                categorie="CONTRAT",
                type_alerte=type_alerte,
                urgence=urgence,
                titre=f"Contrat {row['type_contrat']} expire bientôt",
                description=f"Expire dans {jours_restants} jour(s)",
                personnel_id=row['personnel_id'],
                personnel_nom=row['nom'],
                personnel_prenom=row['prenom'],
                date_alerte=date.today(),
                date_echeance=row['date_fin'],
                jours_restants=jours_restants,
                data={
                    'type_contrat': row['type_contrat'],
                    'date_debut': row['date_debut'].isoformat() if row['date_debut'] else None,
                    'matricule': row['matricule']
                }
            ))

        if alerts:
            logger.info(
                f"get_contrats_expirant({jours}j): {len(alerts)} alerte(s) — "
                f"{nb_critiques} critique(s), {nb_avertissements} avertissement(s)"
            )
        else:
            logger.info(f"get_contrats_expirant({jours}j): aucun contrat expirant")
        return alerts

    @staticmethod
    @monitor_query('AlertService.get_personnel_sans_contrat')
    def get_personnel_sans_contrat() -> List[Alert]:
        query = """
            SELECT p.id, p.nom, p.prenom, p.matricule, pi.date_entree
            FROM personnel p
            LEFT JOIN contrat c ON c.personnel_id = p.id AND c.actif = 1
            LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
            WHERE p.statut = 'ACTIF' AND c.id IS NULL
            ORDER BY p.nom, p.prenom;
        """
        try:
            rows = QueryExecutor.fetch_all(query, dictionary=True)
        except Exception as e:
            logger.exception(f"get_personnel_sans_contrat: erreur DB — {e}")
            return []

        alerts = [
            Alert(
                id=row['id'],
                categorie="PERSONNEL",
                type_alerte=TypeAlerte.PERSONNEL_SANS_CONTRAT,
                urgence="AVERTISSEMENT",
                titre="Personnel sans contrat",
                description="Aucun contrat actif trouvé",
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
            logger.info(f"get_personnel_sans_contrat: {len(alerts)} personnel(s) sans contrat actif")
        else:
            logger.info("get_personnel_sans_contrat: tout le personnel actif a un contrat")
        return alerts

    @staticmethod
    def get_all_contract_alerts(type_contrat: Optional[str] = None) -> List[Alert]:
        alerts = []
        alerts.extend(ContratAlerts.get_contrats_expires())
        alerts.extend(ContratAlerts.get_contrats_expirant(30))
        alerts.extend(ContratAlerts.get_personnel_sans_contrat())

        if type_contrat:
            alerts = [
                a for a in alerts
                if a.data.get('type_contrat') == type_contrat
                or a.type_alerte == TypeAlerte.PERSONNEL_SANS_CONTRAT
            ]

        def sort_key(alert):
            return (alert.urgence_ordre, alert.jours_restants if alert.jours_restants is not None else 9999)

        result = sorted(alerts, key=sort_key)
        logger.info(f"get_all_contract_alerts: {len(result)} alerte(s) contrat au total")
        return result
