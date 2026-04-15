# -*- coding: utf-8 -*-
"""
DetailOperateurViewModel — logique métier/données pour la fiche détail d'un opérateur.

N'importe aucun widget Qt (QMessageBox, QTableWidget, etc.).
Seuls QObject et pyqtSignal sont autorisés depuis PyQt5.
"""

from __future__ import annotations

import datetime as dt
import json

from PyQt5.QtCore import QObject, pyqtSignal

from domain.repositories.personnel_repo import PersonnelRepository
from domain.repositories.polyvalence_repo import PolyvalenceRepository
from domain.services.rh.contrat_service_crud import ContratServiceCRUD
from domain.services.formation.formation_service_crud import FormationServiceCRUD
from domain.services.rh import medical_service
from infrastructure.logging.logging_config import get_logger
from infrastructure.logging.optimized_db_logger import log_hist

logger = get_logger(__name__)


class DetailOperateurViewModel(QObject):
    """
    ViewModel pour DetailOperateurDialog.

    Signaux vers la View :
        profile_loaded(dict)        → données brutes infos complémentaires
        polyvalences_loaded(list)   → liste de dicts polyvalence prêts à afficher
        status_changed(str)         → nouveau statut ('ACTIF' ou 'INACTIF')
        error(str)                  → message d'erreur
    """

    profile_loaded      = pyqtSignal(dict)
    polyvalences_loaded = pyqtSignal(list)
    status_changed      = pyqtSignal(str)
    error               = pyqtSignal(str)

    def __init__(
        self,
        operateur_id: int,
        nom: str,
        prenom: str,
        statut: str,
        is_production: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.operateur_id  = operateur_id
        self.nom           = nom
        self.prenom        = prenom
        self.statut        = statut.upper()
        self.is_production = is_production

        # Chargé de façon synchrone à la construction (petite requête)
        self.date_entree = self._load_date_entree()

        # Cache pour les exports
        self.infos_data: list  = []   # [(section_title, [(label, value)])]
        self.polyvalences: list = []  # [dict prêt à afficher + exporter]

    # ------------------------------------------------------------------
    # Chargement principal (appelé dans un DbWorker)
    # ------------------------------------------------------------------

    def load_all(self, progress_callback=None):
        """
        Point d'entrée unique pour le chargement async.
        Emet profile_loaded et polyvalences_loaded.
        """
        try:
            profile = self._build_profile_data()
            self.infos_data = profile.get("infos_data", [])
            self.profile_loaded.emit(profile)
        except Exception as e:
            logger.exception(f"Erreur chargement profil opérateur {self.operateur_id}: {e}")
            self.error.emit(f"Impossible de charger les informations : {e}")

        if self.is_production:
            try:
                polys = self._build_polyvalences_data()
                self.polyvalences = polys
                self.polyvalences_loaded.emit(polys)
            except Exception as e:
                logger.exception(f"Erreur chargement polyvalences opérateur {self.operateur_id}: {e}")
                self.error.emit(f"Impossible de charger les polyvalences : {e}")

    # ------------------------------------------------------------------
    # Construction des données profil
    # ------------------------------------------------------------------

    def _build_profile_data(self) -> dict:
        """
        Charge et structure toutes les données de l'onglet Infos Complémentaires.

        Retourne un dict :
        {
          "infos_data": [(section_title, [(label, value), ...]), ...],
          "has_contrat": bool,
          "has_formations": bool,
        }
        """
        infos_data = []

        # --- Informations personnelles ---
        _pi = PersonnelRepository.get_personnel_infos(self.operateur_id)
        row_data = [_pi] if _pi else []

        personal_items = []
        if row_data:
            data = row_data[0]
            if data.get('date_entree'):
                date_entree_str = (
                    data['date_entree'].strftime("%d/%m/%Y")
                    if isinstance(data['date_entree'], dt.date)
                    else str(data['date_entree'])
                )
                personal_items.append(("Date d'entrée", date_entree_str))
            for key, val in data.items():
                if key in ("personnel_id", "date_entree"):
                    continue
                label = _format_column_name(key)
                value = (
                    val.strftime("%d/%m/%Y") if isinstance(val, dt.date)
                    else (str(val) if val not in (None, "") else None)
                )
                if value is not None:
                    personal_items.append((label, value))

        if not personal_items:
            personal_items.append(("Information", "Aucune information complémentaire enregistrée"))

        infos_data.append(("Informations Personnelles", personal_items))

        # --- Contrat actuel ---
        contr = ContratServiceCRUD.get_by_operateur(self.operateur_id, actif_only=True)[:1]
        contract_items = []
        if contr:
            c = contr[0]
            if c.get("type_contrat"):
                contract_items.append(("Type", c.get("type_contrat")))
            if c.get("etp") is not None:
                contract_items.append(("ETP", str(c.get("etp"))))
            if c.get("categorie"):
                contract_items.append(("Catégorie", c.get("categorie")))
            d1, d2 = c.get("date_debut"), c.get("date_fin")
            if d1:
                deb = d1.strftime("%d/%m/%Y") if isinstance(d1, dt.date) else str(d1)
                contract_items.append(("Début", deb))
            if d2:
                fin = d2.strftime("%d/%m/%Y") if isinstance(d2, dt.date) else str(d2)
                contract_items.append(("Fin", fin))
        else:
            contract_items.append(("Statut", "Aucun contrat actif"))

        infos_data.append(("Contrat Actuel", contract_items))

        # --- Formations ---
        formations = FormationServiceCRUD.get_by_operateur(self.operateur_id)[:5]
        formation_items = []
        if formations:
            for f in formations:
                d1 = _format_date(f.get("date_debut"))
                d2 = _format_date(f.get("date_fin"))
                cert = " ✓" if f.get("certificat_obtenu") else ""
                intitule = f.get("intitule", "(formation)")
                formation_items.append((intitule, f"{d1} → {d2}{cert}"))
        else:
            formation_items.append(("Aucune formation", "Aucune formation renseignée"))

        infos_data.append(("Formations", formation_items))

        # --- Validités médicales ---
        validites = medical_service.get_validites_operateur(self.operateur_id)
        validite_items = []
        if validites:
            for v in validites:
                d1 = _format_date(v.get("date_debut"))
                d2 = _format_date(v.get("date_fin")) if v.get("date_fin") else "—"
                tc = f" ({v['taux_incapacite']}%)" if v.get("taux_incapacite") is not None else ""
                type_val = v.get("type_validite", "(type)")
                validite_items.append((type_val, f"{d1} → {d2}{tc}"))
        else:
            validite_items.append(("Aucune validité", "Aucune validité enregistrée"))

        infos_data.append(("Validités", validite_items))

        return {
            "infos_data":    infos_data,
            "has_contrat":   bool(contr),
            "has_formations": bool(formations),
        }

    # ------------------------------------------------------------------
    # Construction des données polyvalence
    # ------------------------------------------------------------------

    def _build_polyvalences_data(self) -> list:
        """
        Charge les polyvalences et calcule les stats niveaux.

        Retourne une liste de dicts :
        {
          poste, niveau, date_evaluation, prochaine_evaluation,
          anciennete, statut_eval,   # chaînes formatées
          bg_color, fg_color,        # couleurs Qt (#xxxxxx)
          en_retard: bool,
        }
        Ainsi que le dernier élément spécial :
        {"__stats__": True, "n1": int, "n2": int, "n3": int, "n4": int, "total": int}
        """
        rows = PolyvalenceRepository.get_by_operateur_dict(self.operateur_id)
        niveaux = {1: 0, 2: 0, 3: 0, 4: 0}
        result = []
        anciennete_str = self._calculate_anciennete()

        NIVEAU_COLORS = {
            1: ("#fef2f2", "#dc2626"),
            2: ("#fffbeb", "#d97706"),
            3: ("#f0fdf4", "#059669"),
            4: ("#eff6ff", "#2563eb"),
        }

        for r in rows:
            niveau   = r.get("niveau")
            date_eval = r.get("date_evaluation")
            date_next = r.get("prochaine_evaluation")

            if niveau and isinstance(niveau, int) and niveau in niveaux:
                niveaux[niveau] += 1

            en_retard = False
            if date_next:
                today = dt.date.today()
                if isinstance(date_next, str):
                    next_date = dt.datetime.strptime(date_next, "%Y-%m-%d").date()
                elif hasattr(date_next, "date"):
                    next_date = date_next.date()
                else:
                    next_date = date_next
                en_retard = next_date < today

            if en_retard:
                statut_eval = "En retard"
            elif date_next:
                statut_eval = "À jour"
            else:
                statut_eval = "À planifier"

            bg, fg = NIVEAU_COLORS.get(niveau, ("#ffffff", "#000000")) if niveau else ("#ffffff", "#000000")

            result.append({
                "poste":               str(r.get("poste_code", "")),
                "niveau":              str(niveau) if niveau else "N/A",
                "date_evaluation":     _format_date(date_eval),
                "prochaine_evaluation": _format_date(date_next),
                "anciennete":          anciennete_str,
                "statut_eval":         statut_eval,
                "bg_color":            bg,
                "fg_color":            fg,
                "en_retard":           en_retard,
                "niveau_int":          niveau,
            })

        result.append({
            "__stats__": True,
            "n1": niveaux[1], "n2": niveaux[2],
            "n3": niveaux[3], "n4": niveaux[4],
            "total": sum(niveaux.values()),
        })
        return result

    # ------------------------------------------------------------------
    # Changement de statut
    # ------------------------------------------------------------------

    def toggle_status(self) -> None:
        """
        Bascule le statut ACTIF ↔ INACTIF.
        Emet status_changed(new_statut) en cas de succès, error(msg) en cas d'échec.
        """
        new_statut = "INACTIF" if self.statut == "ACTIF" else "ACTIF"
        try:
            if new_statut == "INACTIF":
                PersonnelRepository.desactiver(self.operateur_id)
            else:
                PersonnelRepository.reactiver(self.operateur_id)

            pers_info = PersonnelRepository.get_info_basique(self.operateur_id)
            if pers_info:
                log_hist(
                    action="UPDATE",
                    table_name="personnel",
                    record_id=self.operateur_id,
                    operateur_id=self.operateur_id,
                    description=json.dumps({
                        "operateur": f"{pers_info['prenom']} {pers_info['nom']}",
                        "old_statut": self.statut,
                        "new_statut": new_statut,
                        "type": "changement_statut",
                    }, ensure_ascii=False),
                    source="GUI/detail_operateur_dialog"
                )

            self.statut = new_statut
            self.status_changed.emit(new_statut)

        except Exception as e:
            logger.exception(f"Erreur modification statut opérateur {self.operateur_id}: {e}")
            self.error.emit(f"Impossible de modifier le statut : {e}")

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------

    def _load_date_entree(self):
        """Charge la date d'entrée depuis personnel_infos."""
        try:
            return PersonnelRepository.get_date_entree(self.operateur_id)
        except Exception:
            return None

    def _calculate_anciennete(self) -> str:
        """Calcule l'ancienneté à partir de la date d'entrée."""
        if self.date_entree is None:
            return "N/A"
        try:
            if isinstance(self.date_entree, str):
                date_obj = dt.datetime.strptime(self.date_entree, "%Y-%m-%d").date()
            elif hasattr(self.date_entree, "date"):
                date_obj = self.date_entree.date()
            else:
                date_obj = self.date_entree

            delta = dt.date.today() - date_obj
            years  = delta.days // 365
            months = (delta.days % 365) // 30

            if years > 0:
                return f"{years} an(s) {months} mois"
            elif months > 0:
                return f"{months} mois"
            else:
                return f"{delta.days} jour(s)"
        except Exception:
            return "N/A"


# ------------------------------------------------------------------
# Fonctions utilitaires (module-level, réutilisables)
# ------------------------------------------------------------------

def _format_date(date_val) -> str:
    """Formate une date en DD/MM/YYYY."""
    import datetime as _dt
    if date_val is None:
        return "N/A"
    if isinstance(date_val, str):
        try:
            return _dt.datetime.strptime(date_val, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return date_val
    if hasattr(date_val, "strftime"):
        return date_val.strftime("%d/%m/%Y")
    return str(date_val)


def _format_column_name(col_name: str) -> str:
    """Convertit un nom de colonne SQL en texte lisible."""
    if not col_name:
        return ""
    formatted = col_name.replace("_", " ")
    formatted = " ".join(word.capitalize() for word in formatted.split())
    replacements = {
        "Cp": "CP", "Rtt": "RTT", "Id": "ID",
        "Nir": "NIR", "Etp": "ETP", "Operateur": "Opérateur",
    }
    for old, new in replacements.items():
        formatted = formatted.replace(old, new)
    return formatted
