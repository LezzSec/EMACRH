# -*- coding: utf-8 -*-
"""
Repository pour la table Personnel.

Centralise toutes les requêtes SQL liées aux employés.
Utilise le pattern Repository avec SafeQueryBuilder.

Usage:
    from core.repositories import PersonnelRepository

    # Lecture
    personnel = PersonnelRepository.get_by_id(123)
    actifs = PersonnelRepository.get_all_actifs()
    results = PersonnelRepository.search("Dupont")

    # Écriture
    new_id = PersonnelRepository.create({"nom": "Dupont", "prenom": "Jean"})
    PersonnelRepository.update(123, {"statut": "INACTIF"})
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date

from core.db.configbd import DatabaseCursor, DatabaseConnection
from core.models import Personnel, PersonnelResume
from core.repositories.base import BaseRepository, SafeQueryBuilder
from core.utils.performance_monitor import monitor_query

logger = logging.getLogger(__name__)


class PersonnelRepository(BaseRepository[Personnel]):
    """
    Repository pour les opérations sur la table personnel.

    Hérite de BaseRepository pour les opérations CRUD de base
    et ajoute des méthodes spécifiques au domaine.
    """

    TABLE = "personnel"
    MODEL = Personnel
    COLUMNS = [
        "id", "nom", "prenom", "matricule", "statut",
        "sexe", "date_entree", "atelier_id", "email", "telephone"
    ]

    # ===========================
    # Requêtes de lecture
    # ===========================

    @classmethod
    @monitor_query('PersonnelRepo.get_all_actifs')
    def get_all_actifs(cls, limit: int = 500) -> List[Personnel]:
        """
        Récupère tous les employés actifs.

        Args:
            limit: Nombre maximum de résultats

        Returns:
            Liste de Personnel triée par nom
        """
        query, params = (cls._get_builder()
            .where("statut", "=", "ACTIF")
            .order_by("nom")
            .limit(limit)
            .build())

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, params)
            return cls._rows_to_models(cur.fetchall())

    @classmethod
    @monitor_query('PersonnelRepo.get_all_inactifs')
    def get_all_inactifs(cls, limit: int = 500) -> List[Personnel]:
        """Récupère tous les employés inactifs."""
        query, params = (cls._get_builder()
            .where("statut", "=", "INACTIF")
            .order_by("nom")
            .limit(limit)
            .build())

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, params)
            return cls._rows_to_models(cur.fetchall())

    @classmethod
    def get_by_matricule(cls, matricule: str) -> Optional[Personnel]:
        """
        Récupère un employé par son matricule.

        Args:
            matricule: Matricule de l'employé

        Returns:
            Personnel ou None
        """
        query, params = (cls._get_builder()
            .where("matricule", "=", matricule)
            .limit(1)
            .build())

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return cls._row_to_model(row)

    @classmethod
    @monitor_query('PersonnelRepo.search')
    def search(
        cls,
        terme: str,
        statut: Optional[str] = None,
        limit: int = 50
    ) -> List[Personnel]:
        """
        Recherche des employés par nom, prénom ou matricule.

        Args:
            terme: Terme de recherche
            statut: Filtrer par statut (ACTIF/INACTIF)
            limit: Nombre maximum de résultats

        Returns:
            Liste de Personnel correspondant
        """
        builder = cls._get_builder()

        # Recherche LIKE sur nom, prénom, matricule
        # Note: On utilise une requête OR manuelle car le builder ne gère pas OR
        search_pattern = f"%{terme}%"
        columns = ", ".join(cls.COLUMNS)

        query = f"""
            SELECT {columns} FROM personnel
            WHERE (nom LIKE %s OR prenom LIKE %s OR matricule LIKE %s)
        """
        params = [search_pattern, search_pattern, search_pattern]

        if statut:
            query += " AND statut = %s"
            params.append(statut)

        query += " ORDER BY nom LIMIT %s"
        params.append(limit)

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, tuple(params))
            return cls._rows_to_models(cur.fetchall())

    @classmethod
    def get_by_atelier(cls, atelier_id: int) -> List[Personnel]:
        """Récupère les employés d'un atelier."""
        query, params = (cls._get_builder()
            .where("atelier_id", "=", atelier_id)
            .where("statut", "=", "ACTIF")
            .order_by("nom")
            .build())

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, params)
            return cls._rows_to_models(cur.fetchall())

    @classmethod
    def get_resume_list(cls, statut: str = "ACTIF") -> List[PersonnelResume]:
        """
        Récupère une liste légère pour les combos/listes.

        Args:
            statut: Filtrer par statut

        Returns:
            Liste de PersonnelResume (id, nom, prenom, matricule)
        """
        query = """
            SELECT id, nom, prenom, matricule
            FROM personnel
            WHERE statut = %s
            ORDER BY nom, prenom
        """

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, (statut,))
            return [PersonnelResume.from_dict(row) for row in cur.fetchall()]

    # ===========================
    # Statistiques
    # ===========================

    @classmethod
    def count_by_statut(cls) -> Dict[str, int]:
        """
        Compte les employés par statut.

        Returns:
            {"ACTIF": X, "INACTIF": Y}
        """
        query = """
            SELECT statut, COUNT(*) as count
            FROM personnel
            GROUP BY statut
        """

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query)
            results = cur.fetchall()
            return {row['statut']: row['count'] for row in results}

    @classmethod
    def count_actifs(cls) -> int:
        """Compte les employés actifs"""
        query, params = (cls._get_builder()
            .where("statut", "=", "ACTIF")
            .build_count())

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, params)
            result = cur.fetchone()
            return result['total'] if result else 0

    # ===========================
    # Opérations d'écriture
    # ===========================

    @classmethod
    def create(cls, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Crée un nouvel employé.

        Args:
            data: Dictionnaire avec les données (nom, prenom, etc.)

        Returns:
            (succès, message, id_créé)
        """
        required = ["nom", "prenom"]
        for field in required:
            if not data.get(field):
                return False, f"Le champ '{field}' est obligatoire", None

        # Colonnes autorisées pour l'insertion
        allowed_columns = ["nom", "prenom", "matricule", "statut", "sexe",
                          "date_entree", "atelier_id", "email", "telephone"]

        # Filtrer les données
        insert_data = {k: v for k, v in data.items() if k in allowed_columns and v is not None}

        # Construire la requête
        columns = list(insert_data.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        columns_str = ", ".join(columns)

        query = f"INSERT INTO personnel ({columns_str}) VALUES ({placeholders})"
        values = tuple(insert_data.values())

        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute(query, values)
                new_id = cur.lastrowid
                conn.commit()

                # Log
                from core.services.logger import log_hist
                log_hist("CREATE", "personnel", new_id,
                        f"Création: {data.get('nom')} {data.get('prenom')}")

                # Émettre l'événement pour déclencher les documents
                from core.services.event_bus import EventBus
                EventBus.emit('personnel.created', {
                    'operateur_id': new_id,
                    'nom': data.get('nom', ''),
                    'prenom': data.get('prenom', ''),
                    'matricule': data.get('matricule'),
                    'is_production': bool(data.get('matricule'))
                }, source='PersonnelRepository.create')

                return True, "Employé créé avec succès", new_id

        except Exception as e:
            logger.error(f"Erreur création personnel: {e}")
            return False, f"Erreur: {str(e)}", None

    @classmethod
    def update(cls, id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Met à jour un employé.

        Args:
            id: ID de l'employé
            data: Dictionnaire avec les champs à mettre à jour

        Returns:
            (succès, message)
        """
        if not cls.exists(id):
            return False, "Employé non trouvé"

        # Colonnes autorisées pour la mise à jour
        allowed_columns = ["nom", "prenom", "matricule", "statut", "sexe",
                          "date_entree", "atelier_id", "email", "telephone"]

        # Filtrer les données
        update_data = {k: v for k, v in data.items() if k in allowed_columns}

        if not update_data:
            return False, "Aucun champ valide à mettre à jour"

        # Construire la requête
        set_clauses = [f"{col} = %s" for col in update_data.keys()]
        set_str = ", ".join(set_clauses)

        query = f"UPDATE personnel SET {set_str} WHERE id = %s"
        values = tuple(list(update_data.values()) + [id])

        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute(query, values)
                conn.commit()

                # Log
                from core.services.logger import log_hist
                log_hist("UPDATE", "personnel", id,
                        f"Mise à jour: {list(update_data.keys())}")

                return True, "Employé mis à jour avec succès"

        except Exception as e:
            logger.error(f"Erreur mise à jour personnel id={id}: {e}")
            return False, f"Erreur: {str(e)}"

    @classmethod
    def set_statut(cls, id: int, statut: str) -> Tuple[bool, str]:
        """
        Change le statut d'un employé.

        Args:
            id: ID de l'employé
            statut: Nouveau statut (ACTIF/INACTIF)

        Returns:
            (succès, message)
        """
        if statut not in ("ACTIF", "INACTIF"):
            return False, "Statut invalide (ACTIF ou INACTIF)"

        # Récupérer l'ancien statut et les infos
        personnel = cls.get_by_id(id)
        if not personnel:
            return False, "Employé non trouvé"

        old_statut = personnel.statut

        success, msg = cls.update(id, {"statut": statut})

        # Émettre l'événement si le statut a changé
        if success and old_statut != statut:
            from core.services.event_bus import EventBus
            event_name = 'personnel.deactivated' if statut == 'INACTIF' else 'personnel.reactivated'
            EventBus.emit(event_name, {
                'operateur_id': id,
                'nom': personnel.nom,
                'prenom': personnel.prenom,
                'old_statut': old_statut,
                'new_statut': statut
            }, source='PersonnelRepository.set_statut')

        return success, msg

    @classmethod
    def desactiver(cls, id: int) -> Tuple[bool, str]:
        """Désactive un employé (statut = INACTIF)"""
        return cls.set_statut(id, "INACTIF")

    @classmethod
    def reactiver(cls, id: int) -> Tuple[bool, str]:
        """Réactive un employé (statut = ACTIF)"""
        return cls.set_statut(id, "ACTIF")

    # ===========================
    # Pagination
    # ===========================

    @classmethod
    @monitor_query('PersonnelRepo.get_paginated')
    def get_paginated(
        cls,
        offset: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict], int]:
        """
        Récupère une page de personnel avec compte total.

        Args:
            offset: Nombre d'enregistrements à sauter
            limit: Nombre d'enregistrements à retourner
            filters: Filtres optionnels {
                "statut": "ACTIF"|"INACTIF",
                "search": "terme de recherche",
                "production_only": True|False,
                "atelier_id": int
            }

        Returns:
            (liste_personnel, total_count)

        Usage:
            rows, total = PersonnelRepository.get_paginated(
                offset=0, limit=50,
                filters={"statut": "ACTIF", "search": "Dupont"}
            )
        """
        filters = filters or {}

        # Construction des clauses WHERE
        where_clauses = []
        params = []

        if filters.get("statut"):
            where_clauses.append("p.statut = %s")
            params.append(filters["statut"])

        if filters.get("search"):
            search = f"%{filters['search']}%"
            where_clauses.append("(p.nom LIKE %s OR p.prenom LIKE %s OR p.matricule LIKE %s)")
            params.extend([search, search, search])

        if filters.get("production_only"):
            where_clauses.append("p.matricule IS NOT NULL AND p.matricule != ''")

        if filters.get("atelier_id"):
            where_clauses.append("p.atelier_id = %s")
            params.append(filters["atelier_id"])

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Requête principale avec stats polyvalence
        query = f"""
            SELECT
                p.id,
                p.nom,
                p.prenom,
                p.matricule,
                UPPER(p.statut) AS statut,
                COUNT(poly.id) AS nb_postes,
                SUM(CASE WHEN poly.niveau = 1 THEN 1 ELSE 0 END) AS n1,
                SUM(CASE WHEN poly.niveau = 2 THEN 1 ELSE 0 END) AS n2,
                SUM(CASE WHEN poly.niveau = 3 THEN 1 ELSE 0 END) AS n3,
                SUM(CASE WHEN poly.niveau = 4 THEN 1 ELSE 0 END) AS n4
            FROM personnel p
            LEFT JOIN polyvalence poly ON p.id = poly.operateur_id
            WHERE {where_sql}
            GROUP BY p.id, p.nom, p.prenom, p.matricule, p.statut
            ORDER BY p.nom, p.prenom
            LIMIT %s OFFSET %s
        """
        params_data = params + [limit, offset]

        # Requête de comptage
        count_query = f"""
            SELECT COUNT(DISTINCT p.id) as total
            FROM personnel p
            WHERE {where_sql}
        """

        with DatabaseCursor(dictionary=True) as cur:
            # Données paginées
            cur.execute(query, tuple(params_data))
            rows = cur.fetchall()

            # Total
            cur.execute(count_query, tuple(params))
            total = cur.fetchone()['total']

        return rows, total

    @classmethod
    @monitor_query('PersonnelRepo.search_paginated')
    def search_paginated(
        cls,
        terme: str,
        offset: int = 0,
        limit: int = 50,
        statut: Optional[str] = None
    ) -> Tuple[List[Personnel], int]:
        """
        Recherche paginée des employés.

        Args:
            terme: Terme de recherche
            offset: Début de la pagination
            limit: Nombre de résultats
            statut: Filtrer par statut

        Returns:
            (liste_personnel, total_count)
        """
        search_pattern = f"%{terme}%"
        params = [search_pattern, search_pattern, search_pattern]

        where_extra = ""
        if statut:
            where_extra = " AND statut = %s"
            params.append(statut)

        # Données
        query = f"""
            SELECT id, nom, prenom, matricule, statut, sexe, date_entree, atelier_id, email, telephone
            FROM personnel
            WHERE (nom LIKE %s OR prenom LIKE %s OR matricule LIKE %s)
            {where_extra}
            ORDER BY nom
            LIMIT %s OFFSET %s
        """
        params_data = params + [limit, offset]

        # Comptage
        count_query = f"""
            SELECT COUNT(*) as total
            FROM personnel
            WHERE (nom LIKE %s OR prenom LIKE %s OR matricule LIKE %s)
            {where_extra}
        """

        with DatabaseCursor(dictionary=True) as cur:
            cur.execute(query, tuple(params_data))
            rows = cls._rows_to_models(cur.fetchall())

            cur.execute(count_query, tuple(params))
            total = cur.fetchone()['total']

        return rows, total
