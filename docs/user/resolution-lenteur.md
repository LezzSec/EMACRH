# Résolution des problèmes de lenteur EMAC

## 🐌 Symptômes

- **Démarrage très lent** : 30 secondes à plusieurs minutes
- **Freezes pendant la saisie** : L'interface se bloque pendant que vous tapez
- **Écran de connexion qui lag** : Délai entre la frappe et l'affichage

---

## 🔍 Diagnostic : D'où vient la lenteur ?

### Cause #1 : Lancement depuis le réseau (99% des cas)

**Symptôme** :
- Temps de démarrage > 1 minute
- Freeze au lancement de 10-30 secondes

**Vérification** :
```
Regardez le chemin de l'exe :
- ❌ \\serveur\partage\EMAC\EMAC.exe → LENT (réseau)
- ✅ C:\Users\...\AppData\Local\EMAC_Cache\EMAC.exe → RAPIDE (local)
```

**Solution** : Utilisez **OBLIGATOIREMENT** le lanceur `Lancer_EMAC.bat`

---

### Cause #2 : Antivirus qui scanne l'exe

**Symptôme** :
- Freeze de 5-10 secondes au démarrage
- CPU élevé du processus antivirus

**Vérification** :
1. Gestionnaire des tâches
2. Regardez si "Antimalware Service Executable" utilise du CPU

**Solution** :
Ajoutez une exclusion antivirus pour `%LOCALAPPDATA%\EMAC_Cache`

**Windows Defender** :
1. Paramètres Windows
2. Confidentialité et sécurité > Sécurité Windows
3. Protection contre les virus et menaces
4. Gérer les paramètres > Exclusions > Ajouter une exclusion
5. Dossier : `C:\Users\VotreNom\AppData\Local\EMAC_Cache`

---

### Cause #3 : Connexion MySQL lente

**Symptôme** :
- Écran de connexion s'affiche rapidement
- Freeze de 5-10 secondes après avoir cliqué sur "Connexion"
- Lag pendant l'utilisation (chargement des données)

**Vérification** :
```batch
# Ouvrir cmd.exe et tester le ping
ping serveur-mysql.entreprise.local

# Résultat attendu :
Réponse de ... : octets=32 temps<10ms TTL=64
```

Si le temps est > 50ms ou si vous voyez "Délai d'attente dépassé", le réseau est lent.

**Solutions** :

1. **MySQL sur serveur distant** :
   - Optimisez les requêtes (ajoutez des index)
   - Utilisez un serveur MySQL plus proche

2. **MySQL local** (recommandé pour tests) :
   - Installez MySQL sur `localhost`
   - Modifiez le `.env` :
     ```
     EMAC_DB_HOST=localhost
     ```

---

### Cause #4 : Trop de modules Python chargés

**Symptôme** :
- Démarrage lent MÊME en local (10-20 secondes)
- Pas de freeze, mais lent au démarrage

**Vérification** :
```batch
dir /b "dist\EMAC\_internal\*.pyd" | find /c ".pyd"
```

Si > 150 fichiers → beaucoup de modules

**Solution** (pour développeurs) :
Recompilez en excluant plus de modules dans `EMAC_optimized.spec`

---

## ✅ Solution PRINCIPALE : Utilisez le lanceur

### Étape 1 : Obtenez le lanceur

Le fichier `Lancer_EMAC.bat` doit vous être fourni par votre service IT.

**Où le mettre** :
- Sur votre bureau
- OU dans un dossier accessible rapidement

---

### Étape 2 : Double-cliquez sur `Lancer_EMAC.bat`

**Premier lancement** (30-60 secondes) :
```
================================================
  EMAC - Gestion Personnel et Polyvalence
================================================

 ⏳ Première installation...
 📂 Copie depuis le réseau vers le disque local
    (Cela peut prendre 30-60 secondes)

 ✅ Copie terminée
 🚀 Lancement d'EMAC...

 ✅ Application lancée avec succès
```

L'application est copiée dans : `C:\Users\VotreNom\AppData\Local\EMAC_Cache`

---

**Lancements suivants** (2-3 secondes) :
```
================================================
  EMAC - Gestion Personnel et Polyvalence
================================================

 ✅ Version locale à jour
 📁 Lancement depuis : C:\Users\...\EMAC_Cache
 🚀 Lancement d'EMAC...

 ✅ Application lancée avec succès
```

**Pas de copie** → Démarrage ultra-rapide ⚡

---

## 🔧 Solutions complémentaires

