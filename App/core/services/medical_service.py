# -*- coding: utf-8 -*-
"""
Service Médical pour la gestion du suivi médical des salariés.

Gère:
- Visites médicales (VIP)
- Maladies professionnelles
- Accidents du travail
- RQTH/OETH
- Alertes médicales

Source: Tableau SIRH.xlsx - Feuille "Medical"

Refactorisé: Utilise QueryExecutor au lieu de DatabaseCursor/DatabaseConnection.
"""

from datetime import date, datetime
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal

from core.db.query_executor import QueryExecutor
from core.services.permission_manager import require
from core.utils.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# 0. VALIDITÉS (accès rapide depuis la fiche personnel)
# ============================================================

def get_validites_operateur(operateur_id: int) -> List[Dict[str, Any]]:
    """
    Retourne toutes les validités d'un opérateur (table validite).

    Args:
        operateur_id: ID de l'opérateur

    Returns:
        Liste de dicts avec type_validite, date_debut, date_fin,
        periodicite, taux_incapacite
    """
    return QueryExecutor.fetch_all(
        """
        SELECT type_validite, date_debut, date_fin, periodicite, taux_incapacite
        FROM validite
        WHERE operateur_id = %s
        ORDER BY date_debut DESC
        """,
        (operateur_id,),
        dictionary=True,
    )


# ============================================================
# 1. DONNÉES MÉDICALES PRINCIPALES
# ============================================================

def get_donnees_medicales(operateur_id: int) -> Dict[str, Any]:
    """
    Récupère toutes les données médicales d'un opérateur.

    Args:
        operateur_id: ID de l'opérateur

    Returns:
        Dictionnaire avec les données médicales
    """
    try:
        # Données principales (table medical)
        medical = QueryExecutor.fetch_one(
            "SELECT m.* FROM medical m WHERE m.operateur_id = %s",
            (operateur_id,), dictionary=True
        )

        # RQTH/OETH depuis table validite existante
        rqth = QueryExecutor.fetch_one(
            """SELECT * FROM validite
               WHERE operateur_id = %s AND type_validite = 'RQTH'
               ORDER BY date_debut DESC LIMIT 1""",
            (operateur_id,), dictionary=True
        )

        oeth = QueryExecutor.fetch_one(
            """SELECT * FROM validite
               WHERE operateur_id = %s AND type_validite = 'OETH'
               ORDER BY date_debut DESC LIMIT 1""",
            (operateur_id,), dictionary=True
        )

        # Dernière visite
        derniere_visite = QueryExecutor.fetch_one(
            """SELECT * FROM medical_visite
               WHERE operateur_id = %s
               ORDER BY date_visite DESC LIMIT 1""",
            (operateur_id,), dictionary=True
        )

        # Statistiques visites
        stats_visites = QueryExecutor.fetch_one(
            """SELECT
                   COUNT(*) as total_visites,
                   MIN(date_visite) as premiere_visite,
                   MAX(date_visite) as derniere_visite
               FROM medical_visite
               WHERE operateur_id = %s""",
            (operateur_id,), dictionary=True
        )

        # Accidents du travail
        stats_at = QueryExecutor.fetch_one(
            """SELECT COUNT(*) as nb_accidents,
                      SUM(CASE WHEN avec_arret = 1 THEN 1 ELSE 0 END) as nb_avec_arret,
                      SUM(COALESCE(nb_jours_absence, 0)) as total_jours_absence
               FROM medical_accident_travail
               WHERE operateur_id = %s""",
            (operateur_id,), dictionary=True
        )

        # Maladies professionnelles
        stats_mp = QueryExecutor.fetch_one(
            """SELECT COUNT(*) as nb_mp
               FROM medical_maladie_pro
               WHERE operateur_id = %s""",
            (operateur_id,), dictionary=True
        )

        # Convertir Decimal en float
        if medical:
            for key in ['taux_professionnel']:
                if medical.get(key) and isinstance(medical[key], Decimal):
                    medical[key] = float(medical[key])

        if rqth and rqth.get('taux_incapacite'):
            rqth['taux_incapacite'] = float(rqth['taux_incapacite'])

        return {
            "medical": medical,
            "rqth": rqth,
            "oeth": oeth,
            "derniere_visite": derniere_visite,
            "statistiques": {
                "visites": stats_visites,
                "accidents": stats_at,
                "maladies_pro": stats_mp
            }
        }

    except Exception as e:
        logger.exception(f"Erreur get_donnees_medicales: {e}")
        return {"error": str(e), "medical": None}


