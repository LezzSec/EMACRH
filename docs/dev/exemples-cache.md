# 📚 Exemples d'utilisation du système de cache EMAC

**Date**: 2026-01-07
**Module**: `core.utils.cache` & `core.utils.emac_cache`

---

## 🎯 Table des matières

1. [Exemples de base](#exemples-de-base)
2. [Cas d'usage par module](#cas-dusage-par-module)
3. [Patterns avancés](#patterns-avancés)
4. [Migration du code existant](#migration-du-code-existant)
5. [Debugging et monitoring](#debugging-et-monitoring)

---

## Exemples de base

### 1. Utiliser un wrapper de cache simple

```python
from core.utils.emac_cache import get_cached_postes

# ✅ C'est tout ! Le cache est géré automatiquement
postes = get_cached_postes()

# Premier appel → Requête DB + mise en cache (50ms)
# Appels suivants (< 10 min) → Cache uniquement (0.05ms)
```

### 2. Invalider le cache après modification

```python
from core.utils.emac_cache import (
    get_cached_postes,
    invalidate_postes_cache
)

# Charger les postes
postes = get_cached_postes()

# Modifier un poste dans la DB
with DatabaseCursor() as cur:
    cur.execute(
        "UPDATE postes SET nom = %s WHERE id = %s",
        ("Nouveau nom", 123)
    )

# ✅ Invalider le cache pour forcer le rechargement
invalidate_postes_cache()

# Prochain appel rechargera depuis la DB
postes = get_cached_postes()  # Données fraîches
```

### 3. Utiliser le décorateur d'invalidation automatique

```python
from core.utils.emac_cache import (
    get_cached_postes,
    invalidate_postes_on_change
)

@invalidate_postes_on_change
def update_poste(poste_id, nom):
    """Met à jour un poste et invalide automatiquement le cache"""
    with DatabaseCursor() as cur:
        cur.execute(
            "UPDATE postes SET nom = %s WHERE id = %s",
            (nom, poste_id)
        )
    # ✅ Cache invalidé automatiquement après l'exécution

# Utilisation
update_poste(123, "Nouveau nom")
postes = get_cached_postes()  # Données fraîches
```

---

## Cas d'usage par module

### Module: Gestion Personnel

#### Charger le personnel actif

```python
from core.utils.emac_cache import get_cached_personnel_actifs

class GestionPersonnelDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_personnel()

    def load_personnel(self):
        """Charge le personnel avec cache"""
        # ✅ Utilise le cache (TTL: 1 minute)
        personnel = get_cached_personnel_actifs()

        # Peupler le tableau
        self.table.setRowCount(len(personnel))
        for i, person in enumerate(personnel):
            self.table.setItem(i, 0, QTableWidgetItem(person['matricule']))
            self.table.setItem(i, 1, QTableWidgetItem(person['nom']))
            self.table.setItem(i, 2, QTableWidgetItem(person['prenom']))
```

#### Ajouter un employé avec invalidation

```python
from core.utils.emac_cache import invalidate_personnel_on_change

@invalidate_personnel_on_change
def add_personnel(nom, prenom, matricule):
    """Ajoute un employé et invalide le cache automatiquement"""
    with DatabaseCursor() as cur:
        cur.execute("""
            INSERT INTO personnel (nom, prenom, matricule, statut)
            VALUES (%s, %s, %s, 'ACTIF')
        """, (nom, prenom, matricule))
        return cur.lastrowid

# Utilisation dans le dialog
def on_save_clicked(self):
    # Sauvegarder
    person_id = add_personnel(
        self.nom_input.text(),
        self.prenom_input.text(),
        self.matricule_input.text()
    )

    # ✅ Cache déjà invalidé par le décorateur
    # Recharger la liste
    self.load_personnel()  # Charge les données fraîches

    QMessageBox.information(self, "Succès", "Employé ajouté avec succès")
```

### Module: Gestion Postes

#### Charger les postes dans un combo

```python
from core.utils.emac_cache import get_cached_postes_actifs

class EvaluationDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.populate_poste_combo()

    def populate_poste_combo(self):
        """Peuple le combo des postes avec cache"""
        # ✅ Utilise le cache (TTL: 10 minutes)
        postes = get_cached_postes_actifs()

        self.poste_combo.clear()
        for poste in postes:
            # Format: "0506 - Assemblage"
            text = f"{poste['poste_code']} - {poste['nom']}"
            self.poste_combo.addItem(text, poste['id'])
```

#### Modifier un poste avec invalidation manuelle

```python
from core.utils.emac_cache import invalidate_postes_cache

class ModifyPosteDialog(QDialog):
    def save_changes(self):
        """Sauvegarde les modifications du poste"""
        with DatabaseCursor() as cur:
            cur.execute("""
                UPDATE postes
                SET nom = %s, atelier_id = %s
                WHERE id = %s
            """, (
                self.nom_input.text(),
                self.atelier_combo.currentData(),
                self.poste_id
            ))

        # ✅ Invalider le cache manuellement
        invalidate_postes_cache()

        # Notifier et fermer
        QMessageBox.information(self, "Succès", "Poste modifié")
        self.accept()
```

### Module: Permissions et Authentification

#### Vérifier les permissions avec cache

```python
from core.utils.emac_cache import get_cached_user_permissions

class MainWindow(QMainWindow):
    def check_permission(self, module: str, action: str) -> bool:
        """Vérifie si l'utilisateur a la permission"""
        # ✅ Utilise le cache (TTL: 5 minutes)
        permissions = get_cached_user_permissions()

        if module not in permissions:
            return False

        return permissions[module].get(action, False)

    def setup_menus(self):
        """Configure les menus selon les permissions"""
        # Vérifier les permissions pour chaque menu
        if self.check_permission('personnel', 'ecriture'):
            self.menu_add_personnel.setEnabled(True)
        else:
            self.menu_add_personnel.setEnabled(False)

        if self.check_permission('evaluations', 'lecture'):
            self.menu_evaluations.setEnabled(True)
        else:
            self.menu_evaluations.setEnabled(False)
```

#### Charger l'utilisateur courant

```python
from core.utils.emac_cache import get_cached_current_user

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_user_info()

    def load_user_info(self):
        """Charge les infos de l'utilisateur courant"""
        # ✅ Utilise le cache (TTL: 1 minute)
        user = get_cached_current_user()

        if user:
            self.status_bar.showMessage(
                f"Connecté: {user['prenom']} {user['nom']} ({user['role_nom']})"
            )
            self.user_label.setText(f"{user['prenom'][0]}. {user['nom']}")
```

### Module: Listes statiques (Rôles, Ateliers)

#### Peupler un combo d'ateliers

```python
from core.utils.emac_cache import get_cached_ateliers

class AddPosteDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.populate_atelier_combo()

    def populate_atelier_combo(self):
        """Peuple le combo des ateliers avec cache"""
        # ✅ Utilise le cache (TTL: 1 heure - changent rarement)
        ateliers = get_cached_ateliers()

        self.atelier_combo.clear()
        self.atelier_combo.addItem("-- Sélectionner --", None)

        for atelier in ateliers:
            self.atelier_combo.addItem(atelier['nom'], atelier['id'])
```

#### Peupler un combo de rôles

```python
from core.utils.emac_cache import get_cached_roles

class UserManagementDialog(QDialog):
    def populate_role_combo(self):
        """Peuple le combo des rôles avec cache"""
        # ✅ Utilise le cache (TTL: 1 heure)
        roles = get_cached_roles()

        self.role_combo.clear()
        for role in roles:
            self.role_combo.addItem(
                f"{role['nom']} - {role['description']}",
                role['id']
            )
```

### Module: Cache d'écran (Dialog State)

#### Sauvegarder l'état d'un dialog

```python
from core.utils.emac_cache import ScreenCache

class GestionPersonnelDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.restore_state()  # ✅ Restaurer l'état sauvegardé

    def restore_state(self):
        """Restaure l'état sauvegardé du dialog"""
        state = ScreenCache.get_state('gestion_personnel')

        if state:
            # Restaurer les filtres
            if 'filter_statut' in state:
                index = self.statut_combo.findText(state['filter_statut'])
                if index >= 0:
                    self.statut_combo.setCurrentIndex(index)

            # Restaurer la sélection
            if 'selected_id' in state:
                self.select_row_by_id(state['selected_id'])

            # Restaurer la position de scroll
            if 'scroll_position' in state:
                self.table.verticalScrollBar().setValue(state['scroll_position'])

    def closeEvent(self, event):
        """Sauvegarde l'état avant fermeture"""
        # ✅ Sauvegarder l'état pour la prochaine ouverture
        state = {
            'filter_statut': self.statut_combo.currentText(),
            'selected_id': self.get_selected_id(),
            'scroll_position': self.table.verticalScrollBar().value()
        }
        ScreenCache.save_state('gestion_personnel', state)

        super().closeEvent(event)
```

#### Cache d'écran avec expiration courte

```python
from core.utils.emac_cache import ScreenCache
from core.utils.cache import CacheTTL

class RapportDialog(QDialog):
    def closeEvent(self, event):
        """Sauvegarde temporaire (5 minutes seulement)"""
        state = {
            'date_debut': self.date_debut.date().toString('yyyy-MM-dd'),
            'date_fin': self.date_fin.date().toString('yyyy-MM-dd'),
            'format': self.format_combo.currentText()
        }

        # ✅ TTL court car les rapports changent souvent
        ScreenCache.save_state('rapport_dialog', state, ttl=CacheTTL.MINUTE_5)

        super().closeEvent(event)
```

---

## Patterns avancés

### Pattern 1: Cache avec fallback

```python
from core.utils.emac_cache import get_cached_postes

def load_postes_safe():
    """Charge les postes avec fallback si erreur"""
    try:
        postes = get_cached_postes()
        return postes
    except Exception as e:
        print(f"❌ Erreur cache: {e}")
        # Fallback: Requête directe sans cache
        from core.db.configbd import DatabaseCursor
        with DatabaseCursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM postes WHERE statut = 'ACTIF'")
            return cur.fetchall()
```

### Pattern 2: Préchargement au démarrage

```python
from core.utils.emac_cache import warm_up_cache
from PyQt5.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

        # ✅ Précharger le cache après 500ms (éviter de bloquer l'ouverture)
        QTimer.singleShot(500, self.warm_up_cache)

    def warm_up_cache(self):
        """Précharge les données courantes"""
        from core.utils.emac_cache import warm_up_cache

        try:
            warm_up_cache()
            print("✅ Cache préchauffé avec succès")
        except Exception as e:
            print(f"⚠️ Erreur préchargement cache: {e}")
```

### Pattern 3: Invalidation en cascade

```python
from core.utils.emac_cache import (
    invalidate_postes_cache,
    invalidate_personnel_cache
)

def archive_atelier(atelier_id):
    """Archive un atelier et invalide tous les caches associés"""
    with DatabaseCursor() as cur:
        # Archiver l'atelier
        cur.execute(
            "UPDATE atelier SET statut = 'ARCHIVE' WHERE id = %s",
            (atelier_id,)
        )

        # Désactiver les postes liés
        cur.execute(
            "UPDATE postes SET statut = 'INACTIF' WHERE atelier_id = %s",
            (atelier_id,)
        )

    # ✅ Invalider en cascade
    invalidate_postes_cache()  # Les postes ont changé
    # Le personnel peut être affecté (si lié aux postes)
    invalidate_personnel_cache()
```

### Pattern 4: Cache conditionnel

```python
from core.utils.cache import CacheManager, CacheTTL

def get_postes_by_atelier(atelier_id: int, use_cache: bool = True):
    """Charge les postes d'un atelier avec option de cache"""
    cache = CacheManager.get_instance()
    key = f"postes:atelier:{atelier_id}"

    if use_cache:
        # ✅ Essayer le cache d'abord
        cached = cache.get(key)
        if cached is not None:
            return cached

    # Charger depuis DB
    from core.db.configbd import DatabaseCursor
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute(
            "SELECT * FROM postes WHERE atelier_id = %s AND statut = 'ACTIF'",
            (atelier_id,)
        )
        postes = cur.fetchall()

    # Mettre en cache
    if use_cache:
        cache.set(key, postes, ttl=CacheTTL.MEDIUM, namespace='postes')

    return postes
```

### Pattern 5: Monitoring des performances

```python
from core.utils.emac_cache import get_cache_stats

class MainWindow(QMainWindow):
    def show_cache_stats(self):
        """Affiche les statistiques de cache dans une dialog"""
        stats = get_cache_stats()

        msg = f"""
📊 Statistiques du cache

Hits: {stats['hits']}
Misses: {stats['misses']}
Hit Rate: {stats['hit_rate']:.1f}%
Entrées: {stats['size']}

Taille mémoire: {stats['memory_usage_mb']:.2f} MB
        """

        QMessageBox.information(self, "Cache Stats", msg.strip())
```

---

## Migration du code existant

### Avant: Code sans cache

```python
# ❌ Ancien code - Requête DB à chaque fois
class GestionEvaluationDialog(QDialog):
    def populate_poste_combo(self):
        """Peuple le combo des postes"""
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT p.id, p.poste_code, p.nom
                FROM postes p
                WHERE p.statut = 'ACTIF'
                ORDER BY p.poste_code
            """)
            postes = cur.fetchall()

            self.poste_combo.clear()
            for poste in postes:
                text = f"{poste['poste_code']} - {poste['nom']}"
                self.poste_combo.addItem(text, poste['id'])
        finally:
            cur.close()
            conn.close()
```

### Après: Code avec cache

```python
# ✅ Nouveau code - Utilise le cache
from core.utils.emac_cache import get_cached_postes_actifs

class GestionEvaluationDialog(QDialog):
    def populate_poste_combo(self):
        """Peuple le combo des postes avec cache"""
        # ✅ Simple et rapide
        postes = get_cached_postes_actifs()

        self.poste_combo.clear()
        for poste in postes:
            text = f"{poste['poste_code']} - {poste['nom']}"
            self.poste_combo.addItem(text, poste['id'])
```

### Migration étape par étape

**Étape 1**: Identifier les requêtes répétitives

```python
# Chercher dans le code:
# - cur.execute("SELECT * FROM postes WHERE ...")
# - cur.execute("SELECT * FROM personnel WHERE statut = 'ACTIF'")
# - cur.execute("SELECT * FROM roles ...")
```

**Étape 2**: Remplacer par les wrappers de cache

```python
# Avant
cur.execute("SELECT * FROM postes WHERE statut = 'ACTIF'")
postes = cur.fetchall()

# Après
from core.utils.emac_cache import get_cached_postes_actifs
postes = get_cached_postes_actifs()
```

**Étape 3**: Ajouter l'invalidation

```python
# Chercher les UPDATE/INSERT/DELETE sur ces tables
# Ajouter le décorateur ou l'invalidation manuelle

# Avant
def update_poste(poste_id, nom):
    cur.execute("UPDATE postes SET nom = %s WHERE id = %s", (nom, poste_id))

# Après
from core.utils.emac_cache import invalidate_postes_on_change

@invalidate_postes_on_change
def update_poste(poste_id, nom):
    cur.execute("UPDATE postes SET nom = %s WHERE id = %s", (nom, poste_id))
```

**Étape 4**: Tester

```python
# Vérifier que:
# 1. Les données sont bien chargées
# 2. Les modifications sont bien reflétées (cache invalidé)
# 3. Le hit rate est > 80% (voir monitoring)
```

---

## Debugging et monitoring

### Afficher l'état du cache

```python
from core.utils.cache import print_cache_stats

# ✅ Affiche les stats détaillées dans la console
print_cache_stats()
```

**Output:**
```
============================================================
📊 Cache Statistics
============================================================
Total Entries : 12
Total Hits    : 487
Total Misses  : 23
Hit Rate      : 95.5%
Memory Usage  : 0.34 MB
============================================================
Top 5 Most Hit Keys:
  1. postes:all (142 hits, TTL: 600s)
  2. roles:all (89 hits, TTL: 3600s)
  3. personnel:actifs (76 hits, TTL: 60s)
  4. permissions:user:5 (54 hits, TTL: 300s)
  5. ateliers:all (43 hits, TTL: 3600s)
============================================================
```

### Vider le cache pour debugging

```python
from core.utils.emac_cache import invalidate_all_caches

# ⚠️ À utiliser uniquement pour debugging
invalidate_all_caches()
print("✅ Tous les caches ont été vidés")
```

### Logger les accès au cache

```python
from core.utils.cache import CacheManager

class DebugCacheManager(CacheManager):
    """Version debug avec logging des accès"""

    def get(self, key: str, default=None):
        result = super().get(key, default)
        if result is not None:
            print(f"✅ Cache HIT: {key}")
        else:
            print(f"❌ Cache MISS: {key}")
        return result
```

### Test de performance

```python
import time
from core.utils.emac_cache import get_cached_postes

# Test sans cache (requête directe)
start = time.time()
from core.db.configbd import DatabaseCursor
with DatabaseCursor(dictionary=True) as cur:
    cur.execute("SELECT * FROM postes WHERE statut = 'ACTIF'")
    postes = cur.fetchall()
time_no_cache = (time.time() - start) * 1000

# Test avec cache (premier appel)
from core.utils.emac_cache import invalidate_postes_cache
invalidate_postes_cache()
start = time.time()
postes = get_cached_postes()
time_first_call = (time.time() - start) * 1000

# Test avec cache (appel suivant)
start = time.time()
postes = get_cached_postes()
time_cached = (time.time() - start) * 1000

print(f"""
📊 Test de performance:
Sans cache    : {time_no_cache:.2f}ms
Premier appel : {time_first_call:.2f}ms
Depuis cache  : {time_cached:.2f}ms
Gain          : {time_no_cache / time_cached:.0f}x plus rapide
""")
```

**Output typique:**
```
📊 Test de performance:
Sans cache    : 52.34ms
Premier appel : 53.12ms
Depuis cache  : 0.05ms
Gain          : 1047x plus rapide
```

---

## ✅ Checklist de migration

- [ ] Identifier les requêtes DB répétitives dans le module
- [ ] Remplacer par les wrappers de cache appropriés
- [ ] Ajouter l'invalidation après les modifications (UPDATE/INSERT/DELETE)
- [ ] Utiliser les décorateurs pour l'invalidation automatique
- [ ] Implémenter ScreenCache pour les dialogs fréquemment rouverts
- [ ] Tester que les données sont correctement chargées
- [ ] Tester que les modifications sont reflétées (cache invalidé)
- [ ] Vérifier le hit rate (> 80%)
- [ ] Monitorer la mémoire (< 10 MB pour l'app entière)
- [ ] Documenter les TTL choisis et les raisons

---

## 📚 Ressources

- [Guide complet du cache](optimisation-cache.md) - Documentation technique complète
- [Guide rapide](../../OPTIMISATIONS_CACHE_APPLIQUEES.md) - Référence rapide
- [Code source cache.py](../../App/core/utils/cache.py) - Système générique
- [Code source emac_cache.py](../../App/core/utils/emac_cache.py) - Wrappers EMAC

---

**Règle d'or**: **Cache = lecture rapide, Invalidation = données fraîches**

**Contact**: Équipe EMAC
