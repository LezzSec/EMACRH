import sys, os, datetime as dt, time, traceback
from dataclasses import dataclass

# Configuration centralisée du logging (doit être en premier)
from core.utils.logging_config import setup_logging, get_logger, set_log_context, clear_log_context

# Déterminer le mode (production si variable d'environnement définie)
_production_mode = os.getenv('EMAC_ENV', '').lower() == 'production'
setup_logging(production_mode=_production_mode)

logger = get_logger(__name__)

# Ajouter le répertoire App au PYTHONPATH pour cx_Freeze
if getattr(sys, 'frozen', False):
    # En mode exécutable compilé
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, app_dir)
else:
    # En mode développement
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QListWidget, QScrollArea,
    QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QMessageBox, QFrame, QDialog
)
from PyQt5.QtCore import (
    Qt, QUrl, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QEvent,
    qInstallMessageHandler, QObject, pyqtSignal, QRunnable, QThreadPool
)
from PyQt5.QtGui import QDesktopServices

# ✅ Import optionnel
try:
    from core.services.log_exporter import export_day
except Exception:
    export_day = None

# ===========================
#  Workers (ThreadPool) - ✅ Utilisation du nouveau module db_worker
# ===========================

# Import du système de workers optimisé
try:
    from core.gui.db_worker import (
        DbWorker, DbThreadPool, run_in_background,
        show_loading_placeholder, show_error_placeholder
    )
    # Initialiser le pool avec la bonne configuration
    _thread_pool = DbThreadPool.get_pool()
except ImportError:
    # Fallback si le module n'existe pas encore
    class WorkerSignals(QObject):
        result = pyqtSignal(object)
        error = pyqtSignal(str)

    class DbWorker(QRunnable):
        """Exécute une fonction DB en background et renvoie le résultat."""
        def __init__(self, fn, *args, **kwargs):
            super().__init__()
            self.fn = fn
            self.args = args
            self.kwargs = kwargs
            self.signals = WorkerSignals()

        def run(self):
            try:
                res = self.fn(*self.args, **self.kwargs)
                self.signals.result.emit(res)
            except Exception:
                self.signals.error.emit(traceback.format_exc())

    _thread_pool = QThreadPool.globalInstance()
    # Limiter à 4 threads par défaut
    _thread_pool.setMaxThreadCount(4)


# Import de show_error_message
try:
    from core.gui.emac_ui_kit import show_error_message
except ImportError:
    show_error_message = None

# Import du gestionnaire de timeout de session
try:
    from core.gui.session_timeout import SessionTimeoutManager
except ImportError:
    SessionTimeoutManager = None
    logger.warning("SessionTimeoutManager non disponible")

# ===========================
#  Fonctions lazy (DB/Auth/Theme)
# ===========================

def _lazy_auth():
    from core.services import auth_service
    return auth_service

def _lazy_theme():
    from core.gui import ui_theme
    return ui_theme

# Cache pour éviter de réimporter à chaque appel
_theme_cache = None

def get_theme_components():
    """Retourne les composants du thème (EmacTheme, EmacButton, etc.)"""
    global _theme_cache
    if _theme_cache is None:
        theme_module = _lazy_theme()
        _theme_cache = {
            'EmacTheme': theme_module.EmacTheme,
            'EmacButton': theme_module.EmacButton,
            'EmacCard': theme_module.EmacCard,
            'EmacStatusCard': theme_module.EmacStatusCard,
            'HamburgerButton': theme_module.HamburgerButton,
        }
    return _theme_cache


# ===========================
#  Main Window
# ===========================

