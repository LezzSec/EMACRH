# Build Scripts

Scripts pour compiler l'application EMAC en exécutable Windows.

## Utilisation

```bash
cd build-scripts
build.bat
```

Le script va :
1. Vérifier Python et PyInstaller
2. Installer les dépendances si nécessaire
3. Nettoyer les anciens builds
4. Compiler avec PyInstaller (5-10 min)
5. Créer la structure de dossiers
6. Générer les fichiers de configuration

**Résultat** : `dist/EMAC/EMAC.exe`

## Structure de sortie

```
dist/EMAC/
├── EMAC.exe           # Exécutable
├── _internal/         # Dépendances
├── config/
│   └── .env.example   # Configuration
├── database/
│   └── schema.sql     # Schéma DB
├── logs/              # Logs
├── exports/           # Exports
├── LISEZMOI.txt       # Instructions
└── CONFIGURER.bat     # Script config rapide
```

## Configuration après build

```bash
cd dist/EMAC
CONFIGURER.bat    # Créer .env
# Éditer .env avec vos paramètres MySQL
EMAC.exe          # Lancer l'application
```

## Problèmes courants

**"Python non installé"**
→ Installer Python 3.12 et l'ajouter au PATH

**"Module not found"**
→ Le script installe automatiquement les dépendances

**Build échoue**
→ Vérifier que `App/core/gui/main_qt.py` existe

## Optimisations

Le script exclut automatiquement :
- pandas, numpy (non utilisés)
- matplotlib, tkinter
- Modules de test

**Taille attendue** : 80-120 MB

## Notes

- Build dans `build/` (temporaire)
- Distribution dans `dist/EMAC/`
- Le script nettoie automatiquement les anciens builds
- Compatible Windows 10/11

---

**Dernière mise à jour** : 2026-03-17
