# -*- coding: utf-8 -*-
"""
StatistiquesDialog - Tableau de bord statistiques global de l'application EMAC.
Affiche des KPIs et graphiques pour Personnel, Évaluations, Contrats, Absences, Mobilité.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QWidget, QLabel, QFrame, QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from gui.workers.db_worker import DbWorker, DbThreadPool
from gui.components.loading_components import LoadingLabel
from gui.components.emac_ui_kit import add_custom_title_bar
from infrastructure.logging.logging_config import get_logger

logger = get_logger(__name__)

# Palette
_COLORS = {
    'blue':   '#3b82f6',
    'green':  '#22c55e',
    'red':    '#ef4444',
    'orange': '#f97316',
    'purple': '#8b5cf6',
    'teal':   '#14b8a6',
    'gray':   '#94a3b8',
    'bg':     '#f8fafc',
    'border': '#e2e8f0',
    'text':   '#1e293b',
    'muted':  '#64748b',
}

_NIVEAU_COLORS = {
    1: '#ef4444',
    2: '#f97316',
    3: '#3b82f6',
    4: '#22c55e',
}
_NIVEAU_LABELS = {
    1: 'Niveau 1 — Apprentissage',
    2: 'Niveau 2 — Application',
    3: 'Niveau 3 — Maîtrise',
    4: 'Niveau 4 — Expert / Formateur',
}
_MODE_LABELS = {
    'voiture': 'Voiture',
    'velo': 'Vélo',
    'transport_commun': 'Transport commun',
    'covoiturage': 'Covoiturage',
    'autre': 'Autre',
}


# ---------------------------------------------------------------------------
# Widgets utilitaires
# ---------------------------------------------------------------------------

class _Separator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet(f"color: {_COLORS['border']}; background: {_COLORS['border']}; max-height: 1px;")


class _KpiCard(QWidget):
    """Carte KPI : valeur principale + libellé + couleur d'accent."""

    def __init__(self, label: str, value, color: str = '#3b82f6', unit: str = '', parent=None):
        super().__init__(parent)
        self.setMinimumWidth(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QWidget {{
                background: white;
                border: 1px solid {_COLORS['border']};
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        accent = QFrame()
        accent.setFixedHeight(3)
        accent.setStyleSheet(f"background: {color}; border-radius: 2px; border: none;")
        layout.addWidget(accent)

        val_label = QLabel(f"{value}{' ' + unit if unit else ''}")
        font = QFont()
        font.setPointSize(22)
        font.setBold(True)
        val_label.setFont(font)
        val_label.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        layout.addWidget(val_label)

        desc = QLabel(label)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {_COLORS['muted']}; font-size: 12px; border: none; background: transparent;")
        layout.addWidget(desc)


class _SectionTitle(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet(f"color: {_COLORS['text']}; padding-top: 8px;")


class _BarRow(QWidget):
    """Ligne de barre horizontale : label | barre | valeur."""

    BAR_MAX_WIDTH = 260

    def __init__(self, label: str, value: int, max_value: int,
                 color: str = '#3b82f6', suffix: str = '', parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setFixedWidth(200)
        lbl.setStyleSheet(f"color: {_COLORS['text']}; font-size: 12px;")
        lbl.setWordWrap(False)
        layout.addWidget(lbl)

        bar_bg = QFrame()
        bar_bg.setFixedHeight(16)
        bar_bg.setStyleSheet(f"background: {_COLORS['border']}; border-radius: 8px;")
        bar_bg.setMinimumWidth(60)
        bar_bg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(bar_bg, 1)

        bar_fill = QFrame(bar_bg)
        bar_fill.setFixedHeight(16)
        proportion = (value / max_value) if max_value > 0 else 0
        bar_fill.setStyleSheet(f"background: {color}; border-radius: 8px;")
        # La largeur est fixée via resizeEvent après l'affichage
        bar_bg._fill = bar_fill
        bar_bg._proportion = proportion

        def _resize(event, bg=bar_bg):
            bg._fill.setFixedWidth(max(4, int(bg.width() * bg._proportion)))
            QFrame.resizeEvent(bg, event)

        bar_bg.resizeEvent = _resize

        val_lbl = QLabel(f"{value}{' ' + suffix if suffix else ''}")
        val_lbl.setFixedWidth(60)
        val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val_lbl.setStyleSheet(f"color: {_COLORS['muted']}; font-size: 12px; font-weight: bold;")
        layout.addWidget(val_lbl)


def _scroll_widget() -> tuple:
    """Retourne (QScrollArea, content_widget, content_layout)."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setStyleSheet("background: transparent;")

    content = QWidget()
    content.setStyleSheet(f"background: {_COLORS['bg']};")
    layout = QVBoxLayout(content)
    layout.setContentsMargins(20, 16, 20, 20)
    layout.setSpacing(12)
    scroll.setWidget(content)
    return scroll, content, layout


# ---------------------------------------------------------------------------
# Dialog principal
# ---------------------------------------------------------------------------

class StatistiquesDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Statistiques")
        self.setMinimumSize(900, 640)
        self.resize(1060, 720)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        add_custom_title_bar(self, "Statistiques")

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {_COLORS['bg']};
            }}
            QTabBar::tab {{
                padding: 10px 18px;
                font-size: 13px;
                color: {_COLORS['muted']};
                border-bottom: 3px solid transparent;
                background: transparent;
            }}
            QTabBar::tab:selected {{
                color: {_COLORS['blue']};
                border-bottom: 3px solid {_COLORS['blue']};
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                color: {_COLORS['text']};
            }}
        """)
        main.addWidget(self._tabs)

        # Placeholders de chargement pour chaque onglet
        self._tab_widgets = {}
        for name in ("Vue d'ensemble", "Personnel", "Évaluations", "Contrats", "Absences", "Mobilité"):
            placeholder = QWidget()
            ph_layout = QVBoxLayout(placeholder)
            ph_layout.addWidget(LoadingLabel("Chargement..."), 0, Qt.AlignCenter)
            self._tabs.addTab(placeholder, name)
            self._tab_widgets[name] = placeholder

        # Chargement des données après l'affichage
        QTimer.singleShot(80, self._load_all)

    # ------------------------------------------------------------------
    # Chargement asynchrone
    # ------------------------------------------------------------------

    def _load_all(self):
        from domain.services.statistiques_service import (
            get_resume, get_stats_personnel, get_stats_evaluations,
            get_stats_contrats, get_stats_absences, get_stats_mobilite,
        )

        def _fetch(progress_callback=None):
            return {
                'resume':      get_resume(),
                'personnel':   get_stats_personnel(),
                'evaluations': get_stats_evaluations(),
                'contrats':    get_stats_contrats(),
                'absences':    get_stats_absences(),
                'mobilite':    get_stats_mobilite(),
            }

        worker = DbWorker(_fetch)
        worker.signals.result.connect(self._on_data)
        worker.signals.error.connect(self._on_error)
        DbThreadPool.start(worker)

    def _on_error(self, error):
        logger.exception(f"StatistiquesDialog erreur: {error}")
        for name, w in self._tab_widgets.items():
            lbl = QLabel("Erreur de chargement des données.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {_COLORS['red']};")
            layout = w.layout()
            for i in reversed(range(layout.count())):
                layout.itemAt(i).widget().deleteLater()
            layout.addWidget(lbl)

    def _on_data(self, data: dict):
        self._build_resume_tab(data.get('resume', {}))
        self._build_personnel_tab(data.get('personnel', {}))
        self._build_evaluations_tab(data.get('evaluations', {}))
        self._build_contrats_tab(data.get('contrats', {}))
        self._build_absences_tab(data.get('absences', {}))
        self._build_mobilite_tab(data.get('mobilite', {}))

    # ------------------------------------------------------------------
    # Helpers de construction de tabs
    # ------------------------------------------------------------------

    def _replace_tab(self, name: str, new_widget: QWidget):
        old = self._tab_widgets[name]
        idx = self._tabs.indexOf(old)
        self._tabs.removeTab(idx)
        self._tabs.insertTab(idx, new_widget, name)
        self._tab_widgets[name] = new_widget
        old.deleteLater()

    # ------------------------------------------------------------------
    # Tab : Vue d'ensemble
    # ------------------------------------------------------------------

    def _build_resume_tab(self, d: dict):
        scroll, _, layout = _scroll_widget()

        layout.addWidget(_SectionTitle("Indicateurs clés"))

        grid = QGridLayout()
        grid.setSpacing(12)

        kpis = [
            ("Effectif actif",            d.get('effectif_actif', 0),   _COLORS['blue'],   ''),
            ("Évaluations en retard",      d.get('evals_retard', 0),     _COLORS['red'],    ''),
            ("Contrats expirant ≤ 30 j",  d.get('contrats_30j', 0),     _COLORS['orange'], ''),
            ("Absences validées ce mois",  d.get('absences_mois', 0),    _COLORS['purple'], ''),
            ("Salariés avec mobilité",     d.get('mobilite_actifs', 0),  _COLORS['teal'],   ''),
        ]
        for col, (label, value, color, unit) in enumerate(kpis):
            grid.addWidget(_KpiCard(label, value, color, unit), 0, col)

        layout.addLayout(grid)
        layout.addWidget(_Separator())
        layout.addWidget(_SectionTitle("À surveiller"))

        notes = []
        if d.get('evals_retard', 0) > 0:
            notes.append((f"{d['evals_retard']} évaluation(s) en retard", _COLORS['red']))
        if d.get('contrats_30j', 0) > 0:
            notes.append((f"{d['contrats_30j']} contrat(s) expirent dans 30 jours", _COLORS['orange']))
        if not notes:
            notes.append(("Aucune alerte en cours.", _COLORS['green']))

        for msg, color in notes:
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setFixedWidth(16)
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            txt = QLabel(msg)
            txt.setStyleSheet(f"color: {_COLORS['text']}; font-size: 13px;")
            row.addWidget(dot)
            row.addWidget(txt)
            row.addStretch()
            layout.addLayout(row)

        layout.addStretch()
        self._replace_tab("Vue d'ensemble", scroll)

    # ------------------------------------------------------------------
    # Tab : Personnel
    # ------------------------------------------------------------------

    def _build_personnel_tab(self, d: dict):
        scroll, _, layout = _scroll_widget()

        # --- Statut ---
        layout.addWidget(_SectionTitle("Effectifs par statut"))
        par_statut = d.get('par_statut', [])
        max_statut = max((r['nb'] for r in par_statut), default=1)
        statut_colors = {'ACTIF': _COLORS['green'], 'INACTIF': _COLORS['gray']}
        for row in par_statut:
            color = statut_colors.get(row['statut'], _COLORS['blue'])
            layout.addWidget(_BarRow(row['statut'], row['nb'], max_statut, color))

        layout.addWidget(_Separator())

        # --- Catégorie ---
        layout.addWidget(_SectionTitle("Répartition par catégorie (actifs)"))
        par_cat = d.get('par_categorie', [])
        cat_labels = {'O': 'Ouvrier', 'E': 'Employé', 'T': 'Technicien', 'C': 'Cadre', '?': 'Non renseigné'}
        cat_colors = {'O': _COLORS['blue'], 'E': _COLORS['teal'], 'T': _COLORS['purple'], 'C': _COLORS['orange'], '?': _COLORS['gray']}
        max_cat = max((r['nb'] for r in par_cat), default=1)
        for row in par_cat:
            cat = row['categorie']
            label = f"{cat_labels.get(cat, cat)} ({cat})"
            color = cat_colors.get(cat, _COLORS['blue'])
            layout.addWidget(_BarRow(label, row['nb'], max_cat, color))

        layout.addWidget(_Separator())

        # --- Ancienneté ---
        layout.addWidget(_SectionTitle("Ancienneté (actifs)"))
        anc = d.get('par_anciennete', {})
        tranches = [
            ("< 1 an",      anc.get('moins_1_an', 0)),
            ("1 – 5 ans",   anc.get('de_1_a_5_ans', 0)),
            ("5 – 10 ans",  anc.get('de_5_a_10_ans', 0)),
            ("> 10 ans",    anc.get('plus_10_ans', 0)),
            ("Inconnue",    anc.get('inconnue', 0)),
        ]
        max_anc = max((v for _, v in tranches), default=1)
        anc_colors = [_COLORS['orange'], _COLORS['blue'], _COLORS['teal'], _COLORS['green'], _COLORS['gray']]
        for (label, value), color in zip(tranches, anc_colors):
            layout.addWidget(_BarRow(label, value, max_anc, color))

        layout.addStretch()
        self._replace_tab("Personnel", scroll)

    # ------------------------------------------------------------------
    # Tab : Évaluations
    # ------------------------------------------------------------------

    def _build_evaluations_tab(self, d: dict):
        scroll, _, layout = _scroll_widget()

        total = d.get('total', 0)
        en_retard = d.get('en_retard', 0)
        a_jour = total - en_retard

        # KPI mini
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        kpi_row.addWidget(_KpiCard("Total évaluations", total, _COLORS['blue']))
        kpi_row.addWidget(_KpiCard("En retard", en_retard, _COLORS['red']))
        kpi_row.addWidget(_KpiCard("À jour", a_jour, _COLORS['green']))
        kpi_row.addStretch()
        layout.addLayout(kpi_row)
        layout.addWidget(_Separator())

        # --- Niveaux ---
        layout.addWidget(_SectionTitle("Répartition par niveau de compétence"))
        par_niveau = d.get('par_niveau', [])
        max_niv = max((r['nb'] for r in par_niveau), default=1)
        for row in par_niveau:
            n = row['niveau']
            label = _NIVEAU_LABELS.get(n, f"Niveau {n}")
            color = _NIVEAU_COLORS.get(n, _COLORS['blue'])
            layout.addWidget(_BarRow(label, row['nb'], max_niv, color))

        layout.addWidget(_Separator())

        # --- Top postes en retard ---
        layout.addWidget(_SectionTitle("Postes avec le plus de retards"))
        top = d.get('top_postes_retard', [])
        if top:
            max_top = max(r['nb_retard'] for r in top)
            for row in top:
                layout.addWidget(_BarRow(row['poste'], row['nb_retard'], max_top, _COLORS['red']))
        else:
            lbl = QLabel("Aucun retard.")
            lbl.setStyleSheet(f"color: {_COLORS['green']}; font-size: 13px;")
            layout.addWidget(lbl)

        layout.addStretch()
        self._replace_tab("Évaluations", scroll)

    # ------------------------------------------------------------------
    # Tab : Contrats
    # ------------------------------------------------------------------

    def _build_contrats_tab(self, d: dict):
        scroll, _, layout = _scroll_widget()

        exp = d.get('expirations', {})

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        kpi_row.addWidget(_KpiCard("Expirés",           exp.get('expires', 0),      _COLORS['red']))
        kpi_row.addWidget(_KpiCard("Expirent ≤ 30 j",  exp.get('dans_30j', 0),     _COLORS['orange']))
        kpi_row.addWidget(_KpiCard("Expirent ≤ 60 j",  exp.get('dans_60j', 0),     _COLORS['orange']))
        kpi_row.addWidget(_KpiCard("Expirent ≤ 90 j",  exp.get('dans_90j', 0),     _COLORS['purple']))
        kpi_row.addWidget(_KpiCard("Sans date de fin",  exp.get('sans_date_fin', 0), _COLORS['blue']))
        kpi_row.addStretch()
        layout.addLayout(kpi_row)
        layout.addWidget(_Separator())

        layout.addWidget(_SectionTitle("Répartition par type de contrat (actifs)"))
        par_type = d.get('par_type', [])
        type_colors = {
            'CDI': _COLORS['blue'], 'CDD': _COLORS['orange'],
            'INTERIMAIRE': _COLORS['purple'], 'APPRENTISSAGE': _COLORS['teal'],
            'PROFESSIONNALISATION': _COLORS['green'],
        }
        max_type = max((r['nb'] for r in par_type), default=1)
        for row in par_type:
            color = type_colors.get(row['type_contrat'], _COLORS['gray'])
            layout.addWidget(_BarRow(row['type_contrat'], row['nb'], max_type, color))

        layout.addStretch()
        self._replace_tab("Contrats", scroll)

    # ------------------------------------------------------------------
    # Tab : Absences
    # ------------------------------------------------------------------

    def _build_absences_tab(self, d: dict):
        scroll, _, layout = _scroll_widget()

        layout.addWidget(_SectionTitle("Par type d'absence (6 derniers mois)"))
        par_type = d.get('par_type', [])
        if par_type:
            max_jours = max((float(r.get('total_jours') or 0) for r in par_type), default=1)
            colors = [_COLORS['blue'], _COLORS['orange'], _COLORS['purple'],
                      _COLORS['teal'], _COLORS['red'], _COLORS['green']]
            for i, row in enumerate(par_type):
                jours = float(row.get('total_jours') or 0)
                color = colors[i % len(colors)]
                layout.addWidget(_BarRow(
                    row['type_absence'], int(jours), int(max_jours) or 1,
                    color, suffix='j'
                ))
        else:
            layout.addWidget(QLabel("Aucune absence validée sur les 6 derniers mois."))

        layout.addWidget(_Separator())

        layout.addWidget(_SectionTitle("Nombre d'absences validées par mois"))
        par_mois = d.get('par_mois', [])
        if par_mois:
            max_nb = max((r['nb_absences'] for r in par_mois), default=1)
            for row in par_mois:
                layout.addWidget(_BarRow(
                    row['mois'], row['nb_absences'], max_nb,
                    _COLORS['blue'], suffix='abs.'
                ))
        else:
            layout.addWidget(QLabel("Aucune donnée mensuelle."))

        layout.addStretch()
        self._replace_tab("Absences", scroll)

    # ------------------------------------------------------------------
    # Tab : Mobilité
    # ------------------------------------------------------------------

    def _build_mobilite_tab(self, d: dict):
        scroll, _, layout = _scroll_widget()

        distances = d.get('distances', {})
        dist_moy = distances.get('distance_moyenne') or 0

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        kpi_row.addWidget(_KpiCard("Distance moyenne", f"{dist_moy}", _COLORS['teal'], 'km'))
        kpi_row.addStretch()
        layout.addLayout(kpi_row)
        layout.addWidget(_Separator())

        layout.addWidget(_SectionTitle("Répartition par mode de transport"))
        par_mode = d.get('par_mode', [])
        max_mode = max((r['nb'] for r in par_mode), default=1)
        mode_colors = {
            'voiture': _COLORS['blue'], 'velo': _COLORS['green'],
            'transport_commun': _COLORS['orange'], 'covoiturage': _COLORS['teal'],
            'autre': _COLORS['gray'],
        }
        for row in par_mode:
            label = f"{_MODE_LABELS.get(row['mode_transport'], row['mode_transport'])}  (moy. {row['dist_moy']} km)"
            color = mode_colors.get(row['mode_transport'], _COLORS['gray'])
            layout.addWidget(_BarRow(label, row['nb'], max_mode, color))

        layout.addWidget(_Separator())

        layout.addWidget(_SectionTitle("Répartition par tranche de distance"))
        tranches = [
            ("0 – 6 km",   int(distances.get('moins_7km') or 0)),
            ("7 – 13 km",  int(distances.get('de_7_a_13') or 0)),
            ("14 – 20 km", int(distances.get('de_14_a_20') or 0)),
            ("21 – 40 km", int(distances.get('de_21_a_40') or 0)),
            ("> 40 km",    int(distances.get('plus_40km') or 0)),
        ]
        max_tr = max((v for _, v in tranches), default=1)
        tr_colors = [_COLORS['green'], _COLORS['blue'], _COLORS['teal'], _COLORS['orange'], _COLORS['purple']]
        for (label, value), color in zip(tranches, tr_colors):
            layout.addWidget(_BarRow(label, value, max_tr, color))

        layout.addStretch()
        self._replace_tab("Mobilité", scroll)
