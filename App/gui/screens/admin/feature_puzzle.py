# -*- coding: utf-8 -*-
"""
Widget "Puzzle" pour la gestion des permissions par features.
Grille visuelle organisée par modules avec affichage enrichi.

Architecture:
- Mode rôle: modifier les features d'un rôle
- Mode utilisateur: modifier les overrides d'un utilisateur
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QPushButton, QComboBox,
    QMessageBox, QDialog, QGroupBox, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

_admin_role_id_cache = None

# Metadata UI lue depuis la table features (colonnes sensitivity, screens).
# Une base non migree affiche simplement les descriptions DB sans badge ecran.
_DEFAULT_SENSITIVITY_BY_MODULE = {'Admin': 'Admin'}

# (background, foreground, label) par niveau de sensibilité
_SENSITIVITY_STYLES = {
    'Standard': ('#f0fdf4', '#166534', 'Standard'),
    'Sensible':  ('#fffbeb', '#92400e', 'Sensible'),
    'Admin':     ('#fef2f2', '#991b1b', 'Admin'),
}


def get_admin_role_id() -> int:
    """
    Recupere l'ID du role admin depuis la base de donnees.
    Utilise un cache pour eviter les requetes repetees.
    """
    global _admin_role_id_cache

    if _admin_role_id_cache is not None:
        return _admin_role_id_cache

    try:
        from application.permission_manager import get_admin_role_id as _svc_admin_id
        role_id = _svc_admin_id()
        if role_id:
            _admin_role_id_cache = role_id
            return _admin_role_id_cache
    except Exception as e:
        logger.warning(f"Impossible de recuperer l'ID du role admin: {e}")

    logger.warning("Utilisation de l'ID admin par defaut (1) - verifier la base de donnees")
    _admin_role_id_cache = 1
    return _admin_role_id_cache


def invalidate_admin_role_cache():
    """Invalide le cache de l'ID admin (apres modification des roles)"""
    global _admin_role_id_cache
    _admin_role_id_cache = None


