# PROMPT CLAUDE CODE — P5 Performance EMAC

## Contexte

Application EMAC : PyQt5/MySQL desktop app de gestion du personnel (~73K lignes, 214 fichiers Python).
Ce prompt couvre le **workstream P5 — Performance** : élimination de 5 N+1 confirmés par analyse statique, regroupement de requêtes COUNT du dashboard, extension du cache existant, dimensionnement du pool et index manquant pour recherches full-text.

**État du code au moment de l'audit** :
- ✅ Accès DB unifié (`QueryExecutor`, `DatabaseConnection`)
- ✅ Cache déjà en place (`infrastructure/cache/emac_cache.py`) : postes, rôles, ateliers, types_contrat, permissions — **à étendre**
- ✅ Migration 030 appliquée (renommage `operateur_id` → `personnel_id` partout)
- ❌ **5 N+1 confirmés** dans `bulk_service.py` (4) et `grilles_service.py` (1)
- ❌ **Dashboard stats = 5 COUNT séquentiels** sur chaque ouverture
- ❌ **Pool DB = 5** (trop bas pour app multi-workers + logging async)
- ❌ **Recherche historique full-scan** : `LIKE '%x%'` sur `description TEXT` sans index FULLTEXT

> **Règle générale** : fix chirurgicaux, pas de refactor. Les N+1 se corrigent par batch `executemany` ou par `WHERE IN (...)` selon le cas. Benchmark avant/après avec `time.perf_counter()` sur 100 personnels pour valider.

---

## TÂCHE 1 — Éliminer les N+1 dans `bulk_service.py`

Fichier : `domain/services/personnel/bulk_service.py`

Les 4 fonctions bulk font un `INSERT`/`UPDATE` **par personnel dans une boucle Python**. Pour 500 personnels = 500 aller-retours réseau, soit ~5-15 secondes de latence purement réseau.

### 1a. `bulk_assign_formation` (ligne 208) — INSERT formation en batch

Remplacer la boucle INSERT par `executemany`, en **gardant** la boucle uniquement pour l'association document (qui est optionnelle).

```python
# AVANT (ligne ~208-233)
for i, personnel_id in enumerate(personnel_ids):
    _emit_progress(progress_callback, int((i / total) * 100), f"Traitement {i+1}/{total}...")
    formation_id = QueryExecutor.execute_write("""
        INSERT INTO formation (personnel_id, intitule, ...) VALUES (%s, %s, ...)
    """, (personnel_id, formation_data.get('intitule'), ...), return_lastrowid=True)
    # + logique document...

# APRÈS — 1 seul round-trip pour les INSERTs
_emit_progress(progress_callback, 10, f"Insertion de {total} formations...")
params_list = [
    (pid, formation_data.get('intitule'), formation_data.get('organisme'),
     formation_data.get('date_debut'), formation_data.get('date_fin'),
     formation_data.get('duree_heures'), formation_data.get('statut', 'Planifiée'),
     formation_data.get('certificat_obtenu', False),
     formation_data.get('cout'), formation_data.get('commentaire'))
    for pid in personnel_ids
]
QueryExecutor.execute_many(
    """INSERT INTO formation (personnel_id, intitule, organisme, date_debut, date_fin,
       duree_heures, statut, certificat_obtenu, cout, commentaire)
       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
    params_list
)

# Si documents à associer : re-fetch les IDs insérés
if doc_service and document_path and categorie_formation_id:
    # Récupérer les formation_id créés (par date_creation la plus récente)
    inserted = QueryExecutor.fetch_all(
        """SELECT id, personnel_id FROM formation
           WHERE personnel_id IN ({}) AND date_debut = %s AND intitule = %s
           ORDER BY id DESC""".format(','.join(['%s']*len(personnel_ids))),
        tuple(personnel_ids) + (formation_data.get('date_debut'), formation_data.get('intitule')),
        dictionary=True
    )
    for i, row in enumerate(inserted):
        _emit_progress(progress_callback, 50 + int((i/total)*50), f"Document {i+1}/{total}...")
        # logique add_document + UPDATE documents SET formation_id existante
```

### 1b. `bulk_assign_demande` (ligne 377) — même pattern

