# Système d'Authentification et de Permissions - EMAC

## Architecture technique

### Vue d'ensemble

Le système d'authentification d'EMAC est basé sur :
- **Hachage bcrypt** pour les mots de passe
- **Système de rôles et permissions** pour le contrôle d'accès
- **Session singleton** pour stocker l'utilisateur connecté
- **Logs de connexion** pour l'audit

### Structure de la base de données

#### Table `roles`
```sql
CREATE TABLE roles (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nom VARCHAR(50) NOT NULL UNIQUE,
  description TEXT
);
```

3 rôles prédéfinis :
- `admin` : Administrateur système
- `gestion_production` : Gestion de la production
- `gestion_rh` : Gestion des ressources humaines

#### Table `utilisateurs`
```sql
CREATE TABLE utilisateurs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  nom VARCHAR(255) NOT NULL,
  prenom VARCHAR(255) NOT NULL,
  role_id INT NOT NULL,
  actif TINYINT(1) DEFAULT 1,
  date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
  derniere_connexion DATETIME DEFAULT NULL,
  FOREIGN KEY (role_id) REFERENCES roles(id)
);
```

#### Table `permissions`
```sql
CREATE TABLE permissions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  role_id INT NOT NULL,
  module VARCHAR(100) NOT NULL,
  lecture TINYINT(1) DEFAULT 1,
  ecriture TINYINT(1) DEFAULT 0,
  suppression TINYINT(1) DEFAULT 0,
  FOREIGN KEY (role_id) REFERENCES roles(id)
);
```

Modules disponibles :
- `personnel`, `evaluations`, `polyvalence`, `contrats`, `documents_rh`
- `planning`, `postes`, `historique`, `grilles`, `gestion_utilisateurs`

#### Table `logs_connexion`
```sql
CREATE TABLE logs_connexion (
  id INT PRIMARY KEY AUTO_INCREMENT,
  utilisateur_id INT NOT NULL,
  date_connexion DATETIME NOT NULL,
  date_deconnexion DATETIME DEFAULT NULL,
  ip_address VARCHAR(45) DEFAULT NULL,
  FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
);
```

---

## Services

### `auth_service.py`

Service principal pour l'authentification et la gestion des utilisateurs.

#### Classes

##### `UserSession` (Singleton)
Stocke les informations de session de l'utilisateur connecté.

```python
from core.services.auth_service import UserSession

# Obtenir l'utilisateur connecté
session = UserSession()
user = session.get_user()

# Vérifier si authentifié
if session.is_authenticated():
    print(f"Utilisateur: {user['username']}")
```

#### Fonctions principales

##### `authenticate_user(username: str, password: str) -> tuple[bool, Optional[str]]`
Authentifie un utilisateur.

```python
from core.services.auth_service import authenticate_user

success, error = authenticate_user("admin", "admin123")
if success:
    print("Connexion réussie")
else:
    print(f"Erreur: {error}")
```

##### `logout_user()`
Déconnecte l'utilisateur actuel.

```python
from core.services.auth_service import logout_user

logout_user()
```

##### `has_permission(module: str, action: str = 'lecture') -> bool`
Vérifie si l'utilisateur a une permission.

```python
from core.services.auth_service import has_permission

if has_permission('contrats', 'ecriture'):
    # Afficher le formulaire de création de contrat
    pass
else:
    # Afficher un message d'erreur
    pass
```

##### `is_admin() -> bool`
Vérifie si l'utilisateur est administrateur.

```python
from core.services.auth_service import is_admin

if is_admin():
    # Afficher le bouton de gestion des utilisateurs
    pass
```

##### `create_user(username, password, nom, prenom, role_id) -> tuple[bool, Optional[str]]`
Crée un nouvel utilisateur (admin uniquement).

```python
from core.services.auth_service import create_user

success, error = create_user(
    "jdupont",
    "motdepasse123",
    "Dupont",
    "Jean",
    2  # role_id pour gestion_production
)
```

