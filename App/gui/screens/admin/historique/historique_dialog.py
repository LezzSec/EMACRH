# -*- coding: utf-8 -*-
import datetime as dt
import os
from itertools import groupby

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QFrame, QDateEdit, QMessageBox, QComboBox,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QCursor

from domain.services.admin.historique_service import fetch_historique_paginated, delete_historique_range, MODULE_TABLES
from infrastructure.logging.log_exporter import export_day
from gui.components.emac_ui_kit import add_custom_title_bar, show_error_message
from gui.workers.db_worker import DbWorker, DbThreadPool
from gui.components.loading_components import LoadingLabel
from infrastructure.logging.logging_config import get_logger

from gui.screens.admin.historique.utils import get_action_config
from gui.screens.admin.historique.date_separator import DateSeparator
from gui.screens.admin.historique.action_card import ActionCard

logger = get_logger(__name__)

_PAGE_SIZE = 100


class HistoriqueDialog(QDialog):
    """Visionneuse moderne de l'historique avec vue en cards/timeline."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique des modifications")
        self.resize(1000, 700)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = add_custom_title_bar(self, "Historique des modifications")
        main_layout.addWidget(title_bar)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: #eef1f5;")
        root = QVBoxLayout(content_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header_bg = QWidget()
        header_bg.setStyleSheet("background: #eef1f5;")
        header_bg_layout = QVBoxLayout(header_bg)
        header_bg_layout.setContentsMargins(18, 16, 18, 14)
        header_bg_layout.setSpacing(0)

        card = QFrame()
        card.setStyleSheet("QFrame { background-color: white; border-radius: 10px; border: none; }")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 40))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        icon_badge = QLabel("~")
        icon_badge.setFont(QFont("Segoe UI", 16))
        icon_badge.setStyleSheet("background-color: #e3f2fd; border-radius: 8px; padding: 4px 8px;")
        title_row.addWidget(icon_badge)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel("Historique des modifications")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #1a237e; background: transparent;")
        title_col.addWidget(title)
        sub = QLabel("Chronologie complète des actions enregistrées")
        sub.setStyleSheet("color: #90a4ae; font-size: 10px; background: transparent;")
        title_col.addWidget(sub)
        title_row.addLayout(title_col, stretch=1)
        card_layout.addLayout(title_row)

        inner_sep = QFrame()
        inner_sep.setFrameShape(QFrame.HLine)
        inner_sep.setFixedHeight(1)
        inner_sep.setStyleSheet("QFrame { background-color: #f0f4f8; border: none; }")
        card_layout.addWidget(inner_sep)

        filters_row = QHBoxLayout()
        filters_row.setSpacing(8)

        field_style = """
            QDateEdit, QComboBox, QLineEdit {
                padding: 5px 10px; border: 1px solid #e0e0e0;
                border-radius: 6px; background: #f8fafc;
                font-size: 11px; color: #37474f;
            }
            QDateEdit:focus, QComboBox:focus, QLineEdit:focus {
                border: 1.5px solid #1976d2; background: white;
            }
        """

        self.from_date = QDateEdit(calendarPopup=True)
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setDisplayFormat("dd/MM/yyyy")
        self.from_date.setFixedHeight(32)
        self.from_date.setStyleSheet(field_style)
        filters_row.addWidget(self.from_date)

        arr = QLabel("→")
        arr.setStyleSheet("color: #b0bec5; font-size: 13px; background: transparent;")
        filters_row.addWidget(arr)

        self.to_date = QDateEdit(calendarPopup=True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setDisplayFormat("dd/MM/yyyy")
        self.to_date.setFixedHeight(32)
        self.to_date.setStyleSheet(field_style)
        filters_row.addWidget(self.to_date)

        def _vsep():
            v = QFrame()
            v.setFrameShape(QFrame.VLine)
            v.setFixedHeight(22)
            v.setStyleSheet("QFrame { color: #e0e0e0; }")
            return v

        filters_row.addWidget(_vsep(), alignment=Qt.AlignVCenter)

        self.action_filter = QComboBox()
        self.action_filter.addItems(["(Toutes les actions)", "Ajout", "Modification", "Suppression", "Erreur"])
        self.action_filter.setFixedHeight(32)
        self.action_filter.setStyleSheet(field_style)
        self.action_filter.currentIndexChanged.connect(self.reload)
        filters_row.addWidget(self.action_filter)

        filters_row.addWidget(_vsep(), alignment=Qt.AlignVCenter)

        self.sort_order_filter = QComboBox()
        self.sort_order_filter.addItems(["Plus récent en premier", "Plus ancien en premier"])
        self.sort_order_filter.setFixedHeight(32)
        self.sort_order_filter.setStyleSheet(field_style)
        self.sort_order_filter.currentIndexChanged.connect(self.reload)
        filters_row.addWidget(self.sort_order_filter)

        filters_row.addWidget(_vsep(), alignment=Qt.AlignVCenter)

        self.search = QLineEdit(placeholderText="Rechercher...")
        self.search.setFixedHeight(32)
        self.search.returnPressed.connect(self.reload)
        self.search.setStyleSheet(field_style)
        filters_row.addWidget(self.search, stretch=1)

        filters_row.addSpacing(4)

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.setFixedHeight(32)
        self.btn_refresh.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_refresh.clicked.connect(self.reload)
        self.btn_refresh.setStyleSheet("""
            QPushButton { background-color: #1976d2; color: white; border: none;
                padding: 0px 18px; border-radius: 6px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:pressed { background-color: #0d47a1; }
        """)
        filters_row.addWidget(self.btn_refresh)

        self.btn_clear = QPushButton("Archiver...")
        self.btn_clear.setFixedHeight(32)
        self.btn_clear.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_clear.clicked.connect(self._clear_range_with_optional_export)
        self.btn_clear.setStyleSheet("""
            QPushButton { background-color: #fff3e0; color: #e65100;
                border: 1px solid #ffcc80; padding: 0px 18px;
                border-radius: 6px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background-color: #ffe0b2; border-color: #ffa726; }
            QPushButton:pressed { background-color: #ffcc80; }
        """)
        filters_row.addWidget(self.btn_clear)

        card_layout.addLayout(filters_row)
        header_bg_layout.addWidget(card)
        root.addWidget(header_bg)

        content_inner = QWidget()
        content_inner.setStyleSheet("background: #eef1f5;")
        inner_layout = QVBoxLayout(content_inner)
        inner_layout.setContentsMargins(18, 0, 18, 14)
        inner_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #eef1f5; border: none; }")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setContentsMargins(0, 8, 0, 4)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        inner_layout.addWidget(scroll, stretch=1)

        self._btn_load_more = QPushButton("Charger plus…")
        self._btn_load_more.clicked.connect(self._load_more)
        self._btn_load_more.setVisible(False)
        self._btn_load_more.setStyleSheet("""
            QPushButton { background-color: #f5f5f5; color: #616161;
                border: 1px solid #e0e0e0; padding: 8px 16px;
                border-radius: 5px; font-size: 11px; }
            QPushButton:hover { background-color: #eeeeee; }
        """)
        inner_layout.addWidget(self._btn_load_more)

        self.count_label = QLabel()
        self.count_label.setStyleSheet("QLabel { padding: 6px 10px; color: #78909c; font-size: 10px; background-color: transparent; }")
        inner_layout.addWidget(self.count_label)

        root.addWidget(content_inner, stretch=1)
        main_layout.addWidget(content_widget)

        self._page_offset = 0
        self._current_worker = None
        self._loading_label = None
        self._last_shown_date = None

        self._allowed_tables = self._resolve_allowed_tables()
        if self._allowed_tables is not None:
            modules = ', '.join(sorted(
                m for m, tables in MODULE_TABLES.items()
                if any(t in self._allowed_tables for t in tables)
            ))
            sub.setText(f"Actions liées à votre périmètre ({modules})")
            self.btn_clear.setVisible(False)

        self.reload()

    def _resolve_allowed_tables(self):
        try:
            from domain.services.admin.auth_service import get_current_user
            user = get_current_user()
            if not user:
                return None
            role = user.get('role_nom', '')
            if role == 'gestion_production':
                return MODULE_TABLES["Production"] + MODULE_TABLES["Planning"] + ["personnel", "personnel_infos"]
            elif role == 'gestion_rh':
                return MODULE_TABLES["RH"] + MODULE_TABLES["Planning"]
            return None
        except Exception:
            return None

    def _cancel_current_worker(self):
        if self._current_worker is None:
            return
        try:
            self._current_worker.signals.result.disconnect()
        except TypeError:
            pass
        try:
            self._current_worker.signals.error.disconnect()
        except TypeError:
            pass
        self._current_worker.cancel()
        self._current_worker = None

    def reload(self):
        self._page_offset = 0
        self._last_shown_date = None
        self._cancel_current_worker()

        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._loading_label = LoadingLabel("Chargement de l'historique")
        self._loading_label.setAlignment(Qt.AlignCenter)
        self.cards_layout.insertWidget(0, self._loading_label)

        self.count_label.setText("⏳ Chargement…")
        self._btn_load_more.setVisible(False)
        self._launch_fetch()

    def _launch_fetch(self):
        d_from = self.from_date.date()
        d_to   = self.to_date.date()
        search_text   = self.search.text()
        action_filter = self.action_filter.currentText()
        sort_order    = "ASC" if self.sort_order_filter.currentIndex() == 1 else "DESC"
        offset        = self._page_offset

        def fetch(progress_callback=None):
            return fetch_historique_paginated(
                date_from=dt.datetime(d_from.year(), d_from.month(), d_from.day(), 0, 0, 0),
                date_to=dt.datetime(d_to.year(), d_to.month(), d_to.day(), 23, 59, 59),
                search_text=search_text,
                action_filter=action_filter,
                table_names=self._allowed_tables,
                offset=offset,
                limit=_PAGE_SIZE + 1,
                sort_order=sort_order,
            )

        def on_result(rows):
            self._on_data_fetched(rows, offset)

        def on_error(err):
            if self._loading_label:
                self._loading_label.stop()
                self._loading_label.setText("Erreur de chargement")
                self._loading_label = None
            self.count_label.setText("Erreur")
            logger.error(f"Erreur fetch historique: {err}")
            QMessageBox.critical(self, "Erreur", "Impossible de charger l'historique.")

        self._current_worker = DbWorker(fetch)
        self._current_worker.signals.result.connect(on_result)
        self._current_worker.signals.error.connect(on_error)
        DbThreadPool.start(self._current_worker)

    def _on_data_fetched(self, rows, offset):
        has_more = len(rows) > _PAGE_SIZE
        if has_more:
            rows = rows[:_PAGE_SIZE]

        if self._loading_label:
            self._loading_label.stop()
            self._loading_label.deleteLater()
            self._loading_label = None

        insert_pos = self.cards_layout.count() - 1
        for row_date, group in groupby(rows, key=self._row_date):
            group_rows = list(group)
            if row_date is not None and row_date != self._last_shown_date:
                sep = DateSeparator(row_date, count=len(group_rows))
                self.cards_layout.insertWidget(insert_pos, sep)
                insert_pos += 1
                self._last_shown_date = row_date
            for row in group_rows:
                card = ActionCard(row)
                self.cards_layout.insertWidget(insert_pos, card)
                insert_pos += 1

        if offset == 0 and len(rows) == 0:
            no_result = QLabel("Aucune action trouvée pour cette période")
            no_result.setAlignment(Qt.AlignCenter)
            no_result.setStyleSheet("color: #9e9e9e; font-size: 12px; padding: 40px;")
            self.cards_layout.insertWidget(0, no_result)

        total = offset + len(rows)
        self._page_offset = total
        suffix = " — suite disponible" if has_more else ""
        self.count_label.setText(f"{total} action(s) affichée(s){suffix}")
        self._btn_load_more.setVisible(has_more)

    @staticmethod
    def _row_date(row: dict):
        dt_val = row.get('date_time')
        if dt_val is None:
            return None
        if hasattr(dt_val, 'date'):
            return dt_val.date()
        if isinstance(dt_val, str):
            try:
                return dt.datetime.fromisoformat(dt_val).date()
            except Exception:
                return None
        return None

    def _load_more(self):
        self._cancel_current_worker()
        self._btn_load_more.setVisible(False)
        self.count_label.setText("⏳ Chargement de la suite…")
        self._launch_fetch()

    def _export_range(self, d_from: QDate, d_to: QDate):
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "exports")
        os.makedirs(base_dir, exist_ok=True)

        if d_from == d_to:
            export_day(dt.date(d_from.year(), d_from.month(), d_from.day()), base_dir=base_dir)
            QMessageBox.information(self, "Export réussi",
                                    f"Export du {d_from.toString('dd/MM/yyyy')} effectué dans:\n{base_dir}")
        else:
            d = dt.date(d_from.year(), d_from.month(), d_from.day())
            end = dt.date(d_to.year(), d_to.month(), d_to.day())
            count = 0
            while d <= end:
                export_day(d, base_dir=base_dir)
                d += dt.timedelta(days=1)
                count += 1
            QMessageBox.information(self, "Export réussi",
                                   f"{count} fichier(s) d'export créé(s) dans:\n{base_dir}")

    def _clear_range_with_optional_export(self):
        d_from = self.from_date.date()
        d_to   = self.to_date.date()

        resp = QMessageBox.question(
            self, "Archivage de l'historique",
            f"Vous êtes sur le point d'archiver les logs du {d_from.toString('dd/MM/yyyy')} au {d_to.toString('dd/MM/yyyy')}.\n\n"
            "Voulez-vous créer une sauvegarde (export) avant la suppression ?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        if resp == QMessageBox.Cancel:
            return
        if resp == QMessageBox.Yes:
            try:
                self._export_range(d_from, d_to)
            except Exception as e:
                logger.exception(f"Erreur export: {e}")
                show_error_message(self, "Erreur d'export", "Échec de l'export", e)
                return

        confirm = QMessageBox.warning(
            self, "Confirmation de suppression",
            "Cette action va supprimer définitivement les logs de la période sélectionnée.\n\n"
            "Êtes-vous certain de vouloir continuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            deleted = delete_historique_range(
                date_from=dt.datetime(d_from.year(), d_from.month(), d_from.day(), 0, 0, 0),
                date_to=dt.datetime(d_to.year(), d_to.month(), d_to.day(), 23, 59, 59),
            )
            QMessageBox.information(self, "Archivage terminé",
                                   f"Archivage effectué avec succès.\n{deleted} ligne(s) supprimée(s) de l'historique.")
            self.reload()

        except Exception as e:
            code = getattr(e, "errno", None) or (e.args[0] if getattr(e, "args", None) else "")
            msg  = getattr(e, "msg", None) or (e.args[1] if getattr(e, "args", None) and len(e.args) > 1 else str(e))
            QMessageBox.critical(self, "Erreur", f"Échec de la suppression :\n{msg or code}")
