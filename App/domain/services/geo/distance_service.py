# -*- coding: utf-8 -*-
"""
Service de calcul de distance routière domicile-entreprise.

Calcule deux distances :
  1. Mairie : mairie commune personnel (OSM) → mairie commune entreprise
     Affichée à l'utilisateur sur la fiche individuelle.
  2. Commune : centroïde commune personnel (geo.api.gouv.fr) →
     centroïde commune entreprise
     Utilisée pour statistiques agrégées et exports RH.

L'adresse exacte du personnel N'EST JAMAIS géocodée (RGPD-friendly).
Seuls CP + ville sont utilisés pour résoudre la commune.

APIs :
  - geo.api.gouv.fr : code INSEE + centroïde commune (gratuit, illimité)
  - overpass-api.de : coordonnées mairie via tag amenity=townhall (gratuit)
  - OpenRouteService : distance routière (clé gratuite, 2000 req/jour)
  - OSRM public : fallback routing sans clé
"""

import os
import json
import urllib.request
import urllib.parse
from typing import Optional
from datetime import datetime

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

_TIMEOUT_SHORT = 5       # APIs rapides (geo.api.gouv.fr)
_TIMEOUT_LONG = 25       # Overpass peut throttler
_ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
_OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
_OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# ═══════════════════════════════════════════════════════════════
# Cache de session — garde-fous anti-surconsommation
# ═══════════════════════════════════════════════════════════════

_failed_communes: set[str] = set()
_mairie_cache: dict[str, tuple[float, float]] = {}


def _commune_key(cp: str, ville: str) -> str:
    return f"{(cp or '').strip()}|{(ville or '').strip().lower()}"


def is_commune_known_failed(cp: str, ville: str) -> bool:
    return _commune_key(cp, ville) in _failed_communes


def mark_commune_failed(cp: str, ville: str) -> None:
    _failed_communes.add(_commune_key(cp, ville))


def clear_failed_cache() -> None:
    _failed_communes.clear()
    _mairie_cache.clear()


# ═══════════════════════════════════════════════════════════════
# Configuration entreprise
# ═══════════════════════════════════════════════════════════════

_company_commune_cache: Optional[tuple[float, float]] = None
_company_mairie_cache: Optional[tuple[float, float]] = None


def _get_company_commune_coords() -> Optional[tuple[float, float]]:
    """Centroïde de la commune de l'entreprise, résolu au premier appel."""
    global _company_commune_cache
    if _company_commune_cache is not None:
        return _company_commune_cache

    code_insee = os.getenv("EMAC_COMPANY_INSEE")
    if not code_insee:
        logger.warning("EMAC_COMPANY_INSEE non défini — distance commune impossible")
        return None

    coords = get_commune_centroid_by_code(code_insee)
    if coords:
        _company_commune_cache = coords
    return coords


def _get_company_mairie_coords() -> Optional[tuple[float, float]]:
    """
    Mairie de l'entreprise.

    Priorité :
      1. Variables EMAC_COMPANY_MAIRIE_LAT/LON (recommandé : évite Overpass)
      2. Résolution Overpass depuis EMAC_COMPANY_COMMUNE
      3. Fallback centroïde commune
    """
    global _company_mairie_cache
    if _company_mairie_cache is not None:
        return _company_mairie_cache

    lat = os.getenv("EMAC_COMPANY_MAIRIE_LAT")
    lon = os.getenv("EMAC_COMPANY_MAIRIE_LON")
    if lat and lon:
        try:
            _company_mairie_cache = (float(lat), float(lon))
            return _company_mairie_cache
        except ValueError:
            logger.error(f"EMAC_COMPANY_MAIRIE_LAT/LON invalides : {lat}, {lon}")

    commune = os.getenv("EMAC_COMPANY_COMMUNE")
    if commune:
        coords = get_mairie_coords(commune)
        if coords:
            _company_mairie_cache = coords
            logger.info(
                f"Mairie entreprise résolue via Overpass : {coords} "
                f"(ajouter EMAC_COMPANY_MAIRIE_LAT/LON dans .env pour mettre en cache)"
            )
            return coords

    logger.info("Mairie entreprise introuvable — fallback sur centroïde commune")
    fallback = _get_company_commune_coords()
    if fallback:
        _company_mairie_cache = fallback
    return fallback


