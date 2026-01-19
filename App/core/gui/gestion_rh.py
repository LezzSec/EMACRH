# -*- coding: utf-8 -*-
"""
Écran RH Opérateur & Documents
Permet de consulter et gérer les données RH d'un opérateur par domaine.

Structure:
- Zone gauche: Recherche et sélection d'opérateur
- Zone droite: Navigation par domaines RH + résumé + documents
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QWidget, QFrame, QScrollArea,
    QStackedWidget, QSizePolicy, QSpacerItem, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QFormLayout, QDateEdit, QComboBox, QTextEdit,
    QDoubleSpinBox, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor

from core.gui.ui_theme import EmacTheme, EmacCard, EmacButton
from core.gui.emac_ui_kit import EmacBadge, EmacAlert, EmacChip, add_custom_title_bar
from core.services.rh_service import (
    rechercher_operateurs,
    get_operateur_by_id,
    get_donnees_domaine,
    get_documents_domaine,
    get_resume_operateur,
    get_domaines_rh,
    DomaineRH,
    update_infos_generales,
    create_contrat, update_contrat, delete_contrat,
    create_declaration, update_declaration, delete_declaration,
    create_formation, update_formation, delete_formation,
    get_types_declaration
)


# ============================================================
# FORMULAIRES D'ÉDITION
# ============================================================

class EditInfosGeneralesDialog(QDialog):
    """Formulaire d'édition des informations générales."""

    def __init__(self, operateur_id: int, donnees: dict, parent=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.donnees = donnees
        self.setWindowTitle("Modifier les informations générales")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        # Sexe
        self.sexe_combo = QComboBox()
        self.sexe_combo.addItems(['', 'M', 'F'])
        if self.donnees.get('sexe'):
            idx = self.sexe_combo.findText(self.donnees['sexe'])
            if idx >= 0:
                self.sexe_combo.setCurrentIndex(idx)
        form.addRow("Sexe:", self.sexe_combo)

        # Date de naissance
        self.date_naissance = QDateEdit()
        self.date_naissance.setCalendarPopup(True)
        self.date_naissance.setDisplayFormat("dd/MM/yyyy")
        self.date_naissance.setSpecialValueText("Non renseignée")
        if self.donnees.get('date_naissance'):
            d = self.donnees['date_naissance']
            self.date_naissance.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de naissance:", self.date_naissance)

        # Date d'entrée
        self.date_entree = QDateEdit()
        self.date_entree.setCalendarPopup(True)
        self.date_entree.setDisplayFormat("dd/MM/yyyy")
        self.date_entree.setSpecialValueText("Non renseignée")
        if self.donnees.get('date_entree'):
            d = self.donnees['date_entree']
            self.date_entree.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date d'entrée:", self.date_entree)

        # Nationalité
        self.nationalite = QLineEdit(self.donnees.get('nationalite') or '')
        form.addRow("Nationalité:", self.nationalite)

        # Adresse
        self.adresse1 = QLineEdit(self.donnees.get('adresse1') or '')
        form.addRow("Adresse:", self.adresse1)

        self.adresse2 = QLineEdit(self.donnees.get('adresse2') or '')
        form.addRow("Adresse (suite):", self.adresse2)

        # CP + Ville
        cp_ville = QHBoxLayout()
        self.cp = QLineEdit(self.donnees.get('cp_adresse') or '')
        self.cp.setMaximumWidth(80)
        self.ville = QLineEdit(self.donnees.get('ville_adresse') or '')
        cp_ville.addWidget(self.cp)
        cp_ville.addWidget(self.ville)
        form.addRow("CP / Ville:", cp_ville)

        # Téléphone
        self.telephone = QLineEdit(self.donnees.get('telephone') or '')
        form.addRow("Téléphone:", self.telephone)

        # Email
        self.email = QLineEdit(self.donnees.get('email') or '')
        form.addRow("Email:", self.email)

        layout.addLayout(form)

        # Boutons
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = EmacButton("Annuler", variant="ghost")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = EmacButton("Enregistrer", variant="primary")
        btn_save.clicked.connect(self._save)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def _save(self):
        data = {
            'sexe': self.sexe_combo.currentText() or None,
            'date_naissance': self.date_naissance.date().toPyDate() if self.date_naissance.date().year() > 1900 else None,
            'date_entree': self.date_entree.date().toPyDate() if self.date_entree.date().year() > 1900 else None,
            'nationalite': self.nationalite.text().strip(),
            'adresse1': self.adresse1.text().strip(),
            'adresse2': self.adresse2.text().strip(),
            'cp_adresse': self.cp.text().strip(),
            'ville_adresse': self.ville.text().strip(),
            'telephone': self.telephone.text().strip(),
            'email': self.email.text().strip(),
        }

        success, message = update_infos_generales(self.operateur_id, data)
        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", message)


class EditContratDialog(QDialog):
    """Formulaire d'édition/création de contrat."""

    def __init__(self, operateur_id: int, contrat: dict = None, parent=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.contrat = contrat
        self.is_edit = contrat is not None
        self.setWindowTitle("Modifier le contrat" if self.is_edit else "Nouveau contrat")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        # Type de contrat
        self.type_combo = QComboBox()
        self.type_combo.addItems(['CDI', 'CDD', 'Intérimaire', 'Apprentissage', 'Stagiaire'])
        if self.contrat and self.contrat.get('type_contrat'):
            idx = self.type_combo.findText(self.contrat['type_contrat'])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        form.addRow("Type de contrat:", self.type_combo)

        # Date début
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setDate(QDate.currentDate())
        if self.contrat and self.contrat.get('date_debut'):
            d = self.contrat['date_debut']
            self.date_debut.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de début:", self.date_debut)

        # Date fin
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setSpecialValueText("Indéterminée (CDI)")
        self.date_fin.setMinimumDate(QDate(1900, 1, 1))
        if self.contrat and self.contrat.get('date_fin'):
            d = self.contrat['date_fin']
            self.date_fin.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_fin.setDate(QDate(1900, 1, 1))
        form.addRow("Date de fin:", self.date_fin)

        # ETP
        self.etp = QDoubleSpinBox()
        self.etp.setRange(0.01, 1.0)
        self.etp.setSingleStep(0.1)
        self.etp.setValue(float(self.contrat.get('etp', 1.0)) if self.contrat else 1.0)
        form.addRow("ETP:", self.etp)

        # Catégorie
        self.categorie = QLineEdit(self.contrat.get('categorie', '') if self.contrat else '')
        form.addRow("Catégorie:", self.categorie)

        # Emploi
        self.emploi = QLineEdit(self.contrat.get('emploi', '') if self.contrat else '')
        form.addRow("Emploi:", self.emploi)

        # Salaire
        self.salaire = QDoubleSpinBox()
        self.salaire.setRange(0, 999999.99)
        self.salaire.setSuffix(" €")
        if self.contrat and self.contrat.get('salaire'):
            self.salaire.setValue(float(self.contrat['salaire']))
        form.addRow("Salaire brut:", self.salaire)

        layout.addLayout(form)

        # Boutons
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = EmacButton("Annuler", variant="ghost")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = EmacButton("Enregistrer", variant="primary")
        btn_save.clicked.connect(self._save)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def _save(self):
        date_fin = self.date_fin.date()
        data = {
            'type_contrat': self.type_combo.currentText(),
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': date_fin.toPyDate() if date_fin.year() > 1900 else None,
            'etp': self.etp.value(),
            'categorie': self.categorie.text().strip() or None,
            'emploi': self.emploi.text().strip() or None,
            'salaire': self.salaire.value() if self.salaire.value() > 0 else None,
        }

        if self.is_edit:
            success, message = update_contrat(self.contrat['id'], data)
        else:
            success, message, _ = create_contrat(self.operateur_id, data)

        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", message)


class EditDeclarationDialog(QDialog):
    """Formulaire d'édition/création de déclaration."""

    def __init__(self, operateur_id: int, declaration: dict = None, parent=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.declaration = declaration
        self.is_edit = declaration is not None
        self.setWindowTitle("Modifier la déclaration" if self.is_edit else "Nouvelle déclaration")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(get_types_declaration())
        if self.declaration and self.declaration.get('type_declaration'):
            idx = self.type_combo.findText(self.declaration['type_declaration'])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        form.addRow("Type:", self.type_combo)

        # Date début
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setDate(QDate.currentDate())
        if self.declaration and self.declaration.get('date_debut'):
            d = self.declaration['date_debut']
            self.date_debut.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de début:", self.date_debut)

        # Date fin
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setDate(QDate.currentDate())
        if self.declaration and self.declaration.get('date_fin'):
            d = self.declaration['date_fin']
            self.date_fin.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de fin:", self.date_fin)

        # Motif
        self.motif = QTextEdit()
        self.motif.setMaximumHeight(80)
        if self.declaration and self.declaration.get('motif'):
            self.motif.setText(self.declaration['motif'])
        form.addRow("Motif:", self.motif)

        layout.addLayout(form)

        # Boutons
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = EmacButton("Annuler", variant="ghost")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = EmacButton("Enregistrer", variant="primary")
        btn_save.clicked.connect(self._save)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def _save(self):
        data = {
            'type_declaration': self.type_combo.currentText(),
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': self.date_fin.date().toPyDate(),
            'motif': self.motif.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_declaration(self.declaration['id'], data)
        else:
            success, message, _ = create_declaration(self.operateur_id, data)

        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", message)


class EditFormationDialog(QDialog):
    """Formulaire d'édition/création de formation."""

    def __init__(self, operateur_id: int, formation: dict = None, parent=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.formation = formation
        self.is_edit = formation is not None
        self.setWindowTitle("Modifier la formation" if self.is_edit else "Nouvelle formation")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        # Intitulé
        self.intitule = QLineEdit(self.formation.get('intitule', '') if self.formation else '')
        form.addRow("Intitulé:", self.intitule)

        # Organisme
        self.organisme = QLineEdit(self.formation.get('organisme', '') if self.formation else '')
        form.addRow("Organisme:", self.organisme)

        # Date début
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setDate(QDate.currentDate())
        if self.formation and self.formation.get('date_debut'):
            d = self.formation['date_debut']
            self.date_debut.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de début:", self.date_debut)

        # Date fin
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setSpecialValueText("Non définie")
        self.date_fin.setMinimumDate(QDate(1900, 1, 1))
        if self.formation and self.formation.get('date_fin'):
            d = self.formation['date_fin']
            self.date_fin.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_fin.setDate(QDate(1900, 1, 1))
        form.addRow("Date de fin:", self.date_fin)

        # Durée
        self.duree = QDoubleSpinBox()
        self.duree.setRange(0, 9999)
        self.duree.setSuffix(" h")
        if self.formation and self.formation.get('duree_heures'):
            self.duree.setValue(float(self.formation['duree_heures']))
        form.addRow("Durée:", self.duree)

        # Statut
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(['Planifiée', 'En cours', 'Terminée', 'Annulée'])
        if self.formation and self.formation.get('statut'):
            idx = self.statut_combo.findText(self.formation['statut'])
            if idx >= 0:
                self.statut_combo.setCurrentIndex(idx)
        form.addRow("Statut:", self.statut_combo)

        # Certificat
        self.certificat = QCheckBox("Certificat obtenu")
        if self.formation and self.formation.get('certificat_obtenu'):
            self.certificat.setChecked(True)
        form.addRow("", self.certificat)

        # Commentaire
        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(80)
        if self.formation and self.formation.get('commentaire'):
            self.commentaire.setText(self.formation['commentaire'])
        form.addRow("Commentaire:", self.commentaire)

        layout.addLayout(form)

        # Boutons
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = EmacButton("Annuler", variant="ghost")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = EmacButton("Enregistrer", variant="primary")
        btn_save.clicked.connect(self._save)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def _save(self):
        if not self.intitule.text().strip():
            QMessageBox.warning(self, "Attention", "L'intitulé est obligatoire")
            return

        date_fin = self.date_fin.date()
        data = {
            'intitule': self.intitule.text().strip(),
            'organisme': self.organisme.text().strip() or None,
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': date_fin.toPyDate() if date_fin.year() > 1900 else None,
            'duree_heures': self.duree.value() if self.duree.value() > 0 else None,
            'statut': self.statut_combo.currentText(),
            'certificat_obtenu': self.certificat.isChecked(),
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_formation(self.formation['id'], data)
        else:
            success, message, _ = create_formation(self.operateur_id, data)

        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", message)


class GestionRHDialog(QDialog):
    """
    Fenêtre principale de gestion RH.
    Divisée en deux zones: sélection opérateur (gauche) et détails RH (droite).
    """

    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion RH")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        # État
        self.operateur_selectionne = None
        self.domaine_actif = DomaineRH.GENERAL
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._executer_recherche)

        self._setup_ui()

    def _setup_ui(self):
        """Construit l'interface utilisateur."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre
        title_bar = add_custom_title_bar(self, "Gestion RH")
        main_layout.addWidget(title_bar)

        # Contenu principal
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Zone gauche: Sélection opérateur
        self.zone_gauche = self._creer_zone_selection()
        content_layout.addWidget(self.zone_gauche)

        # Séparateur vertical
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #e5e7eb;")
        separator.setFixedWidth(1)
        content_layout.addWidget(separator)

        # Zone droite: Détails RH
        self.zone_droite = self._creer_zone_details()
        content_layout.addWidget(self.zone_droite, 1)

        main_layout.addWidget(content, 1)

        # Boutons de bas de page
        footer = self._creer_footer()
        main_layout.addWidget(footer)

    # =========================================================================
    # ZONE GAUCHE - Sélection opérateur
    # =========================================================================

    def _creer_zone_selection(self) -> QWidget:
        """Crée la zone de recherche et sélection d'opérateur."""
        zone = QWidget()
        zone.setFixedWidth(320)
        zone.setStyleSheet("background-color: #f8fafc;")

        layout = QVBoxLayout(zone)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Titre
        titre = QLabel("Sélection Opérateur")
        titre.setFont(QFont("Segoe UI", 14, QFont.Bold))
        titre.setStyleSheet("color: #111827;")
        layout.addWidget(titre)

        # Champ de recherche
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)

        # Label
        search_label = QLabel("Rechercher par nom, prénom ou matricule")
        search_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        search_layout.addWidget(search_label)

        # Input de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tapez pour rechercher...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)

        layout.addWidget(search_container)

        # Liste des résultats
        results_label = QLabel("Résultats")
        results_label.setStyleSheet("color: #374151; font-weight: 600; margin-top: 8px;")
        layout.addWidget(results_label)

        self.liste_operateurs = QListWidget()
        self.liste_operateurs.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: white;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f3f4f6;
            }
            QListWidget::item:selected {
                background-color: #eff6ff;
                color: #1e40af;
            }
            QListWidget::item:hover {
                background-color: #f9fafb;
            }
        """)
        self.liste_operateurs.itemClicked.connect(self._on_operateur_selectionne)
        layout.addWidget(self.liste_operateurs, 1)

        # Compteur de résultats
        self.compteur_resultats = QLabel("0 opérateur(s)")
        self.compteur_resultats.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(self.compteur_resultats)

        # Charger les opérateurs actifs par défaut
        QTimer.singleShot(100, lambda: self._executer_recherche())

        return zone

    def _on_search_changed(self, text: str):
        """Déclenche une recherche avec délai (debounce)."""
        self._search_timer.stop()
        self._search_timer.start(300)  # 300ms de délai

    def _executer_recherche(self):
        """Exécute la recherche d'opérateurs."""
        recherche = self.search_input.text().strip()
        resultats = rechercher_operateurs(recherche=recherche if recherche else None)

        self.liste_operateurs.clear()
        for op in resultats:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, op['id'])

            # Texte formaté
            nom_complet = op.get('nom_complet', f"{op.get('prenom', '')} {op.get('nom', '')}")
            matricule = op.get('matricule', '-')
            statut = op.get('statut', 'ACTIF')

            item.setText(f"{nom_complet}\n{matricule}")
            item.setToolTip(f"ID: {op['id']} | Statut: {statut}")

            self.liste_operateurs.addItem(item)

        self.compteur_resultats.setText(f"{len(resultats)} opérateur(s)")

    def _on_operateur_selectionne(self, item: QListWidgetItem):
        """Appelé quand un opérateur est sélectionné dans la liste."""
        operateur_id = item.data(Qt.UserRole)
        self.operateur_selectionne = get_operateur_by_id(operateur_id)

        if self.operateur_selectionne:
            self._afficher_details_operateur()

    # =========================================================================
    # ZONE DROITE - Détails RH
    # =========================================================================

    def _creer_zone_details(self) -> QWidget:
        """Crée la zone d'affichage des détails RH."""
        zone = QWidget()
        layout = QVBoxLayout(zone)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stack pour basculer entre placeholder et contenu
        self.stack_details = QStackedWidget()

        # Page 0: Placeholder (aucun opérateur sélectionné)
        self.placeholder = self._creer_placeholder()
        self.stack_details.addWidget(self.placeholder)

        # Page 1: Contenu RH
        self.contenu_rh = self._creer_contenu_rh()
        self.stack_details.addWidget(self.contenu_rh)

        layout.addWidget(self.stack_details)

        return zone

    def _creer_placeholder(self) -> QWidget:
        """Crée le placeholder affiché quand aucun opérateur n'est sélectionné."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        # Icône
        icon = QLabel("👤")
        icon.setFont(QFont("Segoe UI", 48))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        # Message
        message = QLabel("Sélectionnez un opérateur")
        message.setFont(QFont("Segoe UI", 18, QFont.Bold))
        message.setStyleSheet("color: #6b7280;")
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)

        # Sous-message
        sous_message = QLabel("Utilisez la zone de recherche à gauche\npour trouver un opérateur")
        sous_message.setStyleSheet("color: #9ca3af;")
        sous_message.setAlignment(Qt.AlignCenter)
        layout.addWidget(sous_message)

        return widget

    def _creer_contenu_rh(self) -> QWidget:
        """Crée le contenu RH (affiché quand un opérateur est sélectionné)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # En-tête avec infos opérateur
        self.header_operateur = self._creer_header_operateur()
        layout.addWidget(self.header_operateur)

        # Barre de navigation des domaines RH
        self.nav_domaines = self._creer_navigation_domaines()
        layout.addWidget(self.nav_domaines)

        # Zone de contenu scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Container pour résumé + documents
        self.container_domaine = QWidget()
        self.layout_domaine = QVBoxLayout(self.container_domaine)
        self.layout_domaine.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.setSpacing(16)

        # Zone résumé des données
        self.zone_resume = QWidget()
        self.layout_resume = QVBoxLayout(self.zone_resume)
        self.layout_resume.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.addWidget(self.zone_resume)

        # Zone documents
        self.zone_documents = QWidget()
        self.layout_documents = QVBoxLayout(self.zone_documents)
        self.layout_documents.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.addWidget(self.zone_documents)

        # Spacer
        self.layout_domaine.addStretch()

        scroll.setWidget(self.container_domaine)
        layout.addWidget(scroll, 1)

        return widget

    def _creer_header_operateur(self) -> QWidget:
        """Crée l'en-tête compact avec les infos de l'opérateur sélectionné."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: #1e40af;
                border-radius: 8px;
            }
        """)
        header.setFixedHeight(50)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)

        # Nom
        self.label_nom_operateur = QLabel("Nom Prénom")
        self.label_nom_operateur.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.label_nom_operateur.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(self.label_nom_operateur)

        # Séparateur
        sep = QLabel("•")
        sep.setStyleSheet("color: #93c5fd; background: transparent; margin: 0 8px;")
        layout.addWidget(sep)

        # Matricule
        self.label_matricule = QLabel("-")
        self.label_matricule.setStyleSheet("color: #bfdbfe; background: transparent; font-size: 13px;")
        layout.addWidget(self.label_matricule)

        layout.addStretch()

        # Badge statut
        self.badge_statut = QLabel("ACTIF")
        self.badge_statut.setStyleSheet("""
            background: #10b981;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 11px;
        """)
        layout.addWidget(self.badge_statut)

        return header

    def _creer_navigation_domaines(self) -> QWidget:
        """Crée la barre de navigation entre les domaines RH."""
        nav = QWidget()
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.boutons_domaines = {}
        domaines = get_domaines_rh()

        for domaine in domaines:
            btn = QPushButton(domaine['nom'])
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty('domaine', domaine['code'])
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 16px;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    background: white;
                    color: #374151;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: #f9fafb;
                    border-color: #d1d5db;
                }
                QPushButton:checked {
                    background: #1e40af;
                    color: white;
                    border-color: #1e40af;
                }
            """)
            btn.clicked.connect(lambda checked, d=domaine['code']: self._on_domaine_change(d))
            layout.addWidget(btn)
            self.boutons_domaines[domaine['code']] = btn

        layout.addStretch()

        return nav

    def _on_domaine_change(self, code_domaine: str):
        """Appelé quand l'utilisateur change de domaine RH."""
        # Mettre à jour l'état des boutons
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == code_domaine)

        # Mettre à jour le domaine actif
        self.domaine_actif = DomaineRH(code_domaine)

        # Recharger le contenu
        if self.operateur_selectionne:
            self._charger_contenu_domaine()

    def _afficher_details_operateur(self):
        """Affiche les détails de l'opérateur sélectionné."""
        if not self.operateur_selectionne:
            return

        op = self.operateur_selectionne

        # Mettre à jour l'en-tête
        nom_complet = op.get('nom_complet', f"{op.get('prenom', '')} {op.get('nom', '')}")
        self.label_nom_operateur.setText(nom_complet)
        self.label_matricule.setText(op.get('matricule', '-'))

        # Badge statut
        statut = op.get('statut', 'ACTIF')
        if statut == 'ACTIF':
            self.badge_statut.setText("ACTIF")
            self.badge_statut.setStyleSheet("""
                background: #10b981;
                color: white;
                padding: 6px 12px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            """)
        else:
            self.badge_statut.setText("INACTIF")
            self.badge_statut.setStyleSheet("""
                background: #6b7280;
                color: white;
                padding: 6px 12px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            """)

        # Activer le premier domaine par défaut
        self.domaine_actif = DomaineRH.GENERAL
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == DomaineRH.GENERAL.value)

        # Charger le contenu du domaine
        self._charger_contenu_domaine()

        # Afficher la zone de contenu
        self.stack_details.setCurrentIndex(1)

    def _charger_contenu_domaine(self):
        """Charge le contenu du domaine RH actif."""
        if not self.operateur_selectionne:
            return

        operateur_id = self.operateur_selectionne['id']

        # Vider les zones
        self._vider_layout(self.layout_resume)
        self._vider_layout(self.layout_documents)

        # Charger les données du domaine
        donnees = get_donnees_domaine(operateur_id, self.domaine_actif)

        # Créer la zone de résumé selon le domaine
        widget_resume = self._creer_widget_resume(donnees)
        if widget_resume:
            self.layout_resume.addWidget(widget_resume)

        # Charger les documents du domaine
        documents = get_documents_domaine(operateur_id, self.domaine_actif)
        widget_documents = self._creer_widget_documents(documents)
        self.layout_documents.addWidget(widget_documents)

    def _creer_widget_resume(self, donnees: dict) -> QWidget:
        """Crée le widget de résumé selon le domaine actif."""
        if self.domaine_actif == DomaineRH.GENERAL:
            return self._creer_resume_general(donnees)
        elif self.domaine_actif == DomaineRH.CONTRAT:
            return self._creer_resume_contrat(donnees)
        elif self.domaine_actif == DomaineRH.DECLARATION:
            return self._creer_resume_declaration(donnees)
        elif self.domaine_actif == DomaineRH.COMPETENCES:
            return self._creer_resume_competences(donnees)
        elif self.domaine_actif == DomaineRH.FORMATION:
            return self._creer_resume_formation(donnees)
        return None

    def _creer_resume_general(self, donnees: dict) -> QWidget:
        """Crée le résumé des données générales."""
        self._donnees_generales = donnees  # Stocker pour édition

        card = EmacCard("Informations Générales")

        if donnees.get('error'):
            card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            return card

        # Bouton modifier en haut à droite
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        btn_edit = EmacButton("Modifier", variant="ghost")
        btn_edit.clicked.connect(self._edit_infos_generales)
        header_layout.addWidget(btn_edit)
        card.body.addLayout(header_layout)

        # Grille d'informations
        grid = QGridLayout()
        grid.setSpacing(12)

        infos = [
            ("Nom", donnees.get('nom', '-')),
            ("Prénom", donnees.get('prenom', '-')),
            ("Matricule", donnees.get('matricule', '-')),
            ("Statut", donnees.get('statut', '-')),
            ("Date de naissance", self._format_date(donnees.get('date_naissance'))),
            ("Âge", f"{donnees.get('age', '-')} ans" if donnees.get('age') else '-'),
            ("Date d'entrée", self._format_date(donnees.get('date_entree'))),
            ("Ancienneté", donnees.get('anciennete', '-')),
            ("Téléphone", donnees.get('telephone', '-')),
            ("Email", donnees.get('email', '-')),
            ("Adresse", donnees.get('adresse1', '-')),
            ("Ville", f"{donnees.get('cp_adresse', '')} {donnees.get('ville_adresse', '')}".strip() or '-'),
        ]

        for i, (label, valeur) in enumerate(infos):
            row, col = divmod(i, 2)
            lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
            lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
            grid.addWidget(lbl, row, col)

        card.body.addLayout(grid)
        return card

    def _edit_infos_generales(self):
        """Ouvre le formulaire d'édition des infos générales."""
        if not self.operateur_selectionne:
            return
        dialog = EditInfosGeneralesDialog(
            self.operateur_selectionne['id'],
            self._donnees_generales,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _creer_resume_contrat(self, donnees: dict) -> QWidget:
        """Crée le résumé du contrat."""
        self._donnees_contrat = donnees  # Stocker pour édition

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Boutons d'action
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        btn_add = EmacButton("+ Nouveau contrat", variant="primary")
        btn_add.clicked.connect(self._add_contrat)
        actions_layout.addWidget(btn_add)
        layout.addLayout(actions_layout)

        contrat = donnees.get('contrat_actif')

        if contrat:
            # Alerte si contrat expire bientôt
            jours = contrat.get('jours_restants')
            if jours is not None and jours <= 30:
                if jours < 0:
                    alert = EmacAlert(f"Contrat expiré depuis {abs(jours)} jour(s) !", variant="error")
                elif jours == 0:
                    alert = EmacAlert("Contrat expire aujourd'hui !", variant="error")
                else:
                    alert = EmacAlert(f"Contrat expire dans {jours} jour(s)", variant="warning")
                layout.addWidget(alert)

            # Carte contrat actif
            card = EmacCard("Contrat Actif")

            # Bouton modifier
            header = QHBoxLayout()
            header.addStretch()
            btn_edit = EmacButton("Modifier", variant="ghost")
            btn_edit.clicked.connect(lambda: self._edit_contrat(contrat))
            header.addWidget(btn_edit)
            card.body.addLayout(header)

            grid = QGridLayout()
            grid.setSpacing(12)

            infos = [
                ("Type", contrat.get('type_contrat', '-')),
                ("Date début", self._format_date(contrat.get('date_debut'))),
                ("Date fin", self._format_date(contrat.get('date_fin')) or "Indéterminée"),
                ("Jours restants", str(jours) if jours else "N/A"),
                ("ETP", str(contrat.get('etp', 1.0))),
                ("Catégorie", contrat.get('categorie', '-')),
                ("Emploi", contrat.get('emploi', '-')),
            ]

            for i, (label, valeur) in enumerate(infos):
                row, col = divmod(i, 2)
                lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
                lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
                grid.addWidget(lbl, row, col)

            card.body.addLayout(grid)
            layout.addWidget(card)
        else:
            alert = EmacAlert("Aucun contrat actif", variant="info")
            layout.addWidget(alert)

        # Historique des contrats
        historique = donnees.get('historique', [])
        if historique:
            card_hist = EmacCard(f"Historique ({len(historique)} contrat(s))")
            card_hist.body.addWidget(QLabel(f"{len(historique)} contrat(s) dans l'historique"))
            layout.addWidget(card_hist)

        return container

    def _add_contrat(self):
        """Ouvre le formulaire de création de contrat."""
        if not self.operateur_selectionne:
            return
        dialog = EditContratDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_contrat(self, contrat: dict):
        """Ouvre le formulaire d'édition de contrat."""
        if not self.operateur_selectionne:
            return
        dialog = EditContratDialog(self.operateur_selectionne['id'], contrat, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_declaration(self):
        """Ouvre le formulaire d'ajout de déclaration."""
        if not self.operateur_selectionne:
            return
        dialog = EditDeclarationDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_declaration(self, declaration: dict):
        """Ouvre le formulaire d'édition de déclaration."""
        if not self.operateur_selectionne:
            return
        dialog = EditDeclarationDialog(self.operateur_selectionne['id'], declaration, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_formation(self):
        """Ouvre le formulaire d'ajout de formation."""
        if not self.operateur_selectionne:
            return
        dialog = EditFormationDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_formation(self, formation: dict):
        """Ouvre le formulaire d'édition de formation."""
        if not self.operateur_selectionne:
            return
        dialog = EditFormationDialog(self.operateur_selectionne['id'], formation, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_declaration(self, declaration: dict):
        """Supprime une déclaration après confirmation."""
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette déclaration ?\n{declaration.get('type_declaration')} du {self._format_date(declaration.get('date_debut'))}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_declaration(declaration['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _delete_formation(self, formation: dict):
        """Supprime une formation après confirmation."""
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette formation ?\n{formation.get('intitule', 'N/A')}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_formation(formation['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _creer_resume_declaration(self, donnees: dict) -> QWidget:
        """Crée le résumé des déclarations."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Bouton ajouter en haut
        btn_add = EmacButton("+ Nouvelle déclaration", variant="primary")
        btn_add.clicked.connect(self._add_declaration)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        # Déclaration en cours
        en_cours = donnees.get('en_cours')
        if en_cours:
            alert = EmacAlert(
                f"Déclaration en cours: {en_cours.get('type_declaration')} "
                f"du {self._format_date(en_cours.get('date_debut'))} "
                f"au {self._format_date(en_cours.get('date_fin'))}",
                variant="info"
            )
            layout.addWidget(alert)

        # Statistiques
        stats = donnees.get('statistiques', {})
        if stats:
            card = EmacCard("Statistiques des déclarations")
            stats_layout = QHBoxLayout()

            for type_decl, data in stats.items():
                chip = EmacChip(f"{type_decl}: {data.get('nombre', 0)}", variant="info")
                stats_layout.addWidget(chip)

            stats_layout.addStretch()
            card.body.addLayout(stats_layout)
            layout.addWidget(card)

        # Liste des déclarations
        declarations = donnees.get('declarations', [])
        card = EmacCard(f"Déclarations ({len(declarations)})")
        if declarations:
            for decl in declarations:
                row = QHBoxLayout()
                info_text = f"{decl.get('type_declaration', 'N/A')} - {self._format_date(decl.get('date_debut'))} au {self._format_date(decl.get('date_fin'))}"
                row.addWidget(QLabel(info_text))
                row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.clicked.connect(lambda checked, d=decl: self._edit_declaration(d))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="ghost")
                btn_delete.clicked.connect(lambda checked, d=decl: self._delete_declaration(d))
                row.addWidget(btn_delete)
                card.body.addLayout(row)
        else:
            card.body.addWidget(QLabel("Aucune déclaration"))
        layout.addWidget(card)

        return container

    def _creer_resume_competences(self, donnees: dict) -> QWidget:
        """Crée le résumé des compétences."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        stats = donnees.get('statistiques', {})

        # Alertes évaluations
        en_retard = stats.get('evaluations_en_retard', 0)
        if en_retard > 0:
            alert = EmacAlert(f"{en_retard} évaluation(s) en retard !", variant="error")
            layout.addWidget(alert)

        a_venir = stats.get('evaluations_a_venir_30j', 0)
        if a_venir > 0:
            alert = EmacAlert(f"{a_venir} évaluation(s) à venir dans les 30 jours", variant="warning")
            layout.addWidget(alert)

        # Carte statistiques
        card = EmacCard("Statistiques Compétences")
        stats_layout = QHBoxLayout()

        niveaux = [
            ("N1", stats.get('niveau_1', 0)),
            ("N2", stats.get('niveau_2', 0)),
            ("N3", stats.get('niveau_3', 0)),
            ("N4", stats.get('niveau_4', 0)),
            ("Total", stats.get('total_postes', 0)),
        ]

        for label, count in niveaux:
            badge = QLabel(f"{label}: {count}")
            badge.setStyleSheet("""
                background: #f1f5f9;
                color: #475569;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            """)
            stats_layout.addWidget(badge)

        stats_layout.addStretch()
        card.body.addLayout(stats_layout)
        layout.addWidget(card)

        # Liste des compétences
        competences = donnees.get('competences', [])
        card_list = EmacCard(f"Postes maîtrisés ({len(competences)})")
        if competences:
            card_list.body.addWidget(QLabel(f"{len(competences)} poste(s)"))
        else:
            card_list.body.addWidget(QLabel("Aucune compétence enregistrée"))
        layout.addWidget(card_list)

        return container

    def _creer_resume_formation(self, donnees: dict) -> QWidget:
        """Crée le résumé des formations."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Bouton ajouter en haut
        btn_add = EmacButton("+ Nouvelle formation", variant="primary")
        btn_add.clicked.connect(self._add_formation)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})

        # Carte statistiques
        card = EmacCard("Statistiques Formations")
        stats_layout = QHBoxLayout()

        items = [
            ("Total", stats.get('total', 0)),
            ("Terminées", stats.get('terminees', 0)),
            ("En cours", stats.get('en_cours', 0)),
            ("Planifiées", stats.get('planifiees', 0)),
            ("Avec certificat", stats.get('avec_certificat', 0)),
        ]

        for label, count in items:
            badge = QLabel(f"{label}: {count}")
            badge.setStyleSheet("""
                background: #f1f5f9;
                color: #475569;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            """)
            stats_layout.addWidget(badge)

        stats_layout.addStretch()
        card.body.addLayout(stats_layout)
        layout.addWidget(card)

        # Liste des formations
        formations = donnees.get('formations', [])
        card_list = EmacCard(f"Formations ({len(formations)})")
        if formations:
            for form in formations:
                row = QHBoxLayout()
                info_text = f"{form.get('intitule', 'N/A')} - {form.get('statut', 'N/A')}"
                if form.get('date_debut'):
                    info_text += f" ({self._format_date(form.get('date_debut'))})"
                row.addWidget(QLabel(info_text))
                row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.clicked.connect(lambda checked, f=form: self._edit_formation(f))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="ghost")
                btn_delete.clicked.connect(lambda checked, f=form: self._delete_formation(f))
                row.addWidget(btn_delete)
                card_list.body.addLayout(row)
        else:
            card_list.body.addWidget(QLabel("Aucune formation enregistrée"))
        layout.addWidget(card_list)

        return container

    def _creer_widget_documents(self, documents: list) -> QWidget:
        """Crée le widget affichant les documents du domaine."""
        card = EmacCard(f"Documents associés ({len(documents)})")

        if not documents:
            label = QLabel("Aucun document pour ce domaine")
            label.setStyleSheet("color: #9ca3af; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(label)
        else:
            # Tableau des documents
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Nom", "Catégorie", "Date ajout", "Expiration", "Statut"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setRowCount(len(documents))

            for row, doc in enumerate(documents):
                table.setItem(row, 0, QTableWidgetItem(doc.get('nom_affichage', '-')))
                table.setItem(row, 1, QTableWidgetItem(doc.get('categorie_nom', '-')))
                table.setItem(row, 2, QTableWidgetItem(self._format_date(doc.get('date_upload'))))
                table.setItem(row, 3, QTableWidgetItem(self._format_date(doc.get('date_expiration')) or '-'))

                # Statut avec couleur
                statut = doc.get('statut', 'actif')
                statut_item = QTableWidgetItem(statut.upper())
                if statut == 'expire':
                    statut_item.setForeground(QColor("#ef4444"))
                elif statut == 'archive':
                    statut_item.setForeground(QColor("#9ca3af"))
                else:
                    statut_item.setForeground(QColor("#10b981"))
                table.setItem(row, 4, statut_item)

            card.body.addWidget(table)

        return card

    # =========================================================================
    # FOOTER
    # =========================================================================

    def _creer_footer(self) -> QWidget:
        """Crée le pied de page avec les boutons d'action."""
        footer = QWidget()
        footer.setStyleSheet("background: #f9fafb; border-top: 1px solid #e5e7eb;")

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 12, 20, 12)

        layout.addStretch()

        btn_fermer = EmacButton("Fermer", variant="ghost")
        btn_fermer.clicked.connect(self.close)
        layout.addWidget(btn_fermer)

        return footer

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _vider_layout(self, layout):
        """Supprime tous les widgets d'un layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._vider_layout(item.layout())

    def _format_date(self, date_val) -> str:
        """Formate une date pour l'affichage."""
        if not date_val:
            return '-'
        if hasattr(date_val, 'strftime'):
            return date_val.strftime('%d/%m/%Y')
        return str(date_val)


class GestionRHWidget(QWidget):
    """
    Widget RH (sans fenêtre) pour intégration dans d'autres dialogues.
    Version embarquable de GestionRHDialog.
    """

    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # État
        self.operateur_selectionne = None
        self.domaine_actif = DomaineRH.GENERAL
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._executer_recherche)

        self._setup_ui()

    def _setup_ui(self):
        """Construit l'interface utilisateur."""
        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Zone gauche: Sélection opérateur
        self.zone_gauche = self._creer_zone_selection()
        main_layout.addWidget(self.zone_gauche)

        # Séparateur vertical
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #e5e7eb;")
        separator.setFixedWidth(1)
        main_layout.addWidget(separator)

        # Zone droite: Détails RH
        self.zone_droite = self._creer_zone_details()
        main_layout.addWidget(self.zone_droite, 1)

    # =========================================================================
    # ZONE GAUCHE - Sélection opérateur
    # =========================================================================

    def _creer_zone_selection(self) -> QWidget:
        """Crée la zone de recherche et sélection d'opérateur."""
        zone = QWidget()
        zone.setFixedWidth(320)
        zone.setStyleSheet("background-color: #f8fafc;")

        layout = QVBoxLayout(zone)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Titre
        titre = QLabel("Sélection Opérateur")
        titre.setFont(QFont("Segoe UI", 14, QFont.Bold))
        titre.setStyleSheet("color: #111827;")
        layout.addWidget(titre)

        # Champ de recherche
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)

        # Label
        search_label = QLabel("Rechercher par nom, prénom ou matricule")
        search_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        search_layout.addWidget(search_label)

        # Input de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tapez pour rechercher...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)

        layout.addWidget(search_container)

        # Liste des résultats
        results_label = QLabel("Résultats")
        results_label.setStyleSheet("color: #374151; font-weight: 600; margin-top: 8px;")
        layout.addWidget(results_label)

        self.liste_operateurs = QListWidget()
        self.liste_operateurs.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: white;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f3f4f6;
            }
            QListWidget::item:selected {
                background-color: #eff6ff;
                color: #1e40af;
            }
            QListWidget::item:hover {
                background-color: #f9fafb;
            }
        """)
        self.liste_operateurs.itemClicked.connect(self._on_operateur_selectionne)
        layout.addWidget(self.liste_operateurs, 1)

        # Compteur de résultats
        self.compteur_resultats = QLabel("0 opérateur(s)")
        self.compteur_resultats.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(self.compteur_resultats)

        # Charger les opérateurs actifs par défaut
        QTimer.singleShot(100, lambda: self._executer_recherche())

        return zone

    def _on_search_changed(self, text: str):
        """Déclenche une recherche avec délai (debounce)."""
        self._search_timer.stop()
        self._search_timer.start(300)  # 300ms de délai

    def _executer_recherche(self):
        """Exécute la recherche d'opérateurs."""
        recherche = self.search_input.text().strip()
        resultats = rechercher_operateurs(recherche=recherche if recherche else None)

        self.liste_operateurs.clear()
        for op in resultats:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, op['id'])

            # Texte formaté
            nom_complet = op.get('nom_complet', f"{op.get('prenom', '')} {op.get('nom', '')}")
            matricule = op.get('matricule', '-')
            statut = op.get('statut', 'ACTIF')

            item.setText(f"{nom_complet}\n{matricule}")
            item.setToolTip(f"ID: {op['id']} | Statut: {statut}")

            self.liste_operateurs.addItem(item)

        self.compteur_resultats.setText(f"{len(resultats)} opérateur(s)")

    def _on_operateur_selectionne(self, item: QListWidgetItem):
        """Appelé quand un opérateur est sélectionné dans la liste."""
        operateur_id = item.data(Qt.UserRole)
        self.operateur_selectionne = get_operateur_by_id(operateur_id)

        if self.operateur_selectionne:
            self._afficher_details_operateur()

    # =========================================================================
    # ZONE DROITE - Détails RH
    # =========================================================================

    def _creer_zone_details(self) -> QWidget:
        """Crée la zone d'affichage des détails RH."""
        zone = QWidget()
        layout = QVBoxLayout(zone)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stack pour basculer entre placeholder et contenu
        self.stack_details = QStackedWidget()

        # Page 0: Placeholder (aucun opérateur sélectionné)
        self.placeholder = self._creer_placeholder()
        self.stack_details.addWidget(self.placeholder)

        # Page 1: Contenu RH
        self.contenu_rh = self._creer_contenu_rh()
        self.stack_details.addWidget(self.contenu_rh)

        layout.addWidget(self.stack_details)

        return zone

    def _creer_placeholder(self) -> QWidget:
        """Crée le placeholder affiché quand aucun opérateur n'est sélectionné."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        # Icône
        icon = QLabel("👤")
        icon.setFont(QFont("Segoe UI", 48))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        # Message
        message = QLabel("Sélectionnez un opérateur")
        message.setFont(QFont("Segoe UI", 18, QFont.Bold))
        message.setStyleSheet("color: #6b7280;")
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)

        # Sous-message
        sous_message = QLabel("Utilisez la zone de recherche à gauche\npour trouver un opérateur")
        sous_message.setStyleSheet("color: #9ca3af;")
        sous_message.setAlignment(Qt.AlignCenter)
        layout.addWidget(sous_message)

        return widget

    def _creer_contenu_rh(self) -> QWidget:
        """Crée le contenu RH (affiché quand un opérateur est sélectionné)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # En-tête avec infos opérateur
        self.header_operateur = self._creer_header_operateur()
        layout.addWidget(self.header_operateur)

        # Barre de navigation des domaines RH
        self.nav_domaines = self._creer_navigation_domaines()
        layout.addWidget(self.nav_domaines)

        # Zone de contenu scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Container pour résumé + documents
        self.container_domaine = QWidget()
        self.layout_domaine = QVBoxLayout(self.container_domaine)
        self.layout_domaine.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.setSpacing(16)

        # Zone résumé des données
        self.zone_resume = QWidget()
        self.layout_resume = QVBoxLayout(self.zone_resume)
        self.layout_resume.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.addWidget(self.zone_resume)

        # Zone documents
        self.zone_documents = QWidget()
        self.layout_documents = QVBoxLayout(self.zone_documents)
        self.layout_documents.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.addWidget(self.zone_documents)

        # Spacer
        self.layout_domaine.addStretch()

        scroll.setWidget(self.container_domaine)
        layout.addWidget(scroll, 1)

        return widget

    def _creer_header_operateur(self) -> QWidget:
        """Crée l'en-tête compact avec les infos de l'opérateur sélectionné."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: #1e40af;
                border-radius: 8px;
            }
        """)
        header.setFixedHeight(50)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)

        # Nom
        self.label_nom_operateur = QLabel("Nom Prénom")
        self.label_nom_operateur.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.label_nom_operateur.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(self.label_nom_operateur)

        # Séparateur
        sep = QLabel("•")
        sep.setStyleSheet("color: #93c5fd; background: transparent; margin: 0 8px;")
        layout.addWidget(sep)

        # Matricule
        self.label_matricule = QLabel("-")
        self.label_matricule.setStyleSheet("color: #bfdbfe; background: transparent; font-size: 13px;")
        layout.addWidget(self.label_matricule)

        layout.addStretch()

        # Badge statut
        self.badge_statut = QLabel("ACTIF")
        self.badge_statut.setStyleSheet("""
            background: #10b981;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 11px;
        """)
        layout.addWidget(self.badge_statut)

        return header

    def _creer_navigation_domaines(self) -> QWidget:
        """Crée la barre de navigation entre les domaines RH."""
        nav = QWidget()
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.boutons_domaines = {}
        domaines = get_domaines_rh()

        for domaine in domaines:
            btn = QPushButton(domaine['nom'])
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty('domaine', domaine['code'])
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 16px;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    background: white;
                    color: #374151;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: #f9fafb;
                    border-color: #d1d5db;
                }
                QPushButton:checked {
                    background: #1e40af;
                    color: white;
                    border-color: #1e40af;
                }
            """)
            btn.clicked.connect(lambda checked, d=domaine['code']: self._on_domaine_change(d))
            layout.addWidget(btn)
            self.boutons_domaines[domaine['code']] = btn

        layout.addStretch()

        return nav

    def _on_domaine_change(self, code_domaine: str):
        """Appelé quand l'utilisateur change de domaine RH."""
        # Mettre à jour l'état des boutons
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == code_domaine)

        # Mettre à jour le domaine actif
        self.domaine_actif = DomaineRH(code_domaine)

        # Recharger le contenu
        if self.operateur_selectionne:
            self._charger_contenu_domaine()

    def _afficher_details_operateur(self):
        """Affiche les détails de l'opérateur sélectionné."""
        if not self.operateur_selectionne:
            return

        op = self.operateur_selectionne

        # Mettre à jour l'en-tête
        nom_complet = op.get('nom_complet', f"{op.get('prenom', '')} {op.get('nom', '')}")
        self.label_nom_operateur.setText(nom_complet)
        self.label_matricule.setText(op.get('matricule', '-'))

        # Badge statut
        statut = op.get('statut', 'ACTIF')
        if statut == 'ACTIF':
            self.badge_statut.setText("ACTIF")
            self.badge_statut.setStyleSheet("""
                background: #10b981;
                color: white;
                padding: 6px 12px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            """)
        else:
            self.badge_statut.setText("INACTIF")
            self.badge_statut.setStyleSheet("""
                background: #6b7280;
                color: white;
                padding: 6px 12px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            """)

        # Activer le premier domaine par défaut
        self.domaine_actif = DomaineRH.GENERAL
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == DomaineRH.GENERAL.value)

        # Charger le contenu du domaine
        self._charger_contenu_domaine()

        # Afficher la zone de contenu
        self.stack_details.setCurrentIndex(1)

    def _charger_contenu_domaine(self):
        """Charge le contenu du domaine RH actif."""
        if not self.operateur_selectionne:
            return

        operateur_id = self.operateur_selectionne['id']

        # Vider les zones
        self._vider_layout(self.layout_resume)
        self._vider_layout(self.layout_documents)

        # Charger les données du domaine
        donnees = get_donnees_domaine(operateur_id, self.domaine_actif)

        # Créer la zone de résumé selon le domaine
        widget_resume = self._creer_widget_resume(donnees)
        if widget_resume:
            self.layout_resume.addWidget(widget_resume)

        # Charger les documents du domaine
        documents = get_documents_domaine(operateur_id, self.domaine_actif)
        widget_documents = self._creer_widget_documents(documents)
        self.layout_documents.addWidget(widget_documents)

    def _creer_widget_resume(self, donnees: dict) -> QWidget:
        """Crée le widget de résumé selon le domaine actif."""
        if self.domaine_actif == DomaineRH.GENERAL:
            return self._creer_resume_general(donnees)
        elif self.domaine_actif == DomaineRH.CONTRAT:
            return self._creer_resume_contrat(donnees)
        elif self.domaine_actif == DomaineRH.DECLARATION:
            return self._creer_resume_declaration(donnees)
        elif self.domaine_actif == DomaineRH.COMPETENCES:
            return self._creer_resume_competences(donnees)
        elif self.domaine_actif == DomaineRH.FORMATION:
            return self._creer_resume_formation(donnees)
        return None

    def _creer_resume_general(self, donnees: dict) -> QWidget:
        """Crée le résumé des données générales."""
        self._donnees_generales = donnees  # Stocker pour édition

        card = EmacCard("Informations Générales")

        if donnees.get('error'):
            card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            return card

        # Bouton modifier en haut à droite
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        btn_edit = EmacButton("Modifier", variant="ghost")
        btn_edit.clicked.connect(self._edit_infos_generales)
        header_layout.addWidget(btn_edit)
        card.body.addLayout(header_layout)

        # Grille d'informations
        grid = QGridLayout()
        grid.setSpacing(12)

        infos = [
            ("Nom", donnees.get('nom', '-')),
            ("Prénom", donnees.get('prenom', '-')),
            ("Matricule", donnees.get('matricule', '-')),
            ("Statut", donnees.get('statut', '-')),
            ("Date de naissance", self._format_date(donnees.get('date_naissance'))),
            ("Âge", f"{donnees.get('age', '-')} ans" if donnees.get('age') else '-'),
            ("Date d'entrée", self._format_date(donnees.get('date_entree'))),
            ("Ancienneté", donnees.get('anciennete', '-')),
            ("Téléphone", donnees.get('telephone', '-')),
            ("Email", donnees.get('email', '-')),
            ("Adresse", donnees.get('adresse1', '-')),
            ("Ville", f"{donnees.get('cp_adresse', '')} {donnees.get('ville_adresse', '')}".strip() or '-'),
        ]

        for i, (label, valeur) in enumerate(infos):
            row, col = divmod(i, 2)
            lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
            lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
            grid.addWidget(lbl, row, col)

        card.body.addLayout(grid)
        return card

    def _edit_infos_generales(self):
        """Ouvre le formulaire d'édition des infos générales."""
        if not self.operateur_selectionne:
            return
        dialog = EditInfosGeneralesDialog(
            self.operateur_selectionne['id'],
            self._donnees_generales,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _creer_resume_contrat(self, donnees: dict) -> QWidget:
        """Crée le résumé du contrat."""
        self._donnees_contrat = donnees  # Stocker pour édition

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Boutons d'action
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        btn_add = EmacButton("+ Nouveau contrat", variant="primary")
        btn_add.clicked.connect(self._add_contrat)
        actions_layout.addWidget(btn_add)
        layout.addLayout(actions_layout)

        contrat = donnees.get('contrat_actif')

        if contrat:
            # Alerte si contrat expire bientôt
            jours = contrat.get('jours_restants')
            if jours is not None and jours <= 30:
                if jours < 0:
                    alert = EmacAlert(f"Contrat expiré depuis {abs(jours)} jour(s) !", variant="error")
                elif jours == 0:
                    alert = EmacAlert("Contrat expire aujourd'hui !", variant="error")
                else:
                    alert = EmacAlert(f"Contrat expire dans {jours} jour(s)", variant="warning")
                layout.addWidget(alert)

            # Carte contrat actif
            card = EmacCard("Contrat Actif")

            # Bouton modifier
            header = QHBoxLayout()
            header.addStretch()
            btn_edit = EmacButton("Modifier", variant="ghost")
            btn_edit.clicked.connect(lambda: self._edit_contrat(contrat))
            header.addWidget(btn_edit)
            card.body.addLayout(header)

            grid = QGridLayout()
            grid.setSpacing(12)

            infos = [
                ("Type", contrat.get('type_contrat', '-')),
                ("Date début", self._format_date(contrat.get('date_debut'))),
                ("Date fin", self._format_date(contrat.get('date_fin')) or "Indéterminée"),
                ("Jours restants", str(jours) if jours else "N/A"),
                ("ETP", str(contrat.get('etp', 1.0))),
                ("Catégorie", contrat.get('categorie', '-')),
                ("Emploi", contrat.get('emploi', '-')),
            ]

            for i, (label, valeur) in enumerate(infos):
                row, col = divmod(i, 2)
                lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
                lbl.setStyleSheet("padding: 8px; background: #f9fafb; border-radius: 6px;")
                grid.addWidget(lbl, row, col)

            card.body.addLayout(grid)
            layout.addWidget(card)
        else:
            alert = EmacAlert("Aucun contrat actif", variant="info")
            layout.addWidget(alert)

        # Historique des contrats
        historique = donnees.get('historique', [])
        if historique:
            card_hist = EmacCard(f"Historique ({len(historique)} contrat(s))")
            card_hist.body.addWidget(QLabel(f"{len(historique)} contrat(s) dans l'historique"))
            layout.addWidget(card_hist)

        return container

    def _add_contrat(self):
        """Ouvre le formulaire de création de contrat."""
        if not self.operateur_selectionne:
            return
        dialog = EditContratDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_contrat(self, contrat: dict):
        """Ouvre le formulaire d'édition de contrat."""
        if not self.operateur_selectionne:
            return
        dialog = EditContratDialog(self.operateur_selectionne['id'], contrat, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_declaration(self):
        """Ouvre le formulaire d'ajout de déclaration."""
        if not self.operateur_selectionne:
            return
        dialog = EditDeclarationDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_declaration(self, declaration: dict):
        """Ouvre le formulaire d'édition de déclaration."""
        if not self.operateur_selectionne:
            return
        dialog = EditDeclarationDialog(self.operateur_selectionne['id'], declaration, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_formation(self):
        """Ouvre le formulaire d'ajout de formation."""
        if not self.operateur_selectionne:
            return
        dialog = EditFormationDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_formation(self, formation: dict):
        """Ouvre le formulaire d'édition de formation."""
        if not self.operateur_selectionne:
            return
        dialog = EditFormationDialog(self.operateur_selectionne['id'], formation, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_declaration(self, declaration: dict):
        """Supprime une déclaration après confirmation."""
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette déclaration ?\n{declaration.get('type_declaration')} du {self._format_date(declaration.get('date_debut'))}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_declaration(declaration['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _delete_formation(self, formation: dict):
        """Supprime une formation après confirmation."""
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette formation ?\n{formation.get('intitule', 'N/A')}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_formation(formation['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _creer_resume_declaration(self, donnees: dict) -> QWidget:
        """Crée le résumé des déclarations."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Bouton ajouter en haut
        btn_add = EmacButton("+ Nouvelle déclaration", variant="primary")
        btn_add.clicked.connect(self._add_declaration)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        # Déclaration en cours
        en_cours = donnees.get('en_cours')
        if en_cours:
            alert = EmacAlert(
                f"Déclaration en cours: {en_cours.get('type_declaration')} "
                f"du {self._format_date(en_cours.get('date_debut'))} "
                f"au {self._format_date(en_cours.get('date_fin'))}",
                variant="info"
            )
            layout.addWidget(alert)

        # Statistiques
        stats = donnees.get('statistiques', {})
        if stats:
            card = EmacCard("Statistiques des déclarations")
            stats_layout = QHBoxLayout()

            for type_decl, data in stats.items():
                chip = EmacChip(f"{type_decl}: {data.get('nombre', 0)}", variant="info")
                stats_layout.addWidget(chip)

            stats_layout.addStretch()
            card.body.addLayout(stats_layout)
            layout.addWidget(card)

        # Liste des déclarations
        declarations = donnees.get('declarations', [])
        card = EmacCard(f"Déclarations ({len(declarations)})")
        if declarations:
            for decl in declarations:
                row = QHBoxLayout()
                info_text = f"{decl.get('type_declaration', 'N/A')} - {self._format_date(decl.get('date_debut'))} au {self._format_date(decl.get('date_fin'))}"
                row.addWidget(QLabel(info_text))
                row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.clicked.connect(lambda checked, d=decl: self._edit_declaration(d))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="ghost")
                btn_delete.clicked.connect(lambda checked, d=decl: self._delete_declaration(d))
                row.addWidget(btn_delete)
                card.body.addLayout(row)
        else:
            card.body.addWidget(QLabel("Aucune déclaration"))
        layout.addWidget(card)

        return container

    def _creer_resume_competences(self, donnees: dict) -> QWidget:
        """Crée le résumé des compétences."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        stats = donnees.get('statistiques', {})

        # Alertes évaluations
        en_retard = stats.get('evaluations_en_retard', 0)
        if en_retard > 0:
            alert = EmacAlert(f"{en_retard} évaluation(s) en retard !", variant="error")
            layout.addWidget(alert)

        a_venir = stats.get('evaluations_a_venir_30j', 0)
        if a_venir > 0:
            alert = EmacAlert(f"{a_venir} évaluation(s) à venir dans les 30 jours", variant="warning")
            layout.addWidget(alert)

        # Carte statistiques
        card = EmacCard("Statistiques Compétences")
        stats_layout = QHBoxLayout()

        niveaux = [
            ("N1", stats.get('niveau_1', 0)),
            ("N2", stats.get('niveau_2', 0)),
            ("N3", stats.get('niveau_3', 0)),
            ("N4", stats.get('niveau_4', 0)),
            ("Total", stats.get('total_postes', 0)),
        ]

        for label, count in niveaux:
            badge = QLabel(f"{label}: {count}")
            badge.setStyleSheet("""
                background: #f1f5f9;
                color: #475569;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            """)
            stats_layout.addWidget(badge)

        stats_layout.addStretch()
        card.body.addLayout(stats_layout)
        layout.addWidget(card)

        # Liste des compétences
        competences = donnees.get('competences', [])
        card_list = EmacCard(f"Postes maîtrisés ({len(competences)})")
        if competences:
            card_list.body.addWidget(QLabel(f"{len(competences)} poste(s)"))
        else:
            card_list.body.addWidget(QLabel("Aucune compétence enregistrée"))
        layout.addWidget(card_list)

        return container

    def _creer_resume_formation(self, donnees: dict) -> QWidget:
        """Crée le résumé des formations."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Bouton ajouter en haut
        btn_add = EmacButton("+ Nouvelle formation", variant="primary")
        btn_add.clicked.connect(self._add_formation)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})

        # Carte statistiques
        card = EmacCard("Statistiques Formations")
        stats_layout = QHBoxLayout()

        items = [
            ("Total", stats.get('total', 0)),
            ("Terminées", stats.get('terminees', 0)),
            ("En cours", stats.get('en_cours', 0)),
            ("Planifiées", stats.get('planifiees', 0)),
            ("Avec certificat", stats.get('avec_certificat', 0)),
        ]

        for label, count in items:
            badge = QLabel(f"{label}: {count}")
            badge.setStyleSheet("""
                background: #f1f5f9;
                color: #475569;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            """)
            stats_layout.addWidget(badge)

        stats_layout.addStretch()
        card.body.addLayout(stats_layout)
        layout.addWidget(card)

        # Liste des formations
        formations = donnees.get('formations', [])
        card_list = EmacCard(f"Formations ({len(formations)})")
        if formations:
            for form in formations:
                row = QHBoxLayout()
                info_text = f"{form.get('intitule', 'N/A')} - {form.get('statut', 'N/A')}"
                if form.get('date_debut'):
                    info_text += f" ({self._format_date(form.get('date_debut'))})"
                row.addWidget(QLabel(info_text))
                row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.clicked.connect(lambda checked, f=form: self._edit_formation(f))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="ghost")
                btn_delete.clicked.connect(lambda checked, f=form: self._delete_formation(f))
                row.addWidget(btn_delete)
                card_list.body.addLayout(row)
        else:
            card_list.body.addWidget(QLabel("Aucune formation enregistrée"))
        layout.addWidget(card_list)

        return container

    def _creer_widget_documents(self, documents: list) -> QWidget:
        """Crée le widget affichant les documents du domaine."""
        card = EmacCard(f"Documents associés ({len(documents)})")

        if not documents:
            label = QLabel("Aucun document pour ce domaine")
            label.setStyleSheet("color: #9ca3af; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(label)
        else:
            # Tableau des documents
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Nom", "Catégorie", "Date ajout", "Expiration", "Statut"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setRowCount(len(documents))

            for row, doc in enumerate(documents):
                table.setItem(row, 0, QTableWidgetItem(doc.get('nom_affichage', '-')))
                table.setItem(row, 1, QTableWidgetItem(doc.get('categorie_nom', '-')))
                table.setItem(row, 2, QTableWidgetItem(self._format_date(doc.get('date_upload'))))
                table.setItem(row, 3, QTableWidgetItem(self._format_date(doc.get('date_expiration')) or '-'))

                # Statut avec couleur
                statut = doc.get('statut', 'actif')
                statut_item = QTableWidgetItem(statut.upper())
                if statut == 'expire':
                    statut_item.setForeground(QColor("#ef4444"))
                elif statut == 'archive':
                    statut_item.setForeground(QColor("#9ca3af"))
                else:
                    statut_item.setForeground(QColor("#10b981"))
                table.setItem(row, 4, statut_item)

            card.body.addWidget(table)

        return card

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _vider_layout(self, layout):
        """Supprime tous les widgets d'un layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._vider_layout(item.layout())

    def _format_date(self, date_val) -> str:
        """Formate une date pour l'affichage."""
        if not date_val:
            return '-'
        if hasattr(date_val, 'strftime'):
            return date_val.strftime('%d/%m/%Y')
        return str(date_val)


# Pour compatibilité avec l'ancien code qui pourrait importer ce module
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = GestionRHDialog()
    dialog.show()
    sys.exit(app.exec_())