def get_ou_creer_medical(operateur_id: int) -> Optional[Dict]:
    """
    Récupère ou crée l'enregistrement médical d'un opérateur.

    Args:
        operateur_id: ID de l'opérateur

    Returns:
        Dictionnaire avec les données médicales
    """
    try:
        medical = QueryExecutor.fetch_one(
            "SELECT * FROM medical WHERE operateur_id = %s",
            (operateur_id,), dictionary=True
        )

        if not medical:
            QueryExecutor.execute_write(
                "INSERT INTO medical (operateur_id) VALUES (%s)",
                (operateur_id,)
            )
            medical = QueryExecutor.fetch_one(
                "SELECT * FROM medical WHERE operateur_id = %s",
                (operateur_id,), dictionary=True
            )

        return medical

    except Exception as e:
        logger.exception(f"Erreur get_ou_creer_medical: {e}")
        return None


def update_donnees_medicales(operateur_id: int, data: Dict) -> Tuple[bool, str]:
    """
    Met à jour les données médicales d'un opérateur.

    Args:
        operateur_id: ID de l'opérateur
        data: Dictionnaire avec les champs à mettre à jour

    Returns:
        (succès, message)
    """
    require('rh.medical.edit')
    # Whitelist des colonnes autorisées
    ALLOWED_COLUMNS = frozenset([
        'type_suivi_vip', 'periodicite_vip_mois', 'date_electrocardiogramme',
        'maladie_pro', 'date_debut_rqth', 'date_fin_rqth',
        'date_debut_oeth', 'date_fin_oeth', 'taux_incapacite',
        'taux_professionnel', 'besoins_adaptation', 'demande_reconnaissance_atmp_en_cours'
    ])

    try:
        exists = QueryExecutor.fetch_one(
            "SELECT id FROM medical WHERE operateur_id = %s",
            (operateur_id,), dictionary=True
        )

        if exists:
            # UPDATE
            fields = []
            values = []
            for key in ALLOWED_COLUMNS:
                if key in data:
                    fields.append(f"{key} = %s")
                    values.append(data[key] if data[key] != '' else None)

            if fields:
                values.append(operateur_id)
                sql = "UPDATE medical SET " + ", ".join(fields) + " WHERE operateur_id = %s"
                QueryExecutor.execute_write(sql, tuple(values), return_lastrowid=False)
        else:
            # INSERT
            columns = ['operateur_id']
            values = [operateur_id]
            placeholders = ['%s']

            for key in ALLOWED_COLUMNS:
                if key in data:
                    columns.append(key)
                    values.append(data[key] if data[key] != '' else None)
                    placeholders.append('%s')

            sql = "INSERT INTO medical (" + ", ".join(columns) + ") VALUES (" + ", ".join(placeholders) + ")"
            QueryExecutor.execute_write(sql, tuple(values))

        return True, "Données médicales mises à jour"

    except Exception as e:
        logger.exception(f"Erreur update_donnees_medicales: {e}")
        return False, f"Erreur: {str(e)}"


# ============================================================
# 2. VISITES MÉDICALES
# ============================================================

def get_visites(operateur_id: int) -> List[Dict]:
    """Récupère l'historique des visites médicales."""
    try:
        return QueryExecutor.fetch_all(
            """SELECT * FROM medical_visite
               WHERE operateur_id = %s
               ORDER BY date_visite DESC""",
            (operateur_id,), dictionary=True
        )
    except Exception as e:
        logger.exception(f"Erreur get_visites: {e}")
        return []


