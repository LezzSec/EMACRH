# Feature : Distance domicile-travail (mairie OSM + centroïde commune)

## Objectif

Calculer et stocker **deux distances** entre chaque membre du personnel et l'entreprise :

1. **Distance mairie** — mairie de la commune du personnel (OSM Overpass) → mairie de la commune de l'entreprise. Affichée à l'utilisateur sur la fiche individuelle.
2. **Distance commune** — centroïde commune du personnel (`geo.api.gouv.fr`) → centroïde commune de l'entreprise. Utilisée pour les statistiques agrégées et les exports.

**Point important RGPD :** on ne géocode **jamais** l'adresse exacte du personnel. Seule la commune (CP + ville) est utilisée pour le calcul. L'adresse précise reste en base mais n'alimente pas le calcul de distance.

## APIs utilisées

| API | Usage | Clé | Limite | Coût |
|-----|-------|-----|--------|------|
| `geo.api.gouv.fr` | Code INSEE + centroïde commune (CP+ville → commune) | Non | Illimité | Gratuit |
| `overpass-api.de` | Coordonnées mairie depuis nom commune | Non | 10k req/j avec throttling | Gratuit |
| OpenRouteService | Distance routière (2 calculs par saisie) | Oui (gratuite) | 2000 req/jour | Gratuit |
| OSRM public | Fallback routing si ORS indisponible | Non | Pas de SLA | Gratuit |

**Budget par saisie d'adresse :** 2 appels gratuits illimités (commune + mairie) + 2 appels ORS (route mairie + route commune). Soit 2 req ORS consommées.

