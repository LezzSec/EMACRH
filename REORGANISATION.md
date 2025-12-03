# Réorganisation du Projet EMAC ✅

## Date de réorganisation
2 décembre 2025

## Changements effectués

### 📁 Nouvelle structure de dossiers

```
EMAC/
├── docs/                          # 📄 Toute la documentation
│   ├── README.md
│   ├── GUIDE_UTILISATION_ABSENCES.md
│   ├── MODULE_ABSENCES_README.md
│   └── ANALYSE_FONCTIONNALITES_RH_MANQUANTES.md
│
├── App/
│   ├── core/                      # ✅ Code applicatif (inchangé)
│   │   ├── db/
│   │   ├── services/
│   │   ├── gui/
│   │   └── exporters/
│   │
│   ├── tests/                     # 🧪 NOUVEAU - Tous les tests
│   │   ├── README.md
│   │   ├── test_add_operateur.py
│   │   ├── test_advanced.py
│   │   ├── test_database_integrity.py
│   │   ├── test_masquage_operateur.py
│   │   ├── test_matricule_service.py
│   │   └── test_personnel_non_production.py
│   │
│   ├── scripts/                   # 🔧 NOUVEAU - Scripts utilitaires
│   │   ├── README.md
│   │   ├── cleanup_test_data.py
│   │   ├── fix_matricule_lowercase.py
│   │   ├── install_absences_module.py
│   │   ├── delete_operators.py
│   │   └── quick_db_query.py
│   │
│   ├── database/                  # 💾 NOUVEAU - Fichiers BDD
│   │   ├── README.md
│   │   ├── schema/
│   │   │   └── bddemac.sql
│   │   ├── migrations/
│   │   │   └── schema_absences_conges.sql
│   │   └── backups/
│   │       ├── (8 fichiers .sql)
│   │
│   ├── logs/                      # ✅ Inchangé
│   ├── run/                       # ✅ Inchangé
│   └── run_emac.vbs              # ✅ Inchangé
│
├── Deploy/                        # ✅ Inchangé
├── Fichiers inutilisés/          # ✅ Inchangé
└── CLAUDE.md                      # ✅ Mis à jour
```

## Déplacements effectués

### ✅ Tests (App/ → App/tests/)
- test_add_operateur.py
- test_advanced.py
- test_database_integrity.py
- test_masquage_operateur.py
- test_matricule_service.py
- test_personnel_non_production.py

### ✅ Scripts (App/ → App/scripts/)
- cleanup_test_data.py
- fix_matricule_lowercase.py
- install_absences_module.py

### ✅ Base de données (racine + App/Version BDD → App/database/)
- **schema/** : bddemac.sql
- **migrations/** : schema_absences_conges.sql
- **backups/** : 8 fichiers .sql (bddserver*.sql, dumpemacbdd.sql)

### ✅ Documentation (racine → docs/)
- GUIDE_UTILISATION_ABSENCES.md
- MODULE_ABSENCES_README.md
- ANALYSE_FONCTIONNALITES_RH_MANQUANTES.md

## Fichiers supprimés
- ❌ App/nul
- ❌ EMAC (2).zip

## Fichiers créés
- ✅ docs/README.md
- ✅ App/tests/README.md
- ✅ App/scripts/README.md
- ✅ App/database/README.md
- ✅ App/.gitignore (mis à jour)

## Fichiers mis à jour
- 📝 CLAUDE.md - Mise à jour de toutes les références de chemins

## Avantages de la nouvelle structure

1. **Organisation claire** : Chaque type de fichier a son dossier dédié
2. **Meilleure maintenabilité** : Plus facile de trouver les fichiers
3. **Documentation centralisée** : Toute la doc dans docs/
4. **Tests isolés** : Facile à exécuter et maintenir
5. **Scripts séparés** : Les utilitaires sont clairement identifiés
6. **BDD organisée** : Schema, migrations et backups bien séparés

## Migration pour les développeurs

### Anciens chemins → Nouveaux chemins

```bash
# Tests
App/test_*.py                           → App/tests/test_*.py

# Scripts
App/cleanup_test_data.py                → App/scripts/cleanup_test_data.py
App/fix_matricule_lowercase.py         → App/scripts/fix_matricule_lowercase.py
App/install_absences_module.py         → App/scripts/install_absences_module.py

# Base de données
App/Version BDD/bddemac.sql             → App/database/schema/bddemac.sql
App/Version BDD/schema_absences_conges.sql → App/database/migrations/schema_absences_conges.sql
bddserver*.sql                          → App/database/backups/bddserver*.sql

# Documentation
GUIDE_UTILISATION_ABSENCES.md           → docs/GUIDE_UTILISATION_ABSENCES.md
MODULE_ABSENCES_README.md               → docs/MODULE_ABSENCES_README.md
ANALYSE_FONCTIONNALITES_RH_MANQUANTES.md → docs/ANALYSE_FONCTIONNALITES_RH_MANQUANTES.md
```

### Commandes à mettre à jour

```bash
# Avant
py test_database_integrity.py

# Après
py tests/test_database_integrity.py

# Avant
py cleanup_test_data.py

# Après
py scripts/cleanup_test_data.py
```

## Notes importantes

⚠️ **Imports dans le code** : Aucun import Python n'a été modifié car les fichiers déplacés sont des scripts indépendants ou des tests.

✅ **Rétrocompatibilité** : Le code source dans `App/core/` n'a pas été modifié, l'application fonctionne exactement comme avant.

📚 **Git** : Pensez à faire un commit après cette réorganisation :
```bash
git add .
git commit -m "Réorganisation de la structure du projet - Tests, scripts, docs et BDD dans des dossiers dédiés"
```
