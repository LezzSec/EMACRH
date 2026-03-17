# Module de Gestion Documentaire RH

## Vue d'ensemble

Le module de **Gestion Documentaire RH** permet de centraliser et organiser tous les documents administratifs liés aux employés de votre entreprise. Il offre une interface intuitive pour ajouter, visualiser, télécharger et supprimer des documents de manière sécurisée.

---

## Fonctionnalités principales

### ✅ Gestion des documents
- **Ajout de documents** : Téléversement de fichiers (PDF, Word, Excel, images, etc.)
- **Catégorisation** : Classement automatique par catégories (Contrats, Formations, Médical, etc.)
- **Visualisation** : Aperçu et ouverture des documents dans l'application par défaut
- **Téléchargement** : Export des documents vers un emplacement de votre choix
- **Suppression sécurisée** : Confirmation obligatoire avant toute suppression

### Organisation et recherche
- **Filtrage par employé** : Voir tous les documents d'un employé spécifique
- **Filtrage par catégorie** : Afficher uniquement les documents d'une catégorie
- **Filtrage par statut** : Actif, Expiré, Archivé
- **Recherche textuelle** : Recherche rapide par nom de fichier

### ⚠️ Gestion des expirations
- **Alertes automatiques** : Documents expirés affichés en rouge
- **Notifications préventives** : Alertes 30 jours avant expiration
- **Gestion du statut** : Mise à jour automatique du statut (actif/expiré)

### Statistiques
- **Nombre total de documents**
- **Taille totale de stockage**
- **Nombre de documents expirés**

---

## Installation

### Prérequis
- MySQL 8.0+
- Python 3.8+
- PyQt5

### Étapes d'installation

1. **Exécuter le script d'installation**

```bash
cd App/scripts
python install_gestion_documentaire.py
```

Ce script va :
- Créer les tables nécessaires (`categories_documents`, `documents`)
- Insérer les catégories par défaut
- Créer les vues SQL pour les statistiques
- Créer le dossier de stockage `documents/`

2. **Vérifier l'installation**

Lancez l'application EMAC et vérifiez que le menu "Gestion Documentaire RH" est disponible dans le menu latéral.

---

## Structure de la base de données

### Table : `categories_documents`

