# gestion_evaluation.py — Gestion moderne des évaluations
# Interface améliorée avec recherche, filtres intégrés et code couleur

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QComboBox, QLabel, QFileDialog,
    QStyledItemDelegate, QDateEdit, QAbstractItemView, QMessageBox,
    QLineEdit, QGroupBox, QWidget, QTabWidget
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from core.services.evaluation_service import (
    get_stats_polyvalence_operateur,
    get_polyvalences_actuelles_operateur, get_polyvalence_par_id,
    get_historique_polyvalence_operateur,
    mettre_a_jour_evaluation, update_date_evaluation_polyvalence,
    update_date_champ_polyvalence, get_operateurs_avec_stats_polyvalences,
    supprimer_polyvalence_par_id,
)
from core.utils.logging_config import get_logger
from core.utils.date_format import format_date, format_datetime

logger = get_logger(__name__)

# Import du thème moderne
try:
    from core.gui.components.ui_theme import EmacButton, EmacCard, EmacHeader, get_current_theme
    from core.gui.components.emac_ui_kit import add_custom_title_bar, show_error_message
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False
    show_error_message = None  # Fallback


# --- Dialogue popup avec 2 onglets pour un opérateur ---
class DetailOperateurDialog(QDialog):
    """Dialogue détaillé pour un opérateur avec résumé et ajout d'anciennes polyvalences."""

    def __init__(self, operateur_id, operateur_nom, operateur_prenom, parent=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.operateur_nom = operateur_nom
        self.operateur_prenom = operateur_prenom

        self.setWindowTitle(f"Détails - {operateur_prenom} {operateur_nom}")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        header_frame = QWidget()
        header_frame.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #a78bfa);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)

        title = QLabel(f"👤 {operateur_prenom} {operateur_nom}")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title)

        layout.addWidget(header_frame)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                background: white;
            }
            QTabBar::tab {
                background: #f3f4f6;
                color: #374151;
                padding: 10px 20px;
                border: 1px solid #e5e7eb;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #8b5cf6;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #e5e7eb;
            }
        """)

        self.tab_resume = QWidget()
        self._init_tab_resume()
        self.tabs.addTab(self.tab_resume, "📊 Résumé")

        self.tab_anciennes = QWidget()
        self._init_tab_anciennes()
        self.tabs.addTab(self.tab_anciennes, "📜 Historique")

        layout.addWidget(self.tabs, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        self._load_data()

    def _init_tab_resume(self):
        """Initialise l'onglet Résumé."""
        layout = QVBoxLayout(self.tab_resume)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        stats_group = QGroupBox("📈 Statistiques")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("Chargement...")
        self.stats_label.setStyleSheet("font-size: 11pt; padding: 10px;")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        layout.addWidget(stats_group)

        poly_group = QGroupBox("🎯 Polyvalences actuelles")
        poly_layout = QVBoxLayout(poly_group)

        self.poly_table = QTableWidget()
        self.poly_table.setColumnCount(6)
        self.poly_table.setHorizontalHeaderLabels([
            "Poste", "Niveau", "Date Éval.", "Prochaine Éval.", "Statut", "_poly_id"
        ])
        self.poly_table.setColumnHidden(5, True)  # Cacher l'ID
        self.poly_table.horizontalHeader().setStretchLastSection(True)
        self.poly_table.setEditTriggers(QAbstractItemView.DoubleClicked)  # Édition au double-clic
        self.poly_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.poly_table.setAlternatingRowColors(True)
        self.poly_table.itemChanged.connect(self._on_poly_cell_changed)
        self.poly_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                gridline-color: #e5e7eb;
            }
            QHeaderView::section {
                background: #f3f4f6;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        poly_layout.addWidget(self.poly_table)
        layout.addWidget(poly_group, 1)

    def _init_tab_anciennes(self):
        """Initialise l'onglet Historique des polyvalences."""
        layout = QVBoxLayout(self.tab_anciennes)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        anciennes_group = QGroupBox("📜 Historique des polyvalences")
        anciennes_layout = QVBoxLayout(anciennes_group)

        self.anciennes_table = QTableWidget()
        self.anciennes_table.setColumnCount(6)
        self.anciennes_table.setHorizontalHeaderLabels([
            "Date", "Poste", "Changement", "Nouveau niveau", "Commentaire", "_id"
        ])
        self.anciennes_table.setColumnHidden(5, True)
        self.anciennes_table.horizontalHeader().setStretchLastSection(True)
        self.anciennes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.anciennes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.anciennes_table.setAlternatingRowColors(True)
        self.anciennes_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                gridline-color: #e5e7eb;
            }
            QHeaderView::section {
                background: #f3f4f6;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        anciennes_layout.addWidget(self.anciennes_table)
        layout.addWidget(anciennes_group, 1)

    def _load_data(self):
        """Charge toutes les données de l'opérateur."""
        try:
            # Charger les statistiques
            stats = get_stats_polyvalence_operateur(self.operateur_id)

            if stats:
                total = stats['total'] or 0
                parts = []
                if stats['n4']: parts.append(f"N4×{stats['n4']}")
                if stats['n3']: parts.append(f"N3×{stats['n3']}")
                if stats['n2']: parts.append(f"N2×{stats['n2']}")
                if stats['n1']: parts.append(f"N1×{stats['n1']}")

                poly_text = " | ".join(parts) if parts else "Aucune"

                eval_parts = []
                if stats['retard']: eval_parts.append(f"⚠️ {stats['retard']} en retard")
                if stats['a_planifier']: eval_parts.append(f"📅 {stats['a_planifier']} à planifier")
                if not eval_parts: eval_parts.append("✅ Toutes à jour")

                eval_text = " | ".join(eval_parts)

                self.stats_label.setText(
                    f"<b>{total} polyvalence(s) actuelle(s)</b><br/>"
                    f"Niveaux : {poly_text}<br/>"
                    f"Évaluations : {eval_text}"
                )

            # Charger les polyvalences actuelles dans le tableau
            polyvalences = get_polyvalences_actuelles_operateur(self.operateur_id)

            # Bloquer temporairement les signaux pour éviter les mises à jour pendant le remplissage
            self.poly_table.blockSignals(True)
            self.poly_table.setRowCount(len(polyvalences))

            for row_idx, poly in enumerate(polyvalences):
                poste_item = QTableWidgetItem(poly['poste_code'])
                poste_item.setFlags(poste_item.flags() & ~Qt.ItemIsEditable)
                self.poly_table.setItem(row_idx, 0, poste_item)
                niveau_item = QTableWidgetItem(str(poly['niveau']))
                niveau_item.setTextAlignment(Qt.AlignCenter)
                self.poly_table.setItem(row_idx, 1, niveau_item)
                date_eval = format_date(poly['date_evaluation']) if poly['date_evaluation'] else "N/A"
                date_eval_item = QTableWidgetItem(date_eval)
                self.poly_table.setItem(row_idx, 2, date_eval_item)
                date_next = format_date(poly['prochaine_evaluation']) if poly['prochaine_evaluation'] else "N/A"
                date_next_item = QTableWidgetItem(date_next)
                date_next_item.setFlags(date_next_item.flags() & ~Qt.ItemIsEditable)
                self.poly_table.setItem(row_idx, 3, date_next_item)
                if poly['prochaine_evaluation']:
                    from datetime import date as dt_date
                    today = dt_date.today()
                    if poly['prochaine_evaluation'] < today:
                        statut = "⚠️ En retard"
                    elif (poly['prochaine_evaluation'] - today).days <= 30:
                        statut = "📅 À planifier"
                    else:
                        statut = "✅ À jour"
                else:
                    statut = "N/A"
                statut_item = QTableWidgetItem(statut)
                statut_item.setFlags(statut_item.flags() & ~Qt.ItemIsEditable)
                self.poly_table.setItem(row_idx, 4, statut_item)
                self.poly_table.setItem(row_idx, 5, QTableWidgetItem(str(poly['id'])))

            # Réactiver les signaux
            self.poly_table.blockSignals(False)

            # Charger les anciennes polyvalences
            self._load_anciennes_polyvalences()

        except Exception as e:
            logger.exception(f"Erreur chargement donnees: {e}")
            if show_error_message:
                show_error_message(self, "Erreur", "Impossible de charger les donnees", e)
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de charger les donnees. Contactez l'administrateur.")

    def _load_anciennes_polyvalences(self):
        """Charge l'historique des polyvalences dans le tableau."""
        anciennes = get_historique_polyvalence_operateur(self.operateur_id)
        self.anciennes_table.setRowCount(len(anciennes))

        action_labels = {
            'MODIFICATION': 'Modification',
            'AJOUT': 'Ajout',
            'SUPPRESSION': 'Suppression',
            'IMPORT_MANUEL': 'Import manuel',
        }

        for row_idx, anc in enumerate(anciennes):
            # Col 0 : Date de l'action
            date_action = anc['date_action']
            if date_action:
                date_str = format_datetime(date_action, default=str(date_action))
            else:
                date_str = "N/A"
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.anciennes_table.setItem(row_idx, 0, date_item)

            # Col 1 : Poste
            self.anciennes_table.setItem(row_idx, 1, QTableWidgetItem(anc['poste_code'] or "N/A"))

            # Col 2 : Changement (ex: "Modification", "N2 → N3")
            action_type = anc.get('action_type', '')
            label = action_labels.get(action_type, action_type)
            ancien = anc.get('ancien_niveau')
            nouveau = anc.get('nouveau_niveau')
            if ancien is not None and nouveau is not None and ancien != nouveau:
                label = f"N{ancien} → N{nouveau}"
            changement_item = QTableWidgetItem(label)
            changement_item.setTextAlignment(Qt.AlignCenter)
            self.anciennes_table.setItem(row_idx, 2, changement_item)

            # Col 3 : Nouveau niveau
            niveau_txt = f"N{nouveau}" if nouveau is not None else "N/A"
            niveau_item = QTableWidgetItem(niveau_txt)
            niveau_item.setTextAlignment(Qt.AlignCenter)
            self.anciennes_table.setItem(row_idx, 3, niveau_item)

            # Col 4 : Commentaire
            self.anciennes_table.setItem(
                row_idx, 4,
                QTableWidgetItem(anc['commentaire'] or "—")
            )

            # Col 5 : ID (caché)
            self.anciennes_table.setItem(
                row_idx, 5,
                QTableWidgetItem(str(anc['id']))
            )

    def _on_poly_cell_changed(self, item):
        """Gère les modifications de cellules dans le tableau des polyvalences."""
        if item is None:
            return

        row = item.row()
        col = item.column()

        # Colonnes éditables : 1 (Niveau) et 2 (Date Éval.) uniquement
        # La colonne 3 (Prochaine Éval.) est calculée automatiquement et non éditable
        if col not in [1, 2]:
            return

        # Récupérer l'ID de la polyvalence
        poly_id_item = self.poly_table.item(row, 5)
        if not poly_id_item:
            return

        poly_id = int(poly_id_item.text())
        new_value = item.text().strip()

        # === GESTION DU NIVEAU (colonne 1) ===
        if col == 1:
            # Cellule vidée → suppression de la polyvalence (comme la grille)
            if new_value == "":
                poste_item = self.poly_table.item(row, 0)
                poste_code = poste_item.text() if poste_item else "?"
                reply = QMessageBox.question(
                    self, "Supprimer la polyvalence",
                    f"Voulez-vous supprimer la polyvalence pour le poste {poste_code} ?\n"
                    "Cette action est irréversible.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    self._load_data()
                    return
                if supprimer_polyvalence_par_id(poly_id):
                    self._load_data()
                    QMessageBox.information(self, "Supprimé",
                        f"Polyvalence pour le poste {poste_code} supprimée.")
                else:
                    QMessageBox.critical(self, "Erreur", "Impossible de supprimer la polyvalence.")
                    self._load_data()
                return

            # Valider que c'est un niveau valide (1-4)
            try:
                new_niveau = int(new_value)
                if new_niveau not in [1, 2, 3, 4]:
                    raise ValueError()
            except ValueError:
                QMessageBox.warning(self, "Valeur invalide", "Le niveau doit être 1, 2, 3 ou 4")
                self._load_data()
                return

            # Récupérer la date d'évaluation actuelle
            date_eval_item = self.poly_table.item(row, 2)
            if not date_eval_item or date_eval_item.text() == "N/A":
                # Pas de date d'évaluation, utiliser aujourd'hui
                from datetime import date, timedelta
                date_eval = date.today()
            else:
                from datetime import datetime
                try:
                    date_eval = datetime.strptime(date_eval_item.text(), "%d/%m/%Y").date()
                except ValueError:
                    date_eval = date.today()

            # Calculer automatiquement la prochaine évaluation selon le niveau
            from datetime import timedelta
            if new_niveau == 1:
                jours = 30  # 1 mois
            elif new_niveau == 2:
                jours = 30  # 1 mois
            elif new_niveau in [3, 4]:
                jours = 3650  # 10 ans
            else:
                jours = 30

            prochaine_eval = date_eval + timedelta(days=jours)

            # Récupérer ancien_niveau pour EventBus AVANT la mise à jour
            poly_info = get_polyvalence_par_id(poly_id)
            ancien_niveau = poly_info['niveau'] if poly_info else None
            operateur_id = poly_info['operateur_id'] if poly_info else None
            poste_id_for_event = poly_info['poste_id'] if poly_info else None

            # Mise à jour via service
            try:
                if not mettre_a_jour_evaluation(poly_id, new_niveau, date_eval, prochaine_eval):
                    raise RuntimeError("Échec de la mise à jour")

                self._load_data()

                QMessageBox.information(self, "Succès",
                    f"Niveau mis à jour.\nProchaine évaluation automatiquement calculée : {format_date(prochaine_eval)}")

                # Émettre l'événement pour le système de déclenchement de documents
                if ancien_niveau != new_niveau:
                    try:
                        from core.services.event_bus import EventBus
                        from core.repositories.poste_repo import PosteRepository
                        poste = PosteRepository.get_by_id(poste_id_for_event) if poste_id_for_event else None

                        event_data = {
                            'polyvalence_id': poly_id,
                            'operateur_id': operateur_id,
                            'nom': self.operateur_nom,
                            'prenom': self.operateur_prenom,
                            'poste_id': poste_id_for_event,
                            'code_poste': poste.poste_code if poste and hasattr(poste, 'poste_code') else str(poste_id_for_event),
                            'old_niveau': ancien_niveau,
                            'new_niveau': new_niveau
                        }

                        EventBus.emit('polyvalence.niveau_changed', event_data,
                                     source='GestionEvaluationDialog.on_cell_changed')

                        if new_niveau == 1:
                            from core.services.evaluation_service import has_operateur_deja_eu_niveau_1
                            is_premier = not has_operateur_deja_eu_niveau_1(
                                operateur_id,
                                old_niveau=ancien_niveau,
                                exclude_polyvalence_id=poly_id,
                            )
                            EventBus.emit('polyvalence.niveau_1_reached', {
                                **event_data,
                                'niveau': 1,
                                'is_premier_niveau_1': is_premier,
                            }, source='GestionEvaluationDialog.on_cell_changed')

                        if new_niveau == 2 and (ancien_niveau is None or ancien_niveau < 2):
                            EventBus.emit('polyvalence.niveau_2_reached', {
                                **event_data,
                                'niveau': 2
                            }, source='GestionEvaluationDialog.on_cell_changed')

                        if new_niveau == 3 and (ancien_niveau is None or ancien_niveau < 3):
                            EventBus.emit('polyvalence.niveau_3_reached', {
                                **event_data,
                                'niveau': 3
                            }, source='GestionEvaluationDialog.on_cell_changed')
                    except Exception as evt_err:
                        logger.warning(f"Erreur émission événement polyvalence: {evt_err}")

            except Exception as e:
                logger.exception(f"Erreur mise à jour niveau: {e}")
                if show_error_message:
                    show_error_message(self, "Erreur", "Impossible de mettre à jour le niveau", e)
                else:
                    QMessageBox.critical(self, "Erreur", "Impossible de mettre à jour le niveau. Contactez l'administrateur.")
                self._load_data()

            return

        # Valider le format de date
        from datetime import datetime
        try:
            new_date = datetime.strptime(new_value, "%d/%m/%Y").date()
        except ValueError:
            QMessageBox.warning(self, "Format invalide", "Le format de date doit être JJ/MM/AAAA")
            # Recharger les données pour annuler la modification
            self._load_data()
            return

        # === GESTION DE LA DATE D'ÉVALUATION (colonne 2) ===
        if col == 2:
            # Si on modifie la date d'évaluation, recalculer automatiquement la prochaine évaluation
            # Récupérer le niveau actuel
            niveau_item = self.poly_table.item(row, 1)
            if niveau_item:
                try:
                    niveau = int(niveau_item.text())

                    # Calculer automatiquement la prochaine évaluation selon le niveau
                    from datetime import timedelta
                    if niveau == 1:
                        jours = 30  # 1 mois
                    elif niveau == 2:
                        jours = 30  # 1 mois
                    elif niveau in [3, 4]:
                        jours = 3650  # 10 ans
                    else:
                        jours = 30

                    prochaine_eval = new_date + timedelta(days=jours)

                    # Mettre à jour les DEUX dates via service
                    try:
                        if not update_date_evaluation_polyvalence(poly_id, new_date, prochaine_eval):
                            raise RuntimeError("Échec de la mise à jour")

                        self._load_data()
                        QMessageBox.information(self, "Succès",
                            f"Date d'évaluation mise à jour.\nProchaine évaluation automatiquement recalculée : {format_date(prochaine_eval)}")

                        # Émettre l'événement evaluation.completed
                        try:
                            from core.services.event_bus import EventBus
                            poly_info = get_polyvalence_par_id(poly_id)
                            EventBus.emit('evaluation.completed', {
                                'polyvalence_id': poly_id,
                                'operateur_id': self.operateur_id,
                                'nom': self.operateur_nom,
                                'prenom': self.operateur_prenom,
                                'poste_id': poly_info['poste_id'] if poly_info else None,
                                'niveau': niveau,
                                'date_evaluation': new_date.isoformat(),
                            }, source='DetailOperateurDialog.on_cell_changed')
                        except Exception as evt_err:
                            logger.warning(f"Erreur émission evaluation.completed: {evt_err}")

                        return

                    except Exception as e:
                        logger.exception(f"Erreur mise à jour date: {e}")
                        if show_error_message:
                            show_error_message(self, "Erreur", "Impossible de mettre à jour la date", e)
                        else:
                            QMessageBox.critical(self, "Erreur", "Impossible de mettre à jour la date. Contactez l'administrateur.")
                        self._load_data()
                        return

                except (ValueError, AttributeError):
                    pass  # Niveau invalide, continuer avec mise à jour simple

            # Si on arrive ici, c'est qu'il n'y avait pas de niveau valide
            # Faire une simple mise à jour de la date d'évaluation sans recalcul
            try:
                if not update_date_champ_polyvalence(poly_id, 'date_evaluation', new_date):
                    raise RuntimeError("Échec de la mise à jour")

                self._load_data()
                QMessageBox.information(self, "Succès", "Date d'évaluation mise à jour.")

            except Exception as e:
                logger.exception(f"Erreur mise à jour date: {e}")
                if show_error_message:
                    show_error_message(self, "Erreur", "Impossible de mettre à jour la date", e)
                else:
                    QMessageBox.critical(self, "Erreur", "Impossible de mettre à jour la date. Contactez l'administrateur.")
                self._load_data()


# --- Délégué pour empêcher l'édition ---
class NoEditDelegate(QStyledItemDelegate):
    """Empêche l'édition des cellules."""

    def createEditor(self, _parent, _option, _index):
        # Retourner None empêche la création d'un éditeur
        return None


# --- Délégué pour éditer les dates dans le tableau ---
class DateDelegate(QStyledItemDelegate):
    """Affiche un QDateEdit pour les cellules de dates."""

    def __init__(self, parent, on_commit):
        super().__init__(parent)
        self.on_commit = on_commit

    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd/MM/yyyy")
        return editor

    def setEditorData(self, editor, index):
        txt = index.model().data(index, Qt.EditRole) or index.model().data(index, Qt.DisplayRole)
        qd = QDate.fromString(str(txt), "dd/MM/yyyy")
        if not qd.isValid():
            qd = QDate.fromString(str(txt), "yyyy-MM-dd")
        if not qd.isValid():
            qd = QDate.currentDate()
        editor.setDate(qd)

    def setModelData(self, editor, model, index):
        qd = editor.date()
        model.setData(index, qd.toString("dd/MM/yyyy"), Qt.EditRole)
        if self.on_commit:
            self.on_commit(index.row(), index.column(), qd)


class GestionEvaluationDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestion des Évaluations")
        self.setGeometry(100, 80, 1400, 800)

        # Données
        self.all_evaluations = []
        self._filtered_evaluations = []

        # Layout principal avec marges nulles
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Gestion des Évaluations")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # === En-tête moderne ===
        if THEME_AVAILABLE:
            header = EmacHeader("Gestion des Évaluations", "Consultez et gérez les évaluations de polyvalence du personnel")
            layout.addWidget(header)
        else:
            header = QLabel("Gestion des Évaluations")
            header.setFont(QFont("Arial", 16, QFont.Bold))
            header.setAlignment(Qt.AlignCenter)
            layout.addWidget(header)

            subtitle = QLabel("Consultez et gérez les évaluations de polyvalence du personnel")
            subtitle.setStyleSheet("color: #6b7280; font-size: 12px;")
            subtitle.setAlignment(Qt.AlignCenter)
            layout.addWidget(subtitle)

        # === Section Recherche et Filtres (Compacte) ===
        if THEME_AVAILABLE:
            filter_layout = QHBoxLayout()
            filter_layout.setSpacing(10)
            filter_layout.setContentsMargins(0, 0, 0, 0)

            # Icône de recherche
            filter_icon = QLabel("🔍")
            filter_layout.addWidget(filter_icon)

            # Recherche
            search_label = QLabel("Rechercher :")
            filter_layout.addWidget(search_label)
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Nom, prénom ou matricule...")
            self.search_input.setMaximumWidth(200)
            self.search_input.textChanged.connect(self.apply_filters)
            filter_layout.addWidget(self.search_input)

            # Séparateur
            separator1 = QLabel("·")
            separator1.setStyleSheet("color: #d1d5db; font-size: 16px; padding: 0 8px;")
            filter_layout.addWidget(separator1)

            # Statut
            statut_label = QLabel("Statut :")
            filter_layout.addWidget(statut_label)
            self.status_filter = QComboBox()
            self.status_filter.addItems(["Tous", "En retard", "À planifier (30j)", "À jour"])
            self.status_filter.setMinimumWidth(120)
            self.status_filter.setMaximumWidth(160)
            self.status_filter.currentIndexChanged.connect(self.apply_filters)
            filter_layout.addWidget(self.status_filter)

            filter_layout.addStretch()
            layout.addLayout(filter_layout)
        else:
            # Version sans thème (ancien style)
            filter_group = QGroupBox("Recherche et Filtres")
            filter_group_layout = QVBoxLayout()

            # Ligne 1: Recherche
            search_row = QHBoxLayout()
            search_row.addWidget(QLabel("Rechercher :"))
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Nom, prénom ou matricule...")
            self.search_input.textChanged.connect(self.apply_filters)
            search_row.addWidget(self.search_input)
            filter_group_layout.addLayout(search_row)

            # Ligne 2: Filtres
            combo_row = QHBoxLayout()

            combo_row.addWidget(QLabel("Statut :"))
            self.status_filter = QComboBox()
            self.status_filter.addItems(["Tous", "En retard", "À planifier (30j)", "À jour"])
            self.status_filter.currentIndexChanged.connect(self.apply_filters)
            combo_row.addWidget(self.status_filter)

            filter_group_layout.addLayout(combo_row)
            filter_group.setLayout(filter_group_layout)
            layout.addWidget(filter_group)


        # === Statistiques dans une carte ===
        if THEME_AVAILABLE:
            stats_card = EmacCard()
            stats_label = QLabel("Statistiques")
            stats_label.setProperty('class', 'h2')
            stats_card.body.addWidget(stats_label)

            stats_layout = QHBoxLayout()

            self.total_label = QLabel("Total : 0")
            self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            stats_layout.addWidget(self.total_label)

            self.retard_label = QLabel("En retard : 0")
            self.retard_label.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 14px;")
            stats_layout.addWidget(self.retard_label)

            self.a_planifier_label = QLabel("À planifier : 0")
            self.a_planifier_label.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 14px;")
            stats_layout.addWidget(self.a_planifier_label)

            self.a_jour_label = QLabel("À jour : 0")
            self.a_jour_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
            stats_layout.addWidget(self.a_jour_label)

            stats_layout.addStretch()
            stats_card.body.addLayout(stats_layout)
            layout.addWidget(stats_card)
        else:
            stats_group = QGroupBox("Statistiques")
            stats_layout = QHBoxLayout()

            self.total_label = QLabel("Total : 0")
            self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            stats_layout.addWidget(self.total_label)

            self.retard_label = QLabel("En retard : 0")
            self.retard_label.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 14px;")
            stats_layout.addWidget(self.retard_label)

            self.a_planifier_label = QLabel("À planifier : 0")
            self.a_planifier_label.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 14px;")
            stats_layout.addWidget(self.a_planifier_label)

            self.a_jour_label = QLabel("À jour : 0")
            self.a_jour_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
            stats_layout.addWidget(self.a_jour_label)

            stats_layout.addStretch()
            stats_group.setLayout(stats_layout)
            layout.addWidget(stats_group)

        # === Tableau dans une carte ===
        if THEME_AVAILABLE:
            table_card = EmacCard()
            table_layout = QVBoxLayout()
            table_layout.setContentsMargins(0, 0, 0, 0)

            self.table = QTableWidget()
            self.table.setColumnCount(7)
            self.table.setHorizontalHeaderLabels([
                "_pers_id", "Nom", "Prénom", "Matricule", "Polyvalences", "Évaluations", "Statut"
            ])
            self.table.setColumnHidden(0, True)  # ID technique caché
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setAlternatingRowColors(True)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setSortingEnabled(True)
            self._style_table()

            # Connexion pour le double-clic sur une ligne d'opérateur
            self.table.cellDoubleClicked.connect(self._on_row_double_click)

            table_layout.addWidget(self.table)
            table_card.body.addLayout(table_layout)
            layout.addWidget(table_card, 1)
        else:
            self.table = QTableWidget()
            self.table.setColumnCount(7)
            self.table.setHorizontalHeaderLabels([
                "_pers_id", "Nom", "Prénom", "Matricule", "Polyvalences", "Évaluations", "Statut"
            ])
            self.table.setColumnHidden(0, True)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setAlternatingRowColors(True)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setSortingEnabled(True)

            # Connexion pour le double-clic sur une ligne d'opérateur
            self.table.cellDoubleClicked.connect(self._on_row_double_click)

            layout.addWidget(self.table, 1)

        # === Boutons d'action modernisés ===
        btn_layout = QHBoxLayout()

        if THEME_AVAILABLE:
            self.refresh_btn = EmacButton("🔄 Actualiser", variant='primary')
            self.refresh_btn.clicked.connect(self.load_data)
            btn_layout.addWidget(self.refresh_btn)

            self.export_btn = EmacButton("📄 Exporter PDF", variant='ghost')
            self.export_btn.clicked.connect(self.export_to_pdf)
            btn_layout.addWidget(self.export_btn)

            self.print_btn = EmacButton("🖨️ Imprimer les documents", variant='ghost')
            self.print_btn.setToolTip("Ouvrir la fenêtre de sélection des documents à imprimer")
            self.print_btn.clicked.connect(self._imprimer_documents_operateur)
            btn_layout.addWidget(self.print_btn)

            btn_layout.addStretch()

            self.close_btn = EmacButton("Fermer", variant='ghost')
            self.close_btn.clicked.connect(self.accept)
            btn_layout.addWidget(self.close_btn)
        else:
            self.refresh_btn = QPushButton("🔄 Actualiser")
            self.refresh_btn.setStyleSheet("""
                QPushButton {
                    background: #10b981;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #059669;
                }
            """)
            self.refresh_btn.clicked.connect(self.load_data)
            btn_layout.addWidget(self.refresh_btn)

            self.export_btn = QPushButton("📄 Exporter PDF")
            self.export_btn.setStyleSheet("""
                QPushButton {
                    background: #6b7280;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #4b5563;
                }
            """)
            self.export_btn.clicked.connect(self.export_to_pdf)
            btn_layout.addWidget(self.export_btn)

            self.print_btn = QPushButton("🖨️ Imprimer les documents")
            self.print_btn.setToolTip("Ouvrir la fenêtre de sélection des documents à imprimer")
            self.print_btn.setStyleSheet("""
                QPushButton {
                    background: #7c3aed;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #6d28d9;
                }
                QPushButton:disabled {
                    background: #d1d5db;
                    color: #9ca3af;
                }
            """)
            self.print_btn.clicked.connect(self._imprimer_documents_operateur)
            btn_layout.addWidget(self.print_btn)

            btn_layout.addStretch()

            self.close_btn = QPushButton("Fermer")
            self.close_btn.clicked.connect(self.accept)
            btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        # Ajouter le widget de contenu au layout principal
        main_layout.addWidget(content_widget)

        # Charger les données
        self.load_data()

    def _style_table(self):
        """Applique un style moderne à la table."""
        if not THEME_AVAILABLE:
            return

        ThemeCls = get_current_theme()

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {ThemeCls.BG_TABLE};
                border: 1px solid {ThemeCls.BDR};
                border-radius: 10px;
                gridline-color: {ThemeCls.BDR};
            }}
            QTableWidget::item {{
                padding: 6px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background: {ThemeCls.PRI};
                color: white;
            }}
            QHeaderView::section {{
                background: {ThemeCls.BG_ELEV};
                color: {ThemeCls.TXT};
                padding: 8px;
                border: 1px solid {ThemeCls.BDR};
                font-weight: 600;
                font-size: 13px;
            }}
            QHeaderView::section:hover {{
                background: {ThemeCls.BDR};
            }}
        """)

        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.verticalHeader().setDefaultSectionSize(32)


    def load_data(self):
        """Charge la liste des opérateurs avec leur résumé de polyvalences."""
        try:
            rows = get_operateurs_avec_stats_polyvalences()

            # Stocker toutes les données
            self.all_evaluations = []

            for row in rows:
                # ATTENTION: L'ordre dans le SELECT est: ..., a_planifier, retard
                pers_id, nom, prenom, matricule, total, n4, n3, n2, n1, a_planifier, retard = row

                # Déterminer le statut global
                if retard and retard > 0:
                    statut = f"⚠️ {retard} en retard"
                    statut_code = "En retard"
                elif a_planifier and a_planifier > 0:
                    statut = f"📅 {a_planifier} à planifier"
                    statut_code = "À planifier"
                else:
                    statut = "✅ À jour"
                    statut_code = "À jour"

                self.all_evaluations.append({
                    'personnel_id': pers_id,
                    'nom': nom,
                    'prenom': prenom,
                    'matricule': matricule or "N/A",
                    'total': total or 0,
                    'n4': n4 or 0,
                    'n3': n3 or 0,
                    'n2': n2 or 0,
                    'n1': n1 or 0,
                    'retard': retard or 0,
                    'a_planifier': a_planifier or 0,
                    'statut': statut,
                    'statut_code': statut_code
                })

            # Appliquer les filtres
            self.apply_filters()

        except Exception as e:
            logger.exception(f"Erreur chargement evaluations: {e}")
            if show_error_message:
                show_error_message(self, "Erreur", "Impossible de charger les évaluations", e)
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de charger les évaluations. Contactez l'administrateur.")

    def apply_filters(self):
        """Applique les filtres de recherche et affiche les résultats."""
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()

        # Filtrer les données
        filtered = []
        for oper_data in self.all_evaluations:
            # Filtre recherche (nom, prénom ou matricule)
            if search_text:
                searchable = f"{oper_data['nom']} {oper_data['prenom']} {oper_data['matricule']}".lower()
                if search_text not in searchable:
                    continue

            # Filtre statut
            if status_filter != "Tous":
                if status_filter == "À planifier (30j)" and oper_data['statut_code'] != "À planifier":
                    continue
                elif status_filter != "À planifier (30j)" and oper_data['statut_code'] != status_filter:
                    continue

            filtered.append(oper_data)

        # Mémoriser pour le bouton impression
        self._filtered_evaluations = filtered

        # Afficher dans le tableau
        self.display_operateurs(filtered)

        # Mettre à jour les statistiques
        self.update_statistics(filtered)

    def display_operateurs(self, operateurs):
        """Affiche la liste des opérateurs dans le tableau."""
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)

        for oper_data in operateurs:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            # Colonne 0: ID (caché)
            self.table.setItem(row_pos, 0, QTableWidgetItem(str(oper_data['personnel_id'])))

            # Colonne 1-3: Nom, Prénom, Matricule
            self.table.setItem(row_pos, 1, QTableWidgetItem(oper_data['nom']))
            self.table.setItem(row_pos, 2, QTableWidgetItem(oper_data['prenom']))
            self.table.setItem(row_pos, 3, QTableWidgetItem(oper_data['matricule']))

            # Colonne 4: Polyvalences (résumé compact)
            poly_parts = []
            if oper_data['n4']: poly_parts.append(f"N4×{oper_data['n4']}")
            if oper_data['n3']: poly_parts.append(f"N3×{oper_data['n3']}")
            if oper_data['n2']: poly_parts.append(f"N2×{oper_data['n2']}")
            if oper_data['n1']: poly_parts.append(f"N1×{oper_data['n1']}")

            poly_text = " | ".join(poly_parts) if poly_parts else "Aucune"
            poly_item = QTableWidgetItem(f"{oper_data['total']} : {poly_text}")
            self.table.setItem(row_pos, 4, poly_item)

            # Colonne 5: Évaluations en retard/à planifier
            eval_parts = []
            if oper_data['retard']: eval_parts.append(f"⚠️ {oper_data['retard']} en retard")
            if oper_data['a_planifier']: eval_parts.append(f"📅 {oper_data['a_planifier']} à planifier")

            eval_text = " | ".join(eval_parts) if eval_parts else "—"
            self.table.setItem(row_pos, 5, QTableWidgetItem(eval_text))

            # Colonne 6: Statut global
            statut_item = QTableWidgetItem(oper_data['statut'])
            statut_item.setTextAlignment(Qt.AlignCenter)

            if oper_data['statut_code'] == "En retard":
                statut_item.setBackground(QColor("#fecaca"))
                statut_item.setForeground(QColor("#dc2626"))
            elif oper_data['statut_code'] == "À planifier":
                statut_item.setBackground(QColor("#fed7aa"))
                statut_item.setForeground(QColor("#ea580c"))
            else:
                statut_item.setBackground(QColor("#d1fae5"))
                statut_item.setForeground(QColor("#059669"))

            font = QFont()
            font.setBold(True)
            statut_item.setFont(font)
            self.table.setItem(row_pos, 6, statut_item)

        self.table.setSortingEnabled(True)

    def update_statistics(self, operateurs):
        """Met à jour les statistiques affichées."""
        total = len(operateurs)
        en_retard = sum(1 for o in operateurs if o['statut_code'] == "En retard")
        a_planifier = sum(1 for o in operateurs if o['statut_code'] == "À planifier")
        a_jour = sum(1 for o in operateurs if o['statut_code'] == "À jour")

        self.total_label.setText(f"Total : {total}")
        self.retard_label.setText(f"En retard : {en_retard}")
        self.a_planifier_label.setText(f"À planifier : {a_planifier}")
        self.a_jour_label.setText(f"À jour : {a_jour}")

    def _imprimer_documents_operateur(self):
        """
        Ouvre la fenêtre de sélection multi-opérateurs pour l'impression
        des documents d'évaluation à la demande.

        Passe la liste des opérateurs actuellement filtrés dans le tableau.
        """
        operateurs = self._filtered_evaluations or self.all_evaluations

        if not operateurs:
            QMessageBox.information(
                self,
                "Liste vide",
                "Aucun opérateur dans la liste courante.\n"
                "Actualisez ou modifiez les filtres."
            )
            return

        try:
            from core.gui.dialogs.imprimer_documents_dialog import ImprimerDocumentsDialog
            dialog = ImprimerDocumentsDialog(operateurs=operateurs, parent=self)
            dialog.exec_()
        except Exception as e:
            logger.exception(f"Erreur ouverture dialog impression: {e}")
            if show_error_message:
                show_error_message(self, "Erreur", "Impossible d'ouvrir la fenêtre d'impression", e)
            else:
                QMessageBox.critical(self, "Erreur",
                                     "Impossible d'ouvrir la fenêtre d'impression. Contactez l'administrateur.")

    def update_date_in_db(self, row, col, qdate):
        """Met à jour une date dans la base de données."""
        poly_id_item = self.table.item(row, 0)
        if not poly_id_item:
            return

        try:
            poly_id = int(poly_id_item.text())
        except ValueError:
            return

        # Whitelist des champs autorisés
        ALLOWED_FIELDS = {
            5: "date_evaluation",
            6: "prochaine_evaluation",
        }

        if col not in ALLOWED_FIELDS:
            return

        field = ALLOWED_FIELDS[col]
        new_date = qdate.toPyDate()

        try:
            if not update_date_champ_polyvalence(poly_id, field, new_date):
                raise RuntimeError("Échec de la mise à jour")

            QMessageBox.information(self, "Succès", "Date mise à jour avec succès.")
            self.load_data()

        except Exception as e:
            logger.exception(f"Erreur mise à jour date: {e}")
            if show_error_message:
                show_error_message(self, "Erreur", "Impossible de mettre à jour la date", e)
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de mettre à jour la date. Contactez l'administrateur.")

    def export_to_pdf(self):
        """Exporte les données affichées en PDF."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter en PDF", "evaluations.pdf", "PDF Files (*.pdf)", options=options
        )
        if not file_path:
            return

        try:
            pdf = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []

            styles = getSampleStyleSheet()
            title_style = styles["Title"]
            normal_style = styles["Normal"]

            # Titre
            elements.append(Paragraph("Rapport des Évaluations", title_style))
            elements.append(Paragraph(" ", normal_style))

            # Données du tableau (colonnes 1-7, sans la colonne cachée 0)
            table_data = []
            headers = ["Nom", "Prénom", "Poste", "Niveau", "Date Éval.", "Prochaine Éval.", "Statut"]
            table_data.append(headers)

            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(1, 8):  # Colonnes 1 à 7
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                table_data.append(row_data)

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            elements.append(table)
            pdf.build(elements)

            QMessageBox.information(self, "Export réussi", f"Le fichier PDF a été créé :\n{file_path}")

        except Exception as e:
            logger.exception(f"Erreur export PDF: {e}")
            if show_error_message:
                show_error_message(self, "Erreur", "Impossible d'exporter en PDF", e)
            else:
                QMessageBox.critical(self, "Erreur", "Impossible d'exporter en PDF. Contactez l'administrateur.")

    def _on_row_double_click(self, row, col):
        """Gère le double-clic sur une ligne du tableau."""
        # Ne pas ouvrir le dialogue si on double-clique sur les colonnes de dates (5-6)
        if col in [5, 6]:
            return

        # Récupérer l'ID depuis la colonne cachée (colonne 0)
        id_item = self.table.item(row, 0)
        if not id_item:
            return

        operateur_id = int(id_item.text())

        # Récupérer nom et prénom depuis les colonnes visibles
        nom_item = self.table.item(row, 1)
        prenom_item = self.table.item(row, 2)

        nom = nom_item.text() if nom_item else ""
        prenom = prenom_item.text() if prenom_item else ""

        # Ouvrir le dialogue détaillé avec 2 onglets
        dialog = DetailOperateurDialog(operateur_id, nom, prenom, self)
        dialog.exec_()

        # Les documents en attente sont gérés par le mécanisme debounce
        # de MainWindow (_on_event_for_documents) via l'EventBus.
        # Ne pas appeler show_pending_documents_if_any ici pour éviter
        # une double apparition du dialog.

        # Recharger les données après fermeture du dialogue
        self.load_data()

