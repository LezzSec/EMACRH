# Monitoring des Performances - Guide Complet

**Date** : 2026-01-07
**Impact** : ✅ Détection proactive des régressions, pratiques "grosses boîtes"

---

## Table des matières

1. [Pourquoi le monitoring](#pourquoi-le-monitoring)
2. [Architecture du système](#architecture-du-système)
3. [Utilisation de base](#utilisation-de-base)
4. [Décorateurs de monitoring](#décorateurs-de-monitoring)
5. [Context managers](#context-managers)
6. [Configuration des seuils](#configuration-des-seuils)
7. [Rapports et statistiques](#rapports-et-statistiques)
8. [Intégration dans EMAC](#intégration-dans-emac)
9. [Bonnes pratiques](#bonnes-pratiques)

---

## Pourquoi le monitoring

### ❌ Problème : Régressions invisibles

Sans monitoring, les régressions de performance passent inaperçues :

```python
# Version 1.0 : Rapide (50ms)
def load_personnel():
    cur.execute("SELECT * FROM personnel WHERE statut = 'ACTIF'")
    return cur.fetchall()

# Version 1.1 : Régression ! (500ms) ❌
# Quelqu'un a supprimé l'index sans le savoir
def load_personnel():
    cur.execute("SELECT * FROM personnel WHERE statut = 'ACTIF'")  # 10x plus lent !
    return cur.fetchall()
```

**Impact** :
- Dégradation progressive de la performance
- Découverte tardive (plaintes utilisateurs)
- Difficile de localiser la régression

### ✅ Solution : Monitoring automatique

```python
from core.utils.performance_monitor import monitor_query

@monitor_query('Load Personnel')
def load_personnel():
    cur.execute("SELECT * FROM personnel WHERE statut = 'ACTIF'")
    return cur.fetchall()

# Version 1.0 : 50ms → OK
# Version 1.1 : 500ms → ⚠️ ALERTE dans les logs !
# "SLOW QUERY: Load Personnel took 500ms (threshold: 100ms)"
```

**Avantages** :
- ✅ Détection immédiate des régressions
- ✅ Localisation précise du problème
- ✅ Historique des performances
- ✅ Statistiques agrégées

---

## Architecture du système

### Composants

```
Application
    ↓
@monitor_* decorators
    ↓
PerformanceMonitor (Singleton)
    ↓
Collecte métriques en mémoire
    ↓
Comparaison avec seuils
    ↓
Si lent → Alerte (console + log)
    ↓
Statistiques agrégées
```

### Métriques collectées

Pour chaque opération :
- **Nom** : "Login", "Load Personnel", etc.
- **Catégorie** : login, query, dialog, cache, export
- **Durée** : temps en millisecondes
- **Seuil** : seuil configuré pour cette catégorie
- **Timestamp** : quand ça s'est produit
- **Détails** : informations additionnelles (optionnel)
- **is_slow** : booléen (dépassement seuil)

---

## Utilisation de base

### Monitorer le login

```python
from core.utils.performance_monitor import monitor_login_time

@monitor_login_time
def authenticate(username, password):
    """Authentifie un utilisateur"""
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT u.*, r.nom as role_nom
            FROM utilisateurs u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = %s
        """, (username,))
        user = cur.fetchone()

    if user and verify_password(password, user['password_hash']):
        return user
    return None

# Si login > 500ms → ⚠️ ALERTE
```

### Monitorer une requête DB

```python
from core.utils.performance_monitor import monitor_query

@monitor_query('Load Personnel Actif')
def load_personnel_actif():
    """Charge le personnel actif"""
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("SELECT * FROM personnel WHERE statut = 'ACTIF'")
        return cur.fetchall()

# Si requête > 100ms → ⚠️ ALERTE
```

### Monitorer l'ouverture d'un dialog

```python
from core.utils.performance_monitor import monitor_dialog

class GestionPersonnelDialog(QDialog):
    @monitor_dialog('Personnel Dialog')
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()

    # Si ouverture > 300ms → ⚠️ ALERTE
```

---

## Décorateurs de monitoring

### @monitor_performance (générique)

```python
from core.utils.performance_monitor import monitor_performance

@monitor_performance('My Operation', category='other', threshold_ms=200)
def my_function():
    # ...
    pass
```

**Paramètres** :
- `operation` : Nom de l'opération (None = nom fonction)
- `category` : Catégorie (login, query, dialog, cache, export, other)
- `threshold_ms` : Seuil personnalisé (None = utiliser config)

### @monitor_query (requêtes DB)

```python
@monitor_query('Load Polyvalence')
def load_polyvalence_by_operateur(operateur_id):
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT p.*, pos.poste_code, pos.nom as poste_nom
            FROM polyvalence p
            JOIN postes pos ON p.poste_id = pos.id
            WHERE p.operateur_id = %s
        """, (operateur_id,))
        return cur.fetchall()
```

**Seuil par défaut** : 100ms

### @monitor_dialog (dialogs)

```python
@monitor_dialog('Evaluation Dialog')
def open_evaluation_dialog(self):
    dialog = GestionEvaluationDialog(self)
    dialog.exec_()
```

**Seuil par défaut** : 300ms

### @monitor_login_time (login)

```python
@monitor_login_time
def verify_credentials(username, password):
    user = get_user(username)
    if user and check_password(password, user['password_hash']):
        return user
    return None
```

**Seuil par défaut** : 500ms

---

## Context managers

### PerformanceTimer (générique)

```python
from core.utils.performance_monitor import PerformanceTimer

def complex_operation():
    with PerformanceTimer('Complex Operation', category='other'):
        # Code à mesurer
        step1()
        step2()
        step3()
```

### measure_query_time (requêtes)

```python
from core.utils.performance_monitor import measure_query_time

def load_data():
    with measure_query_time('Load Evaluations'):
        cur.execute("""
            SELECT * FROM polyvalence
            WHERE prochaine_evaluation < CURDATE()
        """)
        return cur.fetchall()
```

### measure_dialog_time (dialogs)

```python
from core.utils.performance_monitor import measure_dialog_time

def show_settings(self):
    with measure_dialog_time('Settings Dialog'):
        dialog = SettingsDialog(self)
        dialog.exec_()
```

---

## Configuration des seuils

### Seuils par défaut

```python
THRESHOLDS = {
    'login': 500,    # Login peut être plus lent
    'query': 100,    # Requêtes DB doivent être rapides
    'dialog': 300,   # Ouverture dialog
    'cache': 10,     # Cache hit doit être instantané
    'export': 2000,  # Export peut prendre du temps
}
```

### Modifier les seuils

```python
from core.utils.performance_monitor import set_threshold, PerformanceConfig

# Modifier un seuil spécifique
set_threshold('query', 50)  # Requêtes doivent être < 50ms

# Ou modifier directement
PerformanceConfig.THRESHOLDS['dialog'] = 200  # Dialogs < 200ms
```

### Seuil global

```python
from core.utils.performance_monitor import PerformanceConfig

# Seuil par défaut pour catégories non configurées
PerformanceConfig.SLOW_THRESHOLD_MS = 150  # Au lieu de 200ms
```

---

## Rapports et statistiques

### Afficher un rapport console

```python
from core.utils.performance_monitor import print_performance_report

# À la fin de l'exécution ou sur demande
print_performance_report()
```

**Output** :
```
================================================================================
 RAPPORT DE PERFORMANCE EMAC
================================================================================
Total opérations      : 127
Opérations lentes     : 8
Pourcentage lent      : 6.3%

Par catégorie:
--------------------------------------------------------------------------------
  login          :   15 ops, avg   45.3ms,   0 slow
  query          :   87 ops, avg   32.1ms,   5 slow
  dialog         :   18 ops, avg  215.6ms,   3 slow
  cache          :    7 ops, avg    0.8ms,   0 slow
================================================================================
```

### Obtenir les statistiques programmatiquement

```python
from core.utils.performance_monitor import get_stats, get_summary

# Stats détaillées
stats = get_stats('query')  # Filtrer par catégorie
all_stats = get_stats()  # Toutes les stats

# Résumé
summary = get_summary()
print(f"Opérations lentes: {summary['slow_operations']}")
print(f"Pourcentage: {summary['slow_percentage']:.1f}%")
```

### Exporter en CSV

```python
from core.utils.performance_monitor import export_performance_stats

# Exporter dans exports/performance_stats.csv
export_performance_stats()

# Nom personnalisé
export_performance_stats('perf_2026_01_07.csv')
```

**Format CSV** :
```csv
Category,Operation,Count,Avg (ms),Min (ms),Max (ms),Slow Count
query,Load Personnel,45,28.50,15.20,95.30,2
query,Load Polyvalence,32,42.10,18.50,125.60,3
dialog,Personnel Dialog,12,245.30,180.20,315.40,1
...
```

---

## Intégration dans EMAC

### 1. Monitorer l'authentification

**Fichier** : `App/core/services/auth_service.py`

```python
from core.utils.performance_monitor import monitor_login_time

@monitor_login_time
def authenticate_user(username, password):
    """Authentifie un utilisateur"""
    # ... code existant ...
    return user
```

### 2. Monitorer les requêtes clés

**Fichier** : `App/core/services/evaluation_service.py`

```python
from core.utils.performance_monitor import monitor_query

@monitor_query('Get Evaluations Overdue')
def get_evaluations_en_retard():
    """Récupère les évaluations en retard"""
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT p.*, pers.nom, pers.prenom, pos.poste_code
            FROM polyvalence p
            JOIN personnel pers ON p.operateur_id = pers.id
            JOIN postes pos ON p.poste_id = pos.id
            WHERE p.prochaine_evaluation < CURDATE()
            AND pers.statut = 'ACTIF'
        """)
        return cur.fetchall()
```

### 3. Monitorer l'ouverture de dialogs

**Fichier** : `App/core/gui/gestion_personnel.py`

```python
from core.utils.performance_monitor import measure_dialog_time

class MainWindow(QMainWindow):
    def open_personnel_dialog(self):
        """Ouvre le dialog de gestion personnel"""
        with measure_dialog_time('Personnel Dialog'):
            dialog = GestionPersonnelDialog(self)
            dialog.exec_()
```

### 4. Monitorer le chargement initial

**Fichier** : `App/core/gui/main_qt.py`

```python
from core.utils.performance_monitor import PerformanceTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        with PerformanceTimer('Main Window Init', category='dialog'):
            self.setup_ui()
            self.load_initial_data()
```

### 5. Afficher le rapport au shutdown

**Fichier** : `App/core/gui/main_qt.py`

```python
from core.utils.performance_monitor import print_performance_report

class MainWindow(QMainWindow):
    def closeEvent(self, event):
        """Appelé à la fermeture de l'app"""
        # Afficher le rapport de performance
        print_performance_report()

        # ... reste du code ...
        super().closeEvent(event)
```

---

## Bonnes pratiques

### ✅ À FAIRE

#### 1. Monitorer les opérations critiques

```python
# ✅ BON - Monitorer login
@monitor_login_time
def authenticate(username, password):
    # ...

# ✅ BON - Monitorer requêtes fréquentes
@monitor_query('Load Dashboard Data')
def load_dashboard():
    # ...

# ✅ BON - Monitorer dialogs principaux
@monitor_dialog('Main Settings')
def open_settings():
    # ...
```

#### 2. Noms descriptifs

```python
# ✅ BON - Nom clair
@monitor_query('Load Personnel Actif')
def load_personnel_actif():
    # ...

# ❌ MAUVAIS - Nom vague
@monitor_query('Load Data')
def load_stuff():
    # ...
```

#### 3. Seuils appropriés

```python
# ✅ BON - Seuil adapté
@monitor_performance('Export Large CSV', category='export', threshold_ms=5000)
def export_full_database():
    # Export peut prendre du temps

# ❌ MAUVAIS - Seuil trop strict
@monitor_performance('Export Large CSV', category='export', threshold_ms=100)
def export_full_database():
    # Alertera toujours
```

#### 4. Rapport en fin de session

```python
# ✅ BON - Voir les performances après tests
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    exit_code = app.exec_()

    # Afficher rapport avant quitter
    print_performance_report()

    sys.exit(exit_code)
```

### ❌ À ÉVITER

#### 1. Sur-monitoring

```python
# ❌ MAUVAIS - Trop granulaire
@monitor_performance('Add 1+1')
def add(a, b):
    return a + b  # Overhead du monitoring > temps de la fonction !
```

#### 2. Monitoring dans des boucles

```python
# ❌ MAUVAIS - Overhead énorme
for item in items:
    with PerformanceTimer('Process Item'):  # 1000x overhead !
        process_item(item)

# ✅ MEILLEUR - Monitorer toute la boucle
with PerformanceTimer('Process All Items'):
    for item in items:
        process_item(item)
```

#### 3. Oublier de désactiver en production

```python
# ⚠️ ATTENTION - Peut impacter les perfs
# Désactiver si vraiment nécessaire
from core.utils.performance_monitor import disable_monitoring

if production_mode:
    disable_monitoring()  # Désactive tous les monitors
```

---

## Exemple complet

### Scénario : Monitorer une fonctionnalité complète

**Fichier** : `App/core/services/polyvalence_service.py`

```python
from core.db.configbd import DatabaseCursor
from core.utils.performance_monitor import (
    monitor_query,
    measure_query_time,
    PerformanceTimer
)


@monitor_query('Load Polyvalence By Operateur')
def load_polyvalence_by_operateur(operateur_id):
    """Charge la polyvalence d'un opérateur"""
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT p.*, pos.poste_code, pos.nom as poste_nom
            FROM polyvalence p
            JOIN postes pos ON p.poste_id = pos.id
            WHERE p.operateur_id = %s
        """, (operateur_id,))
        return cur.fetchall()


@monitor_query('Update Polyvalence Niveau')
def update_niveau(polyvalence_id, nouveau_niveau):
    """Met à jour le niveau de polyvalence"""
    with DatabaseCursor() as cur:
        cur.execute("""
            UPDATE polyvalence
            SET niveau = %s, date_evaluation = NOW()
            WHERE id = %s
        """, (nouveau_niveau, polyvalence_id))


def process_evaluations_batch(evaluations):
    """Traite un lot d'évaluations"""
    with PerformanceTimer('Process Evaluations Batch', category='other'):
        for eval_data in evaluations:
            update_niveau(eval_data['id'], eval_data['nouveau_niveau'])

        # Log batch dans historique
        with measure_query_time('Log Evaluations Batch'):
            from core.services.optimized_db_logger import log_hist_async
            log_hist_async(
                'BATCH_EVAL',
                'polyvalence',
                None,
                f"Batch de {len(evaluations)} évaluations"
            )
```

**Résultat** :
- ✅ Toutes les requêtes DB monitorées
- ✅ Alerte si > 100ms
- ✅ Statistiques par opération
- ✅ Rapport global disponible

---

## Seuils recommandés

| Catégorie | Seuil | Justification |
|-----------|-------|---------------|
| **login** | 500ms | Authentification peut interroger AD/LDAP |
| **query** | 100ms | Requêtes DB doivent être rapides |
| **dialog** | 300ms | UI doit s'afficher rapidement |
| **cache** | 10ms | Cache hit doit être instantané |
| **export** | 2000ms | Export peut traiter beaucoup de données |
| **other** | 200ms | Défaut raisonnable |

---

## ✅ Checklist d'intégration

### Monitoring de base

- [ ] Monitorer authenticate() (login)
- [ ] Monitorer 5-10 requêtes DB clés
- [ ] Monitorer ouverture dialogs principaux
- [ ] Afficher rapport au shutdown

### Monitoring avancé

- [ ] Monitorer cache hits/misses
- [ ] Monitorer exports (CSV, PDF, Excel)
- [ ] Monitorer imports de données
- [ ] Exporter stats régulièrement

### Configuration

- [ ] Ajuster seuils selon besoins
- [ ] Désactiver en prod si nécessaire
- [ ] Logger les alertes dans fichier

### Analyse

- [ ] Analyser le rapport hebdomadaire
- [ ] Identifier les régressions
- [ ] Optimiser les opérations lentes
- [ ] Mettre à jour les seuils

---

**Date** : 2026-01-07
**Contact** : Équipe EMAC
