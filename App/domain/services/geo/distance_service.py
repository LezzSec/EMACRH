# -*- coding: utf-8 -*-
"""
Service de calcul de distance routière entre un domicile et l'entreprise.

Utilise OpenRouteService (clé API gratuite jusqu'à 2000 requêtes/jour).
Fallback sur OSRM public (router.project-osrm.org) si la clé n'est pas définie.

Lecture de la config :
  - EMAC_COMPANY_LAT, EMAC_COMPANY_LON : coordonnées de l'entreprise
  - EMAC_ORS_API_KEY (optionnel) : clé OpenRouteService
"""

import os
import json
import urllib.request
import urllib.parse
from typing import Optional
from datetime import datetime

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

_TIMEOUT = 8  # secondes — les APIs de routing peuvent être plus lentes que le géocodage
_ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
_OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

# Cache de session : adresses dont le géocodage OU le routing a échoué.
# Évite de retenter en boucle les adresses invalides dans la même session.
# Vidé automatiquement au redémarrage de l'app.
_failed_addresses: set = set()


def _normalize_address(adresse: str, cp: str, ville: str) -> str:
    """Normalise une adresse pour la comparaison (lowercase, strip, espaces)."""
    parts = [s.strip().lower() for s in (adresse or "", cp or "", ville or "") if s]
    return " ".join(parts)


def is_address_known_failed(full_address: str) -> bool:
    """Retourne True si cette adresse a déjà échoué dans cette session."""
    return full_address.strip().lower() in _failed_addresses


def mark_address_failed(full_address: str) -> None:
    """Marque une adresse comme ayant échoué (pour ne pas retenter)."""
    _failed_addresses.add(full_address.strip().lower())


def clear_failed_addresses_cache() -> None:
    """Vide le cache (utile pour un retry manuel utilisateur)."""
    _failed_addresses.clear()


def _get_company_coords() -> Optional[tuple]:
    """Retourne (lat, lon) de l'entreprise depuis les variables d'environnement."""
    lat = os.getenv("EMAC_COMPANY_LAT")
    lon = os.getenv("EMAC_COMPANY_LON")
    if not lat or not lon:
        logger.warning("EMAC_COMPANY_LAT/LON non définis — calcul distance impossible")
        return None
    try:
        return float(lat), float(lon)
    except ValueError:
        logger.error(f"EMAC_COMPANY_LAT/LON invalides : {lat}, {lon}")
        return None


def geocode_address(full_address: str) -> Optional[tuple]:
    """
    Géocode une adresse française complète en (latitude, longitude).

    Utilise api-adresse.data.gouv.fr (même API que address_service).

    Args:
        full_address: Adresse complète, ex: "12 Rue de la Paix 75002 Paris"

    Returns:
        (lat, lon) ou None si l'adresse n'est pas trouvée.
    """
    if not full_address or len(full_address.strip()) < 5:
        return None

    params = urllib.parse.urlencode({
        'q': full_address,
        'limit': 1,
    })
    url = f"https://api-adresse.data.gouv.fr/search/?{params}"

    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur géocodage '{full_address}': {e}")
        return None

    features = data.get('features', [])
    if not features:
        return None

    coords = features[0].get('geometry', {}).get('coordinates', [])
    if len(coords) != 2:
        return None

    # L'API renvoie [lon, lat] — on inverse pour retourner (lat, lon)
    return coords[1], coords[0]


def _compute_route_ors(
    origin: tuple,
    destination: tuple,
    api_key: str
) -> Optional[tuple]:
    """
    Calcule la route via OpenRouteService.

    Returns:
        (distance_km, duree_min) ou None si échec.
    """
    origin_str = f"{origin[1]},{origin[0]}"           # lon,lat
    dest_str = f"{destination[1]},{destination[0]}"    # lon,lat
    url = f"{_ORS_URL}?api_key={api_key}&start={origin_str}&end={dest_str}"

    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur ORS: {e}")
        return None

    features = data.get('features', [])
    if not features:
        return None

    summary = features[0].get('properties', {}).get('summary', {})
    distance_m = summary.get('distance')
    duration_s = summary.get('duration')
    if distance_m is None or duration_s is None:
        return None

    return round(distance_m / 1000, 2), round(duration_s / 60)


def _compute_route_osrm(
    origin: tuple,
    destination: tuple
) -> Optional[tuple]:
    """
    Calcule la route via le serveur public OSRM (fallback sans clé).

    Serveur public sans SLA — pour usage de développement uniquement.

    Returns:
        (distance_km, duree_min) ou None si échec.
    """
    coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    url = f"{_OSRM_URL}/{coords}?overview=false"

    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur OSRM: {e}")
        return None

    routes = data.get('routes', [])
    if not routes:
        return None

    distance_m = routes[0].get('distance')
    duration_s = routes[0].get('duration')
    if distance_m is None or duration_s is None:
        return None

    return round(distance_m / 1000, 2), round(duration_s / 60)


def compute_distance_to_company(
    lat: float,
    lon: float
) -> Optional[dict]:
    """
    Calcule la distance routière entre un domicile et l'entreprise.

    Utilise ORS si EMAC_ORS_API_KEY est défini, sinon fallback OSRM.

    Args:
        lat: Latitude du domicile
        lon: Longitude du domicile

    Returns:
        {
            'distance_km': 12.45,
            'duree_min': 18,
            'calcule_at': datetime,
        }
        ou None si calcul impossible.
    """
    company = _get_company_coords()
    if company is None:
        return None

    api_key = os.getenv("EMAC_ORS_API_KEY")
    if api_key:
        result = _compute_route_ors((lat, lon), company, api_key)
    else:
        logger.debug("EMAC_ORS_API_KEY non défini — fallback OSRM public")
        result = _compute_route_osrm((lat, lon), company)

    if result is None:
        return None

    distance_km, duree_min = result
    return {
        'distance_km': distance_km,
        'duree_min': duree_min,
        'calcule_at': datetime.now(),
    }


def compute_distance_from_address(full_address: str) -> Optional[dict]:
    """
    Fonction de haut niveau : prend une adresse textuelle, géocode, calcule la distance.

    Args:
        full_address: Adresse complète, ex: "12 Rue de la Paix 75002 Paris"

    Returns:
        {
            'latitude': 48.8688,
            'longitude': 2.3320,
            'distance_km': 12.45,
            'duree_min': 18,
            'calcule_at': datetime,
        }
        ou None si échec (géocodage ou routing).
    """
    if not full_address or len(full_address.strip()) < 5:
        return None

    # Garde-fou : adresse déjà identifiée comme échouée cette session
    if is_address_known_failed(full_address):
        logger.debug(f"Adresse déjà en échec, skip : '{full_address}'")
        return None

    coords = geocode_address(full_address)
    if coords is None:
        logger.info(f"Géocodage échoué pour '{full_address}'")
        mark_address_failed(full_address)
        return None

    lat, lon = coords
    distance = compute_distance_to_company(lat, lon)

    if distance is None:
        # Géocodage OK mais routing KO : on retourne les coords quand même,
        # mais on NE marque PAS comme échouée (le routing peut marcher plus tard).
        return {
            'latitude': lat,
            'longitude': lon,
            'distance_km': None,
            'duree_min': None,
            'calcule_at': datetime.now(),
        }

    return {
        'latitude': lat,
        'longitude': lon,
        **distance,
    }
