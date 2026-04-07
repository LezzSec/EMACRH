# -*- coding: utf-8 -*-
"""
GestionAbsencesDialog — View pure (UI uniquement).

Ne contient aucune logique métier ni appel service.
Toute la logique est dans AbsenceViewModel.

Architecture :
    GestionAbsencesDialog (View)  ←→  AbsenceViewModel (ViewModel)
        création des widgets            chargement des données
        connexion des signaux           calculs et validations
        rendu des données               appels services
"""

from datetime import datetime

from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QButtonGroup, QCalendarWidget, QComboBox, QDateEdit, QDialog,
    QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QRadioButton, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget, QMessageBox,
)

from gui.components.emac_ui_kit import add_custom_title_bar, show_error_message
from gui.view_models.absence_view_model import AbsenceViewModel
from infrastructure.config.date_format import format_date, format_datetime
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)


class GestionAbsencesDialog(QDialog):
    """
    Dialogue de gestion des absences et congés.

    Responsabilités (View uniquement) :
        - Construire les widgets
        - Connecter les signaux ViewModel → méthodes _on_*
        - Lire l'état des widgets sur action utilisateur
        - Appeler le ViewModel pour toute opération métier

    Ne pas ajouter ici : appels services, calculs, logique métier.
    """

    data_changed = pyqtSignal()

    def __init__(self, personnel_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Absences et Congés")
        self.setGeometry(100, 100, 1200, 700)
        self.setModal(False)

        self._vm = AbsenceViewModel(personnel_id=personnel_id, parent=self)
        self._connect_viewmodel()
        self._init_ui()

        self._vm.load_all()

    # ------------------------------------------------------------------
    # Connexion ViewModel → View
    # ------------------------------------------------------------------

    def _connect_viewmodel(self) -> None:
        """Connecte les signaux ViewModel aux handlers de la View."""
        self._vm.types_loaded.connect(self._on_types_loaded)
        self._vm.demandes_loaded.connect(self._on_demandes_loaded)
        self._vm.soldes_loaded.connect(self._on_soldes_loaded)
        self._vm.validation_demandes_loaded.connect(self._on_validation_demandes_loaded)
        self._vm.nb_jours_changed.connect(self._on_nb_jours_changed)
        self._vm.demande_submitted.connect(self._on_demande_submitted)
        self._vm.demande_cancelled.connect(self._on_demande_cancelled)
        self._vm.demande_validated.connect(self._on_demande_validated)
        self._vm.error_occurred.connect(self._on_error)
        self._vm.data_changed.connect(self.data_changed)

    # ------------------------------------------------------------------
    # Construction de l'UI
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(add_custom_title_bar(self, "Gestion des Absences et Congés"))

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Gestion des Absences et Congés")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_tab_mes_demandes(), "Mes Demandes")
        self.tabs.addTab(self._build_tab_nouvelle_demande(), "Nouvelle Demande")
        self.tabs.addTab(self._build_tab_calendrier(), "Calendrier")
        self.tabs.addTab(self._build_tab_soldes(), "Mes Soldes")
        self.tabs.addTab(self._build_tab_validation(), "Validation")

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        main_layout.addWidget(content)

    def _build_tab_mes_demandes(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Année:"))

        self.annee_filter = QComboBox()
        annee = datetime.now().year
        for i in range(annee - 2, annee + 2):
            self.annee_filter.addItem(str(i), i)
        self.annee_filter.setCurrentText(str(annee))
        self.annee_filter.currentIndexChanged.connect(self._on_demandes_filter_changed)
        filter_layout.addWidget(self.annee_filter)

        filter_layout.addWidget(QLabel("Statut:"))
        self.statut_filter = QComboBox()
        self.statut_filter.addItem("Tous", None)
        self.statut_filter.addItem("En attente", "EN_ATTENTE")
        self.statut_filter.addItem("Validées", "VALIDEE")
        self.statut_filter.addItem("Refusées", "REFUSEE")
        self.statut_filter.currentIndexChanged.connect(self._on_demandes_filter_changed)
        filter_layout.addWidget(self.statut_filter)

        filter_layout.addStretch()
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.clicked.connect(self._on_demandes_filter_changed)
        filter_layout.addWidget(btn_refresh)
        layout.addLayout(filter_layout)

        self.table_demandes = QTableWidget()
        self.table_demandes.setColumnCount(9)
        self.table_demandes.setHorizontalHeaderLabels([
            "ID", "Type", "Début", "Fin", "Nb jours", "Motif", "Statut", "Validateur", "Date valid."
        ])
        self.table_demandes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_demandes.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_demandes.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_demandes)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Annuler la demande")
        btn_cancel.clicked.connect(self._on_annuler_clicked)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def _build_tab_nouvelle_demande(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form = QGroupBox("Nouvelle demande d'absence")
        form_layout = QVBoxLayout()

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type d'absence:"))
        self.type_combo = QComboBox()
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        form_layout.addLayout(type_layout)

        dates_layout = QHBoxLayout()

        debut_group = QVBoxLayout()
        debut_group.addWidget(QLabel("Date de début:"))
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.dateChanged.connect(self._on_dates_changed)
        debut_group.addWidget(self.date_debut)

        self.demi_debut_group = QButtonGroup()
        demi_debut_layout = QHBoxLayout()
        self.demi_debut_journee = QRadioButton("Journée")
        self.demi_debut_matin = QRadioButton("Matin")
        self.demi_debut_aprem = QRadioButton("Après-midi")
        self.demi_debut_journee.setChecked(True)
        self.demi_debut_group.addButton(self.demi_debut_journee, 0)
        self.demi_debut_group.addButton(self.demi_debut_matin, 1)
        self.demi_debut_group.addButton(self.demi_debut_aprem, 2)
        self.demi_debut_group.buttonClicked.connect(self._on_dates_changed)
        demi_debut_layout.addWidget(self.demi_debut_journee)
        demi_debut_layout.addWidget(self.demi_debut_matin)
        demi_debut_layout.addWidget(self.demi_debut_aprem)
        debut_group.addLayout(demi_debut_layout)
        dates_layout.addLayout(debut_group)

        fin_group = QVBoxLayout()
        fin_group.addWidget(QLabel("Date de fin:"))
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.dateChanged.connect(self._on_dates_changed)
        fin_group.addWidget(self.date_fin)

        self.demi_fin_group = QButtonGroup()
        demi_fin_layout = QHBoxLayout()
        self.demi_fin_journee = QRadioButton("Journée")
        self.demi_fin_matin = QRadioButton("Matin")
        self.demi_fin_aprem = QRadioButton("Après-midi")
        self.demi_fin_journee.setChecked(True)
        self.demi_fin_group.addButton(self.demi_fin_journee, 0)
        self.demi_fin_group.addButton(self.demi_fin_matin, 1)
        self.demi_fin_group.addButton(self.demi_fin_aprem, 2)
        self.demi_fin_group.buttonClicked.connect(self._on_dates_changed)
        demi_fin_layout.addWidget(self.demi_fin_journee)
        demi_fin_layout.addWidget(self.demi_fin_matin)
        demi_fin_layout.addWidget(self.demi_fin_aprem)
        fin_group.addLayout(demi_fin_layout)
        dates_layout.addLayout(fin_group)

        form_layout.addLayout(dates_layout)

        nb_jours_layout = QHBoxLayout()
        nb_jours_layout.addWidget(QLabel("Nombre de jours ouvrés:"))
        self.nb_jours_label = QLabel("0")
        self.nb_jours_label.setFont(QFont("Arial", 12, QFont.Bold))
        nb_jours_layout.addWidget(self.nb_jours_label)
        nb_jours_layout.addStretch()
        form_layout.addLayout(nb_jours_layout)

        form_layout.addWidget(QLabel("Motif (optionnel):"))
        self.motif_text = QTextEdit()
        self.motif_text.setMaximumHeight(80)
        form_layout.addWidget(self.motif_text)

        form.setLayout(form_layout)
        layout.addWidget(form)

        btn_soumettre = QPushButton("Soumettre la demande")
        btn_soumettre.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 10px; font-size: 14px;
                font-weight: bold; border-radius: 5px;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        btn_soumettre.clicked.connect(self._on_soumettre_clicked)
        layout.addWidget(btn_soumettre)
        layout.addStretch()

        return widget

    def _build_tab_calendrier(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self._on_calendar_date_clicked)
        layout.addWidget(self.calendar)

        layout.addWidget(QLabel("Absences du jour:"))
        self.absences_jour_list = QTableWidget()
        self.absences_jour_list.setColumnCount(4)
        self.absences_jour_list.setHorizontalHeaderLabels(["Nom", "Type", "Du", "Au"])
        self.absences_jour_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.absences_jour_list.setMaximumHeight(200)
        layout.addWidget(self.absences_jour_list)

        return widget

    def _build_tab_soldes(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        annee_layout = QHBoxLayout()
        annee_layout.addWidget(QLabel("Année:"))
        self.solde_annee_combo = QComboBox()
        annee = datetime.now().year
        for i in range(annee - 2, annee + 2):
            self.solde_annee_combo.addItem(str(i), i)
        self.solde_annee_combo.setCurrentText(str(annee))
        self.solde_annee_combo.currentIndexChanged.connect(self._on_solde_annee_changed)
        annee_layout.addWidget(self.solde_annee_combo)
        annee_layout.addStretch()
        layout.addLayout(annee_layout)

        soldes_layout = QHBoxLayout()
        self.cp_card, self.cp_value_label = self._build_solde_card("Congés Payés", "#27ae60")
        self.rtt_card, self.rtt_value_label = self._build_solde_card("RTT", "#3498db")
        soldes_layout.addWidget(self.cp_card)
        soldes_layout.addWidget(self.rtt_card)
        layout.addLayout(soldes_layout)

        details_group = QGroupBox("Détails")
        details_layout = QVBoxLayout()
        self.solde_details_label = QLabel()
        self.solde_details_label.setWordWrap(True)
        details_layout.addWidget(self.solde_details_label)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        layout.addStretch()
        return widget

    def _build_solde_card(self, titre: str, couleur: str):
        """Crée une card solde. Retourne (frame, value_label)."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {couleur};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        layout = QVBoxLayout(frame)

        title_label = QLabel(titre)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        layout.addWidget(title_label)

        value_label = QLabel("0")
        value_label.setFont(QFont("Arial", 24, QFont.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        subtitle = QLabel("jours restants")
        subtitle.setStyleSheet("color: white;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        return frame, value_label

    def _build_tab_validation(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Demandes en attente de validation:"))

        self.table_validation = QTableWidget()
        self.table_validation.setColumnCount(7)
        self.table_validation.setHorizontalHeaderLabels([
            "ID", "Personnel", "Type", "Du", "Au", "Nb jours", "Motif"
        ])
        self.table_validation.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_validation)

        btn_layout = QHBoxLayout()
        btn_valider = QPushButton("Valider")
        btn_valider.setStyleSheet("background-color: #27ae60; color: white; padding: 8px;")
        btn_valider.clicked.connect(lambda: self._on_valider_clicked(True))
        btn_layout.addWidget(btn_valider)

        btn_refuser = QPushButton("Refuser")
        btn_refuser.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px;")
        btn_refuser.clicked.connect(lambda: self._on_valider_clicked(False))
        btn_layout.addWidget(btn_refuser)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    # ------------------------------------------------------------------
    # Handlers ViewModel → View (_on_* : rendu uniquement)
    # ------------------------------------------------------------------

    def _on_types_loaded(self, types: list) -> None:
        self.type_combo.clear()
        for t in types:
            self.type_combo.addItem(f"{t['libelle']} ({t['code']})", t["code"])

    def _on_demandes_loaded(self, demandes: list) -> None:
        self.table_demandes.setRowCount(len(demandes))
        for row, d in enumerate(demandes):
            self.table_demandes.setItem(row, 0, QTableWidgetItem(str(d["id"])))
            self.table_demandes.setItem(row, 1, QTableWidgetItem(d["type_libelle"]))
            self.table_demandes.setItem(row, 2, QTableWidgetItem(format_date(d["date_debut"])))
            self.table_demandes.setItem(row, 3, QTableWidgetItem(format_date(d["date_fin"])))
            self.table_demandes.setItem(row, 4, QTableWidgetItem(str(d["nb_jours"])))
            self.table_demandes.setItem(row, 5, QTableWidgetItem(d["motif"] or ""))
            self.table_demandes.setItem(row, 6, QTableWidgetItem(d["statut"]))
            self.table_demandes.setItem(row, 7, QTableWidgetItem(d["validateur"] or ""))
            self.table_demandes.setItem(row, 8, QTableWidgetItem(format_datetime(d["date_validation"])))

            if d["statut"] == "VALIDEE":
                color = QColor(39, 174, 96, 50)
            elif d["statut"] == "REFUSEE":
                color = QColor(231, 76, 60, 50)
            else:
                continue
            for col in range(9):
                self.table_demandes.item(row, col).setBackground(color)

    def _on_soldes_loaded(self, soldes: dict) -> None:
        cp = soldes.get("cp", 0)
        rtt = soldes.get("rtt", 0)
        self.cp_value_label.setText(str(cp))
        self.rtt_value_label.setText(str(rtt))
        self.solde_details_label.setText(
            f"<b>Congés Payés:</b><br>- Pris sur l'année: {cp} jours<br><br>"
            f"<b>RTT:</b><br>- Pris sur l'année: {rtt} jours"
        )

    def _on_validation_demandes_loaded(self, demandes: list) -> None:
        self.table_validation.setRowCount(len(demandes))
        for row, d in enumerate(demandes):
            self.table_validation.setItem(row, 0, QTableWidgetItem(str(d["id"])))
            self.table_validation.setItem(row, 1, QTableWidgetItem(d["nom_complet"]))
            self.table_validation.setItem(row, 2, QTableWidgetItem(d["type_libelle"]))
            self.table_validation.setItem(row, 3, QTableWidgetItem(format_date(d["date_debut"])))
            self.table_validation.setItem(row, 4, QTableWidgetItem(format_date(d["date_fin"])))
            self.table_validation.setItem(row, 5, QTableWidgetItem(str(d["nb_jours"])))
            self.table_validation.setItem(row, 6, QTableWidgetItem(d["motif"] or ""))

    def _on_nb_jours_changed(self, nb: float) -> None:
        self.nb_jours_label.setText(str(nb))

    def _on_demande_submitted(self, demande_id: int) -> None:
        nb = self.nb_jours_label.text()
        QMessageBox.information(
            self, "Succès",
            f"Demande créée avec succès (ID: {demande_id})\n\n"
            f"Nombre de jours: {nb}\nStatut: En attente de validation"
        )
        self.motif_text.clear()
        self._vm.load_demandes(
            self.annee_filter.currentData(),
            self.statut_filter.currentData(),
        )
        self.tabs.setCurrentIndex(0)

    def _on_demande_cancelled(self) -> None:
        QMessageBox.information(self, "Succès", "Demande annulée")
        self._vm.load_demandes(
            self.annee_filter.currentData(),
            self.statut_filter.currentData(),
        )

    def _on_demande_validated(self, valide: bool) -> None:
        msg = "validée" if valide else "refusée"
        QMessageBox.information(self, "Succès", f"Demande {msg}")
        self._vm.load_validation_demandes()

    def _on_error(self, message: str) -> None:
        show_error_message(self, "Erreur", message, Exception(message))

    # ------------------------------------------------------------------
    # Handlers utilisateur → ViewModel (_on_*_clicked / _on_*_changed)
    # ------------------------------------------------------------------

    def _on_demandes_filter_changed(self) -> None:
        self._vm.load_demandes(
            self.annee_filter.currentData(),
            self.statut_filter.currentData(),
        )

    def _on_solde_annee_changed(self) -> None:
        self._vm.load_soldes(self.solde_annee_combo.currentData())

    def _on_dates_changed(self) -> None:
        self._vm.compute_nb_jours(
            self.date_debut.date().toPyDate(),
            self.date_fin.date().toPyDate(),
            self._read_demi_journee(self.demi_debut_group),
            self._read_demi_journee(self.demi_fin_group),
        )

    def _on_soumettre_clicked(self) -> None:
        self._vm.submit_demande(
            date_debut=self.date_debut.date().toPyDate(),
            date_fin=self.date_fin.date().toPyDate(),
            demi_debut=self._read_demi_journee(self.demi_debut_group),
            demi_fin=self._read_demi_journee(self.demi_fin_group),
            type_code=self.type_combo.currentData(),
            motif=self.motif_text.toPlainText(),
        )

    def _on_annuler_clicked(self) -> None:
        selected = self.table_demandes.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une demande")
            return

        row = selected[0].row()
        statut = self.table_demandes.item(row, 6).text()
        if statut != "EN_ATTENTE":
            QMessageBox.warning(
                self, "Attention",
                "Seules les demandes en attente peuvent être annulées"
            )
            return

        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment annuler cette demande ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            demande_id = int(self.table_demandes.item(row, 0).text())
            self._vm.cancel_demande(demande_id)

    def _on_valider_clicked(self, valide: bool) -> None:
        selected = self.table_validation.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une demande")
            return

        action = "valider" if valide else "refuser"
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment {action} cette demande ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            row = selected[0].row()
            demande_id = int(self.table_validation.item(row, 0).text())
            validateur_id = 1  # TODO: récupérer depuis la session
            self._vm.validate_demande(demande_id, valide, validateur_id)

    def _on_calendar_date_clicked(self, date) -> None:
        pass  # TODO: charger les absences du jour via ViewModel

    # ------------------------------------------------------------------
    # Helpers UI
    # ------------------------------------------------------------------

    @staticmethod
    def _read_demi_journee(button_group: QButtonGroup) -> str:
        """Lit la demi-journée sélectionnée dans un QButtonGroup."""
        mapping = {0: "JOURNEE", 1: "MATIN", 2: "APRES_MIDI"}
        return mapping.get(button_group.checkedId(), "JOURNEE")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from domain.repositories.personnel_repo import PersonnelRepository

    app = QApplication(sys.argv)
    dialog = GestionAbsencesDialog(personnel_id=PersonnelRepository.get_first_actif_id())
    dialog.show()
    sys.exit(app.exec_())