# ═══════════════════════════════════════════════════════════════
# Résolution commune (geo.api.gouv.fr)
# ═══════════════════════════════════════════════════════════════

def get_commune_centroid_by_code(code_insee: str) -> Optional[tuple[float, float]]:
    """Centroïde d'une commune par code INSEE via geo.api.gouv.fr."""
    if not code_insee or len(code_insee) != 5:
        return None

    url = f"https://geo.api.gouv.fr/communes/{code_insee}?fields=centre&format=json"
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_SHORT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur geo.api.gouv.fr (code={code_insee}): {e}")
        return None

    centre = data.get('centre', {}).get('coordinates', [])
    if len(centre) != 2:
        return None
    return centre[1], centre[0]  # [lon, lat] → (lat, lon)


def resolve_commune(cp: str, ville: str) -> Optional[dict]:
    """
    Résout une commune à partir de CP + nom de ville.

    Returns:
        {'code_insee': '64024', 'nom': 'Anglet', 'lat': 43.4779, 'lon': -1.5177}
        ou None si non trouvée.
    """
    if not cp or not ville:
        return None

    params = urllib.parse.urlencode({
        'codePostal': cp,
        'fields': 'nom,code,centre',
        'format': 'json',
    })
    url = f"https://geo.api.gouv.fr/communes?{params}"

    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_SHORT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur résolution commune CP={cp}: {e}")
        return None

    if not data:
        return None

    ville_lower = ville.strip().lower()
    best = None
    for commune in data:
        if commune.get('nom', '').strip().lower() == ville_lower:
            best = commune
            break

    if best is None:
        best = data[0]
        logger.debug(
            f"Pas de match exact pour '{ville}' dans CP {cp}, "
            f"fallback sur '{best.get('nom')}'"
        )

    centre = best.get('centre', {}).get('coordinates', [])
    if len(centre) != 2:
        return None

    return {
        'code_insee': best.get('code', ''),
        'nom': best.get('nom', ''),
        'lat': centre[1],
        'lon': centre[0],
    }


# ═══════════════════════════════════════════════════════════════
# Résolution mairie (OSM Overpass)
# ═══════════════════════════════════════════════════════════════

def get_mairie_coords(commune_nom: str, code_insee: str = None) -> Optional[tuple[float, float]]:
    """
    Retourne (lat, lon) de la mairie d'une commune via OSM Overpass.

    Args:
        commune_nom: Nom exact de la commune (ex: 'Anglet')
        code_insee: Code INSEE pour désambiguïsation (optionnel)
    """
    if not commune_nom:
        return None

    cache_key = code_insee or commune_nom.strip().lower()
    if cache_key in _mairie_cache:
        return _mairie_cache[cache_key]

    insee_filter = f'["ref:INSEE"="{code_insee}"]' if code_insee else ''
    query = f"""
    [out:json][timeout:20];
    area["ISO3166-1"="FR"]->.france;
    (
      node["amenity"="townhall"]["name"="{commune_nom}"]{insee_filter}(area.france);
      way["amenity"="townhall"]["name"="{commune_nom}"]{insee_filter}(area.france);
      relation["amenity"="townhall"]["name"="{commune_nom}"]{insee_filter}(area.france);
    );
    out center 1;
    """.strip()

    try:
        data = urllib.parse.urlencode({'data': query}).encode('utf-8')
        req = urllib.request.Request(_OVERPASS_URL, data=data)
        with urllib.request.urlopen(req, timeout=_TIMEOUT_LONG) as resp:
            result = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur Overpass (mairie '{commune_nom}'): {e}")
        return None

    elements = result.get('elements', [])
    if not elements:
        logger.debug(f"Pas de townhall OSM pour '{commune_nom}'")
        return None

    el = elements[0]
    if el.get('type') == 'node':
        lat, lon = el.get('lat'), el.get('lon')
    else:
        center = el.get('center', {})
        lat, lon = center.get('lat'), center.get('lon')

    if lat is None or lon is None:
        return None

    _mairie_cache[cache_key] = (lat, lon)
    return lat, lon


