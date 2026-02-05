# -*- coding: utf-8 -*-
"""
Service Vie du Salarié pour la gestion des événements de carrière.

Gère:
- Sanctions disciplinaires (observations, avertissements, mises à pied)
- Contrôles d'alcoolémie
- Tests salivaires (stupéfiants)
- Entretiens professionnels (EPP, EAP)

Source: Tableau SIRH.xlsx - Feuille "Vie du salarié"
"""

import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal

from core.db.configbd import DatabaseCursor, DatabaseConnection


# ============================================================
# 1. RÉCAPITULATIF VIE DU SALARIÉ
# ============================================================

def get_donnees_vie_salarie(operateur_id: int) -> Dict[str, Any]:
    """
    Récupère toutes les données de vie du salarié.

    Args:
        operateur_id: ID de l'opérateur

    Returns:
        Dictionnaire avec les données
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            # Statistiques sanctions
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN type_sanction = 'Observation verbale' THEN 1 ELSE 0 END) as observations_verbales,
                    SUM(CASE WHEN type_sanction = 'Observation écrite' THEN 1 ELSE 0 END) as observations_ecrites,
                    SUM(CASE WHEN type_sanction = 'Avertissement' THEN 1 ELSE 0 END) as avertissements,
                    SUM(CASE WHEN type_sanction LIKE 'Mise à pied%' THEN 1 ELSE 0 END) as mises_a_pied,
                    MAX(date_sanction) as derniere_sanction
                FROM vie_salarie_sanction
                WHERE operateur_id = %s
            """, (operateur_id,))
            stats_sanctions = cur.fetchone()

            # Statistiques contrôles alcoolémie
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN resultat = 'Positif' THEN 1 ELSE 0 END) as positifs,
                    MAX(date_controle) as dernier_controle
                FROM vie_salarie_alcoolemie
                WHERE operateur_id = %s
            """, (operateur_id,))
            stats_alcool = cur.fetchone()

            # Statistiques tests salivaires
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN resultat = 'Positif' THEN 1 ELSE 0 END) as positifs,
                    MAX(date_test) as dernier_test
                FROM vie_salarie_test_salivaire
                WHERE operateur_id = %s
            """, (operateur_id,))
            stats_salivaire = cur.fetchone()

            # Dernier EPP et EAP
            cur.execute("""
                SELECT type_entretien, MAX(date_entretien) as derniere_date
                FROM vie_salarie_entretien
                WHERE operateur_id = %s AND type_entretien IN ('EPP', 'EAP')
                GROUP BY type_entretien
            """, (operateur_id,))
            entretiens = {row['type_entretien']: row['derniere_date'] for row in cur.fetchall()}

            # Prochain entretien prévu
            cur.execute("""
                SELECT prochaine_date
                FROM vie_salarie_entretien
                WHERE operateur_id = %s AND prochaine_date IS NOT NULL
                ORDER BY date_entretien DESC
                LIMIT 1
            """, (operateur_id,))
            prochain = cur.fetchone()

            return {
                "sanctions": stats_sanctions,
                "alcoolemie": stats_alcool,
                "tests_salivaires": stats_salivaire,
                "entretiens": {
                    "dernier_epp": entretiens.get('EPP'),
                    "dernier_eap": entretiens.get('EAP'),
                    "prochain": prochain['prochaine_date'] if prochain else None
                }
            }

    except Exception as e:
        logger.error(f"Erreur get_donnees_vie_salarie: {e}")
        return {"error": str(e)}


# ============================================================
# 2. SANCTIONS DISCIPLINAIRES
# ============================================================

def get_sanctions(operateur_id: int) -> List[Dict]:
    """Récupère l'historique des sanctions."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT *
                FROM vie_salarie_sanction
                WHERE operateur_id = %s
                ORDER BY date_sanction DESC
            """, (operateur_id,))
            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_sanctions: {e}")
        return []


def create_sanction(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée une nouvelle sanction disciplinaire."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO vie_salarie_sanction (
                    operateur_id, type_sanction, date_sanction,
                    duree_jours, motif, document_reference, commentaire
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                operateur_id,
                data.get('type_sanction'),
                data.get('date_sanction'),
                data.get('duree_jours'),
                data.get('motif'),
                data.get('document_reference'),
                data.get('commentaire')
            ))

            sanction_id = cur.lastrowid
            return True, "Sanction enregistrée", sanction_id

    except Exception as e:
        logger.error(f"Erreur create_sanction: {e}")
        return False, f"Erreur: {str(e)}", None


