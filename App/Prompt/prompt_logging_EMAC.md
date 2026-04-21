# PROMPT CLAUDE CODE — Optimisation Logging EMAC

## Contexte

Application EMAC : PyQt5/MySQL desktop app (~74K lignes).
Le logging en mode dev produit **6.7 Mo / 55K lignes par jour**. 86% sont du DEBUG inutile en fichier. Les 3 modules les plus bruyants (`alert_service`, `query_executor`, `event_rule_service`) représentent à eux seuls ~30 000 lignes/jour de bruit.

**Objectif** : passer de ~6.7 Mo/jour à ~300 Ko/jour sans perdre la capacité de debug quand on en a besoin.

**Fichier de configuration central** : `infrastructure/logging/logging_config.py`

---

## TÂCHE 1 — Niveau fichier : passer de DEBUG à INFO en dev

Dans `setup_logging()`, le `file_level` est actuellement `DEBUG` en mode dev. Le DEBUG n'a pas sa place dans un fichier persistant — c'est du bruit qui noie les vrais problèmes. Le garder uniquement en console pour le dev interactif.

**Fichier** : `infrastructure/logging/logging_config.py`

```python
# AVANT (ligne ~163)
file_level = logging.INFO if production_mode else logging.DEBUG

# APRÈS
file_level = logging.INFO  # Toujours INFO dans le fichier, même en dev
# Le DEBUG reste visible dans la console en mode dev
```

**Impact estimé** : 6.7 Mo → 1.3 Mo/jour (chiffre réel calculé sur les logs du 08/04).

---

## TÂCHE 2 — Museler les modules les plus bavards

Toujours dans `setup_logging()`, ajouter des niveaux par module **après** le bloc existant qui musèle les libs tierces (`urllib3`, `mysql.connector`, `PIL`).

```python
    # --- bloc existant ---
    # Réduire le bruit des bibliothèques tierces
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('mysql.connector').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

    # --- AJOUTER ICI ---
    # Réduire le bruit des modules internes trop verbeux
    # alert_service : 13 000 lignes DEBUG/jour (logue chaque personnel individuellement)
    # query_executor : 10 000 lignes DEBUG/jour ("fetch_all: 0 lignes récupérées")
    # event_rule_service : 5 800 lignes DEBUG/jour (logue chaque condition évaluée)
    # event_bus : 2 000 lignes DEBUG/jour (logue chaque souscription/émission)
    logging.getLogger('domain.services.admin.alert_service').setLevel(logging.INFO)
    logging.getLogger('infrastructure.db.query_executor').setLevel(logging.INFO)
    logging.getLogger('application.event_rule_service').setLevel(logging.INFO)
    logging.getLogger('application.event_bus').setLevel(logging.INFO)
    logging.getLogger('application.document_trigger_service').setLevel(logging.INFO)
```

> Note : ces modules garderont leurs appels `logger.debug(...)` dans le code source — ils ne seront simplement pas émis. Si on a besoin de les réactiver pour debugger un problème, il suffit de commenter la ligne correspondante.

---

## TÂCHE 3 — Nettoyer le DEBUG par-item dans `alert_service`

Le pire contrevenant : `domain/services/admin/alert_service.py` logue **chaque personnel individuellement** dans des boucles `for row in rows: logger.debug(...)`. Avec 81 personnels sans contrat × ~100 appels/jour = ~8 000 lignes de bruit pour une seule méthode.

**Pattern à corriger** (6 méthodes dans le fichier) :

```python
# AVANT — boucle avec debug par item
alerts = []
for row in rows:
    logger.debug(
        f"  sans contrat: {row['prenom']} {row['nom']} "
        f"(matricule={row['matricule']}, date_entree={row['date_entree']})"
    )
    alerts.append(Alert(...))

if alerts:
    logger.info(f"get_personnel_sans_contrat: {len(alerts)} personnel(s) sans contrat actif")
else:
    logger.debug("get_personnel_sans_contrat: tout le personnel actif a un contrat")


# APRÈS — supprimer le debug par item, garder uniquement le résumé
alerts = []
for row in rows:
    alerts.append(Alert(...))

if alerts:
    logger.info(f"get_personnel_sans_contrat: {len(alerts)} personnel(s) sans contrat actif")
else:
    logger.info("get_personnel_sans_contrat: tout le personnel actif a un contrat")
```

**Méthodes à traiter** (chercher `logger.debug` dans le fichier) :
1. `get_contrats_expires()` — lignes ~74, ~92, ~120
2. `get_contrats_expirant()` — lignes ~137, ~170, ~201
3. `get_personnel_sans_contrat()` — lignes ~214, ~242, ~267
4. `get_personnel_sans_competences()` — lignes ~284, ~303, ~329
5. `get_nouveaux_sans_affectation()` — lignes ~346, ~369, ~399
6. `get_all_contract_alerts()` / `get_all_personnel_alerts()` — lignes ~686+

