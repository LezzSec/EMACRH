# Guide de Build Sécurisé - EMAC avec .env chiffré

## 🎯 Objectif

Compiler l'application EMAC avec les identifiants de base de données **chiffrés** dans l'exécutable, sans distribuer le fichier `.env` en clair.

## 📋 Prérequis

1. Python 3.x installé
2. Dépendances installées :
   ```bash
   pip install cryptography python-dotenv
   ```

## 🔐 Étape 1 : Générer une clé de chiffrement unique

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
```

Exemple de sortie :
```
b'YourUniqueKeyHere123456789ABCDEF=='
```

**Copiez cette clé** et remplacez-la dans [App/core/utils/config_crypter.py](App/core/utils/config_crypter.py) ligne 14 :

```python
ENCRYPTION_KEY = b'YourUniqueKeyHere123456789ABCDEF=='  # ← Remplacez ici
```

⚠️ **IMPORTANT** : Cette clé est secrète. Ne la commitez jamais dans Git !

## 🔒 Étape 2 : Chiffrer votre fichier .env

```bash
python encrypt_env.py
```

**Ce qui se passe** :
1. Le script lit votre fichier `App/.env`
2. Vous montre le contenu pour confirmation
3. Crée un fichier chiffré `App/.env.encrypted`

Exemple de sortie :
```
================================================================================
EMAC - Chiffrement du fichier .env
================================================================================

📄 Fichier source: App/.env

Contenu du fichier:
--------------------------------------------------------------------------------
EMAC_DB_HOST=localhost
EMAC_DB_USER=root
EMAC_DB_PASSWORD=votre_mot_de_passe
EMAC_DB_NAME=emac_db
--------------------------------------------------------------------------------

⚠️  Confirmer le chiffrement de ce fichier ? (oui/non): oui

🔐 Chiffrement en cours...
✅ Fichier chiffré créé: App/.env.encrypted

================================================================================
✅ CHIFFREMENT TERMINÉ
================================================================================
```

## 📝 Étape 3 : Activer l'inclusion du .env.encrypted dans le build

Éditez [EMAC.spec](EMAC.spec) ligne 205, **décommentez** cette ligne :

```python
DATA_FILES = [
    ('App/config/.env.example', 'config'),

    # Décommentez la ligne suivante ↓
    ('App/.env.encrypted', '.'),  # ✅ ACTIVÉ

    ('App/database/schema/bddemac.sql', 'database/schema'),
]
```

## 🚀 Étape 4 : Compiler l'application

```bash
build_final.bat
```

ou manuellement :

```bash
pyinstaller EMAC.spec
```

## ✅ Résultat

Votre application dans `dist\EMAC\` :
- ✅ `EMAC.exe` - Application compilée
- ✅ `.env.encrypted` - Configuration chiffrée (incluse dans l'exe)
- ❌ **PAS de `.env` en clair**
- ✅ `_internal\` - Dépendances

## 🔍 Comment ça fonctionne ?

1. **Au démarrage de l'exe** :
   - `configbd.py` cherche d'abord `.env.encrypted`
   - Si trouvé, il le déchiffre en mémoire (avec `config_crypter.py`)
   - Charge les variables d'environnement temporairement
   - Se connecte à la base de données
   - **Aucun fichier `.env` en clair n'est jamais créé**

2. **Ordre de recherche** (priorité) :
   - `dist\EMAC\.env.encrypted` (chiffré) ← **PRIORITÉ**
   - `dist\EMAC\.env` (clair, si présent)
   - `%APPDATA%\EMAC\.env.encrypted`
   - `%APPDATA%\EMAC\.env`

## 🛡️ Sécurité

### ✅ Avantages

- ✅ **Pas de .env en clair** dans la distribution
- ✅ **Clé de chiffrement** compilée dans l'exe (difficile à extraire)
- ✅ **Déchiffrement en mémoire** (pas de fichier temporaire persistant)
- ✅ **Configuration cachée** pour l'utilisateur final

### ⚠️ Limitations

- La sécurité repose sur l'obscurité de la clé dans l'exe
- Un attaquant déterminé **peut** extraire la clé de l'exe (désassemblage)
- **BON pour distribution interne**, pas pour des données ultra-sensibles
- Si la clé est compromise, **tous les exes** utilisant cette clé sont vulnérables

### 🔐 Renforcement (optionnel)

Pour une sécurité accrue :

1. **Obfuscation du code** :
   ```bash
   pip install pyarmor
   pyarmor obfuscate App/core/utils/config_crypter.py
   ```

2. **Clé unique par déploiement** :
   - Générez une clé différente pour chaque client
   - Compilez un exe par client

3. **Authentification Windows** (au lieu de .env) :
   - Utilisez l'authentification Windows pour MySQL
   - Pas de mot de passe en clair du tout

## 📦 Distribution

### Fichiers à distribuer

```
EMAC_v1.0.zip
└── EMAC/
    ├── EMAC.exe           ← Exécutable
    ├── _internal/         ← Dépendances (PyQt5, MySQL, etc.)
    ├── README.txt         ← Instructions utilisateur
    └── (autres DLLs)