def update_sanction(sanction_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour une sanction."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                UPDATE vie_salarie_sanction SET
                    type_sanction = %s, date_sanction = %s, duree_jours = %s,
                    motif = %s, document_reference = %s, commentaire = %s
                WHERE id = %s
            """
            cur.execute(sql, (
                data.get('type_sanction'),
                data.get('date_sanction'),
                data.get('duree_jours'),
                data.get('motif'),
                data.get('document_reference'),
                data.get('commentaire'),
                sanction_id
            ))

            return True, "Sanction mise à jour"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def delete_sanction(sanction_id: int) -> Tuple[bool, str]:
    """Supprime une sanction."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM vie_salarie_sanction WHERE id = %s", (sanction_id,))
            return True, "Sanction supprimée"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


# ============================================================
# 3. CONTRÔLES D'ALCOOLÉMIE
# ============================================================

def get_controles_alcool(operateur_id: int) -> List[Dict]:
    """Récupère l'historique des contrôles d'alcoolémie."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT *
                FROM vie_salarie_alcoolemie
                WHERE operateur_id = %s
                ORDER BY date_controle DESC
            """, (operateur_id,))

            result = cur.fetchall()
            for row in result:
                if row.get('taux') and isinstance(row['taux'], Decimal):
                    row['taux'] = float(row['taux'])
            return result

    except Exception as e:
        logger.error(f"Erreur get_controles_alcool: {e}")
        return []


def create_controle_alcool(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée un nouveau contrôle d'alcoolémie."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO vie_salarie_alcoolemie (
                    operateur_id, date_controle, resultat,
                    taux, type_controle, commentaire
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                operateur_id,
                data.get('date_controle'),
                data.get('resultat'),
                data.get('taux'),
                data.get('type_controle', 'Aléatoire'),
                data.get('commentaire')
            ))

            controle_id = cur.lastrowid
            return True, "Contrôle enregistré", controle_id

    except Exception as e:
        logger.error(f"Erreur create_controle_alcool: {e}")
        return False, f"Erreur: {str(e)}", None


def delete_controle_alcool(controle_id: int) -> Tuple[bool, str]:
    """Supprime un contrôle d'alcoolémie."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM vie_salarie_alcoolemie WHERE id = %s", (controle_id,))
            return True, "Contrôle supprimé"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


# ============================================================
# 4. TESTS SALIVAIRES
# ============================================================

def get_tests_salivaires(operateur_id: int) -> List[Dict]:
    """Récupère l'historique des tests salivaires."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT *
                FROM vie_salarie_test_salivaire
                WHERE operateur_id = %s
                ORDER BY date_test DESC
            """, (operateur_id,))
            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_tests_salivaires: {e}")
        return []


def create_test_salivaire(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée un nouveau test salivaire."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO vie_salarie_test_salivaire (
                    operateur_id, date_test, resultat,
                    type_controle, commentaire
                ) VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                operateur_id,
                data.get('date_test'),
                data.get('resultat'),
                data.get('type_controle', 'Aléatoire'),
                data.get('commentaire')
            ))

            test_id = cur.lastrowid
            return True, "Test enregistré", test_id

    except Exception as e:
        logger.error(f"Erreur create_test_salivaire: {e}")
        return False, f"Erreur: {str(e)}", None


def delete_test_salivaire(test_id: int) -> Tuple[bool, str]:
    """Supprime un test salivaire."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM vie_salarie_test_salivaire WHERE id = %s", (test_id,))
            return True, "Test supprimé"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


# ============================================================
# 5. ENTRETIENS PROFESSIONNELS
# ============================================================

def get_entretiens(operateur_id: int) -> List[Dict]:
    """Récupère l'historique des entretiens professionnels."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT e.*,
                       CONCAT(m.prenom, ' ', m.nom) as manager_nom
                FROM vie_salarie_entretien e
                LEFT JOIN personnel m ON e.manager_id = m.id
                WHERE e.operateur_id = %s
                ORDER BY e.date_entretien DESC
            """, (operateur_id,))
            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_entretiens: {e}")
        return []


