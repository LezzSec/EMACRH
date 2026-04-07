# -*- coding: utf-8 -*-
"""
FormationServiceCRUD - Service métier unifié pour la gestion des formations.

Fusion de formation_service.py (requêtes enrichies + stats)
et formation_service_crud.py (CRUD générique CRUDService).

Usage:
    from core.services.formation_service_crud import FormationServiceCRUD

    # Créer une formation
    success, msg, new_id = FormationServiceCRUD.create(
        operateur_id=1, intitule="Formation Python", organisme="AFPA",
        date_debut=date.today(), statut='Planifiée'
    )

    # Getters enrichis (JOIN personnel + documents)
    formation = FormationServiceCRUD.get_formation_by_id(10)
    toutes = FormationServiceCRUD.get_all_formations(statut='Planifiée')
    stats = FormationServiceCRUD.get_formations_stats()
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from infrastructure.db.query_executor import QueryExecutor
from core.services.crud_service import CRUDService
from core.services.permission_manager import require
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class FormationServiceCRUD(CRUDService):
    """Service métier CRUD unifié pour la table formation."""

    TABLE_NAME = "formation"
    ACTION_PREFIX = "FORMATION_"

    ALLOWED_FIELDS = [
        'personnel_id', 'intitule', 'type_formation', 'code_formation', 'catalogue_formation_id', 'organisme', 'lieu', 'objectif',
        'formateur', 'date_debut', 'date_fin', 'duree_heures', 'statut',
        'certificat_obtenu', 'cout', 'cout_salarial', 'commentaire', 'document_id',
    ]

    TYPE_FORMATION_VALUES = ('Réglementaire', 'Technique/Perfectionnement', 'Poste')

    # ========================= QUERIES ENRICHIES (JOIN) =========================

    @classmethod
    def get_all_formations(
        cls, statut: str = None, operateur_id: int = None
    ) -> List[Dict]:
        """
        Récupère toutes les formations avec JOINs personnel + documents.

        Args:
            statut: Filtrer par statut ('Planifiée', 'En cours', 'Terminée', 'Annulée')
            operateur_id: Filtrer par opérateur
        """
        try:
            sql = """
                SELECT
                    f.id, f.personnel_id, f.intitule, f.organisme,
                    f.lieu, f.objectif, f.formateur,
                    f.date_debut, f.date_fin, f.duree_heures, f.statut,
                    f.certificat_obtenu, f.cout, f.commentaire, f.document_id,
                    f.date_creation, f.date_modification,
                    p.nom, p.prenom,
                    CONCAT(p.prenom, ' ', p.nom) as nom_complet,
                    p.matricule, p.numposte as service,
                    d.nom_fichier as attestation_nom
                FROM formation f
                JOIN personnel p ON f.personnel_id = p.id
                LEFT JOIN documents d ON f.document_id = d.id
                WHERE 1=1
            """
            params = []
            if statut:
                sql += " AND f.statut = %s"
                params.append(statut)
            if operateur_id:
                sql += " AND f.personnel_id = %s"
                params.append(operateur_id)
            sql += " ORDER BY f.date_debut DESC"

            formations = QueryExecutor.fetch_all(sql, tuple(params), dictionary=True)
            for f in formations:
                if f.get('duree_heures') is not None:
                    f['duree_heures'] = float(f['duree_heures'])
                if f.get('cout') is not None:
                    f['cout'] = float(f['cout'])
            return formations
        except Exception as e:
            logger.error(f"Erreur get_all_formations: {e}")
            return []

    @classmethod
    def get_formations_personnel(cls, operateur_id: int) -> List[Dict]:
        """Alias de get_all_formations(operateur_id=...)."""
        return cls.get_all_formations(operateur_id=operateur_id)

    @classmethod
    def get_formation_by_id(cls, formation_id: int) -> Optional[Dict]:
        """Récupère une formation par ID avec JOINs personnel + documents."""
        try:
            formation = QueryExecutor.fetch_one("""
                SELECT
                    f.id, f.personnel_id, f.intitule, f.type_formation,
                    f.code_formation, f.catalogue_formation_id, f.organisme,
                    f.lieu, f.objectif, f.formateur,
                    f.date_debut, f.date_fin, f.duree_heures, f.statut,
                    f.certificat_obtenu, f.cout, f.cout_salarial, f.commentaire,
                    f.document_id, f.date_creation, f.date_modification,
                    p.nom, p.prenom,
                    CONCAT(p.prenom, ' ', p.nom) as nom_complet,
                    p.matricule, p.numposte as service,
                    d.nom_fichier as attestation_nom,
                    pi.categorie,
                    pi.taux_horaire,
                    tf.libelle as libelle_tranche
                FROM formation f
                JOIN personnel p ON f.personnel_id = p.id
                LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
                LEFT JOIN documents d ON f.document_id = d.id
                LEFT JOIN tranche_formation tf ON (
                    f.code_formation >= tf.tranche_min
                    AND (tf.tranche_max IS NULL OR f.code_formation <= tf.tranche_max)
                )
                WHERE f.id = %s
            """, (formation_id,), dictionary=True)
            if formation:
                for field in ('duree_heures', 'cout', 'cout_salarial', 'taux_horaire'):
                    if formation.get(field) is not None:
                        formation[field] = float(formation[field])
            return formation
        except Exception as e:
            logger.error(f"Erreur get_formation_by_id {formation_id}: {e}")
            return None

    # ========================= CRUD MÉTIER =========================

    @classmethod
    def _compute_cout_salarial(cls, personnel_id: int, duree_heures: float) -> Optional[float]:
        """Calcule le coût salarial à partir du taux horaire stocké dans personnel_infos."""
        if not personnel_id or not duree_heures:
            return None
        taux = QueryExecutor.fetch_scalar(
            "SELECT taux_horaire FROM personnel_infos WHERE personnel_id = %s",
            (personnel_id,)
        )
        if taux is None:
            return None
        return round(float(duree_heures) * float(taux), 2)

    @classmethod
    def add_formation(
        cls,
        operateur_id: int,
        intitule: str,
        date_debut: date,
        date_fin: date = None,
        type_formation: str = None,
        code_formation: int = None,
        organisme: str = None,
        lieu: str = None,
        objectif: str = None,
        formateur: str = None,
        duree_heures: float = None,
        statut: str = "Planifiée",
        certificat_obtenu: bool = False,
        cout: float = None,
        commentaire: str = None,
    ) -> Tuple[bool, str, Optional[int]]:
        """Ajoute une nouvelle formation (avec vérification permission)."""
        require('rh.formations.edit')
        cout_salarial = cls._compute_cout_salarial(operateur_id, duree_heures)
        return cls.create(
            operateur_id=operateur_id,
            intitule=intitule,
            type_formation=type_formation,
            code_formation=code_formation,
            date_debut=date_debut,
            date_fin=date_fin,
            organisme=organisme,
            lieu=lieu,
            objectif=objectif,
            formateur=formateur,
            duree_heures=duree_heures,
            statut=statut,
            certificat_obtenu=certificat_obtenu,
            cout=cout,
            cout_salarial=cout_salarial,
            commentaire=commentaire,
        )

    @classmethod
    def update_formation(cls, formation_id: int, **kwargs) -> Tuple[bool, str]:
        """Met à jour une formation (avec vérification permission + whitelist).

        Si duree_heures est modifié, recalcule automatiquement cout_salarial.
        """
        require('rh.formations.edit')
        if 'duree_heures' in kwargs and 'cout_salarial' not in kwargs:
            formation = cls.get_formation_by_id(formation_id)
            if formation:
                kwargs['cout_salarial'] = cls._compute_cout_salarial(
                    formation['personnel_id'], kwargs['duree_heures']
                )
        return cls.update(record_id=formation_id, **kwargs)

    @classmethod
    def delete_formation(cls, formation_id: int) -> Tuple[bool, str]:
        """Supprime une formation (avec vérification permission)."""
        require('rh.formations.delete')
        return cls.delete(record_id=formation_id)

    # ========================= CATALOGUE =========================

    @classmethod
    def search_catalogue(cls, query: str = '', code: int = None) -> List[Dict]:
        """Recherche dans le catalogue (autocomplete / combo UI).

        Args:
            query: texte partiel sur l'intitulé (LIKE %query%)
            code:  filtrer par code exact ou tranche (ex: 1000 → formations 1000-1999)

        Returns:
            Liste de dicts : id, code, intitule, libelle_tranche
        """
        try:
            conditions = ["cf.actif = 1"]
            params: list = []

            if query:
                conditions.append("cf.intitule LIKE %s")
                params.append(f"%{query}%")

            if code is not None:
                conditions.append("""
                    EXISTS (
                        SELECT 1 FROM tranche_formation tf
                        WHERE cf.code >= tf.tranche_min
                          AND (tf.tranche_max IS NULL OR cf.code <= tf.tranche_max)
                          AND tf.tranche_min = %s
                    )
                """)
                params.append(code)

            where = " AND ".join(conditions)
            return QueryExecutor.fetch_all(f"""
                SELECT
                    cf.id, cf.code, cf.intitule,
                    tf.libelle AS libelle_tranche
                FROM catalogue_formation cf
                LEFT JOIN tranche_formation tf ON (
                    cf.code >= tf.tranche_min
                    AND (tf.tranche_max IS NULL OR cf.code <= tf.tranche_max)
                )
                WHERE {where}
                ORDER BY cf.code, cf.intitule
            """, tuple(params), dictionary=True)
        except Exception as e:
            logger.error(f"Erreur search_catalogue: {e}")
            return []

    @classmethod
    def get_catalogue_entry(cls, catalogue_id: int) -> Optional[Dict]:
        """Récupère une entrée du catalogue par son ID."""
        try:
            return QueryExecutor.fetch_one("""
                SELECT cf.id, cf.code, cf.intitule, tf.libelle AS libelle_tranche
                FROM catalogue_formation cf
                LEFT JOIN tranche_formation tf ON (
                    cf.code >= tf.tranche_min
                    AND (tf.tranche_max IS NULL OR cf.code <= tf.tranche_max)
                )
                WHERE cf.id = %s
            """, (catalogue_id,), dictionary=True)
        except Exception as e:
            logger.error(f"Erreur get_catalogue_entry {catalogue_id}: {e}")
            return None

    @classmethod
    def add_catalogue_entry(cls, code: int, intitule: str) -> Tuple[bool, str, Optional[int]]:
        """Ajoute une formation au catalogue."""
        require('rh.formations.edit')
        try:
            new_id = QueryExecutor.execute_write(
                "INSERT INTO catalogue_formation (code, intitule) VALUES (%s, %s)",
                (code, intitule)
            )
            return True, "Formation ajoutée au catalogue.", new_id
        except Exception as e:
            logger.error(f"Erreur add_catalogue_entry: {e}")
            return False, str(e), None

    @classmethod
    def get_tranches(cls) -> List[Dict]:
        """Retourne toutes les tranches (pour les filtres UI)."""
        try:
            return QueryExecutor.fetch_all(
                "SELECT tranche_min, tranche_max, libelle FROM tranche_formation ORDER BY tranche_min",
                dictionary=True
            )
        except Exception as e:
            logger.error(f"Erreur get_tranches: {e}")
            return []

    # ========================= STATISTIQUES =========================

    @classmethod
    def get_formations_stats(cls) -> Dict[str, Any]:
        """Récupère les statistiques agrégées des formations."""
        try:
            stats = {}
            stats['total'] = QueryExecutor.fetch_scalar(
                "SELECT COUNT(*) FROM formation", default=0
            )
            rows = QueryExecutor.fetch_all("""
                SELECT statut, COUNT(*) as count
                FROM formation GROUP BY statut
            """, dictionary=True)
            stats['par_statut'] = {row['statut']: row['count'] for row in rows}
            annee = datetime.now().year
            stats['cette_annee'] = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM formation WHERE YEAR(date_debut) = %s
            """, (annee,), default=0)
            stats['terminees_cette_annee'] = QueryExecutor.fetch_scalar("""
                SELECT COUNT(*) FROM formation
                WHERE statut = 'Terminée' AND YEAR(date_fin) = %s
            """, (annee,), default=0)
            stats['en_cours'] = stats['par_statut'].get('En cours', 0)
            stats['planifiees'] = stats['par_statut'].get('Planifiée', 0)
            return stats
        except Exception as e:
            logger.error(f"Erreur get_formations_stats: {e}")
            return {'total': 0, 'par_statut': {}, 'cette_annee': 0,
                    'terminees_cette_annee': 0, 'en_cours': 0, 'planifiees': 0}

    # ========================= HELPERS UI =========================

    @classmethod
    def get_personnel_list(cls) -> List[Dict]:
        """Récupère la liste du personnel actif pour les combos UI."""
        try:
            return QueryExecutor.fetch_all("""
                SELECT id, CONCAT(prenom, ' ', nom) as nom_complet, matricule
                FROM personnel WHERE statut = 'ACTIF'
                ORDER BY nom, prenom
            """, dictionary=True)
        except Exception as e:
            logger.error(f"Erreur get_personnel_list: {e}")
            return []

    @classmethod
    def get_by_operateur(
        cls,
        operateur_id: int,
        order_by: str = 'date_debut DESC'
    ) -> List[Dict]:
        """
        Récupère toutes les formations d'un opérateur.

        Args:
            operateur_id: ID de l'opérateur
            order_by: Clause ORDER BY (défaut: 'date_debut DESC')

        Returns:
            Liste de dictionnaires représentant les formations

        Example:
            >>> formations = FormationServiceCRUD.get_by_operateur(1)
            >>> for f in formations:
            ...     print(f"{f['intitule']} - {f['statut']}")
        """
        return cls.get_all(
            conditions={'personnel_id': operateur_id},
            order_by=order_by
        )

    @classmethod
    def get_by_statut(
        cls,
        statut: str,
        order_by: str = 'date_debut ASC'
    ) -> List[Dict]:
        """
        Récupère toutes les formations d'un statut donné.

        Args:
            statut: Statut des formations ('Planifiée', 'En cours', 'Terminée', 'Annulée')
            order_by: Clause ORDER BY

        Returns:
            Liste de formations

        Example:
            >>> planifiees = FormationServiceCRUD.get_by_statut('Planifiée')
        """
        return cls.get_all(
            conditions={'statut': statut},
            order_by=order_by
        )

    @classmethod
    def get_planifiees(cls) -> List[Dict]:
        """Récupère toutes les formations planifiées."""
        return cls.get_by_statut('Planifiée')

    @classmethod
    def get_en_cours(cls) -> List[Dict]:
        """Récupère toutes les formations en cours."""
        return cls.get_by_statut('En cours')

    @classmethod
    def get_terminees(cls) -> List[Dict]:
        """Récupère toutes les formations terminées."""
        return cls.get_by_statut('Terminée')

    @classmethod
    def marquer_terminee(
        cls,
        record_id: int,
        certificat_obtenu: bool = False
    ) -> Tuple[bool, str]:
        """
        Marque une formation comme terminée.

        Args:
            record_id: ID de la formation
            certificat_obtenu: Si le certificat a été obtenu

        Returns:
            (success: bool, message: str)

        Example:
            >>> FormationServiceCRUD.marquer_terminee(10, certificat_obtenu=True)
        """
        return cls.update(
            record_id=record_id,
            statut='Terminée',
            certificat_obtenu=certificat_obtenu
        )

    @classmethod
    def annuler(cls, record_id: int, commentaire: str = None) -> Tuple[bool, str]:
        """
        Annule une formation.

        Args:
            record_id: ID de la formation
            commentaire: Raison de l'annulation (optionnel)

        Returns:
            (success: bool, message: str)
        """
        update_data = {'statut': 'Annulée'}
        if commentaire:
            update_data['commentaire'] = commentaire

        return cls.update(record_id=record_id, **update_data)

    @classmethod
    def count_by_operateur(cls, operateur_id: int) -> int:
        """
        Compte le nombre de formations d'un opérateur.

        Args:
            operateur_id: ID de l'opérateur

        Returns:
            Nombre de formations

        Example:
            >>> total = FormationServiceCRUD.count_by_operateur(1)
        """
        return cls.count(personnel_id=operateur_id)

    @classmethod
    def count_by_statut(cls, statut: str) -> int:
        """
        Compte le nombre de formations par statut.

        Args:
            statut: Statut des formations

        Returns:
            Nombre de formations

        Example:
            >>> nb_planifiees = FormationServiceCRUD.count_by_statut('Planifiée')
        """
        return cls.count(statut=statut)

    @classmethod
    def get_catalogue_competences(cls) -> list:
        """Retourne le catalogue des compétences actives (id, code, libelle, categorie, duree_validite_mois)."""
        from infrastructure.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            """
            SELECT id, code, libelle, categorie, duree_validite_mois
            FROM competences_catalogue
            WHERE actif = 1
            ORDER BY categorie, libelle
            """,
            dictionary=True,
        )
