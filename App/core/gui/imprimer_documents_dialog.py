# -*- coding: utf-8 -*-
"""
Dialog multi-opérateurs pour l'impression des documents d'évaluation à la demande.

Affiche la liste des opérateurs (issue du filtre courant) avec leurs documents
configurés selon leur niveau et poste. L'utilisateur coche ce qu'il veut
générer puis valide en une seule action.

Usage:
    from core.gui.imprimer_documents_dialog import ImprimerDocumentsDialog

    dialog = ImprimerDocumentsDialog(
        operateurs=[
            {'personnel_id': 1, 'nom': 'Dupont', 'prenom': 'Jean'},
            ...
        ],
        parent=self
    )
    dialog.exec_()
"""

from typing import List, Dict, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QMessageBox, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from core.services.document_trigger_service import DocumentTriggerService, PendingDocument
from core.utils.logging_config import get_logger

logger = get_logger(__name__)


class ImprimerDocumentsDialog(QDialog):
    """
    Dialog de sélection multi-opérateurs pour l'impression à la demande.

    Charge les documents configurés (via les règles document_event_rules)
    pour chaque opérateur en fonction de ses niveaux et postes actuels.
    Affiche un arbre opérateur → documents avec cases à cocher.
    """

    def __init__(self, operateurs: List[Dict], parent=None):
        """
        Args:
            operateurs: Liste de dicts avec au minimum:
                        personnel_id, nom, prenom
            parent: Widget parent Qt
        """
        super().__init__(parent)
        self._operateurs = operateurs

        self.setWindowTitle("Impression des documents d'évaluation")
        self.setMinimumSize(720, 550)
        self.resize(820, 620)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        self._init_ui()
        self._load_data()
        self._apply_style()

    # ------------------------------------------------------------------ UI --

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        hdr = QHBoxLayout()
        icon = QLabel("🖨️")
        icon.setFont(QFont("Segoe UI", 20))
        hdr.addWidget(icon)

        texts = QVBoxLayout()
        title = QLabel("Impression des documents d'évaluation")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        texts.addWidget(title)

        sub = QLabel(
            "Sélectionnez les opérateurs et documents à générer. "
            "Les documents proposés dépendent du niveau et du poste de chaque opérateur."
        )
        sub.setStyleSheet("color: #64748b; font-size: 11px;")
        sub.setWordWrap(True)
        texts.addWidget(sub)

        hdr.addLayout(texts, 1)
        layout.addLayout(hdr)

        # Barre recherche + boutons globaux
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Rechercher un opérateur…")
        self.search_input.textChanged.connect(self._filter_tree)
        bar.addWidget(self.search_input, 1)

        btn_all = QPushButton("Tout sélectionner")
        btn_all.setObjectName("secondaryButton")
        btn_all.clicked.connect(lambda: self._toggle_all(True))
        bar.addWidget(btn_all)

        btn_none = QPushButton("Tout désélectionner")
        btn_none.setObjectName("secondaryButton")
        btn_none.clicked.connect(lambda: self._toggle_all(False))
        bar.addWidget(btn_none)

        layout.addLayout(bar)

        # Arbre opérateur → documents
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Opérateur / Document", "Déclencheur"])
        self.tree.setColumnWidth(0, 440)
        self.tree.header().setStretchLastSection(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.tree.setAnimated(True)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree, 1)

        # Ligne de statut
        self.status_label = QLabel("Chargement des documents…")
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px; padding: 2px 0;")
        layout.addWidget(self.status_label)

        # Boutons
        btn_row = QHBoxLayout()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("cancelButton")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_row.addStretch()

        self.btn_preview = QPushButton("👁 Visualiser")
        self.btn_preview.setObjectName("secondaryButton")
        self.btn_preview.setEnabled(False)
        self.btn_preview.clicked.connect(self._preview_selected)
        btn_row.addWidget(self.btn_preview)

        self.btn_generate = QPushButton("🖨️ Imprimer")
        self.btn_generate.setObjectName("primaryButton")
        self.btn_generate.setEnabled(False)
        self.btn_generate.clicked.connect(self._generate_selected)
        btn_row.addWidget(self.btn_generate)

        layout.addLayout(btn_row)

    # --------------------------------------------------------------- Data --

    def _load_data(self):
        """Charge les documents disponibles pour chaque opérateur."""
        from core.services.evaluation_service import get_polyvalences_actuelles_operateur
        from core.services.event_rule_service import get_matching_templates

        self.tree.blockSignals(True)
        self.tree.clear()

        total_docs = 0
        ops_with_docs = 0
        ops_without_docs = 0

        for op in self._operateurs:
            op_id = op.get('personnel_id')
            nom = op.get('nom', '')
            prenom = op.get('prenom', '')

            try:
                polyvalences = get_polyvalences_actuelles_operateur(op_id)
                documents = []
                if polyvalences:
                    documents = DocumentTriggerService.compute_documents_for_polyvalences(
                        op_id, nom, prenom, polyvalences
                    )

                # Fallback : si aucun document via les polyvalences,
                # chercher les templates liés à evaluation.overdue (en retard)
                # ou evaluation.planned (à planifier) selon la date de chaque poste.
                if not documents:
                    from datetime import date as _date
                    today = _date.today()
                    seen_template_ids: set = set()

                    for poly in (polyvalences or []):
                        code_poste = poly.get('poste_code') or poly.get('numposte')
                        prochaine = poly.get('prochaine_evaluation')
                        if not code_poste or not prochaine:
                            continue

                        # Événement selon que l'évaluation est en retard ou à venir
                        event_name = (
                            'evaluation.overdue' if prochaine < today
                            else 'evaluation.planned'
                        )
                        event_data = {
                            'operateur_id': op_id,
                            'nom': nom,
                            'prenom': prenom,
                            'code_poste': code_poste,
                        }
                        for tpl in get_matching_templates(event_name, event_data):
                            if tpl['template_id'] in seen_template_ids:
                                continue
                            seen_template_ids.add(tpl['template_id'])
                            documents.append(PendingDocument(
                                template_id=tpl['template_id'],
                                template_nom=tpl['template_nom'],
                                execution_mode=tpl['execution_mode'],
                                operateur_id=op_id,
                                operateur_nom=nom,
                                operateur_prenom=prenom,
                                event_name=event_name,
                                rule_id=tpl.get('rule_id', 0),
                            ))

                if documents:
                    ops_with_docs += 1

                    # Nœud opérateur (niveau 0)
                    op_item = QTreeWidgetItem(self.tree)
                    op_item.setText(0, f"{prenom} {nom}")
                    op_item.setCheckState(0, Qt.Checked)
                    op_item.setFlags(
                        Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate
                    )
                    op_item.setData(0, Qt.UserRole, {'type': 'operator'})
                    bold = QFont()
                    bold.setBold(True)
                    op_item.setFont(0, bold)

                    # Nœuds documents (niveau 1)
                    for doc in documents:
                        doc_item = QTreeWidgetItem(op_item)
                        doc_item.setText(0, f"  📄 {doc.template_nom}")
                        doc_item.setText(1, self._event_label(doc.event_name))
                        doc_item.setCheckState(0, Qt.Checked)
                        doc_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                        doc_item.setData(0, Qt.UserRole, {'type': 'document', 'doc': doc})
                        total_docs += 1

                    op_item.setExpanded(True)

                else:
                    ops_without_docs += 1

                    # Nœud opérateur sans documents (sélectionnable, décoché par défaut)
                    op_item = QTreeWidgetItem(self.tree)
                    op_item.setText(0, f"{prenom} {nom}")
                    op_item.setText(1, "Aucun document configuré")
                    op_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                    op_item.setCheckState(0, Qt.Checked)
                    op_item.setData(0, Qt.UserRole, {
                        'type': 'operator_no_doc',
                        'operateur_id': op_id,
                        'nom': nom,
                        'prenom': prenom,
                    })
                    bold = QFont()
                    bold.setBold(True)
                    op_item.setFont(0, bold)
                    op_item.setForeground(0, QColor('#94a3b8'))
                    op_item.setForeground(1, QColor('#94a3b8'))

            except Exception as e:
                logger.warning(f"Erreur chargement docs pour {prenom} {nom}: {e}")

        self.tree.blockSignals(False)

        if total_docs == 0:
            self.status_label.setText("Aucun document disponible pour ces opérateurs")
        else:
            parts = [f"{total_docs} document(s) disponible(s) pour {ops_with_docs} opérateur(s)"]
            if ops_without_docs:
                parts.append(f"{ops_without_docs} sans document configuré")
            self.status_label.setText(" — ".join(parts))
        self._update_count()

    def _event_label(self, event_name: str) -> str:
        labels = {
            'polyvalence.niveau_1_reached': 'Niveau 1 atteint',
            'polyvalence.niveau_2_reached': 'Niveau 2 atteint',
            'polyvalence.niveau_3_reached': 'Niveau 3 atteint',
            'polyvalence.niveau_4_reached': 'Niveau 4 atteint',
            'polyvalence.niveau_changed': 'Changement de niveau',
            'evaluation.completed': 'Évaluation terminée',
            'evaluation.overdue': 'Évaluation en retard',
            'evaluation.planned': 'Évaluation à planifier',
        }
        return labels.get(event_name, event_name)

    # ---------------------------------------------------------- Interactions --

    def _on_item_changed(self, item, column):
        if column == 0:
            self._update_count()

    def _update_count(self):
        """Recompte les documents cochés et met à jour le bouton Générer."""
        doc_count = 0
        no_doc_count = 0
        for i in range(self.tree.topLevelItemCount()):
            op = self.tree.topLevelItem(i)
            data = op.data(0, Qt.UserRole)
            if data and data.get('type') == 'operator_no_doc':
                if op.checkState(0) == Qt.Checked:
                    no_doc_count += 1
            else:
                for j in range(op.childCount()):
                    if op.child(j).checkState(0) == Qt.Checked:
                        doc_count += 1

        total = doc_count + no_doc_count
        self.btn_generate.setEnabled(total > 0)
        self.btn_preview.setEnabled(doc_count > 0)
        if doc_count > 0:
            self.btn_generate.setText(f"🖨️ Imprimer {doc_count} document(s)")
        elif no_doc_count > 0:
            self.btn_generate.setText(f"🖨️ Imprimer ({no_doc_count} sans document)")
        else:
            self.btn_generate.setText("🖨️ Imprimer")

    def _toggle_all(self, checked: bool):
        """Coche ou décoche tous les opérateurs et documents visibles."""
        state = Qt.Checked if checked else Qt.Unchecked
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            op = self.tree.topLevelItem(i)
            if op.isHidden():
                continue
            op.setCheckState(0, state)
            for j in range(op.childCount()):
                op.child(j).setCheckState(0, state)
        self.tree.blockSignals(False)
        self._update_count()

    def _filter_tree(self, text: str):
        """Masque les opérateurs ne correspondant pas au texte de recherche."""
        text = text.lower().strip()
        for i in range(self.tree.topLevelItemCount()):
            op = self.tree.topLevelItem(i)
            data = op.data(0, Qt.UserRole)
            if not data or data.get('type') not in ('operator', 'operator_no_doc'):
                continue
            op.setHidden(bool(text) and text not in op.text(0).lower())

    def _collect_selected_docs(self):
        """Retourne (selected_docs, no_doc_ops) depuis l'arbre coché."""
        selected: List[PendingDocument] = []
        no_doc_ops: List[str] = []
        for i in range(self.tree.topLevelItemCount()):
            op = self.tree.topLevelItem(i)
            if op.isHidden():
                continue
            data = op.data(0, Qt.UserRole)
            if data and data.get('type') == 'operator_no_doc':
                if op.checkState(0) == Qt.Checked:
                    no_doc_ops.append(op.text(0))
                continue
            for j in range(op.childCount()):
                child = op.child(j)
                if child.checkState(0) == Qt.Checked:
                    child_data = child.data(0, Qt.UserRole)
                    if child_data and child_data.get('type') == 'document':
                        selected.append(child_data['doc'])
        return selected, no_doc_ops

    def _preview_selected(self):
        """Génère et ouvre les documents cochés pour visualisation (sans impression)."""
        from core.services.template_service import open_template_file

        selected, _ = self._collect_selected_docs()
        if not selected:
            return

        errors = []
        for doc in selected:
            success, msg, path = DocumentTriggerService.generate_on_demand(doc)
            if success and path:
                open_template_file(path)
            else:
                errors.append(
                    f"• {doc.template_nom} ({doc.operateur_prenom} {doc.operateur_nom}): {msg}"
                )

        if errors:
            QMessageBox.warning(
                self, "Erreurs de génération",
                "Certains documents n'ont pas pu être générés :\n\n" + "\n".join(errors)
            )

    def _generate_selected(self):
        """Génère tous les documents cochés et lance l'impression."""
        selected, no_doc_ops = self._collect_selected_docs()

        if not selected and not no_doc_ops:
            return

        errors = []
        generated = []

        for doc in selected:
            success, msg, path = DocumentTriggerService.generate_on_demand(doc)
            if success and path:
                generated.append(path)
            else:
                errors.append(
                    f"• {doc.template_nom} ({doc.operateur_prenom} {doc.operateur_nom}): {msg}"
                )

        if errors:
            QMessageBox.warning(
                self, "Erreurs de génération",
                "Certains documents n'ont pas pu être générés :\n\n" + "\n".join(errors)
            )

        if generated:
            from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
            from core.services.template_service import print_template_file

            printer = QPrinter(QPrinter.HighResolution)
            dlg = QPrintDialog(printer, self)
            dlg.setWindowTitle("Impression — Choisir une imprimante")

            if dlg.exec_() == QPrintDialog.Accepted:
                printer_name = printer.printerName()
                print_errors = []
                for path in generated:
                    ok, msg = print_template_file(path, printer_name)
                    if not ok:
                        logger.warning(f"Impression échouée pour {path}: {msg}")
                        print_errors.append(msg)
                if print_errors:
                    QMessageBox.warning(
                        self, "Erreurs d'impression",
                        "Certains documents n'ont pas pu être imprimés :\n\n"
                        + "\n".join(f"• {e}" for e in print_errors)
                    )

        msg_parts = []
        if no_doc_ops:
            noms = "\n".join(f"• {n}" for n in no_doc_ops)
            msg_parts.append(
                f"{len(no_doc_ops)} opérateur(s) sélectionné(s) sans document configuré :\n{noms}"
            )

        if msg_parts:
            QMessageBox.information(self, "Résultat", "\n\n".join(msg_parts))

        if generated or no_doc_ops:
            self.accept()
        elif not errors:
            self.reject()

    # ---------------------------------------------------------------- Style --

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }

            QTreeWidget {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background: #fafafa;
                font-size: 12px;
            }
            QTreeWidget::item { padding: 4px 6px; min-height: 24px; }
            QTreeWidget::item:hover { background: #f1f5f9; }

            QHeaderView::section {
                background: #f8fafc;
                color: #475569;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #e2e8f0;
            }

            QLineEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                background: #f8fafc;
            }
            QLineEdit:focus { border-color: #3b82f6; background: #ffffff; }

            QPushButton {
                padding: 7px 14px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background: #f8fafc;
                color: #475569;
                font-size: 12px;
            }
            QPushButton:hover { background: #f1f5f9; }

            QPushButton#primaryButton {
                background: #3b82f6;
                color: white;
                font-weight: bold;
                border: none;
                min-width: 200px;
                padding: 8px 18px;
            }
            QPushButton#primaryButton:hover { background: #2563eb; }
            QPushButton#primaryButton:disabled {
                background: #cbd5e1;
                color: #94a3b8;
            }

            QPushButton#secondaryButton {
                background: #f1f5f9;
                color: #334155;
                border: 1px solid #e2e8f0;
            }
            QPushButton#secondaryButton:hover { background: #e2e8f0; }

            QPushButton#cancelButton {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
            }
            QPushButton#cancelButton:hover { background: #fee2e2; }
        """)
