# -*- coding: utf-8 -*-
"""
Service RH unifié pour l'écran Gestion RH
Fournit les fonctions d'accès aux données pour tous les domaines RH

Domaines gérés:
- GENERAL: Données générales de l'opérateur
- CONTRAT: Contrats de travail
- DECLARATION: Déclarations (arrêt maladie, AT, congés...)
- COMPETENCES: Polyvalence et niveaux
- FORMATION: Formations suivies et planifiées

L'interface graphique ne doit jamais contenir de logique SQL.
"""

import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

from core.db.configbd import DatabaseCursor, DatabaseConnection
from core.services.permission_manager import require


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


# Mapping catégories de documents → domaines RH
CATEGORIE_TO_DOMAINE = {
    "Contrats de travail": DomaineRH.CONTRAT,
    "Certificats médicaux": DomaineRH.MEDICAL,
    "Diplômes et formations": DomaineRH.FORMATION,
    "Autorisations de travail": DomaineRH.CONTRAT,
    "Pièces d'identité": DomaineRH.GENERAL,
    "Attestations diverses": DomaineRH.GENERAL,
    "Documents administratifs": DomaineRH.GENERAL,
    "Documents médicaux": DomaineRH.MEDICAL,
    "Sanctions disciplinaires": DomaineRH.VIE_SALARIE,
    "Entretiens professionnels": DomaineRH.VIE_SALARIE,
    "Autres": DomaineRH.GENERAL,
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
    Recherche des opérateurs par nom, prénom ou matricule.

    Args:
        recherche: Texte à rechercher (nom, prénom ou matricule)
        statut: Filtrer par statut ('ACTIF', 'INACTIF', None pour tous)
        limit: Nombre max de résultats

    Returns:
        Liste des opérateurs correspondants
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            sql = """
                SELECT
                    p.id,
                    p.nom,
                    p.prenom,
                    p.matricule,
                    p.statut,
                    p.numposte,
                    CONCAT(p.prenom, ' ', p.nom) as nom_complet
                FROM personnel p
                WHERE 1=1
            """
            params = []

            if statut:
                sql += " AND p.statut = %s"
                params.append(statut)

            if recherche:
                recherche_like = f"%{recherche}%"
                sql += """ AND (
                    p.nom LIKE %s
                    OR p.prenom LIKE %s
                    OR p.matricule LIKE %s
                    OR CONCAT(p.prenom, ' ', p.nom) LIKE %s
                )"""
                params.extend([recherche_like] * 4)

            sql += " ORDER BY p.nom, p.prenom LIMIT %s"
            params.append(limit)

            cur.execute(sql, tuple(params))
            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur rechercher_operateurs: {e}")
        return []


def get_operateur_by_id(operateur_id: int) -> Optional[Dict]:
    """
    Récupère un opérateur par son ID.

    Args:
        operateur_id: ID de l'opérateur

    Returns:
        Dictionnaire avec les données de base ou None
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    p.id,
                    p.nom,
                    p.prenom,
                    p.matricule,
                    p.statut,
                    p.numposte,
                    p.service_id,
                    CONCAT(p.prenom, ' ', p.nom) as nom_complet
                FROM personnel p
                WHERE p.id = %s
            """, (operateur_id,))
            return cur.fetchone()

    except Exception as e:
        logger.error(f"Erreur get_operateur_by_id: {e}")
        return None


def get_operateur_by_matricule(matricule: str) -> Optional[Dict]:
    """
    Récupère un opérateur par son matricule.

    Args:
        matricule: Matricule de l'opérateur

    Returns:
        Dictionnaire avec les données de base ou None
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    p.id,
                    p.nom,
                    p.prenom,
                    p.matricule,
                    p.statut,
                    p.numposte,
                    CONCAT(p.prenom, ' ', p.nom) as nom_complet
                FROM personnel p
                WHERE p.matricule = %s
            """, (matricule,))
            return cur.fetchone()

    except Exception as e:
        logger.error(f"Erreur get_operateur_by_matricule: {e}")
        return None


# ============================================================
# 2. DONNÉES PAR DOMAINE
# ============================================================

def get_donnees_domaine(
    operateur_id: int,
    domaine: DomaineRH
) -> Dict[str, Any]:
    """
    Récupère les données d'un opérateur pour un domaine donné.

    Args:
        operateur_id: ID de l'opérateur
        domaine: Domaine RH (GENERAL, CONTRAT, DECLARATION, COMPETENCES, FORMATION, MEDICAL, VIE_SALARIE)

    Returns:
        Dictionnaire avec les données du domaine
    """
    handlers = {
        DomaineRH.GENERAL: _get_donnees_generales,
        DomaineRH.CONTRAT: _get_donnees_contrat,
        DomaineRH.DECLARATION: _get_donnees_declaration,
        DomaineRH.COMPETENCES: _get_donnees_competences,
        DomaineRH.FORMATION: _get_donnees_formation,
        DomaineRH.MEDICAL: _get_donnees_medical,
        DomaineRH.VIE_SALARIE: _get_donnees_vie_salarie,
    }

    handler = handlers.get(domaine)
    if handler:
        return handler(operateur_id)

    return {"error": f"Domaine inconnu: {domaine}"}


