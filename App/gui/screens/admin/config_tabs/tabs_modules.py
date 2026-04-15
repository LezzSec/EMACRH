# -*- coding: utf-8 -*-
"""
Onglet modules de l'application : activation/désactivation des modules de navigation.
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


# Couleurs associées à chaque module
_MODULE_COLORS = {
    "rh":          "#2563eb",
    "production":  "#16a34a",
    "planning":    "#d97706",
    "documents":   "#7c3aed",
    "historique":  "#64748b",
}

# Icônes texte associées à chaque module
_MODULE_ICONS = {
    "rh":          "RH",
    "production":  "PR",
    "planning":    "PL",
    "documents":   "DO",
    "historique":  "HI",
}


class _ModuleCard(QFrame):
    """Carte représentant un module avec un bouton de bascule Activer/Désactiver."""

    toggled = pyqtSignal(str, bool)   # code, new_state

    def __init__(self, module: dict, parent=None):
        super().__init__(parent)
        self._code = module["code"]
        self._enabled = bool(module["is_enabled"])

        color = _MODULE_COLORS.get(self._code, "#6b7280")
        icon  = _MODULE_ICONS.get(self._code, "??")

        self.setObjectName("moduleCard")
        self.setStyleSheet(f"""
            QFrame#moduleCard {{
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                background: white;
            }}
            QFrame#moduleCard:hover {{
                border-color: {color};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(14)

        # Icône colorée
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(44, 44)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            background: {color};
            color: white;
            border-radius: 8px;
            font-size: 13px;
            font-weight: bold;
        """)
        lay.addWidget(icon_lbl)

        # Textes
        txt_col = QVBoxLayout()
        txt_col.setSpacing(2)
        self._lbl_name = QLabel(module["label"])
        self._lbl_name.setStyleSheet("font-size: 13px; font-weight: 600; color: #111827;")
        desc = module.get("description") or ""
        self._lbl_desc = QLabel(desc)
        self._lbl_desc.setStyleSheet("font-size: 11px; color: #6b7280;")
        self._lbl_desc.setWordWrap(True)
        txt_col.addWidget(self._lbl_name)
        txt_col.addWidget(self._lbl_desc)
        lay.addLayout(txt_col, 1)

        # Bouton toggle
        self._btn = QPushButton()
        self._btn.setFixedSize(110, 34)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(self._on_toggle)
        self._refresh_btn()
        lay.addWidget(self._btn, 0, Qt.AlignVCenter)

    def _refresh_btn(self):
        if self._enabled:
            self._btn.setText("Activé")
            self._btn.setStyleSheet("""
                QPushButton {
                    background: #dcfce7;
                    color: #15803d;
                    border: 1px solid #86efac;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #bbf7d0;
                }
            """)
        else:
            self._btn.setText("Désactivé")
            self._btn.setStyleSheet("""
                QPushButton {
                    background: #f1f5f9;
                    color: #64748b;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #e2e8f0;
                }
            """)

    def _on_toggle(self):
        new_state = not self._enabled
        from domain.services.admin.module_service import set_module_enabled
        ok = set_module_enabled(self._code, new_state)
        if ok:
            self._enabled = new_state
            self._refresh_btn()
            self.toggled.emit(self._code, new_state)
        else:
            QMessageBox.warning(
                self,
                "Erreur",
                f"Impossible de modifier le module « {self._code} ».\n"
                "Vérifiez que la migration 046 a bien été appliquée."
            )


class ModulesApplicationTab(QWidget):
    """
    Onglet d'activation/désactivation des modules de l'application.

    Chaque module correspond à une section de navigation (RH, Production…).
    Désactiver un module masque les boutons correspondants dans le menu
    latéral de l'application pour tous les utilisateurs.

    Les modifications sont effectives dès la fermeture de ce panneau.
    """

    modules_changed = pyqtSignal()   # émis quand au moins un module change

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        # Bandeau d'information
        info_frame = QFrame()
        info_frame.setStyleSheet(
            "background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;"
        )
        info_lay = QVBoxLayout(info_frame)
        info_lay.setContentsMargins(14, 10, 14, 10)
        info_lay.setSpacing(3)
        ttl = QLabel("Modules de l'application — navigation principale")
        ttl.setStyleSheet("font-weight: 700; color: #1e40af; font-size: 13px;")
        info_lay.addWidget(ttl)
        sub = QLabel(
            "Activez ou désactivez chaque module pour contrôler ce qui apparaît "
            "dans le menu de l'application. Les changements prennent effet "
            "immédiatement après fermeture de cette fenêtre."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #1e40af; font-size: 11px;")
        info_lay.addWidget(sub)
        outer.addWidget(info_frame)

        # Zone scrollable pour les cartes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(0, 4, 0, 4)
        self._cards_layout.setSpacing(10)
        self._cards_layout.addStretch(1)

        scroll.setWidget(self._cards_widget)
        outer.addWidget(scroll, 1)

        # Barre de statut
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: #6b7280; font-size: 11px;")
        outer.addWidget(self._lbl_status)

    def _load(self):
        from domain.services.admin.module_service import get_all_modules
        try:
            modules = get_all_modules()
        except Exception as e:
            logger.exception(f"Erreur chargement modules: {e}")
            self._lbl_status.setText("Erreur de chargement — migration 046 appliquée ?")
            return

        # Vider les cartes existantes (sauf le stretch final)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for mod in modules:
            card = _ModuleCard(mod, self)
            card.toggled.connect(self._on_module_toggled)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

        n = len(modules)
        self._lbl_status.setText(f"{n} module{'s' if n > 1 else ''} configuré{'s' if n > 1 else ''}")

    def _on_module_toggled(self, code: str, enabled: bool):
        state_txt = "activé" if enabled else "désactivé"
        self._lbl_status.setText(
            f"Module « {code} » {state_txt}. Fermez ce panneau pour appliquer."
        )
        self.modules_changed.emit()
