# -*- coding: utf-8 -*-
"""
Service de gestion des opérations en masse.
Permet d'assigner des formations, absences, visites médicales à plusieurs employés.

Utilise les services existants (formation_service, absence_service, medical_service)
pour les opérations unitaires, et ajoute le tracking batch.
"""

from datetime import date, datetime
from typing import List, Dict, Tuple, Optional, Callable, Any

from core.db.query_executor import QueryExecutor
from core.services.optimized_db_logger import log_hist
from core.services.permission_manager import require, can
from core.services.document_service import DocumentService
from core.utils.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# HELPER: Gestion des catégories de documents
# ============================================================

def _get_categorie_id_by_name(nom_categorie: str) -> Optional[int]:
    """
    Récupère l'ID d'une catégorie de documents par son nom.

    Args:
        nom_categorie: Nom de la catégorie

    Returns:
        ID de la catégorie ou None si introuvable
    """
    try:
        row = QueryExecutor.fetch_one(
            "SELECT id FROM categories_documents WHERE nom = %s",
            (nom_categorie,),
            dictionary=True
        )
        return row['id'] if row else None
    except Exception as e:
        logger.error(f"Erreur récupération catégorie '{nom_categorie}': {e}")
        return None


# ============================================================
# HELPER: Gestion des callbacks de progression
# ============================================================

def _emit_progress(progress_callback: Optional[Callable], *args, **kwargs):
    """
    Émet un callback de progression de manière sécurisée.

    Gère automatiquement les deux cas:
    - Signal PyQt5 (provenant de DbWorker) → utilise .emit()
    - Fonction normale → appel direct
    - None → ignore
    """
    if progress_callback is None:
        return

    # Vérifier si c'est un signal Qt (a une méthode .emit)
    if hasattr(progress_callback, 'emit'):
        progress_callback.emit(*args, **kwargs)
    else:
        # Fonction normale
        progress_callback(*args, **kwargs)


# ============================================================
# 1. GESTION DES OPÉRATIONS BATCH (tracking)
# ============================================================

def create_batch_operation(
    operation_type: str,
    description: str,
    nb_personnel: int,
    created_by: str = None
) -> Optional[int]:
    """
    Crée un enregistrement de suivi pour une opération en masse.

    Args:
        operation_type: Type d'opération (FORMATION, ABSENCE, VISITE_MEDICALE)
        description: Description de l'opération
        nb_personnel: Nombre de personnel ciblé
        created_by: Utilisateur ayant lancé l'opération

    Returns:
        ID de l'opération batch ou None en cas d'erreur
    """
    try:
        return QueryExecutor.execute_write("""
            INSERT INTO batch_operations
            (operation_type, description, nb_personnel, created_by, status)
            VALUES (%s, %s, %s, %s, 'EN_COURS')
        """, (operation_type, description, nb_personnel, created_by),
            return_lastrowid=True)
    except Exception as e:
        logger.error(f"Erreur create_batch_operation: {e}")
        return None


def add_batch_detail(
    batch_id: int,
    personnel_id: int,
    status: str,
    record_id: int = None,
    error_message: str = None
):
    """
    Ajoute un détail à une opération batch.

    Args:
        batch_id: ID de l'opération batch
        personnel_id: ID du personnel
        status: SUCCES, ERREUR ou IGNORE
        record_id: ID de l'enregistrement créé
        error_message: Message d'erreur si échec
    """
    try:
        QueryExecutor.execute_write("""
            INSERT INTO batch_operation_details
            (batch_id, personnel_id, status, record_id, error_message)
            VALUES (%s, %s, %s, %s, %s)
        """, (batch_id, personnel_id, status, record_id, error_message))
    except Exception as e:
        logger.error(f"Erreur add_batch_detail: {e}")


