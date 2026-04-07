# -*- coding: utf-8 -*-
"""
EmacDialog - Classe de base pour tous les dialogs EMAC.

Ce module fournit une classe de base standardisée pour créer des dialogs
avec une structure cohérente : layout, barre de titre, scroll area, etc.

Usage:
    from core.gui.components.emac_dialog import EmacDialog

    class MyDialog(EmacDialog):
        def __init__(self, parent=None):
            super().__init__(
                title="Mon Dialog",
                min_width=800,
                min_height=600,
                add_title_bar=True,
                parent=parent
            )

        def init_ui(self):
            # Ajouter vos widgets au self.content_layout
            label = QLabel("Mon contenu")
            self.content_layout.addWidget(label)

        def load_data(self):
            # Charger vos données
            pass
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QScrollArea, QShortcut
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt
from core.gui.components.ui_theme import EmacButton
from core.gui.components.emac_ui_kit import add_custom_title_bar
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class EmacDialog(QDialog):
    """
    Classe de base pour tous les dialogs EMAC.

    Fournit une structure standardisée :
    - Layout principal avec marges configurables
    - Barre de titre personnalisée (optionnel)
    - Zone de contenu avec scroll automatique (optionnel)
    - Boutons standard Enregistrer/Annuler (optionnel)

    Attributs:
        main_layout: Layout principal du dialog (QVBoxLayout)
        content_widget: Widget contenant le contenu
        content_layout: Layout du contenu (à utiliser dans init_ui)
        title_bar: Barre de titre personnalisée (si add_title_bar=True)
    """

    def __init__(
        self,
        title: str,
        min_width: int = 700,
        min_height: int = 600,
        add_title_bar: bool = False,
        add_scroll_area: bool = False,
        add_buttons: bool = False,
        parent=None
    ):
        """
        Initialise le dialog avec la structure standard.

        Args:
            title: Titre de la fenêtre
            min_width: Largeur minimale (défaut: 700)
            min_height: Hauteur minimale (défaut: 600)
            add_title_bar: Ajouter une barre de titre personnalisée (défaut: False)
            add_scroll_area: Envelopper le contenu dans un QScrollArea (défaut: False)
            add_buttons: Ajouter des boutons Enregistrer/Annuler en bas (défaut: False)
            parent: Widget parent
        """
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setMinimumWidth(min_width)
        self.setMinimumHeight(min_height)

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Barre de titre personnalisée (optionnel)
        self.title_bar = None
        if add_title_bar:
            self.title_bar = add_custom_title_bar(self, title)
            self.main_layout.addWidget(self.title_bar)

        # Widget de contenu
        if add_scroll_area:
            self._setup_with_scroll_area()
        else:
            self._setup_without_scroll_area()

        # Boutons standard (optionnel)
        self.save_button = None
        self.cancel_button = None
        if add_buttons:
            self._setup_buttons()

        # Raccourcis clavier communs
        QShortcut(QKeySequence(Qt.Key_Escape), self).activated.connect(self.close)

        # Appeler les méthodes de sous-classe
        self.init_ui()
        self.load_data()

    def _setup_without_scroll_area(self):
        """Configure le layout sans scroll area."""
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(16)
        self.main_layout.addWidget(self.content_widget)

    def _setup_with_scroll_area(self):
        """Configure le layout avec scroll area."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(16)

        scroll.setWidget(self.content_widget)
        self.main_layout.addWidget(scroll)

    def _setup_buttons(self):
        """Ajoute les boutons Enregistrer/Annuler en bas."""
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(16, 8, 16, 16)
        button_layout.setSpacing(12)

        button_layout.addStretch()

        self.save_button = EmacButton("Enregistrer", 'primary')
        self.save_button.clicked.connect(self.on_save)
        self.save_button.setToolTip("Enregistrer (Ctrl+Entrée)")

        self.cancel_button = EmacButton("Annuler", 'ghost')
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setToolTip("Annuler (Échap)")

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        self.main_layout.addWidget(button_widget)

    def init_ui(self):
        """
        Initialise l'interface utilisateur.

        À surcharger dans les sous-classes pour ajouter des widgets
        au self.content_layout.

        Example:
            def init_ui(self):
                label = QLabel("Mon label")
                self.content_layout.addWidget(label)
        """
        pass

    def load_data(self):
        """
        Charge les données initiales.

        À surcharger dans les sous-classes pour charger les données
        depuis la base de données ou d'autres sources.

        Example:
            def load_data(self):
                self.personnel = QueryExecutor.fetch_all("SELECT ...")
        """
        pass

    def on_save(self):
        """
        Gestionnaire du bouton Enregistrer.

        À surcharger dans les sous-classes. Par défaut, accepte le dialog.

        Example:
            def on_save(self):
                # Validation
                if not self.validate():
                    return

                # Sauvegarde
                self.save_to_db()
                self.accept()
        """
        self.accept()


class EmacFormDialog(EmacDialog):
    """
    Dialog de formulaire avec scroll area et boutons par défaut.

    Spécialisé pour les formulaires de saisie/édition.
    """

    def __init__(
        self,
        title: str,
        min_width: int = 700,
        min_height: int = 600,
        add_title_bar: bool = True,
        parent=None
    ):
        super().__init__(
            title=title,
            min_width=min_width,
            min_height=min_height,
            add_title_bar=add_title_bar,
            add_scroll_area=True,
            add_buttons=True,
            parent=parent
        )
        # Ctrl+Entrée pour sauvegarder
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.on_save)

    def validate(self) -> tuple:
        """
        Valide les données du formulaire.

        À surcharger dans les sous-classes.

        Returns:
            (success: bool, error_message: str)

        Example:
            def validate(self):
                if not self.name_input.text():
                    return False, "Le nom est obligatoire"
                return True, ""
        """
        return True, ""

    def save_to_db(self):
        """
        Sauvegarde les données dans la base de données.

        À surcharger dans les sous-classes.

        Example:
            def save_to_db(self):
                QueryExecutor.execute_write(
                    "INSERT INTO personnel (...) VALUES (...)",
                    (self.name, self.prenom, ...)
                )
        """
        pass

    def on_save(self):
        """Gestionnaire du bouton Enregistrer avec validation."""
        from core.gui.components.emac_ui_kit import show_error_message

        # Validation
        valid, error_msg = self.validate()
        if not valid:
            show_error_message(self, "Validation", error_msg)
            return

        # Sauvegarde
        try:
            self.save_to_db()
            self.accept()
        except Exception as e:
            logger.exception(f"Erreur sauvegarde: {e}")
            show_error_message(self, "Erreur", "Impossible de sauvegarder", e)


class EmacTableDialog(EmacDialog):
    """
    Dialog avec table et boutons d'action.

    Spécialisé pour l'affichage de listes/tables avec actions.
    """

    def __init__(
        self,
        title: str,
        min_width: int = 900,
        min_height: int = 600,
        add_title_bar: bool = True,
        parent=None
    ):
        super().__init__(
            title=title,
            min_width=min_width,
            min_height=min_height,
            add_title_bar=add_title_bar,
            add_scroll_area=False,
            add_buttons=False,
            parent=parent
        )
