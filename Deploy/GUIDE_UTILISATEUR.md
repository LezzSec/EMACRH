# Guide Utilisateur EMAC - Lancement depuis le réseau

## 🚀 Démarrage rapide

### Première utilisation

1. **Double-cliquez** sur le fichier `Lancer EMAC.bat` sur votre bureau

2. **Attendez 30-60 secondes** pendant l'installation automatique :
   ```
   ⏳ Première installation...
   📂 Copie depuis le réseau vers le disque local
      (Cela peut prendre 30-60 secondes)

   ✅ Copie terminée
   🚀 Lancement d'EMAC...
   ```

3. **C'est terminé !** EMAC s'ouvre automatiquement

### Utilisations suivantes

1. **Double-cliquez** sur `Lancer EMAC.bat`

2. **L'application démarre en 2-3 secondes** :
   ```
   ✅ Version locale à jour
   📁 Lancement depuis le disque local
   🚀 Lancement d'EMAC...
   ```

---

## ❓ Questions fréquentes

### Pourquoi la première fois est-elle plus longue ?

Le lanceur copie l'application sur votre ordinateur pour que les prochains démarrages soient rapides (2-3 secondes au lieu de plusieurs minutes).

### Où est stockée l'application ?

Dans un dossier caché sur votre ordinateur :
```
C:\Users\VotreNom\AppData\Local\EMAC_Cache
```

Vous n'avez pas besoin d'y accéder manuellement.

### Que se passe-t-il lors d'une mise à jour ?

Le lanceur détecte automatiquement les nouvelles versions et recopie l'application (30-60 secondes). Vous verrez ce message :
```
🔄 Mise à jour disponible...
📂 Copie depuis le réseau vers le disque local
```

### Puis-je lancer EMAC sans le lanceur ?

**Non recommandé**. Si vous lancez directement `EMAC.exe` depuis le réseau, l'application mettra **plusieurs minutes** à démarrer au lieu de quelques secondes.

---

## 🛠️ Résolution de problèmes

### Problème : "Application non trouvée sur le réseau"

**Message d'erreur** :
```
❌ ERREUR : Application non trouvée sur le réseau
```

**Que faire** :
1. Vérifiez que vous êtes connecté au réseau de l'entreprise
2. Contactez votre service informatique

---

### Problème : "Échec de la copie depuis le réseau"

**Message d'erreur** :
```
❌ ERREUR : Échec de la copie depuis le réseau
   Code d'erreur : 8
```

**Que faire** :
1. Fermez toutes les fenêtres EMAC ouvertes
2. Réessayez de lancer l'application
3. Si le problème persiste, contactez votre service informatique

---

### Problème : L'application plante au démarrage

**Symptôme** : EMAC se lance mais se ferme immédiatement

**Que faire** :
1. **Supprimez le cache** en ouvrant l'Explorateur Windows et en tapant dans la barre d'adresse :
   ```
   %LOCALAPPDATA%\EMAC_Cache
   ```
   Supprimez ce dossier complètement

2. **Relancez** `Lancer EMAC.bat`
   L'application sera réinstallée automatiquement

3. Si le problème persiste, contactez votre service informatique

---

### Problème : Démarrage lent (> 30 secondes)

**Symptôme** : Même après la première installation, l'application met plus de 30 secondes à démarrer

**Que faire** :
1. Contactez votre service informatique
2. Indiquez que vous avez besoin d'une **exclusion antivirus pour EMAC**

---

## 📞 Besoin d'aide ?

Si vous rencontrez un problème non listé ci-dessus :

1. **Notez le message d'erreur exact**
2. **Contactez votre service informatique** en précisant :
   - Le message d'erreur complet
   - L'heure à laquelle le problème s'est produit
   - Si c'était la première utilisation ou non

Votre service informatique pourra consulter les logs techniques pour diagnostiquer le problème.

---

## ✅ Utilisation normale

Une fois EMAC lancé avec succès :

1. **Connectez-vous** avec vos identifiants
2. **Utilisez l'application** normalement
3. **Fermez EMAC** quand vous avez terminé

Le prochain lancement sera **rapide** (2-3 secondes) !

---

**Astuce** : Vous pouvez créer un raccourci de `Lancer EMAC.bat` sur votre bureau ou épingler à la barre des tâches pour un accès rapide.
