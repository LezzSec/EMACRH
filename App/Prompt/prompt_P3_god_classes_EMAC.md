# PROMPT CLAUDE CODE — P3 Décomposition des God Classes EMAC

## Contexte

Application EMAC : PyQt5/MySQL desktop app (~74K lignes, 244 fichiers Python).
Ce prompt couvre le **workstream P3 — Décomposition des God Classes** : les fichiers monolithiques qui concentrent trop de responsabilités et deviennent impossibles à maintenir/tester.

> **Modèle de référence** : Le pattern `gui/screens/admin/config_tabs/` est le bon exemple à suivre — un `__init__.py` qui ré-exporte les classes publiques, un `base.py` pour le code partagé, et des fichiers thématiques (`tabs_rh.py`, `tabs_absences.py`, etc.). Tous les imports existants continuent de fonctionner grâce aux ré-exports.

> **Règle d'or** : Aucun import existant ne doit casser. Utiliser des `__init__.py` avec ré-exports pour maintenir la rétrocompatibilité. Chaque extraction doit être suivie d'un test d'import pour vérifier.

---

## CIBLE 1 — `gui/main_qt.py` (1298 lignes, 59 méthodes)

C'est la pire God Class. `MainWindow` fait tout : bootstrap, drawer, navigation, notifications, alertes, session, export logs, admin.

### Plan de découpage

Créer `gui/main_qt/` comme package :

```
gui/main_qt/
├── __init__.py              # ré-exporte MainWindow (rétrocompat)
├── main_window.py           # MainWindow réduit (~300 lignes) : __init__, bootstrap, eventFilter, closeEvent, resizeEvent
├── drawer.py                # DrawerMixin : create_drawer(), toggle_drawer(), add_btn()
├── navigation.py            # NavigationMixin : tous les show_*() (show_liste_personnel, show_manage_operator, show_gestion_evaluations, show_poste_form, show_historique, show_statistiques, show_regularisation, show_contract_management, show_alertes_rh, show_gestion_documentaire, show_gestion_templates, show_user_management, show_admin_data_panel)
├── dashboard_loaders.py     # DashboardMixin : populate_filters_async, load_evaluations_async, load_alertes_rh_async, _fetch_*, _apply_*
├── notifications.py         # NotificationMixin : _load_notification_counts, _apply_notification_counts, _show_startup_alert_popup (le popup de 150 lignes)
└── session.py               # SessionMixin : _start_timeout_monitoring, _force_logout_timeout, logout, export_logs_today
```

### Implémentation via Mixins

```python
# gui/main_qt/navigation.py
class NavigationMixin:
    """Toutes les méthodes show_*() de la MainWindow."""

    def show_liste_personnel(self):
        from gui.screens.personnel.gestion_personnel import GestionPersonnelDialog
        dialog = GestionPersonnelDialog(self)
        dialog.data_changed.connect(self.load_evaluations_async)
        dialog.exec_()

    def show_manage_operator(self):
        ...
    # etc.
```

```python
# gui/main_qt/main_window.py
from gui.main_qt.drawer import DrawerMixin
from gui.main_qt.navigation import NavigationMixin
from gui.main_qt.dashboard_loaders import DashboardMixin
from gui.main_qt.notifications import NotificationMixin
from gui.main_qt.session import SessionMixin

class MainWindow(QMainWindow, DrawerMixin, NavigationMixin, DashboardMixin, NotificationMixin, SessionMixin):
    DRAWER_WIDTH = 280

    def __init__(self):
        super().__init__()
        # ... init réduit ...
```

```python
# gui/main_qt/__init__.py
from gui.main_qt.main_window import MainWindow

__all__ = ['MainWindow']
```

### Vérification rétrocompat
Après le split, cet import doit continuer à fonctionner :
```python
from gui.main_qt import MainWindow  # OK
```
Mais aussi l'import direct (utilisé dans main.py) :
```python
from gui.main_qt import MainWindow  # Déjà OK car c'est un package avec __init__
```

**Note** : les fonctions module-level `_lazy_auth()`, `_lazy_theme()`, `get_theme_components()` restent dans `main_window.py` car elles sont utilisées uniquement par MainWindow.

---

## CIBLE 2 — `gui/screens/admin/historique.py` (1173 lignes, 4 classes)

Ce fichier contient 4 classes distinctes qui méritent chacune leur fichier.

### Plan de découpage

Créer `gui/screens/admin/historique/` comme package :

```
gui/screens/admin/historique/
├── __init__.py            # ré-exporte HistoriqueDialog (c'est le seul import externe)
├── historique_dialog.py   # HistoriqueDialog (classe principale, ~500 lignes)
├── detail_dialog.py       # DetailDialog (~290 lignes)
├── action_card.py         # ActionCard (~155 lignes)
├── date_separator.py      # DateSeparator (~65 lignes)
└── utils.py               # Fonctions module-level : get_action_config(), fr_action(), get_detailed_action_type(), make_resume()
```