Identique à 1a : remplacer la boucle `execute_write INSERT` par un `execute_many`, re-fetch les IDs si besoin.

### 1c. `bulk_assign_visite_medicale` (ligne 511) — même pattern

Identique.

### 1d. `bulk_assign_competence` (ligne 692) — UPSERT en batch

Celui-ci est différent : il y a une branche `SELECT existing → UPDATE ou INSERT`. À remplacer par **une seule requête MySQL UPSERT** :

```python
# AVANT : SELECT + INSERT/UPDATE pour chaque personnel_id (3 requêtes × N)

# APRÈS : 1 seule requête executemany avec ON DUPLICATE KEY UPDATE
# (nécessite que (personnel_id, competence_id) ait un index UNIQUE ; sinon la migration doit l'ajouter)
params_list = [
    (pid, competence_id,
     competence_data.get('date_acquisition'),
     competence_data.get('date_expiration'),
     competence_data.get('commentaire'))
    for pid in personnel_ids
]
QueryExecutor.execute_many(
    """INSERT INTO personnel_competences
       (personnel_id, competence_id, date_acquisition, date_expiration, commentaire)
       VALUES (%s, %s, %s, %s, %s)
       ON DUPLICATE KEY UPDATE
         date_acquisition = VALUES(date_acquisition),
         date_expiration = VALUES(date_expiration),
         commentaire = VALUES(commentaire)""",
    params_list
)
```

**Pré-requis DB** : vérifier que la contrainte UNIQUE existe :
```sql
SHOW INDEX FROM personnel_competences WHERE Non_unique = 0;
```
Si absente, créer une migration dédiée (prochain numéro dispo : `052_unique_personnel_competences.sql`) :
```sql
ALTER TABLE personnel_competences
  ADD UNIQUE KEY uk_personnel_competence (personnel_id, competence_id);
```

**Attention** : cette migration peut échouer si la DB actuelle contient déjà des doublons. Tester avant en prod :
```sql
SELECT personnel_id, competence_id, COUNT(*)
FROM personnel_competences GROUP BY 1,2 HAVING COUNT(*) > 1;
```
Nettoyer les doublons avant d'appliquer la migration.

---

## TÂCHE 2 — Éliminer le N+1 dans `grilles_service.py`

Fichier : `domain/services/formation/grilles_service.py` ligne 423

`apply_batch_modifications` fait `SELECT existing` puis `REPLACE INTO polyvalence` dans une boucle. `REPLACE INTO` est déjà un upsert — le `SELECT` initial ne sert qu'à logger l'ancienne valeur pour l'historique.

Alternative propre :

```python
# AVANT : SELECT + REPLACE dans la boucle
for operateur_id, poste_id, new_niveau_str, ... in modifications:
    existing = QueryExecutor.fetch_one("SELECT niveau FROM polyvalence WHERE personnel_id = %s AND poste_id = %s", ...)
    QueryExecutor.execute_write("REPLACE INTO polyvalence ...")
    # log_hist...

# APRÈS : SELECT groupé en 1 requête, puis REPLACE batch
if not modifications:
    return 0

# 1. Pré-charger tous les existants en 1 requête
pairs = [(op_id, p_id) for op_id, p_id, *_ in modifications]
placeholders = ','.join(['(%s, %s)'] * len(pairs))
flat_params = tuple(v for pair in pairs for v in pair)
existing_rows = QueryExecutor.fetch_all(
    f"""SELECT personnel_id, poste_id, niveau FROM polyvalence
       WHERE (personnel_id, poste_id) IN ({placeholders})""",
    flat_params, dictionary=True
)
existing_map = {(r['personnel_id'], r['poste_id']): r['niveau'] for r in existing_rows}

# 2. Batch REPLACE en 1 requête
replace_params = [
    (op_id, p_id, int(niveau) if niveau else None)
    for op_id, p_id, niveau, *_ in modifications
]
QueryExecutor.execute_many(
    "REPLACE INTO polyvalence (personnel_id, poste_id, niveau) VALUES (%s, %s, %s)",
    replace_params
)

# 3. Logs historique (à conserver dans une boucle car l'audit doit être individuel)
for operateur_id, poste_id, new_niveau_str, operateur_nom, poste_code in modifications:
    old_niveau = existing_map.get((operateur_id, poste_id))
    action = 'UPDATE' if old_niveau is not None else 'INSERT'
    # ... reste du log_hist inchangé
```

