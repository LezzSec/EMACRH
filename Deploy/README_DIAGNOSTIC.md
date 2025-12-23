# Scripts de diagnostic EMAC

## 📋 Fichiers disponibles

| Fichier | Description | Quand l'utiliser |
|---------|-------------|------------------|
| `diagnostic_simple.bat` | Diagnostic rapide avec rapport sauvegardé | ⭐ **Recommandé** - Problème de lenteur |
| `diagnostic_lenteur.bat` | Diagnostic détaillé interactif | Pour analyse avancée |
| `test_deploiement.bat` | Validation avant déploiement | Avant de copier sur le réseau |

---

## ⚡ Utilisation rapide : `diagnostic_simple.bat`

### Quand l'utiliser ?

- ✅ EMAC met plus de 10 secondes à démarrer
- ✅ Freezes pendant la saisie de texte
- ✅ Vous voulez comprendre pourquoi c'est lent

### Comment l'exécuter ?

1. **Double-cliquez** sur `diagnostic_simple.bat`
2. **Attendez** 5-10 secondes (le script analyse)
3. **Lisez** le rapport qui s'affiche
4. Le fichier `diagnostic_rapport.txt` s'ouvre automatiquement dans Notepad

### Que fait ce script ?

Le script vérifie 6 points critiques :

1. **Emplacement de l'exe** : Réseau ou disque local ?
2. **Taille de l'exe** : Trop gros = plus lent
3. **Configuration MySQL** : Serveur accessible ?
4. **Antivirus** : Exclusions configurées ?
5. **Cache local** : `Lancer_EMAC.bat` déjà utilisé ?
6. **Modules Python** : Trop de bibliothèques chargées ?

### Résultat

Le script génère un fichier `diagnostic_rapport.txt` contenant :

```
===================================================
  DIAGNOSTIC DE LENTEUR EMAC
  Date : 23/12/2025 10:30:15
===================================================

[1/6] Emplacement d'execution
--------------------------------
Chemin : C:\Users\...\App\dist\EMAC\EMAC.exe
Statut : [OK] Exe sur disque local

[2/6] Taille de l'executable
--------------------------------
Taille : 11 Mo
Statut : [ATTENTION] Taille elevee
Impact : +2-3 secondes au demarrage

...

===================================================
  VERDICT : CONFIGURATION CORRECTE
===================================================

La configuration est globalement correcte.
```

---

## 🔧 Exemple de diagnostic typique

### Problème : Lancement depuis le réseau

**Rapport généré** :
```
[1/6] Emplacement d'execution
--------------------------------
Chemin : \\s_data\Bureautique\Services\THOMAS\EMAC\EMAC.exe
Statut : [PROBLEME] EXE SUR PARTAGE RESEAU
Impact : Demarrage 2-5 minutes
Solution : Utiliser Lancer_EMAC.bat

===================================================
  VERDICT : PROBLEME MAJEUR DETECTE
===================================================

[CRITIQUE] L'exe est lance depuis le reseau
  Impact : +2-5 minutes au demarrage
  Solution : Utiliser OBLIGATOIREMENT Lancer_EMAC.bat
```

**Action à prendre** :
```batch
# Au lieu de lancer EMAC.exe directement
\\s_data\...\EMAC\EMAC.exe  ❌

# Utilisez le lanceur
Deploy\Lancer_EMAC.bat  ✅
```

---

### Problème : Pas de cache local

**Rapport généré** :
```
[5/6] Cache local (Lancer_EMAC.bat)
--------------------------------
Statut : [ATTENTION] Pas de cache local

Vous n'avez jamais utilise Lancer_EMAC.bat
ou le cache a ete supprime

Premier lancement avec le lanceur : 30-60 sec (copie)
Lancements suivants : 2-3 sec
```

**Action à prendre** :
Double-cliquez sur `Lancer_EMAC.bat` pour créer le cache

---

### Problème : MySQL inaccessible

**Rapport généré** :
```
[3/6] Configuration MySQL
--------------------------------
Serveur : serveur-mysql.entreprise.local
Base    : emac_db
Test ping vers serveur-mysql.entreprise.local...
Statut : [PROBLEME] Serveur inaccessible ou lent
Solution : Verifier la connexion reseau
```