def _get_donnees_generales(operateur_id: int) -> Dict[str, Any]:
    """Récupère les données générales d'un opérateur."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            # Données de base + infos personnelles
            cur.execute("""
                SELECT
                    p.id,
                    p.nom,
                    p.prenom,
                    p.matricule,
                    p.statut,
                    p.numposte,
                    p.service_id,
                    CONCAT(p.prenom, ' ', p.nom) as nom_complet,
                    -- Infos personnelles
                    pi.sexe,
                    pi.date_naissance,
                    pi.date_entree,
                    pi.nationalite,
                    pi.adresse1,
                    pi.adresse2,
                    pi.cp_adresse,
                    pi.ville_adresse,
                    pi.pays_adresse,
                    pi.telephone,
                    pi.email,
                    pi.ville_naissance,
                    pi.pays_naissance,
                    pi.commentaire
                FROM personnel p
                LEFT JOIN personnel_infos pi ON pi.operateur_id = p.id
                WHERE p.id = %s
            """, (operateur_id,))

            donnees = cur.fetchone()
            if not donnees:
                return {"error": "Opérateur introuvable"}

            # Calculer l'ancienneté
            if donnees.get('date_entree'):
                today = date.today()
                delta = today - donnees['date_entree']
                annees = delta.days // 365
                mois = (delta.days % 365) // 30
                donnees['anciennete'] = f"{annees} ans, {mois} mois"
                donnees['anciennete_jours'] = delta.days
            else:
                donnees['anciennete'] = None
                donnees['anciennete_jours'] = None

            # Calculer l'âge
            if donnees.get('date_naissance'):
                today = date.today()
                age = today.year - donnees['date_naissance'].year
                if (today.month, today.day) < (donnees['date_naissance'].month, donnees['date_naissance'].day):
                    age -= 1
                donnees['age'] = age
            else:
                donnees['age'] = None

            return donnees

    except Exception as e:
        logger.error(f"Erreur _get_donnees_generales: {e}")
        return {"error": str(e)}


def _get_donnees_contrat(operateur_id: int) -> Dict[str, Any]:
    """Récupère les données de contrat d'un opérateur."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            # Contrat actif
            cur.execute("""
                SELECT
                    c.*,
                    DATEDIFF(c.date_fin, CURDATE()) as jours_restants
                FROM contrat c
                WHERE c.operateur_id = %s AND c.actif = 1
                ORDER BY c.date_debut DESC
                LIMIT 1
            """, (operateur_id,))

            contrat_actif = cur.fetchone()

            # Historique des contrats
            cur.execute("""
                SELECT
                    c.*,
                    DATEDIFF(c.date_fin, c.date_debut) as duree_jours
                FROM contrat c
                WHERE c.operateur_id = %s
                ORDER BY c.date_debut DESC
            """, (operateur_id,))

            historique = cur.fetchall()

            # Convertir Decimal en float
            if contrat_actif and contrat_actif.get('etp'):
                contrat_actif['etp'] = float(contrat_actif['etp'])
            if contrat_actif and contrat_actif.get('salaire'):
                contrat_actif['salaire'] = float(contrat_actif['salaire'])

            for c in historique:
                if c.get('etp'):
                    c['etp'] = float(c['etp'])
                if c.get('salaire'):
                    c['salaire'] = float(c['salaire'])

            return {
                "contrat_actif": contrat_actif,
                "historique": historique,
                "nb_contrats": len(historique)
            }

    except Exception as e:
        logger.error(f"Erreur _get_donnees_contrat: {e}")
        return {"error": str(e), "contrat_actif": None, "historique": [], "nb_contrats": 0}