# ═══════════════════════════════════════════════════════════════
# Calcul de distance routière (ORS + fallback OSRM)
# ═══════════════════════════════════════════════════════════════

def _compute_route_ors(origin, destination, api_key):
    """Calcul via OpenRouteService. Retourne (distance_km, duree_min)."""
    origin_str = f"{origin[1]},{origin[0]}"
    dest_str = f"{destination[1]},{destination[0]}"
    url = f"{_ORS_URL}?api_key={api_key}&start={origin_str}&end={dest_str}"

    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_SHORT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur ORS: {e}")
        return None

    features = data.get('features', [])
    if not features:
        return None
    summary = features[0].get('properties', {}).get('summary', {})
    d_m, d_s = summary.get('distance'), summary.get('duration')
    if d_m is None or d_s is None:
        return None
    return round(d_m / 1000, 2), round(d_s / 60)


def _compute_route_osrm(origin, destination):
    """Calcul via OSRM public (fallback). Retourne (distance_km, duree_min)."""
    coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    url = f"{_OSRM_URL}/{coords}?overview=false"

    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_SHORT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur OSRM: {e}")
        return None

    routes = data.get('routes', [])
    if not routes:
        return None
    d_m, d_s = routes[0].get('distance'), routes[0].get('duration')
    if d_m is None or d_s is None:
        return None
    return round(d_m / 1000, 2), round(d_s / 60)


def _compute_route(origin, destination):
    """Calcul de route avec ORS si clé définie, sinon OSRM."""
    api_key = os.getenv("EMAC_ORS_API_KEY")
    if api_key:
        result = _compute_route_ors(origin, destination, api_key)
        if result:
            return result
        logger.warning("ORS a échoué — fallback OSRM")
    return _compute_route_osrm(origin, destination)


# ═══════════════════════════════════════════════════════════════
# Fonction principale : calcul des deux distances
# ═══════════════════════════════════════════════════════════════

def compute_distances_for_commune(cp: str, ville: str) -> Optional[dict]:
    """
    Calcule les deux distances (mairie + commune) pour une commune donnée.

    Args:
        cp: Code postal du personnel
        ville: Nom de la commune du personnel

    Returns:
        {
            'code_insee_commune': '75102',
            'commune_lat': 48.8692, 'commune_lon': 2.3413,
            'distance_commune_km': 11.80, 'duree_trajet_commune_min': 16,
            'mairie_lat': 48.8634, 'mairie_lon': 2.3388,
            'distance_mairie_km': 12.10, 'duree_trajet_mairie_min': 17,
            'distance_calculee_at': datetime,
        }
        ou None si aucune distance n'a pu être calculée.
    """
    if not cp or not ville:
        return None

    if is_commune_known_failed(cp, ville):
        logger.debug(f"Commune en échec connu, skip : {cp} {ville}")
        return None

    commune = resolve_commune(cp, ville)
    if commune is None:
        logger.info(f"Commune introuvable pour CP={cp}, ville='{ville}'")
        mark_commune_failed(cp, ville)
        return None

    result = {
        'code_insee_commune': commune['code_insee'],
        'commune_lat': commune['lat'],
        'commune_lon': commune['lon'],
        'distance_commune_km': None,
        'duree_trajet_commune_min': None,
        'mairie_lat': None,
        'mairie_lon': None,
        'distance_mairie_km': None,
        'duree_trajet_mairie_min': None,
        'distance_calculee_at': datetime.now(),
    }

    any_success = False

    company_commune = _get_company_commune_coords()
    if company_commune:
        commune_coords = (commune['lat'], commune['lon'])
        route = _compute_route(commune_coords, company_commune)
        if route:
            result['distance_commune_km'], result['duree_trajet_commune_min'] = route
            any_success = True

    mairie = get_mairie_coords(commune['nom'], commune['code_insee'])
    if mairie:
        result['mairie_lat'], result['mairie_lon'] = mairie
        company_mairie = _get_company_mairie_coords()
        if company_mairie:
            route = _compute_route(mairie, company_mairie)
            if route:
                result['distance_mairie_km'], result['duree_trajet_mairie_min'] = route
                any_success = True

    if not any_success:
        logger.warning(f"Aucune distance calculée pour {cp} {ville}")

    return result
