# -*- coding: utf-8 -*-
"""
Service de calcul de distance routière domicile-entreprise.

Version corrigée :
- une seule fonction HTTP centralisée avec User-Agent, timeout, retry léger ;
- cache mémoire + cache SQLite persistant pour éviter de rappeler les APIs ;
- résolution commune via geo.api.gouv.fr ;
- mairie via Overpass en priorité, Nominatim en fallback ;
- routing ORS puis OSRM ;
- compatibilité conservée avec compute_distances_for_commune() ;
- compatibilité restaurée avec le script batch via compute_distance_from_address().
"""

import hashlib
import json
import math
import os
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

_TIMEOUT_SHORT = 12
_TIMEOUT_LONG = 25
_RETRIES = 2
_RETRY_SLEEP = 0.8

_GEO_API_URL = "https://geo.api.gouv.fr"
_ADRESSE_API_URL = "https://api-adresse.data.gouv.fr/search/"
_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
_OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

_USER_AGENT = os.getenv(
    "EMAC_HTTP_USER_AGENT",
    "EMAC-RH/1.0 (application interne entreprise; contact=admin@example.local)",
)

# Cache persistant simple. Peut être déplacé via EMAC_DISTANCE_CACHE_DB.
_CACHE_DB = Path(os.getenv("EMAC_DISTANCE_CACHE_DB", ".cache/distance_cache.sqlite"))
_CACHE_TTL_DAYS = int(os.getenv("EMAC_DISTANCE_CACHE_TTL_DAYS", "180"))

_failed_communes: set[str] = set()
_mairie_cache: dict[str, tuple[float, float]] = {}
_route_cache: dict[str, tuple[float, int]] = {}
_company_commune_cache: Optional[tuple[float, float]] = None
_company_mairie_cache: Optional[tuple[float, float]] = None


def _commune_key(cp: str, ville: str) -> str:
    return f"{(cp or '').strip()}|{(ville or '').strip().lower()}"


def is_commune_known_failed(cp: str, ville: str) -> bool:
    return _commune_key(cp, ville) in _failed_communes


def mark_commune_failed(cp: str, ville: str) -> None:
    _failed_communes.add(_commune_key(cp, ville))


def clear_failed_cache() -> None:
    _failed_communes.clear()
    _mairie_cache.clear()
    _route_cache.clear()


def _valid_coords(coords: Any) -> bool:
    if not isinstance(coords, tuple) or len(coords) != 2:
        return False
    lat, lon = coords
    return isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and -90 <= lat <= 90 and -180 <= lon <= 180


