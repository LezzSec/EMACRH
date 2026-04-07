# -*- coding: utf-8 -*-
"""
ConfigService - Services CRUD pour les tables de référence configurables.

Gère les données de paramétrage de l'application :
  - Ateliers, Services, Types d'absence, Jours fériés,
    Compétences, Catégories documents, Motifs de sortie,
    Tranches d'âge, Rôles.

Toutes les opérations d'écriture sont tracées dans l'historique.
"""

from infrastructure.db.query_executor import QueryExecutor
from infrastructure.logging.optimized_db_logger import log_hist
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────
# Ateliers
# ─────────────────────────────────────────

class AtelierService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, nom FROM atelier ORDER BY nom",
            dictionary=True
        )

    @staticmethod
    def create(nom: str) -> int:
        nom = nom.strip()
        new_id = QueryExecutor.execute_write(
            "INSERT INTO atelier (nom) VALUES (%s)", (nom,)
        )
        log_hist("CREATION_ATELIER", f"Atelier créé : {nom}")
        return new_id

    @staticmethod
    def update(atelier_id: int, nom: str) -> None:
        nom = nom.strip()
        QueryExecutor.execute_write(
            "UPDATE atelier SET nom=%s WHERE id=%s", (nom, atelier_id)
        )
        log_hist("MODIFICATION_ATELIER", f"Atelier #{atelier_id} modifié : {nom}")

    @staticmethod
    def delete(atelier_id: int) -> tuple:
        """Retourne (success: bool, message: str)."""
        count = QueryExecutor.count('postes', {'atelier_id': atelier_id})
        if count > 0:
            return False, f"Impossible : {count} poste(s) référencent cet atelier."
        QueryExecutor.execute_write("DELETE FROM atelier WHERE id=%s", (atelier_id,))
        log_hist("SUPPRESSION_ATELIER", f"Atelier #{atelier_id} supprimé")
        return True, "Atelier supprimé."


# ─────────────────────────────────────────
# Services RH
# ─────────────────────────────────────────

class ServicesRHService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, nom_service, description FROM services ORDER BY nom_service",
            dictionary=True
        )

    @staticmethod
    def create(nom_service: str, description: str = None) -> int:
        nom_service = nom_service.strip()
        new_id = QueryExecutor.execute_write(
            "INSERT INTO services (nom_service, description) VALUES (%s, %s)",
            (nom_service, description)
        )
        log_hist("CREATION_SERVICE", f"Service créé : {nom_service}")
        return new_id

    @staticmethod
    def update(service_id: int, nom_service: str, description: str = None) -> None:
        nom_service = nom_service.strip()
        QueryExecutor.execute_write(
            "UPDATE services SET nom_service=%s, description=%s WHERE id=%s",
            (nom_service, description, service_id)
        )
        log_hist("MODIFICATION_SERVICE", f"Service #{service_id} modifié : {nom_service}")

    @staticmethod
    def delete(service_id: int) -> tuple:
        count = QueryExecutor.count('personnel', {'service_id': service_id})
        if count > 0:
            return False, f"Impossible : {count} personnel(s) sont rattachés à ce service."
        QueryExecutor.execute_write("DELETE FROM services WHERE id=%s", (service_id,))
        log_hist("SUPPRESSION_SERVICE", f"Service #{service_id} supprimé")
        return True, "Service supprimé."


# ─────────────────────────────────────────
# Types d'absence
# ─────────────────────────────────────────

