# -*- coding: utf-8 -*-
"""Ouverture de fichiers et dossiers via l'OS avec controle de confinement."""

import os
import platform
import subprocess
import tempfile
from pathlib import Path

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


def _default_allowed_roots():
    """Racines EMAC autorisees par defaut.

    = temp systeme (couvre emac_documents/, EMAC_templates/, formation_poly/...)
      + get_documents_dir() + get_dossiers_dir() + get_exports_dir() + get_logs_dir()
    Les getters qui echouent sont ignores silencieusement (jamais d'exception ici).
    """
    roots = [Path(tempfile.gettempdir())]
    try:
        from infrastructure.config.app_paths import get_documents_dir, get_exports_dir, get_logs_dir
        for getter in (get_documents_dir, get_exports_dir, get_logs_dir):
            try:
                roots.append(getter())
            except Exception:
                pass
    except Exception:
        pass
    try:
        from infrastructure.config.app_paths import get_dossiers_dir
        try:
            roots.append(get_dossiers_dir(create=False))
        except Exception:
            pass
    except Exception:
        pass
    return roots


def _open_path(path_str):
    """Ouvre un chemin via l'OS (fichier ou dossier)."""
    if platform.system() == 'Windows':
        os.startfile(path_str)
    elif platform.system() == 'Darwin':
        subprocess.run(['open', path_str], check=True)
    else:
        subprocess.run(['xdg-open', path_str], check=True)


def _check_confined(resolved, roots):
    """Retourne True si resolved est sous l'une des racines resolues."""
    for root in roots:
        try:
            resolved.relative_to(Path(root).resolve())
            return True
        except Exception:
            pass
    return False


def open_file(path, allowed_roots=None):
    """Ouvre un fichier avec l'application par defaut, apres controle de confinement.

    - Resout le chemin (resolve()), verifie qu'il existe ET que c'est un fichier.
    - Verifie qu'il est contenu dans l'une des racines autorisees
      (allowed_roots, ou _default_allowed_roots() si None) via relative_to.
    - Sur refus de confinement : log warning + retourne (False, "Acces au fichier refuse").
    - Mecanisme : os.startfile sur Windows, 'open' sur macOS, 'xdg-open' sinon.
    Retourne (succes, message) -- message en francais, pret pour l'UI.
    """
    try:
        resolved = Path(path).resolve()

        if not resolved.exists():
            return False, "Fichier introuvable"

        if not resolved.is_file():
            return False, "Chemin invalide"

        roots = allowed_roots if allowed_roots is not None else _default_allowed_roots()

        if not _check_confined(resolved, roots):
            logger.warning(f"Tentative d'ouverture de fichier hors zone autorisee: {resolved}")
            return False, "Acces au fichier refuse"

        _open_path(str(resolved))
        return True, "Fichier ouvert"

    except Exception as e:
        logger.error(f"Erreur ouverture fichier: {e}")
        return False, "Impossible d'ouvrir le fichier"


def open_folder(path, allowed_roots=None):
    """Ouvre un dossier avec l'explorateur de fichiers, apres controle de confinement.

    Utilise pour reveler un dossier dans l'explorateur.
    Retourne (succes, message) -- message en francais, pret pour l'UI.
    """
    try:
        resolved = Path(path).resolve()

        if not resolved.exists():
            return False, "Dossier introuvable"

        if not resolved.is_dir():
            return False, "Chemin invalide"

        roots = allowed_roots if allowed_roots is not None else _default_allowed_roots()

        if not _check_confined(resolved, roots):
            logger.warning(f"Tentative d'ouverture de dossier hors zone autorisee: {resolved}")
            return False, "Acces au dossier refuse"

        _open_path(str(resolved))
        return True, "Dossier ouvert"

    except Exception as e:
        logger.error(f"Erreur ouverture dossier: {e}")
        return False, "Impossible d'ouvrir le dossier"
