# 🚀 Guide Rapide - Réorganisation EMAC v2.0

## ✅ Ce qui a été fait

La nouvelle structure est en place:
- ✅ `src/emac/` - Nouveau package Python
- ✅ `tests/` - Tests organisés
- ✅ `database/` - Schémas et migrations
- ✅ `tools/` - Outils catégorisés
- ✅ `build/` - Build centralisé
- ✅ `docs/` - Documentation structurée
- ✅ `deploy/` - Déploiement organisé
- ✅ Archives créées

## ⏳ Ce qui reste à faire

### 1. Migration des Imports (IMPORTANT!)

Les fichiers dans `src/emac/` ont été copiés mais **gardent les anciens imports**.

**Solution:** Exécuter le script de migration

```bash
cd tools/migration
python migrate_imports.py
```

Ce script va automatiquement convertir:
- `from core.db.configbd import` → `from emac.db.connection import`
- `from core.services.evaluation_service import` → `from emac.services.evaluation import`
- Etc.

### 2. Tester l'Application

```bash
# Depuis la racine
python -m emac
```

Si ça ne fonctionne pas:
1. Vérifier que la migration des imports a été faite
2. Vérifier le fichier `.env` à la racine
3. Consulter `REORGANISATION_2026-01-05.md`

### 3. Mettre à Jour les Configurations

- `build/configs/emac.spec` - Adapter les chemins
- `tests/conftest.py` - Adapter si nécessaire

### 4. Finaliser

Une fois tout testé:
```bash
# Remplacer les anciens fichiers
mv README_NEW.md README.md
mv CLAUDE_NEW.md CLAUDE.md
```

---

## 📋 Checklist Rapide

```
[ ] 1. Exécuter migrate_imports.py
[ ] 2. Tester: python -m emac
[ ] 3. Vérifier build: cd build/scripts && build.bat
[ ] 4. Exécuter tests: cd tests && python run_tests.py
[ ] 5. Remplacer README et CLAUDE
[ ] 6. Commit des changements
```

---

## 🔄 Changements Importants

### Imports
```python
# Ancien
from core.db.configbd import get_connection
from core.services.evaluation_service import calculate_next_evaluation
from core.gui.ui_theme import EmacTheme

# Nouveau
from emac.db.connection import get_connection
from emac.services.evaluation import calculate_next_evaluation
from emac.gui.components.theme import EmacTheme
```

### Lancement
```bash
# Ancien
cd App
py -m core.gui.main_qt

# Nouveau
python -m emac
```

### Build
```bash
# Ancien
cd App
build_clean.bat

# Nouveau
cd build/scripts
build.bat
```

---

## 📚 Documentation Complète

- **Vue d'ensemble:** `README_NEW.md`
- **Guide développeur:** `CLAUDE_NEW.md`
- **Détails migration:** `REORGANISATION_2026-01-05.md`
- **Documentation modules:** `docs/`, `build/README.md`, `database/README.md`, etc.

---

## 🆘 En Cas de Problème

1. **L'application ne démarre pas**
   - Vérifier migration des imports
   - Vérifier fichier `.env`
   - Consulter logs

2. **Imports manquants**
   - Re-exécuter `migrate_imports.py`
   - Vérifier paths dans PYTHONPATH

3. **Build échoue**
   - Mettre à jour `build/configs/emac.spec`
   - Vérifier chemins

4. **Tests échouent**
   - Mettre à jour imports dans tests
   - Vérifier fixtures

---

## 🎯 Prochaines Étapes

1. Migration imports → Tests → Build
2. Validation complète
3. Mise en production v2.0
4. Suppression progressive de l'ancien code `App/`

---

**Date:** 2026-01-05
**Statut:** Structure créée ✅ | Migration code à faire ⏳
