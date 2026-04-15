# -*- coding: utf-8 -*-
"""
Service de géocodage d'adresses françaises.
Utilise l'API officielle adresse.data.gouv.fr (gratuite, sans clé).
"""

import json
import urllib.request
import urllib.parse
from typing import Optional
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

_BASE_URL = "https://api-adresse.data.gouv.fr/search/"
_TIMEOUT = 3  # secondes


def search_addresses(query: str, limit: int = 8) -> list[dict]:
    """
    Recherche des adresses françaises correspondant à la saisie.

    Retourne une liste de dicts:
        {
            'label':  "12 Rue de la Paix 75002 Paris",
            'cp':     "75002",
            'ville':  "Paris",
            'adresse': "12 Rue de la Paix",
        }
    """
    if not query or len(query) < 3:
        return []

    params = urllib.parse.urlencode({
        'q': query,
        'limit': limit,
        'type': 'housenumber',
        'autocomplete': 1,
    })
    url = f"{_BASE_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur API adresse (search): {e}")
        return []

    results = []
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        results.append({
            'label':   props.get('label', ''),
            'cp':      props.get('postcode', ''),
            'ville':   props.get('city', ''),
            'adresse': props.get('name', ''),
        })
    return results


def search_cities(query: str, limit: int = 10) -> list[str]:
    """
    Recherche des communes françaises par nom (pour le champ ville de naissance).
    Retourne une liste de noms de communes.
    """
    if not query or len(query) < 2:
        return []

    params = urllib.parse.urlencode({
        'q': query,
        'limit': limit,
        'type': 'municipality',
        'autocomplete': 1,
    })
    url = f"{_BASE_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur API adresse (search_cities): {e}")
        return []

    cities = []
    for feature in data.get('features', []):
        city = feature.get('properties', {}).get('city', '')
        if city and city not in cities:
            cities.append(city)
    return cities


def get_cities_by_postal_code(cp: str) -> list[str]:
    """
    Retourne la liste des communes correspondant à un code postal à 5 chiffres.
    Utilise geo.api.gouv.fr qui liste exhaustivement toutes les communes d'un CP.
    """
    if not cp or len(cp) != 5 or not cp.isdigit():
        return []

    params = urllib.parse.urlencode({'codePostal': cp, 'fields': 'nom', 'format': 'json'})
    url = f"https://geo.api.gouv.fr/communes?{params}"

    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"Erreur API geo communes (CP={cp}): {e}")
        return []

    return sorted(c['nom'] for c in data if c.get('nom'))
