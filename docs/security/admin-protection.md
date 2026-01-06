# Protection du dernier administrateur

## Vue d'ensemble

Le système EMAC implémente une protection de sécurité critique pour empêcher la désactivation du dernier administrateur actif. Cette mesure garantit qu'il y aura toujours au moins un administrateur capable de gérer le système.

## Fonctionnement

### Vérification automatique

Lorsqu'un administrateur tente de désactiver un utilisateur, le système effectue les vérifications suivantes :

1. **Identification du rôle** : Vérifie si l'utilisateur à désactiver est un administrateur
2. **Comptage des admins actifs** : Compte le nombre total d'administrateurs actifs dans le système
3. **Blocage si nécessaire** : Si l'utilisateur est le dernier administrateur actif (count ≤ 1), la désactivation est bloquée

### Implémentation technique

#### Backend ([auth_service.py](../../App/core/services/auth_service.py))

**Fonction `count_active_admins()`**
```python
def count_active_admins() -> int:
    """Compte le nombre d'administrateurs actifs dans le système"""
    # Requête SQL qui compte les utilisateurs avec :
    # - role = 'admin'
    # - actif = 1 (True)
```

**Fonction `is_user_admin(user_id)`**
```python
def is_user_admin(user_id: int) -> bool:
    """Vérifie si un utilisateur donné est administrateur"""
    # Récupère le rôle de l'utilisateur et vérifie s'il est 'admin'
```

**Protection dans `update_user_status()`**
```python
def update_user_status(user_id: int, actif: bool) -> tuple[bool, Optional[str]]:
    # Vérification de sécurité : empêcher la désactivation du dernier admin
    if not actif and is_user_admin(user_id):
        active_admins = count_active_admins()
        if active_admins <= 1:
            return False, "Impossible de désactiver le dernier administrateur actif du système"
```

#### Frontend ([user_management.py](../../App/core/gui/user_management.py))

L'interface utilisateur désactive visuellement le bouton "Désactiver" pour le dernier administrateur actif :

```python
# Vérifier si c'est le dernier admin actif
is_last_admin = (user['actif'] and
               user['role_nom'] == 'admin' and
               active_admins_count <= 1)

if is_last_admin:
    # Désactiver le bouton pour le dernier admin
    btn_toggle.setEnabled(False)
    btn_toggle.setToolTip("Impossible de désactiver le dernier administrateur actif")
```

### Affichage visuel

- **Bouton désactivé** : Grisé avec curseur "not-allowed"
- **Info-bulle** : "Impossible de désactiver le dernier administrateur actif"
- **Message d'erreur** : Si l'utilisateur tente quand même la désactivation via une autre méthode

## Scénarios d'utilisation

### Cas 1 : Plusieurs administrateurs actifs
- Statut : ✅ Autorisé
- Comportement : Le bouton "Désactiver" est disponible et fonctionnel
- Résultat : L'administrateur peut être désactivé sans problème

### Cas 2 : Un seul administrateur actif
- Statut : ❌ Bloqué
- Comportement : Le bouton "Désactiver" est grisé et désactivé
- Message : "Impossible de désactiver le dernier administrateur actif"
- Résultat : La désactivation est impossible

### Cas 3 : Administrateur inactif
- Statut : ✅ Autorisé (réactivation)
- Comportement : Le bouton "Activer" est toujours disponible
- Résultat : L'administrateur peut être réactivé

## Bonnes pratiques

1. **Créer plusieurs administrateurs** : Il est recommandé d'avoir au moins 2 administrateurs actifs pour éviter les blocages
2. **Avant de désactiver un admin** : S'assurer qu'il existe au moins un autre administrateur actif
3. **Réactivation prioritaire** : Si besoin de changer d'administrateur, activer le nouveau AVANT de désactiver l'ancien

## Sécurité

Cette protection garantit :
- **Continuité d'accès** : Toujours au moins un administrateur pour gérer le système
- **Protection contre les erreurs** : Impossible de se retrouver sans administrateur par accident
- **Double protection** : Vérification côté serveur ET désactivation visuelle côté client

## Logs et traçabilité

Toutes les tentatives de modification de statut sont enregistrées dans l'historique système :

```
Action: MODIFICATION_UTILISATEUR
Description: Utilisateur activé/désactivé
Table: utilisateurs
```

Les tentatives bloquées ne génèrent pas de log de modification (car refusées en amont).

## Code source

- Service d'authentification : [App/core/services/auth_service.py](../../App/core/services/auth_service.py)
  - `count_active_admins()` : ligne 343-364
  - `is_user_admin()` : ligne 367-388
  - `update_user_status()` : ligne 391-434

- Interface de gestion : [App/core/gui/user_management.py](../../App/core/gui/user_management.py)
  - `load_users()` : ligne 84-151
  - Protection visuelle : ligne 123-135
