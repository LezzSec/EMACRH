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

from pathlib import Path
from typing import List, Dict, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QMessageBox, QAbstractItemView,
    QScrollArea, QFrame, QWidget,
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

        self.btn_generate = QPushButton("🖨️ Générer les sélectionnés")
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
        if doc_count > 0:
            self.btn_generate.setText(f"🖨️ Générer {doc_count} document(s)")
        elif no_doc_count > 0:
            self.btn_generate.setText(f"🖨️ Générer ({no_doc_count} sans document)")
        else:
            self.btn_generate.setText("🖨️ Générer les sélectionnés")

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

    def _generate_selected(self):
        """Génère tous les documents cochés puis ouvre l'aperçu avant impression."""
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

        if not selected and not no_doc_ops:
            return

        errors = []
        generated_infos: List[Dict] = []

        for doc in selected:
            success, msg, path = DocumentTriggerService.generate_on_demand(doc)
            if success and path:
                generated_infos.append({
                    'path': path,
                    'nom': doc.template_nom,
                    'operateur': f"{doc.operateur_prenom} {doc.operateur_nom}",
                })
            else:
                errors.append(
                    f"• {doc.template_nom} ({doc.operateur_prenom} {doc.operateur_nom}): {msg}"
                )

        if errors:
            QMessageBox.warning(
                self, "Erreurs de génération",
                "Certains documents n'ont pas pu être générés :\n\n" + "\n".join(errors)
            )

        # Ouvrir la fenêtre d'aperçu avant impression
        if generated_infos:
            preview = PrintPreviewDialog(generated_infos, parent=self)
            preview.exec_()

        # Message pour les opérateurs sans document configuré
        if no_doc_ops:
            noms = "\n".join(f"• {n}" for n in no_doc_ops)
            QMessageBox.information(
                self, "Opérateurs sans document",
                f"{len(no_doc_ops)} opérateur(s) sélectionné(s) sans document configuré :\n{noms}"
            )

        if generated_infos or no_doc_ops:
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


# ---------------------------------------------------------------------------
# Dialog d'aperçu avant impression
# ---------------------------------------------------------------------------

