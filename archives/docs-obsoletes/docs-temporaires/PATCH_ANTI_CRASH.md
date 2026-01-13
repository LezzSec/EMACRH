# Patch Anti-Crash pour EMAC

## Problème identifié

L'application crash après la connexion lors du chargement du dashboard.

## Modifications appliquées

### 1. DatabaseCursor dictionary=True (main_qt.py:619)
**Avant:**
```python
with DatabaseCursor() as cur:
```

**Après:**
```python
with DatabaseCursor(dictionary=True) as cur:
```

### 2. Gestion d'erreur améliorée (main_qt.py:695-707)
Ajout d'un message d'avertissement à l'utilisateur en cas d'erreur de chargement.

## Pour tester

1. **Test des requêtes DB:**
   ```bash
   python test_dashboard.py
   ```
   (Utilisez vos vrais identifiants)

2. **Test application complète:**
   ```bash
   cd App
   python -m core.gui.main_qt
   ```

## Si le crash persiste

Envoyez-moi la sortie complète de la console avec toutes les erreurs.

Le crash se produit probablement dans l'une de ces fonctions:
- `bootstrap_async()` (ligne 247)
- `load_evaluations_async()` (ligne 602)
- `_fetch_evaluations()` (ligne 614)
- `populate_filters_async()` (ligne 579)

## Solution temporaire

Si l'application ne démarre toujours pas, commentez temporairement le chargement async:

Dans `main_qt.py`, ligne 241, commentez:
```python
# QTimer.singleShot(0, self.bootstrap_async)
```

Cela désactivera le chargement des données du dashboard mais permettra à l'application de démarrer.
