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
"""

import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal

from core.db.configbd import DatabaseCursor, DatabaseConnection
from core.services.permission_manager import require


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
        with DatabaseCursor(dictionary=True) as cur:
            # Données principales (table medical)
            cur.execute("""
                SELECT m.*
                FROM medical m
                WHERE m.operateur_id = %s
            """, (operateur_id,))

            medical = cur.fetchone()

            # RQTH/OETH depuis table validite existante
            cur.execute("""
                SELECT *
                FROM validite
                WHERE operateur_id = %s AND type_validite = 'RQTH'
                ORDER BY date_debut DESC
                LIMIT 1
            """, (operateur_id,))
            rqth = cur.fetchone()

            cur.execute("""
                SELECT *
                FROM validite
                WHERE operateur_id = %s AND type_validite = 'OETH'
                ORDER BY date_debut DESC
                LIMIT 1
            """, (operateur_id,))
            oeth = cur.fetchone()

            # Dernière visite
            cur.execute("""
                SELECT *
                FROM medical_visite
                WHERE operateur_id = %s
                ORDER BY date_visite DESC
                LIMIT 1
            """, (operateur_id,))

            derniere_visite = cur.fetchone()

            # Statistiques visites
            cur.execute("""
                SELECT
                    COUNT(*) as total_visites,
                    MIN(date_visite) as premiere_visite,
                    MAX(date_visite) as derniere_visite
                FROM medical_visite
                WHERE operateur_id = %s
            """, (operateur_id,))

            stats_visites = cur.fetchone()

            # Accidents du travail
            cur.execute("""
                SELECT COUNT(*) as nb_accidents,
                       SUM(CASE WHEN avec_arret = 1 THEN 1 ELSE 0 END) as nb_avec_arret,
                       SUM(COALESCE(nb_jours_absence, 0)) as total_jours_absence
                FROM medical_accident_travail
                WHERE operateur_id = %s
            """, (operateur_id,))

            stats_at = cur.fetchone()

            # Maladies professionnelles
            cur.execute("""
                SELECT COUNT(*) as nb_mp
                FROM medical_maladie_pro
                WHERE operateur_id = %s
            """, (operateur_id,))

            stats_mp = cur.fetchone()

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
        logger.error(f"Erreur get_donnees_medicales: {e}")
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
        with DatabaseConnection() as conn:
            cur = conn.cursor(dictionary=True)

            cur.execute("SELECT * FROM medical WHERE operateur_id = %s", (operateur_id,))
            medical = cur.fetchone()

            if not medical:
                cur.execute(
                    "INSERT INTO medical (operateur_id) VALUES (%s)",
                    (operateur_id,)
                )
                conn.commit()
                cur.execute("SELECT * FROM medical WHERE operateur_id = %s", (operateur_id,))
                medical = cur.fetchone()

            return medical

    except Exception as e:
        logger.error(f"Erreur get_ou_creer_medical: {e}")
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
        with DatabaseConnection() as conn:
            cur = conn.cursor(dictionary=True)

            # Vérifier/créer l'enregistrement
            cur.execute("SELECT id FROM medical WHERE operateur_id = %s", (operateur_id,))
            exists = cur.fetchone()

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
                    cur.execute(sql, tuple(values))
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
                cur.execute(sql, tuple(values))

            return True, "Données médicales mises à jour"

    except Exception as e:
        logger.error(f"Erreur update_donnees_medicales: {e}")
        return False, f"Erreur: {str(e)}"


# ============================================================
# 2. VISITES MÉDICALES
# ============================================================

def get_visites(operateur_id: int) -> List[Dict]:
    """Récupère l'historique des visites médicales."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT *
                FROM medical_visite
                WHERE operateur_id = %s
                ORDER BY date_visite DESC
            """, (operateur_id,))
            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_visites: {e}")
        return []


def create_visite(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée une nouvelle visite médicale."""
    try:
        require('rh.medical.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO medical_visite (
                    operateur_id, date_visite, type_visite, resultat,
                    restrictions, medecin, commentaire, prochaine_visite
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                operateur_id,
                data.get('date_visite'),
                data.get('type_visite', 'Périodique'),
                data.get('resultat'),
                data.get('restrictions'),
                data.get('medecin'),
                data.get('commentaire'),
                data.get('prochaine_visite')
            ))

            visite_id = cur.lastrowid
            return True, "Visite enregistrée", visite_id

    except Exception as e:
        logger.error(f"Erreur create_visite: {e}")
        return False, f"Erreur: {str(e)}", None


