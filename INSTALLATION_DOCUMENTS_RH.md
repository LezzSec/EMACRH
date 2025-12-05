# Installation du Module Documents RH

## ⚠️ Prérequis

Avant d'utiliser le module "Documents RH", vous devez l'installer.

## 🚀 Installation en 1 commande

```bash
cd App\scripts
python install_gestion_documentaire.py
```

Le script va :
- ✅ Créer les tables `categories_documents` et `documents`
- ✅ Insérer 8 catégories par défaut
- ✅ Créer les vues SQL
- ✅ Créer le dossier de stockage `documents/`

## ✅ Vérification

Relancez l'application :

```bash
cd App
python -m core.gui.main_qt
```

Menu ☰ → **Documents RH**

L'interface devrait s'afficher sans erreur.

## 🐛 En cas de problème

### Erreur "Table operateurs doesn't exist"

Exécutez :
```bash
cd App\scripts
python fix_documents_foreign_key.py
```

### Erreur lors de l'ajout de document

Vérifiez que l'installation s'est bien déroulée :
```sql
USE emac_db;
SHOW TABLES LIKE 'categories_documents';
SHOW TABLES LIKE 'documents';
```

Si les tables n'existent pas, relancez le script d'installation.

## 📚 Documentation complète

Consultez [docs/GESTION_DOCUMENTAIRE_RH.md](docs/GESTION_DOCUMENTAIRE_RH.md) pour plus d'informations.
