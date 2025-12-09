import mysql.connector
from mysql.connector import pooling

# ✅ OPTIMISATION: Pool de connexions pour réutiliser les connexions DB
# Réduit le temps de création de connexion (~50-100ms par connexion)
_connection_pool = None

def _get_pool():
    """Récupère ou crée le pool de connexions (singleton)."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pooling.MySQLConnectionPool(
            pool_name="emac_pool",
            pool_size=5,  # 5 connexions réutilisables
            pool_reset_session=True,
            host="localhost",
            user="root",
            password="emacViodos$13",
            database="emac_db",
            port=3306,
            charset="utf8mb4",
            use_unicode=True,
            autocommit=False
        )
    return _connection_pool

def get_connection():
    """Récupère une connexion du pool (rapide, réutilise les connexions existantes)."""
    pool = _get_pool()
    return pool.get_connection()