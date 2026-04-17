# -*- coding: utf-8 -*-
"""
Repository pour la table Contrat.

Centralise toutes les requêtes SQL liées aux contrats de travail.

Usage:
    from domain.repositories import ContratRepository

    # Lecture
    contrat = ContratRepository.get_by_id(123)
    actifs = ContratRepository.get_all_actifs()
    expirants = ContratRepository.get_expirant_dans(30)

    # Écriture
    ContratRepository.create(data)
    ContratRepository.prolonger(123, nouvelle_date_fin)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, timedelta

from infrastructure.db.query_executor import QueryExecutor
from domain.models import Contrat, StatistiquesContrats
from domain.repositories.base import BaseRepository
from infrastructure.config.performance_monitor import monitor_query

logger = logging.getLogger(__name__)


class ContratRepository(BaseRepository[Contrat]):
    """Repository pour les opérations sur la table contrat."""

    TABLE = "contrat"
    MODEL = Contrat
    COLUMNS = [
        "id", "personnel_id", "type_contrat", "date_debut", "date_fin",
        "etp", "categorie", "coefficient", "actif", "motif",
        "date_sortie", "motif_sortie"
    ]

    # ===========================
    # Requêtes de lecture
    # ===========================

    @classmethod
    @monitor_query('ContratRepo.get_all_actifs')
    def get_all_actifs(cls, limit: int = 500) -> List[Contrat]:
        """Récupère tous les contrats actifs avec info personnel."""
        query = """
            SELECT c.*, p.nom as personnel_nom, p.prenom as personnel_prenom
            FROM contrat c
            JOIN personnel p ON c.personnel_id = p.id
            WHERE c.actif = 1
            ORDER BY c.date_fin ASC
            LIMIT %s
        """
        return cls._rows_to_models(QueryExecutor.fetch_all(query, (limit,), dictionary=True))

    @classmethod
    def get_by_operateur(cls, operateur_id: int, include_inactifs: bool = False) -> List[Contrat]:
        """Récupère tous les contrats d'un employé."""
        columns = ", ".join(cls.COLUMNS)
        query = f"""
            SELECT {columns} FROM contrat
            WHERE personnel_id = %s
        """
        params = [operateur_id]

        if not include_inactifs:
            query += " AND actif = 1"

        query += " ORDER BY date_debut DESC"

        return cls._rows_to_models(QueryExecutor.fetch_all(query, tuple(params), dictionary=True))

    @classmethod
    def get_actif_by_operateur(cls, operateur_id: int) -> Optional[Contrat]:
        """Récupère le contrat actif d'un employé."""
        columns = ", ".join(cls.COLUMNS)
        query = f"""
            SELECT {columns} FROM contrat
            WHERE personnel_id = %s AND actif = 1
            ORDER BY date_debut DESC
            LIMIT 1
        """
        return cls._row_to_model(QueryExecutor.fetch_one(query, (operateur_id,), dictionary=True))

    @classmethod
    @monitor_query('ContratRepo.get_expirant_dans')
    def get_expirant_dans(cls, jours: int = 30) -> List[Contrat]:
        """
        Récupère les contrats expirant dans les N prochains jours.

        Args:
            jours: Nombre de jours à regarder

        Returns:
            Liste de contrats triés par urgence
        """
        date_limite = date.today() + timedelta(days=jours)

        query = """
            SELECT c.*, p.nom as personnel_nom, p.prenom as personnel_prenom,
                   DATEDIFF(c.date_fin, CURDATE()) as jours_restants
            FROM contrat c
            JOIN personnel p ON c.personnel_id = p.id
            WHERE c.actif = 1
              AND c.date_fin IS NOT NULL
              AND c.date_fin BETWEEN CURDATE() AND %s
              AND p.statut = 'ACTIF'
            ORDER BY c.date_fin ASC
        """
        return cls._rows_to_models(QueryExecutor.fetch_all(query, (date_limite,), dictionary=True))

    @classmethod
    def get_expires(cls) -> List[Contrat]:
        """Récupère les contrats déjà expirés mais encore actifs."""
        query = """
            SELECT c.*, p.nom as personnel_nom, p.prenom as personnel_prenom
            FROM contrat c
            JOIN personnel p ON c.personnel_id = p.id
            WHERE c.actif = 1
              AND c.date_fin IS NOT NULL
              AND c.date_fin < CURDATE()
            ORDER BY c.date_fin ASC
        """
        return cls._rows_to_models(QueryExecutor.fetch_all(query, dictionary=True))

    @classmethod
    def get_cdi(cls) -> List[Contrat]:
        """Récupère tous les CDI actifs."""
        query = """
            SELECT c.*, p.nom as personnel_nom, p.prenom as personnel_prenom
            FROM contrat c
            JOIN personnel p ON c.personnel_id = p.id
            WHERE c.actif = 1 AND c.type_contrat = 'CDI'
            ORDER BY p.nom
        """
        return cls._rows_to_models(QueryExecutor.fetch_all(query, dictionary=True))

    # ===========================
    # Statistiques
    # ===========================

    @classmethod
    @monitor_query('ContratRepo.get_statistiques')
    def get_statistiques(cls) -> StatistiquesContrats:
        """Calcule les statistiques des contrats."""
        stats = StatistiquesContrats()

        row = QueryExecutor.fetch_one(
            "SELECT COUNT(*) as total FROM contrat WHERE actif = 1", dictionary=True
        )
        stats.total = row['total'] if row else 0

        for row in QueryExecutor.fetch_all(
            "SELECT type_contrat, COUNT(*) as count FROM contrat WHERE actif = 1 GROUP BY type_contrat",
            dictionary=True
        ):
            if row['type_contrat'] == 'CDI':
                stats.cdi = row['count']
            elif row['type_contrat'] == 'CDD':
                stats.cdd = row['count']
            elif row['type_contrat'] == 'INTERIM':
                stats.interim = row['count']

        row7 = QueryExecutor.fetch_one("""
            SELECT COUNT(*) as count FROM contrat
            WHERE actif = 1 AND date_fin IS NOT NULL
            AND date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
        """, dictionary=True)
        stats.expirant_7j = row7['count'] if row7 else 0

        row30 = QueryExecutor.fetch_one("""
            SELECT COUNT(*) as count FROM contrat
            WHERE actif = 1 AND date_fin IS NOT NULL
            AND date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """, dictionary=True)
        stats.expirant_30j = row30['count'] if row30 else 0

        return stats

    # ===========================
    # Opérations d'écriture
    # ===========================

    @classmethod
    def create(cls, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Crée un nouveau contrat."""
        required = ["personnel_id", "type_contrat", "date_debut"]
        for field in required:
            if not data.get(field):
                return False, f"Le champ '{field}' est obligatoire", None

        allowed = ["personnel_id", "type_contrat", "date_debut", "date_fin",
                   "etp", "categorie", "coefficient", "actif", "motif",
                   "date_sortie", "motif_sortie"]

        insert_data = {k: v for k, v in data.items() if k in allowed and v is not None}
        insert_data.setdefault("actif", True)

        columns = list(insert_data.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        columns_str = ", ".join(columns)

        query = f"INSERT INTO contrat ({columns_str}) VALUES ({placeholders})"

        try:
            def _do_insert(cur):
                cur.execute(query, tuple(insert_data.values()))
                return cur.lastrowid

            new_id = QueryExecutor.with_transaction(_do_insert)

            from infrastructure.logging.optimized_db_logger import log_hist
            log_hist("CREATE", "contrat", new_id,
                        f"Contrat {data.get('type_contrat')} créé pour personnel {data.get('personnel_id')}")

            from application.event_bus import EventBus
            from domain.repositories.personnel_repo import PersonnelRepository
            personnel = PersonnelRepository.get_by_id(data.get('personnel_id'))
            if personnel:
                EventBus.emit('contrat.created', {
                    'contrat_id': new_id,
                    'personnel_id': data.get('personnel_id'),
                    'nom': personnel.nom,
                    'prenom': personnel.prenom,
                    'type_contrat': data.get('type_contrat'),
                    'date_debut': str(data.get('date_debut')),
                    'date_fin': str(data.get('date_fin')) if data.get('date_fin') else None
                }, source='ContratRepository.create')

            return True, "Contrat créé avec succès", new_id

        except Exception as e:
            logger.error(f"Erreur création contrat: {e}")
            return False, f"Erreur: {str(e)}", None

    @classmethod
    def update(cls, id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Met à jour un contrat."""
        if not cls.exists(id):
            return False, "Contrat non trouvé"

        # SÉCURITÉ: Whitelist stricte des colonnes autorisées (frozenset immuable)
        ALLOWED_COLUMNS = frozenset(["type_contrat", "date_debut", "date_fin", "etp",
                                     "categorie", "coefficient", "actif", "motif",
                                     "date_sortie", "motif_sortie"])

        update_data = {k: v for k, v in data.items() if k in ALLOWED_COLUMNS}

        if not update_data:
            return False, "Aucun champ valide à mettre à jour"

        # SÉCURITÉ: Double validation - chaque colonne DOIT être dans la whitelist
        for col in update_data.keys():
            if col not in ALLOWED_COLUMNS:
                raise ValueError(f"Colonne non autorisée: {col}")

        set_clauses = [f"{col} = %s" for col in update_data.keys()]
        query = f"UPDATE contrat SET {', '.join(set_clauses)} WHERE id = %s"

        try:
            QueryExecutor.execute_write(query, tuple(list(update_data.values()) + [id]))

            from infrastructure.logging.optimized_db_logger import log_hist
            log_hist("UPDATE", "contrat", id, f"Mise à jour: {list(update_data.keys())}")

            return True, "Contrat mis à jour"

        except Exception as e:
            logger.error(f"Erreur mise à jour contrat: {e}")
            return False, f"Erreur: {str(e)}"

    @classmethod
    def prolonger(cls, id: int, nouvelle_date_fin: date) -> Tuple[bool, str]:
        """Prolonge un contrat en modifiant sa date de fin."""
        # Récupérer l'ancien contrat avant la mise à jour
        old_contrat = cls.get_by_id(id)

        success, msg = cls.update(id, {"date_fin": nouvelle_date_fin})

        # Émettre l'événement si la prolongation a réussi
        if success and old_contrat:
            from application.event_bus import EventBus
            from domain.repositories.personnel_repo import PersonnelRepository
            personnel = PersonnelRepository.get_by_id(old_contrat.personnel_id)
            if personnel:
                EventBus.emit('contrat.renewed', {
                    'contrat_id': id,
                    'personnel_id': old_contrat.personnel_id,
                    'nom': personnel.nom,
                    'prenom': personnel.prenom,
                    'type_contrat': old_contrat.type_contrat,
                    'old_date_fin': str(old_contrat.date_fin) if old_contrat.date_fin else None,
                    'new_date_fin': str(nouvelle_date_fin)
                }, source='ContratRepository.prolonger')

        return success, msg

    @classmethod
    def terminer(cls, id: int) -> Tuple[bool, str]:
        """Termine un contrat (actif = False)."""
        return cls.update(id, {"actif": False})

    @classmethod
    def get_resume_for_operateur(cls, operateur_id: int) -> Dict[str, Any]:
        """
        Retourne un résumé léger du contrat actif d'un opérateur.

        Utilisé par get_resume_operateur() dans rh_service.

        Returns:
            {
                "a_contrat_actif": bool,
                "type": str | None,
                "jours_restants": int | None
            }
        """
        row = QueryExecutor.fetch_one(
            """
            SELECT type_contrat,
                   date_fin,
                   DATEDIFF(date_fin, CURDATE()) AS jours_restants
            FROM contrat
            WHERE personnel_id = %s AND actif = 1
            LIMIT 1
            """,
            (operateur_id,),
            dictionary=True,
        )
        return {
            "a_contrat_actif": row is not None,
            "type": row["type_contrat"] if row else None,
            "jours_restants": row["jours_restants"] if row else None,
        }

    @classmethod
    def get_alertes(cls, jours: int = 30, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Retourne les contrats actifs expirant dans les N prochains jours,
        pour les opérateurs actifs.

        Utilisé par get_alertes_rh_dashboard() dans rh_service.

        Returns:
            Liste de dicts (id, personnel_id, type_contrat, date_fin,
                            nom, prenom, matricule, jours_restants)
        """
        return QueryExecutor.fetch_all(
            """
            SELECT
                c.id, c.personnel_id, c.type_contrat, c.date_fin,
                p.nom, p.prenom, p.matricule,
                DATEDIFF(c.date_fin, CURDATE()) AS jours_restants
            FROM contrat c
            INNER JOIN personnel p ON p.id = c.personnel_id
            WHERE c.actif = 1
              AND c.date_fin IS NOT NULL
              AND c.date_fin BETWEEN CURDATE()
                  AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
              AND p.statut = 'ACTIF'
            ORDER BY c.date_fin ASC
            LIMIT %s
            """,
            (jours, limit),
            dictionary=True,
        )

    @classmethod
    def count_alertes(cls, jours: int = 30) -> int:
        """
        Compte les contrats actifs expirant dans les N prochains jours.

        Utilisé par get_alertes_rh_count() dans rh_service.
        """
        return QueryExecutor.fetch_scalar(
            """
            SELECT COUNT(*) FROM contrat c
            INNER JOIN personnel p ON p.id = c.personnel_id
            WHERE c.actif = 1 AND c.date_fin IS NOT NULL
              AND c.date_fin BETWEEN CURDATE()
                  AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
              AND p.statut = 'ACTIF'
            """,
            (jours,),
            default=0,
        )

    @classmethod
    def get_resume_formation(cls, operateur_id: int) -> Dict[str, Any]:
        """
        Retourne un résumé agrégé des formations d'un opérateur.

        Utilisé par get_resume_operateur() dans rh_service.

        Returns:
            {"total": int, "terminees": int, "planifiees": int}
        """
        row = QueryExecutor.fetch_one(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN statut = 'Terminée'  THEN 1 ELSE 0 END) AS terminees,
                SUM(CASE WHEN statut = 'Planifiée' THEN 1 ELSE 0 END) AS planifiees
            FROM formation
            WHERE personnel_id = %s
            """,
            (operateur_id,),
            dictionary=True,
        ) or {}
        return {
            "total": row.get("total") or 0,
            "terminees": row.get("terminees") or 0,
            "planifiees": row.get("planifiees") or 0,
        }
