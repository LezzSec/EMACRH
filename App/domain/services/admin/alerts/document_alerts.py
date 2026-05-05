# -*- coding: utf-8 -*-
from datetime import date
from typing import Dict, List, Optional, Tuple

from domain.models import Alert
from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.logging_config import get_logger
from domain.services.admin.alerts.contrat_alerts import ContratAlerts
from domain.services.admin.alerts.rh_alerts import RHAlerts

logger = get_logger(__name__)


class DocumentAlerts:
    """Agrégation de toutes les alertes documents RH."""

    # ------------------------------------------------------------------
    # Compteurs rapides — une seule requête SQL, aucun objet Alert créé
    # ------------------------------------------------------------------

    _COUNTS_QUERY = """
        SELECT
            (SELECT COUNT(*) FROM v_contrats_fin_proche WHERE jours_restants < 0
            ) AS contrat_expire,
            (SELECT COUNT(*) FROM v_contrats_fin_proche WHERE jours_restants BETWEEN 0 AND 7
            ) AS contrat_critique,
            (SELECT COUNT(*) FROM v_contrats_fin_proche WHERE jours_restants BETWEEN 8 AND %s
            ) AS contrat_avert,
            (SELECT COUNT(*)
             FROM personnel p LEFT JOIN contrat c ON c.personnel_id = p.id AND c.actif = 1
             WHERE p.statut = 'ACTIF' AND c.id IS NULL
            ) AS sans_contrat,
            (SELECT COUNT(DISTINCT mv.personnel_id)
             FROM medical_visite mv JOIN personnel p ON p.id = mv.personnel_id
             WHERE p.statut = 'ACTIF' AND mv.prochaine_visite < CURDATE()
               AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE personnel_id = mv.personnel_id)
            ) AS visite_critique,
            (SELECT COUNT(DISTINCT mv.personnel_id)
             FROM medical_visite mv JOIN personnel p ON p.id = mv.personnel_id
             WHERE p.statut = 'ACTIF'
               AND mv.prochaine_visite BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
               AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE personnel_id = mv.personnel_id)
            ) AS visite_avert,
            (SELECT COUNT(*)
             FROM v_suivi_medical
             WHERE date_fin_rqth IS NOT NULL
               AND date_fin_rqth BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            ) AS rqth_critique,
            (SELECT COUNT(*)
             FROM v_suivi_medical
             WHERE date_fin_rqth IS NOT NULL
               AND date_fin_rqth BETWEEN DATE_ADD(CURDATE(), INTERVAL 8 DAY)
                                     AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
            ) AS rqth_avert,
            (SELECT COUNT(*)
             FROM personnel p JOIN vie_salarie_entretien e ON p.id = e.personnel_id
             WHERE p.statut = 'ACTIF' AND e.prochaine_date IS NOT NULL
               AND e.prochaine_date < CURDATE()
               AND e.id = (SELECT MAX(id) FROM vie_salarie_entretien WHERE personnel_id = p.id)
            ) AS entretien_critique,
            (SELECT COUNT(*)
             FROM personnel p JOIN vie_salarie_entretien e ON p.id = e.personnel_id
             WHERE p.statut = 'ACTIF' AND e.prochaine_date IS NOT NULL
               AND e.prochaine_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
               AND e.id = (SELECT MAX(id) FROM vie_salarie_entretien WHERE personnel_id = p.id)
            ) AS entretien_avert,
            (SELECT COUNT(*)
             FROM mutuelle m JOIN personnel p ON p.id = m.personnel_id
             WHERE p.statut = 'ACTIF' AND m.date_fin IS NOT NULL
               AND m.date_fin <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            ) AS mutuelle_critique,
            (SELECT COUNT(*)
             FROM mutuelle m JOIN personnel p ON p.id = m.personnel_id
             WHERE p.statut = 'ACTIF' AND m.date_fin IS NOT NULL
               AND m.date_fin BETWEEN DATE_ADD(CURDATE(), INTERVAL 8 DAY)
                                  AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
            ) AS mutuelle_avert,
            (SELECT COUNT(*)
             FROM personnel p LEFT JOIN mutuelle m ON m.personnel_id = p.id
             WHERE p.statut = 'ACTIF' AND m.id IS NULL
            ) AS sans_mutuelle,
            (SELECT COUNT(*)
             FROM personnel p LEFT JOIN medical_visite mv ON mv.personnel_id = p.id
             WHERE p.statut = 'ACTIF' AND mv.id IS NULL
            ) AS sans_visite,
            (SELECT COUNT(*)
             FROM personnel p LEFT JOIN vie_salarie_entretien e ON e.personnel_id = p.id
             WHERE p.statut = 'ACTIF' AND e.id IS NULL
            ) AS sans_entretien
    """

    _COUNTS_KEYS = [
        'contrat_expire', 'contrat_critique', 'contrat_avert', 'sans_contrat',
        'visite_critique', 'visite_avert',
        'rqth_critique', 'rqth_avert',
        'entretien_critique', 'entretien_avert',
        'mutuelle_critique', 'mutuelle_avert',
        'sans_mutuelle', 'sans_visite', 'sans_entretien',
    ]

    @staticmethod
    def get_counts(jours: int = 30) -> Dict[str, int]:
        """
        Compteurs d'alertes par catégorie via une seule requête SQL.
        Adapté aux badges dashboard — aucun objet Alert instancié.

        Returns:
            Dict avec clés par catégorie + 'critique', 'avertissement', 'info', 'total'
        """
        try:
            row = QueryExecutor.fetch_one(
                DocumentAlerts._COUNTS_QUERY,
                (jours, jours, jours, jours, jours),
                dictionary=True,
            )
            counts = {k: int(row[k]) for k in DocumentAlerts._COUNTS_KEYS} if row \
                else {k: 0 for k in DocumentAlerts._COUNTS_KEYS}
        except Exception as e:
            logger.exception(f"get_counts: erreur DB — {e}")
            counts = {k: 0 for k in DocumentAlerts._COUNTS_KEYS}

        counts['critique'] = (
            counts['contrat_expire'] + counts['contrat_critique'] +
            counts['visite_critique'] + counts['rqth_critique'] +
            counts['entretien_critique'] + counts['mutuelle_critique']
        )
        counts['avertissement'] = (
            counts['contrat_avert'] + counts['sans_contrat'] +
            counts['visite_avert'] + counts['rqth_avert'] +
            counts['entretien_avert'] + counts['mutuelle_avert'] +
            counts['sans_mutuelle'] + counts['sans_visite']
        )
        counts['info'] = counts['sans_entretien']
        counts['total'] = counts['critique'] + counts['avertissement'] + counts['info']
        return counts

    @staticmethod
    def get_top(
        n: int = 10,
        type_doc: Optional[str] = None,
        jours: int = 30,
    ) -> Tuple[List[Alert], int]:
        """
        Retourne les N alertes les plus urgentes et le total.

        Utile pour le dashboard : seuls N éléments sont envoyés à l'UI
        sans devoir paginer côté service.

        Returns:
            (top_alerts, total) — les N plus urgentes + nombre total
        """
        all_alerts = DocumentAlerts.get_all_document_alerts(type_doc=type_doc, jours=jours)
        return all_alerts[:n], len(all_alerts)

    # ------------------------------------------------------------------
    # Agrégation complète (inchangée)
    # ------------------------------------------------------------------

    @staticmethod
    def get_all_document_alerts(type_doc: Optional[str] = None, jours: int = 30) -> List[Alert]:
        """
        Agrège toutes les alertes documents RH : contrats, visites médicales,
        RQTH, entretiens, mutuelles et personnel sans contrat.

        Args:
            type_doc: Filtre catégorie (CONTRAT, SANS_CONTRAT, VISITE_MEDICALE, RQTH, ENTRETIEN, MUTUELLE)
            jours: Horizon "expire bientôt" en jours
        """
        alerts: List[Alert] = []

        if not type_doc or type_doc == "CONTRAT":
            alerts.extend(ContratAlerts.get_contrats_expires())
            alerts.extend(ContratAlerts.get_contrats_expirant(jours))

        if not type_doc or type_doc == "SANS_CONTRAT":
            alerts.extend(ContratAlerts.get_personnel_sans_contrat())

        if not type_doc or type_doc == "VISITE_MEDICALE":
            from domain.services.rh.medical_service import get_visites_a_planifier
            for v in get_visites_a_planifier(jours_avance=jours):
                jr = v.get('jours_restants') or 0
                if jr <= 0:
                    urgence, desc = "CRITIQUE", "En retard"
                elif jr <= 7:
                    urgence, desc = "CRITIQUE", f"Prévue dans {jr}j"
                else:
                    urgence, desc = "AVERTISSEMENT", f"Prévue dans {jr}j"
                alerts.append(Alert(
                    id=v.get('operateur_id'), categorie="VISITE_MEDICALE",
                    type_alerte="VISITE_A_PLANIFIER", urgence=urgence,
                    titre="Visite médicale", description=desc,
                    personnel_id=v.get('operateur_id'),
                    personnel_nom=v.get('nom', ''), personnel_prenom=v.get('prenom', ''),
                    date_alerte=date.today(), date_echeance=v.get('prochaine_visite'),
                    jours_restants=jr, data={'matricule': v.get('matricule')}
                ))

        if not type_doc or type_doc == "RQTH":
            from domain.services.rh.medical_service import get_rqth_expirant
            for r in get_rqth_expirant(jours_avance=jours):
                jr = r.get('jours_restants') or 0
                urgence = "CRITIQUE" if jr <= 7 else "AVERTISSEMENT"
                alerts.append(Alert(
                    id=r.get('personnel_id'), categorie="RQTH",
                    type_alerte="RQTH_EXPIRANT", urgence=urgence,
                    titre="RQTH expirant", description=f"Expire dans {jr}j",
                    personnel_id=r.get('personnel_id'),
                    personnel_nom=r.get('nom', ''), personnel_prenom=r.get('prenom', ''),
                    date_alerte=date.today(), date_echeance=r.get('date_fin_rqth'),
                    jours_restants=jr, data={'matricule': r.get('matricule')}
                ))

        if not type_doc or type_doc == "ENTRETIEN":
            from domain.services.rh.vie_salarie_service import get_entretiens_a_planifier
            for e in get_entretiens_a_planifier(jours_avance=jours):
                jr = e.get('jours_restants') or 0
                urgence = "CRITIQUE" if jr <= 0 else "AVERTISSEMENT"
                desc = "En retard" if jr <= 0 else f"Prévu dans {jr}j"
                alerts.append(Alert(
                    id=e.get('operateur_id'), categorie="ENTRETIEN",
                    type_alerte="ENTRETIEN_A_PLANIFIER", urgence=urgence,
                    titre=f"Entretien {e.get('type_entretien', '')}", description=desc,
                    personnel_id=e.get('operateur_id'),
                    personnel_nom=e.get('nom', ''), personnel_prenom=e.get('prenom', ''),
                    date_alerte=date.today(), date_echeance=e.get('prochaine_date'),
                    jours_restants=jr,
                    data={'matricule': e.get('matricule'), 'type_entretien': e.get('type_entretien')}
                ))

        if not type_doc or type_doc == "MUTUELLE":
            alerts.extend(RHAlerts._get_mutuelles_expirant(jours))

        if not type_doc or type_doc == "SANS_MUTUELLE":
            alerts.extend(RHAlerts.get_personnel_sans_mutuelle())

        if not type_doc or type_doc == "SANS_VISITE":
            alerts.extend(RHAlerts.get_personnel_sans_visite_medicale())

        if not type_doc or type_doc == "SANS_ENTRETIEN":
            alerts.extend(RHAlerts.get_personnel_sans_entretien())

        def sort_key(a: Alert):
            return (a.urgence_ordre, a.jours_restants if a.jours_restants is not None else 9999)

        return sorted(alerts, key=sort_key)
