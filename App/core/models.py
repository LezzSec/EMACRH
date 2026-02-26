# -*- coding: utf-8 -*-
"""
Module de modèles de données (DTOs) pour EMAC.

Ce module définit les dataclasses représentant les entités métier.
Avantages par rapport aux dictionnaires bruts :
- Typage fort (autocomplétion IDE, détection d'erreurs)
- Validation à la construction
- Documentation intégrée
- Immutabilité optionnelle (frozen=True)

Usage:
    from core.models import Personnel, Contrat, Poste

    # Création depuis un dict (ex: résultat SQL)
    personnel = Personnel.from_dict(row)

    # Accès typé
    print(personnel.nom_complet)  # "DUPONT Jean"

    # Conversion en dict (pour JSON, templates, etc.)
    data = personnel.to_dict()
"""

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from enum import Enum


# ===========================
# Enums
# ===========================

class StatutPersonnel(Enum):
    """Statut d'un membre du personnel"""
    ACTIF = "ACTIF"
    INACTIF = "INACTIF"


class TypeContrat(Enum):
    """Types de contrats possibles (alignés avec l'enum DB)"""
    CDI = "CDI"
    CDD = "CDD"
    STAGIAIRE = "Stagiaire"
    APPRENTISSAGE = "Apprentissage"
    INTERIMAIRE = "Interimaire"
    MISE_A_DISPOSITION_GE = "Mise a disposition GE"
    ETRANGER_HORS_UE = "Etranger hors UE"
    TEMPS_PARTIEL = "Temps partiel"
    CIFRE = "CIFRE"
    AVENANT_CONTRAT = "Avenant contrat"


class NiveauPolyvalence(Enum):
    """Niveaux de compétence (1-4)"""
    APPRENTISSAGE = 1      # En formation
    AUTONOME = 2           # Peut travailler seul
    CONFIRME = 3           # Maîtrise complète
    EXPERT_FORMATEUR = 4   # Peut former les autres


class TypeAbsence(Enum):
    """Types d'absence"""
    CONGE_PAYE = "CP"
    RTT = "RTT"
    MALADIE = "MALADIE"
    ACCIDENT_TRAVAIL = "AT"
    FORMATION = "FORMATION"
    AUTRE = "AUTRE"


class StatutAbsence(Enum):
    """Statut d'une demande d'absence"""
    EN_ATTENTE = "EN_ATTENTE"
    VALIDEE = "VALIDEE"
    REFUSEE = "REFUSEE"


class UrgenceAlerte(Enum):
    """Niveau d'urgence d'une alerte RH"""
    CRITIQUE = "CRITIQUE"      # Rouge - action immédiate requise
    AVERTISSEMENT = "AVERTISSEMENT"  # Orange - attention requise
    INFO = "INFO"              # Bleu - information


# ===========================
# Base Mixin
# ===========================

class ModelMixin:
    """Mixin fournissant les méthodes communes aux modèles"""

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le modèle en dictionnaire"""
        result = asdict(self)
        # Convertir les enums en valeurs
        for key, value in result.items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, (date, datetime)):
                result[key] = value.isoformat() if value else None
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Crée une instance depuis un dictionnaire.
        Gère les clés manquantes et les conversions de type.
        """
        if data is None:
            return None

        # Filtrer uniquement les clés valides pour ce dataclass
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {}

        for key, value in data.items():
            if key in valid_keys:
                # Conversion des types si nécessaire
                field_type = cls.__dataclass_fields__[key].type

                # Gérer Optional[X] → extraire X
                if hasattr(field_type, '__origin__') and field_type.__origin__ is type(None):
                    pass  # Keep as is
                elif hasattr(field_type, '__args__'):
                    # C'est un Optional ou Union
                    inner_types = [t for t in field_type.__args__ if t is not type(None)]
                    if inner_types:
                        field_type = inner_types[0]

                # Conversion date string → date
                if field_type == date and isinstance(value, str):
                    try:
                        value = datetime.strptime(value, "%Y-%m-%d").date()
                    except ValueError:
                        pass
                elif field_type == datetime and isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value)
                    except ValueError:
                        pass

                filtered_data[key] = value

        return cls(**filtered_data)


