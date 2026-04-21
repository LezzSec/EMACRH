# PROMPT CLAUDE CODE — P4 Sécurité / Durcissement EMAC

## Contexte

Application EMAC : PyQt5/MySQL desktop app de gestion du personnel (~73K lignes, 214 fichiers Python).
Ce prompt couvre le **workstream P4 — Sécurité & Durcissement** : correction de 3 failles identifiées lors de l'audit perf+sécu d'avril 2026.

**État du code au moment de l'audit** :
- ✅ Chiffrement config corrigé (plus de clé embarquée)
- ✅ Accès DB unifié via `QueryExecutor` / `DatabaseConnection`
- ✅ Table `logs_tentatives_connexion` présente (migration 012)
- ✅ Logging configuré avec mode production (setup_logging dans `gui/main_qt.py`)
- ❌ **Rate limiting inexistant** : les tentatives échouées sont loggées mais jamais consultées
- ❌ **Session timeout défini mais jamais vérifié** : `UserSession.is_session_expired()` n'est appelée nulle part
- ❌ **Verbosité logs excessive** : `emac.log.2026-04-14` à 1.8 MB/jour suggère que le mode production n'est pas actif en prod

> **Règle générale** : chaque fix doit être minimal et chirurgical. Ne pas toucher au flow d'authentification au-delà du strict nécessaire. Ajouter les nouvelles fonctions dans des endroits isolés pour faciliter les tests.

---

## TÂCHE 1 — Rate limiting sur le login (brute-force protection)

**Problème** : dans `domain/services/admin/auth_service.py`, `_log_failed_attempt()` insère dans `logs_tentatives_connexion` mais **aucune fonction ne lit cette table pour bloquer les tentatives répétées**. Un attaquant peut enchaîner 10 000 tentatives sans friction autre que le coût bcrypt (~200ms/tentative côté serveur), ce qui ne protège pas contre une attaque distribuée ou un dictionnaire ciblé.

La table `logs_tentatives_connexion` a déjà les bons index (`idx_username`, `idx_attempt_time`, `idx_ip_address`) — zéro migration nécessaire.

### 1a. Ajouter une fonction `_check_rate_limit()` dans `auth_service.py`

À placer **juste après** `_log_failed_attempt()` (vers ligne 58). Règles :
- Fenêtre glissante de 15 minutes
- 5 tentatives échouées max par `username`
- 10 tentatives échouées max par `ip_address` (pour couvrir les attaques "username spraying")
- Retourne `(bloque: bool, seconds_to_wait: int, reason: str)`

```python
# Constantes rate limiting
_RATE_LIMIT_WINDOW_MINUTES = 15
_RATE_LIMIT_MAX_PER_USERNAME = 5
_RATE_LIMIT_MAX_PER_IP = 10


def _check_rate_limit(username: str, ip_address: str) -> Tuple[bool, int, str]:
    """
    Vérifie si la tentative de connexion doit être bloquée.

    Args:
        username: Nom d'utilisateur tenté
        ip_address: Identifiant machine cliente

    Returns:
        (blocked, seconds_to_wait, reason)
        blocked=True si la tentative doit être refusée immédiatement.
    """
    try:
        from datetime import timedelta
        window_start = datetime.now() - timedelta(minutes=_RATE_LIMIT_WINDOW_MINUTES)

        # Compteurs en une seule requête
        row = QueryExecutor.fetch_one(
            """SELECT
                 SUM(CASE WHEN username = %s THEN 1 ELSE 0 END) AS by_user,
                 SUM(CASE WHEN ip_address = %s THEN 1 ELSE 0 END) AS by_ip
               FROM logs_tentatives_connexion
               WHERE attempt_time >= %s""",
            (username, ip_address, window_start),
            dictionary=True,
        )
        by_user = int(row['by_user'] or 0) if row else 0
        by_ip = int(row['by_ip'] or 0) if row else 0

        if by_user >= _RATE_LIMIT_MAX_PER_USERNAME:
            return True, _RATE_LIMIT_WINDOW_MINUTES * 60, (
                f"Trop de tentatives échouées pour ce compte. "
                f"Réessayez dans {_RATE_LIMIT_WINDOW_MINUTES} minutes."
            )
        if by_ip >= _RATE_LIMIT_MAX_PER_IP:
            return True, _RATE_LIMIT_WINDOW_MINUTES * 60, (
                f"Trop de tentatives échouées depuis ce poste. "
                f"Réessayez dans {_RATE_LIMIT_WINDOW_MINUTES} minutes."
            )
        return False, 0, ""
    except Exception as e:
        # En cas d'erreur SQL on NE bloque PAS (disponibilité > sécurité stricte ici)
        logger.warning(f"check_rate_limit a échoué, bypass: {e}")
        return False, 0, ""
```

