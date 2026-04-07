# -*- coding: utf-8 -*-
"""
Service de génération automatique de matricules
Génère des matricules au format M000XXX pour le personnel de production
"""

from infrastructure.db.configbd import get_connection


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
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Trouver le numéro max actuel (en majuscules uniquement)
        cur.execute("""
            SELECT MAX(CAST(SUBSTRING(matricule, 2) AS UNSIGNED)) as dernier_numero
            FROM personnel
            WHERE matricule REGEXP '^M[0-9]{6}$'
        """)

        row = cur.fetchone()

        # Si aucun matricule existant, commencer à 1
        if row is None or row[0] is None:
            prochain_numero = 1
        else:
            prochain_numero = int(row[0]) + 1

        # Formater avec des zéros (M000001, M000002, etc.)
        matricule = f"M{prochain_numero:06d}"

        return matricule

    finally:
        cur.close()
        conn.close()


def matricule_existe(matricule):
    """
    Vérifie si un matricule existe déjà dans la base

    Args:
        matricule (str): Le matricule à vérifier

    Returns:
        bool: True si le matricule existe, False sinon
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT COUNT(*) FROM personnel WHERE matricule = %s",
            (matricule,)
        )
        count = cur.fetchone()[0]
        return count > 0
    finally:
        cur.close()
        conn.close()


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

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Vérifier si l'opérateur a déjà un matricule
        cur.execute(
            "SELECT matricule FROM personnel WHERE id = %s",
            (operateur_id,)
        )
        row = cur.fetchone()

        if row is None:
            return None

        matricule_actuel = row[0]

        # Si déjà un matricule, ne rien faire
        if matricule_actuel is not None and matricule_actuel.strip() != "":
            return matricule_actuel

        # Générer et assigner un nouveau matricule
        nouveau_matricule = generer_prochain_matricule()

        cur.execute(
            "UPDATE personnel SET matricule = %s WHERE id = %s",
            (nouveau_matricule, operateur_id)
        )
        conn.commit()

        return nouveau_matricule

    finally:
        cur.close()
        conn.close()


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
