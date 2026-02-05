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

import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from core.db.configbd import DatabaseCursor
from core.models import Alert, StatistiquesAlertes
from core.utils.performance_monitor import monitor_query

logger = logging.getLogger(__name__)


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
        query = """
            SELECT c.id, c.operateur_id, c.type_contrat, c.date_debut, c.date_fin,
                   p.nom, p.prenom, p.matricule,
                   DATEDIFF(CURDATE(), c.date_fin) as jours_expires
            FROM contrat c
            JOIN personnel p ON c.operateur_id = p.id
            WHERE c.actif = 1
              AND c.date_fin IS NOT NULL
              AND c.date_fin < CURDATE()
              AND p.statut = 'ACTIF'
            ORDER BY c.date_fin ASC
        """

        alerts = []
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query)
            for row in cur.fetchall():
                alerts.append(Alert(
                    id=row['id'],
                    categorie="CONTRAT",
                    type_alerte=TypeAlerte.CONTRAT_EXPIRE,
                    urgence="CRITIQUE",
                    titre=f"Contrat expiré ({row['type_contrat']})",
                    description=f"Contrat expiré depuis {row['jours_expires']} jour(s)",
                    personnel_id=row['operateur_id'],
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

        query = """
            SELECT c.id, c.operateur_id, c.type_contrat, c.date_debut, c.date_fin,
                   p.nom, p.prenom, p.matricule,
                   DATEDIFF(c.date_fin, CURDATE()) as jours_restants
            FROM contrat c
            JOIN personnel p ON c.operateur_id = p.id
            WHERE c.actif = 1
              AND c.date_fin IS NOT NULL
              AND c.date_fin BETWEEN CURDATE() AND %s
              AND p.statut = 'ACTIF'
            ORDER BY c.date_fin ASC
        """

        alerts = []
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (date_limite,))
            for row in cur.fetchall():
                jours_restants = row['jours_restants']

                # Déterminer l'urgence
                if jours_restants <= 7:
                    urgence = "CRITIQUE"
                    type_alerte = TypeAlerte.CONTRAT_EXPIRE_7J
                else:
                    urgence = "AVERTISSEMENT"
                    type_alerte = TypeAlerte.CONTRAT_EXPIRE_30J

                alerts.append(Alert(
                    id=row['id'],
                    categorie="CONTRAT",
                    type_alerte=type_alerte,
                    urgence=urgence,
                    titre=f"Contrat {row['type_contrat']} expire bientôt",
                    description=f"Expire dans {jours_restants} jour(s)",
                    personnel_id=row['operateur_id'],
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

        return alerts

    @staticmethod
    @monitor_query('AlertService.get_personnel_sans_contrat')
    def get_personnel_sans_contrat() -> List[Alert]:
        """
        Récupère le personnel actif sans contrat actif.

        Returns:
            Liste d'alertes de type PERSONNEL_SANS_CONTRAT (urgence AVERTISSEMENT)
        """
        query = """
            SELECT
                p.id,
                p.nom,
                p.prenom,
                p.matricule,
                pi.date_entree
            FROM personnel p
            LEFT JOIN contrat c
                   ON c.operateur_id = p.id
                  AND c.actif = 1
            LEFT JOIN personnel_infos pi
                   ON pi.personnel_id = p.id
            WHERE p.statut = 'ACTIF'
              AND c.id IS NULL
            ORDER BY p.nom, p.prenom;
        """

        alerts = []
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query)
            for row in cur.fetchall():
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
        query = """
            SELECT p.id, p.nom, p.prenom, p.matricule, pi.date_entree
            FROM personnel p
            LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
            LEFT JOIN polyvalence poly ON poly.operateur_id = p.id
            WHERE p.statut = 'ACTIF'
              AND poly.id IS NULL
            ORDER BY pi.date_entree DESC, p.nom
        """

        alerts = []
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query)
            for row in cur.fetchall():
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

        query = """
            SELECT p.id, p.nom, p.prenom, p.matricule, pi.date_entree,
                   DATEDIFF(CURDATE(), pi.date_entree) as jours_depuis_entree
            FROM personnel p
            JOIN personnel_infos pi ON pi.personnel_id = p.id
            LEFT JOIN polyvalence poly ON poly.operateur_id = p.id
            WHERE p.statut = 'ACTIF'
              AND pi.date_entree IS NOT NULL
              AND pi.date_entree >= %s
              AND poly.id IS NULL
            ORDER BY pi.date_entree DESC
        """

        alerts = []
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (date_limite,))
            for row in cur.fetchall():
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
        alerts = []

        # Contrats expirés
        alerts.extend(AlertService.get_contrats_expires())

        # Contrats expirant dans 30 jours
        alerts.extend(AlertService.get_contrats_expirant(30))

        # Personnel sans contrat (catégorisé ici car lié aux contrats)
        alerts.extend(AlertService.get_personnel_sans_contrat())

        # Filtrer par type si demandé
        if type_contrat:
            alerts = [a for a in alerts if a.data.get('type_contrat') == type_contrat or a.type_alerte == TypeAlerte.PERSONNEL_SANS_CONTRAT]

        # Trier par urgence puis par jours restants
        def sort_key(alert):
            urgence_order = alert.urgence_ordre
            jours = alert.jours_restants if alert.jours_restants is not None else 9999
            return (urgence_order, jours)

        return sorted(alerts, key=sort_key)

    @staticmethod
    def get_all_personnel_alerts() -> List[Alert]:
        """
        Récupère toutes les alertes liées au personnel.

        Returns:
            Liste combinée d'alertes triées par urgence
        """
        alerts = []

        # Personnel sans contrat
        alerts.extend(AlertService.get_personnel_sans_contrat())

        # Personnel sans compétences
        alerts.extend(AlertService.get_personnel_sans_competences())

        # Nouveaux sans affectation (30 jours)
        alerts.extend(AlertService.get_nouveaux_sans_affectation(30))

        # Dédupliquer (un personnel peut être dans plusieurs listes)
        seen_ids = {}
        unique_alerts = []
        for alert in alerts:
            key = (alert.personnel_id, alert.type_alerte)
            if key not in seen_ids:
                seen_ids[key] = True
                unique_alerts.append(alert)

        # Trier par urgence
        return sorted(unique_alerts, key=lambda a: a.urgence_ordre)

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

        return stats

    @staticmethod
    def get_quick_counts() -> Dict[str, int]:
        """
        Récupère rapidement les comptages pour le dashboard (optimisé).

        Returns:
            Dict avec 'critiques', 'avertissements', 'infos'
        """
        counts = {'critiques': 0, 'avertissements': 0, 'infos': 0}

        with DatabaseCursor(dictionary=True) as cur:
            # Contrats expirés (CRITIQUE)
            cur.execute("""
                SELECT COUNT(*) as count FROM contrat c
                JOIN personnel p ON c.operateur_id = p.id
                WHERE c.actif = 1 AND c.date_fin < CURDATE() AND p.statut = 'ACTIF'
            """)
            counts['critiques'] += cur.fetchone()['count']

            # Contrats expirant < 7j (CRITIQUE)
            cur.execute("""
                SELECT COUNT(*) as count FROM contrat c
                JOIN personnel p ON c.operateur_id = p.id
                WHERE c.actif = 1
                  AND c.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
                  AND p.statut = 'ACTIF'
            """)
            counts['critiques'] += cur.fetchone()['count']

            # Contrats expirant 8-30j (AVERTISSEMENT)
            cur.execute("""
                SELECT COUNT(*) as count FROM contrat c
                JOIN personnel p ON c.operateur_id = p.id
                WHERE c.actif = 1
                  AND c.date_fin BETWEEN DATE_ADD(CURDATE(), INTERVAL 8 DAY) AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                  AND p.statut = 'ACTIF'
            """)
            counts['avertissements'] += cur.fetchone()['count']

            # Personnel sans contrat (AVERTISSEMENT)
            cur.execute("""
                SELECT COUNT(*) as count FROM personnel p
                LEFT JOIN contrat c ON c.operateur_id = p.id AND c.actif = 1
                WHERE p.statut = 'ACTIF' AND c.id IS NULL
            """)
            counts['avertissements'] += cur.fetchone()['count']

            # Personnel sans compétences (INFO)
            cur.execute("""
                SELECT COUNT(*) as count FROM personnel p
                LEFT JOIN polyvalence poly ON poly.operateur_id = p.id
                WHERE p.statut = 'ACTIF' AND poly.id IS NULL
            """)
            counts['infos'] += cur.fetchone()['count']

        return counts
