"""
Service de calcul de dates pour les evaluations
Calcule les prochaines dates d'evaluation en fonction du niveau de competence
"""

from datetime import date, timedelta
from typing import Optional


def calculer_prochaine_evaluation(date_evaluation: date, niveau: int) -> date:
    """
    Calcule la date de la prochaine evaluation selon le niveau de competence

    Regles ACTUALISÉES:
    - Niveau 1 (Debutant): 1 mois
    - Niveau 2 (Intermediaire): 1 mois
    - Niveau 3 (Confirme): 10 ans
    - Niveau 4 (Expert/Formateur): 10 ans

    Args:
        date_evaluation (date): Date de l'evaluation actuelle
        niveau (int): Niveau de competence (1-4)

    Returns:
        date: Date de la prochaine evaluation

    Raises:
        ValueError: Si le niveau n'est pas entre 1 et 4
    """
    if niveau not in [1, 2, 3, 4]:
        raise ValueError(f"Niveau invalide: {niveau}. Doit etre entre 1 et 4.")

    # Definir les delais selon le niveau (ACTUALISÉ)
    delais_par_niveau = {
        1: 30,    # 1 mois
        2: 30,    # 1 mois
        3: 3650,  # 10 ans
        4: 3650   # 10 ans
    }

    delai_jours = delais_par_niveau[niveau]
    prochaine_date = date_evaluation + timedelta(days=delai_jours)

    # S'assurer que c'est un jour ouvrable (lundi-vendredi)
    prochaine_date = ajuster_jour_ouvrable(prochaine_date)

    return prochaine_date


def ajuster_jour_ouvrable(date_cible: date) -> date:
    """
    Ajuste une date au prochain jour ouvrable si elle tombe un weekend

    Args:
        date_cible (date): Date a ajuster

    Returns:
        date: Date ajustee au lundi si weekend
    """
    # 5 = Samedi, 6 = Dimanche
    if date_cible.weekday() == 5:  # Samedi
        return date_cible + timedelta(days=2)  # Passer au lundi
    elif date_cible.weekday() == 6:  # Dimanche
        return date_cible + timedelta(days=1)  # Passer au lundi
    else:
        return date_cible


def calculer_jours_ouvrables(date_debut: date, date_fin: date) -> int:
    """
    Calcule le nombre de jours ouvrables entre deux dates (lundi-vendredi)

    Args:
        date_debut (date): Date de debut
        date_fin (date): Date de fin

    Returns:
        int: Nombre de jours ouvrables
    """
    if date_debut > date_fin:
        return 0

    jours_ouvrables = 0
    current_date = date_debut

    while current_date <= date_fin:
        # Compter seulement les jours de semaine (0-4 = lundi-vendredi)
        if current_date.weekday() < 5:
            jours_ouvrables += 1
        current_date += timedelta(days=1)

    return jours_ouvrables


def get_delai_recommande(niveau: int) -> dict:
    """
    Retourne les informations sur le delai recommande pour un niveau

    Args:
        niveau (int): Niveau de competence (1-4)

    Returns:
        dict: Informations sur le delai (jours, mois, description)
    """
    delais = {
        1: {
            'jours': 30,
            'mois': 1,
            'annees': 0.08,
            'description': 'Debutant - Reevaluation dans 1 mois'
        },
        2: {
            'jours': 30,
            'mois': 1,
            'annees': 0.08,
            'description': 'Intermediaire - Reevaluation dans 1 mois'
        },
        3: {
            'jours': 3650,
            'mois': 120,
            'annees': 10,
            'description': 'Confirme - Reevaluation dans 10 ans'
        },
        4: {
            'jours': 3650,
            'mois': 120,
            'annees': 10,
            'description': 'Expert/Formateur - Reevaluation dans 10 ans'
        }
    }

    return delais.get(niveau, delais[2])  # Par defaut niveau 2


def calculer_retard_evaluation(prochaine_evaluation: date) -> dict:
    """
    Calcule le retard d'une evaluation par rapport a aujourd'hui

    Args:
        prochaine_evaluation (date): Date prevue de la prochaine evaluation

    Returns:
        dict: Informations sur le retard (jours, statut, urgent)
    """
    aujourd_hui = date.today()
    delta = (aujourd_hui - prochaine_evaluation).days

    if delta < 0:
        # Pas encore en retard
        jours_avant = abs(delta)
        statut = 'OK'
        urgent = jours_avant <= 30
        return {
            'jours': 0,
            'jours_avant': jours_avant,
            'statut': statut,
            'urgent': urgent,
            'message': f"Evaluation prevue dans {jours_avant} jours"
        }
    else:
        # En retard
        statut = 'RETARD'
        urgent = delta > 90  # Plus de 3 mois de retard
        return {
            'jours': delta,
            'jours_avant': 0,
            'statut': statut,
            'urgent': urgent,
            'message': f"Evaluation en retard de {delta} jours"
        }


def planifier_evaluation_maintenant(niveau_actuel: int, niveau_cible: Optional[int] = None) -> date:
    """
    Planifie une evaluation a partir d'aujourd'hui

    Args:
        niveau_actuel (int): Niveau actuel de l'operateur
        niveau_cible (int, optional): Niveau cible si different

    Returns:
        date: Date de la prochaine evaluation
    """
    niveau = niveau_cible if niveau_cible else niveau_actuel
    return calculer_prochaine_evaluation(date.today(), niveau)


def est_periode_evaluation_critique(prochaine_evaluation: date, seuil_jours: int = 7) -> bool:
    """
    Verifie si une evaluation est dans une periode critique

    Args:
        prochaine_evaluation (date): Date de la prochaine evaluation
        seuil_jours (int): Nombre de jours avant/apres pour considerer comme critique

    Returns:
        bool: True si dans la periode critique
    """
    aujourd_hui = date.today()
    delta = abs((prochaine_evaluation - aujourd_hui).days)

    # Critique si dans les N jours avant ou apres
    return delta <= seuil_jours or prochaine_evaluation < aujourd_hui
