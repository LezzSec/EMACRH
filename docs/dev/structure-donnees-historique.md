# Structure des Données d'Historique - Guide Technique

## Vue d'ensemble

Ce document décrit la structure de stockage des données d'historique dans EMAC, permettant de conserver et d'afficher les anciennes valeurs lors de modifications.

## Table `historique`

### Schéma SQL

```sql
CREATE TABLE historique (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_time DATETIME NOT NULL,
    action VARCHAR(255) NOT NULL,
    operateur_id INT,
    poste_id INT,
    description TEXT,
    FOREIGN KEY (operateur_id) REFERENCES personnel(id),
    FOREIGN KEY (poste_id) REFERENCES postes(id),
    INDEX idx_operateur (operateur_id),
    INDEX idx_date (date_time),
    INDEX idx_action (action)
);
```

### Colonnes

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INT AUTO_INCREMENT | Identifiant unique de l'action |
| `date_time` | DATETIME | Date et heure de l'action |
| `action` | VARCHAR(255) | Type d'action : INSERT, UPDATE, DELETE, ERROR |
| `operateur_id` | INT (nullable) | ID de l'opérateur concerné |
| `poste_id` | INT (nullable) | ID du poste concerné |
| `description` | TEXT (nullable) | Données JSON avec détails complets |

## Format JSON de la colonne `description`

### Principes de base

1. **Format JSON valide** : toujours utiliser `json.dumps()` avec `ensure_ascii=False`
2. **Stockage des anciennes ET nouvelles valeurs** pour les UPDATE
3. **Métadonnées contextuelles** : nom opérateur, code poste
4. **Type d'opération** : champ `type` pour catégorisation

### Structure selon le type d'action

#### 1. INSERT (Création)

**Objectif** : Enregistrer l'ajout d'une nouvelle compétence

```json
{
  "operateur": "Prénom Nom",
  "poste": "0515",
  "niveau": 3,
  "date_evaluation": "2025-01-12",
  "prochaine_evaluation": "2035-01-12",
  "type": "ajout"
}
```

**Champs obligatoires** :
- `operateur` : Nom complet pour affichage
- `poste` : Code du poste
- `niveau` : Niveau de compétence (1-4 ou N/A)

**Champs optionnels** :
- `date_evaluation` : Date ISO format
- `prochaine_evaluation` : Date ISO format
- `type` : Sous-catégorie (ajout, import, etc.)

**Exemple de code** :
```python
from core.services.logger import log_hist
import json

log_hist(
    action="INSERT",
    table_name="polyvalence",
    record_id=poly_id,
    operateur_id=operateur_id,
    poste_id=poste_id,
    description=json.dumps({
        "operateur": f"{prenom} {nom}",
        "poste": poste_code,
        "niveau": 3,
        "date_evaluation": "2025-01-12",
        "prochaine_evaluation": "2035-01-12",
        "type": "ajout"
    }, ensure_ascii=False),
    source="GUI/gestion_polyvalence"
)
```

#### 2. UPDATE (Modification)

**Objectif** : Enregistrer les modifications avec anciennes et nouvelles valeurs

```json
{
  "operateur": "Prénom Nom",
  "poste": "0515",
  "changes": {
    "niveau": {
      "old": 2,
      "new": 4
    },
    "date_evaluation": {
      "old": "2025-01-12",
      "new": "2025-02-15"
    },
    "prochaine_evaluation": {
      "old": "2035-01-12",
      "new": "2035-02-15"
    }
  },
  "type": "modification"
}
```

**Structure `changes`** :
- Clé = nom du champ modifié
- Valeur = objet avec `old` et `new`

**Champs modifiables courants** :
- `niveau` : Changement de compétence
- `date_evaluation` : Modification de date
- `prochaine_evaluation` : Report d'évaluation
- `statut` : Changement ACTIF/INACTIF

**Exemple de code** :
```python
log_hist(
    action="UPDATE",
    table_name="polyvalence",
    record_id=poly_id,
    operateur_id=operateur_id,
    poste_id=poste_id,
    description=json.dumps({
        "operateur": f"{prenom} {nom}",
        "poste": poste_code,
        "changes": {
            "niveau": {
                "old": old_niveau,
                "new": new_niveau
            }
        },
        "type": "modification_niveau"
    }, ensure_ascii=False),
    source="GUI/gestion_evaluation"
)
```

#### 3. DELETE (Suppression)

**Objectif** : Enregistrer la suppression avec valeur supprimée

```json
{
  "operateur": "Prénom Nom",
  "poste": "0515",
  "niveau": 3,
  "type": "suppression"
}
```

**Champs obligatoires** :
- `operateur` : Nom complet
- `poste` : Code du poste
- `niveau` : Niveau supprimé (pour mémoire)

