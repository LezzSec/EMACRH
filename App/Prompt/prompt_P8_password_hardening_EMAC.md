# PROMPT CLAUDE CODE — P8 Durcissement MDP (bcrypt rehash + politique moderne)

## Contexte

Application EMAC : PyQt5/MySQL desktop app de gestion du personnel (~73K lignes, 214 fichiers Python).
Ce prompt couvre le **workstream P8 — Durcissement des mots de passe** : externalisation du cost bcrypt, rehash transparent au login, politique MDP alignée NIST SP 800-63B (12+ chars, check wordlist, complexité artificielle relâchée), et flag DB pour forcer le changement des MDP legacy.

**État du code au moment de l'audit** :
- ✅ Bcrypt déjà en place avec `gensalt()` par défaut (cost=12 actuellement)
- ✅ `validate_password()` existe avec règles 8 chars + complexité (`auth_service.py` ligne 64)
- ✅ `hash_password()` / `verify_password()` utilisés de façon cohérente (`auth_service.py` lignes 195 et 201)
- ❌ **Cost bcrypt en dur** : pas moyen de le bumper sans redéployer le code
- ❌ **Pas de rehash** : un compte créé en 2023 à cost 10 reste à cost 10 à vie
- ❌ **Politique 8 chars + complexité** : obsolète (NIST recommande 12+ sans complexité artificielle depuis 2020)
- ❌ **Aucun check wordlist** : `Password1!` passe tous les contrôles alors qu'il est dans tous les dicos

**Pré-requis** : le P4 (rate limiting + session timeout) doit être déployé. Sinon forcer le changement de MDP sans rate limiting = aggravation du risque brute-force.

> **Règle générale** : migration douce obligatoire. Aucun utilisateur existant ne doit se retrouver bloqué. Les comptes legacy continuent de fonctionner avec leur MDP actuel ; la nouvelle politique s'applique uniquement au **prochain changement de MDP**.

---

## TÂCHE 1 — Externaliser le cost bcrypt

Fichier : `domain/services/admin/auth_service.py`

### 1a. Constante au niveau module

Après les imports (vers ligne 30, avant `_get_client_ip`), ajouter :

```python
import os

# =============================================================================
# CONFIGURATION BCRYPT
# =============================================================================
# Cost par défaut : 12 (2^12 = 4096 itérations ~250ms sur CPU moderne).
# À augmenter tous les 2-3 ans. Valeur configurable via EMAC_BCRYPT_COST.
# IMPORTANT : tout bump de cette valeur déclenche un rehash automatique
# au prochain login réussi des comptes concernés.
_BCRYPT_COST = int(os.getenv('EMAC_BCRYPT_COST', '12'))

# Garde-fous : cost < 10 est non-sûr, > 15 rend le login insupportable
if not 10 <= _BCRYPT_COST <= 15:
    import logging
    logging.getLogger(__name__).warning(
        f"EMAC_BCRYPT_COST={_BCRYPT_COST} hors plage recommandée [10-15]. "
        f"Valeur corrigée à 12."
    )
    _BCRYPT_COST = 12
```

### 1b. Adapter `hash_password()` (ligne 195)

```python
# AVANT
def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# APRÈS
def hash_password(password: str, rounds: Optional[int] = None) -> str:
    """
    Hash un mot de passe avec bcrypt au cost configuré.

    Args:
        password: Mot de passe en clair
        rounds: Cost bcrypt (override optionnel, sinon _BCRYPT_COST)

    Returns:
        Hash bcrypt au format "$2b$<cost>$<salt+hash>"
    """
    salt = bcrypt.gensalt(rounds=rounds if rounds is not None else _BCRYPT_COST)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
```

### 1c. Ajouter `_extract_bcrypt_cost()` et `_password_needs_rehash()`

Juste après `verify_password()` (vers ligne 208) :

```python
def _extract_bcrypt_cost(password_hash: str) -> Optional[int]:
    """
    Extrait le cost d'un hash bcrypt.

    Format bcrypt : $2b$12$<22 chars salt><31 chars hash>
                    │  │  │
                    │  │  └── cost (2 chiffres)
                    │  └───── version (2a, 2b, 2y)
                    └──────── algorithme

    Args:
        password_hash: Hash au format bcrypt

    Returns:
        Cost entier ou None si format invalide
    """
    try:
        if not password_hash or not password_hash.startswith('$2'):
            return None
        parts = password_hash.split('$')
        if len(parts) < 4:
            return None
        return int(parts[2])
    except (ValueError, IndexError):
        return None


def _password_needs_rehash(password_hash: str) -> bool:
    """
    Détermine si un hash doit être rehashé (cost actuel < cost cible).

    Args:
        password_hash: Hash stocké en DB

    Returns:
        True si le hash doit être régénéré au prochain login réussi
    """
    current_cost = _extract_bcrypt_cost(password_hash)
    if current_cost is None:
        # Format inconnu = à rehasher dès que possible
        return True
    return current_cost < _BCRYPT_COST
```

