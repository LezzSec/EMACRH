# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QScrollArea, QComboBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox, QToolButton,
)
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen

from infrastructure.logging.logging_config import get_logger
from gui.components.emac_ui_kit import show_error_message
from gui.workers.db_worker import DbWorker, DbThreadPool
from gui.workers.session_timeout import SessionTimeoutManager
from gui.main_qt._shared import get_theme_components
from gui.main_qt.drawer import DrawerMixin
from gui.main_qt.navigation import NavigationMixin
from gui.main_qt.dashboard_loaders import DashboardMixin
from gui.main_qt.notifications import NotificationsMixin
from gui.main_qt.session import SessionMixin

logger = get_logger(__name__)


class MainWindow(
    DrawerMixin, NavigationMixin, DashboardMixin, NotificationsMixin, SessionMixin,
    QMainWindow,
):
    DRAWER_WIDTH = 280

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion du Personnel")
        self.setGeometry(80, 80, 1180, 720)

        self.drawer = None
        self.is_drawer_open = False
        self.installEventFilter(self)
        self._last_notification_summary = None
        self._postes_cache = None
        self._postes_cache_time = None

        self._timeout_manager = None
        if SessionTimeoutManager is not None:
            self._timeout_manager = SessionTimeoutManager(self)
            self._timeout_manager.timeout_logout.connect(self._force_logout_timeout)
            QTimer.singleShot(1000, self._start_timeout_monitoring)

        theme = get_theme_components()
        EmacStatusCard = theme['EmacStatusCard']
        EmacButton = theme['EmacButton']
        EmacCard = theme['EmacCard']
        HamburgerButton = theme['HamburgerButton']

        rootw = QWidget()
        self.setCentralWidget(rootw)
        root = QGridLayout(rootw)
        root.setContentsMargins(18, 18, 18, 18)
        root.setHorizontalSpacing(18)
        root.setVerticalSpacing(18)
        rootw.setLayout(root)

        left = QVBoxLayout()
        left.setSpacing(18)

        self.retard_card = EmacStatusCard("Retard Évaluations", variant='danger')
        self.retard_filter = QComboBox()
        self.retard_filter.addItem("Tous les postes", "")
        self.retard_filter.currentIndexChanged.connect(self.load_evaluations_async)
        self.retard_scroll, self.retard_list = self.create_scrollable_list()
        self.retard_card.body.addWidget(self.retard_filter)
        self.retard_card.body.addWidget(self.retard_scroll)

        btn_voir_retards = EmacButton("Voir tout", variant='ghost')
        btn_voir_retards.clicked.connect(lambda: self.ouvrir_gestion_evaluations("En retard"))
        self.retard_card.body.addWidget(btn_voir_retards)
        self.retard_card.setVisible(False)
        left.addWidget(self.retard_card)

        self.next_card = EmacStatusCard("Prochaines Évaluations", variant='success', subtitle="À planifier (30j)")
        self.next_eval_filter = QComboBox()
        self.next_eval_filter.addItem("Tous les postes", "")
        self.next_eval_filter.currentIndexChanged.connect(self.load_evaluations_async)
        self.next_eval_scroll, self.next_eval_list = self.create_scrollable_list()
        self.next_card.body.addWidget(self.next_eval_filter)
        self.next_card.body.addWidget(self.next_eval_scroll)

        btn_voir_prochaines = EmacButton("Voir tout", variant='ghost')
        btn_voir_prochaines.clicked.connect(lambda: self.ouvrir_gestion_evaluations("À planifier (30j)"))
        self.next_card.body.addWidget(btn_voir_prochaines)
        self.next_card.setVisible(False)
        left.addWidget(self.next_card)

        self.alertes_rh_card = EmacStatusCard("Alertes Documents", variant='warning', subtitle="Expirés / Expirent dans 30j")
        self.alertes_rh_filter = QComboBox()
        self.alertes_rh_filter.addItem("Tous les types", "")
        self.alertes_rh_filter.addItem("Contrats", "CONTRAT")
        self.alertes_rh_filter.addItem("Sans contrat", "SANS_CONTRAT")
        self.alertes_rh_filter.addItem("Mutuelles", "MUTUELLE")
        self.alertes_rh_filter.addItem("Sans mutuelle", "SANS_MUTUELLE")
        self.alertes_rh_filter.addItem("Visites médicales", "VISITE_MEDICALE")
        self.alertes_rh_filter.addItem("Sans visite médicale", "SANS_VISITE")
        self.alertes_rh_filter.addItem("Entretiens", "ENTRETIEN")
        self.alertes_rh_filter.addItem("Sans entretien", "SANS_ENTRETIEN")
        self.alertes_rh_filter.addItem("RQTH", "RQTH")
        self.alertes_rh_filter.currentIndexChanged.connect(self.load_alertes_rh_async)
        self.alertes_rh_scroll, self.alertes_rh_list = self.create_scrollable_list()
        self.alertes_rh_list.itemDoubleClicked.connect(self._on_alerte_rh_double_click)
        self.alertes_rh_card.body.addWidget(self.alertes_rh_filter)
        self.alertes_rh_card.body.addWidget(self.alertes_rh_scroll)

        btn_voir_alertes = EmacButton("Gestion RH", variant='ghost')
        btn_voir_alertes.clicked.connect(self.show_contract_management)
        self.alertes_rh_card.body.addWidget(btn_voir_alertes)
        self.alertes_rh_card.setVisible(False)
        left.addWidget(self.alertes_rh_card)

        root.addLayout(left, 0, 0, 3, 1)

        right = QVBoxLayout()
        right.setSpacing(18)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(12)

        logo_lbl = QLabel()
        logo_lbl.setFixedSize(38, 38)
        logo_px = QPixmap(38, 38)
        logo_px.fill(Qt.transparent)
        p = QPainter(logo_px)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(Qt.NoBrush)
        pen = QPen(QColor('#2563eb'))
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawEllipse(7, 7, 8, 8)
        p.drawArc(3, 17, 16, 10, 0, 180 * 16)
        p.drawEllipse(18, 9, 10, 10)
        p.drawArc(14, 20, 17, 11, 0, 180 * 16)
        p.end()
        logo_lbl.setPixmap(logo_px)
        header_layout.addWidget(logo_lbl, 0, Qt.AlignVCenter)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        h1 = QLabel("Gestion du Personnel")
        h1.setProperty('class', 'h1')
        title_layout.addWidget(h1)
        self.user_info = QLabel("...")
        self.user_info.setStyleSheet("color: #666; font-size: 12px;")
        title_layout.addWidget(self.user_info)
        header_layout.addLayout(title_layout, 1)

        _notif_container = QWidget()
        _notif_container.setFixedSize(52, 44)

        self.menu_btn = HamburgerButton(_notif_container, variant="default")
        self.menu_btn.setGeometry(0, 4, 40, 40)
        self.menu_btn.setToolTip("Menu")
        self.menu_btn.clicked.connect(self.toggle_drawer)

        self._notif_badge = QLabel("", _notif_container)
        self._notif_badge.setAlignment(Qt.AlignCenter)
        self._notif_badge.setAttribute(Qt.WA_StyledBackground, True)
        self._notif_badge.setStyleSheet("""
            background-color: #ef4444;
            color: white;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
            padding: 1px 5px;
            min-width: 20px;
            min-height: 20px;
        """)
        self._notif_badge.setGeometry(26, 0, 26, 20)
        self._notif_badge.setToolTip("Alertes en attente")
        self._notif_badge.hide()
        self._notif_badge.raise_()

        header_layout.addWidget(_notif_container, 0, Qt.AlignRight | Qt.AlignVCenter)

        self._startup_alert_shown = False
        right.addWidget(header_widget)

        self.actions_wrap = EmacCard()
        title_lbl = QLabel("Actions rapides")
        title_lbl.setProperty('class', 'h2')
        self.actions_wrap.body.addWidget(title_lbl)

        self.rows = QVBoxLayout()
        self.rows.setSpacing(8)

        r1 = QHBoxLayout()
        b1 = EmacButton("Liste du Personnel", 'primary')
        b1.clicked.connect(self.show_liste_personnel)
        r1.addWidget(b1)
        self.rows.addLayout(r1)

        self.actions_wrap.body.addLayout(self.rows)
        right.addWidget(self.actions_wrap)

        root.addLayout(right, 0, 1)

        quit_btn = QToolButton()
        quit_btn.setText("⏻")
        quit_btn.setToolTip("Quitter l'application")
        quit_btn.clicked.connect(self.close)
        quit_btn.setFixedSize(28, 28)
        quit_btn.setStyleSheet("""
            QToolButton {
                color: #9ca3af;
                font-size: 16px;
                background: transparent;
                border: none;
                border-radius: 6px;
            }
            QToolButton:hover {
                color: #ef4444;
                background: #fef2f2;
            }
        """)
        root.addWidget(quit_btn, 2, 1, Qt.AlignBottom | Qt.AlignRight)

        QTimer.singleShot(0, self.bootstrap_async)

    def bootstrap_async(self):
        self.load_user_and_permissions_async()
        self.populate_filters_async()
        self._init_document_trigger_service()
        QTimer.singleShot(200, self._check_password_upgrade_required)

    def _check_password_upgrade_required(self):
        """Force le changement de MDP si le flag password_needs_upgrade est levé (politique 12+)."""
        from domain.services.admin.auth_service import UserSession, get_password_requirements, logout_user

        user = UserSession.get_user()
        if not user or not user.get('password_needs_upgrade'):
            return

        QMessageBox.warning(
            self,
            "Mise à jour du mot de passe requise",
            "La politique de sécurité a évolué. Votre mot de passe actuel "
            "ne respecte plus les nouvelles exigences.\n\n"
            + get_password_requirements()
            + "\n\nVeuillez choisir un nouveau mot de passe pour continuer."
        )

        try:
            from gui.screens.admin.user_management import ChangePasswordDialog
            dialog = ChangePasswordDialog(user_id=user['id'], parent=self)
        except (ImportError, TypeError):
            dialog = self._build_simple_change_password_dialog(user['id'])

        if dialog is None or dialog.exec_() != dialog.Accepted:
            logout_user()
            self.close()
            return

        user['password_needs_upgrade'] = False

    def _build_simple_change_password_dialog(self, user_id: int):
        """Dialogue minimal de changement de MDP si ChangePasswordDialog n'est pas disponible."""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox
        from domain.services.admin.auth_service import change_password

        dlg = QDialog(self)
        dlg.setWindowTitle("Nouveau mot de passe")
        dlg.setMinimumWidth(480)
        layout = QFormLayout(dlg)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        req_lbl = QLabel("12 caractères min · 2 types de caractères · pas de mot de passe courant")
        req_lbl.setStyleSheet("font-size: 11px; color: #6b7280; padding: 4px 0;")
        req_lbl.setWordWrap(True)
        layout.addRow("", req_lbl)

        pwd_row = QWidget()
        pwd_row_layout = QHBoxLayout(pwd_row)
        pwd_row_layout.setContentsMargins(0, 0, 0, 0)
        pwd_row_layout.setSpacing(4)
        pwd_input = QLineEdit()
        pwd_input.setEchoMode(QLineEdit.Password)
        pwd_input.setMinimumHeight(36)
        pwd_row_layout.addWidget(pwd_input)
        toggle1 = QPushButton("Voir")
        toggle1.setFixedSize(52, 36)
        toggle1.setCheckable(True)
        toggle1.setStyleSheet("font-size: 12px; border-radius: 8px;")
        toggle1.toggled.connect(lambda on: pwd_input.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
        toggle1.toggled.connect(lambda on: toggle1.setText("Cacher" if on else "Voir"))
        pwd_row_layout.addWidget(toggle1)
        layout.addRow("Nouveau mot de passe :", pwd_row)

        pwd2_row = QWidget()
        pwd2_row_layout = QHBoxLayout(pwd2_row)
        pwd2_row_layout.setContentsMargins(0, 0, 0, 0)
        pwd2_row_layout.setSpacing(4)
        pwd2_input = QLineEdit()
        pwd2_input.setEchoMode(QLineEdit.Password)
        pwd2_input.setMinimumHeight(36)
        pwd2_row_layout.addWidget(pwd2_input)
        toggle2 = QPushButton("Voir")
        toggle2.setFixedSize(52, 36)
        toggle2.setCheckable(True)
        toggle2.setStyleSheet("font-size: 12px; border-radius: 8px;")
        toggle2.toggled.connect(lambda on: pwd2_input.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
        toggle2.toggled.connect(lambda on: toggle2.setText("Cacher" if on else "Voir"))
        pwd2_row_layout.addWidget(toggle2)
        layout.addRow("Confirmation :", pwd2_row)

        match_lbl = QLabel("")
        match_lbl.setStyleSheet("font-size: 11px;")

        def _update_match():
            p1, p2 = pwd_input.text(), pwd2_input.text()
            if not p2:
                match_lbl.setText("")
                return
            if p1 == p2:
                match_lbl.setText("Les mots de passe correspondent")
                match_lbl.setStyleSheet("font-size: 11px; color: #059669;")
            else:
                match_lbl.setText("Ne correspondent pas")
                match_lbl.setStyleSheet("font-size: 11px; color: #dc2626;")

        pwd_input.textChanged.connect(_update_match)
        pwd2_input.textChanged.connect(_update_match)
        layout.addRow("", match_lbl)

        err_lbl = QLabel("")
        err_lbl.setStyleSheet("color: #dc2626; font-size: 12px; padding: 4px 0;")
        err_lbl.setWordWrap(True)
        layout.addRow(err_lbl)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)

        def on_ok():
            p1, p2 = pwd_input.text(), pwd2_input.text()
            if p1 != p2:
                err_lbl.setText("Les mots de passe ne correspondent pas.")
                return
            ok, msg = change_password(user_id, p1)
            if ok:
                dlg.accept()
            else:
                err_lbl.setText(msg or "Erreur lors du changement.")

        buttons.accepted.connect(on_ok)
        buttons.rejected.connect(dlg.reject)
        return dlg

    def eventFilter(self, source, event):
        if self.drawer is not None and self.is_drawer_open and event.type() == QEvent.MouseButtonPress:
            if not self.drawer.geometry().contains(self.mapFromGlobal(event.globalPos())):
                if source is not self.menu_btn:
                    self.toggle_drawer()
                    return True
        return super().eventFilter(source, event)

    def _on_bg_error(self, tb):
        logger.error(f"Erreur background:\n{tb}")
        try:
            QMessageBox.warning(
                self,
                "Erreur de chargement",
                "Une erreur s'est produite lors du chargement des données.\n\n"
                "L'application peut continuer à fonctionner mais certaines données\n"
                "peuvent être manquantes.\n\n"
                "Vérifiez les logs pour plus de détails.",
                QMessageBox.Ok
            )
        except Exception:
            pass
