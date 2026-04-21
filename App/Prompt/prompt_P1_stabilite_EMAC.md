# PROMPT CLAUDE CODE — P1 Stabilité EMAC

## Contexte

Application EMAC : PyQt5/MySQL desktop app de gestion du personnel (~74K lignes, 244 fichiers Python).
Ce prompt couvre le **workstream P1 — Stabilité** : correction de bugs de production identifiés dans `logs/crash.log` et nettoyage des exceptions silencieuses.

> **Règle générale** : chaque fix doit être minimal et chirurgical. Ne pas refactorer au-delà du strict nécessaire. Logger les erreurs au lieu de les avaler. Ajouter des gardes `None` défensifs là où la DB peut retourner `NULL`.

---

## TÂCHE 1 — Bug `_selectionner_operateur_par_id` (AttributeError)

**Crash log** :
```
gui/screens/personnel/detail_operateur_dialog.py line 550
gui/screens/rh/gestion_alertes_rh.py line 701
→ AttributeError: 'GestionRHDialog' object has no attribute '_selectionner_operateur_par_id'
```

**Cause** : `GestionRHDialog` n'expose pas cette méthode. Le constructeur accepte `preselect_personnel_id` et utilise `self._vm.selectionner_operateur()` en interne.

**Fix** : Dans les 2 fichiers appelants, remplacer le pattern :
```python
# AVANT (cassé)
dialog = GestionRHDialog(self)
dialog._selectionner_operateur_par_id(some_id)
dialog.exec_()

# APRÈS (utiliser le paramètre constructeur)
dialog = GestionRHDialog(self, preselect_personnel_id=some_id)
dialog.exec_()
```

**Fichiers à modifier** :
- `gui/screens/personnel/detail_operateur_dialog.py` — lignes ~550 et ~565 (méthodes `_open_contract_management` et `_open_formation_rh`)
- `gui/screens/rh/gestion_alertes_rh.py` — ligne ~701

---

## TÂCHE 2 — Bug `add_custom_title_bar()` (TypeError)

**Crash log** :
```
gui/screens/statistiques/statistiques_dialog.py line 195
→ TypeError: add_custom_title_bar() takes from 1 to 2 positional arguments but 3 were given
```

