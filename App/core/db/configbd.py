import mysql.connector
from mysql.connector import pooling
import os

# ✅ OPTIMISATION: Pool de connexions pour réutiliser les connexions DB
# Réduit le temps de création de connexion (~50-100ms par connexion)
_connection_pool = None

def _get_pool():
    """Récupère ou crée le pool de connexions (singleton)."""
    global _connection_pool
    if _connection_pool is None:
        # 🔐 SÉCURITÉ: Mot de passe chargé depuis les variables d'environnement
        # Priorité: 1) Variable d'environnement  2) Fichier .env  3) Valeur par défaut (dev uniquement)
        db_password = os.environ.get('EMAC_DB_PASSWORD')

        if not db_password:
            # Tentative de chargement depuis fichier .env
            env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
            if os.path.exists(env_file):
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('EMAC_DB_PASSWORD='):
                            db_password = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break

        if not db_password:
            # 🔐 SÉCURITÉ: Pas de mot de passe par défaut
            raise ValueError(
                "❌ ERREUR: Mot de passe MySQL non configuré !\n"
                "   Pour configurer, choisissez l'une de ces méthodes :\n"
                "   1) Créer un fichier .env avec : EMAC_DB_PASSWORD=votre_mot_de_passe\n"
                "   2) Définir la variable d'environnement : set EMAC_DB_PASSWORD=votre_mot_de_passe\n"
                "   3) Exécuter le script : configure_db.bat\n"
                f"   Fichier .env recherché : {env_file}"
            )

        _connection_pool = pooling.MySQLConnectionPool(
            pool_name="emac_pool",
            pool_size=5,  # 5 connexions réutilisables
            pool_reset_session=True,
            host=os.environ.get('EMAC_DB_HOST', 'localhost'),
            user=os.environ.get('EMAC_DB_USER', 'root'),
            password=db_password,
            database=os.environ.get('EMAC_DB_NAME', 'emac_db'),
            port=int(os.environ.get('EMAC_DB_PORT', '3306')),
            charset="utf8mb4",
            use_unicode=True,
            autocommit=False
        )
    return _connection_pool

def get_connection():
    """Récupère une connexion du pool (rapide, réutilise les connexions existantes)."""
    pool = _get_pool()
    return pool.get_connection()