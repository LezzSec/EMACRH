# -*- coding: utf-8 -*-
import datetime as dt
import os

from PyQt5.QtWidgets import QMessageBox, QDialog
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtGui import QDesktopServices

from infrastructure.logging.logging_config import get_logger, set_log_context, clear_log_context, get_logs_dir
from gui.components.emac_ui_kit import show_error_message

logger = get_logger(__name__)


class SessionMixin:
    """Gestion de la session, du timeout, de l'authentification et des exports."""

    def _start_timeout_monitoring(self):
        if self._timeout_manager:
            self._timeout_manager.start()
            logger.info("Surveillance timeout de session démarrée")

    def _force_logout_timeout(self):
        logger.warning("Déconnexion automatique: timeout de session")
        if self._timeout_manager:
            self._timeout_manager.stop()

        from gui.main_qt._shared import _lazy_auth
        auth = _lazy_auth()
        auth.logout_user()
        clear_log_context()
        self.close()

        QMessageBox.warning(
            None,
            "Session expirée",
            "Votre session a expiré en raison d'inactivité.\n"
            "Veuillez vous reconnecter pour continuer."
        )

        from gui.screens.admin.login_dialog import LoginDialog
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QDialog.Accepted:
            try:
                user = auth.get_current_user()
                if user:
                    set_log_context(user_id=user.get('username') or user.get('nom'), screen='MainWindow')
            except Exception:
                pass
            from gui.main_qt.main_window import MainWindow
            new_window = MainWindow()
            new_window.show()

    def logout(self):
        box = QMessageBox(self)
        box.setWindowTitle("Déconnexion")
        box.setText("Voulez-vous vraiment vous déconnecter ?")
        box.setIcon(QMessageBox.Question)
        btn_oui = box.addButton("Oui", QMessageBox.YesRole)
        box.addButton("Non", QMessageBox.NoRole)
        box.setDefaultButton(btn_oui)
        box.exec_()
        if box.clickedButton() is not btn_oui:
            return

        if self._timeout_manager:
            self._timeout_manager.stop()

        from gui.main_qt._shared import _lazy_auth
        auth = _lazy_auth()
        auth.logout_user()
        clear_log_context()
        self.close()

        from gui.screens.admin.login_dialog import LoginDialog
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QDialog.Accepted:
            try:
                user = auth.get_current_user()
                if user:
                    set_log_context(user_id=user.get('username') or user.get('nom'), screen='MainWindow')
            except Exception:
                pass
            from gui.main_qt.main_window import MainWindow
            new_window = MainWindow()
            new_window.show()

    def show_user_management(self):
        from gui.main_qt._shared import _lazy_auth
        auth = _lazy_auth()
        if not auth.is_admin():
            QMessageBox.warning(self, "Accès refusé", "Seuls les administrateurs peuvent gérer les utilisateurs.")
            return
        from gui.screens.admin.user_management import UserManagementDialog
        UserManagementDialog(self).exec_()

    def show_admin_data_panel(self):
        from gui.main_qt._shared import _lazy_auth
        auth = _lazy_auth()
        if not auth.is_admin():
            QMessageBox.warning(self, "Accès refusé", "Seuls les administrateurs peuvent accéder à la configuration.")
            return
        from gui.screens.admin.admin_data_panel import AdminDataPanelDialog
        dlg = AdminDataPanelDialog(self)
        dlg.modules_changed.connect(self._on_modules_changed)
        dlg.exec_()

    def _on_modules_changed(self):
        self.load_user_and_permissions_async()

    def closeEvent(self, event):
        if self._timeout_manager:
            self._timeout_manager.stop()
        event.accept()

    def export_logs_today(self):
        from infrastructure.logging.log_exporter import export_day
        if not export_day:
            QMessageBox.warning(self, "Non disponible", "Module d'export non chargé.")
            return
        try:
            paths = export_day(dt.date.today(), base_dir="logs", make_zip=False)
            dossier = os.path.dirname(paths["csv"])
            QMessageBox.information(self, "Export", f"Export terminé\n\nCSV : {paths['csv']}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(dossier))
        except Exception as e:
            logger.exception(f"Erreur export: {e}")
            show_error_message(self, "Erreur", "Export impossible", e)

    # --- Document trigger service ---

    def _init_document_trigger_service(self):
        try:
            from application.document_trigger_service import DocumentTriggerService
            from application.event_bus import EventBus

            self._doc_trigger = DocumentTriggerService()

            self._pending_doc_timer = QTimer(self)
            self._pending_doc_timer.setSingleShot(True)
            self._pending_doc_timer.timeout.connect(self._check_pending_documents)
            self._pending_doc_operateur: dict = {}

            EventBus.get_qt_signals().event_emitted.connect(self._on_event_for_documents)

            logger.info("DocumentTriggerService initialisé dans MainWindow")
        except Exception as e:
            logger.warning(f"DocumentTriggerService non initialisé: {e}")

    def _on_event_for_documents(self, event_name: str, event_data: dict):
        if not event_name.startswith(('personnel.', 'contrat.', 'polyvalence.')):
            return
        operateur_id = event_data.get('operateur_id')
        if not operateur_id:
            return
        self._pending_doc_operateur = {
            'id': operateur_id,
            'nom': event_data.get('nom', ''),
            'prenom': event_data.get('prenom', ''),
        }
        self._pending_doc_timer.start(300)

    def _check_pending_documents(self):
        info = getattr(self, '_pending_doc_operateur', {})
        operateur_id = info.get('id')
        if not operateur_id:
            return
        try:
            from application.document_trigger_service import DocumentTriggerService
            if DocumentTriggerService.has_pending_documents(operateur_id):
                from gui.screens.documents.document_proposal_dialog import DocumentProposalDialog
                dialog = DocumentProposalDialog(
                    operateur_id=operateur_id,
                    operateur_nom=info.get('nom', ''),
                    operateur_prenom=info.get('prenom', ''),
                    parent=self
                )
                dialog.exec_()
        except Exception as e:
            logger.warning(f"Erreur vérification documents en attente: {e}")
