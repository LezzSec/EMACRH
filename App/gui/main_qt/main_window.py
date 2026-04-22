# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QScrollArea, QComboBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer, QEvent

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

        r_quit = QHBoxLayout()
        bq = EmacButton("Quitter", 'ghost')
        bq.clicked.connect(self.close)
        r_quit.addWidget(bq)
        self.rows.addLayout(r_quit)

        self.actions_wrap.body.addLayout(self.rows)
        right.addWidget(self.actions_wrap)

        root.addLayout(right, 0, 1)

        QTimer.singleShot(0, self.bootstrap_async)

    def bootstrap_async(self):
        self.load_user_and_permissions_async()
        self.populate_filters_async()
        self._init_document_trigger_service()

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