class TypeAbsenceService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, code, libelle, decompte_solde, couleur, actif "
            "FROM type_absence ORDER BY code",
            dictionary=True
        )

    @staticmethod
    def create(code: str, libelle: str, decompte_solde: bool = True,
               couleur: str = '#3498db', actif: bool = True) -> int:
        code = code.strip().upper()
        libelle = libelle.strip()
        new_id = QueryExecutor.execute_write(
            "INSERT INTO type_absence (code, libelle, decompte_solde, couleur, actif) "
            "VALUES (%s, %s, %s, %s, %s)",
            (code, libelle, int(decompte_solde), couleur, int(actif))
        )
        log_hist("CREATION_TYPE_ABSENCE", f"Type absence créé : {code} - {libelle}")
        return new_id

    @staticmethod
    def update(type_id: int, code: str, libelle: str,
               decompte_solde: bool, couleur: str, actif: bool) -> None:
        code = code.strip().upper()
        libelle = libelle.strip()
        QueryExecutor.execute_write(
            "UPDATE type_absence SET code=%s, libelle=%s, decompte_solde=%s, "
            "couleur=%s, actif=%s WHERE id=%s",
            (code, libelle, int(decompte_solde), couleur, int(actif), type_id)
        )
        log_hist("MODIFICATION_TYPE_ABSENCE", f"Type absence #{type_id} modifié : {code}")

    @staticmethod
    def delete(type_id: int) -> tuple:
        count = QueryExecutor.count('demande_absence', {'type_absence_id': type_id})
        if count > 0:
            return False, f"Impossible : {count} demande(s) d'absence utilisent ce type."
        QueryExecutor.execute_write("DELETE FROM type_absence WHERE id=%s", (type_id,))
        log_hist("SUPPRESSION_TYPE_ABSENCE", f"Type absence #{type_id} supprimé")
        return True, "Type d'absence supprimé."


# ─────────────────────────────────────────
# Jours fériés
# ─────────────────────────────────────────

class JoursFeriesService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, date_ferie, libelle, fixe FROM jours_feries ORDER BY date_ferie",
            dictionary=True
        )

    @staticmethod
    def create(date_ferie: str, libelle: str, fixe: bool = True) -> int:
        libelle = libelle.strip()
        new_id = QueryExecutor.execute_write(
            "INSERT INTO jours_feries (date_ferie, libelle, fixe) VALUES (%s, %s, %s)",
            (date_ferie, libelle, int(fixe))
        )
        log_hist("CREATION_JOUR_FERIE", f"Jour férié créé : {date_ferie} - {libelle}")
        return new_id

    @staticmethod
    def update(jour_id: int, date_ferie: str, libelle: str, fixe: bool) -> None:
        libelle = libelle.strip()
        QueryExecutor.execute_write(
            "UPDATE jours_feries SET date_ferie=%s, libelle=%s, fixe=%s WHERE id=%s",
            (date_ferie, libelle, int(fixe), jour_id)
        )
        log_hist("MODIFICATION_JOUR_FERIE", f"Jour férié #{jour_id} modifié : {date_ferie}")

    @staticmethod
    def delete(jour_id: int) -> tuple:
        QueryExecutor.execute_write("DELETE FROM jours_feries WHERE id=%s", (jour_id,))
        log_hist("SUPPRESSION_JOUR_FERIE", f"Jour férié #{jour_id} supprimé")
        return True, "Jour férié supprimé."


# ─────────────────────────────────────────
# Compétences catalogue
# ─────────────────────────────────────────

class CompetencesCatalogueService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, code, libelle, description, categorie, "
            "duree_validite_mois, actif FROM competences_catalogue ORDER BY code",
            dictionary=True
        )

    @staticmethod
    def create(code: str, libelle: str, description: str = None,
               categorie: str = None, duree_validite_mois: int = None,
               actif: bool = True) -> int:
        code = code.strip().upper()
        libelle = libelle.strip()
        new_id = QueryExecutor.execute_write(
            "INSERT INTO competences_catalogue "
            "(code, libelle, description, categorie, duree_validite_mois, actif) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (code, libelle, description, categorie, duree_validite_mois, int(actif))
        )
        log_hist("CREATION_COMPETENCE", f"Compétence créée : {code} - {libelle}")
        return new_id

    @staticmethod
    def update(comp_id: int, code: str, libelle: str, description: str,
               categorie: str, duree_validite_mois: int, actif: bool) -> None:
        code = code.strip().upper()
        libelle = libelle.strip()
        QueryExecutor.execute_write(
            "UPDATE competences_catalogue SET code=%s, libelle=%s, description=%s, "
            "categorie=%s, duree_validite_mois=%s, actif=%s WHERE id=%s",
            (code, libelle, description, categorie, duree_validite_mois, int(actif), comp_id)
        )
        log_hist("MODIFICATION_COMPETENCE", f"Compétence #{comp_id} modifiée : {code}")

    @staticmethod
    def delete(comp_id: int) -> tuple:
        count = QueryExecutor.count('personnel_competences', {'competence_id': comp_id})
        if count > 0:
            return False, f"Impossible : {count} personnel(s) possèdent cette compétence."
        QueryExecutor.execute_write(
            "DELETE FROM competences_catalogue WHERE id=%s", (comp_id,)
        )
        log_hist("SUPPRESSION_COMPETENCE", f"Compétence #{comp_id} supprimée")
        return True, "Compétence supprimée."


