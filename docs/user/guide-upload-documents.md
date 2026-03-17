# Guide Rapide - Upload de Documents Existants

## Vue d'ensemble

Le module de **Gestion Documentaire RH** vous permet d'importer et de centraliser tous les documents administratifs de vos employés (certificats médicaux, diplômes, pièces d'identité, etc.).

---

## Comment uploader un document existant

### Étape 1 : Accéder au module

1. Ouvrez l'application EMAC
2. Cliquez sur le bouton **** (menu hamburger) en haut à droite
3. Sélectionnez **"Documents RH"**

![Accès au module](../assets/screenshots/menu-documents.png)

---

### Étape 2 : Sélectionner un employé

Dans la fenêtre "Gestion Documentaire RH" :

1. Utilisez la liste déroulante **"Employé"** en haut de la fenêtre
2. Sélectionnez l'employé pour lequel vous souhaitez ajouter un document
3. Le bouton **" Ajouter un document"** devient actif

---

### Étape 3 : Ajouter le document

1. Cliquez sur **" Ajouter un document"**
2. Une nouvelle fenêtre s'ouvre : **"Ajouter un document"**

#### 3.1 Sélectionner le fichier

1. Cliquez sur **" Sélectionner un fichier..."**
2. Parcourez votre ordinateur et sélectionnez le document à importer
3. **Formats acceptés** : PDF, Word (.doc, .docx), Excel, images (PNG, JPG), etc.
4. Le nom du fichier s'affiche en vert une fois sélectionné

> **Note** : Le fichier sera **copié** dans le dossier de l'application. Le fichier original reste intact sur votre ordinateur.

#### 3.2 Renseigner les informations

| Champ | Obligatoire | Description |
|-------|------------|-------------|
| **Catégorie** | ✅ Oui | Type de document (Certificats médicaux, Diplômes, etc.) |
| **Nom d'affichage** | ❌ Non | Nom personnalisé pour identifier facilement le document |
| **Date d'expiration** | ❌ Non | Date de validité du document (ex: visite médicale) |
| **Date du document** | ❌ Non | Date de création du document lui-même |
| **Description / Notes** | ❌ Non | Commentaires ou informations supplémentaires |

#### 3.3 Enregistrer

1. Vérifiez que toutes les informations sont correctes
2. Cliquez sur **"Enregistrer"**
3. Le document est copié et enregistré dans la base de données
4. Un message de confirmation s'affiche

---

## Visualiser les documents

### Tableau des documents

Une fois qu'un employé est sélectionné, tous ses documents s'affichent dans le tableau :

| Colonne | Description |
|---------|-------------|
| **Nom du document** | Nom d'affichage ou nom du fichier |
| **Catégorie** | Type de document (avec code couleur) |
| **Taille** | Taille du fichier (Ko ou Mo) |
| **Date ajout** | Date d'importation dans EMAC |
| **Expiration** | Date de validité (si applicable) |
| **Statut** | Actif, Expiré, Archivé |
| **Actions** | Boutons d'action rapide |

### Codes couleur des statuts

-  **Actif** : Document valide et à jour
-  **Expiré** : Document dont la date d'expiration est dépassée
-  **Expire bientôt** : Document qui expire dans les 30 jours

---

## Actions sur les documents

### Ouvrir un document

**3 façons d'ouvrir un document** :

1. **Double-clic** sur une ligne du tableau
2. Cliquer sur le bouton **** dans la colonne "Actions"
3. Clic droit → **" Ouvrir"**

Le document s'ouvrira avec l'application par défaut de votre ordinateur (ex: Adobe Reader pour les PDF).

### Télécharger (exporter) un document

1. Cliquez sur le bouton **** dans la colonne "Actions"
2. Choisissez l'emplacement de sauvegarde
3. Le fichier est copié à l'emplacement choisi

> **Astuce** : Utilisez cette fonction pour exporter des documents vers une clé USB ou un email.