class PrintPreviewDialog(QDialog):
    """
    Affiche les documents générés et propose de les prévisualiser ou d'imprimer.

    Chaque document dispose de deux boutons :
      - "Prévisualiser" : ouvre le fichier avec l'application par défaut.
      - "Imprimer"      : envoie directement à l'imprimante (via la commande print OS).

    Un bouton "Tout imprimer" lance l'impression de tous les documents d'un coup.
    """

    def __init__(self, generated_docs: List[Dict], parent=None):
        """
        Args:
            generated_docs: liste de dicts avec les clés :
                            'path'      (str) – chemin complet du fichier généré
                            'nom'       (str) – nom lisible du template
                            'operateur' (str) – "Prénom Nom" de l'opérateur
            parent: widget parent Qt
        """
        super().__init__(parent)
        self._docs = generated_docs

        self.setWindowTitle("Aperçu avant impression")
        self.setMinimumSize(640, 400)
        self.resize(740, min(160 + len(generated_docs) * 80, 620))
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        self._init_ui()
        self._apply_style()

    # ------------------------------------------------------------------ UI --

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # En-tête
        hdr = QHBoxLayout()
        icon = QLabel("🖨️")
        icon.setFont(QFont("Segoe UI", 22))
        hdr.addWidget(icon)

        texts = QVBoxLayout()
        title = QLabel("Documents prêts à l'impression")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        texts.addWidget(title)

        n = len(self._docs)
        sub = QLabel(
            f"{n} document(s) généré(s). "
            "Prévisualisez ou imprimez chacun individuellement, ou tout à la fois."
        )
        sub.setStyleSheet("color: #64748b; font-size: 11px;")
        sub.setWordWrap(True)
        texts.addWidget(sub)

        hdr.addLayout(texts, 1)
        layout.addLayout(hdr)

        # Zone scrollable — liste des documents
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self._docs_layout = QVBoxLayout(container)
        self._docs_layout.setSpacing(8)
        self._docs_layout.setContentsMargins(0, 0, 4, 0)

        for doc_info in self._docs:
            self._add_doc_row(doc_info)

        self._docs_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # Boutons du bas
        btn_row = QHBoxLayout()

        btn_close = QPushButton("Fermer")
        btn_close.setObjectName("cancelButton")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        btn_row.addStretch()

        btn_print_all = QPushButton(f"🖨️  Tout imprimer ({n})")
        btn_print_all.setObjectName("primaryButton")
        btn_print_all.clicked.connect(self._print_all)
        btn_row.addWidget(btn_print_all)

        layout.addLayout(btn_row)

    def _add_doc_row(self, doc_info: Dict):
        """Ajoute une ligne (card) pour un document généré."""
        frame = QFrame()
        frame.setObjectName("docRow")

        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(10)

        # Icône selon extension
        path_str = doc_info.get('path', '')
        ext = Path(path_str).suffix.lower() if path_str else ''
        icon_map = {'.pdf': '📄', '.docx': '📝', '.doc': '📝',
                    '.xlsx': '📊', '.xls': '📊', '.odt': '📝', '.ods': '📊'}
        icon_lbl = QLabel(icon_map.get(ext, '📄'))
        icon_lbl.setFont(QFont("Segoe UI", 16))
        icon_lbl.setFixedWidth(26)
        row.addWidget(icon_lbl)

        # Nom + opérateur
        info_col = QVBoxLayout()
        name_lbl = QLabel(doc_info.get('nom', 'Document'))
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_lbl.setStyleSheet("color: #1e293b;")
        info_col.addWidget(name_lbl)

        op_lbl = QLabel(f"Pour : {doc_info.get('operateur', '')}")
        op_lbl.setStyleSheet("color: #64748b; font-size: 10px;")
        info_col.addWidget(op_lbl)
        row.addLayout(info_col, 1)

        # Bouton Prévisualiser
        btn_preview = QPushButton("👁  Prévisualiser")
        btn_preview.setObjectName("secondaryButton")
        btn_preview.setFixedWidth(135)
        btn_preview.clicked.connect(lambda _checked, p=path_str: self._preview(p))
        row.addWidget(btn_preview)

        # Bouton Imprimer
        btn_print = QPushButton("🖨️  Imprimer")
        btn_print.setObjectName("printButton")
        btn_print.setFixedWidth(115)
        btn_print.clicked.connect(lambda _checked, p=path_str: self._print_one(p))
        row.addWidget(btn_print)

        self._docs_layout.addWidget(frame)

    # --------------------------------------------------------- Actions --

    def _preview(self, path: str):
        """
        Ouvre le fichier pour prévisualisation.

        Pour les fichiers Excel, convertit d'abord en PDF (toutes feuilles) puis
        ouvre le PDF dans le lecteur par défaut — la fenêtre reste ouverte.
        """
        import os
        import platform
        import subprocess
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt as _Qt
        try:
            p = Path(path).resolve()
            if not p.is_file():
                QMessageBox.warning(self, "Fichier introuvable", f"Le fichier n'existe plus :\n{path}")
                return

            if platform.system() == 'Windows':
                ext = p.suffix.lower()
                if ext in ('.xlsx', '.xlsm', '.xls'):
                    # Conversion → PDF pour voir TOUTES les feuilles
                    QApplication.setOverrideCursor(_Qt.WaitCursor)
                    try:
                        pdf_path = self._excel_to_pdf(p)
                    finally:
                        QApplication.restoreOverrideCursor()
                    target = pdf_path if pdf_path else p
                else:
                    target = p
                os.startfile(str(target))
            elif platform.system() == 'Darwin':
                subprocess.run(['open', str(p)], check=True)
            else:
                subprocess.run(['xdg-open', str(p)], check=True)
        except Exception as e:
            logger.error(f"Erreur prévisualisation: {e}")
            QMessageBox.warning(self, "Erreur", "Impossible d'ouvrir le document.")

    def _excel_to_pdf(self, xlsx_path: Path) -> Optional[Path]:
        """
        Convertit un fichier Excel en PDF via PowerShell + Excel COM.

        Toutes les feuilles sont incluses dans le PDF résultant.
        Retourne le chemin du PDF, ou None si la conversion échoue.
        """
        import subprocess
        pdf_path = xlsx_path.with_suffix('.pdf')

        # Apostrophes PowerShell : doubler les apostrophes dans les chemins
        safe_xlsx = str(xlsx_path).replace("'", "''")
        safe_pdf = str(pdf_path).replace("'", "''")

        ps_lines = [
            f"$excel = New-Object -ComObject Excel.Application",
            f"$excel.Visible = $false",
            f"$excel.DisplayAlerts = $false",
            f"$wb = $excel.Workbooks.Open('{safe_xlsx}')",
            f"$wb.ExportAsFixedFormat(0, '{safe_pdf}')",
            f"$wb.Close($false)",
            f"$excel.Quit()",
            f"[System.Runtime.Interopservices.Marshal]::ReleaseComObject($wb) | Out-Null",
            f"[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null",
        ]
        ps_script = "; ".join(ps_lines)

        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_script],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0 and pdf_path.exists():
                return pdf_path
            logger.warning(f"Conversion Excel→PDF échouée (rc={result.returncode}): {result.stderr.strip()}")
        except Exception as e:
            logger.error(f"Erreur conversion Excel→PDF: {e}")
        return None

    def _show_print_dialog(self, file_path: Path):
        """
        Affiche QPrintDialog pour sélectionner l'imprimante, le nombre de copies,
        l'orientation, etc., puis envoie le fichier via PowerShell en arrière-plan
        (sans qu'aucune fenêtre de lecteur n'apparaisse à l'écran).
        """
        import subprocess
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Imprimer — sélectionnez l'imprimante")

        if dialog.exec_() != QPrintDialog.Accepted:
            return  # Annulé par l'utilisateur

        printer_name = printer.printerName()
        copies = max(1, printer.copyCount())

        # Apostrophes PowerShell
        safe_file = str(file_path).replace("'", "''")
        safe_printer = printer_name.replace("'", "''")

        ps_cmd = (
            f"Start-Process -FilePath '{safe_file}' "
            f"-Verb PrintTo "
            f"-ArgumentList '\"{safe_printer}\"' "
            f"-WindowStyle Hidden"
        )

        # CREATE_NO_WINDOW : pas de console PowerShell visible
        CREATE_NO_WINDOW = 0x08000000

        for _ in range(copies):
            try:
                subprocess.Popen(
                    ['powershell', '-NoProfile', '-NonInteractive',
                     '-WindowStyle', 'Hidden', '-Command', ps_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=CREATE_NO_WINDOW,
                )
            except Exception as e:
                logger.error(f"Erreur envoi impression: {e}")

    def _print_excel_via_com(self, xlsx_path: Path):
        """
        Affiche QPrintDialog puis imprime via Excel COM en arrière-plan.

        Excel s'exécute en mode invisible : aucune fenêtre n'apparaît.
        Toutes les feuilles du classeur sont incluses dans le travail d'impression.
        """
        import subprocess
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt as _Qt

        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Imprimer — sélectionnez l'imprimante")

        if dialog.exec_() != QPrintDialog.Accepted:
            return

        printer_name = printer.printerName()
        copies = max(1, printer.copyCount())

        safe_xlsx = str(xlsx_path).replace("'", "''")
        safe_printer = printer_name.replace("'", "''")

        # Excel COM : invisible, imprime toutes les feuilles sur l'imprimante choisie
        ps_script = "\n".join([
            "$excel = New-Object -ComObject Excel.Application",
            "$excel.Visible = $false",
            "$excel.DisplayAlerts = $false",
            f"$wb = $excel.Workbooks.Open('{safe_xlsx}')",
            # Tenter de définir l'imprimante (format exact requis par Excel COM)
            "try {",
            f"    $excel.ActivePrinter = '{safe_printer}'",
            "} catch { }",
            # PrintOut sans From/To = toutes les feuilles
            f"$wb.PrintOut([System.Reflection.Missing]::Value, [System.Reflection.Missing]::Value, {copies}, $false)",
            "$wb.Close($false)",
            "$excel.Quit()",
            "[System.Runtime.Interopservices.Marshal]::ReleaseComObject($wb) | Out-Null",
            "[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null",
        ])

        CREATE_NO_WINDOW = 0x08000000
        QApplication.setOverrideCursor(_Qt.WaitCursor)
        try:
            subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_script],
                capture_output=True, text=True, timeout=60,
                creationflags=CREATE_NO_WINDOW,
            )
        finally:
            QApplication.restoreOverrideCursor()

    def _print_one(self, path: str):
        """
        Ouvre QPrintDialog puis imprime sans faire apparaître de fenêtre de prévisualisation.

        - Excel (.xlsx/.xlsm/.xls) : Excel COM en arrière-plan, aucune fenêtre visible.
        - Autres formats            : PowerShell avec fenêtre cachée.
        """
        import platform
        import subprocess
        try:
            p = Path(path).resolve()
            if not p.is_file():
                QMessageBox.warning(self, "Fichier introuvable", f"Le fichier n'existe plus :\n{path}")
                return

            if platform.system() == 'Windows':
                if p.suffix.lower() in ('.xlsx', '.xlsm', '.xls'):
                    self._print_excel_via_com(p)
                else:
                    self._show_print_dialog(p)
            else:
                subprocess.run(['lpr', str(p)], check=True)
        except Exception as e:
            logger.error(f"Erreur impression: {e}")
            QMessageBox.warning(self, "Erreur", "Impossible d'imprimer le document.")

    def _print_all(self):
        """Imprime tous les documents de la liste."""
        failed = []
        for doc_info in self._docs:
            path = doc_info.get('path', '')
            if not path:
                continue
            try:
                self._print_one(path)
            except Exception:
                failed.append(doc_info.get('nom', path))

        if failed:
            QMessageBox.warning(
                self, "Erreurs d'impression",
                "Les documents suivants n'ont pas pu être imprimés :\n" +
                "\n".join(f"• {n}" for n in failed)
            )

    # ---------------------------------------------------------------- Style --

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QScrollArea { border: none; background: #ffffff; }
            QWidget { background: #ffffff; }

            QFrame#docRow {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QFrame#docRow:hover { background: #f1f5f9; border-color: #cbd5e1; }

            QPushButton {
                padding: 6px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background: #f8fafc;
                color: #475569;
                font-size: 11px;
            }
            QPushButton:hover { background: #f1f5f9; }

            QPushButton#primaryButton {
                background: #3b82f6;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px 20px;
                font-size: 12px;
            }
            QPushButton#primaryButton:hover { background: #2563eb; }

            QPushButton#printButton {
                background: #10b981;
                color: white;
                font-weight: bold;
                border: none;
            }
            QPushButton#printButton:hover { background: #059669; }

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
                padding: 8px 18px;
            }
            QPushButton#cancelButton:hover { background: #fee2e2; }
        """)
