"""
Service de gestion des contrats
Fournit les opérations CRUD et la logique métier pour la table contrat

✅ OPTIMISATIONS APPLIQUÉES:
- Monitoring des requêtes clés (détection régressions)
- Logs DB optimisés (async, non-bloquant)
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple

from core.db.query_executor import QueryExecutor
from core.utils.logging_config import get_logger

logger = get_logger(__name__)

# ✅ OPTIMISATIONS : Monitoring + Logs optimisés
from core.utils.performance_monitor import monitor_query
from core.services.optimized_db_logger import log_hist_async

# ✅ Permissions
from core.services.permission_manager import require, PermissionError


# ========================= VALIDATION =========================

def validate_contract_dates(date_debut: date, date_fin: Optional[date]) -> Tuple[bool, str]:
    """Valide la cohérence des dates du contrat."""
    if not date_debut:
        return False, "La date de début est obligatoire"

    if date_fin:
        if date_fin < date_debut:
            return False, "La date de fin ne peut pas être antérieure à la date de début"

        if date_fin < date.today():
            return False, "La date de fin est dans le passé"

    return True, ""


def validate_etp(etp: float) -> Tuple[bool, str]:
    """Valide l'ETP (doit être entre 0 et 1)."""
    if etp is None:
        return True, ""  # ETP optionnel

    if not (0 < etp <= 1):
        return False, "L'ETP doit être compris entre 0 et 1"

    return True, ""


def validate_contract_data(data: dict) -> Tuple[bool, str]:
    """Valide toutes les données d'un contrat."""
    # Validation des dates
    date_debut = data.get('date_debut')
    date_fin = data.get('date_fin')

    valid_dates, msg_dates = validate_contract_dates(date_debut, date_fin)
    if not valid_dates:
        return False, msg_dates

    # Validation de l'ETP
    etp = data.get('etp', 1.0)
    valid_etp, msg_etp = validate_etp(etp)
    if not valid_etp:
        return False, msg_etp

    # Validation type de contrat
    if not data.get('type_contrat'):
        return False, "Le type de contrat est obligatoire"

    # Validation de l'opérateur
    if not data.get('personnel_id'):
        return False, "L'identifiant du personnel est obligatoire"

    return True, ""


# ========================= CRUD OPERATIONS =========================

def create_contract(data: dict) -> Tuple[bool, str, Optional[int]]:
    """
    Crée un nouveau contrat.

    Args:
        data: Dictionnaire contenant les données du contrat

    Returns:
        Tuple (success, message, contract_id)

    Raises:
        PermissionError: Si l'utilisateur n'a pas la permission rh.contrats.edit
    """
    require('rh.contrats.edit')

    # Validation
    valid, msg = validate_contract_data(data)
    if not valid:
        return False, msg, None

    try:
        # Désactiver les anciens contrats de cet opérateur
        QueryExecutor.execute_write(
            "UPDATE contrat SET actif = 0 WHERE personnel_id = %s AND actif = 1",
            (data['personnel_id'],)
        )

        # Insérer le nouveau contrat
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
            data['personnel_id'],
            data['type_contrat'],
            data['date_debut'],
            data.get('date_fin'),
            data.get('etp', 1.0),
            data.get('categorie'),
            data.get('echelon'),
            data.get('emploi'),
            data.get('salaire'),
            data.get('actif', 1),
            data.get('nom_tuteur'),
            data.get('prenom_tuteur'),
            data.get('ecole'),
            data.get('nom_ett'),
            data.get('adresse_ett'),
            data.get('nom_ge'),
            data.get('adresse_ge'),
            data.get('date_autorisation_travail'),
            data.get('date_demande_autorisation'),
            data.get('type_titre_autorisation'),
            data.get('numero_autorisation_travail'),
            data.get('date_limite_autorisation'),
        )

        contract_id = QueryExecutor.execute_write(query, values, return_lastrowid=True)

        return True, "Contrat créé avec succès", contract_id

    except Exception as e:
        return False, f"Erreur lors de la création du contrat : {e}", None


