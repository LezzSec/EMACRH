# Monitoring des Performances - GUIDE RAPIDE

**Date** : 2026-01-07
**Impact** : ✅ Détection proactive des régressions

---

## ✅ Ce qui a été fait

### Système de monitoring complet 

**Fichier** : [`App/core/utils/performance_monitor.py`](App/core/utils/performance_monitor.py)

- ✅ **PerformanceMonitor** - Singleton thread-safe
- ✅ **Décorateurs** - @monitor_*, @monitor_query, @monitor_dialog
- ✅ **Context managers** - PerformanceTimer, measure_*_time
- ✅ **Seuils configurables** - Par catégorie d'opération
- ✅ **Alertes automatiques** - Console + logs si > seuil
- ✅ **Statistiques** - Agrégation en temps réel
- ✅ **Rapports** - print_performance_report()
- ✅ **Export CSV** - export_performance_stats()

### Script de démonstration 

**Fichier** : [`App/scripts/demo_performance_monitoring.py`](App/scripts/demo_performance_monitoring.py)

- ✅ Exemples concrets d'utilisation
- ✅ Tests avec alertes
- ✅ Rapport et export

### Documentation complète 

**Fichier** : [`docs/dev/monitoring-performance.md`](docs/dev/monitoring-performance.md)

- Guide complet (30+ pages)
- Exemples d'intégration
- Bonnes pratiques

---

## Catégories et seuils

| Catégorie | Seuil | Usage |
|-----------|-------|-------|
| **login** | 500ms | Authentification |
| **query** | 100ms | Requêtes DB |
| **dialog** | 300ms | Ouverture dialogs |
| **cache** | 10ms | Cache hits |
| **export** | 2000ms | Exports fichiers |
| **other** | 200ms | Défaut |

---

## Utilisation

### Cas 1 : Monitorer le login

```python
from core.utils.performance_monitor import monitor_login_time

@monitor_login_time
def authenticate(username, password):
    """Authentifie un utilisateur"""
    user = get_user(username)
    if user and verify_password(password, user['password_hash']):
        return user
    return None

# Si > 500ms → ⚠️ ALERTE: "SLOW LOGIN: Login took 650ms (threshold: 500ms)"
```

### Cas 2 : Monitorer une requête DB

```python
from core.utils.performance_monitor import monitor_query

@monitor_query('Load Personnel Actif')
def load_personnel_actif():
    """Charge le personnel actif"""
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("SELECT * FROM personnel WHERE statut = 'ACTIF'")
        return cur.fetchall()

# Si > 100ms → ⚠️ ALERTE: "SLOW QUERY: Load Personnel Actif took 150ms (threshold: 100ms)"
```

### Cas 3 : Monitorer l'ouverture d'un dialog

```python
from core.utils.performance_monitor import monitor_dialog

class MainWindow(QMainWindow):
    @monitor_dialog('Personnel Dialog')
    def open_personnel_dialog(self):
        """Ouvre le dialog de gestion personnel"""
        dialog = GestionPersonnelDialog(self)
        dialog.exec_()

# Si > 300ms → ⚠️ ALERTE: "SLOW DIALOG: Personnel Dialog took 450ms (threshold: 300ms)"
```

### Cas 4 : Context manager pour blocs de code

```python
from core.utils.performance_monitor import PerformanceTimer, measure_query_time

# Générique
def complex_operation():
    with PerformanceTimer('Complex Operation', category='other'):
        step1()
        step2()
        step3()

# Spécialisé pour requêtes
def load_data():
    with measure_query_time('Load Evaluations'):
        cur.execute("SELECT * FROM polyvalence WHERE ...")
        return cur.fetchall()
```

### Cas 5 : Afficher le rapport

```python
from core.utils.performance_monitor import print_performance_report

# À la fin de l'exécution
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

### Cas 6 : Exporter les stats en CSV

```python
from core.utils.performance_monitor import export_performance_stats

# Export dans exports/performance_stats.csv
export_performance_stats()

# Nom personnalisé
export_performance_stats('perf_2026_01_07.csv')
```

---

## Intégration dans EMAC

### 1. Authentification

**Fichier** : `App/core/services/auth_service.py`

```python
from core.utils.performance_monitor import monitor_login_time

@monitor_login_time
def authenticate_user(username, password):
    # ... code existant ...
    return user
```

### 2. Requêtes clés

**Fichier** : `App/core/services/evaluation_service.py`

```python
from core.utils.performance_monitor import monitor_query