Gain : 2N requêtes → 2 requêtes, soit **~100× plus rapide** pour 100 modifs.

---

## TÂCHE 3 — Regrouper les COUNT du dashboard

Fichier : `domain/services/statistiques_service.py` ligne 17

`get_resume()` fait 5 `COUNT(*)` séquentiels. À regrouper en 1 requête avec sous-sélects :

```python
def get_resume() -> dict:
    """KPIs globaux — 1 seule requête au lieu de 5."""
    try:
        row = QueryExecutor.fetch_one("""
            SELECT
              (SELECT COUNT(*) FROM personnel WHERE statut = 'ACTIF') AS effectif_actif,
              (SELECT COUNT(*) FROM polyvalence WHERE prochaine_evaluation < CURDATE()) AS evals_retard,
              (SELECT COUNT(*) FROM contrat
                 WHERE actif = 1 AND date_fin IS NOT NULL
                 AND date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)) AS contrats_30j,
              (SELECT COUNT(*) FROM demande_absence
                 WHERE MONTH(date_debut) = MONTH(CURDATE())
                 AND YEAR(date_debut) = YEAR(CURDATE())
                 AND statut = 'VALIDEE') AS absences_mois,
              (SELECT COUNT(*) FROM personnel_mobilite
                 WHERE actif = 1 AND date_fin IS NULL) AS mobilite_actifs
        """, dictionary=True)
        return {k: int(v or 0) for k, v in (row or {}).items()}
    except Exception as e:
        logger.exception(f"get_resume: {e}")
        return {}
```

Gain : 5 aller-retours → 1, soit ~4× plus rapide (MySQL exécute les 5 COUNT en parallèle interne).

---

## TÂCHE 4 — Étendre le cache aux listes de référence manquantes

Fichier : `infrastructure/cache/emac_cache.py`

Le cache couvre déjà postes, rôles, ateliers, types_contrat, permissions. Manque les **catégories de documents** et les **compétences catalogue** (listes quasi-statiques utilisées dans beaucoup de combos).

### 4a. Ajouter le cache des catégories de documents

À la fin de `emac_cache.py`, après `get_cached_types_contrat()` :

```python
@cache.cached(key='categories_documents', ttl=600)
def get_cached_categories_documents() -> List[Dict]:
    """Cache les catégories de documents (rare d'être modifié)."""
    return QueryExecutor.fetch_all(
        "SELECT id, nom, description FROM categories_documents ORDER BY nom",
        dictionary=True
    )


@cache.cached(key='competences_catalogue', ttl=600)
def get_cached_competences_catalogue() -> List[Dict]:
    """Cache le catalogue des compétences."""
    return QueryExecutor.fetch_all(
        "SELECT id, intitule, categorie, duree_validite_mois FROM competences_catalogue ORDER BY intitule",
        dictionary=True
    )
```

Puis étendre `invalidate_static_lists_cache()` pour inclure ces nouvelles clés.

### 4b. Remplacer les appels directs

```bash
# Chercher les endroits qui requêtent directement ces tables
grep -rn "FROM categories_documents\|FROM competences_catalogue" \
  --include="*.py" --exclude-dir=__pycache__ domain/ gui/
```

Pour chaque hit dans un service/VM (pas dans un repo bas-niveau), remplacer par `get_cached_*`.

---

## TÂCHE 5 — Dimensionner le pool DB

Fichier : `infrastructure/db/configbd.py` ligne 116

```python
# AVANT
pool_size = _env_int("EMAC_DB_POOL_SIZE", 5)

# APRÈS — défaut plus réaliste pour une app PyQt5 avec workers + logging async
pool_size = _env_int("EMAC_DB_POOL_SIZE", 10)
```

Documenter dans `config/README.md` :
```
EMAC_DB_POOL_SIZE=10   # Défaut raisonnable. Monter à 15-20 si > 5 workers GUI.
```

---

