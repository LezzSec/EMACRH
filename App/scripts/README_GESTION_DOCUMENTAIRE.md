# Installation du Module de Gestion Documentaire RH

## 📋 Prérequis

- MySQL 8.0+ avec la base de données `emac_db`
- Python 3.8+
- PyQt5 installé
- **Table `personnel` existante** dans la base de données

---

## 🚀 Installation

### Étape 1 : Installer les tables et données initiales

```bash
cd App/scripts
python install_gestion_documentaire.py
```

Ce script va créer :
- Tables : `categories_documents`, `documents`
- 8 catégories de documents par défaut
- Vues SQL : `v_documents_complet`, `v_documents_stats_operateur`, `v_documents_expiration_proche`
- Dossier de stockage : `documents/`

### Étape 2 : Corriger la clé étrangère (si nécessaire)

Si vous avez une erreur indiquant que la table `operateurs` n'existe pas :

```bash
python fix_documents_foreign_key.py
```

Ce script va :
- Vérifier la contrainte de clé étrangère existante
- Supprimer l'ancienne contrainte pointant vers `operateurs`
- Créer une nouvelle contrainte pointant vers `personnel`

---

## ✅ Vérification de l'installation

### 1. Vérifier les tables

Connectez-vous à MySQL et exécutez :

```sql
USE emac_db;

-- Vérifier que les tables existent
SHOW TABLES LIKE 'categories_documents';
SHOW TABLES LIKE 'documents';

-- Vérifier les catégories
SELECT * FROM categories_documents;

-- Vérifier la contrainte de clé étrangère
SELECT
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'emac_db'
AND TABLE_NAME = 'documents'
AND REFERENCED_TABLE_NAME IS NOT NULL;
```

Résultat attendu :
- La contrainte `fk_documents_personnel` doit pointer vers `personnel(id)`

### 2. Vérifier le dossier de stockage

Vérifiez que le dossier `documents/` a été créé :

```bash
ls -la documents/
```

ou sous Windows :

```cmd
dir documents\
```

### 3. Lancer l'interface de test

```bash
cd App
python -m core.gui.gestion_documentaire
```

Une fenêtre devrait s'ouvrir avec :
- Liste déroulante des employés
- Tableau vide des documents
- Bouton "Ajouter un document"
- Filtres par catégorie et statut

---

## 🎯 Utilisation

### Accès depuis l'application principale

1. Lancez l'application EMAC :
   ```bash
   cd App
   python -m core.gui.main_qt
   ```

2. Cliquez sur le menu hamburger (☰) en haut à droite

3. Sélectionnez **"Gestion Documentaire RH"**

### Ajouter un document

1. Sélectionnez un employé dans la liste
2. Cliquez sur "➕ Ajouter un document"
3. Choisissez un fichier
4. Remplissez les informations (catégorie, dates, notes)
5. Cliquez sur "Enregistrer"

Le fichier sera copié dans : `documents/operateurs/{id_employe}/{categorie}/`

---

## 🐛 Dépannage

### Erreur : "Table 'emac_db.operateurs' doesn't exist"

**Cause** : Le script d'installation utilisait la table `operateurs` au lieu de `personnel`.

**Solution** :
```bash
python fix_documents_foreign_key.py
```

### Erreur : "Cannot add foreign key constraint"

**Cause** : Des documents existent déjà avec des `operateur_id` invalides.

**Solution** :
```sql
-- Supprimer les documents orphelins
DELETE FROM documents
WHERE operateur_id NOT IN (SELECT id FROM personnel);

-- Réexécuter le script
```

### Erreur : "Permission denied" lors de l'ajout de fichier

**Cause** : Permissions insuffisantes sur le dossier `documents/`.

**Solution** :
```bash
# Linux/Mac
chmod -R 755 documents/

# Windows : Vérifier les permissions du dossier dans l'explorateur
```

### L'interface ne s'affiche pas

**Cause** : Problème avec PyQt5 ou les imports.

**Solution** :
```bash
# Vérifier que PyQt5 est installé
pip list | grep PyQt5

# Réinstaller si nécessaire
pip install --upgrade PyQt5
```

---

## 📊 Structure de la base de données

### Table : `categories_documents`

| Colonne | Type | Description |
|---------|------|-------------|
| id | INT | Clé primaire |
| nom | VARCHAR(100) | Nom de la catégorie |
| description | TEXT | Description |
| couleur | VARCHAR(7) | Couleur (#hexcode) |
| exige_date_expiration | BOOLEAN | Si une date d'expiration est requise |
| ordre_affichage | INT | Ordre d'affichage |

### Table : `documents`

| Colonne | Type | Description |
|---------|------|-------------|
| id | INT | Clé primaire |
| operateur_id | INT | FK → personnel(id) |
| categorie_id | INT | FK → categories_documents(id) |
| nom_fichier | VARCHAR(255) | Nom du fichier original |
| nom_affichage | VARCHAR(255) | Nom affiché dans l'interface |
| chemin_fichier | VARCHAR(500) | Chemin relatif du fichier |
| type_mime | VARCHAR(100) | Type MIME |
| taille_octets | BIGINT | Taille en octets |
| date_upload | TIMESTAMP | Date d'ajout |
| date_expiration | DATE | Date d'expiration (optionnel) |
| statut | ENUM | actif, expire, archive |
| notes | TEXT | Notes |
| uploaded_by | VARCHAR(100) | Utilisateur |

---

## 📁 Organisation des fichiers

```
documents/
├── operateurs/
│   ├── 1/
│   │   ├── contrats/
│   │   ├── formations/
│   │   ├── medicaux/
│   │   └── ...
│   ├── 2/
│   │   └── ...
```

---

## 🔐 Sécurité

### Sauvegardes

Il est recommandé de sauvegarder régulièrement :

1. **La base de données** :
   ```bash
   mysqldump -u root -p emac_db > backup_emac_$(date +%Y%m%d).sql
   ```

2. **Le dossier documents/** :
   ```bash
   # Linux/Mac
   tar -czf backup_documents_$(date +%Y%m%d).tar.gz documents/

   # Windows
   7z a backup_documents_%date%.zip documents\
   ```

### Permissions recommandées

- Dossier `documents/` : 755 (rwxr-xr-x)
- Fichiers dans `documents/` : 644 (rw-r--r--)

### Conformité RGPD

Le système respecte les principes RGPD :
- ✅ Droit à l'effacement (suppression en cascade)
- ✅ Limitation de conservation (dates d'expiration)
- ✅ Traçabilité (logs d'accès)
- ✅ Sécurité (contrôle d'accès)

---

## 📚 Documentation complète

Consultez la documentation détaillée : [docs/GESTION_DOCUMENTAIRE_RH.md](../../docs/GESTION_DOCUMENTAIRE_RH.md)

---

## 💡 Aide et support

En cas de problème :

1. Vérifiez les logs de l'application : `App/logs/`
2. Consultez l'historique : Menu > Historique
3. Vérifiez les permissions du dossier `documents/`
4. Relancez les scripts d'installation si nécessaire

---

## 🎉 Installation terminée !

Votre système de gestion documentaire RH est maintenant opérationnel.

Pour accéder au module :
- Lancez l'application EMAC
- Menu ☰ → "Gestion Documentaire RH"
