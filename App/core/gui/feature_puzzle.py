# -*- coding: utf-8 -*-
"""
Widget "Puzzle" pour la gestion des permissions par features.
Grille visuelle organisée par modules avec checkboxes explicites.

Architecture:
- Mode rôle: modifier les features d'un rôle
- Mode utilisateur: modifier les overrides d'un utilisateur
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QCheckBox, QFrame, QScrollArea, QPushButton, QComboBox,
    QMessageBox, QDialog, QGroupBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from core.gui.ui_theme import EmacTheme, EmacCard, EmacButton
from core.utils.logging_config import get_logger

logger = get_logger(__name__)

# Cache pour l'ID du role admin (evite les requetes repetees)
_admin_role_id_cache = None


def get_admin_role_id() -> int:
    """
    Recupere l'ID du role admin depuis la base de donnees.
    Utilise un cache pour eviter les requetes repetees.

    SECURITE: Ne pas hardcoder l'ID du role admin.

    Returns:
        ID du role admin, ou 1 par defaut si non trouve
    """
    global _admin_role_id_cache

    if _admin_role_id_cache is not None:
        return _admin_role_id_cache

    try:
        from core.services.permission_manager import get_admin_role_id as _svc_admin_id

        role_id = _svc_admin_id()
        if role_id:
            _admin_role_id_cache = role_id
            logger.debug(f"Role admin trouve: ID={_admin_role_id_cache}")
            return _admin_role_id_cache

    except Exception as e:
        logger.warning(f"Impossible de recuperer l'ID du role admin: {e}")

    # Fallback securise: retourner 1 mais logger un warning
    logger.warning("Utilisation de l'ID admin par defaut (1) - verifier la base de donnees")
    _admin_role_id_cache = 1
    return _admin_role_id_cache


def invalidate_admin_role_cache():
    """Invalide le cache de l'ID admin (apres modification des roles)"""
    global _admin_role_id_cache
    _admin_role_id_cache = None


