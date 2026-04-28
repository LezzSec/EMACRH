# -*- coding: utf-8 -*-
"""
Service Mobilité - Gestion des primes de mobilité et indemnités kilométriques.

Gère :
- Distance domicile-entreprise par salarié (personnel_mobilite)
- Barème des primes journalières par tranche km (mobilite_palier)
- Barème des indemnités kilométriques par CV fiscal (mobilite_ik)
- Calcul de la prime applicable selon la distance et le barème en vigueur
- Calcul de l'IK selon la puissance fiscale du véhicule
"""

from datetime import date
from typing import Dict, List, Optional, Tuple

from infrastructure.db.query_executor import QueryExecutor
from application.permission_manager import require
from infrastructure.logging.optimized_db_logger import log_hist
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lecture : situation d'un salarié
# ---------------------------------------------------------------------------

def get_mobilite(personnel_id: int) -> Optional[Dict]:
    """Retourne la situation de mobilité active du salarié (sans date_fin)."""
    return QueryExecutor.fetch_one(
        """
        SELECT * FROM personnel_mobilite
        WHERE personnel_id = %s AND actif = 1 AND date_fin IS NULL
        ORDER BY date_effet DESC LIMIT 1
        """,
        (personnel_id,),
        dictionary=True,
    )


def get_historique_mobilite(personnel_id: int) -> List[Dict]:
    """Retourne tout l'historique de mobilité du salarié."""
    return QueryExecutor.fetch_all(
        "SELECT * FROM personnel_mobilite WHERE personnel_id = %s ORDER BY date_effet DESC",
        (personnel_id,),
        dictionary=True,
    )


def _distance_prime_source(personnel_id: int) -> Optional[Dict]:
    """Retourne la distance à utiliser pour la prime mobilité."""
    row = QueryExecutor.fetch_one(
        """
        SELECT
            p.id AS personnel_id, p.nom, p.prenom, p.matricule,
            pm.id AS mobilite_id, pm.mode_transport, pm.distance_km, pm.cv_fiscaux,
            pm.ville_depart, pm.cp_depart, pm.date_effet AS date_effet_distance,
            'personnel_mobilite' AS source_distance
        FROM personnel p
        JOIN personnel_mobilite pm
          ON pm.personnel_id = p.id
         AND pm.actif = 1
         AND pm.date_fin IS NULL
         AND pm.date_effet <= CURDATE()
        WHERE p.id = %s AND UPPER(COALESCE(p.statut, '')) = 'ACTIF'
        ORDER BY pm.date_effet DESC, pm.id DESC
        LIMIT 1
        """,
        (personnel_id,),
        dictionary=True,
    )
    if row and row.get('distance_km') is not None:
        return row

    return QueryExecutor.fetch_one(
        """
        SELECT
            p.id AS personnel_id, p.nom, p.prenom, p.matricule,
            NULL AS mobilite_id,
            'voiture' AS mode_transport,
            COALESCE(pi.distance_mairie_km, pi.distance_commune_km, pi.distance_domicile_km) AS distance_km,
            pv.cv_fiscaux AS cv_fiscaux,
            pi.ville_adresse AS ville_depart,
            pi.cp_adresse AS cp_depart,
            pi.distance_calculee_at AS date_effet_distance,
            CASE
              WHEN pi.distance_mairie_km IS NOT NULL THEN 'personnel_infos.distance_mairie_km'
              WHEN pi.distance_commune_km IS NOT NULL THEN 'personnel_infos.distance_commune_km'
              WHEN pi.distance_domicile_km IS NOT NULL THEN 'personnel_infos.distance_domicile_km'
              ELSE NULL
            END AS source_distance
        FROM personnel p
        LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
        LEFT JOIN personnel_vehicule pv
          ON pv.personnel_id = p.id
         AND pv.actif = 1
         AND pv.date_fin IS NULL
        WHERE p.id = %s
          AND UPPER(COALESCE(p.statut, '')) = 'ACTIF'
          AND COALESCE(pi.distance_mairie_km, pi.distance_commune_km, pi.distance_domicile_km) IS NOT NULL
        ORDER BY pv.date_debut DESC, pv.id DESC
        LIMIT 1
        """,
        (personnel_id,),
        dictionary=True,
    )