### 1b. Brancher le check dans `authenticate_user()`

Dans la même fonction (ligne ~211), **avant** l'ouverture de la connexion DB, insérer le check :

```python
@monitor_login_time
def authenticate_user(username: str, password: str) -> tuple[bool, Optional[str]]:
    """(docstring existante)"""
    try:
        # ─── NOUVEAU : rate limiting pré-check ───────────────────────────
        client_ip = _get_client_ip()
        blocked, _wait, reason = _check_rate_limit(username, client_ip)
        if blocked:
            _log_failed_attempt(username, "rate_limited")
            logger.warning(f"Login bloqué (rate limit): user={username}, ip={client_ip}")
            return False, reason
        # ────────────────────────────────────────────────────────────────

        with DatabaseConnection() as conn:
            cur = conn.cursor(dictionary=True)
            # ... reste inchangé
```

### 1c. Logger les tentatives échouées aux bons endroits

Dans `authenticate_user()`, le code actuel **ne log pas** les échecs via `_log_failed_attempt()`. Corriger les 3 branches d'échec :

```python
# Ligne ~245 : user introuvable
if not rows:
    cur.close()
    _log_failed_attempt(username, "user_not_found")   # ← AJOUTER
    return False, "Nom d'utilisateur ou mot de passe incorrect"

# Ligne ~251 : compte désactivé
if not user['actif']:
    cur.close()
    _log_failed_attempt(username, "account_inactive")   # ← AJOUTER
    return False, "Ce compte est désactivé. Contactez un administrateur."

# Ligne ~255 : mauvais mot de passe
if not verify_password(password, user['password_hash']):
    cur.close()
    _log_failed_attempt(username, "wrong_password")   # ← AJOUTER
    return False, "Nom d'utilisateur ou mot de passe incorrect"
```

### 1d. Nettoyer le `client_ip` dupliqué

Le code existant recalcule `client_ip = _get_client_ip()` vers la ligne 269 pour le `INSERT logs_connexion`. Après la modif 1b, `client_ip` est déjà calculé en haut de la fonction — supprimer la duplication :

```python
# AVANT (ligne ~269)
client_ip = _get_client_ip()
cur.execute(
    "INSERT INTO logs_connexion (utilisateur_id, date_connexion, ip_address) VALUES (%s, %s, %s)",
    (user['id'], datetime.now(), client_ip)
)

# APRÈS — client_ip vient du check rate limit en haut
cur.execute(
    "INSERT INTO logs_connexion (utilisateur_id, date_connexion, ip_address) VALUES (%s, %s, %s)",
    (user['id'], datetime.now(), client_ip)
)
```

### 1e. Test manuel

Après le fix, vérifier manuellement :
1. Lancer l'app, rentrer 5 fois un mauvais mot de passe pour `admin` → la 6ème tentative doit afficher le message de blocage **sans attendre les 200ms bcrypt** (donc feedback instantané = preuve que le check est bien avant `verify_password`).
2. En parallèle, vérifier dans MySQL :
```sql
SELECT username, reason, COUNT(*) FROM logs_tentatives_connexion
WHERE attempt_time >= NOW() - INTERVAL 15 MINUTE
GROUP BY username, reason;
```

---

## TÂCHE 2 — Brancher le session timeout

**Problème** : `UserSession` dans `auth_service.py` définit `SESSION_TIMEOUT_MINUTES = 30` et expose `is_session_expired()`, `update_activity()`, `get_remaining_time()` — mais **aucun code ne les appelle**. L'app reste ouverte 72h sur un poste sans re-authentification.

### 2a. Ajouter un `QTimer` global dans `MainWindow`

Fichier : `gui/main_qt.py`