def get_entretien_detail(entretien_id: int) -> Optional[Dict]:
    """Récupère le détail d'un entretien."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT e.*,
                       CONCAT(m.prenom, ' ', m.nom) as manager_nom
                FROM vie_salarie_entretien e
                LEFT JOIN personnel m ON e.manager_id = m.id
                WHERE e.id = %s
            """, (entretien_id,))
            return cur.fetchone()

    except Exception as e:
        logger.error(f"Erreur get_entretien_detail: {e}")
        return None


def create_entretien(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée un nouvel entretien professionnel."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO vie_salarie_entretien (
                    operateur_id, type_entretien, date_entretien, manager_id,
                    objectifs_atteints, objectifs_fixes, besoins_formation,
                    souhaits_evolution, commentaire_salarie, commentaire_manager,
                    document_reference, prochaine_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                operateur_id,
                data.get('type_entretien'),
                data.get('date_entretien'),
                data.get('manager_id'),
                data.get('objectifs_atteints'),
                data.get('objectifs_fixes'),
                data.get('besoins_formation'),
                data.get('souhaits_evolution'),
                data.get('commentaire_salarie'),
                data.get('commentaire_manager'),
                data.get('document_reference'),
                data.get('prochaine_date')
            ))

            entretien_id = cur.lastrowid
            return True, "Entretien enregistré", entretien_id

    except Exception as e:
        logger.error(f"Erreur create_entretien: {e}")
        return False, f"Erreur: {str(e)}", None


