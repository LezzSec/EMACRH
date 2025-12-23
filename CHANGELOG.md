# Changelog - EMAC

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

---

## [1.1.0] - 2025-12-17

### ✨ Ajouté - Système de Gestion des Utilisateurs

#### Authentification
- 🔐 Écran de connexion au démarrage de l'application
- 🔑 Hachage sécurisé des mots de passe avec bcrypt (facteur 12)
- 👤 Session utilisateur avec informations de l'utilisateur connecté
- 🚪 Fonctionnalité de déconnexion avec confirmation

#### Rôles et permissions
- 👑 **Rôle Admin** : Accès complet à toutes les fonctionnalités
- 🏭 **Rôle Gestion Production** :
  - Accès complet : personnel, évaluations, polyvalence, postes, grilles
  - Lecture seule : contrats, planning/absences, historique
  - Pas d'accès : documents RH, gestion utilisateurs

- 📋 **Rôle Gestion RH** :
  - Accès complet : contrats, documents RH
  - Lecture seule : personnel, polyvalence, postes, historique, grilles
  - Pas d'accès : évaluations, planning, gestion utilisateurs

#### Interface
- 🎨 Écran de connexion stylisé avec le thème EMAC
- 👥 Interface de gestion des utilisateurs (admin uniquement)
  - Création de nouveaux utilisateurs
  - Activation/désactivation de comptes
  - Changement de mot de passe
  - Liste avec statut et dernière connexion

- 🧭 Menu drawer adaptatif selon les permissions
- 📊 Affichage de l'utilisateur connecté et son rôle dans l'en-tête

#### Base de données
- 📦 Tables ajoutées :
  - `roles` : Définition des rôles
  - `utilisateurs` : Comptes utilisateurs
  - `permissions` : Permissions granulaires par module
  - `logs_connexion` : Audit des connexions/déconnexions

- 🔧 Migration automatisée avec script Python

#### Sécurité
- 🛡️ Contrôle d'accès basé sur les permissions
- 📝 Logs d'audit pour toutes les actions sensibles
- 🔐 Mots de passe jamais stockés en clair
- ⚠️ Validation des entrées utilisateur

#### Documentation
- 📚 Guide utilisateur complet ([`docs/user/guide-gestion-utilisateurs.md`](docs/user/guide-gestion-utilisateurs.md))
- 👨‍💻 Documentation technique pour développeurs ([`docs/dev/authentication-system.md`](docs/dev/authentication-system.md))
- 📖 README du système ([`SYSTEME_UTILISATEURS_README.md`](SYSTEME_UTILISATEURS_README.md))

#### Scripts et outils
- ⚙️ Script de migration : `apply_user_management_migration.py`
- 🧪 Script de test : `test_auth_system.py`
- 🛠️ Helper de permissions : `permission_helper.py`

#### Fichiers créés
```
App/
├── core/
│   ├── services/
│   │   └── auth_service.py                    # Service d'authentification
│   ├── gui/
│   │   ├── login_dialog.py                    # Écran de connexion
│   │   └── user_management.py                 # Gestion des utilisateurs
│   └── utils/
│       └── permission_helper.py               # Helpers de permissions
├── database/
│   └── migrations/
│       └── 001_add_user_management.sql        # Migration SQL
├── scripts/
│   ├── apply_user_management_migration.py     # Script de migration
│   └── test_auth_system.py                    # Tests
└── requirements.txt                            # Dépendances mises à jour

docs/
├── user/
│   └── guide-gestion-utilisateurs.md          # Guide utilisateur
└── dev/
    └── authentication-system.md                # Doc technique

SYSTEME_UTILISATEURS_README.md                  # README principal
CHANGELOG.md                                     # Ce fichier
```

#### Fichiers modifiés
- [`App/core/gui/main_qt.py`](App/core/gui/main_qt.py)
  - Ajout de l'écran de connexion au démarrage
  - Affichage de l'utilisateur connecté
  - Menu filtré par permissions
  - Bouton de déconnexion

### 🔧 Dépendances ajoutées
- `bcrypt==4.1.2` - Hachage sécurisé des mots de passe
- `python-dotenv==1.0.0` - Gestion des variables d'environnement

### 📋 Installation

Pour mettre à jour vers cette version :

1. Installer les nouvelles dépendances :
```bash
pip install bcrypt python-dotenv
```

2. Appliquer la migration :
```bash
cd App
py scripts/apply_user_management_migration.py
```

3. Se connecter avec le compte admin par défaut :
   - Username: `admin`
   - Password: `admin123`
   - ⚠️ **IMPORTANT** : Changer ce mot de passe immédiatement !

### ⚠️ Breaking Changes

- L'application nécessite maintenant une authentification au démarrage
- Les utilisateurs existants doivent être créés via l'interface admin
- Le module `bcrypt` est obligatoire

### 🐛 Corrections
- Aucune dans cette version (nouvelle fonctionnalité)

---

## [1.0.0] - 2025-XX-XX

### Version initiale
- Gestion du personnel
- Gestion des évaluations et polyvalence
- Gestion des contrats
- Documents RH
- Planning et absences
- Historique des actions
- Grilles de compétences
- Export vers Excel et PDF

---

## Format

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

### Types de changements

- `Ajouté` pour les nouvelles fonctionnalités
- `Modifié` pour les changements aux fonctionnalités existantes
- `Déprécié` pour les fonctionnalités bientôt supprimées
- `Supprimé` pour les fonctionnalités supprimées
- `Corrigé` pour les corrections de bugs
- `Sécurité` pour les vulnérabilités corrigées