### Supprimer un document

1. Cliquez sur le bouton **** dans la colonne "Actions"
2. Confirmez la suppression

> ⚠️ **Attention** : La suppression est **irréversible**. Le fichier sera supprimé de la base de données ET du disque.

---

## Filtrer les documents

Le module offre plusieurs options de filtrage pour retrouver rapidement un document :

### Filtres disponibles

1. **Par employé** : Sélectionnez un employé dans la liste déroulante
2. **Par catégorie** : Filtrez par type de document (Médical, Formations, etc.)
3. **Par statut** : Actif, Expiré, Archivé
4. **Recherche textuelle** : Saisissez un terme dans le champ "Recherche"

### Exemple d'utilisation

**Objectif** : Trouver tous les certificats médicaux expirés

1. Catégorie : **"Certificats médicaux"**
2. Statut : **"Expiré"**
3. Employé : **"Tous les employés"**

---

## Statistiques

En haut de la fenêtre, 4 indicateurs affichent les statistiques de l'employé sélectionné :

| Indicateur | Description |
|------------|-------------|
| **Total** | Nombre total de documents |
| **Actifs** | Documents valides (en vert) |
| **Expirés** | Documents dont la date d'expiration est dépassée (en rouge) |
| **Taille** | Espace disque utilisé (en Mo) |

---

## Conseils et bonnes pratiques

### Organisation des fichiers

- **Nommez clairement vos fichiers** : Utilisez le champ "Nom d'affichage" pour donner des noms explicites
- **Renseignez les dates d'expiration** : Cela permet de recevoir des alertes automatiques
- **Ajoutez des notes** : Utilisez le champ "Description / Notes" pour contextualiser le document

### Gestion des expirations

- **Vérifiez régulièrement** les documents expirés (filtre "Statut : Expiré")
- **Anticipez les renouvellements** : Les documents qui expirent dans les 30 jours sont mis en évidence
- **Utilisez le Dashboard** : Le module affiche automatiquement les alertes d'expiration

### Sécurité et conformité

- **RGPD** : Seuls les utilisateurs autorisés peuvent accéder aux documents
- **Traçabilité** : Chaque action est enregistrée dans l'historique
- **Sauvegardes** : Pensez à sauvegarder régulièrement le dossier `documents/`

---

## Dépannage

### Problème : "Fichier introuvable sur le disque"

**Cause** : Le fichier a été déplacé ou supprimé manuellement.

**Solution** :
1. Restaurez le fichier depuis une sauvegarde
2. Ou supprimez l'entrée en base de données (bouton )

### Problème : "Impossible d'ouvrir le document"

**Cause** : Aucune application n'est associée à ce type de fichier.

**Solution** :
1. Installez l'application appropriée (ex: Adobe Reader pour les PDF)
2. Ou téléchargez le document () et ouvrez-le manuellement

### Problème : "Module non installé"

**Cause** : Les tables de la base de données n'existent pas.

**Solution** :
```bash
cd App/scripts
python install_gestion_documentaire.py
```

---

## Aide et support

Pour plus d'informations :

- **Documentation complète** : [Module de gestion documentaire](../features/module-documents.md)
- **Support technique** : Consultez l'historique (Menu > Historique)
- **Logs de l'application** : `App/logs/`

---

## ✅ Récapitulatif rapide

1. **Ouvrir** : Menu  → "Documents RH"
2. **Sélectionner** : Choisir un employé dans la liste
3. **Ajouter** : Cliquer sur " Ajouter un document"
4. **Importer** : Parcourir et sélectionner le fichier existant
5. **Renseigner** : Catégorie, nom, dates (optionnel)
6. **Enregistrer** : Cliquer sur "Enregistrer"
7. **Consulter** : Double-clic pour ouvrir le document

---

**Dernière mise à jour** : 2026-01-09
**Version du module** : 1.0
