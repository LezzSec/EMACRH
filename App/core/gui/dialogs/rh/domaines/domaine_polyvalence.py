# -*- coding: utf-8 -*-
"""
Domaine RH : Polyvalence (niveaux par poste + dossiers de formation).
"""
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QFrame, QWidget
from PyQt5.QtCore import Qt

from core.gui.components.ui_theme import EmacCard, EmacButton
from core.services.permission_manager import can
from .domaine_base import DomaineWidget


class DomainePolyvalence(DomaineWidget):

    def _build(self, donnees: dict, documents: list):
        polyvalences = donnees.get('polyvalences', [])

        if not polyvalences:
            card_empty = EmacCard("Polyvalence")
            card_empty.body.addWidget(QLabel("Aucune polyvalence enregistrée pour cette personne."))
            self._layout.addWidget(card_empty)
            return

        if can("production.grilles.export") or can("admin.permissions"):
            btn_admin = EmacButton("Gérer les dossiers de formation", variant="ghost")
            btn_admin.clicked.connect(self._ouvrir_gestion_docs_formation)
            self._layout.addWidget(btn_admin, alignment=Qt.AlignRight)

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

                if poly.get('prochaine_evaluation'):
                    lbl_date = QLabel(f"  Prochaine éval : {self._format_date(poly['prochaine_evaluation'])}")
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
                        btn_lire.clicked.connect(
                            lambda checked, did=doc['id']: self._ouvrir_doc_formation(did)
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

            self._layout.addWidget(card)

    def _ouvrir_doc_formation(self, doc_id: int):
        self._vm.extraire_doc_formation(doc_id)

    def _ouvrir_gestion_docs_formation(self):
        from core.gui.dialogs.gestion_rh_dialogs import GestionDocsFormationDialog
        dialog = GestionDocsFormationDialog(self)
        dialog.exec_()
        self.refresh_requested.emit()