def update_visite(visite_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour une visite médicale."""
    try:
        require('rh.medical.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                UPDATE medical_visite SET
                    date_visite = %s, type_visite = %s, resultat = %s,
                    restrictions = %s, medecin = %s, commentaire = %s,
                    prochaine_visite = %s
                WHERE id = %s
            """
            cur.execute(sql, (
                data.get('date_visite'),
                data.get('type_visite'),
                data.get('resultat'),
                data.get('restrictions'),
                data.get('medecin'),
                data.get('commentaire'),
                data.get('prochaine_visite'),
                visite_id
            ))

            return True, "Visite mise à jour"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def delete_visite(visite_id: int) -> Tuple[bool, str]:
    """Supprime une visite médicale."""
    try:
        require('rh.medical.delete')
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM medical_visite WHERE id = %s", (visite_id,))
            return True, "Visite supprimée"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


# ============================================================
# 3. ACCIDENTS DU TRAVAIL
# ============================================================

def get_accidents(operateur_id: int) -> List[Dict]:
    """Récupère l'historique des accidents du travail."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT at.*,
                       (SELECT COUNT(*) FROM medical_prolongation_arret p
                        WHERE p.accident_id = at.id) as nb_prolongations
                FROM medical_accident_travail at
                WHERE at.operateur_id = %s
                ORDER BY at.date_accident DESC
            """, (operateur_id,))
            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_accidents: {e}")
        return []


def get_accident_detail(accident_id: int) -> Optional[Dict]:
    """Récupère le détail d'un accident avec ses prolongations."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM medical_accident_travail WHERE id = %s", (accident_id,))
            accident = cur.fetchone()

            if accident:
                cur.execute("""
                    SELECT * FROM medical_prolongation_arret
                    WHERE accident_id = %s
                    ORDER BY numero_prolongation
                """, (accident_id,))
                accident['prolongations'] = cur.fetchall()

            return accident

    except Exception as e:
        logger.error(f"Erreur get_accident_detail: {e}")
        return None


def create_accident(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée un nouvel accident du travail."""
    try:
        require('rh.medical.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO medical_accident_travail (
                    operateur_id, date_accident, heure_accident, jour_semaine,
                    horaires, circonstances, siege_lesions, nature_lesions,
                    avec_arret, date_reconnaissance_at, date_debut_arret,
                    date_fin_arret_initial, commentaire
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
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
            ))

            accident_id = cur.lastrowid

            # Calculer nb_jours_absence si avec arrêt
            if data.get('avec_arret') and data.get('date_debut_arret') and data.get('date_fin_arret_initial'):
                _recalculer_jours_absence(cur, accident_id)

            return True, "Accident enregistré", accident_id

    except Exception as e:
        logger.error(f"Erreur create_accident: {e}")
        return False, f"Erreur: {str(e)}", None