def get_prime_courante(personnel_id: int) -> Optional[Dict]:
    """Retourne la prime et le taux IK applicables aujourd'hui, sans dépendre de la vue SQL."""
    src = _distance_prime_source(personnel_id)
    if not src or src.get('distance_km') is None:
        return None

    distance = float(src['distance_km'])
    prime = calculer_prime(distance)
    ik = calculer_ik(int(src['cv_fiscaux'])) if src.get('cv_fiscaux') else None

    return {
        **src,
        'prime_journaliere': prime.get('taux_journalier') if prime else None,
        'palier_libelle': prime.get('description') if prime else None,
        'date_effet_bareme': prime.get('date_effet') if prime else None,
        'ik_taux_km': ik.get('taux_km') if ik else None,
        'ik_libelle': ik.get('description') if ik else None,
    }


def _get_baremes_prime_applicables(reference_date: date) -> List[Dict]:
    """Retourne les paliers applicables a une date, tries du plus recent au plus ancien."""
    return QueryExecutor.fetch_all(
        """
        SELECT taux_journalier, description, date_effet, distance_min_km, distance_max_km
        FROM mobilite_palier
        WHERE actif = 1
          AND date_effet <= %s
          AND (date_fin_effet IS NULL OR date_fin_effet >= %s)
        ORDER BY date_effet DESC, distance_min_km
        """,
        (reference_date, reference_date),
        dictionary=True,
    )


def _get_baremes_ik_applicables(reference_date: date) -> List[Dict]:
    """Retourne les baremes IK applicables a une date, tries du plus recent au plus ancien."""
    return QueryExecutor.fetch_all(
        """
        SELECT taux_km, description, date_effet, cv_min, cv_max
        FROM mobilite_ik
        WHERE actif = 1
          AND date_effet <= %s
          AND (date_fin_effet IS NULL OR date_fin_effet >= %s)
        ORDER BY date_effet DESC, cv_min
        """,
        (reference_date, reference_date),
        dictionary=True,
    )


def _match_prime_bareme(distance_km: float, paliers: List[Dict]) -> Optional[Dict]:
    """Trouve en memoire le palier correspondant a une distance."""
    if distance_km is None:
        return None

    distance_palier = normaliser_distance_palier(distance_km)
    for palier in paliers:
        distance_min = float(palier['distance_min_km'])
        distance_max = palier.get('distance_max_km')
        if distance_palier < distance_min:
            continue
        if distance_max is not None and distance_palier > float(distance_max):
            continue
        return palier
    return None


def _match_ik_bareme(cv_fiscaux: Optional[int], baremes: List[Dict]) -> Optional[Dict]:
    """Trouve en memoire le bareme IK correspondant a des CV fiscaux."""
    if not cv_fiscaux:
        return None

    cv = int(cv_fiscaux)
    for bareme in baremes:
        cv_min = int(bareme['cv_min'])
        cv_max = bareme.get('cv_max')
        if cv < cv_min:
            continue
        if cv_max is not None and cv > int(cv_max):
            continue
        return bareme
    return None