**Budget Overpass :** 1 appel par saisie. 10k/jour max. Le serveur public applique un throttling progressif (10-20s entre appels intensifs) — pour notre usage (quelques modifications d'adresse par jour), c'est transparent.

## Architecture de la feature

### 1. Migration SQL

Créer `database/migrations/047_add_distance_domicile.sql` :

```sql
-- Migration 047 : Distance domicile/entreprise (mairie + commune)
-- Date : 2026-04-17
-- Description : Ajoute les coordonnées de la commune du personnel,
--               la mairie (OSM townhall), et les deux distances
--               domicile-entreprise associées.

-- ── Commune (centroïde geo.api.gouv.fr, pour les stats) ──────
ALTER TABLE personnel_infos
    ADD COLUMN IF NOT EXISTS code_insee_commune VARCHAR(5) DEFAULT NULL
        COMMENT 'Code INSEE de la commune de domicile',
    ADD COLUMN IF NOT EXISTS commune_lat DECIMAL(10,7) DEFAULT NULL
        COMMENT 'Latitude du centroïde commune domicile',
    ADD COLUMN IF NOT EXISTS commune_lon DECIMAL(10,7) DEFAULT NULL
        COMMENT 'Longitude du centroïde commune domicile',
    ADD COLUMN IF NOT EXISTS distance_commune_km DECIMAL(6,2) DEFAULT NULL
        COMMENT 'Distance routière centroïde-à-centroïde en km (stats)',
    ADD COLUMN IF NOT EXISTS duree_trajet_commune_min INT DEFAULT NULL
        COMMENT 'Durée de trajet entre centroïdes en minutes';

-- ── Mairie (OSM Overpass, pour affichage utilisateur) ────────
ALTER TABLE personnel_infos
    ADD COLUMN IF NOT EXISTS mairie_lat DECIMAL(10,7) DEFAULT NULL
        COMMENT 'Latitude de la mairie de la commune (OSM townhall)',
    ADD COLUMN IF NOT EXISTS mairie_lon DECIMAL(10,7) DEFAULT NULL
        COMMENT 'Longitude de la mairie (OSM townhall)',
    ADD COLUMN IF NOT EXISTS distance_mairie_km DECIMAL(6,2) DEFAULT NULL
        COMMENT 'Distance routière mairie-à-mairie en km (affichage fiche)',
    ADD COLUMN IF NOT EXISTS duree_trajet_mairie_min INT DEFAULT NULL
        COMMENT 'Durée de trajet entre mairies en minutes';

-- ── Horodatage ──────────────────────────────────────────────
ALTER TABLE personnel_infos
    ADD COLUMN IF NOT EXISTS distance_calculee_at TIMESTAMP NULL DEFAULT NULL
        COMMENT 'Date du dernier calcul de distances';

-- ── Index ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_personnel_distance_commune
    ON personnel_infos(distance_commune_km);
CREATE INDEX IF NOT EXISTS idx_personnel_distance_mairie
    ON personnel_infos(distance_mairie_km);
CREATE INDEX IF NOT EXISTS idx_personnel_code_insee
    ON personnel_infos(code_insee_commune);
```

### 2. Configuration de l'entreprise

Ajouter dans `config/.env.example` :

```bash
# ═══════════════════════════════════════════════════════════════
# Calcul des distances domicile-travail
# ═══════════════════════════════════════════════════════════════

# Code INSEE de la commune de l'entreprise
# Trouvable sur https://geo.api.gouv.fr/communes?nom=NomCommune
EMAC_COMPANY_INSEE=64024
EMAC_COMPANY_COMMUNE=Anglet

# Coordonnées de la mairie de l'entreprise (cache pour éviter appel Overpass)
# Valeurs utilisées telles quelles si définies, sinon résolues au démarrage.
# Trouvables via: https://overpass-turbo.eu/ → [amenity=townhall][name="Anglet"]
# EMAC_COMPANY_MAIRIE_LAT=43.4838
# EMAC_COMPANY_MAIRIE_LON=-1.5250

# Clé OpenRouteService (optionnel, fallback OSRM si absent)
# Inscription gratuite : https://openrouteservice.org/dev/#/signup
# EMAC_ORS_API_KEY=
```

### 3. Nouveau service : `domain/services/geo/distance_service.py`

```python
# -*- coding: utf-8 -*-
"""
Service de calcul de distance routière domicile-entreprise.

Calcule deux distances :
  1. Mairie : mairie commune personnel (OSM) → mairie commune entreprise (OSM)
     → Affichée à l'utilisateur sur la fiche individuelle
  2. Commune : centroïde commune personnel (geo.api.gouv.fr) →
     centroïde commune entreprise
     → Utilisée pour statistiques agrégées et exports

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

# Adresses dont le calcul a complètement échoué (pas de commune trouvée)
_failed_communes: set[str] = set()

# Cache mémoire mairie par code INSEE (évite appels Overpass redondants)
_mairie_cache: dict[str, tuple[float, float]] = {}


def _commune_key(cp: str, ville: str) -> str:
    """Clé normalisée pour identifier une commune."""
    return f"{(cp or '').strip()}|{(ville or '').strip().lower()}"


def is_commune_known_failed(cp: str, ville: str) -> bool:
    """Retourne True si cette commune a déjà échoué (pas trouvée)."""
    return _commune_key(cp, ville) in _failed_communes


def mark_commune_failed(cp: str, ville: str) -> None:
    """Marque une commune comme non résolue."""
    _failed_communes.add(_commune_key(cp, ville))


def clear_failed_cache() -> None:
    """Vide les caches (retry manuel ou tests)."""
    _failed_communes.clear()
    _mairie_cache.clear()


# ═══════════════════════════════════════════════════════════════
# Configuration entreprise
# ═══════════════════════════════════════════════════════════════

_company_commune_cache: Optional[tuple[float, float]] = None
_company_mairie_cache: Optional[tuple[float, float]] = None


def _get_company_commune_coords() -> Optional[tuple[float, float]]:
    """
    Retourne (lat, lon) du centroïde de la commune de l'entreprise.
    Résolu au premier appel depuis EMAC_COMPANY_INSEE, puis caché.
    """
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
    Retourne (lat, lon) de la mairie de l'entreprise.

    Priorité :
      1. Variables EMAC_COMPANY_MAIRIE_LAT/LON (cache en dur, recommandé)
      2. Résolution via Overpass depuis EMAC_COMPANY_COMMUNE
      3. Fallback sur le centroïde commune
    """
    global _company_mairie_cache
    if _company_mairie_cache is not None:
        return _company_mairie_cache

    # Priorité 1 : variables d'env
    lat = os.getenv("EMAC_COMPANY_MAIRIE_LAT")
    lon = os.getenv("EMAC_COMPANY_MAIRIE_LON")
    if lat and lon:
        try:
            _company_mairie_cache = (float(lat), float(lon))
            return _company_mairie_cache
        except ValueError:
            logger.error(f"EMAC_COMPANY_MAIRIE_LAT/LON invalides : {lat}, {lon}")

    # Priorité 2 : résoudre via Overpass
    commune = os.getenv("EMAC_COMPANY_COMMUNE")
    if commune:
        coords = get_mairie_coords(commune)
        if coords:
            _company_mairie_cache = coords
            logger.info(
                f"Mairie entreprise résolue via Overpass : {coords} "
                f"(pense à mettre EMAC_COMPANY_MAIRIE_LAT/LON dans .env pour cache)"
            )
            return coords

    # Priorité 3 : fallback centroïde
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
        {
            'code_insee': '64024',
            'nom': 'Anglet',
            'lat': 43.4779,
            'lon': -1.5177,
        }
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

    # Match exact sur le nom
    ville_lower = ville.strip().lower()
    best = None
    for commune in data:
        if commune.get('nom', '').strip().lower() == ville_lower:
            best = commune
            break

    # Fallback : première commune du CP
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

    Cherche les éléments taggés [amenity=townhall] correspondant au nom
    de la commune, en France uniquement.

    Args:
        commune_nom: Nom exact de la commune (ex: 'Anglet')
        code_insee: Code INSEE pour désambiguïsation (optionnel)

    Returns:
        (lat, lon) ou None si aucune mairie trouvée / OSM indisponible.
    """
    if not commune_nom:
        return None

    # Cache mémoire (évite re-requêter Overpass pour la même commune)
    cache_key = code_insee or commune_nom.strip().lower()
    if cache_key in _mairie_cache:
        return _mairie_cache[cache_key]

    # Requête Overpass : townhall en France avec le nom de la commune
    # On cherche sur node, way et relation pour couvrir tous les cas de tagging.
    # Le filtre "ref:INSEE" si fourni désambiguïse les communes homonymes.
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

    # Prendre le premier résultat : pour un node c'est lat/lon direct,
    # pour un way/relation c'est dans 'center'
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
            # Commune (stats)
            'code_insee_commune': '75102',
            'commune_lat': 48.8692,
            'commune_lon': 2.3413,
            'distance_commune_km': 11.80,
            'duree_trajet_commune_min': 16,
            # Mairie (affichage utilisateur)
            'mairie_lat': 48.8634,
            'mairie_lon': 2.3388,
            'distance_mairie_km': 12.10,
            'duree_trajet_mairie_min': 17,
            # Horodatage
            'distance_calculee_at': datetime,
        }
        ou None si aucune distance n'a pu être calculée.
    """
    if not cp or not ville:
        return None

    # Garde-fou : commune déjà en échec cette session
    if is_commune_known_failed(cp, ville):
        logger.debug(f"Commune en échec connu, skip : {cp} {ville}")
        return None

    # ── 1. Résoudre la commune du personnel ──────────────────
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

    # ── 2. Distance commune (centroïde → centroïde) ─────────
    company_commune = _get_company_commune_coords()
    if company_commune:
        commune_coords = (commune['lat'], commune['lon'])
        route = _compute_route(commune_coords, company_commune)
        if route:
            result['distance_commune_km'], result['duree_trajet_commune_min'] = route
            any_success = True

    # ── 3. Distance mairie (OSM townhall → OSM townhall) ────
    mairie = get_mairie_coords(commune['nom'], commune['code_insee'])
    if mairie:
        result['mairie_lat'], result['mairie_lon'] = mairie
        company_mairie = _get_company_mairie_coords()
        if company_mairie:
            route = _compute_route(mairie, company_mairie)
            if route:
                result['distance_mairie_km'], result['duree_trajet_mairie_min'] = route
                any_success = True

    # Rien n'a marché : on sauvegarde quand même le code INSEE si on l'a,
    # mais on marque comme échoué pour éviter de retenter en boucle
    if not any_success:
        logger.warning(f"Aucune distance calculée pour {cp} {ville}")
        # On ne marque PAS en échec car la commune EXISTE,
        # c'est juste le routing qui a échoué (peut marcher plus tard)

    return result
```

### 4. Intégration dans le repository

Ajouter à `domain/repositories/personnel_repo.py` :

```python
@staticmethod
def get_adresse_and_distances(personnel_id: int) -> dict | None:
    """
    Retourne les champs d'adresse + données de distance.
    Utilisé pour détecter si la commune a changé avant recalcul.
    """
    from infrastructure.db.query_executor import QueryExecutor
    return QueryExecutor.fetch_one(
        """SELECT cp_adresse, ville_adresse,
                  code_insee_commune, distance_commune_km, distance_mairie_km
           FROM personnel_infos WHERE operateur_id = %s""",
        (personnel_id,),
        dictionary=True
    )


@staticmethod
def update_distances(
    personnel_id: int,
    code_insee_commune: str | None,
    commune_lat: float | None,
    commune_lon: float | None,
    distance_commune_km: float | None,
    duree_trajet_commune_min: int | None,
    mairie_lat: float | None,
    mairie_lon: float | None,
    distance_mairie_km: float | None,
    duree_trajet_mairie_min: int | None,
) -> None:
    """Met à jour toutes les données de distance."""
    from infrastructure.db.query_executor import QueryExecutor
    QueryExecutor.execute_write(
        """UPDATE personnel_infos
           SET code_insee_commune = %s,
               commune_lat = %s, commune_lon = %s,
               distance_commune_km = %s, duree_trajet_commune_min = %s,
               mairie_lat = %s, mairie_lon = %s,
               distance_mairie_km = %s, duree_trajet_mairie_min = %s,
               distance_calculee_at = NOW()
           WHERE operateur_id = %s""",
        (code_insee_commune, commune_lat, commune_lon,
         distance_commune_km, duree_trajet_commune_min,
         mairie_lat, mairie_lon,
         distance_mairie_km, duree_trajet_mairie_min,
         personnel_id),
        return_lastrowid=False
    )
```

### 5. Intégration dans l'UI — avec garde-fous

**Localiser** le dialog de saisie d'adresse personnelle dans :
- `gui/screens/rh/domaines/dialogs_general.py`
- Ou `gui/screens/personnel/manage_operateur.py`

```python
class PersonnelInfosDialog(QDialog):
    def __init__(self, ...):
        super().__init__(...)
        self._distance_computing = False

    def _on_save_clicked(self):
        # ... sauvegarde existante ...
        self._compute_distances_if_needed()

    def _compute_distances_if_needed(self):
        """
        Calcule les distances UNIQUEMENT si la commune a changé
        et qu'aucun calcul n'est déjà en cours.
        """
        from gui.workers.db_worker import DbWorker, DbThreadPool
        from domain.services.geo.distance_service import (
            compute_distances_for_commune,
            is_commune_known_failed,
        )
        from domain.repositories.personnel_repo import PersonnelRepository

        # ── GARDE-FOU 1 : calcul déjà en cours ? ────────────
        if self._distance_computing:
            return

        cp = self.inp_cp.text().strip()
        ville = self.inp_ville.text().strip()

        if not (cp and ville):
            return

        personnel_id = self.operateur_id

        # ── GARDE-FOU 2 : commune déjà en échec cette session ? ─
        if is_commune_known_failed(cp, ville):
            logger.debug(f"Commune en échec connu, pas de retry")
            return

        # ── GARDE-FOU 3 : la commune a-t-elle changé ? ─────
        # Note : on compare sur CP+ville (pas sur adresse1), car seule
        # la commune impacte nos calculs de distance.
        existing = PersonnelRepository.get_adresse_and_distances(personnel_id)
        if existing:
            old = (
                (existing.get('cp_adresse') or '').strip(),
                (existing.get('ville_adresse') or '').strip().lower(),
            )
            new = (cp, ville.lower())
            already_calculated = existing.get('distance_commune_km') is not None

            if old == new and already_calculated:
                logger.debug(f"Commune inchangée pour #{personnel_id}, skip")
                return

        # ── Lancer le calcul async ──────────────────────────
        self._distance_computing = True

        def compute(progress_callback=None):
            result = compute_distances_for_commune(cp, ville)
            if result is None:
                return None
            PersonnelRepository.update_distances(
                personnel_id=personnel_id,
                code_insee_commune=result['code_insee_commune'],
                commune_lat=result['commune_lat'],
                commune_lon=result['commune_lon'],
                distance_commune_km=result['distance_commune_km'],
                duree_trajet_commune_min=result['duree_trajet_commune_min'],
                mairie_lat=result['mairie_lat'],
                mairie_lon=result['mairie_lon'],
                distance_mairie_km=result['distance_mairie_km'],
                duree_trajet_mairie_min=result['duree_trajet_mairie_min'],
            )
            return result

        def on_success(result):
            self._distance_computing = False
            if result:
                d_mairie = result.get('distance_mairie_km')
                d_commune = result.get('distance_commune_km')
                logger.info(
                    f"Distances pour #{personnel_id}: "
                    f"mairie={d_mairie} km, commune={d_commune} km"
                )

        def on_error(err):
            self._distance_computing = False
            logger.warning(f"Calcul distances échoué #{personnel_id}: {err}")

        worker = DbWorker(compute)
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)
```

### 6. Affichage dans la fiche personnel

Dans `DetailOperateurDialog` (ou son ViewModel), afficher **uniquement la distance mairie** à l'utilisateur :

```python
# Dans la construction de la carte "Informations Personnelles"
if data.get('distance_mairie_km') is not None:
    d = data['distance_mairie_km']
    t = data.get('duree_trajet_mairie_min')
    if t:
        personal_items.append(("Trajet domicile-travail", f"{d} km (~{t} min)"))
    else:
        personal_items.append(("Trajet domicile-travail", f"{d} km"))
```

La distance commune reste en base mais n'est **pas affichée** dans la fiche. Elle sera utilisée dans les écrans de statistiques / exports RH.

Vérifier que `PersonnelRepository.get_personnel_infos()` retourne bien les nouveaux champs. Si la requête liste les colonnes explicitement, ajouter au moins `distance_mairie_km` et `duree_trajet_mairie_min` au SELECT.

### 7. Tests

Créer `tests/unit/test_distance_service.py` :

```python
# -*- coding: utf-8 -*-
"""Tests du service de distance."""
from unittest.mock import patch, MagicMock
from domain.services.geo import distance_service


def test_commune_key_normalizes():
    """La clé de commune doit être normalisée (casse, espaces)."""
    k1 = distance_service._commune_key("75002", "Paris")
    k2 = distance_service._commune_key("  75002  ", "  PARIS  ")
    assert k1 == k2


def test_failed_cache():
    distance_service.clear_failed_cache()
    assert not distance_service.is_commune_known_failed("75002", "Paris")
    distance_service.mark_commune_failed("75002", "Paris")
    assert distance_service.is_commune_known_failed("75002", "Paris")


@patch('domain.services.geo.distance_service.urllib.request.urlopen')
def test_resolve_commune_exact_match(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.return_value = b'''[
        {"nom": "Anglet", "code": "64024",
         "centre": {"coordinates": [-1.5177, 43.4779]}},
        {"nom": "Biarritz", "code": "64122",
         "centre": {"coordinates": [-1.5592, 43.4832]}}
    ]'''
    mock_urlopen.return_value.__enter__.return_value = mock_response

    result = distance_service.resolve_commune("64600", "Anglet")
    assert result['code_insee'] == '64024'
    assert result['lat'] == 43.4779


@patch('domain.services.geo.distance_service.urllib.request.urlopen')
def test_resolve_commune_fallback_first(mock_urlopen):
    """Si pas de match exact sur le nom, prendre la première."""
    mock_response = MagicMock()
    mock_response.read.return_value = b'''[
        {"nom": "Anglet", "code": "64024",
         "centre": {"coordinates": [-1.5177, 43.4779]}}
    ]'''
    mock_urlopen.return_value.__enter__.return_value = mock_response

    result = distance_service.resolve_commune("64600", "NomBidon")
    assert result['code_insee'] == '64024'


@patch('domain.services.geo.distance_service.urllib.request.urlopen')
def test_get_mairie_coords_node(mock_urlopen):
    """Overpass renvoie un node avec lat/lon directs."""
    distance_service.clear_failed_cache()
    mock_response = MagicMock()
    mock_response.read.return_value = b'''{
        "elements": [
            {"type": "node", "lat": 43.4838, "lon": -1.5250,
             "tags": {"amenity": "townhall", "name": "Anglet"}}
        ]
    }'''
    mock_urlopen.return_value.__enter__.return_value = mock_response

    result = distance_service.get_mairie_coords("Anglet", "64024")
    assert result == (43.4838, -1.5250)


@patch('domain.services.geo.distance_service.urllib.request.urlopen')
def test_get_mairie_coords_way_with_center(mock_urlopen):
    """Overpass renvoie un way avec coords dans 'center'."""
    distance_service.clear_failed_cache()
    mock_response = MagicMock()
    mock_response.read.return_value = b'''{
        "elements": [
            {"type": "way", "center": {"lat": 43.4838, "lon": -1.5250}}
        ]
    }'''
    mock_urlopen.return_value.__enter__.return_value = mock_response

    result = distance_service.get_mairie_coords("Anglet", "64024")
    assert result == (43.4838, -1.5250)


@patch('domain.services.geo.distance_service.urllib.request.urlopen')
def test_get_mairie_coords_empty(mock_urlopen):
    distance_service.clear_failed_cache()
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"elements": []}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    result = distance_service.get_mairie_coords("CommuneBidon")
    assert result is None


@patch('domain.services.geo.distance_service.urllib.request.urlopen')
def test_mairie_cache_prevents_duplicate_calls(mock_urlopen):
    """Appeler 2× la même commune ne doit faire qu'UNE requête Overpass."""
    distance_service.clear_failed_cache()
    mock_response = MagicMock()
    mock_response.read.return_value = b'''{
        "elements": [
            {"type": "node", "lat": 43.4838, "lon": -1.5250}
        ]
    }'''
    mock_urlopen.return_value.__enter__.return_value = mock_response

    distance_service.get_mairie_coords("Anglet", "64024")
    distance_service.get_mairie_coords("Anglet", "64024")

    # Un seul appel réseau grâce au cache
    assert mock_urlopen.call_count == 1


@patch('domain.services.geo.distance_service.urllib.request.urlopen')
def test_compute_skips_known_failed_commune(mock_urlopen):
    """Commune marquée échouée → AUCUN appel API."""
    distance_service.clear_failed_cache()
    distance_service.mark_commune_failed("99999", "Nulleville")

    result = distance_service.compute_distances_for_commune("99999", "Nulleville")
    assert result is None
    mock_urlopen.assert_not_called()
```

## Ordre d'exécution

1. Créer migration `047_add_distance_domicile.sql` et l'appliquer
2. Configurer `.env` (INSEE entreprise + coords mairie si connues, sinon laisser Overpass résoudre au premier démarrage et copier le résultat des logs)
3. Créer `domain/services/geo/distance_service.py`
4. Ajouter les 2 méthodes au `personnel_repo.py`
5. Intégrer l'appel async dans le dialog de saisie d'adresse
6. Afficher `distance_mairie_km` dans la fiche détail (la distance commune reste en base pour les stats)
7. Créer les tests unitaires
8. Test manuel : modifier l'adresse d'un personnel, vérifier que la distance mairie apparaît ~10-30s après

## Budget API par opération

| Action | geo.api.gouv.fr | Overpass | ORS |
|--------|----------------|----------|-----|
| Nouvelle commune | 1 (résolution) | 1 (mairie) | 2 (route mairie + route commune) |
| Commune en cache mémoire (2ème pers même commune même session) | 1 | 0 | 2 |
| Commune inchangée (resauvegarde adresse) | 0 | 0 | 0 |
| Commune en échec connu | 0 | 0 | 0 |

## Note RGPD

Cette implémentation **ne géocode jamais l'adresse précise du personnel**. Seule la commune (déduite du couple CP + ville) est utilisée pour les calculs. Les coordonnées GPS stockées sont celles :
- Du centroïde de la commune (donnée publique `geo.api.gouv.fr`)
- De la mairie de la commune (donnée publique OSM)

Les champs `adresse1`, `adresse2` de `personnel_infos` restent en base (nécessaires pour les courriers), mais ne sont pas utilisés dans le calcul de distance. C'est un argument valable pour la documentation RGPD du projet.
