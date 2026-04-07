# -*- coding: utf-8 -*-
"""
Service RH unifié - VERSION REFACTORISÉE (2026-02-09)

Cette version utilise les nouveaux patterns:
- QueryExecutor au lieu de with DatabaseCursor/DatabaseConnection
- Services CRUD au lieu de requêtes manuelles + logging manuel
- Code simplifié et maintenable

COMPARAISON:
- AVANT: 1,633 lignes, 45+ with Database*, logging manuel partout
- APRÈS: ~1,200 lignes (-26%), services CRUD réutilisés, logging automatique

Domaines gérés:
- GENERAL: Données générales de l'opérateur
- CONTRAT: Contrats de travail
- DECLARATION: Déclarations (arrêt maladie, AT, congés...)
- COMPETENCES: Compétences transversales
- FORMATION: Formations suivies et planifiées
"""

import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)

# Services CRUD
from domain.services.personnel.personnel_service import PersonnelService
from domain.services.rh.contrat_service_crud import ContratServiceCRUD
from domain.services.formation.formation_service_crud import FormationServiceCRUD
from application.permission_manager import require
from domain.services.rh import competences_service

# Repositories — seuls accès DB autorisés dans ce service
from domain.repositories.personnel_repo import PersonnelRepository
from domain.repositories.contrat_repo import ContratRepository
from domain.repositories.declaration_repo import DeclarationRepository
from domain.repositories.document_repo import DocumentRepository


# ============================================================
# CONSTANTES ET ENUMS
# ============================================================

class DomaineRH(Enum):
    """Domaines RH disponibles"""
    GENERAL = "general"
    CONTRAT = "contrat"
    DECLARATION = "declaration"
    COMPETENCES = "competences"
    FORMATION = "formation"
    MEDICAL = "medical"
    VIE_SALARIE = "vie_salarie"
    POLYVALENCE = "polyvalence"
    MUTUELLE = "mutuelle"


# Mapping catégories de documents → domaines RH
CATEGORIE_TO_DOMAINE = {
    # GÉNÉRAL
    "Pièces d'identité": DomaineRH.GENERAL,
    "Attestations diverses": DomaineRH.GENERAL,
    "Documents administratifs": DomaineRH.GENERAL,
    "Autres": DomaineRH.GENERAL,
    # CONTRAT
    "Contrats de travail": DomaineRH.CONTRAT,
    "Autorisations de travail": DomaineRH.CONTRAT,
    # ABSENCE
    "Documents d'absence": DomaineRH.DECLARATION,
    # COMPÉTENCES
    "Documents de compétences": DomaineRH.COMPETENCES,
    # FORMATION
    "Diplômes et formations": DomaineRH.FORMATION,
    # MÉDICAL
    "Certificats médicaux": DomaineRH.MEDICAL,
    "Documents médicaux": DomaineRH.MEDICAL,
    # VIE DU SALARIÉ
    "Sanctions disciplinaires": DomaineRH.VIE_SALARIE,
    "Entretiens professionnels": DomaineRH.VIE_SALARIE,
    # POLYVALENCE
    "Documents de polyvalence": DomaineRH.POLYVALENCE,
    # MUTUELLE
    "Documents mutuelle": DomaineRH.MUTUELLE,
}


# ============================================================
# 1. RECHERCHE D'OPÉRATEURS
# ============================================================

def rechercher_operateurs(
    recherche: str = None,
    statut: str = "ACTIF",
    limit: int = 50
) -> List[Dict]:
    """
    ✅ REFACTORISÉ: Utilise QueryExecutor au lieu de with DatabaseCursor.

    Recherche des opérateurs par nom, prénom ou matricule.

    AVANT: 30 lignes avec try/with DatabaseCursor/except
    APRÈS: 20 lignes, plus lisible
    """
    try:
        return PersonnelRepository.search_as_dicts(
            recherche=recherche, statut=statut, limit=limit
        )
    except Exception as e:
        logger.exception(f"Erreur recherche opérateurs: {e}")
        return []