---

## TÂCHE 2 — Rehash transparent au login

Fichier : `domain/services/admin/auth_service.py`, fonction `authenticate_user()` (ligne ~211)

Après le `verify_password` réussi (ligne ~255), **avant** la construction du dict `permissions`, insérer :

```python
if not verify_password(password, user['password_hash']):
    cur.close()
    _log_failed_attempt(username, "wrong_password")
    return False, "Nom d'utilisateur ou mot de passe incorrect"

# ─── NOUVEAU : rehash transparent si cost dépassé ──────────────────────
if _password_needs_rehash(user['password_hash']):
    try:
        new_hash = hash_password(password)  # Utilise _BCRYPT_COST
        cur.execute(
            "UPDATE utilisateurs SET password_hash = %s WHERE id = %s",
            (new_hash, user['id'])
        )
        logger.info(
            f"Rehash bcrypt pour utilisateur {username} : "
            f"{_extract_bcrypt_cost(user['password_hash'])} → {_BCRYPT_COST}"
        )
    except Exception as e:
        # Ne pas bloquer le login si le rehash échoue
        logger.warning(f"Échec rehash bcrypt pour {username}: {e}")
# ────────────────────────────────────────────────────────────────────────

# Construire le dictionnaire des permissions effectives...
```

**Important** : ce rehash se fait dans la même transaction que l'UPDATE de `derniere_connexion`, donc soit les deux passent, soit aucun. Pas d'état incohérent possible.

---

## TÂCHE 3 — Politique MDP alignée NIST

Fichier : `domain/services/admin/auth_service.py`, fonction `validate_password()` (ligne 64)

### 3a. Nouvelle règle

```python
def validate_password(password: str, check_common: bool = True) -> Tuple[bool, str]:
    """
    Valide la robustesse d'un mot de passe (NIST SP 800-63B compatible).

    Règles (2026+) :
    - Minimum 12 caractères
    - Au moins 2 types de caractères distincts (pour éviter "aaaaaaaaaaaa")
    - Pas dans la liste des 10 000 mots de passe les plus courants
    - Pas strictement identique au username (check fait par l'appelant)

    La complexité artificielle (1 maj + 1 chiffre + 1 spécial) est relâchée
    car elle pousse à des patterns prévisibles ("Password1!" reste faible).
    Une passphrase longue est largement préférable.

    Args:
        password: Mot de passe à valider
        check_common: Si True, vérifie contre la wordlist des MDP courants

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Le mot de passe doit contenir au moins 12 caractères."

    # Au moins 2 types de caractères (majuscule / minuscule / chiffre / spécial)
    # → évite "aaaaaaaaaaaa" sans imposer le cocktail complet
    types = 0
    if re.search(r'[a-z]', password):
        types += 1
    if re.search(r'[A-Z]', password):
        types += 1
    if re.search(r'\d', password):
        types += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~ /]', password):
        types += 1

    if types < 2:
        return False, (
            "Le mot de passe doit combiner au moins 2 types de caractères "
            "parmi : minuscules, majuscules, chiffres, caractères spéciaux."
        )

    if check_common and _is_common_password(password):
        return False, (
            "Ce mot de passe fait partie des plus courants et est facile à deviner. "
            "Choisissez une phrase de passe ou un mot de passe unique."
        )

    return True, ""
```

### 3b. Nouvelle fonction `_is_common_password()`

Ajouter juste avant `validate_password()` :

