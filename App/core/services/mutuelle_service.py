# -*- coding: utf-8 -*-
"""
Service Mutuelle - Gestion de la complémentaire santé des salariés.

Gère:
- Statut d'adhésion (adhérent, dispensé, en attente, non couvert)
- Formule choisie (Simple/Turbo x Isolé/Duo/Famille)
- DUE signée
- Dispenses d'adhésion avec suivi du justificatif
- Organisme et numéro adhérent
"""

from typing import Dict, List, Optional, Tuple

from core.db.query_executor import QueryExecutor
from core.services.permission_manager import require
from core.services.logger import log_hist
from core.utils.logging_config import get_logger

logger = get_logger(__name__)


def get_mutuelle(personnel_id: int) -> Optional[Dict]:
    """Retourne la mutuelle du salarié (dernier enregistrement)."""
    return QueryExecutor.fetch_one(
        "SELECT * FROM mutuelle WHERE personnel_id = %s ORDER BY id DESC LIMIT 1",
        (personnel_id,),
        dictionary=True,
    )


def get_historique_mutuelle(personnel_id: int) -> List[Dict]:
    """Retourne tous les enregistrements mutuelle du salarié."""
    return QueryExecutor.fetch_all(
        "SELECT * FROM mutuelle WHERE personnel_id = %s ORDER BY date_adhesion DESC, id DESC",
        (personnel_id,),
        dictionary=True,
    )


def create_mutuelle(personnel_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
    """Crée un enregistrement mutuelle."""
    require('rh.mutuelle.edit')
    try:
        new_id = QueryExecutor.execute_write(
            """
            INSERT INTO mutuelle
                (personnel_id, statut_adhesion, due_signee, type_formule,
                 situation_familiale, type_dispense, justificatif_validite,
                 organisme, numero_adherent, date_adhesion, date_fin, commentaire)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                personnel_id,
                data.get('statut_adhesion', 'NON_COUVERT'),
                bool(data.get('due_signee', False)),
                data.get('type_formule') or None,
                data.get('situation_familiale') or None,
                data.get('type_dispense') or None,
                data.get('justificatif_validite') or None,
                data.get('organisme') or None,
                data.get('numero_adherent') or None,
                data.get('date_adhesion') or None,
                data.get('date_fin') or None,
                data.get('commentaire') or None,
            ),
        )
        log_hist(
            "CREATION_MUTUELLE",
            f"Mutuelle créée (statut: {data.get('statut_adhesion')}) pour personnel {personnel_id}",
            operateur_id=personnel_id,
        )
        return True, "Enregistrement créé", new_id
    except Exception as e:
        logger.exception(f"Erreur create_mutuelle: {e}")
        return False, str(e), None


def update_mutuelle(record_id: int, data: Dict) -> Tuple[bool, str]:
    """Met à jour un enregistrement mutuelle."""
    require('rh.mutuelle.edit')
    try:
        QueryExecutor.execute_write(
            """
            UPDATE mutuelle
            SET statut_adhesion      = %s,
                due_signee           = %s,
                type_formule         = %s,
                situation_familiale  = %s,
                type_dispense        = %s,
                justificatif_validite = %s,
                organisme            = %s,
                numero_adherent      = %s,
                date_adhesion        = %s,
                date_fin             = %s,
                commentaire          = %s
            WHERE id = %s
            """,
            (
                data.get('statut_adhesion', 'NON_COUVERT'),
                bool(data.get('due_signee', False)),
                data.get('type_formule') or None,
                data.get('situation_familiale') or None,
                data.get('type_dispense') or None,
                data.get('justificatif_validite') or None,
                data.get('organisme') or None,
                data.get('numero_adherent') or None,
                data.get('date_adhesion') or None,
                data.get('date_fin') or None,
                data.get('commentaire') or None,
                record_id,
            ),
        )
        log_hist("MODIFICATION_MUTUELLE", f"Mutuelle {record_id} modifiée")
        return True, "Enregistrement mis à jour"
    except Exception as e:
        logger.exception(f"Erreur update_mutuelle: {e}")
        return False, str(e)


def delete_mutuelle(record_id: int) -> Tuple[bool, str]:
    """Supprime un enregistrement mutuelle."""
    require('rh.mutuelle.edit')
    try:
        QueryExecutor.execute_write("DELETE FROM mutuelle WHERE id = %s", (record_id,))
        log_hist("SUPPRESSION_MUTUELLE", f"Mutuelle {record_id} supprimée")
        return True, "Enregistrement supprimé"
    except Exception as e:
        logger.exception(f"Erreur delete_mutuelle: {e}")
        return False, str(e)