class FeatureToggle(QWidget):
    """
    Sélecteur de permission basé sur un QComboBox coloré.
    - Checked (vert) : Accordé
    - Unchecked (rouge) : Refusé
    - PartiallyChecked (bleu) : Hérité du rôle (mode utilisateur uniquement)
    """
    stateChanged = pyqtSignal(int)

    _COMBO_STYLE = """
        QComboBox {{
            background: {bg};
            color: {fg};
            border: 2px solid {border};
            border-radius: 8px;
            padding: 5px 8px 5px 12px;
            font-weight: bold;
            font-size: 11px;
            min-height: 28px;
        }}
        QComboBox:hover {{
            background: {hover_bg};
            border-color: {fg};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: right center;
            width: 22px;
            border-left: 1px solid {border};
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }}
        QComboBox QAbstractItemView {{
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 4px;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            color: #1e293b;
            padding: 6px 12px;
            border-radius: 4px;
            min-height: 28px;
        }}
        QComboBox QAbstractItemView::item:selected {{
            background: {bg};
            color: {fg};
        }}
        QComboBox QAbstractItemView::item:hover {{
            background: #f1f5f9;
            color: #1e293b;
        }}
    """

    _STATE_COLORS = {
        Qt.Checked:          dict(bg='#d1fae5', fg='#047857', border='#10b981', hover_bg='#a7f3d0'),
        Qt.Unchecked:        dict(bg='#fee2e2', fg='#dc2626', border='#ef4444', hover_bg='#fecaca'),
        Qt.PartiallyChecked: dict(bg='#dbeafe', fg='#1d4ed8', border='#3b82f6', hover_bg='#bfdbfe'),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_override_mode = False
        self._source = 'role'
        self._protected = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._combo = QComboBox()
        self._combo.setFixedWidth(115)
        self._combo.setCursor(Qt.PointingHandCursor)
        self._combo.currentIndexChanged.connect(self._on_index_changed)
        layout.addWidget(self._combo)

        self._rebuild_items()

    def _rebuild_items(self):
        """Reconstruit les options du combo selon le mode (rôle ou utilisateur)."""
        self._combo.blockSignals(True)
        current = self._combo.currentData() if self._combo.count() > 0 else Qt.Unchecked
        self._combo.clear()
        if self._is_override_mode:
            self._combo.addItem("Hérité", Qt.PartiallyChecked)
            self._combo.addItem("Accordé", Qt.Checked)
            self._combo.addItem("Refusé", Qt.Unchecked)
        else:
            self._combo.addItem("Accordé", Qt.Checked)
            self._combo.addItem("Refusé", Qt.Unchecked)
        # Restaure l'état précédent si disponible dans la nouvelle liste
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == current:
                self._combo.setCurrentIndex(i)
                break
        self._combo.blockSignals(False)
        self._update_style()

    def _on_index_changed(self, _: int):
        state = self._combo.currentData()
        if state is not None:
            self._update_style()
            self.stateChanged.emit(int(state))
            # Met à jour la source lors d'une interaction utilisateur
            if self._is_override_mode:
                self._source = 'role' if state == Qt.PartiallyChecked else 'override'

    def _update_style(self):
        state = self.checkState()
        colors = self._STATE_COLORS.get(state, self._STATE_COLORS[Qt.Unchecked])
        self._combo.setStyleSheet(self._COMBO_STYLE.format(**colors))

    def set_protected(self, protected: bool):
        self._protected = protected
        self._combo.setEnabled(not protected)
        if protected:
            self._combo.setToolTip(
                "Permission protégée : le rôle Administrateur doit conserver ses permissions d'administration"
            )
        else:
            self._combo.setToolTip("")

    def is_protected(self) -> bool:
        return self._protected

    def set_override_mode(self, enabled: bool):
        if self._is_override_mode == enabled:
            return
        self._is_override_mode = enabled
        self._rebuild_items()

    def set_source(self, source: str):
        self._source = source

    def get_source(self) -> str:
        return self._source

    def checkState(self):
        data = self._combo.currentData()
        return data if data is not None else Qt.Unchecked

    def setCheckState(self, state):
        self._combo.blockSignals(True)
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == state:
                self._combo.setCurrentIndex(i)
                break
        self._combo.blockSignals(False)
        self._update_style()

    def isChecked(self) -> bool:
        return self.checkState() == Qt.Checked

    def setChecked(self, checked: bool):
        self.setCheckState(Qt.Checked if checked else Qt.Unchecked)


class FeatureRow(QWidget):
    """
    Ligne d'affichage enrichie pour une feature :
    nom + description + badge écran + badge sensibilité + toggle.
    """

    def __init__(self, feature: dict, toggle: FeatureToggle, parent=None):
        super().__init__(parent)
        self._key = feature['key_code']
        self._label_text = feature.get('label') or self._key
        self._description = feature.get('description') or ''
        self._sensitivity = (
            feature.get('sensitivity')
            or _DEFAULT_SENSITIVITY_BY_MODULE.get(feature.get('module'), 'Standard')
        )
        self._screens = feature.get('screens') or ''

        self._setup_ui(toggle)

    def _setup_ui(self, toggle: FeatureToggle):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(12)

        # Partie gauche : infos textuelles
        info = QWidget()
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name_label = QLabel(self._label_text)
        name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_label.setStyleSheet("color: #1e293b;")
        info_layout.addWidget(name_label)

        if self._description:
            desc_label = QLabel(self._description)
            desc_label.setFont(QFont("Segoe UI", 9))
            desc_label.setStyleSheet("color: #64748b;")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)

        # Ligne de badges
        badges_widget = QWidget()
        badges_layout = QHBoxLayout(badges_widget)
        badges_layout.setContentsMargins(0, 2, 0, 0)
        badges_layout.setSpacing(6)

        if self._screens:
            screens_label = QLabel(f"Écran : {self._screens}")
            screens_label.setFont(QFont("Segoe UI", 8))
            screens_label.setStyleSheet(
                "color: #475569; background: #f1f5f9; border-radius: 3px; padding: 1px 6px;"
            )
            badges_layout.addWidget(screens_label)

        bg, fg, text = _SENSITIVITY_STYLES.get(self._sensitivity, _SENSITIVITY_STYLES['Standard'])
        sens_label = QLabel(text)
        sens_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        sens_label.setStyleSheet(
            f"color: {fg}; background: {bg}; border-radius: 3px; padding: 1px 6px;"
        )
        badges_layout.addWidget(sens_label)
        badges_layout.addStretch()
        info_layout.addWidget(badges_widget)

        layout.addWidget(info, 1)
        layout.addWidget(toggle, 0, Qt.AlignVCenter)

    def matches_search(self, text: str) -> bool:
        """Retourne True si la feature correspond au texte de recherche."""
        text = text.lower()
        return (
            text in self._label_text.lower()
            or text in self._description.lower()
            or text in self._screens.lower()
            or text in self._key.lower()
        )


