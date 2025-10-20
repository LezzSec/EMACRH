import sys, os, datetime as dt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QListWidget, QScrollArea,
    QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QMessageBox, QFrame 
)
from PyQt5.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QEvent 
from PyQt5.QtGui import QDesktopServices, QIcon
from core.gui.ui_theme import EmacTheme, EmacDarkTheme, EmacButton, EmacCard, EmacHeader, EmacStatusCard 
from .liste_et_grilles import GrillesDialog
from core.gui.creation_modification_poste import CreationModificationPosteDialog
from core.gui.liste_personnel import ListePersonnelDialog
from core.gui.manage_operateur import ManageOperatorsDialog
from core.gui.historique import HistoriqueDialog
from core.gui.gestion_evaluation import GestionEvaluationDialog
from core.gui.evaluation_calendar import EvaluationCalendarDialog
from core.gui.operateurs_inactifs import OperateursInactifsDialog
from core.gui.regularisation import RegularisationDialog
from core.db.configbd import get_connection as get_db_connection
from core.gui.ui_theme import (
    EmacTheme, EmacDarkTheme, EmacButton, EmacCard, EmacHeader, EmacStatusCard, 
    HamburgerButton, get_current_theme 
) 


try:
    from core.services.log_exporter import export_day
except ImportError:
    export_day = None