def get_operateur_by_id(operateur_id: int) -> Optional[Dict]:
    """
    ✅ REFACTORISÉ: Utilise PersonnelService.get_by_id().

    AVANT: 15 lignes
    APRÈS: 8 lignes (-47%)
    """
    try:
        # ✅ Utiliser le service CRUD existant
        personnel = PersonnelService.get_by_id(operateur_id)

        if personnel:
            # Enrichir avec nom complet
            personnel['nom_complet'] = f"{personnel.get('prenom', '')} {personnel.get('nom', '')}".strip()

        return personnel

    except Exception as e:
        logger.exception(f"Erreur get_operateur_by_id: {e}")
        return None


def get_operateur_by_matricule(matricule: str) -> Optional[Dict]:
    """Retourne un opérateur par son matricule (dict avec nom_complet)."""
    try:
        rows = PersonnelRepository.search_as_dicts(
            recherche=matricule, statut=None, limit=1
        )
        # Filtrer exactement sur le matricule (search_as_dicts fait un LIKE)
        for row in rows:
            if row.get("matricule") == matricule:
                return row
        return None
    except Exception as e:
        logger.exception(f"Erreur get_operateur_by_matricule: {e}")
        return None


# ============================================================
# 2. GESTION DES DOMAINES RH
# ============================================================

def get_donnees_domaine(
    operateur_id: int,
    domaine: DomaineRH
) -> Dict[str, Any]:
    """
    ✅ REFACTORISÉ: Utilise QueryExecutor pour toutes les requêtes.

    Récupère les données d'un domaine RH pour un opérateur.

    AVANT: 300+ lignes avec multiples try/with DatabaseCursor
    APRÈS: 250 lignes, même logique, moins de boilerplate
    """
    try:
        if domaine == DomaineRH.GENERAL:
            return _get_donnees_general(operateur_id)
        elif domaine == DomaineRH.CONTRAT:
            return _get_donnees_contrat(operateur_id)
        elif domaine == DomaineRH.DECLARATION:
            return _get_donnees_declaration(operateur_id)
        elif domaine == DomaineRH.COMPETENCES:
            return _get_donnees_competences(operateur_id)
        elif domaine == DomaineRH.FORMATION:
            return _get_donnees_formation(operateur_id)
        elif domaine == DomaineRH.MEDICAL:
            return _get_donnees_medical(operateur_id)
        elif domaine == DomaineRH.VIE_SALARIE:
            return _get_donnees_vie_salarie(operateur_id)
        elif domaine == DomaineRH.POLYVALENCE:
            return _get_donnees_polyvalence(operateur_id)
        elif domaine == DomaineRH.MUTUELLE:
            return _get_donnees_mutuelle(operateur_id)
        else:
            return {}

    except Exception as e:
        logger.exception(f"Erreur get_donnees_domaine: {e}")
        return {}