class FeatureToggle(QWidget):
    """
    Widget toggle tristate pour une feature:
    - Checked (vert): Autorisé
    - Unchecked (rouge): Refusé
    - PartiallyChecked (bleu): Hérite du rôle (mode utilisateur uniquement)
    """
    stateChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = Qt.Unchecked
        self._is_override_mode = False
        self._source = 'role'
        self._protected = False  # Si True, ne peut pas être décoché

        self.setFixedSize(60, 28)
        self.setCursor(Qt.PointingHandCursor)

    def set_protected(self, protected: bool):
        """Marque le toggle comme protégé (ne peut pas être décoché)"""
        self._protected = protected
        if protected:
            self.setToolTip("Permission protégée: le rôle Admin doit conserver ses permissions d'administration")
            self.setCursor(Qt.ForbiddenCursor)
        else:
            self.setToolTip("")
            self.setCursor(Qt.PointingHandCursor)
        self.update()

    def is_protected(self) -> bool:
        return self._protected

    def set_override_mode(self, enabled: bool):
        """Active le mode override (3 états)"""
        self._is_override_mode = enabled
        self.update()

    def set_source(self, source: str):
        self._source = source
        self.update()

    def get_source(self) -> str:
        return self._source

    def checkState(self):
        return self._state

    def setCheckState(self, state):
        if self._state != state:
            self._state = state
            self.stateChanged.emit(state)
            self.update()

    def isChecked(self):
        return self._state == Qt.Checked

    def setChecked(self, checked: bool):
        self.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def mousePressEvent(self, event):
        if self._is_override_mode:
            # Cycle: AUTO -> OUI -> NON -> AUTO
            if self._state == Qt.PartiallyChecked:
                self.setCheckState(Qt.Checked)
                self._source = 'override'
            elif self._state == Qt.Checked:
                # Protégé: ne peut pas être décoché
                if self._protected:
                    return
                self.setCheckState(Qt.Unchecked)
                self._source = 'override'
            else:
                self.setCheckState(Qt.PartiallyChecked)
                self._source = 'role'
        else:
            # Mode rôle: toggle simple
            # Protégé: ne peut pas être décoché
            if self._protected and self.isChecked():
                return
            self.setChecked(not self.isChecked())

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPen, QBrush

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        if self._state == Qt.PartiallyChecked:
            bg_color = QColor("#dbeafe")
            border_color = QColor("#3b82f6")
            text = "AUTO"
            text_color = QColor("#1d4ed8")
        elif self._state == Qt.Checked:
            bg_color = QColor("#d1fae5")
            border_color = QColor("#10b981")
            text = "OUI"
            text_color = QColor("#047857")
        else:
            bg_color = QColor("#fee2e2")
            border_color = QColor("#ef4444")
            text = "NON"
            text_color = QColor("#dc2626")

        # Si protégé et coché, afficher avec un cadenas
        if self._protected and self._state == Qt.Checked:
            text = "OUI"

        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(2, 2, w-4, h-4, 6, 6)

        painter.setPen(text_color)
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, w, h, Qt.AlignCenter, text)

        painter.end()


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

    # Module Admin (protege)
    ADMIN_MODULE = 'Admin'

    @property
    def ADMIN_ROLE_ID(self):
        """
        SECURITE: Recupere l'ID du role admin dynamiquement.
        Ne plus utiliser de valeur hardcodee.
        """
        return get_admin_role_id()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = 'role'  # 'role' ou 'user'
        self._role_id = None
        self._user_id = None
        self._toggles = {}  # {feature_key: FeatureToggle}
        self._role_features = set()  # Features du rôle (pour mode user)
        self._admin_features = set()  # Features du module Admin

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Container
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(16)
        self.container_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)

    def build_grid(self, features_by_module: dict):
        """Construit la grille de features organisée par modules"""
        # Nettoyer
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._toggles = {}
        self._admin_features = set()

        # Mémoriser les features Admin
        if self.ADMIN_MODULE in features_by_module:
            for feature in features_by_module[self.ADMIN_MODULE]:
                self._admin_features.add(feature['key_code'])

        # Ordre des modules
        module_order = ['RH', 'Production', 'Planning', 'Admin']

        for module in module_order:
            if module not in features_by_module:
                continue

            features = features_by_module[module]

            # GroupBox pour le module
            group = ModuleGroupBox(module)
            group_layout = QGridLayout(group)
            group_layout.setSpacing(8)
            group_layout.setContentsMargins(12, 20, 12, 12)

            # En-têtes
            header_style = "color: #64748b; font-size: 11px; font-weight: bold;"
            group_layout.addWidget(QLabel(""), 0, 0)  # Vide pour feature label

            # Lignes de features
            for row, feature in enumerate(features):
                key = feature['key_code']
                label = feature['label']

                # Label de la feature
                feature_label = QLabel(label)
                feature_label.setFont(QFont("Segoe UI", 10))
                feature_label.setStyleSheet("color: #334155; padding: 4px 0;")
                feature_label.setToolTip(feature.get('description', ''))
                group_layout.addWidget(feature_label, row + 1, 0)

                # Toggle
                toggle = FeatureToggle()
                toggle.set_override_mode(self._mode == 'user')
                toggle.stateChanged.connect(lambda state, k=key: self._on_toggle_changed(k))
                self._toggles[key] = toggle

                # Container centré pour le toggle
                toggle_container = QWidget()
                toggle_layout = QHBoxLayout(toggle_container)
                toggle_layout.setContentsMargins(0, 0, 0, 0)
                toggle_layout.addWidget(toggle)
                toggle_layout.addStretch()

                group_layout.addWidget(toggle_container, row + 1, 1)

            # Stretch pour pousser les items vers le haut
            group_layout.setRowStretch(len(features) + 1, 1)

            self.container_layout.addWidget(group)

        # Spacer final
        self.container_layout.addStretch()

    def load_role_features(self, role_id: int):
        """Charge les features d'un rôle"""
        from core.services.permission_manager import get_features_by_module, get_role_features

        self._mode = 'role'
        self._role_id = role_id
        self._user_id = None

        features_by_module = get_features_by_module()
        self.build_grid(features_by_module)

        role_features = get_role_features(role_id)

        # Vérifier si c'est le rôle admin
        is_admin_role = (role_id == self.ADMIN_ROLE_ID)

        for key, toggle in self._toggles.items():
            toggle.set_override_mode(False)
            toggle.setChecked(key in role_features)
            toggle.set_source('role')

            # Protéger les features Admin pour le rôle admin
            if is_admin_role and key in self._admin_features:
                toggle.set_protected(True)
            else:
                toggle.set_protected(False)

    def load_user_features(self, user_id: int, role_id: int):
        """Charge les features d'un utilisateur (avec overrides)"""
        from core.services.permission_manager import (
            get_features_by_module, get_role_features, get_user_feature_overrides
        )

        self._mode = 'user'
        self._user_id = user_id
        self._role_id = role_id

        features_by_module = get_features_by_module()
        self.build_grid(features_by_module)

        # Features du rôle
        self._role_features = get_role_features(role_id)

        # Overrides utilisateur
        user_overrides = get_user_feature_overrides(user_id)

        # Vérifier si l'utilisateur a le rôle admin
        is_admin_role = (role_id == self.ADMIN_ROLE_ID)

        for key, toggle in self._toggles.items():
            toggle.set_override_mode(True)

            if key in user_overrides:
                # Override défini
                toggle.setChecked(user_overrides[key])
                toggle.set_source('override')
            else:
                # Hérite du rôle
                toggle.setCheckState(Qt.PartiallyChecked)
                toggle.set_source('role')

            # Protéger les features Admin pour les utilisateurs du rôle admin
            if is_admin_role and key in self._admin_features:
                toggle.set_protected(True)
            else:
                toggle.set_protected(False)

    def _on_toggle_changed(self, feature_key: str):
        self.permission_changed.emit()

    def get_role_features(self) -> set:
        """Retourne les features sélectionnées (mode rôle)"""
        features = set()
        for key, toggle in self._toggles.items():
            if toggle.isChecked():
                features.add(key)
        return features

    def get_user_overrides(self) -> dict:
        """
        Retourne les overrides utilisateur (mode user).
        {feature_key: True/False/None}
        None = pas d'override (hérite du rôle)
        """
        overrides = {}
        for key, toggle in self._toggles.items():
            if toggle.checkState() == Qt.PartiallyChecked:
                overrides[key] = None  # Hérite du rôle
            else:
                overrides[key] = toggle.isChecked()
        return overrides

    def reset_to_role(self):
        """Remet tous les toggles en mode 'AUTO' (hérite du rôle), sauf les protégés"""
        if self._mode != 'user':
            return

        for toggle in self._toggles.values():
            # Ne pas modifier les toggles protégés
            if toggle.is_protected():
                continue
            toggle.setCheckState(Qt.PartiallyChecked)
            toggle.set_source('role')

        self.permission_changed.emit()

    def select_all(self):
        """Sélectionne toutes les features"""
        for toggle in self._toggles.values():
            toggle.setChecked(True)
            if self._mode == 'user':
                toggle.set_source('override')
        self.permission_changed.emit()

    def deselect_all(self):
        """Désélectionne toutes les features (sauf les protégées)"""
        for toggle in self._toggles.values():
            # Ne pas décocher les toggles protégés
            if toggle.is_protected():
                continue
            toggle.setChecked(False)
            if self._mode == 'user':
                toggle.set_source('override')
        self.permission_changed.emit()