**Action à prendre** :
1. Vérifiez que vous êtes sur le réseau de l'entreprise
2. Testez manuellement : `ping serveur-mysql.entreprise.local`
3. Contactez le service IT si le problème persiste

---

## 📊 Interprétation du verdict

### VERDICT : PROBLEME MAJEUR DETECTE

**Signification** : Un problème critique ralentit EMAC de plusieurs minutes

**Causes fréquentes** :
- Exe lancé depuis le réseau (au lieu du cache local)
- Pas de cache local configuré

**Solution** : Utiliser `Lancer_EMAC.bat` **obligatoirement**

---

### VERDICT : PROBLEMES MINEURS DETECTES

**Signification** : La config est OK mais peut être optimisée

**Causes fréquentes** :
- Antivirus qui scanne l'exe
- Exe un peu volumineux (10+ Mo)
- MySQL légèrement lent

**Solutions** :
1. Ajouter exclusion antivirus : `%LOCALAPPDATA%\EMAC_Cache`
2. Vérifier ping MySQL
3. Pas d'action urgente nécessaire

---

### VERDICT : CONFIGURATION CORRECTE

**Signification** : Tout est optimal

**Si EMAC est toujours lent** :
- Problème matériel (disque dur lent, RAM insuffisante)
- Problème réseau général
- Contactez le support IT avec le fichier `diagnostic_rapport.txt`

---

## 📁 Fichiers générés

### `diagnostic_rapport.txt`

**Emplacement** : `Deploy\diagnostic_rapport.txt`

**Contenu** : Rapport complet du diagnostic

**Usage** :
- Consultez-le pour comprendre le problème
- Envoyez-le au support IT si besoin d'aide
- Conservez-le pour comparer après corrections

**Exemple** :
```
C:\Projet\EMAC\Deploy\
├── diagnostic_simple.bat      ← Script à lancer
├── diagnostic_rapport.txt     ← Rapport généré
└── Lancer_EMAC.bat           ← Solution recommandée
```

---

## 🚀 Actions immédiates recommandées

Après avoir exécuté le diagnostic, suivez ces étapes dans l'ordre :

### 1. Utiliser le lanceur

```batch
# Copiez Lancer_EMAC.bat sur votre bureau
copy Deploy\Lancer_EMAC.bat %USERPROFILE%\Desktop\

# Ensuite, double-cliquez toujours sur ce fichier
# (Jamais sur EMAC.exe directement)
```

**Premier lancement** : 30-60 sec (copie)
**Lancements suivants** : 2-3 sec ⚡

---

### 2. Ajouter exclusion antivirus

**Windows Defender** :
1. Paramètres Windows
2. Confidentialité et sécurité > Sécurité Windows
3. Protection contre les virus et menaces
4. Gérer les paramètres > Exclusions
5. Ajouter un dossier : `%LOCALAPPDATA%\EMAC_Cache`

**Gain attendu** : -5 à -10 secondes

---

### 3. Vérifier MySQL

```batch
# Ouvrir cmd.exe
ping serveur-mysql.entreprise.local

# Résultat attendu :
# temps<10ms = Excellent
# temps 10-50ms = OK
# temps >50ms = Lent (contactez IT)
```

---

## 🔄 Comparer avant/après

### Avant corrections

```
Démarrage : 2-5 minutes
Freeze pendant saisie : Oui (5-10 sec)
Verdict : PROBLEME MAJEUR DETECTE
```

### Après corrections (avec Lancer_EMAC.bat)

```
Démarrage : 2-3 secondes
Freeze pendant saisie : Non
Verdict : CONFIGURATION CORRECTE
```

**Amélioration** : **99% plus rapide** 🚀

---

## 📞 Support

**Le diagnostic indique un problème que vous ne comprenez pas ?**

Envoyez au support IT :
1. Le fichier `diagnostic_rapport.txt`
2. Une description du problème exact
3. Le temps observé (ex: "30 secondes au démarrage")

**Email type** :
```
Objet : EMAC lent - Diagnostic joint

Bonjour,

EMAC met 2 minutes à démarrer sur mon poste.
Ci-joint le rapport de diagnostic.

Merci de votre aide.
```

---

**Version** : 1.0
**Dernière mise à jour** : Décembre 2025