# ===========================
# Personnel / Opérateur
# ===========================

@dataclass
class Personnel(ModelMixin):
    """
    Représente un membre du personnel (opérateur).

    Correspond à la table 'personnel'.
    Les infos étendues (sexe, date_entree, email, telephone) sont dans personnel_infos.
    """
    id: int
    nom: str
    prenom: str
    statut: str = "ACTIF"  # ACTIF ou INACTIF
    matricule: Optional[str] = None
    service_id: Optional[int] = None
    numposte: Optional[str] = None
    # Champs de jointure avec personnel_infos (optionnels)
    sexe: Optional[str] = None
    date_entree: Optional[date] = None
    email: Optional[str] = None
    telephone: Optional[str] = None

    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet formaté (NOM Prénom)"""
        return f"{self.nom.upper()} {self.prenom.capitalize()}"

    @property
    def initiales(self) -> str:
        """Retourne les initiales (ex: 'JD' pour Jean Dupont)"""
        return f"{self.prenom[0].upper()}{self.nom[0].upper()}" if self.prenom and self.nom else ""

    @property
    def est_actif(self) -> bool:
        """Vérifie si le personnel est actif"""
        return self.statut == "ACTIF"

    def __str__(self) -> str:
        return self.nom_complet


@dataclass
class PersonnelResume(ModelMixin):
    """
    Version légère de Personnel pour les listes/combos.
    Utilisé quand on n'a pas besoin de tous les détails.
    """
    id: int
    nom: str
    prenom: str
    matricule: Optional[str] = None

    @property
    def nom_complet(self) -> str:
        return f"{self.nom.upper()} {self.prenom.capitalize()}"

    @property
    def label(self) -> str:
        """Label pour affichage dans combo/liste"""
        return self.nom_complet


# ===========================
# Poste / Atelier
# ===========================

@dataclass
class Atelier(ModelMixin):
    """Représente un atelier (groupe de postes). Table: atelier (id, nom)"""
    id: int
    nom: str


@dataclass
class Poste(ModelMixin):
    """
    Représente un poste de travail.

    Correspond à la table 'postes' (id, poste_code, besoins_postes, visible, atelier_id).
    """
    id: int
    poste_code: str
    atelier_id: Optional[int] = None
    atelier_nom: Optional[str] = None  # Jointure fréquente
    visible: bool = True
    besoins_postes: int = 0

    @property
    def label(self) -> str:
        """Label pour affichage"""
        return self.poste_code


# ===========================
# Contrat
# ===========================

@dataclass
class Contrat(ModelMixin):
    """
    Représente un contrat de travail.

    Correspond à la table 'contrat'.
    """
    id: int
    personnel_id: int
    type_contrat: str  # CDI, CDD, Interimaire, etc.
    date_debut: date
    date_fin: Optional[date] = None
    etp: float = 1.0  # Equivalent Temps Plein (0-1)
    categorie: Optional[str] = None
    coefficient: Optional[int] = None
    actif: bool = True
    motif: Optional[str] = None
    date_sortie: Optional[date] = None
    motif_sortie: Optional[str] = None

    # Champs de jointure (optionnels)
    personnel_nom: Optional[str] = None
    personnel_prenom: Optional[str] = None

    @property
    def est_cdi(self) -> bool:
        """Vérifie si c'est un CDI"""
        return self.type_contrat == "CDI"

    @property
    def est_termine(self) -> bool:
        """Vérifie si le contrat est terminé"""
        if self.date_fin is None:
            return False
        return self.date_fin < date.today()

    @property
    def jours_restants(self) -> Optional[int]:
        """Nombre de jours avant la fin du contrat (None si CDI)"""
        if self.date_fin is None:
            return None
        delta = self.date_fin - date.today()
        return delta.days

    @property
    def est_urgent(self) -> bool:
        """Contrat expirant dans moins de 7 jours"""
        jours = self.jours_restants
        return jours is not None and 0 <= jours < 7

    @property
    def personnel_nom_complet(self) -> Optional[str]:
        """Nom complet du personnel (si jointure)"""
        if self.personnel_nom and self.personnel_prenom:
            return f"{self.personnel_nom.upper()} {self.personnel_prenom.capitalize()}"
        return None


