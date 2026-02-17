# -*- coding: utf-8 -*-
"""
Service de gestion documentaire
Gere le stockage, la recuperation et la manipulation des documents des operateurs.

Stockage : Les fichiers sont stockes en BLOB dans la base de donnees MySQL.
Les anciens documents sur filesystem (legacy) restent accessibles via chemin_fichier.
"""

import os
import tempfile
import logging

logger = logging.getLogger(__name__)
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import mimetypes

from core.db.configbd import get_connection


# Taille max recommandee pour un fichier (16 Mo)
MAX_FILE_SIZE_BYTES = 16 * 1024 * 1024


class DocumentService:
    """Service de gestion des documents des operateurs (stockage BLOB en base)"""

    def __init__(self):
        """Initialise le service documentaire"""
        # Repertoire temporaire pour extraire les BLOBs a ouvrir
        self._temp_dir = Path(tempfile.gettempdir()) / "emac_documents"
        self._temp_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Nettoie un nom de fichier pour eviter les problemes"""
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in ['.', '-', '_', ' ']:
                safe_chars.append(char)
            else:
                safe_chars.append('_')
        return ''.join(safe_chars)

    def add_document(
        self,
        personnel_id: int,
        categorie_id: int,
        fichier_source: str,
        nom_affichage: str = None,
        date_expiration: date = None,
        notes: str = None,
        uploaded_by: str = "Systeme"
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

        Returns:
            (succes, message, document_id)
        """
        conn = None
        try:
            # Verifier que le fichier source existe
            source_path = Path(fichier_source)
            if not source_path.exists():
                return False, f"Fichier source introuvable: {fichier_source}", None

            # Verifier la taille du fichier
            taille_octets = source_path.stat().st_size
            if taille_octets > MAX_FILE_SIZE_BYTES:
                taille_mo = taille_octets / (1024 * 1024)
                return False, f"Fichier trop volumineux ({taille_mo:.1f} Mo). Maximum: 16 Mo", None

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Verifier que l'operateur existe
            cursor.execute(
                "SELECT id FROM personnel WHERE id = %s",
                (personnel_id,)
            )
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return False, f"Operateur ID {personnel_id} introuvable", None

            # Verifier que la categorie existe
            cursor.execute(
                "SELECT id FROM categories_documents WHERE id = %s",
                (categorie_id,)
            )
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return False, f"Categorie ID {categorie_id} introuvable", None

            # Preparer le nom de fichier
            nom_fichier_original = source_path.name
            nom_fichier_clean = self._sanitize_filename(nom_fichier_original)

            if nom_affichage is None:
                nom_affichage = nom_fichier_original

            # Lire le contenu du fichier en binaire
            with open(source_path, 'rb') as f:
                contenu_fichier = f.read()

            # Determiner le type MIME
            type_mime, _ = mimetypes.guess_type(str(source_path))
            if type_mime is None:
                type_mime = "application/octet-stream"

            # Inserer dans la base de donnees avec le BLOB
            sql = """
                INSERT INTO documents (
                    personnel_id, categorie_id, nom_fichier, nom_affichage,
                    chemin_fichier, contenu_fichier, stockage_type,
                    type_mime, taille_octets, date_expiration,
                    notes, uploaded_by
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, 'BLOB', %s, %s, %s, %s, %s
                )
            """

            cursor.execute(sql, (
                personnel_id, categorie_id, nom_fichier_clean, nom_affichage,
                nom_fichier_clean,  # chemin_fichier = nom du fichier (pour reference)
                contenu_fichier,
                type_mime, taille_octets, date_expiration,
                notes, uploaded_by
            ))

            document_id = cursor.lastrowid
            conn.commit()

            cursor.close()
            conn.close()

            logger.info(f"Document '{nom_affichage}' ajoute en BLOB (ID: {document_id}, {taille_octets} octets)")
            return True, f"Document '{nom_affichage}' ajoute avec succes", document_id

        except Exception as e:
            logger.exception(f"Erreur lors de l'ajout du document: {e}")
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
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
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = "SELECT * FROM v_documents_complet WHERE personnel_id = %s"
            params = [personnel_id]

            if categorie_id is not None:
                sql += " AND categorie_id = %s"
                params.append(categorie_id)

            if statut is not None:
                sql += " AND statut = %s"
                params.append(statut)

            sql += " ORDER BY date_upload DESC"

            cursor.execute(sql, tuple(params))
            documents = cursor.fetchall()

            cursor.close()
            conn.close()

            return documents

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
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT contenu_fichier, stockage_type, chemin_fichier, nom_fichier, type_mime "
                "FROM documents WHERE id = %s",
                (document_id,)
            )
            doc = cursor.fetchone()

            cursor.close()
            conn.close()

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

        contenu, nom_fichier, type_mime = result

        # Creer un sous-dossier par document pour eviter les conflits
        doc_temp_dir = self._temp_dir / str(document_id)
        doc_temp_dir.mkdir(parents=True, exist_ok=True)

        temp_path = doc_temp_dir / self._sanitize_filename(nom_fichier)

        with open(temp_path, 'wb') as f:
            f.write(contenu)

        return temp_path

    def get_document_path(self, document_id: int) -> Optional[Path]:
        """
        Retourne un chemin accessible pour un document.
        Pour les BLOBs, extrait vers un fichier temporaire.
        Pour les legacy filesystem, retourne le chemin direct.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT stockage_type, chemin_fichier FROM documents WHERE id = %s",
                (document_id,)
            )
            doc = cursor.fetchone()

            cursor.close()
            conn.close()

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
            from core.utils.app_paths import get_documents_dir
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
        """
        Supprime un document (BLOB en base + entree BDD).

        Args:
            document_id: ID du document

        Returns:
            (succes, message)
        """
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Recuperer les infos du document
            cursor.execute(
                "SELECT stockage_type, chemin_fichier, nom_affichage FROM documents WHERE id = %s",
                (document_id,)
            )
            doc = cursor.fetchone()

            if not doc:
                cursor.close()
                conn.close()
                return False, "Document introuvable"

            # Si legacy filesystem, supprimer le fichier physique
            if doc['stockage_type'] == 'FILESYSTEM' and doc['chemin_fichier']:
                legacy_path = self._resolve_legacy_path(doc['chemin_fichier'])
                if legacy_path and legacy_path.exists():
                    legacy_path.unlink()

            # Nettoyer le fichier temporaire s'il existe
            temp_path = self._temp_dir / str(document_id)
            if temp_path.exists():
                import shutil
                shutil.rmtree(temp_path, ignore_errors=True)

            # Supprimer de la BDD (le BLOB est supprime avec la ligne)
            cursor.execute("DELETE FROM documents WHERE id = %s", (document_id,))
            conn.commit()

            cursor.close()
            conn.close()

            logger.info(f"Document '{doc['nom_affichage']}' supprime (ID: {document_id})")
            return True, f"Document '{doc['nom_affichage']}' supprime avec succes"

        except Exception as e:
            logger.exception(f"Erreur lors de la suppression: {e}")
            return False, f"Erreur lors de la suppression: {str(e)}"

    def archive_document(self, document_id: int) -> Tuple[bool, str]:
        """Archive un document (change son statut)"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE documents SET statut = 'archive' WHERE id = %s",
                (document_id,)
            )
            conn.commit()

            cursor.close()
            conn.close()

            return True, "Document archive avec succes"

        except Exception as e:
            return False, f"Erreur lors de l'archivage: {str(e)}"

    def restore_document(self, document_id: int) -> Tuple[bool, str]:
        """Restaure un document archive (remet son statut a actif)"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE documents SET statut = 'actif' WHERE id = %s",
                (document_id,)
            )
            conn.commit()

            cursor.close()
            conn.close()

            return True, "Document restaure avec succes"

        except Exception as e:
            return False, f"Erreur lors de la restauration: {str(e)}"

    def get_categories(self) -> List[Dict]:
        """Recupere toutes les categories de documents"""
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM categories_documents ORDER BY ordre_affichage"
            )
            categories = cursor.fetchall()

            cursor.close()
            conn.close()

            return categories

        except Exception as e:
            logger.error(f"Erreur lors de la recuperation des categories: {e}")
            return []

    def get_documents_expiring_soon(self, jours: int = 30) -> List[Dict]:
        """Recupere les documents qui expirent bientot"""
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM v_documents_expiration_proche WHERE jours_restants <= %s",
                (jours,)
            )
            documents = cursor.fetchall()

            cursor.close()
            conn.close()

            return documents

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
        try:
            conn = get_connection()
            cursor = conn.cursor()

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

            cursor.execute(sql, tuple(params))
            conn.commit()

            cursor.close()
            conn.close()

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
