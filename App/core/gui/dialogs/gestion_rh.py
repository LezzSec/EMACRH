# -*- coding: utf-8 -*-
"""
Écran RH Opérateur & Documents
Permet de consulter et gérer les données RH d'un opérateur par domaine.

Structure:
- Zone gauche: Recherche et sélection d'opérateur
- Zone droite: Navigation par domaines RH + résumé + documents
"""

import logging

logger = logging.getLogger(__name__)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QWidget, QFrame, QScrollArea,
    QStackedWidget, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication as _QApp
from PyQt5.QtGui import QFont

from core.gui.workers.db_worker import DbWorker, DbThreadPool
from core.gui.components.loading_components import LoadingLabel
from core.gui.components.ui_theme import EmacCard, EmacButton
from core.gui.components.emac_ui_kit import EmacAlert, EmacChip, add_custom_title_bar
from core.services.rh_service import (
    rechercher_operateurs,
    get_operateur_by_id,
    get_donnees_domaine,
    DomaineRH,
    delete_formation,
    delete_declaration,
    get_documents_domaine,
    get_documents_archives_operateur,
    get_domaines_rh,
)
from core.services import competences_service as _competences_service
delete_competence_personnel = _competences_service.remove_assignment
from core.services.medical_service import delete_visite, delete_accident
from core.services.vie_salarie_service import (
    delete_sanction,
    delete_entretien,
)
from core.services.permission_manager import can, require
from core.utils.date_format import format_date
from core.gui.dialogs.gestion_rh_dialogs import (
    EditInfosGeneralesDialog, EditContratDialog, EditDeclarationDialog,
    EditCompetenceDialog, EditFormationDialog, EditVisiteDialog,
    EditAccidentDialog, EditSanctionDialog, EditControleAlcoolDialog,
    EditTestSalivaireDialog, EditEntretienDialog, AjouterDocumentDialog,
)


