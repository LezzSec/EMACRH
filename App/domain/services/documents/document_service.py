# -*- coding: utf-8 -*-
"""
Service de gestion documentaire
Gere le stockage, la recuperation et la manipulation des documents des operateurs.

Stockage : Les fichiers sont stockes en BLOB dans la base de donnees MySQL.
Les anciens documents sur filesystem (legacy) restent accessibles via chemin_fichier.
"""

import unicodedata

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)
from datetime import date
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.storage.file_storage import (
    sanitize_filename, get_temp_base, extract_blob_to_temp, read_upload, UploadError
)


# Taille max recommandee pour un fichier (16 Mo)
MAX_FILE_SIZE_BYTES = 16 * 1024 * 1024


class DocumentService:
    """Service de gestion des documents des operateurs (stockage BLOB en base)"""

    def __init__(self):
        """Initialise le service documentaire"""
        # Repertoire temporaire pour extraire les BLOBs a ouvrir
        self._temp_dir = get_temp_base() / "emac_documents"
        self._temp_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        return sanitize_filename(filename)

    @staticmethod
    def _get_safe_name(text: str) -> str:
        """Convertit un texte en nom de dossier safe (sans accents, sans caracteres speciaux)."""
        normalized = unicodedata.normalize('NFKD', text)
        ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        safe = []
        for c in ascii_text:
            if c.isalnum() or c == '-':
                safe.append(c)
            elif c in (' ', '_'):
                safe.append('_')
        return ''.join(safe) or 'inconnu'

    def _get_person_folder_name(self, personnel_id: int) -> Optional[str]:
        """Retourne le nom de dossier pour une personne : NOM_Prenom_Matricule."""
        try:
            row = QueryExecutor.fetch_one(
                "SELECT nom, prenom, matricule FROM personnel WHERE id = %s",
                (personnel_id,), dictionary=True
            )
            if not row:
                return None
            nom = self._get_safe_name(row.get('nom', '') or '').upper()
            prenom = self._get_safe_name(row.get('prenom', '') or '')
            matricule = self._get_safe_name(row.get('matricule', '') or '')
            parts = [p for p in [nom, prenom, matricule] if p]
            return '_'.join(parts)
        except Exception as e:
            logger.warning(f"Impossible de resoudre le nom du dossier personnel {personnel_id}: {e}")
            return None

    def _get_categorie_folder_name(self, categorie_id: int) -> str:
        """Retourne le nom de dossier pour une categorie."""
        try:
            row = QueryExecutor.fetch_one(
                "SELECT nom FROM categories_documents WHERE id = %s",
                (categorie_id,), dictionary=True
            )
            if row and row.get('nom'):
                return self._get_safe_name(row['nom']) or f"categorie_{categorie_id}"
        except Exception:
            pass
        return f"categorie_{categorie_id}"

    def _sync_to_person_folder(self, personnel_id: int, categorie_id: int, nom_fichier: str, contenu: bytes) -> None:
        """Miroir best-effort sur le filesystem (EMAC/dossiers/{personne}/{categorie}/).

        Source de vérité = BLOB en base. Cette copie FS n'existe que pour permettre
        aux RH de naviguer dans l'explorateur Windows. Une désynchro DB/FS est possible
        et acceptée : si ce miroir échoue, le document reste accessible via l'application.
        Ne jamais utiliser ce chemin comme source autoritaire de contenu.
        """
        try:
            from infrastructure.config.app_paths import get_dossiers_dir
            person_name = self._get_person_folder_name(personnel_id)
            if not person_name:
                return
            cat_name = self._get_categorie_folder_name(categorie_id)
            target_dir = get_dossiers_dir() / person_name / cat_name
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / nom_fichier
            with open(target_file, 'wb') as f:
                f.write(contenu)
        except Exception as e:
            logger.warning(f"Sync dossier personnel impossible (personnel_id={personnel_id}): {e}")

    def _remove_from_person_folder(self, personnel_id: int, categorie_id: int, nom_fichier: str) -> None:
        """Supprime la copie du document dans EMAC/dossiers/{personne}/{categorie}/."""
        try:
            from infrastructure.config.app_paths import get_dossiers_dir
            person_name = self._get_person_folder_name(personnel_id)
            if not person_name:
                return
            cat_name = self._get_categorie_folder_name(categorie_id)
            target_file = get_dossiers_dir() / person_name / cat_name / nom_fichier
            if target_file.exists():
                target_file.unlink()
        except Exception as e:
            logger.warning(f"Suppression dossier personnel impossible (personnel_id={personnel_id}): {e}")

    def _move_to_historique(self, personnel_id: int, categorie_id: int, nom_fichier: str, document_id: int = None) -> bool:
        """Deplace (ou copie depuis BLOB) un document vers Historique/ dans le dossier personnel.

        Retourne True si l'operation a reussi, False sinon.
        """
        try:
            from infrastructure.config.app_paths import get_dossiers_dir
            from datetime import datetime
            person_name = self._get_person_folder_name(personnel_id)
            if not person_name:
                return False
            cat_name = self._get_categorie_folder_name(categorie_id)
            historique_dir = get_dossiers_dir() / person_name / 'Historique'
            historique_dir.mkdir(parents=True, exist_ok=True)
            dest = historique_dir / nom_fichier
            if dest.exists():
                suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
                stem = Path(nom_fichier).stem
                ext = Path(nom_fichier).suffix
                dest = historique_dir / f"{stem}_{suffix}{ext}"
            source = get_dossiers_dir() / person_name / cat_name / nom_fichier
            if source.exists():
                source.rename(dest)
            elif document_id is not None:
                result = self.get_document_content(document_id)
                if result:
                    contenu, _, _ = result
                    with open(dest, 'wb') as f:
                        f.write(contenu)
            return True
        except Exception as e:
            logger.warning(f"Deplacement vers Historique impossible (personnel_id={personnel_id}): {e}")
            return False

    def add_document(
        self,
        personnel_id: int,
        categorie_id: int,
        fichier_source: str,
        nom_affichage: str = None,
        date_expiration: date = None,
        notes: str = None,
        uploaded_by: str = "Systeme",
        formation_id: int = None,
        contrat_id: int = None,
        declaration_id: int = None,
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Ajoute un document pour un operateur (stocke en BLOB dans la base).

        Args:
            personnel_id: ID de l'operateur
            categorie_id: ID de la categorie
            fichier_source: Chemin du fichier a ajouter
            nom_affichage: Nom d'affichage (optionnel, sinon nom du fichier)
            date_expiration: Date d'expiration (optionnel)
            notes: Notes sur le document
            uploaded_by: Nom de l'utilisateur qui uploade
            formation_id: Formation liee (optionnel)
            contrat_id: Contrat lie (optionnel)
            declaration_id: Declaration liee (optionnel)

        Returns:
            (succes, message, document_id)
        """
        from application.permission_manager import require
        require("rh.documents.edit")

        try:
            contenu_fichier, type_mime, taille_octets = read_upload(fichier_source, MAX_FILE_SIZE_BYTES)
        except UploadError as e:
            return False, str(e), None

        source_path = Path(fichier_source)

        try:
            # Verifier que l'operateur existe
            if not QueryExecutor.exists('personnel', {'id': personnel_id}):
                return False, f"Operateur ID {personnel_id} introuvable", None

            # Verifier que la categorie existe
            if not QueryExecutor.exists('categories_documents', {'id': categorie_id}):
                return False, f"Categorie ID {categorie_id} introuvable", None

            # Preparer le nom de fichier
            nom_fichier_original = source_path.name
            nom_fichier_clean = sanitize_filename(nom_fichier_original)

            if nom_affichage is None:
                nom_affichage = nom_fichier_original

            document_id = QueryExecutor.execute_write(
                """INSERT INTO documents (
                    personnel_id, categorie_id, formation_id, contrat_id, declaration_id,
                    nom_fichier, nom_affichage,
                    chemin_fichier, contenu_fichier, stockage_type,
                    type_mime, taille_octets, date_expiration,
                    notes, uploaded_by
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, 'BLOB',
                    %s, %s, %s, %s, %s
                )""",
                (
                    personnel_id, categorie_id, formation_id, contrat_id, declaration_id,
                    nom_fichier_clean, nom_affichage,
                    nom_fichier_clean,
                    contenu_fichier,
                    type_mime, taille_octets, date_expiration,
                    notes, uploaded_by
                )
            )

            logger.info(f"Document '{nom_affichage}' ajoute en BLOB (ID: {document_id}, {taille_octets} octets)")
            self._sync_to_person_folder(personnel_id, categorie_id, nom_fichier_clean, contenu_fichier)  # miroir FS best-effort
            return True, f"Document '{nom_affichage}' ajoute avec succes", document_id

        except Exception as e:
            logger.exception(f"Erreur lors de l'ajout du document: {e}")
            return False, f"Erreur lors de l'ajout du document: {str(e)}", None

    def get_documents_operateur(
        self,
        personnel_id: int,
        categorie_id: int = None,
        statut: str = None
    ) -> List[Dict]:
        """
        Recupere les documents d'un operateur (metadonnees uniquement, sans le BLOB).

        Args:
            personnel_id: ID de l'operateur
            categorie_id: Filtrer par categorie (optionnel)
            statut: Filtrer par statut (optionnel)

        Returns:
            Liste des documents (sans contenu_fichier)
        """
        try:
            sql = "SELECT * FROM v_documents_complet WHERE personnel_id = %s"
            params = [personnel_id]

            if categorie_id is not None:
                sql += " AND categorie_id = %s"
                params.append(categorie_id)

            if statut is not None:
                sql += " AND statut = %s"
                params.append(statut)

            sql += " ORDER BY date_upload DESC"

            return QueryExecutor.fetch_all(sql, tuple(params), dictionary=True)

        except Exception as e:
            logger.error(f"Erreur lors de la recuperation des documents: {e}")
            return []

    def get_document_content(self, document_id: int) -> Optional[Tuple[bytes, str, str]]:
        """
        Recupere le contenu binaire d'un document depuis la base.

        Args:
            document_id: ID du document

        Returns:
            Tuple (contenu_bytes, nom_fichier, type_mime) ou None si introuvable
        """
        try:
            doc = QueryExecutor.fetch_one(
                "SELECT contenu_fichier, stockage_type, chemin_fichier, nom_fichier, type_mime "
                "FROM documents WHERE id = %s",
                (document_id,),
                dictionary=True
            )

            if not doc:
                return None

            # Document stocke en BLOB
            if doc['stockage_type'] == 'BLOB' and doc['contenu_fichier']:
                return (doc['contenu_fichier'], doc['nom_fichier'], doc['type_mime'])

            # Legacy: document sur filesystem
            if doc['chemin_fichier']:
                legacy_path = self._resolve_legacy_path(doc['chemin_fichier'])
                if legacy_path and legacy_path.exists():
                    with open(legacy_path, 'rb') as f:
                        return (f.read(), doc['nom_fichier'], doc['type_mime'])

            logger.warning(f"Document ID {document_id}: contenu introuvable")
            return None

        except Exception as e:
            logger.error(f"Erreur lors de la recuperation du contenu: {e}")
            return None

    def extract_to_temp_file(self, document_id: int) -> Optional[Path]:
        """
        Extrait un document BLOB vers un fichier temporaire pour ouverture.

        Args:
            document_id: ID du document

        Returns:
            Path vers le fichier temporaire, ou None si erreur
        """
        result = self.get_document_content(document_id)
        if not result:
            return None

        contenu, nom_fichier, _ = result

        try:
            return extract_blob_to_temp(contenu, nom_fichier, "emac_documents", document_id)
        except PermissionError:
            # Fichier verrouillé par une application tierce (ex : Excel ouvert).
            # On le retourne tel quel uniquement si un contenu existe déjà.
            temp_path = self._temp_dir / str(document_id) / sanitize_filename(nom_fichier)
            if temp_path.exists() and temp_path.stat().st_size > 0:
                return temp_path
            raise

    def get_document_path(self, document_id: int) -> Optional[Path]:
        """
        Retourne un chemin accessible pour un document.
        Pour les BLOBs, extrait vers un fichier temporaire.
        Pour les legacy filesystem, retourne le chemin direct.
        """
        try:
            doc = QueryExecutor.fetch_one(
                "SELECT stockage_type, chemin_fichier FROM documents WHERE id = %s",
                (document_id,),
                dictionary=True
            )

            if not doc:
                return None

            # BLOB: extraire vers fichier temporaire
            if doc['stockage_type'] == 'BLOB':
                return self.extract_to_temp_file(document_id)

            # Legacy filesystem
            legacy_path = self._resolve_legacy_path(doc['chemin_fichier'])
            if legacy_path and legacy_path.exists():
                return legacy_path

            return None

        except Exception as e:
            logger.error(f"Erreur lors de la recuperation du chemin: {e}")
            return None

    def _resolve_legacy_path(self, chemin_fichier: str) -> Optional[Path]:
        """Resout un chemin legacy (fichier sur filesystem)."""
        try:
            # Essayer d'abord avec get_documents_dir
            from infrastructure.config.app_paths import get_documents_dir
            base = get_documents_dir()
            full_path = base / chemin_fichier
            if full_path.exists():
                return full_path

            # Essayer comme chemin absolu
            abs_path = Path(chemin_fichier)
            if abs_path.exists():
                return abs_path

            return None
        except Exception:
            return None

    def delete_document(self, document_id: int) -> Tuple[bool, str]:
        """Archive le document au lieu de le supprimer definitivement (conservation de la trace)."""
        return self.archive_document(document_id)

    def hard_delete_document(self, document_id: int) -> Tuple[bool, str]:
        """
        Suppression definitive d'un document (BLOB en base + entree BDD).
        Reserver aux cas exceptionnels (RGPD, nettoyage admin).

        Args:
            document_id: ID du document

        Returns:
            (succes, message)
        """
        from application.permission_manager import require
        require("rh.documents.edit")
        try:
            doc = QueryExecutor.fetch_one(
                "SELECT stockage_type, chemin_fichier, nom_affichage, personnel_id, categorie_id, nom_fichier "
                "FROM documents WHERE id = %s",
                (document_id,),
                dictionary=True
            )

            if not doc:
                return False, "Document introuvable"

            if not self._move_to_historique(doc['personnel_id'], doc['categorie_id'], doc['nom_fichier'], document_id):
                logger.warning(
                    f"hard_delete_document: sauvegarde Historique impossible pour doc {document_id} "
                    f"('{doc['nom_affichage']}') — suppression DB continue quand meme"
                )

            if doc['stockage_type'] == 'FILESYSTEM' and doc['chemin_fichier']:
                legacy_path = self._resolve_legacy_path(doc['chemin_fichier'])
                if legacy_path and legacy_path.exists():
                    legacy_path.unlink()

            temp_path = self._temp_dir / str(document_id)
            if temp_path.exists():
                import shutil
                shutil.rmtree(temp_path, ignore_errors=True)

            QueryExecutor.execute_write(
                "DELETE FROM documents WHERE id = %s", (document_id,), return_lastrowid=False
            )

            logger.info(f"Document '{doc['nom_affichage']}' supprime definitivement (ID: {document_id})")
            return True, f"Document '{doc['nom_affichage']}' supprime avec succes"

        except Exception as e:
            logger.exception(f"Erreur lors de la suppression: {e}")
            return False, f"Erreur lors de la suppression: {str(e)}"

    def archive_document(self, document_id: int) -> Tuple[bool, str]:
        """Archive un document (change son statut) et le deplace dans Historique/."""
        from application.permission_manager import require
        require("rh.documents.edit")
        try:
            doc = QueryExecutor.fetch_one(
                "SELECT personnel_id, categorie_id, nom_fichier FROM documents WHERE id = %s",
                (document_id,), dictionary=True
            )
            QueryExecutor.execute_write(
                "UPDATE documents SET statut = 'archive' WHERE id = %s",
                (document_id,), return_lastrowid=False
            )
            if doc:
                self._move_to_historique(doc['personnel_id'], doc['categorie_id'], doc['nom_fichier'], document_id)
            return True, "Document archive avec succes"

        except Exception as e:
            return False, f"Erreur lors de l'archivage: {str(e)}"

    def restore_document(self, document_id: int) -> Tuple[bool, str]:
        """Restaure un document archive (remet son statut a actif)"""
        from application.permission_manager import require
        require("rh.documents.edit")
        try:
            QueryExecutor.execute_write(
                "UPDATE documents SET statut = 'actif' WHERE id = %s",
                (document_id,), return_lastrowid=False
            )
            return True, "Document restaure avec succes"

        except Exception as e:
            return False, f"Erreur lors de la restauration: {str(e)}"

    def get_categories(self) -> List[Dict]:
        """Recupere toutes les categories de documents"""
        try:
            return QueryExecutor.fetch_all(
                "SELECT * FROM categories_documents ORDER BY ordre_affichage",
                dictionary=True
            )
        except Exception as e:
            logger.error(f"Erreur lors de la recuperation des categories: {e}")
            return []

    def get_documents_expiring_soon(self, jours: int = 30) -> List[Dict]:
        """Recupere les documents qui expirent bientot"""
        try:
            return QueryExecutor.fetch_all(
                "SELECT * FROM v_documents_expiration_proche WHERE jours_restants <= %s",
                (jours,),
                dictionary=True
            )
        except Exception as e:
            logger.error(f"Erreur lors de la recuperation des documents expirant: {e}")
            return []

    def update_document_info(
        self,
        document_id: int,
        nom_affichage: str = None,
        date_expiration: date = None,
        notes: str = None,
        categorie_id: int = None
    ) -> Tuple[bool, str]:
        """Met a jour les informations d'un document"""
        from application.permission_manager import require
        require("rh.documents.edit")
        try:
            # SECURITE: Construction securisee - seules les clauses predefinies sont utilisees
            updates = []
            params = []

            if nom_affichage is not None:
                updates.append("nom_affichage = %s")
                params.append(nom_affichage)

            if date_expiration is not None:
                updates.append("date_expiration = %s")
                params.append(date_expiration)

            if notes is not None:
                updates.append("notes = %s")
                params.append(notes)

            if categorie_id is not None:
                updates.append("categorie_id = %s")
                params.append(categorie_id)

            if not updates:
                return False, "Aucune modification a effectuer"

            params.append(document_id)
            sql = "UPDATE documents SET " + ", ".join(updates) + " WHERE id = %s"

            QueryExecutor.execute_write(sql, tuple(params), return_lastrowid=False)
            return True, "Document mis a jour avec succes"

        except Exception as e:
            return False, f"Erreur lors de la mise a jour: {str(e)}"

    def download_document(self, document_id: int, destination: str) -> Tuple[bool, str]:
        """
        Telecharge un document depuis la base vers un fichier sur le disque.

        Args:
            document_id: ID du document
            destination: Chemin de destination sur le disque

        Returns:
            (succes, message)
        """
        result = self.get_document_content(document_id)
        if not result:
            return False, "Document introuvable ou contenu indisponible"

        contenu, nom_fichier, type_mime = result

        try:
            dest_path = Path(destination)
            with open(dest_path, 'wb') as f:
                f.write(contenu)

            logger.info(f"Document ID {document_id} telecharge vers {destination}")
            return True, f"Document telecharge avec succes vers:\n{destination}"
        except Exception as e:
            logger.exception(f"Erreur telechargement document: {e}")
            return False, f"Erreur lors du telechargement: {str(e)}"

    def get_document_nom(self, document_id: int) -> Optional[str]:
        """Retourne le nom de fichier affiché d'un document (nom_fichier)."""
        try:
            row = QueryExecutor.fetch_one(
                "SELECT nom_fichier FROM documents WHERE id = %s",
                (document_id,),
                dictionary=True,
            )
            return row['nom_fichier'] if row else None
        except Exception as e:
            logger.error(f"Erreur get_document_nom {document_id}: {e}")
            return None

    def check_module_installed(self) -> bool:
        """Vérifie que les tables du module documentaire existent."""
        try:
            cat_exists = QueryExecutor.fetch_one("SHOW TABLES LIKE 'categories_documents'")
            doc_exists = QueryExecutor.fetch_one("SHOW TABLES LIKE 'documents'")
            return bool(cat_exists and doc_exists)
        except Exception as e:
            logger.error(f"Erreur vérification tables documentaires: {e}")
            return False

    def get_all_non_contrats(self) -> list:
        """Retourne tous les documents hors catégorie 'Contrats de travail'."""
        try:
            return QueryExecutor.fetch_all(
                """
                SELECT * FROM v_documents_complet
                WHERE categorie_nom != 'Contrats de travail'
                ORDER BY date_upload DESC
                """,
                dictionary=True,
            )
        except Exception as e:
            logger.exception(f"Erreur get_all_non_contrats: {e}")
            return []