```python
_COMMON_PASSWORDS_CACHE: Optional[set] = None


def _is_common_password(password: str) -> bool:
    """
    Vérifie si un mot de passe figure dans la wordlist des plus courants.

    Le fichier `config/common_passwords.txt` contient ~10 000 MDP les plus
    fréquemment vus dans les leaks (source : SecLists/rockyou top 10k).
    Chargé une seule fois en mémoire (~100 KB).

    Args:
        password: Mot de passe en clair

    Returns:
        True si le MDP est dans la wordlist (comparaison case-insensitive)
    """
    global _COMMON_PASSWORDS_CACHE

    if _COMMON_PASSWORDS_CACHE is None:
        try:
            from pathlib import Path
            # Localiser le fichier : App/config/common_passwords.txt
            base = Path(__file__).resolve().parents[3]  # services/admin/auth_service.py → App/
            wordlist_path = base / "config" / "common_passwords.txt"
            if wordlist_path.exists():
                with open(wordlist_path, encoding='utf-8', errors='ignore') as f:
                    _COMMON_PASSWORDS_CACHE = {
                        line.strip().lower() for line in f if line.strip()
                    }
                logger.info(f"Wordlist chargée : {len(_COMMON_PASSWORDS_CACHE)} MDP courants")
            else:
                logger.warning(f"Wordlist introuvable : {wordlist_path} — check désactivé")
                _COMMON_PASSWORDS_CACHE = set()
        except Exception as e:
            logger.error(f"Erreur chargement wordlist : {e}")
            _COMMON_PASSWORDS_CACHE = set()

    return password.lower() in _COMMON_PASSWORDS_CACHE
```

### 3c. Adapter `get_password_requirements()` (ligne ~99)

```python
def get_password_requirements() -> str:
    """Retourne les exigences de mot de passe pour affichage UI"""
    return (
        "Le mot de passe doit :\n"
        "• Contenir au moins 12 caractères\n"
        "• Combiner au moins 2 types parmi : minuscules, majuscules, chiffres, caractères spéciaux\n"
        "• Ne pas figurer dans la liste des mots de passe les plus courants\n"
        "\n"
        "Conseil : une phrase de passe comme « piano bleu vendredi 42 » est "
        "plus sûre qu'un mot complexe comme « P@ssw0rd! »."
    )
```

### 3d. Télécharger la wordlist

Créer le fichier `config/common_passwords.txt` avec le top 10k de SecLists :

```bash
cd App/config
curl -fsSL https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-10000.txt \
  -o common_passwords.txt

# Vérification
wc -l common_passwords.txt  # doit afficher 10000
```

Si pas d'accès internet sur le poste de build : commit manuellement le fichier depuis une machine qui a le réseau. Fichier ~75 KB, négligeable.

**À ajouter dans le build PyInstaller** (`build_release.bat`) : s'assurer que `config/common_passwords.txt` est copié dans le `_internal/config/` du binaire final.

---

## TÂCHE 4 — Migration DB : flag `password_needs_upgrade`

Fichier : nouvelle migration `database/migrations/054_password_upgrade_flag.sql`

```sql
-- Migration 054 : Flag pour forcer le changement de MDP legacy
-- Date : 2026-04-21
-- Contexte : P8 durcissement — comptes existants utilisant MDP 8 chars
--            doivent être forcés à choisir un MDP 12+ au prochain login.

USE emac_db;

-- Ajout du flag. Valeur par défaut = 1 pour TOUS les comptes existants
-- → ils seront forcés de changer leur MDP au prochain login.
-- Les nouveaux comptes créés après la migration auront le flag à 0
-- (géré par le code applicatif dans create_user et change_password).
ALTER TABLE utilisateurs
  ADD COLUMN password_needs_upgrade TINYINT(1) NOT NULL DEFAULT 1
    COMMENT 'Force le changement de MDP au prochain login (politique 12+)',
  ADD COLUMN password_changed_at DATETIME DEFAULT NULL
    COMMENT 'Date du dernier changement de mot de passe';

-- Les comptes qui n'existent pas encore auront le flag à 0 par défaut
-- → corrigé via trigger applicatif dans create_user()
```

**Rollback** : `database/migrations/rollback/054_password_upgrade_flag_rollback.sql`

```sql
USE emac_db;
ALTER TABLE utilisateurs
  DROP COLUMN password_needs_upgrade,
  DROP COLUMN password_changed_at;
```

---

## TÂCHE 5 — Intégration du flag dans le flow

Fichier : `domain/services/admin/auth_service.py`

### 5a. Mettre à jour `create_user()` (ligne 489)

```python
# AVANT
new_id = QueryExecutor.execute_write(
    "INSERT INTO utilisateurs (username, password_hash, nom, prenom, role_id) VALUES (%s, %s, %s, %s, %s)",
    (username, password_hash, nom, prenom, role_id)
)

# APRÈS — les nouveaux comptes sont conformes dès le départ
new_id = QueryExecutor.execute_write(
    """INSERT INTO utilisateurs
       (username, password_hash, nom, prenom, role_id, password_needs_upgrade, password_changed_at)
       VALUES (%s, %s, %s, %s, %s, 0, NOW())""",
    (username, password_hash, nom, prenom, role_id)
)
```