### Si le lanceur ne résout pas tout

#### 1. Exclusion antivirus (IMPORTANT)

**Temps estimé** : 2 minutes

1. Ouvrez **Paramètres Windows**
2. **Confidentialité et sécurité** > **Sécurité Windows**
3. **Protection contre les virus et menaces**
4. **Gérer les paramètres** (en bas)
5. **Exclusions** > **Ajouter une exclusion** > **Dossier**
6. Tapez : `%LOCALAPPDATA%\EMAC_Cache` et validez

**Gain attendu** : -5 à -10 secondes au démarrage

---

#### 2. Optimiser MySQL

**Pour les administrateurs système** :

```sql
-- Ajouter des index sur les tables fréquemment utilisées
USE emac_db;

-- Index pour la table personnel
CREATE INDEX idx_personnel_statut ON personnel(statut);
CREATE INDEX idx_personnel_nom ON personnel(nom, prenom);

-- Index pour la table polyvalence
CREATE INDEX idx_polyvalence_operateur ON polyvalence(operateur_id);
CREATE INDEX idx_polyvalence_poste ON polyvalence(poste_id);
CREATE INDEX idx_polyvalence_date ON polyvalence(date_evaluation);

-- Analyser les performances
ANALYZE TABLE personnel, polyvalence, postes, contrats;
```

**Gain attendu** : -2 à -5 secondes par requête

---

#### 3. Vérifier le réseau

**Test de latence réseau** :
```batch
ping serveur-mysql.entreprise.local -n 10
```

**Résultat attendu** :
- Temps moyen < 10ms : ✅ Excellent
- Temps moyen 10-50ms : ⚠️ Acceptable
- Temps moyen > 50ms : ❌ Problème réseau

**Solutions** :
- Contactez votre service IT si latence > 50ms
- Utilisez un serveur MySQL plus proche
- En dernier recours : MySQL local pour tests

---

## 📊 Tableau récapitulatif

| Problème | Symptôme | Solution | Gain |
|----------|----------|----------|------|
| **Lancement depuis réseau** | Démarrage 2-5 min | Utiliser `Lancer_EMAC.bat` | **⚡ 99%** |
| **Antivirus** | Freeze 5-10s au démarrage | Exclusion `EMAC_Cache` | **30-50%** |
| **MySQL lent** | Lag pendant utilisation | Optimiser/rapprocher serveur | **20-40%** |
| **Trop de modules** | Lent même en local | Recompiler (dev) | **10-20%** |

---

## 🎯 Checklist de résolution

Pour résoudre 99% des problèmes de lenteur :

- [ ] **Utiliser `Lancer_EMAC.bat`** au lieu de lancer directement EMAC.exe
- [ ] **Ajouter exclusion antivirus** pour `%LOCALAPPDATA%\EMAC_Cache`
- [ ] **Vérifier connexion MySQL** avec `ping serveur-mysql`
- [ ] **Premier lancement** : attendre 30-60 sec (copie normale)
- [ ] **Lancements suivants** : devrait démarrer en 2-3 sec

---

## 🆘 Dépannage

### Problème : Le lanceur ne fonctionne pas

**Symptôme** :
```
❌ ERREUR : Application non trouvée sur le réseau
```

**Solution** :
1. Vérifiez que vous êtes connecté au réseau de l'entreprise
2. Contactez votre service IT pour vérifier le partage réseau

---

### Problème : Toujours lent même avec le lanceur

**Symptôme** :
- Lanceur utilisé correctement
- Application dans `EMAC_Cache`
- Mais toujours lent (> 10 secondes)

**Diagnostic** :
1. Exécutez `Deploy\diagnostic_lenteur.bat`
2. Consultez les résultats
3. Appliquez les recommandations spécifiques

**Ou contactez votre service IT avec** :
- Le fichier log : `%LOCALAPPDATA%\EMAC_Cache\launcher.log`
- Le temps exact de démarrage
- Les étapes qui sont lentes (connexion, chargement des données, etc.)

---

## 📞 Support

**Problème persiste** après avoir appliqué toutes les solutions ?

Contactez votre service IT avec :
1. ✅ Confirmation que vous utilisez `Lancer_EMAC.bat`
2. ✅ Résultat de `diagnostic_lenteur.bat`
3. ✅ Fichier log : `%LOCALAPPDATA%\EMAC_Cache\launcher.log`
4. ✅ Temps exact observé (ex: "30 secondes au démarrage")

---

**Version** : 1.0
**Dernière mise à jour** : Décembre 2025
