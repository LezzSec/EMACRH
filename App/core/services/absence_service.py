# -*- coding: utf-8 -*-
"""
Service de gestion des absences et congés
Calcul des jours ouvrés, gestion des soldes, validation des demandes
"""

from datetime import datetime, timedelta, date
from core.db.configbd import get_connection


def calculer_jours_ouvres(date_debut, date_fin, demi_journee_debut='JOURNEE', demi_journee_fin='JOURNEE'):
    """
    Calcule le nombre de jours ouvrés entre deux dates (du lundi au vendredi)
    en excluant les jours fériés

    Args:
        date_debut (date): Date de début
        date_fin (date): Date de fin
        demi_journee_debut (str): 'MATIN', 'APRES_MIDI' ou 'JOURNEE'
        demi_journee_fin (str): 'MATIN', 'APRES_MIDI' ou 'JOURNEE'

    Returns:
        float: Nombre de jours ouvrés (peut être 0.5, 1.5, etc.)
    """
    if date_debut > date_fin:
        return 0

    # Récupérer les jours fériés
    jours_feries = get_jours_feries(date_debut.year, date_fin.year)

    nb_jours = 0
    current_date = date_debut

    while current_date <= date_fin:
        # Vérifier si c'est un jour ouvré (lundi-vendredi) et pas férié
        if current_date.weekday() < 5 and current_date not in jours_feries:
            if current_date == date_debut and demi_journee_debut != 'JOURNEE':
                nb_jours += 0.5
            elif current_date == date_fin and demi_journee_fin != 'JOURNEE':
                nb_jours += 0.5
            else:
                nb_jours += 1

        current_date += timedelta(days=1)

    return nb_jours


def get_jours_feries(annee_debut, annee_fin):
    """
    Récupère les jours fériés entre deux années

    Returns:
        set: Ensemble des dates fériées
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT date_ferie
            FROM jours_feries
            WHERE YEAR(date_ferie) BETWEEN %s AND %s
        """, (annee_debut, annee_fin))

        jours_feries = {row[0] for row in cur.fetchall()}
        return jours_feries

    finally:
        cur.close()
        conn.close()


def creer_demande_absence(personnel_id, type_absence_code, date_debut, date_fin,
                          demi_journee_debut='JOURNEE', demi_journee_fin='JOURNEE',
                          motif=''):
    """
    Crée une nouvelle demande d'absence

    Args:
        personnel_id (int): ID du personnel
        type_absence_code (str): Code du type d'absence (CP, RTT, etc.)
        date_debut (date): Date de début
        date_fin (date): Date de fin
        demi_journee_debut (str): MATIN, APRES_MIDI ou JOURNEE
        demi_journee_fin (str): MATIN, APRES_MIDI ou JOURNEE
        motif (str): Motif de l'absence

    Returns:
        int: ID de la demande créée
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Récupérer l'ID du type d'absence
        cur.execute("SELECT id FROM type_absence WHERE code = %s", (type_absence_code,))
        type_absence_row = cur.fetchone()

        if not type_absence_row:
            raise ValueError(f"Type d'absence '{type_absence_code}' introuvable")

        type_absence_id = type_absence_row[0]

        # Calculer le nombre de jours
        nb_jours = calculer_jours_ouvres(date_debut, date_fin, demi_journee_debut, demi_journee_fin)

        # Insérer la demande
        cur.execute("""
            INSERT INTO demande_absence
            (personnel_id, type_absence_id, date_debut, date_fin,
             demi_journee_debut, demi_journee_fin, nb_jours, motif, statut)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'EN_ATTENTE')
        """, (personnel_id, type_absence_id, date_debut, date_fin,
              demi_journee_debut, demi_journee_fin, nb_jours, motif))

        demande_id = cur.lastrowid
        conn.commit()

        return demande_id

    finally:
        cur.close()
        conn.close()


def valider_demande(demande_id, validateur_id, valide=True, commentaire=''):
    """
    Valide ou refuse une demande d'absence

    Args:
        demande_id (int): ID de la demande
        validateur_id (int): ID du validateur
        valide (bool): True pour valider, False pour refuser
        commentaire (str): Commentaire de validation
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        statut = 'VALIDEE' if valide else 'REFUSEE'

        cur.execute("""
            UPDATE demande_absence
            SET statut = %s,
                validateur_id = %s,
                date_validation = NOW(),
                commentaire_validation = %s
            WHERE id = %s
        """, (statut, validateur_id, commentaire, demande_id))

        # Si validée et type décompté, mettre à jour les soldes
        if valide:
            cur.execute("""
                SELECT da.personnel_id, da.nb_jours, ta.code, YEAR(da.date_debut)
                FROM demande_absence da
                JOIN type_absence ta ON da.type_absence_id = ta.id
                WHERE da.id = %s AND ta.decompte_solde = TRUE
            """, (demande_id,))

            row = cur.fetchone()
            if row:
                personnel_id, nb_jours, type_code, annee = row
                decompter_solde(personnel_id, annee, type_code, nb_jours)

        conn.commit()

    finally:
        cur.close()
        conn.close()