def get_toutes_primes_actives() -> List[Dict]:
    """Retourne la prime applicable pour tous les salaries actifs."""
    ref = date.today()
    paliers = _get_baremes_prime_applicables(ref)
    baremes_ik = _get_baremes_ik_applicables(ref)

    mobilite_rows = QueryExecutor.fetch_all(
        """
        SELECT
            p.id AS personnel_id, p.nom, p.prenom, p.matricule,
            pm.id AS mobilite_id, pm.mode_transport, pm.distance_km, pm.cv_fiscaux,
            pm.ville_depart, pm.cp_depart, pm.date_effet AS date_effet_distance,
            'personnel_mobilite' AS source_distance
        FROM personnel p
        JOIN personnel_mobilite pm
          ON pm.personnel_id = p.id
         AND pm.actif = 1
         AND pm.date_fin IS NULL
         AND pm.date_effet <= CURDATE()
        WHERE UPPER(COALESCE(p.statut, '')) = 'ACTIF'
          AND pm.distance_km IS NOT NULL
        ORDER BY p.nom, p.prenom, p.id, pm.date_effet DESC, pm.id DESC
        """,
        dictionary=True,
    )

    sources_by_personnel: Dict[int, Dict] = {}
    for row in mobilite_rows:
        sources_by_personnel.setdefault(row['personnel_id'], row)

    fallback_rows = QueryExecutor.fetch_all(
        """
        SELECT
            p.id AS personnel_id, p.nom, p.prenom, p.matricule,
            NULL AS mobilite_id,
            'voiture' AS mode_transport,
            COALESCE(pi.distance_mairie_km, pi.distance_commune_km, pi.distance_domicile_km) AS distance_km,
            pv.cv_fiscaux AS cv_fiscaux,
            pi.ville_adresse AS ville_depart,
            pi.cp_adresse AS cp_depart,
            pi.distance_calculee_at AS date_effet_distance,
            CASE
              WHEN pi.distance_mairie_km IS NOT NULL THEN 'personnel_infos.distance_mairie_km'
              WHEN pi.distance_commune_km IS NOT NULL THEN 'personnel_infos.distance_commune_km'
              WHEN pi.distance_domicile_km IS NOT NULL THEN 'personnel_infos.distance_domicile_km'
              ELSE NULL
            END AS source_distance
        FROM personnel p
        LEFT JOIN personnel_infos pi ON pi.personnel_id = p.id
        LEFT JOIN personnel_vehicule pv
          ON pv.personnel_id = p.id
         AND pv.actif = 1
         AND pv.date_fin IS NULL
        WHERE UPPER(COALESCE(p.statut, '')) = 'ACTIF'
          AND COALESCE(pi.distance_mairie_km, pi.distance_commune_km, pi.distance_domicile_km) IS NOT NULL
        ORDER BY p.nom, p.prenom, p.id, pv.date_debut DESC, pv.id DESC
        """,
        dictionary=True,
    )
    for row in fallback_rows:
        sources_by_personnel.setdefault(row['personnel_id'], row)

    result = []
    rows = sorted(
        sources_by_personnel.values(),
        key=lambda r: ((r.get('nom') or ''), (r.get('prenom') or ''), r.get('personnel_id') or 0),
    )
    for src in rows:
        distance = float(src['distance_km'])
        prime = _match_prime_bareme(distance, paliers)
        ik = _match_ik_bareme(src.get('cv_fiscaux'), baremes_ik)
        result.append({
            **src,
            'prime_journaliere': prime.get('taux_journalier') if prime else None,
            'palier_libelle': prime.get('description') if prime else None,
            'date_effet_bareme': prime.get('date_effet') if prime else None,
            'ik_taux_km': ik.get('taux_km') if ik else None,
            'ik_libelle': ik.get('description') if ik else None,
        })
    return result


# ---------------------------------------------------------------------------
# Calcul explicite (sans passer par la vue)
# ---------------------------------------------------------------------------

def normaliser_distance_palier(distance_km: float) -> int:
    """
    Retourne le kilomètre entier utilisé pour chercher le palier mobilité.

    La règle métier prend l'unité du kilométrage, sans arrondir au-dessus :
    6.52 km compte comme 6 km, 13.9 km comme 13 km.
    """
    return int(float(distance_km))