Contient les catégories de documents disponibles.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INT | Identifiant unique (clé primaire) |
| `nom` | VARCHAR(100) | Nom de la catégorie |
| `description` | TEXT | Description de la catégorie |
| `couleur` | VARCHAR(7) | Code couleur hexadécimal (#RRGGBB) |
| `exige_date_expiration` | BOOLEAN | Si la catégorie nécessite une date d'expiration |
| `ordre_affichage` | INT | Ordre d'affichage dans l'interface |
| `date_creation` | TIMESTAMP | Date de création |
| `date_modification` | TIMESTAMP | Date de dernière modification |

### Table : `documents`

Contient les métadonnées des documents.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INT | Identifiant unique (clé primaire) |
| `operateur_id` | INT | Référence à l'employé (FK → operateurs.id) |
| `categorie_id` | INT | Référence à la catégorie (FK → categories_documents.id) |
| `nom_fichier` | VARCHAR(255) | Nom du fichier original |
| `nom_affichage` | VARCHAR(255) | Nom d'affichage dans l'interface |
| `chemin_fichier` | VARCHAR(500) | Chemin relatif du fichier sur le disque |
| `type_mime` | VARCHAR(100) | Type MIME (application/pdf, image/png, etc.) |
| `taille_octets` | BIGINT | Taille du fichier en octets |
| `date_upload` | TIMESTAMP | Date et heure d'ajout du document |
| `date_expiration` | DATE | Date d'expiration (optionnel) |
| `statut` | ENUM | Statut du document (actif, expire, archive) |
| `notes` | TEXT | Notes et commentaires |
| `uploaded_by` | VARCHAR(100) | Nom de l'utilisateur ayant ajouté le document |
| `date_creation` | TIMESTAMP | Date de création |
| `date_modification` | TIMESTAMP | Date de dernière modification |

### Vues SQL

#### `v_documents_complet`
Vue enrichie avec les informations de l'employé et de la catégorie.

#### `v_documents_stats_operateur`
Statistiques par employé (nombre de documents, taille totale, etc.).

#### `v_documents_expiration_proche`
Documents qui expirent dans les 60 prochains jours.

---

## Organisation des fichiers

Les documents sont stockés physiquement dans le dossier `documents/` avec la structure suivante :

```
documents/
├── operateurs/
│   ├── {matricule_employe_1}/
│   │   ├── contrats/
│   │   │   └── contrat_cdi_2024.pdf
│   │   ├── formations/
│   │   │   └── certificat_securite.pdf
│   │   └── medicaux/
│   │       └── visite_medicale_2024.pdf
│   ├── {matricule_employe_2}/
│   │   └── ...
```

**Avantages de cette organisation :**
- Fichiers organisés par employé et par catégorie
- Facilité de sauvegarde et d'archivage
- Conformité avec les réglementations sur la protection des données (RGPD)

---

## Guide d'utilisation

### Accéder au module

1. Ouvrez l'application EMAC
2. Cliquez sur le bouton **** (menu hamburger) en haut à droite
3. Sélectionnez **"Gestion Documentaire RH"**

### Ajouter un document

1. Sélectionnez un employé dans la liste déroulante
2. Cliquez sur **" Ajouter un document"**
3. Remplissez le formulaire :
   - **Fichier** : Sélectionnez le fichier à ajouter
   - **Catégorie** : Choisissez la catégorie appropriée
   - **Nom d'affichage** : (Optionnel) Nom personnalisé pour l'affichage
   - **Date d'expiration** : (Optionnel) Date de validité du document
   - **Date du document** : (Optionnel) Date du document lui-même
   - **Notes** : (Optionnel) Commentaires sur le document
4. Cliquez sur **"Enregistrer"**

### Visualiser un document

- **Double-clic** sur une ligne du tableau
- Ou cliquez sur le bouton **** dans la colonne "Actions"

Le document s'ouvrira avec l'application par défaut de votre système (ex: Adobe Reader pour les PDF).

### Télécharger un document

- Cliquez sur le bouton **** dans la colonne "Actions"
- Choisissez l'emplacement de sauvegarde
- Le fichier sera copié à l'emplacement choisi

### Supprimer un document

- Cliquez sur le bouton **** dans la colonne "Actions"
- Confirmez la suppression (⚠️ action irréversible)

### Filtrer les documents

- **Par employé** : Sélectionnez un employé dans la liste déroulante
- **Par catégorie** : Utilisez le filtre "Catégorie"
- **Par statut** : Actif, Expiré, Archivé
- **Recherche textuelle** : Saisissez un terme dans le champ "Recherche"

---

## Architecture technique

### Structure des modules

```
App/
├── core/
│   ├── services/
│   │   └── document_service.py      # Service de gestion des documents
│   ├── gui/
│   │   └── gestion_documentaire.py  # Interface PyQt5
│   └── db/
│       └── configbd.py               # Configuration de la BDD
├── database/
│   └── migrations/
│       └── schema_gestion_documentaire.sql  # Migration SQL
├── scripts/
│   └── install_gestion_documentaire.py      # Script d'installation
└── documents/                               # Dossier de stockage
```

### Service Python : `document_service.py`

Le service encapsule toute la logique métier :

```python
class DocumentService:
    def add_document(...)       # Ajouter un document
    def get_documents_operateur(...)  # Récupérer les documents d'un employé
    def get_document_path(...)  # Obtenir le chemin d'un document
    def delete_document(...)    # Supprimer un document
    def archive_document(...)   # Archiver un document
    def get_categories(...)     # Obtenir les catégories
    def update_document_info(...) # Mettre à jour les métadonnées
```

### Interface PyQt5 : `gestion_documentaire.py`

Deux classes principales :

- **`GestionDocumentaireDialog`** : Fenêtre principale de gestion
- **`AddDocumentDialog`** : Fenêtre d'ajout de document

---

## Sécurité et bonnes pratiques

### Protection des données

- **Suppression en cascade** : Si un employé est supprimé, ses documents le sont aussi automatiquement
- **Validation des fichiers** : Extensions et tailles de fichiers contrôlées
- **Chemin relatifs** : Tous les chemins sont relatifs au dossier `documents/`

### Conformité RGPD

- **Droit à l'effacement** : Possibilité de supprimer tous les documents d'un employé
- **Traçabilité** : Chaque action est enregistrée (utilisateur, date)
- **Limitation de conservation** : Gestion des dates d'expiration

### Recommandations

1. **Sauvegardes régulières** : Sauvegardez le dossier `documents/` et la base de données
2. **Permissions** : Restreindre l'accès au dossier `documents/` au niveau du système d'exploitation
3. **Nomenclature** : Utilisez des noms de fichiers clairs et explicites
4. **Vérification** : Vérifiez régulièrement les documents expirés

---

## Catégories par défaut

| Catégorie | Couleur | Expiration obligatoire | Description |
|-----------|---------|------------------------|-------------|
| **Contrats de travail** |  Vert | ✅ Oui | Contrats CDI, CDD, avenants |
| **Certificats médicaux** |  Rouge | ✅ Oui | Visites médicales, aptitudes, RQTH |
| **Diplômes et formations** |  Violet | ❌ Non | Diplômes, certificats, habilitations |
| **Autorisations de travail** |  Orange | ✅ Oui | Titres de séjour, autorisations |
| **Pièces d'identité** |  Cyan | ✅ Oui | CNI, passeport, permis |
| **Attestations diverses** |  Indigo | ❌ Non | Attestations employeur, certificats |
| **Documents administratifs** |  Gris | ❌ Non | Fiches de paie, relevés |
| **Autres** |  Gris clair | ❌ Non | Documents non classés |

---

## Améliorations futures possibles

### Fonctionnalités avancées

1. **Versioning des documents**
   - Conserver l'historique des versions d'un document
   - Restaurer une version antérieure
   - Comparaison entre versions

2. **Signature électronique**
   - Signature numérique des documents importants
   - Validation de signature
   - Traçabilité complète

3. **OCR (Reconnaissance optique de caractères)**
   - Extraction automatique du texte des documents scannés
   - Recherche full-text dans les PDF
   - Indexation automatique

4. **Notifications par email**
   - Alerte automatique 30 jours avant expiration
   - Récapitulatif mensuel des documents expirés
   - Notifications aux responsables RH

5. **Génération automatique de documents**
   - Modèles de contrats pré-remplis
   - Génération de certificats de travail
   - Exports vers Word/PDF

6. **Intégration avec le module d'absences**
   - Joindre automatiquement un certificat médical à une absence
   - Lien entre documents et périodes d'absence

7. **Workflow de validation**
   - Circuit de validation des documents (brouillon → en attente → validé)
   - Validation multi-niveaux (RH, Manager, Direction)
   - Commentaires et historique de validation

8. **Dashboard analytique**
   - Graphiques de répartition des documents
   - Taux de complétude des dossiers employés
   - Indicateurs de conformité

9. **Export et archivage**
   - Export d'un dossier complet d'employé en ZIP
   - Archivage automatique des documents anciens
   - Import/export en masse via CSV

10. **Sécurité renforcée**
    - Chiffrement des fichiers sensibles
    - Journal d'audit détaillé (qui a consulté quel document)
    - Gestion des permissions par rôle utilisateur

### Optimisations techniques

1. **Stockage en base64** (optionnel)
   - Alternative au stockage fichier
   - Documents directement dans la BDD
   - Simplifie les sauvegardes

2. **Compression automatique**
   - Compression des PDF volumineux
   - Optimisation des images
   - Réduction de l'espace disque

3. **API REST**
   - Accès aux documents via API
   - Intégration avec d'autres systèmes
   - Application mobile possible

4. **Mode hors-ligne**
   - Synchronisation des documents en local
   - Travail hors connexion
   - Upload différé

---

## Dépannage

### Problème : "Fichier introuvable sur le disque"

**Cause** : Le fichier a été déplacé ou supprimé manuellement du dossier `documents/`.

**Solution** :
1. Vérifiez l'intégrité du dossier `documents/`
2. Restaurez depuis une sauvegarde si nécessaire
3. Supprimez l'entrée en base de données si le fichier est perdu

### Problème : "Impossible de créer les tables"

**Cause** : Contrainte de clé étrangère non satisfaite (table `operateurs` manquante).

**Solution** :
1. Vérifiez que la table `operateurs` existe
2. Exécutez d'abord le schéma principal de la BDD ([bddemac.sql](../App/database/schema/bddemac.sql))
3. Relancez le script d'installation

### Problème : Les documents expirés ne changent pas automatiquement de statut

**Cause** : Les triggers ne sont pas actifs.

**Solution** :
1. Vérifiez que les triggers existent :
   ```sql
   SHOW TRIGGERS FROM emac_db WHERE `Table` = 'documents';
   ```
2. Re-créez les triggers si nécessaire avec le script d'installation

### Problème : Erreur "Permission denied" lors de l'ajout de document

**Cause** : Permissions insuffisantes sur le dossier `documents/`.

**Solution** :
1. Vérifiez les permissions du dossier :
   ```bash
   ls -la documents/
   ```
2. Accordez les permissions nécessaires :
   ```bash
   chmod -R 755 documents/
   ```

---

## Support

Pour toute question ou problème :

1. Consultez la documentation : [CLAUDE.md](../CLAUDE.md)
2. Vérifiez les logs de l'application : `App/logs/`
3. Consultez l'historique des actions : Menu > Historique

---

## Références

- [Guide d'utilisation des absences](GUIDE_UTILISATION_ABSENCES.md)
- [Module absences - README](MODULE_ABSENCES_README.md)
- [Analyse des fonctionnalités RH manquantes](ANALYSE_FONCTIONNALITES_RH_MANQUANTES.md)
- [Documentation PyQt5](https://doc.qt.io/qtforpython/)
- [MySQL 8.0 Documentation](https://dev.mysql.com/doc/refman/8.0/en/)

---

## Licence

Ce module fait partie de l'application EMAC - Gestion du Personnel.

© 2025 - Tous droits réservés.