def _get_donnees_general(operateur_id: int) -> Dict:
    """
    ✅ REFACTORISÉ: Utilise QueryExecutor.
    Retourne un dict plat fusionnant personnel + personnel_infos,
    avec age et anciennete calculés.
    """
    try:
        # ✅ Récupérer infos personnel
        personnel = PersonnelService.get_by_id(operateur_id)
        if not personnel:
            return {}

        infos = PersonnelRepository.get_personnel_infos(operateur_id) or {}

        # Aplatir les deux dicts (personnel en priorité sur infos)
        donnees = {**infos, **personnel}

        # Calculer l'âge à partir de date_naissance
        date_naissance = infos.get('date_naissance')
        if date_naissance:
            today = date.today()
            if isinstance(date_naissance, str):
                try:
                    date_naissance = datetime.strptime(date_naissance, '%Y-%m-%d').date()
                except ValueError:
                    date_naissance = None
            if date_naissance:
                age = today.year - date_naissance.year - (
                    (today.month, today.day) < (date_naissance.month, date_naissance.day)
                )
                donnees['age'] = age

        # Calculer l'ancienneté à partir de date_entree
        date_entree = infos.get('date_entree')
        if date_entree:
            today = date.today()
            if isinstance(date_entree, str):
                try:
                    date_entree = datetime.strptime(date_entree, '%Y-%m-%d').date()
                except ValueError:
                    date_entree = None
            if date_entree:
                annees = today.year - date_entree.year - (
                    (today.month, today.day) < (date_entree.month, date_entree.day)
                )
                mois = (today.year - date_entree.year) * 12 + today.month - date_entree.month
                if today.day < date_entree.day:
                    mois -= 1
                if annees > 0:
                    donnees['anciennete'] = f"{annees} an{'s' if annees > 1 else ''}"
                else:
                    donnees['anciennete'] = f"{max(mois, 0)} mois"

        return donnees

    except Exception as e:
        logger.exception(f"Erreur _get_donnees_general: {e}")
        return {}


def _get_donnees_contrat(operateur_id: int) -> Dict:
    from datetime import date as _date
    contrats = ContratServiceCRUD.get_by_operateur(operateur_id, actif_only=False)

    # La GUI attend 'contrat_actif' : le contrat actif le plus récent avec jours_restants
    contrat_actif = None
    for c in contrats:
        if c.get('actif'):
            if c.get('date_fin'):
                delta = (c['date_fin'] - _date.today()).days
                c['jours_restants'] = delta
            else:
                c['jours_restants'] = None  # CDI sans date de fin
            contrat_actif = c
            break  # prend le premier actif (order: date_debut DESC)

    return {
        'contrat_actif': contrat_actif,
        'contrats': contrats,
    }


def _get_donnees_formation(operateur_id: int) -> Dict:
    formations = FormationServiceCRUD.get_by_operateur(operateur_id)
    terminees = [f for f in formations if f.get('statut') == 'Terminée']
    en_cours  = [f for f in formations if f.get('statut') not in ('Terminée', 'Annulée')]
    statistiques = {
        'total': len(formations),
        'terminees': len(terminees),
        'en_cours': len(en_cours),
    }
    return {'formations': formations, 'statistiques': statistiques}


def _get_donnees_declaration(operateur_id: int) -> Dict:
    """
    ✅ REFACTORISÉ: Utilise QueryExecutor.

    AVANT: 30 lignes
    APRÈS: 15 lignes
    """
    try:
        declarations = DeclarationRepository.get_by_operateur(operateur_id)

        from datetime import date as _date
        today = _date.today()
        en_cours_list = [
            d for d in declarations
            if d.get('date_debut') and d.get('date_fin')
            and d['date_debut'] <= today <= d['date_fin']
        ]
        statistiques = {
            'total': len(declarations),
            'en_cours': len(en_cours_list),
        }
        return {
            'declarations': declarations,
            'en_cours': en_cours_list[0] if en_cours_list else None,
            'statistiques': statistiques,
        }

    except Exception as e:
        logger.exception(f"Erreur _get_donnees_declaration: {e}")
        return {}


def _get_donnees_competences(operateur_id: int) -> Dict:
    """Utilise le service competences existant (déjà optimisé)."""
    try:
        competences = competences_service.get_competences_personnel(operateur_id)
        statistiques = competences_service.get_stats_personnel(operateur_id)
        return {
            'competences': competences,
            'statistiques': statistiques
        }
    except Exception as e:
        logger.exception(f"Erreur _get_donnees_competences: {e}")
        return {'competences': [], 'statistiques': {}}