def complete_batch_operation(
    batch_id: int,
    nb_success: int,
    nb_errors: int,
    status: str = 'TERMINE'
):
    """
    Marque une opération batch comme terminée.

    Args:
        batch_id: ID de l'opération batch
        nb_success: Nombre de succès
        nb_errors: Nombre d'erreurs
        status: TERMINE, ERREUR ou ANNULE
    """
    try:
        QueryExecutor.execute_write("""
            UPDATE batch_operations
            SET nb_success = %s, nb_errors = %s, status = %s, completed_at = NOW()
            WHERE id = %s
        """, (nb_success, nb_errors, status, batch_id))
    except Exception as e:
        logger.error(f"Erreur complete_batch_operation: {e}")


# ============================================================
# 2. FORMATIONS EN MASSE
# ============================================================

def add_formation_batch(
    personnel_ids: List[int],
    formation_data: Dict[str, Any],
    progress_callback: Optional[Callable[[int, str], None]] = None,
    created_by: str = None
) -> Tuple[int, int, List[Dict]]:
    """
    Ajoute une formation à plusieurs employés.

    Args:
        personnel_ids: Liste des IDs de personnel
        formation_data: Dict avec intitule, organisme, date_debut, date_fin, etc.
        progress_callback: Callback(percentage, message) pour la progression
        created_by: Utilisateur ayant lancé l'opération

    Returns:
        (nb_success, nb_errors, details_list)
    """
    require('rh.bulk_operations.formations')

    if not personnel_ids:
        return 0, 0, []

    # Créer le tracking batch
    batch_id = create_batch_operation(
        'FORMATION',
        formation_data.get('intitule', 'Formation'),
        len(personnel_ids),
        created_by
    )

    details = []
    nb_success = 0
    nb_errors = 0
    total = len(personnel_ids)

    # Préparer le service de documents si un fichier est fourni
    doc_service = None
    categorie_formation_id = None
    document_path = formation_data.get('document_path')

    if document_path:
        doc_service = DocumentService()
        categorie_formation_id = _get_categorie_id_by_name("Diplômes et formations")
        if not categorie_formation_id:
            logger.warning("Catégorie 'Diplômes et formations' introuvable - documents ne seront pas ajoutés")

    for i, personnel_id in enumerate(personnel_ids):
        _emit_progress(
            progress_callback,
            int((i / total) * 100),
            f"Traitement {i + 1}/{total}..."
        )

        try:
            # Insérer la formation
            formation_id = QueryExecutor.execute_write("""
                INSERT INTO formation (
                    operateur_id, intitule, organisme, date_debut, date_fin,
                    duree_heures, statut, certificat_obtenu, cout, commentaire
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                personnel_id,
                formation_data.get('intitule'),
                formation_data.get('organisme'),
                formation_data.get('date_debut'),
                formation_data.get('date_fin'),
                formation_data.get('duree_heures'),
                formation_data.get('statut', 'Planifiée'),
                formation_data.get('certificat_obtenu', False),
                formation_data.get('cout'),
                formation_data.get('commentaire')
            ), return_lastrowid=True)

            # Ajouter le document si fourni
            if doc_service and document_path and categorie_formation_id:
                try:
                    success, message, document_id = doc_service.add_document(
                        personnel_id=personnel_id,
                        categorie_id=categorie_formation_id,
                        fichier_source=document_path,
                        nom_affichage=f"Attestation - {formation_data.get('intitule', 'Formation')}",
                        notes=f"Document associé à la formation du {formation_data.get('date_debut')}",
                        uploaded_by=created_by or "Système"
                    )

                    if success and document_id:
                        # Lier le document à la formation
                        QueryExecutor.execute_write(
                            "UPDATE documents SET formation_id = %s WHERE id = %s",
                            (formation_id, document_id)
                        )
                        logger.debug(f"Document {document_id} lié à la formation {formation_id}")
                    else:
                        logger.warning(f"Échec ajout document pour formation {formation_id}: {message}")
                except Exception as doc_error:
                    logger.error(f"Erreur ajout document pour formation {formation_id}: {doc_error}")

            nb_success += 1

            details.append({
                'personnel_id': personnel_id,
                'status': 'SUCCES',
                'record_id': formation_id
            })

            if batch_id:
                add_batch_detail(batch_id, personnel_id, 'SUCCES', formation_id)

        except Exception as e:
            nb_errors += 1
            error_msg = str(e)
            details.append({
                'personnel_id': personnel_id,
                'status': 'ERREUR',
                'error': error_msg
            })
            if batch_id:
                add_batch_detail(batch_id, personnel_id, 'ERREUR', error_message=error_msg)
            logger.error(f"Erreur formation batch pour personnel {personnel_id}: {e}")

    # Finaliser le batch
    if batch_id:
        complete_batch_operation(batch_id, nb_success, nb_errors)

    # Log historique
    log_hist(
        action="FORMATION_BATCH",
        table_name="formation",
        description=f"Formation '{formation_data.get('intitule')}' assignée à {nb_success} personnes ({nb_errors} erreurs)"
    )

    _emit_progress(progress_callback, 100, "Terminé")

    return nb_success, nb_errors, details


# ============================================================
# 3. ABSENCES EN MASSE
# ============================================================

def add_absence_batch(
    personnel_ids: List[int],
    absence_data: Dict[str, Any],
    progress_callback: Optional[Callable[[int, str], None]] = None,
    created_by: str = None
) -> Tuple[int, int, List[Dict]]:
    """
    Crée une demande d'absence pour plusieurs employés.

    Args:
        personnel_ids: Liste des IDs de personnel
        absence_data: Dict avec type_absence_code, date_debut, date_fin, motif, etc.
        progress_callback: Callback(percentage, message) pour la progression
        created_by: Utilisateur ayant lancé l'opération

    Returns:
        (nb_success, nb_errors, details_list)
    """
    require('rh.bulk_operations.absences')

    if not personnel_ids:
        return 0, 0, []

    # Récupérer l'ID du type d'absence
    type_absence_id = None
    type_absence_code = absence_data.get('type_absence_code')

    try:
        row = QueryExecutor.fetch_one(
            "SELECT id FROM type_absence WHERE code = %s",
            (type_absence_code,),
            dictionary=True
        )
        if row:
            type_absence_id = row['id']
    except Exception as e:
        logger.error(f"Type d'absence introuvable: {e}")
        return 0, len(personnel_ids), [{'personnel_id': pid, 'status': 'ERREUR', 'error': f"Type d'absence '{type_absence_code}' introuvable"} for pid in personnel_ids]

    if not type_absence_id:
        return 0, len(personnel_ids), [{'personnel_id': pid, 'status': 'ERREUR', 'error': f"Type d'absence '{type_absence_code}' introuvable"} for pid in personnel_ids]

    # Créer le tracking batch
    batch_id = create_batch_operation(
        'ABSENCE',
        f"{type_absence_code} - {absence_data.get('date_debut')} au {absence_data.get('date_fin')}",
        len(personnel_ids),
        created_by
    )

    details = []
    nb_success = 0
    nb_errors = 0
    total = len(personnel_ids)

    # Préparer le service de documents si un justificatif est fourni
    doc_service = None
    categorie_admin_id = None
    document_path = absence_data.get('document_path')

    if document_path:
        doc_service = DocumentService()
        categorie_admin_id = _get_categorie_id_by_name("Documents administratifs")
        if not categorie_admin_id:
            logger.warning("Catégorie 'Documents administratifs' introuvable - justificatifs ne seront pas ajoutés")

    # Calculer le nombre de jours
    from core.services.absence_service_crud import calculer_jours_ouvres
    nb_jours = calculer_jours_ouvres(
        absence_data.get('date_debut'),
        absence_data.get('date_fin'),
        absence_data.get('demi_journee_debut', 'JOURNEE'),
        absence_data.get('demi_journee_fin', 'JOURNEE')
    )

    for i, personnel_id in enumerate(personnel_ids):
        _emit_progress(
            progress_callback,
            int((i / total) * 100),
            f"Traitement {i + 1}/{total}..."
        )

        try:
            demande_id = QueryExecutor.execute_write("""
                INSERT INTO demande_absence
                (personnel_id, type_absence_id, date_debut, date_fin,
                 demi_journee_debut, demi_journee_fin, nb_jours, motif, statut)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                personnel_id,
                type_absence_id,
                absence_data.get('date_debut'),
                absence_data.get('date_fin'),
                absence_data.get('demi_journee_debut', 'JOURNEE'),
                absence_data.get('demi_journee_fin', 'JOURNEE'),
                nb_jours,
                absence_data.get('motif', ''),
                absence_data.get('statut', 'EN_ATTENTE')
            ), return_lastrowid=True)

            # Ajouter le justificatif si fourni
            if doc_service and document_path and categorie_admin_id:
                try:
                    success, message, document_id = doc_service.add_document(
                        personnel_id=personnel_id,
                        categorie_id=categorie_admin_id,
                        fichier_source=document_path,
                        nom_affichage=f"Justificatif absence - {type_absence_code}",
                        notes=f"Justificatif pour absence du {absence_data.get('date_debut')} au {absence_data.get('date_fin')}",
                        uploaded_by=created_by or "Système"
                    )

                    if not success:
                        logger.warning(f"Échec ajout justificatif pour absence {demande_id}: {message}")
                    else:
                        logger.debug(f"Justificatif {document_id} ajouté pour absence {demande_id}")
                except Exception as doc_error:
                    logger.error(f"Erreur ajout justificatif pour absence {demande_id}: {doc_error}")

            nb_success += 1

            details.append({
                'personnel_id': personnel_id,
                'status': 'SUCCES',
                'record_id': demande_id
            })

            if batch_id:
                add_batch_detail(batch_id, personnel_id, 'SUCCES', demande_id)

        except Exception as e:
            nb_errors += 1
            error_msg = str(e)
            details.append({
                'personnel_id': personnel_id,
                'status': 'ERREUR',
                'error': error_msg
            })
            if batch_id:
                add_batch_detail(batch_id, personnel_id, 'ERREUR', error_message=error_msg)
            logger.error(f"Erreur absence batch pour personnel {personnel_id}: {e}")

    # Finaliser le batch
    if batch_id:
        complete_batch_operation(batch_id, nb_success, nb_errors)

    # Log historique
    log_hist(
        action="ABSENCE_BATCH",
        table_name="demande_absence",
        description=f"Absence '{type_absence_code}' assignée à {nb_success} personnes ({nb_errors} erreurs)"
    )

    _emit_progress(progress_callback, 100, "Terminé")

    return nb_success, nb_errors, details


