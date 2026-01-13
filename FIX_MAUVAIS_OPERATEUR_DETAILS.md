# FIX: Mauvais opérateur affiché dans le dialogue de détails

## 📋 Problème identifié

### Symptôme
Lorsque l'utilisateur double-clique sur une ligne dans le tableau "Gestion des Évaluations", le dialogue de détails affiche toujours **"Stephane Aguerre"** au lieu de l'opérateur sélectionné.

### Exemple
- User clique sur "CAMMARATTA Robert"
- Dialogue affiché: "Détails - Stephane Aguerre" ❌
- Attendu: "Détails - CAMMARATTA Robert" ✅

---

## 🔍 Cause racine

### Architecture du problème

**Fichier**: `App/core/gui/gestion_evaluation.py`

Le dialogue "Gestion des Évaluations" fonctionne en 3 étapes:

1. **Chargement des données** (`load_data()`)
   - Requête SQL qui récupère tous les opérateurs actifs
   - Stockage dans `self.all_evaluations` (liste complète)

2. **Filtrage** (`apply_filters()`)
   - Applique les filtres de recherche et de statut
   - Crée une liste `filtered` à partir de `all_evaluations`
   - Appelle `display_operateurs(filtered)`

3. **Affichage** (`display_operateurs(operateurs)`)
   - Affiche la liste filtrée dans le tableau
   - Colonne 0 (cachée): `personnel_id`
   - Colonnes 1-6: Nom, Prénom, Matricule, etc.

### Bug dans `_on_row_double_click(row, col)`

**Code AVANT (ligne 1377-1398):**
```python
def _on_row_double_click(self, row, col):
    # ...

    # ❌ BUG: Utilise l'index de la ligne visible dans all_evaluations
    if row < len(self.all_evaluations):
        eval_data = self.all_evaluations[row]  # ← Mauvais index!
        operateur_id = eval_data.get('personnel_id')
        nom = eval_data.get('nom')
        prenom = eval_data.get('prenom')
```

**Problème:**
- `row` est l'index dans le **tableau filtré/trié** affiché à l'écran
- `self.all_evaluations[row]` récupère l'élément à la position `row` dans la **liste complète non filtrée**
- Quand le tableau est trié ou filtré, les index ne correspondent plus!

**Exemple concret:**
```
all_evaluations (liste complète):
  [0] Stephane Aguerre
  [1] CAMMARATTA Robert
  [2] Autre Personne

Tableau affiché (filtré par "À planifier"):
  [0] CAMMARATTA Robert  (mais all_evaluations[0] = Aguerre!)

Double-clic sur ligne 0 → Affiche Aguerre au lieu de CAMMARATTA
```

---

## ✅ Correction appliquée

### Solution: Récupérer l'ID depuis la colonne cachée du tableau

**Code APRÈS (ligne 1377-1402):**
```python
def _on_row_double_click(self, row, col):
    """Gère le double-clic sur une ligne du tableau."""
    # Ne pas ouvrir le dialogue si on double-clique sur les colonnes de dates (5-6)
    if col in [5, 6]:
        return

    # ✅ FIX: Récupérer l'ID depuis la colonne cachée (colonne 0)
    id_item = self.table.item(row, 0)
    if not id_item:
        return

    operateur_id = int(id_item.text())

    # ✅ Récupérer nom et prénom depuis les colonnes visibles
    nom_item = self.table.item(row, 1)
    prenom_item = self.table.item(row, 2)

    nom = nom_item.text() if nom_item else ""
    prenom = prenom_item.text() if prenom_item else ""

    # Ouvrir le dialogue détaillé avec 2 onglets
    dialog = DetailOperateurDialog(operateur_id, nom, prenom, self)
    dialog.exec_()

    # Recharger les données après fermeture du dialogue
    self.load_data()
```

### Avantages de cette approche

1. **Indépendant du tri**: Peu importe l'ordre du tableau, l'ID reste correct
2. **Indépendant du filtrage**: Même avec des filtres actifs, l'ID est toujours le bon
3. **Lecture directe**: On lit les données directement depuis le tableau visible
4. **Pas de dépendance**: Plus besoin de `self.all_evaluations` pour récupérer les infos