### 5b. Mettre à jour `change_password()` (ligne 585)

```python
# AVANT
QueryExecutor.execute_write(
    "UPDATE utilisateurs SET password_hash = %s WHERE id = %s",
    (password_hash, user_id), return_lastrowid=False
)

# APRÈS — changement volontaire = flag reset
QueryExecutor.execute_write(
    """UPDATE utilisateurs
       SET password_hash = %s, password_needs_upgrade = 0, password_changed_at = NOW()
       WHERE id = %s""",
    (password_hash, user_id), return_lastrowid=False
)
```

**Important** : dans `change_password()`, ajouter la validation de la nouvelle politique **avant** le hash :

```python
def change_password(user_id: int, new_password: str) -> tuple[bool, Optional[str]]:
    """Change le mot de passe d'un utilisateur"""
    current_user = get_current_user()
    if not current_user:
        return False, "Aucun utilisateur connecté"

    if not is_admin() and current_user['id'] != user_id:
        return False, "Vous ne pouvez pas modifier ce mot de passe"

    # ─── NOUVEAU : validation de la politique ───────────────────────────
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return False, error_msg
    # ────────────────────────────────────────────────────────────────────

    try:
        password_hash = hash_password(new_password)
        # ... UPDATE ...
```

### 5c. Exposer le flag dans `authenticate_user()`

Modifier la requête SELECT (ligne ~228) pour inclure `password_needs_upgrade` :

```python
cur.execute("""
    SELECT
        u.id, u.username, u.password_hash, u.nom, u.prenom,
        u.role_id, u.actif, u.password_needs_upgrade,  -- ← AJOUTER
        r.nom as role_nom,
        p.module,
        COALESCE(pu.lecture, p.lecture) as lecture,
        COALESCE(pu.ecriture, p.ecriture) as ecriture,
        COALESCE(pu.suppression, p.suppression) as suppression
    FROM utilisateurs u
    ...
""", (username,))
```

Puis dans le dict `user_data` (ligne ~282), inclure le flag :

```python
user_data = {
    'id': user['id'],
    'username': user['username'],
    'nom': user['nom'],
    'prenom': user['prenom'],
    'role_id': user['role_id'],
    'role_nom': user['role_nom'],
    'password_needs_upgrade': bool(user['password_needs_upgrade']),  # ← AJOUTER
}
```

---

## TÂCHE 6 — Popup de changement forcé dans le GUI

Fichier : `gui/main_qt.py`

Juste après la création de `MainWindow` dans `__main__.py` (ou dans `MainWindow.__init__`), après que le dashboard soit affiché, vérifier le flag et forcer le changement :

```python
def _check_password_upgrade_required(self):
    """Force le changement de MDP si le flag est levé (politique 12+)."""
    from domain.services.admin.auth_service import UserSession, get_password_requirements
    from PyQt5.QtWidgets import QMessageBox
    from gui.screens.admin.change_password_dialog import ChangePasswordDialog  # à créer si inexistant

    user = UserSession.get_user()
    if not user or not user.get('password_needs_upgrade'):
        return

    QMessageBox.warning(
        self,
        "Mise à jour du mot de passe requise",
        "La politique de sécurité a évolué. Votre mot de passe actuel "
        "ne respecte plus les nouvelles exigences.\n\n"
        + get_password_requirements() +
        "\n\nVeuillez choisir un nouveau mot de passe pour continuer."
    )

    dialog = ChangePasswordDialog(user_id=user['id'], force_change=True, parent=self)
    if dialog.exec_() != dialog.Accepted:
        # L'utilisateur a refusé → déconnexion
        from domain.services.admin.auth_service import logout_user
        logout_user()
        self.close()
        return

    # Rafraîchir la session (le flag doit être à 0 maintenant)
    user['password_needs_upgrade'] = False
```

Appeler cette méthode à la fin de `MainWindow.__init__`, après tout le setup UI.

**Si `ChangePasswordDialog` n'existe pas déjà**, utiliser à la place la popup existante de `user_management.py` (lignes ~374 et ~480 qui appellent déjà `validate_password`), ou créer un dialogue simple avec 2 champs (nouveau MDP + confirmation) qui appelle `change_password(user_id, new_password)`.

---

## TÂCHE 7 — Adapter les tests existants

Fichier : `tests/unit/test_auth_service.py`