### __init__.py
```python
from gui.screens.admin.historique.historique_dialog import HistoriqueDialog

__all__ = ['HistoriqueDialog']
```

### Vérification
```python
from gui.screens.admin.historique import HistoriqueDialog  # doit fonctionner
```

---

## CIBLE 3 — `gui/screens/planning/planning.py` (1072 lignes, 1 classe, 26 méthodes)

`RegularisationDialog` gère 6 onglets complètement indépendants dans une seule classe monolithique.

### Plan de découpage

Créer `gui/screens/planning/regularisation/` comme package :

```
gui/screens/planning/regularisation/
├── __init__.py                  # ré-exporte RegularisationDialog
├── regularisation_dialog.py     # Classe principale réduite : __init__, refresh_all, formats utilitaires (~100 lignes)
├── tab_absents_jour.py          # create_absents_tab() + load_absents_today() (~115 lignes)
├── tab_declaration.py           # create_declare_tab() + load_personnel_combo() + submit_declaration() (~140 lignes)
├── tab_calendrier_absences.py   # create_calendar_tab() + load_calendar_absences() + on_calendar_date_clicked() (~120 lignes)
├── tab_calendrier_eval.py       # create_eval_calendar_tab() + load_eval_* + on_eval_calendar_date_clicked() (~175 lignes)
├── tab_historique.py            # create_history_tab() + load_history() + delete_selected_declaration() (~165 lignes)
└── tab_docs_expiration.py       # create_docs_expiration_tab() + load_docs_expiration() + open_rh_for_selected_doc() (~115 lignes)
```

### Implémentation
Même pattern mixin que main_qt, ou bien chaque tab est un QWidget standalone injecté dans le QTabWidget du dialog principal :

```python
# tab_absents_jour.py
class AbsentsJourTab(QWidget):
    def __init__(self, parent_dialog):
        super().__init__()
        self.parent_dialog = parent_dialog
        self._build_ui()

    def _build_ui(self):
        # ancien code de create_absents_tab()...

    def load_data(self):
        # ancien code de load_absents_today()...
```

```python
# regularisation_dialog.py
class RegularisationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ...
        self.tab_absents = AbsentsJourTab(self)
        self.tab_decl = DeclarationTab(self)
        ...
        tabs.addTab(self.tab_absents, "Absents du jour")
        tabs.addTab(self.tab_decl, "Déclarer")
        ...
```

**Préférer les QWidget standalone aux Mixins pour les tabs** — c'est plus propre car chaque tab a son propre état.

---

## CIBLE 4 — `gui/components/emac_ui_kit.py` (1139 lignes, 12 classes + fonctions)

Ce fichier est une boîte à outils qui mélange des composants réutilisables très différents.

### Plan de découpage

Créer `gui/components/ui_kit/` comme package :

```
gui/components/ui_kit/
├── __init__.py              # ré-exporte TOUT (rétrocompat critique — ce module est importé partout)
├── layout.py                # Card, TopBar, SideNav, SideNavButton (~130 lignes)
├── title_bar.py             # CustomTitleBar, add_custom_title_bar(), add_fullscreen_button() (~260 lignes)
├── feedback.py              # EmacBadge, EmacAlert, EmacChip (~180 lignes)
├── toast.py                 # ToastNotification, ToastManager (~130 lignes)
├── widgets.py               # LoadingButton, SearchBar (~90 lignes)
├── messages.py              # show_error_message(), show_warning_message() (~70 lignes)
└── stylesheet.py            # get_stylesheet() (~35 lignes)
```

### __init__.py CRITIQUE
```python
# Rétrocompatibilité totale — RIEN ne doit casser
from gui.components.ui_kit.layout import Card, TopBar, SideNav, SideNavButton
from gui.components.ui_kit.title_bar import CustomTitleBar, add_custom_title_bar, add_fullscreen_button
from gui.components.ui_kit.feedback import EmacBadge, EmacAlert, EmacChip
from gui.components.ui_kit.toast import ToastNotification, ToastManager
from gui.components.ui_kit.widgets import LoadingButton, SearchBar
from gui.components.ui_kit.messages import show_error_message, show_warning_message
from gui.components.ui_kit.stylesheet import get_stylesheet

__all__ = [
    'Card', 'TopBar', 'SideNav', 'SideNavButton',
    'CustomTitleBar', 'add_custom_title_bar', 'add_fullscreen_button',
    'EmacBadge', 'EmacAlert', 'EmacChip',
    'ToastNotification', 'ToastManager',
    'LoadingButton', 'SearchBar',
    'show_error_message', 'show_warning_message',
    'get_stylesheet',
]
```

