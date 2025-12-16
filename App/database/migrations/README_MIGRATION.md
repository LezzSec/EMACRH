# 📋 GUIDE DE MIGRATION - operateurs → personnel

## 🎯 Objectif
Renommer la table `operateurs` en `personnel` dans la base de données **sans perdre aucune donnée**.

---

## ⚠️ IMPORTANT - Lire avant de commencer

- ✅ Cette migration **NE SUPPRIME AUCUNE DONNÉE**
- ✅ Elle **RENOMME** simplement la table
- ✅ Toutes les données restent intactes
- ⚠️ **MAIS** faites quand même un backup !

---

## 📝 PROCÉDURE COMPLÈTE

### Étape 1️⃣ : BACKUP (OBLIGATOIRE)

```bash
# Windows PowerShell / CMD
cd C:\Users\tlahirigoyen\Desktop\EMAC\App\database\backups

# Créer le backup
mysqldump -u root -p emac_db > backup_avant_migration_%date:~0,4%%date:~5,2%%date:~8,2%.sql

# Vérifier que le fichier existe et n'est pas vide
dir backup_*.sql
```

### Étape 2️⃣ : VÉRIFIER L'ÉTAT ACTUEL

```bash
# Se connecter à MySQL
mysql -u root -p emac_db

# Dans MySQL, vérifier :
SHOW TABLES LIKE 'operateurs';  -- Doit retourner 1 ligne
SHOW TABLES LIKE 'personnel';   -- Doit retourner 0 ligne (vide)
SELECT COUNT(*) FROM operateurs; -- Notez le nombre

# Quitter MySQL
EXIT;
```

### Étape 3️⃣ : APPLIQUER LA MIGRATION (VERSION SÉCURISÉE)

```bash
# Utiliser le script sécurisé avec vérifications
mysql -u root -p emac_db < App/database/migrations/migrate_operateurs_to_personnel_safe.sql
```

**Ce script va :**
1. ✅ Vérifier que `operateurs` existe
2. ✅ Compter les enregistrements (AVANT)
3. ✅ Supprimer les foreign keys
4. ✅ **RENOMMER** `operateurs` → `personnel` (données intactes)
5. ✅ Recréer les foreign keys
6. ✅ Compter les enregistrements (APRÈS)
7. ✅ Afficher un rapport de succès

### Étape 4️⃣ : VÉRIFICATION POST-MIGRATION

```bash
# Se reconnecter à MySQL
mysql -u root -p emac_db

# Vérifier :
SHOW TABLES LIKE 'personnel';    -- Doit retourner 1 ligne
SHOW TABLES LIKE 'operateurs';   -- Doit retourner 0 ligne
SELECT COUNT(*) FROM personnel;  -- Doit avoir le MÊME nombre qu'avant

# Vérifier les foreign keys
SELECT
    TABLE_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'emac_db'
  AND REFERENCED_TABLE_NAME = 'personnel';

-- Doit montrer :
-- historique  | historique_ibfk_1  | personnel
-- polyvalence | polyvalence_ibfk_1 | personnel

EXIT;
```

### Étape 5️⃣ : TESTER L'APPLICATION

```bash
# Lancer EMAC
cd C:\Users\tlahirigoyen\Desktop\EMAC\App
py -m core.gui.main_qt

# Tester :
# ✅ Ouvrir la liste du personnel
# ✅ Ajouter un nouvel employé
# ✅ Modifier une évaluation
# ✅ Consulter l'historique
```

---

## 🚨 EN CAS DE PROBLÈME - ROLLBACK

Si quelque chose ne va pas, vous pouvez **revenir en arrière** :

```bash
# Restaurer depuis le backup
mysql -u root -p emac_db < App/database/backups/backup_avant_migration_XXXXXX.sql

# OU utiliser le script de rollback
mysql -u root -p emac_db < App/database/migrations/rollback_personnel_to_operateurs.sql
```

---

## 📊 CHECKLIST DE MIGRATION

- [ ] Backup créé et vérifié
- [ ] État actuel vérifié (table `operateurs` existe)
- [ ] Migration appliquée avec succès
- [ ] Nombre d'enregistrements identique (avant/après)
- [ ] Foreign keys recréées correctement
- [ ] Application testée et fonctionnelle
- [ ] Backup conservé pendant au moins 1 mois

---

## 🔍 DÉTAILS TECHNIQUES

### Ce qui est modifié :
- Nom de la table : `operateurs` → `personnel`
- Foreign key `historique_ibfk_1` : pointe vers `personnel`
- Foreign key `polyvalence_ibfk_1` : pointe vers `personnel`

### Ce qui N'EST PAS modifié :
- ✅ Toutes les données (0 ligne supprimée)
- ✅ Structure de la table (colonnes identiques)
- ✅ Noms des colonnes (`operateur_id` reste `operateur_id`)
- ✅ Index et contraintes

---

## ❓ FAQ

**Q: Pourquoi le champ s'appelle encore `operateur_id` ?**
R: C'est normal ! Le nom du champ ne change pas, c'est juste la table qui est renommée. `operateur_id` fait référence à `personnel.id`.

**Q: Combien de temps prend la migration ?**
R: Moins de 5 secondes (c'est juste un RENAME, pas de copie de données).

**Q: Est-ce que l'application va planter pendant la migration ?**
R: Oui, arrêtez l'application EMAC avant de migrer. Les queries vont échouer si elles cherchent `operateurs` pendant le RENAME.

**Q: Dois-je modifier mes fichiers Python après ?**
R: Non, tous les fichiers ont déjà été modifiés dans le commit.

---

## 📞 SUPPORT

Si vous rencontrez un problème :
1. Ne paniquez pas !
2. Utilisez le backup pour restaurer
3. Vérifiez les logs MySQL : `SHOW ENGINE INNODB STATUS;`
4. Contactez le support technique

---

**Date de création :** 2025-12-15
**Auteur :** Migration automatique EMAC
**Version :** 1.0.0