def calculer_prime(distance_km: float, reference_date: Optional[date] = None) -> Optional[Dict]:
    """
    Retourne le palier de prime applicable pour une distance donnée.

    Les paliers sont en kilomètres entiers (0-6, 7-13, etc.) alors que
    les distances calculées peuvent être décimales. On utilise la partie
    entière de la distance : 6.52 km compte comme 6 km, 13.9 km comme 13 km.
    """
    if distance_km is None:
        return None

    ref = reference_date or date.today()
    distance_palier = normaliser_distance_palier(distance_km)

    return QueryExecutor.fetch_one(
        """
        SELECT taux_journalier, description, date_effet
        FROM mobilite_palier
        WHERE actif = 1
          AND date_effet <= %s
          AND (date_fin_effet IS NULL OR date_fin_effet >= %s)
          AND %s >= distance_min_km
          AND (distance_max_km IS NULL OR %s <= distance_max_km)
        ORDER BY date_effet DESC
        LIMIT 1
        """,
        (ref, ref, distance_palier, distance_palier),
        dictionary=True,
    )

def calculer_ik(cv_fiscaux: int, reference_date: Optional[date] = None) -> Optional[Dict]:
    """
    Retourne le taux IK applicable pour une puissance fiscale donnée
    à une date de référence (par défaut aujourd'hui).

    Retourne un dict avec : taux_km, description, date_effet
    ou None si aucun barème ne correspond.
    """
    ref = reference_date or date.today()
    return QueryExecutor.fetch_one(
        """
        SELECT taux_km, description, date_effet
        FROM mobilite_ik
        WHERE actif = 1
          AND date_effet <= %s
          AND (date_fin_effet IS NULL OR date_fin_effet >= %s)
          AND %s >= cv_min
          AND (cv_max IS NULL OR %s <= cv_max)
        ORDER BY date_effet DESC
        LIMIT 1
        """,
        (ref, ref, cv_fiscaux, cv_fiscaux),
        dictionary=True,
    )


def calculer_prime_mensuelle(personnel_id: int, jours_travailles: int) -> Optional[Dict]:
    """
    Calcule la prime mensuelle pour un salarié donné.

    Args:
        personnel_id : identifiant du salarié
        jours_travailles : nombre de jours travaillés dans le mois

    Returns:
        Dict avec : prime_journaliere, jours_travailles, montant_total, palier_libelle
        ou None si pas de données de mobilité.
    """
    prime_info = get_prime_courante(personnel_id)
    if not prime_info or prime_info.get('prime_journaliere') is None:
        return None

    taux = float(prime_info['prime_journaliere'])
    montant = round(taux * jours_travailles, 2)

    return {
        'prime_journaliere': taux,
        'jours_travailles': jours_travailles,
        'montant_total': montant,
        'palier_libelle': prime_info.get('palier_libelle'),
        'distance_km': prime_info.get('distance_km'),
        'mode_transport': prime_info.get('mode_transport'),
    }


# ---------------------------------------------------------------------------
# Écriture : situation d'un salarié
# ---------------------------------------------------------------------------

