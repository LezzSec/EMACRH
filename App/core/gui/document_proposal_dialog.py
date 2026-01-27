# -*- coding: utf-8 -*-
"""
Dialog de proposition de documents déclenchés par événement.

Affiche les documents en attente et permet à l'utilisateur de:
- Sélectionner ceux à générer
- Ignorer ceux non souhaités
- Voir l'événement déclencheur

Usage:
    from core.gui.document_proposal_dialog import DocumentProposalDialog

    # Afficher les documents en attente pour un opérateur
    dialog = DocumentProposalDialog(
        operateur_id=123,
        operateur_nom='Dupont',
        operateur_prenom='Jean',
        parent=self
    )

    if dialog.exec_() == QDialog.Accepted:
        print("Documents générés:", dialog.generated_paths)
"""

from typing import List, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QScrollArea, QWidget, QMessageBox, QGroupBox,
    QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from core.services.document_trigger_service import (
    DocumentTriggerService,
    PendingDocument
)
from core.services.template_service import open_template_file


class DocumentProposalDialog(QDialog):
    """
    Dialog de proposition de documents.

    Affiche les documents déclenchés par des événements récents
    et permet à l'utilisateur de choisir lesquels générer.

    Signals:
        documents_generated: Émis quand des documents sont générés (liste des chemins)
    """

    documents_generated = pyqtSignal(list)

    def __init__(
        self,
        operateur_id: int,
        operateur_nom: str,
        operateur_prenom: str,
        parent: Optional[QWidget] = None
    ):
        """
        Initialise le dialog.

        Args:
            operateur_id: ID de l'opérateur
            operateur_nom: Nom de l'opérateur
            operateur_prenom: Prénom de l'opérateur
            parent: Widget parent
        """
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.operateur_nom = operateur_nom
        self.operateur_prenom = operateur_prenom
        self.checkboxes: List[QCheckBox] = []
        self.generated_paths: List[str] = []

        self.setWindowTitle("Documents suggérés")
        self.setMinimumWidth(550)
        self.setMinimumHeight(300)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        self._init_ui()
        self._load_pending()
        self._apply_style()

    def _init_ui(self):
        """Construit l'interface utilisateur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #dbeafe;
                border-radius: 16px;
                padding: 6px;
            }
        """)
        icon_label.setText("📄")
        icon_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(icon_label)

        header_text = QVBoxLayout()
        title = QLabel(f"Documents suggérés")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        header_text.addWidget(title)

        subtitle = QLabel(f"Pour {self.operateur_prenom} {self.operateur_nom}")
        subtitle.setStyleSheet("color: #64748b; font-size: 12px;")
        header_text.addWidget(subtitle)

        header_layout.addLayout(header_text)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Info text
        info = QLabel(
            "Les documents suivants ont été déclenchés par vos actions récentes. "
            "Sélectionnez ceux que vous souhaitez générer."
        )
        info.setStyleSheet("color: #475569; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setMaximumHeight(250)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_container)
        self.checkbox_layout.setSpacing(8)
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self.checkbox_container)
        layout.addWidget(scroll)

        # Spacer
        layout.addStretch()

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_select_all = QPushButton("Tout sélectionner")
        btn_select_all.setObjectName("secondaryButton")
        btn_select_all.clicked.connect(self._toggle_all)
        btn_layout.addWidget(btn_select_all)

        btn_layout.addStretch()

        btn_ignore = QPushButton("Ignorer tout")
        btn_ignore.setObjectName("dangerButton")
        btn_ignore.clicked.connect(self._ignore_all)
        btn_layout.addWidget(btn_ignore)

        btn_generate = QPushButton("Générer les sélectionnés")
        btn_generate.setObjectName("primaryButton")
        btn_generate.clicked.connect(self._generate_selected)
        btn_layout.addWidget(btn_generate)

        layout.addLayout(btn_layout)

    def _load_pending(self):
        """Charge et affiche les documents en attente."""
        pending = DocumentTriggerService.get_pending_documents(self.operateur_id)

        if not pending:
            label = QLabel("Aucun document en attente.")
            label.setStyleSheet("color: #64748b; font-style: italic; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            self.checkbox_layout.addWidget(label)
            return

        # Grouper par événement
        events = {}
        for doc in pending:
            event_display = self._get_event_display_name(doc.event_name)
            if event_display not in events:
                events[event_display] = []
            events[event_display].append(doc)

        # Créer les groupes
        for event_name, docs in events.items():
            group = QGroupBox(event_name)
            group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    color: #334155;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(4)

            for doc in docs:
                cb = QCheckBox(doc.template_nom)
                cb.setChecked(True)
                cb.setProperty('pending_doc', doc)
                cb.setStyleSheet("""
                    QCheckBox {
                        color: #1e293b;
                        padding: 4px;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                    }
                """)
                self.checkboxes.append(cb)
                group_layout.addWidget(cb)

            self.checkbox_layout.addWidget(group)

        self.checkbox_layout.addStretch()

    def _get_event_display_name(self, event_name: str) -> str:
        """
        Convertit un nom d'événement technique en nom affichable.

        Args:
            event_name: Nom technique (ex: 'personnel.created')

        Returns:
            Nom affichable en français
        """
        display_names = {
            'personnel.created': 'Nouvel employé',
            'personnel.updated': 'Modification employé',
            'personnel.deactivated': 'Désactivation employé',
            'personnel.reactivated': 'Réactivation employé',
            'contrat.created': 'Nouveau contrat',
            'contrat.renewed': 'Renouvellement contrat',
            'contrat.expiring_soon': 'Contrat expirant',
            'polyvalence.created': 'Affectation poste',
            'polyvalence.niveau_changed': 'Changement de niveau',
            'polyvalence.niveau_3_reached': 'Passage niveau 3',
            'evaluation.completed': 'Évaluation terminée',
            'evaluation.overdue': 'Évaluation en retard',
        }
        return display_names.get(event_name, event_name)

    def _toggle_all(self):
        """Bascule la sélection de tous les checkboxes."""
        if not self.checkboxes:
            return

        all_checked = all(cb.isChecked() for cb in self.checkboxes)
        for cb in self.checkboxes:
            cb.setChecked(not all_checked)

    def _ignore_all(self):
        """Ignore tous les documents et ferme le dialog."""
        DocumentTriggerService.clear_pending(self.operateur_id)
        self.reject()

    def _generate_selected(self):
        """Génère les documents sélectionnés."""
        selected = [
            cb.property('pending_doc')
            for cb in self.checkboxes
            if cb.isChecked()
        ]

        if not selected:
            QMessageBox.information(
                self,
                "Aucune sélection",
                "Veuillez sélectionner au moins un document à générer."
            )
            return

        self.generated_paths = []
        errors = []

        for doc in selected:
            success, msg, path = DocumentTriggerService.generate_pending(doc)

            if success and path:
                open_template_file(path)
                self.generated_paths.append(path)
            else:
                errors.append(f"{doc.template_nom}: {msg}")

        # Émettre le signal avec les chemins générés
        if self.generated_paths:
            self.documents_generated.emit(self.generated_paths)

        # Afficher les erreurs s'il y en a
        if errors:
            QMessageBox.warning(
                self,
                "Erreurs de génération",
                "Certains documents n'ont pas pu être générés:\n\n" + "\n".join(errors)
            )

        # Afficher le résultat
        if self.generated_paths:
            count = len(self.generated_paths)
            QMessageBox.information(
                self,
                "Documents générés",
                f"{count} document(s) généré(s) et ouvert(s) avec succès."
            )

        self.accept()

    def _apply_style(self):
        """Applique le style au dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }

            QPushButton#primaryButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                min-width: 150px;
            }
            QPushButton#primaryButton:hover {
                background-color: #2563eb;
            }
            QPushButton#primaryButton:pressed {
                background-color: #1d4ed8;
            }

            QPushButton#secondaryButton {
                background-color: #f1f5f9;
                color: #475569;
                padding: 8px 16px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QPushButton#secondaryButton:hover {
                background-color: #e2e8f0;
            }

            QPushButton#dangerButton {
                background-color: #fef2f2;
                color: #dc2626;
                padding: 8px 16px;
                border: 1px solid #fecaca;
                border-radius: 6px;
            }
            QPushButton#dangerButton:hover {
                background-color: #fee2e2;
            }

            QScrollArea {
                background-color: transparent;
            }
        """)


def show_pending_documents_if_any(
    operateur_id: int,
    operateur_nom: str,
    operateur_prenom: str,
    parent: Optional[QWidget] = None
) -> bool:
    """
    Affiche le dialog si des documents sont en attente.

    Fonction utilitaire pour vérifier et afficher le dialog
    en une seule opération.

    Args:
        operateur_id: ID de l'opérateur
        operateur_nom: Nom de l'opérateur
        operateur_prenom: Prénom de l'opérateur
        parent: Widget parent

    Returns:
        True si le dialog a été affiché, False sinon
    """
    if not DocumentTriggerService.has_pending_documents(operateur_id):
        return False

    dialog = DocumentProposalDialog(
        operateur_id=operateur_id,
        operateur_nom=operateur_nom,
        operateur_prenom=operateur_prenom,
        parent=parent
    )
    dialog.exec_()
    return True
