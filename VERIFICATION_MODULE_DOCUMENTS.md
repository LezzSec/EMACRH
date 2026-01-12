# ✅ Liste de vérification - Module de Gestion Documentaire

> **Checklist rapide** pour vérifier que le module fonctionne correctement

---

## 🔍 Test de fonctionnement

Cochez chaque étape au fur et à mesure :

### 1. Installation du module

- [ ] Les tables de base de données existent
  ```bash
  cd App
  py scripts/test_document_upload.py
  ```
  Résultat attendu : ✅ **Tables du module documentaire présentes**

- [ ] Les catégories sont chargées (8 catégories)
  - Contrats de travail
  - Certificats médicaux
  - Diplômes et formations
  - Autorisations de travail
  - Pièces d'identité
  - Attestations diverses
  - Documents administratifs
  - Autres

### 2. Accès à l'interface

- [ ] Le menu "Documents RH" est visible
  - Cliquer sur le menu ☰ (hamburger)
  - Vérifier que "Documents RH" apparaît dans la liste

- [ ] La fenêtre s'ouvre correctement
  - Pas d'erreur au lancement
  - Tous les éléments sont visibles (liste employés, tableau, boutons)

### 3. Upload d'un document

- [ ] Sélection d'un employé fonctionne
  - La liste déroulante affiche les employés actifs
  - Le bouton "➕ Ajouter un document" devient actif

- [ ] Le dialogue d'ajout s'ouvre
  - Tous les champs sont visibles
  - Les catégories se chargent

- [ ] Sélection d'un fichier fonctionne
  - Le bouton "📁 Sélectionner un fichier..." ouvre l'explorateur
  - Le nom du fichier s'affiche en vert après sélection

- [ ] L'enregistrement fonctionne
  - Message de confirmation : "Document ajouté avec succès"
  - Le document apparaît dans le tableau

### 4. Visualisation des documents

- [ ] Le tableau affiche les documents
  - Colonnes visibles : Nom, Catégorie, Taille, Date, Expiration, Statut, Actions
  - Les couleurs de catégorie sont appliquées

- [ ] Les statistiques se mettent à jour
  - Total, Actifs, Expirés, Taille (en Mo)

### 5. Actions sur les documents

- [ ] **Ouvrir** : Double-clic ou bouton 📂
  - Le document s'ouvre avec l'application par défaut

- [ ] **Télécharger** : Bouton 💾
  - La fenêtre "Enregistrer sous" s'ouvre
  - Le fichier est copié à l'emplacement choisi

- [ ] **Supprimer** : Bouton 🗑️
  - Message de confirmation s'affiche
  - Le document est supprimé de la base ET du disque

### 6. Filtres et recherche

- [ ] **Filtre par catégorie** fonctionne
  - Changer la catégorie filtre le tableau

- [ ] **Filtre par statut** fonctionne
  - "Actif", "Expiré", "Archivé" filtrent correctement

- [ ] **Recherche textuelle** fonctionne
  - Taper un mot filtre les résultats en temps réel

### 7. Organisation des fichiers

- [ ] Les fichiers sont bien copiés
  - Vérifier manuellement : `App/documents/operateurs/{matricule}/`

- [ ] L'arborescence est correcte
  - Sous-dossiers par catégorie : `contrats/`, `medicaux/`, etc.

### 8. Gestion des expirations

- [ ] Les documents avec date d'expiration affichent la date

- [ ] Les documents expirés sont colorés en rouge

- [ ] Le filtre "Statut : Expiré" montre uniquement les expirés

---

## 🧪 Test automatisé

**Lancer le script de test complet** :

```bash
cd App
py scripts/test_document_upload.py
```

### Résultat attendu

```
======================================================================
TEST DU MODULE DE GESTION DOCUMENTAIRE - UPLOAD DE FICHIERS
======================================================================

✅ TEST 1: Vérification de l'installation
✅ TEST 2: Récupération des catégories
✅ TEST 3: Création d'un fichier de test
✅ TEST 4: Recherche d'un opérateur actif
✅ TEST 5: Upload du document
✅ TEST 6: Vérification du document
✅ TEST 7: Nettoyage

======================================================================
✅ TOUS LES TESTS ONT RÉUSSI!
======================================================================
```

