# -*- coding: utf-8 -*-
"""
Service de gestion des alertes RH.

Ce service centralise la récupération et l'agrégation de toutes les alertes RH:
- Contrats (expirés, expirant bientôt, personnel sans contrat)
- Personnel (sans compétences, nouveaux sans affectation)

Usage:
    from core.services.alert_service import AlertService

    # Récupérer toutes les alertes contrats
    alertes = AlertService.get_contract_alerts()

    # Récupérer les statistiques
    stats = AlertService.get_statistics()
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from core.db.query_executor import QueryExecutor
from core.models import Alert, StatistiquesAlertes
from core.utils.performance_monitor import monitor_query
from core.utils.logging_config import get_logger

logger = get_logger(__name__)


# ===========================
# Types d'alertes
# ===========================

class TypeAlerte:
    """Types d'alertes disponibles"""
    # Contrats
    CONTRAT_EXPIRE = "CONTRAT_EXPIRE"
    CONTRAT_EXPIRE_7J = "CONTRAT_EXPIRE_7J"
    CONTRAT_EXPIRE_30J = "CONTRAT_EXPIRE_30J"

    # Personnel
    PERSONNEL_SANS_CONTRAT = "PERSONNEL_SANS_CONTRAT"
    PERSONNEL_SANS_COMPETENCES = "PERSONNEL_SANS_COMPETENCES"
    PERSONNEL_NOUVEAU_SANS_AFFECTATION = "PERSONNEL_NOUVEAU_SANS_AFFECTATION"


# ===========================
# Service d'alertes
# ===========================