def create_visite(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée une nouvelle visite médicale."""
    try:
        require('rh.medical.edit')
        visite_id = QueryExecutor.execute_write(
            """INSERT INTO medical_visite (
                   operateur_id, date_visite, type_visite, resultat,
                   restrictions, medecin, commentaire, prochaine_visite
               ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                operateur_id,
                data.get('date_visite'),
                data.get('type_visite', 'Périodique'),
                data.get('resultat'),
                data.get('restrictions'),
                data.get('medecin'),
                data.get('commentaire'),
                data.get('prochaine_visite')
            )
        )
        return True, "Visite enregistrée", visite_id

    except Exception as e:
        logger.exception(f"Erreur create_visite: {e}")
        return False, f"Erreur: {str(e)}", None


def update_visite(visite_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour une visite médicale."""
    try:
        require('rh.medical.edit')
        QueryExecutor.execute_write(
            """UPDATE medical_visite SET
                   date_visite = %s, type_visite = %s, resultat = %s,
                   restrictions = %s, medecin = %s, commentaire = %s,
                   prochaine_visite = %s
               WHERE id = %s""",
            (
                data.get('date_visite'),
                data.get('type_visite'),
                data.get('resultat'),
                data.get('restrictions'),
                data.get('medecin'),
                data.get('commentaire'),
                data.get('prochaine_visite'),
                visite_id
            ),
            return_lastrowid=False
        )
        return True, "Visite mise à jour"

    except Exception as e:
        logger.exception(f"Erreur update_visite: {e}")
        return False, f"Erreur: {str(e)}"


def delete_visite(visite_id: int) -> Tuple[bool, str]:
    """Supprime une visite médicale."""
    try:
        require('rh.medical.delete')
        QueryExecutor.execute_write(
            "DELETE FROM medical_visite WHERE id = %s",
            (visite_id,), return_lastrowid=False
        )
        return True, "Visite supprimée"

    except Exception as e:
        logger.exception(f"Erreur delete_visite: {e}")
        return False, f"Erreur: {str(e)}"


# ============================================================
# 3. ACCIDENTS DU TRAVAIL
# ============================================================

def get_accidents(operateur_id: int) -> List[Dict]:
    """Récupère l'historique des accidents du travail."""
    try:
        return QueryExecutor.fetch_all(
            """SELECT at.*,
                      (SELECT COUNT(*) FROM medical_prolongation_arret p
                       WHERE p.accident_id = at.id) as nb_prolongations
               FROM medical_accident_travail at
               WHERE at.operateur_id = %s
               ORDER BY at.date_accident DESC""",
            (operateur_id,), dictionary=True
        )
    except Exception as e:
        logger.exception(f"Erreur get_accidents: {e}")
        return []


def get_accident_detail(accident_id: int) -> Optional[Dict]:
    """Récupère le détail d'un accident avec ses prolongations."""
    try:
        accident = QueryExecutor.fetch_one(
            "SELECT * FROM medical_accident_travail WHERE id = %s",
            (accident_id,), dictionary=True
        )

        if accident:
            accident['prolongations'] = QueryExecutor.fetch_all(
                """SELECT * FROM medical_prolongation_arret
                   WHERE accident_id = %s
                   ORDER BY numero_prolongation""",
                (accident_id,), dictionary=True
            )

        return accident

    except Exception as e:
        logger.exception(f"Erreur get_accident_detail: {e}")
        return None


def create_accident(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée un nouvel accident du travail."""
    try:
        require('rh.medical.edit')
        accident_id = QueryExecutor.execute_write(
            """INSERT INTO medical_accident_travail (
                   operateur_id, date_accident, heure_accident, jour_semaine,
                   horaires, circonstances, siege_lesions, nature_lesions,
                   avec_arret, date_reconnaissance_at, date_debut_arret,
                   date_fin_arret_initial, commentaire
               ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                operateur_id,
                data.get('date_accident'),
                data.get('heure_accident'),
                data.get('jour_semaine'),
                data.get('horaires'),
                data.get('circonstances'),
                data.get('siege_lesions'),
                data.get('nature_lesions'),
                data.get('avec_arret', 0),
                data.get('date_reconnaissance_at'),
                data.get('date_debut_arret'),
                data.get('date_fin_arret_initial'),
                data.get('commentaire')
            )
        )

        # Calculer nb_jours_absence si avec arrêt
        if data.get('avec_arret') and data.get('date_debut_arret') and data.get('date_fin_arret_initial'):
            _recalculer_jours_absence(accident_id)

        return True, "Accident enregistré", accident_id

    except Exception as e:
        logger.exception(f"Erreur create_accident: {e}")
        return False, f"Erreur: {str(e)}", None


def update_accident(accident_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour un accident du travail."""
    try:
        require('rh.medical.edit')
        QueryExecutor.execute_write(
            """UPDATE medical_accident_travail SET
                   date_accident = %s, heure_accident = %s, jour_semaine = %s,
                   horaires = %s, circonstances = %s, siege_lesions = %s,
                   nature_lesions = %s, avec_arret = %s, date_reconnaissance_at = %s,
                   date_debut_arret = %s, date_fin_arret_initial = %s, commentaire = %s
               WHERE id = %s""",
            (
                data.get('date_accident'),
                data.get('heure_accident'),
                data.get('jour_semaine'),
                data.get('horaires'),
                data.get('circonstances'),
                data.get('siege_lesions'),
                data.get('nature_lesions'),
                data.get('avec_arret', 0),
                data.get('date_reconnaissance_at'),
                data.get('date_debut_arret'),
                data.get('date_fin_arret_initial'),
                data.get('commentaire'),
                accident_id
            ),
            return_lastrowid=False
        )

        _recalculer_jours_absence(accident_id)

        return True, "Accident mis à jour"

    except Exception as e:
        logger.exception(f"Erreur update_accident: {e}")
        return False, f"Erreur: {str(e)}"


def delete_accident(accident_id: int) -> Tuple[bool, str]:
    """Supprime un accident du travail et ses prolongations."""
    try:
        require('rh.medical.delete')
        # Les prolongations sont supprimées en cascade
        QueryExecutor.execute_write(
            "DELETE FROM medical_accident_travail WHERE id = %s",
            (accident_id,), return_lastrowid=False
        )
        return True, "Accident supprimé"

    except Exception as e:
        logger.exception(f"Erreur delete_accident: {e}")
        return False, f"Erreur: {str(e)}"


def ajouter_prolongation(accident_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Ajoute une prolongation d'arrêt à un accident."""
    try:
        # Récupérer le numéro de prolongation suivant
        next_num = QueryExecutor.fetch_scalar(
            """SELECT COALESCE(MAX(numero_prolongation), 0) + 1
               FROM medical_prolongation_arret
               WHERE accident_id = %s""",
            (accident_id,), default=1
        )

        prolongation_id = QueryExecutor.execute_write(
            """INSERT INTO medical_prolongation_arret (
                   accident_id, date_debut, date_fin, numero_prolongation, commentaire
               ) VALUES (%s, %s, %s, %s, %s)""",
            (
                accident_id,
                data.get('date_debut'),
                data.get('date_fin'),
                next_num,
                data.get('commentaire')
            )
        )

        # Mettre à jour date_fin_prolongation
        QueryExecutor.execute_write(
            """UPDATE medical_accident_travail
               SET date_fin_prolongation = %s
               WHERE id = %s""",
            (data.get('date_fin'), accident_id),
            return_lastrowid=False
        )

        _recalculer_jours_absence(accident_id)

        return True, f"Prolongation #{next_num} ajoutée", prolongation_id

    except Exception as e:
        logger.exception(f"Erreur ajouter_prolongation: {e}")
        return False, f"Erreur: {str(e)}", None


def _recalculer_jours_absence(accident_id: int):
    """Recalcule le nombre total de jours d'absence pour un accident."""
    QueryExecutor.execute_write(
        """UPDATE medical_accident_travail at
           SET nb_jours_absence = (
               SELECT DATEDIFF(
                   COALESCE(
                       (SELECT MAX(date_fin) FROM medical_prolongation_arret WHERE accident_id = at.id),
                       at.date_fin_arret_initial
                   ),
                   at.date_debut_arret
               ) + 1
           )
           WHERE at.id = %s AND at.avec_arret = 1 AND at.date_debut_arret IS NOT NULL""",
        (accident_id,), return_lastrowid=False
    )


# ============================================================
# 4. MALADIES PROFESSIONNELLES
# ============================================================

def get_maladies_pro(operateur_id: int) -> List[Dict]:
    """Récupère l'historique des maladies professionnelles."""
    try:
        result = QueryExecutor.fetch_all(
            """SELECT * FROM medical_maladie_pro
               WHERE operateur_id = %s
               ORDER BY date_reconnaissance DESC""",
            (operateur_id,), dictionary=True
        )
        for mp in result:
            if mp.get('taux_ipp') and isinstance(mp['taux_ipp'], Decimal):
                mp['taux_ipp'] = float(mp['taux_ipp'])
        return result

    except Exception as e:
        logger.exception(f"Erreur get_maladies_pro: {e}")
        return []


def create_maladie_pro(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée une nouvelle maladie professionnelle."""
    try:
        require('rh.medical.edit')
        mp_id = QueryExecutor.execute_write(
            """INSERT INTO medical_maladie_pro (
                   operateur_id, date_reconnaissance, numero_tableau,
                   designation, taux_ipp, commentaire
               ) VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                operateur_id,
                data.get('date_reconnaissance'),
                data.get('numero_tableau'),
                data.get('designation'),
                data.get('taux_ipp'),
                data.get('commentaire')
            )
        )

        # Mettre à jour le flag maladie_pro dans la table medical
        QueryExecutor.execute_write(
            "UPDATE medical SET maladie_pro = 1 WHERE operateur_id = %s",
            (operateur_id,), return_lastrowid=False
        )

        return True, "Maladie professionnelle enregistrée", mp_id

    except Exception as e:
        logger.exception(f"Erreur create_maladie_pro: {e}")
        return False, f"Erreur: {str(e)}", None


def delete_maladie_pro(mp_id: int) -> Tuple[bool, str]:
    """Supprime une maladie professionnelle."""
    try:
        require('rh.medical.delete')

        # Récupérer l'operateur_id avant suppression
        row = QueryExecutor.fetch_one(
            "SELECT operateur_id FROM medical_maladie_pro WHERE id = %s",
            (mp_id,), dictionary=True
        )
        if not row:
            return False, "Maladie professionnelle introuvable"

        operateur_id = row['operateur_id']

        QueryExecutor.execute_write(
            "DELETE FROM medical_maladie_pro WHERE id = %s",
            (mp_id,), return_lastrowid=False
        )

        # Vérifier s'il reste des MP pour cet opérateur
        cnt = QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM medical_maladie_pro WHERE operateur_id = %s",
            (operateur_id,), default=0
        )
        if cnt == 0:
            QueryExecutor.execute_write(
                "UPDATE medical SET maladie_pro = 0 WHERE operateur_id = %s",
                (operateur_id,), return_lastrowid=False
            )

        return True, "Maladie professionnelle supprimée"

    except Exception as e:
        logger.exception(f"Erreur delete_maladie_pro: {e}")
        return False, f"Erreur: {str(e)}"


