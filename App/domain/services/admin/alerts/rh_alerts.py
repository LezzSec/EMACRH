# -*- coding: utf-8 -*-
from datetime import date
from typing import List

from infrastructure.db.query_executor import QueryExecutor
from domain.models import Alert
from infrastructure.logging.logging_config import get_logger
from domain.services.admin.alerts.alert_types import TypeAlerte

logger = get_logger(__name__)


class RHAlerts:
    """Alertes RH : mutuelle, visite médicale, entretien."""

    @staticmethod
    def get_personnel_sans_mutuelle() -> List[Alert]:
        query = """
            SELECT p.id, p.nom, p.prenom, p.matricule
            FROM personnel p
            LEFT JOIN mutuelle m ON m.personnel_id = p.id
            WHERE p.statut = 'ACTIF' AND m.id IS NULL
            ORDER BY p.nom, p.prenom
        """
        try:
            rows = QueryExecutor.fetch_all(query, dictionary=True)
        except Exception as e:
            logger.exception(f"get_personnel_sans_mutuelle: erreur DB — {e}")
            return []

        return [
            Alert(
                id=row['id'], categorie="SANS_MUTUELLE",
                type_alerte=TypeAlerte.PERSONNEL_SANS_MUTUELLE, urgence="AVERTISSEMENT",
                titre="Mutuelle manquante", description="Aucune mutuelle enregistrée",
                personnel_id=row['id'], personnel_nom=row['nom'], personnel_prenom=row['prenom'],
                date_alerte=date.today(), date_echeance=None, jours_restants=None,
                data={'matricule': row['matricule']}
            )
            for row in rows
        ]

    @staticmethod
    def get_personnel_sans_visite_medicale() -> List[Alert]:
        query = """
            SELECT p.id, p.nom, p.prenom, p.matricule, pi.date_entree
            FROM personnel p
            LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
            LEFT JOIN medical_visite mv ON mv.personnel_id = p.id
            WHERE p.statut = 'ACTIF' AND mv.id IS NULL
            ORDER BY pi.date_entree, p.nom
        """
        try:
            rows = QueryExecutor.fetch_all(query, dictionary=True)
        except Exception as e:
            logger.exception(f"get_personnel_sans_visite_medicale: erreur DB — {e}")
            return []

        return [
            Alert(
                id=row['id'], categorie="SANS_VISITE",
                type_alerte=TypeAlerte.PERSONNEL_SANS_VISITE, urgence="AVERTISSEMENT",
                titre="Visite médicale manquante", description="Aucune visite médicale enregistrée",
                personnel_id=row['id'], personnel_nom=row['nom'], personnel_prenom=row['prenom'],
                date_alerte=date.today(), date_echeance=None, jours_restants=None,
                data={'matricule': row['matricule']}
            )
            for row in rows
        ]

    @staticmethod
    def get_personnel_sans_entretien() -> List[Alert]:
        query = """
            SELECT p.id, p.nom, p.prenom, p.matricule, pi.date_entree
            FROM personnel p
            LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
            LEFT JOIN vie_salarie_entretien e ON e.personnel_id = p.id
            WHERE p.statut = 'ACTIF' AND e.id IS NULL
            ORDER BY pi.date_entree, p.nom
        """
        try:
            rows = QueryExecutor.fetch_all(query, dictionary=True)
        except Exception as e:
            logger.exception(f"get_personnel_sans_entretien: erreur DB — {e}")
            return []

        return [
            Alert(
                id=row['id'], categorie="SANS_ENTRETIEN",
                type_alerte=TypeAlerte.PERSONNEL_SANS_ENTRETIEN, urgence="INFO",
                titre="Entretien manquant", description="Aucun entretien professionnel enregistré",
                personnel_id=row['id'], personnel_nom=row['nom'], personnel_prenom=row['prenom'],
                date_alerte=date.today(), date_echeance=None, jours_restants=None,
                data={'matricule': row['matricule']}
            )
            for row in rows
        ]

    @staticmethod
    def _get_mutuelles_expirant(jours: int = 30) -> List[Alert]:
        query = """
            SELECT m.id, m.personnel_id, m.date_fin, p.nom, p.prenom, p.matricule,
                   DATEDIFF(m.date_fin, CURDATE()) AS jours_restants
            FROM mutuelle m
            JOIN personnel p ON p.id = m.personnel_id
            WHERE p.statut = 'ACTIF'
              AND m.date_fin IS NOT NULL
              AND m.date_fin <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
            ORDER BY m.date_fin ASC
        """
        try:
            rows = QueryExecutor.fetch_all(query, (jours,), dictionary=True)
        except Exception as e:
            logger.exception(f"_get_mutuelles_expirant: erreur DB — {e}")
            return []

        alerts = []
        for row in rows:
            jr = row['jours_restants'] if row['jours_restants'] is not None else 0
            if jr <= 0:
                urgence, titre, desc = "CRITIQUE", "Mutuelle expirée", f"Expirée depuis {abs(jr)}j"
            elif jr <= 7:
                urgence, titre, desc = "CRITIQUE", "Mutuelle expire bientôt", f"Expire dans {jr}j"
            else:
                urgence, titre, desc = "AVERTISSEMENT", "Mutuelle expire bientôt", f"Expire dans {jr}j"
            alerts.append(Alert(
                id=row['id'], categorie="MUTUELLE",
                type_alerte="MUTUELLE_EXPIRANT", urgence=urgence,
                titre=titre, description=desc,
                personnel_id=row['personnel_id'], personnel_nom=row['nom'], personnel_prenom=row['prenom'],
                date_alerte=date.today(), date_echeance=row['date_fin'], jours_restants=jr,
                data={'matricule': row['matricule']}
            ))
        return alerts