##### `change_password(user_id: int, new_password: str) -> tuple[bool, Optional[str]]`
Change le mot de passe d'un utilisateur.

```python
from core.services.auth_service import change_password

success, error = change_password(5, "nouveau_mot_de_passe")
```

---

## Interfaces graphiques

### `login_dialog.py`

Dialogue de connexion affiché au lancement de l'application.

**Utilisation dans main_qt.py** :
```python
from core.gui.login_dialog import LoginDialog

login_dialog = LoginDialog()
if login_dialog.exec_() == LoginDialog.Accepted:
    # Connexion réussie, afficher la fenêtre principale
    win = MainWindow()
    win.show()
```

### `user_management.py`

Interface de gestion des utilisateurs (admin uniquement).

**Classes** :
- `UserManagementDialog` : Liste des utilisateurs avec actions
- `AddUserDialog` : Formulaire de création d'utilisateur
- `ChangePasswordDialog` : Formulaire de changement de mot de passe

**Utilisation** :
```python
from core.gui.user_management import UserManagementDialog

dialog = UserManagementDialog(parent=self)
dialog.exec_()
```

---

## Contrôle d'accès dans les interfaces

### Méthode 1 : Vérification manuelle

```python
from core.services.auth_service import has_permission
from PyQt5.QtWidgets import QMessageBox

def create_contract(self):
    if not has_permission('contrats', 'ecriture'):
        QMessageBox.warning(
            self,
            "Accès refusé",
            "Vous n'avez pas les permissions pour créer un contrat."
        )
        return

    # Code pour créer le contrat
    ...
```

### Méthode 2 : Helper de permissions

Utiliser `permission_helper.py` :

```python
from core.utils.permission_helper import (
    set_widget_permission,
    set_readonly_if_no_permission
)

# Désactiver un bouton si pas de permission
set_widget_permission(
    self.btn_create_contract,
    module='contrats',
    action='ecriture'
)

# Rendre un champ en lecture seule
set_readonly_if_no_permission(
    self.contract_type_input,
    module='contrats'
)
```

### Méthode 3 : Masquer des éléments du menu

Dans `main_qt.py`, le menu drawer utilise `has_permission` :

```python
if has_permission('contrats', 'lecture'):
    self.add_drawer_button(
        drawer_layout,
        "Gestion des Contrats",
        self.show_contract_management,
        'ghost'
    )
```

---

## Sécurité

### Hachage des mots de passe

Les mots de passe sont hachés avec **bcrypt** (facteur de coût : 12).

```python
import bcrypt

# Hacher un mot de passe
salt = bcrypt.gensalt()
password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

# Vérifier un mot de passe
is_valid = bcrypt.checkpw(password.encode('utf-8'), password_hash)
```

### Bonnes pratiques

1. **Ne jamais stocker de mots de passe en clair**
2. **Toujours utiliser `has_permission()` avant une action sensible**
3. **Logger toutes les actions importantes** avec `log_hist()`
4. **Valider les entrées utilisateur** (longueur minimale du mot de passe, etc.)
5. **Limiter le nombre de tentatives de connexion** (à implémenter si nécessaire)

---

## Logs et audit

