# -*- coding: utf-8 -*-
"""
Service de génération automatique de matricules
Génère des matricules au format M000XXX pour le personnel de production
"""

from infrastructure.db.query_executor import QueryExecutor


def generer_prochain_matricule():
    """
    Génère le prochain matricule disponible au format M000XXX

    IMPORTANT: Cette fonction doit être appelée juste avant l'insertion
    en base de données. Si le matricule n'est pas inséré immédiatement,
    des appels successifs retourneront le même matricule.

    Returns:
        str: Le prochain matricule (ex: 'M000101')

    Raises:
        Exception: Si impossible de se connecter à la base de données
    """
    dernier_numero = QueryExecutor.fetch_scalar(
        "SELECT MAX(CAST(SUBSTRING(matricule, 2) AS UNSIGNED)) FROM personnel WHERE matricule REGEXP '^M[0-9]{6}$'",
        default=0
    )
    prochain_numero = (int(dernier_numero) if dernier_numero else 0) + 1
    return f"M{prochain_numero:06d}"


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
    Génère un nouveau matricule (format M000XXX)

    Args:
        nom (str): Nom de l'employé (non utilisé, pour compatibilité)
        prenom (str): Prénom de l'employé (non utilisé, pour compatibilité)

    Returns:
        str: Nouveau matricule généré
    """
    return generer_prochain_matricule()
