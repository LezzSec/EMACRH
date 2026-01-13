# Guide Rapide - Compilation EMAC

## 🚀 Compilation avec mode debug (RECOMMANDÉ EN PREMIER)

```bash
# Étape 1 : Lancer la compilation debug
build_debug.bat

# Étape 2 : Tester l'application
cd dist\EMAC
EMAC_debug.bat
```

**Résultat attendu** :
- Une console s'affiche
- L'application démarre
- Vous pouvez vous connecter
- Si crash → l'erreur s'affiche dans la console

## ✅ Si l'application fonctionne

### Créer la version finale (sans console)

1. **Modifier [EMAC.spec](EMAC.spec)** lignes 252-254 :
   ```python
   strip=True,     # Au lieu de False
   console=False,  # Au lieu de True
   ```

2. **Compiler la version finale** :
   ```bash
   build_release.bat
   ```

3. **Distribuer** :
   - Copiez tout le dossier `dist\EMAC\`
   - Incluez le fichier `.env` avec les paramètres DB

## 🔴 Si l'application crash

1. **Relevez l'erreur exacte** affichée dans la console

2. **Consultez** [FIX_CRASH_EXE.md](FIX_CRASH_EXE.md) pour les diagnostics

3. **Erreurs courantes** :

### "No module named 'XXX'"
→ Ajoutez `'XXX'` dans `HIDDEN_IMPORTS` du fichier [EMAC.spec](EMAC.spec)

### "cannot import name 'XXX' from 'YYY'"
→ Ajoutez `'YYY.XXX'` dans `HIDDEN_IMPORTS`

### "Failed to execute script"
→ Vérifiez que le fichier `.env` est présent dans `dist\EMAC\`

### Application se ferme immédiatement
→ Utilisez `EMAC_debug.bat` au lieu de `EMAC.exe` directement

## 📁 Structure après compilation

```
dist/
└── EMAC/
    ├── EMAC.exe              ← Exécutable principal
    ├── .env                  ← Configuration DB (REQUIS)
    ├── EMAC_debug.bat        ← Lanceur avec console (debug uniquement)
    ├── python310.dll         ← Runtime Python
    ├── _internal/            ← Dépendances et modules
    │   ├── PyQt5/
    │   ├── mysql/
    │   └── ...
    └── ... (autres DLLs)
```

## 🔧 Scripts disponibles

| Script | Usage | Console |
|--------|-------|---------|
| `build_debug.bat` | Compilation avec console pour debug | ✅ Oui |
| `build_release.bat` | Compilation finale sans console | ❌ Non |
| `dist\EMAC\EMAC_debug.bat` | Lancer l'exe avec pause (debug) | ✅ Oui |

## 📊 Checklist avant distribution

- [ ] L'application fonctionne en mode debug
- [ ] `EMAC.spec` est en mode release (`console=False`, `strip=True`)
- [ ] La version finale fonctionne
- [ ] Le fichier `.env` est inclus avec les paramètres DB corrects
- [ ] Tout le dossier `dist\EMAC\` est copié (pas juste l'exe)

## 💡 Astuces

### Tester rapidement sans recompiler
```bash
cd dist\EMAC
EMAC.exe
```

### Voir les logs de l'application
```bash
# Les logs sont dans :
dist\EMAC\logs\
```

### Réduire la taille du build
Dans [EMAC.spec](EMAC.spec), ajoutez d'autres modules inutilisés dans `EXCLUDES`

### Accélérer la compilation
Ajoutez `--noconfirm` à la commande pyinstaller dans les scripts .bat

## 🆘 Besoin d'aide ?

1. **Logs de compilation** : Consultez la sortie de `build_debug.bat`
2. **Erreurs runtime** : Lancez avec `EMAC_debug.bat` pour voir la console
3. **Documentation complète** : [FIX_CRASH_EXE.md](FIX_CRASH_EXE.md)
4. **Projet** : [CLAUDE.md](CLAUDE.md)

## 📈 Historique des versions

| Date | Version | Changement |
|------|---------|------------|
| 2026-01-13 | Fix crash | Correction exclusions modules (asyncio, concurrent.futures) |
| ... | ... | ... |

## ⚠️ IMPORTANT

**Ne jamais** exclure ces modules dans `EMAC.spec` :
- `concurrent.futures` (utilisé par QThreadPool)
- `asyncio` (requis par Python 3.x)
- `unittest` (dépendances système)
- `email` (modules standard)
- `queue` (threading)
- `traceback` (gestion erreurs)