Toutes les actions de connexion/déconnexion et de gestion des utilisateurs sont enregistrées dans :
- **Table `logs_connexion`** : Connexions et déconnexions avec timestamps
- **Table `historique`** : Actions importantes (création d'utilisateur, changement de mot de passe, etc.)

### Consulter les logs

```python
from core.db.configbd import get_connection

conn = get_connection()
cur = conn.cursor(dictionary=True)

# Logs de connexion
cur.execute("""
    SELECT u.username, lc.date_connexion, lc.date_deconnexion
    FROM logs_connexion lc
    JOIN utilisateurs u ON lc.utilisateur_id = u.id
    ORDER BY lc.date_connexion DESC
    LIMIT 50
""")

for log in cur.fetchall():
    print(f"{log['username']} - {log['date_connexion']}")
```

---

## Migration et installation

### Appliquer la migration

```bash
cd App
py scripts/apply_user_management_migration.py
```

### Compte par défaut

Après la migration, un compte admin est créé :
- **Username** : `admin`
- **Password** : `admin123`

⚠️ **IMPORTANT** : Changez ce mot de passe immédiatement en production !

---

## Extension du système

### Ajouter un nouveau rôle

1. Insérer dans la table `roles` :
```sql
INSERT INTO roles (nom, description) VALUES
('nouveau_role', 'Description du nouveau rôle');
```

2. Configurer les permissions :
```sql
INSERT INTO permissions (role_id, module, lecture, ecriture, suppression)
SELECT id, 'personnel', 1, 0, 0 FROM roles WHERE nom = 'nouveau_role';
```

### Ajouter un nouveau module

1. Ajouter les permissions pour chaque rôle :
```sql
INSERT INTO permissions (role_id, module, lecture, ecriture, suppression) VALUES
(1, 'nouveau_module', 1, 1, 1),  -- admin
(2, 'nouveau_module', 1, 1, 0),  -- gestion_production
(3, 'nouveau_module', 0, 0, 0);  -- gestion_rh
```

2. Utiliser `has_permission('nouveau_module', 'ecriture')` dans le code

---

## Tests

### Tester l'authentification

```python
# Test de connexion valide
success, error = authenticate_user("admin", "admin123")
assert success == True

# Test de connexion invalide
success, error = authenticate_user("admin", "wrong_password")
assert success == False
assert "incorrect" in error.lower()
```

### Tester les permissions

```python
# Connecter un utilisateur gestion_production
authenticate_user("user_prod", "password")

# Vérifier les permissions
assert has_permission('personnel', 'ecriture') == True
assert has_permission('contrats', 'ecriture') == False  # Lecture seule
assert has_permission('documents_rh', 'lecture') == False  # Pas d'accès
```

---

## Dépannage

### Problème : "Module bcrypt introuvable"
```bash
pip install bcrypt
```

### Problème : "Table utilisateurs n'existe pas"
Appliquer la migration :
```bash
py scripts/apply_user_management_migration.py
```

### Problème : "Mot de passe oublié pour admin"
Se connecter directement à MySQL et réinitialiser :
```sql
UPDATE utilisateurs
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5yrOvnN6G/mFa'
WHERE username = 'admin';
-- Nouveau mot de passe : admin123
```

### Problème : "Tous les utilisateurs sont désactivés"
```sql
UPDATE utilisateurs SET actif = 1 WHERE username = 'admin';
```

---

## Diagramme de flux

```
┌─────────────────┐
│   Lancement     │
│   Application   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LoginDialog    │ ────── authenticate_user()
└────────┬────────┘
         │ success
         ▼
┌─────────────────┐
│  UserSession    │ ◄───── get_current_user()
│  (Singleton)    │ ◄───── has_permission()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MainWindow     │
│   + Drawer      │ ────── Boutons filtrés par permissions
└────────┬────────┘
         │
         ├─── Gestion Personnel (si permission personnel)
         ├─── Gestion Contrats (si permission contrats)
         ├─── Documents RH (si permission documents_rh)
         └─── Gestion Users (si is_admin())
```

---

## Références

- **BCrypt** : [https://pypi.org/project/bcrypt/](https://pypi.org/project/bcrypt/)
- **PyQt5** : [https://www.riverbankcomputing.com/static/Docs/PyQt5/](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- **MySQL Connector** : [https://dev.mysql.com/doc/connector-python/en/](https://dev.mysql.com/doc/connector-python/en/)

---

**Version** : 1.0
**Date** : 17 décembre 2025
**Auteur** : Équipe de développement EMAC