# ===========================
# Polyvalence (Compétences/Évaluations)
# ===========================

@dataclass
class Polyvalence(ModelMixin):
    """
    Représente une compétence d'un opérateur sur un poste.

    Correspond à la table 'polyvalence'.
    """
    id: int
    operateur_id: int
    poste_id: int
    niveau: int  # 1-4
    date_evaluation: Optional[date] = None
    prochaine_evaluation: Optional[date] = None

    # Champs de jointure (optionnels)
    operateur_nom: Optional[str] = None
    operateur_prenom: Optional[str] = None
    poste_code: Optional[str] = None
    poste_nom: Optional[str] = None

    @property
    def niveau_label(self) -> str:
        """Label du niveau de compétence"""
        labels = {
            1: "Apprentissage",
            2: "Autonome",
            3: "Confirmé",
            4: "Expert/Formateur"
        }
        return labels.get(self.niveau, f"Niveau {self.niveau}")

    @property
    def est_en_retard(self) -> bool:
        """Évaluation en retard"""
        if self.prochaine_evaluation is None:
            return False
        return self.prochaine_evaluation < date.today()

    @property
    def jours_retard(self) -> Optional[int]:
        """Nombre de jours de retard (négatif si à venir)"""
        if self.prochaine_evaluation is None:
            return None
        delta = date.today() - self.prochaine_evaluation
        return delta.days

    @property
    def operateur_nom_complet(self) -> Optional[str]:
        """Nom complet de l'opérateur (si jointure)"""
        if self.operateur_nom and self.operateur_prenom:
            return f"{self.operateur_nom.upper()} {self.operateur_prenom.capitalize()}"
        return None


# ===========================
# Absence
# ===========================

@dataclass
class Absence(ModelMixin):
    """
    Représente une demande d'absence.

    Correspond à la table 'demande_absence'.
    """
    id: int
    personnel_id: int
    type_absence_id: int
    date_debut: date
    date_fin: date
    nb_jours: float = 1.0
    statut: str = "EN_ATTENTE"  # EN_ATTENTE, VALIDEE, REFUSEE, ANNULEE
    motif: Optional[str] = None
    demi_journee_debut: str = "JOURNEE"  # MATIN, APRES_MIDI, JOURNEE
    demi_journee_fin: str = "JOURNEE"
    validateur_id: Optional[int] = None
    date_validation: Optional[datetime] = None
    commentaire_validation: Optional[str] = None

    # Champs de jointure
    operateur_nom: Optional[str] = None
    operateur_prenom: Optional[str] = None
    type_absence_libelle: Optional[str] = None

    @property
    def duree_jours(self) -> float:
        """Durée en jours"""
        return self.nb_jours

    @property
    def est_en_cours(self) -> bool:
        """L'absence est-elle en cours aujourd'hui?"""
        today = date.today()
        return self.date_debut <= today <= self.date_fin and self.statut == "VALIDEE"

    @property
    def est_future(self) -> bool:
        """L'absence est-elle dans le futur?"""
        return self.date_debut > date.today()


# ===========================
# Formation
# ===========================

@dataclass
class Formation(ModelMixin):
    """
    Représente une formation suivie par un employé.

    Correspond à la table 'formation'.
    """
    id: int
    operateur_id: int
    intitule: str
    date_debut: date
    date_fin: Optional[date] = None
    organisme: Optional[str] = None
    duree_heures: Optional[float] = None
    statut: str = "Planifiee"  # Planifiee, En cours, Terminee, Annulee
    certificat_obtenu: bool = False
    commentaire: Optional[str] = None
    cout: Optional[float] = None
    document_id: Optional[int] = None

    # Champs de jointure
    operateur_nom: Optional[str] = None
    operateur_prenom: Optional[str] = None


# ===========================
# Évaluation (résumé pour dashboard)
# ===========================

@dataclass
class EvaluationResume(ModelMixin):
    """
    Résumé d'une évaluation pour affichage dashboard.
    Combine Personnel + Poste + Polyvalence.
    """
    polyvalence_id: int
    operateur_id: int
    operateur_nom: str
    operateur_prenom: str
    poste_code: str
    poste_nom: Optional[str]
    niveau: int
    prochaine_evaluation: date
    jours_retard: int = 0

    @property
    def operateur_nom_complet(self) -> str:
        return f"{self.operateur_nom.upper()} {self.operateur_prenom.capitalize()}"

    @property
    def est_en_retard(self) -> bool:
        return self.jours_retard > 0

    @property
    def label_poste(self) -> str:
        if self.poste_nom:
            return f"{self.poste_code} - {self.poste_nom}"
        return self.poste_code


