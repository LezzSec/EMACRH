# Configuration EMAC

Ce dossier contient l'exemple de configuration et le script d'aide Windows pour créer le fichier `App/.env`.

## Configuration rapide

Depuis `App/config/` :

```bash
configure_db.bat
```

Ou manuellement :

```bash
copy .env.example ..\.env
```

Puis éditer `App/.env`.

## Variables principales

```env
EMAC_DB_HOST=127.0.0.1
EMAC_DB_PORT=3306
EMAC_DB_USER=gestionrh
EMAC_DB_PASSWORD=votre_mot_de_passe
EMAC_DB_NAME=emac_db
EMAC_DB_POOL_SIZE=10
```

Compatibilité : le code accepte aussi certains anciens noms `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME`, mais les variables `EMAC_*` sont à privilégier.

## Variables optionnelles

Distance domicile / entreprise :

```env
EMAC_COMPANY_INSEE=00000
EMAC_COMPANY_COMMUNE=Votre commune
EMAC_COMPANY_LAT=00.0000
EMAC_COMPANY_LON=0.0000
EMAC_COMPANY_MAIRIE_LAT=00.0000
EMAC_COMPANY_MAIRIE_LON=0.0000
OPENROUTESERVICE_API_KEY=
```

Sécurité mot de passe :

```env
EMAC_BCRYPT_COST=12
```

La plage recommandée est `10` à `15`. La valeur par défaut du code est `12`.

## Lancement après configuration

Depuis `App/` :

```bash
py -m gui.main_qt
```

## Sécurité

- `App/.env` contient des secrets et ne doit pas être commité.
- `App/.env.encrypted` est prévu pour la distribution, mais ne remplace pas la gestion prudente des clés.
- Le mot de passe DB est obligatoire : l'application échoue explicitement si `EMAC_DB_PASSWORD` est vide.
- Ne pas partager `.env` par mail, chat ou dépôt Git.

## Dépannage

### `Configuration DB manquante : EMAC_DB_PASSWORD est vide`

Créer ou compléter `App/.env`, ou définir la variable d'environnement `EMAC_DB_PASSWORD`.

### `Access denied for user`

Vérifier `EMAC_DB_HOST`, `EMAC_DB_USER`, `EMAC_DB_PASSWORD`, les droits MySQL et l'accès au port `3306`.

### `Unknown database 'emac_db'`

Créer la base puis appliquer le schéma/migrations :

```sql
CREATE DATABASE emac_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

```bash
cd App
python -m cli migrate --status
python -m cli migrate --apply-all
```

### `No module named 'PyQt5'`

```bash
cd App
pip install -r requirements.txt
```