## TÂCHE 6 — Index FULLTEXT sur `historique.description`

Fichier : nouvelle migration `database/migrations/053_fulltext_historique.sql`

`historique_service.py` ligne 108-111 fait un `LIKE '%...%'` sur `action`, `description`, `personnel_id`, `poste_id`. Sur `description TEXT`, c'est un full scan garanti — avec 13k entrées/jour d'historique, ça devient vite pénible.

**Migration** :

```sql
-- Migration 053 : Index FULLTEXT sur historique pour recherche rapide
-- Date : 2026-04-21
-- Impact : recherche par mot-clé dans description ~50× plus rapide

USE emac_db;

ALTER TABLE historique
  ADD FULLTEXT INDEX ft_action_description (action, description);
```

**Code** : `domain/services/admin/historique_service.py` ligne 104 — brancher sur FULLTEXT uniquement quand la chaîne est suffisamment longue (≥ 4 chars, limite par défaut MySQL) :

```python
if search_text and len(search_text) >= 4:
    # Utiliser FULLTEXT (rapide) pour les recherches longues
    where.append(
        "(MATCH(action, description) AGAINST (%s IN BOOLEAN MODE) "
        "OR CAST(personnel_id AS CHAR) LIKE %s "
        "OR CAST(poste_id AS CHAR) LIKE %s)"
    )
    # Le + signifie "doit contenir" en BOOLEAN MODE
    params += [f"+{search_text}*", f"%{search_text}%", f"%{search_text}%"]
elif search_text:
    # Recherche courte : fallback sur LIKE (FULLTEXT a min 4 chars par défaut)
    like = f"%{search_text}%"
    where.append(
        "(action LIKE %s OR description LIKE %s "
        "OR CAST(personnel_id AS CHAR) LIKE %s OR CAST(poste_id AS CHAR) LIKE %s)"
    )
    params += [like, like, like, like]
```

Appliquer la même logique à la 2ème occurrence ligne ~187-189 du même fichier.

---

## Vérification finale

```bash
# 1. Aucun import ne casse
python -c "from domain.services.personnel.bulk_service import bulk_assign_formation, bulk_assign_demande, bulk_assign_visite_medicale, bulk_assign_competence"
python -c "from domain.services.formation.grilles_service import *"
python -c "from domain.services.statistiques_service import get_resume"
python -c "from infrastructure.cache.emac_cache import get_cached_categories_documents, get_cached_competences_catalogue"

# 2. Tests existants toujours verts
python -m pytest tests/unit/ -x -q

# 3. Benchmark bulk (à coder en one-shot dans scripts/bench_bulk.py)
# → Générer 100 personnel_ids de test, appeler bulk_assign_formation, chronométrer
# Cible : < 500ms pour 100 personnels (vs ~3-5s avant)

# 4. EXPLAIN sur la nouvelle requête resume
mysql emac_db -e "EXPLAIN SELECT (SELECT COUNT(*) FROM personnel WHERE statut='ACTIF') AS e"
# Cible : 'Using index' sur le sous-select

# 5. Vérifier que FULLTEXT est bien utilisé
mysql emac_db -e "EXPLAIN SELECT * FROM historique WHERE MATCH(action, description) AGAINST ('+test*' IN BOOLEAN MODE)"
# Cible : type=fulltext, key=ft_action_description

# 6. Migration appliquée
python -m App migrate status | grep -E "052|053"
```

---

## Notes pour le dev

- **Ordre d'implémentation** : T3 (regroupement COUNT) en premier (risque quasi nul, gain UX immédiat sur le dashboard). T5 (pool size) ensuite (1 ligne). T6 (FULLTEXT) puis T4 (cache). Finir par T1/T2 (N+1) qui sont plus invasifs.
- **Rollback migration 053** : `ALTER TABLE historique DROP INDEX ft_action_description;`
- **Rollback migration 052** : `ALTER TABLE personnel_competences DROP INDEX uk_personnel_competence;`
- **Pas de nouvelle dépendance Python**.
- **Compat PyQt5** : aucune des modifs ne touche au thread principal GUI ; les gains de latence rendent même les workers plus responsives (moins d'attente sur le pool).