# ============================================================
# 5. ALERTES MÉDICALES
# ============================================================

def get_alertes_medicales(operateur_id: int = None) -> List[Dict]:
    """
    Récupère les alertes médicales.

    Args:
        operateur_id: Si fourni, filtre pour cet opérateur uniquement

    Returns:
        Liste des alertes
    """
    try:
        sql = "SELECT * FROM v_alertes_medicales"
        params = []

        if operateur_id:
            sql += " WHERE operateur_id = %s"
            params.append(operateur_id)

        sql += " ORDER BY jours_retard DESC"

        return QueryExecutor.fetch_all(
            sql, tuple(params) if params else None, dictionary=True
        )

    except Exception as e:
        logger.exception(f"Erreur get_alertes_medicales: {e}")
        return []


def get_visites_a_planifier(jours_avance: int = 30) -> List[Dict]:
    """
    Récupère les visites médicales à planifier dans les N prochains jours.

    Args:
        jours_avance: Nombre de jours d'avance pour la planification

    Returns:
        Liste des opérateurs avec visite à planifier
    """
    try:
        return QueryExecutor.fetch_all(
            """SELECT
                   p.id as operateur_id,
                   p.nom, p.prenom, p.matricule,
                   mv.prochaine_visite,
                   DATEDIFF(mv.prochaine_visite, CURDATE()) as jours_restants,
                   m.type_suivi_vip
               FROM personnel p
               JOIN medical_visite mv ON p.id = mv.operateur_id
               LEFT JOIN medical m ON p.id = m.operateur_id
               WHERE p.statut = 'ACTIF'
                 AND mv.prochaine_visite <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
                 AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE operateur_id = p.id)
               ORDER BY mv.prochaine_visite""",
            (jours_avance,), dictionary=True
        )

    except Exception as e:
        logger.exception(f"Erreur get_visites_a_planifier: {e}")
        return []