class _GestionRHMixin:
    """
    Mixin partagé entre GestionRHDialog et tout futur widget RH.
    Contient toute la logique et l'UI commune.
    """

    def _executer_recherche(self):
        """Exécute la recherche d'opérateurs (async)."""
        recherche = self.search_input.text().strip()

        self.liste_operateurs.clear()
        self.liste_operateurs.addItem("Recherche en cours…")
        self.compteur_resultats.setText("…")

        def fetch(progress_callback=None):
            return rechercher_operateurs(recherche=recherche if recherche else None)

        def on_result(resultats):
            self.liste_operateurs.clear()
            for op in resultats:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, op['id'])
                nom_complet = op.get('nom_complet', f"{op.get('prenom', '')} {op.get('nom', '')}")
                matricule = op.get('matricule', '-')
                statut = op.get('statut', 'ACTIF')
                item.setText(f"{nom_complet}\n{matricule}")
                item.setToolTip(f"ID: {op['id']} | Statut: {statut}")
                self.liste_operateurs.addItem(item)
            self.compteur_resultats.setText(f"{len(resultats)} opérateur(s)")

        def on_error(err):
            self.liste_operateurs.clear()
            self.compteur_resultats.setText("Erreur")
            logger.error(f"Erreur recherche opérateurs: {err}")

        worker = DbWorker(fetch)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(on_error)
        DbThreadPool.start(worker)

    def _charger_contenu_domaine(self):
        """Charge le contenu du domaine RH actif (async)."""
        if not self.operateur_selectionne:
            return

        # Annuler le chargement précédent s'il est encore en cours
        if self._loading_worker:
            self._loading_worker.cancel()
            self._loading_worker = None

        operateur_id = self.operateur_selectionne['id']
        domaine = self.domaine_actif  # Capturer pour éviter la race condition

        # Vider les zones et afficher un indicateur de chargement
        self._vider_layout(self.layout_resume)
        self._vider_layout(self.layout_documents)
        loading = LoadingLabel("Chargement")
        self.layout_resume.addWidget(loading)

        def fetch(progress_callback=None):
            donnees   = get_donnees_domaine(operateur_id, domaine)
            documents = get_documents_domaine(operateur_id, domaine, include_archives=True)
            return donnees, documents, domaine

        def on_result(result):
            donnees, documents, fetched_domaine = result
            # Ignorer si le domaine actif a changé pendant le chargement
            if self.domaine_actif != fetched_domaine:
                return
            self._vider_layout(self.layout_resume)
            self._vider_layout(self.layout_documents)
            widget_resume = self._creer_widget_resume(donnees, documents)
            if widget_resume:
                self.layout_resume.addWidget(widget_resume)
            if fetched_domaine != DomaineRH.CONTRAT and self._domaine_a_contenu(donnees, fetched_domaine):
                widget_documents = self._creer_widget_documents(documents)
                self.layout_resume.addWidget(widget_documents)
            self.data_changed.emit()

        def on_error(err):
            self._vider_layout(self.layout_resume)
            logger.error(f"Erreur chargement domaine RH: {err}")

        self._loading_worker = DbWorker(fetch)
        self._loading_worker.signals.result.connect(on_result)
        self._loading_worker.signals.error.connect(on_error)
        DbThreadPool.start(self._loading_worker)

    def _creer_widget_resume(self, donnees: dict, documents: list = None) -> QWidget:
        """Crée le widget de résumé selon le domaine actif."""
        if self.domaine_actif == DomaineRH.GENERAL:
            return self._creer_resume_general(donnees)
        elif self.domaine_actif == DomaineRH.CONTRAT:
            return self._creer_resume_contrat(donnees, documents or [])
        elif self.domaine_actif == DomaineRH.DECLARATION:
            return self._creer_resume_declaration(donnees)
        elif self.domaine_actif == DomaineRH.COMPETENCES:
            return self._creer_resume_competences(donnees)
        elif self.domaine_actif == DomaineRH.FORMATION:
            return self._creer_resume_formation(donnees)
        elif self.domaine_actif == DomaineRH.MEDICAL:
            return self._creer_resume_medical(donnees)
        elif self.domaine_actif == DomaineRH.VIE_SALARIE:
            return self._creer_resume_vie_salarie(donnees)
        elif self.domaine_actif == DomaineRH.POLYVALENCE:
            return self._creer_resume_polyvalence(donnees)
        return None

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
        header_layout = QHBoxLayout()
        titre = QLabel("Sélection Opérateur")
        titre.setFont(QFont("Segoe UI", 14, QFont.Bold))
        titre.setStyleSheet("color: #111827;")
        header_layout.addWidget(titre)
        header_layout.addStretch()

        layout.addLayout(header_layout)

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

    def _on_operateur_selectionne(self, item: QListWidgetItem):
        """Appelé quand un opérateur est sélectionné dans la liste."""
        operateur_id = item.data(Qt.UserRole)
        self.operateur_selectionne = get_operateur_by_id(operateur_id)

        if self.operateur_selectionne:
            self._afficher_details_operateur()

    def _selectionner_operateur_par_id(self, operateur_id: int):
        """Sélectionne automatiquement un opérateur par son ID."""
        self.operateur_selectionne = get_operateur_by_id(operateur_id)

        if self.operateur_selectionne:
            self._afficher_details_operateur()

            # Sélectionner dans la liste si présent
            for i in range(self.liste_operateurs.count()):
                item = self.liste_operateurs.item(i)
                if item.data(Qt.UserRole) == operateur_id:
                    self.liste_operateurs.setCurrentItem(item)
                    break

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

        icon = QLabel("👤")
        icon.setFont(QFont("Segoe UI", 48))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        message = QLabel("Sélectionnez un opérateur")
        message.setFont(QFont("Segoe UI", 18, QFont.Bold))
        message.setStyleSheet("color: #6b7280;")
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)

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

        self.header_operateur = self._creer_header_operateur()
        layout.addWidget(self.header_operateur)

        self.nav_domaines = self._creer_navigation_domaines()
        layout.addWidget(self.nav_domaines)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container_domaine = QWidget()
        self.layout_domaine = QVBoxLayout(self.container_domaine)
        self.layout_domaine.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.setSpacing(16)

        self.zone_resume = QWidget()
        self.layout_resume = QVBoxLayout(self.zone_resume)
        self.layout_resume.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.addWidget(self.zone_resume)

        self.zone_documents = QWidget()
        self.layout_documents = QVBoxLayout(self.zone_documents)
        self.layout_documents.setContentsMargins(0, 0, 0, 0)
        self.layout_domaine.addWidget(self.zone_documents)

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

        self.label_nom_operateur = QLabel("Nom Prénom")
        self.label_nom_operateur.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.label_nom_operateur.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(self.label_nom_operateur)

        sep = QLabel("•")
        sep.setStyleSheet("color: #93c5fd; background: transparent; margin: 0 8px;")
        layout.addWidget(sep)

        self.label_matricule = QLabel("-")
        self.label_matricule.setStyleSheet("color: #bfdbfe; background: transparent; font-size: 13px;")
        layout.addWidget(self.label_matricule)

        layout.addStretch()

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

        self.btn_archives = QPushButton("📦 Archives")
        self.btn_archives.setCheckable(True)
        self.btn_archives.setCursor(Qt.PointingHandCursor)
        self.btn_archives.setStyleSheet("""
            QPushButton {
                padding: 10px 16px;
                border: 1px solid #f59e0b;
                border-radius: 8px;
                background: #fffbeb;
                color: #92400e;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #fef3c7;
                border-color: #d97706;
            }
            QPushButton:checked {
                background: #f59e0b;
                color: white;
                border-color: #f59e0b;
            }
        """)
        self.btn_archives.clicked.connect(self._on_archives_click)
        self.btn_archives.setVisible(False)
        layout.addWidget(self.btn_archives)

        layout.addStretch()

        return nav

    def _update_archives_tab(self):
        """Met à jour la visibilité et le compteur de l'onglet Archives."""
        if not self.operateur_selectionne:
            if hasattr(self, 'btn_archives'):
                self.btn_archives.setVisible(False)
            return

        archives = get_documents_archives_operateur(self.operateur_selectionne['id'])
        if archives:
            self.btn_archives.setText(f"📦 Archives ({len(archives)})")
            self.btn_archives.setVisible(True)
        else:
            self.btn_archives.setVisible(False)

    def _on_archives_click(self):
        """Appelé quand l'utilisateur clique sur l'onglet Archives."""
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(False)
        self.btn_archives.setChecked(True)
        self._charger_contenu_archives()

    def _on_domaine_change(self, code_domaine: str):
        """Appelé quand l'utilisateur change de domaine RH."""
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == code_domaine)

        self.domaine_actif = DomaineRH(code_domaine)

        if self.operateur_selectionne:
            self._charger_contenu_domaine()

    def _afficher_details_operateur(self):
        """Affiche les détails de l'opérateur sélectionné."""
        if not self.operateur_selectionne:
            return

        op = self.operateur_selectionne

        nom_complet = op.get('nom_complet', f"{op.get('prenom', '')} {op.get('nom', '')}")
        self.label_nom_operateur.setText(nom_complet)
        self.label_matricule.setText(op.get('matricule', '-'))

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

        self.domaine_actif = DomaineRH.GENERAL
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == DomaineRH.GENERAL.value)
        self.btn_archives.setChecked(False)

        self._charger_contenu_domaine()
        self._update_archives_tab()

        self.stack_details.setCurrentIndex(1)

    # =========================================================================
    # RÉSUMÉS PAR DOMAINE
    # =========================================================================

    def _creer_resume_general(self, donnees: dict) -> QWidget:
        """Crée le résumé des données générales."""
        self._donnees_generales = donnees

        card = EmacCard("Informations Générales")

        if donnees.get('error'):
            card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            return card

        header_layout = QHBoxLayout()
        header_layout.addStretch()
        btn_edit = EmacButton("Modifier", variant="ghost")
        btn_edit.setVisible(can("rh.personnel.edit"))
        btn_edit.clicked.connect(self._edit_infos_generales)
        header_layout.addWidget(btn_edit)
        card.body.addLayout(header_layout)

        grid = QGridLayout()
        grid.setSpacing(12)

        def val(key, default='-'):
            v = donnees.get(key)
            return v if v is not None and v != '' else default

        adresse_parts = []
        if donnees.get('adresse1'):
            adresse_parts.append(donnees['adresse1'])
        if donnees.get('adresse2'):
            adresse_parts.append(donnees['adresse2'])
        adresse = ', '.join(adresse_parts) if adresse_parts else '-'

        ville_parts = []
        if donnees.get('cp_adresse'):
            ville_parts.append(donnees['cp_adresse'])
        if donnees.get('ville_adresse'):
            ville_parts.append(donnees['ville_adresse'])
        ville = ' '.join(ville_parts) if ville_parts else '-'

        naissance_parts = []
        if donnees.get('ville_naissance'):
            naissance_parts.append(donnees['ville_naissance'])
        if donnees.get('pays_naissance'):
            naissance_parts.append(f"({donnees['pays_naissance']})")
        lieu_naissance = ' '.join(naissance_parts) if naissance_parts else '-'

        cat_map = {'O': 'O - Ouvrier', 'E': 'E - Employé', 'T': 'T - Technicien', 'C': 'C - Cadre'}
        categorie_display = cat_map.get(donnees.get('categorie', ''), val('categorie'))

        infos = [
            ("Nom", val('nom')),
            ("Prénom", val('prenom')),
            ("Matricule", val('matricule')),
            ("Statut", val('statut')),
            ("Sexe", "Homme" if donnees.get('sexe') == 'M' else "Femme" if donnees.get('sexe') == 'F' else '-'),
            ("Nationalité", val('nationalite')),
            ("Catégorie", categorie_display),
            ("Service / Poste", val('numposte')),
            ("N° Sécurité Sociale", val('numero_ss')),
            ("Date de naissance", self._format_date(donnees.get('date_naissance'))),
            ("Lieu de naissance", lieu_naissance),
            ("Âge", f"{donnees.get('age')} ans" if donnees.get('age') else '-'),
            ("Date d'entrée", self._format_date(donnees.get('date_entree'))),
            ("Ancienneté", val('anciennete')),
            ("Téléphone", val('telephone')),
            ("Email", val('email')),
            ("Adresse", adresse),
            ("Ville", ville),
            ("Pays", val('pays_adresse')),
        ]

        for i, (label, valeur) in enumerate(infos):
            row, col = divmod(i, 3)
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

    def _creer_resume_contrat(self, donnees: dict, documents: list = None) -> QWidget:
        """Crée le résumé du contrat."""
        self._donnees_contrat = donnees

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        btn_add = EmacButton("+ Nouveau contrat", variant="primary")
        btn_add.setVisible(can("rh.contrats.edit"))
        btn_add.clicked.connect(self._add_contrat)
        actions_layout.addWidget(btn_add)
        layout.addLayout(actions_layout)

        contrat = donnees.get('contrat_actif')

        if contrat:
            jours = contrat.get('jours_restants')
            if jours is not None and jours <= 30:
                if jours < 0:
                    alert = EmacAlert(f"Contrat expiré depuis {abs(jours)} jour(s) !", variant="error")
                elif jours == 0:
                    alert = EmacAlert("Contrat expire aujourd'hui !", variant="error")
                else:
                    alert = EmacAlert(f"Contrat expire dans {jours} jour(s)", variant="warning")
                layout.addWidget(alert)

            card = EmacCard("Contrat Actif")

            header = QHBoxLayout()
            header.addStretch()
            btn_edit = EmacButton("Modifier", variant="ghost")
            btn_edit.setVisible(can("rh.contrats.edit"))
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

            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("background: #e5e7eb; margin: 8px 0;")
            card.body.addWidget(sep)

            docs_actifs = [d for d in (documents or []) if d.get('statut') != 'archive']
            doc_header_layout = QHBoxLayout()
            doc_title_lbl = QLabel(f"Documents ({len(docs_actifs)})")
            doc_title_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
            doc_title_lbl.setStyleSheet("color: #374151; background: transparent;")
            doc_header_layout.addWidget(doc_title_lbl)
            doc_header_layout.addStretch()
            btn_ajouter_doc = EmacButton("+ Ajouter un document", variant="secondary")
            btn_ajouter_doc.setVisible(can("rh.documents.edit"))
            btn_ajouter_doc.clicked.connect(self._ajouter_document)
            doc_header_layout.addWidget(btn_ajouter_doc)
            card.body.addLayout(doc_header_layout)

            if not docs_actifs:
                no_doc_lbl = QLabel("Aucun document joint")
                no_doc_lbl.setStyleSheet("color: #9ca3af; padding: 4px 0; background: transparent;")
                card.body.addWidget(no_doc_lbl)
            else:
                for doc in docs_actifs:
                    doc_lbl = QLabel(
                        f"📎 <b>{doc.get('nom_affichage', '-')}</b>"
                        f"<span style='color:#6b7280; font-size:11px;'>"
                        f"  •  Ajouté le {self._format_date(doc.get('date_upload'))}</span>"
                    )
                    doc_lbl.setStyleSheet("padding: 3px 0; background: transparent;")
                    card.body.addWidget(doc_lbl)

            layout.addWidget(card)
        else:
            alert = EmacAlert("Aucun contrat actif", variant="info")
            layout.addWidget(alert)

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
        try:
            require('rh.declarations.edit')
        except PermissionError as e:
            QMessageBox.warning(self, "Accès refusé", str(e))
            return
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
        try:
            require('rh.formations.delete')
        except PermissionError as e:
            QMessageBox.warning(self, "Accès refusé", str(e))
            return
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

        btn_add = EmacButton("+ Nouvelle déclaration", variant="primary")
        btn_add.setVisible(can("rh.declarations.edit"))
        btn_add.clicked.connect(self._add_declaration)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        en_cours = donnees.get('en_cours')
        if en_cours:
            alert = EmacAlert(
                f"Déclaration en cours: {en_cours.get('type_declaration')} "
                f"du {self._format_date(en_cours.get('date_debut'))} "
                f"au {self._format_date(en_cours.get('date_fin'))}",
                variant="info"
            )
            layout.addWidget(alert)

        stats = donnees.get('statistiques', {})
        if stats:
            card = EmacCard("Statistiques des déclarations")
            stats_layout = QHBoxLayout()

            for type_decl, data in stats.items():
                count = data if isinstance(data, int) else data.get('nombre', 0)
                chip = EmacChip(f"{type_decl}: {count}", variant="info")
                stats_layout.addWidget(chip)

            stats_layout.addStretch()
            card.body.addLayout(stats_layout)
            layout.addWidget(card)

        declarations = donnees.get('declarations', [])
        card = EmacCard(f"Déclarations ({len(declarations)})")
        if declarations:
            for decl in declarations:
                frame = QFrame()
                frame.setStyleSheet("QFrame { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; }")
                row = QHBoxLayout(frame)
                row.setContentsMargins(12, 10, 12, 10)
                row.setSpacing(8)
                info_text = f"{decl.get('type_declaration', 'N/A')} - {self._format_date(decl.get('date_debut'))} au {self._format_date(decl.get('date_fin'))}"
                lbl = QLabel(info_text)
                lbl.setStyleSheet("background: transparent;")
                row.addWidget(lbl)
                row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.declarations.edit"))
                btn_edit.clicked.connect(lambda checked, d=decl: self._edit_declaration(d))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="danger")
                btn_delete.setVisible(can("rh.declarations.edit"))
                btn_delete.clicked.connect(lambda checked, d=decl: self._delete_declaration(d))
                row.addWidget(btn_delete)
                card.body.addWidget(frame)
        else:
            card.body.addWidget(QLabel("Aucune déclaration"))
        layout.addWidget(card)

        return container

    def _creer_resume_competences(self, donnees: dict) -> QWidget:
        """Crée le résumé des compétences transversales."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        btn_add = EmacButton("+ Nouvelle compétence", variant="primary")
        btn_add.setVisible(can("rh.competences.edit"))
        btn_add.clicked.connect(self._add_competence)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})

        expirees = stats.get('expirees', 0)
        if expirees > 0:
            alert = EmacAlert(f"{expirees} compétence(s) expirée(s) !", variant="error")
            layout.addWidget(alert)

        expire_bientot = stats.get('expire_bientot_30j', 0)
        if expire_bientot > 0:
            alert = EmacAlert(f"{expire_bientot} compétence(s) expirant dans les 30 jours", variant="warning")
            layout.addWidget(alert)

        card = EmacCard("Statistiques")
        stats_layout = QHBoxLayout()

        items = [
            ("Valides", stats.get('valides', 0)),
            ("Expirées", stats.get('expirees', 0)),
            ("Total", stats.get('total', 0)),
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

        competences = donnees.get('competences', [])
        card_list = EmacCard(f"Compétences ({len(competences)})")

        if competences:
            for comp in competences:
                frame = QFrame()
                frame.setStyleSheet("QFrame { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; }")
                row = QHBoxLayout(frame)
                row.setContentsMargins(12, 10, 12, 10)
                row.setSpacing(8)

                statut = comp.get('statut', 'valide')
                if statut == 'expiree':
                    indicator = "X"
                    color = "#ef4444"
                elif statut == 'expire_bientot':
                    indicator = "!"
                    color = "#f97316"
                elif statut == 'attention':
                    indicator = "~"
                    color = "#eab308"
                else:
                    indicator = "O"
                    color = "#22c55e"

                status_label = QLabel(indicator)
                status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px; background: transparent;")
                status_label.setFixedWidth(20)
                row.addWidget(status_label)

                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                libelle = comp.get('libelle', 'N/A')
                categorie = comp.get('categorie', '')
                if categorie:
                    libelle = f"{libelle} [{categorie}]"
                label_nom = QLabel(libelle)
                label_nom.setStyleSheet("font-weight: 500; background: transparent;")
                info_layout.addWidget(label_nom)

                date_acq = comp.get('date_acquisition')
                date_exp = comp.get('date_expiration')
                date_text = f"Acquis le: {self._format_date(date_acq)}"
                if date_exp:
                    date_text += f" - Expire le: {self._format_date(date_exp)}"
                else:
                    date_text += " - Permanent"

                label_dates = QLabel(date_text)
                label_dates.setStyleSheet("color: #64748b; font-size: 12px;")
                info_layout.addWidget(label_dates)

                if statut in ('expire_bientot', 'attention', 'expiree'):
                    statut_label = comp.get('statut_label', '')
                    if statut_label:
                        label_statut = QLabel(statut_label)
                        label_statut.setStyleSheet(f"color: {color}; font-size: 11px; font-style: italic;")
                        info_layout.addWidget(label_statut)

                row.addLayout(info_layout)
                row.addStretch()

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.competences.edit"))
                btn_edit.clicked.connect(lambda checked, c=comp: self._edit_competence(c))
                row.addWidget(btn_edit)

                btn_delete = EmacButton("Retirer", variant="danger")
                btn_delete.setVisible(can("rh.competences.delete"))
                btn_delete.clicked.connect(lambda checked, c=comp: self._delete_competence(c))
                row.addWidget(btn_delete)

                card_list.body.addWidget(frame)
        else:
            card_list.body.addWidget(QLabel("Aucune compétence assignée"))

        layout.addWidget(card_list)

        return container

    def _add_competence(self):
        """Ouvre le formulaire d'ajout de compétence."""
        if not self.operateur_selectionne:
            return
        dialog = EditCompetenceDialog(self.operateur_selectionne['id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_competence(self, competence: dict):
        """Ouvre le formulaire de modification de compétence."""
        dialog = EditCompetenceDialog(self.operateur_selectionne['id'], competence, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_competence(self, competence: dict):
        """Retire une compétence après confirmation."""
        try:
            require('rh.competences.delete')
        except PermissionError as e:
            QMessageBox.warning(self, "Accès refusé", str(e))
            return
        libelle = competence.get('libelle', 'cette compétence')
        reply = QMessageBox.question(
            self,
            "Confirmer le retrait",
            f"Voulez-vous vraiment retirer la compétence '{libelle}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = delete_competence_personnel(competence['assignment_id'])
            if success:
                QMessageBox.information(self, "Succès", message)
                self._charger_contenu_domaine()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _creer_resume_formation(self, donnees: dict) -> QWidget:
        """Crée le résumé des formations."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        btn_add = EmacButton("+ Nouvelle formation", variant="primary")
        btn_add.setVisible(can("rh.formations.edit"))
        btn_add.clicked.connect(self._add_formation)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        stats = donnees.get('statistiques', {})

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

        formations = donnees.get('formations', [])
        card_list = EmacCard(f"Formations ({len(formations)})")
        if formations:
            for form in formations:
                frame = QFrame()
                frame.setStyleSheet("QFrame { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; }")
                row = QHBoxLayout(frame)
                row.setContentsMargins(12, 10, 12, 10)
                row.setSpacing(8)
                info_text = f"{form.get('intitule', 'N/A')} - {form.get('statut', 'N/A')}"
                if form.get('date_debut'):
                    info_text += f" ({self._format_date(form.get('date_debut'))})"
                lbl = QLabel(info_text)
                lbl.setStyleSheet("background: transparent;")
                row.addWidget(lbl)
                row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.formations.edit"))
                btn_edit.clicked.connect(lambda checked, f=form: self._edit_formation(f))
                row.addWidget(btn_edit)
                btn_delete = EmacButton("Supprimer", variant="danger")
                btn_delete.setVisible(can("rh.formations.delete"))
                btn_delete.clicked.connect(lambda checked, f=form: self._delete_formation(f))
                row.addWidget(btn_delete)
                card_list.body.addWidget(frame)
        else:
            card_list.body.addWidget(QLabel("Aucune formation enregistrée"))
        layout.addWidget(card_list)

        return container

    def _creer_resume_medical(self, donnees: dict) -> QWidget:
        """Crée le résumé du suivi médical."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if donnees.get('error'):
            error_card = EmacCard("Erreur")
            error_card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            layout.addWidget(error_card)
            return container

        medical_info = donnees.get('medical') or {}
        visites = donnees.get('visites') or []
        accidents = donnees.get('accidents') or []
        validites = donnees.get('validites') or []
        alertes = donnees.get('alertes') or []

        self._donnees_medical = donnees

        if alertes:
            alertes_card = EmacCard("Alertes")
            for alerte in alertes:
                alert_widget = QFrame()
                alert_widget.setStyleSheet("""
                    QFrame {
                        background: #fef2f2;
                        border: 1px solid #fecaca;
                        border-radius: 6px;
                        padding: 8px 12px;
                        margin-bottom: 4px;
                    }
                """)
                alert_layout = QHBoxLayout(alert_widget)
                alert_layout.setContentsMargins(8, 4, 8, 4)
                lbl = QLabel(alerte.get('message', str(alerte)))
                lbl.setStyleSheet("color: #dc2626; font-weight: 500;")
                alert_layout.addWidget(lbl)
                alertes_card.body.addWidget(alert_widget)
            layout.addWidget(alertes_card)

        card_medical = EmacCard("Suivi Médical")
        grid = QGridLayout()
        grid.setSpacing(12)

        type_suivi = medical_info.get('type_suivi_vip') or "Non défini"
        periodicite = medical_info.get('periodicite_vip_mois') or 24

        infos = [
            ("Type de suivi VIP", type_suivi),
            ("Périodicité", f"{periodicite} mois"),
            ("Maladie professionnelle", "Oui" if medical_info.get('maladie_pro') else "Non"),
            ("Taux professionnel", f"{medical_info.get('taux_professionnel', 0)}%" if medical_info.get('taux_professionnel') else "-"),
        ]

        if medical_info.get('besoins_adaptation'):
            infos.append(("Besoins d'adaptation", medical_info.get('besoins_adaptation')))

        for i, (label, valeur) in enumerate(infos):
            r, c = divmod(i, 2)
            lbl = QLabel(f"<b>{label}</b><br/>{valeur}")
            lbl.setStyleSheet("padding: 8px 12px; background: #f0f4f8; border: 1px solid #cbd5e1; border-radius: 6px;")
            lbl.setWordWrap(True)
            grid.addWidget(lbl, r, c)

        card_medical.body.addLayout(grid)
        layout.addWidget(card_medical)

        from datetime import date as date_class
        rqth_validites = [v for v in validites if v.get('type_validite') == 'RQTH']
        oeth_validites = [v for v in validites if v.get('type_validite') == 'OETH']

        card_rqth = EmacCard("RQTH / OETH")
        rqth_layout = QHBoxLayout()

        rqth_frame = QFrame()
        rqth_frame.setStyleSheet("padding: 8px; background: #f0fdf4; border-radius: 6px;")
        rqth_inner = QVBoxLayout(rqth_frame)
        rqth_inner.addWidget(QLabel("<b>RQTH</b>"))
        if rqth_validites:
            latest_rqth = rqth_validites[0]
            date_fin = latest_rqth.get('date_fin')
            statut = "Active" if date_fin and date_fin >= date_class.today() else "Expirée"
            rqth_inner.addWidget(QLabel(f"Statut: {statut}"))
            rqth_inner.addWidget(QLabel(f"Fin: {self._format_date(date_fin)}"))
            if latest_rqth.get('taux_incapacite'):
                rqth_inner.addWidget(QLabel(f"Taux: {latest_rqth.get('taux_incapacite')}%"))
        else:
            rqth_inner.addWidget(QLabel("Non applicable"))
        rqth_layout.addWidget(rqth_frame)

        oeth_frame = QFrame()
        oeth_frame.setStyleSheet("padding: 8px; background: #eff6ff; border-radius: 6px;")
        oeth_inner = QVBoxLayout(oeth_frame)
        oeth_inner.addWidget(QLabel("<b>OETH</b>"))
        if oeth_validites:
            latest_oeth = oeth_validites[0]
            date_fin = latest_oeth.get('date_fin')
            statut = "Active" if date_fin and date_fin >= date_class.today() else "Expirée"
            oeth_inner.addWidget(QLabel(f"Statut: {statut}"))
            oeth_inner.addWidget(QLabel(f"Fin: {self._format_date(date_fin)}"))
        else:
            oeth_inner.addWidget(QLabel("Non applicable"))
        rqth_layout.addWidget(oeth_frame)

        card_rqth.body.addLayout(rqth_layout)
        layout.addWidget(card_rqth)

        card_visites = EmacCard(f"Visites médicales ({len(visites)})")

        btn_add_visite = EmacButton("+ Nouvelle visite", variant="primary")
        btn_add_visite.setVisible(can("rh.medical.edit"))
        btn_add_visite.clicked.connect(self._add_visite)
        card_visites.body.addWidget(btn_add_visite, alignment=Qt.AlignLeft)

        if visites:
            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["Date", "Type", "Résultat", "Médecin", "Prochaine", "Actions"])
            table.setRowCount(len(visites))
            hh = table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.Fixed); table.setColumnWidth(0, 100)
            hh.setSectionResizeMode(1, QHeaderView.Stretch)
            hh.setSectionResizeMode(2, QHeaderView.Fixed); table.setColumnWidth(2, 110)
            hh.setSectionResizeMode(3, QHeaderView.Stretch)
            hh.setSectionResizeMode(4, QHeaderView.Fixed); table.setColumnWidth(4, 100)
            hh.setSectionResizeMode(5, QHeaderView.Fixed); table.setColumnWidth(5, 220)
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.verticalHeader().setDefaultSectionSize(52)

            for row_idx, visite in enumerate(visites):
                table.setItem(row_idx, 0, QTableWidgetItem(self._format_date(visite.get('date_visite'))))
                table.setItem(row_idx, 1, QTableWidgetItem(visite.get('type_visite', '-')))
                table.setItem(row_idx, 2, QTableWidgetItem(visite.get('resultat', '-')))
                table.setItem(row_idx, 3, QTableWidgetItem(visite.get('medecin', '-')))
                table.setItem(row_idx, 4, QTableWidgetItem(self._format_date(visite.get('prochaine_visite'))))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(4, 4, 4, 4)
                btn_layout_inner.setSpacing(6)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.medical.edit"))
                btn_edit.clicked.connect(lambda checked, v=visite: self._edit_visite(v))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="danger")
                btn_del.setVisible(can("rh.medical.edit"))
                btn_del.clicked.connect(lambda checked, v=visite: self._delete_visite(v))
                btn_layout_inner.addWidget(btn_del)

                table.setCellWidget(row_idx, 5, btn_widget)

            _h = min(len(visites) * 52 + 32, 420)
            table.setFixedHeight(_h)
            card_visites.body.addWidget(table)
        else:
            card_visites.body.addWidget(QLabel("Aucune visite enregistrée"))

        layout.addWidget(card_visites)

        card_accidents = EmacCard(f"Accidents du travail ({len(accidents)})")

        btn_add_accident = EmacButton("+ Nouvel accident", variant="primary")
        btn_add_accident.setVisible(can("rh.medical.edit"))
        btn_add_accident.clicked.connect(self._add_accident)
        card_accidents.body.addWidget(btn_add_accident, alignment=Qt.AlignLeft)

        if accidents:
            for acc in accidents:
                frame = QFrame()
                frame.setStyleSheet("""
                    QFrame {
                        background: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                    }
                """)
                frame_layout = QVBoxLayout(frame)
                frame_layout.setContentsMargins(12, 8, 12, 8)
                frame_layout.setSpacing(4)

                header_row = QHBoxLayout()
                date_lbl = QLabel(f"<b>{self._format_date(acc.get('date_accident'))}</b>")
                header_row.addWidget(date_lbl)
                avec_arret = acc.get('avec_arret')
                arret_style = "padding: 2px 8px; border-radius: 10px; font-size: 11px; background: #fef3c7; color: #92400e;" if avec_arret else "padding: 2px 8px; border-radius: 10px; font-size: 11px; background: #f0fdf4; color: #166534;"
                arret_lbl = QLabel("Avec arrêt" if avec_arret else "Sans arrêt")
                arret_lbl.setStyleSheet(arret_style)
                header_row.addWidget(arret_lbl)
                jours = acc.get('nb_jours_absence')
                if jours:
                    jours_lbl = QLabel(f"{jours} jour(s) d'absence")
                    jours_lbl.setStyleSheet("color: #64748b; font-size: 12px;")
                    header_row.addWidget(jours_lbl)
                header_row.addStretch()
                frame_layout.addLayout(header_row)

                details = []
                if acc.get('siege_lesions'):
                    details.append(f"Siège : {acc.get('siege_lesions')}")
                if acc.get('nature_lesions'):
                    details.append(f"Nature : {acc.get('nature_lesions')}")
                if details:
                    detail_lbl = QLabel("  ·  ".join(details))
                    detail_lbl.setStyleSheet("color: #475569; font-size: 12px;")
                    frame_layout.addWidget(detail_lbl)

                actions_row = QHBoxLayout()
                actions_row.addStretch()
                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.medical.edit"))
                btn_edit.clicked.connect(lambda checked, a=acc: self._edit_accident(a))
                actions_row.addWidget(btn_edit)
                btn_del = EmacButton("Supprimer", variant="danger")
                btn_del.setVisible(can("rh.medical.edit"))
                btn_del.clicked.connect(lambda checked, a=acc: self._delete_accident(a))
                actions_row.addWidget(btn_del)
                frame_layout.addLayout(actions_row)

                card_accidents.body.addWidget(frame)
        else:
            card_accidents.body.addWidget(QLabel("Aucun accident enregistré"))

        layout.addWidget(card_accidents)

        return container

    def _creer_resume_vie_salarie(self, donnees: dict) -> QWidget:
        """Crée le résumé de la vie du salarié."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if donnees.get('error'):
            error_card = EmacCard("Erreur")
            error_card.body.addWidget(QLabel(f"Erreur: {donnees['error']}"))
            layout.addWidget(error_card)
            return container

        sanctions_data = donnees.get('sanctions', {})
        alcoolemie_data = donnees.get('alcoolemie', {})
        salivaire_data = donnees.get('tests_salivaires', {})
        entretiens_data = donnees.get('entretiens', {})
        alertes = donnees.get('alertes', [])

        self._donnees_vie_salarie = donnees

        if alertes:
            alertes_card = EmacCard("Alertes")
            for alerte in alertes:
                alert_widget = QFrame()
                alert_widget.setStyleSheet("""
                    QFrame {
                        background: #fef2f2;
                        border: 1px solid #fecaca;
                        border-radius: 6px;
                        padding: 8px 12px;
                        margin-bottom: 4px;
                    }
                """)
                alert_layout = QHBoxLayout(alert_widget)
                alert_layout.setContentsMargins(8, 4, 8, 4)
                lbl = QLabel(alerte.get('message', str(alerte)))
                lbl.setStyleSheet("color: #dc2626; font-weight: 500;")
                alert_layout.addWidget(lbl)
                alertes_card.body.addWidget(alert_widget)
            layout.addWidget(alertes_card)

        card_recap = EmacCard("Récapitulatif")
        recap_layout = QHBoxLayout()

        sanctions_frame = QFrame()
        sanctions_frame.setStyleSheet("padding: 12px; background: #fef3c7; border-radius: 8px;")
        sanctions_inner = QVBoxLayout(sanctions_frame)
        sanctions_inner.addWidget(QLabel("<b>Sanctions</b>"))
        nb_sanctions = sanctions_data.get('total', 0) if isinstance(sanctions_data, dict) else 0
        sanctions_inner.addWidget(QLabel(f"Total: {nb_sanctions}"))
        if isinstance(sanctions_data, dict) and sanctions_data.get('derniere_sanction'):
            sanctions_inner.addWidget(QLabel(f"Dernière: {self._format_date(sanctions_data.get('derniere_sanction'))}"))
        recap_layout.addWidget(sanctions_frame)

        alcool_frame = QFrame()
        alcool_frame.setStyleSheet("padding: 12px; background: #dbeafe; border-radius: 8px;")
        alcool_inner = QVBoxLayout(alcool_frame)
        alcool_inner.addWidget(QLabel("<b>Contrôles alcool</b>"))
        nb_alcool = alcoolemie_data.get('total', 0) if isinstance(alcoolemie_data, dict) else 0
        nb_positifs = alcoolemie_data.get('positifs', 0) if isinstance(alcoolemie_data, dict) else 0
        alcool_inner.addWidget(QLabel(f"Total: {nb_alcool}"))
        alcool_inner.addWidget(QLabel(f"Positifs: {nb_positifs}"))
        recap_layout.addWidget(alcool_frame)

        salivaire_frame = QFrame()
        salivaire_frame.setStyleSheet("padding: 12px; background: #f3e8ff; border-radius: 8px;")
        salivaire_inner = QVBoxLayout(salivaire_frame)
        salivaire_inner.addWidget(QLabel("<b>Tests salivaires</b>"))
        nb_salivaire = salivaire_data.get('total', 0) if isinstance(salivaire_data, dict) else 0
        nb_positifs_sal = salivaire_data.get('positifs', 0) if isinstance(salivaire_data, dict) else 0
        salivaire_inner.addWidget(QLabel(f"Total: {nb_salivaire}"))
        salivaire_inner.addWidget(QLabel(f"Positifs: {nb_positifs_sal}"))
        recap_layout.addWidget(salivaire_frame)

        entretiens_frame = QFrame()
        entretiens_frame.setStyleSheet("padding: 12px; background: #dcfce7; border-radius: 8px;")
        entretiens_inner = QVBoxLayout(entretiens_frame)
        entretiens_inner.addWidget(QLabel("<b>Entretiens</b>"))
        dernier_epp = entretiens_data.get('dernier_epp') if isinstance(entretiens_data, dict) else None
        dernier_eap = entretiens_data.get('dernier_eap') if isinstance(entretiens_data, dict) else None
        entretiens_inner.addWidget(QLabel(f"EPP: {self._format_date(dernier_epp) if dernier_epp else '-'}"))
        entretiens_inner.addWidget(QLabel(f"EAP: {self._format_date(dernier_eap) if dernier_eap else '-'}"))
        recap_layout.addWidget(entretiens_frame)

        card_recap.body.addLayout(recap_layout)
        layout.addWidget(card_recap)

        sanctions_list = donnees.get('sanctions_liste', [])
        card_sanctions = EmacCard(f"Sanctions disciplinaires ({len(sanctions_list)})")

        btn_add_sanction = EmacButton("+ Nouvelle sanction", variant="primary")
        btn_add_sanction.setVisible(can("rh.vie_salarie.edit"))
        btn_add_sanction.clicked.connect(self._add_sanction)
        card_sanctions.body.addWidget(btn_add_sanction, alignment=Qt.AlignLeft)

        if sanctions_list:
            table_sanctions = QTableWidget()
            table_sanctions.setColumnCount(5)
            table_sanctions.setHorizontalHeaderLabels(["Date", "Type", "Durée", "Motif", "Actions"])
            table_sanctions.setRowCount(len(sanctions_list))
            hh_s = table_sanctions.horizontalHeader()
            hh_s.setSectionResizeMode(0, QHeaderView.Fixed); table_sanctions.setColumnWidth(0, 100)
            hh_s.setSectionResizeMode(1, QHeaderView.Fixed); table_sanctions.setColumnWidth(1, 150)
            hh_s.setSectionResizeMode(2, QHeaderView.Fixed); table_sanctions.setColumnWidth(2, 70)
            hh_s.setSectionResizeMode(3, QHeaderView.Stretch)
            hh_s.setSectionResizeMode(4, QHeaderView.Fixed); table_sanctions.setColumnWidth(4, 220)
            table_sanctions.setAlternatingRowColors(True)
            table_sanctions.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_sanctions.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table_sanctions.verticalHeader().setDefaultSectionSize(52)

            for row_idx, sanc in enumerate(sanctions_list):
                table_sanctions.setItem(row_idx, 0, QTableWidgetItem(self._format_date(sanc.get('date_sanction'))))
                table_sanctions.setItem(row_idx, 1, QTableWidgetItem(sanc.get('type_sanction', '-')))
                table_sanctions.setItem(row_idx, 2, QTableWidgetItem(str(sanc.get('duree_jours', '-')) if sanc.get('duree_jours') else '-'))
                motif = sanc.get('motif', '-')
                if motif and len(motif) > 50:
                    motif = motif[:50] + "..."
                table_sanctions.setItem(row_idx, 3, QTableWidgetItem(motif))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(4, 4, 4, 4)
                btn_layout_inner.setSpacing(6)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.vie_salarie.edit"))
                btn_edit.clicked.connect(lambda checked, s=sanc: self._edit_sanction(s))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="danger")
                btn_del.setVisible(can("rh.vie_salarie.edit"))
                btn_del.clicked.connect(lambda checked, s=sanc: self._delete_sanction(s))
                btn_layout_inner.addWidget(btn_del)

                table_sanctions.setCellWidget(row_idx, 4, btn_widget)

            _h = min(len(sanctions_list) * 52 + 32, 420)
            table_sanctions.setFixedHeight(_h)
            card_sanctions.body.addWidget(table_sanctions)
        else:
            card_sanctions.body.addWidget(QLabel("Aucune sanction enregistrée"))

        layout.addWidget(card_sanctions)

        controles_alcool = donnees.get('controles_alcool_liste', [])
        controles_salivaire = donnees.get('tests_salivaires_liste', [])

        card_controles = EmacCard("Contrôles (Alcool / Salivaire)")

        btn_layout_ctrl = QHBoxLayout()
        btn_add_alcool = EmacButton("+ Contrôle alcool", variant="primary")
        btn_add_alcool.setVisible(can("rh.vie_salarie.edit"))
        btn_add_alcool.clicked.connect(self._add_controle_alcool)
        btn_layout_ctrl.addWidget(btn_add_alcool)

        btn_add_salivaire = EmacButton("+ Test salivaire", variant="primary")
        btn_add_salivaire.setVisible(can("rh.vie_salarie.edit"))
        btn_add_salivaire.clicked.connect(self._add_test_salivaire)
        btn_layout_ctrl.addWidget(btn_add_salivaire)
        btn_layout_ctrl.addStretch()
        card_controles.body.addLayout(btn_layout_ctrl)

        tables_layout = QHBoxLayout()

        ROW_H = 30

        alcool_container = QVBoxLayout()
        alcool_container.addWidget(QLabel("<b>Alcoolémie</b>"))
        if controles_alcool:
            table_alcool = QTableWidget()
            table_alcool.setColumnCount(3)
            table_alcool.setHorizontalHeaderLabels(["Date", "Résultat", "Taux"])
            table_alcool.setRowCount(len(controles_alcool))
            hh_a = table_alcool.horizontalHeader()
            hh_a.setSectionResizeMode(0, QHeaderView.Fixed); table_alcool.setColumnWidth(0, 95)
            hh_a.setSectionResizeMode(1, QHeaderView.Stretch)
            hh_a.setSectionResizeMode(2, QHeaderView.Fixed); table_alcool.setColumnWidth(2, 80)
            table_alcool.setAlternatingRowColors(True)
            table_alcool.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table_alcool.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_alcool.verticalHeader().setDefaultSectionSize(ROW_H)
            for row_idx, ctrl in enumerate(controles_alcool):
                table_alcool.setItem(row_idx, 0, QTableWidgetItem(self._format_date(ctrl.get('date_controle'))))
                table_alcool.setItem(row_idx, 1, QTableWidgetItem(ctrl.get('resultat', '-')))
                table_alcool.setItem(row_idx, 2, QTableWidgetItem(f"{ctrl.get('taux')} g/L" if ctrl.get('taux') else '-'))
            table_alcool.setFixedHeight(min(len(controles_alcool), 8) * ROW_H + 32)
            alcool_container.addWidget(table_alcool)
        else:
            alcool_container.addWidget(QLabel("Aucun contrôle"))
        tables_layout.addLayout(alcool_container)

        salivaire_container = QVBoxLayout()
        salivaire_container.addWidget(QLabel("<b>Tests salivaires</b>"))
        if controles_salivaire:
            table_salivaire = QTableWidget()
            table_salivaire.setColumnCount(2)
            table_salivaire.setHorizontalHeaderLabels(["Date", "Résultat"])
            table_salivaire.setRowCount(len(controles_salivaire))
            table_salivaire.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_salivaire.setAlternatingRowColors(True)
            table_salivaire.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table_salivaire.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_salivaire.verticalHeader().setDefaultSectionSize(ROW_H)
            for row_idx, test in enumerate(controles_salivaire):
                table_salivaire.setItem(row_idx, 0, QTableWidgetItem(self._format_date(test.get('date_test'))))
                table_salivaire.setItem(row_idx, 1, QTableWidgetItem(test.get('resultat', '-')))
            table_salivaire.setFixedHeight(min(len(controles_salivaire), 8) * ROW_H + 32)
            salivaire_container.addWidget(table_salivaire)
        else:
            salivaire_container.addWidget(QLabel("Aucun test"))
        tables_layout.addLayout(salivaire_container)

        card_controles.body.addLayout(tables_layout)
        layout.addWidget(card_controles)

        entretiens_liste = donnees.get('entretiens_liste', [])
        card_entretiens = EmacCard(f"Entretiens professionnels ({len(entretiens_liste)})")

        btn_add_entretien = EmacButton("+ Nouvel entretien", variant="primary")
        btn_add_entretien.setVisible(can("rh.vie_salarie.edit"))
        btn_add_entretien.clicked.connect(self._add_entretien)
        card_entretiens.body.addWidget(btn_add_entretien, alignment=Qt.AlignLeft)

        if entretiens_liste:
            table_entretiens = QTableWidget()
            table_entretiens.setColumnCount(5)
            table_entretiens.setHorizontalHeaderLabels(["Date", "Type", "Manager", "Prochaine", "Actions"])
            table_entretiens.setRowCount(len(entretiens_liste))
            hh_e = table_entretiens.horizontalHeader()
            hh_e.setSectionResizeMode(0, QHeaderView.Fixed); table_entretiens.setColumnWidth(0, 100)
            hh_e.setSectionResizeMode(1, QHeaderView.Stretch)
            hh_e.setSectionResizeMode(2, QHeaderView.Stretch)
            hh_e.setSectionResizeMode(3, QHeaderView.Fixed); table_entretiens.setColumnWidth(3, 100)
            hh_e.setSectionResizeMode(4, QHeaderView.Fixed); table_entretiens.setColumnWidth(4, 220)
            table_entretiens.setAlternatingRowColors(True)
            table_entretiens.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_entretiens.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table_entretiens.verticalHeader().setDefaultSectionSize(52)

            for row_idx, ent in enumerate(entretiens_liste):
                table_entretiens.setItem(row_idx, 0, QTableWidgetItem(self._format_date(ent.get('date_entretien'))))
                table_entretiens.setItem(row_idx, 1, QTableWidgetItem(ent.get('type_entretien', '-')))
                table_entretiens.setItem(row_idx, 2, QTableWidgetItem(ent.get('manager_nom', '-')))
                table_entretiens.setItem(row_idx, 3, QTableWidgetItem(self._format_date(ent.get('prochaine_date'))))

                btn_widget = QWidget()
                btn_layout_inner = QHBoxLayout(btn_widget)
                btn_layout_inner.setContentsMargins(4, 4, 4, 4)
                btn_layout_inner.setSpacing(6)

                btn_edit = EmacButton("Modifier", variant="outline")
                btn_edit.setVisible(can("rh.vie_salarie.edit"))
                btn_edit.clicked.connect(lambda checked, e=ent: self._edit_entretien(e))
                btn_layout_inner.addWidget(btn_edit)

                btn_del = EmacButton("Suppr.", variant="danger")
                btn_del.setVisible(can("rh.vie_salarie.edit"))
                btn_del.clicked.connect(lambda checked, e=ent: self._delete_entretien(e))
                btn_layout_inner.addWidget(btn_del)

                table_entretiens.setCellWidget(row_idx, 4, btn_widget)

            _h = min(len(entretiens_liste) * 52 + 32, 420)
            table_entretiens.setFixedHeight(_h)
            card_entretiens.body.addWidget(table_entretiens)
        else:
            card_entretiens.body.addWidget(QLabel("Aucun entretien enregistré"))

        layout.addWidget(card_entretiens)

        return container

    def _creer_resume_polyvalence(self, donnees: dict) -> QWidget:
        """Crée la section polyvalence : niveaux par poste + dossiers de formation."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        polyvalences = donnees.get('polyvalences', [])

        if not polyvalences:
            card_empty = EmacCard("Polyvalence")
            card_empty.body.addWidget(QLabel("Aucune polyvalence enregistrée pour cet opérateur."))
            layout.addWidget(card_empty)
            return container

        if can("production.grilles.export") or can("admin.permissions"):
            btn_admin = EmacButton("Gérer les dossiers de formation", variant="ghost")
            btn_admin.clicked.connect(self._ouvrir_gestion_docs_formation)
            layout.addWidget(btn_admin, alignment=Qt.AlignRight)

        NIVEAU_LABELS = {
            1: "Niv.1 - Apprentissage",
            2: "Niv.2 - En cours",
            3: "Niv.3 - Autonome",
            4: "Niv.4 - Expert/Formateur",
        }
        NIVEAU_COLORS = {1: "#ef4444", 2: "#f97316", 3: "#3b82f6", 4: "#22c55e"}

        ateliers = {}
        for poly in polyvalences:
            atelier = poly.get('atelier_nom') or 'Sans atelier'
            ateliers.setdefault(atelier, []).append(poly)

        for atelier_nom, postes in ateliers.items():
            card = EmacCard(atelier_nom)

            for poly in postes:
                poste_code = poly.get('poste_code', '?')
                niveau = poly.get('niveau')
                docs = poly.get('documents', [])

                poste_row = QHBoxLayout()
                poste_row.setSpacing(8)

                badge_poste = QLabel(f"<b>{poste_code}</b>")
                badge_poste.setStyleSheet("font-size: 14px; min-width: 60px;")
                poste_row.addWidget(badge_poste)

                niveau_label = NIVEAU_LABELS.get(niveau, f"Niveau {niveau}") if niveau else "Niveau non défini"
                color = NIVEAU_COLORS.get(niveau, "#6b7280")
                badge_niv = QLabel(niveau_label)
                badge_niv.setStyleSheet(
                    f"background: {color}20; color: {color}; border: 1px solid {color}60;"
                    " border-radius: 4px; padding: 2px 8px; font-size: 12px;"
                )
                poste_row.addWidget(badge_niv)

                prochaine = poly.get('prochaine_evaluation')
                if prochaine:
                    lbl_date = QLabel(f"  Prochaine éval : {self._format_date(prochaine)}")
                    lbl_date.setStyleSheet("color: #6b7280; font-size: 11px;")
                    poste_row.addWidget(lbl_date)

                poste_row.addStretch()
                card.body.addLayout(poste_row)

                if docs:
                    docs_container = QWidget()
                    docs_container.setStyleSheet(
                        "background: #f8fafc; border-left: 3px solid #cbd5e1;"
                        " border-radius: 4px; margin-left: 8px;"
                    )
                    docs_layout = QVBoxLayout(docs_container)
                    docs_layout.setContentsMargins(10, 4, 8, 4)
                    docs_layout.setSpacing(3)

                    titre_docs = QLabel("Dossiers de formation :")
                    titre_docs.setStyleSheet("color: #475569; font-size: 11px; font-style: italic;")
                    docs_layout.addWidget(titre_docs)

                    for doc in docs:
                        doc_row = QHBoxLayout()
                        doc_row.setSpacing(6)

                        doc_nom = QLabel(f"📄 {doc.get('nom_affichage', doc.get('nom_fichier', '?'))}")
                        doc_nom.setStyleSheet("font-size: 12px;")
                        if doc.get('description'):
                            doc_nom.setToolTip(doc['description'])
                        doc_row.addWidget(doc_nom)
                        doc_row.addStretch()

                        btn_lire = EmacButton("Lire", variant="outline")
                        btn_lire.setFixedHeight(24)
                        btn_lire.setFixedWidth(55)
                        doc_id = doc['id']
                        btn_lire.clicked.connect(
                            lambda checked, did=doc_id: self._ouvrir_doc_formation(did)
                        )
                        doc_row.addWidget(btn_lire)
                        docs_layout.addLayout(doc_row)

                    card.body.addWidget(docs_container)
                else:
                    lbl_no_doc = QLabel("     Aucun dossier de formation joint pour ce niveau")
                    lbl_no_doc.setStyleSheet("color: #9ca3af; font-size: 11px; font-style: italic;")
                    card.body.addWidget(lbl_no_doc)

                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet("background: #e2e8f0; margin: 4px 0;")
                card.body.addWidget(sep)

            layout.addWidget(card)

        return container

    def _ouvrir_doc_formation(self, doc_id: int):
        """Ouvre un dossier de formation polyvalence."""
        import os
        from core.services.polyvalence_docs_service import extraire_vers_fichier_temp
        temp_path = extraire_vers_fichier_temp(doc_id)
        if temp_path and temp_path.exists():
            if os.name == 'nt':
                os.startfile(str(temp_path))
            else:
                import subprocess
                subprocess.run(['xdg-open', str(temp_path)])
        else:
            QMessageBox.warning(self, "Fichier introuvable",
                                "Le dossier de formation n'a pas pu être ouvert.")

    def _ouvrir_gestion_docs_formation(self):
        """Ouvre le dialog d'administration des dossiers de formation."""
        from core.gui.dialogs.gestion_rh_dialogs import GestionDocsFormationDialog
        dialog = GestionDocsFormationDialog(self)
        dialog.exec_()
        if self.domaine_actif == DomaineRH.POLYVALENCE:
            self._charger_contenu_domaine()

    # =========================================================================
    # HANDLERS MÉDICAUX
    # =========================================================================

    def _add_visite(self):
        """Ajoute une nouvelle visite médicale."""
        if not self.operateur_selectionne:
            return
        dialog = EditVisiteDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_visite(self, visite: dict):
        """Modifie une visite médicale."""
        if not self.operateur_selectionne:
            return
        dialog = EditVisiteDialog(self.operateur_selectionne['id'], visite, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_visite(self, visite: dict):
        """Supprime une visite médicale."""
        try:
            require('rh.medical.delete')
        except PermissionError as e:
            QMessageBox.warning(self, "Accès refusé", str(e))
            return
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la visite du {self._format_date(visite.get('date_visite'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_visite(visite['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    def _add_accident(self):
        """Ajoute un nouvel accident du travail."""
        if not self.operateur_selectionne:
            return
        dialog = EditAccidentDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_accident(self, accident: dict):
        """Modifie un accident du travail."""
        if not self.operateur_selectionne:
            return
        dialog = EditAccidentDialog(self.operateur_selectionne['id'], accident, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_accident(self, accident: dict):
        """Supprime un accident du travail."""
        try:
            require('rh.medical.delete')
        except PermissionError as e:
            QMessageBox.warning(self, "Accès refusé", str(e))
            return
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'accident du {self._format_date(accident.get('date_accident'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_accident(accident['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    # =========================================================================
    # HANDLERS VIE DU SALARIÉ
    # =========================================================================

    def _add_sanction(self):
        """Ajoute une nouvelle sanction."""
        if not self.operateur_selectionne:
            return
        dialog = EditSanctionDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_sanction(self, sanction: dict):
        """Modifie une sanction."""
        if not self.operateur_selectionne:
            return
        dialog = EditSanctionDialog(self.operateur_selectionne['id'], sanction, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_sanction(self, sanction: dict):
        """Supprime une sanction."""
        try:
            require('rh.vie_salarie.edit')
        except PermissionError as e:
            QMessageBox.warning(self, "Accès refusé", str(e))
            return
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la sanction du {self._format_date(sanction.get('date_sanction'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_sanction(sanction['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    def _add_controle_alcool(self):
        """Ajoute un contrôle d'alcoolémie."""
        if not self.operateur_selectionne:
            return
        dialog = EditControleAlcoolDialog(self.operateur_selectionne['id'], self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_test_salivaire(self):
        """Ajoute un test salivaire."""
        if not self.operateur_selectionne:
            return
        dialog = EditTestSalivaireDialog(self.operateur_selectionne['id'], self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _add_entretien(self):
        """Ajoute un entretien professionnel."""
        if not self.operateur_selectionne:
            return
        dialog = EditEntretienDialog(self.operateur_selectionne['id'], None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _edit_entretien(self, entretien: dict):
        """Modifie un entretien professionnel."""
        if not self.operateur_selectionne:
            return
        dialog = EditEntretienDialog(self.operateur_selectionne['id'], entretien, self)
        if dialog.exec_() == QDialog.Accepted:
            self._charger_contenu_domaine()

    def _delete_entretien(self, entretien: dict):
        """Supprime un entretien professionnel."""
        try:
            require('rh.vie_salarie.edit')
        except PermissionError as e:
            QMessageBox.warning(self, "Accès refusé", str(e))
            return
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'entretien du {self._format_date(entretien.get('date_entretien'))} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = delete_entretien(entretien['id'])
            if success:
                self._charger_contenu_domaine()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    # =========================================================================
    # DOCUMENTS
    # =========================================================================

    def _creer_widget_documents(self, documents: list) -> QWidget:
        """Crée le widget affichant les documents du domaine (actifs uniquement)."""
        docs_actifs = [d for d in documents if d.get('statut') != 'archive']

        card = EmacCard(f"Documents associés ({len(docs_actifs)})")

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 10)

        btn_ajouter = EmacButton("+ Ajouter un document", variant="primary")
        btn_ajouter.setVisible(can("rh.documents.edit"))
        btn_ajouter.clicked.connect(self._ajouter_document)
        btn_layout.addWidget(btn_ajouter)

        btn_layout.addStretch()
        card.body.addLayout(btn_layout)

        if not docs_actifs:
            label = QLabel("Aucun document pour ce domaine")
            label.setStyleSheet("color: #9ca3af; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(label)
        else:
            for doc in docs_actifs:
                doc_widget = QFrame()
                doc_widget.setStyleSheet("""
                    QFrame {
                        background: #f9fafb;
                        border: 1px solid #e5e7eb;
                        border-radius: 8px;
                        padding: 10px;
                        margin: 2px 0;
                    }
                    QFrame:hover {
                        background: #f3f4f6;
                        border-color: #3b82f6;
                    }
                """)

                doc_layout = QHBoxLayout(doc_widget)
                doc_layout.setContentsMargins(10, 8, 10, 8)

                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                nom_label = QLabel(doc.get('nom_affichage', '-'))
                nom_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
                nom_label.setStyleSheet("color: #1f2937; background: transparent;")
                info_layout.addWidget(nom_label)

                details = f"{doc.get('categorie_nom', '-')} • Ajouté le {self._format_date(doc.get('date_upload'))}"
                if doc.get('date_expiration'):
                    details += f" • Expire le {self._format_date(doc.get('date_expiration'))}"
                details_label = QLabel(details)
                details_label.setStyleSheet("color: #6b7280; font-size: 11px; background: transparent;")
                info_layout.addWidget(details_label)

                doc_layout.addLayout(info_layout, 1)

                doc_id = doc.get('id')

                btn_archiver = QPushButton("📦 Archiver")
                btn_archiver.setVisible(can("rh.documents.edit"))
                btn_archiver.setCursor(Qt.PointingHandCursor)
                btn_archiver.setStyleSheet("""
                    QPushButton {
                        background: #f59e0b;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #d97706;
                    }
                """)
                btn_archiver.clicked.connect(lambda checked, d=doc_id: self._archiver_document_par_id(d))
                doc_layout.addWidget(btn_archiver)

                btn_ouvrir = QPushButton("📂 Ouvrir")
                btn_ouvrir.setCursor(Qt.PointingHandCursor)
                btn_ouvrir.setStyleSheet("""
                    QPushButton {
                        background: #3b82f6;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #2563eb;
                    }
                """)
                btn_ouvrir.clicked.connect(lambda checked, d=doc_id: self._ouvrir_document_par_id(d))
                doc_layout.addWidget(btn_ouvrir)

                card.body.addWidget(doc_widget)

        return card

    def _restaurer_document_par_id(self, doc_id: int):
        """Restaure un document archivé."""
        from core.services.document_service import DocumentService

        reply = QMessageBox.question(
            self,
            "Confirmer la restauration",
            "Voulez-vous restaurer ce document ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            try:
                doc_service = DocumentService()
                success, message = doc_service.restore_document(doc_id)

                if success:
                    QMessageBox.information(self, "Succès", "Document restauré avec succès")
                    self._charger_contenu_domaine()
                    self._update_archives_tab()
                else:
                    QMessageBox.warning(self, "Erreur", message)
            except Exception as e:
                logger.exception(f"Erreur restauration document: {e}")
                QMessageBox.critical(self, "Erreur", "Impossible de restaurer le document")

    def _ouvrir_document_par_id(self, doc_id: int):
        """Ouvre un document par son ID."""
        from core.services.document_service import DocumentService
        doc_service = DocumentService()
        doc_path = doc_service.get_document_path(doc_id)

        if doc_path and doc_path.exists():
            import os
            if os.name == 'nt':
                os.startfile(str(doc_path))
            else:
                import subprocess
                subprocess.run(['xdg-open', str(doc_path)])
        else:
            QMessageBox.warning(self, "Erreur", "Le fichier n'a pas été trouvé sur le disque")

    def _archiver_document_par_id(self, doc_id: int):
        """Archive un document après confirmation."""
        from core.services.document_service import DocumentService

        reply = QMessageBox.question(
            self,
            "Confirmer l'archivage",
            "Voulez-vous archiver ce document ?\n\nIl ne sera plus visible dans la liste mais pourra être restauré via l'onglet Archives.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                doc_service = DocumentService()
                success, message = doc_service.archive_document(doc_id)

                if success:
                    QMessageBox.information(self, "Succès", "Document archivé avec succès")
                    self._charger_contenu_domaine()
                    self._update_archives_tab()
                else:
                    QMessageBox.warning(self, "Erreur", message)
            except Exception as e:
                logger.exception(f"Erreur archivage document: {e}")

    def _charger_contenu_archives(self):
        """Charge et affiche les documents archivés."""
        if not self.operateur_selectionne:
            return

        operateur_id = self.operateur_selectionne['id']

        self._vider_layout(self.layout_resume)
        self._vider_layout(self.layout_documents)

        archives = get_documents_archives_operateur(operateur_id)

        card = EmacCard(f"📦 Documents archivés ({len(archives)})")

        if not archives:
            label = QLabel("Aucun document archivé")
            label.setStyleSheet("color: #9ca3af; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            card.body.addWidget(label)
        else:
            for doc in archives:
                doc_widget = QFrame()
                doc_widget.setStyleSheet("""
                    QFrame {
                        background: #f3f4f6;
                        border: 1px dashed #9ca3af;
                        border-radius: 8px;
                        padding: 10px;
                        margin: 2px 0;
                    }
                    QFrame:hover {
                        background: #e5e7eb;
                        border-color: #6b7280;
                    }
                """)

                doc_layout = QHBoxLayout(doc_widget)
                doc_layout.setContentsMargins(10, 8, 10, 8)

                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                nom_label = QLabel(f"📦 {doc.get('nom_affichage', '-')}")
                nom_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
                nom_label.setStyleSheet("color: #6b7280; background: transparent;")
                info_layout.addWidget(nom_label)

                details = f"{doc.get('categorie_nom', '-')} • Ajouté le {self._format_date(doc.get('date_upload'))}"
                details_label = QLabel(details)
                details_label.setStyleSheet("color: #9ca3af; font-size: 11px; background: transparent;")
                info_layout.addWidget(details_label)

                doc_layout.addLayout(info_layout, 1)

                doc_id = doc.get('id')

                btn_restaurer = QPushButton("🔄 Restaurer")
                btn_restaurer.setVisible(can("rh.documents.edit"))
                btn_restaurer.setCursor(Qt.PointingHandCursor)
                btn_restaurer.setStyleSheet("""
                    QPushButton {
                        background: #10b981;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #059669;
                    }
                """)
                btn_restaurer.clicked.connect(lambda checked, d=doc_id: self._restaurer_document_par_id(d))
                doc_layout.addWidget(btn_restaurer)

                btn_ouvrir = QPushButton("📂 Ouvrir")
                btn_ouvrir.setCursor(Qt.PointingHandCursor)
                btn_ouvrir.setStyleSheet("""
                    QPushButton {
                        background: #3b82f6;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #2563eb;
                    }
                """)
                btn_ouvrir.clicked.connect(lambda checked, d=doc_id: self._ouvrir_document_par_id(d))
                doc_layout.addWidget(btn_ouvrir)

                card.body.addWidget(doc_widget)

        self.layout_resume.addWidget(card)

    def _ajouter_document(self):
        """Ouvre le dialogue pour ajouter un document."""
        if not self.operateur_selectionne:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un opérateur")
            return

        dialog = AjouterDocumentDialog(
            operateur_id=self.operateur_selectionne['id'],
            domaine=self.domaine_actif,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            self._afficher_details_operateur()

    def _ouvrir_document(self):
        """Ouvre le document sélectionné."""
        if not hasattr(self, 'documents_table'):
            return

        current_row = self.documents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un document")
            return

        doc_id = int(self.documents_table.item(current_row, 0).text())

        from core.services.document_service import DocumentService
        doc_service = DocumentService()
        doc_path = doc_service.get_document_path(doc_id)

        if doc_path and doc_path.exists():
            import os
            import subprocess
            if os.name == 'nt':
                os.startfile(str(doc_path))
            elif os.name == 'posix':
                subprocess.run(['xdg-open', str(doc_path)])
        else:
            QMessageBox.warning(self, "Erreur", "Le fichier n'a pas été trouvé sur le disque")

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _open_bulk_assignment_dialog(self):
        """Ouvre le dialogue d'actions en masse."""
        from core.gui.dialogs.bulk_assignment import BulkAssignmentDialog
        dialog = BulkAssignmentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            if self.operateur_selectionne:
                self._charger_contenu_domaine()

    def _domaine_a_contenu(self, donnees: dict, domaine) -> bool:
        """Retourne True si le domaine a au moins un enregistrement."""
        if domaine == DomaineRH.DECLARATION:
            return bool(donnees.get('declarations'))
        if domaine == DomaineRH.COMPETENCES:
            return bool(donnees.get('competences'))
        if domaine == DomaineRH.FORMATION:
            return bool(donnees.get('formations'))
        if domaine == DomaineRH.MEDICAL:
            return bool(donnees.get('visites_medicales'))
        if domaine == DomaineRH.VIE_SALARIE:
            return bool(donnees.get('entretiens') or donnees.get('sanctions'))
        return True  # GENERAL : toujours afficher

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
            return format_date(date_val)
        return str(date_val)


class GestionRHDialog(_GestionRHMixin, QDialog):
    """
    Fenêtre principale de gestion RH.
    Divisée en deux zones: sélection opérateur (gauche) et détails RH (droite).
    Toute la logique métier et UI est dans _GestionRHMixin.
    """

    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion RH")
        screen = _QApp.primaryScreen().availableGeometry()
        w = min(1400, screen.width() - 40)
        h = min(800, screen.height() - 60)
        self.setMinimumSize(min(1000, w), min(650, h))
        self.resize(w, h)

        self.operateur_selectionne = None
        self.domaine_actif = DomaineRH.GENERAL
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._executer_recherche)
        self._loading_worker = None

        self._setup_ui()

    def _setup_ui(self):
        """Construit l'interface utilisateur."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = add_custom_title_bar(self, "Gestion RH")
        main_layout.addWidget(title_bar)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.zone_gauche = self._creer_zone_selection()
        content_layout.addWidget(self.zone_gauche)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #e5e7eb;")
        separator.setFixedWidth(1)
        content_layout.addWidget(separator)

        self.zone_droite = self._creer_zone_details()
        content_layout.addWidget(self.zone_droite, 1)

        main_layout.addWidget(content, 1)

        footer = self._creer_footer()
        main_layout.addWidget(footer)

    def _creer_footer(self) -> QWidget:
        """Crée le pied de page avec les boutons d'action."""
        footer = QWidget()
        footer.setStyleSheet("background: #f9fafb; border-top: 1px solid #e5e7eb;")

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 12, 20, 12)

        btn_bulk = QPushButton("Actions en masse")
        btn_bulk.setToolTip("Assigner formations, absences ou visites médicales à plusieurs employés")
        btn_bulk.setCursor(Qt.PointingHandCursor)
        btn_bulk.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #a855f7);
                color: white;
                padding: 10px 24px;
                border-radius: 8px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #9333ea);
            }
            QPushButton:pressed {
                background: #5b21b6;
            }
        """)
        btn_bulk.clicked.connect(self._open_bulk_assignment_dialog)
        btn_bulk.setVisible(can("rh.personnel.edit"))
        layout.addWidget(btn_bulk)

        layout.addStretch()

        btn_fermer = EmacButton("Fermer", variant="ghost")
        btn_fermer.clicked.connect(self.close)
        layout.addWidget(btn_fermer)

        return footer


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = GestionRHDialog()
    dialog.show()
    sys.exit(app.exec_())