def decompter_solde(personnel_id, annee, type_code, nb_jours):
    """
    Décompte le solde de congés/RTT

    Args:
        personnel_id (int): ID du personnel
        annee (int): Année
        type_code (str): CP ou RTT
        nb_jours (float): Nombre de jours à décompter
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Vérifier si le solde existe
        cur.execute("""
            SELECT id FROM solde_conges
            WHERE personnel_id = %s AND annee = %s
        """, (personnel_id, annee))

        if not cur.fetchone():
            # Créer le solde si inexistant
            cur.execute("""
                INSERT INTO solde_conges (personnel_id, annee)
                VALUES (%s, %s)
            """, (personnel_id, annee))

        # Décompter selon le type
        if type_code == 'CP':
            cur.execute("""
                UPDATE solde_conges
                SET cp_pris = cp_pris + %s
                WHERE personnel_id = %s AND annee = %s
            """, (nb_jours, personnel_id, annee))
        elif type_code == 'RTT':
            cur.execute("""
                UPDATE solde_conges
                SET rtt_pris = rtt_pris + %s
                WHERE personnel_id = %s AND annee = %s
            """, (nb_jours, personnel_id, annee))

        conn.commit()

    finally:
        cur.close()
        conn.close()


def get_solde_conges(personnel_id, annee):
    """
    Récupère le solde de congés d'un personnel

    Returns:
        dict: {cp_restant, rtt_restant, cp_acquis, etc.}
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT
                cp_acquis,
                cp_n_1,
                cp_pris,
                (cp_acquis + cp_n_1 - cp_pris) as cp_restant,
                rtt_acquis,
                rtt_pris,
                (rtt_acquis - rtt_pris) as rtt_restant
            FROM solde_conges
            WHERE personnel_id = %s AND annee = %s
        """, (personnel_id, annee))

        solde = cur.fetchone()

        if not solde:
            # Retourner un solde vide
            return {
                'cp_acquis': 0,
                'cp_n_1': 0,
                'cp_pris': 0,
                'cp_restant': 0,
                'rtt_acquis': 0,
                'rtt_pris': 0,
                'rtt_restant': 0
            }

        return solde

    finally:
        cur.close()
        conn.close()


def get_demandes_personnel(personnel_id, annee=None, statut=None):
    """
    Récupère les demandes d'absence d'un personnel

    Args:
        personnel_id (int): ID du personnel
        annee (int, optional): Filtrer par année
        statut (str, optional): Filtrer par statut

    Returns:
        list: Liste des demandes
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT
                da.id,
                da.date_debut,
                da.date_fin,
                da.demi_journee_debut,
                da.demi_journee_fin,
                da.nb_jours,
                da.motif,
                da.statut,
                ta.code as type_code,
                ta.libelle as type_libelle,
                ta.couleur,
                CONCAT(v.prenom, ' ', v.nom) as validateur,
                da.date_validation,
                da.commentaire_validation
            FROM demande_absence da
            JOIN type_absence ta ON da.type_absence_id = ta.id
            LEFT JOIN personnel v ON da.validateur_id = v.id
            WHERE da.personnel_id = %s
        """

        params = [personnel_id]

        if annee:
            query += " AND YEAR(da.date_debut) = %s"
            params.append(annee)

        if statut:
            query += " AND da.statut = %s"
            params.append(statut)

        query += " ORDER BY da.date_debut DESC"

        cur.execute(query, tuple(params))
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def get_absences_periode(date_debut, date_fin, statut='VALIDEE'):
    """
    Récupère toutes les absences sur une période (pour le calendrier)

    Args:
        date_debut (date): Date de début
        date_fin (date): Date de fin
        statut (str): Filtrer par statut

    Returns:
        list: Liste des absences
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT
                da.id,
                da.personnel_id,
                CONCAT(p.prenom, ' ', p.nom) as nom_complet,
                p.matricule,
                da.date_debut,
                da.date_fin,
                da.nb_jours,
                ta.code as type_code,
                ta.libelle as type_libelle,
                ta.couleur
            FROM demande_absence da
            JOIN personnel p ON da.personnel_id = p.id
            JOIN type_absence ta ON da.type_absence_id = ta.id
            WHERE p.statut = 'ACTIF'
            AND da.statut = %s
            AND da.date_debut <= %s
            AND da.date_fin >= %s
            ORDER BY da.date_debut, p.nom
        """, (statut, date_fin, date_debut))

        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def initialiser_soldes_annee(annee, cp_standard=25, rtt_standard=10):
    """
    Initialise les soldes de congés pour tous les personnel actifs

    Args:
        annee (int): Année
        cp_standard (float): CP acquis par défaut
        rtt_standard (float): RTT acquis par défaut
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Récupérer tous les personnel actifs
        cur.execute("SELECT id FROM personnel WHERE statut = 'ACTIF'")
        personnel_ids = [row[0] for row in cur.fetchall()]

        for personnel_id in personnel_ids:
            # Vérifier si le solde existe déjà
            cur.execute("""
                SELECT id FROM solde_conges
                WHERE personnel_id = %s AND annee = %s
            """, (personnel_id, annee))

            if not cur.fetchone():
                # Créer le solde
                cur.execute("""
                    INSERT INTO solde_conges
                    (personnel_id, annee, cp_acquis, rtt_acquis)
                    VALUES (%s, %s, %s, %s)
                """, (personnel_id, annee, cp_standard, rtt_standard))

        conn.commit()
        return len(personnel_ids)

    finally:
        cur.close()
        conn.close()


def get_types_absence():
    """Récupère tous les types d'absence actifs"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT id, code, libelle, decompte_solde, couleur
            FROM type_absence
            WHERE actif = TRUE
            ORDER BY code
        """)
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


# ========================= ALIASES POUR COMPATIBILITÉ =========================

def get_absences_actuelles():
    """
    Alias pour get_absences_periode()
    Récupère les absences en cours (période de 30 jours)

    Returns:
        Liste des absences actuelles
    """
    from datetime import date, timedelta
    date_debut = date.today() - timedelta(days=7)  # 7 jours avant
    date_fin = date.today() + timedelta(days=30)   # 30 jours après
    return get_absences_periode(date_debut, date_fin)