def get_rqth_expirant(jours_avance: int = 90) -> List[Dict]:
    """
    Récupère les RQTH qui expirent dans les N prochains jours.
    Utilise la table validite existante.

    Args:
        jours_avance: Nombre de jours d'avance

    Returns:
        Liste des opérateurs avec RQTH expirant
    """
    try:
        return QueryExecutor.fetch_all(
            """SELECT operateur_id, nom, prenom, matricule, date_fin_rqth,
                      DATEDIFF(date_fin_rqth, CURDATE()) AS jours_restants
               FROM v_suivi_medical
               WHERE date_fin_rqth IS NOT NULL
                 AND date_fin_rqth BETWEEN CURDATE() AND CURDATE() + INTERVAL %s DAY
               ORDER BY date_fin_rqth""",
            (jours_avance,), dictionary=True
        )

    except Exception as e:
        logger.exception(f"Erreur get_rqth_expirant: {e}")
        return []


# ============================================================
# 6. STATISTIQUES MÉDICALES
# ============================================================

def get_statistiques_medicales_globales() -> Dict[str, Any]:
    """
    Récupère les statistiques médicales globales pour le tableau de bord.

    Returns:
        Dictionnaire avec les statistiques
    """
    try:
        stats = {}

        # Visites en retard
        stats['visites_en_retard'] = QueryExecutor.fetch_scalar(
            """SELECT COUNT(DISTINCT p.id)
               FROM personnel p
               JOIN medical_visite mv ON p.id = mv.operateur_id
               WHERE p.statut = 'ACTIF'
                 AND mv.prochaine_visite < CURDATE()
                 AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE operateur_id = p.id)""",
            default=0
        )

        # Visites à planifier (30 jours)
        stats['visites_a_planifier'] = QueryExecutor.fetch_scalar(
            """SELECT COUNT(DISTINCT p.id)
               FROM personnel p
               JOIN medical_visite mv ON p.id = mv.operateur_id
               WHERE p.statut = 'ACTIF'
                 AND mv.prochaine_visite BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                 AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE operateur_id = p.id)""",
            default=0
        )

        # RQTH actives (via vue v_suivi_medical)
        stats['rqth_actives'] = QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM v_suivi_medical WHERE statut_rqth = 'Active'",
            default=0
        )

        # RQTH expirant bientôt (90 jours, via vue v_suivi_medical)
        stats['rqth_expirant'] = QueryExecutor.fetch_scalar(
            """SELECT COUNT(*) FROM v_suivi_medical
               WHERE date_fin_rqth BETWEEN CURDATE() AND CURDATE() + INTERVAL 90 DAY""",
            default=0
        )

        # Accidents de l'année
        at_annee = QueryExecutor.fetch_one(
            """SELECT
                   COUNT(*) as total,
                   SUM(CASE WHEN avec_arret = 1 THEN 1 ELSE 0 END) as avec_arret,
                   SUM(COALESCE(nb_jours_absence, 0)) as jours_absence
               FROM medical_accident_travail
               WHERE YEAR(date_accident) = YEAR(CURDATE())""",
            dictionary=True
        )
        stats['accidents_annee'] = {
            'total': (at_annee or {}).get('total') or 0,
            'avec_arret': (at_annee or {}).get('avec_arret') or 0,
            'jours_absence': (at_annee or {}).get('jours_absence') or 0
        }

        return stats

    except Exception as e:
        logger.exception(f"Erreur get_statistiques_medicales_globales: {e}")
        return {}