### Rétrocompat : garder l'ancien fichier comme proxy
Si trop d'imports utilisent `from gui.components.emac_ui_kit import ...`, on peut garder `emac_ui_kit.py` comme fichier proxy :
```python
# gui/components/emac_ui_kit.py (garde temporaire)
from gui.components.ui_kit import *  # noqa: F401,F403
```

---

## CIBLE 5 — `domain/services/admin/alert_service.py` (1032 lignes, 1 classe, 16 méthodes statiques)

`AlertService` est une God Class de service — chaque méthode est indépendante (pas d'état partagé, tout est `@staticmethod`). Parfait pour un split.

### Plan de découpage

Créer `domain/services/admin/alerts/` comme package :

```
domain/services/admin/alerts/
├── __init__.py              # ré-exporte AlertService, TypeAlerte
├── alert_types.py           # TypeAlerte (~20 lignes)
├── contrat_alerts.py        # get_contrats_expires(), get_contrats_expirant(), get_personnel_sans_contrat(), get_all_contract_alerts() (~250 lignes)
├── personnel_alerts.py      # get_personnel_sans_competences(), get_nouveaux_sans_affectation(), get_all_personnel_alerts() (~200 lignes)
├── document_alerts.py       # get_all_document_alerts() (~100 lignes)
├── rh_alerts.py             # get_personnel_sans_mutuelle(), get_personnel_sans_visite_medicale(), get_personnel_sans_entretien(), _get_mutuelles_expirant() (~200 lignes)
└── alert_aggregator.py      # AlertService (façade) : get_statistics(), get_quick_counts(), get_startup_summary() (~150 lignes) — appelle les sous-modules
```

### Implémentation
```python
# alert_aggregator.py
from domain.services.admin.alerts.contrat_alerts import ContratAlerts
from domain.services.admin.alerts.personnel_alerts import PersonnelAlerts
from domain.services.admin.alerts.document_alerts import DocumentAlerts
from domain.services.admin.alerts.rh_alerts import RHAlerts

class AlertService:
    """Façade qui agrège toutes les alertes."""

    # Délégation aux sous-modules
    get_contrats_expires = ContratAlerts.get_contrats_expires
    get_contrats_expirant = ContratAlerts.get_contrats_expirant
    get_personnel_sans_contrat = ContratAlerts.get_personnel_sans_contrat
    # ...

    @staticmethod
    def get_startup_summary() -> Dict[str, int]:
        # Agrège les résultats de tous les sous-modules
        ...
```

### __init__.py
```python
from domain.services.admin.alerts.alert_aggregator import AlertService
from domain.services.admin.alerts.alert_types import TypeAlerte

__all__ = ['AlertService', 'TypeAlerte']
```

### Rétrocompat
Garder `alert_service.py` comme proxy temporaire :
```python
# domain/services/admin/alert_service.py
from domain.services.admin.alerts import AlertService, TypeAlerte  # noqa: F401
```

---

## CIBLE 6 — `gui/screens/formation/gestion_formations.py` (1083 lignes, 2 classes)

### Plan de découpage

```
gui/screens/formation/gestion_formations/
├── __init__.py                    # ré-exporte GestionFormationsDialog
├── gestion_formations_dialog.py   # Dialog principal (~600 lignes)
└── add_edit_formation_dialog.py   # AddEditFormationDialog (~450 lignes)
```

Simple split : les 2 classes sont déjà indépendantes.

---

## ORDRE D'EXÉCUTION RECOMMANDÉ

1. **`emac_ui_kit.py`** en premier — c'est le plus importé, et le split est simple (pas de logique partagée entre classes). Permet de valider le pattern avant d'attaquer les autres.
2. **`historique.py`** — 4 classes clairement séparées, split mécanique.
3. **`gestion_formations.py`** — 2 classes, trivial.
4. **`alert_service.py`** — fonctions statiques indépendantes, split propre.
5. **`planning.py`** — plus complexe car il faut extraire les tabs en QWidgets standalone.
6. **`main_qt.py`** — le plus risqué, faire en dernier quand le pattern est rodé.

## VÉRIFICATION APRÈS CHAQUE SPLIT

```bash
# 1. Vérifier que tous les imports existants fonctionnent
grep -rn "from gui.components.emac_ui_kit import\|from gui.screens.admin.historique import\|from gui.main_qt import\|from domain.services.admin.alert_service import" --include="*.py" | grep -v __pycache__ | while read line; do
    import_stmt=$(echo "$line" | cut -d: -f3-)
    echo "Testing: $import_stmt"
    python -c "$import_stmt" 2>&1 || echo "FAIL: $line"
done

# 2. Lancer les tests
python -m pytest tests/unit/ -x -q

# 3. Vérifier les imports circulaires
python -c "import gui.main_qt; print('OK')"
```
