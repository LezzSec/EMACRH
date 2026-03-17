# Guide de démarrage rapide - EMAC

## Installation et configuration en 3 étapes

### Étape 1 : Configuration de la base de données

**Méthode rapide (Windows)** :
```bash
configure_db.bat
```

**Méthode manuelle** :
```bash
copy .env.example .env
# Éditer .env avec vos paramètres MySQL
```

### Étape 2 : Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### Étape 3 : Lancer l'application

```bash
py -m core.gui.main_qt
```

Ou double-cliquer sur `run_emac.vbs`

---

## Configuration avancée

Pour plus de détails sur la configuration sécurisée, voir :
- [docs/security/database-credentials.md](../../docs/security/database-credentials.md) - Guide complet de configuration MySQL
- [CLAUDE.md](../../CLAUDE.md) - Documentation complète du projet

---

## ⚠️ Dépannage

### Erreur : "Access denied for user 'root'@'localhost'"
- Vérifier le mot de passe dans `.env`
- S'assurer que MySQL est démarré

### Erreur : "No module named 'PyQt5'"
```bash
pip install PyQt5
```

### Erreur : "Unknown database 'emac_db'"
```bash
mysql -u root -p
CREATE DATABASE emac_db;
exit
mysql -u root -p emac_db < database/schema/bddemac.sql
```

---

## Sécurité

Le fichier `.env` contient des informations sensibles (mot de passe) :
- ✅ Il est dans `.gitignore` et ne sera jamais commité
- ✅ Chaque développeur doit créer son propre `.env` local
- ❌ Ne JAMAIS partager le `.env` par email ou chat

---

## Support

Pour des questions ou problèmes, consulter la documentation complète dans [../CLAUDE.md](../CLAUDE.md)
