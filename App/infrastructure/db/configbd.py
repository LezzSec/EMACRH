# App/core/db/configbd.py
# -*- coding: utf-8 -*-
"""
Module de configuration et gestion du pool de connexions MySQL.
Centralise toute la logique de connexion à la base de données.
"""

import os
import sys
import time
import logging
import threading
from contextlib import contextmanager
from pathlib import Path

import mysql.connector
from mysql.connector import pooling, Error as MySQLError

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_connection_pool = None
_env_loaded = False
_last_activity: float = 0.0
# Ping only when the app has been idle longer than this (covers PC-sleep reconnect).
_PING_IDLE_S: int = 300
_timeout_context = threading.local()


def _get_statement_timeout_ms() -> int:
    """Retourne le timeout SQL courant du thread, en millisecondes."""
    return int(getattr(_timeout_context, "statement_timeout_ms", 0) or 0)


@contextmanager
def db_statement_timeout(seconds: float | None):
    """
    Définit un timeout SQL pour les connexions ouvertes dans le thread courant.

    MySQL applique MAX_EXECUTION_TIME aux SELECT. Les écritures et le code Python
    restent couverts par la cancellation logique du worker.
    """
    previous = _get_statement_timeout_ms()
    timeout_ms = int(seconds * 1000) if seconds and seconds > 0 else 0
    _timeout_context.statement_timeout_ms = timeout_ms
    try:
        yield
    finally:
        _timeout_context.statement_timeout_ms = previous


def _set_session_statement_timeout(conn, timeout_ms: int) -> bool:
    """
    Applique MAX_EXECUTION_TIME sur la session MySQL courante.
    Retourne True si une valeur a été appliquée et doit être remise à zéro.
    """
    if timeout_ms <= 0:
        return False

    cur = None
    try:
        cur = conn.cursor()
        cur.execute("SET SESSION MAX_EXECUTION_TIME = %s", (timeout_ms,))
        return True
    except Exception as e:
        logger.debug(f"Timeout SQL non appliqué (MAX_EXECUTION_TIME={timeout_ms}ms): {e}")
        return False
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass


def _clear_session_statement_timeout(conn) -> None:
    """Remet le timeout SQL de la session MySQL à zéro."""
    cur = None
    try:
        cur = conn.cursor()
        cur.execute("SET SESSION MAX_EXECUTION_TIME = 0")
    except Exception as e:
        logger.debug(f"Reset timeout SQL ignoré: {e}")
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass


def _load_env_once() -> None:
    """Charge un .env si présent (en dev ou en exe PyInstaller).
    Supporte également .env.encrypted pour une distribution sécurisée."""
    global _env_loaded
    if _env_loaded:
        return

    # Base dir = dossier de l'exe (PyInstaller) ou racine App/ (dev)
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).parent
        # PyInstaller met les fichiers data dans _internal/
        internal_dir = base_dir / "_internal"
    else:
        # .../App/core/db/configbd.py -> parents[2] = App/
        base_dir = Path(__file__).resolve().parents[2]
        internal_dir = base_dir

    # Dossier AppData (tu l'utilises déjà ailleurs dans l'app)
    appdata_dir = None
    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            appdata_dir = Path(appdata) / "EMAC"

    # Candidats: .env en clair (priorité dev) puis .env.encrypted (production)
    # Le .env local prend toujours le dessus sur le .env.encrypted
    candidates = [
        # Mode dev: fichier .env en clair (prioritaire)
        (internal_dir / ".env", False),
        (base_dir / ".env", False),
        (base_dir / "config" / ".env", False),
        ((appdata_dir / ".env") if appdata_dir else None, False),
        # Mode production: fichier chiffré (fallback si pas de .env)
        (internal_dir / ".env.encrypted", True),
        (base_dir / ".env.encrypted", True),
        (base_dir / "config" / ".env.encrypted", True),
        ((appdata_dir / ".env.encrypted") if appdata_dir else None, True),
    ]

    for p, is_encrypted in candidates:
        if p and p.exists():
            if is_encrypted:
                # Charger le fichier chiffré
                try:
                    from infrastructure.security.config_crypter import decrypt_env_file
                    import tempfile
                    # Déchiffrer dans un fichier temporaire
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as tmp:
                        content = decrypt_env_file(str(p))
                        tmp.write(content)
                        tmp_path = tmp.name
                    # Charger le .env déchiffré
                    load_dotenv(dotenv_path=tmp_path, override=False)
                    # Supprimer le fichier temporaire immédiatement
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                except Exception as e:
                    # Si le déchiffrement échoue, continuer avec les autres candidats
                    logger.warning(f"Impossible de déchiffrer {p}: {e}")
                    continue
            else:
                # Charger le .env normal
                load_dotenv(dotenv_path=str(p), override=False)
            break

    _env_loaded = True


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def get_db_pool_size() -> int:
    """Retourne la taille du pool MySQL configurée (pour aligner le pool de threads)."""
    config = _get_db_config()
    return config.get('pool_size', 5)


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
    pool_size = _env_int("EMAC_DB_POOL_SIZE", 10)  # Défaut raisonnable — monter à 15-20 si > 5 workers GUI

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
        # Timeouts pour éviter les blocages réseau
        connection_timeout=5,  # Max 5 secondes pour établir la connexion
        # mysql-connector-python ne prend pas toujours collation ici selon versions,
        # mais on la garde en option (et tu peux aussi la SET après connexion si besoin).
        # collation=cfg["collation"],
    )
    return _connection_pool


