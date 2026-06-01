# -*- coding: utf-8 -*-
"""
Connexion en lecture seule à la base de données SQL Server externe.
Variables d'environnement (dans .env) :
    EMAC_EXT_SS_SERVER    - Nom ou IP du serveur (ex: SERVEUR\\INSTANCE ou 192.168.142.10)
    EMAC_EXT_SS_DATABASE  - Nom de la base de données
    EMAC_EXT_SS_USER      - Utilisateur SQL (laisser vide pour auth Windows)
    EMAC_EXT_SS_PASSWORD  - Mot de passe SQL (laisser vide pour auth Windows)
    EMAC_EXT_SS_DRIVER    - Driver ODBC (défaut: ODBC Driver 18 for SQL Server)
    EMAC_EXT_SS_TIMEOUT   - Timeout de connexion en secondes (défaut: 10)
    EMAC_EXT_SS_ENCRYPT   - Chiffrement TLS : yes/no/optional (défaut: yes)
"""

import os
import logging
from contextlib import contextmanager
from functools import lru_cache

try:
    import pyodbc
except ImportError:
    pyodbc = None

from infrastructure.db.configbd import _load_env_once

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def _get_sqlserver_config() -> dict:
    _load_env_once()
    return {
        "server":   os.getenv("EMAC_EXT_SS_SERVER", ""),
        "database": os.getenv("EMAC_EXT_SS_DATABASE", ""),
        "user":     os.getenv("EMAC_EXT_SS_USER", ""),
        "password": os.getenv("EMAC_EXT_SS_PASSWORD", ""),
        "driver":   os.getenv("EMAC_EXT_SS_DRIVER", "ODBC Driver 18 for SQL Server"),
        "timeout":  int(os.getenv("EMAC_EXT_SS_TIMEOUT", "10")),
        "encrypt":  os.getenv("EMAC_EXT_SS_ENCRYPT", "yes"),
    }


def _build_connection_string(cfg: dict) -> str:
    base = f"DRIVER={{{cfg['driver']}}};SERVER={cfg['server']};DATABASE={cfg['database']};Encrypt={cfg['encrypt']};"
    if cfg["user"]:
        return base + f"UID={cfg['user']};PWD={cfg['password']};"
    return base + "Trusted_Connection=yes;"


def get_sqlserver_connection():
    """
    Retourne une connexion pyodbc à SQL Server (lecture seule).
    Penser à appeler conn.close() après usage.
    """
    if pyodbc is None:
        raise RuntimeError(
            "Le module 'pyodbc' n'est pas installé.\n"
            "Exécuter : pip install pyodbc\n"
            "Et installer le driver ODBC : 'ODBC Driver 17 for SQL Server'."
        )

    cfg = _get_sqlserver_config()

    if not cfg["server"] or not cfg["database"]:
        raise RuntimeError(
            "Configuration SQL Server manquante.\n"
            "Ajouter dans .env :\n"
            "  EMAC_EXT_SS_SERVER=<serveur>\n"
            "  EMAC_EXT_SS_DATABASE=<base>"
        )

    conn_str = _build_connection_string(cfg)
    try:
        conn = pyodbc.connect(conn_str, timeout=cfg["timeout"])
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='cp1252')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16-le')
        return conn
    except pyodbc.Error as e:
        raise RuntimeError(f"Connexion SQL Server impossible : {e}") from e


class SqlServerCursor:
    """
    Gestionnaire de contexte pour une requête SQL Server en lecture seule.

    Usage :
        with SqlServerCursor() as cur:
            cur.execute("SELECT id, nom FROM ma_table WHERE statut = ?", ('ACTIF',))
            rows = cur.fetchall()
    """
    def __init__(self):
        self._conn = None
        self._cursor = None

    def __enter__(self):
        self._conn = get_sqlserver_connection()
        self._cursor = self._conn.cursor()
        return self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._cursor:
            try:
                self._cursor.close()
            except Exception:
                pass
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
        return False


def test_connection() -> tuple[bool, str]:
    """
    Vérifie que la connexion SQL Server fonctionne.
    Retourne (True, message_ok) ou (False, message_erreur).
    """
    try:
        with SqlServerCursor() as cur:
            cur.execute("SELECT @@VERSION")
            version = cur.fetchone()[0]
        short_version = version.split('\n')[0].strip()
        logger.info(f"Connexion SQL Server OK : {short_version}")
        return True, f"Connexion réussie\n{short_version}"
    except Exception as e:
        logger.error(f"Échec connexion SQL Server : {e}")
        return False, str(e)