# ============================================================
# 7. RQTH / OETH (utilise la table validite existante)
# ============================================================

def get_validites(operateur_id: int, type_validite: str = None) -> List[Dict]:
    """
    Récupère les validités (RQTH/OETH) d'un opérateur.

    Args:
        operateur_id: ID de l'opérateur
        type_validite: 'RQTH', 'OETH' ou None pour tous

    Returns:
        Liste des validités
    """
    try:
        sql = "SELECT * FROM validite WHERE operateur_id = %s"
        params = [operateur_id]

        if type_validite:
            sql += " AND type_validite = %s"
            params.append(type_validite)

        sql += " ORDER BY date_debut DESC"

        result = QueryExecutor.fetch_all(sql, tuple(params), dictionary=True)

        for v in result:
            if v.get('taux_incapacite') and isinstance(v['taux_incapacite'], Decimal):
                v['taux_incapacite'] = float(v['taux_incapacite'])

        return result

    except Exception as e:
        logger.exception(f"Erreur get_validites: {e}")
        return []


def create_validite(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """
    Crée une nouvelle validité (RQTH ou OETH).

    Args:
        operateur_id: ID de l'opérateur
        data: Dictionnaire avec type_validite, date_debut, date_fin, etc.

    Returns:
        (succès, message, id)
    """
    try:
        require('rh.medical.edit')
        validite_id = QueryExecutor.execute_write(
            """INSERT INTO validite (
                   operateur_id, type_validite, date_debut, date_fin,
                   periodicite, taux_incapacite, document_justificatif, commentaire
               ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                operateur_id,
                data.get('type_validite'),
                data.get('date_debut'),
                data.get('date_fin'),
                data.get('periodicite', 'Périodique'),
                data.get('taux_incapacite'),
                data.get('document_justificatif'),
                data.get('commentaire')
            )
        )
        return True, f"{data.get('type_validite')} enregistré", validite_id

    except Exception as e:
        logger.exception(f"Erreur create_validite: {e}")
        return False, f"Erreur: {str(e)}", None


def update_validite(validite_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour une validité existante."""
    try:
        require('rh.medical.edit')
        QueryExecutor.execute_write(
            """UPDATE validite SET
                   date_debut = %s, date_fin = %s, periodicite = %s,
                   taux_incapacite = %s, document_justificatif = %s, commentaire = %s
               WHERE id = %s""",
            (
                data.get('date_debut'),
                data.get('date_fin'),
                data.get('periodicite'),
                data.get('taux_incapacite'),
                data.get('document_justificatif'),
                data.get('commentaire'),
                validite_id
            ),
            return_lastrowid=False
        )
        return True, "Validité mise à jour"

    except Exception as e:
        logger.exception(f"Erreur update_validite: {e}")
        return False, f"Erreur: {str(e)}"


def delete_validite(validite_id: int) -> Tuple[bool, str]:
    """Supprime une validité."""
    try:
        require('rh.medical.delete')
        QueryExecutor.execute_write(
            "DELETE FROM validite WHERE id = %s",
            (validite_id,), return_lastrowid=False
        )
        return True, "Validité supprimée"

    except Exception as e:
        logger.exception(f"Erreur delete_validite: {e}")
        return False, f"Erreur: {str(e)}"