def _get_donnees_declaration(operateur_id: int) -> Dict[str, Any]:
    """Récupère les déclarations d'un opérateur."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            # Toutes les déclarations
            cur.execute("""
                SELECT
                    d.*,
                    DATEDIFF(d.date_fin, d.date_debut) + 1 as duree_jours
                FROM declaration d
                WHERE d.operateur_id = %s
                ORDER BY d.date_debut DESC
            """, (operateur_id,))

            declarations = cur.fetchall()

            # Statistiques par type
            cur.execute("""
                SELECT
                    type_declaration,
                    COUNT(*) as nombre,
                    SUM(DATEDIFF(date_fin, date_debut) + 1) as total_jours
                FROM declaration
                WHERE operateur_id = %s
                GROUP BY type_declaration
            """, (operateur_id,))

            stats = {row['type_declaration']: row for row in cur.fetchall()}

            # Déclaration en cours
            cur.execute("""
                SELECT *
                FROM declaration
                WHERE operateur_id = %s
                  AND date_debut <= CURDATE()
                  AND date_fin >= CURDATE()
                ORDER BY date_debut DESC
                LIMIT 1
            """, (operateur_id,))

            en_cours = cur.fetchone()

            return {
                "declarations": declarations,
                "statistiques": stats,
                "en_cours": en_cours,
                "nb_declarations": len(declarations)
            }

    except Exception as e:
        logger.error(f"Erreur _get_donnees_declaration: {e}")
        return {"error": str(e), "declarations": [], "statistiques": {}, "en_cours": None, "nb_declarations": 0}


def _get_donnees_competences(operateur_id: int) -> Dict[str, Any]:
    """Récupère les compétences (polyvalence) d'un opérateur."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            # Polyvalence avec infos postes
            cur.execute("""
                SELECT
                    pv.id,
                    pv.poste_id,
                    pv.niveau,
                    pv.date_evaluation,
                    pv.prochaine_evaluation,
                    ps.poste_code,
                    a.nom as atelier_nom,
                    DATEDIFF(pv.prochaine_evaluation, CURDATE()) as jours_avant_evaluation
                FROM polyvalence pv
                JOIN postes ps ON pv.poste_id = ps.id
                LEFT JOIN atelier a ON ps.atelier_id = a.id
                WHERE pv.operateur_id = %s
                ORDER BY ps.poste_code
            """, (operateur_id,))

            competences = cur.fetchall()

            # Statistiques
            stats = {
                "total_postes": len(competences),
                "niveau_1": sum(1 for c in competences if c['niveau'] == 1),
                "niveau_2": sum(1 for c in competences if c['niveau'] == 2),
                "niveau_3": sum(1 for c in competences if c['niveau'] == 3),
                "niveau_4": sum(1 for c in competences if c['niveau'] == 4),
                "evaluations_en_retard": sum(1 for c in competences if c['jours_avant_evaluation'] and c['jours_avant_evaluation'] < 0),
                "evaluations_a_venir_30j": sum(1 for c in competences if c['jours_avant_evaluation'] and 0 <= c['jours_avant_evaluation'] <= 30),
            }

            return {
                "competences": competences,
                "statistiques": stats
            }

    except Exception as e:
        logger.error(f"Erreur _get_donnees_competences: {e}")
        return {"error": str(e), "competences": [], "statistiques": {}}


def _get_donnees_formation(operateur_id: int) -> Dict[str, Any]:
    """Récupère les formations d'un opérateur."""
    try:
        with DatabaseCursor(dictionary=True) as cur:
            # Toutes les formations
            cur.execute("""
                SELECT
                    f.*,
                    d.nom_fichier as attestation_nom,
                    d.id as document_id
                FROM formation f
                LEFT JOIN documents d ON f.document_id = d.id
                WHERE f.operateur_id = %s
                ORDER BY f.date_debut DESC
            """, (operateur_id,))

            formations = cur.fetchall()

            # Convertir Decimal
            for f in formations:
                if f.get('duree_heures'):
                    f['duree_heures'] = float(f['duree_heures'])
                if f.get('cout'):
                    f['cout'] = float(f['cout'])

            # Statistiques
            stats = {
                "total": len(formations),
                "terminees": sum(1 for f in formations if f['statut'] == 'Terminée'),
                "en_cours": sum(1 for f in formations if f['statut'] == 'En cours'),
                "planifiees": sum(1 for f in formations if f['statut'] == 'Planifiée'),
                "avec_certificat": sum(1 for f in formations if f['certificat_obtenu']),
            }

            return {
                "formations": formations,
                "statistiques": stats
            }

    except Exception as e:
        logger.error(f"Erreur _get_donnees_formation: {e}")
        return {"error": str(e), "formations": [], "statistiques": {}}


def _get_donnees_medical(operateur_id: int) -> Dict[str, Any]:
    """Récupère les données médicales d'un opérateur."""
    try:
        from core.services.medical_service import (
            get_donnees_medicales, get_visites, get_accidents,
            get_validites, get_alertes_medicales
        )
        # Récupérer les données principales
        donnees = get_donnees_medicales(operateur_id)

        # Ajouter les listes détaillées pour l'UI
        donnees['visites'] = get_visites(operateur_id)
        donnees['accidents'] = get_accidents(operateur_id)
        donnees['validites'] = get_validites(operateur_id)
        donnees['alertes'] = get_alertes_medicales(operateur_id)

        return donnees
    except Exception as e:
        logger.error(f"Erreur _get_donnees_medical: {e}")
        return {"error": str(e), "medical": None, "visites": [], "accidents": [], "validites": [], "alertes": []}