# ===========================
# Statistiques (pour dashboards)
# ===========================

@dataclass
class StatistiquesContrats(ModelMixin):
    """Statistiques sur les contrats"""
    total: int = 0
    cdi: int = 0
    cdd: int = 0
    interim: int = 0
    expirant_7j: int = 0
    expirant_30j: int = 0


@dataclass
class StatistiquesEvaluations(ModelMixin):
    """Statistiques sur les évaluations"""
    total: int = 0
    en_retard: int = 0
    a_venir_7j: int = 0
    a_venir_30j: int = 0


# ===========================
# Alertes RH
# ===========================

@dataclass
class Alert(ModelMixin):
    """
    Représente une alerte RH (contrat expirant, personnel sans affectation, etc.)

    Utilisé par le module de gestion des alertes RH.
    """
    id: int
    categorie: str  # "CONTRAT" ou "PERSONNEL"
    type_alerte: str  # Type spécifique (CONTRAT_EXPIRE, SANS_COMPETENCES, etc.)
    urgence: str  # CRITIQUE, AVERTISSEMENT, INFO
    titre: str
    description: str
    personnel_id: Optional[int] = None
    personnel_nom: Optional[str] = None
    personnel_prenom: Optional[str] = None
    date_alerte: Optional[date] = None
    date_echeance: Optional[date] = None
    jours_restants: Optional[int] = None  # Négatif si dépassé
    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def personnel_nom_complet(self) -> str:
        """Nom complet du personnel concerné"""
        if self.personnel_nom and self.personnel_prenom:
            return f"{self.personnel_nom.upper()} {self.personnel_prenom.capitalize()}"
        return ""

    @property
    def urgence_ordre(self) -> int:
        """Ordre de tri par urgence (0=plus urgent)"""
        return {'CRITIQUE': 0, 'AVERTISSEMENT': 1, 'INFO': 2}.get(self.urgence, 3)

    @property
    def est_critique(self) -> bool:
        return self.urgence == "CRITIQUE"

    @property
    def est_avertissement(self) -> bool:
        return self.urgence == "AVERTISSEMENT"


@dataclass
class StatistiquesAlertes(ModelMixin):
    """Statistiques sur les alertes RH"""
    total: int = 0
    critiques: int = 0
    avertissements: int = 0
    infos: int = 0


# ===========================
# Factory helpers
# ===========================

def personnel_from_row(row: Dict) -> Personnel:
    """Crée un Personnel depuis une ligne SQL (dict)"""
    return Personnel.from_dict(row)


def contrat_from_row(row: Dict) -> Contrat:
    """Crée un Contrat depuis une ligne SQL (dict)"""
    return Contrat.from_dict(row)


def poste_from_row(row: Dict) -> Poste:
    """Crée un Poste depuis une ligne SQL (dict)"""
    return Poste.from_dict(row)


def polyvalence_from_row(row: Dict) -> Polyvalence:
    """Crée une Polyvalence depuis une ligne SQL (dict)"""
    return Polyvalence.from_dict(row)


# ===========================
# Exports
# ===========================

__all__ = [
    # Enums
    'StatutPersonnel',
    'TypeContrat',
    'NiveauPolyvalence',
    'TypeAbsence',
    'StatutAbsence',
    'UrgenceAlerte',

    # Modèles principaux
    'Personnel',
    'PersonnelResume',
    'Atelier',
    'Poste',
    'Contrat',
    'Polyvalence',
    'Absence',
    'Formation',

    # Modèles résumés
    'EvaluationResume',
    'StatistiquesContrats',
    'StatistiquesEvaluations',

    # Alertes RH
    'Alert',
    'StatistiquesAlertes',

    # Factory helpers
    'personnel_from_row',
    'contrat_from_row',
    'poste_from_row',
    'polyvalence_from_row',
]
