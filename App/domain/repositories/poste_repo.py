# -*- coding: utf-8 -*-
"""
Repository pour la table Poste.

Centralise toutes les requêtes SQL liées aux postes de travail.

Usage:
    from domain.repositories import PosteRepository

    # Lecture
    poste = PosteRepository.get_by_id(123)
    postes = PosteRepository.get_all_visibles()
    postes_atelier = PosteRepository.get_by_atelier(1)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

from infrastructure.db.query_executor import QueryExecutor
from domain.models import Poste, Atelier
from domain.repositories.base import BaseRepository
from infrastructure.config.performance_monitor import monitor_query

logger = logging.getLogger(__name__)


class PosteRepository(BaseRepository[Poste]):
    """Repository pour les opérations sur la table postes."""

    TABLE = "postes"
    MODEL = Poste
    COLUMNS = [
        "id", "poste_code", "besoins_postes",
        "visible", "atelier_id"
    ]

    # ===========================
    # Requêtes de lecture
    # ===========================

    @classmethod
    @monitor_query('PosteRepo.get_all_visibles')
    def get_all_visibles(cls) -> List[Poste]:
        """Récupère tous les postes visibles avec leur atelier."""
        query = """
            SELECT p.*, a.nom as atelier_nom
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            WHERE p.visible = 1
            ORDER BY a.nom, p.poste_code
        """
        return cls._rows_to_models(QueryExecutor.fetch_all(query, dictionary=True))

    @classmethod
    def get_by_code(cls, poste_code: str) -> Optional[Poste]:
        """Récupère un poste par son code."""
        query = """
            SELECT p.*, a.nom as atelier_nom
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            WHERE p.poste_code = %s
            LIMIT 1
        """
        return cls._row_to_model(QueryExecutor.fetch_one(query, (poste_code,), dictionary=True))

    @classmethod
    @monitor_query('PosteRepo.get_by_atelier')
    def get_by_atelier(cls, atelier_id: int, visibles_only: bool = True) -> List[Poste]:
        """Récupère les postes d'un atelier."""
        query = """
            SELECT p.*, a.nom as atelier_nom
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            WHERE p.atelier_id = %s
        """
        params = [atelier_id]

        if visibles_only:
            query += " AND p.visible = 1"

        query += " ORDER BY p.poste_code"

        return cls._rows_to_models(QueryExecutor.fetch_all(query, tuple(params), dictionary=True))

    @classmethod
    def get_codes_list(cls) -> List[str]:
        """Récupère la liste des codes de postes (pour combos)."""
        query = "SELECT DISTINCT poste_code FROM postes WHERE visible = 1 ORDER BY poste_code"
        return [row[0] for row in QueryExecutor.fetch_all(query)]

    @classmethod
    def search(cls, terme: str, limit: int = 20) -> List[Poste]:
        """Recherche des postes par code ou nom d'atelier."""
        pattern = f"%{terme}%"
        query = """
            SELECT p.*, a.nom as atelier_nom
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            WHERE p.visible = 1
              AND (p.poste_code LIKE %s OR a.nom LIKE %s)
            ORDER BY p.poste_code
            LIMIT %s
        """
        return cls._rows_to_models(QueryExecutor.fetch_all(query, (pattern, pattern, limit), dictionary=True))

    # ===========================
    # Statistiques
    # ===========================

    @classmethod
    def count_visibles(cls) -> int:
        """Compte les postes visibles."""
        query = "SELECT COUNT(*) as total FROM postes WHERE visible = 1"
        row = QueryExecutor.fetch_one(query, dictionary=True)
        return row['total'] if row else 0

    @classmethod
    def count_par_atelier(cls) -> Dict[str, int]:
        """Compte les postes par atelier."""
        query = """
            SELECT a.nom as atelier, COUNT(p.id) as count
            FROM postes p
            JOIN atelier a ON p.atelier_id = a.id
            WHERE p.visible = 1
            GROUP BY a.id, a.nom
            ORDER BY a.nom
        """
        return {row['atelier']: row['count'] for row in QueryExecutor.fetch_all(query, dictionary=True)}

    @classmethod
    def get_avec_besoin(cls) -> List[Dict]:
        """
        Récupère les postes avec leur besoin et le nombre d'opérateurs compétents.
        Utile pour identifier les postes sous-staffés.
        """
        query = """
            SELECT
                p.id, p.poste_code, p.besoins_postes,
                a.nom as atelier_nom,
                COUNT(DISTINCT poly.personnel_id) as nb_competents,
                SUM(CASE WHEN poly.niveau >= 3 THEN 1 ELSE 0 END) as nb_confirmes
            FROM postes p
            LEFT JOIN atelier a ON p.atelier_id = a.id
            LEFT JOIN polyvalence poly ON p.id = poly.poste_id
            LEFT JOIN personnel pers ON poly.personnel_id = pers.id AND pers.statut = 'ACTIF'
            WHERE p.visible = 1
            GROUP BY p.id, p.poste_code, p.besoins_postes, a.nom
            ORDER BY a.nom, p.poste_code
        """
        return QueryExecutor.fetch_all(query, dictionary=True)

    # ===========================
    # Opérations d'écriture
    # ===========================

    @classmethod
    def create(cls, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Crée un nouveau poste."""
        if not data.get('poste_code'):
            return False, "Le code du poste est obligatoire", None

        # Vérifier unicité du code
        if cls.get_by_code(data['poste_code']):
            return False, f"Le code '{data['poste_code']}' existe déjà", None

        allowed = ["poste_code", "atelier_id", "visible", "besoins_postes"]
        insert_data = {k: v for k, v in data.items() if k in allowed and v is not None}
        insert_data.setdefault("visible", True)
        insert_data.setdefault("besoins_postes", 0)

        columns = list(insert_data.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO postes ({', '.join(columns)}) VALUES ({placeholders})"

        try:
            def _do_insert(cur):
                cur.execute(query, tuple(insert_data.values()))
                return cur.lastrowid

            new_id = QueryExecutor.with_transaction(_do_insert)

            from infrastructure.logging.optimized_db_logger import log_hist
            log_hist("CREATE", "postes", new_id, f"Poste {data['poste_code']} créé")

            return True, "Poste créé", new_id

        except Exception as e:
            logger.error(f"Erreur création poste: {e}")
            return False, f"Erreur: {str(e)}", None

    @classmethod
    def update(cls, id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Met à jour un poste."""
        if not cls.exists(id):
            return False, "Poste non trouvé"

        # SÉCURITÉ: Whitelist stricte des colonnes autorisées (frozenset immuable)
        ALLOWED_COLUMNS = frozenset(["poste_code", "atelier_id", "visible", "besoins_postes"])
        update_data = {k: v for k, v in data.items() if k in ALLOWED_COLUMNS}

        if not update_data:
            return False, "Aucun champ valide à mettre à jour"

        # SÉCURITÉ: Double validation - chaque colonne DOIT être dans la whitelist
        for col in update_data.keys():
            if col not in ALLOWED_COLUMNS:
                raise ValueError(f"Colonne non autorisée: {col}")

        set_clauses = [f"{col} = %s" for col in update_data.keys()]
        query = f"UPDATE postes SET {', '.join(set_clauses)} WHERE id = %s"

        try:
            QueryExecutor.execute_write(query, tuple(list(update_data.values()) + [id]))

            from infrastructure.logging.optimized_db_logger import log_hist
            log_hist("UPDATE", "postes", id, f"Mise à jour: {list(update_data.keys())}")

            return True, "Poste mis à jour"

        except Exception as e:
            logger.error(f"Erreur mise à jour poste: {e}")
            return False, f"Erreur: {str(e)}"

    @classmethod
    def set_visible(cls, id: int, visible: bool) -> Tuple[bool, str]:
        """Change la visibilité d'un poste."""
        return cls.update(id, {"visible": visible})

    @classmethod
    def set_besoin(cls, id: int, besoin: int) -> Tuple[bool, str]:
        """Met à jour le besoin en effectif d'un poste."""
        if besoin < 0:
            return False, "Le besoin ne peut pas être négatif"
        return cls.update(id, {"besoins_postes": besoin})

    @classmethod
    def get_all_codes(cls) -> List[str]:
        """Retourne tous les codes de postes (y compris invisibles) triés."""
        rows = QueryExecutor.fetch_all(
            "SELECT poste_code FROM postes ORDER BY poste_code ASC",
            dictionary=True,
        )
        return [r["poste_code"] for r in rows]

    @classmethod
    def delete_by_code(cls, poste_code: str) -> Tuple[bool, str]:
        """Supprime un poste par son code."""
        from infrastructure.logging.optimized_db_logger import log_hist
        import json
        try:
            QueryExecutor.execute_write(
                "DELETE FROM postes WHERE poste_code = %s",
                (poste_code,),
            )
            log_hist(
                "DELETE", "postes", None,
                json.dumps({"poste_code": poste_code, "type": "suppression_poste"}, ensure_ascii=False),
            )
            return True, f"Poste '{poste_code}' supprimé"
        except Exception as e:
            logger.error(f"Erreur suppression poste {poste_code}: {e}")
            return False, f"Erreur: {str(e)}"


class AtelierRepository(BaseRepository[Atelier]):
    """Repository pour les opérations sur la table atelier."""

    TABLE = "atelier"
    MODEL = Atelier
    COLUMNS = ["id", "nom"]

    @classmethod
    def get_all(cls, limit: int = 100) -> List[Atelier]:
        """Récupère tous les ateliers."""
        columns = ", ".join(cls.COLUMNS)
        query = f"SELECT {columns} FROM atelier ORDER BY nom LIMIT %s"
        return cls._rows_to_models(QueryExecutor.fetch_all(query, (limit,), dictionary=True))

    @classmethod
    def get_by_nom(cls, nom: str) -> Optional[Atelier]:
        """Récupère un atelier par son nom."""
        columns = ", ".join(cls.COLUMNS)
        query = f"SELECT {columns} FROM atelier WHERE nom = %s LIMIT 1"
        return cls._row_to_model(QueryExecutor.fetch_one(query, (nom,), dictionary=True))

    @classmethod
    def get_noms_list(cls) -> List[str]:
        """Récupère la liste des noms d'ateliers (pour combos)."""
        query = "SELECT nom FROM atelier ORDER BY nom"
        return [row[0] for row in QueryExecutor.fetch_all(query)]
