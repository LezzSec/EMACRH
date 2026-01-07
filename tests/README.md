# 🧪 Scripts de Test

Ce dossier contient les scripts de test pour valider les fonctionnalités de l'application EMAC.

## 📁 Scripts disponibles

### Tests du module Gestion Évaluation

- **`test_gestion_evaluation.py`** - Test basique d'import et création du dialogue
- **`test_gestion_eval_full.py`** - Test complet avec connexion DB
- **`test_gestion_eval_crash.py`** - Diagnostic détaillé pour identifier les erreurs
- **`test_menu_gestion_eval.py`** - Simulation du clic sur le menu

### Utilisation

```bash
# Depuis la racine du projet
py tests/test_gestion_evaluation.py
py tests/test_gestion_eval_full.py
py tests/test_menu_gestion_eval.py
```

## 🔍 Tests de diagnostic

Pour diagnostiquer un problème spécifique :

```bash
# Test complet avec stack traces détaillées
py tests/test_gestion_eval_crash.py
```

Ce script affiche :
- ✅ Import du module
- ✅ Création de l'interface Qt
- ✅ Connexion à la base de données
- ✅ Chargement des données
- ❌ Messages d'erreur détaillés si échec

## 📝 Notes

- Les tests nécessitent une connexion à la base de données MySQL
- Assurez-vous que le fichier `App/.env` est configuré
- Les tests ne modifient pas les données de production
- Pour les tests unitaires complets, voir `App/tests/`

## 🎯 Ajout de nouveaux tests

Pour ajouter un nouveau test :

1. Créer un fichier `test_<nom_module>.py`
2. Importer le module à tester depuis `App/`
3. Créer une fonction de test avec gestion d'erreur
4. Documenter le test dans ce README

Exemple de structure :

```python
import sys
import traceback

def test_mon_module():
    try:
        sys.path.insert(0, 'App')
        from core.gui.mon_module import MonDialog

        # Tests ici
        print("[OK] Test réussi")
        return True
    except Exception as e:
        print(f"[ERREUR] {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_mon_module()
```