**Exemple de code** :
```python
log_hist(
    action="DELETE",
    table_name="polyvalence",
    record_id=poly_id,
    operateur_id=operateur_id,
    poste_id=poste_id,
    description=json.dumps({
        "operateur": f"{prenom} {nom}",
        "poste": poste_code,
        "niveau": niveau_supprime,
        "type": "suppression"
    }, ensure_ascii=False),
    source="GUI/gestion_polyvalence"
)
```

#### 4. ERROR (Erreur)

**Objectif** : Enregistrer les erreurs système

```json
{
  "operateur": "Prénom Nom",
  "poste": "0515",
  "error_message": "Description de l'erreur",
  "error_code": "ERR_001",
  "context": "Détails contextuels",
  "type": "erreur"
}
```

## Bonnes pratiques de logging

### 1. Toujours utiliser la fonction `log_hist()`

```python
from core.services.logger import log_hist

log_hist(
    action="INSERT|UPDATE|DELETE|ERROR",
    table_name="nom_table",
    record_id=id_enregistrement,
    operateur_id=id_operateur,  # Optionnel
    poste_id=id_poste,          # Optionnel
    description=json_string,
    source="GUI/nom_module"
)
```

### 2. Récupérer les anciennes valeurs AVANT modification

```python
# ❌ MAUVAIS : Modifier puis logger
cursor.execute("UPDATE polyvalence SET niveau = %s WHERE id = %s", (new_val, id))
log_hist(...)  # On a perdu l'ancienne valeur !

# ✅ BON : Récupérer l'ancienne valeur d'abord
cursor.execute("SELECT niveau, date_evaluation FROM polyvalence WHERE id = %s", (id,))
old_data = cursor.fetchone()

cursor.execute("UPDATE polyvalence SET niveau = %s WHERE id = %s", (new_val, id))

log_hist(
    action="UPDATE",
    description=json.dumps({
        "changes": {
            "niveau": {
                "old": old_data['niveau'],
                "new": new_val
            }
        }
    })
)
```

### 3. Inclure le contexte métier

```python
# ❌ MAUVAIS : Données brutes
description = json.dumps({"niveau": 3})

# ✅ BON : Contexte complet
description = json.dumps({
    "operateur": f"{prenom} {nom}",
    "poste": poste_code,
    "niveau": 3,
    "date_evaluation": date_str,
    "type": "ajout_competence"
}, ensure_ascii=False)
```

### 4. Gérer les transactions

```python
try:
    conn = get_db_connection()
    cur = conn.cursor()

    # Opération métier
    cur.execute("INSERT INTO polyvalence (...) VALUES (...)")
    poly_id = cur.lastrowid

    # Log (dans la même transaction)
    log_hist(...)

    # Commit si tout va bien
    conn.commit()

except Exception as e:
    conn.rollback()
    raise
finally:
    cur.close()
    conn.close()
```

## Requêtes SQL utiles

### Historique complet d'un opérateur

```sql
SELECT h.date_time, h.action, p.poste_code, h.description
FROM historique h
LEFT JOIN postes p ON h.poste_id = p.id
WHERE h.operateur_id = ?
ORDER BY h.date_time DESC;
```

### Actions par type

```sql
SELECT action, COUNT(*) as count
FROM historique
WHERE operateur_id = ?
GROUP BY action;
```

### Modifications de niveau

```sql
SELECT h.date_time, p.poste_code,
       JSON_EXTRACT(description, '$.changes.niveau.old') as old_niveau,
       JSON_EXTRACT(description, '$.changes.niveau.new') as new_niveau
FROM historique h
JOIN postes p ON h.poste_id = p.id
WHERE h.operateur_id = ?
  AND h.action = 'UPDATE'
  AND JSON_CONTAINS_PATH(description, 'one', '$.changes.niveau')
ORDER BY h.date_time DESC;
```

### Historique d'un poste spécifique

```sql
SELECT h.date_time, h.action, h.description
FROM historique h
WHERE h.operateur_id = ?
  AND h.poste_id = ?
ORDER BY h.date_time DESC;
```

### Dernière action par poste

```sql
SELECT p.poste_code,
       h.date_time as derniere_action,
       h.action as type_action
FROM (
    SELECT poste_id, MAX(date_time) as max_date
    FROM historique
    WHERE operateur_id = ?
    GROUP BY poste_id
) latest
JOIN historique h ON h.poste_id = latest.poste_id
                  AND h.date_time = latest.max_date
                  AND h.operateur_id = ?
JOIN postes p ON p.id = h.poste_id;
```

## Validation des données

### Script de vérification JSON

