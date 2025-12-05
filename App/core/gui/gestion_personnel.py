# gestion_personnel.py – Gestion complète du personnel (actifs et inactifs)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QGroupBox,
    QMessageBox, QAbstractItemView, QWidget, QTabWidget, QCheckBox,
    QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from core.db.configbd import get_connection as get_db_connection
from core.services.logger import log_hist
from core.services.contrat_service import get_all_contracts
from core.gui.contract_management import ContractFormDialog
from core.gui.historique_personnel import HistoriquePersonnelTab
from core.gui.emac_ui_kit import add_custom_title_bar

import datetime as dt


# -------- Helpers DB --------
def _cursor(conn):
    """Retourne (cursor, dict_mode)."""
    try:
        cur = conn.cursor(dictionary=True)
        return cur, True
    except TypeError:
        cur = conn.cursor()
        return cur, False


def _rows(cur, dict_mode):
    """Retourne une liste de dicts quelle que soit la lib DB."""
    if dict_mode:
        return cur.fetchall()
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


class DetailOperateurDialog(QDialog):
    """Fenêtre modale affichant tous les détails d'un opérateur."""
    
    operateur_status_changed = pyqtSignal(int)  # Signal émis si changement de statut
    
    def __init__(self, operateur_id, nom, prenom, statut, parent=None):
        super().__init__(parent)
        self.operateur_id = operateur_id
        self.current_statut = statut.upper()
        self.setWindowTitle(f"Détails - {nom} {prenom}")
        self.setGeometry(200, 150, 900, 600)

        # Créer le layout principal avec marges nulles pour la barre de titre
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Ajouter la barre de titre personnalisée
        title_bar = add_custom_title_bar(self, f"Détails - {nom} {prenom}")
        main_layout.addWidget(title_bar)

        # Créer le widget de contenu avec marges normales
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # === Header avec infos opérateur ===
        header_content = QVBoxLayout()
        header = QLabel(f"{nom} {prenom}")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header_content.addWidget(header)

        status_label = QLabel(f"Statut : {self.current_statut}")
        if self.current_statut == "ACTIF":
            status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
        else:
            status_label.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 14px;")
        status_label.setAlignment(Qt.AlignCenter)
        header_content.addWidget(status_label)

        layout.addLayout(header_content)
        
        # === Onglets ===
        tabs = QTabWidget()
        
        # Onglet 1 : Polyvalences
        poly_tab = QWidget()
        poly_layout = QVBoxLayout(poly_tab)
        
        poly_label = QLabel("Polyvalences et Compétences")
        poly_label.setFont(QFont("Arial", 12, QFont.Bold))
        poly_layout.addWidget(poly_label)
        
        self.poly_table = QTableWidget()
        self.poly_table.setColumnCount(6)
        self.poly_table.setHorizontalHeaderLabels([
            "Poste", "Niveau", "Date Évaluation", "Prochaine Éval.", "Ancienneté", "Statut"
        ])
        self.poly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.poly_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        poly_layout.addWidget(self.poly_table)
        
        # Stats des niveaux
        stats_box = QHBoxLayout()
        self.stat_n1 = self._create_mini_stat("N1", "0", "#ef4444")
        self.stat_n2 = self._create_mini_stat("N2", "0", "#f59e0b")
        self.stat_n3 = self._create_mini_stat("N3", "0", "#10b981")
        self.stat_n4 = self._create_mini_stat("N4", "0", "#3b82f6")
        self.stat_total = self._create_mini_stat("Total", "0", "#6b7280")
        
        stats_box.addWidget(self.stat_n1)
        stats_box.addWidget(self.stat_n2)
        stats_box.addWidget(self.stat_n3)
        stats_box.addWidget(self.stat_n4)
        stats_box.addWidget(self.stat_total)
        poly_layout.addLayout(stats_box)
        
        tabs.addTab(poly_tab, "Polyvalences")

        # Onglet 2 : Infos Complémentaires
        infos_tab = QWidget()
        infos_layout = QVBoxLayout(infos_tab)
        infos_layout.setSpacing(15)
        infos_layout.setContentsMargins(20, 20, 20, 20)

        # En-tête avec design moderne
        header_infos = QWidget()
        header_infos.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #10b981);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_infos)

        infos_label = QLabel("ℹ️ Informations Complémentaires")
        infos_label.setFont(QFont("Arial", 16, QFont.Bold))
        infos_label.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(infos_label)

        infos_subtitle = QLabel("Contrat, formations, validités et autres données")
        infos_subtitle.setStyleSheet("color: #d1fae5; font-size: 11px; background: transparent;")
        header_layout.addWidget(infos_subtitle)

        infos_layout.addWidget(header_infos)

        # Tableau Catégorie / Valeur
        self.infos_table = QTableWidget()
        self.infos_table.setColumnCount(2)
        self.infos_table.setHorizontalHeaderLabels(["Catégorie", "Valeur"])
        self.infos_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.infos_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.infos_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.infos_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.infos_table.setSelectionMode(QAbstractItemView.NoSelection)

        infos_layout.addWidget(self.infos_table)

        tabs.addTab(infos_tab, "Infos Complémentaires")

        # Onglet 4 : Contrats
        contract_tab = QWidget()
        contract_layout = QVBoxLayout(contract_tab)
        contract_layout.setSpacing(15)
        contract_layout.setContentsMargins(20, 20, 20, 20)

        # En-tête avec design moderne
        header_contract = QWidget()
        header_contract.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d97706, stop:1 #f59e0b);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        header_layout_contract = QVBoxLayout(header_contract)

        contract_label = QLabel("📄 Contrats de Travail")
        contract_label.setFont(QFont("Arial", 16, QFont.Bold))
        contract_label.setStyleSheet("color: white; background: transparent;")
        header_layout_contract.addWidget(contract_label)

        contract_subtitle = QLabel("Historique complet des contrats")
        contract_subtitle.setStyleSheet("color: #fef3c7; font-size: 11px; background: transparent;")
        header_layout_contract.addWidget(contract_subtitle)

        contract_layout.addWidget(header_contract)

        # Boutons d'action pour les contrats
        contract_actions = QHBoxLayout()
        self.add_contract_btn = QPushButton("+ Nouveau contrat")
        self.add_contract_btn.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #d97706;
            }
        """)
        self.add_contract_btn.clicked.connect(self.add_contract)
        contract_actions.addWidget(self.add_contract_btn)

        self.edit_contract_btn = QPushButton("✏️ Modifier")
        self.edit_contract_btn.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #4b5563;
            }
        """)
        self.edit_contract_btn.clicked.connect(self.edit_contract)
        contract_actions.addWidget(self.edit_contract_btn)

        contract_actions.addStretch()
        contract_layout.addLayout(contract_actions)

        # Tableau des contrats
        self.contract_table = QTableWidget()
        self.contract_table.setColumnCount(7)
        self.contract_table.setHorizontalHeaderLabels([
            "ID", "Type", "Début", "Fin", "ETP", "Catégorie", "Actif"
        ])
        self.contract_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.contract_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.contract_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.contract_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.contract_table.setColumnHidden(0, True)  # Cacher l'ID
        self.contract_table.setAlternatingRowColors(True)
        self.contract_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #fef3c7;
                gridline-color: #fde68a;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                font-size: 11px;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f1f5f9, stop:1 #e2e8f0);
                color: #1e293b;
                font-weight: bold;
                font-size: 12px;
                padding: 12px 15px;
                border: none;
                border-bottom: 3px solid #f59e0b;
            }
            QTableWidget::item {
                padding: 12px 15px;
                border-bottom: 1px solid #f1f5f9;
            }
            QTableWidget::item:selected {
                background-color: #fde68a;
                color: #92400e;
            }
        """)
        self.contract_table.doubleClicked.connect(self.edit_contract)
        contract_layout.addWidget(self.contract_table)

        tabs.addTab(contract_tab, "Contrats")

        # Onglet 5 : Historique des modifications (nouveau widget complet)
        self.history_tab = HistoriquePersonnelTab(
            operateur_id=self.operateur_id,
            operateur_nom=nom,
            operateur_prenom=prenom,
            parent=self
        )
        tabs.addTab(self.history_tab, "Historique")

        self.tabs_widget = tabs
        layout.addWidget(tabs)
        
        # === Boutons d'action ===
        actions = QHBoxLayout()
        
        self.toggle_status_btn = QPushButton()
        self.update_status_button()
        self.toggle_status_btn.clicked.connect(self.toggle_operateur_status)
        actions.addWidget(self.toggle_status_btn)
        
        actions.addStretch()
        
        self.export_btn = QPushButton("Exporter le profil")
        self.export_btn.clicked.connect(self.export_profile)
        actions.addWidget(self.export_btn)
        
        self.close_btn = QPushButton("Fermer")
        self.close_btn.clicked.connect(self.close)
        actions.addWidget(self.close_btn)

        layout.addLayout(actions)

        # Ajouter le widget de contenu au layout principal
        main_layout.addWidget(content_widget)

        # Charger les données
        self.load_data()
    
    def update_status_button(self):
        """Met à jour le texte et le style du bouton de changement de statut."""
        if self.current_statut == "ACTIF":
            self.toggle_status_btn.setText("Désactiver l'opérateur")
            self.toggle_status_btn.setStyleSheet("""
                QPushButton {
                    background: #dc2626;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: #b91c1c;
                }
            """)
        else:
            self.toggle_status_btn.setText("Réactiver l'opérateur")
            self.toggle_status_btn.setStyleSheet("""
                QPushButton {
                    background: #10b981;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: #059669;
                }
            """)
    
    def _create_mini_stat(self, label, value, color):
        """Crée une mini-carte de statistique."""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background: {color};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        val_label = QLabel(value)
        val_label.setFont(QFont("Arial", 16, QFont.Bold))
        val_label.setStyleSheet("color: white;")
        val_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(val_label)
        
        text_label = QLabel(label)
        text_label.setStyleSheet("color: white; font-size: 10px;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        
        widget.value_label = val_label
        return widget
    
    def load_data(self):
        """Charge toutes les données de l'opérateur."""
        self.load_polyvalences()
        self.load_additional_infos() # <--- AJOUT : Chargement des nouvelles infos
        self.load_contracts()
        # L'historique se charge automatiquement via le widget HistoriquePersonnelTab

    
    
    def load_additional_infos(self):
        """Charge les infos complémentaires de manière plus lisible (sans sections vides)."""
        try:
            self.infos_table.setRowCount(0)

            # -------- Informations personnelles --------
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            cursor.execute("SELECT * FROM personnel_infos WHERE operateur_id = %s", (self.operateur_id,))
            row_data = _rows(cursor, dict_mode)
            cursor.close(); connection.close()

            if row_data:
                self._insert_section("👤 Informations personnelles")
                data = row_data[0]
                for key, val in data.items():
                    if key == "operateur_id":
                        continue
                    label = self._format_column_name(key)
                    value = (
                        val.strftime("%d/%m/%Y") if isinstance(val, dt.date)
                        else (str(val) if val not in (None, "",) else None)
                    )
                    if value is not None:
                        self._insert_kv(label, value)

            # -------- Contrat actuel --------
            self._insert_section("📄 Contrat actuel")
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            cursor.execute("""
                SELECT type_contrat, date_debut, date_fin, etp, categorie
                FROM contrat
                WHERE operateur_id = %s AND actif = 1
                ORDER BY date_debut DESC LIMIT 1
            """, (self.operateur_id,))
            contr = _rows(cursor, dict_mode)
            cursor.close(); connection.close()

            if contr:
                c = contr[0]
                parts = [c.get("type_contrat", "")]
                if c.get("etp") is not None:
                    parts.append(f"ETP {c['etp']}")
                d1, d2 = c.get("date_debut"), c.get("date_fin")
                if d1 or d2:
                    deb = d1.strftime("%d/%m/%Y") if isinstance(d1, dt.date) else str(d1)
                    fin = (
                        d2.strftime("%d/%m/%Y") if isinstance(d2, dt.date)
                        else (str(d2) if d2 else "…")
                    )
                    parts.append(f"{deb} → {fin}")
                self._insert_kv("Contrat actif", " — ".join([p for p in parts if p]))
            else:
                self._insert_kv("Contrat actif", "Aucun contrat actif pour cet opérateur.")

            # -------- Congés / Absences --------
            # Les tables compteur_conges et absences_conges ne sont plus utilisées.
            self._insert_section("⛱ Congés / absences")
            self._insert_kv(
                "Information",
                "Module congés/absences non utilisé dans cette application."
            )

            # -------- Formations --------
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            cursor.execute("""
                SELECT intitule, organisme, date_debut, date_fin, statut, certificat_obtenu
                FROM formation
                WHERE operateur_id = %s
                ORDER BY date_debut DESC LIMIT 5
            """, (self.operateur_id,))
            formations = _rows(cursor, dict_mode)
            cursor.close(); connection.close()

            self._insert_section("📚 Formations")
            if formations:
                for f in formations:
                    d1 = self._format_date(f.get("date_debut"))
                    d2 = self._format_date(f.get("date_fin"))
                    cert = "✅" if f.get("certificat_obtenu") else "—"
                    texte = f"{d1} → {d2} — {f.get('statut','')} {cert}"
                    self._insert_kv(f.get("intitule", "(formation)"), texte)
            else:
                self._insert_kv("Formations", "Aucune formation renseignée pour le moment.")

            # -------- Validités --------
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            cursor.execute("""
                SELECT type_validite, date_debut, date_fin, periodicite, taux_incapacite
                FROM validite
                WHERE operateur_id = %s
                ORDER BY date_debut DESC
            """, (self.operateur_id,))
            validites = _rows(cursor, dict_mode)
            cursor.close(); connection.close()

            self._insert_section("✅ Validités")
            if validites:
                for v in validites:
                    d1 = self._format_date(v.get("date_debut"))
                    d2 = self._format_date(v.get("date_fin")) if v.get("date_fin") else "—"
                    tc = (
                        f" ({v['taux_incapacite']}%)"
                        if v.get("taux_incapacite") is not None
                        else ""
                    )
                    texte = f"{d1} → {d2} — {v.get('periodicite', '')}{tc}"
                    self._insert_kv(v.get("type_validite", "(type)"), texte)
            else:
                self._insert_kv("Validités", "Aucune validité enregistrée.")

            # largeur colonnes
            self.infos_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.infos_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur de chargement",
                f"Impossible de charger les infos détaillées :\n{e}"
            )

    def _insert_kv(self, label: str, value: str | None):
        """Insère une ligne Catégorie / Valeur (texte gris + italique si vide)."""
        row = self.infos_table.rowCount()
        self.infos_table.insertRow(row)

        cat = QTableWidgetItem(label)
        cat.setFont(QFont("Arial", 10, QFont.Bold))
        self.infos_table.setItem(row, 0, cat)

        if value in (None, "",):
            display = "Aucune information"
            val = QTableWidgetItem(display)
            val.setForeground(QColor("#9ca3af"))
            f = val.font()
            f.setItalic(True)
            val.setFont(f)
        else:
            val = QTableWidgetItem(value)

        val.setFlags(val.flags() & ~Qt.ItemIsEditable)
        self.infos_table.setItem(row, 1, val)


    def _format_column_name(self, col_name: str) -> str:
        """
        Formate un nom de colonne SQL en texte lisible.
        Exemple: 'date_naissance' → 'Date Naissance'
        """
        if not col_name:
            return ""

        formatted = col_name.replace("_", " ")
        formatted = " ".join(word.capitalize() for word in formatted.split())

        replacements = {
            "Cp": "CP",
            "Rtt": "RTT",
            "Id": "ID",
            "Nir": "NIR",
            "Etp": "ETP",
            "Operateur": "Opérateur",
        }
        for old, new in replacements.items():
            formatted = formatted.replace(old, new)

        return formatted


    
    def load_polyvalences(self):
        """Charge les polyvalences."""
        try:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            
            query = """
                SELECT 
                    ps.poste_code,
                    p.niveau,
                    p.date_evaluation,
                    p.prochaine_evaluation
                FROM polyvalence p
                JOIN postes ps ON p.poste_id = ps.id
                WHERE p.operateur_id = %s
                ORDER BY ps.poste_code
            """
            
            cursor.execute(query, (self.operateur_id,))
            rows = _rows(cursor, dict_mode)
            
            cursor.close()
            connection.close()
            
            self.poly_table.setRowCount(0)
            
            niveaux = {1: 0, 2: 0, 3: 0, 4: 0}
            
            for r in rows:
                row = self.poly_table.rowCount()
                self.poly_table.insertRow(row)
                
                poste = r.get("poste_code", "")
                niveau = r.get("niveau")
                date_eval = r.get("date_evaluation")
                date_next = r.get("prochaine_evaluation")
                
                # Poste
                self.poly_table.setItem(row, 0, QTableWidgetItem(str(poste)))
                
                # Niveau
                niveau_item = QTableWidgetItem(str(niveau) if niveau else "N/A")
                if niveau:
                    niveaux[int(niveau)] += 1
                    if niveau == 1:
                        niveau_item.setBackground(QColor("#fef2f2"))
                        niveau_item.setForeground(QColor("#dc2626"))
                    elif niveau == 2:
                        niveau_item.setBackground(QColor("#fffbeb"))
                        niveau_item.setForeground(QColor("#d97706"))
                    elif niveau == 3:
                        niveau_item.setBackground(QColor("#f0fdf4"))
                        niveau_item.setForeground(QColor("#059669"))
                    elif niveau == 4:
                        niveau_item.setBackground(QColor("#eff6ff"))
                        niveau_item.setForeground(QColor("#2563eb"))
                niveau_item.setTextAlignment(Qt.AlignCenter)
                self.poly_table.setItem(row, 1, niveau_item)
                
                # Dates
                self.poly_table.setItem(row, 2, QTableWidgetItem(self._format_date(date_eval)))
                self.poly_table.setItem(row, 3, QTableWidgetItem(self._format_date(date_next)))
                
                # Ancienneté
                anciennete = self._calculate_anciennete(date_eval)
                self.poly_table.setItem(row, 4, QTableWidgetItem(anciennete))
                
                # Statut (À jour / En retard)
                statut_item = QTableWidgetItem()
                if date_next:
                    today = dt.date.today()
                    if isinstance(date_next, str):
                        next_date = dt.datetime.strptime(date_next, "%Y-%m-%d").date()
                    elif hasattr(date_next, "date"):
                        next_date = date_next.date()
                    else:
                        next_date = date_next
                    
                    if next_date < today:
                        statut_item.setText("En retard")
                        statut_item.setForeground(QColor("#dc2626"))
                    else:
                        statut_item.setText("À jour")
                        statut_item.setForeground(QColor("#059669"))
                else:
                        statut_item.setText("À planifier")
                        statut_item.setForeground(QColor("#d97706"))  # orange
                
                statut_item.setTextAlignment(Qt.AlignCenter)
                self.poly_table.setItem(row, 5, statut_item)
            
            # Mise à jour des stats
            self.stat_n1.value_label.setText(str(niveaux[1]))
            self.stat_n2.value_label.setText(str(niveaux[2]))
            self.stat_n3.value_label.setText(str(niveaux[3]))
            self.stat_n4.value_label.setText(str(niveaux[4]))
            self.stat_total.value_label.setText(str(sum(niveaux.values())))
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les polyvalences :\n{e}")
    
    # Méthode load_summary() supprimée - l'onglet Résumé a été retiré
    
    # Méthode load_history() supprimée - remplacée par le widget HistoriquePersonnelTab

    def toggle_operateur_status(self):
        """Change le statut de l'opérateur (ACTIF <-> INACTIF)."""
        new_statut = "INACTIF" if self.current_statut == "ACTIF" else "ACTIF"
        action = "désactiver" if new_statut == "INACTIF" else "réactiver"
        
        reply = QMessageBox.question(
            self, f"Confirmer {action}",
            f"Êtes-vous sûr de vouloir {action} cet opérateur ?\n\n"
            f"Son statut passera à {new_statut}.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            connection = get_db_connection()
            cursor, _ = _cursor(connection)

            # Récupérer nom/prénom pour le log
            cursor.execute("SELECT nom, prenom FROM personnel WHERE id = %s", (self.operateur_id,))
            pers = cursor.fetchone()

            cursor.execute(
                "UPDATE personnel SET statut = %s WHERE id = %s",
                (new_statut, self.operateur_id)
            )

            connection.commit()

            # Logger le changement de statut
            if pers:
                from core.services.logger import log_hist
                import json
                log_hist(
                    action="UPDATE",
                    table_name="personnel",
                    record_id=self.operateur_id,
                    operateur_id=self.operateur_id,
                    description=json.dumps({
                        "operateur": f"{pers[1]} {pers[0]}",
                        "old_statut": self.current_statut,
                        "new_statut": new_statut,
                        "type": "changement_statut"
                    }, ensure_ascii=False),
                    source="GUI/gestion_personnel"
                )

            cursor.close()
            connection.close()

            self.current_statut = new_statut
            self.update_status_button()

            QMessageBox.information(
                self, "Statut modifié",
                f"Le statut de l'opérateur a été changé à {new_statut} avec succès !"
            )

            self.operateur_status_changed.emit(self.operateur_id)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de modifier le statut :\n{e}")

    def load_contracts(self):
        """Charge l'historique des contrats de l'opérateur."""
        try:
            contracts = get_all_contracts(self.operateur_id, include_inactive=True)

            self.contract_table.setRowCount(0)

            for contract in contracts:
                row = self.contract_table.rowCount()
                self.contract_table.insertRow(row)

                # ID (caché)
                self.contract_table.setItem(row, 0, QTableWidgetItem(str(contract['id'])))

                # Type
                type_item = QTableWidgetItem(contract['type_contrat'])
                self.contract_table.setItem(row, 1, type_item)

                # Date début
                date_debut_str = contract['date_debut'].strftime('%d/%m/%Y') if contract['date_debut'] else ''
                self.contract_table.setItem(row, 2, QTableWidgetItem(date_debut_str))

                # Date fin
                date_fin_str = contract['date_fin'].strftime('%d/%m/%Y') if contract['date_fin'] else 'Indéterminée'
                self.contract_table.setItem(row, 3, QTableWidgetItem(date_fin_str))

                # ETP
                etp_str = str(contract.get('etp', '1.0'))
                self.contract_table.setItem(row, 4, QTableWidgetItem(etp_str))

                # Catégorie
                categorie = contract.get('categorie', '')
                self.contract_table.setItem(row, 5, QTableWidgetItem(categorie or ''))

                # Actif
                actif_str = "✅ Actif" if contract.get('actif') else "❌ Inactif"
                actif_item = QTableWidgetItem(actif_str)
                if contract.get('actif'):
                    actif_item.setForeground(QColor("#10b981"))
                else:
                    actif_item.setForeground(QColor("#6b7280"))
                self.contract_table.setItem(row, 6, actif_item)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les contrats : {e}")

    def add_contract(self):
        """Ouvre le formulaire pour ajouter un nouveau contrat."""
        dialog = ContractFormDialog(self, operateur_id=self.operateur_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_contracts()
            self.load_additional_infos()  # Recharger les infos complémentaires

    def edit_contract(self):
        """Modifie le contrat sélectionné."""
        current_row = self.contract_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un contrat")
            return

        contract_id = int(self.contract_table.item(current_row, 0).text())
        dialog = ContractFormDialog(self, contract_id=contract_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_contracts()
            self.load_additional_infos()  # Recharger les infos complémentaires

    def export_profile(self):
        """Demande le format d'export puis lance PDF ou Excel."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

        dlg = QDialog(self)
        dlg.setWindowTitle("Exporter le profil")
        dlg.setMinimumWidth(360)

        v = QVBoxLayout(dlg)
        v.addWidget(QLabel("Choisir le format d'export :"))

        btns = QHBoxLayout()
        b_pdf = QPushButton("PDF")
        b_xlsx = QPushButton("Excel")
        b_cancel = QPushButton("Annuler")
        b_pdf.clicked.connect(lambda: (setattr(dlg, "_choice", "pdf"), dlg.accept()))
        b_xlsx.clicked.connect(lambda: (setattr(dlg, "_choice", "xlsx"), dlg.accept()))
        b_cancel.clicked.connect(dlg.reject)

        btns.addStretch(1)
        btns.addWidget(b_pdf)
        btns.addWidget(b_xlsx)
        btns.addWidget(b_cancel)
        v.addLayout(btns)

        if dlg.exec_() != QDialog.Accepted or getattr(dlg, "_choice", None) is None:
            return

        if dlg._choice == "pdf":
            self.export_profile_pdf()
        else:
            self.export_profile_excel()

    def export_profile_pdf(self):
        """
        Export PDF professionnel avec mise en page améliorée.
        Analyse et structure le contenu en sections claires.
        """
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, KeepTogether
            )
            from reportlab.lib.units import cm
            from reportlab.pdfgen.canvas import Canvas
            import datetime as _dt
            import re
    
            # ---------- Helpers ----------
            def _clean_text(text: str) -> str:
                """Nettoie le texte des caractères de formatage."""
                if not text:
                    return ""
                # Supprimer les barres décoratives
                text = re.sub(r'[■█╔╗╚╝═─│┐└┘├┤┬┴┼]', '', text)
                # Supprimer les lignes vides multiples
                text = re.sub(r'\n{3,}', '\n\n', text)
                # Normaliser les espaces autour des :
                text = re.sub(r'\s*:\s*', ' : ', text)
                return text.strip()
    
            def _parse_section(text: str) -> dict:
                """Parse une section et extrait les données structurées."""
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                sections = {}
                current_section = None
                current_items = []
                
                for line in lines:
                    # Détecter les titres de section (avec emoji ou tout en majuscules)
                    if re.match(r'^[🔊📅⭐💡■]', line) or (line.isupper() and len(line) > 3):
                        if current_section:
                            sections[current_section] = current_items
                        current_section = re.sub(r'^[🔊📅⭐💡■]\s*', '', line)
                        current_items = []
                    elif line.startswith('•') or line.startswith('-'):
                        # Item de liste
                        item = re.sub(r'^[•\-]\s*', '', line)
                        current_items.append(item)
                    elif ':' in line and not line.startswith(' '):
                        # Ligne clé : valeur
                        current_items.append(line)
                
                if current_section:
                    sections[current_section] = current_items
                
                return sections
    
            # ---------- Données opérateur ----------
            nom = prenom = matricule = statut = "-"
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT nom, prenom, COALESCE(matricule,'-'), UPPER(statut)
                    FROM personnel WHERE id=%s
                """, (self.operateur_id,))
                row = cur.fetchone()
                if row:
                    nom, prenom, matricule, statut = row
                cur.close()
                conn.close()
            except Exception:
                pass
    
            # ---------- Fichier ----------
            default_name = f"profil_{(matricule or 'operateur')}_{_dt.date.today():%Y%m%d}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(self, "Exporter en PDF", default_name, "PDF (*.pdf)")
            if not file_path:
                return
    
            # ---------- Styles améliorés ----------
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=18,
                textColor=colors.HexColor("#1e40af"),
                spaceAfter=8,
                fontName="Helvetica-Bold"
            )
            
            section_style = ParagraphStyle(
                "CustomSection",
                parent=styles["Heading2"],
                fontSize=13,
                textColor=colors.HexColor("#1e40af"),
                spaceBefore=14,
                spaceAfter=8,
                fontName="Helvetica-Bold",
                borderWidth=0,
                borderColor=colors.HexColor("#3b82f6"),
                borderPadding=4
            )
            
            subsection_style = ParagraphStyle(
                "CustomSubsection",
                parent=styles["Heading3"],
                fontSize=11,
                textColor=colors.HexColor("#475569"),
                spaceBefore=8,
                spaceAfter=4,
                fontName="Helvetica-Bold"
            )
            
            body_style = ParagraphStyle(
                "CustomBody",
                parent=styles["Normal"],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#1f2937")
            )
            
            bullet_style = ParagraphStyle(
                "CustomBullet",
                parent=body_style,
                leftIndent=20,
                bulletIndent=10,
                spaceBefore=2,
                spaceAfter=2
            )
    
            # ---------- En-tête / Pied ----------
            def _header_footer(canvas: Canvas, doc):
                canvas.saveState()
                
                # Bandeau supérieur
                canvas.setFillColor(colors.HexColor("#1e40af"))
                canvas.rect(0, A4[1]-40, A4[0], 40, fill=1, stroke=0)
                
                canvas.setFillColor(colors.white)
                canvas.setFont("Helvetica-Bold", 12)
                canvas.drawString(doc.leftMargin, A4[1]-25, f"{nom} {prenom}")
                
                canvas.setFont("Helvetica", 9)
                canvas.drawString(doc.leftMargin, A4[1]-38, 
                                f"Matricule : {matricule}  •  Statut : {statut}")
                
                # Pied de page
                canvas.setFillColor(colors.HexColor("#64748b"))
                canvas.setFont("Helvetica", 8)
                canvas.drawCentredString(A4[0]/2, 15, f"Page {doc.page}")
                canvas.drawRightString(A4[0]-doc.rightMargin, 15, 
                                     f"Généré le {_dt.date.today().strftime('%d/%m/%Y')}")
                
                canvas.restoreState()
    
            # ---------- Document ----------
            doc = SimpleDocTemplate(
                file_path, pagesize=A4,
                leftMargin=2*cm, rightMargin=2*cm, 
                topMargin=2.5*cm, bottomMargin=2*cm
            )
            flow = []
            
            # Titre principal
            flow.append(Paragraph(f"Profil Opérateur", title_style))
            flow.append(Spacer(1, 0.3*cm))
    
            # Note: L'onglet résumé a été supprimé, donc on n'affiche plus le résumé textuel
            # On affiche directement les informations principales
            flow.append(Paragraph(f"<b>Nom :</b> {self.operateur_nom}", body_style))
            flow.append(Paragraph(f"<b>Prénom :</b> {self.operateur_prenom}", body_style))
            flow.append(Spacer(1, 0.3*cm))
    
            # ---------- Informations complémentaires ----------
            flow.append(Paragraph("Informations Complémentaires", section_style))
            
            infos_data = []
            if hasattr(self, "infos_table") and self.infos_table.rowCount() > 0:
                for r in range(self.infos_table.rowCount()):
                    c0 = self.infos_table.item(r, 0)
                    c1 = self.infos_table.item(r, 1)
                    if c0 and c1:
                        label = c0.text().strip()
                        value = c1.text().strip()
                        if label and "Aucune information" not in label:
                            infos_data.append([label, value])
            
            if infos_data:
                t_infos = Table(infos_data, colWidths=[6*cm, 11*cm])
                t_infos.setStyle(TableStyle([
                    ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
                    ("FONTSIZE", (0,0), (-1,-1), 9),
                    ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#475569")),
                    ("TEXTCOLOR", (1,0), (1,-1), colors.HexColor("#1f2937")),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("ROWBACKGROUNDS", (0,0), (-1,-1), 
                     [colors.white, colors.HexColor("#f8fafc")]),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                    ("LEFTPADDING", (0,0), (-1,-1), 8),
                    ("RIGHTPADDING", (0,0), (-1,-1), 8),
                    ("TOPPADDING", (0,0), (-1,-1), 6),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
                ]))
                flow.append(t_infos)
            else:
                flow.append(Paragraph("<i>Aucune information complémentaire disponible</i>", body_style))
            
            flow.append(Spacer(1, 0.5*cm))
    
            # ---------- Polyvalences ----------
            flow.append(Paragraph("Polyvalences et Évaluations", section_style))
            
            poly_data = [["Poste", "Niveau", "Dernière\néval.", "Prochaine\néval.", "Ancienneté", "Statut"]]
            
            if hasattr(self, "poly_table") and self.poly_table.rowCount() > 0:
                for r in range(self.poly_table.rowCount()):
                    row_data = []
                    for c in range(6):
                        item = self.poly_table.item(r, c)
                        row_data.append(item.text() if item else "")
                    poly_data.append(row_data)
            else:
                poly_data.append(["Aucune polyvalence enregistrée", "", "", "", "", ""])
            
            col_widths = [4*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm]
            t_poly = Table(poly_data, colWidths=col_widths, repeatRows=1)
            
            t_poly.setStyle(TableStyle([
                # En-tête
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE", (0,0), (-1,0), 9),
                ("ALIGN", (0,0), (-1,0), "CENTER"),
                ("VALIGN", (0,0), (-1,0), "MIDDLE"),
                # Corps
                ("FONTSIZE", (0,1), (-1,-1), 9),
                ("ALIGN", (1,1), (-1,-1), "CENTER"),
                ("ALIGN", (0,1), (0,-1), "LEFT"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), 
                 [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ("LEFTPADDING", (0,0), (-1,-1), 6),
                ("RIGHTPADDING", (0,0), (-1,-1), 6),
                ("TOPPADDING", (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ]))
            
            flow.append(t_poly)
    
            # ---------- Build ----------
            doc.build(flow, onFirstPage=_header_footer, onLaterPages=_header_footer)
            QMessageBox.information(self, "Export réussi", 
                                  f"Le profil a été exporté avec succès !\n\n{file_path}")
    
        except ImportError:
            QMessageBox.warning(self, "Module manquant",
                              "Le module 'reportlab' est requis pour l'export PDF.\n\n"
                              "Installez-le avec : pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", 
                               f"Une erreur s'est produite lors de l'export PDF :\n\n{str(e)}")



    def export_profile_excel(self):
        """Export Excel lisible : Résumé (A..S, wrap + hauteur auto), Informations, Polyvalences."""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            import datetime as _dt
    
            # ----- Styles -----
            THIN = Side(style="thin", color="DDDDDD")
            BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
            HDR_FILL = PatternFill("solid", fgColor="4472C4")
            HDR_FONT = Font(bold=True, color="FFFFFF")
            SEC_FILL = PatternFill("solid", fgColor="EEF2FF")
            TITLE_FONT = Font(bold=True, size=16)
            SUB_FONT = Font(bold=True, size=12, color="555555")
            CENTER = Alignment(horizontal="center", vertical="center")
            LEFT = Alignment(horizontal="left", vertical="center")
            LEFT_WRAP = Alignment(horizontal="left", vertical="top", wrap_text=True)
    
            def style_header(row):
                for c in row:
                    c.fill = HDR_FILL
                    c.font = HDR_FONT
                    c.alignment = CENTER
                    c.border = BORDER
    
            def style_table(ws, start_row, start_col, end_row, end_col, zebra=False):
                for r in range(start_row, end_row + 1):
                    fill = PatternFill("solid", fgColor="F8FAFC") if zebra and r > start_row and (r - start_row) % 2 == 1 else None
                    for c in range(start_col, end_col + 1):
                        cell = ws.cell(r, c)
                        cell.border = BORDER
                        if fill:
                            cell.fill = fill
    
            def autofit(ws, min_w=10, max_w=80):
                for col in range(1, ws.max_column + 1):
                    letter = get_column_letter(col)
                    longest = 0
                    for row in ws.iter_rows(min_col=col, max_col=col):
                        v = row[0].value
                        if v is not None:
                            longest = max(longest, len(str(v)))
                    ws.column_dimensions[letter].width = max(min(longest + 2, max_w), min_w)
    
            # estimation de hauteur pour cellule fusionnée (wrap)
            def set_wrapped_row_height(ws, row_idx, merged_cols, char_width=7):
                """Calcule et définit la hauteur de ligne pour du texte wrappé."""
                # Largeur totale disponible en pixels (approximation)
                total_width = 0
                for col in merged_cols:
                    col_width = ws.column_dimensions[col].width or 10
                    total_width += col_width * char_width  # Conversion largeur Excel -> pixels
                
                txt = str(ws.cell(row_idx, 1).value or "")
                if not txt:
                    ws.row_dimensions[row_idx].height = 20
                    return
                
                # Calculer le nombre de lignes en tenant compte des sauts de ligne
                lines_content = txt.split('\n')
                total_lines = 0
                
                for line in lines_content:
                    if not line.strip():
                        total_lines += 1  # Ligne vide
                    else:
                        # Nombre de lignes nécessaires pour cette ligne de contenu
                        line_chars = len(line)
                        chars_per_line = max(1, total_width // char_width)
                        lines_needed = max(1, (line_chars + chars_per_line - 1) // chars_per_line)
                        total_lines += lines_needed
                
                # Définir la hauteur (15 points par ligne + marge)
                ws.row_dimensions[row_idx].height = max(20, total_lines * 15 + 10)
    
            # ----- En-tête opérateur -----
            nom = prenom = matricule = statut = "-"
            try:
                conn = get_db_connection(); cur = conn.cursor()
                cur.execute("SELECT nom, prenom, COALESCE(matricule,'-'), UPPER(statut) FROM personnel WHERE id=%s", (self.operateur_id,))
                row = cur.fetchone()
                if row:
                    nom, prenom, matricule, statut = row
            finally:
                try: cur.close(); conn.close()
                except: pass
    
            default_name = f"profil_{(matricule or 'operateur')}_{_dt.date.today():%Y%m%d}.xlsx"
            file_path, _ = QFileDialog.getSaveFileName(self, "Exporter le profil", default_name, "Excel Files (*.xlsx)")
            if not file_path:
                return
    
            wb = Workbook()
    
            # =========================================================
            # 1) FEUILLE RÉSUMÉ (grande largeur A..S)
            # =========================================================
            ws1 = wb.active; ws1.title = "Résumé"
            ws1.sheet_view.zoomScale = 120  # zoom confortable
    
            # colonnes A..S bien larges
            wide_cols = [chr(c) for c in range(ord('A'), ord('S')+1)]  # A..S
            for col in wide_cols:
                ws1.column_dimensions[col].width = 24  # large et lisible
    
            # Titre & sous-titre fusionnés sur A..S
            ws1.merge_cells("A1:S1")
            ws1["A1"] = f"Profil opérateur — {nom or ''} {prenom or ''}".strip()
            ws1["A1"].font = TITLE_FONT
            ws1["A1"].alignment = LEFT
    
            ws1.merge_cells("A2:S2")
            ws1["A2"] = f"Matricule : {matricule or '-'}    |    Statut : {statut or '-'}"
            ws1["A2"].font = SUB_FONT
            ws1["A2"].alignment = LEFT
    
            # Note: L'onglet résumé a été supprimé, donc pas de contenu ici
            ws1["A4"] = "Informations de base"
            ws1["A4"].font = Font(bold=True)
            ws1["A4"].fill = SEC_FILL
            ws1["A4"].alignment = LEFT

            ws1.freeze_panes = "A5"
    
            # =========================================================
            # 2) FEUILLE INFORMATIONS
            # =========================================================
            ws2 = wb.create_sheet("Informations")
            ws2.sheet_view.zoomScale = 120
            ws2.merge_cells("A1:D1")
            ws2["A1"] = "Informations complémentaires"
            ws2["A1"].font = TITLE_FONT
            ws2["A1"].alignment = LEFT
    
            ws2.append(["Catégorie", "Valeur"])
            style_header(ws2[2])
    
            if hasattr(self, "infos_table"):
                for r in range(self.infos_table.rowCount()):
                    c0 = self.infos_table.item(r, 0)
                    c1 = self.infos_table.item(r, 1)
                    if not c0:
                        continue
                    label = c0.text().strip()
                    if label == "Aucune information complémentaire disponible.":
                        continue
                    ws2.append([label, (c1.text() if c1 else "")])
    
            style_table(ws2, 3, 1, ws2.max_row, 2, zebra=True)
            for cell in ws2["B"][2:]:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            autofit(ws2, min_w=18, max_w=80)
            ws2.freeze_panes = "A3"
    
            # =========================================================
            # 3) FEUILLE POLYVALENCES
            # =========================================================
            ws3 = wb.create_sheet("Polyvalences")
            ws3.sheet_view.zoomScale = 120
            ws3.merge_cells("A1:F1")
            ws3["A1"] = "Polyvalences & Évaluations"
            ws3["A1"].font = TITLE_FONT
            ws3["A1"].alignment = LEFT
    
            headers = ["Poste", "Niveau", "Date Évaluation", "Prochaine Éval.", "Ancienneté", "Statut"]
            ws3.append(headers)
            style_header(ws3[2])
    
            if hasattr(self, "poly_table"):
                for row in range(self.poly_table.rowCount()):
                    def t(c):
                        it = self.poly_table.item(row, c)
                        return it.text() if it else ""
                    ws3.append([t(0), t(1), t(2), t(3), t(4), t(5)])
    
            style_table(ws3, 3, 1, ws3.max_row, 6, zebra=True)
            for row in ws3.iter_rows(min_row=3, min_col=1, max_col=6, max_row=ws3.max_row):
                for c in row:
                    c.alignment = CENTER
            for c in ws3["A"][2:]:
                c.alignment = Alignment(horizontal="left", vertical="center")
            autofit(ws3, min_w=12, max_w=28)
            ws3.freeze_panes = "A3"
    
            # ----- Save -----
            wb.save(file_path)
            QMessageBox.information(self, "Export réussi", f"Profil exporté :\n{file_path}")
    
        except ImportError:
            QMessageBox.warning(self, "Module manquant",
                                "Le module 'openpyxl' est requis pour l'export Excel.\n\npip install openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'exporter le profil :\n{e}")


    
    def _format_date(self, date_val):
        """Formate une date."""
        if date_val is None:
            return "N/A"
        if isinstance(date_val, str):
            try:
                return dt.datetime.strptime(date_val, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                return date_val
        if hasattr(date_val, "strftime"):
            return date_val.strftime("%d/%m/%Y")
        return str(date_val)
    
    def _format_datetime(self, datetime_val):
        """Formate un datetime."""
        if datetime_val is None:
            return "N/A"
        if isinstance(datetime_val, str):
            try:
                return dt.datetime.fromisoformat(datetime_val).strftime("%d/%m/%Y %H:%M")
            except:
                return datetime_val
        if hasattr(datetime_val, "strftime"):
            return datetime_val.strftime("%d/%m/%Y %H:%M")
        return str(datetime_val)
    
    def _insert_info_row(self, row_index: int, label: str, value: str):
        """Insère une ligne (Catégorie, Valeur) dans infos_table."""
        # Sécurité: s'assurer que la table existe
        if not hasattr(self, "infos_table"):
            return
        self.infos_table.insertRow(row_index)

        # Colonne 0 : libellé
        cat_item = QTableWidgetItem(label)
        cat_item.setFont(QFont("Arial", 10, QFont.Bold))
        self.infos_table.setItem(row_index, 0, cat_item)

        # Colonne 1 : valeur
        val_item = QTableWidgetItem(value if value is not None else "—")
        val_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        val_item.setFlags(val_item.flags() & ~Qt.ItemIsEditable)
        self.infos_table.setItem(row_index, 1, val_item)

    def _insert_section(self, title: str):
        """Insère un séparateur de section (ligne pleine largeur)."""
        row = self.infos_table.rowCount()
        self.infos_table.insertRow(row)
        item = QTableWidgetItem(title.upper())
        item.setFont(QFont("Arial", 10, QFont.Bold))
        item.setForeground(QColor("#111827"))
        item.setBackground(QColor("#f1f5f9"))
        item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
        self.infos_table.setItem(row, 0, item)
        self.infos_table.setSpan(row, 0, 1, 2)

    def _insert_kv(self, label: str, value: str | None):
        """Insère une ligne Catégorie/ Valeur (— grisé si vide)."""
        row = self.infos_table.rowCount()
        self.infos_table.insertRow(row)

        cat = QTableWidgetItem(label)
        cat.setFont(QFont("Arial", 10, QFont.Bold))
        self.infos_table.setItem(row, 0, cat)

        val = QTableWidgetItem(value if value not in (None, "",) else "—")
        if value in (None, "",):
            val.setForeground(QColor("#9ca3af"))
        val.setFlags(val.flags() & ~Qt.ItemIsEditable)
        self.infos_table.setItem(row, 1, val)
    
    def _calculate_anciennete(self, date_eval):
        """Calcule l'ancienneté."""
        if date_eval is None:
            return "N/A"
        try:
            if isinstance(date_eval, str):
                date_obj = dt.datetime.strptime(date_eval, "%Y-%m-%d").date()
            elif hasattr(date_eval, "date"):
                date_obj = date_eval.date()
            else:
                date_obj = date_eval
            
            delta = dt.date.today() - date_obj
            years = delta.days // 365
            months = (delta.days % 365) // 30
            
            if years > 0:
                return f"{years} an(s) {months} mois"
            elif months > 0:
                return f"{months} mois"
            else:
                return f"{delta.days} jour(s)"
        except:
            return "N/A"


class GestionPersonnelDialog(QDialog):
    """
    Fenêtre principale de gestion du personnel.
    Affiche tous les opérateurs avec filtrage par statut.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion du Personnel")
        self.setGeometry(100, 100, 1000, 600)

        # Layout principal avec marges nulles
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Gestion du Personnel")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # === Header ===
        header = QLabel("Gestion du Personnel")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Vue complète de tous les opérateurs")
        subtitle.setStyleSheet("color: #6b7280; font-style: italic;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # === Filtres ===
        filters_group = QGroupBox("Filtres")
        filters_layout = QVBoxLayout()
        
        # Ligne 1 : Recherche
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Recherche :"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom ou prénom...")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input, 1)
        filters_layout.addLayout(search_layout)
        
        # Ligne 2 : Statut (Radio buttons)
        statut_layout = QHBoxLayout()
        statut_layout.addWidget(QLabel("Statut :"))
        
        self.radio_tous = QRadioButton("Tous")
        self.radio_actifs = QRadioButton("Actifs")
        self.radio_inactifs = QRadioButton("Inactifs")
        
        self.radio_tous.setChecked(True)
        
        self.radio_tous.toggled.connect(self.filter_table)
        self.radio_actifs.toggled.connect(self.filter_table)
        self.radio_inactifs.toggled.connect(self.filter_table)
        
        statut_layout.addWidget(self.radio_tous)
        statut_layout.addWidget(self.radio_actifs)
        statut_layout.addWidget(self.radio_inactifs)
        statut_layout.addStretch()
        
        self.show_stats_check = QCheckBox("Afficher les statistiques")
        self.show_stats_check.setChecked(True)
        self.show_stats_check.toggled.connect(self.toggle_stats_columns)
        statut_layout.addWidget(self.show_stats_check)
        
        self.refresh_btn = QPushButton("Actualiser")
        self.refresh_btn.clicked.connect(self.load_data)
        statut_layout.addWidget(self.refresh_btn)
        
        filters_layout.addLayout(statut_layout)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # === Table principale ===
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Nom", "Prénom", "Statut", "Nb Postes", "Niveau 1", "Niveau 2", "Niveau 3", "Niveau 4"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_detail_dialog)
        layout.addWidget(self.table, 1)
        
        # === Stats globales ===
        stats_label = QLabel("💡 Double-cliquez sur une ligne pour voir les détails complets")
        stats_label.setStyleSheet("color: #6b7280; font-style: italic; padding: 8px;")
        stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(stats_label)
        
        self.total_label = QLabel("Total : 0 opérateur(s)")
        self.total_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.total_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.total_label)
        
        # === Actions ===
        actions = QHBoxLayout()
        actions.addStretch()
        
        self.export_btn = QPushButton("Exporter la liste")
        self.export_btn.clicked.connect(self.export_list)
        actions.addWidget(self.export_btn)
        
        self.close_btn = QPushButton("Fermer")
        self.close_btn.clicked.connect(self.close)
        actions.addWidget(self.close_btn)
        
        layout.addLayout(actions)

        # Ajouter le widget de contenu au layout principal
        main_layout.addWidget(content_widget)

        # Charger les données
        self.all_data = []
        self.load_data()
    
    def load_data(self):
        """Charge tous les opérateurs avec leurs stats."""
        try:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            
            query = """
                SELECT 
                o.id,
                o.nom,
                o.prenom,
                UPPER(o.statut) AS statut,
                COUNT(p.id) AS nb_postes,
                SUM(CASE WHEN p.niveau = 1 THEN 1 ELSE 0 END) AS n1,
                SUM(CASE WHEN p.niveau = 2 THEN 1 ELSE 0 END) AS n2,
                SUM(CASE WHEN p.niveau = 3 THEN 1 ELSE 0 END) AS n3,
                SUM(CASE WHEN p.niveau = 4 THEN 1 ELSE 0 END) AS n4
            FROM personnel o
            LEFT JOIN polyvalence p ON o.id = p.operateur_id
            GROUP BY o.id, o.nom, o.prenom, o.statut
            ORDER BY o.nom, o.prenom;
            """
            
            cursor.execute(query)
            self.all_data = _rows(cursor, dict_mode)
            
            cursor.close()
            connection.close()
            
            self.filter_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données :\n{e}")
    
    def filter_table(self):
        """Filtre et affiche les données dans la table."""
        search_text = self.search_input.text().lower()
        
        # Déterminer le filtre de statut
        statut_filter = None
        if self.radio_actifs.isChecked():
            statut_filter = "ACTIF"
        elif self.radio_inactifs.isChecked():
            statut_filter = "INACTIF"
        
        self.table.setRowCount(0)
        
        count = 0
        count_actifs = 0
        count_inactifs = 0
        
        for data in self.all_data:
            nom = data.get("nom", "").lower()
            prenom = data.get("prenom", "").lower()
            statut = data.get("statut", "").upper()
            
            # Filtre de recherche
            if search_text and search_text not in nom and search_text not in prenom:
                continue
            
            # Filtre de statut
            if statut_filter and statut != statut_filter:
                continue
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Stocker l'ID et le statut en UserRole
            nom_item = QTableWidgetItem(data.get("nom", ""))
            nom_item.setData(Qt.UserRole, data.get("id"))
            nom_item.setData(Qt.UserRole + 1, statut)
            self.table.setItem(row, 0, nom_item)
            
            self.table.setItem(row, 1, QTableWidgetItem(data.get("prenom", "")))
            
            # Colonne Statut avec couleur
            statut_item = QTableWidgetItem(statut)
            statut_item.setTextAlignment(Qt.AlignCenter)
            if statut == "ACTIF":
                statut_item.setBackground(QColor("#d1fae5"))
                statut_item.setForeground(QColor("#065f46"))
                count_actifs += 1
            else:
                statut_item.setBackground(QColor("#fee2e2"))
                statut_item.setForeground(QColor("#991b1b"))
                count_inactifs += 1
            self.table.setItem(row, 2, statut_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(str(data.get("nb_postes", 0))))
            
            # Colonnes stats avec couleurs
            n1_item = QTableWidgetItem(str(data.get("n1", 0)))
            n1_item.setBackground(QColor("#fef2f2"))
            n1_item.setForeground(QColor("#dc2626"))
            n1_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, n1_item)
            
            n2_item = QTableWidgetItem(str(data.get("n2", 0)))
            n2_item.setBackground(QColor("#fffbeb"))
            n2_item.setForeground(QColor("#d97706"))
            n2_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, n2_item)
            
            n3_item = QTableWidgetItem(str(data.get("n3", 0)))
            n3_item.setBackground(QColor("#f0fdf4"))
            n3_item.setForeground(QColor("#059669"))
            n3_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, n3_item)
            
            n4_item = QTableWidgetItem(str(data.get("n4", 0)))
            n4_item.setBackground(QColor("#eff6ff"))
            n4_item.setForeground(QColor("#2563eb"))
            n4_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 7, n4_item)
            
            count += 1
        
        # Mise à jour du label total
        total_text = f"Total : {count} opérateur(s)"
        if self.radio_tous.isChecked():
            total_text += f" ({count_actifs} actifs, {count_inactifs} inactifs)"
        self.total_label.setText(total_text)
    
    def toggle_stats_columns(self, checked):
        """Affiche/masque les colonnes de statistiques."""
        for col in range(4, 8):  # Colonnes Nb Postes, N1, N2, N3, N4
            self.table.setColumnHidden(col, not checked)
    
    def open_detail_dialog(self):
        """Ouvre la fenêtre de détails pour l'opérateur sélectionné."""
        selected = self.table.selectedItems()
        if not selected:
            return
        
        operateur_id = selected[0].data(Qt.UserRole)
        statut = selected[0].data(Qt.UserRole + 1)
        nom = selected[0].text()
        prenom = selected[1].text()
        
        detail_dialog = DetailOperateurDialog(operateur_id, nom, prenom, statut, self)
        detail_dialog.operateur_status_changed.connect(self.on_operateur_status_changed)
        detail_dialog.exec_()
    
    def on_operateur_status_changed(self, operateur_id):
        """Callback quand le statut d'un opérateur est modifié."""
        self.load_data()
    
    def export_list(self):
        """Exporte la liste en Excel."""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from PyQt5.QtWidgets import QFileDialog
            
            # Déterminer le nom du fichier selon le filtre
            if self.radio_actifs.isChecked():
                default_name = f"operateurs_actifs_{dt.date.today().strftime('%Y%m%d')}.xlsx"
            elif self.radio_inactifs.isChecked():
                default_name = f"operateurs_inactifs_{dt.date.today().strftime('%Y%m%d')}.xlsx"
            else:
                default_name = f"personnel_complet_{dt.date.today().strftime('%Y%m%d')}.xlsx"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter la liste",
                default_name,
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Personnel"
            
            # En-têtes
            headers = ["Nom", "Prénom", "Statut", "Nb Postes", "Niveau 1", "Niveau 2", "Niveau 3", "Niveau 4"]
            ws.append(headers)
            
            # Style en-têtes
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")
            
            # Données (filtrées selon la vue actuelle)
            search_text = self.search_input.text().lower()
            statut_filter = None
            if self.radio_actifs.isChecked():
                statut_filter = "ACTIF"
            elif self.radio_inactifs.isChecked():
                statut_filter = "INACTIF"
            
            for data in self.all_data:
                nom = data.get("nom", "").lower()
                prenom = data.get("prenom", "").lower()
                statut = data.get("statut", "").upper()
                
                # Appliquer les mêmes filtres que la table
                if search_text and search_text not in nom and search_text not in prenom:
                    continue
                if statut_filter and statut != statut_filter:
                    continue
                
                ws.append([
                    data.get("nom", ""),
                    data.get("prenom", ""),
                    statut,
                    data.get("nb_postes", 0),
                    data.get("n1", 0),
                    data.get("n2", 0),
                    data.get("n3", 0),
                    data.get("n4", 0)
                ])
                
                # Colorer la colonne statut
                row_idx = ws.max_row
                statut_cell = ws.cell(row=row_idx, column=3)
                if statut == "ACTIF":
                    statut_cell.fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
                    statut_cell.font = Font(color="065F46", bold=True)
                else:
                    statut_cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                    statut_cell.font = Font(color="991B1B", bold=True)
                statut_cell.alignment = Alignment(horizontal="center")
            
            # Ajuster les largeurs
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            wb.save(file_path)
            
            QMessageBox.information(
                self, "Export réussi",
                f"Liste exportée avec succès !\n\n{file_path}"
            )
            
        except ImportError:
            QMessageBox.warning(
                self, "Module manquant",
                "Le module 'openpyxl' est requis pour l'export Excel.\n\n"
                "Installez-le avec : pip install openpyxl"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'exporter :\n{e}")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = GestionPersonnelDialog()
    dialog.show()
    sys.exit(app.exec_())