# -*- coding: utf-8 -*-
"""
Repository pour la table Absence.

Centralise toutes les requêtes SQL liées aux absences.

Usage:
    from core.repositories import AbsenceRepository

    # Lecture
    absences = AbsenceRepository.get_by_operateur(123)
    en_cours = AbsenceRepository.get_en_cours()
    planning = AbsenceRepository.get_planning_periode(date_debut, date_fin)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, timedelta

from core.db.configbd import DatabaseCursor, DatabaseConnection
from core.models import Absence
from core.repositories.base import BaseRepository
from core.utils.performance_monitor import monitor_query

logger = logging.getLogger(__name__)


class AbsenceRepository(BaseRepository[Absence]):
    """Repository pour les opérations sur la table absences."""

    TABLE = "absences"
    MODEL = Absence
    COLUMNS = [
        "id", "operateur_id", "type_absence", "date_debut", "date_fin",
        "statut", "commentaire", "justificatif"
    ]

    # Types d'absence valides
    TYPES_VALIDES = ["CP", "RTT", "MALADIE", "AT", "FORMATION", "AUTRE"]
    STATUTS_VALIDES = ["EN_ATTENTE", "VALIDEE", "REFUSEE"]

    # ===========================
    # Requêtes de lecture
    # ===========================

    @classmethod
    @monitor_query('AbsenceRepo.get_by_operateur')
    def get_by_operateur(cls, operateur_id: int, annee: Optional[int] = None) -> List[Absence]:
        """Récupère les absences d'un opérateur."""
        columns = ", ".join(cls.COLUMNS)
        query = f"""
            SELECT {columns} FROM absences
            WHERE operateur_id = %s
        """
        params = [operateur_id]

        if annee:
            query += " AND YEAR(date_debut) = %s"
            params.append(annee)

        query += " ORDER BY date_debut DESC"

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, tuple(params))
            return cls._rows_to_models(cur.fetchall())

    @classmethod
    @monitor_query('AbsenceRepo.get_en_cours')
    def get_en_cours(cls) -> List[Absence]:
        """Récupère les absences en cours aujourd'hui."""
        query = """
            SELECT a.*, p.nom as operateur_nom, p.prenom as operateur_prenom
            FROM absences a
            JOIN personnel p ON a.operateur_id = p.id
            WHERE a.statut = 'VALIDEE'
              AND CURDATE() BETWEEN a.date_debut AND a.date_fin
              AND p.statut = 'ACTIF'
            ORDER BY a.date_fin ASC
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query)
            return cls._rows_to_models(cur.fetchall())

    @classmethod
    @monitor_query('AbsenceRepo.get_futures')
    def get_futures(cls, jours: int = 30) -> List[Absence]:
        """Récupère les absences planifiées pour les N prochains jours."""
        date_limite = date.today() + timedelta(days=jours)

        query = """
            SELECT a.*, p.nom as operateur_nom, p.prenom as operateur_prenom
            FROM absences a
            JOIN personnel p ON a.operateur_id = p.id
            WHERE a.statut = 'VALIDEE'
              AND a.date_debut > CURDATE()
              AND a.date_debut <= %s
              AND p.statut = 'ACTIF'
            ORDER BY a.date_debut ASC
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (date_limite,))
            return cls._rows_to_models(cur.fetchall())

    @classmethod
    def get_planning_periode(cls, date_debut: date, date_fin: date) -> List[Dict]:
        """
        Récupère toutes les absences qui chevauchent une période.
        Utile pour afficher un planning.
        """
        query = """
            SELECT
                a.*,
                p.nom as operateur_nom,
                p.prenom as operateur_prenom,
                p.matricule
            FROM absences a
            JOIN personnel p ON a.operateur_id = p.id
            WHERE a.statut = 'VALIDEE'
              AND a.date_debut <= %s
              AND a.date_fin >= %s
              AND p.statut = 'ACTIF'
            ORDER BY a.date_debut, p.nom
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (date_fin, date_debut))
            return cur.fetchall()

    @classmethod
    def get_en_attente(cls) -> List[Absence]:
        """Récupère les demandes d'absence en attente de validation."""
        query = """
            SELECT a.*, p.nom as operateur_nom, p.prenom as operateur_prenom
            FROM absences a
            JOIN personnel p ON a.operateur_id = p.id
            WHERE a.statut = 'EN_ATTENTE'
              AND p.statut = 'ACTIF'
            ORDER BY a.date_debut ASC
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query)
            return cls._rows_to_models(cur.fetchall())

    @classmethod
    def check_chevauchement(cls, operateur_id: int, date_debut: date, date_fin: date,
                            exclude_id: Optional[int] = None) -> bool:
        """
        Vérifie s'il y a chevauchement avec une absence existante.

        Args:
            operateur_id: ID de l'opérateur
            date_debut: Date de début de l'absence à vérifier
            date_fin: Date de fin de l'absence à vérifier
            exclude_id: ID d'absence à exclure (pour les modifications)

        Returns:
            True s'il y a chevauchement
        """
        query = """
            SELECT COUNT(*) as count FROM absences
            WHERE operateur_id = %s
              AND statut != 'REFUSEE'
              AND date_debut <= %s
              AND date_fin >= %s
        """
        params = [operateur_id, date_fin, date_debut]

        if exclude_id:
            query += " AND id != %s"
            params.append(exclude_id)

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, tuple(params))
            return cur.fetchone()['count'] > 0

    # ===========================
    # Statistiques
    # ===========================

    @classmethod
    def count_par_type(cls, annee: Optional[int] = None) -> Dict[str, int]:
        """Compte les absences par type."""
        query = """
            SELECT type_absence, COUNT(*) as count
            FROM absences
            WHERE statut = 'VALIDEE'
        """
        params = []

        if annee:
            query += " AND YEAR(date_debut) = %s"
            params.append(annee)

        query += " GROUP BY type_absence"

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, tuple(params) if params else None)
            return {row['type_absence']: row['count'] for row in cur.fetchall()}

    @classmethod
    def get_jours_par_operateur(cls, annee: int) -> List[Dict]:
        """
        Calcule le nombre de jours d'absence par opérateur pour une année.
        """
        query = """
            SELECT
                a.operateur_id,
                p.nom, p.prenom, p.matricule,
                SUM(DATEDIFF(a.date_fin, a.date_debut) + 1) as total_jours,
                SUM(CASE WHEN a.type_absence = 'CP' THEN DATEDIFF(a.date_fin, a.date_debut) + 1 ELSE 0 END) as jours_cp,
                SUM(CASE WHEN a.type_absence = 'MALADIE' THEN DATEDIFF(a.date_fin, a.date_debut) + 1 ELSE 0 END) as jours_maladie
            FROM absences a
            JOIN personnel p ON a.operateur_id = p.id
            WHERE a.statut = 'VALIDEE'
              AND YEAR(a.date_debut) = %s
              AND p.statut = 'ACTIF'
            GROUP BY a.operateur_id, p.nom, p.prenom, p.matricule
            ORDER BY total_jours DESC
        """
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (annee,))
            return cur.fetchall()

    # ===========================
    # Opérations d'écriture
    # ===========================

    @classmethod
    def create(cls, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Crée une nouvelle absence."""
        required = ["operateur_id", "type_absence", "date_debut", "date_fin"]
        for field in required:
            if not data.get(field):
                return False, f"Le champ '{field}' est obligatoire", None

        # Valider le type
        if data['type_absence'] not in cls.TYPES_VALIDES:
            return False, f"Type invalide. Valides: {cls.TYPES_VALIDES}", None

        # Valider les dates
        if data['date_fin'] < data['date_debut']:
            return False, "La date de fin doit être après la date de début", None

        # Vérifier chevauchement
        if cls.check_chevauchement(data['operateur_id'], data['date_debut'], data['date_fin']):
            return False, "Cette période chevauche une absence existante", None

        allowed = ["operateur_id", "type_absence", "date_debut", "date_fin", "statut", "commentaire", "justificatif"]
        insert_data = {k: v for k, v in data.items() if k in allowed and v is not None}
        insert_data.setdefault("statut", "EN_ATTENTE")

        columns = list(insert_data.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO absences ({', '.join(columns)}) VALUES ({placeholders})"

        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute(query, tuple(insert_data.values()))
                new_id = cur.lastrowid
                conn.commit()

                from core.services.logger import log_hist
                log_hist("CREATE", "absences", new_id,
                        f"Absence {data['type_absence']} du {data['date_debut']} au {data['date_fin']}",
                        operateur_id=data['operateur_id'])

                return True, "Absence créée", new_id

        except Exception as e:
            logger.error(f"Erreur création absence: {e}")
            return False, f"Erreur: {str(e)}", None

    @classmethod
    def update(cls, id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Met à jour une absence."""
        if not cls.exists(id):
            return False, "Absence non trouvée"

        # Récupérer l'absence existante pour validation
        existing = cls.get_by_id(id)
        if not existing:
            return False, "Absence non trouvée"

        # Vérifier chevauchement si dates modifiées
        date_debut = data.get('date_debut', existing.date_debut)
        date_fin = data.get('date_fin', existing.date_fin)
        if 'date_debut' in data or 'date_fin' in data:
            if cls.check_chevauchement(existing.operateur_id, date_debut, date_fin, exclude_id=id):
                return False, "Cette période chevauche une absence existante", None

        allowed = ["type_absence", "date_debut", "date_fin", "statut", "commentaire", "justificatif"]
        update_data = {k: v for k, v in data.items() if k in allowed}

        if not update_data:
            return False, "Aucun champ valide à mettre à jour"

        set_clauses = [f"{col} = %s" for col in update_data.keys()]
        query = f"UPDATE absences SET {', '.join(set_clauses)} WHERE id = %s"

        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute(query, tuple(list(update_data.values()) + [id]))
                conn.commit()

                from core.services.logger import log_hist
                log_hist("UPDATE", "absences", id, f"Mise à jour: {list(update_data.keys())}")

                return True, "Absence mise à jour"

        except Exception as e:
            logger.error(f"Erreur mise à jour absence: {e}")
            return False, f"Erreur: {str(e)}"

    @classmethod
    def valider(cls, id: int) -> Tuple[bool, str]:
        """Valide une demande d'absence."""
        return cls.update(id, {"statut": "VALIDEE"})

    @classmethod
    def refuser(cls, id: int, motif: Optional[str] = None) -> Tuple[bool, str]:
        """Refuse une demande d'absence."""
        data = {"statut": "REFUSEE"}
        if motif:
            data["commentaire"] = motif
        return cls.update(id, data)

    @classmethod
    def annuler(cls, id: int) -> Tuple[bool, str]:
        """Annule une absence (suppression logique via statut REFUSEE)."""
        return cls.update(id, {"statut": "REFUSEE"})