@monitor_query('Get Evaluations Overdue')
def get_evaluations_en_retard():
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT p.*, pers.nom, pers.prenom, pos.poste_code
            FROM polyvalence p
            JOIN personnel pers ON p.operateur_id = pers.id
            JOIN postes pos ON p.poste_id = pos.id
            WHERE p.prochaine_evaluation < CURDATE()
        """)
        return cur.fetchall()
```

### 3. Dialogs

**Fichier** : `App/core/gui/gestion_personnel.py`

```python
from core.utils.performance_monitor import measure_dialog_time

class MainWindow(QMainWindow):
    def open_personnel_dialog(self):
        with measure_dialog_time('Personnel Dialog'):
            dialog = GestionPersonnelDialog(self)
            dialog.exec_()
```

### 4. Rapport au shutdown

**Fichier** : `App/core/gui/main_qt.py`

```python
from core.utils.performance_monitor import print_performance_report, export_performance_stats

class MainWindow(QMainWindow):
    def closeEvent(self, event):
        # Rapport de performance
        print_performance_report()

        # Export stats
        export_performance_stats('session_stats.csv')

        # ... reste du code ...
        super().closeEvent(event)
```

---

## Configuration

### Modifier les seuils

```python
from core.utils.performance_monitor import set_threshold, PerformanceConfig

# Modifier un seuil spécifique
set_threshold('query', 50)  # Requêtes doivent être < 50ms

# Modifier le seuil global
PerformanceConfig.SLOW_THRESHOLD_MS = 150
```

### Désactiver temporairement

```python
from core.utils.performance_monitor import disable_monitoring, enable_monitoring

# Désactiver
disable_monitoring()

# Réactiver
enable_monitoring()
```

---

## Exemple complet

### Scénario : Monitorer le chargement du dashboard

```python
from core.utils.performance_monitor import (
    monitor_query,
    measure_dialog_time,
    PerformanceTimer
)

class MainWindow(QMainWindow):
    def load_dashboard(self):
        """Charge les données du dashboard"""
        with PerformanceTimer('Load Dashboard', category='other'):
            # Charge personnel
            personnel = self.load_personnel_data()

            # Charge évaluations
            evaluations = self.load_evaluations_data()

            # Charge contrats
            contrats = self.load_contrats_data()

            # Affiche
            self.populate_dashboard(personnel, evaluations, contrats)

    @monitor_query('Dashboard Personnel')
    def load_personnel_data(self):
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("SELECT COUNT(*) as total FROM personnel WHERE statut = 'ACTIF'")
            return cur.fetchone()

    @monitor_query('Dashboard Evaluations')
    def load_evaluations_data(self):
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT COUNT(*) as total
                FROM polyvalence
                WHERE prochaine_evaluation < CURDATE()
            """)
            return cur.fetchone()

    @monitor_query('Dashboard Contrats')
    def load_contrats_data(self):
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("""
                SELECT COUNT(*) as total
                FROM contrats
                WHERE date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            """)
            return cur.fetchone()
```

**Résultat** :
- ✅ Chaque requête monitorée séparément
- ✅ Temps total du dashboard mesuré
- ✅ Alertes si une partie est lente
- ✅ Stats détaillées disponibles

---

## Tests

### Tester le monitoring

```bash
cd App\scripts
python demo_performance_monitoring.py
```

**Output attendu** :
```
 DÉMONSTRATION DU MONITORING DE PERFORMANCE
================================================================================

1️⃣ Test Login (threshold: 500ms)
  Authenticating john.doe...
  ✅ User john.doe authenticated

2️⃣ Test Requêtes DB (threshold: 100ms)
  Loading personnel...
  ✅ Personnel loaded

...

⚠️ SLOW QUERY: Slow Query took 250ms (threshold: 100ms)

 RAPPORT DE PERFORMANCE EMAC
================================================================================
...
```

---

## ✅ Bonnes pratiques

### ✅ À FAIRE

1. **Monitorer les opérations critiques** :
   ```python
   @monitor_login_time  # Login
   @monitor_query  # Requêtes fréquentes
   @monitor_dialog  # Dialogs principaux
   ```

2. **Noms descriptifs** :
   ```python
   @monitor_query('Load Personnel Actif')  # ✅ Clair
   # vs
   @monitor_query('Load Data')  # ❌ Vague
   ```

3. **Rapport en fin de session** :
   ```python
   def closeEvent(self, event):
       print_performance_report()
       export_performance_stats()
   ```

4. **Analyser régulièrement** :
   - Vérifier le rapport hebdomadaire
   - Identifier les régressions
   - Optimiser les opérations lentes

### ❌ À ÉVITER

1. **Sur-monitoring** :
   ```python
   # ❌ Fonction trop petite
   @monitor_performance('Add Numbers')
   def add(a, b):
       return a + b  # Overhead > temps fonction
   ```

2. **Monitoring dans des boucles** :
   ```python
   # ❌ Overhead énorme
   for item in items:
       with PerformanceTimer('Item'):  # 1000x overhead !
           process(item)

   # ✅ Meilleur
   with PerformanceTimer('All Items'):
       for item in items:
           process(item)
   ```

---

## Documentation

-  [Guide complet](docs/dev/monitoring-performance.md) - 30+ pages
-  [performance_monitor.py](App/core/utils/performance_monitor.py) - Code source
-  [demo_performance_monitoring.py](App/scripts/demo_performance_monitoring.py) - Démo

---

## Résumé

### API

```python
# Décorateurs
from core.utils.performance_monitor import (
    monitor_login_time,      # Pour login
    monitor_query,           # Pour requêtes DB
    monitor_dialog,          # Pour dialogs
    monitor_performance      # Générique
)

# Context managers
from core.utils.performance_monitor import (
    PerformanceTimer,        # Générique
    measure_query_time,      # Pour requêtes
    measure_dialog_time      # Pour dialogs
)

# Rapports
from core.utils.performance_monitor import (
    print_performance_report,   # Affiche rapport
    export_performance_stats,   # Export CSV
    get_stats,                  # Stats programmatiques
    get_summary                 # Résumé
)
```

### Seuils

- **login** : 500ms
- **query** : 100ms
- **dialog** : 300ms
- **cache** : 10ms
- **export** : 2000ms

### Alertes

Si opération > seuil :
```
⚠️ SLOW QUERY: Load Personnel took 150ms (threshold: 100ms)
```

---

**Règle d'or** : **Monitorer = Détecter les régressions = Performance stable**

**Contact** : Équipe EMAC