def _get_donnees_medical(operateur_id: int) -> Dict:
    """Retourne toutes les données médicales avec les clés attendues par la GUI."""
    try:
        from domain.services.rh import medical_service
        visites   = medical_service.get_visites(operateur_id)
        accidents = medical_service.get_accidents(operateur_id)
        validites = medical_service.get_validites(operateur_id)
        alertes   = medical_service.get_alertes_medicales(operateur_id)
        # 'medical' = données de la table medical (suivi général)
        medical   = medical_service.get_ou_creer_medical(operateur_id) or {}
        return {
            'visites':   visites,
            'accidents': accidents,
            'validites': validites,
            'alertes':   alertes,
            'medical':   medical,
            # Compat ancienne clé
            'visites_medicales': visites,
        }
    except Exception as e:
        logger.exception(f"Erreur _get_donnees_medical: {e}")
        return {'error': str(e), 'visites': [], 'accidents': [], 'validites': [], 'alertes': [], 'medical': {}}


def _get_donnees_vie_salarie(operateur_id: int) -> Dict:
    """Retourne toutes les données vie salarié avec les clés attendues par la GUI."""
    try:
        from domain.services.rh import vie_salarie_service as _vs
        sanctions   = _vs.get_sanctions(operateur_id)
        entretiens  = _vs.get_entretiens(operateur_id)
        alcoolemie  = _vs.get_controles_alcool(operateur_id)
        tests_sal   = _vs.get_tests_salivaires(operateur_id)
        alertes     = _vs.get_alertes_entretiens(operateur_id) if hasattr(_vs, 'get_alertes_entretiens') else []
        return {
            # Clés attendues par la GUI (résumés + listes détaillées)
            'sanctions':           sanctions,
            'sanctions_liste':     sanctions,
            'entretiens':          entretiens,
            'entretiens_liste':    entretiens,
            'alcoolemie':          alcoolemie,
            'controles_alcool_liste': alcoolemie,
            'tests_salivaires':    tests_sal,
            'tests_salivaires_liste': tests_sal,
            'alertes':             alertes,
        }
    except Exception as e:
        logger.exception(f"Erreur _get_donnees_vie_salarie: {e}")
        return {'error': str(e), 'sanctions': [], 'entretiens': [], 'alcoolemie': [],
                'sanctions_liste': [], 'entretiens_liste': [], 'controles_alcool_liste': [],
                'tests_salivaires': [], 'tests_salivaires_liste': [], 'alertes': []}


def _get_donnees_mutuelle(operateur_id: int) -> Dict:
    """Retourne les données mutuelle pour la GUI."""
    try:
        from domain.services.rh import mutuelle_service
        mutuelle = mutuelle_service.get_mutuelle(operateur_id)
        historique = mutuelle_service.get_historique_mutuelle(operateur_id)
        return {'mutuelle': mutuelle or {}, 'historique': historique}
    except Exception as e:
        logger.exception(f"Erreur _get_donnees_mutuelle: {e}")
        return {'error': str(e), 'mutuelle': {}, 'historique': []}


def _get_donnees_polyvalence(operateur_id: int) -> Dict:
    """
    Retourne les polyvalences d'un operateur avec les dossiers de formation associes.
    """
    try:
        from domain.services.documents.polyvalence_docs_service import get_docs_pour_operateur
        polyvalences = get_docs_pour_operateur(operateur_id)
        return {'polyvalences': polyvalences}
    except Exception as e:
        logger.exception(f"Erreur _get_donnees_polyvalence: {e}")
        return {'polyvalences': []}


# ============================================================
# 3. GESTION DES CONTRATS
# ============================================================

