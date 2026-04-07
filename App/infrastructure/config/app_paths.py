# -*- coding: utf-8 -*-
"""
Module de gestion des chemins de fichiers pour EMAC.
Gère automatiquement les chemins en mode développement et en mode .exe (PyInstaller).

Utilisation:
    from infrastructure.config.app_paths import get_logs_dir, get_documents_dir, get_exports_dir

    logs_dir = get_logs_dir()  # Retourne Path vers logs/
    docs_dir = get_documents_dir()  # Retourne Path vers documents/
    exports_dir = get_exports_dir(create=True)  # Retourne Path vers exports/ (crée si demandé)
"""

import sys
import os
from pathlib import Path


def is_frozen():
    """
    Détecte si l'application tourne en mode .exe (PyInstaller) ou en mode développement.

    Returns:
        bool: True si en mode .exe, False si en mode développement
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_base_dir():
    """
    Retourne le répertoire de base de l'application.

    En mode développement : Retourne le dossier App/
    En mode .exe : Retourne le dossier où se trouve l'exécutable

    Returns:
        Path: Chemin absolu vers le répertoire de base
    """
    if is_frozen():
        # Mode .exe : dossier contenant l'exécutable
        return Path(sys.executable).parent
    else:
        # Mode développement : dossier App/
        return Path(__file__).parent.parent.parent


def get_data_dir():
    """
    Retourne le répertoire pour les données utilisateur persistantes.

    Windows : %APPDATA%\\EMAC
    Linux/Mac : ~/.emac

    Le dossier est créé automatiquement s'il n'existe pas.

    Returns:
        Path: Chemin absolu vers le répertoire de données
    """
    if os.name == 'nt':  # Windows
        appdata = os.getenv('APPDATA')
        if appdata:
            data_dir = Path(appdata) / 'EMAC'
        else:
            # Fallback si APPDATA n'est pas défini
            data_dir = Path.home() / 'AppData' / 'Roaming' / 'EMAC'
    else:  # Linux, Mac
        data_dir = Path.home() / '.emac'

    # Créer le dossier s'il n'existe pas
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_logs_dir():
    """
    Retourne le répertoire des logs de l'application.

    En mode développement : App/logs/
    En mode .exe : %APPDATA%\\EMAC\\logs\\

    Le dossier est créé automatiquement s'il n'existe pas.

    Returns:
        Path: Chemin absolu vers le répertoire des logs
    """
    if is_frozen():
        # Mode .exe : logs dans %APPDATA%
        logs_dir = get_data_dir() / 'logs'
    else:
        # Mode développement : logs dans App/logs/
        logs_dir = get_base_dir() / 'logs'

    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_documents_dir():
    """
    Retourne le répertoire des documents RH de l'application.

    En mode développement : App/documents/
    En mode .exe : %APPDATA%\\EMAC\\documents\\

    Le dossier est créé automatiquement s'il n'existe pas.

    Returns:
        Path: Chemin absolu vers le répertoire des documents
    """
    if is_frozen():
        # Mode .exe : documents dans %APPDATA%
        docs_dir = get_data_dir() / 'documents'
    else:
        # Mode développement : documents dans App/documents/
        docs_dir = get_base_dir() / 'documents'

    docs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir


def get_exports_dir(create: bool = False):
    """
    Retourne le répertoire des exports de l'application.

    En mode développement : App/exports/
    En mode .exe : %APPDATA%\\EMAC\\exports\\

    IMPORTANT: Le dossier n'est PAS créé automatiquement par défaut.
    Utiliser create=True uniquement lors d'un export explicite.

    Args:
        create (bool): Si True, crée le dossier s'il n'existe pas

    Returns:
        Path: Chemin absolu vers le répertoire des exports
    """
    if is_frozen():
        # Mode .exe : exports dans %APPDATA%
        exports_dir = get_data_dir() / 'exports'
    else:
        # Mode développement : exports dans App/exports/
        exports_dir = get_base_dir() / 'exports'

    # Créer seulement si demandé explicitement
    if create:
        exports_dir.mkdir(parents=True, exist_ok=True)

    return exports_dir


def get_temp_dir():
    """
    Retourne le répertoire temporaire de PyInstaller (en mode .exe uniquement).

    Ce répertoire contient les fichiers extraits du bundle .exe.
    Utilisé uniquement pour accéder aux ressources embarquées (SQL, etc.).

    Returns:
        Path: Chemin vers _MEIPASS en mode .exe, None en mode développement
    """
    if is_frozen():
        return Path(sys._MEIPASS)
    return None


# ============ Fonctions utilitaires ============

def get_log_file_path(filename="emac.log"):
    """
    Retourne le chemin complet vers un fichier de log.

    Args:
        filename (str): Nom du fichier de log

    Returns:
        Path: Chemin complet vers le fichier de log
    """
    return get_logs_dir() / filename


def get_document_path(personnel_id, category, filename):
    """
    Retourne le chemin complet vers un document RH.

    Args:
        personnel_id (int): ID du personnel
        category (str): Catégorie du document (contrats, evaluations, etc.)
        filename (str): Nom du fichier

    Returns:
        Path: Chemin complet vers le document
    """
    doc_dir = get_documents_dir() / str(personnel_id) / category
    doc_dir.mkdir(parents=True, exist_ok=True)
    return doc_dir / filename


# ============ Informations de debug ============

def get_paths_info():
    """
    Retourne un dictionnaire avec tous les chemins de l'application.
    Utile pour le debug.

    Returns:
        dict: Dictionnaire avec tous les chemins
    """
    return {
        'is_frozen': is_frozen(),
        'base_dir': str(get_base_dir()),
        'data_dir': str(get_data_dir()),
        'logs_dir': str(get_logs_dir()),
        'documents_dir': str(get_documents_dir()),
        'exports_dir': str(get_exports_dir()),
        'temp_dir': str(get_temp_dir()) if get_temp_dir() else 'N/A (dev mode)',
    }


if __name__ == '__main__':
    # Test du module
    print("=== EMAC Paths Info ===")
    for key, value in get_paths_info().items():
        print(f"{key:15} : {value}")
