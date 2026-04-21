# -*- coding: utf-8 -*-
from datetime import date
from typing import List, Optional

from domain.models import Alert
from infrastructure.logging.logging_config import get_logger
from domain.services.admin.alerts.contrat_alerts import ContratAlerts
from domain.services.admin.alerts.rh_alerts import RHAlerts

logger = get_logger(__name__)


class DocumentAlerts:
    """Agrégation de toutes les alertes documents RH."""

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