class FeatureEditorDialog(QDialog):
    """Dialog complet pour éditer les features (rôles et utilisateurs)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Permissions (Features)")
        self.setMinimumSize(700, 650)
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
        layout.setSpacing(16)

        # Titre
        title = QLabel("Gestion des Permissions")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #1e293b; margin-bottom: 8px;")
        layout.addWidget(title)

        # Card de sélection
        selection_card = QFrame()
        selection_card.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        selection_layout = QVBoxLayout(selection_card)
        selection_layout.setSpacing(12)

        # Mode
        mode_row = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        mode_label.setStyleSheet("color: #64748b;")
        mode_label.setFixedWidth(100)
        mode_row.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Modifier un rôle", "role")
        self.mode_combo.addItem("Modifier un utilisateur", "user")
        self.mode_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background: white;
                min-width: 250px;
                font-size: 13px;
            }
            QComboBox:hover { border-color: #94a3b8; }
        """)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        selection_layout.addLayout(mode_row)

        # Rôle
        role_row = QHBoxLayout()
        role_label = QLabel("Rôle:")
        role_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        role_label.setStyleSheet("color: #64748b;")
        role_label.setFixedWidth(100)
        role_row.addWidget(role_label)

        self.role_combo = QComboBox()
        self.role_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background: white;
                min-width: 350px;
                font-size: 13px;
            }
        """)
        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        role_row.addWidget(self.role_combo)
        role_row.addStretch()
        selection_layout.addLayout(role_row)

        # Utilisateur (caché par défaut)
        self.user_row_widget = QWidget()
        user_row = QHBoxLayout(self.user_row_widget)
        user_row.setContentsMargins(0, 0, 0, 0)
        user_label = QLabel("Utilisateur:")
        user_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        user_label.setStyleSheet("color: #64748b;")
        user_label.setFixedWidth(100)
        user_row.addWidget(user_label)

        self.user_combo = QComboBox()
        self.user_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background: white;
                min-width: 350px;
                font-size: 13px;
            }
        """)
        self.user_combo.currentIndexChanged.connect(self._on_user_changed)
        user_row.addWidget(self.user_combo)
        user_row.addStretch()
        self.user_row_widget.setVisible(False)
        selection_layout.addWidget(self.user_row_widget)

        layout.addWidget(selection_card)

        # Légende
        legend_frame = QFrame()
        legend_frame.setStyleSheet("background: transparent;")
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(24)

        legend_items = [
            ("OUI", "#d1fae5", "#047857", "Permission accordée"),
            ("NON", "#fee2e2", "#dc2626", "Permission refusée"),
            ("AUTO", "#dbeafe", "#1d4ed8", "Hérite du rôle"),
        ]

        for text, bg, color, tooltip in legend_items:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(6)

            badge = QLabel(text)
            badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg};
                    color: {color};
                    font-weight: bold;
                    font-size: 10px;
                    padding: 4px 8px;
                    border-radius: 4px;
                }}
            """)
            item_layout.addWidget(badge)

            desc = QLabel(f"= {tooltip}")
            desc.setStyleSheet("color: #64748b; font-size: 11px;")
            item_layout.addWidget(desc)

            legend_layout.addWidget(item_widget)

        legend_layout.addStretch()
        layout.addWidget(legend_frame)

        # Grille des features
        self.puzzle_widget = FeaturePuzzleWidget()
        self.puzzle_widget.permission_changed.connect(self._on_permission_changed)
        layout.addWidget(self.puzzle_widget, 1)

        # Boutons d'action rapide
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(8)

        btn_select_all = QPushButton("Tout cocher")
        btn_select_all.setStyleSheet("""
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
        btn_select_all.clicked.connect(self.puzzle_widget.select_all)
        quick_actions.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("Tout décocher")
        btn_deselect_all.setStyleSheet("""
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
        btn_deselect_all.clicked.connect(self.puzzle_widget.deselect_all)
        quick_actions.addWidget(btn_deselect_all)

        self.btn_reset = QPushButton("↻ Réinitialiser au rôle")
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

    def load_data(self):
        """Charge les données initiales"""
        from core.services.permission_manager import get_all_roles
        from core.services.auth_service import get_all_users

        # Charger les rôles
        roles = get_all_roles()
        self.role_combo.clear()
        for role in roles:
            desc = role.get('description', '')
            display = f"{role['nom']}" + (f" - {desc}" if desc else "")
            self.role_combo.addItem(display, role['id'])

        # Charger les utilisateurs
        users = get_all_users()
        self.user_combo.clear()
        for user in users:
            display = f"{user['nom']} {user['prenom']} ({user['username']}) - {user['role_nom']}"
            self.user_combo.addItem(display, {
                'id': user['id'],
                'role_id': None  # Sera récupéré au moment du chargement
            })

        # Charger les features du premier rôle
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
            from core.services.permission_manager import get_user_with_role

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
            "Réinitialiser toutes les permissions aux valeurs du rôle ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.puzzle_widget.reset_to_role()

    def _on_save(self):
        from core.services.permission_manager import save_role_features, save_user_feature_overrides

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
            QMessageBox.critical(self, "Erreur", "Impossible d'enregistrer les permissions. Consultez les logs pour plus de détails.")