Chercher la méthode `__init__` de `MainWindow` (la fin de l'initialisation, après tout le setup UI). Ajouter :

```python
# À la fin de MainWindow.__init__(), après que l'UI soit construite
from PyQt5.QtCore import QTimer
from domain.services.admin.auth_service import UserSession, logout_user

self._session_timer = QTimer(self)
self._session_timer.setInterval(60_000)  # Check toutes les minutes
self._session_timer.timeout.connect(self._check_session_expired)
self._session_timer.start()
```

Puis ajouter la méthode suivante dans `MainWindow` (où les autres slots sont définis) :

```python
def _check_session_expired(self):
    """Déconnecte l'utilisateur si la session a expiré par inactivité."""
    from domain.services.admin.auth_service import UserSession, logout_user
    from PyQt5.QtWidgets import QMessageBox

    if not UserSession.is_authenticated():
        return

    if UserSession.is_session_expired():
        self._session_timer.stop()
        logout_user()
        QMessageBox.information(
            self,
            "Session expirée",
            f"Votre session a expiré après "
            f"{UserSession.SESSION_TIMEOUT_MINUTES} minutes d'inactivité.\n\n"
            "Veuillez vous reconnecter."
        )
        self.close()
        # Relance du login
        from gui.screens.admin.login_dialog import LoginDialog
        from PyQt5.QtWidgets import QApplication
        login = LoginDialog()
        if login.exec_() == LoginDialog.Accepted:
            # Relancer une nouvelle MainWindow (l'ancienne est fermée)
            new_main = MainWindow()
            new_main.show()
        else:
            QApplication.instance().quit()
```

### 2b. Appeler `update_activity()` sur les interactions utilisateur

Le `QMainWindow.eventFilter` est le hook le plus simple. Dans `MainWindow.__init__`, ajouter :

```python
from PyQt5.QtCore import QEvent

# Filtre d'événements pour rafraîchir l'activité
QApplication.instance().installEventFilter(self)
```

Puis méthode :

```python
def eventFilter(self, obj, event):
    # Rafraîchir l'activité sur les interactions utilisateur réelles
    if event.type() in (QEvent.MouseButtonPress, QEvent.KeyPress):
        from domain.services.admin.auth_service import UserSession
        UserSession.update_activity()
    return super().eventFilter(obj, event)
```

### 2c. Rendre le timeout configurable via env

Dans `auth_service.py::UserSession` (ligne ~120), remplacer la constante en dur par une lecture env :

```python
# AVANT
SESSION_TIMEOUT_MINUTES = 30

# APRÈS
import os
SESSION_TIMEOUT_MINUTES = int(os.getenv('EMAC_SESSION_TIMEOUT_MINUTES', '30'))
```

Documenter dans `config/README.md` (ou créer la doc si elle manque) :
```
EMAC_SESSION_TIMEOUT_MINUTES=30   # Timeout inactivité en minutes (défaut: 30)
```

### 2d. Test manuel

1. Baisser temporairement `EMAC_SESSION_TIMEOUT_MINUTES=2` dans le `.env`.
2. Se connecter, laisser l'app ouverte sans la toucher 2 minutes.
3. Vérifier qu'une popup "Session expirée" apparaît et que l'écran de login se relance.
4. Remettre la valeur à 30 avant commit.

---

## TÂCHE 3 — Audit et réduction de la verbosité des logs

**Problème** : le fichier `logs/emac.log.2026-04-14` fait **1.8 MB pour une journée** d'utilisation. Avec un mode production correctement activé (niveau WARNING), on attend ~10-50 KB/jour. Deux hypothèses à vérifier :
1. `EMAC_ENV=production` n'est pas set sur les postes de prod → `setup_logging` tourne en mode DEV (niveau DEBUG)
2. Certains `logger.info()` sont appelés dans des boucles chaudes

### 3a. Diagnostic de verbosité

Depuis le dossier `App/`, exécuter et analyser :

```bash
# Compter les niveaux de log dans le plus gros fichier
grep -cE "\[DEBUG\]" logs/emac.log.2026-04-14
grep -cE "\[INFO\]" logs/emac.log.2026-04-14
grep -cE "\[WARNING\]" logs/emac.log.2026-04-14
grep -cE "\[ERROR\]" logs/emac.log.2026-04-14

# Top 20 des loggers les plus bavards
awk -F'\\[' '{for(i=1;i<=NF;i++) if($i ~ /^[a-z]/) print $i}' logs/emac.log.2026-04-14 \
  | cut -d']' -f1 | sort | uniq -c | sort -rn | head -20
```

Reporter les chiffres dans un commentaire de commit. Si le ratio DEBUG > 20% des lignes → `EMAC_ENV=production` manquant. Si un logger tire > 10 000 lignes → cibler ce module dans l'étape 3c.

### 3b. Vérifier que le mode production est activable

Fichier : `gui/main_qt.py` (lignes ~7-9). Vérifier que le pattern est :

```python
_production_mode = os.getenv('EMAC_ENV', '').lower() == 'production'
setup_logging(production_mode=_production_mode)
```

Si ce n'est pas exactement ce pattern (par ex. `production_mode=False` en dur), corriger.

**Documentation à jour dans le README de déploiement** : expliquer qu'il faut `EMAC_ENV=production` dans le `.env` des postes de production. C'est la 1ère cause probable du problème.

### 3c. Chasser les `logger.info` dans des boucles chaudes

Le `logging_config.py` a déjà neutralisé les 5 loggers connus bavards (alert_service, query_executor, event_rule_service, event_bus, document_trigger_service). Chercher d'autres coupables :

```bash
# logger.info à l'intérieur de boucles for/while
grep -rn "logger.info\|logger\.debug" --include="*.py" --exclude-dir=__pycache__ \
  --exclude-dir=tests --exclude-dir=scripts \
  domain/ application/ infrastructure/ gui/ \
  | wc -l
```

Si > 500 occurrences, faire un tri manuel des plus suspectes : celles dont le message contient un identifiant (id=, personnel_id=, etc.) sont les plus susceptibles d'être dans une boucle.

Pour chaque logger.info identifié dans une boucle sur N éléments :
- Si le log est utile : descendre à `logger.debug` (invisible en prod)
- Si le log est purement observationnel : remplacer par un log agrégé après la boucle

Exemple de pattern à corriger :
```python
# AVANT — explose à 1000+ lignes pour 1000 personnels
for p in personnel_list:
    logger.info(f"Traitement personnel id={p['id']}")
    process(p)

# APRÈS — 1 ligne agrégée
logger.info(f"Traitement de {len(personnel_list)} personnels")
for p in personnel_list:
    logger.debug(f"Traitement personnel id={p['id']}")  # invisible en prod
    process(p)
```

### 3d. Vérifier la rotation et la rétention

Dans `infrastructure/logging/logging_config.py`, vérifier la valeur de `_BACKUP_COUNT`. Si > 30, c'est excessif (risque de saturer le disque sur les postes avec 13 MB × 30 = 400 MB). Recommandation : 14 jours max.

```bash
grep -n "_BACKUP_COUNT" infrastructure/logging/logging_config.py
```

Si > 14, descendre à 14 avec un commentaire expliquant pourquoi.

### 3e. Nettoyage des anciens logs au démarrage (optionnel)

Dans `setup_logging()`, après la config du `TimedRotatingFileHandler`, ajouter un nettoyage défensif des fichiers plus anciens que `_BACKUP_COUNT` jours :

```python
# Nettoyage défensif des logs orphelins (si _BACKUP_COUNT a été réduit)
try:
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=_BACKUP_COUNT)
    for log_file in logs_dir.glob('emac.log.*'):
        try:
            if log_file.stat().st_mtime < cutoff.timestamp():
                log_file.unlink()
        except Exception:
            pass  # Ne pas bloquer le démarrage si un fichier est verrouillé
except Exception as e:
    startup_logger.debug(f"Nettoyage logs orphelins échoué: {e}")
```

---

## Vérification finale

```bash
# 1. Vérifier qu'aucun import ne casse
python -c "from domain.services.admin.auth_service import authenticate_user, UserSession, _check_rate_limit"
python -c "from gui.main_qt import MainWindow"
python -c "from gui.screens.admin.login_dialog import LoginDialog"

# 2. Vérifier la signature de la nouvelle fonction
python -c "
from domain.services.admin.auth_service import _check_rate_limit
import inspect
sig = inspect.signature(_check_rate_limit)
assert list(sig.parameters.keys()) == ['username', 'ip_address'], sig
print('OK:', sig)
"

# 3. Lancer les tests existants (doivent toujours passer)
python -m pytest tests/unit/ -x -q

# 4. Test d'intégration manuel du rate limiting
# → Lancer l'app, rentrer 5 fois un mauvais password, vérifier le blocage à la 6ème
# → Vérifier dans MySQL :
#   SELECT username, reason, COUNT(*) FROM logs_tentatives_connexion
#   WHERE attempt_time >= NOW() - INTERVAL 15 MINUTE GROUP BY username, reason;

# 5. Test d'intégration manuel du session timeout
# → EMAC_SESSION_TIMEOUT_MINUTES=2, se connecter, attendre 2 min sans activité
# → Popup "Session expirée" doit apparaître

# 6. Diagnostic verbosité logs (à relancer après 1 journée d'usage)
ls -lh logs/emac.log.$(date +%Y-%m-%d) 2>/dev/null || echo "Pas encore de log du jour"
# Cible : < 100 KB/jour en mode production
```

---

## Notes pour le dev

- **Ordre d'implémentation recommandé** : Tâche 3 (logs) en premier car sans risque fonctionnel, Tâche 1 (rate limiting) en second car isolée, Tâche 2 (session timeout) en dernier car touche au flow principal du MainWindow.
- **Rollback** : chaque tâche est indépendante. Un `git revert` d'un seul commit doit suffire à annuler une tâche sans casser les autres.
- **Pas de nouvelle dépendance Python** : tout se fait avec le stack existant (bcrypt, PyQt5, mysql-connector).
- **Pas de migration SQL nécessaire** : la table `logs_tentatives_connexion` existe déjà (migration 012).