```

### ❌ Fichiers à NE PAS distribuer

- ❌ `App/.env` (original en clair)
- ❌ `App/core/utils/config_crypter.py` (contient la clé)
- ❌ `encrypt_env.py` (script de chiffrement)

### ✅ Fichiers à garder secrets

- 🔒 `App/.env` (backup sécurisé)
- 🔒 `ENCRYPTION_KEY` (dans config_crypter.py)

## 🔄 Mise à jour des identifiants

Si vous devez changer le mot de passe MySQL :

1. **Modifiez** `App/.env`
2. **Rechiffrez** : `python encrypt_env.py`
3. **Recompilez** : `build_final.bat`
4. **Redistribuez** le nouvel exe

## 🐛 Dépannage

### Problème : "Impossible de déchiffrer"

**Cause** : La clé ne correspond pas

**Solution** :
1. Vérifiez que `ENCRYPTION_KEY` est correct dans `config_crypter.py`
2. Rechiffrez avec `python encrypt_env.py`
3. Recompilez

### Problème : "No module named 'cryptography'"

**Cause** : Module manquant dans l'exe

**Solution** :
1. Vérifiez que `'cryptography'` est dans `HIDDEN_IMPORTS` de EMAC.spec
2. Installez : `pip install cryptography`
3. Recompilez

### Problème : L'application ne se connecte pas à la DB

**Cause** : Le `.env.encrypted` n'est pas inclus dans l'exe

**Solution** :
1. Vérifiez ligne 205 de EMAC.spec : `('App/.env.encrypted', '.'),` doit être décommenté
2. Vérifiez que `App/.env.encrypted` existe
3. Recompilez

## 📊 Mode dev vs Mode production

| Aspect | Mode Dev | Mode Production |
|--------|----------|-----------------|
| Fichier config | `App/.env` (clair) | `App/.env.encrypted` (chiffré) |
| Lancement | `python -m core.gui.main_qt` | `EMAC.exe` |
| Sécurité | Faible (fichier local) | Moyenne (chiffré dans exe) |
| Modification | Facile (éditer .env) | Difficile (rechiffrer + rebuild) |

## 🎓 Alternative : Configuration sans .env

Si vous ne voulez **aucun fichier de configuration** :

**Hardcodez dans configbd.py** (pas recommandé) :

```python
def _get_db_config() -> dict:
    return {
        "host": "prod-server.company.com",
        "port": 3306,
        "user": "emac_user",
        "password": "HardcodedPasswordHere",  # ⚠️ Visible dans l'exe
        "database": "emac_db",
        # ...
    }
```

**Inconvénient** : Changer la config nécessite une recompilation complète.

## 📚 Fichiers créés par ce guide

- ✅ [App/core/utils/config_crypter.py](App/core/utils/config_crypter.py) - Module de chiffrement
- ✅ [encrypt_env.py](encrypt_env.py) - Script de chiffrement
- ✅ [EMAC.spec](EMAC.spec) - Configuration PyInstaller modifiée
- ✅ [App/core/db/configbd.py](App/core/db/configbd.py) - Support .env.encrypted
- ✅ Ce guide

## ✅ Checklist finale

Avant de distribuer :

- [ ] Clé unique générée et copiée dans `config_crypter.py`
- [ ] `App/.env` chiffré avec `encrypt_env.py`
- [ ] `App/.env.encrypted` existe
- [ ] Ligne 205 de EMAC.spec décommentée
- [ ] Application compilée avec `build_final.bat`
- [ ] Application testée sur une autre machine
- [ ] `.env` original en clair **supprimé** du dossier de distribution
- [ ] Archive ZIP créée et testée

## 🚀 Bonne distribution !
