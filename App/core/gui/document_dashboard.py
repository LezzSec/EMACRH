"""
Dashboard des documents - Vue d'ensemble et alertes
Widget autonome affichant les statistiques globales de gestion documentaire
"""

import sys
import logging
from datetime import datetime, date

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QGroupBox, QGridLayout, QPushButton, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont

from core.db.configbd import get_connection
from core.services.document_service import DocumentService

logger = logging.getLogger(__name__)


class DocumentDashboard(QWidget):
    """Dashboard affichant les statistiques et alertes documentaires"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc_service = DocumentService()
        self.init_ui()
        self.load_data()
        
        # Rafraîchir toutes les 5 minutes
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(300000)  # 5 minutes
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("📊 Tableau de Bord - Gestion Documentaire")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # === Statistiques générales ===
        stats_group = QGroupBox("📈 Statistiques Générales")
        stats_layout = QGridLayout()
        
        self.label_total = self._create_stat_label("0", "Total de documents")
        self.label_actifs = self._create_stat_label("0", "Documents actifs", "#059669")
        self.label_expires = self._create_stat_label("0", "Documents expirés", "#dc2626")
        self.label_archives = self._create_stat_label("0", "Documents archivés", "#64748b")
        
        stats_layout.addWidget(self.label_total, 0, 0)
        stats_layout.addWidget(self.label_actifs, 0, 1)
        stats_layout.addWidget(self.label_expires, 0, 2)
        stats_layout.addWidget(self.label_archives, 0, 3)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # === Alertes d'expiration ===
        alert_group = QGroupBox("⚠️ Alertes - Documents expirant dans les 30 jours")
        alert_layout = QVBoxLayout()
        
        self.table_alerts = QTableWidget()
        self.table_alerts.setColumnCount(5)
        self.table_alerts.setHorizontalHeaderLabels([
            "Opérateur", "Document", "Catégorie", "Date d'expiration", "Jours restants"
        ])
        self.table_alerts.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_alerts.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_alerts.setAlternatingRowColors(True)
        self.table_alerts.horizontalHeader().setStretchLastSection(False)
        self.table_alerts.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_alerts.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        alert_layout.addWidget(self.table_alerts)
        alert_group.setLayout(alert_layout)
        layout.addWidget(alert_group)
        
        # === Documents par catégorie ===
        category_group = QGroupBox("📁 Répartition par Catégorie")
        category_layout = QVBoxLayout()
        
        self.table_categories = QTableWidget()
        self.table_categories.setColumnCount(3)
        self.table_categories.setHorizontalHeaderLabels([
            "Catégorie", "Nombre de documents", "Pourcentage"
        ])
        self.table_categories.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_categories.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_categories.setAlternatingRowColors(True)
        self.table_categories.horizontalHeader().setStretchLastSection(True)
        self.table_categories.setMaximumHeight(300)
        
        category_layout.addWidget(self.table_categories)
        category_group.setLayout(category_layout)
        layout.addWidget(category_group)
        
        # === Opérateurs avec le plus de documents ===
        operateur_group = QGroupBox("👥 Top 10 - Opérateurs avec le plus de documents")
        operateur_layout = QVBoxLayout()
        
        self.table_operateurs = QTableWidget()
        self.table_operateurs.setColumnCount(5)
        self.table_operateurs.setHorizontalHeaderLabels([
            "Opérateur", "Total docs", "Actifs", "Expirés", "Taille totale"
        ])
        self.table_operateurs.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_operateurs.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_operateurs.setAlternatingRowColors(True)
        self.table_operateurs.horizontalHeader().setStretchLastSection(True)
        self.table_operateurs.setMaximumHeight(300)
        
        operateur_layout.addWidget(self.table_operateurs)
        operateur_group.setLayout(operateur_layout)
        layout.addWidget(operateur_group)
        
        # === Boutons d'action ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_refresh = QPushButton("🔄 Actualiser")
        self.btn_refresh.clicked.connect(self.load_data)
        btn_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(btn_layout)
        
        # === Barre de statut ===
        self.status_label = QLabel("Chargement des données...")
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.status_label)
    
    def _create_stat_label(self, value: str, label: str, color: str = "#3b82f6") -> QWidget:
        """Crée un widget de statistique avec valeur et label"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Valeur
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        # Label
        text_label = QLabel(label)
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(text_label)
        
        container.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        
        # Stocker le label de valeur pour mise à jour ultérieure
        container.value_label = value_label
        
        return container
    
    def load_data(self):
        """Charge toutes les données du dashboard"""
        try:
            self.load_statistics()
            self.load_alerts()
            self.load_categories()
            self.load_top_operateurs()
            
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.status_label.setText(f"✅ Dernière mise à jour : {now}")
            
        except Exception as e:
            self.status_label.setText(f"❌ Erreur : {str(e)}")
    
    def load_statistics(self):
        """Charge les statistiques générales"""
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Total
            cursor.execute("SELECT COUNT(*) as total FROM documents")
            total = cursor.fetchone()['total']
            self.label_total.value_label.setText(str(total))
            
            # Par statut
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN statut = 'actif' THEN 1 ELSE 0 END) as actifs,
                    SUM(CASE WHEN statut = 'expire' THEN 1 ELSE 0 END) as expires,
                    SUM(CASE WHEN statut = 'archive' THEN 1 ELSE 0 END) as archives
                FROM documents
            """)
            stats = cursor.fetchone()
            
            self.label_actifs.value_label.setText(str(stats['actifs'] or 0))
            self.label_expires.value_label.setText(str(stats['expires'] or 0))
            self.label_archives.value_label.setText(str(stats['archives'] or 0))
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des statistiques: {e}")
    
    def load_alerts(self):
        """Charge les documents expirant bientôt"""
        try:
            docs = self.doc_service.get_documents_expiring_soon(jours=30)
            
            self.table_alerts.setRowCount(len(docs))
            
            for row, doc in enumerate(docs):
                # Opérateur
                self.table_alerts.setItem(row, 0, QTableWidgetItem(doc['operateur_nom']))
                
                # Document
                self.table_alerts.setItem(row, 1, QTableWidgetItem(doc['nom_affichage']))
                
                # Catégorie
                self.table_alerts.setItem(row, 2, QTableWidgetItem(doc['categorie_nom']))
                
                # Date d'expiration
                date_exp = doc['date_expiration']
                if isinstance(date_exp, str):
                    date_exp = datetime.strptime(date_exp, "%Y-%m-%d").date()
                date_str = date_exp.strftime("%d/%m/%Y")
                self.table_alerts.setItem(row, 3, QTableWidgetItem(date_str))
                
                # Jours restants avec couleur
                jours = doc['jours_restants']
                jours_item = QTableWidgetItem(f"{jours} jour(s)")
                
                if jours <= 7:
                    jours_item.setBackground(QColor("#fecaca"))
                    jours_item.setForeground(QColor("#991b1b"))
                elif jours <= 15:
                    jours_item.setBackground(QColor("#fed7aa"))
                    jours_item.setForeground(QColor("#9a3412"))
                else:
                    jours_item.setBackground(QColor("#fef3c7"))
                    jours_item.setForeground(QColor("#92400e"))
                
                self.table_alerts.setItem(row, 4, jours_item)
            
            self.table_alerts.resizeColumnsToContents()
            
            if len(docs) == 0:
                # Afficher un message si aucune alerte
                self.table_alerts.setRowCount(1)
                item = QTableWidgetItem("✅ Aucun document n'expire dans les 30 jours")
                item.setForeground(QColor("#059669"))
                item.setTextAlignment(Qt.AlignCenter)
                self.table_alerts.setItem(0, 0, item)
                self.table_alerts.setSpan(0, 0, 1, 5)
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des alertes: {e}")
    
    def load_categories(self):
        """Charge la répartition par catégorie"""
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    c.nom,
                    c.couleur,
                    COUNT(d.id) as count
                FROM categories_documents c
                LEFT JOIN documents d ON c.id = d.categorie_id AND d.statut = 'actif'
                GROUP BY c.id, c.nom, c.couleur
                ORDER BY count DESC
            """)
            categories = cursor.fetchall()
            
            # Calculer le total pour les pourcentages
            total = sum(cat['count'] for cat in categories)
            
            self.table_categories.setRowCount(len(categories))
            
            for row, cat in enumerate(categories):
                # Catégorie avec couleur
                cat_item = QTableWidgetItem(cat['nom'])
                if cat['couleur']:
                    cat_item.setBackground(QColor(cat['couleur'] + "20"))
                    cat_item.setForeground(QColor(cat['couleur']))
                self.table_categories.setItem(row, 0, cat_item)
                
                # Nombre
                self.table_categories.setItem(row, 1, QTableWidgetItem(str(cat['count'])))
                
                # Pourcentage
                if total > 0:
                    pct = (cat['count'] / total) * 100
                    pct_str = f"{pct:.1f}%"
                else:
                    pct_str = "0%"
                self.table_categories.setItem(row, 2, QTableWidgetItem(pct_str))
            
            self.table_categories.resizeColumnsToContents()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des catégories: {e}")
    
    def load_top_operateurs(self):
        """Charge le top 10 des opérateurs avec le plus de documents"""
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    operateur_nom,
                    total_documents,
                    documents_actifs,
                    documents_expires,
                    taille_totale_mo
                FROM v_documents_stats_operateur
                WHERE total_documents > 0
                ORDER BY total_documents DESC
                LIMIT 10
            """)
            operateurs = cursor.fetchall()
            
            self.table_operateurs.setRowCount(len(operateurs))
            
            for row, op in enumerate(operateurs):
                # Nom
                self.table_operateurs.setItem(row, 0, QTableWidgetItem(op['operateur_nom']))
                
                # Total
                self.table_operateurs.setItem(row, 1, QTableWidgetItem(str(op['total_documents'])))
                
                # Actifs
                actifs_item = QTableWidgetItem(str(op['documents_actifs']))
                actifs_item.setForeground(QColor("#059669"))
                self.table_operateurs.setItem(row, 2, actifs_item)
                
                # Expirés
                expires_item = QTableWidgetItem(str(op['documents_expires']))
                if op['documents_expires'] > 0:
                    expires_item.setForeground(QColor("#dc2626"))
                self.table_operateurs.setItem(row, 3, expires_item)
                
                # Taille
                taille = f"{op['taille_totale_mo']:.2f} Mo" if op['taille_totale_mo'] else "0 Mo"
                self.table_operateurs.setItem(row, 4, QTableWidgetItem(taille))
            
            self.table_operateurs.resizeColumnsToContents()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des opérateurs: {e}")


# ============================================================================
# APPLICATION STANDALONE POUR TESTER
# ============================================================================

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dashboard = DocumentDashboard()
    dashboard.setWindowTitle("Dashboard - Gestion Documentaire")
    dashboard.resize(1200, 800)
    dashboard.show()
    
    sys.exit(app.exec_())