# Guide du Système d'Historique de Polyvalence

## Vue d'ensemble

Le système d'historique de polyvalence EMAC permet de :
- **Tracer automatiquement** toutes les modifications de polyvalences (ajouts, modifications, suppressions)
- **Importer manuellement** des données historiques pour lesquelles vous n'aviez pas de traçabilité
- **Visualiser** l'historique complet avec filtres avancés et détails

## Fonctionnalités principales

### 1. Traçabilité automatique
Toutes les actions sur les polyvalences sont automatiquement enregistrées avec :
- Date et heure de l'action
- Type d'action (AJOUT, MODIFICATION, SUPPRESSION)
- Anciennes et nouvelles valeurs (niveaux, dates d'évaluation)
- Utilisateur ayant effectué l'action
- Source de l'action (GUI, Import, etc.)

### 2. Import manuel de données historiques
Pour ajouter des actions passées sans traçabilité automatique :
- Interface dédiée pour saisir les anciennes données
- Possibilité d'ajouter un commentaire pour chaque action
- Regroupement par lot d'import (batch)
- Import CSV (à venir)

### 3. Visualisation avancée
- Tableau avec toutes les actions pour un opérateur
- Filtres par type, poste, période
- Recherche textuelle
- Double-clic pour voir les détails complets
- Badge "[Détaillé]" pour les données importées manuellement

## Architecture du système

### Tables de base de données

#### Table `historique_polyvalence`
Table principale stockant les détails de chaque action :

```sql
CREATE TABLE historique_polyvalence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_action DATETIME NOT NULL,
    action_type ENUM('AJOUT', 'MODIFICATION', 'SUPPRESSION', 'IMPORT_MANUEL'),
    operateur_id INT NOT NULL,
    poste_id INT NOT NULL,
    polyvalence_id INT NULL,

    -- Anciennes valeurs
    ancien_niveau INT NULL,
    ancienne_date_evaluation DATE NULL,
    ancienne_prochaine_evaluation DATE NULL,

    -- Nouvelles valeurs
    nouveau_niveau INT NULL,
    nouvelle_date_evaluation DATE NULL,
    nouvelle_prochaine_evaluation DATE NULL,

    -- Métadonnées
    utilisateur VARCHAR(100) NULL,
    commentaire TEXT NULL,
    source VARCHAR(100) NOT NULL DEFAULT 'SYSTEM',
    import_batch_id VARCHAR(50) NULL,

    -- Indexes et clés étrangères...
)
```

#### Vue `v_historique_polyvalence_complet`
Vue facilitant les requêtes avec jointures automatiques sur personnel et postes.

#### Table `historique` (existante)
La table historique générale continue d'exister. Un **trigger automatique** synchronise les deux tables :
- Chaque insertion dans `historique_polyvalence` crée automatiquement une entrée dans `historique`
- Permet de conserver la compatibilité avec l'ancien système

## Utilisation

### Pour l'utilisateur final

#### 1. Voir l'historique d'un opérateur

1. Ouvrir **Gestion du Personnel**
2. Double-cliquer sur un opérateur
3. Cliquer sur l'onglet **"Historique"**
4. L'historique complet s'affiche avec :
   - Colonne "Date/Heure" : Quand l'action a eu lieu
   - Colonne "Type" : Type d'action avec code couleur
   - Colonne "Table" : Source des données
   - Colonne "Résumé" : Description de l'action

#### 2. Filtrer l'historique

Utilisez les filtres en haut de l'interface :
- **Type** : Tous / Ajouts / Modifications / Suppressions / Erreurs
- **Poste** : Filtrer par poste spécifique
- **Période** : Date de début et date de fin
- **Recherche** : Recherche textuelle dans les descriptions

Cliquez sur **"Réinitialiser"** pour réinitialiser tous les filtres.

#### 3. Voir les détails d'une action

- **Double-cliquez** sur une ligne du tableau
- Un dialogue s'ouvre avec :
  - Toutes les informations de l'action
  - Anciennes et nouvelles valeurs
  - Commentaires éventuels
  - Source et utilisateur

#### 4. Importer des données historiques

1. Dans l'onglet "Historique", cliquez sur **" Import manuel"**
2. Remplissez le formulaire :
   - Date de l'action
   - Type d'action (AJOUT, MODIFICATION, SUPPRESSION)
   - Opérateur et poste
   - Niveaux (ancien et/ou nouveau selon le type)
   - Dates d'évaluation
   - Commentaire explicatif (recommandé !)
3. Cliquez sur **" Ajouter à la liste"**
4. Répétez pour toutes les actions à ajouter
5. Cliquez sur **" Enregistrer toutes les actions"**

**Astuce** : Ajoutez toujours un commentaire pour expliquer le contexte de l'action historique !

### Pour le développeur

#### 1. Logger une action automatiquement

Utilisez le service `polyvalence_logger` dans votre code :

```python
from core.services.polyvalence_logger import log_polyvalence_ajout

# Lors de l'ajout d'une polyvalence
log_polyvalence_ajout(
    operateur_id=operateur_id,
    poste_id=poste_id,
    polyvalence_id=poly_id,
    niveau=3,
    date_evaluation=date_evaluation,
    prochaine_evaluation=prochaine_evaluation,
    utilisateur="Jean Dupont",  # optionnel
    source="GUI"
)
```

Fonctions disponibles :
- `log_polyvalence_ajout()` - Pour un ajout
- `log_polyvalence_modification()` - Pour une modification
- `log_polyvalence_suppression()` - Pour une suppression
- `log_polyvalence_action()` - Fonction générique

#### 2. Récupérer l'historique

```python
from core.services.polyvalence_logger import (
    get_historique_operateur,
    get_historique_poste,
    get_statistiques_operateur
)

# Historique complet d'un opérateur
historique = get_historique_operateur(operateur_id, limit=50)

# Historique pour un poste spécifique
historique_poste = get_historique_poste(operateur_id, poste_id)

# Statistiques
stats = get_statistiques_operateur(operateur_id)
# Returns: {total_actions, nb_ajouts, nb_modifications, nb_suppressions, ...}
```

#### 3. Import programmatique

```python
from core.services.polyvalence_logger import log_polyvalence_action
from datetime import datetime, date

# Import d'une ancienne action
log_polyvalence_action(
    action_type='IMPORT_MANUEL',
    operateur_id=123,
    poste_id=45,
    polyvalence_id=None,  # NULL pour import manuel
    nouveau_niveau=2,
    nouvelle_date_evaluation=date(2020, 1, 15),
    nouvelle_prochaine_evaluation=date(2030, 1, 15),
    utilisateur="Import Script",
    commentaire="Import des données 2020",
    source="IMPORT_MANUEL",
    import_batch_id="BATCH_2020_Q1",
    date_action=datetime(2020, 1, 15, 10, 0, 0)
)
```

## Administration

### Scripts utiles

#### Créer la table (première installation)
```bash
cd App
python scripts/create_historique_polyvalence.py
```

#### Tester le système
```bash
cd App
python tests/test_historique_polyvalence.py
```

#### Requêtes SQL utiles

```sql
-- Voir toutes les actions d'un opérateur
SELECT * FROM v_historique_polyvalence_complet
WHERE operateur_id = 123
ORDER BY date_action DESC;

-- Statistiques globales
SELECT
    action_type,
    COUNT(*) as nb_actions,
    COUNT(DISTINCT operateur_id) as nb_operateurs
FROM historique_polyvalence
GROUP BY action_type;

-- Actions importées manuellement
SELECT * FROM historique_polyvalence
WHERE action_type = 'IMPORT_MANUEL'
ORDER BY date_action DESC;

-- Actions par lot d'import
SELECT import_batch_id, COUNT(*) as nb_actions
FROM historique_polyvalence
WHERE import_batch_id IS NOT NULL
GROUP BY import_batch_id;
```

### Maintenance

#### Archivage des anciennes données
Si la table devient trop volumineuse (> 100 000 lignes), vous pouvez archiver :

```sql
-- Créer table d'archive
CREATE TABLE historique_polyvalence_archive LIKE historique_polyvalence;

-- Archiver données > 5 ans
INSERT INTO historique_polyvalence_archive
SELECT * FROM historique_polyvalence
WHERE date_action < DATE_SUB(NOW(), INTERVAL 5 YEAR);

DELETE FROM historique_polyvalence
WHERE date_action < DATE_SUB(NOW(), INTERVAL 5 YEAR);
```

#### Nettoyer les données de test
```sql
-- Supprimer les actions de test
DELETE FROM historique_polyvalence
WHERE source LIKE '%TEST%' OR import_batch_id LIKE 'TEST%';
```

## Bonnes pratiques

### Pour les imports manuels

1. **Grouper par période** : Utilisez le même `import_batch_id` pour un ensemble cohérent
   - Exemple : "IMPORT_2020_Q1", "IMPORT_MIGRATION_SYSTEME"

2. **Ajouter des commentaires clairs** : Expliquez le contexte
   - ✅ "Formation initiale sur le poste - Évaluation théorique + pratique"
   - ❌ "Formation"

3. **Respecter la chronologie** : Importez dans l'ordre chronologique

4. **Vérifier les données** : Avant l'import définitif, vérifiez dans l'interface

### Pour le développement

1. **Toujours récupérer les anciennes valeurs avant UPDATE** :
   ```python
   # ✅ BON
   cur.execute("SELECT * FROM polyvalence WHERE id = %s", (id,))
   old_data = cur.fetchone()

   cur.execute("UPDATE polyvalence SET niveau = %s WHERE id = %s", (new_level, id))

   log_polyvalence_modification(
       ancien_niveau=old_data['niveau'],
       nouveau_niveau=new_level,
       ...
   )
   ```

2. **Utiliser les transactions** : Log et modification dans la même transaction

3. **Gérer les erreurs** : Log les erreurs dans `historique` avec action='ERROR'

4. **Documenter le code** : Commentez pourquoi vous loggez telle action

## Dépannage

### Problème : Les données ne s'affichent pas

**Causes possibles** :
1. Filtres trop restrictifs → Cliquer sur "Réinitialiser"
2. Aucune donnée pour cet opérateur → Vérifier en SQL
3. Erreur de connexion BDD → Vérifier les logs

### Problème : Erreur lors de l'import manuel

**Erreur** : "Cannot add or update a child row: a foreign key constraint fails"

**Solution** : L'opérateur ou le poste n'existe plus dans la base. Vérifiez les IDs.

### Problème : Données en double

Si vous voyez des doublons dans l'historique :
- C'est normal si une action existe dans les deux tables (historique + historique_polyvalence)
- Les données de `historique_polyvalence` ont le badge "[Détaillé]"
- C'est voulu pour avoir le maximum d'informations

## Support

Pour toute question :
1. Consulter cette documentation
2. Vérifier les scripts dans `App/scripts/`
3. Consulter les tests dans `App/tests/test_historique_polyvalence.py`
4. Vérifier les logs d'erreur Python

---

**Version** : 1.0
**Date** : Décembre 2025
**Auteur** : Claude Code
**Projet** : EMAC - Gestion du Personnel
