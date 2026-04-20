# -*- coding: utf-8 -*-
"""
Repository pour la table Personnel.

Centralise toutes les requêtes SQL liées aux employés.
Utilise le pattern Repository avec SafeQueryBuilder.

Usage:
    from domain.repositories import PersonnelRepository

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

from infrastructure.db.query_executor import QueryExecutor
from domain.models import Personnel, PersonnelResume
from domain.repositories.base import BaseRepository
from infrastructure.config.performance_monitor import monitor_query

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
        "service_id", "numposte"
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

        return cls._rows_to_models(QueryExecutor.fetch_all(query, params, dictionary=True))

    @classmethod
    @monitor_query('PersonnelRepo.get_all_inactifs')
    def get_all_inactifs(cls, limit: int = 500) -> List[Personnel]:
        """Récupère tous les employés inactifs."""
        query, params = (cls._get_builder()
            .where("statut", "=", "INACTIF")
            .order_by("nom")
            .limit(limit)
            .build())

        return cls._rows_to_models(QueryExecutor.fetch_all(query, params, dictionary=True))

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

        return cls._row_to_model(QueryExecutor.fetch_one(query, params, dictionary=True))

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

        return cls._rows_to_models(QueryExecutor.fetch_all(query, tuple(params), dictionary=True))

    @classmethod
    def get_by_atelier(cls, atelier_id: int) -> List[Personnel]:
        """Récupère les employés d'un atelier via les postes rattachés."""
        # Note: personnel n'a pas de atelier_id directement
        # On passe par polyvalence -> postes -> atelier
        query = """
            SELECT DISTINCT p.id, p.nom, p.prenom, p.matricule, p.statut, p.service_id, p.numposte
            FROM personnel p
            JOIN polyvalence pv ON pv.personnel_id = p.id
            JOIN postes po ON po.id = pv.poste_id
            WHERE po.atelier_id = %s AND p.statut = 'ACTIF'
            ORDER BY p.nom
        """
        params = (atelier_id,)

        return cls._rows_to_models(QueryExecutor.fetch_all(query, params, dictionary=True))

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

        rows = QueryExecutor.fetch_all(query, (statut,), dictionary=True)
        return [PersonnelResume.from_dict(row) for row in rows]

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

        results = QueryExecutor.fetch_all(query, dictionary=True)
        return {row['statut']: row['count'] for row in results}

    @classmethod
    def count_actifs(cls) -> int:
        """Compte les employés actifs"""
        query, params = (cls._get_builder()
            .where("statut", "=", "ACTIF")
            .build_count())

        result = QueryExecutor.fetch_one(query, params, dictionary=True)
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

        # Colonnes autorisées pour l'insertion (colonnes réelles de la table personnel)
        allowed_columns = ["nom", "prenom", "matricule", "statut", "service_id", "numposte"]

        # Filtrer les données
        insert_data = {k: v for k, v in data.items() if k in allowed_columns and v is not None}

        # Construire la requête
        columns = list(insert_data.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        columns_str = ", ".join(columns)

        query = f"INSERT INTO personnel ({columns_str}) VALUES ({placeholders})"
        values = tuple(insert_data.values())

        try:
            def _do_create(cur):
                cur.execute(query, values)
                return cur.lastrowid

            new_id = QueryExecutor.with_transaction(_do_create)

            from infrastructure.logging.optimized_db_logger import log_hist
            log_hist("CREATE", "personnel", new_id,
                    f"Création: {data.get('nom')} {data.get('prenom')}")

            from application.event_bus import EventBus
            EventBus.emit('personnel.created', {
                'operateur_id': new_id,
                'nom': data.get('nom', ''),
                'prenom': data.get('prenom', ''),
                'matricule': data.get('matricule'),
                'is_production': data.get('numposte') == 'Production'
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

        # SÉCURITÉ: Whitelist stricte des colonnes autorisées (frozenset immuable)
        ALLOWED_COLUMNS = frozenset(["nom", "prenom", "matricule", "statut", "service_id", "numposte"])

        # Filtrer les données
        update_data = {k: v for k, v in data.items() if k in ALLOWED_COLUMNS}

        if not update_data:
            return False, "Aucun champ valide à mettre à jour"

        # SÉCURITÉ: Double validation - chaque colonne DOIT être dans la whitelist
        for col in update_data.keys():
            if col not in ALLOWED_COLUMNS:
                raise ValueError(f"Colonne non autorisée: {col}")

        # Construire la requête
        set_clauses = [f"{col} = %s" for col in update_data.keys()]
        set_str = ", ".join(set_clauses)

        query = f"UPDATE personnel SET {set_str} WHERE id = %s"
        values = tuple(list(update_data.values()) + [id])

        try:
            QueryExecutor.execute_write(query, values)

            from infrastructure.logging.optimized_db_logger import log_hist
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
            from application.event_bus import EventBus
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
    # Méthodes utilitaires (GUI-safe)
    # ===========================

    @classmethod
    def get_by_nom_prenom(cls, nom: str, prenom: str) -> Optional[int]:
        """Retourne l'id d'un personnel si nom+prenom existe, sinon None."""
        from infrastructure.db.query_executor import QueryExecutor
        row = QueryExecutor.fetch_one(
            "SELECT id FROM personnel WHERE `nom` = %s AND `prenom` = %s ORDER BY id DESC LIMIT 1",
            (nom, prenom),
        )
        return row[0] if row else None

    @classmethod
    def get_first_actif_id(cls) -> Optional[int]:
        """Retourne l'id du premier personnel actif (utilisé pour ouvrir des dialogs)."""
        from infrastructure.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_scalar(
            "SELECT id FROM personnel WHERE statut = 'ACTIF' LIMIT 1"
        )

    @classmethod
    def save_date_entree(cls, personnel_id: int, date_entree) -> bool:
        """Upsert la date d'entrée dans personnel_infos."""
        from infrastructure.db.query_executor import QueryExecutor
        existing = QueryExecutor.exists("personnel_infos", {"personnel_id": personnel_id})
        if existing:
            QueryExecutor.execute_write(
                "UPDATE personnel_infos SET date_entree = %s WHERE personnel_id = %s",
                (date_entree, personnel_id),
            )
        else:
            QueryExecutor.execute_write(
                "INSERT INTO personnel_infos (personnel_id, date_entree) VALUES (%s, %s)",
                (personnel_id, date_entree),
            )
        return True

    @classmethod
    def get_date_entree(cls, personnel_id: int):
        """Retourne la date d'entrée d'un personnel depuis personnel_infos."""
        from infrastructure.db.query_executor import QueryExecutor
        row = QueryExecutor.fetch_one(
            "SELECT date_entree FROM personnel_infos WHERE personnel_id = %s",
            (personnel_id,),
            dictionary=True,
        )
        return row.get("date_entree") if row else None

    @classmethod
    def get_info_basique(cls, personnel_id: int) -> Optional[Dict[str, Any]]:
        """Retourne nom, prenom, matricule, statut pour les exports."""
        from infrastructure.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_one(
            "SELECT nom, prenom, COALESCE(matricule,'-') AS matricule, UPPER(statut) AS statut "
            "FROM personnel WHERE id = %s",
            (personnel_id,),
            dictionary=True,
        )

    @classmethod
    def get_personnel_infos(cls, personnel_id: int) -> Optional[Dict[str, Any]]:
        """Retourne l'ensemble des données de personnel_infos."""
        from infrastructure.db.query_executor import QueryExecutor
        rows = QueryExecutor.fetch_all(
            "SELECT * FROM personnel_infos WHERE personnel_id = %s",
            (personnel_id,),
            dictionary=True,
        )
        return rows[0] if rows else None

    @classmethod
    def get_personnel_avec_stats(cls) -> List[Dict[str, Any]]:
        """
        Retourne tous les personnels avec stats polyvalence et contrat actif.
        Utilisé par la liste principale de GestionPersonnelDialog.
        """
        from infrastructure.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            """
            SELECT
                o.id, o.nom, o.prenom, o.matricule, o.numposte,
                UPPER(o.statut) AS statut, ct.type_contrat,
                COUNT(p.id) AS nb_postes,
                SUM(CASE WHEN p.niveau = 1 THEN 1 ELSE 0 END) AS n1,
                SUM(CASE WHEN p.niveau = 2 THEN 1 ELSE 0 END) AS n2,
                SUM(CASE WHEN p.niveau = 3 THEN 1 ELSE 0 END) AS n3,
                SUM(CASE WHEN p.niveau = 4 THEN 1 ELSE 0 END) AS n4
            FROM personnel o
            LEFT JOIN polyvalence p ON o.id = p.personnel_id
            LEFT JOIN contrat ct ON ct.personnel_id = o.id AND ct.actif = 1
            GROUP BY o.id, o.nom, o.prenom, o.matricule, o.numposte, o.statut, ct.type_contrat
            ORDER BY o.nom, o.prenom
            """,
            dictionary=True,
        )

    @classmethod
    def get_personnel_sans_date_entree(cls) -> List[Dict[str, Any]]:
        """Retourne les personnels sans date d'entrée (pour régularisation)."""
        from infrastructure.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            """
            SELECT p.id, p.nom, p.prenom, p.matricule, p.statut, pi.date_entree
            FROM personnel p
            LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
            WHERE (pi.date_entree IS NULL OR pi.personnel_id IS NULL)
              AND p.statut = 'ACTIF'
            ORDER BY p.nom, p.prenom
            """,
            dictionary=True,
        )

    @classmethod
    def get_all_as_dicts(cls) -> List[Dict[str, Any]]:
        """
        Retourne tout le personnel sous forme de dicts (id, nom, prenom, matricule, statut, nom_service).
        Utilisé pour les listes de sélection dans les interfaces.
        """
        from infrastructure.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_all(
            "SELECT p.id, p.nom, p.prenom, p.matricule, UPPER(p.statut) AS statut, "
            "s.nom_service FROM personnel p LEFT JOIN services s ON p.service_id = s.id "
            "ORDER BY p.nom, p.prenom",
            dictionary=True,
        )

    @classmethod
    def get_by_ids(cls, ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retourne les personnels correspondant à une liste d'IDs.
        Utilisé pour résoudre les noms depuis une liste d'identifiants.
        """
        if not ids:
            return []
        from infrastructure.db.query_executor import QueryExecutor
        placeholders = ','.join(['%s'] * len(ids))
        return QueryExecutor.fetch_all(
            f"SELECT id, nom, prenom FROM personnel WHERE id IN ({placeholders})",
            tuple(ids),
            dictionary=True,
        )

    @classmethod
    def search_as_dicts(
        cls,
        recherche: Optional[str] = None,
        statut: str = "ACTIF",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Recherche des opérateurs et retourne des dicts avec nom_complet.

        Remplace le SQL inline de rechercher_operateurs() dans rh_service.

        Args:
            recherche: Terme de recherche (nom, prénom, matricule) ou None
            statut: Filtre sur le statut (None = tous)
            limit: Nombre maximum de résultats

        Returns:
            Liste de dicts : id, nom, prenom, matricule, statut, numposte, nom_complet
        """
        from infrastructure.db.query_executor import QueryExecutor
        sql = (
            "SELECT id, nom, prenom, matricule, statut, numposte, "
            "CONCAT(prenom, ' ', nom) AS nom_complet "
            "FROM personnel WHERE 1=1"
        )
        params: list = []

        if statut:
            sql += " AND statut = %s"
            params.append(statut)

        if recherche:
            like = f"%{recherche}%"
            sql += (
                " AND (nom LIKE %s OR prenom LIKE %s OR matricule LIKE %s"
                " OR CONCAT(prenom, ' ', nom) LIKE %s)"
            )
            params.extend([like, like, like, like])

        sql += " ORDER BY nom, prenom LIMIT %s"
        params.append(limit)

        return QueryExecutor.fetch_all(sql, tuple(params), dictionary=True)

    @classmethod
    def upsert_infos(cls, personnel_id: int, data: Dict[str, Any]) -> bool:
        """
        INSERT ou UPDATE dans personnel_infos pour un personnel donné.

        Remplace le bloc upsert manuel de update_infos_generales() dans rh_service.

        Seuls les champs présents dans data sont écrits ; les autres restent inchangés.

        Args:
            personnel_id: ID du personnel
            data: Champs à écrire (clés = colonnes de personnel_infos, sauf personnel_id)

        Returns:
            True si succès
        """
        from infrastructure.db.query_executor import QueryExecutor
        if not data:
            return True

        exists = QueryExecutor.exists("personnel_infos", {"personnel_id": personnel_id})

        if exists:
            fields = [f"{k} = %s" for k in data.keys()]
            values = list(data.values()) + [personnel_id]
            QueryExecutor.execute_write(
                f"UPDATE personnel_infos SET {', '.join(fields)} WHERE personnel_id = %s",
                tuple(values),
                return_lastrowid=False,
            )
        else:
            row = {"personnel_id": personnel_id, **data}
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["%s"] * len(row))
            QueryExecutor.execute_write(
                f"INSERT INTO personnel_infos ({cols}) VALUES ({placeholders})",
                tuple(row.values()),
            )
        return True

    @classmethod
    def get_adresse_and_coords(cls, personnel_id: int) -> Optional[Dict[str, Any]]:
        """
        Retourne l'adresse actuellement enregistrée et les coordonnées GPS.
        Utilisé pour détecter si l'adresse a changé avant de recalculer la distance.
        """
        from infrastructure.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_one(
            """SELECT adresse1, cp_adresse, ville_adresse,
                      latitude, longitude, distance_domicile_km
               FROM personnel_infos WHERE personnel_id = %s""",
            (personnel_id,),
            dictionary=True,
        )

    @classmethod
    def get_adresse_and_distances(cls, personnel_id: int) -> Optional[Dict[str, Any]]:
        """
        Retourne CP + ville + données de distance existantes.
        Utilisé pour détecter si la commune a changé avant recalcul.
        """
        from infrastructure.db.query_executor import QueryExecutor
        return QueryExecutor.fetch_one(
            """SELECT cp_adresse, ville_adresse,
                      code_insee_commune, distance_commune_km, distance_mairie_km
               FROM personnel_infos WHERE personnel_id = %s""",
            (personnel_id,),
            dictionary=True,
        )

    @classmethod
    def update_distances(
        cls,
        personnel_id: int,
        code_insee_commune: Optional[str],
        commune_lat: Optional[float],
        commune_lon: Optional[float],
        distance_commune_km: Optional[float],
        duree_trajet_commune_min: Optional[int],
        mairie_lat: Optional[float],
        mairie_lon: Optional[float],
        distance_mairie_km: Optional[float],
        duree_trajet_mairie_min: Optional[int],
    ) -> None:
        """Met à jour toutes les données de distance (mairie + commune)."""
        from infrastructure.db.query_executor import QueryExecutor
        QueryExecutor.execute_write(
            """UPDATE personnel_infos
               SET code_insee_commune = %s,
                   commune_lat = %s, commune_lon = %s,
                   distance_commune_km = %s, duree_trajet_commune_min = %s,
                   mairie_lat = %s, mairie_lon = %s,
                   distance_mairie_km = %s, duree_trajet_mairie_min = %s,
                   distance_calculee_at = NOW()
               WHERE personnel_id = %s""",
            (code_insee_commune, commune_lat, commune_lon,
             distance_commune_km, duree_trajet_commune_min,
             mairie_lat, mairie_lon,
             distance_mairie_km, duree_trajet_mairie_min,
             personnel_id),
            return_lastrowid=False,
        )

    @classmethod
    def update_distance_domicile(
        cls,
        personnel_id: int,
        latitude: Optional[float],
        longitude: Optional[float],
        distance_km: Optional[float],
        duree_min: Optional[int],
    ) -> None:
        """
        Met à jour les coordonnées GPS et la distance domicile-entreprise
        d'un membre du personnel.
        """
        from infrastructure.db.query_executor import QueryExecutor
        QueryExecutor.execute_write(
            """UPDATE personnel_infos
               SET latitude = %s,
                   longitude = %s,
                   distance_domicile_km = %s,
                   duree_trajet_min = %s,
                   distance_calculee_at = NOW()
               WHERE personnel_id = %s""",
            (latitude, longitude, distance_km, duree_min, personnel_id),
            return_lastrowid=False,
        )

    @classmethod
    def is_matricule_disponible(cls, matricule: str, exclude_id: int) -> bool:
        """
        Vérifie si un matricule est libre (non utilisé par un autre personnel).

        Remplace is_matricule_disponible() dans rh_service.

        Returns:
            True si le matricule est disponible
        """
        from infrastructure.db.query_executor import QueryExecutor
        existing = QueryExecutor.fetch_one(
            "SELECT id FROM personnel WHERE matricule = %s AND id != %s",
            (matricule, exclude_id),
            dictionary=True,
        )
        return existing is None

    @classmethod
    def get_resume_competences(cls, personnel_id: int) -> Dict[str, Any]:
        """
        Retourne un résumé agrégé polyvalence pour un opérateur.

        Utilisé par get_resume_operateur() dans rh_service.

        Returns:
            {"nb_postes": int, "niveau_moyen": float|None, "evaluations_en_retard": int}
        """
        from infrastructure.db.query_executor import QueryExecutor
        row = QueryExecutor.fetch_one(
            """
            SELECT
                COUNT(*)    AS total,
                AVG(niveau) AS niveau_moyen,
                SUM(CASE WHEN prochaine_evaluation < CURDATE() THEN 1 ELSE 0 END) AS en_retard
            FROM polyvalence
            WHERE personnel_id = %s
            """,
            (personnel_id,),
            dictionary=True,
        ) or {}
        return {
            "nb_postes": row.get("total") or 0,
            "niveau_moyen": float(row["niveau_moyen"]) if row.get("niveau_moyen") else None,
            "evaluations_en_retard": row.get("en_retard") or 0,
        }

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
            where_clauses.append("p.numposte = 'Production'")

        if filters.get("atelier_id"):
            where_clauses.append("""p.id IN (
                SELECT DISTINCT pv.personnel_id FROM polyvalence pv
                JOIN postes po ON po.id = pv.poste_id
                WHERE po.atelier_id = %s
            )""")
            params.append(filters["atelier_id"])

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Requête principale avec stats polyvalence + contrat actif
        query = f"""
            SELECT
                p.id,
                p.nom,
                p.prenom,
                p.matricule,
                p.numposte,
                UPPER(p.statut) AS statut,
                ct.type_contrat,
                COUNT(poly.id) AS nb_postes,
                SUM(CASE WHEN poly.niveau = 1 THEN 1 ELSE 0 END) AS n1,
                SUM(CASE WHEN poly.niveau = 2 THEN 1 ELSE 0 END) AS n2,
                SUM(CASE WHEN poly.niveau = 3 THEN 1 ELSE 0 END) AS n3,
                SUM(CASE WHEN poly.niveau = 4 THEN 1 ELSE 0 END) AS n4
            FROM personnel p
            LEFT JOIN polyvalence poly ON p.id = poly.personnel_id
            LEFT JOIN contrat ct ON ct.personnel_id = p.id AND ct.actif = 1
            WHERE {where_sql}
            GROUP BY p.id, p.nom, p.prenom, p.matricule, p.numposte, p.statut, ct.type_contrat
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

        rows = QueryExecutor.fetch_all(query, tuple(params_data), dictionary=True)
        count_row = QueryExecutor.fetch_one(count_query, tuple(params), dictionary=True)
        total = count_row['total'] if count_row else 0
        return rows, total