Les tests existants (lignes 28-56 visibles à l'inventaire) utilisent des MDP 8 chars comme `"Test1234!"`. Avec la nouvelle règle 12+, ils vont échouer.

Mise à jour :

```python
# AVANT
valid, message = validate_password("Test1234!")  # 9 chars → KO désormais

# APRÈS
valid, message = validate_password("TestPassword1234!")  # 17 chars, 3 types → OK
assert valid, message

# Test de la nouvelle règle 12 chars
valid, message = validate_password("Test1234!")  # 9 chars → doit échouer
assert not valid
assert "12 caractères" in message

# Test du check wordlist
valid, message = validate_password("password1234")  # dans wordlist
assert not valid
assert "courants" in message

# Test cost extraction
from domain.services.admin.auth_service import _extract_bcrypt_cost
import bcrypt
h = bcrypt.hashpw(b"x", bcrypt.gensalt(rounds=11)).decode()
assert _extract_bcrypt_cost(h) == 11

# Test rehash detection
from domain.services.admin.auth_service import _password_needs_rehash, _BCRYPT_COST
old_hash = bcrypt.hashpw(b"x", bcrypt.gensalt(rounds=10)).decode()
assert _password_needs_rehash(old_hash) is (10 < _BCRYPT_COST)
```

---

## Vérification finale

```bash
# 1. Imports OK
python -c "from domain.services.admin.auth_service import (
    hash_password, verify_password, validate_password,
    _extract_bcrypt_cost, _password_needs_rehash,
    _is_common_password, _BCRYPT_COST
)"

# 2. Wordlist accessible et de la bonne taille
python -c "
from domain.services.admin.auth_service import _is_common_password
assert _is_common_password('password') is True, 'wordlist non chargée ?'
assert _is_common_password('un-mot-de-passe-unique-2026') is False
print('OK wordlist')
"

# 3. Tests unitaires verts
python -m pytest tests/unit/test_auth_service.py -x -v

# 4. Migration appliquée
python -m App migrate status | grep 054
mysql emac_db -e "DESCRIBE utilisateurs" | grep -E "password_needs_upgrade|password_changed_at"

# 5. Test d'intégration manuel du rehash
# → Créer un compte de test avec cost=10 via SQL direct :
#   UPDATE utilisateurs SET password_hash = '$2b$10$...' WHERE username = 'test';
# → Se connecter avec ce compte
# → Vérifier en DB que le hash est passé à cost=12 :
#   SELECT SUBSTRING(password_hash, 1, 7) FROM utilisateurs WHERE username = 'test';
#   Doit afficher $2b$12$

# 6. Test d'intégration manuel du forced change
# → UPDATE utilisateurs SET password_needs_upgrade = 1 WHERE username = 'moi';
# → Se connecter → la popup doit apparaître
# → Refuser → déconnexion immédiate
# → Re-connecter, accepter, choisir un MDP 12+ → connexion OK, flag remis à 0

# 7. Benchmark du login (doit rester < 500ms avec cost 12)
python -c "
import time
from domain.services.admin.auth_service import hash_password, verify_password
h = hash_password('TestPassword1234!')
t = time.perf_counter()
for _ in range(5):
    verify_password('TestPassword1234!', h)
print(f'Temps moyen verify: {(time.perf_counter()-t)/5*1000:.0f}ms')
"
```

---

## Notes pour le dev

- **Ordre d'implémentation** : T1 (cost externalisé) en premier, puis T2 (rehash) qui en dépend. Ensuite T3+T4 ensemble (politique + migration), puis T5 (intégration flag), T6 (popup GUI) et T7 (tests) en dernier.
- **Rollback complet possible** : `git revert` du code + `054_password_upgrade_flag_rollback.sql`. Les hashes bcrypt rehashés ne sont pas réversibles (normal) mais restent compatibles avec l'ancien code.
- **Aucune dépendance Python ajoutée** : tout fonctionne avec `bcrypt` déjà présent.
- **Déploiement** : penser à définir `EMAC_BCRYPT_COST=12` dans le `.env` de prod pour être explicite (même si c'est la valeur par défaut). Le jour où tu passes à 14, il suffira de changer cette ligne et les comptes se mettront à niveau au fil des logins.
- **Impact utilisateur** : tous les utilisateurs existants devront choisir un nouveau MDP au prochain login (≥ 12 chars). Prévenir par mail ou annonce interne **avant** le déploiement pour éviter les tickets de support. Prévoir une procédure de reset admin pour les cas où un user bloque.
- **Pas de prompts P6/P7 encore** : garder ce prompt isolé, ne pas mélanger avec observabilité ou couverture tests.
