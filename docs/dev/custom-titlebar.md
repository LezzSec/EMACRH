# Barre de Titre Personnalisée - EMAC

## Vue d'ensemble

La barre de titre personnalisée permet d'avoir les boutons de contrôle de fenêtre (minimiser, maximiser/plein écran, fermer) **directement dans la barre de titre**, comme dans les applications Windows modernes.

## Apparence

```
┌─────────────────────────────────────────────────┐
│ Nom du Dialog                    ―  ⛶  ✕       │ ← Barre de titre personnalisée
├─────────────────────────────────────────────────┤
│                                                 │
│  Contenu de votre dialog ici                   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Boutons :
- **― (Minimiser)** : Réduit la fenêtre dans la barre des tâches
- **⛶ (Maximiser/Plein écran)** : Bascule entre mode normal et maximisé
  - Change en **❐** quand la fenêtre est maximisée
- **✕ (Fermer)** : Ferme la fenêtre
  - Devient rouge au survol (comme Windows)

## Utilisation

### Import

```python
from core.gui.emac_ui_kit import add_custom_title_bar
```

### Exemple basique

```python
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from core.gui.emac_ui_kit import add_custom_title_bar

class MonDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mon Dialog")
        self.setGeometry(200, 200, 800, 600)

        # 1. Layout principal avec marges NULLES
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 2. Ajouter la barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Mon Dialog Personnalisé")
        main_layout.addWidget(title_bar)

        # 3. Créer un widget de contenu avec marges normales
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # 4. Ajouter votre contenu
        content_layout.addWidget(QLabel("Contenu du dialog"))
        content_layout.addWidget(QPushButton("OK"))

        # 5. Ajouter le widget de contenu au layout principal
        main_layout.addWidget(content_widget)
```

## Structure de code requise

### ✅ Structure correcte (OBLIGATOIRE)

```python
def __init__(self):
    super().__init__()

    # Layout principal avec marges nulles
    main_layout = QVBoxLayout(self)
    main_layout.setContentsMargins(0, 0, 0, 0)  # IMPORTANT !
    main_layout.setSpacing(0)

    # Barre de titre
    title_bar = add_custom_title_bar(self, "Titre")
    main_layout.addWidget(title_bar)

    # Widget de contenu séparé
    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(20, 20, 20, 20)  # Marges normales ici

    # Ajouter vos widgets au content_layout
    content_layout.addWidget(...)

    # Ajouter le contenu au main_layout
    main_layout.addWidget(content_widget)
```

### ❌ Structure incorrecte (NE PAS FAIRE)

```python
# ❌ Mauvais : layout avec marges normales
layout = QVBoxLayout(self)  # Devrait être main_layout avec marges nulles

# ❌ Mauvais : ajouter des widgets directement après la barre
title_bar = add_custom_title_bar(self, "Titre")
layout.addWidget(QLabel("..."))  # Devrait être dans un content_widget séparé
```

## Fonctionnalités

### Déplacement de la fenêtre
- **Cliquez et glissez** sur la barre de titre pour déplacer la fenêtre
- **Double-cliquez** sur la barre de titre pour maximiser/restaurer

### Raccourcis clavier
- **F11** : Bascule entre mode normal et plein écran
- Les raccourcis sont automatiquement ajoutés

### Changement d'icône
Le bouton maximiser change automatiquement d'apparence :
- **⛶** : Fenêtre normale (clic → maximiser)
- **❐** : Fenêtre maximisée (clic → restaurer)

## Styles visuels

### Style Windows 11
La barre de titre utilise le style Windows 11 :
```css
- Fond : Blanc (#ffffff)
- Bordure inférieure : Gris clair (#e5e7eb)
- Hauteur : 32px
- Boutons : 46px × 32px
- Hover : Gris très clair (#f3f4f6)
- Hover fermer : Rouge Windows (#e81123)
```

### Personnalisation du style

Vous pouvez modifier le style de la barre via la classe `CustomTitleBar` :

```python
title_bar = add_custom_title_bar(self, "Titre")

# Changer la couleur de fond
title_bar.setStyleSheet("""
    QWidget {
        background: #1e293b;  /* Fond sombre */
        border-bottom: 1px solid #334155;
    }
""")

# Changer la couleur du titre
title_bar.title_label.setStyleSheet("color: white; font-size: 12px; border: none;")
```

## Exemple : Migration d'un dialog existant

### Avant (avec bouton plein écran séparé)

```python
class MonDialog(QDialog):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Header avec bouton plein écran
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Titre"))
        header_layout.addStretch()
        add_fullscreen_button(self, header_layout, style="compact")
        layout.addLayout(header_layout)

        # Contenu
        layout.addWidget(QLabel("Contenu"))
```

### Après (avec barre de titre personnalisée)

```python
class MonDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        title_bar = add_custom_title_bar(self, "Mon Dialog")
        main_layout.addWidget(title_bar)

        # Widget de contenu
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)

        # Contenu (pas de header layout nécessaire)
        layout.addWidget(QLabel("Contenu"))

        main_layout.addWidget(content)
```

## Dialogs déjà migrés

- ✅ [DetailOperateurDialog](../App/core/gui/gestion_personnel.py) - Détails opérateur

## À migrer

Pour migrer les autres dialogs, appliquez la même structure :

1. **GestionEvaluationDialog** ([gestion_evaluation.py](../App/core/gui/gestion_evaluation.py))
2. **HistoriqueDialog** ([historique.py](../App/core/gui/historique.py))
3. **GrillesDialog** ([liste_et_grilles.py](../App/core/gui/liste_et_grilles.py))
4. **RegularisationDialog** ([planning.py](../App/core/gui/planning.py))
5. **GestionAbsencesDialog** ([gestion_absences.py](../App/core/gui/gestion_absences.py))

## Test

Un fichier de test est disponible : [test_custom_titlebar.py](../App/tests/test_custom_titlebar.py)

```bash
cd App/tests
py test_custom_titlebar.py
```

## Limitations

- La barre de titre personnalisée **supprime le cadre par défaut de Windows** (frameless window)
- Le redimensionnement se fait uniquement par les bords de la fenêtre, pas par les coins de la barre de titre
- La fenêtre ne peut pas être "snappée" avec Windows + flèches (limitation des fenêtres frameless PyQt)

## Support

Pour toute question ou problème, voir [emac_ui_kit.py](../App/core/gui/emac_ui_kit.py) lignes 290-446.