def _http_json(url: str, *, timeout: int, method: str = "GET", data: bytes | None = None) -> Any | None:
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "application/json",
    }
    for attempt in range(_RETRIES + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            if attempt >= _RETRIES:
                logger.warning("Erreur HTTP JSON %s: %s", url[:120], exc)
                return None
            time.sleep(_RETRY_SLEEP * (attempt + 1))
    return None


def _cache_init() -> None:
    try:
        _CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(_CACHE_DB) as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS distance_cache (
                    key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
    except Exception as exc:
        logger.debug("Cache SQLite indisponible: %s", exc)


def _cache_get(key: str) -> Any | None:
    try:
        _cache_init()
        min_date = datetime.now() - timedelta(days=_CACHE_TTL_DAYS)
        with sqlite3.connect(_CACHE_DB) as con:
            row = con.execute("SELECT payload, created_at FROM distance_cache WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        payload, created_at = row
        if datetime.fromisoformat(created_at) < min_date:
            return None
        return json.loads(payload)
    except Exception:
        return None


def _cache_set(key: str, payload: Any) -> None:
    try:
        _cache_init()
        with sqlite3.connect(_CACHE_DB) as con:
            con.execute(
                "REPLACE INTO distance_cache(key, payload, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(payload), datetime.now().isoformat()),
            )
    except Exception:
        pass


def get_commune_centroid_by_code(code_insee: str) -> Optional[tuple[float, float]]:
    if not code_insee or len(code_insee) != 5:
        return None
    cache_key = f"commune_code:{code_insee}"
    cached = _cache_get(cache_key)
    if cached:
        return tuple(cached)  # type: ignore[return-value]

    url = f"{_GEO_API_URL}/communes/{urllib.parse.quote(code_insee)}?fields=centre&format=json"
    data = _http_json(url, timeout=_TIMEOUT_SHORT)
    centre = (data or {}).get("centre", {}).get("coordinates", [])
    if len(centre) != 2:
        return None
    coords = (float(centre[1]), float(centre[0]))
    if not _valid_coords(coords):
        return None
    _cache_set(cache_key, coords)
    return coords


def resolve_commune(cp: str, ville: str) -> Optional[dict]:
    if not cp or not ville:
        return None

    cp = cp.strip()
    ville_clean = ville.strip()
    cache_key = f"commune:{_commune_key(cp, ville_clean)}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    params = urllib.parse.urlencode({"codePostal": cp, "fields": "nom,code,centre", "format": "json"})
    data = _http_json(f"{_GEO_API_URL}/communes?{params}", timeout=_TIMEOUT_SHORT)
    if not data:
        return None

    ville_lower = ville_clean.lower()
    best = next((c for c in data if (c.get("nom") or "").strip().lower() == ville_lower), None)
    if best is None:
        # Plus sûr que l'ancien comportement : fallback seulement si le CP ne renvoie qu'une commune.
        if len(data) != 1:
            logger.warning("Commune ambiguë pour CP=%s ville='%s' : %s", cp, ville_clean, [c.get("nom") for c in data])
            return None
        best = data[0]

    centre = best.get("centre", {}).get("coordinates", [])
    if len(centre) != 2:
        return None
    result = {
        "code_insee": best.get("code", ""),
        "nom": best.get("nom", ""),
        "lat": float(centre[1]),
        "lon": float(centre[0]),
    }
    _cache_set(cache_key, result)
    return result


def _get_townhall_overpass(commune_nom: str, hint_lat: float | None, hint_lon: float | None) -> Optional[tuple[float, float]]:
    # Recherche limitée autour du centroïde quand possible, sinon par nom France.
    if hint_lat is not None and hint_lon is not None:
        query = f"""
        [out:json][timeout:12];
        (
          node["amenity"="townhall"](around:15000,{hint_lat},{hint_lon});
          way["amenity"="townhall"](around:15000,{hint_lat},{hint_lon});
          relation["amenity"="townhall"](around:15000,{hint_lat},{hint_lon});
        );
        out center tags 10;
        """
    else:
        safe_name = commune_nom.replace('"', '\\"')
        query = f"""
        [out:json][timeout:12];
        area["ISO3166-1"="FR"][admin_level=2]->.fr;
        (
          node["amenity"="townhall"]["addr:city"~"^{safe_name}$",i](area.fr);
          way["amenity"="townhall"]["addr:city"~"^{safe_name}$",i](area.fr);
          relation["amenity"="townhall"]["addr:city"~"^{safe_name}$",i](area.fr);
        );
        out center tags 10;
        """

    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    result = _http_json(_OVERPASS_URL, timeout=_TIMEOUT_LONG, method="POST", data=data)
    elements = (result or {}).get("elements", [])
    if not elements:
        return None

    def score(el: dict) -> float:
        tags = el.get("tags", {}) or {}
        name = (tags.get("name") or "").lower()
        s = 0.0 if commune_nom.lower() in name or "mairie" in name else 10.0
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if hint_lat is not None and hint_lon is not None and lat is not None and lon is not None:
            s += math.hypot(float(lat) - hint_lat, float(lon) - hint_lon)
        return s

    for el in sorted(elements, key=score):
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is not None and lon is not None:
            coords = (float(lat), float(lon))
            if _valid_coords(coords):
                return coords
    return None


def _get_townhall_nominatim(commune_nom: str, hint_lat: float | None, hint_lon: float | None) -> Optional[tuple[float, float]]:
    params = {
        "q": f"mairie {commune_nom}, France",
        "format": "json",
        "limit": "1",
    }
    if hint_lat is not None and hint_lon is not None:
        buf = 0.3
        params["viewbox"] = f"{hint_lon - buf},{hint_lat + buf},{hint_lon + buf},{hint_lat - buf}"
        params["bounded"] = "1"
    data = _http_json(f"{_NOMINATIM_URL}?{urllib.parse.urlencode(params)}", timeout=_TIMEOUT_SHORT)
    if not data:
        return None
    try:
        coords = (float(data[0]["lat"]), float(data[0]["lon"]))
    except Exception:
        return None
    return coords if _valid_coords(coords) else None


def get_mairie_coords(commune_nom: str, code_insee: str = None, hint_lat: float = None, hint_lon: float = None) -> Optional[tuple[float, float]]:
    if not commune_nom:
        return None
    cache_key = f"mairie:{code_insee or commune_nom.strip().lower()}"
    if cache_key in _mairie_cache:
        return _mairie_cache[cache_key]
    cached = _cache_get(cache_key)
    if cached:
        coords = tuple(cached)  # type: ignore[assignment]
        if _valid_coords(coords):
            _mairie_cache[cache_key] = coords  # type: ignore[assignment]
            return coords  # type: ignore[return-value]

    coords = _get_townhall_overpass(commune_nom, hint_lat, hint_lon)
    if coords is None:
        coords = _get_townhall_nominatim(commune_nom, hint_lat, hint_lon)
    if coords:
        _mairie_cache[cache_key] = coords
        _cache_set(cache_key, coords)
        return coords
    return None


def _route_key(origin: tuple[float, float], destination: tuple[float, float]) -> str:
    raw = f"{origin[0]:.5f},{origin[1]:.5f}>{destination[0]:.5f},{destination[1]:.5f}"
    return "route:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _compute_route_ors(origin: tuple[float, float], destination: tuple[float, float], api_key: str) -> Optional[tuple[float, int]]:
    params = urllib.parse.urlencode({
        "api_key": api_key,
        "start": f"{origin[1]},{origin[0]}",
        "end": f"{destination[1]},{destination[0]}",
    })
    data = _http_json(f"{_ORS_URL}?{params}", timeout=_TIMEOUT_LONG)
    features = (data or {}).get("features", [])
    if not features:
        return None
    summary = features[0].get("properties", {}).get("summary", {})
    d_m, d_s = summary.get("distance"), summary.get("duration")
    if d_m is None or d_s is None:
        return None
    return round(float(d_m) / 1000, 2), round(float(d_s) / 60)


def _compute_route_osrm(origin: tuple[float, float], destination: tuple[float, float]) -> Optional[tuple[float, int]]:
    coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    data = _http_json(f"{_OSRM_URL}/{coords}?overview=false", timeout=_TIMEOUT_LONG)
    routes = (data or {}).get("routes", [])
    if not routes:
        return None
    d_m, d_s = routes[0].get("distance"), routes[0].get("duration")
    if d_m is None or d_s is None:
        return None
    return round(float(d_m) / 1000, 2), round(float(d_s) / 60)


def _compute_route(origin: tuple[float, float], destination: tuple[float, float]) -> Optional[tuple[float, int]]:
    if not _valid_coords(origin) or not _valid_coords(destination):
        return None

    key = _route_key(origin, destination)
    if key in _route_cache:
        return _route_cache[key]
    cached = _cache_get(key)
    if cached:
        result = (float(cached[0]), int(cached[1]))
        _route_cache[key] = result
        return result

    api_key = os.getenv("EMAC_ORS_API_KEY")
    result = _compute_route_ors(origin, destination, api_key) if api_key else None
    if result is None:
        result = _compute_route_osrm(origin, destination)
    if result:
        _route_cache[key] = result
        _cache_set(key, result)
    return result


def _get_company_commune_coords() -> Optional[tuple[float, float]]:
    global _company_commune_cache
    if _company_commune_cache is not None:
        return _company_commune_cache

    lat, lon = os.getenv("EMAC_COMPANY_LAT"), os.getenv("EMAC_COMPANY_LON")
    if lat and lon:
        try:
            coords = (float(lat), float(lon))
            if _valid_coords(coords):
                _company_commune_cache = coords
                return coords
        except ValueError:
            logger.error("EMAC_COMPANY_LAT/LON invalides")

    code_insee = os.getenv("EMAC_COMPANY_INSEE")
    if code_insee:
        _company_commune_cache = get_commune_centroid_by_code(code_insee)
    return _company_commune_cache


def _get_company_mairie_coords() -> Optional[tuple[float, float]]:
    global _company_mairie_cache
    if _company_mairie_cache is not None:
        return _company_mairie_cache

    lat, lon = os.getenv("EMAC_COMPANY_MAIRIE_LAT"), os.getenv("EMAC_COMPANY_MAIRIE_LON")
    if lat and lon:
        try:
            coords = (float(lat), float(lon))
            if _valid_coords(coords):
                _company_mairie_cache = coords
                return coords
        except ValueError:
            logger.error("EMAC_COMPANY_MAIRIE_LAT/LON invalides")

    commune = os.getenv("EMAC_COMPANY_COMMUNE")
    if commune:
        centre = _get_company_commune_coords()
        _company_mairie_cache = get_mairie_coords(
            commune,
            code_insee=os.getenv("EMAC_COMPANY_INSEE"),
            hint_lat=centre[0] if centre else None,
            hint_lon=centre[1] if centre else None,
        )
    if _company_mairie_cache is None:
        _company_mairie_cache = _get_company_commune_coords()
    return _company_mairie_cache


def compute_distances_for_commune(cp: str, ville: str) -> Optional[dict]:
    if not cp or not ville:
        return None
    if is_commune_known_failed(cp, ville):
        return None

    commune = resolve_commune(cp, ville)
    if commune is None:
        mark_commune_failed(cp, ville)
        return None

    result = {
        "code_insee_commune": commune["code_insee"],
        "commune_lat": commune["lat"],
        "commune_lon": commune["lon"],
        "distance_commune_km": None,
        "duree_trajet_commune_min": None,
        "mairie_lat": None,
        "mairie_lon": None,
        "distance_mairie_km": None,
        "duree_trajet_mairie_min": None,
        "distance_calculee_at": datetime.now(),
    }

    any_success = False
    company_commune = _get_company_commune_coords()
    if company_commune:
        route = _compute_route((commune["lat"], commune["lon"]), company_commune)
        if route:
            result["distance_commune_km"], result["duree_trajet_commune_min"] = route
            any_success = True

    mairie = get_mairie_coords(commune["nom"], commune["code_insee"], commune["lat"], commune["lon"])
    if mairie:
        result["mairie_lat"], result["mairie_lon"] = mairie
        company_mairie = _get_company_mairie_coords()
        if company_mairie:
            route = _compute_route(mairie, company_mairie)
            if route:
                result["distance_mairie_km"], result["duree_trajet_mairie_min"] = route
                any_success = True

    if not any_success:
        logger.warning("Aucune distance calculée pour %s %s", cp, ville)
    return result


def compute_distance_from_address(adresse: str) -> Optional[dict]:
    """
    Compatibilité avec scripts/affecter_distances.py.
    Attention : cette fonction géocode une adresse complète. Pour l'usage RH courant,
    préférer compute_distances_for_commune(cp, ville), plus RGPD-friendly.
    """
    if not adresse:
        return None

    cache_key = "addr:" + hashlib.sha1(adresse.strip().lower().encode("utf-8")).hexdigest()
    cached = _cache_get(cache_key)
    if cached:
        return cached

    params = urllib.parse.urlencode({"q": adresse, "limit": 1})
    data = _http_json(f"{_ADRESSE_API_URL}?{params}", timeout=_TIMEOUT_SHORT)
    features = (data or {}).get("features", [])
    if not features:
        return None

    lon, lat = features[0].get("geometry", {}).get("coordinates", [None, None])
    if lat is None or lon is None:
        return None
    origin = (float(lat), float(lon))
    if not _valid_coords(origin):
        return None

    destination = _get_company_mairie_coords() or _get_company_commune_coords()
    route = _compute_route(origin, destination) if destination else None
    result = {
        "latitude": origin[0],
        "longitude": origin[1],
        "distance_km": route[0] if route else None,
        "duree_min": route[1] if route else None,
    }
    _cache_set(cache_key, result)
    return result