class AlertService:
    """
    Service pour la gestion centralisée des alertes RH.

    Toutes les méthodes sont statiques pour faciliter l'utilisation.
    """

    # ===========================
    # Alertes Contrats
    # ===========================

    @staticmethod
    @monitor_query('AlertService.get_contrats_expires')
    def get_contrats_expires() -> List[Alert]:
        """
        Récupère les contrats déjà expirés mais encore marqués actifs.

        Returns:
            Liste d'alertes de type CONTRAT_EXPIRE (urgence CRITIQUE)
        """
        logger.debug("get_contrats_expires: début de la requête")
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
            logger.debug(
                f"  contrat expiré: {row['prenom']} {row['nom']} (matricule={row['matricule']}, "
                f"type={row['type_contrat']}, date_fin={row['date_fin']}, "
                f"jours_expires={row['jours_expires']})"
            )
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
            logger.debug("get_contrats_expires: aucun contrat expiré")

        return alerts

    @staticmethod
    @monitor_query('AlertService.get_contrats_expirant')
    def get_contrats_expirant(jours: int = 30) -> List[Alert]:
        """
        Récupère les contrats expirant dans les N prochains jours.

        Args:
            jours: Nombre de jours à regarder

        Returns:
            Liste d'alertes CRITIQUE (<= 7j) ou AVERTISSEMENT (8-30j)
        """
        date_limite = date.today() + timedelta(days=jours)
        logger.debug(f"get_contrats_expirant: horizon={jours}j, date_limite={date_limite}")

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
        nb_critiques = 0
        nb_avertissements = 0
        for row in rows:
            jours_restants = row['jours_restants']

            # Déterminer l'urgence
            if jours_restants <= 7:
                urgence = "CRITIQUE"
                type_alerte = TypeAlerte.CONTRAT_EXPIRE_7J
                nb_critiques += 1
            else:
                urgence = "AVERTISSEMENT"
                type_alerte = TypeAlerte.CONTRAT_EXPIRE_30J
                nb_avertissements += 1

            logger.debug(
                f"  contrat expirant: {row['prenom']} {row['nom']} (matricule={row['matricule']}, "
                f"type={row['type_contrat']}, date_fin={row['date_fin']}, "
                f"jours_restants={jours_restants}, urgence={urgence})"
            )
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
            logger.debug(f"get_contrats_expirant({jours}j): aucun contrat expirant")

        return alerts

    @staticmethod
    @monitor_query('AlertService.get_personnel_sans_contrat')
    def get_personnel_sans_contrat() -> List[Alert]:
        """
        Récupère le personnel actif sans contrat actif.

        Returns:
            Liste d'alertes de type PERSONNEL_SANS_CONTRAT (urgence AVERTISSEMENT)
        """
        logger.debug("get_personnel_sans_contrat: début de la requête")
        query = """
            SELECT
                p.id,
                p.nom,
                p.prenom,
                p.matricule,
                pi.date_entree
            FROM personnel p
            LEFT JOIN contrat c
                   ON c.personnel_id = p.id
                  AND c.actif = 1
            LEFT JOIN personnel_infos pi
                   ON pi.personnel_id = p.id
            WHERE p.statut = 'ACTIF'
              AND c.id IS NULL
            ORDER BY p.nom, p.prenom;
        """

        try:
            rows = QueryExecutor.fetch_all(query, dictionary=True)
        except Exception as e:
            logger.exception(f"get_personnel_sans_contrat: erreur DB — {e}")
            return []

        alerts = []
        for row in rows:
            logger.debug(
                f"  sans contrat: {row['prenom']} {row['nom']} "
                f"(matricule={row['matricule']}, date_entree={row['date_entree']})"
            )
            alerts.append(Alert(
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
            ))

        if alerts:
            logger.info(f"get_personnel_sans_contrat: {len(alerts)} personnel(s) sans contrat actif")
        else:
            logger.debug("get_personnel_sans_contrat: tout le personnel actif a un contrat")

        return alerts

    # ===========================
    # Alertes Personnel
    # ===========================

    @staticmethod
    @monitor_query('AlertService.get_personnel_sans_competences')
    def get_personnel_sans_competences() -> List[Alert]:
        """
        Récupère le personnel actif sans aucune compétence (polyvalence).

        Returns:
            Liste d'alertes de type PERSONNEL_SANS_COMPETENCES (urgence INFO)
        """
        logger.debug("get_personnel_sans_competences: début de la requête")
        query = """
            SELECT p.id, p.nom, p.prenom, p.matricule, pi.date_entree
            FROM personnel p
            LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
            LEFT JOIN polyvalence poly ON poly.personnel_id = p.id
            WHERE p.statut = 'ACTIF'
              AND poly.id IS NULL
            ORDER BY pi.date_entree DESC, p.nom
        """

        try:
            rows = QueryExecutor.fetch_all(query, dictionary=True)
        except Exception as e:
            logger.exception(f"get_personnel_sans_competences: erreur DB — {e}")
            return []

        alerts = []
        for row in rows:
            logger.debug(
                f"  sans compétences: {row['prenom']} {row['nom']} "
                f"(matricule={row['matricule']}, date_entree={row['date_entree']})"
            )
            alerts.append(Alert(
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
            ))

        if alerts:
            logger.info(f"get_personnel_sans_competences: {len(alerts)} personnel(s) sans polyvalence")
        else:
            logger.debug("get_personnel_sans_competences: tout le personnel actif a des compétences")

        return alerts

    @staticmethod
    @monitor_query('AlertService.get_nouveaux_sans_affectation')
    def get_nouveaux_sans_affectation(jours: int = 30) -> List[Alert]:
        """
        Récupère les nouveaux employés (< N jours) sans aucune compétence.

        Args:
            jours: Nombre de jours depuis l'entrée

        Returns:
            Liste d'alertes de type PERSONNEL_NOUVEAU_SANS_AFFECTATION (urgence INFO)
        """
        date_limite = date.today() - timedelta(days=jours)
        logger.debug(f"get_nouveaux_sans_affectation: fenêtre={jours}j, depuis={date_limite}")

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

        alerts = []
        for row in rows:
            logger.debug(
                f"  nouveau sans affectation: {row['prenom']} {row['nom']} "
                f"(matricule={row['matricule']}, date_entree={row['date_entree']}, "
                f"jours_depuis_entree={row['jours_depuis_entree']})"
            )
            alerts.append(Alert(
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
            ))

        if alerts:
            logger.info(
                f"get_nouveaux_sans_affectation({jours}j): {len(alerts)} nouveau(x) sans compétences"
            )
        else:
            logger.debug(f"get_nouveaux_sans_affectation({jours}j): aucun nouveau sans affectation")

        return alerts

    # ===========================
    # Agrégation
    # ===========================

    @staticmethod
    def get_all_contract_alerts(type_contrat: Optional[str] = None) -> List[Alert]:
        """
        Récupère toutes les alertes liées aux contrats.

        Args:
            type_contrat: Filtrer par type (CDI, CDD, INTERIM, etc.)

        Returns:
            Liste combinée d'alertes triées par urgence puis par jours restants
        """
        logger.debug(f"get_all_contract_alerts: agrégation (filtre type_contrat={type_contrat!r})")
        alerts = []

        # Contrats expirés
        expires = AlertService.get_contrats_expires()
        alerts.extend(expires)

        # Contrats expirant dans 30 jours
        expirant = AlertService.get_contrats_expirant(30)
        alerts.extend(expirant)

        # Personnel sans contrat (catégorisé ici car lié aux contrats)
        sans_contrat = AlertService.get_personnel_sans_contrat()
        alerts.extend(sans_contrat)

        logger.debug(
            f"get_all_contract_alerts: brut — {len(expires)} expirés, "
            f"{len(expirant)} expirant, {len(sans_contrat)} sans contrat"
        )

        # Filtrer par type si demandé
        if type_contrat:
            avant = len(alerts)
            alerts = [a for a in alerts if a.data.get('type_contrat') == type_contrat or a.type_alerte == TypeAlerte.PERSONNEL_SANS_CONTRAT]
            logger.debug(f"get_all_contract_alerts: filtre '{type_contrat}' — {avant} → {len(alerts)} alertes")

        # Trier par urgence puis par jours restants
        def sort_key(alert):
            urgence_order = alert.urgence_ordre
            jours = alert.jours_restants if alert.jours_restants is not None else 9999
            return (urgence_order, jours)

        result = sorted(alerts, key=sort_key)
        logger.info(f"get_all_contract_alerts: {len(result)} alerte(s) contrat au total")
        return result

    @staticmethod
    def get_all_personnel_alerts() -> List[Alert]:
        """
        Récupère toutes les alertes liées au personnel.

        Returns:
            Liste combinée d'alertes triées par urgence
        """
        logger.debug("get_all_personnel_alerts: agrégation")
        alerts = []

        # Personnel sans contrat
        sans_contrat = AlertService.get_personnel_sans_contrat()
        alerts.extend(sans_contrat)

        # Nouveaux sans affectation (30 jours)
        nouveaux = AlertService.get_nouveaux_sans_affectation(30)
        alerts.extend(nouveaux)

        logger.debug(
            f"get_all_personnel_alerts: brut — {len(sans_contrat)} sans contrat, "
            f"{len(nouveaux)} nouveaux sans affectation"
        )

        # Dédupliquer (un personnel peut être dans plusieurs listes)
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
            logger.debug(f"get_all_personnel_alerts: {doublons} doublon(s) supprimé(s)")

        result = sorted(unique_alerts, key=lambda a: a.urgence_ordre)
        logger.info(f"get_all_personnel_alerts: {len(result)} alerte(s) personnel au total")
        return result

    # ===========================
    # Statistiques
    # ===========================

    @staticmethod
    @monitor_query('AlertService.get_statistics')
    def get_statistics() -> Dict[str, StatistiquesAlertes]:
        """
        Calcule les statistiques d'alertes par catégorie.

        Returns:
            Dict avec clés 'contrats', 'personnel', 'total'
        """
        logger.debug("get_statistics: calcul des statistiques d'alertes")
        stats = {
            'contrats': StatistiquesAlertes(),
            'personnel': StatistiquesAlertes(),
            'total': StatistiquesAlertes()
        }

        # Alertes contrats
        contract_alerts = AlertService.get_all_contract_alerts()
        stats['contrats'].total = len(contract_alerts)
        stats['contrats'].critiques = len([a for a in contract_alerts if a.urgence == "CRITIQUE"])
        stats['contrats'].avertissements = len([a for a in contract_alerts if a.urgence == "AVERTISSEMENT"])
        stats['contrats'].infos = len([a for a in contract_alerts if a.urgence == "INFO"])

        # Alertes personnel
        personnel_alerts = AlertService.get_all_personnel_alerts()
        stats['personnel'].total = len(personnel_alerts)
        stats['personnel'].critiques = len([a for a in personnel_alerts if a.urgence == "CRITIQUE"])
        stats['personnel'].avertissements = len([a for a in personnel_alerts if a.urgence == "AVERTISSEMENT"])
        stats['personnel'].infos = len([a for a in personnel_alerts if a.urgence == "INFO"])

        # Total (attention aux doublons)
        all_alerts = contract_alerts + [a for a in personnel_alerts if a.type_alerte != TypeAlerte.PERSONNEL_SANS_CONTRAT]
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
        """
        Récupère rapidement les comptages pour le dashboard (optimisé).

        Returns:
            Dict avec 'critiques', 'avertissements', 'infos'
        """
        logger.debug("get_quick_counts: calcul rapide des comptages")
        counts = {'critiques': 0, 'avertissements': 0, 'infos': 0}

        try:
            # Contrats expirés (CRITIQUE)
            n = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM v_contrats_fin_proche
                WHERE jours_restants < 0
            """, default=0)
            logger.debug(f"  contrats expirés (CRITIQUE): {n}")
            counts['critiques'] += n

            # Contrats expirant < 7j (CRITIQUE)
            n = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM v_contrats_fin_proche
                WHERE jours_restants BETWEEN 0 AND 7
            """, default=0)
            logger.debug(f"  contrats expirant ≤7j (CRITIQUE): {n}")
            counts['critiques'] += n

            # Contrats expirant 8-30j (AVERTISSEMENT)
            n = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM v_contrats_fin_proche
                WHERE jours_restants BETWEEN 8 AND 30
            """, default=0)
            logger.debug(f"  contrats expirant 8-30j (AVERTISSEMENT): {n}")
            counts['avertissements'] += n

            # Personnel sans contrat (AVERTISSEMENT)
            n = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM personnel p
                LEFT JOIN contrat c ON c.personnel_id = p.id AND c.actif = 1
                WHERE p.statut = 'ACTIF' AND c.id IS NULL
            """, default=0)
            logger.debug(f"  personnel sans contrat (AVERTISSEMENT): {n}")
            counts['avertissements'] += n

        except Exception as e:
            logger.exception(f"get_quick_counts: erreur DB — {e}")

        logger.info(
            f"get_quick_counts: critiques={counts['critiques']}, "
            f"avertissements={counts['avertissements']}, infos={counts['infos']}"
        )
        return counts

    @staticmethod
    def get_startup_summary() -> Dict[str, int]:
        """
        Résumé détaillé par catégorie pour le popup de démarrage.

        Returns:
            Dict avec 'evaluations_retard', 'contrats_expires', 'contrats_expirant',
            'personnel_sans_contrat', 'total_critique', 'total_avertissement'
        """
        logger.debug("get_startup_summary: calcul du résumé de démarrage")
        result = {}

        try:
            # Évaluations en retard (CRITIQUE)
            result['evaluations_retard'] = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM polyvalence poly
                JOIN personnel p ON p.id = poly.personnel_id
                WHERE poly.prochaine_evaluation < CURDATE() AND p.statut = 'ACTIF'
            """, default=0)

            # Contrats expirés (CRITIQUE)
            result['contrats_expires'] = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM v_contrats_fin_proche
                WHERE jours_restants < 0
            """, default=0)

            # Contrats expirant dans 30j (AVERTISSEMENT)
            result['contrats_expirant'] = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM v_contrats_fin_proche
                WHERE jours_restants BETWEEN 0 AND 30
            """, default=0)

            # Personnel sans contrat actif (AVERTISSEMENT)
            result['personnel_sans_contrat'] = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM personnel p
                LEFT JOIN contrat c ON c.personnel_id = p.id AND c.actif = 1
                WHERE p.statut = 'ACTIF' AND c.id IS NULL
            """, default=0)

        except Exception as e:
            logger.exception(f"get_startup_summary: erreur DB — {e}")
            result.setdefault('evaluations_retard', 0)
            result.setdefault('contrats_expires', 0)
            result.setdefault('contrats_expirant', 0)
            result.setdefault('personnel_sans_contrat', 0)

        result['total_critique'] = result['evaluations_retard'] + result['contrats_expires']
        result['total_avertissement'] = result['contrats_expirant'] + result['personnel_sans_contrat']

        logger.info(
            f"get_startup_summary: éval_retard={result['evaluations_retard']}, "
            f"contrats_expirés={result['contrats_expires']}, "
            f"contrats_expirant={result['contrats_expirant']}, "
            f"sans_contrat={result['personnel_sans_contrat']} | "
            f"total_critique={result['total_critique']}, "
            f"total_avertissement={result['total_avertissement']}"
        )
        return result
