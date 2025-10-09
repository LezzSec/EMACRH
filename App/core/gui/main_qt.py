import sys, os, datetime as dt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QListWidget, QScrollArea,
    QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QAction, QMessageBox, QMenu
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices

# Thème clair + cartes pastel
from core.gui.ui_theme import EmacTheme, EmacButton, EmacCard, EmacHeader, EmacStatusCard

# Modules applicatifs (inchangés)
from core.gui.liste_et_grilles import GrillesDialog
from core.gui.creation_modification_poste import CreationModificationPosteDialog
from core.gui.liste_personnel import ListePersonnelDialog
from core.gui.manage_operateur import ManageOperatorsDialog
from core.gui.historique import HistoriqueDialog
from core.gui.gestion_evaluation import GestionEvaluationDialog
from core.gui.evaluation_calendar import EvaluationCalendarDialog
from core.db.configbd import get_connection as get_db_connection

try:
    from core.services.log_exporter import export_day
except ImportError:
    export_day = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion du Personnel")
        self.setGeometry(80, 80, 1180, 720)

        # ---------- Widget central + layout principal ----------
        rootw = QWidget(); self.setCentralWidget(rootw)
        root = QGridLayout(rootw)
        root.setContentsMargins(18, 18, 18, 18)
        root.setHorizontalSpacing(18)
        root.setVerticalSpacing(18)
        rootw.setLayout(root)

        # =====================
        # Colonne gauche — cartes pastel
        # =====================
        left = QVBoxLayout(); left.setSpacing(18)

        # Retards (bandeau rouge pastel)
        retard_card = EmacStatusCard("Retard Évaluations", variant='danger')
        self.retard_filter = QComboBox(); self.retard_filter.addItem("Tous les postes", "")
        self.retard_filter.currentIndexChanged.connect(self.load_evaluations)
        self.retard_scroll, self.retard_list = self.create_scrollable_list()
        retard_card.body.addWidget(self.retard_filter)
        retard_card.body.addWidget(self.retard_scroll)
        left.addWidget(retard_card)

        # Prochaines (bandeau vert pastel)
        next_card = EmacStatusCard("Prochaines Évaluations", variant='success', subtitle="10 prochaines")
        self.next_eval_filter = QComboBox(); self.next_eval_filter.addItem("Tous les postes", "")
        self.next_eval_filter.currentIndexChanged.connect(self.load_evaluations)
        self.next_eval_scroll, self.next_eval_list = self.create_scrollable_list()
        next_card.body.addWidget(self.next_eval_filter)
        next_card.body.addWidget(self.next_eval_scroll)
        left.addWidget(next_card)

        root.addLayout(left, 0, 0, 2, 1)

        # =====================
        # Colonne droite — header + actions
        # =====================
        right = QVBoxLayout(); right.setSpacing(18)

        header = EmacHeader("Gestion du Personnel")
        # bouton menu en action à droite
        self.menu = QMenu(self)
        menu_btn = EmacButton("Menu")
        menu_btn.clicked.connect(self.show_menu)
        header.add_action(menu_btn)
        right.addWidget(header)

        actions_wrap = EmacCard()
        title = QLabel("Actions rapides"); title.setProperty('class','h2')
        actions_wrap.body.addWidget(title)

        rows = QVBoxLayout(); rows.setSpacing(8)
        r1 = QHBoxLayout(); b1 = EmacButton("Liste du Personnel", 'primary'); b1.clicked.connect(self.show_liste_personnel); r1.addWidget(b1)
        r2 = QHBoxLayout(); b2 = EmacButton("Liste et Grilles"); b2.clicked.connect(self.show_listes_grilles_dialog); r2.addWidget(b2)
        r3 = QHBoxLayout(); b3 = EmacButton("Gestion des Évaluations"); b3.clicked.connect(self.show_gestion_evaluations); r3.addWidget(b3)
        r4 = QHBoxLayout(); b4 = EmacButton("Historique"); b4.clicked.connect(self.show_historique); r4.addWidget(b4)
        r5 = QHBoxLayout(); b5 = EmacButton("Calendrier"); b5.clicked.connect(self.show_calendrier_evaluations); r5.addWidget(b5)
        r6 = QHBoxLayout(); b6 = EmacButton("Quitter"); b6.clicked.connect(self.close); r6.addWidget(b6)
        for r in (r1, r2, r3, r4, r5, r6):
            rows.addLayout(r)
        actions_wrap.body.addLayout(rows)
        right.addWidget(actions_wrap)

        root.addLayout(right, 0, 1)

        # --- Data init ---
        self.populate_filters()
        self.load_evaluations()

        # --- Menu déroulant (fonctions existantes) ---
        self.add_menu_action("Ajouter un opérateur", self.show_manage_operator)
        self.add_menu_action("Création/Suppression de poste", self.show_poste_form)
        self.add_menu_action("Calendrier des évaluations", self.show_calendrier_evaluations)
        if export_day:
            self.add_menu_action("Exporter les logs du jour", self.export_logs_today)

    # ================= Helpers UI =================
    def add_menu_action(self, title, action):
        act = QAction(title, self); act.triggered.connect(action); self.menu.addAction(act)

    def show_menu(self):
        self.menu.exec_(self.mapToGlobal(self.rect().topRight()))

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

    # ================= Données / DB =================
    def populate_filters(self):
        conn = get_db_connection(); cur = conn.cursor()
        try:
            cur.execute("SELECT DISTINCT poste_code FROM postes ORDER BY poste_code;")
            for (poste,) in cur.fetchall():
                self.retard_filter.addItem(poste, poste)
                self.next_eval_filter.addItem(poste, poste)
        finally:
            cur.close(); conn.close()

    def load_evaluations(self):
        conn = get_db_connection(); cur = conn.cursor()
        try:
            poste_retard = self.retard_filter.currentData()
            poste_next = self.next_eval_filter.currentData()

            # Retards
            q1 = """
                SELECT o.nom, o.prenom, p.poste_code, poly.prochaine_evaluation
                FROM polyvalence poly
                JOIN operateurs o ON o.id = poly.operateur_id
                LEFT JOIN postes p ON p.id = poly.poste_id
                WHERE poly.prochaine_evaluation < CURDATE()
            """; pr = []
            if poste_retard:
                q1 += " AND p.poste_code = %s"; pr.append(poste_retard)
            q1 += " ORDER BY poly.prochaine_evaluation ASC"
            cur.execute(q1, tuple(pr)); retard = cur.fetchall()

            # Prochaines (limité 10)
            q2 = """
                SELECT o.nom, o.prenom, p.poste_code, poly.prochaine_evaluation
                FROM polyvalence poly
                JOIN operateurs o ON o.id = poly.operateur_id
                LEFT JOIN postes p ON p.id = poly.poste_id
                WHERE poly.prochaine_evaluation >= CURDATE()
                ORDER BY poly.prochaine_evaluation ASC LIMIT 10
            """; pn = []
            if poste_next:
                q2 = q2.replace("WHERE poly.prochaine_evaluation >= CURDATE()",
                                "WHERE poly.prochaine_evaluation >= CURDATE() AND p.poste_code = %s")
                pn.append(poste_next)
            cur.execute(q2, tuple(pn)); prochaines = cur.fetchall()

            # Rendu
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

    # ================= Export =================
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
