# App/core/db/configbd.py
import os
import sys
from pathlib import Path

import mysql.connector
from mysql.connector import pooling

from dotenv import load_dotenv

_connection_pool = None
_env_loaded = False


def _load_env_once() -> None:
    """Charge un .env si présent (en dev ou en exe PyInstaller)."""
    global _env_loaded
    if _env_loaded:
        return

    # Base dir = dossier de l'exe (PyInstaller) ou racine App/ (dev)
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).parent
    else:
        # .../App/core/db/configbd.py -> parents[2] = App/
        base_dir = Path(__file__).resolve().parents[2]

    # Dossier AppData (tu l'utilises déjà ailleurs dans l'app)
    appdata_dir = None
    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            appdata_dir = Path(appdata) / "EMAC"

    candidates = [
        base_dir / ".env",
        base_dir / "config" / ".env",
        (appdata_dir / ".env") if appdata_dir else None,
    ]

    for p in candidates:
        if p and p.exists():
            load_dotenv(dotenv_path=str(p), override=False)
            break

    _env_loaded = True


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _get_db_config() -> dict:
    """
    Centralise la config DB.
    Supporte tes variables EMAC_* (celles vues dans ton code).
    """
    _load_env_once()

    host = os.getenv("EMAC_DB_HOST", os.getenv("DB_HOST", "127.0.0.1"))
    port = _env_int("EMAC_DB_PORT", _env_int("DB_PORT", 3306))
    user = os.getenv("EMAC_DB_USER", os.getenv("DB_USER", "root"))
    password = os.getenv("EMAC_DB_PASSWORD", os.getenv("DB_PASS", ""))
    database = os.getenv("EMAC_DB_NAME", os.getenv("DB_NAME", "emac_db"))

    # Paramètres pool (optionnels)
    pool_name = os.getenv("EMAC_DB_POOL_NAME", "emac_pool")
    pool_size = _env_int("EMAC_DB_POOL_SIZE", 10)

    # Charset/collation (si tu veux les forcer)
    charset = os.getenv("EMAC_DB_CHARSET", os.getenv("DB_CHARSET", "utf8mb4"))
    collation = os.getenv(
        "EMAC_DB_COLLATION", os.getenv("DB_COLLATION", "utf8mb4_general_ci")
    )

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "pool_name": pool_name,
        "pool_size": pool_size,
        "charset": charset,
        "collation": collation,
    }


def _get_pool() -> pooling.MySQLConnectionPool:
    global _connection_pool
    if _connection_pool is not None:
        return _connection_pool

    cfg = _get_db_config()

    # Erreur claire si mot de passe absent (évite un crash “mystère” en exe)
    if not cfg["password"]:
        raise RuntimeError(
            "Configuration DB manquante : EMAC_DB_PASSWORD est vide.\n"
            "Ajoute un fichier .env à côté de EMAC.exe (ou dans %APPDATA%\\EMAC) "
            "ou définis la variable d'environnement EMAC_DB_PASSWORD."
        )

    _connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name=cfg["pool_name"],
        pool_size=cfg["pool_size"],
        pool_reset_session=True,
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset=cfg["charset"],
        use_unicode=True,
        autocommit=False,
        # mysql-connector-python ne prend pas toujours collation ici selon versions,
        # mais on la garde en option (et tu peux aussi la SET après connexion si besoin).
        # collation=cfg["collation"],
    )
    return _connection_pool


def get_connection():
    """
    Retourne une connexion depuis le pool.
    IMPORTANT : pense à conn.close() après usage (ça la rend au pool).
    """
    pool = _get_pool()
    conn = pool.get_connection()
    return conn
