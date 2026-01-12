# 📁 Plan de réorganisation du projet EMAC

## 🎯 Objectifs

1. **Séparer** la documentation de développement et utilisateur
2. **Regrouper** les fichiers de sécurité et configuration
3. **Clarifier** la structure pour les nouveaux développeurs
4. **Supprimer** les fichiers obsolètes

---

## 📊 Structure AVANT

```
EMAC/
├── docs/                           # Documentation mélangée (dev + user)
│   ├── ANALYSE_*.md
│   ├── MODULE_*.md
│   ├── GUIDE_*.md (14 fichiers)
│   └── README.md
├── App/
│   ├── core/
│   ├── database/
│   ├── scripts/
│   ├── tests/
│   ├── .env
│   ├── .env.example
│   ├── configure_db.bat
│   ├── SECURITE_DB.md
│   └── README_CONFIG.md
├── CLAUDE.md                       # À la racine
├── SECURITE_CHANGELOG.md           # À la racine
├── STRUCTURE.md                    # À la racine
├── REORGANISATION.md               # À la racine
├── TESTS_RAPPORT.md               # À la racine
└── 10+ autres .md à la racine
```

**Problèmes** :
- ❌ 15+ fichiers Markdown à la racine
- ❌ Documentation de sécurité éparpillée
- ❌ Pas de séparation docs dev/user
- ❌ Fichiers obsolètes (REORGANISATION.md, STRUCTURE.md)

---

## 📊 Structure APRÈS

```
EMAC/
├── 📄 README.md                    # Guide principal (nouveau)
├── 📄 CLAUDE.md                    # Instructions pour Claude Code
├── 📄 CHANGELOG.md                 # Historique des versions (nouveau)
│
├── 📁 docs/                        # Documentation
│   ├── 📁 dev/                     # Documentation développeur
│   │   ├── architecture.md         # Architecture technique
│   │   ├── contributing.md         # Guide de contribution
│   │   ├── database-schema.md      # Schéma base de données
│   │   └── tests.md                # Guide des tests
│   │
│   ├── 📁 user/                    # Documentation utilisateur
│   │   ├── guide-absences.md
│   │   ├── guide-evaluations.md
│   │   ├── guide-documents.md
│   │   └── faq.md
│   │
│   ├── 📁 features/                # Documentation fonctionnelle
│   │   ├── module-absences.md
│   │   ├── module-documents.md
│   │   ├── module-evaluations.md
│   │   └── historique-polyvalence.md
│   │
│   └── 📁 security/                # Documentation sécurité
│       ├── sql-injection-fixes.md
│       ├── credentials-management.md
│       └── security-changelog.md
│
├── 📁 App/
│   ├── 📁 core/                    # Code applicatif
│   │   ├── db/
│   │   ├── gui/
│   │   ├── services/
│   │   ├── exporters/
│   │   └── utils/
│   │
│   ├── 📁 database/                # Base de données
│   │   ├── schema/
│   │   ├── migrations/
│   │   └── backups/
│   │
│   ├── 📁 scripts/                 # Scripts utilitaires
│   │   ├── maintenance/            # Scripts de maintenance
│   │   ├── setup/                  # Scripts d'installation
│   │   └── dev/                    # Scripts de développement
│   │
│   ├── 📁 tests/                   # Tests
│   │   ├── unit/
│   │   ├── integration/
│   │   └── reports/
│   │
│   ├── 📁 config/                  # Configuration (NOUVEAU)
│   │   ├── .env.example
│   │   ├── settings.example.json
│   │   └── README.md
│   │
│   ├── 📁 docs/                    # Documentation spécifique App
│   │   ├── installation.md
│   │   ├── configuration.md
│   │   └── security.md
│   │
│   ├── 📁 logs/                    # Logs (ignoré par Git)
│   ├── 📁 run/                     # Fichiers d'exécution
│   │
│   ├── .env                        # Configuration locale (Git ignored)
│   ├── .gitignore
│   ├── configure_db.bat            # Script de config
│   └── run_emac.vbs                # Lanceur Windows
│
└── 📁 Deploy/                      # Déploiement
    └── (fichiers de build)
```

---

## 🔄 Migrations de fichiers

### Racine → docs/dev/
- `STRUCTURE.md` → `docs/dev/architecture.md` (renommé)
- `TESTS_RAPPORT.md` → `docs/dev/tests-report.md`
- `OPTIMISATION_EXECUTABLE.md` → `docs/dev/build-optimization.md`

### Racine → docs/security/
- `SECURITE_CHANGELOG.md` → `docs/security/security-changelog.md`
- `App/SECURITE_DB.md` → `docs/security/database-credentials.md`

### Racine → docs/user/
- Créer `docs/user/installation.md` (consolider les guides)

### App/ → App/config/
- `App/.env.example` → `App/config/.env.example`
- `App/README_CONFIG.md` → `App/config/README.md`

### docs/ → docs/features/
- Réorganiser par module fonctionnel

---

## 🗑️ Fichiers à supprimer (obsolètes)

- `REORGANISATION.md` (ancien plan)
- `BUGFIX_TRI_URGENCE.md` (rapport temporaire)
- `INSTALLATION_DOCUMENTS_RH.md` (dupliquer dans docs/)
- `RAPPORT_TESTS_SIMULATION.md` (ancien)

---

## ✅ Nouveaux fichiers à créer

1. **README.md** (racine) : Guide d'accueil du projet
2. **CHANGELOG.md** : Historique des versions
3. **docs/dev/contributing.md** : Guide de contribution
4. **docs/dev/architecture.md** : Architecture technique
5. **docs/user/faq.md** : Questions fréquentes

---

## 📝 Mises à jour nécessaires

### 1. CLAUDE.md
- Mettre à jour tous les chemins de fichiers
- Ajouter référence à la nouvelle structure

### 2. .gitignore
- Ajouter `App/logs/*`
- Ajouter `App/config/.env`

### 3. Scripts Python
- Vérifier les imports après déplacement de `.env.example`

---

## 🚀 Ordre d'exécution

1. ✅ Créer la structure de dossiers
2. ✅ Déplacer les fichiers de documentation
3. ✅ Déplacer les fichiers de configuration
4. ✅ Mettre à jour CLAUDE.md
5. ✅ Mettre à jour .gitignore
6. ✅ Créer README.md principal
7. ✅ Supprimer fichiers obsolètes
8. ✅ Tester l'application
9. ✅ Commit

---

## 🎯 Avantages

### Pour les développeurs
- ✅ Structure claire et logique
- ✅ Documentation séparée par type
- ✅ Facile de trouver l'information
- ✅ Moins de fichiers à la racine

### Pour les nouveaux contributeurs
- ✅ README.md clair à la racine
- ✅ Guide de contribution dédié
- ✅ Architecture documentée

### Pour la sécurité
- ✅ Documentation sécurité centralisée
- ✅ Configuration dans un dossier dédié
- ✅ Meilleure visibilité des fichiers sensibles

---

## ⚠️ Précautions

- [ ] Sauvegarder avant la réorganisation
- [ ] Vérifier que l'application fonctionne après
- [ ] Mettre à jour tous les chemins dans le code
- [ ] Tester les imports Python
- [ ] Vérifier les liens dans la documentation

---

**Prêt à exécuter ?** 🚀
