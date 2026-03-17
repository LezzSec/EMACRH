# Documentation Complète - Système d'Historique EMAC

## Vue d'ensemble

Le système d'historique EMAC permet de tracer toutes les actions effectuées sur les données du personnel, avec conservation des anciennes valeurs et affichage dans une interface moderne et intuitive.

## Fonctionnalités principales

### ✅ Ce que le système fait :

1. **Enregistre toutes les actions** : INSERT, UPDATE, DELETE sur les compétences
2. **Conserve les anciennes valeurs** : Stockage JSON avec "old" et "new"
3. **Interface utilisateur complète** : Tableau filtrable, zone de détails, dialogue complet
4. **Filtrage avancé** : Par type, poste, période, recherche textuelle
5. **Visualisation claire** : Code couleur, icônes, résumés lisibles
6. **Double-clic pour détails** : Dialogue modal avec toutes les informations

## Documentation disponible

### 1. [GUIDE_INTERFACE_HISTORIQUE.md](GUIDE_INTERFACE_HISTORIQUE.md)
**Pour les utilisateurs finaux**

- Description complète de l'interface
- Comment utiliser les filtres
- Comment lire les détails des actions
- Trucs et astuces d'utilisation

### 2. [STRUCTURE_DONNEES_HISTORIQUE.md](STRUCTURE_DONNEES_HISTORIQUE.md)
**Pour les développeurs**

- Structure de la table `historique`
- Format JSON détaillé pour chaque type d'action
- Requêtes SQL utiles
- Scripts de maintenance et migration
- Bonnes pratiques de logging

### 3. [EXEMPLES_LOGGING_HISTORIQUE.md](EXEMPLES_LOGGING_HISTORIQUE.md)
**Guide pratique avec code**

- Exemples complets pour chaque type d'action
- Code prêt à l'emploi (copy-paste)
- Patterns avancés
- Tests unitaires

## Démarrage rapide

### Pour utiliser l'interface

1. Ouvrir l'application EMAC
2. Aller dans "Gestion du Personnel"
3. Double-cliquer sur un opérateur
4. Cliquer sur l'onglet "**Historique**"

### Pour logger une action dans votre code

```python
from core.services.logger import log_hist
import json

# Exemple : Ajout de compétence
log_hist(
    action="INSERT",
    table_name="polyvalence",
    record_id=poly_id,
    operateur_id=operateur_id,
    poste_id=poste_id,
    description=json.dumps({
        "operateur": f"{prenom} {nom}",
        "poste": poste_code,
        "niveau": 3,
        "type": "ajout"
    }, ensure_ascii=False),
    source="GUI/mon_module"
)
```

## Captures d'écran (descriptions)

### Interface principale
```
┌─────────────────────────────────────────────────────────┐
│  Historique complet                                   │
│ Toutes les actions concernant Jean Dupont              │
├─────────────────────────────────────────────────────────┤
│ Filtres: [Type ▼] [Poste ▼] [Du: __/__/__] [Au: __/__/__]│
│          [ Rechercher...             ] [ Réinitialiser]│
├─────────────────────────────────────────────────────────┤
│ Date/Heure     │ Type  │ Poste │ Résumé                │
├────────────────┼───────┼───────┼───────────────────────┤
│ 01/12/25 14:30 │  UPD │ 0515  │ Modif niveau: 2 → 4   │
│ 15/11/25 09:15 │  INS │ 0830  │ Ajout compétence: N3  │
│ 10/10/25 16:45 │  DEL │ 0620  │ Suppression: N2       │
├─────────────────────────────────────────────────────────┤
│  Détails de l'action sélectionnée                     │
│ ┌─────────────────────────────────────────────────────┐ │
│ │  Opérateur : Jean Dupont                          │ │
│ │  Poste : 0515                                     │ │
│ │ ⭐ Changement niveau : [N2] → [N4]                  │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  3 action(s) affichée(s) sur 15 au total              │
│ Légende: ■ Ajout ■ Modification ■ Suppression ■ Erreur │
└─────────────────────────────────────────────────────────┘
```

