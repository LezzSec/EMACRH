# -*- coding: utf-8 -*-
"""
Header opérateur + barre de navigation entre les domaines RH.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from gui.view_models.gestion_rh_view_model import DomaineRH, get_domaines_rh


class RhHeaderWidget(QWidget):
    """
    Affiche le nom/matricule/statut de l'opérateur sélectionné
    et la barre de navigation entre les domaines RH.
    """

    domaine_changed = pyqtSignal(str)
    archives_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self._creer_header_operateur())
        layout.addWidget(self._creer_navigation_domaines())

    def _creer_header_operateur(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet("QFrame { background: #1e40af; border-radius: 8px; }")
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
            background: #10b981; color: white; padding: 4px 10px;
            border-radius: 12px; font-weight: bold; font-size: 11px;
        """)
        layout.addWidget(self.badge_statut)

        return header

    def _creer_navigation_domaines(self) -> QWidget:
        nav = QWidget()
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.boutons_domaines = {}
        for domaine in get_domaines_rh():
            btn = QPushButton(domaine['nom'])
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty('domaine', domaine['code'])
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 16px; border: 1px solid #e5e7eb; border-radius: 8px;
                    background: white; color: #374151; font-weight: 500;
                }
                QPushButton:hover { background: #f9fafb; border-color: #d1d5db; }
                QPushButton:checked { background: #1e40af; color: white; border-color: #1e40af; }
            """)
            btn.clicked.connect(lambda checked, d=domaine['code']: self.domaine_changed.emit(d))
            layout.addWidget(btn)
            self.boutons_domaines[domaine['code']] = btn

        self.btn_archives = QPushButton("📦 Archives")
        self.btn_archives.setCheckable(True)
        self.btn_archives.setCursor(Qt.PointingHandCursor)
        self.btn_archives.setStyleSheet("""
            QPushButton {
                padding: 10px 16px; border: 1px solid #f59e0b; border-radius: 8px;
                background: #fffbeb; color: #92400e; font-weight: 500;
            }
            QPushButton:hover { background: #fef3c7; border-color: #d97706; }
            QPushButton:checked { background: #f59e0b; color: white; border-color: #f59e0b; }
        """)
        self.btn_archives.clicked.connect(self._on_archives_click)
        self.btn_archives.setVisible(False)
        layout.addWidget(self.btn_archives)

        layout.addStretch()
        return nav

    def refresh(self, operateur: dict):
        nom_complet = operateur.get('nom_complet', f"{operateur.get('prenom', '')} {operateur.get('nom', '')}")
        self.label_nom_operateur.setText(nom_complet)
        self.label_matricule.setText(operateur.get('matricule', '-'))

        statut = operateur.get('statut', 'ACTIF')
        if statut == 'ACTIF':
            self.badge_statut.setText("ACTIF")
            self.badge_statut.setStyleSheet("""
                background: #10b981; color: white; padding: 6px 12px;
                border-radius: 16px; font-weight: bold; font-size: 12px;
            """)
        else:
            self.badge_statut.setText("INACTIF")
            self.badge_statut.setStyleSheet("""
                background: #6b7280; color: white; padding: 6px 12px;
                border-radius: 16px; font-weight: bold; font-size: 12px;
            """)

        is_production = (operateur.get('numposte') or '') == 'Production'
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == DomaineRH.GENERAL.value)
            if code == DomaineRH.POLYVALENCE.value:
                btn.setVisible(is_production)
        self.btn_archives.setChecked(False)

    def set_domaine(self, code_domaine: str):
        for code, btn in self.boutons_domaines.items():
            btn.setChecked(code == code_domaine)
        self.btn_archives.setChecked(False)

    def update_archives_count(self, n: int):
        if n > 0:
            self.btn_archives.setText(f"📦 Archives ({n})")
            self.btn_archives.setVisible(True)
        else:
            self.btn_archives.setVisible(False)

    def _on_archives_click(self):
        for btn in self.boutons_domaines.values():
            btn.setChecked(False)
        self.btn_archives.setChecked(True)
        self.archives_clicked.emit()

    @property
    def archives_actif(self) -> bool:
        return self.btn_archives.isChecked()
