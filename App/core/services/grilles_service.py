# -*- coding: utf-8 -*-
"""
GrillesService - Service métier pour la grille de polyvalence.

Centralise toute la logique SQL de la vue GrillesDialog (liste_et_grilles.py).
La couche GUI ne doit plus contenir d'appels directs à QueryExecutor ou DatabaseConnection.

Usage:
    from core.services.grilles_service import GrillesService

    # Données pour construire la grille
    data = GrillesService.get_grille_data()

    # Mise à jour d'une cellule
    GrillesService.update_polyvalence_from_grille(
        operateur_id=1, poste_id=5,
        new_niveau_str="3",
        operateur_nom="Dupont Jean", poste_code="0506"
    )
"""

import json
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from core.db.query_executor import QueryExecutor
from core.db.configbd import DatabaseConnection

logger = logging.getLogger(__name__)


class GrillesService:
    """Service métier pour toutes les opérations sur la grille de polyvalence."""

    # =========================================================================
    # CHARGEMENT DES DONNÉES
    # =========================================================================

    @staticmethod
    def get_grille_data() -> Dict[str, Any]:
        """
        Retourne toutes les données nécessaires à la construction de la grille.

        Returns:
            dict avec clés:
              - operateurs: list de (id, nom_complet)
              - postes: list de (id, poste_code)
              - niveaux: dict {(operateur_id, poste_id): niveau}
              - besoins: dict {poste_id: besoins_postes}
        """
        operateurs_rows = QueryExecutor.fetch_all("""
            SELECT DISTINCT p.id, p.nom, p.prenom
            FROM personnel p
            INNER JOIN polyvalence pv ON pv.operateur_id = p.id
            WHERE p.statut = 'ACTIF'
            ORDER BY p.nom, p.prenom
        """, dictionary=True)

        postes_rows = QueryExecutor.fetch_all("""
            SELECT id, poste_code
            FROM postes
            WHERE visible = 1
              AND poste_code != 'PRODUCTION'
            ORDER BY poste_code
        """, dictionary=True)

        polyvalences_rows = QueryExecutor.fetch_all("""
            SELECT operateur_id, poste_id, niveau
            FROM polyvalence
            WHERE operateur_id IN (
                SELECT DISTINCT p.id FROM personnel p
                INNER JOIN polyvalence pv ON pv.operateur_id = p.id
                WHERE p.statut = 'ACTIF'
            )
            AND poste_id IN (
                SELECT id FROM postes WHERE visible = 1
            )
        """, dictionary=True)

        besoins_rows = QueryExecutor.fetch_all(
            "SELECT id, besoins_postes FROM postes WHERE visible = 1",
            dictionary=True
        )

        return {
            'operateurs': [(r['id'], f"{r['nom']} {r['prenom']}".strip()) for r in operateurs_rows],
            'postes': [(r['id'], r['poste_code']) for r in postes_rows],
            'niveaux': {(r['operateur_id'], r['poste_id']): r['niveau'] for r in polyvalences_rows},
            'besoins': {r['id']: r.get('besoins_postes', '') for r in besoins_rows},
        }

    @staticmethod
    def get_polyvalence_niveau(operateur_id: int, poste_id: int) -> Optional[int]:
        """Retourne le niveau de polyvalence ou None si inexistant."""
        result = QueryExecutor.fetch_one(
            "SELECT niveau FROM polyvalence WHERE operateur_id = %s AND poste_id = %s",
            (operateur_id, poste_id),
            dictionary=True
        )
        return result.get('niveau') if result else None

    @staticmethod
    def get_operateurs_actifs() -> List[Dict]:
        """Liste des opérateurs actifs (pour selection dans remove_data)."""
        return QueryExecutor.fetch_all("""
            SELECT DISTINCT p.id, p.nom, p.prenom, p.matricule
            FROM personnel p
            INNER JOIN polyvalence pv ON pv.operateur_id = p.id
            WHERE p.statut = 'ACTIF'
            ORDER BY p.nom, p.prenom
        """, dictionary=True)

    # =========================================================================
    # MISE À JOUR CELLULE (on_cell_changed)
    # =========================================================================

    @staticmethod
    def update_polyvalence_from_grille(
        operateur_id: int,
        poste_id: int,
        new_niveau_str: str,
        operateur_nom: str,
        poste_code: str,
    ) -> Tuple[str, Optional[int], Optional[int]]:
        """
        Met à jour (ou supprime) une cellule de polyvalence depuis la grille.

        Args:
            operateur_id: ID de l'opérateur
            poste_id: ID du poste
            new_niveau_str: Nouveau niveau (chaîne vide = suppression, "1"-"4" = niveau)
            operateur_nom: Nom complet de l'opérateur (pour les logs)
            poste_code: Code du poste (pour les logs)

        Returns:
            (action, old_niveau, new_niveau_int)
            action est 'DELETE', 'INSERT' ou 'UPDATE'

        Raises:
            ValueError: Si le niveau n'est pas un entier valide
            Exception: En cas d'erreur DB
        """
        # 1. Lire ancienne valeur
        old_result = QueryExecutor.fetch_one("""
            SELECT niveau, date_evaluation, prochaine_evaluation
            FROM polyvalence
            WHERE operateur_id = %s AND poste_id = %s
        """, (operateur_id, poste_id))

        old_niveau = None
        old_date_eval = None
        old_date_next = None
        if old_result:
            old_niveau, old_date_eval, old_date_next = old_result

        # 2. Appliquer la modification
        action = None
        new_niveau_int = None

        if new_niveau_str == "":
            # Suppression
            QueryExecutor.execute_write(
                "DELETE FROM polyvalence WHERE operateur_id = %s AND poste_id = %s",
                (operateur_id, poste_id)
            )
            action = 'DELETE'

        else:
            new_niveau_int = int(new_niveau_str)

            # Archiver si modification de niveau
            if old_niveau is not None and old_niveau != new_niveau_int:
                try:
                    QueryExecutor.execute_write("""
                        INSERT INTO historique_polyvalence
                        (operateur_id, poste_id, action_type,
                         ancien_niveau, nouveau_niveau,
                         ancienne_date_evaluation, nouvelle_date_evaluation,
                         commentaire, date_action)
                        VALUES (%s, %s, 'IMPORT_MANUEL',
                                %s, %s,
                                %s, NULL,
                                'Ancienne polyvalence archivée lors de modification depuis la grille',
                                NOW())
                    """, (operateur_id, poste_id, old_niveau, new_niveau_int, old_date_eval))
                except Exception as arch_err:
                    logger.warning(f"Erreur archivage historique_polyvalence: {arch_err}")

            # Calculer la prochaine évaluation
            jours = 30 if new_niveau_int in [1, 2] else 3650
            prochaine_eval = date.today() + timedelta(days=jours)

            if old_niveau is None:
                QueryExecutor.execute_write("""
                    INSERT INTO polyvalence (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
                    VALUES (%s, %s, %s, CURDATE(), %s)
                """, (operateur_id, poste_id, new_niveau_int, prochaine_eval))
                action = 'INSERT'
                GrillesService._emit_polyvalence_events(
                    action='INSERT',
                    operateur_id=operateur_id,
                    poste_id=poste_id,
                    poste_code=poste_code,
                    old_niveau=None,
                    new_niveau=new_niveau_int,
                )
            else:
                QueryExecutor.execute_write("""
                    UPDATE polyvalence
                    SET niveau = %s, date_evaluation = CURDATE(), prochaine_evaluation = %s
                    WHERE operateur_id = %s AND poste_id = %s
                """, (new_niveau_int, prochaine_eval, operateur_id, poste_id))
                action = 'UPDATE'
                GrillesService._emit_polyvalence_events(
                    action='UPDATE',
                    operateur_id=operateur_id,
                    poste_id=poste_id,
                    poste_code=poste_code,
                    old_niveau=old_niveau,
                    new_niveau=new_niveau_int,
                )

        # 3. Logging dans l'historique
        GrillesService._log_modification(
            action, operateur_id, poste_id,
            operateur_nom, poste_code,
            old_niveau, new_niveau_int,
            old_date_eval,
            date.today() if action != 'DELETE' else None,
            (date.today() + timedelta(days=30 if new_niveau_int in [1, 2] else 3650)) if new_niveau_int else None
        )

        return action, old_niveau, new_niveau_int

    @staticmethod
    def _emit_polyvalence_events(
        action: str,
        operateur_id: int,
        poste_id: int,
        poste_code: str,
        old_niveau: Optional[int],
        new_niveau: int,
    ):
        """
        Émet les événements EventBus après modification de polyvalence.

        - INSERT → polyvalence.created (pour déclencher le document du poste)
        - UPDATE avec nouveau niveau → polyvalence.niveau_changed
          + polyvalence.niveau_1_reached si passage à 1
          + polyvalence.niveau_2_reached si passage à 2
          + polyvalence.niveau_3_reached si passage à 3
        """
        try:
            from core.services.event_bus import EventBus
            from core.repositories.personnel_repo import PersonnelRepository

            personnel = PersonnelRepository.get_by_id(operateur_id)
            if not personnel:
                return

            base_data = {
                'operateur_id': operateur_id,
                'nom': personnel.nom,
                'prenom': personnel.prenom,
                'poste_id': poste_id,
                'code_poste': poste_code,
                'niveau': new_niveau,
            }

            if action == 'INSERT':
                EventBus.emit('polyvalence.created', base_data,
                              source='GrillesService.update_polyvalence_from_grille')

            elif action == 'UPDATE' and old_niveau != new_niveau:
                event_data = {**base_data, 'old_niveau': old_niveau, 'new_niveau': new_niveau}
                EventBus.emit('polyvalence.niveau_changed', event_data,
                              source='GrillesService.update_polyvalence_from_grille')

                if new_niveau == 1:
                    EventBus.emit('polyvalence.niveau_1_reached', {**event_data, 'niveau': 1},
                                  source='GrillesService.update_polyvalence_from_grille')

                if new_niveau == 2 and (old_niveau is None or old_niveau < 2):
                    EventBus.emit('polyvalence.niveau_2_reached', {**event_data, 'niveau': 2},
                                  source='GrillesService.update_polyvalence_from_grille')

                if new_niveau == 3 and (old_niveau is None or old_niveau < 3):
                    EventBus.emit('polyvalence.niveau_3_reached', {**event_data, 'niveau': 3},
                                  source='GrillesService.update_polyvalence_from_grille')

        except Exception as e:
            logger.warning(f"Erreur émission événement polyvalence: {e}")

    @staticmethod
    def _log_modification(
        action: str,
        operateur_id: int,
        poste_id: int,
        operateur_nom: str,
        poste_code: str,
        old_niveau: Optional[int],
        new_niveau: Optional[int],
        old_date_eval,
        new_date_eval,
        prochaine_eval,
    ):
        """Enregistre la modification dans l'historique."""
        try:
            matricule = None
            atelier_nom = None
            utilisateur = None

            try:
                r = QueryExecutor.fetch_one(
                    "SELECT matricule FROM personnel WHERE id = %s",
                    (operateur_id,), dictionary=True
                )
                if r:
                    matricule = r.get('matricule')

                r = QueryExecutor.fetch_one("""
                    SELECT a.nom as atelier_nom
                    FROM postes p
                    LEFT JOIN atelier a ON p.atelier_id = a.id
                    WHERE p.id = %s
                """, (poste_id,), dictionary=True)
                if r:
                    atelier_nom = r.get('atelier_nom')

                from core.services.auth_service import get_current_user
                current_user = get_current_user()
                if current_user:
                    utilisateur = current_user.get('username') or \
                        f"{current_user.get('prenom', '')} {current_user.get('nom', '')}".strip()
            except Exception:
                pass

            base_info = {
                "operateur": operateur_nom,
                "matricule": matricule,
                "poste": poste_code,
                "atelier": atelier_nom,
                "source": "Grille de polyvalence"
            }

            if action == 'DELETE':
                description = json.dumps({
                    **base_info,
                    "niveau_supprime": old_niveau,
                    "date_eval_supprimee": str(old_date_eval) if old_date_eval else None,
                    "type": "suppression"
                }, ensure_ascii=False)
            elif action == 'INSERT':
                description = json.dumps({
                    **base_info,
                    "niveau": new_niveau,
                    "date_evaluation": str(new_date_eval),
                    "prochaine_evaluation": str(prochaine_eval),
                    "type": "ajout"
                }, ensure_ascii=False)
            else:
                description = json.dumps({
                    **base_info,
                    "changes": {"niveau": {"old": old_niveau, "new": new_niveau}},
                    "ancienne_date_eval": str(old_date_eval) if old_date_eval else None,
                    "nouvelle_date_eval": str(new_date_eval),
                    "prochaine_evaluation": str(prochaine_eval),
                    "type": "modification"
                }, ensure_ascii=False)

            QueryExecutor.execute_write("""
                INSERT INTO historique (date_time, action, operateur_id, poste_id, description, utilisateur)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (datetime.now(), action, operateur_id, poste_id, description, utilisateur))

        except Exception as e:
            logger.warning(f"Erreur logging historique grille: {e}")

    # =========================================================================
    # IMPORT EN LOT (save_modified_cells)
    # =========================================================================

    @staticmethod
    def save_polyvalence_batch(
        modifications: List[Tuple[int, int, str, str, str]]
    ) -> int:
        """
        Enregistre un lot de modifications de polyvalence.

        Args:
            modifications: liste de (operateur_id, poste_id, new_niveau_str, operateur_nom, poste_code)

        Returns:
            Nombre de modifications réussies
        """
        count = 0
        for operateur_id, poste_id, new_niveau_str, operateur_nom, poste_code in modifications:
            try:
                # Vérifier ancienne valeur
                existing = QueryExecutor.fetch_one("""
                    SELECT niveau FROM polyvalence
                    WHERE operateur_id = %s AND poste_id = %s
                """, (operateur_id, poste_id), dictionary=True)

                old_niveau = existing.get('niveau') if existing else None
                action = 'UPDATE' if existing else 'INSERT'
                new_niveau_int = int(new_niveau_str) if new_niveau_str else None

                QueryExecutor.execute_write(
                    "REPLACE INTO polyvalence (operateur_id, poste_id, niveau) VALUES (%s, %s, %s)",
                    (operateur_id, poste_id, new_niveau_int)
                )

                try:
                    from core.services.auth_service import get_current_user
                    current_user = get_current_user()
                    utilisateur = None
                    if current_user:
                        utilisateur = current_user.get('username') or \
                            f"{current_user.get('prenom', '')} {current_user.get('nom', '')}".strip()

                    changes = {}
                    if old_niveau != new_niveau_int:
                        changes["niveau"] = {"old": old_niveau, "new": new_niveau_int}

                    description = json.dumps({
                        "operateur": operateur_nom,
                        "poste": poste_code,
                        "changes": changes,
                        "type": "ajout" if action == 'INSERT' else "modification"
                    }, ensure_ascii=False)

                    QueryExecutor.execute_write("""
                        INSERT INTO historique (date_time, action, operateur_id, poste_id, description, utilisateur)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (datetime.now(), action, operateur_id, poste_id, description, utilisateur))
                except Exception as e:
                    logger.warning(f"Erreur logging batch: {e}")

                count += 1
            except Exception as e:
                logger.error(f"Erreur modification batch ({operateur_id}, {poste_id}): {e}")

        return count

    # =========================================================================
    # GESTION DES POSTES ET OPÉRATEURS (add_data / remove_data / duplicate_data)
    # =========================================================================

    @staticmethod
    def ajouter_poste(poste_code: str, besoin: Optional[int] = None) -> Tuple[bool, str]:
        """Ajoute un nouveau poste visible dans la grille."""
        if QueryExecutor.exists("postes", {"poste_code": poste_code}):
            return False, f"Le poste '{poste_code}' existe déjà."

        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO postes (poste_code, visible) VALUES (%s, 1)",
                (poste_code,)
            )
            if besoin is not None:
                cur.execute(
                    "UPDATE postes SET besoins_postes = %s WHERE poste_code = %s",
                    (besoin, poste_code)
                )
        return True, f"Poste '{poste_code}' créé avec succès."

    @staticmethod
    def ajouter_operateur(nom: str, prenom: str) -> Tuple[bool, str, Optional[int]]:
        """Ajoute un nouvel opérateur actif."""
        new_id = QueryExecutor.execute_write(
            "INSERT INTO personnel (nom, prenom, statut) VALUES (%s, %s, 'ACTIF')",
            (nom, prenom)
        )
        return True, f"Opérateur '{nom} {prenom}' ajouté.", new_id

    @staticmethod
    def masquer_poste(poste_code: str) -> Tuple[bool, str]:
        """Masque un poste (visible = 0)."""
        poste = QueryExecutor.fetch_one(
            "SELECT id FROM postes WHERE poste_code = %s AND visible = 1",
            (poste_code,), dictionary=True
        )
        if not poste:
            return False, f"Le poste '{poste_code}' n'existe pas ou est déjà masqué."

        QueryExecutor.execute_write(
            "UPDATE postes SET visible = 0 WHERE id = %s",
            (poste['id'],)
        )
        return True, f"Poste '{poste_code}' masqué."

    @staticmethod
    def masquer_operateur(operateur_id: int) -> Tuple[bool, str]:
        """Passe un opérateur en statut INACTIF."""
        QueryExecutor.execute_write(
            "UPDATE personnel SET statut = 'INACTIF' WHERE id = %s",
            (operateur_id,)
        )
        return True, "Opérateur masqué."

    @staticmethod
    def dupliquer_poste(poste_code: str) -> Tuple[bool, str]:
        """Duplique un poste et toute sa polyvalence."""
        poste = QueryExecutor.fetch_one(
            "SELECT id, poste_code FROM postes WHERE poste_code = %s AND visible = 1",
            (poste_code,), dictionary=True
        )
        if not poste:
            return False, f"Le poste '{poste_code}' n'existe pas ou est masqué."

        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO postes (poste_code, visible) VALUES (%s, 1)",
                (f"{poste_code}_copy",)
            )
            new_poste_id = cur.lastrowid
            cur.execute("""
                INSERT INTO polyvalence (operateur_id, poste_id, niveau)
                SELECT operateur_id, %s, niveau FROM polyvalence WHERE poste_id = %s
            """, (new_poste_id, poste['id']))

        return True, f"Poste '{poste_code}' dupliqué en '{poste_code}_copy'."

    @staticmethod
    def dupliquer_operateur(nom_complet: str) -> Tuple[bool, str]:
        """Duplique un opérateur et toute sa polyvalence."""
        operateur = QueryExecutor.fetch_one(
            "SELECT id, nom, prenom FROM personnel WHERE CONCAT(nom, ' ', prenom) = %s AND statut = 'ACTIF'",
            (nom_complet,), dictionary=True
        )
        if not operateur:
            return False, f"L'opérateur '{nom_complet}' n'existe pas ou est inactif."

        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO personnel (nom, prenom, statut) VALUES (%s, %s, 'ACTIF')",
                (f"{operateur['nom']}_copy", operateur['prenom'])
            )
            new_op_id = cur.lastrowid
            cur.execute("""
                INSERT INTO polyvalence (operateur_id, poste_id, niveau)
                SELECT %s, poste_id, niveau FROM polyvalence WHERE operateur_id = %s
            """, (new_op_id, operateur['id']))

        return True, f"Opérateur '{nom_complet}' dupliqué."