## Architecture du code

### Fichiers créés/modifiés

```
EMAC/
├── App/
│   └── core/
│       ├── gui/
│       │   ├── historique_personnel.py    ← NOUVEAU (widget complet)
│       │   └── gestion_personnel.py       ← MODIFIÉ (intégration)
│       └── services/
│           └── logger.py                  ← EXISTANT (utilisé)
└── docs/
    ├── README_HISTORIQUE.md               ← VOUS ÊTES ICI
    ├── GUIDE_INTERFACE_HISTORIQUE.md      ← Guide utilisateur
    ├── STRUCTURE_DONNEES_HISTORIQUE.md    ← Guide développeur
    └── EXEMPLES_LOGGING_HISTORIQUE.md     ← Exemples de code
```

### Classes principales

```python
# historique_personnel.py

class HistoriquePersonnelTab(QWidget):
    """Widget principal - onglet historique dans fiche personnel"""
    - __init__(operateur_id, nom, prenom)
    - _init_ui()            # Construit l'interface
    - _load_data()          # Charge depuis BDD
    - _apply_filters()      # Filtre les données
    - _display_data()       # Affiche dans tableau
    - _on_selection_changed() # Met à jour zone détails
    - _on_double_click()    # Ouvre dialogue complet

class DetailHistoriqueDialog(QDialog):
    """Dialogue modal avec détails complets d'une action"""

class NoEditDelegate(QStyledItemDelegate):
    """Empêche l'édition des cellules"""

# Fonctions utilitaires
def format_datetime(dt)
def get_action_icon_and_color(action)
def parse_description_json(json_str)
def format_action_resume(action, data, poste)
def format_details_html(action, data, poste)
```

## Flux de données

```
┌──────────────────┐
│   Action User    │ (Modifie niveau, ajoute compétence, etc.)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Code métier     │ (manage_operateur.py, gestion_evaluation.py, etc.)
│  1. SELECT old   │ ← IMPORTANT : Récupérer anciennes valeurs
│  2. UPDATE/...   │
│  3. log_hist()   │ ← Appel fonction de logging
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  logger.py       │
│  log_hist(...)   │ Construit et insère dans historique
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Table historique │
│  - id            │
│  - date_time     │
│  - action        │
│  - operateur_id  │
│  - poste_id      │
│  - description   │ ← JSON avec old/new
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────┐
│ HistoriquePersonnelTab      │
│  1. Charge données filtrées │
│  2. Parse JSON              │
│  3. Formate pour affichage  │
│  4. Affiche dans UI         │
└─────────────────────────────┘
```

## Types d'actions supportés

| Type | Couleur | Icône | Usage |
|------|---------|-------|-------|
| INSERT |  Vert |  | Ajout de compétence, import |
| UPDATE |  Bleu |  | Modification niveau, dates |
| DELETE |  Rouge |  | Suppression compétence |
| ERROR |  Orange | ⚠ | Erreurs système |

## Configuration

### Paramètres par défaut

```python
# Dans HistoriquePersonnelTab.__init__()

# Période par défaut : 6 mois
self.date_from.setDate(QDate.currentDate().addMonths(-6))

# Nombre de résultats : illimité (scroll)
# Pour limiter, ajouter LIMIT dans la requête SQL
```

### Personnalisation des couleurs

```python
# Dans get_action_icon_and_color()
ACTION_COLORS = {
    "INSERT": ("#10b981", "#d1fae5"),   # (texte, fond)
    "UPDATE": ("#3b82f6", "#dbeafe"),
    "DELETE": ("#ef4444", "#fee2e2"),
    "ERROR": ("#f59e0b", "#fed7aa")
}
```

## Tests

### Test manuel rapide

1. Ouvrir fiche opérateur
2. Aller sur onglet Historique
3. Vérifier que des actions s'affichent
4. Tester filtres un par un
5. Sélectionner ligne → vérifier zone détails
6. Double-cliquer → vérifier dialogue

### Test automatisé (TODO)