class MainWindow(QMainWindow):
    DRAWER_WIDTH = 280

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion du Personnel")
        self.setGeometry(80, 80, 1180, 720)

        # Drawer
        self.drawer = None
        self.is_drawer_open = False
        self.installEventFilter(self)

        # Cache postes
        self._postes_cache = None
        self._postes_cache_time = None

        # Session timeout manager (sécurité: déconnexion automatique après inactivité)
        self._timeout_manager = None
        if SessionTimeoutManager is not None:
            self._timeout_manager = SessionTimeoutManager(self)
            self._timeout_manager.timeout_logout.connect(self._force_logout_timeout)
            # Démarrer la surveillance après l'affichage de la fenêtre
            QTimer.singleShot(1000, self._start_timeout_monitoring)

        # ✅ Charger les composants du thème
        theme = get_theme_components()
        EmacStatusCard = theme['EmacStatusCard']
        EmacButton = theme['EmacButton']
        EmacCard = theme['EmacCard']
        HamburgerButton = theme['HamburgerButton']

        # UI
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

        btn_voir_retards = EmacButton("📋 Voir tout", variant='ghost')
        btn_voir_retards.clicked.connect(lambda: self.ouvrir_gestion_evaluations("En retard"))
        self.retard_card.body.addWidget(btn_voir_retards)

        # Masqué par défaut, affiché uniquement pour les utilisateurs Production
        self.retard_card.setVisible(False)
        left.addWidget(self.retard_card)

        # Carte Prochaines Évaluations (uniquement pour utilisateurs Production)
        self.next_card = EmacStatusCard("Prochaines Évaluations", variant='success', subtitle="À planifier (30j)")
        self.next_eval_filter = QComboBox()
        self.next_eval_filter.addItem("Tous les postes", "")
        self.next_eval_filter.currentIndexChanged.connect(self.load_evaluations_async)
        self.next_eval_scroll, self.next_eval_list = self.create_scrollable_list()
        self.next_card.body.addWidget(self.next_eval_filter)
        self.next_card.body.addWidget(self.next_eval_scroll)

        btn_voir_prochaines = EmacButton("📋 Voir tout", variant='ghost')
        btn_voir_prochaines.clicked.connect(lambda: self.ouvrir_gestion_evaluations("À planifier (30j)"))
        self.next_card.body.addWidget(btn_voir_prochaines)

        # Masqué par défaut, affiché uniquement pour les utilisateurs Production
        self.next_card.setVisible(False)
        left.addWidget(self.next_card)

        # Carte Alertes RH (uniquement pour utilisateurs RH)
        self.alertes_rh_card = EmacStatusCard("Alertes Contrats", variant='warning', subtitle="Expirent dans 30j")
        self.alertes_rh_filter = QComboBox()
        self.alertes_rh_filter.addItem("Tous les types", "")
        self.alertes_rh_filter.addItem("CDI", "CDI")
        self.alertes_rh_filter.addItem("CDD", "CDD")
        self.alertes_rh_filter.addItem("Intérim", "Intérim")
        self.alertes_rh_filter.addItem("Alternance", "Alternance")
        self.alertes_rh_filter.currentIndexChanged.connect(self.load_alertes_rh_async)
        self.alertes_rh_scroll, self.alertes_rh_list = self.create_scrollable_list()
        self.alertes_rh_card.body.addWidget(self.alertes_rh_filter)
        self.alertes_rh_card.body.addWidget(self.alertes_rh_scroll)

        btn_voir_alertes = EmacButton("📋 Gestion RH", variant='ghost')
        btn_voir_alertes.clicked.connect(self.show_contract_management)
        self.alertes_rh_card.body.addWidget(btn_voir_alertes)

        # Masqué par défaut, affiché uniquement pour les utilisateurs RH
        self.alertes_rh_card.setVisible(False)
        left.addWidget(self.alertes_rh_card)

        root.addLayout(left, 0, 0, 3, 1)  # 3 cartes maintenant

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

        # ✅ IMPORTANT: ne pas appeler get_current_user() ici (peut toucher DB/session)
        # On met un placeholder et on remplira après (async)
        self.user_info = QLabel("👤 ...")
        self.user_info.setStyleSheet("color: #666; font-size: 12px;")
        title_layout.addWidget(self.user_info)

        header_layout.addLayout(title_layout, 1)

        self.menu_btn = HamburgerButton(self, variant="default")
        self.menu_btn.setToolTip("Menu")
        self.menu_btn.clicked.connect(self.toggle_drawer)
        header_layout.addWidget(self.menu_btn, 0, Qt.AlignRight | Qt.AlignVCenter)

        right.addWidget(header_widget)

        self.actions_wrap = EmacCard()
        title = QLabel("Actions rapides")
        title.setProperty('class', 'h2')
        self.actions_wrap.body.addWidget(title)

        # ✅ IMPORTANT: ne pas appeler has_permission() ici (peut toucher DB)
        # On construit un layout minimal et on l’enrichit après (async).
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

        # ✅ Lancement ultra rapide : on affiche, puis on charge le reste en background
        QTimer.singleShot(0, self.bootstrap_async)

    # ---------------------------
    # Bootstrap async
    # ---------------------------

    def bootstrap_async(self):
        """Charge user + permissions + filtres sans bloquer l'UI."""
        self.load_user_and_permissions_async()
        self.populate_filters_async()
        # Note: load_evaluations_async() et load_alertes_rh_async() sont appelés
        # dans _apply_user_and_perms selon les permissions de l'utilisateur
        self._init_document_trigger_service()

    def load_user_and_permissions_async(self):
        w = DbWorker(self._fetch_user_and_perms)
        w.signals.result.connect(self._apply_user_and_perms)
        w.signals.error.connect(self._on_bg_error)
        DbThreadPool.start(w)

    def _fetch_user_and_perms(self, progress_callback=None):
        auth = _lazy_auth()
        current_user = auth.get_current_user()

        # ✅ Nouveau système de permissions par features
        from core.services.permission_manager import can
        perms = {
            "grilles_lecture": can('production.grilles.view'),
            "evaluations_lecture": can('production.evaluations.view'),
            "personnel_ecriture": can('rh.personnel.edit'),
            "personnel_lecture": can('rh.personnel.view'),
            "postes_ecriture": can('production.postes.edit'),
            "contrats_lecture": can('rh.contrats.view'),
            "contrats_ecriture": can('rh.contrats.edit'),
            "documentsrh_lecture": can('rh.documents.view'),
            "documentsrh_ecriture": can('rh.documents.edit'),  # Pour alertes RH
            "planning_lecture": can('planning.view'),
            "historique_lecture": can('admin.historique.view'),
            "is_admin": auth.is_admin(),
        }
        return {"user": current_user, "perms": perms}

    def _apply_user_and_perms(self, payload):
        user = payload.get("user")
        perms = payload.get("perms", {})

        # User label
        if user:
            user_text = f"👤 {user.get('prenom','')} {user.get('nom','')} - {user.get('role_nom','')}"
            self.user_info.setText(user_text)
        else:
            self.user_info.setText("👤 Non connecté")

        # Charger EmacButton
        theme = get_theme_components()
        EmacButton = theme['EmacButton']

        # Actions rapides : on ajoute les boutons conditionnels
        # (on évite de les créer au démarrage)
        if perms.get("grilles_lecture"):
            r2 = QHBoxLayout()
            b2 = EmacButton("Liste et Grilles", 'ghost')
            b2.clicked.connect(self.show_listes_grilles_dialog)
            r2.addWidget(b2)
            self.rows.insertLayout(1, r2)

        if perms.get("evaluations_lecture"):
            r3 = QHBoxLayout()
            b3 = EmacButton("Gestion des Évaluations", 'ghost')
            b3.clicked.connect(self.show_gestion_evaluations)
            r3.addWidget(b3)
            self.rows.insertLayout(2, r3)

        # Cartes Évaluations : afficher uniquement pour les utilisateurs Production
        has_production_access = perms.get("evaluations_lecture")
        self.retard_card.setVisible(has_production_access)
        self.next_card.setVisible(has_production_access)
        if has_production_access:
            self.load_evaluations_async()

        # Alertes Contrats : afficher uniquement pour les utilisateurs RH
        # Utilise rh.contrats.edit ou rh.documents.edit (permissions d'écriture RH uniquement)
        has_rh_access = perms.get("contrats_ecriture") or perms.get("documentsrh_ecriture")
        self.alertes_rh_card.setVisible(has_rh_access)
        if has_rh_access:
            self.load_alertes_rh_async()

        # Drawer : on le construit au premier clic, mais on garde les perms en mémoire
        self._perms_cache = perms

        # Forcer la recréation du drawer si les permissions ont changé
        if self.drawer is not None:
            self.drawer.deleteLater()
            self.drawer = None

    # ---------------------------
    # Document Trigger Service
    # ---------------------------

    def _init_document_trigger_service(self):
        """Initialise le service de déclenchement de documents et connecte les signaux."""
        try:
            from core.services.document_trigger_service import DocumentTriggerService
            from core.services.event_bus import EventBus

            # Initialiser le service (singleton)
            self._doc_trigger = DocumentTriggerService()

            # Timer debounce : évite d'afficher plusieurs dialogs quand plusieurs
            # événements sont émis en rafale pour le même opérateur (ex : niveau_changed
            # + niveau_1_reached émis consécutivement lors d'un changement de niveau).
            self._pending_doc_timer = QTimer(self)
            self._pending_doc_timer.setSingleShot(True)
            self._pending_doc_timer.timeout.connect(self._check_pending_documents)
            self._pending_doc_operateur: dict = {}

            # Connecter le signal Qt pour afficher les dialogs de proposition
            EventBus.get_qt_signals().event_emitted.connect(self._on_event_for_documents)

            logger.info("DocumentTriggerService initialisé dans MainWindow")
        except Exception as e:
            logger.warning(f"DocumentTriggerService non initialisé: {e}")

    def _on_event_for_documents(self, event_name: str, event_data: dict):
        """
        Appelé lors de chaque événement pour vérifier s'il y a des documents à proposer.
        Ce handler est connecté au signal Qt, donc exécuté dans le thread principal.
        """
        # Ne traiter que les événements qui peuvent générer des documents
        if not event_name.startswith(('personnel.', 'contrat.', 'polyvalence.')):
            return

        operateur_id = event_data.get('operateur_id')
        if not operateur_id:
            return

        # Mémoriser le dernier opérateur concerné et relancer le timer debounce.
        # Si plusieurs événements arrivent en rafale pour le même opérateur,
        # le timer est réinitialisé à chaque fois → un seul dialog au final.
        self._pending_doc_operateur = {
            'id': operateur_id,
            'nom': event_data.get('nom', ''),
            'prenom': event_data.get('prenom', ''),
        }
        self._pending_doc_timer.start(300)

    def _check_pending_documents(self):
        """Affiche le dialog de proposition si des documents sont en attente."""
        info = getattr(self, '_pending_doc_operateur', {})
        operateur_id = info.get('id')
        nom = info.get('nom', '')
        prenom = info.get('prenom', '')
        if not operateur_id:
            return
        try:
            from core.services.document_trigger_service import DocumentTriggerService

            if DocumentTriggerService.has_pending_documents(operateur_id):
                from core.gui.document_proposal_dialog import DocumentProposalDialog
                dialog = DocumentProposalDialog(
                    operateur_id=operateur_id,
                    operateur_nom=nom,
                    operateur_prenom=prenom,
                    parent=self
                )
                dialog.exec_()
        except Exception as e:
            logger.warning(f"Erreur vérification documents en attente: {e}")

    # ---------------------------
    # Event filter
    # ---------------------------

    def eventFilter(self, source, event):
        if self.drawer is not None and self.is_drawer_open and event.type() == QEvent.MouseButtonPress:
            if not self.drawer.geometry().contains(self.mapFromGlobal(event.globalPos())):
                if source is not self.menu_btn:
                    self.toggle_drawer()
                    return True
        return super().eventFilter(source, event)

    # ---------------------------
    # Drawer
    # ---------------------------

    def create_drawer(self):
        if self.drawer is not None:
            return

        # Charger les composants du thème
        theme = get_theme_components()
        EmacTheme = theme['EmacTheme']
        EmacButton = theme['EmacButton']

        self.drawer = QFrame(self)
        self.drawer.setObjectName("card")
        self.drawer.setFixedSize(self.DRAWER_WIDTH, self.height())

        ThemeCls = EmacTheme
        border_color = ThemeCls.BDR
        bg_card = ThemeCls.BG_CARD

        self.drawer.setStyleSheet(f"""
            QFrame#card {{
                background: {bg_card};
                border-left: 1px solid {border_color};
                border-top: 1px solid {border_color};
                border-bottom: 1px solid {border_color};
                border-right: 0px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 14px;
                border-bottom-right-radius: 14px;
            }}
        """)

        self.drawer.move(self.width(), 0)
        self.drawer.hide()

        drawer_layout = QVBoxLayout(self.drawer)
        drawer_layout.setContentsMargins(16, 16, 16, 16)
        drawer_layout.setAlignment(Qt.AlignTop)

        title = QLabel("Menu")
        title.setProperty('class', 'h2')
        drawer_layout.addWidget(title)
        drawer_layout.addSpacing(15)

        # ✅ Permissions depuis cache si dispo, sinon fallback lazy (sans bloquer)
        perms = getattr(self, "_perms_cache", None)
        if perms is None:
            # fallback minimal (si jamais)
            perms = {"is_admin": False}

        def add_btn(text, fn, variant='ghost'):
            btn = EmacButton(text, variant=variant)
            btn.setFixedHeight(44)
            btn.clicked.connect(fn)
            if fn not in (self.close, self.export_logs_today):
                btn.clicked.connect(self.toggle_drawer)
            drawer_layout.addWidget(btn)

        if perms.get("personnel_ecriture"):
            add_btn("Ajouter du personnel", self.show_manage_operator)
        if perms.get("postes_ecriture"):
            add_btn("Création/Suppression de poste", self.show_poste_form)
        if perms.get("contrats_ecriture") or perms.get("contrats_lecture") or perms.get("documentsrh_lecture"):
            add_btn("Gestion RH", self.show_contract_management)
        if perms.get("contrats_ecriture") or perms.get("documentsrh_ecriture"):
            add_btn("Alertes RH", self.show_alertes_rh)
        if perms.get("planning_lecture"):
            add_btn("Planning", self.show_regularisation)
        if perms.get("documentsrh_lecture"):
            add_btn("Documents", self.show_gestion_templates)
        if perms.get("is_admin"):
            add_btn("Historique", self.show_historique)
            drawer_layout.addSpacing(10)
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("color: #ddd;")
            drawer_layout.addWidget(sep)
            drawer_layout.addSpacing(10)
            add_btn("Gestion des Utilisateurs", self.show_user_management)

        drawer_layout.addStretch(1)

        drawer_layout.addSpacing(10)
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #ddd;")
        drawer_layout.addWidget(sep2)
        drawer_layout.addSpacing(10)
        add_btn("🚪 Déconnexion", self.logout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.drawer is not None:
            self.drawer.setFixedHeight(self.height())
            current_x = self.width() - self.DRAWER_WIDTH if self.is_drawer_open else self.width()
            self.drawer.move(current_x, 0)

    def toggle_drawer(self):
        if self.drawer is None:
            self.create_drawer()
        if self.drawer is None:
            logger.error("Impossible de créer le drawer")
            return

        self.is_drawer_open = not self.is_drawer_open
        end_x = self.width() - self.DRAWER_WIDTH if self.is_drawer_open else self.width()

        if hasattr(self, 'animation') and self.animation is not None:
            self.animation.stop()
            try:
                self.animation.finished.disconnect()
            except Exception:
                pass

        self.animation = QPropertyAnimation(self.drawer, b"pos")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setStartValue(self.drawer.pos())
        self.animation.setEndValue(QPoint(end_x, 0))

        if self.is_drawer_open:
            self.drawer.show()
            self.drawer.raise_()
        else:
            self.animation.finished.connect(self.drawer.hide)

        self.animation.start()

    # ---------------------------
    # UI helpers
    # ---------------------------

    def create_scrollable_list(self):
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        lw = QListWidget()
        sc.setWidget(lw)
        return sc, lw

    # ---------------------------
    # Dialogs (lazy imports)
    # ---------------------------

    def show_liste_personnel(self):
        from core.gui.gestion_personnel import GestionPersonnelDialog
        dialog = GestionPersonnelDialog(self)
        dialog.data_changed.connect(self.load_evaluations_async)
        dialog.exec_()

    def show_manage_operator(self):
        from core.gui.manage_operateur import ManageOperatorsDialog
        dialog = ManageOperatorsDialog()
        dialog.data_changed.connect(lambda _: self.load_evaluations_async())
        dialog.exec_()

    def show_gestion_evaluations(self):
        """Ouvre le dialogue de gestion des évaluations"""
        try:
            from core.gui.gestion_evaluation import GestionEvaluationDialog
            dialog = GestionEvaluationDialog()
            dialog.exec_()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            import traceback
            error_msg = f"Erreur lors de l'ouverture de la gestion des évaluations :\n\n{str(e)}\n\n"
            error_msg += f"Type: {type(e).__name__}\n\n"
            error_msg += "Stack trace:\n" + traceback.format_exc()
            QMessageBox.critical(self, "Erreur - Gestion Évaluations", error_msg)
            logger.error(f"show_gestion_evaluations: {e}", exc_info=True)

    def ouvrir_gestion_evaluations(self, filtre_statut):
        try:
            from core.gui.gestion_evaluation import GestionEvaluationDialog
            dialog = GestionEvaluationDialog()
            if hasattr(dialog, 'status_filter'):
                index = dialog.status_filter.findText(filtre_statut)
                if index >= 0:
                    dialog.status_filter.setCurrentIndex(index)
            dialog.exec_()
            self.load_evaluations_async()
        except Exception as e:
            logger.exception(f"Erreur ouverture gestion evaluations: {e}")
            if show_error_message:
                show_error_message(self, "Erreur", "Impossible d'ouvrir la gestion des évaluations", e)
            else:
                QMessageBox.critical(self, "Erreur", "Impossible d'ouvrir la gestion des évaluations. Contactez l'administrateur.")

    def show_listes_grilles_dialog(self):
        from core.gui.liste_et_grilles import GrillesDialog
        GrillesDialog().exec_()

    def show_poste_form(self):
        from core.gui.creation_modification_poste import CreationModificationPosteDialog
        CreationModificationPosteDialog().exec_()
        self._postes_cache = None
        self._postes_cache_time = None
        self.populate_filters_async()

    def show_historique(self):
        from core.gui.historique import HistoriqueDialog
        HistoriqueDialog().exec_()

    def show_regularisation(self):
        # ⚠️ DB => on passe en background, puis on ouvre le dialog sur le thread UI
        w = DbWorker(self._fetch_one_actif_personnel_id)
        w.signals.result.connect(self._open_regularisation)
        w.signals.error.connect(self._on_bg_error)
        DbThreadPool.start(w)

    def _fetch_one_actif_personnel_id(self, progress_callback=None):
        from core.repositories.personnel_repo import PersonnelRepository
        return PersonnelRepository.get_first_actif_id()

    def _open_regularisation(self, personnel_id):
        if not personnel_id:
            QMessageBox.warning(self, "Erreur", "Aucun personnel actif trouvé")
            return
        from core.gui.planning_absences import PlanningAbsencesDialog
        dialog = PlanningAbsencesDialog(personnel_id=personnel_id, parent=self)
        dialog.data_changed.connect(self.load_evaluations_async)
        dialog.exec_()

    def show_contract_management(self):
        from core.gui.gestion_rh import GestionRHDialog
        dialog = GestionRHDialog(self)
        dialog.data_changed.connect(self.load_evaluations_async)
        dialog.data_changed.connect(self.load_alertes_rh_async)
        dialog.exec_()

    def show_alertes_rh(self):
        """Ouvre le dialog de gestion des alertes RH."""
        from core.gui.gestion_alertes_rh import GestionAlertesRHDialog
        dialog = GestionAlertesRHDialog(self)
        dialog.data_changed.connect(self.load_alertes_rh_async)
        dialog.exec_()

    def show_gestion_documentaire(self):
        from core.gui.gestion_documentaire import GestionDocumentaireDialog
        dialog = GestionDocumentaireDialog(self)
        dialog.document_added.connect(self.load_evaluations_async)
        dialog.document_added.connect(self.load_alertes_rh_async)
        dialog.exec_()


    def show_gestion_templates(self):
        from core.gui.gestion_templates import GestionTemplatesDialog
        GestionTemplatesDialog(parent=self).exec_()

    # ---------------------------
    # DB async (filters + evaluations)
    # ---------------------------

    def populate_filters_async(self):
        w = DbWorker(self._fetch_postes_cached)
        w.signals.result.connect(self._apply_postes_to_filters)
        w.signals.error.connect(self._on_bg_error)
        DbThreadPool.start(w)

    def _fetch_postes_cached(self, progress_callback=None):
        # Cache 5 minutes
        if self._postes_cache is not None and self._postes_cache_time is not None:
            if (time.time() - self._postes_cache_time) < 300:
                return self._postes_cache

        from core.repositories.poste_repo import PosteRepository

        codes = PosteRepository.get_codes_list()
        # Garder le format tuple pour la compatibilité avec _apply_postes_to_filters
        postes = [(code,) for code in codes]
        self._postes_cache = postes
        self._postes_cache_time = time.time()
        return postes

    def _apply_postes_to_filters(self, postes):
        try:
            for (poste,) in postes:
                if self.retard_filter.findData(poste) == -1:
                    self.retard_filter.addItem(poste, poste)
                if self.next_eval_filter.findData(poste) == -1:
                    self.next_eval_filter.addItem(poste, poste)
        except Exception as e:
            logger.warning(f"Erreur apply filtres: {e}")

    def load_evaluations_async(self):
        poste_retard = self.retard_filter.currentData()
        poste_next = self.next_eval_filter.currentData()

        w = DbWorker(self._fetch_evaluations, poste_retard, poste_next)
        w.signals.result.connect(self._apply_evaluations_to_ui)
        w.signals.error.connect(self._on_bg_error)
        DbThreadPool.start(w)

    def _fetch_evaluations(self, poste_retard, poste_next, progress_callback=None):
        from core.repositories.polyvalence_repo import PolyvalenceRepository
        try:
            retard = PolyvalenceRepository.get_en_retard_filtre(
                poste_code=poste_retard or None, limit=10
            )
            prochaines = PolyvalenceRepository.get_a_venir_filtre(
                jours=30, poste_code=poste_next or None, limit=10
            )
            return {"retard": retard, "prochaines": prochaines}
        except Exception as e:
            logger.error(f"Erreur dans _fetch_evaluations: {e}", exc_info=True)
            raise

    def _apply_evaluations_to_ui(self, payload):
        try:
            retard = payload.get("retard", [])
            prochaines = payload.get("prochaines", [])

            self.retard_list.clear()
            for r in retard:
                nom = r.get('nom', '')
                prenom = r.get('prenom', '')
                poste = r.get('poste_code', '')
                date_ev = r.get('prochaine_evaluation')
                date_txt = date_ev.strftime('%d/%m/%Y') if hasattr(date_ev, 'strftime') else str(date_ev)
                self.retard_list.addItem(f"{nom} {prenom} · {poste or ''}  —  Retard: {date_txt}")

            self.next_eval_list.clear()
            for r in prochaines:
                nom = r.get('nom', '')
                prenom = r.get('prenom', '')
                poste = r.get('poste_code', '')
                date_ev = r.get('prochaine_evaluation')
                date_txt = date_ev.strftime('%d/%m/%Y') if hasattr(date_ev, 'strftime') else str(date_ev)
                self.next_eval_list.addItem(f"{nom} {prenom} · {poste or ''}  —  Prévu: {date_txt}")
        except Exception as e:
            logger.error(f"Erreur dans _apply_evaluations_to_ui: {e}", exc_info=True)

    # ---------------------------
    # Alertes Contrats (RH uniquement)
    # ---------------------------

    def load_alertes_rh_async(self):
        """Charge les contrats expirant bientôt."""
        type_contrat = self.alertes_rh_filter.currentData() if hasattr(self, 'alertes_rh_filter') else ""
        w = DbWorker(self._fetch_alertes_rh, type_contrat)
        w.signals.result.connect(self._apply_alertes_rh_to_ui)
        w.signals.error.connect(self._on_bg_error)
        DbThreadPool.start(w)

    def _fetch_alertes_rh(self, type_contrat_filter, progress_callback=None):
        from core.services.contrat_service_crud import ContratServiceCRUD
        try:
            contrats = ContratServiceCRUD.get_expiring_soon(
                jours=30,
                type_contrat=type_contrat_filter or None,
                limit=10,
            )
            return {"contrats": contrats}
        except Exception as e:
            logger.error(f"Erreur dans _fetch_alertes_rh: {e}", exc_info=True)
            raise

    def _apply_alertes_rh_to_ui(self, payload):
        try:
            contrats = payload.get("contrats", [])

            self.alertes_rh_list.clear()

            for c in contrats:
                nom = c.get('nom', '')
                prenom = c.get('prenom', '')
                type_contrat = c.get('type_contrat', '')
                date_fin = c.get('date_fin')
                date_txt = date_fin.strftime('%d/%m/%Y') if hasattr(date_fin, 'strftime') else str(date_fin)
                self.alertes_rh_list.addItem(f"{nom} {prenom} · {type_contrat}  —  Expire: {date_txt}")

            if not contrats:
                self.alertes_rh_list.addItem("✅ Aucun contrat à renouveler")
        except Exception as e:
            logger.error(f"Erreur dans _apply_alertes_rh_to_ui: {e}", exc_info=True)

    def _on_bg_error(self, tb):
        # Ne bloque pas l'app au démarrage
        logger.error(f"Erreur background:\n{tb}")

        # Afficher un message à l'utilisateur si possible
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
            pass  # Si on ne peut même pas afficher le message, tant pis

    # ---------------------------
    # Export
    # ---------------------------

    def export_logs_today(self):
        if not export_day:
            QMessageBox.warning(self, "Non disponible", "Module d'export non chargé.")
            return
        try:
            paths = export_day(dt.date.today(), base_dir="logs", make_zip=False)
            dossier = os.path.dirname(paths["csv"])
            QMessageBox.information(self, "Export", f"Export terminé ✅\n\nCSV : {paths['csv']}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(dossier))
        except Exception as e:
            logger.exception(f"Erreur export: {e}")
            if show_error_message:
                show_error_message(self, "Erreur", "Export impossible", e)
            else:
                QMessageBox.critical(self, "Erreur", "Export impossible. Contactez l'administrateur.")

    # ---------------------------
    # Auth & Session Timeout
    # ---------------------------

    def _start_timeout_monitoring(self):
        """Démarre la surveillance du timeout de session."""
        if self._timeout_manager:
            self._timeout_manager.start()
            logger.info("Surveillance timeout de session démarrée")

    def _force_logout_timeout(self):
        """
        Déconnexion forcée suite à un timeout de session.
        Pas de confirmation demandée - la session a expiré.
        """
        logger.warning("Déconnexion automatique: timeout de session")

        # Arrêter le timeout manager
        if self._timeout_manager:
            self._timeout_manager.stop()

        # Déconnecter l'utilisateur
        auth = _lazy_auth()
        auth.logout_user()
        clear_log_context()

        # Fermer la fenêtre actuelle
        self.close()

        # Afficher un message informatif
        QMessageBox.warning(
            None,
            "Session expirée",
            "Votre session a expiré en raison d'inactivité.\n"
            "Veuillez vous reconnecter pour continuer."
        )

        # Afficher le dialog de login
        from core.gui.login_dialog import LoginDialog
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QDialog.Accepted:
            try:
                user = auth.get_current_user()
                if user:
                    set_log_context(user_id=user.get('username') or user.get('nom'), screen='MainWindow')
            except Exception:
                pass
            new_window = MainWindow()
            new_window.show()

    def logout(self):
        reply = QMessageBox.question(
            self, "Déconnexion", "Voulez-vous vraiment vous déconnecter?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Arrêter le timeout manager
            if self._timeout_manager:
                self._timeout_manager.stop()

            auth = _lazy_auth()
            auth.logout_user()
            clear_log_context()  # Réinitialiser le contexte de logging
            self.close()

            from core.gui.login_dialog import LoginDialog
            login_dialog = LoginDialog()
            if login_dialog.exec_() == QDialog.Accepted:
                # Définir le nouveau contexte de logging
                try:
                    user = auth.get_current_user()
                    if user:
                        set_log_context(user_id=user.get('username') or user.get('nom'), screen='MainWindow')
                except Exception:
                    pass
                new_window = MainWindow()
                new_window.show()

    def show_user_management(self):
        auth = _lazy_auth()
        if not auth.is_admin():
            QMessageBox.warning(self, "Accès refusé", "Seuls les administrateurs peuvent gérer les utilisateurs.")
            return
        from core.gui.user_management import UserManagementDialog
        UserManagementDialog(self).exec_()

    def closeEvent(self, event):
        """Gère la fermeture de l'application."""
        # Arrêter le timeout manager
        if self._timeout_manager:
            self._timeout_manager.stop()
        event.accept()


# ===========================
#  Entry point
# ===========================

if __name__ == "__main__":
    # Crash handler global - ecrit dans crash.log meme si la console ferme
    def _crash_handler(exc_type, exc_value, exc_tb):
        crash_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        crash_file = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else '.', 'crash.log')
        with open(crash_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n{dt.datetime.now()}\n{crash_msg}\n")
        print(crash_msg, file=sys.stderr)
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    sys.excepthook = _crash_handler

    # Handler silencieux pour les messages Qt
    qInstallMessageHandler(lambda *_: None)

    app = QApplication(sys.argv)

    # ✅ Charger et appliquer le thème (lazy)
    theme = get_theme_components()
    EmacTheme = theme['EmacTheme']
    EmacTheme.apply(app)

    # ✅ Login (lazy)
    from core.gui.login_dialog import LoginDialog
    login_dialog = LoginDialog()

    if login_dialog.exec_() == LoginDialog.Accepted:
        # Définir le contexte de logging avec l'utilisateur connecté
        try:
            from core.services.auth_service import get_current_user
            user = get_current_user()
            if user:
                set_log_context(user_id=user.get('username') or user.get('nom'), screen='MainWindow')
        except Exception:
            pass

        win = MainWindow()
        win.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)