def _get_donnees_vie_salarie(operateur_id: int) -> Dict[str, Any]:
    """Récupère les données vie du salarié d'un opérateur."""
    try:
        from core.services.vie_salarie_service import (
            get_donnees_vie_salarie, get_sanctions, get_controles_alcool,
            get_tests_salivaires, get_entretiens, get_alertes_entretiens
        )
        # Récupérer les données de base (statistiques)
        donnees = get_donnees_vie_salarie(operateur_id)

        # Ajouter les listes détaillées pour l'UI
        donnees['sanctions_liste'] = get_sanctions(operateur_id)
        donnees['controles_alcool_liste'] = get_controles_alcool(operateur_id)
        donnees['tests_salivaires_liste'] = get_tests_salivaires(operateur_id)
        donnees['entretiens_liste'] = get_entretiens(operateur_id)
        donnees['alertes'] = get_alertes_entretiens(operateur_id)

        return donnees
    except Exception as e:
        logger.error(f"Erreur _get_donnees_vie_salarie: {e}")
        return {"error": str(e), "sanctions_liste": [], "controles_alcool_liste": [], "tests_salivaires_liste": [], "entretiens_liste": [], "alertes": []}


# ============================================================
# 3. DOCUMENTS PAR DOMAINE
# ============================================================

