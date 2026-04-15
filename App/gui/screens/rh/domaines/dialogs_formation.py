# -*- coding: utf-8 -*-
"""
Dialogs de formation :
  - EditFormationDialog
  - GestionDocsFormationDialog
  - AjouterDocFormationDialog
  - ConsulterFormationDialog
"""

from PyQt5.QtWidgets import (
    QFormLayout, QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox,
    QTextEdit, QCheckBox, QHBoxLayout, QLabel
)
from PyQt5.QtCore import QDate

from gui.components.ui_theme import EmacButton
from gui.components.emac_dialog import EmacFormDialog
from gui.screens.rh.domaines.dialogs_shared import JustificatifMixin
from domain.services.rh.rh_service import create_formation, update_formation


class EditFormationDialog(JustificatifMixin, EmacFormDialog):
    """Formulaire d'édition/création de formation."""

    def __init__(self, operateur_id: int, formation: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.formation = formation
        self.is_edit = formation is not None
        self._saved_id = None
        title = "Modifier la formation" if self.is_edit else "Nouvelle formation"
        min_h = 560 if self.is_edit else 700
        super().__init__(title=title, min_width=480, min_height=min_h, add_title_bar=False, parent=parent)

    def init_ui(self):
        form = QFormLayout()
        form.setSpacing(12)

        self.intitule = QLineEdit(self.formation.get('intitule', '') if self.formation else '')
        form.addRow("Intitulé:", self.intitule)

        self.organisme = QLineEdit(self.formation.get('organisme', '') if self.formation else '')
        form.addRow("Organisme:", self.organisme)

        self.lieu = QLineEdit(self.formation.get('lieu', '') if self.formation else '')
        self.lieu.setPlaceholderText("Ex: Salle A, site externe...")
        form.addRow("Lieu:", self.lieu)

        self.formateur = QLineEdit(self.formation.get('formateur', '') if self.formation else '')
        self.formateur.setPlaceholderText("Nom du formateur / intervenant")
        form.addRow("Formateur:", self.formateur)

        self.objectif = QTextEdit()
        self.objectif.setMaximumHeight(65)
        self.objectif.setPlaceholderText("Objectif pédagogique de la formation...")
        if self.formation and self.formation.get('objectif'):
            self.objectif.setText(self.formation['objectif'])
        form.addRow("Objectif:", self.objectif)

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setDate(QDate.currentDate())
        if self.formation and self.formation.get('date_debut'):
            d = self.formation['date_debut']
            self.date_debut.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date de début:", self.date_debut)

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setSpecialValueText("Non définie")
        self.date_fin.setMinimumDate(QDate(1900, 1, 1))
        if self.formation and self.formation.get('date_fin'):
            d = self.formation['date_fin']
            self.date_fin.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_fin.setDate(QDate.currentDate())
        form.addRow("Date de fin:", self.date_fin)

        self.duree = QDoubleSpinBox()
        self.duree.setRange(0, 9999)
        self.duree.setSuffix(" h")
        if self.formation and self.formation.get('duree_heures'):
            self.duree.setValue(float(self.formation['duree_heures']))
        form.addRow("Durée:", self.duree)

        self.statut_combo = QComboBox()
        self.statut_combo.addItems(['Planifiée', 'En cours', 'Terminée', 'Annulée'])
        if self.formation and self.formation.get('statut'):
            idx = self.statut_combo.findText(self.formation['statut'])
            if idx >= 0:
                self.statut_combo.setCurrentIndex(idx)
        form.addRow("Statut:", self.statut_combo)

        self.certificat = QCheckBox("Certificat obtenu")
        if self.formation and self.formation.get('certificat_obtenu'):
            self.certificat.setChecked(True)
        form.addRow("", self.certificat)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(80)
        if self.formation and self.formation.get('commentaire'):
            self.commentaire.setText(self.formation['commentaire'])
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addLayout(form)

        if not self.is_edit:
            self._ajouter_section_justificatif_facultatif("Diplômes et formations")

    def _ajouter_section_justificatif_facultatif(self, categorie_nom_hint: str = ""):
        """Section justificatif facultative — peut être ajouté ultérieurement."""
        from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
        self._justificatif_path = None
        self._justificatif_categorie_nom = categorie_nom_hint

        group = QGroupBox("Document justificatif (facultatif)")
        group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                margin-top: 10px;
                padding: 10px 8px 8px 8px;
                font-weight: bold;
                color: #475569;
                background: #f8fafc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(6)

        note = QLabel(
            "Vous pouvez joindre dès maintenant l'attestation ou le certificat. "
            "Si le document n'est pas encore disponible, il pourra être ajouté "
            "ultérieurement via l'onglet Documents du profil salarié."
        )
        note.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        note.setWordWrap(True)
        group_layout.addWidget(note)

        file_row = QHBoxLayout()
        self._justificatif_label = QLineEdit()
        self._justificatif_label.setReadOnly(True)
        self._justificatif_label.setPlaceholderText("Aucun fichier sélectionné (facultatif)…")
        self._justificatif_label.setStyleSheet("background: white;")
        file_row.addWidget(self._justificatif_label)

        btn = EmacButton("Parcourir…", variant="ghost")
        btn.setFixedWidth(100)
        btn.clicked.connect(self._parcourir_justificatif)
        file_row.addWidget(btn)
        group_layout.addLayout(file_row)

        self.content_layout.addWidget(group)

    def validate(self):
        if not self.intitule.text().strip():
            return False, "L'intitulé est obligatoire"
        return True, ""

    def save_to_db(self):
        date_fin = self.date_fin.date()
        data = {
            'intitule': self.intitule.text().strip(),
            'organisme': self.organisme.text().strip() or None,
            'lieu': self.lieu.text().strip() or None,
            'formateur': self.formateur.text().strip() or None,
            'objectif': self.objectif.toPlainText().strip() or None,
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': date_fin.toPyDate() if date_fin.year() > 1900 else None,
            'duree_heures': self.duree.value() if self.duree.value() > 0 else None,
            'statut': self.statut_combo.currentText(),
            'certificat_obtenu': self.certificat.isChecked(),
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_formation(self.formation['id'], data)
            if success:
                self._saved_id = self.formation['id']
        else:
            success, message, new_id = create_formation(self.operateur_id, data)
            if success:
                self._saved_id = new_id
                if getattr(self, '_justificatif_path', None):
                    self._sauvegarder_justificatif(self.operateur_id)
                else:
                    self._justificatif_manquant = True

        if not success:
            raise Exception(message)


class GestionDocsFormationDialog:
    """
    Dialog d'administration des dossiers de formation pour les niveaux de polyvalence.

    Permet aux responsables de :
    - Voir tous les postes et leurs documents de formation
    - Ajouter un document (PDF, Word, etc.) pour un poste + niveau
    - Supprimer un document
    """

    def __init__(self, parent=None):
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSplitter,
            QListWidget, QTableWidget, QTableWidgetItem,
            QHeaderView, QAbstractItemView, QWidget, QLineEdit
        )
        from PyQt5.QtCore import Qt

        self._parent = parent
        self._dialog = QDialog(parent)
        self._dialog.setWindowTitle("Gestion des dossiers de formation – Polyvalence")
        self._dialog.setMinimumSize(900, 600)
        self._dialog.resize(1000, 650)

        self._poste_selectionne = None

        main_layout = QVBoxLayout(self._dialog)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        titre = QLabel("Dossiers de formation de compétences – Niveaux de polyvalence")
        titre.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        main_layout.addWidget(titre)

        sous_titre = QLabel(
            "Associez des documents (PDF, Word, etc.) à un poste et un niveau de polyvalence. "
            "Ils seront lisibles par tous les utilisateurs depuis l'onglet Polyvalence."
        )
        sous_titre.setStyleSheet("color: #64748b; font-size: 12px;")
        sous_titre.setWordWrap(True)
        main_layout.addWidget(sous_titre)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Panneau gauche : liste des postes
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        lbl_postes = QLabel("Postes :")
        lbl_postes.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(lbl_postes)

        self._search_poste = QLineEdit()
        self._search_poste.setPlaceholderText("Filtrer par code poste...")
        self._search_poste.textChanged.connect(self._filtrer_postes)
        left_layout.addWidget(self._search_poste)

        self._list_postes = QListWidget()
        self._list_postes.setMaximumWidth(220)
        self._list_postes.currentRowChanged.connect(self._on_poste_change)
        left_layout.addWidget(self._list_postes)

        splitter.addWidget(left_panel)

        # Panneau droit : tableau + ajout
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(8)

        toolbar = QHBoxLayout()
        self._lbl_poste_titre = QLabel("Sélectionnez un poste")
        self._lbl_poste_titre.setStyleSheet("font-size: 14px; font-weight: bold;")
        toolbar.addWidget(self._lbl_poste_titre)
        toolbar.addStretch()

        self._btn_ajouter = EmacButton("+ Ajouter un document", variant="primary")
        self._btn_ajouter.setEnabled(False)
        self._btn_ajouter.clicked.connect(self._ajouter_doc)
        toolbar.addWidget(self._btn_ajouter)
        right_layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Nom", "Niveau", "Taille", "Ajouté par", "Actions"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in [1, 2, 3]:
            self._table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        right_layout.addWidget(self._table)

        splitter.addWidget(right_panel)
        splitter.setSizes([220, 680])

        btn_fermer = EmacButton("Fermer", variant="ghost")
        btn_fermer.clicked.connect(self._dialog.accept)
        main_layout.addWidget(btn_fermer, alignment=Qt.AlignRight)

        self._tous_postes = []
        self._charger_postes()

    def exec_(self):
        return self._dialog.exec_()

    def _charger_postes(self):
        from domain.services.documents.polyvalence_docs_service import get_tous_les_postes_avec_docs
        self._tous_postes = get_tous_les_postes_avec_docs()
        self._remplir_liste_postes(self._tous_postes)

    def _remplir_liste_postes(self, postes):
        from PyQt5.QtWidgets import QListWidgetItem
        self._list_postes.clear()
        for p in postes:
            nb = p.get('nb_documents', 0)
            label = p['poste_code']
            if p.get('atelier_nom'):
                label = f"{p['atelier_nom']} / {label}"
            if nb:
                label += f"  ({nb})"
            item = QListWidgetItem(label)
            item.setData(32, p)  # Qt.UserRole = 32
            self._list_postes.addItem(item)

    def _filtrer_postes(self, texte):
        texte = texte.lower()
        filtered = [p for p in self._tous_postes if texte in p['poste_code'].lower()]
        self._remplir_liste_postes(filtered)

    def _on_poste_change(self, row):
        if row < 0:
            return
        item = self._list_postes.item(row)
        if not item:
            return
        self._poste_selectionne = item.data(32)
        self._lbl_poste_titre.setText(f"Poste {self._poste_selectionne['poste_code']}")
        self._btn_ajouter.setEnabled(True)
        self._charger_docs_poste()

    def _charger_docs_poste(self):
        from PyQt5.QtWidgets import QTableWidgetItem, QWidget, QHBoxLayout
        from domain.services.documents.polyvalence_docs_service import get_docs_pour_poste

        if not self._poste_selectionne:
            return

        docs = get_docs_pour_poste(self._poste_selectionne['poste_id'])
        self._table.setRowCount(len(docs))

        NIVEAU_LABELS = {None: "Tous niveaux", 1: "Niv. 1", 2: "Niv. 2", 3: "Niv. 3", 4: "Niv. 4"}

        for row_idx, doc in enumerate(docs):
            nom = doc.get('nom_affichage', doc.get('nom_fichier', '?'))
            self._table.setItem(row_idx, 0, QTableWidgetItem(nom))
            self._table.setItem(row_idx, 1, QTableWidgetItem(
                NIVEAU_LABELS.get(doc.get('niveau'), f"Niv. {doc['niveau']}")))
            taille = doc.get('taille_octets')
            self._table.setItem(row_idx, 2, QTableWidgetItem(
                f"{taille // 1024} Ko" if taille else "-"))
            self._table.setItem(row_idx, 3, QTableWidgetItem(doc.get('ajoute_par', '-')))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)

            btn_ouvrir = EmacButton("Ouvrir", variant="outline")
            btn_ouvrir.setFixedHeight(26)
            doc_id = doc['id']
            btn_ouvrir.clicked.connect(lambda checked, did=doc_id: self._ouvrir_doc(did))
            btn_layout.addWidget(btn_ouvrir)

            btn_suppr = EmacButton("Suppr.", variant="ghost")
            btn_suppr.setFixedHeight(26)
            btn_suppr.clicked.connect(lambda checked, did=doc_id, n=nom: self._supprimer_doc(did, n))
            btn_layout.addWidget(btn_suppr)

            self._table.setCellWidget(row_idx, 4, btn_widget)

    def _ajouter_doc(self):
        if not self._poste_selectionne:
            return
        dialog = AjouterDocFormationDialog(self._poste_selectionne, self._dialog)
        if dialog.exec_() == 1:
            self._charger_docs_poste()
            self._charger_postes()

    def _ouvrir_doc(self, doc_id: int):
        import os
        from domain.services.documents.polyvalence_docs_service import extraire_vers_fichier_temp
        temp_path = extraire_vers_fichier_temp(doc_id)
        if temp_path and temp_path.exists():
            if os.name == 'nt':
                os.startfile(str(temp_path))
            else:
                import subprocess
                subprocess.run(['xdg-open', str(temp_path)])
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self._dialog, "Erreur", "Le fichier n'a pas pu être extrait.")

    def _supprimer_doc(self, doc_id: int, nom: str):
        from PyQt5.QtWidgets import QMessageBox
        from domain.services.documents.polyvalence_docs_service import supprimer_document
        reply = QMessageBox.question(
            self._dialog,
            "Confirmer la suppression",
            f"Supprimer le document '{nom}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = supprimer_document(doc_id)
            if success:
                self._charger_docs_poste()
                self._charger_postes()
            else:
                QMessageBox.critical(self._dialog, "Erreur", message)


class AjouterDocFormationDialog:
    """Dialog pour ajouter un document de formation à un poste + niveau."""

    def __init__(self, poste_info: dict, parent=None):
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
            QFormLayout, QComboBox, QTextEdit
        )
        from PyQt5.QtCore import Qt

        self._poste_info = poste_info
        self._fichier_path = None

        self._dialog = QDialog(parent)
        self._dialog.setWindowTitle(f"Ajouter un dossier – Poste {poste_info['poste_code']}")
        self._dialog.setMinimumWidth(480)

        layout = QVBoxLayout(self._dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(10)

        file_row = QHBoxLayout()
        self._file_label = QLineEdit()
        self._file_label.setReadOnly(True)
        self._file_label.setPlaceholderText("Aucun fichier sélectionné...")
        file_row.addWidget(self._file_label)
        btn_parcourir = EmacButton("Parcourir...", variant="ghost")
        btn_parcourir.clicked.connect(self._parcourir)
        file_row.addWidget(btn_parcourir)
        form.addRow("Fichier :", file_row)

        self._nom_input = QLineEdit()
        self._nom_input.setPlaceholderText("Titre du document (optionnel)")
        form.addRow("Titre :", self._nom_input)

        self._niveau_combo = QComboBox()
        self._niveau_combo.addItem("Tous les niveaux", None)
        self._niveau_combo.addItem("Niveau 1 – Apprentissage", 1)
        self._niveau_combo.addItem("Niveau 2 – En cours", 2)
        self._niveau_combo.addItem("Niveau 3 – Autonome", 3)
        self._niveau_combo.addItem("Niveau 4 – Expert / Formateur", 4)
        form.addRow("Niveau concerné :", self._niveau_combo)

        self._desc_input = QTextEdit()
        self._desc_input.setMaximumHeight(70)
        self._desc_input.setPlaceholderText("Description ou contexte (optionnel)")
        form.addRow("Description :", self._desc_input)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_annuler = EmacButton("Annuler", variant="ghost")
        btn_annuler.clicked.connect(self._dialog.reject)
        btn_row.addWidget(btn_annuler)
        btn_ok = EmacButton("Ajouter", variant="primary")
        btn_ok.clicked.connect(self._valider)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def exec_(self):
        return self._dialog.exec_()

    def _parcourir(self):
        from PyQt5.QtWidgets import QFileDialog
        from pathlib import Path
        path, _ = QFileDialog.getOpenFileName(
            self._dialog,
            "Sélectionner un fichier",
            "",
            "Documents (*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.odt *.png *.jpg *.jpeg);;Tous les fichiers (*)"
        )
        if path:
            self._fichier_path = path
            self._file_label.setText(Path(path).name)
            if not self._nom_input.text():
                self._nom_input.setText(Path(path).stem.replace('_', ' ').replace('-', ' '))

    def _valider(self):
        from PyQt5.QtWidgets import QMessageBox
        from domain.services.documents.polyvalence_docs_service import ajouter_document
        from domain.services.admin.auth_service import get_current_user

        if not self._fichier_path:
            QMessageBox.warning(self._dialog, "Fichier manquant", "Veuillez sélectionner un fichier.")
            return

        nom = self._nom_input.text().strip() or None
        niveau = self._niveau_combo.currentData()
        description = self._desc_input.toPlainText().strip() or None

        user = get_current_user()
        ajoute_par = user.get('nom_complet', 'Utilisateur') if user else 'Utilisateur'

        success, message, _ = ajouter_document(
            poste_id=self._poste_info['poste_id'],
            nom_affichage=nom,
            fichier_source=self._fichier_path,
            niveau=niveau,
            description=description,
            ajoute_par=ajoute_par
        )

        if success:
            self._dialog.accept()
        else:
            QMessageBox.critical(self._dialog, "Erreur", message)


class ConsulterFormationDialog:
    """Affiche le détail complet d'une formation en lecture seule avec export Excel."""

    def __init__(self, formation: dict, parent=None):
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
            QScrollArea, QWidget, QFrame, QMessageBox
        )
        from PyQt5.QtCore import Qt
        from infrastructure.config.date_format import format_date

        self._formation = formation
        self._parent_widget = parent

        dialog = QDialog(parent)
        dialog.setWindowTitle("Détail de la formation")
        dialog.setMinimumWidth(480)
        dialog.resize(520, 560)

        main = QVBoxLayout(dialog)
        main.setContentsMargins(20, 16, 20, 16)
        main.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        form = QFormLayout(content)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        def _val(v):
            return str(v) if v not in (None, '') else '—'

        def _date(v):
            if not v:
                return '—'
            try:
                return format_date(v)
            except Exception:
                return str(v)

        def _lbl(text):
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #111827;")
            return lbl

        fields = [
            ("Intitulé",      _val(formation.get('intitule'))),
            ("Statut",        _val(formation.get('statut'))),
            ("Type",          _val(formation.get('type_formation'))),
            ("Organisme",     _val(formation.get('organisme'))),
            ("Lieu",          _val(formation.get('lieu'))),
            ("Formateur",     _val(formation.get('formateur'))),
            ("Date début",    _date(formation.get('date_debut'))),
            ("Date fin",      _date(formation.get('date_fin'))),
            ("Durée",         f"{formation['duree_heures']} h" if formation.get('duree_heures') else '—'),
            ("Certificat",    "Oui" if formation.get('certificat_obtenu') else "Non"),
            ("Coût",          f"{formation['cout']} €" if formation.get('cout') else '—'),
            ("Coût salarial", f"{formation['cout_salarial']} €" if formation.get('cout_salarial') else '—'),
            ("Objectif",      _val(formation.get('objectif'))),
            ("Commentaire",   _val(formation.get('commentaire'))),
        ]

        for label, value in fields:
            key = QLabel(f"{label} :")
            key.setStyleSheet("color: #6b7280; font-weight: bold;")
            form.addRow(key, _lbl(value))

        scroll.setWidget(content)
        main.addWidget(scroll, 1)

        btn_layout = QHBoxLayout()

        btn_excel = QPushButton("Ouvrir dans Excel")
        btn_excel.setFixedHeight(36)
        btn_excel.setStyleSheet("""
            QPushButton {
                background: #217346; color: white;
                border: none; border-radius: 6px;
                padding: 0 16px; font-weight: bold;
            }
            QPushButton:hover { background: #185c37; }
        """)

        def _generer_et_ouvrir():
            from domain.services.formation.formation_export_service import FormationExportService
            from domain.services.formation.formation_service_crud import FormationServiceCRUD
            formation_id = formation.get('id')
            data = FormationServiceCRUD.get_formation_by_id(formation_id) if formation_id else formation
            if not data:
                data = formation
            success, msg, path = FormationExportService.generate_dossier_formation(data)
            if success and path:
                FormationExportService.open_file(path)
            else:
                QMessageBox.warning(dialog, "Erreur", msg)

        btn_excel.clicked.connect(_generer_et_ouvrir)
        btn_layout.addWidget(btn_excel)

        btn_layout.addStretch()

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setFixedHeight(36)
        btn_fermer.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_fermer)

        main.addLayout(btn_layout)

        dialog.exec_()
