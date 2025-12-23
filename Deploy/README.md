# EMAC - Déploiement Réseau

Ce dossier contient tous les outils nécessaires pour déployer EMAC sur un partage réseau d'entreprise avec un démarrage optimisé.

## 📁 Fichiers disponibles

| Fichier | Description | Pour qui ? |
|---------|-------------|------------|
| `Lancer_EMAC.bat` | Lanceur optimisé avec cache local | 👥 Utilisateurs finaux |
| `README_DEPLOIEMENT.md` | Guide complet de déploiement | 👨‍💼 Administrateurs système |
| `GUIDE_UTILISATEUR.md` | Instructions simples pour les utilisateurs | 👥 Utilisateurs finaux |
| `test_deploiement.bat` | Script de validation pré-déploiement | 👨‍💼 Administrateurs système |
| `README.md` | Ce fichier | Tous |

---

## 🚀 Démarrage rapide

### Pour les administrateurs système

1. **Testez le déploiement** :
   ```batch
   cd Deploy
   test_deploiement.bat
   ```

2. **Consultez le guide complet** :
   - Ouvrez [README_DEPLOIEMENT.md](README_DEPLOIEMENT.md)

3. **Déployez en 3 étapes** :
   - Copier `dist\EMAC` sur le réseau
   - Configurer `Lancer_EMAC.bat` avec le chemin réseau
   - Distribuer le lanceur aux utilisateurs

### Pour les utilisateurs finaux

1. **Recevez** `Lancer_EMAC.bat` de votre service IT
2. **Copiez-le** sur votre bureau
3. **Double-cliquez** pour lancer EMAC

Consultez le [GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md) en cas de problème.

---

## ⚡ Performances attendues

| Situation | Temps de démarrage |
|-----------|-------------------|
| Premier lancement (installation locale) | 30-60 secondes |
| Lancements suivants (cache local) | 2-3 secondes |
| Mise à jour détectée | 30-60 secondes |
| **Sans lanceur** (réseau direct) | ❌ 2-5 minutes |

---

## 🔧 Comment ça marche ?

Le système de **cache local** :

1. Le lanceur détecte si EMAC est déjà installé localement
2. Si non → Copie depuis le réseau vers `%LOCALAPPDATA%\EMAC_Cache`
3. Si oui → Vérifie les mises à jour et lance depuis le cache

**Résultat** : Démarrage aussi rapide qu'une installation locale, avec mises à jour automatiques depuis le réseau.

---

## 📋 Checklist de déploiement

- [ ] Tests passés avec `test_deploiement.bat`
- [ ] Partage réseau configuré avec permissions lecture seule
- [ ] `.env` présent dans `dist\EMAC` avec le mot de passe MySQL
- [ ] `Lancer_EMAC.bat` configuré avec le bon chemin réseau
- [ ] Test réussi depuis un poste utilisateur
- [ ] Documentation distribuée aux utilisateurs
- [ ] Exclusions antivirus configurées sur `%LOCALAPPDATA%\EMAC_Cache`

---

## 📞 Support

**Problèmes de déploiement** :
- Consultez [README_DEPLOIEMENT.md](README_DEPLOIEMENT.md) section "Dépannage"
- Vérifiez les logs : `%LOCALAPPDATA%\EMAC_Cache\launcher.log`

**Questions utilisateurs** :
- Dirigez-les vers [GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md)

---

## 🔄 Mise à jour de l'application

1. Recompilez avec PyInstaller
2. Copiez `dist\EMAC` sur le réseau (écrase l'ancienne version)
3. Les utilisateurs seront automatiquement mis à jour au prochain lancement

**Aucune action utilisateur requise !**

---

**Version** : 1.0
**Dernière mise à jour** : Décembre 2025