# ============================================================
# 4. VISITES MÉDICALES EN MASSE
# ============================================================

def add_visite_batch(
    personnel_ids: List[int],
    visite_data: Dict[str, Any],
    progress_callback: Optional[Callable[[int, str], None]] = None,
    created_by: str = None
) -> Tuple[int, int, List[Dict]]:
    """
    Crée une visite médicale pour plusieurs employés.

    Args:
        personnel_ids: Liste des IDs de personnel
        visite_data: Dict avec date_visite, type_visite, medecin, etc.
        progress_callback: Callback(percentage, message) pour la progression
        created_by: Utilisateur ayant lancé l'opération

    Returns:
        (nb_success, nb_errors, details_list)
    """
    require('rh.bulk_operations.medical')

    if not personnel_ids:
        return 0, 0, []

    # Créer le tracking batch
    batch_id = create_batch_operation(
        'VISITE_MEDICALE',
        f"{visite_data.get('type_visite', 'Visite')} - {visite_data.get('date_visite')}",
        len(personnel_ids),
        created_by
    )

    details = []
    nb_success = 0
    nb_errors = 0
    total = len(personnel_ids)

    # Préparer le service de documents si une fiche d'aptitude est fournie
    doc_service = None
    categorie_medical_id = None
    document_path = visite_data.get('document_path')

    if document_path:
        doc_service = DocumentService()
        categorie_medical_id = _get_categorie_id_by_name("Certificats médicaux")
        if not categorie_medical_id:
            logger.warning("Catégorie 'Certificats médicaux' introuvable - documents ne seront pas ajoutés")

    for i, personnel_id in enumerate(personnel_ids):
        _emit_progress(
            progress_callback,
            int((i / total) * 100),
            f"Traitement {i + 1}/{total}..."
        )

        try:
            visite_id = QueryExecutor.execute_write("""
                INSERT INTO medical_visite (
                    operateur_id, date_visite, type_visite, resultat,
                    restrictions, medecin, commentaire, prochaine_visite
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                personnel_id,
                visite_data.get('date_visite'),
                visite_data.get('type_visite', 'Périodique'),
                visite_data.get('resultat'),
                visite_data.get('restrictions'),
                visite_data.get('medecin'),
                visite_data.get('commentaire'),
                visite_data.get('prochaine_visite')
            ), return_lastrowid=True)

            # Ajouter le document médical si fourni
            if doc_service and document_path and categorie_medical_id:
                try:
                    success, message, document_id = doc_service.add_document(
                        personnel_id=personnel_id,
                        categorie_id=categorie_medical_id,
                        fichier_source=document_path,
                        nom_affichage=f"Fiche aptitude - {visite_data.get('type_visite', 'Visite')}",
                        notes=f"Document pour visite {visite_data.get('type_visite')} du {visite_data.get('date_visite')}",
                        uploaded_by=created_by or "Système"
                    )

                    if not success:
                        logger.warning(f"Échec ajout document médical pour visite {visite_id}: {message}")
                    else:
                        logger.debug(f"Document médical {document_id} ajouté pour visite {visite_id}")
                except Exception as doc_error:
                    logger.error(f"Erreur ajout document médical pour visite {visite_id}: {doc_error}")

            nb_success += 1

            details.append({
                'personnel_id': personnel_id,
                'status': 'SUCCES',
                'record_id': visite_id
            })

            if batch_id:
                add_batch_detail(batch_id, personnel_id, 'SUCCES', visite_id)

        except Exception as e:
            nb_errors += 1
            error_msg = str(e)
            details.append({
                'personnel_id': personnel_id,
                'status': 'ERREUR',
                'error': error_msg
            })
            if batch_id:
                add_batch_detail(batch_id, personnel_id, 'ERREUR', error_message=error_msg)
            logger.error(f"Erreur visite batch pour personnel {personnel_id}: {e}")

    # Finaliser le batch
    if batch_id:
        complete_batch_operation(batch_id, nb_success, nb_errors)

    # Log historique
    log_hist(
        action="VISITE_MEDICALE_BATCH",
        table_name="medical_visite",
        description=f"Visite '{visite_data.get('type_visite')}' assignée à {nb_success} personnes ({nb_errors} erreurs)"
    )

    _emit_progress(progress_callback, 100, "Terminé")

    return nb_success, nb_errors, details


# ============================================================
# 5. COMPÉTENCES EN MASSE
# ============================================================

def add_competence_batch(
    personnel_ids: List[int],
    competence_data: Dict[str, Any],
    progress_callback: Optional[Callable[[int, str], None]] = None,
    created_by: str = None
) -> Tuple[int, int, List[Dict]]:
    """
    Assigne une compétence à plusieurs employés.

    Args:
        personnel_ids: Liste des IDs de personnel
        competence_data: Dict avec competence_id, date_acquisition, date_expiration, commentaire
        progress_callback: Callback(percentage, message) pour la progression
        created_by: Utilisateur ayant lancé l'opération

    Returns:
        (nb_success, nb_errors, details_list)
    """
    require('rh.competences.edit')

    if not personnel_ids:
        return 0, 0, []

    competence_id = competence_data.get('competence_id')
    competence_libelle = competence_data.get('competence_libelle', 'Compétence')

    # Si pas d'ID mais un libellé libre, créer la compétence dans le catalogue
    if not competence_id and competence_libelle:
        from core.services.competences_service import create_competence
        import re
        # Générer un code à partir du libellé
        code = re.sub(r'[^A-Z0-9]', '', competence_libelle.upper().replace(' ', '_'))[:20]
        code = f"LIBRE_{code}" if code else f"LIBRE_{id(competence_libelle)}"
        success, msg, new_id = create_competence(
            code=code,
            libelle=competence_libelle,
            categorie="Autre",
            description="Compétence ajoutée via saisie libre"
        )
        if success and new_id:
            competence_id = new_id
            competence_data['competence_id'] = new_id
        else:
            # Si le code existe déjà, chercher par libellé
            existing = QueryExecutor.fetch_one(
                "SELECT id FROM competences_catalogue WHERE libelle = %s AND actif = 1",
                (competence_libelle,),
                dictionary=True
            )
            if existing:
                competence_id = existing['id']
                competence_data['competence_id'] = existing['id']
            else:
                return 0, len(personnel_ids), [{'personnel_id': pid, 'status': 'ERREUR', 'error': f"Impossible de créer la compétence: {msg}"} for pid in personnel_ids]

    if not competence_id:
        return 0, len(personnel_ids), [{'personnel_id': pid, 'status': 'ERREUR', 'error': "Compétence non spécifiée"} for pid in personnel_ids]

    # Récupérer le libellé de la compétence pour le tracking
    if not competence_libelle or competence_libelle == 'Compétence':
        try:
            row = QueryExecutor.fetch_one(
                "SELECT libelle FROM competences_catalogue WHERE id = %s",
                (competence_id,),
                dictionary=True
            )
            if row:
                competence_libelle = row['libelle']
        except Exception as e:
            logger.error(f"Erreur récupération libellé compétence: {e}")

    # Créer le tracking batch
    batch_id = create_batch_operation(
        'COMPETENCE',
        f"{competence_libelle} - {competence_data.get('date_acquisition')}",
        len(personnel_ids),
        created_by
    )

    details = []
    nb_success = 0
    nb_errors = 0
    total = len(personnel_ids)

    # Préparer le service de documents si une attestation est fournie
    doc_service = None
    categorie_formation_id = None
    document_path = competence_data.get('document_path')

    if document_path:
        doc_service = DocumentService()
        categorie_formation_id = _get_categorie_id_by_name("Diplômes et formations")
        if not categorie_formation_id:
            logger.warning("Catégorie 'Diplômes et formations' introuvable - attestations ne seront pas ajoutées")

    for i, personnel_id in enumerate(personnel_ids):
        _emit_progress(
            progress_callback,
            int((i / total) * 100),
            f"Traitement {i + 1}/{total}..."
        )

        try:
            # Vérifier si déjà assignée (pour éviter les doublons)
            existing = QueryExecutor.fetch_one("""
                SELECT id FROM personnel_competences
                WHERE personnel_id = %s AND competence_id = %s
            """, (personnel_id, competence_id), dictionary=True)

            if existing:
                # Mettre à jour au lieu de créer
                QueryExecutor.execute_write("""
                    UPDATE personnel_competences
                    SET date_acquisition = %s, date_expiration = %s, commentaire = %s
                    WHERE personnel_id = %s AND competence_id = %s
                """, (
                    competence_data.get('date_acquisition'),
                    competence_data.get('date_expiration'),
                    competence_data.get('commentaire'),
                    personnel_id,
                    competence_id
                ))
                record_id = existing['id']
            else:
                # Créer une nouvelle assignation
                record_id = QueryExecutor.execute_write("""
                    INSERT INTO personnel_competences
                    (personnel_id, competence_id, date_acquisition, date_expiration, commentaire)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    personnel_id,
                    competence_id,
                    competence_data.get('date_acquisition'),
                    competence_data.get('date_expiration'),
                    competence_data.get('commentaire')
                ), return_lastrowid=True)

            # Ajouter l'attestation de compétence si fournie
            if doc_service and document_path and categorie_formation_id:
                try:
                    success, message, document_id = doc_service.add_document(
                        personnel_id=personnel_id,
                        categorie_id=categorie_formation_id,
                        fichier_source=document_path,
                        nom_affichage=f"Attestation - {competence_libelle}",
                        notes=f"Attestation pour compétence acquise le {competence_data.get('date_acquisition')}",
                        date_expiration=competence_data.get('date_expiration'),
                        uploaded_by=created_by or "Système"
                    )

                    if not success:
                        logger.warning(f"Échec ajout attestation pour compétence {record_id}: {message}")
                    else:
                        logger.debug(f"Attestation {document_id} ajoutée pour compétence {record_id}")
                except Exception as doc_error:
                    logger.error(f"Erreur ajout attestation pour compétence {record_id}: {doc_error}")

            nb_success += 1

            details.append({
                'personnel_id': personnel_id,
                'status': 'SUCCES',
                'record_id': record_id
            })

            if batch_id:
                add_batch_detail(batch_id, personnel_id, 'SUCCES', record_id)

        except Exception as e:
            nb_errors += 1
            error_msg = str(e)
            details.append({
                'personnel_id': personnel_id,
                'status': 'ERREUR',
                'error': error_msg
            })
            if batch_id:
                add_batch_detail(batch_id, personnel_id, 'ERREUR', error_message=error_msg)
            logger.error(f"Erreur compétence batch pour personnel {personnel_id}: {e}")

    # Finaliser le batch
    if batch_id:
        complete_batch_operation(batch_id, nb_success, nb_errors)

    # Log historique
    log_hist(
        action="COMPETENCE_BATCH",
        table_name="personnel_competences",
        description=f"Compétence '{competence_libelle}' assignée à {nb_success} personnes ({nb_errors} erreurs)"
    )

    _emit_progress(progress_callback, 100, "Terminé")

    return nb_success, nb_errors, details