```python
import mysql.connector
import json

conn = mysql.connector.connect(...)
cur = conn.cursor(dictionary=True)

cur.execute("SELECT id, description FROM historique WHERE description IS NOT NULL")

errors = []
for row in cur.fetchall():
    try:
        data = json.loads(row['description'])

        # Vérifier structure obligatoire pour UPDATE
        if 'changes' in data:
            for field, change in data['changes'].items():
                if 'old' not in change or 'new' not in change:
                    errors.append(f"ID {row['id']}: champ {field} incomplet")

    except json.JSONDecodeError as e:
        errors.append(f"ID {row['id']}: JSON invalide - {e}")

if errors:
    print("Erreurs détectées :")
    for err in errors:
        print(f"  - {err}")
else:
    print("✅ Tous les JSON sont valides")
```

## Maintenance

### Archivage des anciennes données

```sql
-- Créer table d'archive (même structure)
CREATE TABLE historique_archive LIKE historique;

-- Archiver données > 2 ans
INSERT INTO historique_archive
SELECT * FROM historique
WHERE date_time < DATE_SUB(NOW(), INTERVAL 2 YEAR);

-- Supprimer de la table principale
DELETE FROM historique
WHERE date_time < DATE_SUB(NOW(), INTERVAL 2 YEAR);
```

### Optimisation des index

```sql
-- Analyser les requêtes lentes
EXPLAIN SELECT * FROM historique WHERE operateur_id = 123 ORDER BY date_time DESC;

-- Ajouter index composé si nécessaire
CREATE INDEX idx_operateur_date ON historique(operateur_id, date_time DESC);
```

## Migration de données existantes

### Script de migration pour anciennes données sans JSON

```python
import mysql.connector
import json
from datetime import datetime

conn = mysql.connector.connect(...)
cur = conn.cursor(dictionary=True)

# Récupérer anciennes entrées sans structure JSON
cur.execute("""
    SELECT h.id, h.action, h.operateur_id, h.poste_id, h.description
    FROM historique h
    WHERE h.description NOT LIKE '{%'
      AND h.description IS NOT NULL
""")

for row in cur.fetchall():
    # Récupérer infos opérateur et poste
    cur2 = conn.cursor(dictionary=True)
    cur2.execute("SELECT nom, prenom FROM personnel WHERE id = %s", (row['operateur_id'],))
    pers = cur2.fetchone()

    cur2.execute("SELECT poste_code FROM postes WHERE id = %s", (row['poste_id'],))
    poste = cur2.fetchone()

    # Créer nouveau JSON structuré
    new_desc = {
        "operateur": f"{pers['prenom']} {pers['nom']}" if pers else "Inconnu",
        "poste": poste['poste_code'] if poste else "Inconnu",
        "old_description": row['description'],
        "type": "migration"
    }

    # Mettre à jour
    cur2.execute(
        "UPDATE historique SET description = %s WHERE id = %s",
        (json.dumps(new_desc, ensure_ascii=False), row['id'])
    )

    cur2.close()

conn.commit()
print("✅ Migration terminée")
```

## Exemples d'utilisation avancée

### Comparer deux états d'un opérateur

```python
def compare_states(operateur_id, date1, date2):
    """Compare l'état de l'opérateur entre deux dates."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # État à date1
    cur.execute("""
        SELECT poste_id, JSON_EXTRACT(description, '$.niveau') as niveau
        FROM historique
        WHERE operateur_id = %s
          AND date_time <= %s
          AND action = 'INSERT'
        ORDER BY date_time DESC
    """, (operateur_id, date1))
    state1 = {row['poste_id']: row['niveau'] for row in cur.fetchall()}

    # État à date2
    cur.execute("""
        SELECT poste_id, JSON_EXTRACT(description, '$.niveau') as niveau
        FROM historique
        WHERE operateur_id = %s
          AND date_time <= %s
          AND action = 'INSERT'
        ORDER BY date_time DESC
    """, (operateur_id, date2))
    state2 = {row['poste_id']: row['niveau'] for row in cur.fetchall()}

    # Comparer
    changes = {}
    for poste_id in set(state1.keys()) | set(state2.keys()):
        old = state1.get(poste_id)
        new = state2.get(poste_id)
        if old != new:
            changes[poste_id] = {"old": old, "new": new}

    return changes
```

### Générer rapport d'activité

```python
def generate_activity_report(operateur_id, start_date, end_date):
    """Génère un rapport d'activité pour une période."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            DATE(date_time) as jour,
            action,
            COUNT(*) as nb_actions
        FROM historique
        WHERE operateur_id = %s
          AND date_time BETWEEN %s AND %s
        GROUP BY DATE(date_time), action
        ORDER BY jour DESC
    """, (operateur_id, start_date, end_date))

    report = {}
    for row in cur.fetchall():
        jour = row['jour'].strftime('%Y-%m-%d')
        if jour not in report:
            report[jour] = {}
        report[jour][row['action']] = row['nb_actions']

    return report
```

---

**Version** : 1.0
**Date** : Décembre 2025
**Projet** : EMAC - Système d'Historique
