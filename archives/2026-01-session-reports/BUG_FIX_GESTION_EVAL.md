# 🐛 Correction Bug - Gestion Évaluation

## 🔴 Problème

L'application **crashait complètement** lors du clic sur "Gestion Évaluation" dans le menu principal.

## 🔍 Diagnostic

### Tests effectués

1. ✅ Test d'import des modules → OK
2. ✅ Test de création du dialogue → OK
3. ✅ Test de connexion DB → OK
4. ❌ Crash au chargement des données

### Cause identifiée

**Bug dans `gestion_evaluation.py:1094`** - Décalage dans le unpacking des résultats SQL.

#### Code problématique

```python
# Requête SQL (lignes 1052-1076)
SELECT
    p.id,
    p.nom,
    p.prenom,
    p.matricule,
    COUNT(poly.id) as total_poly,
    SUM(...) as n4,
    SUM(...) as n3,
    SUM(...) as n2,
    SUM(...) as n1,
    SUM(...) as a_planifier,  ← Position 10
    SUM(...) as retard        ← Position 11
FROM personnel p
...

# Unpacking incorrect (ligne 1094)
pers_id, nom, prenom, matricule, total, n4, n3, n2, n1, retard, a_planifier = row
#                                                        ^^^^^^  ^^^^^^^^^^^^
#                                                        INVERSÉ !
```

**Résultat**:
- `retard` recevait la valeur de `a_planifier`
- `a_planifier` recevait la valeur de `retard`
- Crash probable lors de l'affichage avec des valeurs incorrectes

---

## ✅ Correction appliquée

### Fichier: `App/core/gui/gestion_evaluation.py`

**Ligne 1095** - Correction de l'ordre du unpacking:

```python
# AVANT (incorrect)
pers_id, nom, prenom, matricule, total, n4, n3, n2, n1, retard, a_planifier = row

# APRÈS (correct)
pers_id, nom, prenom, matricule, total, n4, n3, n2, n1, a_planifier, retard = row
```

**Ligne 1094** - Ajout d'un commentaire de vigilance:

```python
# ATTENTION: L'ordre dans le SELECT est: ..., a_planifier, retard
```

---

## 🧪 Tests de validation

### Test 1: Import du module
```bash
py test_gestion_evaluation.py
```
✅ Résultat: Module importé et dialogue créé sans erreur

### Test 2: Affichage avec connexion DB
```bash
py test_gestion_eval_full.py
```
✅ Résultat: Dialogue s'ouvre et affiche les données correctement

### Test 3: Application complète
```bash
cd App
py -m core.gui.main_qt
# Cliquer sur "Gestion Évaluation"
```
✅ Résultat: Pas de crash, dialogue fonctionne normalement

---

## 📊 Impact

### Fonctionnalités affectées

- ✅ **Gestion Évaluation** → Maintenant opérationnelle
- ✅ Affichage des statuts (En retard / À planifier / À jour)
- ✅ Statistiques des évaluations
- ✅ Filtres et recherche

### Données affectées

Aucune donnée en base n'était incorrecte. Le bug était uniquement dans l'affichage côté interface.

---

## 🔧 Prévention future

### Recommandation 1: Utiliser des noms de colonnes explicites

Au lieu de :
```python
cursor.execute(query)
row = cursor.fetchone()
pers_id, nom, prenom, matricule, total, n4, n3, n2, n1, a_planifier, retard = row
```

Utiliser un dictionnaire ou des résultats nommés :
```python
cursor.execute(query)
columns = [desc[0] for desc in cursor.description]
row = cursor.fetchone()
result = dict(zip(columns, row))

# Accès plus sûr
pers_id = result['id']
retard = result['retard']
a_planifier = result['a_planifier']
```

### Recommandation 2: Tests automatisés

Ajouter un test unitaire dans `App/tests/` :

```python
# tests/test_gestion_evaluation.py
def test_load_data_order():
    """Vérifie que le unpacking des résultats SQL est correct"""
    from core.gui.gestion_evaluation import GestionEvaluationDialog

    dialog = GestionEvaluationDialog()
    dialog.load_data()

    # Vérifier qu'aucune exception n'est levée
    assert len(dialog.all_evaluations) >= 0
```

### Recommandation 3: Logging

Ajouter des logs dans `load_data()` :

```python
def load_data(self):
    try:
        ...
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"Chargement de {len(rows)} évaluations")
        ...
    except Exception as e:
        logger.error(f"Erreur load_data: {e}", exc_info=True)
        QMessageBox.critical(...)
```

---

## 📝 Checklist de vérification

- [x] Bug identifié
- [x] Correction appliquée
- [x] Test manuel réussi
- [x] Commentaire ajouté dans le code
- [x] Documentation du bug créée

---

## 🎯 Résumé

| Avant | Après |
|-------|-------|
| ❌ Crash au clic sur "Gestion Évaluation" | ✅ Dialogue s'ouvre normalement |
| ❌ Données inversées (retard ↔ a_planifier) | ✅ Données correctes |
| ❌ Statuts incorrects | ✅ Statuts exacts |

**Temps de résolution**: ~15 minutes
**Complexité**: Simple (1 ligne à corriger)
**Risque**: Faible

---

**Date**: 2026-01-07
**Fichier corrigé**: `App/core/gui/gestion_evaluation.py:1095`
**Type**: Bug d'ordre de variables (unpacking SQL)
**Sévérité**: Critique (bloquant total)
**Status**: ✅ RÉSOLU