def update_accident(accident_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour un accident du travail."""
    try:
        require('rh.medical.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                UPDATE medical_accident_travail SET
                    date_accident = %s, heure_accident = %s, jour_semaine = %s,
                    horaires = %s, circonstances = %s, siege_lesions = %s,
                    nature_lesions = %s, avec_arret = %s, date_reconnaissance_at = %s,
                    date_debut_arret = %s, date_fin_arret_initial = %s, commentaire = %s
                WHERE id = %s
            """
            cur.execute(sql, (
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
            ))

            _recalculer_jours_absence(cur, accident_id)

            return True, "Accident mis à jour"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def delete_accident(accident_id: int) -> Tuple[bool, str]:
    """Supprime un accident du travail et ses prolongations."""
    try:
        require('rh.medical.delete')
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            # Les prolongations sont supprimées en cascade
            cur.execute("DELETE FROM medical_accident_travail WHERE id = %s", (accident_id,))
            return True, "Accident supprimé"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def ajouter_prolongation(accident_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Ajoute une prolongation d'arrêt à un accident."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor(dictionary=True)

            # Récupérer le numéro de prolongation suivant
            cur.execute("""
                SELECT COALESCE(MAX(numero_prolongation), 0) + 1 as next_num
                FROM medical_prolongation_arret
                WHERE accident_id = %s
            """, (accident_id,))
            next_num = cur.fetchone()['next_num']

            cur.execute("""
                INSERT INTO medical_prolongation_arret (
                    accident_id, date_debut, date_fin, numero_prolongation, commentaire
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                accident_id,
                data.get('date_debut'),
                data.get('date_fin'),
                next_num,
                data.get('commentaire')
            ))

            prolongation_id = cur.lastrowid

            # Mettre à jour date_fin_prolongation et nb_jours
            cur.execute("""
                UPDATE medical_accident_travail
                SET date_fin_prolongation = %s
                WHERE id = %s
            """, (data.get('date_fin'), accident_id))

            _recalculer_jours_absence(cur, accident_id)

            return True, f"Prolongation #{next_num} ajoutée", prolongation_id

    except Exception as e:
        logger.error(f"Erreur ajouter_prolongation: {e}")
        return False, f"Erreur: {str(e)}", None


def _recalculer_jours_absence(cur, accident_id: int):
    """Recalcule le nombre total de jours d'absence pour un accident."""
    cur.execute("""
        UPDATE medical_accident_travail at
        SET nb_jours_absence = (
            SELECT DATEDIFF(
                COALESCE(
                    (SELECT MAX(date_fin) FROM medical_prolongation_arret WHERE accident_id = at.id),
                    at.date_fin_arret_initial
                ),
                at.date_debut_arret
            ) + 1
        )
        WHERE at.id = %s AND at.avec_arret = 1 AND at.date_debut_arret IS NOT NULL
    """, (accident_id,))


# ============================================================
# 4. MALADIES PROFESSIONNELLES
# ============================================================

def get_maladies_pro(operateur_id: int) -> List[Dict]:
    """Récupère l'historique des maladies professionnelles."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT *
                FROM medical_maladie_pro
                WHERE operateur_id = %s
                ORDER BY date_reconnaissance DESC
            """, (operateur_id,))

            result = cur.fetchall()
            for mp in result:
                if mp.get('taux_ipp') and isinstance(mp['taux_ipp'], Decimal):
                    mp['taux_ipp'] = float(mp['taux_ipp'])
            return result

    except Exception as e:
        logger.error(f"Erreur get_maladies_pro: {e}")
        return []


def create_maladie_pro(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée une nouvelle maladie professionnelle."""
    try:
        require('rh.medical.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO medical_maladie_pro (
                    operateur_id, date_reconnaissance, numero_tableau,
                    designation, taux_ipp, commentaire
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                operateur_id,
                data.get('date_reconnaissance'),
                data.get('numero_tableau'),
                data.get('designation'),
                data.get('taux_ipp'),
                data.get('commentaire')
            ))

            mp_id = cur.lastrowid

            # Mettre à jour le flag maladie_pro dans la table medical
            cur.execute("""
                UPDATE medical SET maladie_pro = 1
                WHERE operateur_id = %s
            """, (operateur_id,))

            return True, "Maladie professionnelle enregistrée", mp_id

    except Exception as e:
        logger.error(f"Erreur create_maladie_pro: {e}")
        return False, f"Erreur: {str(e)}", None


def delete_maladie_pro(mp_id: int) -> Tuple[bool, str]:
    """Supprime une maladie professionnelle."""
    try:
        require('rh.medical.delete')
        with DatabaseConnection() as conn:
            cur = conn.cursor(dictionary=True)

            # Récupérer l'operateur_id avant suppression
            cur.execute("SELECT operateur_id FROM medical_maladie_pro WHERE id = %s", (mp_id,))
            row = cur.fetchone()
            if not row:
                return False, "Maladie professionnelle introuvable"

            operateur_id = row['operateur_id']

            cur.execute("DELETE FROM medical_maladie_pro WHERE id = %s", (mp_id,))

            # Vérifier s'il reste des MP pour cet opérateur
            cur.execute("SELECT COUNT(*) as cnt FROM medical_maladie_pro WHERE operateur_id = %s", (operateur_id,))
            if cur.fetchone()['cnt'] == 0:
                cur.execute("UPDATE medical SET maladie_pro = 0 WHERE operateur_id = %s", (operateur_id,))

            return True, "Maladie professionnelle supprimée"

    except Exception as e:
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
        with DatabaseCursor(dictionary=True) as cur:
            sql = "SELECT * FROM v_alertes_medicales"
            params = []

            if operateur_id:
                sql += " WHERE operateur_id = %s"
                params.append(operateur_id)

            sql += " ORDER BY jours_retard DESC"

            cur.execute(sql, tuple(params) if params else None)
            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_alertes_medicales: {e}")
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
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    p.id as operateur_id,
                    p.nom,
                    p.prenom,
                    p.matricule,
                    mv.prochaine_visite,
                    DATEDIFF(mv.prochaine_visite, CURDATE()) as jours_restants,
                    m.type_suivi_vip
                FROM personnel p
                JOIN medical_visite mv ON p.id = mv.operateur_id
                LEFT JOIN medical m ON p.id = m.operateur_id
                WHERE p.statut = 'ACTIF'
                  AND mv.prochaine_visite <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
                  AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE operateur_id = p.id)
                ORDER BY mv.prochaine_visite
            """, (jours_avance,))

            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_visites_a_planifier: {e}")
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
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    p.id as operateur_id,
                    p.nom,
                    p.prenom,
                    p.matricule,
                    v.date_fin as date_fin_rqth,
                    v.taux_incapacite,
                    DATEDIFF(v.date_fin, CURDATE()) as jours_restants
                FROM personnel p
                JOIN validite v ON p.id = v.operateur_id
                WHERE p.statut = 'ACTIF'
                  AND v.type_validite = 'RQTH'
                  AND v.date_fin IS NOT NULL
                  AND v.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
                ORDER BY v.date_fin
            """, (jours_avance,))

            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_rqth_expirant: {e}")
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
        with DatabaseCursor(dictionary=True) as cur:
            stats = {}

            # Visites en retard
            cur.execute("""
                SELECT COUNT(DISTINCT p.id) as count
                FROM personnel p
                JOIN medical_visite mv ON p.id = mv.operateur_id
                WHERE p.statut = 'ACTIF'
                  AND mv.prochaine_visite < CURDATE()
                  AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE operateur_id = p.id)
            """)
            stats['visites_en_retard'] = cur.fetchone()['count']

            # Visites à planifier (30 jours)
            cur.execute("""
                SELECT COUNT(DISTINCT p.id) as count
                FROM personnel p
                JOIN medical_visite mv ON p.id = mv.operateur_id
                WHERE p.statut = 'ACTIF'
                  AND mv.prochaine_visite BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                  AND mv.id = (SELECT MAX(id) FROM medical_visite WHERE operateur_id = p.id)
            """)
            stats['visites_a_planifier'] = cur.fetchone()['count']

            # RQTH actives (utilise table validite existante)
            cur.execute("""
                SELECT COUNT(DISTINCT p.id) as count
                FROM personnel p
                JOIN validite v ON p.id = v.operateur_id
                WHERE p.statut = 'ACTIF'
                  AND v.type_validite = 'RQTH'
                  AND (v.date_fin IS NULL OR v.date_fin >= CURDATE())
            """)
            stats['rqth_actives'] = cur.fetchone()['count']

            # RQTH expirant bientôt (90 jours) - utilise table validite
            cur.execute("""
                SELECT COUNT(DISTINCT p.id) as count
                FROM personnel p
                JOIN validite v ON p.id = v.operateur_id
                WHERE p.statut = 'ACTIF'
                  AND v.type_validite = 'RQTH'
                  AND v.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)
            """)
            stats['rqth_expirant'] = cur.fetchone()['count']

            # Accidents de l'année
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN avec_arret = 1 THEN 1 ELSE 0 END) as avec_arret,
                    SUM(COALESCE(nb_jours_absence, 0)) as jours_absence
                FROM medical_accident_travail
                WHERE YEAR(date_accident) = YEAR(CURDATE())
            """)
            at_annee = cur.fetchone()
            stats['accidents_annee'] = {
                'total': at_annee['total'] or 0,
                'avec_arret': at_annee['avec_arret'] or 0,
                'jours_absence': at_annee['jours_absence'] or 0
            }

            return stats

    except Exception as e:
        logger.error(f"Erreur get_statistiques_medicales_globales: {e}")
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
        with DatabaseCursor(dictionary=True) as cur:
            sql = """
                SELECT *
                FROM validite
                WHERE operateur_id = %s
            """
            params = [operateur_id]

            if type_validite:
                sql += " AND type_validite = %s"
                params.append(type_validite)

            sql += " ORDER BY date_debut DESC"

            cur.execute(sql, tuple(params))
            result = cur.fetchall()

            for v in result:
                if v.get('taux_incapacite') and isinstance(v['taux_incapacite'], Decimal):
                    v['taux_incapacite'] = float(v['taux_incapacite'])

            return result

    except Exception as e:
        logger.error(f"Erreur get_validites: {e}")
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
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO validite (
                    operateur_id, type_validite, date_debut, date_fin,
                    periodicite, taux_incapacite, document_justificatif, commentaire
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                operateur_id,
                data.get('type_validite'),
                data.get('date_debut'),
                data.get('date_fin'),
                data.get('periodicite', 'Périodique'),
                data.get('taux_incapacite'),
                data.get('document_justificatif'),
                data.get('commentaire')
            ))

            validite_id = cur.lastrowid
            return True, f"{data.get('type_validite')} enregistré", validite_id

    except Exception as e:
        logger.error(f"Erreur create_validite: {e}")
        return False, f"Erreur: {str(e)}", None


def update_validite(validite_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour une validité existante."""
    try:
        require('rh.medical.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                UPDATE validite SET
                    date_debut = %s, date_fin = %s, periodicite = %s,
                    taux_incapacite = %s, document_justificatif = %s, commentaire = %s
                WHERE id = %s
            """
            cur.execute(sql, (
                data.get('date_debut'),
                data.get('date_fin'),
                data.get('periodicite'),
                data.get('taux_incapacite'),
                data.get('document_justificatif'),
                data.get('commentaire'),
                validite_id
            ))

            return True, "Validité mise à jour"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def delete_validite(validite_id: int) -> Tuple[bool, str]:
    """Supprime une validité."""
    try:
        require('rh.medical.delete')
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM validite WHERE id = %s", (validite_id,))
            return True, "Validité supprimée"

    except Exception as e:
        return False, f"Erreur: {str(e)}"
