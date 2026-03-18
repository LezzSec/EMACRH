# -*- coding: utf-8 -*-
"""
ContratServiceCRUD - Service métier unifié pour la gestion des contrats.

Fusion de contrat_service.py (validation + requêtes riches + monitoring)
et contrat_service_crud.py (CRUD générique CRUDService).

Usage:
    from core.services.contrat_service_crud import ContratServiceCRUD

    # Créer un contrat (désactive l'ancien actif automatiquement)
    success, msg, new_id = ContratServiceCRUD.create_contract({
        'personnel_id': 1,
        'type_contrat': 'CDI',
        'date_debut': date.today(),
        'etp': 1.0,
    })

    # Getters enrichis (JOIN personnel)
    contrat = ContratServiceCRUD.get_active_contract(operateur_id=1)
    expirants = ContratServiceCRUD.get_expiring_contracts(days=30)

    # Helpers UI
    types = ContratServiceCRUD.get_contract_types()
    categories = ContratServiceCRUD.get_categories()
"""

from datetime import date
from typing import Dict, List, Optional, Tuple

from core.db.query_executor import QueryExecutor
from core.services.crud_service import CRUDService
from core.services.permission_manager import require
from core.utils.logging_config import get_logger
from core.utils.performance_monitor import monitor_query

logger = get_logger(__name__)