```python
# tests/test_historique_personnel.py
def test_load_historique():
    """Teste le chargement des données"""
    pass

def test_filters():
    """Teste les filtres"""
    pass

def test_json_parsing():
    """Teste le parsing JSON"""
    pass
```

## Résolution de problèmes

### Problème : Aucune donnée n'apparaît

**Causes possibles :**
1. Aucune action enregistrée pour cet opérateur
2. Filtres trop restrictifs
3. Erreur de connexion base de données

**Solutions :**
```python
# Vérifier en SQL
SELECT * FROM historique WHERE operateur_id = 123;

# Réinitialiser les filtres
# Cliquer sur " Réinitialiser"
```

### Problème : JSON invalide dans description

**Cause :** Description mal formée

**Solution :**
```python
# Vérifier validité JSON
import json

try:
    data = json.loads(description)
    print("✅ JSON valide")
except json.JSONDecodeError as e:
    print(f"❌ JSON invalide : {e}")
```

### Problème : Anciennes valeurs manquantes

**Cause :** Log créé sans récupérer l'ancienne valeur

**Solution :**
```python
# TOUJOURS récupérer avant UPDATE/DELETE
cur.execute("SELECT * FROM table WHERE id = %s", (id,))
old_data = cur.fetchone()

# PUIS modifier
cur.execute("UPDATE table SET ... WHERE id = %s", (..., id))

# PUIS logger avec old_data
log_hist(..., description=json.dumps({
    "changes": {
        "field": {
            "old": old_data['field'],
            "new": new_value
        }
    }
}))
```

## Performances

### Optimisations appliquées

- ✅ Index sur `operateur_id` et `date_time`
- ✅ Filtrage en mémoire (rapide pour < 10000 lignes)
- ✅ Pas de rechargement à chaque filtre
- ✅ Parsing JSON à la demande

### Recommandations

- **< 1000 actions** : Performance excellente
- **1000-10000 actions** : Performance bonne
- **> 10000 actions** : Envisager pagination ou archivage

### Script d'archivage

```sql
-- Archiver actions > 2 ans
INSERT INTO historique_archive
SELECT * FROM historique
WHERE date_time < DATE_SUB(NOW(), INTERVAL 2 YEAR);

DELETE FROM historique
WHERE date_time < DATE_SUB(NOW(), INTERVAL 2 YEAR);
```

## Évolutions futures

### Priorité haute
- [ ] Export Excel/PDF de l'historique filtré
- [ ] Graphiques d'évolution (niveaux dans le temps)
- [ ] Comparaison de périodes

### Priorité moyenne
- [ ] Annotations utilisateur sur actions
- [ ] Tags personnalisés
- [ ] Recherche full-text avancée

### Priorité basse
- [ ] Undo/redo (restauration)
- [ ] Notifications temps réel
- [ ] Statistiques avancées

## Support

### Questions fréquentes

**Q : Comment voir l'historique global (tous opérateurs) ?**
R : Utiliser le module `historique.py` existant (menu principal)

**Q : Puis-je modifier l'historique ?**
R : Non, l'historique est en lecture seule (audit trail)

**Q : Combien de temps sont conservées les données ?**
R : Indéfiniment, sauf archivage manuel

**Q : Puis-je exporter l'historique ?**
R : Pas encore implémenté (feature à venir)

### Contact

Pour toute question ou problème :
- Consulter d'abord cette documentation
- Vérifier les logs d'erreur Python
- Vérifier les données SQL directement

## Changelog

### Version 1.0 (Décembre 2025)
- ✅ Création du widget `HistoriquePersonnelTab`
- ✅ Intégration dans `DetailOperateurDialog`
- ✅ Système de filtres complet
- ✅ Zone de détails dynamique
- ✅ Dialogue de détails complets
- ✅ Code couleur par type d'action
- ✅ Documentation complète

---

**Projet** : EMAC - Gestion du Personnel
**Module** : Système d'Historique
**Version** : 1.0
**Date** : Décembre 2025
**Auteur** : Claude Code

**Licence** : Usage interne uniquement