def get_documents_domaine(
    operateur_id: int,
    domaine: DomaineRH,
    include_archives: bool = False
) -> List[Dict]:
    """
    Récupère les documents d'un opérateur pour un domaine donné.

    Args:
        operateur_id: ID de l'opérateur
        domaine: Domaine RH
        include_archives: Inclure les documents archivés

    Returns:
        Liste des documents
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            # Récupérer toutes les catégories de la base de données
            cur.execute("SELECT id, nom FROM categories_documents")
            all_categories = cur.fetchall()

            # Trouver les IDs des catégories correspondant au domaine
            categories_ids = []
            for cat in all_categories:
                cat_domaine = CATEGORIE_TO_DOMAINE.get(cat['nom'], DomaineRH.GENERAL)
                if cat_domaine == domaine:
                    categories_ids.append(cat['id'])

            if not categories_ids:
                return []

            placeholders = ', '.join(['%s'] * len(categories_ids))

            sql = f"""
                SELECT
                    d.id,
                    d.operateur_id,
                    d.categorie_id,
                    d.nom_fichier,
                    d.nom_affichage,
                    d.chemin_fichier,
                    d.type_mime,
                    d.taille_octets,
                    d.date_upload,
                    d.date_expiration,
                    d.statut,
                    d.notes,
                    d.uploaded_by,
                    c.nom as categorie_nom,
                    c.couleur as categorie_couleur,
                    CASE
                        WHEN d.date_expiration IS NULL THEN NULL
                        WHEN d.date_expiration < CURDATE() THEN 'EXPIRE'
                        WHEN d.date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 'EXPIRE_BIENTOT'
                        ELSE 'VALIDE'
                    END as statut_expiration,
                    DATEDIFF(d.date_expiration, CURDATE()) as jours_avant_expiration
                FROM documents d
                JOIN categories_documents c ON d.categorie_id = c.id
                WHERE d.operateur_id = %s
                  AND d.categorie_id IN ({placeholders})
            """

            params = [operateur_id] + categories_ids

            if not include_archives:
                sql += " AND (d.statut IS NULL OR d.statut != 'archive')"

            sql += " ORDER BY d.date_upload DESC"

            cur.execute(sql, tuple(params))
            return cur.fetchall()

    except Exception as e:
        logger.exception(f"Erreur get_documents_domaine: {e}")
        return []


def get_documents_entite(
    entite_type: str,
    entite_id: int
) -> List[Dict]:
    """
    Récupère les documents liés à une entité spécifique.

    Args:
        entite_type: Type d'entité ('contrat', 'formation', 'declaration')
        entite_id: ID de l'entité

    Returns:
        Liste des documents
    """
    # SECURITE: Whitelist stricte des colonnes autorisées
    # Ne JAMAIS ajouter de colonnes sans validation
    ALLOWED_COLUMNS = {
        'contrat': 'contrat_id',
        'formation': 'formation_id',
        'declaration': 'declaration_id'
    }

    try:
        column = ALLOWED_COLUMNS.get(entite_type)
        if column is None:
            logger.warning(f"Type d'entité non autorisé: {entite_type}")
            return []

        # Double vérification de sécurité
        assert column in ('contrat_id', 'formation_id', 'declaration_id'), \
            f"Colonne non autorisée: {column}"

        # Construction sécurisée de la requête
        # La colonne est validée par whitelist, pas d'injection possible
        query = {
            'contrat_id': """
                SELECT d.*, c.nom as categorie_nom, c.couleur as categorie_couleur
                FROM documents d
                JOIN categories_documents c ON d.categorie_id = c.id
                WHERE d.contrat_id = %s
                ORDER BY d.date_upload DESC
            """,
            'formation_id': """
                SELECT d.*, c.nom as categorie_nom, c.couleur as categorie_couleur
                FROM documents d
                JOIN categories_documents c ON d.categorie_id = c.id
                WHERE d.formation_id = %s
                ORDER BY d.date_upload DESC
            """,
            'declaration_id': """
                SELECT d.*, c.nom as categorie_nom, c.couleur as categorie_couleur
                FROM documents d
                JOIN categories_documents c ON d.categorie_id = c.id
                WHERE d.declaration_id = %s
                ORDER BY d.date_upload DESC
            """
        }

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query[column], (entite_id,))

            return cur.fetchall()

    except Exception as e:
        logger.error(f"Erreur get_documents_entite: {e}")
        return []


# ============================================================
# 4. MISE À JOUR DES DOCUMENTS
# ============================================================

def update_document_statut(
    document_id: int,
    nouveau_statut: str
) -> Tuple[bool, str]:
    """
    Met à jour le statut d'un document.

    Args:
        document_id: ID du document
        nouveau_statut: Nouveau statut ('actif', 'expire', 'archive')

    Returns:
        (succès, message)
    """
    require('rh.documents.edit')
    statuts_valides = ['actif', 'expire', 'archive']
    if nouveau_statut not in statuts_valides:
        return False, f"Statut invalide. Valeurs possibles: {statuts_valides}"

    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE documents SET statut = %s WHERE id = %s",
                (nouveau_statut, document_id)
            )

            if cur.rowcount == 0:
                return False, "Document introuvable"

            return True, f"Statut mis à jour: {nouveau_statut}"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def lier_document_entite(
    document_id: int,
    entite_type: str,
    entite_id: int
) -> Tuple[bool, str]:
    """
    Lie un document à une entité (contrat, formation, déclaration).

    Args:
        document_id: ID du document
        entite_type: Type d'entité ('contrat', 'formation', 'declaration')
        entite_id: ID de l'entité

    Returns:
        (succès, message)
    """
    require('rh.documents.edit')
    column_map = {
        'contrat': 'contrat_id',
        'formation': 'formation_id',
        'declaration': 'declaration_id'
    }

    column = column_map.get(entite_type)
    if not column:
        return False, f"Type d'entité invalide: {entite_type}"

    # SÉCURITÉ: Validation stricte - la colonne DOIT être dans la whitelist
    assert column in ('contrat_id', 'formation_id', 'declaration_id'), \
        f"Colonne non autorisée: {column}"

    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            # SÉCURITÉ: Utilisation de requêtes distinctes pour chaque colonne valide
            if column == 'contrat_id':
                cur.execute("UPDATE documents SET contrat_id = %s WHERE id = %s", (entite_id, document_id))
            elif column == 'formation_id':
                cur.execute("UPDATE documents SET formation_id = %s WHERE id = %s", (entite_id, document_id))
            elif column == 'declaration_id':
                cur.execute("UPDATE documents SET declaration_id = %s WHERE id = %s", (entite_id, document_id))

            if cur.rowcount == 0:
                return False, "Document introuvable"

            return True, f"Document lié à {entite_type} #{entite_id}"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def delier_document_entite(
    document_id: int,
    entite_type: str
) -> Tuple[bool, str]:
    """
    Supprime le lien entre un document et une entité.

    Args:
        document_id: ID du document
        entite_type: Type d'entité ('contrat', 'formation', 'declaration')

    Returns:
        (succès, message)
    """
    require('rh.documents.edit')
    column_map = {
        'contrat': 'contrat_id',
        'formation': 'formation_id',
        'declaration': 'declaration_id'
    }

    column = column_map.get(entite_type)
    if not column:
        return False, f"Type d'entité invalide: {entite_type}"

    # SÉCURITÉ: Validation stricte - la colonne DOIT être dans la whitelist
    assert column in ('contrat_id', 'formation_id', 'declaration_id'), \
        f"Colonne non autorisée: {column}"

    try:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            # SÉCURITÉ: Utilisation de requêtes distinctes pour chaque colonne valide
            if column == 'contrat_id':
                cur.execute("UPDATE documents SET contrat_id = NULL WHERE id = %s", (document_id,))
            elif column == 'formation_id':
                cur.execute("UPDATE documents SET formation_id = NULL WHERE id = %s", (document_id,))
            elif column == 'declaration_id':
                cur.execute("UPDATE documents SET declaration_id = NULL WHERE id = %s", (document_id,))

            if cur.rowcount == 0:
                return False, "Document introuvable"

            return True, f"Lien avec {entite_type} supprimé"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


# ============================================================
# 5. STATISTIQUES ET RÉSUMÉ
# ============================================================

def get_resume_operateur(operateur_id: int) -> Dict[str, Any]:
    """
    Récupère un résumé complet d'un opérateur pour tous les domaines.

    Args:
        operateur_id: ID de l'opérateur

    Returns:
        Dictionnaire avec résumé de chaque domaine
    """
    resume = {
        "operateur_id": operateur_id,
        "domaines": {}
    }

    # Données générales (juste nom et matricule)
    operateur = get_operateur_by_id(operateur_id)
    if not operateur:
        return {"error": "Opérateur introuvable"}

    resume["nom_complet"] = operateur.get("nom_complet")
    resume["matricule"] = operateur.get("matricule")
    resume["statut"] = operateur.get("statut")

    try:
        with DatabaseCursor(dictionary=True) as cur:
            # Résumé contrat
            cur.execute("""
                SELECT type_contrat, date_fin, DATEDIFF(date_fin, CURDATE()) as jours_restants
                FROM contrat
                WHERE operateur_id = %s AND actif = 1
                LIMIT 1
            """, (operateur_id,))
            contrat = cur.fetchone()
            resume["domaines"]["contrat"] = {
                "a_contrat_actif": contrat is not None,
                "type": contrat['type_contrat'] if contrat else None,
                "jours_restants": contrat['jours_restants'] if contrat else None
            }

            # Résumé déclarations
            cur.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN date_debut <= CURDATE() AND date_fin >= CURDATE() THEN 1 ELSE 0 END) as en_cours
                FROM declaration
                WHERE operateur_id = %s
            """, (operateur_id,))
            decl = cur.fetchone()
            resume["domaines"]["declaration"] = {
                "total": decl['total'] if decl else 0,
                "en_cours": decl['en_cours'] if decl else 0
            }

            # Résumé compétences
            cur.execute("""
                SELECT COUNT(*) as total,
                       AVG(niveau) as niveau_moyen,
                       SUM(CASE WHEN prochaine_evaluation < CURDATE() THEN 1 ELSE 0 END) as en_retard
                FROM polyvalence
                WHERE operateur_id = %s
            """, (operateur_id,))
            comp = cur.fetchone()
            resume["domaines"]["competences"] = {
                "nb_postes": comp['total'] if comp else 0,
                "niveau_moyen": float(comp['niveau_moyen']) if comp and comp['niveau_moyen'] else None,
                "evaluations_en_retard": comp['en_retard'] if comp else 0
            }

            # Résumé formations
            cur.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN statut = 'Terminée' THEN 1 ELSE 0 END) as terminees,
                       SUM(CASE WHEN statut = 'Planifiée' THEN 1 ELSE 0 END) as planifiees
                FROM formation
                WHERE operateur_id = %s
            """, (operateur_id,))
            form = cur.fetchone()
            resume["domaines"]["formation"] = {
                "total": form['total'] if form else 0,
                "terminees": form['terminees'] if form else 0,
                "planifiees": form['planifiees'] if form else 0
            }

            # Résumé documents
            cur.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN statut = 'expire' THEN 1 ELSE 0 END) as expires,
                       SUM(CASE WHEN date_expiration IS NOT NULL
                                AND date_expiration <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                                AND date_expiration > CURDATE() THEN 1 ELSE 0 END) as expire_bientot
                FROM documents
                WHERE operateur_id = %s AND statut != 'archive'
            """, (operateur_id,))
            docs = cur.fetchone()
            resume["documents"] = {
                "total": docs['total'] if docs else 0,
                "expires": docs['expires'] if docs else 0,
                "expire_bientot": docs['expire_bientot'] if docs else 0
            }

    except Exception as e:
        logger.error(f"Erreur get_resume_operateur: {e}")
        resume["error"] = str(e)

    return resume