def update_contract(contract_id: int, data: dict) -> Tuple[bool, str]:
    """
    Met à jour un contrat existant.

    Args:
        contract_id: ID du contrat à modifier
        data: Dictionnaire contenant les nouvelles données

    Returns:
        Tuple (success, message)

    Raises:
        PermissionError: Si l'utilisateur n'a pas la permission rh.contrats.edit
    """
    require('rh.contrats.edit')

    # Validation
    valid, msg = validate_contract_data(data)
    if not valid:
        return False, msg

    try:
        query = """
            UPDATE contrat SET
                type_contrat = %s,
                date_debut = %s,
                date_fin = %s,
                etp = %s,
                categorie = %s,
                echelon = %s,
                emploi = %s,
                salaire = %s,
                actif = %s,
                nom_tuteur = %s,
                prenom_tuteur = %s,
                ecole = %s,
                nom_ett = %s,
                adresse_ett = %s,
                nom_ge = %s,
                adresse_ge = %s,
                date_autorisation_travail = %s,
                date_demande_autorisation = %s,
                type_titre_autorisation = %s,
                numero_autorisation_travail = %s,
                date_limite_autorisation = %s
            WHERE id = %s
        """

        values = (
            data['type_contrat'],
            data['date_debut'],
            data.get('date_fin'),
            data.get('etp', 1.0),
            data.get('categorie'),
            data.get('echelon'),
            data.get('emploi'),
            data.get('salaire'),
            data.get('actif', 1),
            data.get('nom_tuteur'),
            data.get('prenom_tuteur'),
            data.get('ecole'),
            data.get('nom_ett'),
            data.get('adresse_ett'),
            data.get('nom_ge'),
            data.get('adresse_ge'),
            data.get('date_autorisation_travail'),
            data.get('date_demande_autorisation'),
            data.get('type_titre_autorisation'),
            data.get('numero_autorisation_travail'),
            data.get('date_limite_autorisation'),
            contract_id
        )

        QueryExecutor.execute_write(query, values)

        return True, "Contrat mis à jour avec succès"

    except Exception as e:
        return False, f"Erreur lors de la mise à jour du contrat : {e}"


def delete_contract(contract_id: int) -> Tuple[bool, str]:
    """
    Supprime (désactive) un contrat.

    Args:
        contract_id: ID du contrat à supprimer

    Returns:
        Tuple (success, message)

    Raises:
        PermissionError: Si l'utilisateur n'a pas la permission rh.contrats.delete
    """
    require('rh.contrats.delete')

    try:
        # Soft delete : on désactive plutôt que de supprimer
        QueryExecutor.execute_write(
            "UPDATE contrat SET actif = 0 WHERE id = %s",
            (contract_id,)
        )

        return True, "Contrat désactivé avec succès"

    except Exception as e:
        return False, f"Erreur lors de la suppression du contrat : {e}"


# ========================= QUERIES =========================

@monitor_query('Get Active Contract')
def get_active_contract(operateur_id: int) -> Optional[dict]:
    """Récupère le contrat actif d'un opérateur."""
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
        logger.error(f"Erreur lors de la récupération du contrat actif : {e}")
        return None


def get_all_contracts(operateur_id: int, include_inactive: bool = False) -> List[dict]:
    """Récupère tous les contrats d'un opérateur."""
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
        logger.error(f"Erreur lors de la récupération des contrats : {e}")
        return []


def get_contract_by_id(contract_id: int) -> Optional[dict]:
    """Récupère un contrat par son ID."""
    try:
        return QueryExecutor.fetch_one("""
            SELECT c.*, p.nom, p.prenom
            FROM contrat c
            LEFT JOIN personnel p ON p.id = c.personnel_id
            WHERE c.id = %s
        """, (contract_id,), dictionary=True)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération du contrat : {e}")
        return None


