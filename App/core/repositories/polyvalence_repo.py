# -*- coding: utf-8 -*-
"""
Repository pour la table Polyvalence (compétences/évaluations).

Centralise toutes les requêtes SQL liées aux compétences des opérateurs.

Usage:
    from core.repositories import PolyvalenceRepository

    # Lecture
    skills = PolyvalenceRepository.get_by_operateur(123)
    retards = PolyvalenceRepository.get_en_retard()
    matrix = PolyvalenceRepository.get_matrice_atelier(1)

    # Écriture
    PolyvalenceRepository.update_niveau(poly_id, 3, date_eval, prochaine)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, timedelta

from core.db.configbd import DatabaseCursor, DatabaseConnection
from core.models import Polyvalence, EvaluationResume, StatistiquesEvaluations
from core.repositories.base import BaseRepository
from core.utils.performance_monitor import monitor_query

logger = logging.getLogger(__name__)


class PolyvalenceRepository(BaseRepository[Polyvalence]):
    """Repository pour les opérations sur la table polyvalence."""

    TABLE = "polyvalence"
    MODEL = Polyvalence
    COLUMNS = [
        "id", "operateur_id", "poste_id", "niveau",
        "date_evaluation", "prochaine_evaluation"
    ]

    # ===========================
    # Requêtes de lecture
    # ===========================

    @classmethod
    @monitor_query('PolyvalenceRepo.get_by_operateur')
    def get_by_operateur(cls, operateur_id: int) -> List[Polyvalence]:
        """Récupère toutes les compétences d'un opérateur."""
        query = """
            SELECT p.*, pos.poste_code, pos.poste_code as poste_nom
            FROM polyvalence p
            JOIN postes pos ON p.poste_id = pos.id
            WHERE p.operateur_id = %s
            ORDER BY pos.poste_code
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (operateur_id,))
            return cls._rows_to_models(cur.fetchall())

    @classmethod
    @monitor_query('PolyvalenceRepo.get_by_poste')
    def get_by_poste(cls, poste_id: int, actifs_only: bool = True) -> List[Polyvalence]:
        """Récupère tous les opérateurs compétents sur un poste."""
        query = """
            SELECT p.*, pers.nom as operateur_nom, pers.prenom as operateur_prenom
            FROM polyvalence p
            JOIN personnel pers ON p.operateur_id = pers.id
            WHERE p.poste_id = %s
        """
        params = [poste_id]

        if actifs_only:
            query += " AND pers.statut = 'ACTIF'"

        query += " ORDER BY p.niveau DESC, pers.nom"

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, tuple(params))
            return cls._rows_to_models(cur.fetchall())

    @classmethod
    @monitor_query('PolyvalenceRepo.get_en_retard')
    def get_en_retard(cls, limit: int = 100) -> List[EvaluationResume]:
        """Récupère les évaluations en retard."""
        query = """
            SELECT
                p.id as polyvalence_id,
                p.operateur_id,
                pers.nom as operateur_nom,
                pers.prenom as operateur_prenom,
                pos.poste_code,
                pos.poste_code as poste_nom,
                p.niveau,
                p.prochaine_evaluation,
                DATEDIFF(CURDATE(), p.prochaine_evaluation) as jours_retard
            FROM polyvalence p
            JOIN personnel pers ON p.operateur_id = pers.id
            JOIN postes pos ON p.poste_id = pos.id
            WHERE pers.statut = 'ACTIF'
              AND p.prochaine_evaluation < CURDATE()
            ORDER BY jours_retard DESC
            LIMIT %s
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (limit,))
            return [
                EvaluationResume(
                    polyvalence_id=row['polyvalence_id'],
                    operateur_id=row['operateur_id'],
                    operateur_nom=row['operateur_nom'],
                    operateur_prenom=row['operateur_prenom'],
                    poste_code=row['poste_code'],
                    poste_nom=row['poste_nom'],
                    niveau=row['niveau'],
                    prochaine_evaluation=row['prochaine_evaluation'],
                    jours_retard=row['jours_retard']
                )
                for row in cur.fetchall()
            ]

    @classmethod
    @monitor_query('PolyvalenceRepo.get_a_venir')
    def get_a_venir(cls, jours: int = 30, limit: int = 100) -> List[EvaluationResume]:
        """Récupère les évaluations à venir dans les N prochains jours."""
        date_limite = date.today() + timedelta(days=jours)

        query = """
            SELECT
                p.id as polyvalence_id,
                p.operateur_id,
                pers.nom as operateur_nom,
                pers.prenom as operateur_prenom,
                pos.poste_code,
                pos.poste_code as poste_nom,
                p.niveau,
                p.prochaine_evaluation,
                DATEDIFF(p.prochaine_evaluation, CURDATE()) as jours_restants
            FROM polyvalence p
            JOIN personnel pers ON p.operateur_id = pers.id
            JOIN postes pos ON p.poste_id = pos.id
            WHERE pers.statut = 'ACTIF'
              AND p.prochaine_evaluation BETWEEN CURDATE() AND %s
            ORDER BY p.prochaine_evaluation ASC
            LIMIT %s
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (date_limite, limit))
            return [
                EvaluationResume(
                    polyvalence_id=row['polyvalence_id'],
                    operateur_id=row['operateur_id'],
                    operateur_nom=row['operateur_nom'],
                    operateur_prenom=row['operateur_prenom'],
                    poste_code=row['poste_code'],
                    poste_nom=row['poste_nom'],
                    niveau=row['niveau'],
                    prochaine_evaluation=row['prochaine_evaluation'],
                    jours_retard=-row['jours_restants']  # Négatif = à venir
                )
                for row in cur.fetchall()
            ]

    @classmethod
    def get_matrice_poste(cls, poste_id: int) -> List[Dict]:
        """
        Récupère la matrice de compétences pour un poste.
        Retourne tous les opérateurs avec leur niveau sur ce poste.
        """
        query = """
            SELECT
                pers.id as operateur_id,
                pers.nom,
                pers.prenom,
                pers.matricule,
                COALESCE(p.niveau, 0) as niveau,
                p.date_evaluation,
                p.prochaine_evaluation
            FROM personnel pers
            LEFT JOIN polyvalence p ON pers.id = p.operateur_id AND p.poste_id = %s
            WHERE pers.statut = 'ACTIF'
            ORDER BY pers.nom, pers.prenom
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (poste_id,))
            return cur.fetchall()

    @classmethod
    def get_matrice_operateur(cls, operateur_id: int) -> List[Dict]:
        """
        Récupère la matrice de compétences pour un opérateur.
        Retourne tous les postes visibles avec le niveau de l'opérateur.
        """
        query = """
            SELECT
                pos.id as poste_id,
                pos.poste_code,
                pos.poste_code as poste_nom,
                a.nom as atelier_nom,
                COALESCE(p.niveau, 0) as niveau,
                p.date_evaluation,
                p.prochaine_evaluation
            FROM postes pos
            LEFT JOIN atelier a ON pos.atelier_id = a.id
            LEFT JOIN polyvalence p ON pos.id = p.poste_id AND p.operateur_id = %s
            WHERE pos.visible = 1
            ORDER BY a.nom, pos.poste_code
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (operateur_id,))
            return cur.fetchall()

    # ===========================
    # Statistiques
    # ===========================

    @classmethod
    @monitor_query('PolyvalenceRepo.get_statistiques')
    def get_statistiques(cls) -> StatistiquesEvaluations:
        """Calcule les statistiques des évaluations (1 seule requête agrégée)."""
        stats = StatistiquesEvaluations()

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN p.prochaine_evaluation < CURDATE()
                        THEN 1 ELSE 0 END) AS en_retard,
                    SUM(CASE WHEN p.prochaine_evaluation
                        BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
                        THEN 1 ELSE 0 END) AS a_venir_7j,
                    SUM(CASE WHEN p.prochaine_evaluation
                        BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                        THEN 1 ELSE 0 END) AS a_venir_30j
                FROM polyvalence p
                JOIN personnel pers ON p.operateur_id = pers.id
                WHERE pers.statut = 'ACTIF'
            """)
            row = cur.fetchone()
            if row:
                stats.total       = row['total']       or 0
                stats.en_retard   = row['en_retard']   or 0
                stats.a_venir_7j  = row['a_venir_7j']  or 0
                stats.a_venir_30j = row['a_venir_30j'] or 0

        return stats

    @classmethod
    def count_par_niveau(cls) -> Dict[int, int]:
        """Compte les compétences par niveau."""
        query = """
            SELECT niveau, COUNT(*) as count
            FROM polyvalence p
            JOIN personnel pers ON p.operateur_id = pers.id
            WHERE pers.statut = 'ACTIF'
            GROUP BY niveau
            ORDER BY niveau
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query)
            return {row['niveau']: row['count'] for row in cur.fetchall()}

    # ===========================
    # Opérations d'écriture
    # ===========================

    @classmethod
    def create(cls, operateur_id: int, poste_id: int, niveau: int = 1,
               date_evaluation: Optional[date] = None,
               prochaine_evaluation: Optional[date] = None) -> Tuple[bool, str, Optional[int]]:
        """Crée une nouvelle compétence."""
        if niveau not in [1, 2, 3, 4]:
            return False, "Le niveau doit être entre 1 et 4", None

        # Vérifier si existe déjà
        query_check = "SELECT id FROM polyvalence WHERE operateur_id = %s AND poste_id = %s"
        with DatabaseCursor() as cur:
            cur.execute(query_check, (operateur_id, poste_id))
            if cur.fetchone():
                return False, "Cette compétence existe déjà", None

        query = """
            INSERT INTO polyvalence (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute(query, (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation))
                new_id = cur.lastrowid
                conn.commit()

                from core.services.logger import log_hist
                log_hist("CREATE", "polyvalence", new_id,
                        f"Compétence N{niveau} créée", operateur_id=operateur_id, poste_id=poste_id)

                from core.services.evaluation_service import log_historique_polyvalence
                log_historique_polyvalence(
                    operateur_id=operateur_id, poste_id=poste_id,
                    polyvalence_id=new_id,
                    action_type='AJOUT',
                    nouveau_niveau=niveau,
                    nouvelle_date_evaluation=date_evaluation,
                    source='GUI',
                )

                # Émettre l'événement pour déclencher les documents
                from core.services.event_bus import EventBus
                from core.repositories.personnel_repo import PersonnelRepository
                from core.repositories.poste_repo import PosteRepository
                personnel = PersonnelRepository.get_by_id(operateur_id)
                poste = PosteRepository.get_by_id(poste_id)
                if personnel and poste:
                    EventBus.emit('polyvalence.created', {
                        'polyvalence_id': new_id,
                        'operateur_id': operateur_id,
                        'nom': personnel.nom,
                        'prenom': personnel.prenom,
                        'poste_id': poste_id,
                        'code_poste': poste.poste_code if hasattr(poste, 'poste_code') else str(poste_id),
                        'niveau': niveau
                    }, source='PolyvalenceRepository.create')

                return True, "Compétence créée", new_id

        except Exception as e:
            logger.error(f"Erreur création polyvalence: {e}")
            return False, f"Erreur: {str(e)}", None

    @classmethod
    def update_niveau(cls, id: int, nouveau_niveau: int,
                      date_evaluation: date, prochaine_evaluation: date) -> Tuple[bool, str]:
        """Met à jour le niveau d'une compétence après évaluation."""
        if nouveau_niveau not in [1, 2, 3, 4]:
            return False, "Le niveau doit être entre 1 et 4"

        # Récupérer l'ancien niveau pour le log
        query_old = "SELECT operateur_id, poste_id, niveau FROM polyvalence WHERE id = %s"
        with DatabaseCursor() as cur:
            cur.execute(query_old, (id,))
            old = cur.fetchone()
            if not old:
                return False, "Compétence non trouvée"

        query = """
            UPDATE polyvalence
            SET niveau = %s, date_evaluation = %s, prochaine_evaluation = %s
            WHERE id = %s
        """
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute(query, (nouveau_niveau, date_evaluation, prochaine_evaluation, id))
                conn.commit()

                from core.services.logger import log_hist
                log_hist("UPDATE", "polyvalence", id,
                        f"Évaluation: N{old[2]}→N{nouveau_niveau}",
                        operateur_id=old[0], poste_id=old[1])

                if old[2] != nouveau_niveau:
                    from core.services.evaluation_service import log_historique_polyvalence
                    log_historique_polyvalence(
                        operateur_id=old[0], poste_id=old[1],
                        polyvalence_id=id,
                        action_type='MODIFICATION',
                        ancien_niveau=old[2],
                        nouveau_niveau=nouveau_niveau,
                        nouvelle_date_evaluation=date_evaluation,
                        source='GUI',
                    )

                # Émettre les événements si le niveau a changé
                old_niveau = old[2]
                if old_niveau != nouveau_niveau:
                    from core.services.event_bus import EventBus
                    from core.repositories.personnel_repo import PersonnelRepository
                    from core.repositories.poste_repo import PosteRepository
                    personnel = PersonnelRepository.get_by_id(old[0])
                    poste = PosteRepository.get_by_id(old[1])

                    if personnel and poste:
                        event_data = {
                            'polyvalence_id': id,
                            'operateur_id': old[0],
                            'nom': personnel.nom,
                            'prenom': personnel.prenom,
                            'poste_id': old[1],
                            'code_poste': poste.poste_code if hasattr(poste, 'poste_code') else str(old[1]),
                            'old_niveau': old_niveau,
                            'new_niveau': nouveau_niveau
                        }

                        EventBus.emit('polyvalence.niveau_changed', event_data,
                                     source='PolyvalenceRepository.update_niveau')

                        # Événement spécial pour le passage au niveau 2
                        if nouveau_niveau == 2 and old_niveau < 2:
                            EventBus.emit('polyvalence.niveau_2_reached', {
                                **event_data,
                                'niveau': 2
                            }, source='PolyvalenceRepository.update_niveau')

                        # Événement spécial pour le passage au niveau 3
                        if nouveau_niveau == 3 and old_niveau < 3:
                            EventBus.emit('polyvalence.niveau_3_reached', {
                                **event_data,
                                'niveau': 3
                            }, source='PolyvalenceRepository.update_niveau')

                return True, "Évaluation enregistrée"

        except Exception as e:
            logger.error(f"Erreur mise à jour polyvalence: {e}")
            return False, f"Erreur: {str(e)}"

    @classmethod
    def get_by_operateur_dict(cls, operateur_id: int) -> List[Dict]:
        """
        Retourne les polyvalences d'un opérateur sous forme de dicts.

        Inclut poste_code, niveau, date_evaluation, prochaine_evaluation.
        Utilisé par les vues qui ont besoin d'accès par clé de chaîne.
        """
        from core.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            """
            SELECT ps.poste_code, p.niveau, p.date_evaluation, p.prochaine_evaluation
            FROM polyvalence p
            JOIN postes ps ON p.poste_id = ps.id
            WHERE p.operateur_id = %s
            ORDER BY ps.poste_code
            """,
            (operateur_id,),
            dictionary=True,
        )

    @classmethod
    def upsert_prochaine_evaluation(
        cls,
        operateur_id: int,
        poste_id: int,
        niveau: int,
        prochaine_evaluation,
    ) -> Tuple[bool, str]:
        """
        Insère ou met à jour la prochaine évaluation (UPSERT).

        Utilisé lors de la création d'un opérateur pour initialiser
        sa polyvalence sans lever d'erreur si elle existe déjà.
        """
        from core.db.query_executor import QueryExecutor
        existing = QueryExecutor.fetch_one(
            "SELECT id FROM polyvalence WHERE operateur_id = %s AND poste_id = %s",
            (operateur_id, poste_id),
        )
        if existing:
            poly_id = existing[0]
            QueryExecutor.execute_write(
                "UPDATE polyvalence SET prochaine_evaluation = %s, niveau = %s WHERE id = %s",
                (prochaine_evaluation, niveau, poly_id),
            )
            return True, "Polyvalence mise à jour"
        else:
            QueryExecutor.execute_write(
                "INSERT INTO polyvalence (operateur_id, poste_id, niveau, prochaine_evaluation) "
                "VALUES (%s, %s, %s, %s)",
                (operateur_id, poste_id, niveau, prochaine_evaluation),
            )

            # Émettre l'événement pour déclencher la proposition du document du poste
            try:
                from core.services.event_bus import EventBus
                from core.repositories.personnel_repo import PersonnelRepository
                from core.repositories.poste_repo import PosteRepository
                personnel = PersonnelRepository.get_by_id(operateur_id)
                poste = PosteRepository.get_by_id(poste_id)
                if personnel and poste:
                    EventBus.emit('polyvalence.created', {
                        'operateur_id': operateur_id,
                        'nom': personnel.nom,
                        'prenom': personnel.prenom,
                        'poste_id': poste_id,
                        'code_poste': poste.poste_code if hasattr(poste, 'poste_code') else str(poste_id),
                        'niveau': niveau,
                    }, source='PolyvalenceRepository.upsert_prochaine_evaluation')
            except Exception as _e:
                logger.warning(f"Erreur émission polyvalence.created (upsert): {_e}")

            return True, "Polyvalence créée"

    @classmethod
    def get_en_retard_filtre(cls, poste_code: str = None, limit: int = 10) -> List[Dict]:
        """
        Retourne les évaluations en retard pour le tableau de bord.

        Args:
            poste_code: Filtre optionnel sur le code poste
            limit: Nombre max de résultats
        """
        from core.db.query_executor import QueryExecutor
        query = """
            SELECT p.nom, p.prenom, pos.poste_code, poly.prochaine_evaluation
            FROM polyvalence poly
            INNER JOIN personnel p ON p.id = poly.operateur_id
            LEFT JOIN postes pos ON pos.id = poly.poste_id
            WHERE poly.prochaine_evaluation < CURDATE()
              AND p.statut = 'ACTIF'
        """
        params: List[Any] = []
        if poste_code:
            query += " AND pos.poste_code = %s"
            params.append(poste_code)
        query += " ORDER BY poly.prochaine_evaluation ASC LIMIT %s"
        params.append(limit)
        return QueryExecutor.fetch_all(query, tuple(params), dictionary=True)

    @classmethod
    def get_a_venir_filtre(
        cls, jours: int = 30, poste_code: str = None, limit: int = 10
    ) -> List[Dict]:
        """
        Retourne les évaluations à venir pour le tableau de bord.

        Args:
            jours: Horizon en jours (défaut 30)
            poste_code: Filtre optionnel sur le code poste
            limit: Nombre max de résultats
        """
        from core.db.query_executor import QueryExecutor
        query = """
            SELECT p.nom, p.prenom, pos.poste_code, poly.prochaine_evaluation
            FROM polyvalence poly
            INNER JOIN personnel p ON p.id = poly.operateur_id
            LEFT JOIN postes pos ON pos.id = poly.poste_id
            WHERE poly.prochaine_evaluation BETWEEN CURDATE()
              AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
              AND p.statut = 'ACTIF'
        """
        params: List[Any] = [jours]
        if poste_code:
            query += " AND pos.poste_code = %s"
            params.append(poste_code)
        query += " ORDER BY poly.prochaine_evaluation ASC LIMIT %s"
        params.append(limit)
        return QueryExecutor.fetch_all(query, tuple(params), dictionary=True)

    @classmethod
    def delete_competence(cls, operateur_id: int, poste_id: int) -> Tuple[bool, str]:
        """Supprime une compétence."""
        # Lire l'état avant suppression pour l'historique
        from core.db.query_executor import QueryExecutor as QE
        old = QE.fetch_one(
            "SELECT id, niveau, date_evaluation FROM polyvalence WHERE operateur_id = %s AND poste_id = %s",
            (operateur_id, poste_id), dictionary=True
        )

        query = "DELETE FROM polyvalence WHERE operateur_id = %s AND poste_id = %s"

        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute(query, (operateur_id, poste_id))
                deleted = cur.rowcount > 0
                conn.commit()

                if deleted:
                    from core.services.logger import log_hist
                    log_hist("DELETE", "polyvalence", None,
                            f"Compétence supprimée", operateur_id=operateur_id, poste_id=poste_id)

                    from core.services.evaluation_service import log_historique_polyvalence
                    log_historique_polyvalence(
                        operateur_id=operateur_id, poste_id=poste_id,
                        action_type='SUPPRESSION',
                        ancien_niveau=old['niveau'] if old else None,
                        ancienne_date_evaluation=old['date_evaluation'] if old else None,
                        source='GUI',
                    )

                return deleted, "Compétence supprimée" if deleted else "Compétence non trouvée"

        except Exception as e:
            logger.error(f"Erreur suppression polyvalence: {e}")
            return False, f"Erreur: {str(e)}"

    @classmethod
    def get_actuelles_with_type(cls, operateur_id: int) -> List[Dict]:
        """
        Retourne les polyvalences actuelles avec les champs type/id/commentaire
        pour la vue historique personnel (HistoriquePersonnelTab).
        """
        from core.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            """
            SELECT 'ACTUELLE' AS type, p.id, ps.poste_code, p.niveau,
                   p.date_evaluation, p.prochaine_evaluation, NULL AS commentaire
            FROM polyvalence p
            JOIN postes ps ON p.poste_id = ps.id
            WHERE p.operateur_id = %s
            ORDER BY ps.poste_code
            """,
            (operateur_id,),
            dictionary=True,
        )

    @classmethod
    def get_anciennes_historique(cls, operateur_id: int) -> List[Dict]:
        """
        Retourne l'historique des polyvalences depuis historique_polyvalence
        (IMPORT_MANUEL + MODIFICATION + AJOUT + SUPPRESSION).
        """
        from core.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            """
            SELECT 'ANCIENNE' AS type, hp.id, p.poste_code,
                   CASE
                       WHEN hp.action_type = 'MODIFICATION' THEN hp.ancien_niveau
                       ELSE hp.nouveau_niveau
                   END AS niveau,
                   CASE
                       WHEN hp.action_type = 'MODIFICATION' THEN hp.ancienne_date_evaluation
                       ELSE hp.nouvelle_date_evaluation
                   END AS date_evaluation,
                   NULL AS prochaine_evaluation,
                   CASE
                       WHEN hp.action_type = 'MODIFICATION' THEN
                           CONCAT('Modifié le ', DATE_FORMAT(hp.date_action, '%d/%m/%Y'),
                                  ' → N', hp.nouveau_niveau)
                       ELSE hp.commentaire
                   END AS commentaire
            FROM historique_polyvalence hp
            LEFT JOIN postes p ON hp.poste_id = p.id
            WHERE hp.operateur_id = %s
            ORDER BY hp.date_action DESC
            """,
            (operateur_id,),
            dictionary=True,
        )
