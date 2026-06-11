# -*- coding: utf-8 -*-
"""
Service de génération automatique de matricules
Génère des matricules au format 8 chiffres selon le type d'emploi :
  00xxxxxx → Employé CDI/CDD
  10xxxxxx → Intérimaire
  20xxxxxx → Stagiaire
"""

from infrastructure.db.query_executor import QueryExecutor

# regexp de filtrage, valeur de base si aucun matricule n'existe encore
_TYPE_CONFIG = {
    'CDI_CDD':     ('^00[0-9]{6}$', 0),
    'INTERIMAIRE': ('^10[0-9]{6}$', 10_000_000),
    'STAGIAIRE':   ('^20[0-9]{6}$', 20_000_000),
}


def generer_prochain_matricule_par_type(type_emploi='CDI_CDD'):
    """
    Génère le prochain matricule disponible pour le type d'emploi donné.

    Args:
        type_emploi (str): 'CDI_CDD', 'INTERIMAIRE' ou 'STAGIAIRE'

    Returns:
        str: Matricule 8 chiffres (ex: '00000438', '10000001', '20000001')
    """
    regexp, base = _TYPE_CONFIG.get(type_emploi, _TYPE_CONFIG['CDI_CDD'])
    dernier = QueryExecutor.fetch_scalar(
        "SELECT MAX(CAST(matricule AS UNSIGNED)) FROM personnel WHERE matricule REGEXP %s",
        (regexp,), default=base
    )
    prochain = (int(dernier) if dernier else base) + 1
    return f"{prochain:08d}"


def generer_prochain_matricule():
    """Alias CDI/CDD — conservé pour compatibilité."""
    return generer_prochain_matricule_par_type('CDI_CDD')


def matricule_existe(matricule):
    """
    Vérifie si un matricule existe déjà dans la base

    Args:
        matricule (str): Le matricule à vérifier

    Returns:
        bool: True si le matricule existe, False sinon
    """
    return QueryExecutor.fetch_scalar(
        "SELECT COUNT(*) FROM personnel WHERE matricule = %s",
        (matricule,), default=0
    ) > 0


def assigner_matricule_si_production(operateur_id, est_production=True):
    """
    Assigne un matricule à un opérateur existant s'il n'en a pas déjà un
    et s'il est marqué comme personnel de production

    Args:
        operateur_id (int): L'ID de l'opérateur
        est_production (bool): True si l'opérateur est du personnel de production

    Returns:
        str or None: Le matricule assigné, ou None si pas assigné
    """
    if not est_production:
        return None

    row = QueryExecutor.fetch_one(
        "SELECT matricule FROM personnel WHERE id = %s", (operateur_id,)
    )

    if row is None:
        return None

    matricule_actuel = row[0]

    if matricule_actuel is not None and matricule_actuel.strip() != "":
        return matricule_actuel

    nouveau_matricule = generer_prochain_matricule()
    QueryExecutor.execute_write(
        "UPDATE personnel SET matricule = %s WHERE id = %s",
        (nouveau_matricule, operateur_id), return_lastrowid=False
    )

    return nouveau_matricule


# ========================= ALIASES POUR COMPATIBILITÉ =========================

def generer_matricule(nom: str, prenom: str) -> str:
    """
    Alias pour generer_prochain_matricule()
    Génère un nouveau matricule (format 8 chiffres)

    Args:
        nom (str): Nom de l'employé (non utilisé, pour compatibilité)
        prenom (str): Prénom de l'employé (non utilisé, pour compatibilité)

    Returns:
        str: Nouveau matricule généré
    """
    return generer_prochain_matricule()
