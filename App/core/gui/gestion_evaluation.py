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
from datetime import date, timedelta
from core.db.configbd import get_connection as get_db_connection

# Import du thème moderne
try:
    from core.gui.ui_theme import EmacButton, EmacCard, EmacHeader, get_current_theme
    from core.gui.emac_ui_kit import add_custom_title_bar
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False


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

        # En-tête avec nom de l'opérateur
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

        # Tabs
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

        # Onglet 1 : Résumé
        self.tab_resume = QWidget()
        self._init_tab_resume()
        self.tabs.addTab(self.tab_resume, "📊 Résumé")

        # Onglet 2 : Ajouter anciennes polyvalences
        self.tab_anciennes = QWidget()
        self._init_tab_anciennes()
        self.tabs.addTab(self.tab_anciennes, "➕ Ajouter anciennes polyvalences")

        layout.addWidget(self.tabs, 1)

        # Bouton Fermer
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

        # Charger les données
        self._load_data()

    def _init_tab_resume(self):
        """Initialise l'onglet Résumé."""
        layout = QVBoxLayout(self.tab_resume)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Statistiques générales
        stats_group = QGroupBox("📈 Statistiques")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("Chargement...")
        self.stats_label.setStyleSheet("font-size: 11pt; padding: 10px;")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        layout.addWidget(stats_group)

        # Tableau des polyvalences actuelles
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
        """Initialise l'onglet Ajouter anciennes polyvalences."""
        layout = QVBoxLayout(self.tab_anciennes)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Formulaire
        form_group = QGroupBox("Nouvelle ancienne polyvalence")
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(10)

        # Ligne 1 : Poste + Niveau
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Poste :"))
        self.poste_combo = QComboBox()
        self.poste_combo.setMinimumWidth(150)
        row1.addWidget(self.poste_combo, 1)

        row1.addWidget(QLabel("Niveau :"))
        self.niveau_combo = QComboBox()
        self.niveau_combo.addItem("Niveau 1 - Débutant (réévaluation dans 1 mois)", 1)
        self.niveau_combo.addItem("Niveau 2 - Intermédiaire (réévaluation dans 1 mois)", 2)
        self.niveau_combo.addItem("Niveau 3 - Confirmé (réévaluation dans 10 ans)", 3)
        self.niveau_combo.addItem("Niveau 4 - Expert/Formateur (réévaluation dans 10 ans)", 4)
        self.niveau_combo.setCurrentIndex(0)  # Par défaut : niveau 1
        self.niveau_combo.setMinimumWidth(200)
        self.niveau_combo.currentIndexChanged.connect(self._calculer_prochaine_eval_ancienne)
        row1.addWidget(self.niveau_combo)

        form_layout.addLayout(row1)

        # Ligne 2 : Date évaluation
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Date d'évaluation :"))
        self.date_eval = QDateEdit()
        self.date_eval.setCalendarPopup(True)
        self.date_eval.setDisplayFormat("dd/MM/yyyy")
        self.date_eval.setDate(QDate.currentDate().addYears(-1))
        self.date_eval.dateChanged.connect(self._calculer_prochaine_eval_ancienne)
        row2.addWidget(self.date_eval, 1)
        form_layout.addLayout(row2)

        # Ligne 2b : Prochaine évaluation (calculée automatiquement)
        row2b = QHBoxLayout()
        row2b.addWidget(QLabel("Prochaine évaluation :"))
        self.date_prochaine_eval = QDateEdit()
        self.date_prochaine_eval.setCalendarPopup(True)
        self.date_prochaine_eval.setDisplayFormat("dd/MM/yyyy")
        self.date_prochaine_eval.setDate(QDate.currentDate())
        row2b.addWidget(self.date_prochaine_eval, 1)
        form_layout.addLayout(row2b)

        # Calcul initial de la prochaine évaluation
        self._calculer_prochaine_eval_ancienne()

        # Ligne 3 : Commentaire
        row3 = QVBoxLayout()
        row3.addWidget(QLabel("Commentaire (optionnel) :"))
        self.commentaire = QLineEdit()
        self.commentaire.setPlaceholderText("Ex: Ancienne certification, formation passée...")
        row3.addWidget(self.commentaire)
        form_layout.addLayout(row3)

        # Bouton Ajouter
        add_btn = QPushButton("✓ Ajouter cette polyvalence")
        add_btn.clicked.connect(self._add_ancienne_poly)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        form_layout.addWidget(add_btn)

        layout.addWidget(form_group)

        # Tableau des anciennes polyvalences déjà ajoutées
        anciennes_group = QGroupBox("📜 Anciennes polyvalences déjà enregistrées")
        anciennes_layout = QVBoxLayout(anciennes_group)

        self.anciennes_table = QTableWidget()
        self.anciennes_table.setColumnCount(5)
        self.anciennes_table.setHorizontalHeaderLabels([
            "Poste", "Niveau", "Date Éval.", "Commentaire", "_id"
        ])
        self.anciennes_table.setColumnHidden(4, True)
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
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Charger tous les postes pour le combo
            cursor.execute("SELECT id, poste_code FROM postes ORDER BY poste_code")
            postes = cursor.fetchall()
            for poste in postes:
                self.poste_combo.addItem(poste['poste_code'], poste['id'])

            # Charger les statistiques
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN niveau = 4 THEN 1 ELSE 0 END) as n4,
                       SUM(CASE WHEN niveau = 3 THEN 1 ELSE 0 END) as n3,
                       SUM(CASE WHEN niveau = 2 THEN 1 ELSE 0 END) as n2,
                       SUM(CASE WHEN niveau = 1 THEN 1 ELSE 0 END) as n1,
                       SUM(CASE WHEN prochaine_evaluation < CURDATE() THEN 1 ELSE 0 END) as retard,
                       SUM(CASE WHEN prochaine_evaluation BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) as a_planifier
                FROM polyvalence
                WHERE operateur_id = %s
            """, (self.operateur_id,))
            stats = cursor.fetchone()

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
            cursor.execute("""
                SELECT poly.id,
                       ps.poste_code,
                       poly.niveau,
                       poly.date_evaluation,
                       poly.prochaine_evaluation
                FROM polyvalence poly
                JOIN postes ps ON poly.poste_id = ps.id
                WHERE poly.operateur_id = %s
                  AND poly.id = (
                      SELECT MAX(p2.id)
                      FROM polyvalence p2
                      WHERE p2.operateur_id = poly.operateur_id
                        AND p2.poste_id = poly.poste_id
                  )
                ORDER BY ps.poste_code
            """, (self.operateur_id,))

            polyvalences = cursor.fetchall()

            # Bloquer temporairement les signaux pour éviter les mises à jour pendant le remplissage
            self.poly_table.blockSignals(True)
            self.poly_table.setRowCount(len(polyvalences))

            for row_idx, poly in enumerate(polyvalences):
                # Colonne 0 : Poste (non éditable)
                poste_item = QTableWidgetItem(poly['poste_code'])
                poste_item.setFlags(poste_item.flags() & ~Qt.ItemIsEditable)
                self.poly_table.setItem(row_idx, 0, poste_item)

                # Colonne 1 : Niveau (éditable - seulement les chiffres 1-4)
                niveau_item = QTableWidgetItem(str(poly['niveau']))
                niveau_item.setTextAlignment(Qt.AlignCenter)
                self.poly_table.setItem(row_idx, 1, niveau_item)

                # Colonne 2 : Date évaluation (éditable)
                date_eval = poly['date_evaluation'].strftime('%d/%m/%Y') if poly['date_evaluation'] else "N/A"
                date_eval_item = QTableWidgetItem(date_eval)
                self.poly_table.setItem(row_idx, 2, date_eval_item)

                # Colonne 3 : Prochaine évaluation (NON éditable - calculée automatiquement)
                date_next = poly['prochaine_evaluation'].strftime('%d/%m/%Y') if poly['prochaine_evaluation'] else "N/A"
                date_next_item = QTableWidgetItem(date_next)
                date_next_item.setFlags(date_next_item.flags() & ~Qt.ItemIsEditable)
                self.poly_table.setItem(row_idx, 3, date_next_item)

                # Colonne 4 : Statut (non éditable)
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

                # Colonne 5 : ID (caché)
                self.poly_table.setItem(row_idx, 5, QTableWidgetItem(str(poly['id'])))

            # Réactiver les signaux
            self.poly_table.blockSignals(False)

            # Charger les anciennes polyvalences
            self._load_anciennes_polyvalences(cursor)

            cursor.close()
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données :\n{e}")

    def _calculer_prochaine_eval_ancienne(self):
        """Calcule automatiquement la date de prochaine évaluation selon le niveau et la date d'évaluation."""
        niveau = self.niveau_combo.currentData()
        if niveau is None:
            return

        # Récupérer la date d'évaluation
        date_eval = self.date_eval.date()

        # Calcul selon le niveau
        if niveau == 1:
            jours = 30  # 1 mois
        elif niveau == 2:
            jours = 30  # 1 mois
        elif niveau in [3, 4]:
            jours = 3650  # 10 ans
        else:
            jours = 30  # Par défaut 1 mois

        date_future = date_eval.addDays(jours)
        self.date_prochaine_eval.setDate(date_future)

    def _load_anciennes_polyvalences(self, cursor):
        """Charge les anciennes polyvalences dans le tableau."""
        cursor.execute("""
            SELECT
                hp.id,
                p.poste_code,
                hp.ancien_niveau AS niveau_affiche,
                hp.ancienne_date_evaluation AS date_eval_affiche,
                hp.commentaire
            FROM historique_polyvalence hp
            LEFT JOIN postes p ON hp.poste_id = p.id
            WHERE hp.operateur_id = %s
              AND hp.action_type = 'IMPORT_MANUEL'
            ORDER BY hp.date_action DESC
        """, (self.operateur_id,))

        anciennes = cursor.fetchall()
        self.anciennes_table.setRowCount(len(anciennes))

        for row_idx, anc in enumerate(anciennes):
            self.anciennes_table.setItem(row_idx, 0, QTableWidgetItem(anc['poste_code'] or "N/A"))

            niveau_txt = (
                f"N{anc['niveau_affiche']}"
                if anc['niveau_affiche'] is not None else "N/A"
            )
            niveau_item = QTableWidgetItem(niveau_txt)
            niveau_item.setTextAlignment(Qt.AlignCenter)
            self.anciennes_table.setItem(row_idx, 1, niveau_item)

            if anc['date_eval_affiche']:
                date_eval = anc['date_eval_affiche'].strftime('%d/%m/%Y')
            else:
                date_eval = "N/A"
            self.anciennes_table.setItem(row_idx, 2, QTableWidgetItem(date_eval))

            self.anciennes_table.setItem(
                row_idx, 3,
                QTableWidgetItem(anc['commentaire'] or "—")
            )
            self.anciennes_table.setItem(
                row_idx, 4,
                QTableWidgetItem(str(anc['id']))
            )

    def _add_ancienne_poly(self):
        """Ajoute une ancienne polyvalence."""
        poste_id = self.poste_combo.currentData()
        if not poste_id:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un poste.")
            return

        niveau = self.niveau_combo.currentData()  # Utiliser currentData() au lieu de currentText()
        date_eval = self.date_eval.date().toPyDate()
        date_prochaine = self.date_prochaine_eval.date().toPyDate()  # Récupérer la prochaine évaluation calculée
        commentaire = self.commentaire.text().strip()

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insérer dans historique_polyvalence
            cursor.execute("""
                INSERT INTO historique_polyvalence
                (operateur_id, poste_id, action_type, nouveau_niveau, nouvelle_date_evaluation, commentaire, date_action)
                VALUES (%s, %s, 'IMPORT_MANUEL', %s, %s, %s, NOW())
            """, (self.operateur_id, poste_id, niveau, date_eval, commentaire or None))

            # Également insérer/mettre à jour dans polyvalence avec la prochaine évaluation
            cursor.execute("""
                INSERT INTO polyvalence (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    niveau = VALUES(niveau),
                    date_evaluation = VALUES(date_evaluation),
                    prochaine_evaluation = VALUES(prochaine_evaluation)
            """, (self.operateur_id, poste_id, niveau, date_eval, date_prochaine))

            conn.commit()
            cursor.close()
            conn.close()

            QMessageBox.information(self, "Succès", "Ancienne polyvalence ajoutée avec succès.")

            # Recharger les données
            self._load_data()

            # Réinitialiser le formulaire
            self.commentaire.clear()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter la polyvalence :\n{e}")

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

            # Mettre à jour dans la base de données
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE polyvalence
                    SET niveau = %s, date_evaluation = %s, prochaine_evaluation = %s
                    WHERE id = %s
                """, (new_niveau, date_eval, prochaine_eval, poly_id))

                conn.commit()
                cursor.close()
                conn.close()

                # Recharger les données pour afficher la nouvelle prochaine évaluation
                self._load_data()

                QMessageBox.information(self, "Succès",
                    f"Niveau mis à jour.\nProchaine évaluation automatiquement calculée : {prochaine_eval.strftime('%d/%m/%Y')}")

            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de mettre à jour le niveau :\n{e}")
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

                    # Mettre à jour les DEUX dates
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()

                        cursor.execute("""
                            UPDATE polyvalence
                            SET date_evaluation = %s, prochaine_evaluation = %s
                            WHERE id = %s
                        """, (new_date, prochaine_eval, poly_id))

                        conn.commit()
                        cursor.close()
                        conn.close()

                        # Recharger les données pour mettre à jour le statut
                        self._load_data()

                        QMessageBox.information(self, "Succès",
                            f"Date d'évaluation mise à jour.\nProchaine évaluation automatiquement recalculée : {prochaine_eval.strftime('%d/%m/%Y')}")
                        return

                    except Exception as e:
                        QMessageBox.critical(self, "Erreur", f"Impossible de mettre à jour la date :\n{e}")
                        self._load_data()
                        return

                except (ValueError, AttributeError):
                    pass  # Niveau invalide, continuer avec mise à jour simple

            # Si on arrive ici, c'est qu'il n'y avait pas de niveau valide
            # Faire une simple mise à jour de la date d'évaluation sans recalcul
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("UPDATE polyvalence SET date_evaluation = %s WHERE id = %s", (new_date, poly_id))

                conn.commit()
                cursor.close()
                conn.close()

                self._load_data()
                QMessageBox.information(self, "Succès", "Date d'évaluation mise à jour.")

            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de mettre à jour la date :\n{e}")
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
            conn = get_db_connection()
            cursor = conn.cursor()

            # Charger les opérateurs avec statistiques de polyvalences
            # Filtrer uniquement ceux qui ont au moins une polyvalence
            query = """
                SELECT
                    p.id,
                    p.nom,
                    p.prenom,
                    p.matricule,
                    COUNT(poly.id) as total_poly,
                    SUM(CASE WHEN poly.niveau = 4 THEN 1 ELSE 0 END) as n4,
                    SUM(CASE WHEN poly.niveau = 3 THEN 1 ELSE 0 END) as n3,
                    SUM(CASE WHEN poly.niveau = 2 THEN 1 ELSE 0 END) as n2,
                    SUM(CASE WHEN poly.niveau = 1 THEN 1 ELSE 0 END) as n1,
                    SUM(
                        CASE
                            WHEN poly.prochaine_evaluation IS NULL THEN 1
                            WHEN poly.prochaine_evaluation BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 1
                            ELSE 0
                        END
                    ) as a_planifier,

                    SUM(
                        CASE
                            WHEN poly.prochaine_evaluation < CURDATE() THEN 1
                            ELSE 0
                        END
                    ) as retard
                FROM personnel p
                INNER JOIN polyvalence poly ON poly.operateur_id = p.id
                WHERE p.statut = 'ACTIF'
                GROUP BY p.id, p.nom, p.prenom, p.matricule
                HAVING COUNT(poly.id) > 0
                ORDER BY p.nom, p.prenom
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            # Stocker toutes les données
            self.all_evaluations = []

            for row in rows:
                pers_id, nom, prenom, matricule, total, n4, n3, n2, n1, retard, a_planifier = row

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
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les évaluations :\n{e}")

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

    def update_date_in_db(self, row, col, qdate):
        """Met à jour une date dans la base de données."""
        from core.services.logger import log_hist
        import json

        poly_id_item = self.table.item(row, 0)
        if not poly_id_item:
            return

        try:
            poly_id = int(poly_id_item.text())
        except ValueError:
            return

        if col == 5:
            field = "date_evaluation"
            field_display = "Date d'évaluation"
        elif col == 6:
            field = "prochaine_evaluation"
            field_display = "Prochaine évaluation"
        else:
            return

        date_iso = qdate.toString("yyyy-MM-dd")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Récupérer l'ancienne valeur et les infos pour le log
            cursor.execute(f"""
                SELECT pv.{field}, p.nom, p.prenom, po.poste_code, po.id
                FROM polyvalence pv
                JOIN personnel p ON p.id = pv.operateur_id
                JOIN postes po ON po.id = pv.poste_id
                WHERE pv.id = %s
            """, (poly_id,))
            result = cursor.fetchone()

            if result:
                old_date = result[0]
                nom = result[1]
                prenom = result[2]
                poste_code = result[3]
                poste_id = result[4]

                # Mettre à jour la date
                cursor.execute(f"UPDATE polyvalence SET {field} = %s WHERE id = %s", (date_iso, poly_id))
                conn.commit()

                # Logger l'action
                log_hist(
                    action="UPDATE",
                    table_name="polyvalence",
                    record_id=poly_id,
                    operateur_id=None,
                    poste_id=poste_id,
                    description=json.dumps({
                        "operateur": f"{prenom} {nom}",
                        "poste": poste_code,
                        "field": field_display,
                        "old_value": str(old_date) if old_date else "Non défini",
                        "new_value": date_iso,
                        "type": "modification_date_evaluation"
                    }, ensure_ascii=False),
                    source="GUI/gestion_evaluation"
                )

            cursor.close()
            conn.close()

            QMessageBox.information(self, "Succès", "Date mise à jour avec succès.")

            # Recharger les données
            self.load_data()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de mettre à jour la date :\n{e}")

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
            QMessageBox.critical(self, "Erreur", f"Impossible d'exporter en PDF :\n{e}")

    def _on_row_double_click(self, row, col):
        """Gère le double-clic sur une ligne du tableau."""
        # Ne pas ouvrir le dialogue si on double-clique sur les colonnes de dates (5-6)
        if col in [5, 6]:
            return

        # Récupérer les infos de l'opérateur depuis all_evaluations
        if row < len(self.all_evaluations):
            eval_data = self.all_evaluations[row]
            operateur_id = eval_data.get('personnel_id')
            nom = eval_data.get('nom')
            prenom = eval_data.get('prenom')

            if not operateur_id:
                return

            # Ouvrir le dialogue détaillé avec 2 onglets
            dialog = DetailOperateurDialog(operateur_id, nom, prenom, self)
            dialog.exec_()

            # Recharger les données après fermeture du dialogue
            self.load_data()