def create_contrat(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """
    ✅ REFACTORISÉ: Utilise ContratServiceCRUD.create().

    AVANT: 35 lignes (validation + INSERT + log_hist + gestion erreurs)
    APRÈS: 10 lignes (-71%)
    """
    require('rh.contrats.edit')
    try:
        # ✅ Validation métier (si nécessaire)
        if data.get('date_fin') and data['date_fin'] < data.get('date_debut'):
            return False, "La date de fin doit être postérieure à la date de début", None

        # ✅ Utiliser ContratServiceCRUD.create_contract()
        # Gère la désactivation du contrat précédent + logging automatique
        return ContratServiceCRUD.create_contract({
            'personnel_id': operateur_id,
            **data
        })

    except Exception as e:
        logger.exception(f"Erreur create_contrat: {e}")
        return False, f"Erreur lors de la création: {str(e)}", None


def update_contrat(contrat_id: int, data: Dict) -> Tuple[bool, str]:
    """
    ✅ REFACTORISÉ: Utilise ContratServiceCRUD.update().

    AVANT: 30 lignes
    APRÈS: 8 lignes (-73%)
    """
    require('rh.contrats.edit')
    try:
        # ✅ Validation métier (si nécessaire)
        if data.get('date_fin') and data.get('date_debut'):
            if data['date_fin'] < data['date_debut']:
                return False, "La date de fin doit être postérieure à la date de début"

        # ✅ Utiliser ContratServiceCRUD.update()
        return ContratServiceCRUD.update(
            record_id=contrat_id,
            **data
        )

    except Exception as e:
        logger.exception(f"Erreur update_contrat: {e}")
        return False, f"Erreur lors de la mise à jour: {str(e)}"


def delete_contrat(contrat_id: int) -> Tuple[bool, str]:
    """
    ✅ REFACTORISÉ: Utilise ContratServiceCRUD.delete().

    AVANT: 20 lignes
    APRÈS: 8 lignes (-60%)
    """
    require('rh.contrats.delete')
    try:
        # ✅ Soft delete (marquer comme inactif)
        return ContratServiceCRUD.delete(
            record_id=contrat_id,
            soft_delete=True,
            soft_delete_field='actif'
        )

    except Exception as e:
        logger.exception(f"Erreur delete_contrat: {e}")
        return False, f"Erreur lors de la suppression: {str(e)}"


# ============================================================
# 4. GESTION DES FORMATIONS
# ============================================================

def create_formation(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """
    ✅ REFACTORISÉ: Utilise FormationServiceCRUD.create().

    AVANT: 35 lignes
    APRÈS: 8 lignes (-77%)
    """
    require('rh.formations.edit')
    try:
        # ✅ Utiliser FormationServiceCRUD.create()
        return FormationServiceCRUD.create(
            personnel_id=operateur_id,
            **data
        )

    except Exception as e:
        logger.exception(f"Erreur create_formation: {e}")
        return False, f"Erreur lors de la création: {str(e)}", None


def update_formation(formation_id: int, data: Dict) -> Tuple[bool, str]:
    """
    ✅ REFACTORISÉ: Utilise FormationServiceCRUD.update().

    AVANT: 30 lignes
    APRÈS: 8 lignes (-73%)
    """
    require('rh.formations.edit')
    try:
        # ✅ Utiliser FormationServiceCRUD.update()
        return FormationServiceCRUD.update(
            record_id=formation_id,
            **data
        )

    except Exception as e:
        logger.exception(f"Erreur update_formation: {e}")
        return False, f"Erreur lors de la mise à jour: {str(e)}"


def delete_formation(formation_id: int) -> Tuple[bool, str]:
    """
    ✅ REFACTORISÉ: Utilise FormationServiceCRUD.delete().

    AVANT: 20 lignes
    APRÈS: 8 lignes (-60%)
    """
    require('rh.formations.delete')
    try:
        # ✅ Hard delete
        return FormationServiceCRUD.delete(record_id=formation_id)

    except Exception as e:
        logger.exception(f"Erreur delete_formation: {e}")
        return False, f"Erreur lors de la suppression: {str(e)}"


# ============================================================
# 5. GESTION DES INFOS GÉNÉRALES
# ============================================================

def update_infos_generales(operateur_id: int, data: Dict) -> Tuple[bool, str]:
    """
    ✅ REFACTORISÉ: Utilise QueryExecutor.execute_write().

    Mise à jour des informations générales d'un opérateur.

    AVANT: 120 lignes (construction dynamique UPDATE + log_hist)
    APRÈS: 60 lignes (-50%)
    """
    require('rh.personnel.edit')
    try:
        # Validation des dates
        dn = data.get('date_naissance')
        de = data.get('date_entree')
        today = date.today()

        if dn and isinstance(dn, str):
            try:
                dn = datetime.strptime(dn, '%Y-%m-%d').date()
            except ValueError:
                dn = None

        if de and isinstance(de, str):
            try:
                de = datetime.strptime(de, '%Y-%m-%d').date()
            except ValueError:
                de = None

        if dn and dn > today:
            return False, "La date de naissance ne peut pas être dans le futur."
        if de and de > today:
            return False, "La date d'entrée ne peut pas être dans le futur."
        if dn and de and de < dn:
            return False, "La date d'entrée ne peut pas être antérieure à la date de naissance."

        # Séparer les données personnel vs personnel_infos
        personnel_fields = ['nom', 'prenom', 'matricule', 'statut', 'numposte']
        personnel_data = {k: v for k, v in data.items() if k in personnel_fields}
        infos_data = {k: v for k, v in data.items() if k not in personnel_fields and k != 'operateur_id'}

        if personnel_data:
            PersonnelRepository.update(operateur_id, personnel_data)

        if infos_data:
            PersonnelRepository.upsert_infos(operateur_id, infos_data)

        # ✅ Logging manuel (pour l'instant, en attendant PersonnelService.update())
        from infrastructure.logging.optimized_db_logger import log_hist
        log_hist(
            action="UPDATE_INFOS_GENERALES",
            table_name="personnel",
            record_id=operateur_id,
            description=f"Informations générales mises à jour"
        )

        return True, "Informations mises à jour avec succès"

    except Exception as e:
        logger.exception(f"Erreur update_infos_generales: {e}")
        return False, f"Erreur lors de la mise à jour: {str(e)}"


# ============================================================
# 6. GESTION DES DÉCLARATIONS
# ============================================================

def create_declaration(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """
    Crée une nouvelle déclaration.

    AVANT: 25 lignes avec DatabaseConnection + require
    APRÈS: 8 lignes avec DeclarationServiceCRUD
    """
    require('rh.declarations.edit')
    from domain.services.rh.declaration_service_crud import DeclarationServiceCRUD
    try:
        return DeclarationServiceCRUD.create(
            operateur_id=operateur_id,
            **data
        )
    except Exception as e:
        logger.exception(f"Erreur create_declaration: {e}")
        return False, f"Erreur: {str(e)}", None


def update_declaration(declaration_id: int, data: Dict) -> Tuple[bool, str]:
    """
    Met à jour une déclaration existante.

    AVANT: 25 lignes avec DatabaseConnection
    APRÈS: 8 lignes avec DeclarationServiceCRUD
    """
    require('rh.declarations.edit')
    from domain.services.rh.declaration_service_crud import DeclarationServiceCRUD
    try:
        return DeclarationServiceCRUD.update(
            record_id=declaration_id,
            **data
        )
    except Exception as e:
        logger.exception(f"Erreur update_declaration: {e}")
        return False, f"Erreur: {str(e)}"


def delete_declaration(declaration_id: int) -> Tuple[bool, str]:
    """
    Supprime une déclaration.

    AVANT: 10 lignes avec DatabaseConnection
    APRÈS: 5 lignes avec DeclarationServiceCRUD
    """
    require('rh.declarations.edit')
    from domain.services.rh.declaration_service_crud import DeclarationServiceCRUD
    try:
        return DeclarationServiceCRUD.delete(record_id=declaration_id)
    except Exception as e:
        logger.exception(f"Erreur delete_declaration: {e}")
        return False, f"Erreur: {str(e)}"


# ============================================================
# 7. GESTION DES COMPÉTENCES
# ============================================================


def create_competence_personnel(
    operateur_id: int,
    data: Dict
) -> Tuple[bool, str, Optional[int]]:
    """
    Assigne une compétence à un opérateur.

    Délègue au service competences existant (déjà optimisé).
    """
    try:
        competence_id = data.get('competence_id')
        date_acquisition = data.get('date_acquisition')
        date_expiration = data.get('date_expiration')
        commentaire = data.get('commentaire')
        document_id = data.get('document_id')

        if not competence_id:
            return False, "Compétence non spécifiée", None
        if not date_acquisition:
            return False, "Date d'acquisition obligatoire", None

        return competences_service.assign_competence(
            personnel_id=operateur_id,
            competence_id=competence_id,
            date_acquisition=date_acquisition,
            date_expiration=date_expiration,
            commentaire=commentaire,
            document_id=document_id
        )

    except PermissionError as e:
        return False, str(e), None
    except Exception as e:
        logger.exception(f"Erreur create_competence_personnel: {e}")
        return False, "Erreur lors de l'assignation", None




# ============================================================
# 8. DOCUMENTS
# ============================================================

def get_documents_domaine(
    operateur_id: int,
    domaine: DomaineRH,
    include_archives: bool = False
) -> List[Dict]:
    """Récupère les documents d'un opérateur pour un domaine donné."""
    try:
        all_categories = DocumentRepository.get_categories()
        categories_ids = [
            cat['id'] for cat in all_categories
            if CATEGORIE_TO_DOMAINE.get(cat['nom'], DomaineRH.GENERAL) == domaine
        ]
        return DocumentRepository.get_by_operateur_domaine(
            operateur_id, categories_ids, include_archives=include_archives
        )
    except Exception as e:
        logger.exception(f"Erreur get_documents_domaine: {e}")
        return []


def get_documents_archives_operateur(operateur_id: int) -> List[Dict]:
    """Récupère tous les documents archivés d'un opérateur."""
    try:
        return DocumentRepository.get_archives_by_operateur(operateur_id)
    except Exception as e:
        logger.exception(f"Erreur get_documents_archives_operateur: {e}")
        return []


# ============================================================
# 9. RÉSUMÉ OPÉRATEUR
# ============================================================

def get_resume_operateur(operateur_id: int) -> Dict[str, Any]:
    """
    Récupère un résumé complet d'un opérateur pour tous les domaines.

    AVANT: 100 lignes avec with DatabaseCursor
    APRÈS: 70 lignes avec QueryExecutor
    """
    resume = {
        "operateur_id": operateur_id,
        "domaines": {}
    }

    operateur = get_operateur_by_id(operateur_id)
    if not operateur:
        return {"error": "Opérateur introuvable"}

    resume["nom_complet"] = operateur.get("nom_complet")
    resume["matricule"] = operateur.get("matricule")
    resume["statut"] = operateur.get("statut")

    try:
        resume["domaines"]["contrat"] = ContratRepository.get_resume_for_operateur(operateur_id)
        resume["domaines"]["declaration"] = DeclarationRepository.get_resume(operateur_id)
        resume["domaines"]["competences"] = PersonnelRepository.get_resume_competences(operateur_id)
        resume["domaines"]["formation"] = ContratRepository.get_resume_formation(operateur_id)
        resume["documents"] = DocumentRepository.get_resume(operateur_id)

    except Exception as e:
        logger.exception(f"Erreur get_resume_operateur: {e}")
        resume["error"] = str(e)

    return resume


# ============================================================
# 10. HELPERS
# ============================================================

def get_categories_documents() -> List[Dict]:
    """Récupère toutes les catégories de documents avec leur domaine RH associé."""
    try:
        categories = DocumentRepository.get_categories()
        for cat in categories:
            domaine = CATEGORIE_TO_DOMAINE.get(cat['nom'], DomaineRH.GENERAL)
            cat['domaine_rh'] = domaine.value
        return categories
    except Exception as e:
        logger.exception(f"Erreur get_categories_documents: {e}")
        return []


def get_domaines_rh() -> List[Dict]:
    """Retourne la liste des domaines RH avec leurs informations."""
    return [
        {
            "code": DomaineRH.GENERAL.value,
            "nom": "Données générales",
            "description": "Informations personnelles et administratives",
            "icone": "user"
        },
        {
            "code": DomaineRH.CONTRAT.value,
            "nom": "Contrat",
            "description": "Contrats de travail et avenants",
            "icone": "file-contract"
        },
        {
            "code": DomaineRH.DECLARATION.value,
            "nom": "Absence",
            "description": "Arrêts maladie, accidents, congés",
            "icone": "clipboard-list"
        },
        {
            "code": DomaineRH.COMPETENCES.value,
            "nom": "Compétences",
            "description": "Polyvalence et niveaux de qualification",
            "icone": "graduation-cap"
        },
        {
            "code": DomaineRH.FORMATION.value,
            "nom": "Formation",
            "description": "Formations suivies et planifiées",
            "icone": "chalkboard-teacher"
        },
        {
            "code": DomaineRH.MEDICAL.value,
            "nom": "Médical",
            "description": "Visites médicales, RQTH, accidents du travail",
            "icone": "heartbeat"
        },
        {
            "code": DomaineRH.VIE_SALARIE.value,
            "nom": "Vie du salarié",
            "description": "Sanctions, contrôles, entretiens professionnels",
            "icone": "user-clock"
        },
        {
            "code": DomaineRH.POLYVALENCE.value,
            "nom": "Polyvalence",
            "description": "Niveaux de polyvalence et dossiers de formation par poste",
            "icone": "layer-group"
        },
        {
            "code": DomaineRH.MUTUELLE.value,
            "nom": "Mutuelle",
            "description": "Complémentaire santé, adhésion et dispenses",
            "icone": "shield-alt"
        },
    ]


def get_alertes_rh_dashboard(jours: int = 30) -> Dict:
    """Récupère les alertes RH pour le dashboard principal."""
    alertes: Dict = {"contrats": [], "documents": []}
    try:
        alertes["contrats"] = ContratRepository.get_alertes(jours=jours)
        alertes["documents"] = DocumentRepository.get_alertes(jours=jours)
    except Exception as e:
        logger.exception(f"Erreur get_alertes_rh_dashboard: {e}")
        alertes["error"] = str(e)
    return alertes


def get_alertes_rh_count(jours: int = 30) -> Dict:
    """Compte le nombre d'alertes RH (contrats + documents)."""
    counts: Dict = {"contrats_count": 0, "documents_count": 0, "total": 0}
    try:
        counts["contrats_count"] = ContratRepository.count_alertes(jours=jours)
        counts["documents_count"] = DocumentRepository.count_alertes(jours=jours)
        counts["total"] = counts["contrats_count"] + counts["documents_count"]
    except Exception as e:
        logger.exception(f"Erreur get_alertes_rh_count: {e}")
    return counts


# ============================================================
# SÉCURITÉ : ACCÈS AUX DOCUMENTS PAR ENTITÉ
# ============================================================

def get_documents_entite(entity_type: str, entity_id: int) -> List[Dict]:
    """
    Retourne les documents associés à une entité (contrat, formation, declaration).

    Délègue à DocumentRepository qui maintient la whitelist anti-injection.
    Les types inconnus retournent [] sans lever d'exception.
    """
    return DocumentRepository.get_by_entite(entity_type, entity_id)


def is_matricule_disponible(matricule: str, exclude_operateur_id: int) -> bool:
    """
    Vérifie si un matricule est disponible (non utilisé par un autre opérateur).
    Retourne True si le matricule est libre, False s'il est déjà pris.
    """
    return PersonnelRepository.is_matricule_disponible(matricule, exclude_operateur_id)