# ─────────────────────────────────────────
# Catégories de documents
# ─────────────────────────────────────────

class CategoriesDocsService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, nom, description, couleur, exige_date_expiration, ordre_affichage "
            "FROM categories_documents ORDER BY ordre_affichage, nom",
            dictionary=True
        )

    @staticmethod
    def create(nom: str, description: str = None, couleur: str = '#3b82f6',
               exige_date_expiration: bool = False, ordre_affichage: int = 0) -> int:
        nom = nom.strip()
        new_id = QueryExecutor.execute_write(
            "INSERT INTO categories_documents "
            "(nom, description, couleur, exige_date_expiration, ordre_affichage) "
            "VALUES (%s, %s, %s, %s, %s)",
            (nom, description, couleur, int(exige_date_expiration), ordre_affichage)
        )
        log_hist("CREATION_CATEGORIE_DOC", f"Catégorie document créée : {nom}")
        return new_id

    @staticmethod
    def update(cat_id: int, nom: str, description: str, couleur: str,
               exige_date_expiration: bool, ordre_affichage: int) -> None:
        nom = nom.strip()
        QueryExecutor.execute_write(
            "UPDATE categories_documents SET nom=%s, description=%s, couleur=%s, "
            "exige_date_expiration=%s, ordre_affichage=%s WHERE id=%s",
            (nom, description, couleur, int(exige_date_expiration), ordre_affichage, cat_id)
        )
        log_hist("MODIFICATION_CATEGORIE_DOC", f"Catégorie document #{cat_id} modifiée : {nom}")

    @staticmethod
    def delete(cat_id: int) -> tuple:
        count = QueryExecutor.count('documents', {'categorie_id': cat_id})
        if count > 0:
            return False, f"Impossible : {count} document(s) appartiennent à cette catégorie."
        QueryExecutor.execute_write(
            "DELETE FROM categories_documents WHERE id=%s", (cat_id,)
        )
        log_hist("SUPPRESSION_CATEGORIE_DOC", f"Catégorie document #{cat_id} supprimée")
        return True, "Catégorie supprimée."


# ─────────────────────────────────────────
# Motifs de sortie
# ─────────────────────────────────────────

class RefMotifSortieService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, libelle, actif FROM ref_motif_sortie ORDER BY libelle",
            dictionary=True
        )

    @staticmethod
    def create(libelle: str, actif: bool = True) -> int:
        libelle = libelle.strip()
        new_id = QueryExecutor.execute_write(
            "INSERT INTO ref_motif_sortie (libelle, actif) VALUES (%s, %s)",
            (libelle, int(actif))
        )
        log_hist("CREATION_MOTIF_SORTIE", f"Motif de sortie créé : {libelle}")
        return new_id

    @staticmethod
    def update(motif_id: int, libelle: str, actif: bool) -> None:
        libelle = libelle.strip()
        QueryExecutor.execute_write(
            "UPDATE ref_motif_sortie SET libelle=%s, actif=%s WHERE id=%s",
            (libelle, int(actif), motif_id)
        )
        log_hist("MODIFICATION_MOTIF_SORTIE", f"Motif de sortie #{motif_id} modifié : {libelle}")

    @staticmethod
    def delete(motif_id: int) -> tuple:
        QueryExecutor.execute_write(
            "DELETE FROM ref_motif_sortie WHERE id=%s", (motif_id,)
        )
        log_hist("SUPPRESSION_MOTIF_SORTIE", f"Motif de sortie #{motif_id} supprimé")
        return True, "Motif de sortie supprimé."


