# Guide de Gestion des Utilisateurs - EMAC

## Table des matières
1. [Introduction](#introduction)
2. [Installation et Configuration](#installation-et-configuration)
3. [Connexion à l'application](#connexion-à-lapplication)
4. [Les différents rôles](#les-différents-rôles)
5. [Gestion des utilisateurs (Admin)](#gestion-des-utilisateurs-admin)
6. [Changement de mot de passe](#changement-de-mot-de-passe)
7. [Déconnexion](#déconnexion)
8. [Sécurité et bonnes pratiques](#sécurité-et-bonnes-pratiques)

---

## Introduction

Le système de gestion des utilisateurs d'EMAC permet de contrôler l'accès aux différentes fonctionnalités de l'application en fonction du rôle de chaque utilisateur. Ce système garantit que chaque utilisateur n'a accès qu'aux fonctionnalités nécessaires à son travail.

## Installation et Configuration

### Prérequis

- Application EMAC installée
- Base de données MySQL configurée
- Module Python `bcrypt` installé

```bash
pip install bcrypt
```

### Application de la migration

Avant la première utilisation, vous devez appliquer la migration pour créer les tables nécessaires :

```bash
cd App
py scripts/apply_user_management_migration.py
```

Cette commande va :
- Créer les tables `roles`, `utilisateurs`, `permissions`, et `logs_connexion`
- Configurer les 3 rôles par défaut (admin, gestion_production, gestion_rh)
- Créer un compte administrateur par défaut

### Compte administrateur par défaut

**IMPORTANT** : Après l'installation, un compte administrateur est créé avec les identifiants suivants :

- **Nom d'utilisateur** : `admin`
- **Mot de passe** : `admin123`

⚠️ **VOUS DEVEZ CHANGER CE MOT DE PASSE** lors de votre première connexion !

---

## Connexion à l'application

### Écran de connexion

Lors du lancement de l'application, un écran de connexion s'affiche :

1. Entrez votre nom d'utilisateur
2. Entrez votre mot de passe
3. Cliquez sur "Se connecter" ou appuyez sur Entrée

### En cas d'erreur

Si la connexion échoue, vérifiez :
- Que votre nom d'utilisateur est correct (sensible à la casse)
- Que votre mot de passe est correct
- Que votre compte est actif (contactez l'administrateur si nécessaire)

---

## Les différents rôles

### 1. Administrateur (`admin`)

**Accès complet** à toutes les fonctionnalités de l'application.

**Permissions** :
- ✅ Gestion du personnel (lecture, écriture, suppression)
- ✅ Gestion des évaluations (lecture, écriture, suppression)
- ✅ Gestion de la polyvalence (lecture, écriture, suppression)
- ✅ Gestion des contrats (lecture, écriture, suppression)
- ✅ Documents RH (lecture, écriture, suppression)
- ✅ Planning et absences (lecture, écriture, suppression)
- ✅ Gestion des postes (lecture, écriture, suppression)
- ✅ Historique (lecture, écriture, suppression)
- ✅ Grilles de compétences (lecture, écriture, suppression)
- ✅ **Gestion des utilisateurs** (création, modification, désactivation)

**Menu disponible** :
- Ajouter du personnel
- Création/Suppression de poste
- Gestion des Contrats
- Documents RH
- Planning & Évaluations
- Historique
- **Gestion des Utilisateurs** (unique à l'admin)

---

### 2. Gestion Production (`gestion_production`)

Accès aux fonctionnalités de gestion de la production et des évaluations.

**Permissions** :
- ✅ Gestion du personnel (lecture, écriture, suppression)
- ✅ Gestion des évaluations (lecture, écriture, suppression)
- ✅ Gestion de la polyvalence (lecture, écriture, suppression)
-  Gestion des contrats (**LECTURE SEULE** - peut consulter mais pas créer/modifier)
- ❌ Documents RH (pas d'accès)
-  Planning et absences (**LECTURE SEULE** - peut consulter mais pas modifier les absences)
- ✅ Gestion des postes (lecture, écriture, suppression)
-  Historique (lecture seule)
- ✅ Grilles de compétences (lecture, écriture, suppression)
- ❌ Gestion des utilisateurs (pas d'accès)

**Menu disponible** :
- Ajouter du personnel
- Création/Suppression de poste
- Planning & Évaluations (consultation seulement)
- Historique (consultation seulement)

**Restrictions** :
- Ne peut **PAS** créer ou modifier de contrats (lecture seule dans l'onglet Contrats du personnel)
- Ne peut **PAS** gérer les absences dans le planning
- Ne peut **PAS** accéder aux documents RH

---

### 3. Gestion RH (`gestion_rh`)

Accès aux fonctionnalités administratives et de gestion des ressources humaines.

**Permissions** :
-  Gestion du personnel (**LECTURE SEULE** - peut consulter les employés)
- ❌ Gestion des évaluations (pas d'accès)
-  Gestion de la polyvalence (**LECTURE SEULE** - peut consulter mais pas modifier)
- ✅ Gestion des contrats (lecture, écriture, suppression)
- ✅ Documents RH (lecture, écriture, suppression)
- ❌ Planning et absences (pas d'accès)
-  Gestion des postes (lecture seule)
-  Historique (lecture seule)
-  Grilles de compétences (lecture seule)
- ❌ Gestion des utilisateurs (pas d'accès)

**Menu disponible** :
- Gestion des Contrats
- Documents RH
- Historique (consultation seulement)

**Restrictions** :
- Ne peut **PAS** modifier la polyvalence ou les évaluations
- Ne peut **PAS** ajouter ou modifier du personnel (sauf dans le contexte des contrats)
- Ne peut **PAS** créer ou supprimer de postes

---

## Gestion des utilisateurs (Admin)

### Accéder à la gestion des utilisateurs

1. Cliquez sur le bouton menu () en haut à droite
2. Cliquez sur "Gestion des Utilisateurs"

### Créer un nouvel utilisateur

1. Cliquez sur " Nouvel Utilisateur"
2. Remplissez le formulaire :
   - **Nom d'utilisateur** : Identifiant unique (ex: jdupont)
   - **Mot de passe** : Minimum 6 caractères
   - **Confirmer le mot de passe** : Doit être identique
   - **Nom** : Nom de famille de l'utilisateur
   - **Prénom** : Prénom de l'utilisateur
   - **Rôle** : Sélectionnez le rôle approprié
3. Cliquez sur "Créer"

**Bonnes pratiques** :
- Utilisez des noms d'utilisateur faciles à retenir (prénom.nom, initiales+nom, etc.)
- Imposez un mot de passe fort (minimum 8 caractères, mélange de lettres, chiffres, symboles)
- Demandez à l'utilisateur de changer son mot de passe lors de sa première connexion

### Désactiver un utilisateur

Pour désactiver temporairement un utilisateur sans supprimer son compte :

1. Dans la liste des utilisateurs, cliquez sur "Désactiver"
2. Confirmez l'action

L'utilisateur ne pourra plus se connecter mais ses données sont conservées.

### Réactiver un utilisateur

1. Dans la liste, cliquez sur "Activer" pour l'utilisateur désactivé
2. Confirmez l'action

### Changer le mot de passe d'un utilisateur

1. Dans la liste, cliquez sur "Changer MDP"
2. Entrez le nouveau mot de passe (minimum 6 caractères)
3. Confirmez le mot de passe
4. Cliquez sur "Enregistrer"

---

## Changement de mot de passe

### Pour l'administrateur

Un administrateur peut changer n'importe quel mot de passe via l'interface de gestion des utilisateurs.

### Pour les utilisateurs

Actuellement, les utilisateurs non-administrateurs doivent demander à un administrateur de changer leur mot de passe.

**Note** : Une fonctionnalité "Changer mon mot de passe" peut être ajoutée dans une future version.

---

## Déconnexion

Pour se déconnecter de l'application :

1. Cliquez sur le bouton menu ()
2. Cliquez sur " Déconnexion"
3. Confirmez la déconnexion

L'écran de connexion s'affichera à nouveau.

**Important** : Pensez à vous déconnecter :
- À la fin de votre journée de travail
- Si vous quittez temporairement votre poste
- Avant de transmettre votre session à quelqu'un d'autre

---

## Sécurité et bonnes pratiques

### Mots de passe

#### Pour les administrateurs
- **Changez immédiatement** le mot de passe administrateur par défaut (`admin123`)
- Utilisez un mot de passe fort : minimum 12 caractères, mélange de majuscules, minuscules, chiffres et symboles
- Ne partagez **JAMAIS** le mot de passe administrateur
- Changez régulièrement les mots de passe (tous les 3-6 mois)

#### Pour les utilisateurs
- N'utilisez pas de mots de passe évidents (date de naissance, "123456", etc.)
- Ne notez pas vos mots de passe sur papier
- Ne partagez pas votre mot de passe avec vos collègues

### Gestion des comptes

#### Administrateurs
- Créez uniquement les comptes nécessaires
- Désactivez immédiatement les comptes des employés qui quittent l'entreprise
- Vérifiez régulièrement la liste des utilisateurs actifs
- Auditez les logs de connexion en cas de comportement suspect

#### Principe du moindre privilège
- N'accordez que les permissions nécessaires à chaque utilisateur
- Utilisez le rôle `gestion_production` pour la majorité du personnel de production
- Utilisez le rôle `gestion_rh` uniquement pour le personnel RH
- Limitez le nombre d'administrateurs (2-3 maximum recommandés)

### Logs et traçabilité

Toutes les actions sensibles sont enregistrées dans la table `historique` :
- Connexions et déconnexions
- Création de nouveaux utilisateurs
- Changements de mot de passe
- Activation/désactivation de comptes

Un administrateur peut consulter ces logs via l'onglet "Historique".

### Que faire en cas de problème ?

#### Mot de passe oublié
Contactez un administrateur qui pourra réinitialiser votre mot de passe.

#### Compte bloqué
Contactez un administrateur pour vérifier si votre compte a été désactivé.

#### Accès refusé à une fonctionnalité
Vérifiez avec votre administrateur que vous avez le rôle approprié pour cette fonctionnalité.

#### Comportement suspect
Si vous remarquez des connexions suspectes ou des actions non autorisées :
1. Informez immédiatement un administrateur
2. Changez votre mot de passe
3. L'administrateur pourra consulter les logs de connexion

---

## Résumé des permissions par rôle

| Fonctionnalité | Admin | Gestion Production | Gestion RH |
|----------------|-------|-------------------|------------|
| Ajouter/Modifier personnel | ✅ | ✅ |  Lecture |
| Gérer évaluations | ✅ | ✅ | ❌ |
| Gérer polyvalence | ✅ | ✅ |  Lecture |
| Gérer contrats | ✅ |  Lecture | ✅ |
| Documents RH | ✅ | ❌ | ✅ |
| Planning (absences) | ✅ |  Lecture | ❌ |
| Créer/Supprimer postes | ✅ | ✅ |  Lecture |
| Consulter historique | ✅ |  Lecture |  Lecture |
| Grilles de compétences | ✅ | ✅ |  Lecture |
| **Gérer utilisateurs** | ✅ | ❌ | ❌ |

**Légende** :
- ✅ : Accès complet (lecture, écriture, suppression)
-  : Lecture seule (consultation uniquement)
- ❌ : Pas d'accès

---

## Support

Pour toute question concernant la gestion des utilisateurs, contactez votre administrateur système ou l'équipe de développement EMAC.

**Version du document** : 1.0
**Date** : 17 décembre 2025