def create_mobilite(personnel_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """
    Enregistre la situation de mobilité d'un salarié.
    Clôture automatiquement l'entrée active précédente.
    """
    require('rh.mobilite.edit')
    try:
        date_effet = data.get('date_effet') or date.today()

        # Clôturer la ligne active précédente
        QueryExecutor.execute_write(
            """
            UPDATE personnel_mobilite
            SET date_fin = %s, actif = 0
            WHERE personnel_id = %s AND actif = 1 AND date_fin IS NULL
            """,
            (date_effet, personnel_id),
        )

        new_id = QueryExecutor.execute_write(
            """
            INSERT INTO personnel_mobilite
                (personnel_id, distance_km, cv_fiscaux, mode_transport,
                 adresse_depart, cp_depart, ville_depart,
                 methode_calcul, date_effet, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                personnel_id,
                data['distance_km'],
                data.get('cv_fiscaux') or None,
                data.get('mode_transport', 'voiture'),
                data.get('adresse_depart') or None,
                data.get('cp_depart') or None,
                data.get('ville_depart') or None,
                data.get('methode_calcul', 'manuel'),
                date_effet,
                data.get('notes') or None,
            ),
        )
        log_hist(
            "CREATION_MOBILITE",
            f"Mobilité enregistrée : {data['distance_km']} km "
            f"({data.get('mode_transport', 'voiture')}) pour personnel {personnel_id}",
            operateur_id=personnel_id,
        )
        return True, "Enregistrement créé", new_id
    except Exception as e:
        logger.exception(f"Erreur create_mobilite: {e}")
        return False, str(e), None


def update_mobilite(record_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour un enregistrement de mobilité existant."""
    require('rh.mobilite.edit')
    try:
        QueryExecutor.execute_write(
            """
            UPDATE personnel_mobilite
            SET distance_km    = %s,
                cv_fiscaux     = %s,
                mode_transport = %s,
                adresse_depart = %s,
                cp_depart      = %s,
                ville_depart   = %s,
                methode_calcul = %s,
                date_effet     = %s,
                notes          = %s
            WHERE id = %s
            """,
            (
                data['distance_km'],
                data.get('cv_fiscaux') or None,
                data.get('mode_transport', 'voiture'),
                data.get('adresse_depart') or None,
                data.get('cp_depart') or None,
                data.get('ville_depart') or None,
                data.get('methode_calcul', 'manuel'),
                data.get('date_effet') or date.today(),
                data.get('notes') or None,
                record_id,
            ),
        )
        log_hist("MODIFICATION_MOBILITE", f"Mobilité {record_id} modifiée")
        return True, "Enregistrement mis à jour"
    except Exception as e:
        logger.exception(f"Erreur update_mobilite: {e}")
        return False, str(e)


def delete_mobilite(record_id: int) -> Tuple[bool, str]:
    """Supprime un enregistrement de mobilité."""
    require('rh.mobilite.edit')
    try:
        QueryExecutor.execute_write(
            "DELETE FROM personnel_mobilite WHERE id = %s", (record_id,)
        )
        log_hist("SUPPRESSION_MOBILITE", f"Mobilité {record_id} supprimée")
        return True, "Enregistrement supprimé"
    except Exception as e:
        logger.exception(f"Erreur delete_mobilite: {e}")
        return False, str(e)


# ---------------------------------------------------------------------------
# Lecture : barèmes (pour UI de configuration)
# ---------------------------------------------------------------------------

def get_paliers(actif_only: bool = True) -> List[Dict]:
    """Retourne les paliers de prime mobilité."""
    where = "WHERE actif = 1" if actif_only else ""
    return QueryExecutor.fetch_all(
        f"SELECT * FROM mobilite_palier {where} ORDER BY date_effet DESC, distance_min_km",
        dictionary=True,
    )


def get_baremes_ik(actif_only: bool = True) -> List[Dict]:
    """Retourne les barèmes IK."""
    where = "WHERE actif = 1" if actif_only else ""
    return QueryExecutor.fetch_all(
        f"SELECT * FROM mobilite_ik {where} ORDER BY date_effet DESC, cv_min",
        dictionary=True,
    )


# ---------------------------------------------------------------------------
# Véhicules du salarié
# ---------------------------------------------------------------------------

def get_vehicule_actif(personnel_id: int) -> Optional[Dict]:
    """Retourne le véhicule actuellement utilisé par le salarié."""
    return QueryExecutor.fetch_one(
        """
        SELECT * FROM personnel_vehicule
        WHERE personnel_id = %s AND actif = 1 AND date_fin IS NULL
        ORDER BY date_debut DESC LIMIT 1
        """,
        (personnel_id,),
        dictionary=True,
    )


def get_vehicules(personnel_id: int) -> List[Dict]:
    """Retourne tous les véhicules (historique) du salarié."""
    return QueryExecutor.fetch_all(
        "SELECT * FROM personnel_vehicule WHERE personnel_id = %s ORDER BY actif DESC, date_debut DESC",
        (personnel_id,),
        dictionary=True,
    )


def create_vehicule(personnel_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """
    Enregistre un véhicule pour le salarié.
    Si actif=True, clôture le véhicule actif précédent.
    """
    require('rh.mobilite.edit')
    try:
        est_actif = bool(data.get('actif', True))
        date_debut = data.get('date_debut') or date.today()

        if est_actif:
            QueryExecutor.execute_write(
                """
                UPDATE personnel_vehicule
                SET date_fin = %s, actif = 0
                WHERE personnel_id = %s AND actif = 1 AND date_fin IS NULL
                """,
                (date_debut, personnel_id),
            )

        new_id = QueryExecutor.execute_write(
            """
            INSERT INTO personnel_vehicule
                (personnel_id, immatriculation, marque, modele, annee,
                 cv_fiscaux, energie, actif, date_debut, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                personnel_id,
                data.get('immatriculation') or None,
                data.get('marque') or None,
                data.get('modele') or None,
                data.get('annee') or None,
                data['cv_fiscaux'],
                data.get('energie', 'essence'),
                1 if est_actif else 0,
                date_debut,
                data.get('notes') or None,
            ),
        )

        label = f"{data.get('marque', '')} {data.get('modele', '')}".strip() or f"véhicule {new_id}"
        log_hist(
            "CREATION_VEHICULE",
            f"Véhicule ajouté : {label} — {data['cv_fiscaux']} CV ({data.get('energie', 'essence')}) "
            f"pour personnel {personnel_id}",
            operateur_id=personnel_id,
        )
        return True, "Véhicule enregistré", new_id
    except Exception as e:
        logger.exception(f"Erreur create_vehicule: {e}")
        return False, str(e), None


def update_vehicule(record_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour les informations d'un véhicule."""
    require('rh.mobilite.edit')
    try:
        QueryExecutor.execute_write(
            """
            UPDATE personnel_vehicule
            SET immatriculation = %s,
                marque          = %s,
                modele          = %s,
                annee           = %s,
                cv_fiscaux      = %s,
                energie         = %s,
                date_debut      = %s,
                notes           = %s
            WHERE id = %s
            """,
            (
                data.get('immatriculation') or None,
                data.get('marque') or None,
                data.get('modele') or None,
                data.get('annee') or None,
                data['cv_fiscaux'],
                data.get('energie', 'essence'),
                data.get('date_debut') or None,
                data.get('notes') or None,
                record_id,
            ),
        )
        log_hist("MODIFICATION_VEHICULE", f"Véhicule {record_id} modifié")
        return True, "Véhicule mis à jour"
    except Exception as e:
        logger.exception(f"Erreur update_vehicule: {e}")
        return False, str(e)


def delete_vehicule(record_id: int) -> Tuple[bool, str]:
    """Supprime un véhicule."""
    require('rh.mobilite.edit')
    try:
        QueryExecutor.execute_write(
            "DELETE FROM personnel_vehicule WHERE id = %s", (record_id,)
        )
        log_hist("SUPPRESSION_VEHICULE", f"Véhicule {record_id} supprimé")
        return True, "Véhicule supprimé"
    except Exception as e:
        logger.exception(f"Erreur delete_vehicule: {e}")
        return False, str(e)


def get_cv_fiscaux_actif(personnel_id: int) -> Optional[int]:
    """
    Retourne les CV fiscaux du véhicule actif du salarié.
    Utilisé pour pré-remplir le champ cv_fiscaux dans le formulaire mobilité.
    """
    vehicule = get_vehicule_actif(personnel_id)
    return vehicule['cv_fiscaux'] if vehicule else None