# ─────────────────────────────────────────
# Tranches d'âge
# ─────────────────────────────────────────

class TranchesAgeService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, libelle, age_min, age_max FROM tranche_age ORDER BY age_min",
            dictionary=True
        )

    @staticmethod
    def create(libelle: str, age_min: int, age_max: int = None) -> int:
        libelle = libelle.strip()
        new_id = QueryExecutor.execute_write(
            "INSERT INTO tranche_age (libelle, age_min, age_max) VALUES (%s, %s, %s)",
            (libelle, age_min, age_max)
        )
        log_hist("CREATION_TRANCHE_AGE", f"Tranche d'âge créée : {libelle}")
        return new_id

    @staticmethod
    def update(tranche_id: int, libelle: str, age_min: int, age_max: int = None) -> None:
        libelle = libelle.strip()
        QueryExecutor.execute_write(
            "UPDATE tranche_age SET libelle=%s, age_min=%s, age_max=%s WHERE id=%s",
            (libelle, age_min, age_max, tranche_id)
        )
        log_hist("MODIFICATION_TRANCHE_AGE", f"Tranche d'âge #{tranche_id} modifiée : {libelle}")

    @staticmethod
    def delete(tranche_id: int) -> tuple:
        QueryExecutor.execute_write(
            "DELETE FROM tranche_age WHERE id=%s", (tranche_id,)
        )
        log_hist("SUPPRESSION_TRANCHE_AGE", f"Tranche d'âge #{tranche_id} supprimée")
        return True, "Tranche d'âge supprimée."


# ─────────────────────────────────────────
# Rôles
# ─────────────────────────────────────────

class RolesConfigService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, nom, description FROM roles ORDER BY nom",
            dictionary=True
        )

    @staticmethod
    def create(nom: str, description: str = None) -> int:
        nom = nom.strip()
        new_id = QueryExecutor.execute_write(
            "INSERT INTO roles (nom, description) VALUES (%s, %s)",
            (nom, description)
        )
        log_hist("CREATION_ROLE", f"Rôle créé : {nom}")
        return new_id

    @staticmethod
    def update(role_id: int, nom: str, description: str = None) -> None:
        nom = nom.strip()
        QueryExecutor.execute_write(
            "UPDATE roles SET nom=%s, description=%s WHERE id=%s",
            (nom, description, role_id)
        )
        log_hist("MODIFICATION_ROLE", f"Rôle #{role_id} modifié : {nom}")

    @staticmethod
    def delete(role_id: int) -> tuple:
        count = QueryExecutor.count('utilisateurs', {'role_id': role_id})
        if count > 0:
            return False, f"Impossible : {count} utilisateur(s) ont ce rôle."
        QueryExecutor.execute_write("DELETE FROM roles WHERE id=%s", (role_id,))
        log_hist("SUPPRESSION_ROLE", f"Rôle #{role_id} supprimé")
        return True, "Rôle supprimé."


# ─────────────────────────────────────────
# Solde de congés
# ─────────────────────────────────────────