# ============================================================
# 6. UTILITAIRES
# ============================================================

def get_personnel_list_for_bulk() -> List[Dict]:
    """
    Récupère la liste du personnel pour les opérations en masse.

    Returns:
        Liste des opérateurs (id, nom, prenom, matricule, statut)
    """
    try:
        return QueryExecutor.fetch_all("""
            SELECT id, nom, prenom, matricule, statut
            FROM personnel
            WHERE statut = 'ACTIF'
            ORDER BY nom, prenom
        """, dictionary=True)
    except Exception as e:
        logger.error(f"Erreur get_personnel_list_for_bulk: {e}")
        return []


def get_batch_operations_history(limit: int = 50) -> List[Dict]:
    """
    Récupère l'historique des opérations batch.

    Args:
        limit: Nombre maximum d'enregistrements

    Returns:
        Liste des opérations batch
    """
    try:
        return QueryExecutor.fetch_all("""
            SELECT *
            FROM v_batch_operations_stats
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,), dictionary=True)
    except Exception as e:
        logger.error(f"Erreur get_batch_operations_history: {e}")
        return []


def get_batch_operation_details(batch_id: int) -> List[Dict]:
    """
    Récupère les détails d'une opération batch.

    Args:
        batch_id: ID de l'opération batch

    Returns:
        Liste des détails avec infos personnel
    """
    try:
        return QueryExecutor.fetch_all("""
            SELECT
                bod.*,
                p.nom,
                p.prenom,
                p.matricule
            FROM batch_operation_details bod
            JOIN personnel p ON bod.personnel_id = p.id
            WHERE bod.batch_id = %s
            ORDER BY p.nom, p.prenom
        """, (batch_id,), dictionary=True)
    except Exception as e:
        logger.error(f"Erreur get_batch_operation_details: {e}")
        return []