**Statut** :
- [ ] ✅ Tous les tests ont réussi
- [ ] ❌ Un ou plusieurs tests ont échoué → Voir la section dépannage

---

## ⚠️ Dépannage

### Problème 1 : "Module non installé"

**Symptôme** : Message d'avertissement "Le module n'est pas encore installé"

**Solution** :
```bash
cd App/scripts
py install_gestion_documentaire.py
```

### Problème 2 : "Aucun employé dans la liste"

**Symptôme** : La liste déroulante "Employé" est vide

**Causes possibles** :
1. Aucun employé actif dans la base de données
2. Problème de connexion à la base de données

**Solution** :
```bash
# Vérifier la connexion DB
cd App/scripts
py diagnose_db.py
```

### Problème 3 : "Impossible d'ouvrir le document"

**Symptôme** : Erreur lors de l'ouverture d'un document PDF

**Causes possibles** :
1. Adobe Reader ou équivalent n'est pas installé
2. Aucune application n'est associée à ce type de fichier

**Solution** :
1. Installer Adobe Reader ou un lecteur PDF
2. Ou télécharger le document (💾) et l'ouvrir manuellement

### Problème 4 : "Fichier introuvable"

**Symptôme** : Message "Fichier introuvable sur le disque"

**Causes possibles** :
1. Le fichier a été supprimé manuellement
2. Le dossier `documents/` a été déplacé

**Solution** :
1. Restaurer depuis une sauvegarde
2. Ou supprimer l'entrée en base de données (bouton 🗑️)

### Problème 5 : "Erreur d'encodage" (Windows)

**Symptôme** : Caractères bizarres dans l'interface

**Solution** :
- Redémarrer l'application
- Vérifier que Windows est en UTF-8

---

## 📊 Résultats attendus

### Après upload réussi

**Dans l'interface :**
- ✅ Document visible dans le tableau
- ✅ Statistiques mises à jour
- ✅ Icône de catégorie avec couleur

**Sur le disque :**
- ✅ Fichier copié dans `App/documents/operateurs/{matricule}/{categorie}/`
- ✅ Nom du fichier nettoyé (caractères spéciaux remplacés)

**Dans la base de données :**
- ✅ Entrée dans la table `documents`
- ✅ Métadonnées complètes (nom, catégorie, dates, etc.)

### Organisation attendue

```
App/
└── documents/
    └── operateurs/
        ├── M000001/
        │   ├── contrats/
        │   │   └── CDI_2024.pdf
        │   ├── medicaux/
        │   │   └── visite_medicale_2024.pdf
        │   └── formations/
        │       └── habilitation_electrique.pdf
        ├── M000002/
        │   └── ...
        └── M000003/
            └── ...
```

---

## 📈 Métriques de performance

### Temps de réponse attendus

| Action | Temps attendu | Commentaire |
|--------|---------------|-------------|
| Ouverture de l'interface | < 1 seconde | Chargement de la liste des employés |
| Sélection d'un employé | < 0.5 seconde | Chargement des documents |
| Upload d'un document (1 Mo) | < 2 secondes | Copie + insertion en BDD |
| Ouverture d'un document | < 1 seconde | Dépend de l'application externe |
| Suppression d'un document | < 1 seconde | Suppression fichier + BDD |

### Capacité

- **Nombre de documents par employé** : Illimité (limité par l'espace disque)
- **Taille maximale d'un fichier** : Recommandé < 50 Mo
- **Formats supportés** : Tous (PDF, Word, Excel, images, etc.)

---

## ✅ Validation finale

**Le module est opérationnel si :**

- [x] Tous les tests automatisés passent (script `test_document_upload.py`)
- [x] L'interface s'ouvre sans erreur
- [x] Au moins un document peut être uploadé avec succès
- [x] Le document peut être ouvert, téléchargé et supprimé
- [x] Les filtres fonctionnent correctement

**Si toutes les cases sont cochées : 🎉 Le module est prêt à être utilisé !**

---

## 📞 Support

En cas de problème persistant :

1. Consulter le [guide d'upload](docs/user/guide-upload-documents.md)
2. Lire les [exemples pratiques](docs/user/exemples-upload-documents.md)
3. Vérifier les logs : `App/logs/`
4. Consulter l'historique : Menu > Historique

---

**Dernière mise à jour** : 2026-01-09
**Version** : 1.0