class SoldeCongesService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT sc.*, p.nom, p.prenom "
            "FROM solde_conges sc "
            "JOIN personnel p ON p.id = sc.personnel_id "
            "ORDER BY sc.annee DESC, p.nom",
            dictionary=True
        )

    @staticmethod
    def get_all_personnel() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, nom, prenom FROM personnel WHERE statut='ACTIF' ORDER BY nom",
            dictionary=True
        )

    @staticmethod
    def create(personnel_id: int, annee: int, cp_acquis: float = 0.0,
               cp_n_1: float = 0.0, cp_pris: float = 0.0,
               rtt_acquis: float = 0.0, rtt_pris: float = 0.0) -> int:
        new_id = QueryExecutor.execute_write(
            "INSERT INTO solde_conges "
            "(personnel_id, annee, cp_acquis, cp_n_1, cp_pris, rtt_acquis, rtt_pris, date_maj) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
            (personnel_id, annee, cp_acquis, cp_n_1, cp_pris, rtt_acquis, rtt_pris)
        )
        log_hist("CREATION_SOLDE_CONGES", f"Solde congés créé : personnel #{personnel_id} année {annee}")
        return new_id

    @staticmethod
    def update(solde_id: int, personnel_id: int, annee: int, cp_acquis: float,
               cp_n_1: float, cp_pris: float, rtt_acquis: float, rtt_pris: float) -> None:
        QueryExecutor.execute_write(
            "UPDATE solde_conges SET personnel_id=%s, annee=%s, cp_acquis=%s, "
            "cp_n_1=%s, cp_pris=%s, rtt_acquis=%s, rtt_pris=%s, date_maj=NOW() "
            "WHERE id=%s",
            (personnel_id, annee, cp_acquis, cp_n_1, cp_pris, rtt_acquis, rtt_pris, solde_id)
        )
        log_hist("MODIFICATION_SOLDE_CONGES", f"Solde congés #{solde_id} modifié")

    @staticmethod
    def delete(solde_id: int) -> tuple:
        QueryExecutor.execute_write("DELETE FROM solde_conges WHERE id=%s", (solde_id,))
        log_hist("SUPPRESSION_SOLDE_CONGES", f"Solde congés #{solde_id} supprimé")
        return True, "Solde de congés supprimé."


# ─────────────────────────────────────────
# Règles événements documents
# ─────────────────────────────────────────

class DocumentEventRulesService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT der.*, dt.nom as template_nom "
            "FROM document_event_rules der "
            "LEFT JOIN documents_templates dt ON dt.id = der.template_id "
            "ORDER BY der.event_name, der.priority",
            dictionary=True
        )

    @staticmethod
    def get_all_templates() -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, nom FROM documents_templates WHERE actif=1 ORDER BY nom",
            dictionary=True
        )

    @staticmethod
    def create(event_name: str, template_id: int = None, execution_mode: str = 'AUTO',
               priority: int = 0, actif: bool = True, description: str = None) -> int:
        event_name = event_name.strip()
        new_id = QueryExecutor.execute_write(
            "INSERT INTO document_event_rules "
            "(event_name, template_id, execution_mode, priority, actif, description) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (event_name, template_id, execution_mode, priority, int(actif), description)
        )
        log_hist("CREATION_DOC_EVENT_RULE", f"Règle événement créée : {event_name}")
        return new_id

    @staticmethod
    def update(rule_id: int, event_name: str, template_id: int = None,
               execution_mode: str = 'AUTO', priority: int = 0,
               actif: bool = True, description: str = None) -> None:
        event_name = event_name.strip()
        QueryExecutor.execute_write(
            "UPDATE document_event_rules SET event_name=%s, template_id=%s, "
            "execution_mode=%s, priority=%s, actif=%s, description=%s WHERE id=%s",
            (event_name, template_id, execution_mode, priority, int(actif), description, rule_id)
        )
        log_hist("MODIFICATION_DOC_EVENT_RULE", f"Règle événement #{rule_id} modifiée : {event_name}")

    @staticmethod
    def delete(rule_id: int) -> tuple:
        QueryExecutor.execute_write("DELETE FROM document_event_rules WHERE id=%s", (rule_id,))
        log_hist("SUPPRESSION_DOC_EVENT_RULE", f"Règle événement #{rule_id} supprimée")
        return True, "Règle supprimée."


# ─────────────────────────────────────────
# Demandes d'absence (admin)
# ─────────────────────────────────────────