@monitor_query('Get Expiring Contracts')
def get_expiring_contracts(days: int = 30) -> List[dict]:
    """
    Récupère les contrats qui expirent dans les N prochains jours.

    Args:
        days: Nombre de jours pour la recherche (défaut: 30)

    Returns:
        Liste des contrats à renouveler
    """
    try:
        end_date = date.today() + timedelta(days=days)

        return QueryExecutor.fetch_all("""
            SELECT
                c.*,
                p.nom,
                p.prenom,
                DATEDIFF(c.date_fin, CURDATE()) as jours_restants
            FROM contrat c
            LEFT JOIN personnel p ON p.id = c.personnel_id
            WHERE c.actif = 1
              AND c.date_fin IS NOT NULL
              AND c.date_fin BETWEEN CURDATE() AND %s
              AND p.statut = 'ACTIF'
            ORDER BY c.date_fin ASC
        """, (end_date,), dictionary=True)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des contrats expirants : {e}")
        return []


@monitor_query('Get All Active Contracts')
def get_all_active_contracts() -> List[dict]:
    """Récupère tous les contrats actifs de tous les opérateurs."""
    try:
        return QueryExecutor.fetch_all("""
            SELECT
                c.*,
                p.nom,
                p.prenom,
                p.matricule,
                p.statut
            FROM contrat c
            LEFT JOIN personnel p ON p.id = c.personnel_id
            WHERE c.actif = 1
            ORDER BY p.nom, p.prenom, c.date_debut DESC
        """, dictionary=True)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des contrats actifs : {e}")
        return []


# ========================= STATISTICS =========================

@monitor_query('Get Contract Statistics')
def get_contract_statistics() -> dict:
    """Récupère des statistiques sur les contrats."""
    try:
        stats = {}

        # Total contrats actifs
        stats['total_actifs'] = QueryExecutor.fetch_scalar(
            "SELECT COUNT(*) FROM contrat WHERE actif = 1",
            default=0
        )

        # Répartition par type
        stats['par_type'] = QueryExecutor.fetch_all("""
            SELECT type_contrat, COUNT(*) as count
            FROM contrat
            WHERE actif = 1
            GROUP BY type_contrat
            ORDER BY count DESC
        """, dictionary=True)

        # Contrats expirant < 30j
        stats['expiration_30j'] = QueryExecutor.fetch_scalar("""
            SELECT COUNT(*) FROM contrat
            WHERE actif = 1
              AND date_fin IS NOT NULL
              AND date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """, default=0)

        # Contrats expirés
        stats['expires'] = QueryExecutor.fetch_scalar("""
            SELECT COUNT(*) FROM contrat
            WHERE actif = 1
              AND date_fin IS NOT NULL
              AND date_fin < CURDATE()
        """, default=0)

        return stats

    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques : {e}")
        return {}


# ========================= HELPERS =========================

def get_contract_types() -> List[str]:
    """Retourne la liste des types de contrats disponibles."""
    return [
        'CDI',
        'CDD',
        'Stagiaire',
        'Apprentissage',
        'Intérimaire',
        'Temps partiel',
        'Mise à disposition GE',
        'Etranger hors UE',
        'CIFRE'
    ]


def get_categories() -> List[str]:
    """Retourne la liste des catégories professionnelles."""
    return [
        'Ouvrier',
        'Ouvrier qualifié',
        'Employé',
        'Agent de maîtrise',
        'Cadre'
    ]


# ========================= ALIASES POUR COMPATIBILITÉ =========================

def get_contrats_expirant_bientot(days: int = 30) -> List[dict]:
    """
    Alias pour get_expiring_contracts()
    Récupère les contrats qui expirent bientôt

    Args:
        days (int): Nombre de jours (défaut: 30)

    Returns:
        Liste des contrats expirant dans les N jours
    """
    return get_expiring_contracts(days)


def get_tous_contrats() -> List[dict]:
    """
    Alias pour get_all_active_contracts()
    Récupère tous les contrats actifs

    Returns:
        Liste de tous les contrats actifs
    """
    return get_all_active_contracts()