def _ensure_connection_alive(conn) -> bool:
    """
    Vérifie qu'une connexion est vivante et tente de la reconnecter si nécessaire.
    Utile après une mise en veille du PC ou une perte réseau temporaire.

    Returns:
        bool: True si la connexion est opérationnelle, False sinon
    """
    try:
        conn.ping(reconnect=True, attempts=2, delay=1)
        return True
    except Exception:
        return False


def get_connection():
    """
    Retourne une connexion depuis le pool avec vérification de la santé.
    IMPORTANT : pense à conn.close() après usage (ça la rend au pool).

    Le ping n'est effectué que si l'application est inactive depuis plus de
    _PING_IDLE_S secondes (veille PC, etc.). Pendant une session active,
    aucun round-trip supplémentaire n'est nécessaire.

    Returns:
        Connection: Une connexion MySQL opérationnelle

    Raises:
        RuntimeError: Si impossible d'obtenir une connexion saine
    """
    global _last_activity
    pool = _get_pool()
    now = time.monotonic()
    try:
        conn = pool.get_connection()
        if (now - _last_activity) > _PING_IDLE_S:
            if not _ensure_connection_alive(conn):
                try:
                    conn.close()
                except Exception:
                    pass
                conn = pool.get_connection()
        _last_activity = now
        return conn
    except MySQLError as e:
        raise RuntimeError(f"Impossible d'obtenir une connexion DB: {e}") from e


class DatabaseConnection:
    """
    Gestionnaire de contexte pour gérer automatiquement les connexions avec commit/rollback.

    Recommandé : À utiliser partout pour standardiser l'accès DB.

    Usage simple:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT ...")
            # Commit automatique si pas d'erreur
            # Rollback automatique en cas d'exception
            # conn.close() appelé automatiquement

    Usage avec transaction explicite:
        with DatabaseConnection(auto_commit=False) as conn:
            cur = conn.cursor()
            cur.execute("INSERT ...")
            cur.execute("UPDATE ...")
            conn.commit()  # Commit manuel
    """
    def __init__(self, auto_commit: bool = True):
        """
        Args:
            auto_commit: Si True, commit automatique à la fin si pas d'erreur.
                        Si False, nécessite conn.commit() manuel.
        """
        self.conn = None
        self.auto_commit = auto_commit
        self._committed = False
        self._statement_timeout_applied = False

    def __enter__(self):
        self.conn = get_connection()
        self._statement_timeout_applied = _set_session_statement_timeout(
            self.conn, _get_statement_timeout_ms()
        )
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            try:
                if exc_type is not None:
                    # En cas d'erreur, rollback
                    self.conn.rollback()
                elif self.auto_commit and not self._committed:
                    # Commit automatique si demandé et pas déjà fait
                    self.conn.commit()
            except Exception:
                # Ignorer les erreurs de rollback/commit pendant le cleanup
                pass
            finally:
                if self._statement_timeout_applied:
                    _clear_session_statement_timeout(self.conn)
                try:
                    self.conn.close()
                except Exception:
                    pass
        return False  # Ne pas supprimer l'exception

    def commit(self):
        """Commit manuel (optionnel)"""
        if self.conn:
            self.conn.commit()
            self._committed = True


class DatabaseCursor:
    """
    Gestionnaire de contexte pour gérer automatiquement connexion + curseur.

    Option Pro : Simplifie encore plus le code en gérant conn + cursor.

    Usage:
        with DatabaseCursor() as cur:
            cur.execute("SELECT ...")
            results = cur.fetchall()
            # Commit + close automatiques

    Usage avec dictionary cursor:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("SELECT id, nom FROM personnel")
            rows = cur.fetchall()
            # rows = [{'id': 1, 'nom': 'Dupont'}, ...]
    """
    def __init__(self, dictionary: bool = False, auto_commit: bool = True):
        """
        Args:
            dictionary: Si True, retourne des dict au lieu de tuples
            auto_commit: Si True, commit automatique si pas d'erreur
        """
        self.dictionary = dictionary
        self.auto_commit = auto_commit
        self.conn = None
        self.cursor = None
        self._statement_timeout_applied = False

    def __enter__(self):
        self.conn = get_connection()
        self._statement_timeout_applied = _set_session_statement_timeout(
            self.conn, _get_statement_timeout_ms()
        )
        self.cursor = self.conn.cursor(dictionary=self.dictionary)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            try:
                self.cursor.close()
            except Exception:
                pass

        if self.conn:
            try:
                if exc_type is not None:
                    self.conn.rollback()
                elif self.auto_commit:
                    self.conn.commit()
            except Exception:
                pass
            finally:
                if self._statement_timeout_applied:
                    _clear_session_statement_timeout(self.conn)
                try:
                    self.conn.close()
                except Exception:
                    pass
        return False