**Règles pour chaque méthode** :
- **Supprimer** les `logger.debug("... début de la requête")` — inutile, on sait qu'on est dans la méthode
- **Supprimer** les `logger.debug(...)` à l'intérieur des boucles `for row in rows` — c'est le principal générateur de bruit
- **Convertir** les `logger.debug("... aucun ...")` en `logger.info(...)` — c'est une information utile
- **Garder** les `logger.info(...)` de résumé existants tels quels

---

## TÂCHE 4 — Nettoyer le DEBUG dans `query_executor`

**Fichier** : `infrastructure/db/query_executor.py`

Le `logger.debug(f"fetch_all: {len(result)} lignes récupérées")` s'exécute à **chaque requête SQL**. C'est le 2ème plus gros pollueur (10K lignes/jour).

```python
# AVANT (ligne ~76)
logger.debug(f"fetch_all: {len(result)} lignes récupérées")

# APRÈS — ne loguer que les gros résultats (seuil à 100 lignes)
if len(result) > 100:
    logger.info(f"fetch_all: {len(result)} lignes récupérées (requête volumineuse)")
```

Appliquer la même logique aux autres méthodes :
- `fetch_one` (ligne ~110) : **supprimer** le debug `"trouvé"` / `"non trouvé"` — trop fréquent, aucune valeur
- `execute_write` (lignes ~190, ~194) : **garder** mais passer en `logger.info` uniquement pour les INSERT (utile pour l'audit)
- `execute_many` (ligne ~229) : **garder** tel quel (moins fréquent)
- `execute_transaction` (ligne ~310) : **garder** tel quel
- `with_transaction` (ligne ~348) : **garder** tel quel

---

## TÂCHE 5 — Ajouter une option `EMAC_LOG_LEVEL` pour override

Permettre de forcer un niveau de log via variable d'environnement, pour pouvoir remettre du DEBUG temporairement sans toucher au code.

**Fichier** : `infrastructure/logging/logging_config.py`, dans `setup_logging()` :

```python
def setup_logging(production_mode: bool = False) -> None:
    global _initialized, _production_mode

    if _initialized:
        return

    _production_mode = production_mode

    # Override via variable d'environnement (utile pour debug ponctuel)
    # Usage: EMAC_LOG_LEVEL=DEBUG python main.py
    env_level = os.getenv('EMAC_LOG_LEVEL', '').upper()
    level_override = getattr(logging, env_level, None) if env_level else None

    # Niveau de log selon le mode
    root_level = level_override or (logging.WARNING if production_mode else logging.DEBUG)
    console_level = level_override or (logging.WARNING if production_mode else logging.INFO)
    file_level = level_override or logging.INFO  # toujours INFO sauf override

    # ... reste inchangé ...
```

Ajouter `import os` en haut du fichier s'il n'y est pas déjà.

**Documentation** : Ajouter dans le docstring du module :
```python
# Pour activer temporairement le DEBUG complet :
#   set EMAC_LOG_LEVEL=DEBUG   (Windows)
#   EMAC_LOG_LEVEL=DEBUG python main.py   (Linux)
```

---

## TÂCHE 6 — Documenter dans `config/.env.example`

Ajouter dans `config/.env.example` :

```ini
# --- Logging ---
# Forcer un niveau de log (DEBUG, INFO, WARNING, ERROR)
# Laisser vide pour le comportement par défaut (INFO fichier, DEBUG console en dev)
# EMAC_LOG_LEVEL=DEBUG
```

---

## Vérification

```bash
# 1. Vérifier que l'import fonctionne
python -c "from infrastructure.logging.logging_config import setup_logging; setup_logging(); print('OK')"

# 2. Compter les logger.debug restants (devrait être ~50, pas 86)
grep -rn "logger.debug" --include="*.py" domain/services/admin/alert_service.py infrastructure/db/query_executor.py | wc -l

# 3. Vérifier que EMAC_LOG_LEVEL fonctionne
EMAC_LOG_LEVEL=WARNING python -c "
from infrastructure.logging.logging_config import setup_logging, get_logger
setup_logging()
logger = get_logger('test')
logger.info('should not appear')
logger.warning('should appear')
"
```

## Résumé des gains attendus

| Métrique               | Avant     | Après     |
|------------------------|-----------|-----------|
| Volume fichier/jour    | 6.7 Mo    | ~300 Ko   |
| Lignes fichier/jour    | 55 000    | ~6 000    |
| % DEBUG dans fichier   | 86%       | 0%        |
| Capacité debug console | Oui       | Oui       |
| Override env possible  | Non       | Oui       |