def update_entretien(entretien_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour un entretien professionnel."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                UPDATE vie_salarie_entretien SET
                    type_entretien = %s, date_entretien = %s, manager_id = %s,
                    objectifs_atteints = %s, objectifs_fixes = %s, besoins_formation = %s,
                    souhaits_evolution = %s, commentaire_salarie = %s, commentaire_manager = %s,
                    document_reference = %s, prochaine_date = %s
                WHERE id = %s
            """
            cur.execute(sql, (
                data.get('type_entretien'),
                data.get('date_entretien'),
                data.get('manager_id'),
                data.get('objectifs_atteints'),
                data.get('objectifs_fixes'),
                data.get('besoins_formation'),
                data.get('souhaits_evolution'),
                data.get('commentaire_salarie'),
                data.get('commentaire_manager'),
                data.get('document_reference'),
                data.get('prochaine_date'),
                entretien_id
            ))

            return True, "Entretien mis à jour"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def delete_entretien(entretien_id: int) -> Tuple[bool, str]:
    """Supprime un entretien professionnel."""
    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM vie_salarie_entretien WHERE id = %s", (entretien_id,))
            return True, "Entretien supprimé"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


# ============================================================
# 6. ALERTES ENTRETIENS
# ============================================================

def get_alertes_entretiens(operateur_id: int = None) -> List[Dict]:
    """
    Récupère les alertes d'entretiens en retard.

    Args:
        operateur_id: Si fourni, filtre pour cet opérateur uniquement

    Returns:
        Liste des alertes
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            sql = "SELECT * FROM v_alertes_entretiens"
            params = []

            if operateur_id:
                sql += " WHERE operateur_id = %s"
                params.append(operateur_id)

            sql += " ORDER BY jours_retard DESC"

            cur.execute(sql, tuple(params) if params else None)
            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_alertes_entretiens: {e}")
        return []


def get_entretiens_a_planifier(type_entretien: str = None, jours_avance: int = 30) -> List[Dict]:
    """
    Récupère les entretiens à planifier.

    Args:
        type_entretien: 'EPP', 'EAP' ou None pour tous
        jours_avance: Nombre de jours d'avance

    Returns:
        Liste des opérateurs avec entretien à planifier
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            sql = """
                SELECT
                    p.id as operateur_id,
                    p.nom,
                    p.prenom,
                    p.matricule,
                    e.type_entretien,
                    e.prochaine_date,
                    DATEDIFF(e.prochaine_date, CURDATE()) as jours_restants
                FROM personnel p
                JOIN vie_salarie_entretien e ON p.id = e.operateur_id
                WHERE p.statut = 'ACTIF'
                  AND e.prochaine_date IS NOT NULL
                  AND e.prochaine_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
                  AND e.id = (
                      SELECT MAX(id) FROM vie_salarie_entretien
                      WHERE operateur_id = p.id
            """
            params = [jours_avance]

            if type_entretien:
                sql += " AND type_entretien = %s"
                params.append(type_entretien)

            sql += """
                  )
                ORDER BY e.prochaine_date
            """

            cur.execute(sql, tuple(params))
            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_entretiens_a_planifier: {e}")
        return []


# ============================================================
# 7. STATISTIQUES GLOBALES
# ============================================================

def get_statistiques_vie_salarie_globales() -> Dict[str, Any]:
    """
    Récupère les statistiques globales pour le tableau de bord.

    Returns:
        Dictionnaire avec les statistiques
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            stats = {}

            # Sanctions de l'année
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN type_sanction = 'Avertissement' THEN 1 ELSE 0 END) as avertissements,
                    SUM(CASE WHEN type_sanction LIKE 'Mise à pied%' THEN 1 ELSE 0 END) as mises_a_pied
                FROM vie_salarie_sanction
                WHERE YEAR(date_sanction) = YEAR(CURDATE())
            """)
            stats['sanctions_annee'] = cur.fetchone()

            # Contrôles alcoolémie de l'année
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN resultat = 'Positif' THEN 1 ELSE 0 END) as positifs
                FROM vie_salarie_alcoolemie
                WHERE YEAR(date_controle) = YEAR(CURDATE())
            """)
            stats['alcoolemie_annee'] = cur.fetchone()

            # Tests salivaires de l'année
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN resultat = 'Positif' THEN 1 ELSE 0 END) as positifs
                FROM vie_salarie_test_salivaire
                WHERE YEAR(date_test) = YEAR(CURDATE())
            """)
            stats['salivaire_annee'] = cur.fetchone()

            # EPP en retard (> 2 ans depuis dernier ou entrée)
            cur.execute("""
                SELECT COUNT(DISTINCT p.id) as count
                FROM personnel p
                LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
                LEFT JOIN (
                    SELECT operateur_id, MAX(date_entretien) as derniere_date
                    FROM vie_salarie_entretien
                    WHERE type_entretien = 'EPP'
                    GROUP BY operateur_id
                ) e ON p.id = e.operateur_id
                WHERE p.statut = 'ACTIF'
                  AND DATEDIFF(CURDATE(),
                      COALESCE(e.derniere_date, pi.date_entree, DATE_SUB(CURDATE(), INTERVAL 3 YEAR))
                  ) > 730
            """)
            stats['epp_en_retard'] = cur.fetchone()['count']

            # Entretiens de l'année
            cur.execute("""
                SELECT
                    type_entretien,
                    COUNT(*) as nombre
                FROM vie_salarie_entretien
                WHERE YEAR(date_entretien) = YEAR(CURDATE())
                GROUP BY type_entretien
            """)
            stats['entretiens_annee'] = {row['type_entretien']: row['nombre'] for row in cur.fetchall()}

            return stats

    except Exception as e:
        logger.error(f"Erreur get_statistiques_vie_salarie_globales: {e}")
        return {}


# ============================================================
# 8. HELPERS
# ============================================================

def get_types_sanction() -> List[str]:
    """Retourne la liste des types de sanction disponibles."""
    return [
        'Observation verbale',
        'Observation écrite',
        'Avertissement',
        'Mise à pied disciplinaire',
        'Mise à pied conservatoire'
    ]


def get_types_entretien() -> List[str]:
    """Retourne la liste des types d'entretien disponibles."""
    return [
        'EPP',
        'EAP',
        'Bilan 6 ans',
        'Entretien annuel',
        'Autre'
    ]


def get_managers_liste() -> List[Dict]:
    """Retourne la liste des managers potentiels."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT id, nom, prenom, matricule,
                       CONCAT(prenom, ' ', nom) as nom_complet
                FROM personnel
                WHERE statut = 'ACTIF'
                ORDER BY nom, prenom
            """)
            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_managers_liste: {e}")
        return []
