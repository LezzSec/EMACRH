# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QWidget,
)
from PyQt5.QtCore import Qt, QTimer

from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date
from gui.workers.db_worker import DbWorker, DbThreadPool
from gui.main_qt._shared import get_theme_components

logger = get_logger(__name__)


class NotificationsMixin:
    """Badge de notification et popup de démarrage des alertes."""

    def _load_notification_counts(self):
        from domain.services.admin.alert_service import AlertService
        def _fetch(progress_callback=None):
            return AlertService.get_startup_summary()
        w = DbWorker(_fetch)
        w.signals.result.connect(self._apply_notification_counts)
        w.signals.error.connect(lambda tb: logger.warning(f"Erreur compteurs alertes: {tb}"))
        DbThreadPool.start(w)

    def _apply_notification_counts(self, summary):
        logger.debug(f"Compteurs alertes: {summary}")
        self._last_notification_summary = summary
        total = summary.get('total_critique', 0) + summary.get('total_avertissement', 0)
        display = str(total) if total < 100 else "99+"

        if total > 0:
            self._notif_badge.setText(display)
            self._notif_badge.show()
        else:
            self._notif_badge.hide()

        if self.drawer is not None and hasattr(self, '_drawer_notif_badge'):
            if total > 0:
                self._drawer_notif_badge.setText(display)
                self._drawer_notif_badge.show()
            else:
                self._drawer_notif_badge.hide()

        total_all = summary.get('total_critique', 0) + summary.get('total_avertissement', 0)
        if not self._startup_alert_shown and total_all > 0:
            self._startup_alert_shown = True
            QTimer.singleShot(300, lambda: self._show_startup_alert_popup(summary))

    def _show_startup_alert_popup(self, summary):
        nb_critiques = summary.get('total_critique', 0)
        nb_avertissements = summary.get('total_avertissement', 0)

        dlg = QDialog(self)
        dlg.setWindowTitle("Alertes en attente")
        dlg.setFixedWidth(480)
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        header = QLabel("Des alertes necessitent votre attention")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #dc2626;")
        header.setWordWrap(True)
        layout.addWidget(header)

        totals_row = QHBoxLayout()
        totals_row.setSpacing(8)
        if nb_critiques > 0:
            lbl_crit = QLabel(f"  {nb_critiques} critique(s)  ")
            lbl_crit.setStyleSheet(
                "background: #fee2e2; color: #991b1b; font-weight: bold; "
                "font-size: 12px; border-radius: 4px; padding: 2px 6px;"
            )
            totals_row.addWidget(lbl_crit)
        if nb_avertissements > 0:
            lbl_warn = QLabel(f"  {nb_avertissements} avertissement(s)  ")
            lbl_warn.setStyleSheet(
                "background: #fef3c7; color: #92400e; font-weight: bold; "
                "font-size: 12px; border-radius: 4px; padding: 2px 6px;"
            )
            totals_row.addWidget(lbl_warn)
        totals_row.addStretch()
        layout.addLayout(totals_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e5e7eb;")
        layout.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMaximumHeight(340)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 4, 4, 4)
        scroll_layout.setSpacing(4)

        def add_section_header(title, bg, fg):
            lbl = QLabel(f"  {title}")
            lbl.setStyleSheet(
                f"background: {bg}; color: {fg}; font-weight: bold; "
                f"font-size: 11px; border-radius: 4px; padding: 4px 8px;"
            )
            scroll_layout.addWidget(lbl)

        def add_row(label, count, color, bg_color):
            if count <= 0:
                return
            row_widget = QWidget()
            row_widget.setStyleSheet(f"background: {bg_color}; border-radius: 4px;")
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(10, 5, 10, 5)
            row.setSpacing(8)
            txt = QLabel(label)
            txt.setStyleSheet("color: #1f2937; font-size: 12px; background: transparent;")
            cnt = QLabel(str(count))
            cnt.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; background: transparent;")
            cnt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(txt, 1)
            row.addWidget(cnt)
            scroll_layout.addWidget(row_widget)

        critiques = [
            ("Evaluations en retard",       summary.get('evaluations_retard', 0)),
            ("Contrats expires",            summary.get('contrats_expires', 0)),
            ("Mutuelles expirees",          summary.get('mutuelles_expirees', 0)),
            ("Visites medicales en retard", summary.get('visites_retard', 0)),
            ("Competences expirees",        summary.get('competences_expirees', 0)),
            ("Documents expires",           summary.get('documents_expires', 0)),
        ]
        if any(c > 0 for _, c in critiques):
            add_section_header("CRITIQUES — action immediate requise", "#fee2e2", "#991b1b")
            for label, count in critiques:
                add_row(label, count, "#dc2626", "#fff5f5")
            scroll_layout.addSpacing(6)

        avertissements = [
            ("Personnel sans contrat",      summary.get('personnel_sans_contrat', 0)),
            ("Contrats expirant (30j)",     summary.get('contrats_expirant', 0)),
            ("Mutuelles expirant (30j)",    summary.get('mutuelles_expirant', 0)),
            ("Visites medicales (30j)",     summary.get('visites_a_planifier', 0)),
            ("RQTH expirant (90j)",         summary.get('rqth_expirant', 0)),
            ("OETH expirant (90j)",         summary.get('oeth_expirant', 0)),
            ("Competences expirant (30j)",  summary.get('competences_expirant', 0)),
            ("Documents expirant (30j)",    summary.get('documents_expirant', 0)),
        ]
        if any(c > 0 for _, c in avertissements):
            add_section_header("AVERTISSEMENTS — a traiter prochainement", "#fef3c7", "#92400e")
            for label, count in avertissements:
                add_row(label, count, "#d97706", "#fffbeb")

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #e5e7eb;")
        layout.addWidget(sep2)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        EmacButton = get_theme_components()['EmacButton']
        btn_fermer = EmacButton("Fermer", variant='ghost')
        btn_fermer.clicked.connect(dlg.accept)
        btn_voir = EmacButton("Voir les alertes RH", variant='primary')
        btn_voir.clicked.connect(dlg.accept)
        btn_voir.clicked.connect(self.show_alertes_rh)
        btn_layout.addWidget(btn_fermer)
        btn_layout.addWidget(btn_voir)
        layout.addLayout(btn_layout)

        dlg.exec_()
