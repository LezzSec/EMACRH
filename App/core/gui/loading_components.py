# -*- coding: utf-8 -*-
"""
Composants UI de chargement réutilisables pour EMAC.
Fournit des placeholders, spinners, et indicateurs de progression.
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer


# ===========================
# Loading Label (simple)
# ===========================

class LoadingLabel(QLabel):
    """
    Label de chargement simple avec animation de points.

    Usage:
        loading = LoadingLabel("Chargement des données")
        layout.addWidget(loading)
        # ... chargement ...
        loading.stop()
        loading.setText("Données chargées ✅")
    """

    def __init__(self, text: str = "Chargement", parent=None):
        super().__init__(parent)
        self.base_text = text
        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_dots)
        self.setStyleSheet("color: #999; font-style: italic;")
        self.start()

    def start(self):
        """Démarre l'animation"""
        self._dots = 0
        self._timer.start(500)  # Mise à jour toutes les 500ms
        self._update_dots()

    def stop(self):
        """Arrête l'animation"""
        self._timer.stop()

    def _update_dots(self):
        """Met à jour les points d'animation"""
        self._dots = (self._dots + 1) % 4
        dots = "." * self._dots
        self.setText(f"⏳ {self.base_text}{dots}")


# ===========================
# Loading Placeholder (widget complet)
# ===========================

class LoadingPlaceholder(QWidget):
    """
    Widget de placeholder de chargement avec icône et texte.

    Usage:
        placeholder = LoadingPlaceholder("Chargement du personnel")
        layout.addWidget(placeholder)
    """

    def __init__(self, text: str = "Chargement", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        # Icône/emoji
        icon_label = QLabel("⏳")
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Texte
        self.text_label = LoadingLabel(text)
        self.text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.text_label)

        self.setStyleSheet("""
            LoadingPlaceholder {
                background: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 24px;
            }
        """)

    def set_text(self, text: str):
        """Change le texte"""
        self.text_label.base_text = text
        self.text_label._update_dots()


# ===========================
# Empty State Placeholder
# ===========================

