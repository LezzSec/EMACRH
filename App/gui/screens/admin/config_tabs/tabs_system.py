# -*- coding: utf-8 -*-
"""
Onglets de configuration système : Rôles, Historique (lecture seule), Logs connexion (lecture seule).
"""

from PyQt5.QtWidgets import (
    QDialog, QLineEdit, QTextEdit, QMessageBox
)

from infrastructure.logging.logging_config import get_logger
from .base import _ConfigTab, _SimpleFormDialog, _ReadOnlyTab

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════════
#  9. RÔLES
# ════════════════════════════════════════════════════════════════

class _RoleForm(_SimpleFormDialog):
    def __init__(self, data: dict | None = None, parent=None):
        title = "Modifier le rôle" if data else "Nouveau rôle"
        super().__init__(title, parent)

        self.inp_nom = QLineEdit()
        self.inp_nom.setMaxLength(50)
        self.inp_nom.setPlaceholderText("Ex: Responsable RH")
        self.form.addRow("Nom *", self.inp_nom)

        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(80)
        self.form.addRow("Description", self.inp_desc)

        if data:
            self.inp_nom.setText(data.get('nom', ''))
            self.inp_desc.setPlainText(data.get('description') or '')

    def validate(self):
        return self._require_text(self.inp_nom, "Nom")

    def get_values(self) -> dict:
        return {
            'nom': self.inp_nom.text().strip(),
            'description': self.inp_desc.toPlainText().strip() or None
        }


class RolesTab(_ConfigTab):
    COLUMNS = [("ID", "id"), ("Nom", "nom"), ("Description", "description")]
    DESCRIPTION = "Rôles utilisateurs — définissent les droits d'accès dans l'application. Chaque utilisateur est assigné à un rôle."
    USAGE = "Gestion des utilisateurs, système de permissions (features), contrôle d'accès"

    def fetch_data(self):
        from domain.services.admin.config_service import RolesConfigService
        return RolesConfigService.get_all()

    def show_form(self, data):
        from domain.services.admin.config_service import RolesConfigService
        dlg = _RoleForm(data, self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            try:
                if data:
                    RolesConfigService.update(data['id'], **vals)
                else:
                    RolesConfigService.create(**vals)
                self._load_async()
            except Exception as e:
                logger.exception(f"Erreur rôle: {e}")
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue. Consultez les logs pour plus de détails.")

    def delete_record(self, record_id):
        from domain.services.admin.config_service import RolesConfigService
        return RolesConfigService.delete(record_id)


# ════════════════════════════════════════════════════════════════
#  14. HISTORIQUE (lecture seule)
# ════════════════════════════════════════════════════════════════

class HistoriqueAdminTab(_ReadOnlyTab):
    INFO_LABEL = "Affichage des 100 dernières entrées (lecture seule)"
    COLUMNS = [
        ("ID", "id"), ("Date/Heure", "date_time"), ("Action", "action"),
        ("Table", "table_name"), ("Utilisateur", "utilisateur"), ("Description", "description"),
    ]
    DATETIME_KEYS = {'date_time'}

    def fetch_data(self):
        from domain.services.admin.config_service import HistoriqueAdminService
        return HistoriqueAdminService.get_recent(100)


# ════════════════════════════════════════════════════════════════
#  15. LOGS DE CONNEXION (lecture seule)
# ════════════════════════════════════════════════════════════════

class LogsConnexionTab(_ReadOnlyTab):
    INFO_LABEL = "Affichage des 50 dernières connexions (lecture seule)"
    COLUMNS = [
        ("ID", "id"), ("Utilisateur", "username"), ("Connexion", "date_connexion"),
        ("Déconnexion", "date_deconnexion"), ("IP", "ip_address"),
    ]
    DATETIME_KEYS = {'date_connexion', 'date_deconnexion'}

    def fetch_data(self):
        from domain.services.admin.config_service import LogsConnexionService
        return LogsConnexionService.get_recent(50)