class ModuleGroupBox(QGroupBox):
    """GroupBox stylisé pour un module de features"""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 12px;
                padding: 8px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 8px;
                background-color: #ffffff;
            }
        """)


class FeaturePuzzleWidget(QWidget):
    """
    Widget grille pour afficher et modifier les features par module.
    """
    permission_changed = pyqtSignal()

    ADMIN_MODULE = 'Admin'

    @property
    def ADMIN_ROLE_ID(self):
        return get_admin_role_id()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = 'role'
        self._role_id = None
        self._user_id = None
        self._toggles = {}          # {feature_key: FeatureToggle}
        self._feature_rows = []     # [(key, FeatureRow)] pour le filtrage
        self._module_rows = {}      # {module: [FeatureRow]} pour les actions de groupe
        self._role_features = set()
        self._admin_features = set()

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(16)
        self.container_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)

    def build_grid(self, features_by_module: dict):
        """Construit la grille de features organisée par modules."""
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._toggles = {}
        self._feature_rows = []
        self._module_rows = {}
        self._admin_features = set()

        if self.ADMIN_MODULE in features_by_module:
            for feature in features_by_module[self.ADMIN_MODULE]:
                self._admin_features.add(feature['key_code'])

        module_order = ['RH', 'Production', 'Planning', 'Admin']

        for module in module_order:
            if module not in features_by_module:
                continue

            features = features_by_module[module]
            group = ModuleGroupBox(module)
            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(0)
            group_layout.setContentsMargins(8, 22, 8, 8)

            # Ligne d'actions rapides par groupe
            action_row = self._make_group_action_row(module)
            group_layout.addWidget(action_row)

            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("color: #e2e8f0; margin: 2px 0;")
            group_layout.addWidget(sep)

            module_feature_rows = []
            for i, feature in enumerate(features):
                key = feature['key_code']

                toggle = FeatureToggle()
                toggle.set_override_mode(self._mode == 'user')
                toggle.stateChanged.connect(lambda _: self._on_toggle_changed())
                self._toggles[key] = toggle

                row = FeatureRow(feature, toggle)
                bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
                row.setStyleSheet(f"background: {bg}; border-radius: 4px;")

                group_layout.addWidget(row)
                self._feature_rows.append((key, row))
                module_feature_rows.append(row)

            self._module_rows[module] = module_feature_rows
            self.container_layout.addWidget(group)

        self.container_layout.addStretch()

    def _make_group_action_row(self, module: str) -> QWidget:
        """Crée la ligne de boutons d'action rapide pour un module."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(6)

        micro_style = """
            QPushButton {
                padding: 3px 8px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background: #f8fafc;
                color: #475569;
                font-size: 11px;
            }
            QPushButton:hover { background: #e2e8f0; }
        """

        btn_grant = QPushButton("Tout accorder")
        btn_grant.setStyleSheet(micro_style)
        btn_grant.clicked.connect(lambda: self._group_action(module, 'grant'))
        layout.addWidget(btn_grant)

        btn_deny = QPushButton("Tout refuser")
        btn_deny.setStyleSheet(micro_style)
        btn_deny.clicked.connect(lambda: self._group_action(module, 'deny'))
        layout.addWidget(btn_deny)

        if self._mode == 'user':
            btn_inherit = QPushButton("Restaurer l'héritage")
            btn_inherit.setStyleSheet(micro_style)
            btn_inherit.clicked.connect(lambda: self._group_action(module, 'inherit'))
            layout.addWidget(btn_inherit)

        layout.addStretch()
        return row

    def _group_action(self, module: str, action: str):
        """Applique une action (grant/deny/inherit) à toutes les features d'un module."""
        for row in self._module_rows.get(module, []):
            toggle = self._toggles.get(row._key)
            if toggle is None or toggle.is_protected():
                continue
            if action == 'grant':
                toggle.setChecked(True)
                if self._mode == 'user':
                    toggle.set_source('override')
            elif action == 'deny':
                toggle.setChecked(False)
                if self._mode == 'user':
                    toggle.set_source('override')
            elif action == 'inherit' and self._mode == 'user':
                toggle.setCheckState(Qt.PartiallyChecked)
                toggle.set_source('role')
        self.permission_changed.emit()

    def filter_features(self, text: str):
        """Affiche/masque les lignes de features selon le texte de recherche."""
        text = text.strip()
        for _, row in self._feature_rows:
            row.setVisible(not text or row.matches_search(text))

    def load_role_features(self, role_id: int):
        """Charge les features d'un rôle."""
        from application.permission_manager import get_features_by_module, get_role_features

        self._mode = 'role'
        self._role_id = role_id
        self._user_id = None

        features_by_module = get_features_by_module()
        self.build_grid(features_by_module)

        role_features = get_role_features(role_id)
        is_admin_role = (role_id == self.ADMIN_ROLE_ID)

        for key, toggle in self._toggles.items():
            toggle.set_override_mode(False)
            toggle.setChecked(key in role_features)
            toggle.set_source('role')
            toggle.set_protected(is_admin_role and key in self._admin_features)

    def load_user_features(self, user_id: int, role_id: int):
        """Charge les features d'un utilisateur (avec overrides)."""
        from application.permission_manager import (
            get_features_by_module, get_role_features, get_user_feature_overrides
        )

        self._mode = 'user'
        self._user_id = user_id
        self._role_id = role_id

        features_by_module = get_features_by_module()
        self.build_grid(features_by_module)

        self._role_features = get_role_features(role_id)
        user_overrides = get_user_feature_overrides(user_id)
        is_admin_role = (role_id == self.ADMIN_ROLE_ID)

        for key, toggle in self._toggles.items():
            toggle.set_override_mode(True)
            if key in user_overrides:
                toggle.setChecked(user_overrides[key])
                toggle.set_source('override')
            else:
                toggle.setCheckState(Qt.PartiallyChecked)
                toggle.set_source('role')
            toggle.set_protected(is_admin_role and key in self._admin_features)

    def _on_toggle_changed(self):
        self.permission_changed.emit()

    def get_role_features(self) -> set:
        """Retourne les features sélectionnées (mode rôle)."""
        return {key for key, toggle in self._toggles.items() if toggle.isChecked()}

    def get_user_overrides(self) -> dict:
        """
        Retourne les overrides utilisateur (mode user).
        {feature_key: True/False/None}  —  None = hérite du rôle
        """
        overrides = {}
        for key, toggle in self._toggles.items():
            if toggle.checkState() == Qt.PartiallyChecked:
                overrides[key] = None
            else:
                overrides[key] = toggle.isChecked()
        return overrides

    def reset_to_role(self):
        """Remet tous les toggles en mode 'Hérité', sauf les protégés."""
        if self._mode != 'user':
            return
        for toggle in self._toggles.values():
            if toggle.is_protected():
                continue
            toggle.setCheckState(Qt.PartiallyChecked)
            toggle.set_source('role')
        self.permission_changed.emit()

    def select_all(self):
        """Accorde toutes les features."""
        for toggle in self._toggles.values():
            toggle.setChecked(True)
            if self._mode == 'user':
                toggle.set_source('override')
        self.permission_changed.emit()

    def deselect_all(self):
        """Refuse toutes les features (sauf les protégées)."""
        for toggle in self._toggles.values():
            if toggle.is_protected():
                continue
            toggle.setChecked(False)
            if self._mode == 'user':
                toggle.set_source('override')
        self.permission_changed.emit()