# ============================================================
# 6. HELPERS
# ============================================================

def get_categories_documents() -> List[Dict]:
    """
    Récupère toutes les catégories de documents avec leur domaine RH associé.

    Returns:
        Liste des catégories
    """
    try:
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT * FROM categories_documents
                ORDER BY ordre_affichage
            """)
            categories = cur.fetchall()

            # Ajouter le domaine RH
            for cat in categories:
                domaine = CATEGORIE_TO_DOMAINE.get(cat['nom'], DomaineRH.GENERAL)
                cat['domaine_rh'] = domaine.value

            return categories

    except Exception as e:
        logger.error(f"Erreur get_categories_documents: {e}")
        return []


def get_types_declaration() -> List[str]:
    """Retourne la liste des types de déclaration disponibles."""
    return [
        'CongePaye',
        'RTT',
        'SansSolde',
        'Maladie',
        'AccidentTravail',
        'AccidentTrajet',
        'ArretTravail',
        'CongeNaissance',
        'Formation',
        'Autorisation',
        'Autre'
    ]


def get_domaines_rh() -> List[Dict]:
    """
    Retourne la liste des domaines RH avec leurs informations.

    Returns:
        Liste des domaines
    """
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
    ]


# ============================================================
# 7. CRUD - DONNÉES GÉNÉRALES (personnel_infos)
# ============================================================

def update_infos_generales(operateur_id: int, data: Dict) -> Tuple[bool, str]:
    """
    Met à jour les informations générales d'un opérateur.

    Args:
        operateur_id: ID de l'opérateur
        data: Dictionnaire avec les champs à mettre à jour
              - 'matricule' est mis à jour dans la table 'personnel'
              - Les autres champs sont mis à jour dans 'personnel_infos'

    Returns:
        (succès, message)
    """
    try:
        require('rh.personnel.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor(dictionary=True)

            # 1. Mise à jour des champs dans la table personnel (nom, prenom, matricule)
            personnel_updates = []
            personnel_values = []
            log_changes = []

            # Récupérer les anciennes valeurs pour le log
            cur.execute("SELECT nom, prenom, matricule FROM personnel WHERE id = %s", (operateur_id,))
            ancien = cur.fetchone()

            if 'nom' in data and data['nom']:
                ancien_nom = ancien['nom'] if ancien else None
                if ancien_nom != data['nom']:
                    personnel_updates.append("nom = %s")
                    personnel_values.append(data['nom'])
                    log_changes.append(f"Nom: {ancien_nom} → {data['nom']}")

            if 'prenom' in data and data['prenom']:
                ancien_prenom = ancien['prenom'] if ancien else None
                if ancien_prenom != data['prenom']:
                    personnel_updates.append("prenom = %s")
                    personnel_values.append(data['prenom'])
                    log_changes.append(f"Prénom: {ancien_prenom} → {data['prenom']}")

            if 'matricule' in data:
                ancien_matricule = ancien['matricule'] if ancien else None
                if ancien_matricule != data['matricule']:
                    personnel_updates.append("matricule = %s")
                    personnel_values.append(data['matricule'])
                    log_changes.append(f"Matricule: {ancien_matricule} → {data['matricule']}")

            # Exécuter la mise à jour de la table personnel si nécessaire
            if personnel_updates:
                personnel_values.append(operateur_id)
                sql = "UPDATE personnel SET " + ", ".join(personnel_updates) + " WHERE id = %s"
                cur.execute(sql, tuple(personnel_values))

                # Logger les modifications
                from core.services.logger import log_hist
                log_hist(
                    action="UPDATE",
                    table_name="personnel",
                    record_id=operateur_id,
                    description="; ".join(log_changes),
                    operateur_id=operateur_id
                )

            # 2. Vérifier si personnel_infos existe
            cur.execute("SELECT id FROM personnel_infos WHERE operateur_id = %s", (operateur_id,))
            exists = cur.fetchone()

            # SÉCURITÉ: Whitelist stricte des colonnes autorisées pour personnel_infos
            ALLOWED_COLUMNS = frozenset([
                'sexe', 'date_naissance', 'date_entree', 'nationalite',
                'adresse1', 'adresse2', 'cp_adresse', 'ville_adresse',
                'pays_adresse', 'telephone', 'email', 'ville_naissance',
                'pays_naissance', 'commentaire'
            ])

            if exists:
                # UPDATE
                fields = []
                values = []
                for key in ALLOWED_COLUMNS:
                    if key in data:
                        # SÉCURITÉ: Double vérification que la clé est dans la whitelist
                        assert key in ALLOWED_COLUMNS, f"Colonne non autorisée: {key}"
                        fields.append(f"{key} = %s")
                        values.append(data[key] if data[key] != '' else None)

                if fields:
                    values.append(operateur_id)
                    # SÉCURITÉ: Les colonnes proviennent uniquement de ALLOWED_COLUMNS (constante)
                    sql = "UPDATE personnel_infos SET " + ", ".join(fields) + " WHERE operateur_id = %s"
                    cur.execute(sql, tuple(values))
            else:
                # INSERT
                columns = ['operateur_id']
                values = [operateur_id]
                placeholders = ['%s']

                for key in ALLOWED_COLUMNS:
                    if key in data:
                        # SÉCURITÉ: Double vérification que la clé est dans la whitelist
                        assert key in ALLOWED_COLUMNS, f"Colonne non autorisée: {key}"
                        columns.append(key)
                        values.append(data[key] if data[key] != '' else None)
                        placeholders.append('%s')

                # SÉCURITÉ: Les colonnes proviennent uniquement de ALLOWED_COLUMNS (constante)
                sql = "INSERT INTO personnel_infos (" + ", ".join(columns) + ") VALUES (" + ", ".join(placeholders) + ")"
                cur.execute(sql, tuple(values))

            return True, "Informations mises à jour avec succès"

    except Exception as e:
        logger.error(f"Erreur update_infos_generales: {e}")
        return False, f"Erreur: {str(e)}"


# ============================================================
# 8. CRUD - CONTRATS
# ============================================================

def create_contrat(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée un nouveau contrat."""
    try:
        require('rh.contrats.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO contrat (
                    operateur_id, type_contrat, date_debut, date_fin,
                    etp, categorie, echelon, emploi, salaire, actif
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """
            cur.execute(sql, (
                operateur_id,
                data.get('type_contrat'),
                data.get('date_debut'),
                data.get('date_fin'),
                data.get('etp', 1.0),
                data.get('categorie'),
                data.get('echelon'),
                data.get('emploi'),
                data.get('salaire')
            ))

            contrat_id = cur.lastrowid
            return True, "Contrat créé avec succès", contrat_id

    except Exception as e:
        logger.error(f"Erreur create_contrat: {e}")
        return False, f"Erreur: {str(e)}", None


def update_contrat(contrat_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour un contrat existant."""
    try:
        require('rh.contrats.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                UPDATE contrat SET
                    type_contrat = %s, date_debut = %s, date_fin = %s,
                    etp = %s, categorie = %s, echelon = %s,
                    emploi = %s, salaire = %s
                WHERE id = %s
            """
            cur.execute(sql, (
                data.get('type_contrat'),
                data.get('date_debut'),
                data.get('date_fin'),
                data.get('etp', 1.0),
                data.get('categorie'),
                data.get('echelon'),
                data.get('emploi'),
                data.get('salaire'),
                contrat_id
            ))

            return True, "Contrat mis à jour avec succès"

    except Exception as e:
        logger.error(f"Erreur update_contrat: {e}")
        return False, f"Erreur: {str(e)}"


def delete_contrat(contrat_id: int) -> Tuple[bool, str]:
    """Désactive un contrat (soft delete)."""
    try:
        require('rh.contrats.delete')
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE contrat SET actif = 0 WHERE id = %s", (contrat_id,))
            return True, "Contrat désactivé avec succès"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


# ============================================================
# 9. CRUD - DÉCLARATIONS
# ============================================================

def create_declaration(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée une nouvelle déclaration."""
    try:
        require('rh.declarations.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO declaration (
                    operateur_id, type_declaration, date_debut, date_fin, motif
                ) VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                operateur_id,
                data.get('type_declaration'),
                data.get('date_debut'),
                data.get('date_fin'),
                data.get('motif')
            ))

            declaration_id = cur.lastrowid
            return True, "Déclaration créée avec succès", declaration_id

    except Exception as e:
        logger.error(f"Erreur create_declaration: {e}")
        return False, f"Erreur: {str(e)}", None