class ContratServiceCRUD(CRUDService):
    """Service métier CRUD unifié pour la table contrat."""

    TABLE_NAME = "contrat"
    ACTION_PREFIX = "CONTRAT_"

    ALLOWED_FIELDS = [
        'personnel_id', 'type_contrat', 'date_debut', 'date_fin', 'etp',
        'categorie', 'echelon', 'emploi', 'salaire', 'actif',
        'nom_tuteur', 'prenom_tuteur', 'ecole',
        'nom_ett', 'adresse_ett', 'nom_ge', 'adresse_ge',
        'date_autorisation_travail', 'date_demande_autorisation',
        'type_titre_autorisation', 'numero_autorisation_travail',
        'date_limite_autorisation',
    ]

    # ========================= VALIDATION =========================

    @classmethod
    def validate_contract_dates(
        cls, date_debut: date, date_fin: Optional[date]
    ) -> Tuple[bool, str]:
        """Valide la cohérence des dates du contrat."""
        if not date_debut:
            return False, "La date de début est obligatoire"
        if date_fin:
            if date_fin < date_debut:
                return False, "La date de fin ne peut pas être antérieure à la date de début"
            if date_fin < date.today():
                return False, "La date de fin est dans le passé"
        return True, ""

    @classmethod
    def validate_etp(cls, etp: float) -> Tuple[bool, str]:
        """Valide l'ETP (doit être entre 0 et 1)."""
        if etp is None:
            return True, ""
        if not (0 < etp <= 1):
            return False, "L'ETP doit être compris entre 0 et 1"
        return True, ""

    @classmethod
    def validate_contract_data(cls, data: dict) -> Tuple[bool, str]:
        """Valide toutes les données d'un contrat."""
        valid, msg = cls.validate_contract_dates(data.get('date_debut'), data.get('date_fin'))
        if not valid:
            return False, msg

        valid, msg = cls.validate_etp(data.get('etp', 1.0))
        if not valid:
            return False, msg

        if not data.get('type_contrat'):
            return False, "Le type de contrat est obligatoire"

        if not data.get('personnel_id'):
            return False, "L'identifiant du personnel est obligatoire"

        return True, ""

    # ========================= CRUD MÉTIER =========================

    @classmethod
    def create_contract(cls, data: dict) -> Tuple[bool, str, Optional[int]]:
        """
        Crée un nouveau contrat.

        Désactive automatiquement les contrats actifs existants pour cet opérateur,
        valide les données, puis insère le nouveau contrat.

        Raises:
            PermissionError: Si l'utilisateur n'a pas rh.contrats.edit
        """
        require('rh.contrats.edit')

        valid, msg = cls.validate_contract_data(data)
        if not valid:
            return False, msg, None

        try:
            QueryExecutor.execute_write(
                "UPDATE contrat SET actif = 0 WHERE personnel_id = %s AND actif = 1",
                (data['personnel_id'],)
            )

            query = """
                INSERT INTO contrat (
                    personnel_id, type_contrat, date_debut, date_fin, etp,
                    categorie, echelon, emploi, salaire, actif,
                    nom_tuteur, prenom_tuteur, ecole, nom_ett, adresse_ett,
                    nom_ge, adresse_ge, date_autorisation_travail,
                    date_demande_autorisation, type_titre_autorisation,
                    numero_autorisation_travail, date_limite_autorisation
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            values = (
                data['personnel_id'], data['type_contrat'],
                data['date_debut'], data.get('date_fin'), data.get('etp', 1.0),
                data.get('categorie'), data.get('echelon'), data.get('emploi'),
                data.get('salaire'), data.get('actif', 1),
                data.get('nom_tuteur'), data.get('prenom_tuteur'), data.get('ecole'),
                data.get('nom_ett'), data.get('adresse_ett'),
                data.get('nom_ge'), data.get('adresse_ge'),
                data.get('date_autorisation_travail'), data.get('date_demande_autorisation'),
                data.get('type_titre_autorisation'), data.get('numero_autorisation_travail'),
                data.get('date_limite_autorisation'),
            )
            contract_id = QueryExecutor.execute_write(query, values, return_lastrowid=True)
            return True, "Contrat créé avec succès", contract_id

        except Exception as e:
            logger.exception(f"Erreur création contrat: {e}")
            return False, f"Erreur lors de la création du contrat : {e}", None

    @classmethod
    def update_contract(cls, contract_id: int, data: dict) -> Tuple[bool, str]:
        """
        Met à jour un contrat existant avec validation complète.

        Raises:
            PermissionError: Si l'utilisateur n'a pas rh.contrats.edit
        """
        require('rh.contrats.edit')

        valid, msg = cls.validate_contract_data(data)
        if not valid:
            return False, msg

        try:
            query = """
                UPDATE contrat SET
                    type_contrat = %s, date_debut = %s, date_fin = %s, etp = %s,
                    categorie = %s, echelon = %s, emploi = %s, salaire = %s, actif = %s,
                    nom_tuteur = %s, prenom_tuteur = %s, ecole = %s,
                    nom_ett = %s, adresse_ett = %s, nom_ge = %s, adresse_ge = %s,
                    date_autorisation_travail = %s, date_demande_autorisation = %s,
                    type_titre_autorisation = %s, numero_autorisation_travail = %s,
                    date_limite_autorisation = %s
                WHERE id = %s
            """
            values = (
                data['type_contrat'], data['date_debut'], data.get('date_fin'),
                data.get('etp', 1.0), data.get('categorie'), data.get('echelon'),
                data.get('emploi'), data.get('salaire'), data.get('actif', 1),
                data.get('nom_tuteur'), data.get('prenom_tuteur'), data.get('ecole'),
                data.get('nom_ett'), data.get('adresse_ett'),
                data.get('nom_ge'), data.get('adresse_ge'),
                data.get('date_autorisation_travail'), data.get('date_demande_autorisation'),
                data.get('type_titre_autorisation'), data.get('numero_autorisation_travail'),
                data.get('date_limite_autorisation'),
                contract_id,
            )
            QueryExecutor.execute_write(query, values)
            return True, "Contrat mis à jour avec succès"

        except Exception as e:
            logger.exception(f"Erreur mise à jour contrat {contract_id}: {e}")
            return False, f"Erreur lors de la mise à jour du contrat : {e}"

    # ========================= QUERIES ENRICHIES (JOIN personnel) =========================

    @classmethod
    @monitor_query('Get Active Contract')
    def get_active_contract(cls, operateur_id: int) -> Optional[dict]:
        """Récupère le contrat actif d'un opérateur (avec nom/prenom)."""
        try:
            return QueryExecutor.fetch_one("""
                SELECT c.*, p.nom, p.prenom
                FROM contrat c
                LEFT JOIN personnel p ON p.id = c.personnel_id
                WHERE c.personnel_id = %s AND c.actif = 1
                ORDER BY c.date_debut DESC
                LIMIT 1
            """, (operateur_id,), dictionary=True)
        except Exception as e:
            logger.error(f"Erreur récupération contrat actif opérateur {operateur_id}: {e}")
            return None

    @classmethod
    def get_all_contracts(cls, operateur_id: int, include_inactive: bool = False) -> List[dict]:
        """Récupère tous les contrats d'un opérateur (avec nom/prenom)."""
        try:
            query = """
                SELECT c.*, p.nom, p.prenom
                FROM contrat c
                LEFT JOIN personnel p ON p.id = c.personnel_id
                WHERE c.personnel_id = %s
            """
            if not include_inactive:
                query += " AND c.actif = 1"
            query += " ORDER BY c.date_debut DESC"
            return QueryExecutor.fetch_all(query, (operateur_id,), dictionary=True)
        except Exception as e:
            logger.error(f"Erreur récupération contrats opérateur {operateur_id}: {e}")
            return []

    @classmethod
    def get_contract_by_id(cls, contract_id: int) -> Optional[dict]:
        """Récupère un contrat par ID (avec nom/prenom du personnel)."""
        try:
            return QueryExecutor.fetch_one("""
                SELECT c.*, p.nom, p.prenom
                FROM contrat c
                LEFT JOIN personnel p ON p.id = c.personnel_id
                WHERE c.id = %s
            """, (contract_id,), dictionary=True)
        except Exception as e:
            logger.error(f"Erreur récupération contrat {contract_id}: {e}")
            return None

    @classmethod
    @monitor_query('Get Expiring Contracts')
    def get_expiring_contracts(cls, days: int = 30) -> List[dict]:
        """
        Récupère les contrats expirant dans les N prochains jours.
        Inclut jours_restants calculé, nom/prenom et filtre statut ACTIF.
        """
        try:
            return QueryExecutor.fetch_all("""
                SELECT *
                FROM v_contrats_fin_proche
                WHERE jours_restants BETWEEN 0 AND %s
                ORDER BY date_fin ASC
            """, (days,), dictionary=True)
        except Exception as e:
            logger.error(f"Erreur récupération contrats expirants: {e}")
            return []

    @classmethod
    @monitor_query('Get All Active Contracts')
    def get_all_active_contracts(cls) -> List[dict]:
        """Récupère tous les contrats actifs avec nom, prenom et matricule."""
        try:
            return QueryExecutor.fetch_all("""
                SELECT
                    c.*,
                    p.nom, p.prenom, p.matricule, p.statut
                FROM contrat c
                LEFT JOIN personnel p ON p.id = c.personnel_id
                WHERE c.actif = 1
                ORDER BY p.nom, p.prenom, c.date_debut DESC
            """, dictionary=True)
        except Exception as e:
            logger.error(f"Erreur récupération tous contrats actifs: {e}")
            return []

    # ========================= STATISTIQUES =========================

    @classmethod
    @monitor_query('Get Contract Statistics')
    def get_contract_statistics(cls) -> dict:
        """Récupère des statistiques agrégées sur les contrats."""
        try:
            stats = {}
            stats['total_actifs'] = QueryExecutor.fetch_scalar(
                "SELECT COUNT(*) FROM contrat WHERE actif = 1", default=0
            )
            stats['par_type'] = QueryExecutor.fetch_all("""
                SELECT type_contrat, COUNT(*) as count
                FROM contrat WHERE actif = 1
                GROUP BY type_contrat ORDER BY count DESC
            """, dictionary=True)
            stats['expiration_30j'] = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM v_contrats_fin_proche
                WHERE jours_restants BETWEEN 0 AND 30
            """, default=0)
            stats['expires'] = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM v_contrats_fin_proche
                WHERE jours_restants < 0
            """, default=0)
            return stats
        except Exception as e:
            logger.error(f"Erreur calcul statistiques contrats: {e}")
            return {}

    # ========================= QUERIES SIMPLES (sans JOIN) =========================

    @classmethod
    def get_by_operateur(
        cls,
        operateur_id: int,
        actif_only: bool = False,
        order_by: str = 'date_debut DESC'
    ) -> List[Dict]:
        """Récupère les contrats d'un opérateur (sans JOIN, rapide)."""
        conditions = {'personnel_id': operateur_id}
        if actif_only:
            conditions['actif'] = 1
        return cls.get_all(conditions=conditions, order_by=order_by)

    @classmethod
    def get_expiring_soon(
        cls,
        jours: int = 30,
        type_contrat: str = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Retourne les contrats actifs expirant dans les N prochains jours.
        Version filtrée par type et limitée (pour tableaux de bord).
        Pour la version complète avec jours_restants, utiliser get_expiring_contracts().
        """
        if type_contrat:
            sql = """
                SELECT c.id, c.type_contrat, c.date_fin, p.nom, p.prenom
                FROM contrat c
                INNER JOIN personnel p ON p.id = c.personnel_id
                WHERE c.actif = 1
                  AND c.date_fin IS NOT NULL
                  AND c.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
                  AND p.statut = 'ACTIF'
                  AND c.type_contrat = %s
                ORDER BY c.date_fin ASC
                LIMIT %s
            """
            params = (jours, type_contrat, limit)
        else:
            sql = """
                SELECT c.id, c.type_contrat, c.date_fin, p.nom, p.prenom
                FROM contrat c
                INNER JOIN personnel p ON p.id = c.personnel_id
                WHERE c.actif = 1
                  AND c.date_fin IS NOT NULL
                  AND c.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
                  AND p.statut = 'ACTIF'
                ORDER BY c.date_fin ASC
                LIMIT %s
            """
            params = (jours, limit)
        return QueryExecutor.fetch_all(sql, params, dictionary=True)

    @classmethod
    def get_actifs(cls, order_by: str = 'date_debut DESC') -> List[Dict]:
        """Récupère tous les contrats actifs (sans JOIN)."""
        return cls.get_all(conditions={'actif': 1}, order_by=order_by)

    @classmethod
    def get_by_type(cls, type_contrat: str, actif_only: bool = False) -> List[Dict]:
        """Récupère tous les contrats d'un type donné."""
        conditions = {'type_contrat': type_contrat}
        if actif_only:
            conditions['actif'] = 1
        return cls.get_all(conditions=conditions, order_by='date_debut DESC')

    @classmethod
    def activer(cls, record_id: int) -> Tuple[bool, str]:
        """Active un contrat."""
        return cls.update(record_id=record_id, actif=1)

    @classmethod
    def desactiver(cls, record_id: int) -> Tuple[bool, str]:
        """Désactive un contrat."""
        return cls.update(record_id=record_id, actif=0)

    @classmethod
    def count_by_operateur(cls, operateur_id: int, actif_only: bool = False) -> int:
        """Compte le nombre de contrats d'un opérateur."""
        conditions = {'personnel_id': operateur_id}
        if actif_only:
            conditions['actif'] = 1
        return cls.count(**conditions)

    @classmethod
    def count_by_type(cls, type_contrat: str, actif_only: bool = False) -> int:
        """Compte le nombre de contrats par type."""
        conditions = {'type_contrat': type_contrat}
        if actif_only:
            conditions['actif'] = 1
        return cls.count(**conditions)

    # ========================= HELPERS UI (STATIQUES) =========================

    @staticmethod
    def get_contract_types() -> List[str]:
        """Retourne la liste des types de contrats disponibles."""
        return [
            'CDI', 'CDD', 'Stagiaire', 'Apprentissage', 'Intérimaire',
            'Temps partiel', 'Mise à disposition GE', 'Etranger hors UE', 'CIFRE',
        ]

    @staticmethod
    def get_categories() -> List[str]:
        """Retourne la liste des catégories professionnelles."""
        return [
            'Ouvrier', 'Ouvrier qualifié', 'Employé', 'Agent de maîtrise', 'Cadre',
        ]

    # ========================= ALIASES (COMPATIBILITÉ) =========================

    @classmethod
    def get_contrats_expirant_bientot(cls, days: int = 30) -> List[dict]:
        """Alias de get_expiring_contracts()."""
        return cls.get_expiring_contracts(days)

    @classmethod
    def get_tous_contrats(cls) -> List[dict]:
        """Alias de get_all_active_contracts()."""
        return cls.get_all_active_contracts()

    @classmethod
    def get_expirant_soon(cls, jours: int = 30) -> List[Dict]:
        """Alias simplifié de get_expiring_soon() (sans filtre type/limit)."""
        return cls.get_expiring_soon(jours=jours, limit=1000)