class DemandeAbsenceAdminService:

    @staticmethod
    def get_all() -> list:
        return QueryExecutor.fetch_all(
            "SELECT da.*, p.nom, p.prenom, ta.libelle as type_libelle "
            "FROM demande_absence da "
            "JOIN personnel p ON p.id = da.personnel_id "
            "JOIN type_absence ta ON ta.id = da.type_absence_id "
            "ORDER BY da.date_creation DESC",
            dictionary=True
        )

    @staticmethod
    def update_statut(demande_id: int, statut: str, commentaire: str = None) -> None:
        QueryExecutor.execute_write(
            "UPDATE demande_absence SET statut=%s, commentaire_validation=%s, "
            "date_validation=NOW() WHERE id=%s",
            (statut, commentaire, demande_id)
        )
        log_hist("MODIF_STATUT_DEMANDE_ABSENCE", f"Demande absence #{demande_id} → {statut}")

    @staticmethod
    def delete(demande_id: int) -> tuple:
        QueryExecutor.execute_write("DELETE FROM demande_absence WHERE id=%s", (demande_id,))
        log_hist("SUPPRESSION_DEMANDE_ABSENCE", f"Demande absence #{demande_id} supprimée")
        return True, "Demande d'absence supprimée."


# ─────────────────────────────────────────
# Polyvalence (admin corrections)
# ─────────────────────────────────────────

class PolyvalenceAdminService:

    @staticmethod
    def get_all_recent(limit: int = 200) -> list:
        return QueryExecutor.fetch_all(
            "SELECT pv.id, p.nom, p.prenom, pos.poste_code, pv.niveau, "
            "pv.date_evaluation, pv.prochaine_evaluation "
            "FROM polyvalence pv "
            "JOIN personnel p ON p.id = pv.personnel_id "
            "JOIN postes pos ON pos.id = pv.poste_id "
            "ORDER BY p.nom, pos.poste_code "
            f"LIMIT {int(limit)}",
            dictionary=True
        )

    @staticmethod
    def update(polyvalence_id: int, niveau: int,
               date_evaluation: str, prochaine_evaluation: str) -> None:
        QueryExecutor.execute_write(
            "UPDATE polyvalence SET niveau=%s, date_evaluation=%s, "
            "prochaine_evaluation=%s WHERE id=%s",
            (niveau, date_evaluation, prochaine_evaluation, polyvalence_id)
        )
        log_hist("ADMIN_MODIF_POLYVALENCE", f"Polyvalence #{polyvalence_id} modifiée (admin)")

    @staticmethod
    def delete(polyvalence_id: int) -> tuple:
        QueryExecutor.execute_write("DELETE FROM polyvalence WHERE id=%s", (polyvalence_id,))
        log_hist("ADMIN_SUPPRESSION_POLYVALENCE", f"Polyvalence #{polyvalence_id} supprimée (admin)")
        return True, "Entrée de polyvalence supprimée."


# ─────────────────────────────────────────
# Historique (lecture seule)
# ─────────────────────────────────────────

class HistoriqueAdminService:

    @staticmethod
    def get_recent(limit: int = 100) -> list:
        return QueryExecutor.fetch_all(
            "SELECT id, date_time, action, table_name, utilisateur, description "
            "FROM historique ORDER BY date_time DESC "
            f"LIMIT {int(limit)}",
            dictionary=True
        )


# ─────────────────────────────────────────
# Logs de connexion (lecture seule)
# ─────────────────────────────────────────

class LogsConnexionService:

    @staticmethod
    def get_recent(limit: int = 50) -> list:
        return QueryExecutor.fetch_all(
            "SELECT lc.id, u.username, lc.date_connexion, lc.date_deconnexion, lc.ip_address "
            "FROM logs_connexion lc "
            "JOIN utilisateurs u ON u.id = lc.utilisateur_id "
            "ORDER BY lc.date_connexion DESC "
            f"LIMIT {int(limit)}",
            dictionary=True
        )