class FeatureEditorDialog(QDialog):
    """Dialog complet pour éditer les features (rôles et utilisateurs)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Permissions")
        self.setMinimumSize(820, 720)
        self.setModal(True)

        self._current_mode = 'role'
        self._current_role_id = None
        self._current_user_id = None
        self._loading = True

        self.setup_ui()
        self.load_data()
        self._loading = False

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Titre
        title = QLabel("Gestion des Permissions")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #1e293b; margin-bottom: 4px;")
        layout.addWidget(title)

        # Card de sélection (mode + rôle + utilisateur)
        selection_card = QFrame()
        selection_card.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 12px;
            }
        """)
        selection_layout = QVBoxLayout(selection_card)
        selection_layout.setSpacing(10)

        combo_style = """
            QComboBox {
                padding: 7px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background: white;
                min-width: 280px;
                font-size: 13px;
            }
            QComboBox:hover { border-color: #94a3b8; }
        """
        label_style = "color: #64748b; font-size: 10pt; font-weight: bold;"

        mode_row = QHBoxLayout()
        mode_label = QLabel("Mode :")
        mode_label.setStyleSheet(label_style)
        mode_label.setFixedWidth(110)
        mode_row.addWidget(mode_label)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Modifier un rôle", "role")
        self.mode_combo.addItem("Modifier un utilisateur", "user")
        self.mode_combo.setStyleSheet(combo_style)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        selection_layout.addLayout(mode_row)

        role_row = QHBoxLayout()
        role_label = QLabel("Rôle :")
        role_label.setStyleSheet(label_style)
        role_label.setFixedWidth(110)
        role_row.addWidget(role_label)
        self.role_combo = QComboBox()
        self.role_combo.setStyleSheet(combo_style.replace("min-width: 280px", "min-width: 360px"))
        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        role_row.addWidget(self.role_combo)
        role_row.addStretch()
        selection_layout.addLayout(role_row)

        self.user_row_widget = QWidget()
        user_row = QHBoxLayout(self.user_row_widget)
        user_row.setContentsMargins(0, 0, 0, 0)
        user_label = QLabel("Utilisateur :")
        user_label.setStyleSheet(label_style)
        user_label.setFixedWidth(110)
        user_row.addWidget(user_label)
        self.user_combo = QComboBox()
        self.user_combo.setStyleSheet(combo_style.replace("min-width: 280px", "min-width: 360px"))
        self.user_combo.currentIndexChanged.connect(self._on_user_changed)
        user_row.addWidget(self.user_combo)
        user_row.addStretch()
        self.user_row_widget.setVisible(False)
        selection_layout.addWidget(self.user_row_widget)

        layout.addWidget(selection_card)

        # Barre de recherche
        search_frame = QFrame()
        search_frame.setStyleSheet("background: transparent;")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)

        search_lbl = QLabel("Rechercher :")
        search_lbl.setStyleSheet("color: #64748b; font-size: 12px;")
        search_layout.addWidget(search_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filtrer par nom, description, écran concerné...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 7px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background: white;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #3b82f6; }
        """)
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input, 1)

        clear_btn = QPushButton("Effacer")
        clear_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: white;
                color: #475569;
                font-size: 12px;
            }
            QPushButton:hover { background: #f1f5f9; }
        """)
        clear_btn.clicked.connect(self.search_input.clear)
        search_layout.addWidget(clear_btn)
        layout.addWidget(search_frame)

        # Légende combinée (état + sensibilité)
        legend_card = QFrame()
        legend_card.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        legend_outer = QVBoxLayout(legend_card)
        legend_outer.setContentsMargins(12, 8, 12, 8)
        legend_outer.setSpacing(6)

        # Ligne 1 : états des toggles
        state_row = QHBoxLayout()
        state_row.setSpacing(20)
        state_lbl = QLabel("État :")
        state_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        state_lbl.setStyleSheet("color: #475569;")
        state_lbl.setFixedWidth(80)
        state_row.addWidget(state_lbl)

        for text, bg, fg, desc in [
            ("Accordé", "#d1fae5", "#047857", "L'accès est explicitement autorisé"),
            ("Refusé",  "#fee2e2", "#dc2626", "L'accès est explicitement interdit"),
            ("Hérité",  "#dbeafe", "#1d4ed8", "Suit les droits du rôle (mode utilisateur)"),
        ]:
            badge = QLabel(text)
            badge.setStyleSheet(
                f"background:{bg}; color:{fg}; font-weight:bold; font-size:10px;"
                "padding: 3px 8px; border-radius: 4px;"
            )
            state_row.addWidget(badge)
            desc_lbl = QLabel(f"= {desc}")
            desc_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
            state_row.addWidget(desc_lbl)

        state_row.addStretch()
        legend_outer.addLayout(state_row)

        # Ligne 2 : niveaux de sensibilité
        sens_row = QHBoxLayout()
        sens_row.setSpacing(16)
        sens_title = QLabel("Sensibilité :")
        sens_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        sens_title.setStyleSheet("color: #475569;")
        sens_title.setFixedWidth(80)
        sens_row.addWidget(sens_title)

        sens_descs = {
            'Standard': 'Fonctionnalité courante, faible impact',
            'Sensible':  'Modification de données, impact sur les salariés',
            'Admin':     'Réservé aux administrateurs',
        }
        for level, (bg, fg, text) in _SENSITIVITY_STYLES.items():
            badge = QLabel(text)
            badge.setStyleSheet(
                f"background:{bg}; color:{fg}; font-weight:bold; font-size:10px;"
                "padding: 2px 7px; border-radius: 3px;"
            )
            badge.setToolTip(sens_descs[level])
            sens_row.addWidget(badge)
            desc_lbl = QLabel(sens_descs[level])
            desc_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
            sens_row.addWidget(desc_lbl)

        sens_row.addStretch()
        legend_outer.addLayout(sens_row)

        layout.addWidget(legend_card)

        # Grille des features
        self.puzzle_widget = FeaturePuzzleWidget()
        self.puzzle_widget.permission_changed.connect(self._on_permission_changed)
        layout.addWidget(self.puzzle_widget, 1)

        # Actions globales
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(8)

        btn_grant_all = QPushButton("Tout accorder")
        btn_grant_all.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #10b981;
                border-radius: 6px;
                background: #d1fae5;
                color: #047857;
                font-size: 12px;
            }
            QPushButton:hover { background: #a7f3d0; }
        """)
        btn_grant_all.clicked.connect(self.puzzle_widget.select_all)
        quick_actions.addWidget(btn_grant_all)

        btn_deny_all = QPushButton("Tout refuser")
        btn_deny_all.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ef4444;
                border-radius: 6px;
                background: #fee2e2;
                color: #dc2626;
                font-size: 12px;
            }
            QPushButton:hover { background: #fecaca; }
        """)
        btn_deny_all.clicked.connect(self.puzzle_widget.deselect_all)
        quick_actions.addWidget(btn_deny_all)

        self.btn_reset = QPushButton("Restaurer l'héritage du rôle")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                background: #dbeafe;
                color: #1d4ed8;
                font-size: 12px;
            }
            QPushButton:hover { background: #bfdbfe; }
        """)
        self.btn_reset.clicked.connect(self._on_reset)
        self.btn_reset.setVisible(False)
        quick_actions.addWidget(self.btn_reset)

        quick_actions.addStretch()
        layout.addLayout(quick_actions)

        # Boutons principaux
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background: white;
                color: #475569;
                font-weight: 500;
            }
            QPushButton:hover { background: #f1f5f9; }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        self.save_btn = QPushButton("Enregistrer")
        self.save_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                border: none;
                border-radius: 8px;
                background: #0f172a;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover { background: #1e293b; }
            QPushButton:disabled { background: #94a3b8; }
        """)
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _on_search(self, text: str):
        self.puzzle_widget.filter_features(text)

    def load_data(self):
        """Charge les données initiales."""
        from application.permission_manager import get_all_roles
        from domain.services.admin.auth_service import get_all_users

        roles = get_all_roles()
        self.role_combo.clear()
        for role in roles:
            desc = role.get('description', '')
            display = role['nom'] + (f" - {desc}" if desc else "")
            self.role_combo.addItem(display, role['id'])

        users = get_all_users()
        self.user_combo.clear()
        for user in users:
            display = f"{user['nom']} {user['prenom']} ({user['username']}) - {user['role_nom']}"
            self.user_combo.addItem(display, {'id': user['id'], 'role_id': None})

        if roles:
            self._load_role_features()

    def _on_mode_changed(self):
        if self._loading:
            return
        mode = self.mode_combo.currentData()
        self._current_mode = mode
        self.user_row_widget.setVisible(mode == 'user')
        self.btn_reset.setVisible(mode == 'user')
        if mode == 'role':
            self._load_role_features()
        else:
            self._load_user_features()
        self.save_btn.setEnabled(False)

    def _on_role_changed(self):
        if self._loading:
            return
        if self._current_mode == 'role':
            self._load_role_features()
        self.save_btn.setEnabled(False)

    def _on_user_changed(self):
        if self._loading:
            return
        if self._current_mode == 'user':
            self._load_user_features()
        self.save_btn.setEnabled(False)

    def _load_role_features(self):
        role_id = self.role_combo.currentData()
        if role_id:
            self._current_role_id = role_id
            self.puzzle_widget.load_role_features(role_id)

    def _load_user_features(self):
        user_data = self.user_combo.currentData()
        if user_data:
            from application.permission_manager import get_user_with_role
            user_id = user_data['id']
            user_info = get_user_with_role(user_id)
            if user_info:
                self._current_user_id = user_id
                self._current_role_id = user_info['role_id']
                self.puzzle_widget.load_user_features(user_id, user_info['role_id'])

    def _on_permission_changed(self):
        self.save_btn.setEnabled(True)

    def _on_reset(self):
        reply = QMessageBox.question(
            self, "Confirmation",
            "Restaurer toutes les permissions aux valeurs héritées du rôle ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.puzzle_widget.reset_to_role()

    def _on_save(self):
        from application.permission_manager import save_role_features, save_user_feature_overrides

        if self._current_mode == 'role':
            features = self.puzzle_widget.get_role_features()
            success, error = save_role_features(self._current_role_id, features)
        else:
            overrides = self.puzzle_widget.get_user_overrides()
            success, error = save_user_feature_overrides(self._current_user_id, overrides)

        if success:
            QMessageBox.information(self, "Succès", "Permissions enregistrées avec succès.")
            self.save_btn.setEnabled(False)
        else:
            logger.error(f"Erreur lors de l'enregistrement des permissions: {error}")
            QMessageBox.critical(
                self, "Erreur",
                "Impossible d'enregistrer les permissions. Consultez les logs pour plus de détails."
            )
