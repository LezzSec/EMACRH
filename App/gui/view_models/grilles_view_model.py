# -*- coding: utf-8 -*-
"""
ViewModel pour la grille de polyvalence.
Encapsule toute la logique métier : chargement, sauvegarde cellule, calcul statistiques.
Aucune dépendance PyQt5.QtWidgets.
"""

from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import QObject, pyqtSignal

from domain.services.formation.grilles_service import GrillesService
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class GrillesViewModel(QObject):
    """Gère les données de la grille de polyvalence, sans logique d'affichage.

    Signals:
        grille_loaded(postes, operateurs, niveaux, besoins)
            postes    : list[(id, poste_code)]
            operateurs: list[(id, nom_complet)]   — triés A→Z
            niveaux   : dict{(operateur_id, poste_id): niveau_int_ou_str}
            besoins   : dict{poste_id: valeur_ou_None}

        cell_saved(row, col, action, old_niveau, new_niveau)
            action : 'INSERT' | 'UPDATE' | 'DELETE'

        statistics_updated(stats)
            stats : dict{col_idx: {'n1','n2','n3','n4','total','total_34'}}

        error(message)
    """

    grille_loaded = pyqtSignal(list, list, dict, dict)
    cell_saved = pyqtSignal(int, int, str, object, object)
    statistics_updated = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.postes: List[Tuple[int, str]] = []
        self.operateurs: List[Tuple[int, str]] = []
        self._niveaux: Dict = {}
        self._besoins: Dict = {}

    # ------------------------------------------------------------------ #
    # Chargement                                                           #
    # ------------------------------------------------------------------ #

    def load_grille(self) -> None:
        """Charge la grille depuis le service et émet grille_loaded."""
        try:
            grille = GrillesService.get_grille_data()

            raw_postes: List[Tuple[int, str]] = grille['postes']
            raw_niveaux: Dict = grille['niveaux']
            raw_besoins: Dict = grille['besoins']

            operateurs_dict: Dict[str, Dict] = {}
            for op_id, nom_complet in grille['operateurs']:
                operateurs_dict[nom_complet] = {'id': op_id}

            sorted_ops = sorted(operateurs_dict.items())
            self.operateurs = [(data['id'], nom) for nom, data in sorted_ops]
            self.postes = list(raw_postes)
            self._niveaux = dict(raw_niveaux)
            self._besoins = dict(raw_besoins)

            self.grille_loaded.emit(
                list(self.postes),
                list(self.operateurs),
                dict(self._niveaux),
                dict(self._besoins),
            )
        except Exception as e:
            logger.exception(f"Erreur chargement grille: {e}")
            self.error.emit(str(e))

    # ------------------------------------------------------------------ #
    # Sauvegarde cellule                                                   #
    # ------------------------------------------------------------------ #

    def save_cell(
        self,
        row: int,
        col: int,
        operateur_id: int,
        poste_id: int,
        new_niveau_str: str,
        operateur_nom: str,
        poste_code: str,
    ) -> None:
        """Persiste une modification de cellule et émet cell_saved."""
        try:
            action, old_niveau, new_niveau = GrillesService.update_polyvalence_from_grille(
                operateur_id=operateur_id,
                poste_id=poste_id,
                new_niveau_str=new_niveau_str,
                operateur_nom=operateur_nom,
                poste_code=poste_code,
            )
            self.cell_saved.emit(row, col, action, old_niveau, new_niveau)
        except Exception as e:
            logger.exception(f"Erreur sauvegarde cellule ({row},{col}): {e}")
            self.error.emit(str(e))

    # ------------------------------------------------------------------ #
    # Sauvegarde en lot                                                    #
    # ------------------------------------------------------------------ #

    def save_batch(self, modifications: List[Tuple]) -> int:
        """Sauvegarde un ensemble de modifications.

        Args:
            modifications: list of (operateur_id, poste_id, new_niveau, operateur_nom, poste_code)

        Returns:
            Nombre de modifications enregistrées.
        """
        try:
            count = GrillesService.save_polyvalence_batch(modifications)
            return count
        except Exception as e:
            logger.exception(f"Erreur sauvegarde batch: {e}")
            self.error.emit(str(e))
            return 0

    # ------------------------------------------------------------------ #
    # Rechargement d'une cellule                                           #
    # ------------------------------------------------------------------ #

    def get_cell_niveau(self, operateur_id: int, poste_id: int) -> Optional[int]:
        """Recharge le niveau d'une cellule depuis la DB."""
        try:
            return GrillesService.get_polyvalence_niveau(operateur_id, poste_id)
        except Exception as e:
            logger.error(f"Erreur rechargement cellule: {e}")
            return None

    # ------------------------------------------------------------------ #
    # Calcul statistiques                                                  #
    # ------------------------------------------------------------------ #

    def compute_statistics(
        self,
        cell_values: Dict[Tuple[int, int], str],
        n_operators: int,
        n_columns: int,
    ) -> Dict[int, Dict]:
        """Calcule les statistiques par colonne à partir des valeurs de cellule.

        Args:
            cell_values: dict{(row, col): text} pour les lignes opérateurs uniquement.
            n_operators: Nombre d'opérateurs (lignes de données).
            n_columns: Nombre de colonnes (postes).

        Returns:
            dict{col: {'n1','n2','n3','n4','total','total_34'}}
        """
        stats: Dict[int, Dict] = {}
        for col in range(n_columns):
            niveaux = []
            for row in range(n_operators):
                txt = cell_values.get((row, col), "").strip()
                if txt.isdigit():
                    niveaux.append(int(txt))
            n1, n2, n3, n4 = (niveaux.count(i) for i in (1, 2, 3, 4))
            total = len(niveaux)
            stats[col] = {
                'n1': n1, 'n2': n2, 'n3': n3, 'n4': n4,
                'total': total, 'total_34': n3 + n4,
            }
        return stats
