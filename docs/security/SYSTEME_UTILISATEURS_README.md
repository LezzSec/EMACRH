# Système de Gestion des Utilisateurs - EMAC

## Résumé

Un système complet de gestion des utilisateurs avec authentification et contrôle d'accès basé sur les rôles a été implémenté dans l'application EMAC. Ce système permet de gérer 3 types d'utilisateurs avec des permissions différenciées.

---

## Fonctionnalités implémentées

### Authentification
- Écran de connexion au démarrage de l'application
- Hachage sécurisé des mots de passe avec bcrypt
- Session utilisateur persistante pendant l'utilisation
- Déconnexion avec confirmation

### Gestion des rôles

#### 1. Administrateur (`admin`)
- ✅ Accès complet à toutes les fonctionnalités
- ✅ Gestion des utilisateurs (création, modification, désactivation)
- ✅ Modification de tous les modules de l'application

#### 2. Gestion Production (`gestion_production`)
- ✅ Accès complet à la gestion du personnel, évaluations et polyvalence
-  Lecture seule sur les contrats
-  Lecture seule sur le planning (pas de modification d'absences)
- ❌ Pas d'accès aux documents RH

#### 3. Gestion RH (`gestion_rh`)
- ✅ Accès complet aux contrats et documents RH
-  Lecture seule sur le personnel et la polyvalence
- ❌ Pas d'accès aux évaluations et au planning

### Contrôle d'accès
- Filtrage automatique du menu en fonction des permissions
- Désactivation des boutons non autorisés
- Messages d'erreur explicites en cas d'accès refusé
- Affichage du nom et rôle de l'utilisateur connecté

### Audit et logs
- Enregistrement de toutes les connexions/déconnexions
- Logs des créations et modifications d'utilisateurs
- Historique consultable par les administrateurs

---

## Fichiers créés

### Base de données
- [`App/database/migrations/001_add_user_management.sql`](App/database/migrations/001_add_user_management.sql)
  - Tables : `roles`, `utilisateurs`, `permissions`, `logs_connexion`
  - Rôles et permissions prédéfinis
  - Utilisateur admin par défaut

### Services
- [`App/core/services/auth_service.py`](App/core/services/auth_service.py)
  - Authentification et gestion des sessions
  - Hachage bcrypt des mots de passe
  - Vérification des permissions
  - CRUD des utilisateurs

### Interfaces graphiques
- [`App/core/gui/login_dialog.py`](App/core/gui/login_dialog.py)
  - Écran de connexion avec validation
  - Gestion des erreurs d'authentification

- [`App/core/gui/user_management.py`](App/core/gui/user_management.py)
  - Interface de gestion des utilisateurs (admin)
  - Création, activation/désactivation
  - Changement de mot de passe

### Utilitaires
- [`App/core/utils/permission_helper.py`](App/core/utils/permission_helper.py)
  - Helpers pour contrôler l'accès aux widgets
  - Fonctions de désactivation/masquage automatiques

### Scripts
- [`App/scripts/apply_user_management_migration.py`](App/scripts/apply_user_management_migration.py)
  - Script d'application de la migration
  - Création des tables et données initiales

### Documentation
- [`docs/user/guide-gestion-utilisateurs.md`](docs/user/guide-gestion-utilisateurs.md)
  - Guide utilisateur complet
  - Instructions pour chaque rôle
  - Bonnes pratiques de sécurité

- [`docs/dev/authentication-system.md`](docs/dev/authentication-system.md)
  - Documentation technique
  - Architecture du système
  - Exemples de code

---

## Fichiers modifiés

### [`App/core/gui/main_qt.py`](App/core/gui/main_qt.py)
**Modifications** :
- Import des fonctions d'authentification
- Ajout de l'écran de connexion au lancement
- Affichage de l'utilisateur connecté dans l'en-tête
- Filtrage du menu drawer par permissions
- Bouton de déconnexion
- Méthode `show_user_management()` pour les admins

---

## Installation et utilisation

### 1. Installer les dépendances

```bash
pip install bcrypt
```

### 2. Appliquer la migration

```bash
cd App
py scripts/apply_user_management_migration.py
```

Cette commande va :
- Créer les tables nécessaires
- Configurer les 3 rôles
- Créer un utilisateur admin par défaut

### 3. Première connexion

**Identifiants par défaut** :
- Username : `admin`
- Password : `admin123`

⚠️ **IMPORTANT** : Changez ce mot de passe dès la première connexion !

### 4. Créer des utilisateurs

1. Connectez-vous en tant qu'admin
2. Cliquez sur le menu () → "Gestion des Utilisateurs"
3. Cliquez sur " Nouvel Utilisateur"
4. Remplissez le formulaire et sélectionnez le rôle approprié

---

## Permissions par rôle

| Module | Admin | Gestion Production | Gestion RH |
|--------|-------|-------------------|------------|
| Personnel | ✅ Complet | ✅ Complet |  Lecture |
| Évaluations | ✅ Complet | ✅ Complet | ❌ Aucun |
| Polyvalence | ✅ Complet | ✅ Complet |  Lecture |
| **Contrats** | ✅ Complet |  **Lecture** | ✅ Complet |
| **Documents RH** | ✅ Complet | ❌ **Aucun** | ✅ Complet |
| **Planning/Absences** | ✅ Complet |  **Lecture** | ❌ Aucun |
| Postes | ✅ Complet | ✅ Complet |  Lecture |
| Historique | ✅ Complet |  Lecture |  Lecture |
| Grilles | ✅ Complet | ✅ Complet |  Lecture |
| **Utilisateurs** | ✅ **Complet** | ❌ Aucun | ❌ Aucun |

---

## Détails techniques

### Architecture de sécurité

- **Hachage bcrypt** : Facteur de coût 12 pour une sécurité optimale
- **Singleton UserSession** : Une seule instance de session par application
- **Permissions granulaires** : Lecture, écriture, suppression par module
- **Audit trail** : Tous les événements sensibles sont enregistrés

### Structure de la base de données

#### Table `utilisateurs`
```sql
id | username | password_hash | nom | prenom | role_id | actif | date_creation | derniere_connexion
```

#### Table `permissions`
```sql
id | role_id | module | lecture | ecriture | suppression
```

#### Table `logs_connexion`
```sql
id | utilisateur_id | date_connexion | date_deconnexion | ip_address
```

---

## Tester le système

### Test 1 : Connexion en tant qu'admin
```
Username: admin
Password: admin123
```
✅ Vous devriez voir tous les menus disponibles, y compris "Gestion des Utilisateurs"

### Test 2 : Créer un utilisateur "Gestion Production"
1. Menu → Gestion des Utilisateurs
2. Créer un utilisateur avec le rôle "gestion_production"
3. Se déconnecter
4. Se reconnecter avec le nouvel utilisateur
5. ✅ Vérifier que "Gestion des Contrats" et "Documents RH" ne sont pas dans le menu

### Test 3 : Créer un utilisateur "Gestion RH"
1. Reconnecter en admin
2. Créer un utilisateur avec le rôle "gestion_rh"
3. Se déconnecter et se reconnecter avec ce compte
4. ✅ Vérifier l'accès aux contrats et documents RH uniquement

### Test 4 : Désactiver un utilisateur
1. En tant qu'admin, désactiver un utilisateur
2. Essayer de se connecter avec ce compte
3. ✅ Devrait afficher "Ce compte est désactivé"

---

## Documentation

### Pour les utilisateurs
Consultez le guide complet : [`docs/user/guide-gestion-utilisateurs.md`](docs/user/guide-gestion-utilisateurs.md)

### Pour les développeurs
Documentation technique : [`docs/dev/authentication-system.md`](docs/dev/authentication-system.md)

---

## Dépannage

### Problème : Module bcrypt introuvable
```bash
pip install bcrypt
```

### Problème : Tables non créées
```bash
py scripts/apply_user_management_migration.py
```

### Problème : Mot de passe admin oublié
Connectez-vous à MySQL et exécutez :
```sql
UPDATE utilisateurs
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5yrOvnN6G/mFa'
WHERE username = 'admin';
-- Nouveau mot de passe : admin123
```

---

## ✅ Checklist de déploiement

- [ ] Installer bcrypt : `pip install bcrypt`
- [ ] Appliquer la migration : `py scripts/apply_user_management_migration.py`
- [ ] Se connecter avec admin/admin123
- [ ] **CHANGER LE MOT DE PASSE ADMIN**
- [ ] Créer les comptes utilisateurs nécessaires
- [ ] Tester chaque type de compte
- [ ] Vérifier les permissions dans chaque module
- [ ] Former les utilisateurs sur le nouveau système

---

## Avantages du système

### Sécurité
- ✅ Mots de passe hachés (jamais stockés en clair)
- ✅ Contrôle d'accès granulaire
- ✅ Audit des connexions et actions sensibles
- ✅ Possibilité de désactiver rapidement un compte

### Organisation
- ✅ Séparation claire des responsabilités
- ✅ Chaque utilisateur ne voit que ce dont il a besoin
- ✅ Réduction des erreurs de manipulation
- ✅ Traçabilité des actions

### Flexibilité
- ✅ Facile d'ajouter de nouveaux rôles
- ✅ Permissions modulaires et extensibles
- ✅ Interface admin intuitive
- ✅ Documentation complète

---

## Support

Pour toute question ou problème :
1. Consultez la documentation utilisateur ou développeur
2. Vérifiez la section dépannage ci-dessus
3. Contactez l'administrateur système

---

**Version** : 1.0
**Date de création** : 17 décembre 2025
**Statut** : ✅ Prêt pour la production
