# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint

from infrastructure.logging.logging_config import get_logger
from gui.main_qt._shared import get_theme_components

logger = get_logger(__name__)


class DrawerMixin:
    """Gestion du panneau latéral (drawer) glissant."""

    def create_drawer(self):
        if self.drawer is not None:
            return

        theme = get_theme_components()
        EmacTheme = theme['EmacTheme']
        EmacButton = theme['EmacButton']

        self.drawer = QFrame(self)
        self.drawer.setObjectName("card")
        self.drawer.setFixedSize(self.DRAWER_WIDTH, self.height())

        border_color = EmacTheme.BDR
        bg_card = EmacTheme.BG_CARD
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

        perms = getattr(self, "_perms_cache", {"is_admin": False})
        mods = getattr(self, "_modules_cache", {"rh", "production", "planning", "documents", "historique"})

        def mod(code):
            return code in mods

        def add_btn(text, fn, variant='ghost'):
            btn = EmacButton(text, variant=variant)
            btn.setFixedHeight(44)
            btn.clicked.connect(fn)
            if fn not in (self.close, self.export_logs_today):
                btn.clicked.connect(self.toggle_drawer)
            drawer_layout.addWidget(btn)

        if mod("rh") and perms.get("personnel_ecriture"):
            add_btn("Ajouter du personnel", self.show_manage_operator)
        if mod("production") and perms.get("postes_ecriture"):
            add_btn("Création/Suppression de poste", self.show_poste_form)
        if mod("rh") and (perms.get("contrats_ecriture") or perms.get("documentsrh_ecriture")):
            row_alertes = QWidget()
            row_alertes_layout = QHBoxLayout(row_alertes)
            row_alertes_layout.setContentsMargins(0, 0, 0, 0)
            row_alertes_layout.setSpacing(6)

            btn_alertes = EmacButton("Alertes RH", 'ghost')
            btn_alertes.setFixedHeight(44)
            btn_alertes.clicked.connect(self.show_alertes_rh)
            btn_alertes.clicked.connect(self.toggle_drawer)
            row_alertes_layout.addWidget(btn_alertes, 1)

            self._drawer_notif_badge = QLabel("")
            self._drawer_notif_badge.setAlignment(Qt.AlignCenter)
            self._drawer_notif_badge.setAttribute(Qt.WA_StyledBackground, True)
            self._drawer_notif_badge.setStyleSheet("""
                background-color: #ef4444;
                color: white;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
                padding: 1px 6px;
                min-width: 20px;
                min-height: 20px;
            """)
            self._drawer_notif_badge.setFixedHeight(20)
            self._drawer_notif_badge.hide()
            row_alertes_layout.addWidget(self._drawer_notif_badge, 0, Qt.AlignVCenter | Qt.AlignRight)

            if self._last_notification_summary:
                total = (self._last_notification_summary.get('total_critique', 0) +
                         self._last_notification_summary.get('total_avertissement', 0))
                if total > 0:
                    display = str(total) if total < 100 else "99+"
                    self._drawer_notif_badge.setText(display)
                    self._drawer_notif_badge.show()

            drawer_layout.addWidget(row_alertes)

        if mod("planning") and perms.get("planning_lecture"):
            add_btn("Planning", self.show_regularisation)
        if mod("documents") and perms.get("documentsrh_lecture"):
            add_btn("Documents", self.show_gestion_templates)
        if mod("historique") and (perms.get("historique_lecture") or perms.get("is_admin")):
            add_btn("Historique", self.show_historique)

        if any(perms.get(k) for k in ("personnel_lecture", "contrats_lecture", "evaluations_lecture", "planning_lecture")):
            add_btn("Statistiques", self.show_statistiques)

        if perms.get("is_admin"):
            drawer_layout.addSpacing(10)
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("color: #ddd;")
            drawer_layout.addWidget(sep)
            drawer_layout.addSpacing(10)
            add_btn("Gestion des Utilisateurs", self.show_user_management)
            add_btn("Configuration BDD", self.show_admin_data_panel)

        drawer_layout.addStretch(1)
        drawer_layout.addSpacing(10)
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #ddd;")
        drawer_layout.addWidget(sep2)
        drawer_layout.addSpacing(10)
        add_btn("Déconnexion", self.logout)

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
