"""
Service de gestion documentaire
Gère le stockage, la récupération et la manipulation des documents des opérateurs
"""

import os
import shutil
import logging

logger = logging.getLogger(__name__)
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import mimetypes

from core.db.configbd import get_connection
from core.utils.app_paths import get_documents_dir


class DocumentService:
    """Service de gestion des documents des opérateurs"""

    def __init__(self, base_path: str = None):
        """
        Initialise le service documentaire

        Args:
            base_path: Chemin de base pour le stockage des documents
                      Par défaut: Utilise get_documents_dir() (compatible .exe)
        """
        if base_path is None:
            # Chemin par défaut compatible dev et .exe
            self.base_path = get_documents_dir()
        else:
            self.base_path = Path(base_path)

        # Créer le répertoire de base s'il n'existe pas
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_operateur_path(self, nom_dossier: str) -> Path:
        """Retourne le chemin du dossier d'un opérateur (Nom Prenom)"""
        # Nettoyer le nom du dossier pour éviter les caractères problématiques
        nom_clean = self._sanitize_filename(nom_dossier)
        operateur_dir = self.base_path / "operateurs" / nom_clean
        operateur_dir.mkdir(parents=True, exist_ok=True)
        return operateur_dir
    
    def _get_categorie_subdir(self, categorie_nom: str) -> str:
        """Retourne le nom du sous-dossier pour une catégorie"""
        mapping = {
            "Contrats de travail": "contrats",
            "Certificats médicaux": "medicaux",
            "Diplômes et formations": "formations",
            "Autorisations de travail": "autorisations",
            "Pièces d'identité": "identite",
            "Attestations diverses": "attestations",
            "Documents administratifs": "administratifs",
            "Autres": "autres"
        }
        return mapping.get(categorie_nom, "autres")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Nettoie un nom de fichier pour éviter les problèmes"""
        # Garder uniquement les caractères alphanumériques, points, tirets et underscores
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
        uploaded_by: str = "Système"
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Ajoute un document pour un opérateur
        
        Args:
            personnel_id: ID de l'opérateur
            categorie_id: ID de la catégorie
            fichier_source: Chemin du fichier à ajouter
            nom_affichage: Nom d'affichage (optionnel, sinon nom du fichier)
            date_expiration: Date d'expiration (optionnel)
            notes: Notes sur le document
            uploaded_by: Nom de l'utilisateur qui uploade
        
        Returns:
            (succès, message, document_id)
        """
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Récupérer les infos de l'opérateur
            cursor.execute(
                "SELECT nom, prenom FROM personnel WHERE id = %s",
                (personnel_id,)
            )
            operateur = cursor.fetchone()
            if not operateur:
                return False, f"Opérateur ID {personnel_id} introuvable", None

            # Créer le nom du dossier: "Nom Prenom"
            nom_dossier = f"{operateur['nom']} {operateur['prenom']}"
            
            # Récupérer les infos de la catégorie
            cursor.execute(
                "SELECT nom FROM categories_documents WHERE id = %s",
                (categorie_id,)
            )
            categorie = cursor.fetchone()
            if not categorie:
                return False, f"Catégorie ID {categorie_id} introuvable", None
            
            # Vérifier que le fichier source existe
            source_path = Path(fichier_source)
            if not source_path.exists():
                return False, f"Fichier source introuvable: {fichier_source}", None
            
            # Préparer le nom de fichier
            nom_fichier_original = source_path.name
            nom_fichier_clean = self._sanitize_filename(nom_fichier_original)
            
            if nom_affichage is None:
                nom_affichage = nom_fichier_original
            
            # Créer le chemin de destination
            operateur_dir = self._get_operateur_path(nom_dossier)
            categorie_subdir = self._get_categorie_subdir(categorie['nom'])
            dest_dir = operateur_dir / categorie_subdir
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Gérer les doublons de noms de fichiers
            dest_path = dest_dir / nom_fichier_clean
            counter = 1
            while dest_path.exists():
                stem = source_path.stem
                suffix = source_path.suffix
                nom_fichier_clean = f"{stem}_{counter}{suffix}"
                dest_path = dest_dir / nom_fichier_clean
                counter += 1
            
            # Copier le fichier
            shutil.copy2(source_path, dest_path)
            
            # Déterminer le type MIME
            type_mime, _ = mimetypes.guess_type(str(dest_path))
            if type_mime is None:
                type_mime = "application/octet-stream"
            
            # Obtenir la taille du fichier
            taille_octets = dest_path.stat().st_size
            
            # Chemin relatif pour la BDD
            chemin_relatif = str(dest_path.relative_to(self.base_path))
            
            # Insérer dans la base de données
            sql = """
                INSERT INTO documents (
                    personnel_id, categorie_id, nom_fichier, nom_affichage,
                    chemin_fichier, type_mime, taille_octets, date_expiration,
                    notes, uploaded_by
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cursor.execute(sql, (
                personnel_id, categorie_id, nom_fichier_clean, nom_affichage,
                chemin_relatif, type_mime, taille_octets, date_expiration,
                notes, uploaded_by
            ))
            
            document_id = cursor.lastrowid
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True, f"Document '{nom_affichage}' ajouté avec succès", document_id
            
        except Exception as e:
            return False, f"Erreur lors de l'ajout du document: {str(e)}", None
    
    def get_documents_operateur(
        self,
        personnel_id: int,
        categorie_id: int = None,
        statut: str = None
    ) -> List[Dict]:
        """
        Récupère les documents d'un opérateur
        
        Args:
            personnel_id: ID de l'opérateur
            categorie_id: Filtrer par catégorie (optionnel)
            statut: Filtrer par statut (optionnel)
        
        Returns:
            Liste des documents
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
            logger.error(f"Erreur lors de la récupération des documents: {e}")
            return []
    
    def get_document_path(self, document_id: int) -> Optional[Path]:
        """Retourne le chemin complet d'un document"""
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT chemin_fichier FROM documents WHERE id = %s",
                (document_id,)
            )
            doc = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if doc:
                return self.base_path / doc['chemin_fichier']
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du chemin: {e}")
            return None
    
    def delete_document(self, document_id: int) -> Tuple[bool, str]:
        """
        Supprime un document (fichier + entrée BDD)
        
        Args:
            document_id: ID du document
        
        Returns:
            (succès, message)
        """
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Récupérer les infos du document
            cursor.execute(
                "SELECT chemin_fichier, nom_affichage FROM documents WHERE id = %s",
                (document_id,)
            )
            doc = cursor.fetchone()
            
            if not doc:
                cursor.close()
                conn.close()
                return False, "Document introuvable"
            
            # Supprimer le fichier physique
            file_path = self.base_path / doc['chemin_fichier']
            if file_path.exists():
                file_path.unlink()
            
            # Supprimer de la BDD
            cursor.execute("DELETE FROM documents WHERE id = %s", (document_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True, f"Document '{doc['nom_affichage']}' supprimé avec succès"
            
        except Exception as e:
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

            return True, "Document archivé avec succès"

        except Exception as e:
            return False, f"Erreur lors de l'archivage: {str(e)}"

    def restore_document(self, document_id: int) -> Tuple[bool, str]:
        """Restaure un document archivé (remet son statut à actif)"""
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

            return True, "Document restauré avec succès"

        except Exception as e:
            return False, f"Erreur lors de la restauration: {str(e)}"

    def get_categories(self) -> List[Dict]:
        """Récupère toutes les catégories de documents"""
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
            logger.error(f"Erreur lors de la récupération des catégories: {e}")
            return []
    
    def get_documents_expiring_soon(self, jours: int = 30) -> List[Dict]:
        """Récupère les documents qui expirent bientôt"""
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
            logger.error(f"Erreur lors de la récupération des documents expirant: {e}")
            return []
    
    def update_document_info(
        self,
        document_id: int,
        nom_affichage: str = None,
        date_expiration: date = None,
        notes: str = None,
        categorie_id: int = None
    ) -> Tuple[bool, str]:
        """Met à jour les informations d'un document"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # SÉCURITÉ: Construction sécurisée - seules les clauses prédéfinies sont utilisées
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
                return False, "Aucune modification à effectuer"

            params.append(document_id)
            # SÉCURITÉ: Les clauses dans 'updates' sont des constantes littérales définies ci-dessus
            # Pas d'input utilisateur dans la construction SQL
            sql = "UPDATE documents SET " + ", ".join(updates) + " WHERE id = %s"

            cursor.execute(sql, tuple(params))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True, "Document mis à jour avec succès"
            
        except Exception as e:
            return False, f"Erreur lors de la mise à jour: {str(e)}"