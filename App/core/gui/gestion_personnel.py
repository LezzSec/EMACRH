# gestion_personnel.py – Gestion complète du personnel (actifs et inactifs)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QGroupBox,
    QMessageBox, QAbstractItemView, QWidget, QTextEdit, QTabWidget, QCheckBox,
    QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from core.db.configbd import get_connection as get_db_connection
from core.services.logger import log_hist

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
        
        layout = QVBoxLayout(self)
        
        # === Header avec infos opérateur ===
        header = QLabel(f"{nom} {prenom}")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        status_label = QLabel(f"Statut : {self.current_statut}")
        if self.current_statut == "ACTIF":
            status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
        else:
            status_label.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 14px;")
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)
        
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
        
        # Onglet 2 : Résumé / Notes
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        summary_label = QLabel("Résumé du Parcours")
        summary_label.setFont(QFont("Arial", 12, QFont.Bold))
        summary_layout.addWidget(summary_label)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        tabs.addTab(summary_tab, "Résumé")
        
        # Onglet 3 : Infos Complémentaires (NOUVELLE CATÉGORIE)
        infos_tab = QWidget()
        infos_layout = QVBoxLayout(infos_tab)
        
        infos_label = QLabel("Informations Complémentaires")
        infos_label.setFont(QFont("Arial", 12, QFont.Bold))
        infos_layout.addWidget(infos_label)
        
        self.infos_table = QTableWidget()
        self.infos_table.setColumnCount(2)
        self.infos_table.setHorizontalHeaderLabels(["Catégorie", "Valeur"])
        self.infos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.infos_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        infos_layout.addWidget(self.infos_table)

        self.infos_table.setShowGrid(False)
        self.infos_table.verticalHeader().setVisible(False)
        self.infos_table.setAlternatingRowColors(True)
        self.infos_table.setStyleSheet("""
        QHeaderView::section{
            background:#f1f5f9; color:#374151; font-weight:600; border:0; padding:6px 8px;
        }
        QTableWidget{
            background:#ffffff; alternate-background-color:#f9fafb;
        }
        QTableWidget::item{
            padding:8px;
        }
        QTableWidget::item:selected{
            background:#e0f2fe; color:#111827;
        }
        """)
        
        tabs.addTab(infos_tab, "Infos Complémentaires")
        
        # Onglet 4 : Historique des modifications
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        
        history_label = QLabel("Historique")
        history_label.setFont(QFont("Arial", 12, QFont.Bold))
        history_layout.addWidget(history_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Date", "Action", "Description"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        history_layout.addWidget(self.history_table)
        
        tabs.addTab(history_tab, "Historique")
        
        layout.addWidget(tabs, 1)
        
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
        self.load_summary()
        self.load_additional_infos() # <--- AJOUT : Chargement des nouvelles infos
        self.load_history()
    
    def load_additional_infos(self):
        try:
            self.infos_table.setRowCount(0)

            # -------- Section: Informations personnelles --------
            self._insert_section("Informations personnelles")
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            cursor.execute("SELECT * FROM operateur_infos WHERE operateur_id = %s", (self.operateur_id,))
            row_data = _rows(cursor, dict_mode)
            cursor.close(); connection.close()

            if row_data:
                data = row_data[0]
                showed = False
                for key, val in data.items():
                    if key == "operateur_id":
                        continue
                    label = format_column_name(key)
                    value = val.strftime("%d/%m/%Y") if isinstance(val, dt.date) else (str(val) if val not in (None, "",) else None)
                    if value is not None:
                        self._insert_kv(label, value); showed = True
                if not showed:
                    self._insert_kv("—", None)
            else:
                self._insert_kv("—", None)

            # -------- Section: Contrat actuel --------
            self._insert_section("Contrat actuel")
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
                    fin = d2.strftime("%d/%m/%Y") if isinstance(d2, dt.date) else (str(d2) if d2 else "…")
                    parts.append(f"{deb} → {fin}")
                self._insert_kv("Contrat", " — ".join([p for p in parts if p]))
            else:
                self._insert_kv("Contrat", None)

            # -------- Section: Solde congés (année) --------
            self._insert_section("Solde congés (année)")
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            cursor.execute("""
                SELECT cp_acquis, cp_pris, cp_restant, rtt_acquis, rtt_pris, rtt_restant
                FROM compteur_conges
                WHERE operateur_id = %s AND annee = YEAR(CURDATE())
            """, (self.operateur_id,))
            solde = _rows(cursor, dict_mode)
            cursor.close(); connection.close()

            if solde:
                s = solde[0]
                self._insert_kv("CP", f"{s.get('cp_restant',0)} j restants (pris {s.get('cp_pris',0)}/{s.get('cp_acquis',0)} acquis)")
                self._insert_kv("RTT", f"{s.get('rtt_restant',0)} j restants (pris {s.get('rtt_pris',0)})")
            else:
                self._insert_kv("CP", None)
                self._insert_kv("RTT", None)

            # -------- Section: Absences récentes --------
            self._insert_section("Absences récentes")
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            cursor.execute("""
                SELECT type_absence, date_debut, date_fin, statut
                FROM absences_conges
                WHERE operateur_id = %s
                ORDER BY date_debut DESC LIMIT 6
            """, (self.operateur_id,))
            absences = _rows(cursor, dict_mode)
            cursor.close(); connection.close()

            if absences:
                for a in absences:
                    d1 = self._format_date(a.get("date_debut"))
                    d2 = self._format_date(a.get("date_fin"))
                    self._insert_kv(a.get("type_absence","(type)"), f"{d1} → {d2} — {a.get('statut','')}")
            else:
                self._insert_kv("—", None)

            # -------- Section: Formations --------
            self._insert_section("Formations")
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

            if formations:
                for f in formations:
                    d1 = self._format_date(f.get("date_debut"))
                    d2 = self._format_date(f.get("date_fin"))
                    cert = "✅" if f.get("certificat_obtenu") else "—"
                    self._insert_kv(f.get("intitule","(formation)"), f"{d1} → {d2} — {f.get('statut','')} {cert}")
            else:
                self._insert_kv("—", None)

            # -------- Section: Validités --------
            self._insert_section("Validités")
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

            if validites:
                for v in validites:
                    d1 = self._format_date(v.get("date_debut"))
                    d2 = self._format_date(v.get("date_fin")) if v.get("date_fin") else "—"
                    tc = f" ({v['taux_incapacite']}%)" if v.get("taux_incapacite") is not None else ""
                    self._insert_kv(v.get("type_validite","(type)"), f"{d1} → {d2} — {v.get('periodicite','')}{tc}")
            else:
                self._insert_kv("—", None)

            # largeur colonnes
            self.infos_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.infos_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        except Exception as e:
            QMessageBox.critical(self, "Erreur de chargement",
                                 f"Impossible de charger les infos détaillées :\n{e}")


    
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
                    statut_item.setText("N/A")
                
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
    
    def load_summary(self):
        """Génère un résumé textuel du parcours."""
        try:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            
            # Récupérer les infos
            cursor.execute(
                "SELECT nom, prenom, statut FROM operateurs WHERE id = %s",
                (self.operateur_id,)
            )
            op = cursor.fetchone()
            
            if not op:
                return
            
            nom = op["nom"] if dict_mode else op[0]
            prenom = op["prenom"] if dict_mode else op[1]
            statut = op["statut"] if dict_mode else op[2]
            
            # Statistiques
            cursor.execute(
                """SELECT COUNT(*) as total, 
                   SUM(CASE WHEN niveau = 1 THEN 1 ELSE 0 END) as n1,
                   SUM(CASE WHEN niveau = 2 THEN 1 ELSE 0 END) as n2,
                   SUM(CASE WHEN niveau = 3 THEN 1 ELSE 0 END) as n3,
                   SUM(CASE WHEN niveau = 4 THEN 1 ELSE 0 END) as n4,
                   MIN(date_evaluation) as premiere_eval,
                   MAX(date_evaluation) as derniere_eval
                   FROM polyvalence WHERE operateur_id = %s""",
                (self.operateur_id,)
            )
            stats = cursor.fetchone()
            
            if dict_mode:
                total = stats["total"]
                n1, n2, n3, n4 = stats["n1"], stats["n2"], stats["n3"], stats["n4"]
                premiere = stats["premiere_eval"]
                derniere = stats["derniere_eval"]
            else:
                total = stats[0]
                n1, n2, n3, n4 = stats[1], stats[2], stats[3], stats[4]
                premiere = stats[5]
                derniere = stats[6]
            
            cursor.close()
            connection.close()
            
            # Générer le résumé
            summary = f"""
═══════════════════════════════════════════════════
  PROFIL : {nom} {prenom}
═══════════════════════════════════════════════════

📊 STATISTIQUES GÉNÉRALES
─────────────────────────────────────────────────
• Statut actuel : {statut.upper()}
• Nombre total de postes occupés : {total}
• Répartition des niveaux :
  - Niveau 1 : Opérateur nouveau à encadrer par titulaire N3/4 ou absent du poste depuis plus de 12 mois. (< 80%)     : {n1} poste(s)
  - Niveau 2 : Opérateur formé et apte à conduire le poste seul. Certaines notions sont en cours d'acquisition. (> 80%)     : {n2} poste(s)
  - Niveau 3 : Opérateur titulaire, formé, apte à conduire le poste et apte à former. (> 90%)       : {n3} poste(s)
  - Niveau 4 : N3 + Leader ou Polyvalent (maîtrise 3 postes d'une ligne : mél. interne, cylindres, conditionnement) (> 90%)     : {n4} poste(s)

📅 PÉRIODE D'ACTIVITÉ
─────────────────────────────────────────────────
• Première évaluation : {self._format_date(premiere)}
• Dernière évaluation : {self._format_date(derniere)}

⭐ POINTS FORTS
─────────────────────────────────────────────────
"""
            
            if n4 > 0:
                summary += f"• {n4} poste(s) maîtrisé(s) au niveau Référent (N4)\n"
            if n3 > 0:
                summary += f"• {n3} poste(s) maîtrisé(s) au niveau Expert (N3)\n"
            
            if n3 + n4 >= 3:
                summary += "• Opérateur polyvalent (3+ postes de niveau 3/4)\n"
            
            if statut.upper() == "INACTIF":
                summary += """
💡 REMARQUES
─────────────────────────────────────────────────
L'opérateur est actuellement INACTIF.
Toutes ses compétences et évaluations sont conservées
dans le système pour référence future.

Vous pouvez réactiver cet opérateur à tout moment
en cliquant sur le bouton "Réactiver l'opérateur".
"""
            else:
                summary += """
💡 REMARQUES
─────────────────────────────────────────────────
L'opérateur est actuellement ACTIF et disponible
pour les affectations de poste.
"""
            
            self.summary_text.setPlainText(summary)
            
        except Exception as e:
            self.summary_text.setPlainText(f"Erreur lors du chargement du résumé :\n{e}")
    
    def load_history(self):
        """Charge l'historique des modifications."""
        try:
            connection = get_db_connection()
            cursor, dict_mode = _cursor(connection)
            
            cursor.execute(
                """SELECT date_time, action, description 
                   FROM historique 
                   WHERE operateur_id = %s 
                   ORDER BY date_time DESC 
                   LIMIT 50""",
                (self.operateur_id,)
            )
            rows = _rows(cursor, dict_mode)
            
            cursor.close()
            connection.close()
            
            self.history_table.setRowCount(0)
            
            for r in rows:
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)
                
                date_str = self._format_datetime(r.get("date_time"))
                action = r.get("action", "")
                desc = r.get("description", "")
                
                self.history_table.setItem(row, 0, QTableWidgetItem(date_str))
                self.history_table.setItem(row, 1, QTableWidgetItem(action))
                self.history_table.setItem(row, 2, QTableWidgetItem(desc))
            
        except Exception as e:
            QMessageBox.warning(self, "Historique", f"Impossible de charger l'historique :\n{e}")
    
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
            
            cursor.execute(
                "UPDATE operateurs SET statut = %s WHERE id = %s",
                (new_statut, self.operateur_id)
            )
            
            connection.commit()
            cursor.close()
            connection.close()
            
            self.current_statut = new_statut
            self.update_status_button()
            
            QMessageBox.information(
                self, "Statut modifié",
                f"Le statut de l'opérateur a été changé à {new_statut} avec succès !"
            )
            
            self.operateur_status_changed.emit(self.operateur_id)
            self.load_summary()  # Recharger le résumé pour mettre à jour le statut
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de modifier le statut :\n{e}")

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
                    FROM operateurs WHERE id=%s
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
    
            # ---------- Traiter le résumé ----------
            resume_raw = self.summary_text.toPlainText() if hasattr(self, "summary_text") else ""
            resume_clean = _clean_text(resume_raw)
            sections_data = _parse_section(resume_clean)
            
            # Afficher chaque section du résumé
            for section_title, items in sections_data.items():
                flow.append(Paragraph(section_title, section_style))
                
                for item in items:
                    if ':' in item:
                        # Format clé : valeur
                        parts = item.split(':', 1)
                        key = parts[0].strip()
                        value = parts[1].strip() if len(parts) > 1 else ""
                        text = f"<b>{key}</b> : {value}"
                        flow.append(Paragraph(text, body_style))
                    else:
                        # Item de liste
                        flow.append(Paragraph(f"• {item}", bullet_style))
                
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
                cur.execute("SELECT nom, prenom, COALESCE(matricule,'-'), UPPER(statut) FROM operateurs WHERE id=%s", (self.operateur_id,))
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
    
            # Sous-titre de section
            ws1["A4"] = "Résumé du parcours"
            ws1["A4"].font = Font(bold=True)
            ws1["A4"].fill = SEC_FILL
            ws1["A4"].alignment = LEFT
    
            # Contenu (wrap), sur A..S
            ws1.merge_cells("A5:S5")
            resume_txt = (self.summary_text.toPlainText().strip() if hasattr(self, "summary_text") else "") or "—"
            ws1["A5"] = resume_txt
            ws1["A5"].alignment = LEFT_WRAP
    
            # Hauteur auto suffisante pour voir tout le bloc résumé
            set_wrapped_row_height(ws1, 5, wide_cols)
    
            ws1.freeze_panes = "A6"
    
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
        
        layout = QVBoxLayout(self)
        
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
                    UPPER(o.statut) as statut,
                    COUNT(p.id) as nb_postes,
                    SUM(CASE WHEN p.niveau = 1 THEN 1 ELSE 0 END) as n1,
                    SUM(CASE WHEN p.niveau = 2 THEN 1 ELSE 0 END) as n2,
                    SUM(CASE WHEN p.niveau = 3 THEN 1 ELSE 0 END) as n3,
                    SUM(CASE WHEN p.niveau = 4 THEN 1 ELSE 0 END) as n4
                FROM operateurs o
                LEFT JOIN polyvalence p ON o.id = p.operateur_id
                GROUP BY o.id, o.nom, o.prenom, o.statut
                ORDER BY o.nom, o.prenom
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