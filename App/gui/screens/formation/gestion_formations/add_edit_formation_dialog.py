# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QMessageBox, QWidget, QTextEdit, QDateEdit, QGroupBox,
    QCheckBox, QDoubleSpinBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from gui.components.emac_ui_kit import show_error_message
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class AddEditFormationDialog(QDialog):
    """Dialogue d'ajout/modification de formation."""

    def __init__(self, formation=None, vm=None, parent=None):
        super().__init__(parent)
        self.formation = formation
        self.is_edit = formation is not None
        self.document_id = formation.get('document_id') if formation else None
        self._vm = vm

        self.setWindowTitle("Modifier la formation" if self.is_edit else "Nouvelle formation")
        self.setFixedSize(640, 820)

        self.init_ui()
        self._connect_viewmodel()

        if self.is_edit:
            self.load_formation_data()

    def _connect_viewmodel(self):
        if not self._vm:
            return
        self._vm.personnel_loaded.connect(self._on_personnel_loaded)
        self._vm.document_path_ready.connect(self._on_document_path_ready)
        self._vm.document_nom_ready.connect(self._on_document_nom_ready)

    def _on_personnel_loaded(self, operateurs: list):
        self.operateur_combo.clear()
        for op in operateurs:
            self.operateur_combo.addItem(
                f"{op['nom_complet']} ({op['matricule']})",
                op['id']
            )
        if self.is_edit and self.formation:
            operateur_id = self.formation.get('operateur_id')
            for i in range(self.operateur_combo.count()):
                if self.operateur_combo.itemData(i) == operateur_id:
                    self.operateur_combo.setCurrentIndex(i)
                    break

    def _on_document_path_ready(self, path: str):
        self._vm.open_file(path)

    def _on_document_nom_ready(self, nom: str):
        self.attestation_label.setText(f"📄 {nom}")
        self.attestation_label.setStyleSheet("color: #10b981; font-weight: bold;")
        self.btn_voir.setEnabled(True)
        self.btn_supprimer_doc.setEnabled(True)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Modifier la formation" if self.is_edit else "Nouvelle formation")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.operateur_combo = QComboBox()
        self.operateur_combo.setMinimumWidth(300)
        self._load_operateurs()
        form_layout.addRow("Employe *:", self.operateur_combo)

        self.intitule_input = QLineEdit()
        self.intitule_input.setPlaceholderText("Ex: Formation securite incendie")
        form_layout.addRow("Intitule *:", self.intitule_input)

        self.organisme_input = QLineEdit()
        self.organisme_input.setPlaceholderText("Ex: AFPA, CNAM...")
        form_layout.addRow("Organisme:", self.organisme_input)

        self.lieu_input = QLineEdit()
        self.lieu_input.setPlaceholderText("Ex: Salle de formation Bat A, site externe...")
        form_layout.addRow("Lieu:", self.lieu_input)

        self.formateur_input = QLineEdit()
        self.formateur_input.setPlaceholderText("Nom du formateur / intervenant")
        form_layout.addRow("Formateur:", self.formateur_input)

        self.objectif_text = QTextEdit()
        self.objectif_text.setMaximumHeight(65)
        self.objectif_text.setPlaceholderText("Objectif pédagogique de la formation...")
        form_layout.addRow("Objectif:", self.objectif_text)

        dates_layout = QHBoxLayout()
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        dates_layout.addWidget(QLabel("Debut *:"))
        dates_layout.addWidget(self.date_debut)
        dates_layout.addSpacing(20)
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        dates_layout.addWidget(QLabel("Fin *:"))
        dates_layout.addWidget(self.date_fin)
        dates_layout.addStretch()
        form_layout.addRow("Dates:", dates_layout)

        self.duree_spin = QDoubleSpinBox()
        self.duree_spin.setRange(0, 9999)
        self.duree_spin.setDecimals(1)
        self.duree_spin.setSuffix(" h")
        form_layout.addRow("Duree:", self.duree_spin)

        self.statut_combo = QComboBox()
        self.statut_combo.addItems(["Planifiee", "En cours", "Terminee", "Annulee"])
        form_layout.addRow("Statut:", self.statut_combo)

        self.certificat_check = QCheckBox("Certificat obtenu")
        form_layout.addRow("", self.certificat_check)

        self.cout_spin = QDoubleSpinBox()
        self.cout_spin.setRange(0, 999999)
        self.cout_spin.setDecimals(2)
        self.cout_spin.setSuffix(" EUR")
        form_layout.addRow("Cout:", self.cout_spin)

        self.commentaire_text = QTextEdit()
        self.commentaire_text.setMaximumHeight(80)
        self.commentaire_text.setPlaceholderText("Notes ou commentaires...")
        form_layout.addRow("Commentaire:", self.commentaire_text)

        layout.addLayout(form_layout)

        attestation_group = QGroupBox("Attestation / Certificat")
        attestation_layout = QVBoxLayout()

        self.attestation_label = QLabel("Aucune attestation jointe")
        self.attestation_label.setStyleSheet("color: #64748b; font-style: italic;")
        attestation_layout.addWidget(self.attestation_label)

        btn_attestation_layout = QHBoxLayout()

        self.btn_joindre = QPushButton("Joindre une attestation...")
        self.btn_joindre.clicked.connect(self.joindre_attestation)
        self.btn_joindre.setStyleSheet("""
            QPushButton { background-color: #10b981; color: white; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_attestation_layout.addWidget(self.btn_joindre)

        self.btn_voir = QPushButton("Voir")
        self.btn_voir.clicked.connect(self.voir_attestation)
        self.btn_voir.setEnabled(False)
        btn_attestation_layout.addWidget(self.btn_voir)

        self.btn_supprimer_doc = QPushButton("Retirer")
        self.btn_supprimer_doc.clicked.connect(self.retirer_attestation)
        self.btn_supprimer_doc.setEnabled(False)
        self.btn_supprimer_doc.setStyleSheet("color: #dc2626;")
        btn_attestation_layout.addWidget(self.btn_supprimer_doc)

        btn_attestation_layout.addStretch()
        attestation_layout.addLayout(btn_attestation_layout)
        attestation_group.setLayout(attestation_layout)
        layout.addWidget(attestation_group)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Enregistrer")
        btn_save.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: white; font-weight: bold;
                padding: 8px 20px; border-radius: 4px; }
            QPushButton:hover { background-color: #2563eb; }
        """)
        btn_save.clicked.connect(self.save_formation)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _load_operateurs(self):
        if self._vm:
            self._vm.load_personnel()

    def load_formation_data(self):
        if not self.formation:
            return

        operateur_id = self.formation.get('operateur_id')
        for i in range(self.operateur_combo.count()):
            if self.operateur_combo.itemData(i) == operateur_id:
                self.operateur_combo.setCurrentIndex(i)
                break

        self.intitule_input.setText(self.formation.get('intitule', ''))
        self.organisme_input.setText(self.formation.get('organisme') or '')
        self.lieu_input.setText(self.formation.get('lieu') or '')
        self.formateur_input.setText(self.formation.get('formateur') or '')
        self.objectif_text.setPlainText(self.formation.get('objectif') or '')

        date_debut = self.formation.get('date_debut')
        if date_debut:
            if isinstance(date_debut, str):
                self.date_debut.setDate(QDate.fromString(date_debut, "yyyy-MM-dd"))
            else:
                self.date_debut.setDate(QDate(date_debut.year, date_debut.month, date_debut.day))

        date_fin = self.formation.get('date_fin')
        if date_fin:
            if isinstance(date_fin, str):
                self.date_fin.setDate(QDate.fromString(date_fin, "yyyy-MM-dd"))
            else:
                self.date_fin.setDate(QDate(date_fin.year, date_fin.month, date_fin.day))

        duree = self.formation.get('duree_heures')
        if duree:
            self.duree_spin.setValue(float(duree))

        statut = self.formation.get('statut', 'Planifiee')
        statut_map = {'Planifiée': 'Planifiee', 'Terminée': 'Terminee', 'Annulée': 'Annulee', 'En cours': 'En cours'}
        statut_normalized = statut_map.get(statut, statut)
        index = self.statut_combo.findText(statut_normalized)
        if index >= 0:
            self.statut_combo.setCurrentIndex(index)

        self.certificat_check.setChecked(bool(self.formation.get('certificat_obtenu')))

        cout = self.formation.get('cout')
        if cout:
            self.cout_spin.setValue(float(cout))

        self.commentaire_text.setText(self.formation.get('commentaire') or '')

        self.document_id = self.formation.get('document_id')
        attestation_nom = self.formation.get('attestation_nom')
        if self.document_id and attestation_nom:
            self.attestation_label.setText(f"📄 {attestation_nom}")
            self.attestation_label.setStyleSheet("color: #10b981; font-weight: bold;")
            self.btn_voir.setEnabled(True)
            self.btn_supprimer_doc.setEnabled(True)

    def joindre_attestation(self):
        operateur_id = self.operateur_combo.currentData()
        if not operateur_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord selectionner un employe.")
            return

        try:
            from gui.screens.documents.gestion_documentaire import AddDocumentDialog
            dialog = AddDocumentDialog(operateur_id=operateur_id, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                if hasattr(dialog, 'created_document_id') and dialog.created_document_id:
                    self.document_id = dialog.created_document_id
                    self._update_attestation_display()
                    QMessageBox.information(self, "Succes", "Attestation jointe avec succes.")
        except Exception as e:
            logger.exception(f"Erreur joindre attestation: {e}")
            show_error_message(self, "Erreur", "Impossible de joindre l'attestation", e)

    def voir_attestation(self):
        if not self.document_id or not self._vm:
            return
        self._vm.get_document_path(self.document_id)

    def retirer_attestation(self):
        reply = QMessageBox.question(
            self, "Confirmation",
            "Retirer le lien vers cette attestation ?\n(Le document restera dans la base)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.document_id = None
            self.attestation_label.setText("Aucune attestation jointe")
            self.attestation_label.setStyleSheet("color: #64748b; font-style: italic;")
            self.btn_voir.setEnabled(False)
            self.btn_supprimer_doc.setEnabled(False)

    def _update_attestation_display(self):
        if self.document_id and self._vm:
            self._vm.get_document_nom(self.document_id)

    def save_formation(self):
        operateur_id = self.operateur_combo.currentData()
        if not operateur_id:
            QMessageBox.warning(self, "Validation", "Veuillez selectionner un employe.")
            return

        intitule = self.intitule_input.text().strip()
        if not intitule:
            QMessageBox.warning(self, "Validation", "L'intitule est obligatoire.")
            return

        organisme = self.organisme_input.text().strip() or None
        lieu = self.lieu_input.text().strip() or None
        formateur = self.formateur_input.text().strip() or None
        objectif = self.objectif_text.toPlainText().strip() or None
        date_debut = self.date_debut.date().toPyDate()
        date_fin = self.date_fin.date().toPyDate()

        if date_fin < date_debut:
            QMessageBox.warning(self, "Validation", "La date de fin doit etre posterieure a la date de debut.")
            return

        duree_heures = self.duree_spin.value() if self.duree_spin.value() > 0 else None

        statut_text = self.statut_combo.currentText()
        statut_map = {'Planifiee': 'Planifiée', 'Terminee': 'Terminée', 'Annulee': 'Annulée', 'En cours': 'En cours'}
        statut = statut_map.get(statut_text, statut_text)

        certificat_obtenu = self.certificat_check.isChecked()
        cout = self.cout_spin.value() if self.cout_spin.value() > 0 else None
        commentaire = self.commentaire_text.toPlainText().strip() or None

        data = dict(
            operateur_id=operateur_id,
            intitule=intitule,
            organisme=organisme,
            lieu=lieu,
            objectif=objectif,
            formateur=formateur,
            date_debut=date_debut,
            date_fin=date_fin,
            duree_heures=duree_heures,
            statut=statut,
            certificat_obtenu=certificat_obtenu,
            cout=cout,
            commentaire=commentaire,
            document_id=self.document_id,
        )
        formation_id_edit = self.formation['id'] if self.is_edit else None

        if not self._vm:
            QMessageBox.critical(self, "Erreur", "ViewModel non disponible.")
            return

        self._vm.dossier_generated.connect(self._on_dossier_generated_inner)
        self._vm.action_succeeded.connect(self._on_save_succeeded)
        self._vm.save_formation(data, formation_id=formation_id_edit)

    def _on_save_succeeded(self, msg: str):
        reply = QMessageBox.question(
            self, "Formation enregistrée",
            f"{msg}\n\nVoulez-vous générer les documents de formation pré-remplis ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes and self._vm:
            self._vm.formation_loaded.connect(self._on_saved_formation_for_dossier)
        else:
            self.accept()

    def _on_saved_formation_for_dossier(self, formation: dict):
        saved_id = formation.get('_saved_id')
        if saved_id and self._vm:
            self._vm.generate_dossier(saved_id)
        else:
            self.accept()

    def _on_dossier_generated_inner(self, success: bool, msg: str, path: str):
        if success and path:
            reply = QMessageBox.information(
                self, "Documents générés",
                f"Dossier de formation généré :\n{path}\n\nOuvrir le fichier ?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes and self._vm:
                self._vm.open_file(path)
        else:
            QMessageBox.warning(self, "Génération échouée", msg)
        self.accept()
