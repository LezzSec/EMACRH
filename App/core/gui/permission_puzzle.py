# -*- coding: utf-8 -*-
"""
Widget "Puzzle" pour la gestion des permissions
Grille visuelle de checkboxes pour activer/désactiver les permissions par module
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QCheckBox, QFrame, QScrollArea, QPushButton, QComboBox,
    QMessageBox, QSizePolicy, QDialog, QSpacerItem, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from core.gui.ui_theme import EmacTheme, EmacCard, EmacButton


class PermissionToggle(QWidget):
    """
    Widget toggle pour une permission avec indicateur visuel clair
    """
    stateChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = Qt.Unchecked  # Unchecked, Checked, PartiallyChecked
        self._is_override_mode = False
        self._source = 'role'

        self.setFixedSize(50, 28)
        self.setCursor(Qt.PointingHandCursor)

    def set_override_mode(self, enabled: bool):
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

    def setTristate(self, enabled: bool):
        pass  # Pour compatibilité

    def mousePressEvent(self, event):
        if self._is_override_mode:
            # Cycle: PartiallyChecked -> Checked -> Unchecked -> PartiallyChecked
            if self._state == Qt.PartiallyChecked:
                self.setCheckState(Qt.Checked)
                self._source = 'override'
            elif self._state == Qt.Checked:
                self.setCheckState(Qt.Unchecked)
                self._source = 'override'
            else:
                self.setCheckState(Qt.PartiallyChecked)
                self._source = 'role'
        else:
            # Mode rôle: toggle simple
            self.setChecked(not self.isChecked())

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPen, QBrush

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        # Couleurs selon l'état
        if self._state == Qt.PartiallyChecked:
            # Hérité du rôle - bleu
            bg_color = QColor("#dbeafe")
            border_color = QColor("#3b82f6")
            text = "AUTO"
            text_color = QColor("#1d4ed8")
        elif self._state == Qt.Checked:
            # Autorisé - vert
            bg_color = QColor("#d1fae5")
            border_color = QColor("#10b981")
            text = "OUI"
            text_color = QColor("#047857")
        else:
            # Refusé - rouge/gris
            bg_color = QColor("#fee2e2")
            border_color = QColor("#ef4444")
            text = "NON"
            text_color = QColor("#dc2626")

        # Dessiner le fond arrondi
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(2, 2, w-4, h-4, 6, 6)

        # Dessiner le texte
        painter.setPen(text_color)
        font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, w, h, Qt.AlignCenter, text)

        painter.end()

    def update_style(self):
        self.update()


class PermissionPuzzleWidget(QWidget):
    """
    Widget grille pour afficher et modifier les permissions
    """
    permission_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = 'role'
        self._role_id = None
        self._user_id = None
        self._checkboxes = {}

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Scroll area pour la grille
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Container pour la grille
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)

    def build_grid(self, modules: list, actions: list):
        """Construit la grille de permissions"""
        # Nettoyer
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._checkboxes = {}

        # Style des en-têtes
        header_style = """
            QLabel {
                background-color: #f1f5f9;
                color: #475569;
                font-weight: bold;
                padding: 10px 16px;
                border-radius: 6px;
                font-size: 12px;
            }
        """

        # Style des lignes
        row_style_even = "background-color: #ffffff; border-radius: 8px;"
        row_style_odd = "background-color: #f8fafc; border-radius: 8px;"

        # En-tête - Module
        header_module = QLabel("MODULE")
        header_module.setStyleSheet(header_style)
        header_module.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_module.setMinimumWidth(180)
        self.grid_layout.addWidget(header_module, 0, 0)

        # En-têtes des actions
        action_labels = {
            'lecture': 'LECTURE',
            'ecriture': 'ÉCRITURE',
            'suppression': 'SUPPRESSION'
        }

        for col, action in enumerate(actions):
            header = QLabel(action_labels.get(action, action.upper()))
            header.setStyleSheet(header_style)
            header.setAlignment(Qt.AlignCenter)
            header.setMinimumWidth(100)
            self.grid_layout.addWidget(header, 0, col + 1)

        # Lignes des modules
        for row, module_info in enumerate(modules):
            module_code = module_info['code']
            is_even = row % 2 == 0

            # Container de la ligne
            row_widget = QWidget()
            row_widget.setStyleSheet(row_style_even if is_even else row_style_odd)

            # Label du module
            module_label = QLabel(f"  {module_info['nom']}")
            module_label.setFont(QFont("Segoe UI", 10))
            module_label.setStyleSheet(f"""
                QLabel {{
                    padding: 12px 8px;
                    color: #1e293b;
                    {row_style_even if is_even else row_style_odd}
                }}
            """)
            module_label.setMinimumHeight(44)
            self.grid_layout.addWidget(module_label, row + 1, 0)

            # Toggles pour chaque action
            for col, action in enumerate(actions):
                toggle = PermissionToggle()
                toggle.set_override_mode(self._mode == 'user')
                toggle.stateChanged.connect(lambda state, m=module_code, a=action: self._on_checkbox_changed(m, a))
                self._checkboxes[(module_code, action)] = toggle

                # Container centré
                container = QWidget()
                container.setStyleSheet(row_style_even if is_even else row_style_odd)
                container_layout = QHBoxLayout(container)
                container_layout.setContentsMargins(8, 8, 8, 8)
                container_layout.setAlignment(Qt.AlignCenter)
                container_layout.addWidget(toggle)

                self.grid_layout.addWidget(container, row + 1, col + 1)

        # Stretch final
        self.grid_layout.setRowStretch(len(modules) + 1, 1)

    def load_role_permissions(self, role_id: int, modules: list, actions: list):
        from core.services.permission_service import get_role_permissions

        self._mode = 'role'
        self._role_id = role_id
        self._user_id = None

        self.build_grid(modules, actions)
        self._role_permissions = get_role_permissions(role_id)

        for (module, action), toggle in self._checkboxes.items():
            toggle.set_override_mode(False)
            perm = self._role_permissions.get(module, {})
            toggle.setChecked(perm.get(action, False))
            toggle.set_source('role')

    def load_user_permissions(self, user_id: int, role_id: int, modules: list, actions: list):
        from core.services.permission_service import get_effective_permissions

        self._mode = 'user'
        self._user_id = user_id
        self._role_id = role_id

        self.build_grid(modules, actions)
        effective = get_effective_permissions(user_id, role_id)

        for (module, action), toggle in self._checkboxes.items():
            toggle.set_override_mode(True)
            perm = effective.get(module, {})
            value = perm.get(action, False)
            source = perm.get(f'{action}_source', 'role')

            if source == 'role':
                toggle.setCheckState(Qt.PartiallyChecked)
            else:
                toggle.setChecked(value)
            toggle.set_source(source)

    def _on_checkbox_changed(self, module: str, action: str):
        self.permission_changed.emit()

    def get_permissions(self) -> dict:
        permissions = {}
        for (module, action), toggle in self._checkboxes.items():
            if module not in permissions:
                permissions[module] = {}
            if self._mode == 'user' and toggle.checkState() == Qt.PartiallyChecked:
                permissions[module][action] = None
            else:
                permissions[module][action] = toggle.isChecked()
        return permissions

    def reset_to_role(self, module: str = None):
        if self._mode != 'user':
            return
        for (m, action), toggle in self._checkboxes.items():
            if module is None or m == module:
                toggle.setCheckState(Qt.PartiallyChecked)
                toggle.set_source('role')
        self.permission_changed.emit()


class PermissionEditorDialog(QDialog):
    """Dialog pour éditer les permissions"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Permissions")
        self.setMinimumSize(750, 650)
        self.setModal(True)

        self._current_mode = 'role'
        self._current_role_id = None
        self._current_user_id = None
        self._modules = []
        self._actions = []
        self._loading = True

        self.setup_ui()
        self.load_data()
        self._loading = False

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

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
        mode_label.setFixedWidth(80)
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
            QComboBox::drop-down { border: none; padding-right: 8px; }
        """)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        selection_layout.addLayout(mode_row)

        # Rôle
        self.role_row = QHBoxLayout()
        role_label = QLabel("Rôle:")
        role_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        role_label.setStyleSheet("color: #64748b;")
        role_label.setFixedWidth(80)
        self.role_row.addWidget(role_label)

        self.role_combo = QComboBox()
        self.role_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background: white;
                min-width: 400px;
                font-size: 13px;
            }
            QComboBox:hover { border-color: #94a3b8; }
        """)
        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        self.role_row.addWidget(self.role_combo)
        self.role_row.addStretch()
        selection_layout.addLayout(self.role_row)

        # Utilisateur (caché par défaut)
        self.user_row_widget = QWidget()
        self.user_row = QHBoxLayout(self.user_row_widget)
        self.user_row.setContentsMargins(0, 0, 0, 0)
        user_label = QLabel("Utilisateur:")
        user_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        user_label.setStyleSheet("color: #64748b;")
        user_label.setFixedWidth(80)
        self.user_row.addWidget(user_label)

        self.user_combo = QComboBox()
        self.user_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background: white;
                min-width: 400px;
                font-size: 13px;
            }
        """)
        self.user_combo.currentIndexChanged.connect(self._on_user_changed)
        self.user_row.addWidget(self.user_combo)
        self.user_row.addStretch()
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

        # Grille des permissions
        self.puzzle_widget = PermissionPuzzleWidget()
        self.puzzle_widget.permission_changed.connect(self._on_permission_changed)
        layout.addWidget(self.puzzle_widget, 1)

        # Boutons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.reset_btn = QPushButton("↻ Réinitialiser au rôle")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background: white;
                color: #475569;
                font-weight: 500;
            }
            QPushButton:hover { background: #f1f5f9; border-color: #94a3b8; }
        """)
        self.reset_btn.clicked.connect(self._on_reset)
        self.reset_btn.setVisible(False)
        button_layout.addWidget(self.reset_btn)

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

        self.save_btn = QPushButton("✓ Enregistrer")
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
        from core.services.permission_service import get_all_roles, MODULES_DISPONIBLES, ACTIONS_DISPONIBLES
        from core.services.auth_service import get_all_users

        roles = get_all_roles()
        self.role_combo.clear()
        for role in roles:
            self.role_combo.addItem(role['nom'], role['id'])

        users = get_all_users()
        self.user_combo.clear()
        for user in users:
            display = f"{user['nom']} {user['prenom']} ({user['username']})"
            self.user_combo.addItem(display, {'id': user['id'], 'role_id': None})

        self._modules = MODULES_DISPONIBLES
        self._actions = ACTIONS_DISPONIBLES

        if roles:
            self._load_role_permissions()

    def _on_mode_changed(self):
        if self._loading:
            return
        mode = self.mode_combo.currentData()
        self._current_mode = mode
        self.user_row_widget.setVisible(mode == 'user')
        self.reset_btn.setVisible(mode == 'user')
        if mode == 'role':
            self._load_role_permissions()
        else:
            self._load_user_permissions()
        self.save_btn.setEnabled(False)

    def _on_role_changed(self):
        if self._loading:
            return
        if self._current_mode == 'role':
            self._load_role_permissions()
        self.save_btn.setEnabled(False)

    def _on_user_changed(self):
        if self._loading:
            return
        if self._current_mode == 'user':
            self._load_user_permissions()
        self.save_btn.setEnabled(False)

    def _load_role_permissions(self):
        role_id = self.role_combo.currentData()
        if role_id and self._modules and self._actions:
            self._current_role_id = role_id
            self.puzzle_widget.load_role_permissions(role_id, self._modules, self._actions)

    def _load_user_permissions(self):
        user_data = self.user_combo.currentData()
        if user_data and self._modules and self._actions:
            from core.services.permission_service import get_user_with_role
            user_id = user_data['id']
            user_info = get_user_with_role(user_id)
            if user_info:
                self._current_user_id = user_id
                self._current_role_id = user_info['role_id']
                self.puzzle_widget.load_user_permissions(
                    user_id, user_info['role_id'], self._modules, self._actions
                )

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
        from core.services.permission_service import save_role_permissions, save_user_permission_overrides

        permissions = self.puzzle_widget.get_permissions()

        if self._current_mode == 'role':
            success, error = save_role_permissions(self._current_role_id, permissions)
        else:
            success, error = save_user_permission_overrides(self._current_user_id, permissions)

        if success:
            QMessageBox.information(self, "Succès", "Permissions enregistrées avec succès.")
            self.save_btn.setEnabled(False)
        else:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement:\n{error}")
