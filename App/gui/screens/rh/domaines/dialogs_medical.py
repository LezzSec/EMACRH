# -*- coding: utf-8 -*-
"""
Dialogs médicaux :
  - EditVisiteDialog
  - EditAccidentDialog
  - EditValiditeDialog  (RQTH / OETH)
"""

from PyQt5.QtWidgets import (
    QFormLayout, QComboBox, QDateEdit, QTimeEdit, QTextEdit, QLineEdit,
    QCheckBox, QDoubleSpinBox, QLabel, QHBoxLayout, QWidget,
    QGroupBox,
)
from PyQt5.QtCore import QDate, QTime

from gui.components.emac_dialog import EmacFormDialog
from gui.screens.rh.domaines.dialogs_shared import JustificatifMixin
from domain.services.rh.medical_service import (
    create_visite, update_visite,
    create_accident, update_accident,
    create_validite, update_validite,
)


class EditVisiteDialog(JustificatifMixin, EmacFormDialog):
    """Formulaire pour ajouter/modifier une visite médicale."""

    def __init__(self, operateur_id: int, visite: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.visite = visite
        self.is_edit = visite is not None
        title = "Modifier la visite" if self.is_edit else "Nouvelle visite médicale"
        super().__init__(title=title, min_width=450, min_height=590, add_title_bar=False, parent=parent)

    def init_ui(self):
        visite_group = QGroupBox("Visite médicale et aptitude")
        form = QFormLayout(visite_group)
        form.setSpacing(10)

        self.date_visite = QDateEdit()
        self.date_visite.setCalendarPopup(True)
        self.date_visite.setDisplayFormat("dd/MM/yyyy")
        if self.is_edit and self.visite.get('date_visite'):
            d = self.visite['date_visite']
            self.date_visite.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_visite.setDate(QDate.currentDate())
        form.addRow("Date de visite:", self.date_visite)

        self.type_combo = QComboBox()
        self.type_combo.addItems(['Embauche', 'Périodique', 'Reprise', 'À la demande', 'Pré-reprise'])
        if self.is_edit and self.visite.get('type_visite'):
            idx = self.type_combo.findText(self.visite['type_visite'])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        form.addRow("Type de visite:", self.type_combo)

        self.resultat_combo = QComboBox()
        self.resultat_combo.addItems(['', 'Apte', 'Apte avec restrictions', 'Inapte temporaire', 'Inapte définitif'])
        if self.is_edit and self.visite.get('resultat'):
            idx = self.resultat_combo.findText(self.visite['resultat'])
            if idx >= 0:
                self.resultat_combo.setCurrentIndex(idx)
        form.addRow("Résultat:", self.resultat_combo)

        self.restrictions = QTextEdit()
        self.restrictions.setMaximumHeight(60)
        self.restrictions.setPlaceholderText("Détail des restrictions si applicable")
        if self.is_edit:
            self.restrictions.setText(self.visite.get('restrictions') or '')
        form.addRow("Restrictions:", self.restrictions)

        self.medecin = QLineEdit()
        self.medecin.setPlaceholderText("Nom du médecin")
        if self.is_edit:
            self.medecin.setText(self.visite.get('medecin') or '')
        form.addRow("Médecin:", self.medecin)

        self.prochaine_visite = QDateEdit()
        self.prochaine_visite.setCalendarPopup(True)
        self.prochaine_visite.setDisplayFormat("dd/MM/yyyy")
        self.prochaine_visite.setSpecialValueText("Non définie")
        if self.is_edit and self.visite.get('prochaine_visite'):
            d = self.visite['prochaine_visite']
            self.prochaine_visite.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Prochaine visite:", self.prochaine_visite)

        self.date_prochaine_convocation = QDateEdit()
        self.date_prochaine_convocation.setCalendarPopup(True)
        self.date_prochaine_convocation.setDisplayFormat("dd/MM/yyyy")
        self.date_prochaine_convocation.setSpecialValueText("Non définie")
        if self.is_edit and self.visite.get('date_prochaine_convocation'):
            d = self.visite['date_prochaine_convocation']
            self.date_prochaine_convocation.setDate(QDate(d.year, d.month, d.day))
        form.addRow("Date prochaine convocation:", self.date_prochaine_convocation)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(60)
        if self.is_edit:
            self.commentaire.setText(self.visite.get('commentaire') or '')
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addWidget(visite_group)

        self._ajouter_section_justificatif("Certificats médicaux", optionnel=True)

    def validate(self):
        return True, ""

    def save_to_db(self):
        prochaine = self.prochaine_visite.date()
        convocation = self.date_prochaine_convocation.date()
        data = {
            'date_visite': self.date_visite.date().toPyDate(),
            'type_visite': self.type_combo.currentText(),
            'resultat': self.resultat_combo.currentText() or None,
            'restrictions': self.restrictions.toPlainText().strip() or None,
            'medecin': self.medecin.text().strip() or None,
            'prochaine_visite': prochaine.toPyDate() if prochaine.year() > 1900 else None,
            'date_prochaine_convocation': convocation.toPyDate() if convocation.year() > 1900 else None,
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_visite(self.visite['id'], data)
        else:
            success, message, _ = create_visite(self.operateur_id, data)

        if success:
            self._sauvegarder_justificatif(
                self.operateur_id,
                date_expiration=data.get('prochaine_visite'),
            )

        if not success:
            raise Exception(message)


class EditAccidentDialog(JustificatifMixin, EmacFormDialog):
    """Formulaire pour ajouter/modifier un accident du travail."""

    def __init__(self, operateur_id: int, accident: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.accident = accident
        self.is_edit = accident is not None
        title = "Modifier l'accident" if self.is_edit else "Nouvel accident du travail"
        min_h = 500 if self.is_edit else 640
        super().__init__(title=title, min_width=500, min_height=min_h, add_title_bar=False, parent=parent)

    def init_ui(self):
        accident_group = QGroupBox("Accident et arrêt de travail")
        form = QFormLayout(accident_group)
        form.setSpacing(10)

        self.date_accident = QDateEdit()
        self.date_accident.setCalendarPopup(True)
        self.date_accident.setDisplayFormat("dd/MM/yyyy")
        if self.is_edit and self.accident.get('date_accident'):
            d = self.accident['date_accident']
            self.date_accident.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_accident.setDate(QDate.currentDate())
        self.date_accident.dateChanged.connect(self._on_date_changed)
        form.addRow("Date de l'accident:", self.date_accident)

        self.heure_accident = QTimeEdit()
        self.heure_accident.setDisplayFormat("HH:mm")
        if self.is_edit and self.accident.get('heure_accident'):
            h = self.accident['heure_accident']
            total_seconds = int(h.total_seconds()) if hasattr(h, 'total_seconds') else 0
            hours, remainder = divmod(total_seconds, 3600)
            minutes = remainder // 60
            self.heure_accident.setTime(QTime(hours % 24, minutes))
        else:
            self.heure_accident.setTime(QTime(8, 0))
        form.addRow("Heure de l'accident:", self.heure_accident)

        JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        self.jour_semaine = QComboBox()
        self.jour_semaine.addItems(JOURS)
        if self.is_edit and self.accident.get('jour_semaine'):
            idx = JOURS.index(self.accident['jour_semaine']) if self.accident['jour_semaine'] in JOURS else 0
            self.jour_semaine.setCurrentIndex(idx)
        else:
            self._sync_jour_from_date(self.date_accident.date())
        form.addRow("Jour de la semaine:", self.jour_semaine)

        self.lieu_accident = QLineEdit()
        self.lieu_accident.setPlaceholderText("Ex: Atelier usinage, Poste 0506, Quai de chargement...")
        if self.is_edit:
            self.lieu_accident.setText(self.accident.get('lieu_accident') or '')
        form.addRow("Lieu / poste de travail:", self.lieu_accident)

        self.avec_arret = QCheckBox("Accident avec arrêt de travail")
        if self.is_edit:
            self.avec_arret.setChecked(self.accident.get('avec_arret', False))
        form.addRow("", self.avec_arret)

        self.circonstances = QTextEdit()
        self.circonstances.setMaximumHeight(80)
        self.circonstances.setPlaceholderText("Décrivez les circonstances de l'accident")
        if self.is_edit:
            self.circonstances.setText(self.accident.get('circonstances') or '')
        form.addRow("Circonstances:", self.circonstances)

        self.siege_lesions = QLineEdit()
        self.siege_lesions.setPlaceholderText("Ex: Main droite, Dos, Pied gauche")
        if self.is_edit:
            self.siege_lesions.setText(self.accident.get('siege_lesions') or '')
        form.addRow("Siège des lésions:", self.siege_lesions)

        self.nature_lesions = QLineEdit()
        self.nature_lesions.setPlaceholderText("Ex: Fracture, Brûlure, Contusion")
        if self.is_edit:
            self.nature_lesions.setText(self.accident.get('nature_lesions') or '')
        form.addRow("Nature des lésions:", self.nature_lesions)

        self.nb_jours = QDoubleSpinBox()
        self.nb_jours.setRange(0, 365)
        self.nb_jours.setDecimals(0)
        self.nb_jours.setSuffix(" jours")
        if self.is_edit and self.accident.get('nb_jours_absence'):
            self.nb_jours.setValue(self.accident['nb_jours_absence'])
        form.addRow("Jours d'absence:", self.nb_jours)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(60)
        if self.is_edit:
            self.commentaire.setText(self.accident.get('commentaire') or '')
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addWidget(accident_group)

        if not self.is_edit:
            self._ajouter_section_justificatif("Documents médicaux")

    def _sync_jour_from_date(self, qdate: QDate):
        JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        day_of_week = qdate.dayOfWeek() - 1  # Qt: 1=Lundi..7=Dimanche -> index 0..6
        self.jour_semaine.setCurrentIndex(day_of_week)

    def _on_date_changed(self, qdate: QDate):
        self._sync_jour_from_date(qdate)

    def validate(self):
        if not self.is_edit:
            ok, msg = self._valider_justificatif()
            if not ok:
                return False, msg
        return True, ""

    def save_to_db(self):
        JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        heure = self.heure_accident.time()
        data = {
            'date_accident': self.date_accident.date().toPyDate(),
            'heure_accident': f"{heure.hour():02d}:{heure.minute():02d}:00",
            'jour_semaine': JOURS[self.jour_semaine.currentIndex()],
            'lieu_accident': self.lieu_accident.text().strip() or None,
            'avec_arret': self.avec_arret.isChecked(),
            'circonstances': self.circonstances.toPlainText().strip() or None,
            'siege_lesions': self.siege_lesions.text().strip() or None,
            'nature_lesions': self.nature_lesions.text().strip() or None,
            'nb_jours_absence': int(self.nb_jours.value()) if self.nb_jours.value() > 0 else None,
            'commentaire': self.commentaire.toPlainText().strip() or None,
        }

        if self.is_edit:
            success, message = update_accident(self.accident['id'], data)
        else:
            success, message, _ = create_accident(self.operateur_id, data)
            if success:
                self._sauvegarder_justificatif(self.operateur_id)

        if not success:
            raise Exception(message)


class EditValiditeDialog(JustificatifMixin, EmacFormDialog):
    """Dialog pour déclarer ou modifier une validité RQTH ou OETH."""

    def __init__(self, operateur_id: int, type_validite: str, validite: dict = None, parent=None):
        self.operateur_id = operateur_id
        self.type_validite = type_validite  # 'RQTH' ou 'OETH'
        self.validite = validite
        self.is_edit = validite is not None
        action = "Modifier" if self.is_edit else "Déclarer"
        super().__init__(
            title=f"{action} {type_validite}",
            min_width=420,
            min_height=360,
            add_title_bar=False,
            parent=parent,
        )

    def init_ui(self):
        validite_group = QGroupBox(f"Validité {self.type_validite}")
        form = QFormLayout(validite_group)
        form.setSpacing(10)

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        if self.is_edit and self.validite.get('date_debut'):
            d = self.validite['date_debut']
            self.date_debut.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_debut.setDate(QDate.currentDate())
        form.addRow("Date de début:", self.date_debut)

        # Ligne "Date de validité" + checkbox "Permanent" côte à côte
        date_fin_row = QWidget()
        date_fin_layout = QHBoxLayout(date_fin_row)
        date_fin_layout.setContentsMargins(0, 0, 0, 0)
        date_fin_layout.setSpacing(8)

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")

        is_permanent = (
            self.is_edit and self.validite.get('periodicite') == 'Permanent'
        )
        if self.is_edit and self.validite.get('date_fin'):
            d = self.validite['date_fin']
            self.date_fin.setDate(QDate(d.year, d.month, d.day))
        else:
            self.date_fin.setDate(QDate.currentDate().addYears(3))
        self.date_fin.setEnabled(not is_permanent)

        self.chk_permanent = QCheckBox("Permanent")
        self.chk_permanent.setChecked(is_permanent)
        self.chk_permanent.toggled.connect(self._on_permanent_toggled)

        date_fin_layout.addWidget(self.date_fin)
        date_fin_layout.addWidget(self.chk_permanent)
        form.addRow("Date de validité:", date_fin_row)

        if self.type_validite == 'OETH':
            self.taux_incapacite = QDoubleSpinBox()
            self.taux_incapacite.setRange(0, 100)
            self.taux_incapacite.setDecimals(1)
            self.taux_incapacite.setSuffix(" %")
            if self.is_edit and self.validite.get('taux_incapacite') is not None:
                self.taux_incapacite.setValue(float(self.validite['taux_incapacite']))
            form.addRow("Taux d'incapacité:", self.taux_incapacite)
        else:
            self.taux_incapacite = None

        self.commentaire = QLineEdit()
        if self.is_edit:
            self.commentaire.setText(self.validite.get('commentaire') or '')
        form.addRow("Commentaire:", self.commentaire)

        self.content_layout.addWidget(validite_group)
        self._ajouter_section_justificatif(self.type_validite, optionnel=True)

    def _on_permanent_toggled(self, checked: bool):
        self.date_fin.setEnabled(not checked)
        if checked:
            self.date_fin.setStyleSheet("color: #9ca3af;")
        else:
            self.date_fin.setStyleSheet("")

    def validate(self):
        if not self.chk_permanent.isChecked():
            if self.date_fin.date() < self.date_debut.date():
                return False, "La date de validité doit être postérieure à la date de début."
        return True, ""

    def save_to_db(self):
        permanent = self.chk_permanent.isChecked()
        data = {
            'type_validite': self.type_validite,
            'date_debut': self.date_debut.date().toPyDate(),
            'date_fin': None if permanent else self.date_fin.date().toPyDate(),
            'periodicite': 'Permanent' if permanent else 'Périodique',
            'taux_incapacite': self.taux_incapacite.value() if self.taux_incapacite else None,
            'commentaire': self.commentaire.text().strip() or None,
        }

        if self.is_edit:
            success, message = update_validite(self.validite['id'], data)
        else:
            success, message, _ = create_validite(self.operateur_id, data)

        if success:
            self._sauvegarder_justificatif(
                self.operateur_id,
                date_expiration=data.get('date_fin'),
                notes=f"Justificatif {self.type_validite}",
            )

        if not success:
            raise Exception(message)