def update_declaration(declaration_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour une déclaration existante."""
    try:
        require('rh.declarations.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                UPDATE declaration SET
                    type_declaration = %s, date_debut = %s, date_fin = %s, motif = %s
                WHERE id = %s
            """
            cur.execute(sql, (
                data.get('type_declaration'),
                data.get('date_debut'),
                data.get('date_fin'),
                data.get('motif'),
                declaration_id
            ))

            return True, "Déclaration mise à jour avec succès"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def delete_declaration(declaration_id: int) -> Tuple[bool, str]:
    """Supprime une déclaration."""
    try:
        require('rh.declarations.delete')
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM declaration WHERE id = %s", (declaration_id,))
            return True, "Déclaration supprimée avec succès"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


# ============================================================
# 10. CRUD - FORMATIONS
# ============================================================

def create_formation(operateur_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée une nouvelle formation."""
    try:
        require('rh.formations.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                INSERT INTO formation (
                    operateur_id, intitule, organisme, date_debut, date_fin,
                    duree_heures, statut, certificat_obtenu, commentaire
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                operateur_id,
                data.get('intitule'),
                data.get('organisme'),
                data.get('date_debut'),
                data.get('date_fin'),
                data.get('duree_heures'),
                data.get('statut', 'Planifiée'),
                data.get('certificat_obtenu', False),
                data.get('commentaire')
            ))

            formation_id = cur.lastrowid
            return True, "Formation créée avec succès", formation_id

    except Exception as e:
        logger.error(f"Erreur create_formation: {e}")
        return False, f"Erreur: {str(e)}", None


def update_formation(formation_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour une formation existante."""
    try:
        require('rh.formations.edit')
        with DatabaseConnection() as conn:
            cur = conn.cursor()

            sql = """
                UPDATE formation SET
                    intitule = %s, organisme = %s, date_debut = %s, date_fin = %s,
                    duree_heures = %s, statut = %s, certificat_obtenu = %s, commentaire = %s
                WHERE id = %s
            """
            cur.execute(sql, (
                data.get('intitule'),
                data.get('organisme'),
                data.get('date_debut'),
                data.get('date_fin'),
                data.get('duree_heures'),
                data.get('statut'),
                data.get('certificat_obtenu', False),
                data.get('commentaire'),
                formation_id
            ))

            return True, "Formation mise à jour avec succès"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def delete_formation(formation_id: int) -> Tuple[bool, str]:
    """Supprime une formation."""
    try:
        require('rh.formations.delete')
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM formation WHERE id = %s", (formation_id,))
            return True, "Formation supprimée avec succès"

    except Exception as e:
        return False, f"Erreur: {str(e)}"