class EmptyStatePlaceholder(QWidget):
    """
    Widget pour afficher un état vide (pas de données).

    Usage:
        empty = EmptyStatePlaceholder(
            icon="📭",
            title="Aucune évaluation",
            subtitle="Toutes les évaluations sont à jour"
        )
    """

    def __init__(self, icon: str = "📋", title: str = "Aucune donnée",
                 subtitle: str = "", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        # Icône
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #666;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Sous-titre
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("font-size: 13px; color: #999;")
            subtitle_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(subtitle_label)

        self.setStyleSheet("""
            EmptyStatePlaceholder {
                background: #fafafa;
                border: 1px dashed #ddd;
                border-radius: 8px;
                padding: 32px;
            }
        """)


# ===========================
# Error Placeholder
# ===========================

class ErrorPlaceholder(QWidget):
    """
    Widget pour afficher une erreur de chargement.

    Usage:
        error = ErrorPlaceholder(
            title="Erreur de chargement",
            message="Impossible de se connecter à la base de données"
        )
    """

    def __init__(self, title: str = "Erreur", message: str = "",
                 show_retry: bool = False, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        # Icône
        icon_label = QLabel("❌")
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Message
        if message:
            msg_label = QLabel(message)
            msg_label.setStyleSheet("font-size: 13px; color: #666;")
            msg_label.setAlignment(Qt.AlignCenter)
            msg_label.setWordWrap(True)
            layout.addWidget(msg_label)

        self.setStyleSheet("""
            ErrorPlaceholder {
                background: #ffebee;
                border: 1px solid #ffcdd2;
                border-radius: 8px;
                padding: 24px;
            }
        """)


# ===========================
# Progress Widget
# ===========================

class ProgressWidget(QWidget):
    """
    Widget de progression avec barre et pourcentage.

    Usage:
        progress = ProgressWidget("Import des données")
        layout.addWidget(progress)
        progress.set_progress(50, "50 éléments sur 100")
    """

    def __init__(self, title: str = "Chargement", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Titre
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                background: #f5f5f5;
                height: 24px;
            }
            QProgressBar::chunk {
                background: #1976d2;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Message de statut
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(self.status_label)

    def set_progress(self, percentage: int, status: str = ""):
        """
        Met à jour la progression.

        Args:
            percentage: Pourcentage (0-100)
            status: Message de statut optionnel
        """
        self.progress_bar.setValue(percentage)
        if status:
            self.status_label.setText(status)

    def set_title(self, title: str):
        """Change le titre"""
        self.title_label.setText(title)


# ===========================
# Skeleton Loader (effet de shimmer)
# ===========================

class SkeletonLoader(QWidget):
    """
    Widget "skeleton" pour simuler du contenu en cours de chargement.
    Utile pour afficher des placeholders de lignes/cartes.

    Usage:
        skeleton = SkeletonLoader(lines=5)
        layout.addWidget(skeleton)
    """

    def __init__(self, lines: int = 3, line_height: int = 40, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        for i in range(lines):
            line = QFrame()
            line.setFixedHeight(line_height)
            line.setStyleSheet("""
                QFrame {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #f0f0f0,
                        stop:0.5 #e0e0e0,
                        stop:1 #f0f0f0
                    );
                    border-radius: 4px;
                }
            """)
            layout.addWidget(line)

        # Animation de "shimmer" (optionnel, nécessite plus de code)
        # Pour l'instant, c'est un placeholder statique


# ===========================
# Helper functions
# ===========================

def replace_widget_with_loading(layout, old_widget, loading_text: str = "Chargement"):
    """
    Remplace un widget par un placeholder de chargement.

    Args:
        layout: Le layout contenant le widget
        old_widget: Le widget à remplacer
        loading_text: Texte du placeholder

    Returns:
        Le nouveau LoadingPlaceholder

    Example:
        # Avant chargement
        loading = replace_widget_with_loading(layout, my_table, "Chargement des données")

        # Après chargement
        replace_widget_with_content(layout, loading, my_table)
    """
    index = layout.indexOf(old_widget)
    if index >= 0:
        old_widget.setParent(None)
        placeholder = LoadingPlaceholder(loading_text)
        layout.insertWidget(index, placeholder)
        return placeholder
    return None


def replace_widget_with_content(layout, placeholder, new_widget):
    """
    Remplace un placeholder par le widget de contenu.

    Args:
        layout: Le layout contenant le placeholder
        placeholder: Le placeholder à remplacer
        new_widget: Le nouveau widget à afficher
    """
    index = layout.indexOf(placeholder)
    if index >= 0:
        placeholder.setParent(None)
        layout.insertWidget(index, new_widget)


def replace_widget_with_error(layout, old_widget, error_msg: str):
    """
    Remplace un widget par un placeholder d'erreur.

    Args:
        layout: Le layout contenant le widget
        old_widget: Le widget à remplacer
        error_msg: Message d'erreur

    Returns:
        Le nouveau ErrorPlaceholder
    """
    index = layout.indexOf(old_widget)
    if index >= 0:
        old_widget.setParent(None)
        error = ErrorPlaceholder("Erreur de chargement", error_msg)
        layout.insertWidget(index, error)
        return error
    return None


def replace_widget_with_empty_state(layout, old_widget, icon: str, title: str, subtitle: str = ""):
    """
    Remplace un widget par un état vide.

    Args:
        layout: Le layout contenant le widget
        old_widget: Le widget à remplacer
        icon: Icône/emoji
        title: Titre
        subtitle: Sous-titre optionnel

    Returns:
        Le nouveau EmptyStatePlaceholder
    """
    index = layout.indexOf(old_widget)
    if index >= 0:
        old_widget.setParent(None)
        empty = EmptyStatePlaceholder(icon, title, subtitle)
        layout.insertWidget(index, empty)
        return empty
    return None
