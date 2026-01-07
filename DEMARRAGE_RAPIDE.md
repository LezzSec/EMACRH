# 🚀 Démarrage Rapide - EMAC

Guide ultra-rapide pour démarrer avec le projet EMAC.

---

## ⚡ Installation en 5 minutes

### 1. Prérequis

```bash
# Vérifier Python (3.8+)
python --version

# Vérifier MySQL (8.0+)
mysql --version
```

### 2. Configuration

```bash
# Cloner le projet
git clone <repo-url>
cd EMAC

# Installer les dépendances
pip install -r App/requirements.txt

# Configurer la base de données
cd App/config
configure_db.bat  # Windows

# Initialiser la base MySQL
cd ../..
mysql -u root -p emac_db < App/database/schema/bddemac.sql
```

### 3. Lancement

```bash
cd App
py -m core.gui.main_qt
```

✅ **C'est tout !** L'application devrait se lancer.

---

## 📁 Structure Essentielle

```
EMAC/
├── App/              # Code source (c'est ici que vous codez)
├── docs/             # Documentation (à lire en premier)
├── build-scripts/    # Pour compiler l'application
├── tests/            # Pour tester vos modifications
└── README.md         # Documentation complète
```

**Pour plus de détails** : voir [STRUCTURE.md](STRUCTURE.md)

---

## 🎯 Cas d'Usage Courants

### Je veux...

#### ...lancer l'application en développement
```bash
cd App
py -m core.gui.main_qt
```

#### ...compiler l'application pour distribution
```bash
cd build-scripts
build_optimized.bat
# Résultat dans : temp/dist/EMAC/EMAC.exe
```

#### ...tester mes modifications
```bash
# Test spécifique
py tests/test_gestion_evaluation.py

# Tous les tests unitaires
cd App
py tests/run_all_tests.py
```

#### ...modifier l'interface
- Fichiers dans : `App/core/gui/`
- Thème : `App/core/gui/ui_theme.py`
- Composants : `App/core/gui/emac_ui_kit.py`

#### ...modifier la logique métier
- Services dans : `App/core/services/`
- Exemples :
  - Évaluations : `evaluation_service.py`
  - Contrats : `contrat_service.py`
  - Absences : `absence_service.py`

#### ...modifier la base de données
1. Modifier : `App/database/schema/bddemac.sql`
2. Créer migration : `App/database/migrations/XXX_ma_migration.sql`
3. Appliquer : `mysql -u root -p emac_db < App/database/migrations/XXX_ma_migration.sql`

#### ...comprendre l'architecture
- Lire : `docs/dev/architecture.md`
- Voir : `STRUCTURE.md`

#### ...ajouter une nouvelle fonctionnalité
1. Planifier dans `docs/features/`
2. Coder dans `App/core/`
3. Tester dans `tests/` ou `App/tests/`
4. Documenter dans `docs/`

---

## 🔧 Dépannage Rapide

### Erreur : "Module not found"
```bash
# Vérifier les dépendances
pip install -r App/requirements.txt
```

### Erreur : "Can't connect to MySQL"
```bash
# Vérifier que MySQL est lancé
mysql -u root -p

# Vérifier la configuration
cat App/.env
# Doit contenir :
# EMAC_DB_PASSWORD=votre_mot_de_passe
# EMAC_DB_HOST=localhost
# EMAC_DB_USER=root
# EMAC_DB_NAME=emac_db
```

### Erreur : "Table doesn't exist"
```bash
# Réinitialiser la base
mysql -u root -p emac_db < App/database/schema/bddemac.sql
```

### L'application ne se lance pas
```bash
# Test de diagnostic complet
py tests/test_menu_gestion_eval.py

# Vérifier les logs
cat App/logs/emac.log
```

### Erreur de build
```bash
# Analyser les dépendances
cd build-scripts
py analyze_imports.py

# Vérifier la configuration PyInstaller
notepad EMAC_optimized.spec
```

---

## 📚 Documentation Complète

| Document | Contenu |
|----------|---------|
| [README.md](README.md) | Documentation principale complète |
| [CLAUDE.md](CLAUDE.md) | Instructions pour Claude Code |
| [STRUCTURE.md](STRUCTURE.md) | Arborescence détaillée du projet |
| [docs/dev/architecture.md](docs/dev/architecture.md) | Architecture système |
| [docs/user/](docs/user/) | Guides utilisateur |
| [build-scripts/README.md](build-scripts/README.md) | Guide de compilation |
| [tests/README.md](tests/README.md) | Guide des tests |

---

## 🆘 Besoin d'Aide ?

### Problème de code
1. Lire [docs/dev/architecture.md](docs/dev/architecture.md)
2. Chercher dans [docs/features/](docs/features/)
3. Voir les exemples dans `App/core/`

### Problème de configuration
1. Lire [App/config/README.md](App/config/README.md)
2. Voir [docs/security/database-credentials.md](docs/security/database-credentials.md)

### Problème de base de données
1. Vérifier [App/database/schema/bddemac.sql](App/database/schema/bddemac.sql)
2. Voir les migrations dans [App/database/migrations/](App/database/migrations/)

### Bug connu
1. Chercher dans [session-reports/](session-reports/)
2. Format : `BUG_FIX_*.md` ou `DIAGNOSTIC_*.md`

---

## ✅ Checklist de Validation

Après l'installation, vérifier :

- [ ] Python 3.8+ installé
- [ ] MySQL 8.0+ installé et démarré
- [ ] Dépendances installées (`pip install -r App/requirements.txt`)
- [ ] Fichier `App/.env` configuré
- [ ] Base de données `emac_db` créée et initialisée
- [ ] Application se lance (`py -m core.gui.main_qt`)
- [ ] Tests passent (`py tests/test_gestion_evaluation.py`)

---

## 🎓 Pour Aller Plus Loin

### Apprendre l'architecture
1. Lire [docs/dev/architecture.md](docs/dev/architecture.md)
2. Explorer `App/core/` module par module
3. Lire les commentaires dans le code

### Contribuer
1. Lire [CLAUDE.md](CLAUDE.md) (conventions de code)
2. Créer une branche pour votre fonctionnalité
3. Tester avec `tests/`
4. Documenter dans `docs/`

### Optimiser
1. Lire [docs/dev/guide-optimisation-build.md](docs/dev/guide-optimisation-build.md)
2. Analyser avec `build-scripts/analyze_imports.py`
3. Compiler avec `build-scripts/build_optimized.bat`

---

**Dernière mise à jour** : 2026-01-07
**Temps de lecture** : 5 minutes
**Temps d'installation** : 5-10 minutes

**Prêt à coder !** 🚀