class MainWindow(QMainWindow):
    DRAWER_WIDTH = 280

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion du Personnel")
        self.setGeometry(80, 80, 1180, 720)
        
        # État initial du thème
        self.current_theme = EmacTheme

        # État initial du Drawer et Event Filter 
        self.is_drawer_open = False
        self.installEventFilter(self) 

        # ---------- Widget central + layout principal ----------
        rootw = QWidget(); self.setCentralWidget(rootw)
        root = QGridLayout(rootw)
        root.setContentsMargins(18, 18, 18, 18)
        root.setHorizontalSpacing(18)
        root.setVerticalSpacing(18)
        rootw.setLayout(root)

        # =====================
        # Colonne gauche – cartes neutres (Rendues self. pour rebuild_status_cards)
        # =====================
        left = QVBoxLayout(); left.setSpacing(18)

        self.retard_card = EmacStatusCard("Retard Évaluations", variant='danger')
        self.retard_filter = QComboBox(); self.retard_filter.addItem("Tous les postes", "")
        self.retard_filter.currentIndexChanged.connect(self.load_evaluations)
        self.retard_scroll, self.retard_list = self.create_scrollable_list()
        self.retard_card.body.addWidget(self.retard_filter)
        self.retard_card.body.addWidget(self.retard_scroll)
        left.addWidget(self.retard_card)

        self.next_card = EmacStatusCard("Prochaines Évaluations", variant='success', subtitle="10 prochaines")
        self.next_eval_filter = QComboBox(); self.next_eval_filter.addItem("Tous les postes", "")
        self.next_eval_filter.currentIndexChanged.connect(self.load_evaluations)
        self.next_eval_scroll, self.next_eval_list = self.create_scrollable_list()
        self.next_card.body.addWidget(self.next_eval_filter)
        self.next_card.body.addWidget(self.next_eval_scroll)
        left.addWidget(self.next_card)

        root.addLayout(left, 0, 0, 2, 1)

        # =====================
        # Colonne droite – header + actions
        # =====================
        right = QVBoxLayout(); right.setSpacing(18)

        # Header avec menu burger discret
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(12)
        
        # Titre
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        h1 = QLabel("Gestion du Personnel")
        h1.setProperty('class', 'h1')
        title_layout.addWidget(h1)
        header_layout.addLayout(title_layout, 1)
        
        # Menu burger à droite (Connecté au Drawer)
        # MODIFICATION: HamburgerButton n'a plus la couleur bleue (voir ui_theme.py)
        self.menu_btn = HamburgerButton(self, variant="default") # 'default' pour un style non primaire
        self.menu_btn.setToolTip("Menu")
        self.menu_btn.clicked.connect(self.toggle_drawer) 
        header_layout.addWidget(self.menu_btn, 0, Qt.AlignRight | Qt.AlignVCenter)
        
        right.addWidget(header_widget)

        
        # Actions rapides
        self.actions_wrap = EmacCard() 
        title = QLabel("Actions rapides"); title.setProperty('class','h2')
        self.actions_wrap.body.addWidget(title)

        # AMÉLIORATION VISUELLE: Boutons secondaires en 'ghost'
        rows = QVBoxLayout(); rows.setSpacing(8)
        r1 = QHBoxLayout(); b1 = EmacButton("Liste du Personnel", 'primary'); b1.clicked.connect(self.show_liste_personnel); r1.addWidget(b1)
        r2 = QHBoxLayout(); b2 = EmacButton("Liste et Grilles", 'ghost'); b2.clicked.connect(self.show_listes_grilles_dialog); r2.addWidget(b2)
        r3 = QHBoxLayout(); b3 = EmacButton("Gestion des Évaluations", 'ghost'); b3.clicked.connect(self.show_gestion_evaluations); r3.addWidget(b3)
        r4 = QHBoxLayout(); b4 = EmacButton("Régularisation Opérateur", 'ghost'); b4.clicked.connect(self.show_regularisation); r4.addWidget(b4)
        r5 = QHBoxLayout(); b5 = EmacButton("Quitter", 'ghost'); b5.clicked.connect(self.close); r5.addWidget(b5)
        for r in (r1, r2, r3, r4, r5):
            rows.addLayout(r)
        self.actions_wrap.body.addLayout(rows)
        right.addWidget(self.actions_wrap)


        root.addLayout(right, 0, 1)
        
        # =====================
        # Menu Latéral (Drawer) 
        # =====================
        self.create_drawer()

        # --- Data init ---
        self.populate_filters()
        self.load_evaluations()

    # ================= Filtre d'événements pour clic extérieur =================
    def eventFilter(self, source, event):
        """
        Filtre les événements de clic de souris pour fermer le menu latéral 
        s'il est ouvert et que l'événement ne provient pas du menu ou du bouton menu.
        """
        if self.is_drawer_open and event.type() == QEvent.MouseButtonPress:
            # Vérifie si le clic est en dehors du drawer
            if not self.drawer.geometry().contains(self.mapFromGlobal(event.globalPos())):
                # Assurez-vous que le clic ne vient pas du bouton menu lui-même
                if source is not self.menu_btn:
                    self.toggle_drawer()
                    return True  # L'événement est consommé, empêchant la propagation
        return super().eventFilter(source, event)


    # ================= Menu Latéral (Drawer) =================
    def create_drawer(self):
        """Crée et initialise le menu latéral coulissant."""
        if hasattr(self, 'drawer'):
            self.drawer.deleteLater() 
            del self.drawer
            
        self.drawer = QFrame(self)
        self.drawer.setObjectName("card")
        
        # MODIFICATION: L'ombre du drawer est supprimée ici aussi.
        # apply_soft_shadow(self.drawer, radius=22, alpha=36)
        
        self.drawer.setFixedSize(self.DRAWER_WIDTH, self.height())
        
        # Style pour le drawer. Utilise self.current_theme.
        ThemeCls = self.current_theme
        border_color = ThemeCls.BDR
        bg_card = ThemeCls.BG_CARD
        
        # Le style du drawer est hérité de QFrame#card, mais on force border-left et border-radius
        self.drawer.setStyleSheet(f"""
            QFrame#card {{
                background: {bg_card};
                border-left: 1px solid {border_color};
                border-top: 1px solid {border_color};
                border-bottom: 1px solid {border_color};
                border-right: 0px; /* S'assure qu'il n'y a pas de bordure à droite */
                border-top-left-radius: 0px; 
                border-bottom-left-radius: 0px;
                border-top-right-radius: 14px; 
                border-bottom-right-radius: 14px;
            }}
        """)
        
        # Initialise la position et l'état
        self.is_drawer_open = getattr(self, 'is_drawer_open', False)
        
        # Calcule la position idéale (ouverte ou fermée) en fonction de la taille actuelle de la fenêtre
        current_x = self.width() - self.DRAWER_WIDTH if self.is_drawer_open else self.width()
        
        # Force le déplacement du nouveau Drawer à la bonne position (essentiel après recréation)
        self.drawer.move(current_x, 0)
        self.drawer.updateGeometry() 
        
        # Cache par défaut si fermé
        if not self.is_drawer_open:
             self.drawer.hide()
        
        # Layout du Drawer
        drawer_layout = QVBoxLayout(self.drawer)
        drawer_layout.setContentsMargins(16, 16, 16, 16)
        drawer_layout.setAlignment(Qt.AlignTop)
        
        # Titre dans le Drawer
        title = QLabel("Menu")
        title.setProperty('class', 'h2')
        drawer_layout.addWidget(title)
        drawer_layout.addSpacing(15)

        
        # Ajout des boutons dans le Drawer
        self.add_drawer_button(drawer_layout, "Changer de Thème (Light/Dark)", self.toggle_theme, 'primary')
        drawer_layout.addSpacing(15)
        self.add_drawer_button(drawer_layout, "Ajouter un opérateur", self.show_manage_operator, 'ghost')
        self.add_drawer_button(drawer_layout, "Création/Suppression de poste", self.show_poste_form, 'ghost')
        self.add_drawer_button(drawer_layout, "Historique", self.show_historique, 'ghost')
        self.add_drawer_button(drawer_layout, "Calendrier", self.show_calendrier_evaluations, 'ghost')
        self.add_drawer_button(drawer_layout, "Opérateurs Inactifs", self.show_operateurs_inactifs, 'ghost')
        
        if export_day:
            self.add_drawer_button(drawer_layout, "Exporter les logs", self.export_logs_today, 'ghost')

        drawer_layout.addStretch(1)



    def add_drawer_button(self, layout: QVBoxLayout, text: str, action: callable, variant: str = None):
        """Ajoute un bouton de menu au layout du Drawer."""
        btn = EmacButton(text, variant=variant)
        btn.setFixedHeight(44)
        btn.clicked.connect(action)
        # Ferme le drawer après l'action 
        if action not in (self.close, self.export_logs_today, self.toggle_theme):
            btn.clicked.connect(self.toggle_drawer)
        layout.addWidget(btn)

    def _recreate_drawer_safe(self):
        """
        Méthode intermédiaire pour recréer le drawer et forcer 
        le rafraîchissement visuel après un changement de thème.
        """
        self.create_drawer()
        
        # On force la mise à jour des layouts et le rafraîchissement
        self.centralWidget().update()
        self.update()
        
    def toggle_theme(self):
        """Bascule entre le thème clair et le thème sombre."""
        # 1. Détermine le nouveau thème
        new_theme = EmacDarkTheme if self.current_theme == EmacTheme else EmacTheme
        self.current_theme = new_theme
        
        # 2. Applique le nouveau thème
        new_theme.apply(QApplication.instance())
        
        # 3. Recrée les widgets qui dépendent des couleurs (StatusCard/Drawer)
        self.rebuild_status_cards()
        
        # 4. Utilise QTimer.singleShot pour appeler la fonction de recréation sécurisée. 
        # C'est la solution stable aux conflits de géométrie.
        QTimer.singleShot(50, self._recreate_drawer_safe) 

    def rebuild_status_cards(self):
        """
        Recrée les EmacStatusCard pour appliquer les couleurs pastel du nouveau thème.
        """
        
        main_layout = self.centralWidget().layout().itemAtPosition(0, 0).layout()
        
        # --- GESTION DES RETARDS ---
        # NOTE: On utilise takeAt(0).widget() pour retirer les widgets enfants sans les détruire
        # Le 0 est le filtre, le 1 est le QScrollArea (liste)
        retard_filter_widget = self.retard_card.body.takeAt(0).widget() 
        retard_scroll_widget = self.retard_card.body.takeAt(0).widget() 

        main_layout.removeWidget(self.retard_card)
        self.retard_card.deleteLater()

        # RECREATION de la carte SANS ombre ni bordure colorée (maintenant géré par EmacStatusCard)
        self.retard_card = EmacStatusCard("Retard Évaluations", variant='danger') 
        main_layout.insertWidget(0, self.retard_card)
        self.retard_card.body.addWidget(retard_filter_widget)
        self.retard_card.body.addWidget(retard_scroll_widget)
        
        # --- GESTION DES PROCHAINES ÉVALUATIONS ---
        next_filter_widget = self.next_card.body.takeAt(0).widget() 
        next_scroll_widget = self.next_card.body.takeAt(0).widget() 

        main_layout.removeWidget(self.next_card)
        self.next_card.deleteLater()

        # RECREATION de la carte SANS ombre ni bordure colorée
        self.next_card = EmacStatusCard("Prochaines Évaluations", variant='success', subtitle="10 prochaines")
        main_layout.insertWidget(1, self.next_card)
        self.next_card.body.addWidget(next_filter_widget)
        self.next_card.body.addWidget(next_scroll_widget)
        
        self.load_evaluations()

    
    def resizeEvent(self, event):
        """Met à jour la taille et la position du Drawer au redimensionnement."""
        super().resizeEvent(event)
        if hasattr(self, 'drawer'):
            self.drawer.setFixedHeight(self.height())
            
            current_x = self.width() - self.DRAWER_WIDTH if self.is_drawer_open else self.width()
            self.drawer.move(current_x, 0)
    
    
    def toggle_drawer(self):
        """Anime l'ouverture et la fermeture du menu latéral."""
        self.is_drawer_open = not self.is_drawer_open
        
        end_x = self.width() - self.DRAWER_WIDTH if self.is_drawer_open else self.width()
        
        self.animation = QPropertyAnimation(self.drawer, b"pos")
        self.animation.setDuration(250) 
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.animation.setStartValue(self.drawer.pos())
        self.animation.setEndValue(QPoint(end_x, 0))
        
        if self.is_drawer_open:
            self.drawer.show() 
            self.drawer.raise_()
            try: self.animation.finished.disconnect()
            except: pass
        else:
            try: self.animation.finished.disconnect()
            except: pass
            self.animation.finished.connect(self.drawer.hide)

        self.animation.start()


    def create_scrollable_list(self):
        sc = QScrollArea(); sc.setWidgetResizable(True)
        lw = QListWidget(); sc.setWidget(lw)
        return sc, lw

    # ================= Fenêtres secondaires =================
    def show_liste_personnel(self):
        ListePersonnelDialog(self).exec_()
    def show_manage_operator(self):
        ManageOperatorsDialog().exec_()
    def show_gestion_evaluations(self):
        GestionEvaluationDialog().exec_()
    def show_listes_grilles_dialog(self):
        GrillesDialog().exec_()
    def show_poste_form(self):
        CreationModificationPosteDialog().exec_()
    def show_historique(self):
        HistoriqueDialog().exec_()
    def show_calendrier_evaluations(self):
        EvaluationCalendarDialog(self).exec_()
    def show_regularisation(self):
        RegularisationDialog(self).exec_()
    def show_operateurs_inactifs(self):
        OperateursInactifsDialog(self).exec_()

    # ================= Données / DB (Fonctions inchangées) =================
    def populate_filters(self):
        conn = get_db_connection(); cur = conn.cursor()
        try:
            cur.execute("SELECT DISTINCT poste_code FROM postes ORDER BY poste_code;")
            for (poste,) in cur.fetchall():
                # Vérifie si l'élément existe déjà pour éviter le doublon (cas rare)
                if self.retard_filter.findData(poste) == -1: 
                    self.retard_filter.addItem(poste, poste)
                    self.next_eval_filter.addItem(poste, poste)
        finally:
            cur.close(); conn.close()
            
    def load_evaluations(self):
        conn = get_db_connection(); cur = conn.cursor()
        try:
            poste_retard = self.retard_filter.currentData()
            poste_next = self.next_eval_filter.currentData()
    
            # --------------------
            # Retards (opérateurs Actifs uniquement)
            # --------------------
            q1 = """
                SELECT o.nom, o.prenom, p.poste_code, poly.prochaine_evaluation
                FROM polyvalence poly
                JOIN operateurs o ON o.id = poly.operateur_id
                LEFT JOIN postes p ON p.id = poly.poste_id
                WHERE poly.prochaine_evaluation < CURDATE()
                  AND o.statut = 'Actif'
            """
            pr = []
            if poste_retard:
                q1 += " AND p.poste_code = %s"
                pr.append(poste_retard)
            q1 += " ORDER BY poly.prochaine_evaluation ASC"
            cur.execute(q1, tuple(pr))
            retard = cur.fetchall()
    
            # --------------------
            # Prochaines (opérateurs Actifs uniquement, limité à 10)
            # --------------------
            q2 = """
                SELECT o.nom, o.prenom, p.poste_code, poly.prochaine_evaluation
                FROM polyvalence poly
                JOIN operateurs o ON o.id = poly.operateur_id
                LEFT JOIN postes p ON p.id = poly.poste_id
                WHERE poly.prochaine_evaluation >= CURDATE()
                  AND o.statut = 'Actif'
            """
            pn = []
            if poste_next:
                q2 += " AND p.poste_code = %s"
                pn.append(poste_next)
            q2 += " ORDER BY poly.prochaine_evaluation ASC LIMIT 10"
            cur.execute(q2, tuple(pn))
            prochaines = cur.fetchall()
    
            # --------------------
            # Rendu UI
            # --------------------
            self.retard_list.clear()
            for nom, prenom, poste, date_ev in retard:
                date_txt = date_ev.strftime('%d/%m/%Y') if hasattr(date_ev, 'strftime') else str(date_ev)
                self.retard_list.addItem(f"{nom} {prenom} · {poste or ''}  —  Retard: {date_txt}")
    
            self.next_eval_list.clear()
            for nom, prenom, poste, date_ev in prochaines:
                date_txt = date_ev.strftime('%d/%m/%Y') if hasattr(date_ev, 'strftime') else str(date_ev)
                self.next_eval_list.addItem(f"{nom} {prenom} · {poste or ''}  —  Prévu: {date_txt}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec du chargement des évaluations : {e}")
        finally:
            cur.close(); conn.close()

    # ================= Export (Fonction inchangée) =================
    def export_logs_today(self):
        if not export_day:
            QMessageBox.warning(self, "Non disponible", "Module d'export non chargé.")
            return
        try:
            paths = export_day(dt.date.today(), base_dir="logs", make_zip=False)
            dossier = os.path.dirname(paths["csv"])
            QMessageBox.information(self, "Export", f"Export terminé ✅\n\nCSV : {paths['csv']}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(dossier))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Export impossible : {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    EmacTheme.apply(app)
    win = MainWindow(); win.show()
    sys.exit(app.exec_())