**Cause** : Ce bug a déjà été corrigé dans le code actuel (l'appel est maintenant `add_custom_title_bar(self, "Statistiques")` avec 2 args). MAIS vérifier qu'aucun autre fichier n'appelle encore cette fonction avec 3 arguments.

**Action** :
```bash
grep -rn "add_custom_title_bar" --include="*.py" | grep -v __pycache__
```
Vérifier que tous les appels correspondent à la signature `add_custom_title_bar(dialog, title=None)` définie dans `gui/components/emac_ui_kit.py` ligne 439. Si un appel a 3 args, supprimer le 3ème argument.

---

## TÂCHE 3 — Bug `NoneType` dans `_build_mobilite_tab` (TypeError)

**Crash log** :
```
gui/screens/statistiques/statistiques_dialog.py line 552
→ max_tr = max((v for _, v in tranches), default=1)
→ TypeError: '>' not supported between instances of 'NoneType' and 'NoneType'
```

**Cause** : Les valeurs de `distances.get(...)` retournent `None` depuis la DB. Le cast `int(None or 0)` fonctionne, MAIS si TOUTES les valeurs sont `None`, le `max()` compare des `0` entre eux — ce n'est pas le problème. Le vrai problème c'est que `tranches` est construite plus haut avec des valeurs potentiellement `None` avant le cast. Vérifier le code exact et ajouter un `or 0` de sécurité.

**Fix** dans `gui/screens/statistiques/statistiques_dialog.py` :
```python
# AVANT
max_tr = max((v for _, v in tranches), default=1)

# APRÈS — forcer les None à 0 et garantir un minimum de 1
max_tr = max((v or 0 for _, v in tranches), default=1) or 1
```

---

## TÂCHE 4 — Bug `.lower()` sur `None` (AttributeError)

**Crash log** (3 occurrences) :
```
gui/screens/personnel/bulk_assignment.py line ~341 (devenu gui/screens/personnel/bulk_tabs/ après refactor)
→ matricule = row_data.get('matricule', '').lower()
→ AttributeError: 'NoneType' object has no attribute 'lower'
```

**Cause** : `dict.get('matricule', '')` retourne `''` si la clé n'existe pas, mais retourne `None` si la clé existe avec valeur `None` (ce qui arrive quand la DB a un champ NULL).

**Fix** : Chercher **tous** les patterns `row_data.get(...).lower()` ou `.upper()` ou `.strip()` dans le dossier `gui/` et appliquer le pattern défensif :
```python
# AVANT
matricule = row_data.get('matricule', '').lower()

# APRÈS
matricule = (row_data.get('matricule') or '').lower()
```

**Commande de recherche** :
```bash
grep -rn "\.get(.*).lower()\|\.get(.*).upper()\|\.get(.*).strip()" gui/ --include="*.py" | grep -v __pycache__
```
Appliquer le pattern `(x or '')` systématiquement sur tous les résultats.

---

## TÂCHE 5 — Bug `KeyError: 'operateur_id'`

**Crash log** :
```
gui/screens/formation/gestion_evaluation.py line ~444
→ operateur_id = poly_info['operateur_id'] if poly_info else None
→ KeyError: 'operateur_id'
```

**Cause** : Le dict `poly_info` existe mais ne contient pas la clé `operateur_id` (probablement renommé en `personnel_id` dans la migration 016/030).

**Fix** dans `gui/screens/formation/gestion_evaluation.py` :
```python
# AVANT
operateur_id = poly_info['operateur_id'] if poly_info else None

# APRÈS — supporter les 2 noms de clé (rétrocompat)
operateur_id = poly_info.get('personnel_id') or poly_info.get('operateur_id') if poly_info else None
```

**Action complémentaire** : Vérifier si d'autres fichiers utilisent `['operateur_id']` en accès direct (sans `.get()`) :
```bash
grep -rn "\['operateur_id'\]" --include="*.py" gui/ domain/ | grep -v __pycache__
```
Convertir les accès directs en `.get()` avec fallback `personnel_id` si c'est un dict venant de la DB.

---

## TÂCHE 6 — Nettoyage des `except Exception: pass` silencieux

**7 occurrences identifiées.** Pour chacune, remplacer `pass` par un `logger.debug()` minimum afin de ne plus avaler les erreurs silencieusement.

### 6a. `gui/screens/personnel/detail_operateur_dialog.py` lignes ~328 et ~369
```python
# AVANT
except Exception:
    pass

# APRÈS
except Exception:
    logger.debug("Impossible de charger info_basique pour operateur_id=%s", self.vm.operateur_id, exc_info=True)
```
S'assurer que `logger = logging.getLogger(__name__)` est présent en haut du fichier.

### 6b. `gui/screens/personnel/gestion_personnel.py` ligne ~459
```python
# AVANT — calcul de largeur de colonne Excel
try:
    if len(str(cell.value)) > max_length:
        max_length = len(cell.value)
except Exception:
    pass

# APRÈS — celui-ci est acceptable tel quel (c'est du cosmétique Excel)
# mais corriger le bug potentiel : len(cell.value) devrait être len(str(cell.value))
try:
    if len(str(cell.value)) > max_length:
        max_length = len(str(cell.value))  # <-- str() manquant sur la 2ème ligne
except Exception:
    pass  # OK ici, c'est du formatage non-critique
```

### 6c. `gui/screens/admin/config_tabs/tabs_documents.py` ligne ~76
### 6d. `gui/screens/admin/config_tabs/tabs_absences.py` ligne ~82
Ces 2 cas sont des previews de couleur CSS — le `pass` est acceptable car c'est purement cosmétique. Ne pas modifier.

### 6e. `gui/screens/formation/liste_et_grilles.py` lignes ~177 et ~198
Ce sont des `disconnect`/`connect` sur `cellChanged` — pattern Qt classique. Le `pass` est acceptable car `disconnect()` lève une exception si le signal n'était pas connecté. Ne pas modifier.

---

## TÂCHE 7 — Dépendance manquante `cryptography`

**Fichier** : `requirements.txt`

**Fix** : Ajouter `cryptography` dans les dépendances (utilisé par `infrastructure/security/config_crypter.py`).

```
# Sécurité - Chiffrement configuration
cryptography>=42.0.0
```

---

## Vérification finale

Après tous les fixes, lancer :
```bash
# Vérifier qu'aucun import ne casse
python -c "from gui.screens.statistiques.statistiques_dialog import StatistiquesDialog"
python -c "from gui.screens.personnel.detail_operateur_dialog import DetailOperateurDialog"
python -c "from gui.screens.rh.gestion_alertes_rh import GestionAlertesRHDialog"

# Chercher d'autres usages dangereux de .get().lower/upper/strip
grep -rn "\.get(.*)\.\(lower\|upper\|strip\)()" gui/ --include="*.py" | grep -v __pycache__

# Chercher d'autres accès directs à operateur_id
grep -rn "\['operateur_id'\]" --include="*.py" gui/ domain/ | grep -v __pycache__

# Lancer les tests existants
python -m pytest tests/unit/ -x -q
```
