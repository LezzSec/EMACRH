# -*- coding: utf-8 -*-
"""Infrastructure de stockage fichier/BLOB commune aux services documentaires."""

import mimetypes
import tempfile
import unicodedata
from pathlib import Path

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_MAX_UPLOAD_BYTES = 16 * 1024 * 1024


class UploadError(Exception):
    """Erreur métier lors d'un upload (fichier absent, trop volumineux…)."""


def sanitize_filename(name: str) -> str:
    """Nom de fichier sûr et déterministe (implémentation CANONIQUE unique).

    - Normalisation NFKD puis réduction ASCII (suppression des accents).
    - On conserve : alphanumériques, '.', '-', '_', ' '.
    - Tout autre caractère (y compris '/' et '\\') est remplacé par '_'.
    - Retourne 'fichier' si le résultat est '', '.' ou '..'.
    """
    normalized = unicodedata.normalize('NFKD', name)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    result = []
    for c in ascii_text:
        if c.isalnum() or c in ('.', '-', '_', ' '):
            result.append(c)
        else:
            result.append('_')
    safe = ''.join(result)
    if safe in ('', '.', '..'):
        return 'fichier'
    return safe


def get_temp_base() -> Path:
    """Répertoire temporaire racine EMAC, créé si besoin."""
    base = Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    return base


def extract_blob_to_temp(content: bytes, filename: str, subdir: str, key) -> Path:
    """Écrit un BLOB dans {temp_base}/{subdir}/{key}/{sanitize_filename(filename)}.

    Crée l'arborescence. Retourne le Path écrit.
    Le couple (subdir, key) reproduit à l'identique les emplacements temporaires
    de chaque service.
    """
    target_dir = get_temp_base() / subdir / str(key)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / sanitize_filename(filename)
    target_path.write_bytes(content)
    return target_path


def read_upload(source, max_size: int = DEFAULT_MAX_UPLOAD_BYTES) -> tuple:
    """Lit un fichier source à uploader.

    Retourne (contenu_bytes, type_mime, taille_octets).
    Lève UploadError si le fichier est absent ou dépasse max_size
    (message en français, déjà formaté pour l'utilisateur).
    Le type MIME tombe sur 'application/octet-stream' si indéterminé.
    """
    source_path = Path(source)
    if not source_path.exists():
        raise UploadError(f"Fichier introuvable : {source}")

    taille = source_path.stat().st_size
    if taille > max_size:
        taille_mo = taille / (1024 * 1024)
        max_mo = max_size / (1024 * 1024)
        raise UploadError(
            f"Fichier trop volumineux ({taille_mo:.1f} Mo). Maximum : {max_mo:.0f} Mo"
        )

    with open(source_path, 'rb') as f:
        contenu = f.read()

    type_mime, _ = mimetypes.guess_type(str(source_path))
    if type_mime is None:
        type_mime = 'application/octet-stream'

    return contenu, type_mime, taille