---

## 🧪 Test de validation

### Scénario 1: Tableau non filtré
1. ✅ Ouvrir "Gestion des Évaluations"
2. ✅ Double-cliquer sur "CAMMARATTA Robert"
3. ✅ Vérifier que le dialogue affiche "Détails - CAMMARATTA Robert"

### Scénario 2: Tableau filtré
1. ✅ Ouvrir "Gestion des Évaluations"
2. ✅ Filtrer par "À planifier (30j)"
3. ✅ Double-cliquer sur le premier opérateur listé
4. ✅ Vérifier que le dialogue affiche le bon opérateur

### Scénario 3: Tableau trié
1. ✅ Ouvrir "Gestion des Évaluations"
2. ✅ Cliquer sur l'en-tête "Nom" pour trier
3. ✅ Double-cliquer sur n'importe quel opérateur
4. ✅ Vérifier que le dialogue affiche le bon opérateur

### Scénario 4: Recherche active
1. ✅ Ouvrir "Gestion des Évaluations"
2. ✅ Rechercher "Robert"
3. ✅ Double-cliquer sur un résultat
4. ✅ Vérifier que le dialogue affiche le bon opérateur

---

## 📊 Structure du tableau

### Colonnes du QTableWidget

| Col | Champ          | Visible | Source                        |
|-----|----------------|---------|-------------------------------|
| 0   | personnel_id   | ❌ Non  | `oper_data['personnel_id']`   |
| 1   | Nom            | ✅ Oui  | `oper_data['nom']`            |
| 2   | Prénom         | ✅ Oui  | `oper_data['prenom']`         |
| 3   | Matricule      | ✅ Oui  | `oper_data['matricule']`      |
| 4   | Polyvalences   | ✅ Oui  | Calculé (N4×X, N3×Y, etc.)    |
| 5   | Évaluations    | ✅ Oui  | Calculé (retard, à planifier) |
| 6   | Statut         | ✅ Oui  | `oper_data['statut']`         |

La colonne 0 (personnel_id) est cachée avec `setColumnHidden(0, True)` mais reste accessible via `table.item(row, 0)`.

---

## 🎯 Impact utilisateur

**Avant le fix:**
- ❌ Impossible de consulter les détails du bon opérateur
- ❌ Toujours "Stephane Aguerre" affiché (premier dans all_evaluations)
- ❌ Confusion totale pour l'utilisateur

**Après le fix:**
- ✅ Le dialogue affiche le bon opérateur sélectionné
- ✅ Fonctionne avec tri, filtrage, et recherche
- ✅ Expérience utilisateur cohérente

---

## 📁 Fichiers modifiés

1. **`App/core/gui/gestion_evaluation.py`**
   - Ligne 1377-1402: Méthode `_on_row_double_click()` corrigée

---

## 🔍 Leçons apprises

### Anti-pattern identifié
❌ **Ne jamais utiliser l'index de ligne visuel pour accéder à une liste de données séparée**

```python
# ❌ MAUVAIS
row = tableau_visual_index
data = all_data[row]  # Les index ne correspondent pas après tri/filtrage!
```

### Pattern recommandé
✅ **Toujours stocker l'ID unique dans une colonne cachée du tableau**

```python
# ✅ BON
id_item = table.item(row, 0)  # Colonne cachée avec l'ID
id = int(id_item.text())
# Utiliser l'ID pour faire une requête ou chercher dans les données
```

### Alternative possible
Si on ne veut pas utiliser de colonne cachée, on peut:
1. Utiliser `setData()` sur un QTableWidgetItem pour stocker des données Python
2. Créer un mapping `{row_visual: personnel_id}` mis à jour après chaque affichage
3. Utiliser un QTableView avec un modèle custom au lieu de QTableWidget

---

## ✅ Validation finale

- [x] Bug identifié et compris
- [x] Correction appliquée
- [x] Code testé avec différents scénarios
- [x] Documentation complète rédigée
- [x] Utilisateur peut maintenant voir les bons détails

**Date du fix**: 2026-01-13
**Version**: EMAC v1.0
**Auteur**: Claude Code + tlahirigoyen
